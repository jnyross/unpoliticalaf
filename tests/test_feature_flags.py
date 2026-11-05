"""Rollout configuration, real rendering boundaries and reproducible records."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from builder import build, feature_flags as flags, html


class Configuration(unittest.TestCase):
    def test_existing_features_keep_defaults_and_new_features_default_off(self):
        self.assertEqual(dict(flags.resolve({})), {
            "chart_interactions": True, "sticky_navigation": True,
        })
        self.assertFalse(flags.FeatureFlag("An experimental enhancement").default)

    def test_partial_overrides_keep_other_defaults(self):
        self.assertEqual(dict(flags.resolve({flags.ENV_VAR: '{"chart_interactions":false}'})), {
            "chart_interactions": False, "sticky_navigation": True,
        })
        self.assertTrue(flags.resolve({flags.ENV_VAR: '{"chart_interactions":true}'})["chart_interactions"])

    def test_invalid_configuration_never_silently_enables_features(self):
        bad_values = [
            "", "{", "[]", "null", "true", '"flags"',
            '{"chart_interactions":"false"}', '{"chart_interactions":0}',
            '{"chart_interactions":1}', '{"chart_interactions":null}',
            '{"chart_interactions":[]}', '{"chart_interactions":{}}',
            '{"chart_interactions":NaN}', '{"typo":true}',
            '{"chart_interactions":true,"chart_interactions":false}',
        ]
        for raw in bad_values:
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, flags.ENV_VAR):
                flags.resolve({flags.ENV_VAR: raw})

    def test_registry_and_resolved_settings_are_immutable(self):
        with self.assertRaises(TypeError):
            flags.FLAGS["oops"] = flags.FeatureFlag("oops")
        with self.assertRaises(TypeError):
            flags.resolve({})["chart_interactions"] = False

    def test_environment_changes_do_not_reuse_old_settings(self):
        with patch.dict(os.environ, {flags.ENV_VAR: '{"chart_interactions":false}'}):
            self.assertFalse(flags.enabled("chart_interactions"))
        with patch.dict(os.environ, {flags.ENV_VAR: "{}"}):
            self.assertTrue(flags.enabled("chart_interactions"))
            with self.assertRaises(KeyError):
                flags.enabled("chart_interactons")


class Rendering(unittest.TestCase):
    def render(self, overrides):
        chart = html.line_chart("Example chart", ["2020", "2021"], [("Example", [1, 2], "a")], "units", kind="int")
        body = chart + '<table><caption>Example data</caption><tr><th>Year</th><td>2020</td></tr></table>'
        body += '<a href="#view" data-view="0">Cash view</a>'
        with patch.dict(os.environ, {flags.ENV_VAR: json.dumps(overrides)}):
            return html.page("example.html", "Example", body, folded=False, contents=False,
                             scripts="<script>/* page-specific script */</script>")

    def test_defaults_preserve_both_enhancements(self):
        output = self.render({})
        self.assertIn(html.CHART_JS, output)
        self.assertIn(html.BACKTOP_JS, output)

    def test_flags_control_only_their_own_enhancements(self):
        for charts in (False, True):
            for sticky in (False, True):
                with self.subTest(charts=charts, sticky=sticky):
                    output = self.render({"chart_interactions": charts, "sticky_navigation": sticky})
                    self.assertEqual(html.CHART_JS in output, charts)
                    self.assertEqual(html.BACKTOP_JS in output, sticky)
                    for retained in ('<svg', '<table', 'Example data', 'Example chart',
                                     'href="#top"', 'aria-label="Main"', html.VIEW_LINK_JS,
                                     "/* page-specific script */"):
                        self.assertIn(retained, output)

    def test_static_body_does_not_change_when_flags_change(self):
        def content(output):
            return output.split('<main id="main" class="wrap">')[1].split("</main>")[0]
        self.assertEqual(content(self.render({})),
                         content(self.render({"chart_interactions": False, "sticky_navigation": False})))


class BuildSafety(unittest.TestCase):
    def test_bad_configuration_preserves_last_good_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            index = site / "index.html"
            index.write_text("last good build")
            with patch.object(build, "OUT", site), patch.object(build, "all_sources") as sources:
                with patch.dict(os.environ, {flags.ENV_VAR: '{"typo":true}'}):
                    with self.assertRaises(ValueError):
                        build.main()
                sources.assert_not_called()
            self.assertEqual(index.read_text(), "last good build")

    def test_build_record_includes_effective_flags_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "index.html").write_text("home")
            with patch.object(build, "OUT", site), patch.object(build.version, "commit", return_value="a" * 40):
                with patch.dict(os.environ, {flags.ENV_VAR: '{"chart_interactions":false}'}):
                    build.write_build_record()
                    first = (site / "build.json").read_bytes()
                    build.write_build_record()
                    self.assertEqual((site / "build.json").read_bytes(), first)
            record = json.loads(first)
            self.assertEqual(record["feature_flags"], {"chart_interactions": False, "sticky_navigation": True})
            self.assertEqual(record["files"], {"index.html": hashlib.sha256(b"home").hexdigest()})


if __name__ == "__main__":
    unittest.main()
