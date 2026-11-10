"""Deployment evidence must reflect real, verified shipping, not daily checks."""

import contextlib
import copy
import datetime as dt
import hashlib
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
VERCEL_CREATOR = {"login": "vercel[bot]", "id": 35613825, "type": "Bot"}
ACTIONS_CREATOR = {"login": "github-actions[bot]", "id": 41898282, "type": "Bot"}
PROVIDER = {
    "context": "Vercel",
    "state": "success",
    "target_url": "https://vercel.com/johns-projects-d6b53aae/unpoliticalaf/deployment-id",
    "creator": VERCEL_CREATOR,
    "created_at": "2026-11-04T12:00:00Z",
}
RUN = "https://github.com/jnyross/unpoliticalaf/actions/runs/123"
DIGEST = "f" * 64


class ReceiptRegressions(unittest.TestCase):
    def test_recovery_never_relabels_a_different_provider_deployment(self):
        api = mock.Mock()
        old = deployment()
        api.pages.side_effect = [[old], []]
        api.request.return_value = {"id": 42}
        provider = {
            **PROVIDER,
            "target_url": PROVIDER["target_url"] + "-new",
            "created_at": "2026-11-05T12:00:00Z",
        }
        self.assertEqual(deploy.record(api, SHA, provider, RUN, DIGEST), (42, True))
        self.assertEqual(api.request.call_args_list[0].args[0], "deployments")
        payload = api.request.call_args_list[0].args[1]["payload"]
        self.assertEqual(payload["provider_url"], provider["target_url"])
        self.assertEqual(payload["deployed_at"], provider["created_at"])
        self.assertEqual(payload["build_sha256"], DIGEST)

    def test_payload_marker_does_not_make_malformed_rows_trusted(self):
        api = mock.Mock()
        rows = [
            None,
            [],
            {},
            {"payload": {"source": deploy.SOURCE}},
            {**deployment(), "id": "../bad"},
            {**deployment(), "sha": "not-a-sha"},
            {**deployment(), "payload": {"source": deploy.SOURCE}},
            {
                **deployment(),
                "payload": {**deployment()["payload"], "provider_url": "https://[invalid/"},
            },
        ]
        api.pages.return_value = rows
        report = "\n".join(deploy.frequency_report(api))
        self.assertIn("| 0–7 | 0 |", report)
        api.request.assert_not_called()

    def test_api_rejects_foreign_repository_and_arbitrary_endpoint(self):
        with self.assertRaises(ValueError):
            deploy.GitHub("attacker/project")
        api = deploy.GitHub("jnyross/unpoliticalaf")
        for path in ("https://evil.test/", "//evil.test/", "../secrets", "deployments/../keys"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                api.request(path)

    def test_pagination_fails_closed_instead_of_reporting_partial_history(self):
        api = deploy.GitHub("jnyross/unpoliticalaf")
        api.request = mock.Mock(return_value=[{}] * 100)
        with mock.patch.object(deploy, "MAX_PAGES", 2), self.assertRaises(ValueError):
            list(api.pages("deployments"))
        self.assertEqual(api.request.call_count, 2)

    def test_provider_rejects_url_credentials_ports_and_fragments(self):
        for url in (
            "https://user@vercel.com/team/id",
            "https://vercel.com:444/team/id",
            "https://vercel.com/team/id#fake",
        ):
            api = mock.Mock()
            api.request.return_value = {"sha": SHA, "statuses": [{**PROVIDER, "target_url": url}]}
            api.pages.return_value = [{**PROVIDER, "target_url": url}]
            with self.subTest(url=url), self.assertRaises(ValueError):
                deploy.vercel_success(api, SHA, 0)


def deployment(identifier=1, sha=SHA, when=PROVIDER["created_at"]):
    return {
        "id": identifier,
        "sha": sha,
        "environment": deploy.ENVIRONMENT,
        "task": "deploy",
        "creator": ACTIONS_CREATOR,
        "payload": {
            "source": deploy.SOURCE,
            "deployed_at": when,
            "provider_url": PROVIDER["target_url"],
            "recording_run": RUN,
            "build_sha256": DIGEST,
        },
    }


def success_status(run_url=RUN):
    return {
        "state": "success",
        "environment_url": deploy.check_live.DEFAULT_URL,
        "log_url": run_url,
        "creator": ACTIONS_CREATOR,
    }


def workflow_run(identifier=123):
    return {
        "id": identifier,
        "head_sha": SHA,
        "head_branch": "main",
        "repository": {"full_name": "jnyross/unpoliticalaf"},
        "head_repository": {"full_name": "jnyross/unpoliticalaf"},
        "path": ".github/workflows/deploy.yml",
        "status": "completed",
        "conclusion": "success",
        "event": "push",
    }


class GitHubClient(unittest.TestCase):
    @mock.patch.object(deploy.subprocess, "run")
    def test_post_preserves_boolean_and_list_types(self, run):
        run.return_value.stdout = '{"id": 1}'
        payload = {"auto_merge": False, "required_contexts": []}
        api = deploy.GitHub("jnyross/unpoliticalaf")
        self.assertEqual(api.request("deployments", payload), {"id": 1})
        args, kwargs = run.call_args
        self.assertEqual(
            args[0],
            [
                "gh",
                "api",
                "--hostname",
                "github.com",
                "--method",
                "POST",
                "repos/jnyross/unpoliticalaf/deployments",
                "--input",
                "-",
            ],
        )
        self.assertEqual(json.loads(kwargs["input"]), payload)
        self.assertTrue(kwargs["check"])

    def test_pagination_with_existing_query(self):
        api = deploy.GitHub("jnyross/unpoliticalaf")
        api.request = mock.Mock(side_effect=[list(range(100)), [100]])
        self.assertEqual(list(api.pages("deployments?sha=abc")), list(range(101)))
        self.assertEqual(
            api.request.call_args_list,
            [
                mock.call("deployments?sha=abc&per_page=100&page=1"),
                mock.call("deployments?sha=abc&per_page=100&page=2"),
            ],
        )

    @mock.patch.object(deploy.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "gh"))
    def test_api_failures_propagate(self, run):
        with self.assertRaises(subprocess.CalledProcessError):
            deploy.GitHub("jnyross/unpoliticalaf").request("deployments")

    @mock.patch.object(deploy.subprocess, "run")
    def test_api_pins_host_and_does_not_pass_debug_or_foreign_host_settings(self, run):
        run.return_value.stdout = "[]"
        with mock.patch.dict(os.environ, {"GH_HOST": "evil.test", "GH_DEBUG": "api"}):
            deploy.GitHub("jnyross/unpoliticalaf").request("deployments")
        environment = run.call_args.kwargs["env"]
        self.assertNotIn("GH_HOST", environment)
        self.assertNotIn("GH_DEBUG", environment)
        self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_malformed_page_is_not_silently_accepted_as_history(self):
        api = deploy.GitHub("jnyross/unpoliticalaf")
        api.request = mock.Mock(return_value={"message": "not a page"})
        with self.assertRaises(ValueError):
            list(api.pages("deployments"))


class ProviderEvidence(unittest.TestCase):
    def api(self, *statuses):
        api = mock.Mock()
        api.request.side_effect = [{"sha": SHA, "statuses": s} for s in statuses]
        api.pages.side_effect = list(statuses)
        return api

    def test_provider_success_is_required_for_the_exact_sha(self):
        api = self.api([PROVIDER])
        self.assertEqual(deploy.vercel_success(api, SHA, 0), PROVIDER)
        api.request.assert_called_once_with(f"commits/{SHA}/status")

    def test_missing_pending_failed_or_other_context_does_not_pass(self):
        for status in (
            None,
            {**PROVIDER, "state": "pending"},
            {**PROVIDER, "state": "failure"},
            {**PROVIDER, "state": "error"},
            {**PROVIDER, "context": "Build and check"},
        ):
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

    def test_latest_pending_status_cannot_inherit_older_success(self):
        api = self.api([{**PROVIDER, "state": "pending"}, PROVIDER])
        with self.assertRaises(ValueError):
            deploy.vercel_success(api, SHA, 0)

    def test_provider_status_can_be_beyond_the_first_page(self):
        api = deploy.GitHub("jnyross/unpoliticalaf")
        api.request = mock.Mock(
            side_effect=[{"sha": SHA}, [{"context": "Another check"}] * 100, [PROVIDER]]
        )
        self.assertEqual(deploy.vercel_success(api, SHA, 0), PROVIDER)
        self.assertEqual(
            api.request.call_args_list[-1], mock.call(f"commits/{SHA}/statuses?per_page=100&page=2")
        )

    def test_spoofed_vercel_creator_or_other_project_is_rejected(self):
        for creator in (
            None,
            {},
            {**VERCEL_CREATOR, "login": "attacker"},
            {**VERCEL_CREATOR, "id": 1},
            {**VERCEL_CREATOR, "type": "User"},
        ):
            with self.subTest(creator=creator), self.assertRaises(ValueError):
                deploy.vercel_success(self.api([{**PROVIDER, "creator": creator}]), SHA, 0)
        for url in (
            "https://vercel.com/another-team/unpoliticalaf/deployment-id",
            "https://vercel.com/johns-projects-d6b53aae/other-project/deployment-id",
            "https://vercel.com/johns-projects-d6b53aae/unpoliticalaf/../other/id",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                deploy.vercel_success(self.api([{**PROVIDER, "target_url": url}]), SHA, 0)


class Recording(unittest.TestCase):
    def test_records_provider_evidence_and_success(self):
        api = mock.Mock()
        api.pages.return_value = []
        api.request.return_value = {"id": 42}
        self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN, DIGEST), (42, True))
        create, status = api.request.call_args_list
        path, payload = create.args
        self.assertEqual(path, "deployments")
        self.assertEqual(payload["ref"], SHA)
        self.assertEqual(payload["environment"], deploy.ENVIRONMENT)
        self.assertFalse(payload["production_environment"])
        self.assertFalse(payload["transient_environment"])
        self.assertFalse(payload["auto_merge"])
        self.assertEqual(payload["payload"]["provider_url"], PROVIDER["target_url"])
        self.assertEqual(payload["payload"]["deployed_at"], PROVIDER["created_at"])
        self.assertEqual(payload["payload"]["recording_run"], RUN)
        self.assertEqual(payload["payload"]["build_sha256"], DIGEST)
        self.assertEqual(status.args[0], "deployments/42/statuses")
        self.assertEqual(status.args[1]["state"], "success")
        self.assertEqual(status.args[1]["environment_url"], deploy.check_live.DEFAULT_URL)

    def test_daily_check_does_not_duplicate_even_an_inactive_deployment(self):
        api = mock.Mock()
        api.pages.side_effect = [[deployment()], [{"state": "inactive"}, success_status()]]
        self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN, DIGEST), (1, False))
        api.request.assert_not_called()

    def test_interrupted_record_is_reused_only_after_new_verification(self):
        api = mock.Mock()
        api.pages.side_effect = [[deployment()], []]
        new_run = RUN + "4"
        self.assertEqual(deploy.record(api, SHA, PROVIDER, new_run, DIGEST), (1, False))
        self.assertEqual(api.request.call_count, 1)
        self.assertEqual(api.request.call_args.args[0], "deployments/1/statuses")
        self.assertEqual(api.request.call_args.args[1]["log_url"], new_run)

    def test_later_run_reuses_receipt_but_appends_its_own_success_proof_once(self):
        api = mock.Mock()
        row = deployment()
        original_payload = copy.deepcopy(row["payload"])
        new_run = RUN + "4"
        history = [{"state": "inactive"}, success_status()]
        api.pages.side_effect = lambda path: [row] if path.startswith("deployments?") else history
        self.assertEqual(deploy.record(api, SHA, PROVIDER, new_run, DIGEST), (1, False))
        api.request.assert_called_once_with(
            "deployments/1/statuses",
            {
                "state": "success",
                "environment_url": deploy.check_live.DEFAULT_URL,
                "log_url": new_run,
                "auto_inactive": False,
                "description": "Vercel succeeded; every live file matches this commit",
            },
        )
        self.assertEqual(row["payload"], original_payload)
        history.insert(0, success_status(new_run))
        api.request.reset_mock()
        self.assertEqual(deploy.record(api, SHA, PROVIDER, new_run, DIGEST), (1, False))
        api.request.assert_not_called()
        self.assertIn(success_status(), history)

    def test_receipt_and_status_creators_must_be_the_actions_bot(self):
        for creator in (
            None,
            {},
            {**ACTIONS_CREATOR, "login": "attacker"},
            {**ACTIONS_CREATOR, "id": 1},
            {**ACTIONS_CREATOR, "type": "User"},
        ):
            with self.subTest(creator=creator):
                self.assertFalse(deploy.owned({**deployment(), "creator": creator}))
                api = mock.Mock()
                api.pages.return_value = [{**success_status(), "creator": creator}]
                self.assertFalse(deploy.was_successful(api, deployment()))

    def test_spoofed_same_run_success_cannot_suppress_current_proof(self):
        api = mock.Mock()
        api.pages.side_effect = [[deployment()], [{**success_status(), "creator": VERCEL_CREATOR}]]
        self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN, DIGEST), (1, False))
        api.request.assert_called_once()
        self.assertEqual(api.request.call_args.args[0], "deployments/1/statuses")
        self.assertEqual(api.request.call_args.args[1]["log_url"], RUN)

    def test_different_timestamp_or_build_digest_is_never_recovered(self):
        for changes in ({"deployed_at": "2026-11-03T12:00:00Z"}, {"build_sha256": "e" * 64}):
            row = deployment()
            row["payload"].update(changes)
            api = mock.Mock()
            api.pages.return_value = [row]
            api.request.return_value = {"id": 42}
            with self.subTest(changes=changes):
                self.assertEqual(deploy.record(api, SHA, PROVIDER, RUN, DIGEST), (42, True))
                self.assertEqual(api.request.call_args_list[0].args[0], "deployments")

    def test_receipt_environment_is_separate_from_vercel_deployment_records(self):
        # GitHub environment names are case-insensitive; Vercel uses Production/Preview.
        name = deploy.ENVIRONMENT.casefold()
        for vercel in ("production", "preview"):
            with self.subTest(vercel=vercel):
                self.assertNotEqual(name, vercel)
                self.assertFalse(name.startswith(vercel))
        api = mock.Mock()
        api.pages.return_value = []
        api.request.return_value = {"id": 42}
        deploy.record(api, SHA, PROVIDER, RUN, DIGEST)
        query = api.pages.call_args_list[0].args[0]
        self.assertIn(f"environment={deploy.ENVIRONMENT}&", query)
        create, status = api.request.call_args_list
        self.assertEqual(create.args[1]["environment"], deploy.ENVIRONMENT)
        self.assertFalse(create.args[1]["production_environment"])
        # A receipt status must never mark any other deployment record inactive.
        self.assertIs(status.args[1]["auto_inactive"], False)
        api.pages.reset_mock()
        api.pages.return_value = []
        deploy.frequency_report(api)
        self.assertEqual(
            api.pages.call_args_list[0].args[0],
            f"deployments?environment={deploy.ENVIRONMENT}&task=deploy",
        )

    def test_vercel_or_other_environment_records_are_never_receipts(self):
        for environment in ("Production", "production", "Preview", "Production – unpoliticalaf"):
            with self.subTest(environment=environment):
                self.assertFalse(deploy.owned({**deployment(), "environment": environment}))

    def test_malformed_success_statuses_cannot_authenticate_a_receipt(self):
        api = mock.Mock()
        api.pages.return_value = [
            None,
            {},
            {"state": "success"},
            {**success_status(), "log_url": "https://evil.test/run"},
        ]
        self.assertFalse(deploy.was_successful(api, deployment()))


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
        self.root = root
        enter(mock.patch.object(deploy.check_live, "ROOT", root))
        enter(
            mock.patch.dict(
                os.environ,
                {
                    "GITHUB_REF": "refs/heads/main",
                    "GITHUB_SHA": SHA,
                    "GITHUB_REPOSITORY": "jnyross/unpoliticalaf",
                    "GITHUB_RUN_ID": "123",
                    "GITHUB_EVENT_NAME": "push",
                },
            )
        )
        self.api = enter(mock.patch.object(deploy, "GitHub")).return_value
        self.api.request.side_effect = lambda path: (
            {"status": "identical"} if path.startswith("compare/") else workflow_run()
        )
        self.provider = enter(mock.patch.object(deploy, "vercel_success", return_value=PROVIDER))
        self.live = enter(mock.patch.object(deploy.check_live, "main", return_value=0))
        self.fetch = enter(
            mock.patch.object(
                deploy.check_live,
                "fetch",
                return_value=(200, (root / "site/build.json").read_bytes()),
            )
        )
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
        (self.root / "site/build.json").write_text(json.dumps({"commit": "b" * 40}))
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
        self.assertEqual(self.provider.call_args_list, [mock.call(self.api, SHA, 0)] * 2)
        self.live.assert_called_once_with(
            [
                "--url",
                deploy.check_live.DEFAULT_URL,
                "--site",
                str(self.root / "site"),
                "--wait",
                "0",
            ]
        )
        digest = hashlib.sha256((self.root / "site/build.json").read_bytes()).hexdigest()
        self.record.assert_called_once_with(self.api, SHA, PROVIDER, RUN, digest)

    def test_live_manifest_must_match_raw_bytes_not_only_json_semantics(self):
        self.fetch.return_value = (200, b'{"commit": "different"}')
        with self.assertRaises(ValueError):
            deploy.main([])
        self.record.assert_not_called()

    def test_provider_changing_during_live_verification_is_refused(self):
        self.provider.side_effect = [
            PROVIDER,
            {**PROVIDER, "target_url": PROVIDER["target_url"] + "2"},
        ]
        with self.assertRaises(ValueError):
            deploy.main([])
        self.record.assert_not_called()

    def test_report_failure_does_not_hide_a_successfully_retained_receipt(self):
        self.report.side_effect = subprocess.CalledProcessError(1, "gh")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(deploy.main([]), 0)
        self.assertIn("Recorded", output.getvalue())
        self.assertIn("frequency history is unavailable", output.getvalue())
        self.assertNotIn("| 0–7 |", output.getvalue())

    def test_unreachable_candidate_is_rejected_before_provider(self):
        self.api.request.side_effect = lambda path: (
            {"status": "ahead"} if path.startswith("compare/") else workflow_run()
        )
        with self.assertRaises(ValueError):
            deploy.main([])
        self.provider.assert_not_called()
        self.record.assert_not_called()

    def test_completed_run_event_guards_are_checked_at_cli(self):
        path = self.root / "event.json"
        self.api.request.side_effect = lambda endpoint: {**workflow_run(), "event": "workflow_run"}
        for changes in (
            {"status": "in_progress"},
            {"conclusion": "failure"},
            {"head_branch": "feature"},
            {"head_sha": "b" * 40},
            {"head_repository": {"full_name": "attacker/fork"}},
            {"repository": {"full_name": "attacker/fork"}},
            {"path": ".github/workflows/attacker.yml"},
        ):
            path.write_text(
                json.dumps({"action": "completed", "workflow_run": {**workflow_run(), **changes}})
            )
            with (
                self.subTest(changes=changes),
                mock.patch.dict(
                    os.environ,
                    {"GITHUB_EVENT_NAME": "workflow_run", "GITHUB_EVENT_PATH": str(path)},
                ),
                self.assertRaises(ValueError),
            ):
                deploy.main([])
        self.record.assert_not_called()

    def test_compatibility_live_workflow_path_is_allowed(self):
        self.api.request.side_effect = lambda endpoint: (
            {"status": "identical"}
            if endpoint.startswith("compare/")
            else {**workflow_run(), "path": ".github/workflows/live.yml"}
        )
        self.assertEqual(deploy.main([]), 0)
        self.record.assert_called_once()

    def test_successfully_completed_run_can_record(self):
        path = self.root / "event.json"
        path.write_text(
            json.dumps({"action": "completed", "workflow_run": {**workflow_run(), "id": 456}})
        )
        self.api.request.side_effect = lambda endpoint: (
            {"status": "behind"}
            if endpoint.startswith("compare/")
            else {**workflow_run(int(endpoint.rsplit("/", 1)[1])), "event": "workflow_run"}
        )
        with mock.patch.dict(
            os.environ, {"GITHUB_EVENT_NAME": "workflow_run", "GITHUB_EVENT_PATH": str(path)}
        ):
            self.assertEqual(deploy.main([]), 0)
        self.record.assert_called_once()

    def test_environment_cannot_spoof_github_branch_or_trigger_evidence(self):
        for changes in (
            {"head_branch": "feature"},
            {"event": "pull_request"},
            {"head_repository": {"full_name": "attacker/fork"}},
            {"repository": {"full_name": "attacker/fork"}},
            {"id": 456},
            {"path": ".github/workflows/attacker.yml"},
        ):
            self.api.request.side_effect = None
            self.api.request.return_value = {**workflow_run(), **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                deploy.main([])
        self.record.assert_not_called()

    def test_completed_run_api_evidence_cannot_be_spoofed_by_event_file(self):
        path = self.root / "event.json"
        path.write_text(
            json.dumps({"action": "completed", "workflow_run": {**workflow_run(), "id": 456}})
        )

        def request(endpoint):
            if endpoint == "actions/runs/456":
                return {**workflow_run(456), "status": "in_progress"}
            return {**workflow_run(), "event": "workflow_run"}

        self.api.request.side_effect = request
        with (
            mock.patch.dict(
                os.environ, {"GITHUB_EVENT_NAME": "workflow_run", "GITHUB_EVENT_PATH": str(path)}
            ),
            self.assertRaises(ValueError),
        ):
            deploy.main([])
        self.record.assert_not_called()

    def test_upstream_api_id_repository_and_path_are_validated(self):
        path = self.root / "event.json"
        path.write_text(json.dumps({"action": "completed", "workflow_run": workflow_run(456)}))
        for changes in (
            {"id": 999},
            {"repository": {"full_name": "attacker/fork"}},
            {"path": ".github/workflows/attacker.yml"},
            {"event": "pull_request"},
        ):

            def request(endpoint):
                if endpoint == "actions/runs/123":
                    return {**workflow_run(), "event": "workflow_run"}
                return {**workflow_run(456), **changes}

            self.api.request.side_effect = request
            with (
                self.subTest(changes=changes),
                mock.patch.dict(
                    os.environ,
                    {"GITHUB_EVENT_NAME": "workflow_run", "GITHUB_EVENT_PATH": str(path)},
                ),
                self.assertRaises(ValueError),
            ):
                deploy.main([])
        self.record.assert_not_called()

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
        rows = [
            deployment(),
            deployment(2),  # duplicate SHA is not a second deploy
            deployment(3, "b" * 40),
            deployment(4, "c" * 40, "2026-10-29T12:00:00Z"),  # exact 7-day boundary
            deployment(5, "d" * 40, "2026-10-08T12:00:00Z"),  # too old
            deployment(6, "e" * 40, "2026-11-06T12:00:00Z"),  # future
            deployment(7, "f" * 40),
        ]  # incomplete record
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
            return [{"state": "inactive"}, success_status()]

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
        rows = [
            deployment(i, when=value)
            for i, value in enumerate((None, "", "not-a-date", "2026-11-04T12:00:00"))
        ]
        rows[0]["payload"].pop("deployed_at")
        api.pages.return_value = rows
        report = "\n".join(deploy.frequency_report(api))
        self.assertIn("| 0–7 | 0 |", report)
        self.assertIn("excluded 4 record(s)", report)


if __name__ == "__main__":
    unittest.main()
