"""Person-analysis household means cannot establish once-per-household tax totals."""
import csv
import hashlib
import io
import json
import re
import unittest

import openpyxl

from builder import downloads
from builder.build import render
from builder.data import Facts, who_pays
from builder.readers import ROOT

WITHDRAWN_PREFIXES = ("etb.2a.hhtax.", "etb.2a.taxshare.")


class HouseholdTaxShares(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts, _, cls.pages, _ = render()

    def test_person_ranked_means_are_not_household_totals(self):
        self.assertEqual(
            [fid for fid in self.facts if fid.startswith(WITHDRAWN_PREFIXES)], []
        )
        for fact in self.facts.values():
            self.assertFalse(any(i.startswith(WITHDRAWN_PREFIXES) for i in fact.inputs))

    def test_supported_means_explain_person_weighting(self):
        for group in ("q1", "q2", "q3", "q4", "q5", "all"):
            for measure in ("gross", "direct", "indirect", "alltax"):
                fact = self.facts[f"etb.2a.{measure}.{group}"]
                self.assertIsNotNone(fact.value)
                self.assertIn("person-weighted", fact.note)

    def test_current_pages_and_downloads_do_not_reuse_withdrawn_claims(self):
        for path, page in self.pages.items():
            for prefix in WITHDRAWN_PREFIXES:
                self.assertNotIn(f'data-fact="{prefix}', page, path)
                self.assertNotIn(f'"{prefix}', page, path)
        for path, csv_text in downloads.FILES.items():
            if path.startswith("csv/who-pays/"):
                self.assertNotIn("Share of all household taxes", csv_text, path)
                self.assertNotIn("46.0%", csv_text, path)
                self.assertNotIn("44.93", csv_text, path)
        page = self.pages["who-pays.html"]
        key_figures = re.search(r'<ul class="keyfigs">(.*?)</ul>', page, re.S).group(1)
        self.assertIn("Not established", key_figures)
        self.assertIn("claim is withdrawn", key_figures)
        self.assertIn('id="richest-share"', page)  # preserve the public fragment
        self.assertIn("does not establish the richest fifth", page)
        self.assertIn('href="corrections.html"', page)
        self.assertIn('href="figures/etb.html', page)

    def test_six_supported_rows_match_the_adjacent_csv(self):
        page = self.pages["who-pays.html"]
        hrefs = re.findall(r'href="(csv/who-pays/[^"]+)"', page)
        tables = [
            list(csv.reader(io.StringIO(downloads.FILES[href].lstrip("\ufeff"))))
            for href in hrefs
        ]
        rows = next(rows for rows in tables if rows[0] == [
            "Fifth of people", "Gross income", "Direct taxes", "Indirect taxes", "All taxes"
        ])
        self.assertEqual(len(rows), 7)
        for row, group in zip(rows[1:], ("q1", "q2", "q3", "q4", "q5", "all")):
            for shown, measure in zip(row[1:], ("gross", "direct", "indirect", "alltax")):
                self.assertEqual(shown, f"£{self.facts[f'etb.2a.{measure}.{group}'].value:,.0f}")
        self.assertIn("person-weighted", page.lower())

    def test_question_keeps_intent_but_withdraws_unsupported_answer(self):
        questions = json.loads((ROOT / "docs/johns-questions/questions.json").read_text())
        group = next(q for q in questions["questions"] if q["id"] == "J4")
        probe = next(p for p in group["probes"] if p["id"] == "J4.3")
        self.assertIn("all taxes", probe["question"])
        self.assertIn("does not establish", probe["options"][probe["answer"]])
        self.assertIn("46.0%", probe["history"][0]["question"])
        self.assertIn("withdrawn", probe["history"][0]["reason"])
        self.assertNotIn("paid 46.0%", probe["why"])

    def test_correction_records_error_and_actual_withdrawal(self):
        page = self.pages["corrections.html"]
        self.assertIn("6 November 2026", page)
        self.assertIn("person-weighted", page)
        self.assertIn("withdrawn", page)
        self.assertIn("46.0%", page)
        self.assertIn("2 November 2026", page)  # retain the earlier corrections


class Table2aSourcePopulation(unittest.TestCase):
    def test_independent_six_column_reopening(self):
        path = ROOT / "data/payers/raw/ons-etb-fye2024.xlsx"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "2e38c1694d922427509879b9553a4c3473b8ba1174898c2dd414668ecbb2bf73",
        )
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        try:
            ws = wb["Table 2a"]
            for row in (1, 3, 4, 8, 9, 48, 70):
                print("Table 2a", row, [ws.cell(row, col).value for col in range(1, 9)])
            for name in wb.sheetnames:
                if "note" in name.lower():
                    for row in wb[name].iter_rows():
                        line = " ".join(str(c.value) for c in row if c.value is not None)
                        if any(word in line.lower() for word in ("individual", "rank", "weight")):
                            print(name, row[0].coordinate, line)
            expected = {
                8: [13405, 13449, 13427, 13426, 13429, 67135],
                9: [5875, 5902, 5559, 5298, 5806, 28440],
                48: [3696, 6308, 10482, 17012, 41215, 15743],
                70: [4929, 6072, 6856, 8268, 10688, 7363],
            }
            for row, values in expected.items():
                self.assertEqual([ws.cell(row, col).value for col in range(3, 9)], values)
            self.assertIn("all individuals", ws["A1"].value)
            self.assertIn("Number of individuals", ws["B8"].value)
            self.assertIn("Number of households", ws["B9"].value)
            note = next(
                " ".join(str(v) for v in row if v is not None)
                for row in wb["Notes"].iter_rows(values_only=True)
                if row[0] == "note 3"
            )
            self.assertIn("ranking individuals by equivalised household disposable income", note)
            bulletin = (ROOT / "data/fetched/explain/ons-etb-latest.html").read_text()
            self.assertIn("The mean measure of income divides the total income of individuals by the number of individuals.", bulletin)
            facts = Facts()
            who_pays(facts)
            for col, group in zip(range(3, 9), ("q1", "q2", "q3", "q4", "q5", "all")):
                for row, measure in ((8, "people"), (9, "households"), (48, "direct"), (70, "indirect")):
                    fact = facts[f"etb.2a.{measure}.{group}"]
                    self.assertEqual(fact.value, ws.cell(row, col).value)
                    self.assertEqual(fact.locator, f"Table 2a!{ws.cell(row, col).coordinate}")
                    self.assertEqual(fact.period, "2023/24")
            self.assertEqual(
                [ws.cell(48, col).value for col in range(3, 9)],
                [3696, 6308, 10482, 17012, 41215, 15743],
            )
            means = [ws.cell(48, col).value for col in range(3, 8)]
            households = [ws.cell(9, col).value for col in range(3, 8)]
            household_weighted = sum(m * h for m, h in zip(means, households)) / sum(households)
            self.assertGreater(abs(household_weighted - ws["H48"].value), 30)
            # Published All individuals is a separate source column, not a
            # count-weighted reconstruction. Counts are rounded (people sum
            # to 67,136 thousand, versus the published 67,135 thousand).
            self.assertEqual(sum(expected[8][:5]) - expected[8][5], 1)
            for row in (48, 70):
                means = expected[row][:5]
                household_weighted = sum(m * h for m, h in zip(means, households)) / sum(households)
                people = expected[8][:5]
                person_weighted = sum(m * p for m, p in zip(means, people)) / sum(people)
                print("Row", row, "published All individuals", expected[row][5],
                      "household-weighted (unsupported)", household_weighted,
                      "person-weighted", person_weighted)
                # Pound-rounded means and thousand-rounded population counts
                # cannot reproduce an all-population mean to the penny.
                self.assertAlmostEqual(person_weighted, expected[row][5], delta=1.5)
                self.assertGreater(abs(household_weighted - expected[row][5]), 20)
        finally:
            wb.close()
