"""Characterize charged actions and replay state across the session refactor."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import MagicMock, patch

from scripts import standins


class StandinActions(unittest.TestCase):
    def setUp(self):
        self.page = MagicMock()
        self.page.url = "http://example.test/index.html"
        self.page.evaluate.return_value = 120
        self.state = {
            "actions": 0,
            "log": [],
            "ops": [],
            "url": "index.html",
            "history": [],
            "scroll": 50,
            "items": [{"sel": "#choice", "kind": "select", "label": "Year"}],
        }

    def action(self, action, rest=(), mode="phone"):
        with redirect_stdout(StringIO()):
            return standins._session_action(
                self.page, "http://example.test/", self.state, "unused.json", mode, action, rest
            )

    def test_scroll_charges_one_action_and_logs_direction(self):
        self.assertEqual(self.action("scroll", ["up"]), (0, ""))
        self.assertEqual(self.state["actions"], 1)
        self.assertEqual(self.state["log"], ["scroll up"])
        self.assertEqual(self.page.evaluate.call_args.args[1], -standins.STEP)

    def test_successful_same_page_tap_is_replayed(self):
        self.assertEqual(self.action("tap", ["1"]), (0, ""))
        self.assertEqual(self.state["actions"], 1)
        self.assertEqual(self.state["ops"], [{"op": "tap", "sel": "#choice", "y": 120}])
        self.assertEqual(self.state["log"], ["tap [1] select: Year"])

    def test_failed_tap_is_charged_but_not_replayed(self):
        self.page.locator.return_value.first.click.side_effect = RuntimeError("blocked")
        self.assertEqual(self.action("tap", ["1"]), (0, ""))
        self.assertEqual(self.state["actions"], 1)
        self.assertEqual(self.state["ops"], [])

    def test_navigation_retains_history_and_resets_replay(self):
        self.page.url = "http://example.test/life/index.html"
        old_ops = [{"op": "choose", "sel": "#year", "value": "2024", "y": 0}]
        self.state["ops"] = old_ops
        self.assertEqual(self.action("tap", ["1"]), (0, "(new page)"))
        self.assertEqual(self.state["url"], "life/index.html")
        self.assertEqual(self.state["ops"], [])
        self.assertEqual(
            self.state["history"], [{"url": "index.html", "ops": old_ops, "scroll": 50}]
        )
        with patch.object(standins, "_open") as reopen:
            self.assertEqual(self.action("back"), (0, ""))
        reopen.assert_called_once()
        self.assertEqual(self.state["url"], "index.html")
        self.assertEqual(self.state["ops"], old_ops)
        self.assertEqual(self.state["actions"], 2)

    def test_successful_choice_is_charged_logged_and_replayed(self):
        self.assertEqual(self.action("choose", ["1", "2024"]), (0, ""))
        self.page.locator.return_value.first.select_option.assert_called_once_with(label="2024")
        self.assertEqual(self.state["actions"], 1)
        self.assertEqual(self.state["log"], ["choose [1] Year = 2024"])
        self.assertEqual(
            self.state["ops"], [{"op": "choose", "sel": "#choice", "value": "2024", "y": 120}]
        )

    def test_failed_choices_persist_charged_state(self):
        for kind in ("a", "select"):
            with self.subTest(kind=kind):
                self.state["items"][0]["kind"] = kind
                self.page.locator.return_value.first.select_option.side_effect = ValueError("bad")
                before = self.state["actions"]
                with patch.object(standins, "save_state") as save:
                    self.assertEqual(self.action("choose", ["1", "absent"]), (1, ""))
                save.assert_called_once_with("unused.json", self.state)
                self.assertEqual(self.state["actions"], before + 1)
                self.assertIn("failed choose [1]", self.state["log"][-1])
                self.assertEqual(self.state["ops"], [])

    def test_invalid_target_and_unknown_action_do_not_charge_or_save(self):
        with patch.object(standins, "save_state") as save:
            self.assertEqual(self.action("tap", ["2"]), (1, ""))
            self.assertEqual(self.action("unknown"), (2, ""))
        save.assert_not_called()
        self.assertEqual(self.state["actions"], 0)
        self.assertEqual(self.state["log"], [])
