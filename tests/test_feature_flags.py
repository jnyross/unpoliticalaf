"""Rollout configuration, real rendering boundaries and reproducible records."""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from builder import build, feature_flags as flags, html
from builder.data import Facts

ROOT = Path(__file__).resolve().parents[1]


class Configuration(unittest.TestCase):
    def test_existing_features_keep_defaults_and_new_features_default_off(self):
        self.assertEqual(
            dict(flags.resolve({})),
            {
                "chart_interactions": True,
                "sticky_navigation": True,
            },
        )
        self.assertFalse(flags.FeatureFlag("An experimental enhancement").default)

    def test_partial_overrides_keep_other_defaults(self):
        self.assertEqual(
            dict(flags.resolve({flags.ENV_VAR: '{"chart_interactions":false}'})),
            {
                "chart_interactions": False,
                "sticky_navigation": True,
            },
        )
        self.assertTrue(
            flags.resolve({flags.ENV_VAR: '{"chart_interactions":true}'})["chart_interactions"]
        )

    def test_invalid_configuration_never_silently_enables_features(self):
        bad_values = [
            "",
            "{",
            "[]",
            "null",
            "true",
            '"flags"',
            '{"chart_interactions":"false"}',
            '{"chart_interactions":0}',
            '{"chart_interactions":1}',
            '{"chart_interactions":null}',
            '{"chart_interactions":[]}',
            '{"chart_interactions":{}}',
            '{"chart_interactions":NaN}',
            '{"typo":true}',
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
            self.assertFalse(flags.resolve()["chart_interactions"])
        with patch.dict(os.environ, {flags.ENV_VAR: "{}"}):
            self.assertTrue(flags.resolve()["chart_interactions"])
            with self.assertRaises(KeyError):
                flags.resolve()["chart_interactons"]


class ProductionConfiguration(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config = Path(temporary.name) / "production.json"
        self.config.write_text('{"chart_interactions":false,"sticky_navigation":false}')
        mocked = patch.object(flags, "PRODUCTION_CONFIG", self.config)
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_production_uses_only_explicit_configuration(self):
        self.assertEqual(
            dict(flags.production({})),
            {
                "chart_interactions": False,
                "sticky_navigation": False,
            },
        )

    def test_production_rejects_environment_overrides_even_when_empty(self):
        for value in ("", "{}", '{"chart_interactions":true}'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unsetting"):
                flags.production({flags.ENV_VAR: value})

    def test_incomplete_or_invalid_production_configuration_fails(self):
        for value in (
            "{}",
            '{"chart_interactions":false}',
            "[]",
            "{",
            '{"chart_interactions":false,"sticky_navigation":"false"}',
            '{"chart_interactions":false,"sticky_navigation":false,"extra":false}',
            '{"chart_interactions":false,"chart_interactions":true,"sticky_navigation":false}',
        ):
            with self.subTest(value=value):
                self.config.write_text(value)
                with self.assertRaises(ValueError):
                    flags.production({})

    def test_missing_production_file_never_falls_back_to_defaults(self):
        self.config.unlink()
        with self.assertRaises(FileNotFoundError):
            flags.production({})

    def test_production_snapshot_is_immutable_and_not_cached_by_path(self):
        before = flags.production({})
        self.config.write_text('{"chart_interactions":true,"sticky_navigation":true}')
        self.assertFalse(before["chart_interactions"])
        self.assertTrue(flags.production({})["chart_interactions"])
        with self.assertRaises(TypeError):
            before["chart_interactions"] = True

    def test_all_production_entrypoints_share_the_explicit_build(self):
        root = Path(__file__).resolve().parents[1]
        vercel = json.loads((root / "vercel.json").read_text())
        self.assertEqual(vercel["buildCommand"], "make production-build")
        for target in ("production-build", "live"):
            command = subprocess.check_output(["make", "-n", target], cwd=root, text=True)
            self.assertIn("-m builder.build --production", command)
        legacy = (root / ".github/workflows/live.yml").read_text()
        self.assertIn("uses: ./.github/workflows/deploy.yml", legacy)
        live = (root / ".github/workflows/deploy.yml").read_text()
        self.assertIn("- run: make production-build", live)
        self.assertNotIn("- run: make build\n", live)


class Rendering(unittest.TestCase):
    def render(self, overrides):
        chart = html.line_chart(
            "Example chart", ["2020", "2021"], [("Example", [1, 2], "a")], "units", kind="int"
        )
        body = (
            chart
            + "<table><caption>Example data</caption><tr><th>Year</th><td>2020</td></tr></table>"
        )
        body += '<a href="#view" data-view="0">Cash view</a>'
        with patch.dict(os.environ, {flags.ENV_VAR: json.dumps(overrides)}):
            output = html.page(
                "example.html",
                "Example",
                body,
                folded=False,
                contents=False,
                scripts="<script>/* page-specific script */</script>",
            )
            return build.apply_feature_flags({"example.html": output}, flags.resolve())[
                "example.html"
            ]

    def test_defaults_preserve_both_enhancements(self):
        output = self.render({})
        self.assertIn(html.CHART_JS, output)
        self.assertIn(html.BACKTOP_JS, output)

    def test_flags_control_only_their_own_enhancements(self):
        for charts in (False, True):
            for sticky in (False, True):
                with self.subTest(charts=charts, sticky=sticky):
                    output = self.render(
                        {"chart_interactions": charts, "sticky_navigation": sticky}
                    )
                    self.assertEqual(html.CHART_JS in output, charts)
                    self.assertEqual(html.BACKTOP_JS in output, sticky)
                    for retained in (
                        "<svg",
                        "<table",
                        "Example data",
                        "Example chart",
                        'href="#top"',
                        'aria-label="Main"',
                        html.VIEW_LINK_JS,
                        "/* page-specific script */",
                    ):
                        self.assertIn(retained, output)

    def test_static_body_does_not_change_when_flags_change(self):
        def content(output):
            return output.split('<main id="main" class="wrap">')[1].split("</main>")[0]

        self.assertEqual(
            content(self.render({})),
            content(self.render({"chart_interactions": False, "sticky_navigation": False})),
        )


class BuildSafety(unittest.TestCase):
    def test_one_production_snapshot_drives_rendering_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets/icon.svg").write_text("<svg/>")
            config = root / "production.json"
            config.write_text('{"chart_interactions":false,"sticky_navigation":false}')
            seen = []

            def render(settings):
                seen.append(settings)
                config.write_text('{"chart_interactions":true,"sticky_navigation":true}')
                os.environ[flags.ENV_VAR] = '{"chart_interactions":true}'
                with self.assertRaises(TypeError):
                    settings["chart_interactions"] = True
                facts = Facts()
                output = html.page("index.html", "Test", "<p>Static answer</p>")
                pages = build.apply_feature_flags({"index.html": output}, settings)
                return facts, {}, pages, html.Num(facts)

            with patch.object(build, "ROOT", root), patch.object(build, "OUT", root / "site"):
                with patch.object(flags, "PRODUCTION_CONFIG", config):
                    with patch.object(build, "render", side_effect=render):
                        with patch.object(build.downloads, "FILES", {}):
                            with patch.object(
                                build, "write_build_record", wraps=build.write_build_record
                            ) as writer:
                                self.assertEqual(build.main(["--production"]), 0)
                                self.assertIs(writer.call_args.args[0], seen[0])
            record = json.loads((root / "site/build.json").read_text())
            self.assertEqual(
                record["feature_flags"], {"chart_interactions": False, "sticky_navigation": False}
            )
            self.assertNotIn(html.BACKTOP_JS, (root / "site/index.html").read_text())

    def test_bad_production_configuration_preserves_last_good_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            site.mkdir()
            index = site / "index.html"
            index.write_text("last good build")
            config = Path(tmp) / "production.json"
            config.write_text("{}")
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(flags, "PRODUCTION_CONFIG", config),
            ):
                with patch.object(build, "OUT", site), patch.object(build, "render") as render:
                    with self.assertRaises(ValueError):
                        build.main(["--production"])
                    render.assert_not_called()
            self.assertEqual(index.read_text(), "last good build")

    def test_bad_configuration_preserves_last_good_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            index = site / "index.html"
            index.write_text("last good build")
            with patch.object(build, "OUT", site), patch.object(build, "all_sources") as sources:
                with patch.dict(os.environ, {flags.ENV_VAR: '{"typo":true}'}):
                    with self.assertRaises(ValueError):
                        build.main([])
                sources.assert_not_called()
            self.assertEqual(index.read_text(), "last good build")

    def test_build_record_includes_effective_flags_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "index.html").write_text("home")
            with (
                patch.object(build, "OUT", site),
                patch.object(build.version, "commit", return_value="a" * 40),
            ):
                with patch.dict(os.environ, {flags.ENV_VAR: '{"chart_interactions":false}'}):
                    build.write_build_record(flags.resolve())
                    first = (site / "build.json").read_bytes()
                    build.write_build_record(flags.resolve())
                    self.assertEqual((site / "build.json").read_bytes(), first)
            record = json.loads(first)
            self.assertEqual(
                record["feature_flags"], {"chart_interactions": False, "sticky_navigation": True}
            )
            self.assertEqual(record["files"], {"index.html": hashlib.sha256(b"home").hexdigest()})


class RejectedBuildCommands(unittest.TestCase):
    def check_rejection(self, raw, production=False, override=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            (site / "index.html").write_bytes(b"last good output\n")
            (site / "build.json").write_bytes(b"last good manifest\n")
            before = {p.name: p.read_bytes() for p in site.iterdir()}
            config = root / "production.json"
            if raw is not None:
                config.write_text(raw)
            environment = dict(os.environ)
            environment.pop(flags.ENV_VAR, None)
            if not production:
                environment[flags.ENV_VAR] = raw
            elif override is not None:
                environment[flags.ENV_VAR] = override
            program = (
                "from builder import build, feature_flags; from pathlib import Path; import sys; "
                "build.OUT=Path(sys.argv[1]); feature_flags.PRODUCTION_CONFIG=Path(sys.argv[2]); "
                "sys.exit(build.run_logged(lambda: build.main(sys.argv[3:]), build.logger))"
            )
            result = subprocess.run(
                [sys.executable, "-c", program, str(site), str(config)]
                + (["--production"] if production else []),
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            exception = "FileNotFoundError" if raw is None else "ValueError"
            self.assertIn(exception, result.stderr)
            self.assertNotIn("build.started", result.stderr)
            self.assertIn("production.json" if production else flags.ENV_VAR, result.stderr)
            self.assertEqual({p.name: p.read_bytes() for p in site.iterdir()}, before)

    def test_rejected_local_commands_preserve_last_good_bytes(self):
        for raw in (
            "",
            "{",
            "[]",
            "null",
            "true",
            '"flags"',
            '{"chart_interactions":"false"}',
            '{"chart_interactions":0}',
            '{"chart_interactions":null}',
            '{"unknown":true}',
            '{"chart_interactions":true,"chart_interactions":false}',
        ):
            with self.subTest(raw=raw):
                self.check_rejection(raw)

    def test_rejected_production_commands_preserve_last_good_bytes(self):
        for raw in (
            None,
            "",
            "{",
            "[]",
            "null",
            "true",
            '"flags"',
            "{}",
            '{"chart_interactions":true}',
            '{"chart_interactions":true,"sticky_navigation":0}',
            '{"chart_interactions":true,"sticky_navigation":"false"}',
            '{"chart_interactions":true,"sticky_navigation":null}',
            '{"chart_interactions":true,"sticky_navigation":true,"unknown":false}',
            '{"chart_interactions":true,"chart_interactions":false,"sticky_navigation":true}',
        ):
            with self.subTest(raw=raw):
                self.check_rejection(raw, production=True)

    def test_every_production_override_presence_is_rejected(self):
        raw = '{"chart_interactions":true,"sticky_navigation":true}'
        for override in ("", "{}", '{"chart_interactions":true}'):
            with self.subTest(override=override):
                self.check_rejection(raw, production=True, override=override)


class Workflow(unittest.TestCase):
    def test_all_boolean_combinations_and_production_extend_existing_pipeline(self):
        text = (ROOT / ".github/workflows/check.yml").read_text()
        combinations = {
            tuple(sorted(json.loads(raw).items())) for raw in re.findall(r"flags: '([^']+)'", text)
        }
        self.assertEqual(
            combinations,
            {
                (("chart_interactions", charts), ("sticky_navigation", sticky))
                for charts in (False, True)
                for sticky in (False, True)
            },
        )
        for command in (
            "make benchmark",
            "make verify-coverage",
            "make test-stability",
            "make quality",
            "make architecture",
            "make production-verify",
        ):
            self.assertIn(command, text)
        self.assertIn("fail-fast: false", text)
        self.assertIn("make setup-test", text)

    def test_stable_check_accepts_only_successful_matrix_result(self):
        text = (ROOT / ".github/workflows/check.yml").read_text()
        check_job = text.split("  check:\n", 1)[1].split("\n  duplicates:", 1)[0]
        self.assertIn("needs: flag_configurations", check_job)
        self.assertIn("if: always()", check_job)
        self.assertIn("RESULT: ${{ needs.flag_configurations.result }}", check_job)
        command = next(
            line.strip().removeprefix("run: ")
            for line in check_job.splitlines()
            if line.strip().startswith('run: test "$RESULT"')
        )
        for result in ("success", "failure", "cancelled", "skipped", ""):
            with self.subTest(result=result):
                checked = subprocess.run(["sh", "-c", command], env=dict(os.environ, RESULT=result))
                self.assertEqual(checked.returncode == 0, result == "success")


if __name__ == "__main__":
    unittest.main()
