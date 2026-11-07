"""Container isolation and configurable setup contracts, without requiring Docker."""

import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def make_plan(*targets, venv=".venv", quality=False):
    arguments = ["make", "-n", f"VENV={venv}"]
    if quality:
        arguments.extend(["-f", "quality/Makefile"])
    return subprocess.run(
        [*arguments, *targets], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


class VirtualenvPaths(unittest.TestCase):
    def test_default_setup_remains_workspace_local(self):
        plan = make_plan("setup", "setup-quality", "verify")
        self.assertIn("-m venv .venv", plan)
        self.assertIn(".venv/bin/python -m builder.build", plan)

    def test_external_venv_routes_all_setup_and_checks(self):
        venv = "/tmp/unpoliticalaf-test-venv"
        plan = make_plan(
            "setup-dev-tools", "setup-quality", "check-deps", "verify", "hooks", venv=venv
        )
        self.assertIn(f"-m venv {venv}", plan)
        self.assertIn(f"{venv}/bin/python -m pip", plan)
        self.assertIn(f"{venv}/bin/python -m builder.build", plan)
        self.assertIn(f"cd quality && {venv}/bin/python -m deptry", plan)
        self.assertIn(f"{venv}/bin/python -m pre_commit install", plan)
        self.assertNotIn(".venv/bin/python", plan)

    def test_relative_override_resolves_deptry_before_changing_directory(self):
        plan = make_plan("check-deps", venv="custom-venv")
        self.assertIn(f"cd quality && {ROOT}/custom-venv/bin/python -m deptry", plan)

    def test_dashboard_uses_same_external_interpreter(self):
        venv = "/tmp/unpoliticalaf-test-venv"
        plan = make_plan("metrics", venv=venv, quality=True)
        self.assertIn(f"{venv}/bin/python -m quality.measure", plan)
        self.assertIn(f"{venv}/bin/python -m unittest", plan)
        self.assertNotIn(".venv/bin/python", plan)

    def test_dashboard_setup_preserves_exported_bootstrap_interpreter(self):
        result = subprocess.run(
            ["make", "-n", "-f", "quality/Makefile", "setup", "VENV=/tmp/new-quality-venv"],
            cwd=ROOT,
            env={**os.environ, "PYTHON": "/usr/local/bin/python3"},
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("/usr/local/bin/python3 -m venv /tmp/new-quality-venv", result.stdout)
        self.assertNotIn("/tmp/new-quality-venv/bin/python -m venv", result.stdout)

    def test_tools_only_setup_never_installs_outer_hook(self):
        plan = make_plan("setup-dev-tools")
        self.assertIn("-r requirements-dev.txt", plan)
        self.assertNotIn("pre_commit install", plan)
        self.assertNotIn("make hooks", plan)


class Devcontainer(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())

    def test_volume_never_mounts_over_outer_workspace(self):
        mounts = self.config["mounts"]
        self.assertEqual(len(mounts), 1)
        self.assertIn("source=unpoliticalaf-venv-${devcontainerId}", mounts[0])
        self.assertIn("target=/opt/unpoliticalaf/venv,type=volume,volume-nocopy", mounts[0])
        self.assertNotIn("containerWorkspaceFolder", mounts[0])
        self.assertNotIn("initializeCommand", self.config)

    def test_nonroot_tools_and_editor_share_isolated_python(self):
        self.assertEqual(self.config["remoteUser"], "vscode")
        environment = self.config["containerEnv"]
        self.assertEqual(environment["VENV"], "/opt/unpoliticalaf/venv")
        self.assertEqual(environment["PYTHON"], "/usr/local/bin/python3")
        settings = self.config["customizations"]["vscode"]["settings"]
        self.assertEqual(
            settings["python.defaultInterpreterPath"], "/opt/unpoliticalaf/venv/bin/python"
        )
        self.assertTrue(settings["python.testing.pytestEnabled"])
        self.assertFalse(settings["python.testing.unittestEnabled"])
        self.assertEqual(settings["python.testing.pytestArgs"], ["tests", "quality/tests"])

    def test_creation_installs_browsers_and_locked_node_tools_without_host_hooks(self):
        command = self.config["postCreateCommand"]
        self.assertIn("make setup-dev-tools", command)
        self.assertIn("npm ci --ignore-scripts", command)
        self.assertIn('"$VENV/bin/python" -m playwright install --with-deps chromium', command)
        self.assertNotIn("make setup-dev &&", command)
        self.assertNotIn("chown -R", command)
        self.assertNotIn("chown vscode:vscode .venv", command)


if __name__ == "__main__":
    unittest.main()
