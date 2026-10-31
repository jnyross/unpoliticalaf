"""Focused negative fixtures for the private, whole-source methods foundation."""
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
import check_holiday_methods as checker
import holiday_methods_projection as producer
from build import PUBLIC_FILES, validate_output


class MethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals, cls.evidence, cls.quotes = checker.reopen(ROOT)
        cls.projection = producer.project(ROOT)

    def check(self, projection=None, originals=None, quotes=None):
        return checker.check(
            self.projection if projection is None else projection,
            self.originals if originals is None else originals,
            self.evidence, self.quotes if quotes is None else quotes)

    def test_whole_originals_independently_validate_memory_only(self):
        self.assertEqual(checker.validate(ROOT), 20)
        self.assertEqual(self.check(), 20)
        self.assertEqual(self.projection, producer.project(ROOT))
        self.assertEqual(self.projection["observations"], [])
        self.assertEqual(sum(map(len, self.originals.values())), 589144)
        # Source reads do not depend on a producer parser or a saved projection.
        with patch.object(producer, "sources", side_effect=AssertionError("producer reader called")):
            self.assertEqual(checker.validate(ROOT, self.projection), 20)
        self.assertEqual(len(self.projection["sources"]), 4)

    def test_projection_rejects_vintage_semantics_and_fabrication(self):
        mutations = {
            "QMI governs GB": lambda p: p["records"][8].__setitem__("applies_to", "current-GB-methods-2024-2025"),
            "current governs UK history": lambda p: p["records"][0].__setitem__("applies_to", "older-UK-methods"),
            "visitors": lambda p: p["records"][9].__setitem__("quote", "Unique people, not visits."),
            "permission": lambda p: p["records"][6].__setitem__("context", "Users can:"),
            "removed not": lambda p: p["records"][4].__setitem__("quote", p["records"][4]["quote"].replace("do not represent", "represent")),
            "provisional inference": lambda p: p.__setitem__("status", "All 2025 estimates provisional"),
            "workbook cells": lambda p: p["observations"].append({"year": 2025, "value": 58396000}),
            "missing to zero": lambda p: p["observations"].append({"year": 2020, "value": 0}),
            "invented forecast": lambda p: p["observations"].append({"year": 2026, "status": "observed"}),
            "adjusted history": lambda p: p.__setitem__("formula", "historical visits * level shift"),
            "denominator": lambda p: p["scope"].__setitem__("denominator", "households"),
            "domestic": lambda p: p["scope"]["excluded"].remove("Domestic holidays"),
            "2021 observed": lambda p: p["scope"]["series_boundaries"].__setitem__(2, "2021 pure observed annual series"),
            "no gaps": lambda p: p["scope"]["series_boundaries"].clear(),
            "unverified erased": lambda p: p["scope"]["unverified"].clear(),
            "human evidence": lambda p: p.__setitem__("status", "SATISFIED"),
            "quote dropped": lambda p: p["records"].pop(),
            "quote duplicated": lambda p: p["records"].append(deepcopy(p["records"][0])),
            "source hash": lambda p: p["records"][0]["source"].__setitem__("sha256", "0" * 64),
            "heading": lambda p: p["records"][0]["source"].__setitem__("heading", "Unrelated"),
            "anchor": lambda p: p["records"][0]["source"].__setitem__("anchor", "glossary"),
            "URL": lambda p: p["records"][0]["source"].__setitem__("url", "https://example.org"),
            "custody": lambda p: p["sources"][checker.INPUTS[0]].__setitem__("returned_body", "Exact compressed wire bytes"),
            "bool schema": lambda p: p.__setitem__("schema_version", True),
            "nonfinite": lambda p: p.__setitem__("extra", float("nan")),
        }
        for label, change in mutations.items():
            with self.subTest(label=label):
                candidate = deepcopy(self.projection)
                change(candidate)
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def test_raw_semantics_beneath_hash_gate(self):
        # Intentionally bypass only custody to exercise independent semantic
        # locators on modified originals, retaining the frozen quote assertions.
        changes = [
            (0, "terminal-basis", "terminal-total"),
            (0, "UK-level estimates</h3>", "GB-only estimates</h3>"),
            (0, 'id="progress-updates"', 'id="wrong-section"'),
            (0, "do not recommend comparing", "recommend comparing"),
            (0, "They do not represent final", "They represent final"),
            (1, "Users should not:", "Users can:"),
            (1, "our previous International Passenger Survey", "our new International Passenger Survey"),
            (1, 'id="how-these-estimates-can-be-used"', 'id="main-points"'),
            (2, "final travel and tourism estimates for 2019", "preliminary estimates for 2019"),
            (3, "10 May 2023", "10 May 2026"),
            (3, "about 90% of passengers", "all passengers"),
            (3, "each visit", "each person"),
            (3, "16 March 2020 and 18 January 2021", "16 March 2020 and 18 March 2020"),
            (3, "using alternative sources", "using only interviews"),
            (3, "no discontinuities have been identified", "discontinuities have been identified"),
        ]
        for index, before, after in changes:
            with self.subTest(before=before):
                name = checker.INPUTS[index]
                originals = dict(self.originals)
                self.assertIn(before.encode(), originals[name])
                originals[name] = originals[name].replace(before.encode(), after.encode())
                with self.assertRaises(ValueError):
                    self.check(originals=originals)

    def test_quote_hash_binding_checked_independently(self):
        quotes = deepcopy(self.quotes)
        quotes[0]["original_sha256"] = self.evidence[checker.INPUTS[2]]["sha256"]
        with self.assertRaisesRegex(ValueError, "quote original hash"):
            self.check(quotes=quotes)

    def test_semantic_normalisation_does_not_rewrite_sources(self):
        originals = dict(self.originals)
        name = checker.INPUTS[0]
        originals[name] = originals[name].replace(b"terminal-basis", b"terminal&#45;basis")
        originals[name] = originals[name].replace(b"Sampling at airports", b"Sampling \n at airports")
        self.assertEqual(self.check(originals=originals), 20)
        self.assertNotEqual(originals[name], self.originals[name])

    def test_projection_instances_do_not_share_mutable_scope(self):
        first = producer.project(ROOT)
        first["scope"]["excluded"].clear()
        self.assertEqual(checker.validate(ROOT), 20)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data/life").mkdir(parents=True)
        for name in (checker.REGISTER, checker.QUOTES):
            shutil.copy2(ROOT / name, self.root / name)
        shutil.copytree(ROOT / checker.DIRECTORY, self.root / checker.DIRECTORY)

    def update_register(self, change):
        path = self.root / checker.REGISTER
        register = json.loads(path.read_bytes())
        change(register)
        path.write_text(json.dumps(register), encoding="utf-8")
        return checker.digest(path.read_bytes())

    def test_stored_whitespace_and_original_bytes_fail_both_readers(self):
        for name in checker.INPUTS:
            path = self.root / checker.DIRECTORY / name
            raw = path.read_bytes()
            for changed in (raw + b" ", raw.replace(b"original_response", b"changed_response", 1)):
                with self.subTest(name=name, changed=changed[-1:]):
                    path.write_bytes(changed)
                    with self.assertRaisesRegex(ValueError, "stored hash/length"):
                        checker.reopen(self.root)
                    with self.assertRaises(ValueError):
                        producer.project(self.root)
            path.write_bytes(raw)

    def test_original_hash_after_rehashed_envelope_and_exact_encoding(self):
        name = checker.INPUTS[0]
        path = self.root / checker.DIRECTORY / name
        original = json.loads(path.read_bytes())
        for label in ("original", "encoding", "extra", "type"):
            with self.subTest(label=label):
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
                expected = "recovered original hash/length" if label == "original" else "envelope encoding/keys"
                with patch.object(checker, "REGISTER_SHA256", pin), patch.object(producer, "REGISTER_SHA256", pin):
                    with self.assertRaisesRegex(ValueError, expected):
                        checker.reopen(self.root)
                    with self.assertRaisesRegex(ValueError, expected):
                        producer.project(self.root)

    def test_manifest_closed_paths_urls_duplicates_and_missing_sources(self):
        mutations = [
            lambda r: r["sources"][0].__setitem__("path", "../outside.json"),
            lambda r: r["sources"][0].__setitem__("path", "/tmp/outside.json"),
            lambda r: r["sources"][0].__setitem__("url", checker.URLS[1]),
            lambda r: r["sources"].pop(),
            lambda r: r["sources"].__setitem__(0, deepcopy(r["sources"][1])),
        ]
        for change in mutations:
            with self.subTest(change=repr(change)):
                shutil.copy2(ROOT / checker.REGISTER, self.root / checker.REGISTER)
                pin = self.update_register(change)
                with self.assertRaisesRegex(ValueError, "Pinned holiday register"):
                    checker.reopen(self.root)
                with patch.object(checker, "REGISTER_SHA256", pin):
                    with self.assertRaises(ValueError):
                        checker.reopen(self.root)

    def test_symlinks_nonregular_extra_sources_and_unsafe_paths(self):
        path = self.root / checker.DIRECTORY / checker.INPUTS[0]
        outside = self.root / "original.json"
        path.rename(outside)
        path.symlink_to(outside)
        for reader in (checker.reopen, producer.sources):
            with self.assertRaisesRegex(ValueError, "symlinks"):
                reader(self.root)
        path.unlink()
        outside.rename(path)
        path.rename(outside)
        path.mkdir()
        with self.assertRaisesRegex(ValueError, "regular file"):
            checker.reopen(self.root)
        path.rmdir()
        outside.rename(path)
        extra = path.with_name("extra.json")
        extra.write_text("{}")
        with self.assertRaisesRegex(ValueError, "directory set"):
            checker.reopen(self.root)
        extra.unlink()
        directory = self.root / checker.DIRECTORY
        moved = directory.with_name("moved")
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        for reader in (checker.reopen, producer.sources):
            with self.assertRaisesRegex(ValueError, "symlinks"):
                reader(self.root)
        for relative in ("../outside", "/tmp/outside", ""):
            for reader in (checker.read, producer.read):
                with self.assertRaises(ValueError):
                    reader(self.root, relative)

    def test_hard_linked_source_is_rejected(self):
        path = self.root / checker.DIRECTORY / checker.INPUTS[0]
        os.link(path, self.root / "linked-original.json")
        for reader in (checker.reopen, producer.sources):
            with self.assertRaisesRegex(ValueError, "hard links"):
                reader(self.root)

    def test_strict_json_and_quote_register_pin(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}',
                    '{"x":-Infinity}', '{"x":1e999}'):
            for decoder in (checker.decode, producer.strict_json):
                with self.subTest(raw=raw, decoder=decoder.__name__):
                    with self.assertRaises(ValueError):
                        decoder(raw)
        path = self.root / checker.QUOTES
        path.write_bytes(path.read_bytes() + b" ")
        for reader in (checker.reopen, producer.project):
            with self.assertRaisesRegex(ValueError, "Pinned holiday quote register"):
                reader(self.root)

    def test_verify_requires_holiday_gate(self):
        import verify
        with patch.object(verify, "validate_audit"), patch.object(verify, "validate_receipt_audit"), \
                patch.object(verify, "validate_payer_sources"), patch.object(verify, "validate_schools"):
            with patch.object(verify, "validate_holiday_methods", side_effect=ValueError("holiday gate failed")) as gate:
                with self.assertRaisesRegex(ValueError, "holiday gate failed"):
                    verify.main()
                gate.assert_called_once_with()

    def test_existing_public_allowlist_rejects_methods_and_life(self):
        self.assertEqual(PUBLIC_FILES, {
            "index.html", "methods.html", "icon.svg", "data/spending.json",
            "taxes.html", "data/taxes.json", "who-pays.html", "data/payers.json"})
        output = self.root / "public"
        for name in ("life.html", "data/life.json", checker.REGISTER, checker.QUOTES,
                     checker.DIRECTORY + "/" + checker.INPUTS[0]):
            with self.subTest(name=name):
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private")
                with self.assertRaisesRegex(ValueError, "unexpected file"):
                    validate_output(output)
                shutil.rmtree(output)


if __name__ == "__main__":
    unittest.main()
