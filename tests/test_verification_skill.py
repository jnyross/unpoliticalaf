"""Keep the public verification recipe discoverable and executable."""

import re
import unittest
from pathlib import Path

from scripts.check_agents import LINK, local_reference


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude/skills/verify-static-site/SKILL.md"


def missing_links(text, base):
    """Resolve Markdown links relative to their document, not the process cwd."""
    return [
        path
        for match in LINK.finditer(text)
        if (path := local_reference(match[1])) and not (base / path).exists()
    ]


def unknown_targets(text):
    """Check literal make invocations against the canonical root Makefile."""
    targets = set(re.findall(r"^([\w-]+):", (ROOT / "Makefile").read_text(), re.MULTILINE))
    return sorted(set(re.findall(r"\bmake ([\w-]+)", text)) - targets)


class VerificationSkill(unittest.TestCase):
    def test_metadata_and_discovery(self):
        text = SKILL.read_text()
        self.assertTrue(text.startswith("---\nname: verify-static-site\ndescription: "))
        self.assertIn("\n---\n", text)
        for name in ("README.md", "CONTRIBUTING.md"):
            self.assertIn(".claude/skills/verify-static-site/SKILL.md", (ROOT / name).read_text())

    def test_document_links_and_make_commands_exist(self):
        text = SKILL.read_text()
        self.assertEqual(missing_links(text, SKILL.parent), [])
        self.assertEqual(unknown_targets(text), [])
        self.assertIn("make setup-test", text)
        for command in ("make verify", "make quality", "make a11y"):
            self.assertIn(command, text)

    def test_broken_link_and_unknown_command_are_rejected(self):
        self.assertEqual(
            missing_links("[bad](missing-verification.md)", ROOT), ["missing-verification.md"]
        )
        self.assertEqual(
            unknown_targets("make nonexistent-verification-target"),
            ["nonexistent-verification-target"],
        )

    def test_current_safety_and_evidence_boundaries(self):
        text = SKILL.read_text()
        for required in (
            "--no-env",
            "Boat",
            "VERCEL_GIT_COMMIT_SHA",
            "staged",
            "independent agent review",
            "production flags",
            "actual exit",
            "not passed",
            "met (simulated)",
            "agent-browser",
            "quality/tests/",
            "pytest",
            "no-JavaScript",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        for obsolete in (
            "real five-person phone study",
            "controller-only",
            "/home/john/",
            "make setup && make verify",
        ):
            self.assertNotIn(obsolete, text)


if __name__ == "__main__":
    unittest.main()
