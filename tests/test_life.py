"""Life product regression checks; controller alone executes this suite.

Integration fixtures isolate unrelated fiscal source gates with named patches.
Life source custody, projection, rendering, independent validation and byte
regeneration remain real. Existing foundation corruption tests remain separate.
"""
from contextlib import ExitStack
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_life
import build as build_module
import check_life as checker
import check_schools as school
import life_projection as producer
import verify


class LifeProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = producer.project(ROOT)
        cls.html = build_life.render(cls.data)

    def test_full_projection_and_native_page_reopen_originals(self):
        self.assertEqual(checker.validate_candidate(ROOT, self.data, self.html), 176)
        self.assertEqual(len(self.data["anchors"]), 19)
        self.assertEqual(len(self.data["comparisons"]), 1444)
        self.assertEqual(sum(p["available"] for p in self.data["comparisons"]), 484)
        self.assertEqual({(p["from"], p["to"], p["phase"]) for p in self.data["comparisons"]},
                         {(a, b, phase) for a in range(2008, 2027) for b in range(2008, 2027)
                          for phase in ("5kyxd", "tfHTE", "TaWMP", "cDwC3")})
        self.assertEqual(producer.project(ROOT), self.data)
        self.assertEqual(build_life.render(self.data), self.html)

    def test_frozen_school_task_outputs_are_test_only(self):
        pairs = {p["id"]: p for p in self.data["comparisons"]}
        self.assertEqual(pairs["2016:2026:5kyxd"]["display"], "-1.0")
        self.assertEqual(pairs["2026:2016:5kyxd"]["display"], "+1.0")
        self.assertEqual(pairs["2026:2026:5kyxd"]["display"], "+0.0")
        primary = pairs["2026:2026:5kyxd"]["right"]
        secondary = pairs["2026:2026:tfHTE"]["right"]
        self.assertLess(Decimal(secondary), Decimal(primary))
        rows_2021 = [r for r in self.data["schools"]["rows"] if r["anchor"] == 2021]
        self.assertEqual(len(rows_2021), 16)
        self.assertTrue(next(a for a in self.data["anchors"] if a["year"] == 2021)["available"])
        missing = pairs["2015:2026:5kyxd"]
        self.assertFalse(missing["available"])
        self.assertIsNone(missing["display"])
        self.assertIsNone(missing["left"])
        self.assertIsNone(missing["right"])
        self.assertEqual(missing["operands"], [])

    def test_complete_life_semantics_reject_wrong_mappings_and_answer_changes(self):
        mutations = {
            "extra key": lambda d: d.__setitem__("invented", 1),
            "default": lambda d: d.__setitem__("default_anchor", 2015),
            "false topic": lambda d: d["topics"].__setitem__("housing", "available"),
            "anchor missing": lambda d: d["anchors"].pop(),
            "anchor period": lambda d: d["anchors"][-1].__setitem__("period", "2026/2027"),
            "navigation skips gap": lambda d: d["anchors"][6].__setitem__("next", 2016),
            "nearest": lambda d: d["anchors"][0].__setitem__("nearest", 2026),
            "gap zero": lambda d: d["comparisons"][0].__setitem__("display", "+0.0"),
            "pair missing": lambda d: d["comparisons"].pop(),
            "pair duplicate": lambda d: d["comparisons"].__setitem__(0, deepcopy(d["comparisons"][1])),
            "pair swapped": lambda d: d["comparisons"][-1].__setitem__("phase", "5kyxd"),
            "operand": lambda d: d["comparisons"][-1]["operands"][0].__setitem__("raw", "0"),
            "source": lambda d: d["comparisons"][-1]["operands"][0]["source"].__setitem__("locator", "/wrong"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = deepcopy(self.data)
                mutate(changed)
                with self.assertRaises(ValueError):
                    checker.validate_data(ROOT, changed)

    def test_visible_dom_values_headers_sources_and_year_labels_are_checked(self):
        # Each replacement is required to occur, so a selector drift cannot
        # silently convert a negative test into a positive check.
        changes = {
            "header": ("<th scope=\"col\">Class share (%)</th>", "<th scope=\"col\">Pupil share (%)</th>"),
            "source hash": (self.data["schools"]["sources"][school.INPUTS[0]]["sha256"], "0" * 64),
            "date": (self.data["schools"]["publication"]["api_published"], "2099-01-01"),
            "band": (">31 to 35<", ">31 to 36<"),
            "scope": ("not pupil residence", "pupil residence"),
        }
        for label, (old, new) in changes.items():
            with self.subTest(label=label):
                self.assertIn(old, self.html)
                changed = self.html.replace(old, new, 1)
                with self.assertRaises(ValueError):
                    checker.validate_candidate(ROOT, self.data, changed)
        match = re.search(r'(<span[^>]*data-measure="classes"[^>]*>)([^<]+)(</span>)', self.html)
        self.assertIsNotNone(match)
        changed = self.html[:match.start(2)] + "0" + self.html[match.end(2):]
        with self.assertRaises(ValueError):
            checker.validate_candidate(ROOT, self.data, changed)

    def test_core_concealment_and_unreviewed_attributes_are_rejected(self):
        self.assertEqual(checker.validate_candidate(ROOT, self.data, self.html), 176)
        changes = {
            "main hidden": ('<main id="main">', '<main id="main" hidden>'),
            "aria hidden": ('<main id="main">', '<main id="main" aria-hidden="true">'),
            "inert core": ('<section id="year-2016"', '<section inert id="year-2016"'),
            "unknown span attribute": ('data-measure="classes"', 'data-measure="classes" data-extra="unreviewed"'),
            "inline opacity": ('data-measure="classes"', 'data-measure="classes" style="opacity:0"'),
            "unknown class": ('<body class="nojs">', '<body class="concealed">'),
            "native popover": ('<main id="main">', '<main id="main" popover>'),
        }
        for label, (old, new) in changes.items():
            with self.subTest(label=label):
                self.assertIn(old, self.html)
                changed = self.html.replace(old, new, 1)
                with self.assertRaisesRegex(ValueError, "Life (hidden|unexpected)"):
                    checker.validate_candidate(ROOT, self.data, changed)
        document = checker.Document(self.html).root
        hidden = [node for node in document.find() if "hidden" in node.attrs]
        self.assertEqual({node.attrs["id"] for node in hidden}, {"life-year-controls", "compare-controls"})
        self.assertEqual(len(hidden), 2)
        self.assertEqual(len(document.find("details")), 16)


class LifeRegenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data/life").mkdir(parents=True)
        shutil.copy2(ROOT / school.REGISTER, self.root / school.REGISTER)
        shutil.copytree(ROOT / school.DIRECTORY, self.root / school.DIRECTORY)
        self.data = producer.project(self.root)
        self.public = producer.encode(self.data)
        self.html = build_life.render(self.data).encode("utf-8")
        self.write("data/life.json", self.public)
        self.write("site/data/life.json", self.public)
        self.write("site/life.html", self.html)

    def write(self, relative, body):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    def test_actual_generated_private_and_public_json_reject_staleness(self):
        generate = self.fiscal_isolation()
        verify.verify_life_generated(self.root)
        for relative, message in (
                ("data/life.json", "Generated life data is stale or changed; run make build"),
                ("site/data/life.json", "Published life data is stale or changed; run make build")):
            with self.subTest(relative=relative):
                stale = deepcopy(self.data)
                stale["comparisons"][-1]["display"] = "+9.9"
                self.write(relative, producer.encode(stale))
                with self.assertRaises(AssertionError) as failure:
                    verify.verify_life_generated(self.root)
                self.assertEqual(str(failure.exception), message)
                # Exercise the actual verify entry point with the same retained
                # corruption. Its real helper must stop before independent page
                # validation, receipt gates or public payload regeneration.
                with self.assertRaises(AssertionError) as integration_failure:
                    verify.main()
                self.assertEqual(str(integration_failure.exception), message)
                generate.assert_not_called()
                self.write(relative, self.public)
        verify.verify_life_generated(self.root)

    def test_real_regeneration_detects_stale_producer_arithmetic(self):
        original_mean = producer._mean
        def changed_mean(row):
            return original_mean(row) + Decimal("1")
        # Real project() and encode() run twice from retained originals. Only
        # one producer arithmetic primitive is deliberately corrupted.
        with patch.object(producer, "_mean", side_effect=changed_mean) as arithmetic:
            with self.assertRaises(AssertionError) as failure:
                verify.verify_life_generated(self.root)
            self.assertEqual(str(failure.exception),
                             "Generated life data is stale or changed; run make build")
            self.assertGreater(arithmetic.call_count, 0)

    def test_public_private_semantic_divergence_and_symlinks_are_rejected(self):
        changed = deepcopy(self.data)
        changed["default_anchor"] = 2015
        self.write("site/data/life.json", producer.encode(changed))
        with self.assertRaisesRegex(ValueError, "private/public life semantic parity"):
            checker.validate(self.root)
        self.write("site/data/life.json", self.public)
        target = self.root / "site/data/life.json"
        target.unlink()
        target.symlink_to(self.root / "data/life.json")
        with self.assertRaisesRegex(ValueError, "regular files"):
            verify.verify_life_generated(self.root)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            checker.validate(self.root)

    def fiscal_isolation(self):
        """Explicit source-free fiscal placeholders isolate life integration.

        Every life generator/checker remains real. Each unrelated fiscal gate
        has a named patch; no blanket exception handling or skipped assertion.
        """
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(verify, "ROOT", self.root))
        for name in ("validate_audit", "validate_receipt_audit", "validate_payer_sources",
                     "validate_schools", "validate_holiday_methods", "validate_work_methods",
                     "validate_work_data", "validate_receipts", "independent_basics_checks",
                     "independent_payer_checks"):
            stack.enter_context(patch.object(verify, name))
        stack.enter_context(patch.object(verify, "build_data", return_value={}))
        stack.enter_context(patch.object(verify, "build_receipts", return_value={}))
        base = {name: b"{}\n" for name in verify.PUBLIC_FILES
                if name not in ("life.html", "data/life.json")}
        for name, body in base.items():
            self.write("site/" + name, body)
        self.write("data/spending.json", base["data/spending.json"])
        self.write("data/receipts.json", verify.encode_receipts({}))

        def regenerate(_spending, _receipts):
            # The exact real life candidate is regenerated and independently
            # checked, then compared by verify.main with retained public bytes.
            current = producer.project(self.root)
            html = build_life.render(current)
            checker.validate_candidate(self.root, current, html)
            return {**base, "data/life.json": producer.encode(current),
                    "life.html": html.encode("utf-8")}
        return stack.enter_context(patch.object(verify, "payloads", side_effect=regenerate))

    def test_actual_stale_html_hits_exact_regenerate_compare_boundary(self):
        generate = self.fiscal_isolation()
        self.write("site/life.html", self.html + b"\n")
        # Harmless whitespace passes independent semantics. Only the real
        # regeneration byte comparison should reject this stale public file.
        self.assertEqual(checker.validate(self.root), 176)
        with self.assertRaises(AssertionError) as failure:
            verify.main()
        self.assertEqual(str(failure.exception), "Generated output is stale or changed; run make build")
        self.assertEqual(generate.call_count, 2)

    def test_verify_propagates_independent_life_gate_failure(self):
        self.fiscal_isolation()
        with patch.object(verify, "validate_life", side_effect=ValueError("life gate failed")) as gate:
            with self.assertRaises(ValueError) as failure:
                verify.main()
            self.assertEqual(str(failure.exception), "life gate failed")
            gate.assert_called_once_with(self.root)

    def test_build_private_life_symlink_and_directory_reject_before_producers(self):
        path = self.root / "data/life.json"
        original = path.read_bytes()
        outside = self.root / "outside.json"
        outside.write_bytes(b"preserve outside")
        for kind in ("symlink", "directory"):
            with self.subTest(kind=kind):
                path.unlink()
                if kind == "symlink":
                    path.symlink_to(outside)
                else:
                    path.mkdir()
                before = verify.snapshot(self.root / "site")
                with patch.object(build_module, "ROOT", self.root), patch.object(
                        build_module, "build_receipts", side_effect=AssertionError("producer must not run")) as producer_gate:
                    with self.assertRaises(ValueError) as failure:
                        build_module.build(self.root / "site")
                    self.assertEqual(str(failure.exception), "data/life.json must be a regular file")
                    producer_gate.assert_not_called()
                self.assertEqual(verify.snapshot(self.root / "site"), before)
                self.assertEqual(outside.read_bytes(), b"preserve outside")
                if kind == "symlink":
                    self.assertTrue(path.is_symlink())
                    path.unlink()
                else:
                    self.assertTrue(path.is_dir())
                    path.rmdir()
                path.write_bytes(original)

    def test_real_payload_generation_rejects_stale_renderer_before_publication(self):
        # Fiscal families are outside this focused test. Keep the actual life
        # render call and independent candidate check inside build.payloads.
        self.write("data/corrections.json", b"{}")
        self.write("data/tax-basics/sources.json", b"{}")
        actual_render = build_life.render
        def corrupted_render(data):
            html = actual_render(data)
            match = re.search(r'(<span[^>]*data-measure="classes"[^>]*>)([^<]+)(</span>)', html)
            self.assertIsNotNone(match)
            return html[:match.start(2)] + "0" + html[match.end(2):]
        before = verify.snapshot(self.root)
        with ExitStack() as stack:
            stack.enter_context(patch.object(build_module, "ROOT", self.root))
            for name in ("public_fields", "validate_basics_sources", "validate_payer_data",
                         "validate_payer_page", "validate_basics_fragments"):
                stack.enter_context(patch.object(build_module, name))
            stack.enter_context(patch.object(build_module, "project_taxes", return_value={}))
            stack.enter_context(patch.object(build_module.build_site, "configure"))
            stack.enter_context(patch.object(build_module.build_payers, "render", return_value="<html></html>"))
            stack.enter_context(patch.object(build_module.build_taxes, "render", return_value="<html></html>"))
            stack.enter_context(patch.object(build_life, "render", side_effect=corrupted_render))
            with self.assertRaisesRegex(ValueError, "life DOM classes complete cell"):
                build_module.payloads({}, {}, {}, self.data)
        self.assertEqual(verify.snapshot(self.root), before)


class LifePublicationLimitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.public = {name: b"small" for name in build_module.PUBLIC_FILES}
        for name in ("spending", "receipts", "life"):
            path = self.root / "data" / (name + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"old private " + name.encode())
        source = self.root / "data/life/retained-source.txt"
        source.parent.mkdir()
        source.write_bytes(b"source must be unchanged")
        for name, body in self.public.items():
            path = self.root / "site" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)

    def isolate_payload_boundary(self):
        # Validate caps and transactional publication after candidate generation.
        # The payload is explicit; no claim of source validation is made here.
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(build_module, "ROOT", self.root))
        stack.enter_context(patch.object(build_module, "build_receipts", return_value={}))
        stack.enter_context(patch.object(build_module, "validate_receipts"))
        stack.enter_context(patch.object(build_module, "build_data", return_value={}))
        stack.enter_context(patch.object(build_module, "project_payers", return_value={}))
        stack.enter_context(patch.object(build_module, "validate_payer_data"))
        return stack.enter_context(patch.object(build_module, "payloads", return_value=self.public))

    def test_each_html_exactly_500000_bytes_rejected_before_any_write(self):
        self.isolate_payload_boundary()
        before = verify.snapshot(self.root)
        for name in ("index.html", "methods.html", "taxes.html", "who-pays.html", "life.html"):
            with self.subTest(name=name):
                self.public[name] = b"x" * 500000
                with self.assertRaises(ValueError) as failure:
                    build_module.build(self.root / "site")
                self.assertEqual(str(failure.exception), name + ": over the public page/projection size limit")
                self.assertEqual(verify.snapshot(self.root), before)
                self.public[name] = b"small"

    def test_life_json_larger_than_html_cap_is_published_without_new_json_cap(self):
        self.isolate_payload_boundary()
        self.public["data/life.json"] = b"x" * 500001
        source = self.root / "data/life/retained-source.txt"
        original_source = source.read_bytes()
        build_module.build(self.root / "site")
        self.assertEqual((self.root / "site/data/life.json").read_bytes(), self.public["data/life.json"])
        self.assertEqual((self.root / "data/life.json").read_bytes(), self.public["data/life.json"])
        self.assertEqual(source.read_bytes(), original_source)


if __name__ == "__main__":
    unittest.main()
