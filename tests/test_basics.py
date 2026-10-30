"""Bounded tests: fixtures copy only the retained tax-basics directory.

Run with the project's existing unittest discovery. No network or dependencies.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_basics, check_basics

ROOT = Path(__file__).resolve().parents[1]


class BasicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "data/tax-basics", self.root / "data/tax-basics")
        self.tax = build_basics.tax_basics()
        self.payer = build_basics.payer_basics()

    def validate(self, tax=None, payer=None):
        return check_basics.validate_fragments(
            self.tax if tax is None else tax,
            self.payer if payer is None else payer,
            root=self.root,
        )

    def replace(self, html, before, after):
        self.assertIn(before, html, "mutation must actually change the candidate")
        return html.replace(before, after, 1)

    def test_source_pins_and_fragments(self):
        self.assertTrue(check_basics.validate_sources(self.root))
        self.assertTrue(self.validate())
        raw = (self.root / "data/tax-basics/sources.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), check_basics.PINNED_REGISTER_SHA256)
        self.assertEqual(len(check_basics.PINS), 7)

    def test_register_change_is_not_trusted(self):
        path = self.root / "data/tax-basics/sources.json"
        register = json.loads(path.read_bytes())
        register["sources"][0]["url"] = "https://example.org/income-tax"
        path.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "register hash"):
            self.validate()

    def test_raw_tamper_for_each_envelope(self):
        for pin in check_basics.PINS:
            with self.subTest(source=pin[0]):
                path = self.root / f"data/tax-basics/raw/basics-{pin[0]}.html.json"
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                try:
                    with self.assertRaisesRegex(ValueError, "envelope changed"):
                        check_basics.validate_sources(self.root)
                finally:
                    path.write_bytes(original)

    def test_lossless_envelope_reformat_is_also_rejected(self):
        path = self.root / "data/tax-basics/raw/basics-income-tax.html.json"
        envelope = json.loads(path.read_bytes())
        body = envelope["original_response"]
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        self.assertEqual(json.loads(path.read_bytes())["original_response"], body)
        with self.assertRaisesRegex(ValueError, "envelope changed"):
            self.validate()

    def test_original_response_hash_is_independent_of_envelope_hash(self):
        path = self.root / "data/tax-basics/raw/basics-income-tax.html.json"
        envelope = json.loads(path.read_bytes())
        envelope["original_response"] = envelope["original_response"].replace(
            "Income Tax is a tax", "Income Tax NOT a tax", 1)
        stored = json.dumps(envelope, ensure_ascii=True).encode("utf-8")
        path.write_bytes(stored)
        # Simulate a valid envelope layer without changing the original-body pin.
        # The register stays pinned and the body layer must still fail.
        pins = list(check_basics.PINS)
        pins[0] = pins[0][:4] + (len(stored), hashlib.sha256(stored).hexdigest())
        with patch.object(check_basics, "PINS", tuple(pins)):
            with self.assertRaisesRegex(ValueError, "original response changed"):
                check_basics.validate_sources(self.root)

    def test_missing_or_wrong_fragment(self):
        for tax, payer in (("", self.payer), (self.tax, ""),
                           (self.tax + self.tax, self.payer),
                           (self.tax.replace('data-basics="taxes"', 'data-basics="other"'), self.payer)):
            with self.subTest(tax=bool(tax), payer=bool(payer)):
                with self.assertRaises(ValueError):
                    self.validate(tax, payer)

    def test_meaning_changes(self):
        cases = (
            ("tax", "not every tax", "every tax"),
            ("tax", "still pay VAT", "never pay VAT"),
            ("tax", "does not by itself mean", "means"),
            ("tax", "not all", "all"),
            ("tax", "exclude the Personal Allowance", "include the Personal Allowance"),
            ("tax", "They are not a personal savings pot.", "They are a personal savings pot."),
            ("payer", "normally deduct", "never deduct"),
            ("payer", "They also deduct National Insurance.", "They do not deduct National Insurance."),
            ("payer", "They send this money to HMRC.", "They keep this money."),
            ("payer", "They do not tell us who bears the cost.", "They tell us who bears the cost."),
            ("payer", "the difference between VAT charged", "all VAT charged"),
            ("payer", "not the same question", "the same question"),
            ("payer", "They do not send the whole", "They send the whole"),
        )
        for page, before, after in cases:
            with self.subTest(page=page, mutation=before):
                html = self.tax if page == "tax" else self.payer
                changed = self.replace(html, before, after)
                with self.assertRaisesRegex(ValueError, "changed meaning"):
                    self.validate(tax=changed) if page == "tax" else self.validate(payer=changed)

    def test_shorter_guidance_preserves_ni_payroll_and_cost_boundaries(self):
        self.assertIn("Contributions help you qualify for certain benefits and the State Pension. "
                      "They are not a personal savings pot.", self.tax)
        self.assertIn("Employers normally deduct Income Tax from employees&#x27; pay. "
                      "They also deduct National Insurance. They send this money to HMRC. "
                      "They can also owe employer National Insurance.", self.payer)
        self.assertIn("These rules explain how tax is sent. They do not tell us who bears the cost.", self.payer)
        for before, after in (
            ("They do not model tax costs.", "They model tax costs."),
            ("Read the household analysis for the model's assumptions and limits.",
             "The collection rules prove the model's assumptions."),
        ):
            with self.subTest(mutation=before), self.assertRaisesRegex(ValueError, "added unverified copy"):
                self.validate(payer=self.replace(self.payer, before, after))

    def test_source_href_and_locator_are_bound_to_claim(self):
        changed = self.replace(self.tax, 'href="https://www.gov.uk/income-tax"',
                               'href="https://www.gov.uk/national-insurance"')
        with self.assertRaisesRegex(ValueError, "source URL/locator"):
            self.validate(tax=changed)
        # Equal-set link substitution must fail even though both URLs still exist.
        changed = self.tax.replace('href="https://www.gov.uk/income-tax"', 'href="SWAP"')
        changed = changed.replace('href="https://www.gov.uk/national-insurance"',
                                  'href="https://www.gov.uk/income-tax"')
        changed = changed.replace('href="SWAP"', 'href="https://www.gov.uk/national-insurance"')
        with self.assertRaisesRegex(ValueError, "source URL/locator"):
            self.validate(tax=changed)
        changed = self.replace(self.tax, "Income Tax guidance: Overview", "Income Tax guidance: Rates")
        with self.assertRaisesRegex(ValueError, "source URL/locator"):
            self.validate(tax=changed)

    def test_corporation_definition_and_obr_scope_have_separate_source_contracts(self):
        definition = ('<p data-basics-claim="ct">Corporation Tax applies to taxable company or association profits. '
                      '<a href="https://www.gov.uk/corporation-tax">Corporation Tax guidance: Overview</a></p>')
        scope = ('<p data-basics-scope="ct">The OBR group also includes related charges. '
                 'See the OBR group scope and source note. '
                 '<a href="#tax-sources">OBR Receipts (£bn): U4 and note C42</a></p>')
        self.assertIn(definition, self.tax)
        self.assertIn(scope, self.tax)
        self.assertTrue(self.validate())
        cases = (
            ('href="#tax-sources"', 'href="https://www.gov.uk/corporation-tax"', "OBR scope URL/locator"),
            ("U4 and note C42", "U4 and note C41", "OBR scope URL/locator"),
            ("also includes related charges", "excludes related charges", "OBR scope meaning"),
            ('href="https://www.gov.uk/corporation-tax"', 'href="#tax-sources"', "source URL/locator for ct"),
            ('data-basics-scope="ct"', 'data-basics-scope="vat"', "OBR scope marker"),
            (scope, "", "missing or reordered"),
            (scope, scope + scope, "duplicate or nested claim"),
        )
        for before, after, error in cases:
            with self.subTest(mutation=before), self.assertRaisesRegex(ValueError, error):
                self.validate(tax=self.replace(self.tax, before, after))
        self.assertEqual(build_basics.COPY["ct"],
                         "Corporation Tax applies to taxable company or association profits.")
        assertion = build_basics.source_assertions["ct"]
        self.assertEqual(assertion["source_ids"], ["basics-corporation-tax"])
        self.assertTrue(all("profits" in anchor for anchor in assertion["quotedanchor"]))
        self.assertNotIn("OBR", " ".join(assertion["quotedanchor"]))

    def test_collection_heading_is_one_subheading_not_a_repeated_section_title(self):
        heading = '<h3 id="payer-basics-title">How is the tax collected?</h3>'
        self.assertEqual(self.payer.count(heading), 1)
        self.assertNotIn("<h2", self.payer)
        self.assertNotIn("Who sends the tax?", self.payer)
        for replacement in (
            '<h2 id="payer-basics-title">How is the tax collected?</h2>',
            '<h3 id="payer-basics-title">Who sends the tax?</h3>',
            heading + heading,
        ):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.validate(payer=self.replace(self.payer, heading, replacement))

    def test_selection_is_not_rates_or_source_metadata(self):
        self.assertNotIn("scottish-income-tax\"", self.tax)
        self.assertNotIn("%", self.tax + self.payer)
        for addition in ("VAT is 20%.", "Your allowance is £12,570.",
                         "datePublished: 2012", 'original_response: retained HTML'):
            with self.subTest(addition=addition):
                changed = self.replace(self.tax, "</section>", f"<p>{addition}</p></section>")
                with self.assertRaises(ValueError):
                    self.validate(tax=changed)
        # Scope guards must not reject fiscal numbers or publication data elsewhere.
        outside = '<p>2023/24: £100, 20%; publication date 25 June 2020.</p>'
        self.assertTrue(self.validate(tax=outside + self.tax + outside,
                                      payer=outside + self.payer + outside))

    def test_correct_text_cannot_mask_added_false_claim(self):
        changed = self.replace(self.tax, "still pay VAT through purchases.",
                               "still pay VAT through purchases. Everyone pays VAT on every purchase.")
        with self.assertRaisesRegex(ValueError, "changed meaning"):
            self.validate(tax=changed)
        changed = self.replace(self.payer, '<p data-basics-claim="burden">',
                               '<p hidden data-basics-claim="burden">')
        with self.assertRaisesRegex(ValueError, "hidden or active"):
            self.validate(payer=changed)

    def test_assertions_cover_all_derived_qualitative_claims(self):
        self.assertEqual(set(build_basics.source_assertions), set(check_basics.EXPECTED) - {"age"})
        retained_ids = {"basics-" + pin[0] for pin in check_basics.PINS}
        for field, assertion in build_basics.source_assertions.items():
            with self.subTest(field=field):
                self.assertEqual(assertion["field"], field)
                self.assertTrue(set(assertion["source_ids"]) <= retained_ids)
                self.assertTrue(assertion["officialheading"])
                self.assertTrue(assertion["quotedanchor"])
                # Every producer anchor must occur in the independently selected
                # source anchors, not merely in a navigation label or whole file.
                anchors = [anchor for source in assertion["source_ids"]
                           for anchor in check_basics.ANCHORS[source.removeprefix("basics-")]]
                for anchor in assertion["quotedanchor"]:
                    self.assertIn(anchor, anchors)


if __name__ == "__main__":
    unittest.main()
