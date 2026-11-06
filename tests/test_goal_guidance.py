"""Protect the approved autonomous goal without rewriting historical evidence."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def active_text(path):
    """Archived contract and handoff sections are evidence, not instructions."""
    text = (ROOT / path).read_text(encoding="utf-8")
    return text.split("## Historical", 1)[0]


class GoalGuidance(unittest.TestCase):
    def test_active_entry_points_select_current_goal(self):
        for path in (
            "AGENTS.md", "START.md", "AUTONOMOUS-BRIEF.md", "README.md",
            "docs/product-spec.md", "docs/v2-contract.md", "docs/HANDOFF.md",
            "docs/goal-scorecard.md", "docs/user-test/README.md",
            "docs/standins/README.md",
        ):
            with self.subTest(path=path):
                text = active_text(path)
                self.assertIn("goal-rubric.md", text)
                self.assertIn("5 November 2026", text)

    def test_current_target_has_no_required_human_upgrade(self):
        text = active_text("docs/goal-rubric.md")
        self.assertIn("49 out of 55", text)
        self.assertIn("Every dimension scores at least 4", text)
        self.assertIn("D11 scores 5", text)
        self.assertIn("no probe is still open", text)
        self.assertIn("same live", text)
        self.assertIn("no unresolved material finding", text)
        self.assertNotIn("only when the real five-person", text)
        self.assertNotIn("is not the goal's own definition of success", text)
        self.assertIn("does not prove that real newcomers understand it", text)

    def test_historical_labels_preserve_unaffected_product_requirements(self):
        text = active_text("docs/product-spec.md")
        self.assertIn("v1 product requirements 1–12", text)
        self.assertIn("reuse/source boundaries remain applicable", text)
        self.assertIn("except where explicitly superseded", text)

    def test_delivery_is_public_independent_pr_not_controller(self):
        text = active_text("AGENTS.md")
        for required in ("public", "pull requests", "independent", "Boat", "CI"):
            self.assertIn(required, text)
        for obsolete in (
            "Direct-main publication is authorised",
            "Keep this repository private",
            "Use the explicit human-gate issues",
            "meaning at least\n  31/32",
        ):
            self.assertNotIn(obsolete, text)

    def test_phone_prompt_uses_grouped_actions_not_human_seconds(self):
        text = active_text("docs/standins/prompts/phone-reader.md")
        self.assertIn("RN-johns-<group>.json", text)
        self.assertIn("seven", text)
        self.assertNotIn("RN-johns.json", text)
        self.assertNotIn("about 8 minutes", text)


if __name__ == "__main__":
    unittest.main()
