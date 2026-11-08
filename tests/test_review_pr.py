"""PR review protocol and trust-boundary regressions (no credentials/tools needed)."""

import base64
import html
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import review_pr as review


SHA = "a" * 40
BASE = "b" * 40
PR = {
    "state": "open",
    "draft": False,
    "changed_files": 1,
    "head": {"sha": SHA, "repo": {"full_name": "owner/repo"}},
    "base": {"sha": BASE},
}


def api_for(pr=None):
    api = Mock(token="not-a-real-token")
    api.request.return_value = pr or PR
    api.pages.side_effect = [[], [{"filename": "builder/data.py"}], []]
    return api


class GitHubTests(unittest.TestCase):
    def test_posts_json_to_fixed_https_host_and_closes_connection(self):
        response = BytesIO(b'{"id": 123}')
        response.status = 201
        with patch.object(review, "HTTPSConnection") as connection:
            client = connection.return_value
            client.getresponse.return_value = response
            result = review.GitHub("owner/repo", "not-a-real-token").request(
                "pulls/42/reviews",
                {"event": "COMMENT"},
            )
        self.assertEqual(result, {"id": 123})
        connection.assert_called_once_with("api.github.com", timeout=30)
        self.assertEqual(
            client.request.call_args.args[:2], ("POST", "/repos/owner/repo/pulls/42/reviews")
        )
        client.close.assert_called_once()

    def test_http_error_or_redirect_is_not_followed(self):
        for status in [301, 403, 422, 500]:
            with patch.object(review, "HTTPSConnection") as connection:
                client = connection.return_value
                client.getresponse.return_value.status = status
                with self.assertRaises(review.ReviewError):
                    review.GitHub("owner/repo", "not-a-real-token").request("pulls/42")
                client.close.assert_called_once()

    def test_pagination_reads_past_first_page(self):
        github = review.GitHub("owner/repo", "not-a-real-token")
        with patch.object(github, "request", side_effect=[list(range(100)), [100]]) as request:
            self.assertEqual(list(github.pages("pulls/42/files")), list(range(101)))
        self.assertEqual(request.call_args.args[0], "pulls/42/files?per_page=100&page=2")

    def test_rejects_untrusted_repository_urls(self):
        for repository in ["https://evil.test/repo", "owner/repo/../../x", "owner/repo\n"]:
            with self.assertRaises(review.ReviewError):
                review.GitHub(repository, "not-a-real-token")


class ChangedLinesTests(unittest.TestCase):
    def test_multiple_hunks_and_removed_lines(self):
        patch_text = (
            "@@ -1,3 +1,3 @@\n context\n-old\n+replacement\n context\n"
            "@@ -10,0 +11,2 @@\n+first\n+second\n\\ No newline at end of file"
        )
        self.assertEqual(review.added_lines(patch_text), {2, 11, 12})

    def test_deletion_and_context_are_not_additions(self):
        self.assertEqual(review.added_lines("@@ -1,2 +1 @@\n-old\n context"), set())

    def test_added_content_that_looks_like_a_header(self):
        self.assertEqual(review.added_lines("@@ -0,0 +1 @@\n+++content"), {1})

    def test_source_separators_do_not_change_patch_line_numbers(self):
        for separator in ["\f", "\v", "\r", "\x85", "\u2028", "\u2029"]:
            patch_text = f"@@ -0,0 +1,2 @@\n+# comment{separator} padding\n+undefined_name\n"
            self.assertEqual(review.added_lines(patch_text), {1, 2})


class AnalyzerTests(unittest.TestCase):
    def test_timeout_removes_only_its_named_container_without_credentials(self):
        for image in ["", "sha256:" + "a" * 64]:
            with patch.dict(
                "os.environ", {"REVIEW_ANALYZER_IMAGE": image, "GITHUB_TOKEN": "synthetic"}
            ):
                with patch.object(
                    review.subprocess,
                    "run",
                    side_effect=[
                        review.subprocess.TimeoutExpired("analyzer", 120),
                        SimpleNamespace(returncode=0),
                    ],
                ) as run:
                    with self.assertRaisesRegex(review.ReviewError, "timed out"):
                        review.run_json("ruff", [], Path("/tmp"))
            first = run.call_args_list[0]
            self.assertNotIn("GITHUB_TOKEN", first.kwargs["env"])
            if image:
                command = first.args[0]
                name = command[command.index("--name") + 1]
                self.assertRegex(name, r"^pr-review-[0-9a-f]{16}$")
                self.assertEqual(run.call_args_list[1].args[0], ["docker", "rm", "--force", name])
                self.assertEqual(run.call_args_list[1].kwargs["env"], first.kwargs["env"])
                self.assertEqual(run.call_count, 2)
            else:
                self.assertEqual(run.call_count, 1)

    def test_filters_old_findings_and_anchors_multiline_security_issues(self):
        outputs = [
            [
                {
                    "filename": "/tmp/0.py",
                    "location": {"row": 2},
                    "code": "F821",
                    "message": "Undefined name",
                },
                {
                    "filename": "/tmp/0.py",
                    "location": {"row": 1},
                    "code": "F821",
                    "message": "Existing issue",
                },
            ],
            {
                "errors": [],
                "results": [
                    {
                        "filename": "/tmp/0.py",
                        "line_number": 1,
                        "line_range": [1, 2],
                        "test_id": "B602",
                        "issue_severity": "HIGH",
                        "issue_text": "Shell injection",
                    },
                    {
                        "filename": "/tmp/0.py",
                        "line_number": 5,
                        "test_id": "B301",
                        "issue_severity": "MEDIUM",
                        "issue_text": "Existing issue",
                    },
                ],
            },
        ]
        with patch.object(review, "run_json", side_effect=outputs):
            findings = review.analyze(Path("/tmp"), {"0.py": ("builder/data.py", {2})})
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(f[0:2] == ("builder/data.py", 2) for f in findings))
        self.assertTrue(any("B602" in f[2] for f in findings))

    def test_parse_failure_is_not_clean(self):
        with patch.object(
            review,
            "run_json",
            side_effect=[
                [],
                {"errors": [{"reason": "syntax error"}], "results": []},
            ],
        ):
            with self.assertRaises(review.ReviewError):
                review.analyze(Path("/tmp"), {})

    def test_analyzer_receives_no_token_or_repo_config(self):
        with patch.dict(
            "os.environ",
            {
                "GITHUB_TOKEN": "not-a-real-token",
                "GH_TOKEN": "also-not-real",
                "PYTHONPATH": "/untrusted",
                "REVIEW_ANALYZER_PYTHON": "/trusted/bin/python",
                "REVIEW_ANALYZER_IMAGE": "",
            },
        ):
            with patch.object(
                review.subprocess,
                "run",
                return_value=SimpleNamespace(
                    returncode=0,
                    stdout="[]",
                ),
            ) as run:
                self.assertEqual(review.run_json("ruff", ["check"], Path("/tmp")), [])
        self.assertNotIn("GITHUB_TOKEN", run.call_args.kwargs["env"])
        self.assertNotIn("GH_TOKEN", run.call_args.kwargs["env"])
        self.assertNotIn("PYTHONPATH", run.call_args.kwargs["env"])
        self.assertEqual(run.call_args.args[0][:4], ["/trusted/bin/python", "-I", "-m", "ruff"])
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertFalse(run.call_args.kwargs.get("shell", False))
        self.assertEqual(run.call_args.kwargs["cwd"], Path("/tmp"))

    def test_container_uses_immutable_image_without_host_access_or_credentials(self):
        image = "sha256:" + "a" * 64
        with patch.dict(
            "os.environ", {"REVIEW_ANALYZER_IMAGE": image, "GITHUB_TOKEN": "synthetic"}
        ):
            command = review.analyzer_command("ruff", ["check", "/tmp/source"], Path("/tmp/source"))
        for flag in [
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            "--memory=1g",
        ]:
            self.assertIn(flag, command)
        self.assertIn("type=bind,source=/tmp/source,target=/scan,readonly", command)
        self.assertEqual(command[-6:], ["python", "-I", "-m", "ruff", "check", "/scan"])
        self.assertEqual(command.count("--mount"), 1)
        self.assertNotIn("--pid=host", command)
        self.assertNotIn("--privileged", command)
        self.assertNotIn("synthetic", command)
        for invalid in ["python:latest", "sha256:bad", "--privileged"]:
            with patch.dict("os.environ", {"REVIEW_ANALYZER_IMAGE": invalid}):
                with self.assertRaises(review.ReviewError):
                    review.analyzer_command("ruff", [], Path("/tmp"))

    def test_credentialed_cli_rejects_noncontainer_fallback(self):
        with (
            patch.dict("os.environ", {"REVIEW_ANALYZER_IMAGE": ""}),
            patch.object(review, "GitHub") as github,
        ):
            with patch("builtins.print"), self.assertRaises(SystemExit) as error:
                review.main()
        self.assertEqual(error.exception.code, 1)
        github.assert_not_called()

    def test_tool_failure_and_invalid_json_are_not_clean(self):
        for code, output in [(2, "[]"), (0, "not JSON")]:
            with self.subTest(code=code):
                with patch.object(
                    review.subprocess,
                    "run",
                    return_value=SimpleNamespace(
                        returncode=code,
                        stdout=output,
                    ),
                ):
                    with self.assertRaises(review.ReviewError):
                        review.run_json("ruff", [], Path("/tmp"))


class BlobTests(unittest.TestCase):
    def test_total_byte_limit_and_exact_boundary(self):
        content = b"x\n"
        api = Mock()
        api.request.return_value = {"size": 2, "encoding": "base64", "content": "eAo="}
        file = {
            "filename": "x.py",
            "status": "added",
            "sha": SHA,
            "patch": "@@ -0,0 +1 @@\n+x",
            "additions": 1,
        }
        with (
            patch.object(review, "MAX_FILE_BYTES", len(content)),
            patch.object(review, "MAX_TOTAL_BYTES", 4),
        ):
            with patch.object(review, "analyze", return_value=[]):
                self.assertEqual(review.scan([file, file], api), ([], 2))
                with self.assertRaises(review.ReviewError):
                    review.scan([file, file, file], api)

    def test_invalid_base64_and_mismatched_size_cannot_be_clean(self):
        file = {
            "filename": "x.py",
            "status": "added",
            "sha": SHA,
            "patch": "@@ -0,0 +1 @@\n+x",
            "additions": 1,
        }
        for encoded, size in [("!!!!", 0), ("eAo=", 3), ("eAo=" * 20, 2)]:
            api = Mock()
            api.request.return_value = {"size": size, "encoding": "base64", "content": encoded}
            with self.subTest(encoded=encoded):
                with (
                    self.assertRaises((ValueError, review.ReviewError)),
                    patch.object(review, "analyze") as analyze,
                ):
                    review.scan([file], api)
                analyze.assert_not_called()

    def test_untrusted_path_is_never_used_on_disk(self):
        content = b"print('data, not executed')\n"
        api = Mock()
        api.request.return_value = {
            "size": len(content),
            "encoding": "base64",
            "content": base64.b64encode(content).decode(),
        }
        files = [
            {
                "filename": "../../escape.py",
                "status": "added",
                "additions": 1,
                "sha": SHA,
                "patch": "@@ -0,0 +1 @@\n+print('data, not executed')",
            }
        ]

        def analyze(directory, sources):
            self.assertEqual([p.name for p in directory.iterdir()], ["0.py"])
            self.assertEqual((directory / "0.py").read_bytes(), content)
            self.assertEqual(sources["0.py"], ("../../escape.py", {1}))
            return []

        with patch.object(review, "analyze", side_effect=analyze):
            self.assertEqual(review.scan(files, api), ([], 1))
        api.request.assert_called_once_with(f"git/blobs/{SHA}")

    def test_missing_patch_and_file_limit_fail_closed(self):
        file = {"filename": "data.py", "status": "modified", "sha": SHA, "additions": 1}
        for files in [[file], [file] * (review.MAX_FILES + 1)]:
            with self.assertRaises(review.ReviewError):
                review.scan(files, Mock())

    def test_blob_size_limit_fails_closed(self):
        api = Mock()
        api.request.return_value = {
            "size": review.MAX_FILE_BYTES + 1,
            "encoding": "base64",
        }
        file = {"filename": "data.py", "status": "added", "sha": SHA, "patch": "", "additions": 0}
        with self.assertRaises(review.ReviewError):
            review.scan([file], api)

    def test_deletions_and_non_python_do_not_run_tools(self):
        files = [
            {"filename": "old.py", "status": "removed"},
            {"filename": "README.md", "status": "modified"},
        ]
        api = Mock()
        self.assertEqual(review.scan(files, api), ([], 0))
        api.request.assert_not_called()

    def test_truncated_diff_fails_closed(self):
        file = {
            "filename": "data.py",
            "status": "added",
            "sha": SHA,
            "patch": "@@ -0,0 +1 @@\n+first",
            "additions": 2,
        }
        with self.assertRaises(review.ReviewError):
            review.scan([file], Mock())


class PublicationTests(unittest.TestCase):
    def test_serialized_rerun_does_not_scan_or_post_twice(self):
        published = []
        api = Mock()

        def request(path, payload=None):
            if payload is not None:
                published.append({"user": {"login": "github-actions[bot]"}, **payload})
                return {"id": 1}
            return PR

        def pages(path):
            return list(published) if path.endswith("/reviews") else [{"filename": "x.py"}]

        api.request.side_effect = request
        api.pages.side_effect = pages
        with patch.object(review, "scan", return_value=([], 1)) as scan:
            self.assertTrue(review.review(api, 42, SHA))
            self.assertFalse(review.review(api, 42, SHA))
            scan.assert_called_once()
        self.assertEqual(len(published), 1)

    def test_state_is_rechecked_after_publication_time_review_pagination(self):
        api = api_for()
        api.request.side_effect = [PR, {**PR, "draft": True}]
        with patch.object(review, "scan", return_value=([], 1)):
            self.assertFalse(review.review(api, 42, SHA))
        self.assertEqual(api.pages.call_count, 3)
        self.assertEqual(api.request.call_count, 2)

    def test_deleted_author_and_quoted_marker_do_not_prevent_review(self):
        api = api_for()
        marker = f"<!-- automated-python-review:{SHA}:{BASE} -->"
        api.pages.side_effect = [
            [
                {"user": None, "body": marker},
                {"user": {"login": "github-actions[bot]"}, "body": "quoted " + marker},
            ],
            [{"filename": "x.py"}],
            [],
        ]
        with patch.object(review, "scan", return_value=([], 1)):
            self.assertTrue(review.review(api, 42, SHA))

    def test_publication_api_failures_never_retry_or_claim_success(self):
        for phase in ["duplicate", "state", "post"]:
            api = api_for()
            if phase == "duplicate":
                api.pages.side_effect = [[], [{"filename": "x.py"}], review.ReviewError("API")]
            else:
                api.request.side_effect = (
                    [PR, review.ReviewError("API")]
                    if phase == "state"
                    else [PR, PR, review.ReviewError("422")]
                )
            with self.subTest(phase=phase), patch.object(review, "scan", return_value=([], 1)):
                with self.assertRaises(review.ReviewError):
                    review.review(api, 42, SHA)
            self.assertLessEqual(api.request.call_count, 3)

    def test_invalid_dispatch_values_never_call_api(self):
        for number, sha in [
            ("0", SHA),
            ("42\n", SHA),
            ("1e3", SHA),
            ("1" * 11, SHA),
            (42, SHA + "\n"),
        ]:
            api = Mock()
            with self.subTest(number=number), self.assertRaises(review.ReviewError):
                review.review(api, number, sha)
            api.request.assert_not_called()

    def test_worst_case_payloads_preserve_actual_inline_paths_and_byte_bounds(self):
        for value in ["`" * 4000, "&" * 4000, "😀" * 4000, "\u202e" * 4000]:
            findings = [(value + ".py", line, value, value) for line in range(1, 51)]
            payload = review.review_payload(SHA, "marker", findings, 1, 1)
            self.assertLessEqual(len(payload["body"].encode()), review.MAX_BODY_BYTES)
            self.assertEqual(payload["comments"][0]["path"], value + ".py")
            self.assertEqual(payload["comments"][-1]["line"], 50)
            json.dumps(payload).encode("utf-8")

    def test_publication_time_duplicate_blocks_post_after_scan(self):
        api = api_for()
        marker = f"<!-- automated-python-review:{SHA}:{BASE} -->"
        api.pages.side_effect = [
            [],
            [{"filename": "fixture.py"}],
            [
                {"user": {"login": "github-actions[bot]"}, "body": marker + "\nreview"},
            ],
        ]
        with patch.object(review, "scan", return_value=([], 1)):
            self.assertFalse(review.review(api, 42, SHA))
        self.assertEqual(api.request.call_count, 1)

    def test_untrusted_markdown_is_encoded_not_active(self):
        corpus = [
            "docs/[click](https://evil.test)/x.py",
            "![image](https://evil.test)",
            "`code` **bold** _italic_",
            "https://evil.test www.evil.test someone@evil.test",
            "@someone #123",
            "</code><img src=x> &lt;tag&gt;",
            "line\n# forged heading",
            "\\[escaped] | table",
        ]
        for value in corpus:
            with self.subTest(value=value):
                encoded = review.safe_text(value)
                self.assertNotIn("[", encoded)
                self.assertNotIn("`", encoded)
                self.assertNotIn("@", encoded)
                self.assertNotIn("\n", encoded)
                expected = value.replace("\n", "\\u000a")
                self.assertEqual(
                    html.unescape(encoded.removeprefix("<code>").removesuffix("</code>")), expected
                )

    def test_truncation_never_slices_entities_or_unicode(self):
        for value in ["&" * 100, "<" * 100, "😀" * 100, "\u202e" * 100]:
            for limit in range(24, 45):
                with self.subTest(value=value[:1], limit=limit):
                    rendered = review.safe_text(value, limit)
                    self.assertLessEqual(len(rendered.encode("utf-8")), limit)
                    inner = rendered.removeprefix("<code>").removesuffix("</code>")
                    self.assertNotRegex(inner, r"&[^;]*$")
                    self.assertNotRegex(html.unescape(inner), r"\\u[0-9a-f]{0,3}…$")

    def test_posts_review_bound_to_commit_with_inline_findings(self):
        api = api_for()
        findings = [("builder/data.py", 2, "Ruff F821", "Undefined name")]
        with patch.object(review, "scan", return_value=(findings, 1)):
            self.assertTrue(review.review(api, 42, SHA))
        path, payload = api.request.call_args.args
        self.assertEqual(path, "pulls/42/reviews")
        self.assertEqual(payload["commit_id"], SHA)
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(payload["comments"][0]["line"], 2)
        self.assertEqual(payload["comments"][0]["side"], "RIGHT")
        self.assertIn("Ruff F821", payload["body"])
        self.assertIn("not an approval", payload["body"])

    def test_fork_blobs_use_the_authorized_base_client(self):
        api = api_for(
            {
                **PR,
                "head": {
                    "sha": SHA,
                    "repo": {"full_name": "contributor/private-fork"},
                },
            }
        )
        with patch.object(review, "scan", return_value=([], 1)) as scan:
            self.assertTrue(review.review(api, 42, SHA))
        self.assertIs(scan.call_args.args[1], api)

    def test_skips_drafts_closed_and_stale_events(self):
        for change in [
            {"draft": True},
            {"state": "closed"},
            {"head": {**PR["head"], "sha": "c" * 40}},
        ]:
            api = api_for({**PR, **change})
            self.assertFalse(review.review(api, 42, SHA))
            api.pages.assert_not_called()

    def test_deduplicates_only_our_bot_review(self):
        marker = f"<!-- automated-python-review:{SHA}:{BASE} -->"
        for author, expected in [("github-actions[bot]", False), ("contributor", True)]:
            api = api_for()
            api.pages.side_effect = [
                [{"user": {"login": author}, "body": marker}],
                [{"filename": "builder/data.py"}],
                [],
            ]
            with patch.object(review, "scan", return_value=([], 1)):
                self.assertEqual(review.review(api, 42, SHA), expected)

    def test_does_not_publish_if_head_or_base_changes_during_scan(self):
        for updated in [
            {**PR, "head": {**PR["head"], "sha": "c" * 40}},
            {**PR, "base": {"sha": "d" * 40}},
            {**PR, "state": "closed"},
        ]:
            api = api_for()
            api.request.side_effect = [PR, updated]
            with patch.object(review, "scan", return_value=([], 1)):
                self.assertFalse(review.review(api, 42, SHA))
            self.assertEqual(api.request.call_count, 2)

    def test_incomplete_file_list_never_posts(self):
        api = api_for({**PR, "changed_files": 2})
        with self.assertRaises(review.ReviewError):
            review.review(api, 42, SHA)
        self.assertEqual(api.request.call_count, 1)

    def test_scan_failure_never_posts(self):
        api = api_for()
        with patch.object(review, "scan", side_effect=review.ReviewError("tool failure")):
            with self.assertRaises(review.ReviewError):
                review.review(api, 42, SHA)
        self.assertEqual(api.request.call_count, 1)

    def test_comment_cap_and_safe_untrusted_text(self):
        findings = [
            ("builder/<data>.py", line, "Ruff F821", "Undefined @someone <tag>")
            for line in range(1, 53)
        ]
        payload = review.review_payload(SHA, "marker", findings, 1, 1)
        self.assertEqual(len(payload["comments"]), 50)
        self.assertIn("Only the first 50", payload["body"])
        self.assertNotIn("@someone", payload["body"])
        self.assertNotIn("<tag>", payload["body"])
        self.assertIn("<tag>", html.unescape(payload["body"]))

    def test_non_python_coverage_is_explicit(self):
        payload = review.review_payload(SHA, "marker", [], 0, 3)
        self.assertIn("Non-Python changes were not assessed", payload["body"])
        self.assertEqual(payload["comments"], [])

    def test_oversized_diagnostic_text_is_bounded(self):
        findings = [("x" * 4000 + ".py", line, "Ruff F821", "&" * 10000) for line in range(1, 51)]
        payload = review.review_payload(SHA, "marker", findings, 1, 1)
        self.assertLess(len(payload["body"]), 65536)
        self.assertTrue(all(len(c["body"]) < 65536 for c in payload["comments"]))


class WorkflowTests(unittest.TestCase):
    def test_privileged_workflow_remains_held_trusted_and_serialized(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/pr-review.yml").read_text()
        for required in [
            "workflow_dispatch:",
            "false && github.ref == 'refs/heads/main'",
            "group: pr-review-${{ github.repository }}-${{ inputs.pr_number }}",
            "cancel-in-progress: false",
            "ref: ${{ github.sha }}",
            "persist-credentials: false",
            "python -I -S scripts/review_pr.py",
            "docker build --file config/review-analyzers.Dockerfile --iidfile",
            "contents: read",
            "pull-requests: write",
            "PR_NUMBER: ${{ inputs.pr_number }}",
            "EXPECTED_HEAD_SHA: ${{ inputs.expected_head_sha }}",
        ]:
            self.assertIn(required, workflow)
        for forbidden in [
            "pull_request_target:",
            "pull_request:",
            "schedule:",
            "continue-on-error",
            "make setup",
            "pip install -e",
            "head.sha",
        ]:
            self.assertNotIn(forbidden, workflow)
        for line in workflow.split("\n"):
            if "uses:" in line:
                self.assertRegex(line, r"@[0-9a-f]{40}(?: |$)")
            if "run:" in line:
                self.assertNotIn("${{ inputs.", line)
            if "${{ inputs." in line:
                self.assertTrue(
                    line.strip().startswith(("group:", "PR_NUMBER:", "EXPECTED_HEAD_SHA:"))
                )
        self.assertIn("    if: ${{ false && github.ref == 'refs/heads/main' }}\n", workflow)
        self.assertEqual(workflow.count("runs-on:"), 1)
        dockerfile = (root / "config/review-analyzers.Dockerfile").read_text()
        self.assertIn("--only-binary=:all:", dockerfile)
        self.assertNotIn("COPY .", dockerfile)
        self.assertEqual(
            (root / "requirements-review.txt").read_text().splitlines()[1:],
            ["ruff==0.14.3", "bandit==1.8.6"],
        )


if __name__ == "__main__":
    unittest.main()
