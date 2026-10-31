"""Focused negative fixtures for the private whole-source work-data foundation."""
from contextlib import ExitStack
from copy import deepcopy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_work_data as checker
import work_data_projection as producer
from build import PUBLIC_FILES, validate_output


class WorkDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals, cls.evidence = checker.reopen(ROOT)
        cls.projection = producer.project(ROOT)

    def check(self, candidate=None, originals=None):
        # This seam bypasses custody only to challenge semantics below the hash
        # gate. Production validate() always reopens the complete pinned bytes.
        with patch.object(checker, "reopen", return_value=(
                self.originals if originals is None else originals, self.evidence)):
            return checker.validate(ROOT, self.projection if candidate is None else candidate)

    def test_complete_deterministic_projection_and_independent_reopen(self):
        self.assertEqual(checker.validate(ROOT), 960)
        self.assertEqual(self.check(), 960)
        self.assertEqual(producer.project(ROOT), self.projection)
        self.assertEqual(len(self.evidence), 20)
        self.assertEqual(sum(map(len, self.originals.values())), 690629)
        self.assertEqual(sum(e.get("stored_bytes", e["bytes"]) for e in self.evidence.values()), 749071)
        self.assertEqual([len(d["rows"]) for d in self.projection["datasets"]], [660, 300])
        self.assertEqual([len(d["catalogues"]["time"]["selected"])
                          for d in self.projection["datasets"]], [11, 5])
        self.assertEqual(self.projection["datasets"][0]["rows"][0]["value"], 29079700)
        self.assertEqual(self.projection["datasets"][1]["rows"][0]["value"], 32130300)
        with patch.object(producer, "project", side_effect=AssertionError("producer oracle")), \
                patch.object(producer, "sources", side_effect=AssertionError("producer reader")):
            self.assertEqual(checker.validate(ROOT, self.projection), 960)

    def test_exact_rows_context_and_provenance_reject_mutation(self):
        for dataset in (0, 1):
            for field, value in (
                    ("DATE", "2026-06"), ("DATE_NAME", "Jan 2026-Dec 2026"),
                    ("GEOGRAPHY_CODE", "K03000001"), ("GEOGRAPHY_NAME", "Great Britain"),
                    ("JTYPE_NAME", "Permanent"), ("FTPT_NAME", "Full-time"),
                    ("ETYPE_NAME", "Employee"), ("C_SEX_NAME", "Males"),
                    ("MEASURE_NAME", "Rate"), ("MEASURES_NAME", "value"),
                    ("OBS_VALUE", ""), ("OBS_VALUE", "0"), ("OBS_STATUS", "F"),
                    ("OBS_STATUS_NAME", "Forecast"), ("OBS_CONF", "C"),
                    ("OBS_CONF_NAME", "Suppressed"), ("RECORD_COUNT", "0")):
                with self.subTest(dataset=dataset, field=field, value=value):
                    candidate = deepcopy(self.projection)
                    candidate["datasets"][dataset]["rows"][0]["fields"][field] = value
                    with self.assertRaises(ValueError):
                        self.check(candidate)
            for field, value in (("value", 0), ("value", 29.1), ("line", 1),
                                 ("line", True), ("value", float("nan"))):
                candidate = deepcopy(self.projection)
                candidate["datasets"][dataset]["rows"][0][field] = value
                with self.subTest(dataset=dataset, field=field), self.assertRaises(ValueError):
                    self.check(candidate)
            for field in ("JTYPE", "FTPT", "ETYPE", "C_SEX", "MEASURE", "MEASURES"):
                candidate = deepcopy(self.projection)
                candidate["datasets"][dataset]["rows"][0]["codes"][field] = -1
                with self.subTest(dataset=dataset, code=field), self.assertRaises(ValueError):
                    self.check(candidate)
            for field, value in (("path", "../outside.csv"), ("url", "https://example.org/"),
                                 ("sha256", "0" * 64)):
                candidate = deepcopy(self.projection)
                candidate["datasets"][dataset]["source"][field] = value
                with self.subTest(dataset=dataset, source=field), self.assertRaises(ValueError):
                    self.check(candidate)
        for change in (
                lambda p: p["datasets"][0]["rows"].pop(),
                lambda p: p["datasets"][0]["rows"].append(deepcopy(p["datasets"][0]["rows"][0])),
                lambda p: p["datasets"][0].__setitem__("classification", "SOC2020"),
                lambda p: p["datasets"][0]["catalogues"]["occupation"]["selected"][1]
                    ["description"].__setitem__("value", "1 : Managers, Directors And Senior Official"),
                lambda p: p["datasets"][1]["catalogues"]["occupation"].__setitem__(
                    "source", deepcopy(p["datasets"][0]["catalogues"]["occupation"]["source"])),
                lambda p: p["datasets"][1]["rows"][0].__setitem__("forecast", False)):
            with self.subTest(change=repr(change)):
                candidate = deepcopy(self.projection)
                change(candidate)
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def test_interpretations_and_scope_are_closed(self):
        mutations = [
            lambda p: p.__setitem__("private", False),
            lambda p: p.__setitem__("schema_version", True),
            lambda p: p.__setitem__("status", "SATISFIED"),
            lambda p: p["scope"].__setitem__("unit", "thousands"),
            lambda p: p["scope"]["geography"].__setitem__("name", "Great Britain"),
            lambda p: p["scope"].__setitem__("population_contract", "Employee jobs on adult rates."),
            lambda p: p["scope"].__setitem__("confidence_20701", "95% half-width"),
            lambda p: p["scope"].__setitem__("suppression_definition", "Confidence"),
            lambda p: p["scope"].__setitem__("indicative_definition", "Suppressed zero"),
            lambda p: p["scope"].__setitem__("denominator", "Nine exhaustive occupation groups"),
            lambda p: p["scope"]["formulas"].append("APS people / ASHE employee jobs"),
            lambda p: p["scope"]["formulas"].append("2021 SOC2020 - 2021 SOC2010"),
            lambda p: p["scope"]["formulas"].append("(2020 + 2022) / 2"),
            lambda p: p["scope"].__setitem__("quality_cross_check", "Exact headcounts without limitations."),
            lambda p: p["scope"]["revision_limits"].clear(),
            lambda p: p["scope"]["required_later_ui_notes"].clear(),
            lambda p: p["scope"]["revision_limits"].__setitem__(2, "NI adjustment starts October 2020."),
            lambda p: p["scope"].__setitem__("comparisons", "SOC alone caused the overlap difference."),
            lambda p: p.__setitem__("notes", "All corrections and weighting vintages known."),
            lambda p: p.__setitem__("styles", {"forecast": "observed"}),
            lambda p: p.__setitem__("extra", float("inf"))]
        for change in mutations:
            with self.subTest(change=repr(change)):
                candidate = deepcopy(self.projection)
                change(candidate)
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def test_literal_metadata_and_conflicting_annotations_survive(self):
        for dataset, period, title, value in (
                (0, "2019-12", "end period", "2010-12-01"),
                (1, "2025-12", "start period", "2025-09-01")):
            selected = self.projection["datasets"][dataset]["catalogues"]["time"]["selected"]
            code = next(c for c in selected if c["value"] == period)
            self.assertEqual(checker.annotations(code)[title], value)
            candidate = deepcopy(self.projection)
            item = next(c for c in candidate["datasets"][dataset]["catalogues"]["time"]["selected"]
                        if c["value"] == period)
            next(a for a in item["annotations"]["annotation"]
                 if a["annotationtitle"] == title)["annotationtext"] = "repaired"
            with self.assertRaises(ValueError):
                self.check(candidate)
        first = self.projection["datasets"][0]["catalogues"]["time"]["selected"][0]
        self.assertNotIn("annotations", first)
        for dataset in (0, 1):
            measures = self.projection["datasets"][dataset]["catalogues"]["measures"]["selected"]
            self.assertEqual([c["description"]["value"] for c in measures], ["value", "confidence"])
            self.assertEqual([checker.annotations(c)["Description"] for c in measures], ["Value", "Confidence"])
            for change in ("dropped", "relabelled"):
                candidate = deepcopy(self.projection)
                code = candidate["datasets"][dataset]["catalogues"]["measures"]["selected"][1]
                if change == "dropped":
                    code["annotations"]["annotation"].clear()
                else:
                    code["description"]["value"] = "95% confidence interval"
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def csv_mutation(self, number, change):
        originals = dict(self.originals)
        name = f"aps{number}-uk-calendar-annual.csv"
        table = list(csv.reader(io.StringIO(originals[name].decode("utf-8"))))
        change(table)
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerows(table)
        originals[name] = stream.getvalue().encode("utf-8")
        return originals

    def project_changed_originals(self, originals):
        with patch.object(producer, "sources", return_value=(originals, self.evidence)):
            return producer.project(ROOT)

    def test_semantic_grid_context_and_missing_fail_below_custody(self):
        # Both producer and checker see the modified raw bytes. Matching a
        # corrupted projection to itself must not bypass domain assertions.
        for number in (210, 218):
            mutations = [
                lambda t: t.pop(),
                lambda t: t.append(t[1][:]),
                lambda t: t.__setitem__(2, t[1][:]),
                lambda t: t[1].__setitem__(0, "2026-06"),
                lambda t: t[1].__setitem__(1, "Jul 2010-Jun 2011"),
                lambda t: t[1].__setitem__(2, "K03000001"),
                lambda t: t[1].__setitem__(3, "Great Britain"),
                lambda t: t[1].__setitem__(9, "Approximate occupation name"),
                lambda t: t[1].__setitem__(13, "F"),
                lambda t: t[1].__setitem__(14, "Forecast"),
                lambda t: t[1].__setitem__(15, "C"),
                lambda t: t[1].__setitem__(16, "Confidential"),
                lambda t: t[1].__setitem__(17, "0")]
            for change in mutations:
                with self.subTest(number=number, change=repr(change)):
                    originals = self.csv_mutation(number, change)
                    candidate = self.project_changed_originals(originals)
                    with self.assertRaises(ValueError):
                        self.check(candidate, originals)
            for invalid in ("", "NaN", "Infinity", "1e6", "1.5", "-1", "1,000"):
                originals = self.csv_mutation(number, lambda t: t[1].__setitem__(12, invalid))
                with self.subTest(number=number, value=invalid):
                    with self.assertRaises(ValueError):
                        self.project_changed_originals(originals)
                    with self.assertRaises(ValueError):
                        self.check(originals=originals)
            for column, invalid in ((4, "Permanent"), (5, "Part-time"), (6, "Employee"),
                                    (7, "People"), (10, "Rate"), (11, "confidence")):
                originals = self.csv_mutation(number, lambda t: t[1].__setitem__(column, invalid))
                with self.subTest(number=number, column=column):
                    with self.assertRaises(ValueError):
                        self.project_changed_originals(originals)
                    with self.assertRaises(ValueError):
                        self.check(originals=originals)

    def test_raw_catalogues_not_producer_metadata_are_the_oracle(self):
        mutations = [
            ("aps210-definition.json.json", lambda j: j["structure"]["keyfamilies"]["keyfamily"][0]
             ["annotations"]["annotation"][1].__setitem__("annotationtext", "Thousands")),
        ]
        # Complete originals remain test fixtures in memory, never edited on disk.
        for name, change in mutations:
            originals = dict(self.originals)
            doc = json.loads(originals[name])
            change(doc)
            originals[name] = json.dumps(doc).encode()
            candidate = self.project_changed_originals(originals)
            with self.assertRaises(ValueError):
                self.check(candidate, originals)
        for number in (210, 218):
            name = f"aps{number}-time.json.json"
            originals = dict(self.originals)
            doc = json.loads(originals[name])
            codes = doc["structure"]["codelists"]["codelist"][0]["code"]
            codes.remove(next(c for c in codes if not c["value"].endswith("-12")))
            # Unselected rolling metadata still belongs to the whole catalogue.
            originals[name] = json.dumps(doc).encode()
            candidate = self.project_changed_originals(originals)
            with self.assertRaises(ValueError):
                self.check(candidate, originals)
            name = f"aps{number}-occupation.json.json"
            originals = dict(self.originals)
            doc = json.loads(originals[name])
            doc["structure"]["codelists"]["codelist"][0]["code"].append(
                deepcopy(doc["structure"]["codelists"]["codelist"][0]["code"][0]))
            originals[name] = json.dumps(doc).encode()
            with self.assertRaises(ValueError):
                self.check(originals=originals)
            with self.assertRaises(ValueError):
                self.project_changed_originals(originals)

    def test_projection_instances_have_no_shared_mutable_scope(self):
        first = producer.project(ROOT)
        first["scope"]["revision_limits"].clear()
        first["datasets"][0]["catalogues"]["time"]["selected"].clear()
        self.assertEqual(checker.validate(ROOT), 960)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data/life").mkdir(parents=True)
        shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
        shutil.copytree(ROOT / checker.DIRECTORY, self.root / checker.DIRECTORY)

    def both_reject(self):
        for reader in (checker.reopen, producer.sources):
            with self.subTest(reader=reader.__module__), self.assertRaises(ValueError):
                reader(self.root)

    def update_register(self, change):
        path = self.root / checker.REGISTER
        register = json.loads(path.read_bytes())
        change(register)
        path.write_text(json.dumps(register), encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def pin_register(self, pin):
        stack = ExitStack()
        stack.enter_context(patch.object(checker, "REGISTER_SHA256", pin))
        stack.enter_context(patch.object(producer, "REGISTER_SHA256", pin))
        return stack

    def test_all_original_and_stored_hashes_are_checked(self):
        for name in producer.FILES:
            path = self.root / checker.DIRECTORY / name
            raw = path.read_bytes()
            path.write_bytes(raw + b" ")
            self.both_reject()
            path.write_bytes(raw)
        for field, value in (("stored_bytes", 0), ("stored_sha256", "0" * 64),
                             ("bytes", 0), ("sha256", "0" * 64)):
            shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
            pin = self.update_register(lambda r: r["sources"][2].__setitem__(field, value))
            with self.subTest(field=field), self.pin_register(pin):
                self.both_reject()

    def test_envelope_recovery_after_rehashed_storage(self):
        name = "aps210-definition.json.json"
        path = self.root / checker.DIRECTORY / name
        envelope = json.loads(path.read_bytes())
        for change in (
                lambda e: e.__setitem__("encoding", "ascii"),
                lambda e: e.__setitem__("original_response", 0),
                lambda e: e.__setitem__("extra", "ignored"),
                lambda e: e.__setitem__("original_response", e["original_response"] + " ")):
            shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
            changed = deepcopy(envelope)
            change(changed)
            path.write_text(json.dumps(changed), encoding="utf-8")
            def rehash(register):
                entry = next(e for e in register["sources"] if e["path"].endswith("/" + name))
                entry.update(stored_bytes=len(path.read_bytes()),
                             stored_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            pin = self.update_register(rehash)
            with self.pin_register(pin):
                self.both_reject()

    def test_closed_source_register_and_directory(self):
        for change in (
                lambda r: r["sources"].pop(),
                lambda r: r["sources"].append(deepcopy(r["sources"][0])),
                lambda r: r["sources"][0].__setitem__("path", "../outside.csv"),
                lambda r: r["sources"][0].__setitem__("path", "/tmp/outside.csv"),
                lambda r: r["sources"][0].__setitem__("path", checker.DIRECTORY + "/../outside.csv"),
                lambda r: r["sources"][0].__setitem__("url", "https://example.org/"),
                lambda r: r["sources"][0].__setitem__("retrieval", "Exact wire receipt proved.")):
            shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
            self.update_register(change)
            self.both_reject()
        shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
        directory = self.root / checker.DIRECTORY
        extra = directory / "unregistered.json"
        extra.write_text("{}")
        self.both_reject()
        extra.unlink()
        path = directory / producer.FILES[0]
        path.unlink()
        self.both_reject()

    def test_unsafe_files_links_and_paths(self):
        path = self.root / checker.DIRECTORY / producer.FILES[0]
        outside = self.root / "retained.csv"
        path.rename(outside)
        path.symlink_to(outside)
        self.both_reject()
        path.unlink()
        path.mkdir()
        self.both_reject()
        path.rmdir()
        outside.rename(path)
        os.link(path, self.root / "alias.csv")
        self.both_reject()
        (self.root / "alias.csv").unlink()
        directory = self.root / checker.DIRECTORY
        moved = directory.with_name("moved")
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.both_reject()
        for relative in ("", "../outside", "/tmp/outside", "data//life/a", "data/./life/a"):
            for reader in (checker.read, producer.read):
                with self.subTest(relative=relative, reader=reader.__module__), self.assertRaises(ValueError):
                    reader(self.root, relative)

    def test_duplicate_and_nonfinite_json_rejected_by_both_readers(self):
        for raw in ('{"x":1,"x":2}', '{"x":{"y":1,"y":2}}', '{"x":NaN}',
                    '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}'):
            for decoder in (checker.decode, producer.strict_json):
                with self.subTest(raw=raw, decoder=decoder.__module__), self.assertRaises(ValueError):
                    decoder(raw)

    def test_no_derived_files_or_public_activation(self):
        def snapshot():
            return {p.relative_to(self.root).as_posix(): p.read_bytes()
                    for p in self.root.rglob("*") if p.is_file()}
        before = snapshot()
        projection = producer.project(self.root)
        self.assertEqual(checker.validate(self.root, projection), 960)
        self.assertEqual(before, snapshot())
        self.assertEqual(PUBLIC_FILES, {
            "index.html", "methods.html", "icon.svg", "data/spending.json",
            "taxes.html", "data/taxes.json", "who-pays.html", "data/payers.json"})
        output = self.root / "public"
        for name in ("life.html", "data/life.json", checker.REGISTER,
                     checker.DIRECTORY + "/" + producer.FILES[0]):
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("private")
            with self.assertRaisesRegex(ValueError, "unexpected file"):
                validate_output(output)
            shutil.rmtree(output)

    def test_verify_stops_at_work_data_gate(self):
        import verify
        with ExitStack() as stack:
            for name in ("validate_audit", "validate_receipt_audit", "validate_payer_sources",
                         "validate_schools", "validate_holiday_methods", "validate_work_methods"):
                stack.enter_context(patch.object(verify, name))
            downstream = stack.enter_context(patch.object(verify, "validate_receipts"))
            gate = stack.enter_context(patch.object(
                verify, "validate_work_data", side_effect=ValueError("work data gate failed")))
            with self.assertRaisesRegex(ValueError, "work data gate failed"):
                verify.main()
            gate.assert_called_once_with()
            downstream.assert_not_called()


if __name__ == "__main__":
    unittest.main()
