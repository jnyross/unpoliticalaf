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
            f'<title>{title}</title></head><body><nav aria-label="Main pages">'
            '<a href="index.html">Spending</a><a href="taxes.html">Taxes</a>'
            '<a href="who-pays.html" aria-current="page">Who pays</a><a href="methods.html">Methods</a>'
            f'</nav>{body}</body></html>')


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

    def test_plain_language_rewrite_keeps_full_causal_limits_and_negations(self):
        document = check_payers.Page(self.page)
        limits = [n for n in document.nodes if "data-payer-limit" in n["attrs"]]
        self.assertEqual({n["attrs"]["data-payer-limit"] for n in limits},
                         {"deferred", "low-income", "model-costs", "separate-views"})
        self.assertEqual(len(limits), 4)
        for old, new in (
            ("These payments need not match a typical year's tax bill.", "These payments match a typical year's tax bill."),
            ("They can use savings or borrowing.", "They cannot use savings or borrowing."),
            ("This is an assumption. It is not a settled fact.", "This is a settled fact."),
            ("It must not be mapped wholly to either ONS group.", "It must be mapped wholly to either ONS group."),
            ("They cannot give a top-1% all-tax burden.", "They give a top-1% all-tax burden."),
            ("Do not take an average across the panels.", "Take an average across the panels."),
            ("Do not match them to tax receipts.", "Match them to tax receipts."),
        ):
            with self.subTest(negation=old):
                self.assertIn(old, self.page)
                changed = self.page.replace(old, new, 1)
                with self.assertRaisesRegex(ValueError, "Changed visible payer limit"):
                    check_payers.validate_page(ROOT, self.data, changed)
        self.assert_bad_page('data-payer-limit="model-costs"', 'data-payer-limit="model-costs" hidden')
        self.assert_bad_page('data-payer-limit="low-income"', 'data-payer-limit="model-costs"')

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

    def test_bar_value_labels_match_sources_without_extra_data_elements(self):
        document = check_payers.Page(self.page)
        labels = [n for n in document.nodes if "data-payer-bar-label" in n["attrs"]]
        self.assertEqual(len(labels), 8)
        self.assertEqual(len([n for n in document.nodes if n["tag"] == "data"]), 23)
        values = {v["id"]: v for v in self.data["values"]}
        for label in labels:
            vid = label["attrs"]["data-payer-bar-label"]
            self.assertEqual("".join(label["text"]), f'{values[vid]["value"]:.1f}%')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50">9.9%</span>',
                             'data-payer-bar-label="hmrc-bottom50">99.9%</span>')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50"',
                             'data-payer-bar-label="hmrc-top10"')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50"',
                             'data-payer-bar-label="hmrc-bottom50" hidden')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50"',
                             'data-payer-bar-label="hmrc-bottom50" style="display:none"')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50"',
                             'data-payer-bar-label="hmrc-bottom50" aria-hidden="true"')
        self.assert_bad_page('data-payer-bar-label="hmrc-bottom50"',
                             'data-wrong-bar-label="hmrc-bottom50"')
        # Swap equal-format labels without changing the approved table figures.
        a = 'data-payer-bar-label="hmrc-bottom50">9.9%</span>'
        b = 'data-payer-bar-label="hmrc-top10">59.1%</span>'
        swapped = self.page.replace(a, '__BAR_LABEL__', 1).replace(b, a, 1).replace('__BAR_LABEL__', b, 1)
        with self.assertRaisesRegex(ValueError, "moved away"):
            check_payers.validate_page(ROOT, self.data, swapped)

    def test_only_four_column_table_has_a_wide_minimum(self):
        # Static CSS regression contract. Real 360px layout still needs the browser gate.
        css = build_payers.STYLE
        self.assertIn('.payers table{width:100%;min-width:0;table-layout:auto}', css)
        self.assertNotIn('.payers table{min-width:34rem}', css)
        self.assertIn('.payers .payer-scroll[aria-labelledby="hmrc-table"] table,', css)
        self.assertIn('.payers .payer-scroll[aria-labelledby="ons-expenditure-table"] table'
                      '{width:100%;min-width:0;table-layout:auto}', css)
        self.assertIn('.payers .payer-scroll[aria-labelledby="ons-income-table"] table{min-width:34rem}', css)
        self.assertIn('.payers caption{white-space:normal;text-align:left;', css)
        self.assertIn('white-space:normal;overflow-wrap:anywhere}', css)

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
        self.assert_bad_page('The top 1% is part of the top 10%.', 'The groups are disjoint.')
        self.assert_bad_page('The top 10% is part of the top 50%.', '')
        self.assert_bad_page('The top 10% is part of the top 50%.', 'The top 50% is part of the top 10%.')
        self.assert_bad_page('Two official views answer different questions.',
                             'The top 50% pays 90.1%. Two official views answer different questions.')
        self.assert_bad_page('The bottom 50% and top 10% do not overlap.', 'The top 10% is inside the top 50%.')
        self.assert_bad_page('high gross income but low disposable income', 'no caveat')
        self.assert_bad_page('href="data/payers.json"', 'href="data/missing.json"')
        self.assert_bad_page('href="' + check_payers.URLS[1] + '"', 'href="#missing"')
        region = '<div class="payer-scroll" role="region" aria-labelledby="ons-income-table"'
        self.assert_bad_page(region, region.replace('"ons-income-table"', '"missing"'))
        self.assert_bad_page(region, region.replace('"ons-income-table"', '"hmrc-table"'))

    def test_each_scroll_region_names_its_own_caption(self):
        for caption_id in ("hmrc-table", "ons-income-table", "ons-expenditure-table"):
            region = f'<div class="payer-scroll" role="region" aria-labelledby="{caption_id}"'
            for wrong in ("missing", "hmrc-table" if caption_id != "hmrc-table" else "ons-income-table"):
                with self.subTest(caption=caption_id, wrong=wrong):
                    mutated = self.page.replace(region, region.replace(f'"{caption_id}"', f'"{wrong}"'), 1)
                    self.assertNotEqual(mutated, self.page)
                    with self.assertRaisesRegex(ValueError, "own caption"):
                        check_payers.validate_page(ROOT, self.data, mutated)

    def test_source_links_bind_to_panels_and_details_not_global_href_set(self):
        for sid, index, label in (("hmrc", 1, "HMRC Table 2.4 (ODS)"),
                                   ("ons", 4, "ONS reference tables (XLSX), Table 8")):
            url = check_payers.URLS[index]
            adjacent = f'<a data-payer-source="{sid}" href="{url}">{label}</a>'
            detail = f'<a data-payer-source="{sid}" href="{url}">Download the original workbook</a>'
            for anchor in (adjacent, detail):
                with self.subTest(sid=sid, anchor=anchor):
                    self.assertIn(anchor, self.page)
                    mutated = self.page.replace(anchor, anchor.replace(url, "#missing"), 1)
                    # Other valid links remain. They must not mask a broken contextual link.
                    self.assertIn(f'href="{url}"', mutated)
                    with self.assertRaisesRegex(ValueError, "workbook link"):
                        check_payers.validate_page(ROOT, self.data, mutated)
            self.assert_bad_page(f'id="{sid}-source-note"', 'id="misplaced-source-note"')
            self.assert_bad_page(f'id="{sid}-sources"', 'id="misplaced-source-details"')
            self.assert_bad_page(adjacent, adjacent.replace(f'data-payer-source="{sid}"', 'data-payer-source="wrong"'))
            self.assert_bad_page(detail, detail.replace('Download the original workbook', 'Unrelated source'))
        self.assert_bad_page('Source SHA-256: <code>' + self.data["sources"]["hmrc"]["sha256"],
                             'Source SHA-256: <code>' + '0' * 64)
        self.assert_bad_page('<code>2_4_Taxpayer_share_tax!F27</code>. Denominator:',
                             '<code>2_4_Taxpayer_share_tax!F28</code>. Denominator:')
        self.assert_bad_page('<code>Table 8!D5</code>. Denominator:',
                             '<code>Table 8!E5</code>. Denominator:')

    def test_council_reading_order_plain_definitions_and_callback_navigation(self):
        document = check_payers.Page(self.page)
        nodes = document.nodes
        main = next(n for n in nodes if n["tag"] == "main")
        navs = [n for n in nodes if n["tag"] == "nav" and n["attrs"].get("aria-label") == "Main pages"]
        self.assertEqual(len(navs), 1)
        self.assertNotIn(main, navs[0]["parents"])
        source_section = next(n for n in nodes if n["attrs"].get("id") == "payer-sources")
        tables = [n for n in nodes if n["tag"] == "table"]
        details = [n for n in nodes if n["tag"] == "details"]
        self.assertEqual(len(tables), 3)
        self.assertEqual(len(details), 3)
        source_details = [n for n in details if n["attrs"].get("id") in {"hmrc-sources", "ons-sources"}]
        self.assertEqual(len(source_details), 2)
        self.assertEqual({n["attrs"]["id"] for n in source_details}, {"hmrc-sources", "ons-sources"})
        self.assertTrue(all(n["parents"][-1] is source_section for n in source_details))
        self.assertTrue(all(nodes.index(t) < nodes.index(d) for t in tables for d in source_details))
        burden = next(n for n in nodes if n["attrs"].get("id") == "burden")
        basics = [n for n in nodes if n["attrs"].get("data-basics") == "payers"]
        self.assertEqual(len(basics), 1)
        basics = basics[0]
        self.assertEqual(basics["tag"], "aside")
        self.assertIs(basics["parents"][-1], burden)
        basics_details = [n for n in details if basics in n["parents"]]
        self.assertEqual(len(basics_details), 1)
        self.assertIs(basics_details[0]["parents"][-1], basics)
        self.assertTrue(all(nodes.index(t) < nodes.index(basics) for t in tables))
        self.assertTrue(all(nodes.index(n) < nodes.index(d) for n in nodes
                            if n is burden or burden in n["parents"] for d in source_details))
        self.assertEqual(len([n for n in nodes if n["tag"] == "h2"]), 4)
        collection_headings = [n for n in nodes if n["tag"] in {"h2", "h3"} and basics in n["parents"]]
        self.assertEqual(len(collection_headings), 1)
        self.assertEqual(collection_headings[0]["tag"], "h3")
        self.assertEqual("".join(collection_headings[0]["text"]), "How is the tax collected?")
        siblings = [n for n in nodes if n["parents"] and n["parents"][-1] is burden]
        self.assertEqual(siblings[0]["tag"], "h2")
        self.assertIs(siblings[1], basics)
        self.assertTrue(" ".join("".join(siblings[2]["text"]).split()).startswith(
            "ONS assigns final and intermediate indirect taxes fully to consumers in this model."))
        self.assert_bad_page('<h3 id="payer-basics-title">How is the tax collected?</h3>',
                             '<h2 id="payer-basics-title">How is the tax collected?</h2>')
        self.assert_bad_page('data-basics="payers"', 'data-basics="unmarked"')
        bottom = next(n for n in nodes if n["attrs"].get("id") == "bottom-group")
        ons_bars = [n for n in nodes if n["attrs"].get("data-payer-bar", "").startswith("ons-")]
        self.assertTrue(all(nodes.index(bottom) < nodes.index(n) for n in ons_bars))
        self.assert_bad_page('equivalised household disposable income.', 'household wealth.')
        self.assert_bad_page('household size and needs.', 'household size only.')
        self.assert_bad_page('tax year 2023 to 2024, estimated outturn', 'financial year ending 2024, estimated outturn')
        self.assert_bad_page('<main id="main" class="payers">',
                             '<main id="main" class="payers"><nav aria-label="Main pages"></nav>')
        # Move the complete warning after the ONS bars, with every warning word intact.
        start = self.page.index('<div class="payer-note" id="bottom-group">')
        end = self.page.index('</div>', start) + len('</div>')
        warning = self.page[start:end]
        candidate = self.page[:start] + self.page[end:]
        target = '<div class="payer-scroll" role="region" aria-labelledby="ons-income-table"'
        candidate = candidate.replace(target, warning + target, 1)
        with self.assertRaisesRegex(ValueError, "precede the bars"):
            check_payers.validate_page(ROOT, self.data, candidate)
        # Move both complete source details before the data. Their source links remain intact.
        moved = self.page
        blocks = []
        for sid in ("hmrc", "ons"):
            start = moved.index(f'<details id="{sid}-sources">')
            end = moved.index('</details>', start) + len('</details>')
            blocks.append(moved[start:end])
            moved = moved[:start] + moved[end:]
        moved = moved.replace('<section id="income-tax">', ''.join(blocks) + '<section id="income-tax">', 1)
        with self.assertRaisesRegex(ValueError, "Only the marked basics disclosure"):
            check_payers.validate_page(ROOT, self.data, moved)
        # Keep each adjacent source anchor intact, but move its note to the source section.
        for sid in ("hmrc", "ons"):
            start = self.page.index(f'<p class="source-links" id="{sid}-source-note">')
            end = self.page.index('</p>', start) + len('</p>')
            note = self.page[start:end]
            moved = self.page[:start] + self.page[end:]
            moved = moved.replace('<section id="payer-sources">', '<section id="payer-sources">' + note, 1)
            with self.subTest(sid=sid), self.assertRaisesRegex(ValueError, "source note moved"):
                check_payers.validate_page(ROOT, self.data, moved)

    def test_public_aliases_are_bound_to_raw_labels_independently(self):
        from unittest.mock import patch
        real_reader = check_payers.raw_cells(ROOT)
        # Keep numeric cells unchanged, but change labels in the independent raw reader.
        labels = (("hmrc", "2_4_Taxpayer_share_tax", "F2"),
                  ("hmrc", "2_4_Taxpayer_share_tax", "I2"),
                  ("hmrc", "2_4_Taxpayer_share_tax", "K2")) + tuple(
                      ("ons", "Table 8", cell) for cell in
                      ("D4", "E4", "F4", "G4", "H4", "B5", "B9", "B15", "B22", "A5", "A22"))
        for target in labels:
            def altered(sid, sheet, address):
                raw = real_reader(sid, sheet, address)
                if (sid, sheet, address) == target:
                    raw["value"] = "Wrong semantic label"
                return raw
            with self.subTest(target=target), patch.object(check_payers, "raw_cells", return_value=altered):
                with self.assertRaisesRegex(ValueError, "Source label does not support"):
                    check_payers.validate_data(ROOT, self.data)

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
