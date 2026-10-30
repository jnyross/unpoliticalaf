"""Corrupt public current-tax nodes and rendered claims against pinned raw evidence.

The controller builds first. Raw sources are reopened once for the fixture;
mutations are compared with that independent expectation, never producer maps.
"""
import copy
import html
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_taxes
import tax_projection
import build_taxes


class TaxSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = check_taxes.expected_data(ROOT)
        cls.public = check_taxes.read_json(ROOT / "site/data/taxes.json")
        cls.page = (ROOT / "site/taxes.html").read_text()
        cls.latest = cls.expected["latest_year"]

    def test_public_projection_and_every_rendered_value_match_reopened_current_source(self):
        self.assertEqual(len(self.expected["years"]), 33)
        self.assertEqual(len(self.expected["nodes"]), 287)
        self.assertEqual(self.latest, "2025-26")
        check_taxes.compare(self.public, self.expected)
        self.assertEqual(check_taxes.validate_html(self.page, self.expected),
                         set(self.expected["nodes"]))

    def reject(self, mutation):
        data = copy.deepcopy(self.public)
        mutation(data)
        with self.assertRaises(ValueError):
            check_taxes.compare(data, self.expected)

    def test_equal_number_wrong_cell_is_rejected(self):
        receipt = f"cash/C/{self.latest}"
        component = f"component/AG/{self.latest}"
        self.assertEqual(self.public["nodes"][receipt]["v"], self.public["nodes"][component]["v"])
        self.reject(lambda data: data["nodes"][receipt].update(
            ref=data["nodes"][component]["ref"]))

    def test_number_units_status_year_scope_and_identity_changes_are_rejected(self):
        identity = f"cash/C/{self.latest}"
        for field, wrong in (("v", 1), ("unit", "GBP million"), ("status", "forecast"),
                             ("year", "2024-25"), ("year_ref", "Aggregates (£bn)!B86"),
                             ("basis", "cash_stock"), ("scope", "central_government"),
                             ("geography", "England"), ("label", "Tax"),
                             ("code", "wrong"), ("label_ref", "Aggregates (£bn)!D4")):
            with self.subTest(field=field):
                self.reject(lambda data: data["nodes"][identity].update({field: wrong}))

    def test_missing_field_year_node_and_extra_private_data_are_rejected(self):
        self.reject(lambda data: data.pop("notes"))
        self.reject(lambda data: data["years"].pop())
        self.reject(lambda data: data["nodes"].pop(f"cash/O/{self.latest}"))
        self.reject(lambda data: data.update(private_audit="private sentinel"))
        self.reject(lambda data: data["source"].update(file="data/raw/private.xlsx"))

    def test_wrong_source_version_and_note_are_rejected(self):
        self.reject(lambda data: data["source"].update(sha256="0" * 64))
        self.reject(lambda data: data["notes"].update(
            {"Aggregates (per cent of GDP)!C90": "Debt uses annual GDP."}))

    def test_group_formula_order_double_count_and_denominator_are_rejected(self):
        group = f"group/income_tax/{self.latest}"
        share = f"share/income_tax/{self.latest}"
        self.reject(lambda data: data["nodes"][group]["operands"].reverse())
        self.reject(lambda data: data["nodes"][group]["operands"].append(
            copy.deepcopy(data["nodes"][group]["operands"][0])))
        self.reject(lambda data: data["nodes"][share]["operands"][1].update(
            id=f"component/AH/{self.latest}"))
        self.reject(lambda data: data["nodes"][group].update(formula="sum_all_taxes"))
        self.reject(lambda data: data["nodes"][group].update(budget=1000))

    def test_same_table_balance_cannot_be_mixed_with_pesa(self):
        balance = f"balance/{self.latest}"
        self.reject(lambda data: data["nodes"][balance]["operands"][0].update(ref="4_1!X20"))
        self.reject(lambda data: data["nodes"][balance].update(v=0))
        self.assertEqual(self.expected["nodes"][balance]["v"],
                         self.expected["nodes"][f"cash/D/{self.latest}"]["v"] -
                         self.expected["nodes"][f"cash/C/{self.latest}"]["v"])

    def test_published_debt_share_is_retained_separately_from_cash_stock(self):
        cash = self.expected["nodes"][f"cash/X/{self.latest}"]
        share = self.expected["nodes"][f"gdp/X/{self.latest}"]
        self.assertEqual(cash["basis"], "cash_stock")
        self.assertEqual(share["basis"], "cash_stock")
        self.assertEqual(share["formula"], "source_cell")
        self.assertIn("GDP centred on end-March",
                      self.expected["notes"]["Aggregates (per cent of GDP)!C90"])
        self.reject(lambda data: data["nodes"][f"gdp/X/{self.latest}"].update(
            formula="cash_divided_by_annual_GDP"))

    def test_forecasts_are_not_outturn_and_last_source_year_is_present(self):
        self.assertEqual(self.expected["years"][-1], "2031-32")
        for family in ("cash", "gdp"):
            self.assertEqual(self.expected["nodes"][f"{family}/C/2026-27"]["status"], "forecast")
        self.reject(lambda data: data["nodes"]["cash/C/2026-27"].update(status="outturn"))

    def test_raw_blank_dash_zero_and_negative_are_distinct(self):
        raw = check_taxes.Raw.__new__(check_taxes.Raw)
        for marker in (None, "", "-", " - "):
            raw.cell = lambda ref, value=marker: value
            self.assertIsNone(raw.numeric("test!A1"))
        for number in (0, -5.246):
            raw.cell = lambda ref, value=number: value
            self.assertEqual(raw.numeric("test!A1"), number)
        raw.cell = lambda ref: "not available"
        with self.assertRaises(ValueError):
            raw.numeric("test!A1")

    def test_nonfinite_boolean_and_replaced_missing_values_are_rejected(self):
        identity = f"component/S/{self.latest}"
        for wrong in (float("nan"), float("inf"), True, None):
            with self.subTest(wrong=wrong):
                self.reject(lambda data: data["nodes"][identity].update(v=wrong))
        with self.assertRaises(ValueError):
            check_taxes.compare(0, None)

    def test_hashes_and_input_root_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                check_taxes.expected_data(root)
            (root / "data/raw").mkdir(parents=True)
            shutil.copy2(ROOT / "data/sources.json", root / "data/sources.json")
            shutil.copy2(ROOT / check_taxes.SOURCE_FILE, root / check_taxes.SOURCE_FILE)
            with (root / check_taxes.SOURCE_FILE).open("ab") as stream:
                stream.write(b"corrupt")
            with self.assertRaisesRegex(ValueError, "hash"):
                check_taxes.expected_data(root)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"v":1,"v":2}', object_pairs_hook=check_taxes.unique_object)

    def changed_element(self, identity, change):
        pattern = re.compile(r"<data\b[^>]*>.*?</data>", re.S)
        altered = False
        def mutate(match):
            nonlocal altered
            if not altered and f'data-tax-id="{identity}"' in match.group(0):
                altered = True
                return change(match.group(0))
            return match.group(0)
        page = pattern.sub(mutate, self.page)
        self.assertTrue(altered)
        return page

    def check_bad_html(self, page):
        with self.assertRaises(ValueError):
            check_taxes.validate_html(page, self.expected)

    def test_changed_rendered_value_text_and_source_identity_are_rejected(self):
        identity = f"cash/C/{self.latest}"
        mutations = [
            lambda element: re.sub(r'value="[^"]*"', 'value="0"', element, count=1),
            lambda element: re.sub(r">[^<]*</data>", ">£0.000bn</data>", element),
            lambda element: re.sub(r'data-ref="[^"]*"', 'data-ref="Receipts (£bn)!AG33"', element),
            lambda element: element.replace('data-status="outturn"', 'data-status="forecast"'),
            lambda element: element.replace('data-unit="GBP billion"', 'data-unit="GBP million"'),
            lambda element: element.replace(f'data-year="{self.latest}"', 'data-year="2024-25"'),
            lambda element: element.replace(check_taxes.SOURCE_HASH, "0" * 64),
            lambda element: element.replace("<data ", '<data tabindex="0" '),
            lambda element: element.replace("data-tax-id=", "data-unchecked-id="),
            lambda element: re.sub(r'data-operands="[^"]*"', 'data-operands="[]"', element),
        ]
        for index, change in enumerate(mutations):
            with self.subTest(mutation=index):
                self.check_bad_html(self.changed_element(identity, change))



    def test_visible_tax_table_year_status_label_and_multiplier_cannot_be_swapped(self):
        changes = [
            ("<th scope=\"row\">Income tax</th>", "<th scope=\"row\">VAT</th>"),
            ("<th scope=\"row\">1999-00</th>", "<th scope=\"row\">1998-99</th>"),
            ("<td>outturn</td>", "<td>forecast</td>"),
            ("<td>+1</td>", "<td>-1</td>"),
        ]
        for old, new in changes:
            with self.subTest(old=old):
                page = self.page.replace(old, new, 1)
                self.assertNotEqual(page, self.page)
                self.check_bad_html(page)

    def test_chart_geometry_cannot_disagree_with_signed_table_values(self):
        page, count = re.subn(r'(<span class="tax-fill" style="left:)[^"]+',
                              r'\g<1>0%;width:100%', self.page, count=1)
        self.assertEqual(count, 1)
        self.check_bad_html(page)

    def test_negative_income_component_sign_cannot_be_hidden(self):
        identity = f"component/S/{self.latest}"
        self.assertLess(self.expected["nodes"][identity]["v"], 0)
        self.check_bad_html(self.changed_element(
            identity, lambda element: element.replace("£-", "£")))

    def test_missing_rendered_node_is_rejected_even_when_data_remains(self):
        identity = f"cash/C/1999-00"
        pattern = re.compile(r'<data\b[^>]*data-tax-id="' + re.escape(identity) + r'"[^>]*>.*?</data>', re.S)
        page, count = pattern.subn("", self.page)
        self.assertGreater(count, 0)
        self.check_bad_html(page)

    def test_forecast_prose_markers_mask_exact_bound_current_claims_only(self):
        checked = check_taxes.checked_forecast_prose(self.page, self.expected)
        self.assertNotIn('data-tax-forecast=', checked)
        for old, new in (
                ('data-tax-forecast="outlook"', 'data-tax-forecast="arbitrary"'),
                ("These years are forecasts, not observed facts.", "These years are observed facts."),
                ("October 2026 OBR forecasts:", "March 2026 OBR forecasts:")):
            with self.subTest(old=old):
                changed = self.page.replace(old, new)
                self.assertNotEqual(changed, self.page)
                with self.assertRaises(ValueError):
                    check_taxes.checked_forecast_prose(changed, self.expected)
        # Unmarked words and dates are retained for the unchanged PESA guard.
        injected = self.page.replace("</main>", "<p>PESA March 2026 forecast.</p></main>")
        self.assertIn("PESA March 2026 forecast.",
                      check_taxes.checked_forecast_prose(injected, self.expected))



class TaxProjectionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipts = check_taxes.read_json(ROOT / "data/receipts.json")

    def test_projection_drops_private_extras_at_every_selected_level(self):
        receipts = copy.deepcopy(self.receipts)
        year = "2025-26"
        sentinel = "private_tax_projection_sentinel"
        table = receipts["tables"]["current_receipts"]
        for container in (receipts, receipts["sources"]["obr_databank"], table,
                          table["series"]["Q"]["values"][year],
                          table["derived"]["income_tax"][year]):
            container[sentinel] = sentinel
        encoded = tax_projection.encode(tax_projection.project(receipts))
        self.assertNotIn(sentinel.encode(), encoded)
        self.assertLess(len(encoded), 500_000)

    def test_missing_numerator_and_zero_denominator_stay_missing(self):
        year = "2025-26"
        for case in ("missing_group", "zero_denominator", "missing_denominator"):
            with self.subTest(case=case):
                receipts = copy.deepcopy(self.receipts)
                table = receipts["tables"]["current_receipts"]
                if case == "missing_group":
                    table["derived"]["income_tax"][year].update(
                        v=None, missing_operands=["Receipts (£bn)!Q33"])
                    missing = [f"group/income_tax/{year}"]
                else:
                    table["series"]["AG"]["values"][year]["v"] = (
                        0 if case == "zero_denominator" else None)
                    missing = [f"component/AG/{year}"]
                projected = tax_projection.project(receipts)
                identity = f"share/income_tax/{year}"
                node = projected["nodes"][identity]
                self.assertIsNone(node["v"])
                self.assertEqual(node["missing_operands"], missing)
                markup = build_taxes.figure(projected, identity)
                self.assertIn('value=""', markup)
                self.assertIn(">not given</data>", markup)


if __name__ == "__main__":
    unittest.main()
