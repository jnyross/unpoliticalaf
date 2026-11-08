"""Synthetic API fixtures test the gate; they are not deployment evidence."""

import contextlib
import copy
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from builder import feature_flags
from scripts import release_evidence as evidence
from scripts import record_deployment as deploy

COMMIT = "a" * 40
RUN_ID = "123"
RUN_URL = f"https://github.com/{deploy.REPOSITORY}/actions/runs/{RUN_ID}"
ACTIONS_CREATOR = {"login": "github-actions[bot]", "id": 41898282, "type": "Bot"}


class ReleaseEvidence(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.site = Path(temporary.name) / "site"
        self.site.mkdir()
        body = b"<h1>Synthetic test fixture</h1>"
        (self.site / "index.html").write_bytes(body)
        self.build = {
            "commit": COMMIT,
            "feature_flags": dict(feature_flags.production({})),
            "files": {"index.html": hashlib.sha256(body).hexdigest()},
        }
        self.write_build()
        self.run = {
            "id": int(RUN_ID),
            "head_sha": COMMIT,
            "head_branch": "main",
            "head_repository": {"full_name": deploy.REPOSITORY},
            "repository": {"full_name": deploy.REPOSITORY},
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "path": ".github/workflows/deploy.yml",
            "html_url": RUN_URL,
        }
        self.receipt = {
            "id": 42,
            "sha": COMMIT,
            "environment": deploy.ENVIRONMENT,
            "task": "deploy",
            "creator": dict(ACTIONS_CREATOR),
            "payload": {
                "source": deploy.SOURCE,
                "provider_url": f"https://vercel.com{deploy.VERCEL_PROJECT_PATH}synthetic-fixture",
                "deployed_at": "2026-11-05T12:00:00Z",
                "recording_run": RUN_URL,
                "build_sha256": self.digest(),
            },
        }
        self.status = {
            "state": "success",
            "environment_url": deploy.check_live.DEFAULT_URL,
            "log_url": RUN_URL,
            "creator": dict(ACTIONS_CREATOR),
        }
        self.comparison = {"status": "behind"}
        self.receipts = [self.receipt]
        self.statuses = [self.status]
        # Exercise the actual bounded pagination client, replacing only transport.
        self.api = deploy.GitHub(deploy.REPOSITORY)
        self.transport = mock.Mock(side_effect=self.response)
        self.api.request = self.transport

    def write_build(self):
        (self.site / "build.json").write_text(json.dumps(self.build), encoding="utf-8")

    def digest(self):
        return hashlib.sha256((self.site / "build.json").read_bytes()).hexdigest()

    def response(self, path, *writes):
        self.assertFalse(writes, "The evidence gate must never write GitHub state")
        if path == f"actions/runs/{RUN_ID}":
            return self.run
        if path == f"compare/main...{COMMIT}":
            return self.comparison
        if path.startswith("deployments?"):
            self.assertIn(f"sha={COMMIT}", path)
            self.assertIn(f"environment={deploy.ENVIRONMENT}&", path)
            self.assertIn("task=deploy", path)
            return self.receipts
        if path == "deployments/42/statuses?per_page=100&page=1":
            return self.statuses
        self.fail(f"Unexpected API read: {path}")

    def verify(self):
        return evidence.verify(self.api, COMMIT, RUN_ID, self.site)

    def test_success_returns_receipt_id_without_mutating_local_or_remote_state(self):
        before = {p.name: p.read_bytes() for p in self.site.iterdir()}
        self.assertEqual(self.verify(), 42)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.site.iterdir()})
        self.assertEqual(self.transport.call_count, 4)

    def test_live_caller_and_manual_main_dispatch_are_supported(self):
        self.run.update(path=".github/workflows/live.yml", event="workflow_dispatch")
        self.comparison = {"status": "identical"}
        self.assertEqual(self.verify(), 42)

    def test_wrong_run_identity_or_unapproved_workflow_cannot_pass(self):
        for changes in (
            {"id": 124},
            {"id": True},
            {"head_sha": "b" * 40},
            {"head_branch": "feature"},
            {"status": "in_progress"},
            {"conclusion": "failure"},
            {"event": "pull_request"},
            {"event": "workflow_run"},
            {"event": "workflow_call"},
            {"path": ".github/workflows/test.yml"},
            {"path": ".github/workflows/deploy.yml@refs/heads/main"},
            {"head_repository": {"full_name": "other/repo"}},
            {"repository": {"full_name": "other/repo"}},
            {"html_url": RUN_URL + "/attempts/1"},
        ):
            original = copy.deepcopy(self.run)
            self.run.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.verify()
            self.run = original

    def test_only_main_ancestors_are_allowed(self):
        for comparison in (None, {}, {"status": "ahead"}, {"status": "diverged"}):
            self.comparison = comparison
            with self.subTest(comparison=comparison), self.assertRaises(ValueError):
                self.verify()

    def test_recovery_keeps_original_recording_run_but_requires_current_success(self):
        self.receipt["payload"]["recording_run"] = RUN_URL + "4"
        self.assertEqual(self.verify(), 42)
        self.status["log_url"] = RUN_URL + "4"
        with self.assertRaises(ValueError):
            self.verify()

    def test_missing_malformed_or_wrong_receipts_fail_closed(self):
        original = copy.deepcopy(self.receipt)
        invalid = [
            None,
            {},
            {**original, "sha": "b" * 40},
            {**original, "environment": "preview"},
            {**original, "id": "../bad"},
            {**original, "task": "other"},
        ]
        for changes in (
            {"source": "other"},
            {"build_sha256": "f" * 64},
            {"recording_run": "https://evil.test/run"},
            {"provider_url": "https://evil.test/deployment"},
            {"deployed_at": "2026-11-05T12:00:00"},
            {"deployed_at": None},
        ):
            invalid.append({**original, "payload": {**original["payload"], **changes}})
        for row in invalid:
            self.receipts = [row]
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.verify()
        self.receipts = []
        with self.assertRaises(ValueError):
            self.verify()

    def test_only_exact_success_link_and_production_url_pass(self):
        original = dict(self.status)
        for status in (
            None,
            {},
            {**original, "state": "pending"},
            {**original, "environment_url": "https://preview.example/"},
            {**original, "log_url": RUN_URL + "4"},
            {**original, "log_url": RUN_URL + "?spoof=1"},
        ):
            self.statuses = [status]
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.verify()
        self.statuses = []
        with self.assertRaises(ValueError):
            self.verify()

    def test_historical_success_remains_valid_after_inactive_status(self):
        self.statuses = [{"state": "inactive"}, self.status]
        self.assertEqual(self.verify(), 42)

    def test_receipt_and_success_status_require_verified_actions_bot(self):
        for target in (self.receipt, self.status):
            for creator in (
                None,
                {},
                {**ACTIONS_CREATOR, "login": "someone"},
                {**ACTIONS_CREATOR, "id": 1},
                {**ACTIONS_CREATOR, "id": "41898282"},
                {**ACTIONS_CREATOR, "type": "User"},
            ):
                target["creator"] = creator
                with self.subTest(target=target, creator=creator), self.assertRaises(ValueError):
                    self.verify()
            target["creator"] = dict(ACTIONS_CREATOR)
        self.assertEqual(self.verify(), 42)

    def test_receipt_provider_must_be_the_approved_project(self):
        self.receipt["payload"]["provider_url"] = "https://vercel.com/other/project/deployment"
        with self.assertRaises(ValueError):
            self.verify()

    def test_raw_build_bytes_not_equivalent_json_must_match_receipt(self):
        (self.site / "build.json").write_text(json.dumps(self.build, indent=2))
        with self.assertRaises(ValueError):
            self.verify()

    def test_full_local_site_is_validated_before_api_reads(self):
        (self.site / "index.html").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.verify()
        self.transport.assert_not_called()

    def test_wrong_commit_flags_extra_files_and_duplicate_manifest_keys_fail(self):
        changed_flags = {name: not value for name, value in self.build["feature_flags"].items()}
        for change in (
            {"commit": "b" * 40},
            {"feature_flags": {}},
            {"feature_flags": changed_flags},
        ):
            original = copy.deepcopy(self.build)
            self.build.update(change)
            self.write_build()
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.verify()
            self.build = original
        self.write_build()
        extra = self.site / "extra.txt"
        extra.write_text("unlisted")
        with self.assertRaises(ValueError):
            self.verify()
        extra.unlink()
        manifest = self.site / "build.json"
        manifest.write_text('{"commit":"' + COMMIT + '",' + manifest.read_text()[1:])
        with self.assertRaises(ValueError):
            self.verify()

    def test_bad_commit_and_run_id_are_rejected_before_reads(self):
        for commit, run_id in (
            ("short", RUN_ID),
            (COMMIT, "../123"),
            (COMMIT, "0"),
            (COMMIT, "123\n"),
            (COMMIT, "1" * 21),
        ):
            with self.subTest(commit=commit, run_id=run_id), self.assertRaises(ValueError):
                evidence.verify(self.api, commit, run_id, self.site)
        self.transport.assert_not_called()

    def test_cli_uses_restricted_client_and_does_not_echo_api_error_or_token(self):
        with mock.patch.object(evidence.deploy, "GitHub", return_value=self.api):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    evidence.main(
                        ["--commit", COMMIT, "--run-id", RUN_ID, "--site", str(self.site)]
                    ),
                    0,
                )
            self.transport.side_effect = subprocess.CalledProcessError(
                1, "gh", stderr="secret-token"
            )
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(
                    evidence.main(
                        ["--commit", COMMIT, "--run-id", RUN_ID, "--site", str(self.site)]
                    ),
                    1,
                )
            self.assertNotIn("secret-token", output.getvalue())


if __name__ == "__main__":
    unittest.main()
