"""Payer contract and negative tests. These tests require the retained sources.

No generated site, network or sourcechecker import is needed. The controller
must run these and the independent source evidence gate on the exact candidate.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_payers
import check_payers
import payer_projection


def shell(title, body):
    return ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title></head><body>{body}</body></html>')


class PayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = payer_projection.project(ROOT)
        cls.page = build_payers.render(cls.data, shell)

    def assert_bad_data(self, mutate):
        candidate = deepcopy(self.data)
        mutate(candidate)
        with self.assertRaises(ValueError):
            check_payers.validate_data(ROOT, candidate)

    def assert_bad_page(self, old, new):
        self.assertIn(old, self.page)
        candidate = self.page.replace(old, new, 1)
        with self.assertRaises(ValueError):
            check_payers.validate_page(ROOT, self.data, candidate)

    def copy_sources(self, directory):
        root = Path(directory)
        shutil.copytree(ROOT / "data/payers", root / "data/payers")
        return root

    def test_valid_public_data_and_no_javascript_page(self):
        self.assertTrue(check_payers.validate_data(ROOT, self.data))
        self.assertTrue(check_payers.validate_page(ROOT, self.data, self.page))
        self.assertNotIn("<script", self.page)
        self.assertLess(len(self.page.encode()), 500000)
        self.assertEqual(len(self.data["values"]), 23)
        document = check_payers.Page(self.page)
        tables = [n for n in document.nodes if n["tag"] == "table"]
        self.assertEqual(len(tables), 3)
        self.assertFalse(any(p["tag"] == "details" for n in tables for p in n["parents"]))

    def test_repeatable_projection_and_renderer(self):
        self.assertEqual(self.data, payer_projection.project(ROOT))
        self.assertEqual(self.page, build_payers.render(deepcopy(self.data), shell))

    def test_full_source_identity_and_public_minimisation(self):
        payload = json.loads(json.dumps(self.data, ensure_ascii=False, allow_nan=False))
        self.assertEqual(payload, self.data)
        for forbidden in ("original_response", "data/payers/raw/", "/home/", "<html", "36.7 million"):
            self.assertNotIn(forbidden, json.dumps(payload))
        self.assertEqual(set(payload["sources"]), set(check_payers.IDS))
        self.assertEqual({v["period"] for v in payload["values"]}, {"2023/24"})
        self.assertTrue(all(v["formula"] is None and v["operands"] == [] for v in payload["values"]))

    def test_wrong_equal_number_cell_and_group_are_rejected(self):
        # D5 and E5 both contain 15.7. Equal numbers do not prove cell identity.
        def wrong_cell(data):
            data["values"][3]["cell"] = "E5"
            data["values"][3]["source_cell"] = "ons:Table 8!E5"
        self.assert_bad_data(wrong_cell)
        self.assert_bad_data(lambda d: d["values"][3].update(group="Second fifth"))
        # F28 equals F27 in this source. It is a projection, not the approved outturn.
        self.assert_bad_data(lambda d: d["values"][0].update(cell="F28"))

    def test_source_corruption_register_repin_and_envelope_are_rejected(self):
        for name in ("hmrc-table24-july2026.ods", "ons-etb-fye2024.xlsx", "ons-qmi.html.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.copy_sources(directory)
                source = root / "data/payers/raw" / name
                source.write_bytes(source.read_bytes() + b" ")
                with self.assertRaises(ValueError):
                    payer_projection.project(root)
                # Editing the mutable register still cannot change the independent pin.
                register_path = root / "data/payers/sources.json"
                register = json.loads(register_path.read_text())
                entry = next(e for e in register["sources"] if e["file"].endswith("/" + name))
                prefix = "stored_" if name.endswith(".json") else ""
                entry[prefix + "sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
                entry[prefix + "bytes"] = source.stat().st_size
                register_path.write_text(json.dumps(register))
                with self.assertRaises(ValueError):
                    check_payers.validate_data(root, self.data)

    def test_source_labels_notes_and_source_metadata_are_exact(self):
        self.assert_bad_data(lambda d: d["source_cells"]["hmrc:2_4_Taxpayer_share_tax!F2"].update(value="Top 50% percentile group"))
        self.assert_bad_data(lambda d: d["source_cells"]["ons:Notes!B9"].update(value="No warning"))
        self.assert_bad_data(lambda d: d["sources"]["ons"].update(sha256="0" * 64))
        self.assert_bad_data(lambda d: d["sources"]["ons_method"].update(published="2025-09-25"))
        self.assert_bad_data(lambda d: d["sources"]["ons_qmi"].pop("stored_sha256"))
        self.assert_bad_data(lambda d: d["values"][0].update(source_sha256="0" * 64))

    def test_published_combined_total_not_sum_of_rounded_parts(self):
        values = {v["id"]: v for v in self.data["values"]}
        combined = values["ons-2-combined"]["value"]
        rounded_sum = round(values["ons-2-direct"]["value"] + values["ons-2-indirect"]["value"], 1)
        self.assertNotEqual(combined, rounded_sum)
        def replace(data):
            next(v for v in data["values"] if v["id"] == "ons-2-combined")["value"] = rounded_sum
        self.assert_bad_data(replace)
        self.assert_bad_data(lambda d: d["values"][5].update(formula="direct + indirect", operands=["ons-1-direct", "ons-1-indirect"]))

    def test_suppression_missing_and_zero_are_distinct(self):
        for missing in (None, "..", "-", "", True, float("nan")):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                payer_projection.number(missing)
        self.assertEqual(payer_projection.number(0), 0)
        self.assert_bad_data(lambda d: d["source_cells"]["ons:Table 2b!C45"].update(value=0))
        self.assert_bad_data(lambda d: d["values"][0].update(value=None))

    def test_period_status_population_denominator_and_overlap(self):
        for field, value in (("period", "2024/25"), ("status", "Forecast"),
                             ("population", "All UK residents"), ("unit", "£"),
                             ("denominator", "All UK taxes"), ("ranking", "Wealth")):
            with self.subTest(field=field):
                self.assert_bad_data(lambda d, f=field, v=value: d["values"][0].update({f: v}))
        self.assert_bad_data(lambda d: d.update(groups_overlap=False))
        self.assert_bad_data(lambda d: d.update(ons_group_basis="Five equal-household groups"))
        self.assert_bad_data(lambda d: d["values"].pop())
        self.assert_bad_data(lambda d: d["values"].append(deepcopy(d["values"][0])))

    def test_display_text_exact_attributes_and_bar_values(self):
        self.assert_bad_page(">9.9%</data>", ">8.9%</data>")
        self.assert_bad_page('data-ref="2_4_Taxpayer_share_tax!F27"', 'data-ref="2_4_Taxpayer_share_tax!F28"')
        self.assert_bad_page('data-ref="Table 8!D5"', 'data-ref="Table 8!E5"')
        self.assert_bad_page('data-denominator="Gross household income"', 'data-denominator="Household expenditure"')
        self.assert_bad_page('data-status="Estimated outturn"', 'data-status="Forecast"')
        self.assert_bad_page('data-population="UK people in private households"', 'data-population="All UK households"')
        self.assert_bad_page('data-period="2023/24"', 'data-period="2024/25"')
        self.assert_bad_page('style="width:9.9%"', 'style="width:99.0%"')
        self.assert_bad_page('data-chart-denominator="Gross household income"', 'data-chart-denominator="Household expenditure"')

    def test_headings_tables_and_groups_cannot_mix_measures(self):
        self.assert_bad_page('Who owed Income Tax in 2023/24?', 'Who paid all taxes in 2023/24?')
        self.assert_bad_page('Direct / gross income', 'Direct / expenditure')
        self.assert_bad_page('Combined / gross income', 'Combined / disposable income')
        self.assert_bad_page('<th scope="row">Bottom fifth</th>', '<th scope="row">Top fifth</th>')
        self.assert_bad_page('HMRC: shares of total Income Tax liabilities, 2023/24 estimated outturn',
                             'HMRC: shares of total Income Tax liabilities, 2024/25 outturn')

    def test_core_tables_caveats_and_source_download_routes_remain_available(self):
        self.assert_bad_page('<table>', '<table hidden>')
        self.assert_bad_page('<div class="payer-note" id="bottom-group">', '<details id="bottom-group">')
        self.assert_bad_page('<div class="payer-note" id="bottom-group">', '<div class="payer-note" id="bottom-group" hidden>')
        self.assert_bad_page('overlapping groups. Do not add their shares', 'groups are disjoint. Add their shares')
        self.assert_bad_page('high gross income but low disposable income', 'no caveat')
        self.assert_bad_page('href="data/payers.json"', 'href="data/missing.json"')
        self.assert_bad_page('href="' + check_payers.URLS[1] + '"', 'href="#missing"')
        self.assert_bad_page('aria-labelledby="ons-income-table"', 'aria-labelledby="missing"')

    def test_public_data_extra_raw_response_and_count_are_rejected(self):
        self.assert_bad_data(lambda d: d.update(original_response="raw HTML"))
        self.assert_bad_data(lambda d: d["values"].append({"id": "taxpayer-count", "value": 36700000}))
        self.assert_bad_page('Two official views answer different questions.', '36.7 million taxpayers. Two official views answer different questions.')

    def test_source_root_and_source_file_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_sources(Path(directory) / "actual")
            alias = Path(directory) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                check_payers.validate_data(alias, self.data)
            source = root / "data/payers/raw/hmrc-table24-july2026.ods"
            original = source.with_suffix(".original")
            source.rename(original)
            source.symlink_to(original)
            with self.assertRaises(ValueError):
                check_payers.validate_data(root, self.data)
            with self.assertRaises(ValueError):
                payer_projection.project(root)

    def test_direct_source_read_does_not_depend_on_csv_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_sources(directory)
            shutil.rmtree(root / "data/payers/audit")
            self.assertEqual(payer_projection.project(root), self.data)
            self.assertTrue(check_payers.validate_data(root, self.data))

    def test_odf_explicit_spaces_and_repeats_are_preserved(self):
        t = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
        p = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        o = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
        xml = f'''<o:document-content xmlns:o="{o}" xmlns:t="{t}" xmlns:p="{p}">
<t:table t:name="Sample"><t:table-row t:number-rows-repeated="2">
<t:table-cell t:number-columns-repeated="2"><p:p>A<p:s p:c="2"/>B<p:tab/>C<p:line-break/>D<p:s/></p:p></t:table-cell>
<t:table-cell o:value="9.9"><p:p>9.9</p:p></t:table-cell></t:table-row>
<t:table-row><t:table-cell t:number-columns-repeated="1000"/></t:table-row>
</t:table></o:document-content>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.ods"
            with ZipFile(path, "w") as archive:
                archive.writestr("content.xml", xml)
            result = payer_projection.ods_cells(path)
        self.assertEqual(result[("Sample", "A1")]["text"], "A  B\tC\nD ")
        self.assertEqual(result[("Sample", "B2")]["text"], "A  B\tC\nD ")
        self.assertEqual(result[("Sample", "C2")]["value"], 9.9)
        self.assertNotIn(("Sample", "A3"), result)


if __name__ == "__main__":
    unittest.main()
