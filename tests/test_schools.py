"""School foundation corruption checks; execution belongs to the controller.

Synthetic source mutations below isolate the semantic audit beneath its pinned
byte gate. They never replace retained inputs or count as revalidated sources.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
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
import check_schools as checker
import school_projection as producer
from build import PUBLIC_FILES, validate_output


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals, cls.evidence = checker.reopen(ROOT)
        cls.candidate = producer.project(ROOT)

    def check(self, candidate=None, originals=None):
        with localcontext() as context:
            context.prec = 50
            return checker.check(self.candidate if candidate is None else candidate,
                                 self.originals if originals is None else originals, self.evidence)

    def reject_projection(self, mutate):
        changed = deepcopy(self.candidate)
        mutate(changed)
        with self.assertRaises(ValueError):
            self.check(changed)

    def reject_query(self, mutate):
        changed = deepcopy(self.originals)
        query = checker.decode(changed[checker.INPUTS[0]])
        mutate(query)
        changed[checker.INPUTS[0]] = json.dumps(query).encode()
        with self.assertRaises(ValueError):
            self.check(originals=changed)

    def reject_metadata(self, mutate):
        changed = deepcopy(self.originals)
        meta = checker.decode(changed[checker.INPUTS[1]])
        mutate(meta)
        changed[checker.INPUTS[1]] = json.dumps(meta).encode()
        with self.assertRaises(ValueError):
            self.check(originals=changed)

    @staticmethod
    def change_page(originals, name, mutate):
        body = originals[name].decode("utf-8")
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', body)
        document = json.loads(match[1])
        mutate(document["props"]["pageProps"])
        originals[name] = (body[:match.start(1)] + json.dumps(document) + body[match.end(1):]).encode("utf-8")

    def test_full_projection_is_deterministic_and_input_only(self):
        paths = [ROOT / checker.REGISTER] + [ROOT / checker.DIRECTORY / n for n in checker.INPUTS]
        before = {str(p): p.read_bytes() for p in paths}
        self.assertEqual(checker.validate(ROOT, self.candidate), 176)
        self.assertEqual(producer.project(ROOT), self.candidate)
        self.assertEqual(before, {str(p): p.read_bytes() for p in paths})
        self.assertFalse((ROOT / "data/life/schools.json").exists())
        self.assertEqual(len(self.candidate["comparisons"]), 2)
        self.assertEqual(len(self.candidate["reconciliations"]), 88)
        self.assertEqual({r["anchor"] for r in self.candidate["rows"]}, set(range(2016, 2027)))
        self.assertEqual(sum(r["anchor"] == 2021 for r in self.candidate["rows"]), 16)

    def test_grid_order_has_no_statistical_meaning(self):
        candidate = deepcopy(self.candidate)
        candidate["rows"].reverse()
        self.assertEqual(self.check(candidate), 176)

    def test_published_precision_z_blank_and_scoped_notes_survive(self):
        for row in self.candidate["rows"]:
            self.assertEqual(row["published"]["Wc9V2"]["raw"],
                             checker.decode(self.originals[checker.INPUTS[0]])["results"][
                                 int(row["source"]["locator"].split("/")[-1])]["values"]["Wc9V2"])
            self.assertIn("method", row["notes"])
            self.assertIn("one_teacher", row["notes"])
            self.assertIn("school location", row["geography"])
        preview = self.candidate["catalogue_preview"]["data"]
        self.assertEqual(preview["rows"][2][-1], "z")
        self.assertEqual(preview["rows"][2][10:12], ["", ""])
        self.assertIn("Not applicable", self.candidate["quality_codes"]["z"])
        self.assertIn("for all years", self.candidate["notes"]["method"]["text"])
        release = self.candidate["sources"][checker.INPUTS[4]]
        self.assertEqual(release["reported_request_status"], 308)
        self.assertIn("no final200headerclaim", release["custody_caution"])

    def test_published_band_residuals_are_not_normalized_away(self):
        residuals = {(r["timePeriod"]["period"], r["phase"]): r["residual_total_minus_bands"]
                     for r in self.candidate["reconciliations"]
                     if r["indicator"] == "EAicq" and r["residual_total_minus_bands"] != "0"}
        self.assertEqual(residuals, {("2015/2016", "Primary"): "1",
                                     ("2015/2016", "Secondary"): "3", ("2017/2018", "Secondary"): "2"})
        row = next(r for r in self.candidate["rows"] if r["timePeriod"]["period"] == "2015/2016"
                   and r["phase"] == "Secondary" and r["band"] == "1 to 30")
        self.assertEqual(row["derived"]["class_share"]["operands"][1]["raw"], "145397")

    def test_reject_stale_producer_without_using_producer_as_oracle(self):
        stale = deepcopy(self.candidate)
        stale["rows"][0]["published"]["EAicq"]["raw"] = "0"
        with patch.object(producer, "project", return_value=stale) as build:
            with self.assertRaises(ValueError):
                checker.validate(ROOT)
            build.assert_called_once_with(ROOT)

    def test_missing_duplicate_extra_wrong_and_gap_projected_rows(self):
        changes = {
            "missing": lambda p: p["rows"].pop(),
            "duplicate": lambda p: p["rows"].__setitem__(0, deepcopy(p["rows"][1])),
            "extra": lambda p: p["rows"].append(deepcopy(p["rows"][0])),
            "year": lambda p: p["rows"][0]["timePeriod"].__setitem__("period", "2014/2015"),
            "2021 gap": lambda p: p.__setitem__("rows", [r for r in p["rows"] if r["anchor"] != 2021]),
            "geography": lambda p: p["rows"][0].__setitem__("geographicLevel", "LA"),
            "location": lambda p: p["rows"][0].__setitem__("locations", {"NAT": "other"}),
            "phase": lambda p: p["rows"][0]["filters"].__setitem__("5cGdi", "unknown"),
            "band": lambda p: p["rows"][0]["filters"].__setitem__("cAd31", "unknown"),
            "anchor": lambda p: p["rows"][0].__setitem__("anchor", 2015),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                self.reject_projection(mutate)

    def test_wrong_measure_denominators_rounding_and_operands(self):
        changes = {
            "wrong class share": lambda p: p["rows"][0]["derived"].__setitem__(
                "class_share", deepcopy(p["rows"][0]["derived"]["pupil_share"])),
            "wrong pupil share": lambda p: p["rows"][0]["derived"].__setitem__(
                "pupil_share", deepcopy(p["rows"][0]["derived"]["class_share"])),
            "wrong phase denominator": lambda p: p["rows"][0]["derived"]["class_share"]["operands"][1]["filters"].__setitem__("5cGdi", "tfHTE"),
            "unweighted mean": lambda p: p["rows"][0]["derived"]["mean"].__setitem__("formula", "mean(local means)"),
            "changed mean": lambda p: p["rows"][0]["derived"]["mean"].__setitem__("display", "0.0"),
            "mean precision": lambda p: p["rows"][0]["published"]["Wc9V2"].__setitem__("decimalPlaces", 2),
            "wrong unit": lambda p: p["rows"][0]["published"]["EAicq"].__setitem__("unit", "pupils"),
            "trimmed precision": lambda p: p["rows"][0]["published"]["Wc9V2"].__setitem__("raw", p["rows"][0]["published"]["Wc9V2"]["display"]),
            "missing to zero": lambda p: p["rows"][0]["published"]["EAicq"].__setitem__("raw", "0"),
            "nan": lambda p: p["rows"][0]["derived"]["mean"].__setitem__("display", float("nan")),
            "inf": lambda p: p["rows"][0]["derived"]["mean"].__setitem__("display", float("inf")),
            "quality": lambda p: p["rows"][0]["published"]["Wc9V2"].pop("quality"),
            "dropped operand": lambda p: p["rows"][0]["derived"]["mean"]["operands"].pop(),
            "primary double count": lambda p: p["rows"][0]["derived"]["mean"].__setitem__("formula", "Primary + Infant + KS2"),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                self.reject_projection(mutate)

    def test_notes_quality_scope_vintage_and_provenance_tampering(self):
        changes = {
            "z lost": lambda p: p["catalogue_preview"]["data"]["rows"][2].__setitem__(-1, "0"),
            "z meaning": lambda p: p["quality_codes"].__setitem__("z", "Zero"),
            "blank": lambda p: p["catalogue_preview"]["data"]["rows"][0].__setitem__(10, "0"),
            "notes lost": lambda p: p["rows"][0]["notes"].clear(),
            "note altered": lambda p: p["notes"]["method"].__setitem__("text", "Secondary excluded before 2018/19"),
            "method splice": lambda p: p["rows"][0]["source"].__setitem__("sha256", "old-release"),
            "raw locator": lambda p: p["rows"][0]["published"]["QtxWw"]["source"].__setitem__("locator", "/results/1/values/QtxWw"),
            "scope": lambda p: p["rows"][0].__setitem__("population", "All UK pupils"),
            "residence": lambda p: p["rows"][0].__setitem__("geography", "England residents"),
            "forecast": lambda p: p["rows"][0].__setitem__("status", "Forecast"),
            "pandemic gap": lambda p: p["scope"].__setitem__("series", "January 2021 missing"),
            "date invented": lambda p: p["rows"][0].__setitem__("census", "2016-01-01"),
            "final200": lambda p: p["sources"][checker.INPUTS[4]].__setitem__("reported_request_status", 200),
            "footnote": lambda p: p["publication"]["catalogue_footnotes"].clear(),
            "version": lambda p: p["publication"].__setitem__("version", "2.0"),
            "published": lambda p: p["publication"].__setitem__("api_published", "2026-10-31"),
            "pair": lambda p: p["comparisons"][0].__setitem__("display", "+0.0"),
            "pair raw operand": lambda p: p["comparisons"][0]["operands"][0].__setitem__("raw", "0"),
            "residual hidden": lambda p: p["reconciliations"].clear(),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                self.reject_projection(mutate)

    def test_class_and_pupil_shares_have_distinct_raw_denominators(self):
        row = next(r for r in self.candidate["rows"] if r["timePeriod"]["period"] == "2025/2026"
                   and r["phase"] == "Infant (Reception plus KS1)" and r["band"] == "31 to 35")
        self.assertEqual([o["raw"] for o in row["derived"]["class_share"]["operands"]], ["1260", "56961"])
        self.assertEqual([o["raw"] for o in row["derived"]["pupil_share"]["operands"]], ["39354", "1476175"])
        self.assertNotEqual(row["derived"]["class_share"]["display"], row["derived"]["pupil_share"]["display"])
        altered = deepcopy(self.candidate)
        wrong = next(r for r in altered["rows"] if r["source"] == row["source"])
        wrong["derived"]["class_share"]["display"] = row["derived"]["pupil_share"]["display"]
        with self.assertRaises(ValueError):
            self.check(altered)

    def test_original_grid_semantics_beneath_hash_gate(self):
        mutations = {
            "missing": lambda q: q["results"].pop(),
            "duplicate": lambda q: q["results"].__setitem__(0, deepcopy(q["results"][1])),
            "extra": lambda q: q["results"].append(deepcopy(q["results"][0])),
            "warning": lambda q: q.__setitem__("warnings", ["truncated"]),
            "paging": lambda q: q["paging"].__setitem__("totalPages", 2),
            "year": lambda q: q["results"][0]["timePeriod"].__setitem__("period", "2014/2015"),
            "period code": lambda q: q["results"][0]["timePeriod"].__setitem__("code", "CY"),
            "geo": lambda q: q["results"][0].__setitem__("geographicLevel", "REG"),
            "location": lambda q: q["results"][0]["locations"].__setitem__("NAT", "other"),
            "phase": lambda q: q["results"][0]["filters"].__setitem__("5cGdi", "other"),
            "band": lambda q: q["results"][0]["filters"].__setitem__("cAd31", "other"),
            "mean": lambda q: q["results"][0]["values"].__setitem__("Wc9V2", "0.1"),
            "missing value": lambda q: q["results"][0]["values"].__setitem__("QtxWw", None),
            "zero divisor": lambda q: q["results"][0]["values"].__setitem__("EAicq", "0"),
            "nan": lambda q: q["results"][0]["values"].__setitem__("Wc9V2", "NaN"),
            "inf": lambda q: q["results"][0]["values"].__setitem__("Wc9V2", "Infinity"),
            "numeric coercion": lambda q: q["results"][0]["values"].__setitem__("EAicq", 0),
            "not applicable to zero": lambda q: q["results"][0]["values"].__setitem__("Wc9V2", "z"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                self.reject_query(mutate)

    def test_original_metadata_semantics_beneath_hash_gate(self):
        mutations = {
            "label": lambda m: m["filters"][0]["options"][0].__setitem__("label", "Other"),
            "code": lambda m: m["filters"][0]["options"][0].__setitem__("id", "other"),
            "column": lambda m: m["indicators"][0].__setitem__("column", "pupil_teacher_ratio"),
            "unit": lambda m: m["indicators"][0].__setitem__("unit", "percent"),
            "precision": lambda m: m["indicators"][0].__setitem__("decimalPlaces", 2),
            "indicator label": lambda m: m["indicators"][0].__setitem__("label", "Other"),
            "year": lambda m: m["timePeriods"].pop(),
            "geographic level label": lambda m: m["geographicLevels"][1].__setitem__("label", "UK"),
            "national label": lambda m: next(g for g in m["locations"] if g["level"]["code"] == "NAT")["options"][0].__setitem__("label", "UK"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                self.reject_metadata(mutate)

    def test_original_page_identity_and_notes_beneath_hash_gate(self):
        mutations = [
            (checker.INPUTS[2], lambda p: p["apiDataSet"].__setitem__("id", "wrong")),
            (checker.INPUTS[2], lambda p: p["apiDataSetVersion"].__setitem__("version", "2.0")),
            (checker.INPUTS[2], lambda p: p["apiDataSet"].__setitem__("title", "Pupil teacher ratios")),
            (checker.INPUTS[2], lambda p: p["apiDataSetVersion"].__setitem__("published", "2026-10-31")),
            (checker.INPUTS[3], lambda p: next(b for s in p["data"]["content"] for b in s["content"]
                if b["id"] == "e61523ad-ce39-49b1-85b2-193730b8d02e").__setitem__(
                    "body", "<p>From 2019, old releases exclude secondary before 2018/19.</p>")),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name, mutation=repr(mutate)):
                originals = deepcopy(self.originals)
                self.change_page(originals, name, mutate)
                with self.assertRaises(ValueError):
                    self.check(originals=originals)

    def test_signed_change_uses_unrounded_counts_and_half_up(self):
        originals = deepcopy(self.originals)
        q = json.loads(originals[checker.INPUTS[0]])
        for r in q["results"]:
            if r["filters"] == {"cAd31": "XdTUf", "5cGdi": "5kyxd"}:
                if r["timePeriod"]["period"] in ("2015/2016", "2025/2026"):
                    r["values"] = {"EAicq": "1000",
                                   "QtxWw": "26740" if r["timePeriod"]["period"] == "2015/2016" else "26260",
                                   "Wc9V2": "26.740000" if r["timePeriod"]["period"] == "2015/2016" else "26.260000"}
        originals[checker.INPUTS[0]] = json.dumps(q).encode()
        with patch.object(producer, "sources", return_value=(originals, self.evidence)):
            candidate = producer.project(ROOT)
        self.assertEqual(candidate["comparisons"][0]["display"], "-0.5")
        self.assertEqual(self.check(candidate, originals), 176)
        self.assertNotEqual(Decimal("26.3") - Decimal("26.7"), Decimal("-0.5"))
        for raw, expected in (("1.25", "1.3"), ("-1.25", "-1.3"), ("0.05", "+0.1"), ("-0.05", "-0.1")):
            signed = raw in ("0.05", "-0.05")
            self.assertEqual(producer.rounded(Decimal(raw), signed=signed), expected)
            self.assertEqual(checker.display(Decimal(raw), signed=signed), expected)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data/life").mkdir(parents=True)
        shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
        shutil.copytree(ROOT / checker.DIRECTORY, self.root / checker.DIRECTORY)

    def update_register(self, name, mutate):
        path = self.root / checker.REGISTER
        register = json.loads(path.read_bytes())
        entry = next(e for e in register["sources"] if e["path"].endswith("/" + name))
        mutate(entry)
        path.write_text(json.dumps(register), encoding="utf-8")
        return checker.digest(path.read_bytes())

    def test_raw_and_envelope_whitespace_changes_fail(self):
        for name in checker.INPUTS:
            with self.subTest(name=name):
                path = self.root / checker.DIRECTORY / name
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "hash/length mismatch"):
                    checker.validate(self.root, {})
                with self.assertRaises(ValueError):
                    producer.project(self.root)
                path.write_bytes(original)

    def test_recovered_hash_checked_after_rehashed_envelope(self):
        name = checker.INPUTS[2]
        path = self.root / checker.DIRECTORY / name
        envelope = json.loads(path.read_bytes())
        envelope["original_response"] += " "
        path.write_text(json.dumps(envelope), encoding="utf-8")
        pin = self.update_register(name, lambda e: e.update(
            stored_bytes=path.stat().st_size, stored_sha256=checker.digest(path.read_bytes())))
        with self.assertRaisesRegex(ValueError, "Pinned school register"):
            checker.validate(self.root, {})
        # Isolate recovered original checking after the stored-byte gate agrees.
        with patch.object(checker, "REGISTER_SHA256", pin):
            with self.assertRaisesRegex(ValueError, "recovered original hash/length mismatch"):
                checker.validate(self.root, {})

    def test_exact_envelope_encoding_and_key_set(self):
        name = checker.INPUTS[2]
        path = self.root / checker.DIRECTORY / name
        original = path.read_bytes()
        for field, value in (("encoding", "ascii"), ("extra", "field"), ("original_response", 0)):
            with self.subTest(field=field):
                envelope = json.loads(original)
                envelope[field] = value
                path.write_text(json.dumps(envelope), encoding="utf-8")
                pin = self.update_register(name, lambda e: e.update(
                    stored_bytes=path.stat().st_size, stored_sha256=checker.digest(path.read_bytes())))
                with patch.object(checker, "REGISTER_SHA256", pin):
                    with self.assertRaisesRegex(ValueError, "envelope encoding/keys"):
                        checker.validate(self.root, {})
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
        path.write_bytes(original)

    def test_manifest_hash_urls_and_closed_paths(self):
        name = checker.INPUTS[0]
        for change in (
                lambda e: e.__setitem__("url", e["url"].replace("dataSetVersion=1.0", "dataSetVersion=2.0")),
                lambda e: e.__setitem__("url", e["url"].replace("NAT", "LA")),
                lambda e: e.__setitem__("path", "../outside.json"),
                lambda e: e.__setitem__("path", "/tmp/outside.json")):
            with self.subTest(change=repr(change)):
                pin = self.update_register(name, change)
                with self.assertRaisesRegex(ValueError, "Pinned school register"):
                    checker.validate(self.root, {})
                with patch.object(checker, "REGISTER_SHA256", pin):
                    with self.assertRaises(ValueError):
                        checker.validate(self.root, {})
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)

    def test_duplicate_and_missing_manifest_entries(self):
        path = self.root / checker.REGISTER
        original = path.read_bytes()
        for duplicate in (True, False):
            register = json.loads(original)
            if duplicate:
                register["sources"][0] = deepcopy(register["sources"][1])
            else:
                register["sources"].pop()
            path.write_text(json.dumps(register), encoding="utf-8")
            with patch.object(checker, "REGISTER_SHA256", checker.digest(path.read_bytes())):
                with self.assertRaisesRegex(ValueError, "closed source path"):
                    checker.validate(self.root, {})

    def test_source_and_parent_symlinks_and_extra_input_rejected(self):
        path = self.root / checker.DIRECTORY / checker.INPUTS[0]
        outside = self.root / "original.json"
        path.rename(outside)
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            checker.validate(self.root, {})
        with self.assertRaises(ValueError):
            producer.project(self.root)
        path.unlink()
        outside.rename(path)
        extra = path.with_name("extra.json")
        extra.write_text("{}")
        with self.assertRaisesRegex(ValueError, "directory set"):
            checker.validate(self.root, {})
        extra.unlink()
        directory = self.root / checker.DIRECTORY
        moved = directory.with_name("moved")
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            checker.validate(self.root, {})

    def test_safe_json_and_path_parsers(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
                    '{"encoding":"utf-8","encoding":"ascii","original_response":""}'):
            for reader in (checker.decode, producer.strict_json):
                with self.subTest(raw=raw, reader=reader.__name__):
                    with self.assertRaises(ValueError):
                        reader(raw)
        for name in ("../outside", "/tmp/outside"):
            with self.assertRaises(ValueError):
                checker.read(self.root, name)
            with self.assertRaises(ValueError):
                producer.safe_path(self.root, name)

    def test_verify_requires_independent_school_gate(self):
        import verify
        with patch.object(verify, "validate_audit"), patch.object(verify, "validate_receipt_audit"), patch.object(verify, "validate_payer_sources"):
            with patch.object(verify, "validate_schools", side_effect=ValueError("school gate failed")) as gate:
                with self.assertRaisesRegex(ValueError, "school gate failed"):
                    verify.main()
                gate.assert_called_once_with()

    def test_public_paths_stay_exactly_ten_and_reject_private_sources(self):
        self.assertEqual(PUBLIC_FILES, {
            "index.html", "methods.html", "icon.svg", "data/spending.json",
            "taxes.html", "data/taxes.json", "who-pays.html", "data/payers.json",
            "life.html", "data/life.json"})
        output = self.root / "public"
        for name in ("data/life/school-sources.json", "data/life/schools.json",
                     "data/undeclared-life.json", checker.DIRECTORY + "/" + checker.INPUTS[0]):
            with self.subTest(path=name):
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private")
                with self.assertRaisesRegex(ValueError, "unexpected file"):
                    validate_output(output)
                shutil.rmtree(output)


if __name__ == "__main__":
    unittest.main()
