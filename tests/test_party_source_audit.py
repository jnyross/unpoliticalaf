"""Real pinned assets and corrupt/rehashed inputs; no invented fiscal verdicts."""
import copy
from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from party_source_audit import (DEFAULT_INVENTORY, MISSING, OBSERVATION_PREFIX,
                                PREFIX, PinnedReader, digest, load_json, local_read,
                                locator, validate_inventory)
from party_source_storage import decode_response, encode_response


class PartySourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = PinnedReader()
        cls.inventory = load_json(DEFAULT_INVENTORY.read_bytes())

    def check(self, inventory=None, **kwargs):
        return validate_inventory(inventory or self.inventory, self.reader,
                                  as_of=kwargs.pop("as_of", date(2026, 10, 30)), **kwargs)

    def corrupt_reader(self, changes):
        return PinnedReader(lambda p: changes[p] if p in changes else local_read(p))

    def test_real_whole_pin_and_every_party_stays_incomplete(self):
        self.assertEqual(self.reader.verify_all(), 65)
        report = self.check()
        self.assertEqual((report["party_count"], report["source_count"]), (15, 29))
        self.assertFalse(report["current_coverage_complete"])
        self.assertFalse(report["public_accepted"])
        self.assertEqual(len(report["missing_current_parties"]), 15)
        self.assertTrue(all(p["missing"] == MISSING for p in self.inventory["parties"]))
        with self.assertRaisesRegex(ValueError, "all 15 current inventories remain incomplete"):
            self.check(require_current=True)

    def test_full_retained_pdfs_and_physical_page_locators(self):
        pdfs = [d for d in self.inventory["documents"] if d["text_method"] == "retained_pdftotext_layout"]
        self.assertEqual(len(pdfs), 14)  # 13 party publications plus IFS comparison.
        for document in pdfs:
            with self.subTest(source=document["source_id"]):
                info, content, raw = self.reader.source(document["source_id"])
                self.assertTrue(raw.startswith(b"%PDF-"))
                self.assertIn("pdftotext", info["extraction_tool"])
                ref = document["evidence"]
                self.assertEqual(ref, locator(content, ref["start"], ref["end"]))
                self.assertGreaterEqual(ref["pdf_page"], 1)

    def test_libdem_unknown_encoding_is_lossless_byte_view(self):
        info, content, raw = self.reader.source("libdem-2024-plain-text")
        self.assertTrue(raw.startswith(b"\xffContents"))
        self.assertEqual(info["text_method"], "latin1_byte_view_encoding_unverified")
        self.assertEqual(content.encode("latin-1"), raw)
        self.assertIn("\r\n", content)
        self.assertIn("\x13", content)

    def test_new_complete_observation_has_original_and_decoded_hashes(self):
        info, content, raw = self.reader.source("yourparty-explainer-observed")
        self.assertEqual((info["raw_bytes"], info["raw_sha256"]),
                         (70521, "8542d622823d324d1ed7d5c0ff54a419c59ce2130ab16bc9f402c296eb3dd5c7"))
        self.assertEqual(decode_response(local_read(info["raw_path"])), raw)
        self.assertIn("not a manifesto", content.casefold())
        self.assertIn("2026-10-30T18:17:45", info["retrieved_at"])

    def test_corrupt_and_validly_rehashed_raw_pdf_both_refused(self):
        name = "green-2024.pdf"
        path = PREFIX + name
        changed = b"%PDF-" + b"X" + local_read(path)[6:]
        reader = self.corrupt_reader({path: changed})
        with self.assertRaisesRegex(ValueError, "pinned asset bytes/hash changed"):
            reader.source("green-2024")
        snapshot = load_json(local_read(PREFIX + "SNAPSHOT.json"))
        next(r for r in snapshot["files"] if r["path"] == name)["sha256"] = digest(changed)
        with self.assertRaisesRegex(ValueError, "snapshot anchor changed"):
            self.corrupt_reader({path: changed, PREFIX + "SNAPSHOT.json": json.dumps(snapshot).encode()})

    def test_corrupt_extraction_and_rehashed_extraction_refused(self):
        path = PREFIX + "green-2024.extracted.txt"
        changed = b"Wrong" + local_read(path)[5:]
        reader = self.corrupt_reader({path: changed})
        with self.assertRaisesRegex(ValueError, "pinned asset bytes/hash changed"):
            reader.source("green-2024")
        extraction = load_json(local_read(PREFIX + "EXTRACTION.json"))
        next(r for r in extraction["records"] if r["output"] == "green-2024.extracted.txt")["output_sha256"] = digest(changed)
        with self.assertRaisesRegex(ValueError, "pinned asset bytes/hash changed"):
            self.corrupt_reader({PREFIX + "EXTRACTION.json": json.dumps(extraction).encode()})

    def test_rehashed_new_container_cannot_replace_original_observation(self):
        path = OBSERVATION_PREFIX + "yourparty-explainer-observed-response.json"
        raw = decode_response(local_read(path))
        changed = raw.replace(b"manifesto", b"manifexto", 1)
        self.assertNotEqual(changed, raw)
        reader = self.corrupt_reader({path: encode_response(changed)})
        with self.assertRaisesRegex(ValueError, "observed original response changed"):
            reader.source("yourparty-explainer-observed")
        manifest = load_json(local_read(OBSERVATION_PREFIX + "observation.json"))
        manifest["sources"][0]["sha256"] = digest(changed)
        with self.assertRaisesRegex(ValueError, "observation anchor changed"):
            self.corrupt_reader({OBSERVATION_PREFIX + "observation.json": json.dumps(manifest).encode()})

    def test_offsets_pages_and_quotes_cannot_be_relabelled(self):
        for field, value in (("start", 1), ("end", 2), ("quote", "Invented source"), ("pdf_page", 999)):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                inventory["documents"][0]["evidence"][field] = value
                with self.assertRaisesRegex(ValueError, "locator mismatch|invalid source offsets"):
                    self.check(inventory)

    def test_provenance_source_owner_and_missingness_are_bound(self):
        cases = [
            (lambda i: i["parties"].pop(), "Commons party coverage incomplete"),
            (lambda i: i["parties"][0].update(current_status="complete"), "cannot assert current coverage"),
            (lambda i: i["parties"][0].update(missing=[]), "cannot be cleared"),
            (lambda i: i["documents"][0].update(raw_sha256="0"*64), "provenance mismatch"),
            (lambda i: i["documents"][0].update(party_id="4"), "provenance mismatch"),
            (lambda i: i["documents"][0].update(unexpected=True), "extra fields"),
            (lambda i: i["parties"].reverse(), "must be alphabetical"),
            (lambda i: i["documents"].append(i["documents"][0]), "duplicate inventory source"),
            (lambda i: i["parties"][0].update(documents=["conservative-2024"]), "belongs to another party"),
        ]
        for mutate, message in cases:
            inventory = copy.deepcopy(self.inventory)
            mutate(inventory)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.check(inventory)

    def test_same_field_order_and_limits_for_all_parties(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["parties"][0] = dict(reversed(list(inventory["parties"][0].items())))
        with self.assertRaisesRegex(ValueError, "party field order differs"):
            self.check(inventory)
        inventory = copy.deepcopy(self.inventory)
        inventory["documents"][0]["scope"] = "x" * 401
        with self.assertRaisesRegex(ValueError, "at most 400"):
            self.check(inventory)

    def test_publication_date_needs_original_locator_and_is_not_retrieval_date(self):
        inventory = copy.deepcopy(self.inventory)
        historical = inventory["documents"][0]
        self.assertIsNone(historical["published_on"])
        historical.update(published_on="2026-10-30", publication_locator="2026-10-30")
        with self.assertRaises((ValueError, UnicodeError)):
            self.check(inventory)

    def test_freshness_and_paths_fail_closed(self):
        for stamp in (date(2026, 10, 29), date(2026, 11, 30)):
            with self.subTest(stamp=stamp), self.assertRaisesRegex(ValueError, "stale/future"):
                self.check(as_of=stamp)
        for path in ("reference/party-sources/2026-10-30/../secret", "/etc/passwd",
                     "data/party-evidence/other/secret.txt"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "outside reviewed"):
                local_read(path)
        with self.assertRaisesRegex(ValueError, "no complete retained HTTP response"):
            self.reader.source("reform-economic-plan-pdf")


if __name__ == "__main__":
    unittest.main()
