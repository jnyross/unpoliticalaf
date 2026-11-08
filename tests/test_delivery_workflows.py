"""Canonical routing, fail-closed activation and production configuration."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"


class DeliveryWorkflows(unittest.TestCase):
    def test_canonical_deploy_preserves_metrics_even_when_verification_fails(self):
        workflow = (WORKFLOWS / "deploy.yml").read_text()
        self.assertIn("name: Verify and record production deployment", workflow)
        self.assertIn("- run: make production-build", workflow)
        self.assertIn(".venv/bin/python scripts/check_live.py", workflow)
        self.assertIn(".venv/bin/python scripts/record_deployment.py", workflow)
        self.assertNotIn("python3 scripts/", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertIn("retention-days: 14", workflow)
        self.assertIn("live-site-metrics-${{ github.run_id }}-${{ github.run_attempt }}", workflow)
        self.assertIn("receipt-metrics-${{ github.run_id }}-${{ github.run_attempt }}", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertIn("vars.REVIEWED_PRODUCTION_DELIVERY == 'true'", workflow)
        self.assertIn("persist-credentials: false", workflow)

    def test_legacy_entrypoint_only_delegates_and_disabled_writer_stays_disabled(self):
        legacy = (WORKFLOWS / "live.yml").read_text()
        self.assertIn("uses: ./.github/workflows/deploy.yml", legacy)
        self.assertNotIn("schedule:", legacy)
        self.assertNotIn("make build", legacy)
        merge = (WORKFLOWS / "auto-merge.yml").read_text()
        self.assertIn("deploy.yml", merge)
        self.assertIn("workflow_dispatch", merge)
        self.assertNotIn("\n  pull_request:", merge)

    def test_release_requires_exact_main_success_and_matching_receipt_before_publish(self):
        workflow = (WORKFLOWS / "release.yml").read_text()
        for text in (
            "Verify and record production deployment",
            "Live site matches main",
            "conclusion == 'success'",
            "head_branch == 'main'",
            "head_repository.full_name == github.repository",
            "vars.REVIEWED_PRODUCTION_DELIVERY == 'true'",
            'fromJSON(\'["push","workflow_dispatch"]\')',
            "ref: ${{ github.event.workflow_run.head_sha }}",
            "VERCEL_GIT_COMMIT_SHA: ${{ github.event.workflow_run.head_sha }}",
            "make setup-release",
            "make production-verify",
            ".venv/bin/python scripts/release_evidence.py",
            ".venv/bin/python scripts/package_release.py",
            "PYTHON: .venv/bin/python",
            "cancel-in-progress: false",
        ):
            self.assertIn(text, workflow)
        self.assertNotIn("make setup-test", workflow)
        self.assertNotIn("download-artifact", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertLess(workflow.index("release_evidence.py"), workflow.index("publish_release.sh"))

    def test_version_notes_use_separate_reviewed_helper(self):
        workflow = (WORKFLOWS / "release-notes.yml").read_text()
        self.assertIn('tags: ["v[0-9]*"]', workflow)
        self.assertIn('require("./scripts/release_notes.cjs")', workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("site-", workflow)
