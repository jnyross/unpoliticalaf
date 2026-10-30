"""PESA prose-date boundary after a consistent simulated source-note refresh."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_site
import check_fiscal
import check_site
import fiscal_schema


class ForecastDate24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = check_fiscal.RawReader()
        cls.original = check_fiscal.pesa_forecast_date(cls.raw)
        cls.future = "1 April 2027"  # Simulated only; retained inputs stay intact.
        cls.data = copy.deepcopy(json.loads((ROOT / "data/spending.json").read_text()))
        cls.data["pesa_context"]["forecast_date"] = cls.future
        with patch("fiscal_schema.audit_reader", return_value=cls.moved(fiscal_schema.audit_reader())):
            fiscal_schema.enrich(cls.data)
        build_site.configure(cls.data)
        cls.pages = {"index.html": build_site.index(), "methods.html": build_site.methods()}

    @classmethod
    def moved(cls, reader):
        def read(ref):
            cell = reader(ref)
            if ref in ("4_1!B51", "4_1!B52"):
                return dict(cell, value=cell["value"].replace(cls.original, cls.future))
            return cell
        return read

    def check(self, page, name):
        check_site.check_pesa_dates(page, self.data, self.moved(self.raw), name)

    def inject(self, page, fragment):
        changed = page.replace("</main>", fragment + "</main>")
        self.assertNotEqual(changed, page)
        return changed

    def test_future_pages_have_only_the_required_source_derived_dates(self):
        self.assertEqual(check_fiscal.pesa_forecast_date(self.moved(self.raw)), self.future)
        for name, page in self.pages.items():
            self.assertNotIn(self.original, page)
            parsed = check_site.Page()
            parsed.feed(page)
            self.assertEqual(parsed.date_labels, [self.future, self.future] if name == "index.html" else [])
            self.check(page, name)

    def test_stale_full_and_month_year_prose_fails_with_or_without_forecast(self):
        for name, page in self.pages.items():
            for date in ("3 March 2026", "March 2026"):
                for wording in ("The {} forecast note", "Economic and fiscal outlook of {}"):
                    for markup in ("plain", "inline", "block", "line-break"):
                        text = wording.format(date)
                        if markup == "inline":
                            text = text.replace("March", "<em>March</em>")
                        elif markup == "block":
                            text = text.replace(date, "</p><p>" + date)
                        elif markup == "line-break":
                            text = text.replace("March", "<br>March")
                        with self.subTest(page=name, date=date, wording=wording, markup=markup):
                            with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                                self.check(self.inject(page, "<p>" + text + ".</p>"), name)

    def test_unrelated_dates_outside_the_mandatory_guards_remain_allowed(self):
        fragments = (
            "<p>PESA was published on 21 July 2026 and retrieved in October 2026.</p>",
            "<p>The archive records 3 <em>March</em> 2026 and March 2026.</p>",
            "<p>The archive records 2 April 2027.</p>",
        )
        for name, page in self.pages.items():
            for fragment in fragments:
                with self.subTest(page=name, fragment=fragment):
                    self.check(self.inject(page, fragment), name)

    def test_unmarked_current_date_fails_regardless_of_wording_or_markup(self):
        # The actual source date and a consistently moved note pair must obey
        # the same unconditional guard. These contain no forecast/outlook word.
        original_data = json.loads((ROOT / "data/spending.json").read_text())
        build_site.configure(original_data)
        original_pages = {"index.html": build_site.index(), "methods.html": build_site.methods()}
        for date, data, reader, pages in (
                (self.original, original_data, self.raw, original_pages),
                (self.future, self.data, self.moved(self.raw), self.pages)):
            for name, page in pages.items():
                for wording in ("Treasury totals use OBR {} projections.",
                                "PESA aggregate values are dated {}.",
                                "The archive records {}.",
                                "PESA outturn notes were dated {}."):
                    month = date.split()[1]
                    for rendered_date in (date, date.replace(month, "<em>" + month + "</em>"),
                                          "</p><p>" + date, date.replace(month, "<br>" + month)):
                        fragment = "<p>" + wording.format(rendered_date) + "</p>"
                        with self.subTest(page=name, date=date, fragment=fragment):
                            with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                                check_site.check_pesa_dates(self.inject(page, fragment), data, reader, name)

    def test_obr_mentions_never_exempt_stale_forecast_prose(self):
        # No PESA/Treasury keyword is needed. OBR headings and captions without
        # punctuation must not grant an exemption to a following paragraph.
        for name, page in self.pages.items():
            for date in ("3 March 2026", "March 2026"):
                fragments = [
                    "<p>The {} forecast note above applies to these totals, not the OBR historical databank.</p>".format(d)
                    for d in (date, date.replace("March", "<em>March</em>"),
                              "</p><p>" + date, date.replace("March", "<br>March"))
                ]
                fragments.extend(prefix + "<p>The " + date + " forecast note applies to these totals.</p>"
                                 for prefix in ("<h2>OBR historical databank</h2>",
                                                "<figure><figcaption>OBR historical databank</figcaption></figure>",
                                                "<p>The OBR historical</p><p>databank</p>"))
                fragments.append("<p>The OBR historical</p><p>databank names the " + date + " forecast.</p>")
                for fragment in fragments:
                    with self.subTest(page=name, fragment=fragment):
                        with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                            self.check(self.inject(page, fragment), name)

    def test_obr_history_cannot_hide_a_pesa_or_outlook_claim(self):
        fragments = (
            "<p>The OBR historical databank differs from the PESA March 2026 forecast.</p>",
            "<p>The OBR historical notes cite Economic and fiscal outlook of 3 March 2026.</p>",
            "<p>The OBR historical databank notes name March 2026 and October 2026 forecasts.</p>",
        )
        for name, page in self.pages.items():
            for fragment in fragments:
                with self.subTest(page=name, fragment=fragment):
                    with self.assertRaisesRegex(ValueError, "PESA.*date|PESA.*vintage"):
                        self.check(self.inject(page, fragment), name)


if __name__ == "__main__":
    unittest.main()
