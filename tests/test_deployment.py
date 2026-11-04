"""Deployment evidence must reflect real, verified shipping, not daily checks."""
import contextlib
import copy
import datetime as dt
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import record_deployment as deploy

SHA = "a" * 40
PROVIDER = {"context": "Vercel", "state": "success",
            "target_url": "https://vercel.com/team/unpoliticalaf/deployment-id",
            "created_at": "2026-11-04T12:00:00Z"}
RUN = "https://github.com/jnyross/unpoliticalaf/actions/runs/123"


def deployment(identifier=1, sha=SHA, when=PROVIDER["created_at"]):
    return {"id": identifier, "sha": sha, "environment": "production", "task": "deploy",
            "payload": {"source": deploy.SOURCE, "deployed_at": when,
                        "provider_url": PROVIDER["target_url"], "recording_run": RUN}}


class GitHubClient(unittest.TestCase):
    @mock.patch.object(deploy.subprocess, "run")
    def test_post_preserves_boolean_and_list_types(self, run):
        run.return_value.stdout = '{"id": 1}'
        payload = {"auto_merge": False, "required_contexts": []}
        api = deploy.GitHub("owner/repo")
        self.assertEqual(api.request("deployments", payload), {"id": 1})
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["gh", "api", "--method", "POST",
                                  "repos/owner/repo/deployments", "--input", "-"])
        self.assertEqual(json.loads(kwargs["input"]), payload)
        self.assertTrue(kwargs["check"])

    def test_pagination_with_existing_query(self):
        api = deploy.GitHub("owner/repo")
        api.request = mock.Mock(side_effect=[list(range(100)), [100]])
        self.assertEqual(list(api.pages("deployments?sha=abc")), list(range(101)))
        self.assertEqual(api.request.call_args_list,
                         [mock.call("deployments?sha=abc&per_page=100&page=1"),
                          mock.call("deployments?sha=abc&per_page=100&page=2")])

    @mock.patch.object(deploy.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "gh"))
    def test_api_failures_propagate(self, run):
        with self.assertRaises(subprocess.CalledProcessError):
            deploy.GitHub("owner/repo").request("deployments")


class ProviderEvidence(unittest.TestCase):
    def api(self, *statuses):
        api = mock.Mock()
        api.request.side_effect = [{"sha": SHA, "statuses": s} for s in statuses]
        return api

    def test_provider_success_is_required_for_the_exact_sha(self):
        api = self.api([PROVIDER])
        self.assertEqual(deploy.vercel_success(api, SHA, 0), PROVIDER)
        api.request.assert_called_once_with(f"commits/{SHA}/status")

    def test_missing_pending_failed_or_other_context_does_not_pass(self):
        for status in (None, {**PROVIDER, "state": "pending"},
                       {**PROVIDER, "state": "failure"}, {**PROVIDER, "state": "error"},
                       {**PROVIDER, "context": "Build and check"}):
            with self.subTest(status=status), self.assertRaises(ValueError):
                deploy.vercel_success(self.api([status] if status else []), SHA, 0)

    @mock.patch.object(deploy.time, "sleep")
    def test_pending_waits_for_provider_success(self, sleep):
        api = self.api([{**PROVIDER, "state": "pending"}], [PROVIDER])
        self.assertEqual(deploy.vercel_success(api, SHA, 30), PROVIDER)
        sleep.assert_called_once()

    def test_wrong_commit_or_missing_provider_link_is_rejected(self):
        api = mock.Mock()
        api.request.return_value = {"sha": "b" * 40, "statuses": [PROVIDER]}
        with self.assertRaises(ValueError):
            deploy.vercel_success(api, SHA, 0)
        for url in ("", "http://vercel.com/team/id", "https://vercel.com.evil.test/id"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                deploy.vercel_success(self.api([{**PROVIDER, "target_url": url}]), SHA, 0)

    def test_invalid_or_naive_provider_timestamp_is_rejected(self):
        for when in (None, "", "not-a-date", "2026-11-04T12:00:00"):
            with self.subTest(when=when), self.assertRaises(ValueError):
                deploy.vercel_success(self.api([{**PROVIDER, "created_at": when}]), SHA, 0)


class Recording(unittest.TestCase):
    def test_records_provider_evidence_and_success(self):
        api = mock.Mock()
        api.pages.return_value = []
        api.request.return_value = {"id": 42}
        self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN), (42, True))
        create, status = api.request.call_args_list
        path, payload = create.args
        self.assertEqual(path, "deployments")
        self.assertEqual(payload["ref"], SHA)
        self.assertTrue(payload["production_environment"])
        self.assertFalse(payload["auto_merge"])
        self.assertEqual(payload["payload"]["provider_url"], PROVIDER["target_url"])
        self.assertEqual(payload["payload"]["deployed_at"], PROVIDER["created_at"])
        self.assertEqual(payload["payload"]["recording_run"], RUN)
        self.assertEqual(status.args[0], "deployments/42/statuses")
        self.assertEqual(status.args[1]["state"], "success")
        self.assertEqual(status.args[1]["environment_url"], deploy.check_live.DEFAULT_URL)

    def test_daily_check_does_not_duplicate_even_an_inactive_deployment(self):
        api = mock.Mock()
        api.pages.side_effect = [[deployment()], [{"state": "inactive"}, {"state": "success"}]]
        self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN), (1, False))
        api.request.assert_not_called()

    def test_interrupted_record_is_reused_only_after_new_verification(self):
        api = mock.Mock()
        api.pages.side_effect = [[deployment()], []]
        new_run = RUN + "4"
        self.assertEqual(deploy.record(api, SHA, PROVIDER, new_run), (1, True))
        self.assertEqual(api.request.call_count, 1)
        self.assertEqual(api.request.call_args.args[0], "deployments/1/statuses")
        self.assertEqual(api.request.call_args.args[1]["log_url"], new_run)


class WorkflowGates(unittest.TestCase):
    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        enter = stack.enter_context
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "site").mkdir()
        (root / "site/build.json").write_text(json.dumps({"commit": SHA, "files": {}}))
        enter(mock.patch.object(deploy.check_live, "ROOT", root))
        enter(mock.patch.dict(os.environ, {
            "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": SHA,
            "GITHUB_REPOSITORY": "jnyross/unpoliticalaf", "GITHUB_RUN_ID": "123",
        }))
        self.api = enter(mock.patch.object(deploy, "GitHub")).return_value
        self.provider = enter(mock.patch.object(deploy, "vercel_success", return_value=PROVIDER))
        self.live = enter(mock.patch.object(deploy.check_live, "main", return_value=0))
        self.record = enter(mock.patch.object(deploy, "record", return_value=(1, True)))
        self.report = enter(mock.patch.object(deploy, "frequency_report", return_value=[]))
        enter(mock.patch.object(deploy.check_live, "summary"))
        enter(contextlib.redirect_stdout(io.StringIO()))

    def test_feature_branch_dispatch_is_refused_before_provider_or_writes(self):
        with mock.patch.dict(os.environ, {"GITHUB_REF": "refs/heads/feature"}):
            with self.assertRaises(ValueError):
                deploy.main([])
        self.provider.assert_not_called()
        self.record.assert_not_called()

    def test_wrong_local_build_is_refused(self):
        with mock.patch.dict(os.environ, {"GITHUB_SHA": "b" * 40}):
            with self.assertRaises(ValueError):
                deploy.main([])
        self.provider.assert_not_called()
        self.record.assert_not_called()

    def test_failed_provider_never_checks_live_or_records(self):
        self.provider.side_effect = ValueError("failed deployment")
        with self.assertRaises(ValueError):
            deploy.main([])
        self.live.assert_not_called()
        self.record.assert_not_called()

    def test_failed_live_check_never_records(self):
        self.live.return_value = 1
        self.assertEqual(deploy.main([]), 1)
        self.record.assert_not_called()

    def test_success_passes_exact_evidence_to_recorder(self):
        self.assertEqual(deploy.main([]), 0)
        self.provider.assert_called_once_with(self.api, SHA, 0)
        self.live.assert_called_once()
        self.record.assert_called_once_with(self.api, SHA, PROVIDER, RUN)

    def test_report_is_read_only_and_works_outside_a_workflow(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(deploy.main(["--report"]), 0)
        self.provider.assert_not_called()
        self.live.assert_not_called()
        self.record.assert_not_called()
        self.report.assert_called_once()


class Frequency(unittest.TestCase):
    def test_counts_real_successes_by_provider_time_not_recheck_time(self):
        now = dt.datetime(2026, 11, 5, 12, tzinfo=dt.timezone.utc)
        rows = [deployment(), deployment(2),  # duplicate SHA is not a second deploy
                deployment(3, "b" * 40),
                deployment(4, "c" * 40, "2026-10-29T12:00:00Z"),  # exact 7-day boundary
                deployment(5, "d" * 40, "2026-10-08T12:00:00Z"),  # too old
                deployment(6, "e" * 40, "2026-11-06T12:00:00Z"),  # future
                deployment(7, "f" * 40)]  # incomplete record
        foreign = copy.deepcopy(deployment(8))
        foreign["payload"]["source"] = "another-tool"
        preview = copy.deepcopy(deployment(9))
        preview["environment"] = "preview"
        rows += [foreign, preview]
        api = mock.Mock()

        def pages(path):
            if path.startswith("deployments?"):
                return rows
            if path == "deployments/7/statuses":
                return [{"state": "failure"}]
            return [{"state": "inactive"}, {"state": "success"}]

        api.pages.side_effect = pages
        report = "\n".join(deploy.frequency_report(api, now))
        self.assertIn("| 0–7 | 2 |", report)
        self.assertIn("| 7–14 | 1 |", report)
        self.assertIn("| 14–21 | 0 |", report)
        self.assertIn("| 21–28 | 0 |", report)
        api.request.assert_not_called()

    def test_empty_history_does_not_claim_frequency(self):
        api = mock.Mock()
        api.pages.return_value = []
        report = "\n".join(deploy.frequency_report(api))
        self.assertIn("| 0–7 | 0 |", report)
        self.assertIn("do not yet demonstrate", report)

    def test_malformed_timestamps_are_reported_not_counted(self):
        api = mock.Mock()
        rows = [deployment(i, when=value) for i, value in enumerate(
            (None, "", "not-a-date", "2026-11-04T12:00:00"))]
        rows[0]["payload"].pop("deployed_at")
        api.pages.return_value = rows
        report = "\n".join(deploy.frequency_report(api))
        self.assertIn("| 0–7 | 0 |", report)
        self.assertIn("excluded 4 record(s)", report)


if __name__ == "__main__":
    unittest.main()
