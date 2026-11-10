"""Independent retained-source and population checks for existing life topics."""

import csv
import json
import unittest
import warnings
from unittest.mock import patch

from builder import data, pages_life, uncertainty
from builder.html import Num
from builder.readers import ROOT


class MissingDenominators(unittest.TestCase):
    def test_suppressed_occupation_total_is_not_a_share(self):
        read_rows = data.csv_rows

        def suppressed_rows(path):
            rows = read_rows(path)
            if path.endswith("aps218-uk-calendar-annual.csv"):
                rows = [dict(row) for row in rows]
                for row in rows:
                    if row["SOC2020_FULL"] == "0":
                        row["OBS_VALUE"] = "!"
            return rows

        facts = data.Facts()
        with patch.object(data, "csv_rows", side_effect=suppressed_rows):
            data.work(facts)
        shares = [fact for fid, fact in facts.items() if fid.startswith("work.occshare.SOC2020.")]
        self.assertTrue(shares)
        self.assertTrue(all(fact.value is None for fact in shares))

    def test_missing_child_household_total_is_not_zero_or_a_share(self):
        read_sheets = data.ods

        def suppressed_sheets(path):
            sheets = read_sheets(path)
            if "FT1241_" in path:
                sheets = {name: [list(row) for row in rows] for name, rows in sheets.items()}
                for rows in sheets.values():
                    for row in rows:
                        if row and str(row[0]) == "2024-25" and len(row) > 6:
                            row[6] = None
            return sheets

        facts = data.Facts()
        with patch.object(data, "ods", side_effect=suppressed_sheets):
            data.housing(facts)
        self.assertIn("house.kidsk.couple.couple.all.2024", facts)
        for tenure in ("owners", "social", "private"):
            self.assertIsNone(facts[f"house.kids.{tenure}.2024"].value)

    def test_zero_and_missing_share_inputs_remain_missing(self):
        for part, total in ((3, 0), (None, 5), (3, None)):
            self.assertIsNone(data._share_of_total(part, total))
        self.assertIsNone(data._complete_sum([3, None, 7]))
        self.assertEqual(data._share_of_total(0, 5), 0)


class LifeConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for state in (uncertainty.MARGINS, uncertainty.INFO):
            preserved = patch.dict(state)
            preserved.start()
            cls.addClassCleanup(preserved.stop)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = data.build_all()
        pages_life.init(cls.d)
        uncertainty.add_facts(cls.facts, cls.d)

    def test_earnings_page_documents_the_ons_lineage_not_a_new_survey(self):
        from builder.sources import all_sources

        html = pages_life.topic_page(self.facts, self.d, Num(self.facts), all_sources(), "earnings")
        self.assertIn("Both routes publish the same ONS Annual Survey of Hours and Earnings", html)
        self.assertIn("https://www.nomisweb.co.uk/datasets/asher", html)
        self.assertIn("UK totals do not depend on where within the UK employees live or work", html)

    def test_home_year_coverage_is_not_the_latest_full_year_holiday_period(self):
        from builder.build import render

        with patch.dict(uncertainty.MARGINS), patch.dict(uncertainty.INFO):
            _, _, pages, _ = render()
        html = pages["index.html"]
        self.assertIn("Pick any year from 1971 to 2026", html)
        self.assertIn("See any two years from 1971 to 2026", html)
        self.assertEqual(html.count("The year pages run to 2026"), 2)
        self.assertNotIn("The year pages stop at 2025", html)
        self.assertIn('data-fact="hol.world.holiday.2025"', html)
        self.assertNotIn('data-fact="hol.world.holiday.2026"', html)

    def test_2026_work_reopens_every_supported_split_at_q2(self):
        expected = {
            "rate": ("lf24", 75.1),
            "men": ("mgsv", 78.0),
            "women": ("lf25", 72.3),
            "level": ("mgrz", 34469),
            "ft": ("ycbe", 25746),
            "pt": ("ycbh", 8724),
            "age.18_24": ("ybud", 59.1),
            "age.25_34": ("ybug", 84.5),
            "age.35_49": ("ybuj", 85.1),
            "age.50_64": ("lf2u", 72.2),
            "age.65": ("lfk6", 13.3),
        }
        for key, (code, value) in expected.items():
            with (ROOT / f"data/fetched/ons/{code}.csv").open() as stream:
                rows = dict(csv.reader(stream))
            self.assertEqual(float(rows["2026 Q2"]), value, code)
            fact = self.facts[f"work.{key}.2026"]
            self.assertEqual(fact.value, value)
            self.assertEqual(fact.period, "April to June 2026")
            self.assertEqual(fact.locator, f"{code.upper()} row '2026 Q2'")
            self.assertEqual(fact.status, "published")
        self.assertIn("16 to 64", self.facts["work.rate.2026"].note)
        self.assertIn("16 and over", self.facts["work.level.2026"].note)
        self.assertAlmostEqual(self.facts["work.ptshare.2026"].value, 100 * 8724 / (25746 + 8724))
        self.assertFalse(any(k.startswith("work.occ.") and k.endswith(".2026") for k in self.facts))
        self.assertFalse(
            any(k.startswith("work.place.") and k.endswith(".2026") for k in self.facts)
        )

    def test_nomis_join_has_matching_ons_bulletin_values_at_source_precision(self):
        from decimal import Decimal, ROUND_HALF_UP

        with (ROOT / "data/fetched/ons/ashe-2025-fig1.csv").open() as stream:
            bulletin = {
                row[0]: row[1:] for row in csv.reader(stream) if row and row[0] in ("2024", "2025")
            }
        with (ROOT / "data/fetched/nomis/ashe-resident-uk-median-weekly.csv").open() as stream:
            nomis = list(csv.DictReader(stream))
        for year in ("2024", "2025"):
            for code, column in (("7", 0), ("8", 1), ("9", 2)):
                row = next(
                    row
                    for row in nomis
                    if row["DATE_NAME"] == year
                    and row["SEX"] == code
                    and row["MEASURES_NAME"] == "Value"
                )
                rounded = Decimal(bulletin[year][column]).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                self.assertEqual(Decimal(row["OBS_VALUE"]), rounded, (year, code))
        # The overlap is 2024 revised/2025 provisional; current 2025 pay uses its later revision.
        self.assertEqual(self.facts["earn.ft.2024"].source, "nomis-ashe-resident")
        self.assertEqual(self.facts["earn.ft.2025"].source, "ashe-2025-table1-revised")
        self.assertEqual(self.facts["earn.pt.2025"].value, 279.9)

    def test_every_dfe_phase_and_band_uses_pupils_not_classes_as_share_denominator(self):
        path = ROOT / "data/life/sources/schools/dfe-national-class-sizes-1.0.json"
        rows = json.loads(path.read_text())["results"]
        phases = {"TaWMP": "infant", "cDwC3": "ks2", "5kyxd": "primary", "tfHTE": "secondary"}
        bands = {"zeoRF": "le30", "kxKDh": "31to35", "u2cKo": "36plus", "XdTUf": "total"}
        cells = {}
        for i, row in enumerate(rows):
            y = int(row["timePeriod"]["period"][-4:])
            phase, band = phases[row["filters"]["5cGdi"]], bands[row["filters"]["cAd31"]]
            pupils, classes = float(row["values"]["QtxWw"]), float(row["values"]["EAicq"])
            cells[phase, band, y] = pupils, classes
            fact = self.facts[f"school.pupils.{phase}.{band}.{y}"]
            self.assertEqual(fact.value, pupils)
            self.assertEqual(fact.locator, f"results[{i}] values.QtxWw")
            self.assertEqual(fact.period, f"January {y} census ({y - 1}/{str(y)[2:]} school year)")
            if band == "total":
                self.assertEqual(
                    self.facts[f"school.{phase}.{y}"].value, round(pupils / classes, 1)
                )
        self.assertEqual(len(cells), 176)
        for phase, band, y in cells:
            if band != "total":
                continue
            large = cells[phase, "31to35", y][0] + cells[phase, "36plus", y][0]
            self.assertAlmostEqual(
                self.facts[f"school.large.{phase}.{y}"].value,
                100 * large / cells[phase, "total", y][0],
            )
        self.assertEqual(self.facts["school.primary.2026"].value, 26.1)
        self.assertEqual(self.facts["school.secondary.2026"].value, 22.6)
        self.assertFalse(any(k.startswith("school.uk.") for k in self.facts))

    def test_retained_travel_2020_spending_and_nights_are_explicitly_missing(self):
        import openpyxl

        wb = openpyxl.load_workbook(
            ROOT / "data/fetched/ott/section3-2019to2023.xlsx", data_only=True
        )
        for sheet, key in (("3", "spend"), ("4", "nights")):
            row = next(
                row for row in wb[sheet].values if row[:2] == ("Total World", "Holiday - All")
            )
            self.assertEqual(row[3], "Not available")
            self.assertIsNone(self.facts[f"hol.{key}.holiday.2020"].value)
            self.assertEqual(self.facts[f"hol.{key}.holiday.2020"].status, "missing")
        self.assertNotIn("hol.spendper.2020", self.facts)
        self.assertEqual(
            self.facts["hol.world.holiday.2020.part"].period, "January to mid-March 2020"
        )
        for y in (2024, 2025):
            self.assertIn("Great Britain residents", self.facts[f"hol.world.holiday.{y}"].note)
        self.assertEqual(pages_life.hol_basis(2023), "UK")
        self.assertEqual(pages_life.hol_basis(2024), "GB, mixed methods")
        self.assertEqual(pages_life.hol_basis(2025), "GB")

    def test_direct_life_source_population_reopens_originals(self):
        from builder.check import cell_value, as_number
        from builder.sources import all_sources

        sources = all_sources()
        checked = 0
        cache = {}
        for fid, fact in self.facts.items():
            if not fid.startswith(
                ("work.", "house.", "school.", "hol.", "jobs.", "afford.", "holafford.")
            ):
                continue
            if fact.status in ("calculated", "missing") or not fact.locator or fact.value is None:
                continue
            raw = as_number(cell_value(sources[fact.source]["file"], fact.locator, cache))
            self.assertIsNotNone(raw, fid)
            expected = raw * fact.scale
            if fact.source == "dfe_api":
                expected = round(expected, 1)
            self.assertAlmostEqual(
                fact.value, expected, delta=max(1e-9, abs(fact.value) * 1e-9), msg=fid
            )
            checked += 1
        self.assertEqual(checked, 6142)


if __name__ == "__main__":
    unittest.main()
