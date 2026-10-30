"""Full-row and rendered-date regressions, using independently reopened sources."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fiscal_schema
import check_fiscal
import check_site
import build_site


class Recovery22Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/spending.json").read_text())
        cls.raw = check_fiscal.RawReader()
        cls.audit = staticmethod(fiscal_schema.audit_reader())

    def test_all_original_base_price_rows_are_present(self):
        reports = [r for r in fiscal_schema.reconciliations(self.audit)
                   if r["id"].startswith("base-price/")]
        self.assertEqual(len(reports), 22)
        self.assertEqual({o["ref"] for r in reports for o in r["operands"]},
                         {f"{sheet}!X{row}" for sheet in ("4_2", "4_3") for row in range(6, 28)})
        check_fiscal.check_reports({"reconciliations": fiscal_schema.reconciliations(self.audit)}, self.raw)

    def test_every_base_price_row_missing_cell_or_label_fails_both_readers(self):
        for row in range(6, 28):
            for sheet in ("4_2", "4_3"):
                for col in ("A", "X"):
                    ref = f"{sheet}!{col}{row}"
                    for reader, verify in (
                        (self.audit, lambda read: fiscal_schema.reconciliations(read)),
                        (self.raw, lambda read: check_fiscal.check_reports(self.data, read)),
                    ):
                        def missing(key):
                            cell = reader(key)
                            return dict(cell, kind="blank", value=None) if key == ref else cell
                        with self.subTest(ref=ref, reader=type(reader).__name__):
                            with self.assertRaisesRegex(ValueError, "[Ii]dentity|[Ss]emantic|[Mm]issing required"):
                                verify(missing)

    def test_base_price_units_cannot_agree_on_the_wrong_unit(self):
        for reader, verify in (
            (self.audit, lambda read: fiscal_schema.reconciliations(read)),
            (self.raw, lambda read: check_fiscal.check_reports(self.data, read)),
        ):
            def wrong(ref):
                cell = reader(ref)
                return dict(cell, value="£ million") if ref in ("4_2!X3", "4_3!X3") else cell
            with self.assertRaisesRegex(ValueError, "[Uu]nit|[Ii]dentity|[Ss]emantic"):
                verify(wrong)

    def test_blank_required_base_price_headers_fail_both_readers(self):
        for sheet in ("4_2", "4_3"):
            for header in ("X3", "X5", "B4"):
                ref = f"{sheet}!{header}"
                for reader, verify in (
                    (self.audit, fiscal_schema.reconciliations),
                    (self.raw, lambda read: check_fiscal.check_reports(self.data, read)),
                ):
                    def missing(key):
                        cell = reader(key)
                        return dict(cell, kind="blank", value=None) if key == ref else cell
                    with self.subTest(ref=ref, reader=type(reader).__name__):
                        with self.assertRaisesRegex(ValueError, "identity|semantic|period missing"):
                            verify(missing)

    def test_base_price_identity_requires_present_text_kind_and_value(self):
        refs = [f"{sheet}!{cell}" for sheet in ("4_2", "4_3")
                for cell in [*(f"A{row}" for row in range(6, 28)), "X3", "X5", "B4"]]
        for reader, boundary in ((self.audit, fiscal_schema.base_price_evidence),
                                 (self.raw, check_fiscal.independent_base_rows)):
            for ref in refs:
                original = reader(ref)
                for changes in ({"kind": "blank"}, {"kind": "number"},
                                {"kind": "text", "value": None}, {"kind": "text", "value": ""}):
                    def malformed(key):
                        return dict(original, **changes) if key == ref else reader(key)
                    with self.subTest(ref=ref, reader=type(reader).__name__, changes=changes):
                        with self.assertRaisesRegex(ValueError, "identity"):
                            boundary(malformed)

    def test_every_displayed_identity_requires_present_text_in_both_readers(self):
        # Exercise each retained label, period and unit directly at both semantic
        # boundaries. A later retained-cell comparison must not mask acceptance
        # of a matching string with a contradictory blank/number kind.
        seen = set()
        for _, contract in fiscal_schema.selections(self.data):
            for reader, boundary in ((self.audit, fiscal_schema.metadata),
                                     (self.raw, check_fiscal.source_metadata)):
                boundary(contract, reader)
            for role, (ref, _) in contract["identity"].items():
                if (role, ref) in seen:
                    continue
                seen.add((role, ref))
                for reader, boundary in ((self.audit, fiscal_schema.metadata),
                                         (self.raw, check_fiscal.source_metadata)):
                    original = reader(ref)
                    for changes in ({"kind": "blank"}, {"kind": "number"},
                                    {"kind": "text", "value": None},
                                    {"kind": "text", "value": ""},
                                    {"kind": "text", "value": "   "},
                                    {"kind": "text", "value": 0},
                                    {"kind": "text", "value": False}):
                        def malformed(key):
                            return dict(original, **changes) if key == ref else reader(key)
                        with self.subTest(role=role, ref=ref, reader=type(reader).__name__,
                                          changes=changes):
                            with self.assertRaisesRegex(ValueError, "semantic"):
                                boundary(contract, malformed)

    def test_equal_valued_wrong_subcategory_identity_fails(self):
        specs = list(fiscal_schema.reconciliation_specs())
        index = next((i for i, s in enumerate(specs) if any(t[0] == "4_2!X7" for t in s[3])), None)
        self.assertIsNotNone(index, "Undisplayed subcategory has no base-price guard")
        name, year, unit, terms, excluded, basis = specs[index]
        self.assertEqual(float(self.audit("4_2!X7")["value"]), self.raw("4_3!X7")["value"])
        # Swap both cash/real identities; the residual remains exactly zero.
        terms = [(ref.replace("4_2!", "4_3!") if ref.startswith("4_2!") else ref.replace("4_3!", "4_2!"), c, q)
                 for ref, c, q in terms]
        specs[index] = name, year, unit, terms, excluded, basis
        with patch("fiscal_schema.reconciliation_specs", return_value=iter(specs)):
            reports = fiscal_schema.reconciliations(self.audit)
        with self.assertRaisesRegex(ValueError, "Wrong or overlapping reconciliation source cells"):
            check_fiscal.check_reports({"reconciliations": reports}, self.raw)

    def test_equal_valued_wrong_row_and_duplicate_labels_fail(self):
        # Deliberately make another numeric row equal in BOTH readers. Numeric
        # agreement must still not validate public/common services as international.
        def equalized(reader):
            def read(ref):
                return reader(ref.replace("X8", "X7")) if ref in ("4_2!X8", "4_3!X8") else reader(ref)
            return read
        specs = list(fiscal_schema.reconciliation_specs())
        index = next(i for i, s in enumerate(specs) if s[0] == "base-price/public-common")
        name, year, unit, terms, excluded, basis = specs[index]
        specs[index] = name, year, unit, [("4_2!X8" if ref == "4_2!X7" else ref, c, q)
                                         for ref, c, q in terms], excluded, basis
        with patch("fiscal_schema.reconciliation_specs", return_value=iter(specs)):
            reports = fiscal_schema.reconciliations(equalized(self.audit))
        with self.assertRaisesRegex(ValueError, "Wrong or overlapping reconciliation source cells"):
            check_fiscal.check_reports({"reconciliations": reports}, equalized(self.raw))
        for reader, verify in (
            (self.audit, lambda read: fiscal_schema.reconciliations(read)),
            (self.raw, lambda read: check_fiscal.check_reports(self.data, read)),
        ):
            def duplicated(ref):
                return reader("4_2!A7") if ref == "4_2!A8" else reader(ref)
            with self.assertRaisesRegex(ValueError, "[Ii]dentity"):
                verify(duplicated)

    def test_undisplayed_base_price_arithmetic_cannot_be_skipped(self):
        for reader, verify in (
            (self.audit, lambda read: fiscal_schema.reconciliations(read)),
            (self.raw, lambda read: check_fiscal.check_reports(self.data, read)),
        ):
            def broken(ref):
                cell = reader(ref)
                return dict(cell, value=float(cell["value"]) + 1) if ref == "4_3!X7" else cell
            with self.assertRaisesRegex(ValueError, "reconciliation failed: base-price/public-common"):
                verify(broken)

    def test_raw_source_date_mutation_cannot_be_approved_by_shared_status(self):
        # Both notes change together, so the producer's date-conflict guard alone
        # cannot catch a stale date. Shared STATUS equality must not approve it.
        def changed(ref):
            cell = self.raw(ref)
            if ref in ("4_1!B51", "4_1!B52"):
                return dict(cell, value=cell["value"].replace("3 March 2026", "1 April 2026"))
            return cell
        data = copy.deepcopy(self.data)
        data["pesa_context"]["forecast_date"] = "1 April 2026"
        for ref in ("4_1!B51", "4_1!B52"):
            data["source_cells"][ref]["value"] = changed(ref)["value"]
        with self.assertRaisesRegex(ValueError, "PESA.*[Dd]ate|PESA.*vintage"):
            check_fiscal.validate_fiscal(data, changed)

    def test_stale_forecast_label_rejected_even_if_shared_policy_agrees(self):
        data = copy.deepcopy(self.data)
        data["status_definitions"]["pesa_forecast"]["label"] = "PESA forecast; OBR 1 April 2026"
        with patch.dict(fiscal_schema.STATUS, data["status_definitions"]):
            with self.assertRaisesRegex(ValueError, "PESA.*[Dd]ate|PESA.*vintage"):
                check_fiscal.validate_fiscal(data, self.raw)

    def test_all_forecast_date_rendering_follows_changed_source_context(self):
        data = copy.deepcopy(self.data)
        data["pesa_context"]["forecast_date"] = "1 April 2026"
        # Simulate a future consistent note pair, without altering retained inputs.
        def changed(ref):
            cell = self.audit(ref)
            if ref in ("4_1!B51", "4_1!B52"):
                return dict(cell, value=cell["value"].replace("3 March 2026", "1 April 2026"))
            return cell
        with patch("fiscal_schema.audit_reader", return_value=changed):
            fiscal_schema.enrich(data)
        build_site.configure(data)
        rendered = build_site.index()
        self.assertNotIn("3 March 2026", rendered)
        self.assertNotIn("The March 2026 forecast note above", rendered)
        self.assertIn("PESA forecast; OBR 1 April 2026", rendered)
        self.assertEqual(rendered.count('data-pesa-forecast-date="1"'), 2)
        def changed_raw(ref):
            cell = self.raw(ref)
            if ref in ("4_1!B51", "4_1!B52"):
                return dict(cell, value=cell["value"].replace("3 March 2026", "1 April 2026"))
            return cell
        check_site.check_pesa_dates(rendered, data, changed_raw, "index.html")
        methods = build_site.methods()
        self.assertNotIn("3 March 2026", methods)
        check_site.check_pesa_dates(methods, data, changed_raw, "methods.html")
        # Once both source notes move forward, the old literal must still fail
        # in prose as well as in marked labels and forecast value tooltips.
        for name, page in (("index.html", rendered), ("methods.html", methods)):
            injected = page.replace("</main>",
                "<p>The PESA forecast</p><p>3 <em>March</em> 2026.</p></main>")
            self.assertNotEqual(injected, page)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                check_site.check_pesa_dates(injected, data, changed_raw, name)

    def test_unmarked_forecast_date_prose_fails_on_every_page(self):
        build_site.configure(copy.deepcopy(self.data))
        for name, rendered in (("index.html", build_site.index()), ("methods.html", build_site.methods())):
            check_site.check_pesa_dates(rendered, self.data, self.raw, name)
            for date in ("3 March 2026", "1 April 2026", "3 <em>March</em> 2026"):
                injected = rendered.replace("</main>", f"<p>The PESA forecast is dated {date}.</p></main>")
                self.assertNotEqual(injected, rendered)
                with self.subTest(name=name, date=date), self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                    check_site.check_pesa_dates(injected, self.data, self.raw, name)

    def test_forecast_date_prose_preserves_block_and_inline_boundaries(self):
        build_site.configure(copy.deepcopy(self.data))
        fragments = (
            "<p>The PESA forecast</p><p>1 April 2026.</p>",
            "<p>The PESA forecast<br>1 April 2026.</p>",
            "<blockquote>The PESA forecast</blockquote><blockquote>1 April 2026.</blockquote>",
            "<article>The PESA forecast</article><article>1 April 2026.</article>",
            "<details><summary>The PESA forecast</summary>1 April 2026.</details>",
            "<p>The PESA fore<em>cast</em> is dated 1 April 2026.</p>",
            "<p>The PESA forecast is dated 1 <span>April</span> 2026.</p>",
        )
        for name, rendered in (("index.html", build_site.index()), ("methods.html", build_site.methods())):
            for fragment in fragments:
                injected = rendered.replace("</main>", fragment + "</main>")
                self.assertNotEqual(injected, rendered)
                with self.subTest(name=name, fragment=fragment):
                    with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                        check_site.check_pesa_dates(injected, self.data, self.raw, name)

    def test_marked_dates_allow_inline_markup_without_hiding_stale_text(self):
        build_site.configure(copy.deepcopy(self.data))
        rendered = build_site.index()
        original = '<span data-pesa-forecast-date="1">3 March 2026</span>'
        self.assertIn(original, rendered)
        inline = rendered.replace(original,
            '<span data-pesa-forecast-date="1">3 <span><em>March</em></span> 2026</span>', 1)
        check_site.check_pesa_dates(inline, self.data, self.raw, "index.html")
        for replacement in (
            '<span data-pesa-forecast-date="1">1 <span>April</span> 2026</span>',
            '<span data-pesa-forecast-date="1">1 April 2026 / '
            '<span data-pesa-forecast-date="1">3 March 2026</span></span>',
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                    check_site.check_pesa_dates(rendered.replace(original, replacement, 1),
                                               self.data, self.raw, "index.html")

    def test_rendered_date_and_tooltip_mutations_fail_raw_checker(self):
        build_site.configure(copy.deepcopy(self.data))
        rendered = build_site.index()
        # Independently validate actual HTML, not just generated JSON policy.
        check_site.check_pesa_dates(rendered, self.data, self.raw, "index.html")
        for old, new in (
            ('data-pesa-forecast-date="1">3 March 2026', 'data-pesa-forecast-date="1">1 April 2026'),
            ("PESA forecast; OBR 3 March 2026", "PESA forecast; OBR 1 April 2026"),
            ('data-pesa-forecast-date="1"', 'data-stale-date="1"'),
        ):
            self.assertIn(old, rendered)
            with self.subTest(old=old), self.assertRaisesRegex(ValueError, "PESA.*[Dd]ate|PESA.*vintage"):
                check_site.check_pesa_dates(rendered.replace(old, new, 1), self.data, self.raw, "index.html")


if __name__ == "__main__":
    unittest.main()
