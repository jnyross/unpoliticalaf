"""Negative fixtures for the private whole-source work-method foundation."""
from contextlib import ExitStack
from copy import deepcopy
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
import check_work_methods as checker
import work_methods_projection as producer
from build import PUBLIC_FILES, validate_output


class MethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals, cls.evidence = checker.reopen(ROOT)
        cls.projection = producer.project(ROOT)

    def check(self, projection=None, originals=None):
        return checker.check(
            self.projection if projection is None else projection,
            self.originals if originals is None else originals, self.evidence)

    def record(self, candidate, identity):
        return next(r for r in candidate["records"] if r["id"] == identity)

    def test_whole_originals_and_independent_memory_only_projection(self):
        self.assertEqual(checker.validate(ROOT), 31)
        self.assertEqual(self.check(), 31)
        self.assertEqual(self.projection, producer.project(ROOT))
        self.assertEqual(self.projection["observations"], [])
        self.assertEqual(len(self.projection["sources"]), 6)
        # These are custody totals, not candidate review payload measurements.
        self.assertEqual(sum(map(len, self.originals.values())), 413349)
        self.assertEqual(sum(e["stored_bytes"] for e in self.evidence.values()), 445383)
        with patch.object(producer, "sources", side_effect=AssertionError("producer reader called")), \
                patch.object(producer, "project", side_effect=AssertionError("producer oracle called")):
            self.assertEqual(checker.validate(ROOT, self.projection), 31)

    def test_scope_notes_status_and_fabrication_are_closed(self):
        mutations = {
            "employee-only population": lambda p: p["scope"].__setitem__("population", "Employees aged 16+."),
            "exact headcounts": lambda p: p["scope"].__setitem__("measure", "Exact employee job headcounts."),
            "rolling calendar": lambda p: p["scope"].__setitem__("periods", "Jul 2025-Jun 2026 is calendar 2026."),
            "warnings erased": lambda p: p["scope"].__setitem__("quality", "No limitations."),
            "guessed Confidence20701": lambda p: p["scope"].__setitem__("confidence", "Confidence 20701 is a 95% half-width."),
            "confidence definition guessed": lambda p: p["scope"]["quality_definitions"].__setitem__("confidence_20701", "95% half-width"),
            "suppression conflated": lambda p: p["scope"]["quality_definitions"].__setitem__("suppression", "Confidence 20701"),
            "indicative conflated": lambda p: p["scope"]["quality_definitions"].__setitem__("indicative", "Suppressed zero"),
            "ASHE population erased": lambda p: p["scope"]["unverified"].__setitem__(1, "APS and ASHE have equivalent populations."),
            "complete revision audit": lambda p: p["scope"]["revision_limits"].clear(),
            "unverified erased": lambda p: p["scope"]["unverified"].clear(),
            "pending notes erased": lambda p: p["scope"]["frozen_contract_pending_notes"].clear(),
            "Wales correction proved": lambda p: p["scope"]["frozen_contract_pending_notes"].__setitem__(1, "All affected 2020 counts were corrected."),
            "SOC-only cause": lambda p: p["scope"]["revision_limits"].__setitem__(2, "All 2021 overlap differences are caused by SOC alone."),
            "notes extra": lambda p: p.__setitem__("notes", "All source limitations resolved."),
            "acceptance": lambda p: p.__setitem__("status", "SATISFIED"),
            "numeric observations": lambda p: p["observations"].append({"year": 2021, "value": 100}),
            "missing to zero": lambda p: p["observations"].append({"year": 2020, "value": 0}),
            "forecast observed": lambda p: p["observations"].append({"year": 2027, "status": "observed"}),
            "ratio": lambda p: p.__setitem__("formula", "APS people / ASHE employee jobs"),
            "interpolation": lambda p: p.__setitem__("formula", "(2020 + 2022) / 2"),
            "bool schema": lambda p: p.__setitem__("schema_version", True),
            "public": lambda p: p.__setitem__("private", False),
            "NaN": lambda p: p.__setitem__("extra", float("nan")),
        }
        for label, change in mutations.items():
            with self.subTest(label=label):
                candidate = deepcopy(self.projection)
                change(candidate)
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def test_record_set_and_exact_provenance_are_closed(self):
        for field, value in (
                ("id", "invented"), ("quote", "All people are employees."),
                ("applies_to", "all-vintages")):
            with self.subTest(field=field):
                candidate = deepcopy(self.projection)
                candidate["records"][0][field] = value
                with self.assertRaises(ValueError):
                    self.check(candidate)
        for field, value in (
                ("path", "../outside.json"), ("url", "https://example.org/"),
                ("sha256", "0" * 64), ("anchor", "wrong-section"),
                ("heading", "Unrelated heading"), ("tag", "div")):
            with self.subTest(source_field=field):
                candidate = deepcopy(self.projection)
                candidate["records"][0]["source"][field] = value
                with self.assertRaises(ValueError):
                    self.check(candidate)
        for duplicate in (False, True):
            candidate = deepcopy(self.projection)
            if duplicate:
                candidate["records"].append(deepcopy(candidate["records"][0]))
            else:
                candidate["records"].pop()
            with self.assertRaises(ValueError):
                self.check(candidate)
        candidate = deepcopy(self.projection)
        candidate["sources"][checker.INPUTS[0]]["returned_body"] = "Exact compressed wire bytes"
        with self.assertRaises(ValueError):
            self.check(candidate)

    def test_aps_and_lfs_periods_cannot_be_interchanged(self):
        candidate = deepcopy(self.projection)
        self.record(candidate, "notice2023-aps-range")["applies_to"] = "lfs-coding-paper-2023"
        with self.assertRaises(ValueError):
            self.check(candidate)
        candidate = deepcopy(self.projection)
        self.record(candidate, "coding-lfs-title-range")["applies_to"] = "aps-2023-notice"
        with self.assertRaises(ValueError):
            self.check(candidate)

    def test_original_semantics_beneath_the_custody_gate(self):
        # Only custody is bypassed: the independent exact semantic assertions
        # and the frozen projection stay unchanged.
        changes = [
            (0, "6 February 2026", "6 February 2025"),
            (0, "survey covering the UK", "survey covering Great Britain"),
            (0, "official statistics in development", "accredited official statistics"),
            (0, "except for NHS housing", "including all NHS housing"),
            (0, "students in boarding schools and halls of residence", "no students in halls of residence"),
            (0, "only included if they live in private accommodation", "included in all accommodation"),
            (0, "Workers aged under 16 years are not included", "Workers aged under 16 years are included"),
            (0, "aged 16 years or over", "aged 18 years or over"),
            (0, "whether as an employee or self-employed", "only as an employee"),
            (0, "temporarily away from", "permanently separated from"),
            (0, "government-supported training and employment programmes", "unpaid volunteering programmes"),
            (0, "are doing unpaid family work", "are not doing unpaid family work"),
            (0, "rather than exact measures", "as exact measures"),
            (0, 'id="quality-characteristics-of-the-data"', 'id="unrelated-quality-section"'),
            (1, "slowly decreasing over time", "steadily increasing over time"),
            (1, "use caution when analysing results", "assume certainty when analysing results"),
            (1, "avoid assuming that small differences", "assume that small differences"),
            (1, "APS datasets have not been updated since their 2022-based weights", "APS datasets have been updated to 2024-based weights"),
            (1, "are not fully consistent with current population statistics", "are fully consistent with current population statistics"),
            (1, "may have affected the quality of LFS and APS results", "did not affect the quality of LFS and APS results"),
            (2, "16 August 2022", "16 August 2021"),
            (2, "October 2020 to September 2021 onwards", "October 2021 to September 2022 onwards"),
            (2, "Real Time Information (RTI) data", "occupation classification data"),
            (2, "applied to Northern Ireland data", "not applied to Northern Ireland data"),
            (2, "largely unaffected", "entirely unaffected"),
            (2, "Apr 2019-Mar 2020 to Jul 2020-Jun 2021", "Apr 2020-Mar 2021 to Jul 2021-Jun 2022"),
            (2, "are not affected", "are affected"),
            (3, "15 August 2023", "15 August 2022"),
            (3, "Apr 2020 - Mar 2021 period", "January 2021 to September 2022 period"),
            (4, "<p>United Kingdom</p>", "<p>Great Britain</p>"),
            (4, "<p>Persons</p>", "<p>Employee jobs</p>"),
            (5, "January 2021 to September 2022", "April 2020 to March 2021"),
            (5, "main jobs for LFS from January to March 2021", "main jobs for APS from January to March 2021"),
            (5, "October 2022 is therefore not affected", "October 2022 is therefore affected"),
        ]
        for index, before, after in changes:
            with self.subTest(before=before):
                name = checker.INPUTS[index]
                originals = dict(self.originals)
                self.assertIn(before.encode(), originals[name])
                originals[name] = originals[name].replace(before.encode(), after.encode())
                with self.assertRaises(ValueError):
                    self.check(originals=originals)

    def test_normalisation_preserves_html_meaning(self):
        originals = dict(self.originals)
        name = checker.INPUTS[0]
        originals[name] = originals[name].replace(b"self-employed", b"self&#45;employed")
        originals[name] = originals[name].replace(b"unpaid family work", b"unpaid \n family work")
        self.assertEqual(self.check(originals=originals), 31)
        self.assertNotEqual(originals[name], self.originals[name])

    def test_projection_instances_have_no_shared_mutable_scope(self):
        first = producer.project(ROOT)
        first["scope"]["revision_limits"].clear()
        first["scope"]["frozen_contract_pending_notes"].clear()
        self.assertEqual(checker.validate(ROOT), 31)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data/life").mkdir(parents=True)
        shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
        shutil.copytree(ROOT / checker.DIRECTORY, self.root / checker.DIRECTORY)

    def update_register(self, change):
        path = self.root / checker.REGISTER
        register = json.loads(path.read_bytes())
        change(register)
        path.write_text(json.dumps(register), encoding="utf-8")
        return checker.digest(path.read_bytes())

    def assert_both_reject(self):
        for reader in (checker.reopen, producer.sources):
            with self.subTest(reader=reader.__module__):
                with self.assertRaises(ValueError):
                    reader(self.root)

    def pinned_register(self, pin):
        stack = ExitStack()
        stack.enter_context(patch.object(checker, "REGISTER_SHA256", pin))
        stack.enter_context(patch.object(producer, "REGISTER_SHA256", pin))
        return stack

    def test_stored_bytes_and_original_custody_for_both_readers(self):
        for name in checker.INPUTS:
            path = self.root / checker.DIRECTORY / name
            raw = path.read_bytes()
            for changed in (raw + b" ", raw.replace(b"original_response", b"changed_response", 1)):
                with self.subTest(name=name, mutation=changed[-1:]):
                    path.write_bytes(changed)
                    self.assert_both_reject()
            path.write_bytes(raw)

    def test_each_manifest_hash_and_length_is_required(self):
        for field, value in (
                ("stored_bytes", 0), ("stored_sha256", "0" * 64),
                ("bytes", 0), ("sha256", "0" * 64)):
            with self.subTest(field=field):
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
                pin = self.update_register(lambda r: r["sources"][0].__setitem__(field, value))
                with self.pinned_register(pin):
                    self.assert_both_reject()

    def test_original_bytes_and_envelope_shape_after_rehashed_storage(self):
        name = checker.INPUTS[0]
        path = self.root / checker.DIRECTORY / name
        original = json.loads(path.read_bytes())
        for label in ("original", "encoding", "extra", "type"):
            with self.subTest(label=label):
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
                envelope = deepcopy(original)
                if label == "original":
                    envelope["original_response"] += " "
                elif label == "encoding":
                    envelope["encoding"] = "ascii"
                elif label == "extra":
                    envelope["extra"] = "ignored"
                else:
                    envelope["original_response"] = 0
                path.write_text(json.dumps(envelope), encoding="utf-8")
                def refresh(register):
                    entry = next(e for e in register["sources"] if e["path"].endswith("/" + name))
                    entry.update(stored_bytes=len(path.read_bytes()), stored_sha256=checker.digest(path.read_bytes()))
                pin = self.update_register(refresh)
                with self.pinned_register(pin):
                    self.assert_both_reject()

    def test_closed_manifest_paths_urls_duplicates_and_missing_sources(self):
        mutations = [
            lambda r: r["sources"][0].__setitem__("path", "../outside.json"),
            lambda r: r["sources"][0].__setitem__("path", "/tmp/outside.json"),
            lambda r: r["sources"][0].__setitem__("path", checker.DIRECTORY + "/../outside.json"),
            lambda r: r["sources"][0].__setitem__("url", checker.URLS[1]),
            lambda r: r["sources"].pop(),
            lambda r: r["sources"].append(deepcopy(r["sources"][0])),
            lambda r: r["sources"].__setitem__(0, deepcopy(r["sources"][1])),
        ]
        for change in mutations:
            with self.subTest(change=repr(change)):
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
                pin = self.update_register(change)
                self.assert_both_reject()
                with self.pinned_register(pin):
                    self.assert_both_reject()

    def test_symlink_nonregular_hardlink_and_extra_source_rejected(self):
        path = self.root / checker.DIRECTORY / checker.INPUTS[0]
        outside = self.root / "original.json"
        path.rename(outside)
        path.symlink_to(outside)
        self.assert_both_reject()
        path.unlink()
        outside.rename(path)
        path.rename(outside)
        path.mkdir()
        self.assert_both_reject()
        path.rmdir()
        outside.rename(path)
        os.link(path, self.root / "linked-original.json")
        self.assert_both_reject()
        (self.root / "linked-original.json").unlink()
        extra = path.with_name("extra.json")
        extra.write_text("{}")
        self.assert_both_reject()
        extra.unlink()
        directory = self.root / checker.DIRECTORY
        moved = directory.with_name("moved")
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.assert_both_reject()

    def test_traversal_and_noncanonical_paths_rejected_before_read(self):
        for relative in ("../outside", "/tmp/outside", "", "data//life/file", "data/./life/file"):
            for reader in (checker.read, producer.read):
                with self.subTest(relative=relative, reader=reader.__module__):
                    with self.assertRaises(ValueError):
                        reader(self.root, relative)

    def test_strict_json_rejects_duplicates_constants_and_overflow(self):
        for raw in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
                    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}'):
            for decoder in (checker.decode, producer.strict_json):
                with self.subTest(raw=raw, decoder=decoder.__module__):
                    with self.assertRaises(ValueError):
                        decoder(raw)

    def test_projection_and_check_do_not_write_derived_files(self):
        def snapshot():
            return {p.relative_to(self.root).as_posix(): p.read_bytes()
                    for p in self.root.rglob("*") if p.is_file()}
        before = snapshot()
        projection = producer.project(self.root)
        self.assertEqual(checker.validate(self.root, projection), 31)
        self.assertEqual(snapshot(), before)

    def test_verify_requires_work_gate_before_build_or_publication_checks(self):
        import verify
        with ExitStack() as stack:
            for name in ("validate_audit", "validate_receipt_audit", "validate_payer_sources",
                         "validate_schools", "validate_holiday_methods"):
                stack.enter_context(patch.object(verify, name))
            downstream = stack.enter_context(patch.object(verify, "validate_receipts"))
            gate = stack.enter_context(patch.object(
                verify, "validate_work_methods", side_effect=ValueError("work gate failed")))
            with self.assertRaisesRegex(ValueError, "work gate failed"):
                verify.main()
            gate.assert_called_once_with()
            downstream.assert_not_called()

    def test_exact_public_allowlist_still_rejects_private_work_inputs(self):
        self.assertEqual(PUBLIC_FILES, {
            "index.html", "methods.html", "icon.svg", "data/spending.json",
            "taxes.html", "data/taxes.json", "who-pays.html", "data/payers.json"})
        output = self.root / "public"
        for name in ("life.html", "data/life.json", "data/life/work-methods.json",
                     checker.REGISTER, checker.DIRECTORY + "/" + checker.INPUTS[0]):
            with self.subTest(name=name):
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private")
                with self.assertRaisesRegex(ValueError, "unexpected file"):
                    validate_output(output)
                shutil.rmtree(output)


if __name__ == "__main__":
    unittest.main()
