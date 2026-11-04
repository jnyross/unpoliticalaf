"""Extract every figure the site shows from the retained official files.

Each figure becomes a Fact: a value plus where exactly it came from (source id
and cell or row locator), its period, unit and status. Derived figures (shares,
real-terms values, changes) record their formula and the facts they use.
Nothing is filled in: a missing source value stays missing (None).
"""
import csv
import io
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from .readers import ROOT, xlsx, ods, ref, ons_series, csv_rows, pdf_number

YEARS = list(range(2008, 2026))  # year explorer range (calendar years)
# Years before the explorer's full range. Only some series reach back this far;
# their figures are read by history() and shown on the topic pages and the
# earlier-year pages, each with its own survey and break.
EARLY_YEARS = list(range(1971, 2008))


@dataclass
class Fact:
    id: str
    value: Optional[float]
    unit: str
    period: str
    source: str
    locator: str
    status: str = "published"
    note: str = ""
    formula: str = ""
    inputs: list = field(default_factory=list)
    scale: float = 1  # value = source cell × scale (e.g. 0.001 when a source in units is shown in thousands)


class Facts(dict):
    def add(self, fact):
        if fact.id in self:
            raise ValueError(f"duplicate fact id {fact.id}")
        self[fact.id] = fact
        return fact

    def get_value(self, fid):
        return self[fid].value

    def to_json(self):
        return [asdict(f) for f in self.values()]


def num(v):
    """Turn a source cell into a number, or None for blanks and markers."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").lstrip("±").strip()  # "± 0.4": a published margin of error
    if s in ("", "-", "..", "x", "u", "n/a", "*", "Not available", "[x]", "[c]", "[not available]"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def find_row(rows, label, col=0, start=0, exact=False):
    for i in range(start, len(rows)):
        cell = rows[i][col] if col < len(rows[i]) else None
        if cell is None:
            continue
        text = str(cell).strip()
        if (text == label) if exact else text.startswith(label):
            return i
    raise KeyError(label)


# ---------------------------------------------------------------- spending

FUNCTIONS = [
    # (key, plain name, PESA row label prefix)
    ("social", "Social protection (pensions, benefits, social care)", "10. Social protection"),
    ("health", "Health", "7. Health"),
    ("general", "General public services (incl. debt interest)", "1. General public services"),
    ("education", "Education", "9. Education"),
    ("economic", "Economic affairs (incl. transport)", "4. Economic affairs"),
    ("defence", "Defence", "2. Defence"),
    ("order", "Public order and safety (police, courts, prisons, fire)", "3. Public order and safety"),
    ("housing", "Housing and community amenities", "6. Housing and community amenities"),
    ("environment", "Environment protection", "5. Environment protection"),
    ("recreation", "Recreation, culture and religion", "8. Recreation, culture and religion"),
    ("eu", "EU transactions", "EU transactions"),
]
SUBITEMS = [
    ("debt_interest", "Interest on government debt (inside general public services)", "of which: public sector debt interest"),
    ("transport", "Transport (inside economic affairs)", "of which: transport"),
]


def spending(facts):
    path = "data/raw/PESA_2026_CP_Chapter_4_tables.xlsx"
    wb = xlsx(path)
    out = {"years": [], "views": {}}
    for view, sheet, unit in (("cash", "4_2", "£bn"), ("real", "4_3", "£bn (2025-26 prices)"), ("gdp", "4_4", "% of GDP")):
        ws = wb[sheet]
        rows = [[c.value for c in r] for r in ws.iter_rows()]
        header = rows[4]
        years = [(j, str(v)) for j, v in enumerate(header) if v and re.fullmatch(r"\d{4}-\d{2}", str(v))]
        out["years"] = [y for _, y in years]
        series = {}
        for key, name, label in FUNCTIONS + SUBITEMS + [("services", "Spending on services", "Public sector expenditure on services"),
                                                       ("adjustments", "Accounting adjustments", "Accounting adjustments"),
                                                       ("tme", "Total managed expenditure", "Total Managed Expenditure")]:
            i = find_row(rows, label)
            vals = {}
            for j, y in years:
                fid = f"spend.{view}.{key}.{y}"
                facts.add(Fact(fid, num(rows[i][j]), unit, y, "pesa4", f"{sheet}!{ref(i, j)}", "outturn"))
                vals[y] = fid
            series[key] = {"name": name, "values": vals}
        out["views"][view] = {"unit": unit, "series": series, "sheet": sheet}
    latest = out["years"][-1]
    out["latest"] = latest
    # Shares of spending on services, per £100 (calculated)
    total = facts[f"spend.cash.services.{latest}"]
    shares = {}
    for key, name, _ in FUNCTIONS:
        part = facts[f"spend.cash.{key}.{latest}"]
        fid = f"spend.per100.{key}.{latest}"
        facts.add(Fact(fid, 100 * part.value / total.value, "£ per £100", latest, "pesa4", part.locator,
                       "calculated", formula=f"100 × {part.id} ÷ {total.id}", inputs=[part.id, total.id]))
        shares[key] = fid
    for key, name, _ in SUBITEMS:
        part = facts[f"spend.cash.{key}.{latest}"]
        fid = f"spend.per100.{key}.{latest}"
        facts.add(Fact(fid, 100 * part.value / total.value, "£ per £100", latest, "pesa4", part.locator,
                       "calculated", formula=f"100 × {part.id} ÷ {total.id}", inputs=[part.id, total.id]))
        shares[key] = fid
    out["per100"] = shares
    # State pension detail from Table 5.2 (social protection: old age)
    path5 = "data/raw/PESA_2026_CP_Chapter_5_tables.xlsx"
    rows5 = [[c.value for c in r] for r in xlsx(path5)["5_2"].iter_rows()]
    hdr = rows5[4]
    col = max(j for j, v in enumerate(hdr) if v == latest)
    i = find_row(rows5, "of which: pensions", col=1, start=find_row(rows5, "10.2 Old age", col=1))
    facts.add(Fact(f"spend.oldage.{latest}", num(rows5[i][col]) / 1000, "£bn", latest, "pesa5", f"5_2!{ref(i, col)}", "outturn", scale=0.001,
                   note="Old age: of which pensions. Table 5.2 is in £ million; shown here in £ billion."))
    out["oldage"] = f"spend.oldage.{latest}"
    return out


# ---------------------------------------------------------------- receipts

TAX_GROUPS = [
    # key, plain name, OBR column headers (summed), notes
    ("income_tax", "Income Tax", ["Pay as your earn (PAYE) income tax", "Self assessed (SA) income tax", "Other income tax"]),
    ("nics", "National Insurance contributions", ["National insurance contributions (NICs)"]),
    ("vat", "VAT", ["VAT (net of VAT refunds)"]),
    ("corp", "Corporation Tax", ["Onshore corporation tax (includes Bank Surcharge and EGL)3", "Offshore corporation tax"]),
    ("council", "Council Tax", ["Council tax"]),
    ("fuel", "Fuel duties", ["Fuel duties"]),
    ("cgt", "Capital Gains Tax", ["Capital gains tax"]),
    ("stamp", "Stamp duties on property and shares", ["Stamp duty land tax (includes Scottish LBTT and ATED)", "Stamp taxes on shares"]),
    ("alcohol_tobacco", "Alcohol and tobacco duties", ["Alcohol duties", "Tobacco duties"]),
    ("iht", "Inheritance Tax", ["Inheritance tax"]),
]


def receipts(facts):
    path = "data/raw/OBR_Public_finances_databank_October_2026.xlsx"
    wb = xlsx(path)
    rows = [[c.value for c in r] for r in wb["Receipts (£bn)"].iter_rows()]
    head = rows[3]
    cols = {str(v).strip(): j for j, v in enumerate(head) if v}
    year_rows = {str(r[1]): i for i, r in enumerate(rows) if len(r) > 1 and r[1] and re.fullmatch(r"\d{4}-\d{2}", str(r[1]))}
    note = " ".join(str(r[1] or r[0] or "") for r in rows[39:43])
    # Forecast years start from 2026-27 in this vintage (sheet note row 41).
    forecast_from = "2026-27"
    out = {"years": list(year_rows), "groups": [], "forecast_from": forecast_from}

    def status(y):
        return "forecast" if y >= forecast_from else "outturn"

    def cellfact(fid, colname, y, label=None):
        i, j = year_rows[y], cols[colname]
        return facts.add(Fact(fid, num(rows[i][j]), "£bn", y, "obr", f"Receipts (£bn)!{ref(i, j)}", status(y), note=label or colname))

    for y in year_rows:
        cellfact(f"rec.total.{y}", "Public sector current receipts", y)
        cellfact(f"rec.taxes.{y}", "National accounts taxes", y)
        cellfact(f"rec.vatrefunds.{y}", "VAT refunds", y)
        t, tx = facts[f"rec.total.{y}"], facts[f"rec.taxes.{y}"]
        facts.add(Fact(f"rec.nontax.{y}", t.value - tx.value, "£bn", y, "obr", t.locator, "calculated",
                       formula=f"{t.id} − {tx.id}", inputs=[t.id, tx.id]))
        listed = 0
        for key, name, colnames in TAX_GROUPS:
            ids = []
            for k, c in enumerate(colnames):
                ids.append(cellfact(f"rec.part.{key}.{k}.{y}", c, y).id)
            v = sum(facts[i].value for i in ids)
            facts.add(Fact(f"rec.{key}.{y}", v, "£bn", y, "obr", ", ".join(facts[i].locator for i in ids),
                           "calculated" if len(ids) > 1 else status(y), formula=" + ".join(ids) if len(ids) > 1 else "", inputs=ids if len(ids) > 1 else []))
            listed += v
        facts.add(Fact(f"rec.othertax.{y}", tx.value - listed, "£bn", y, "obr", tx.locator, "calculated",
                       formula=f"{tx.id} − (" + " + ".join(f"rec.{k}.{y}" for k, _, _ in TAX_GROUPS) + ")", inputs=[tx.id] + [f"rec.{k}.{y}" for k, _, _ in TAX_GROUPS]))
    out["groups"] = [(k, n) for k, n, _ in TAX_GROUPS]
    # Aggregates: borrowing, spending, debt (OBR basis)
    rows = [[c.value for c in r] for r in wb["Aggregates (£bn)"].iter_rows()]
    head = [str(v).strip() if v else "" for v in rows[3]]
    yrows = {str(r[1]): i for i, r in enumerate(rows) if len(r) > 1 and r[1] and re.fullmatch(r"\d{4}-\d{2}", str(r[1]))}
    want = {"receipts": "Public sector current receipts", "tme": "Total managed expenditure", "psnb": "Public sector net borrowing",
            "psnd": "Public sector net debt", "gdpcash": "Nominal GDP (£ billion)", "deflator": "GDP Deflator (2025-26=100)"}
    found = {}
    for key, label in want.items():
        js = [j for j, h in enumerate(head) if h.startswith(label)]
        if js:
            found[key] = js[0]
    units = {"deflator": "index, 2025-26 = 100"}
    for y, i in yrows.items():
        for key, j in found.items():
            src = "obr-prices" if key in ("receipts", "tme", "gdpcash", "deflator") else "obr"
            facts.add(Fact(f"agg.{key}.{y}", num(rows[i][j]), units.get(key, "£bn"), y, src, f"Aggregates (£bn)!{ref(i, j)}", status(y), note=head[j]))
    out["agg_years"] = list(yrows)
    out["agg_keys"] = list(found)
    # Real terms (2025-26 prices) with the OBR's GDP deflator, and shares of GDP for
    # single taxes, so the money pages can switch between cash, real terms and % of GDP.
    out["real_years"] = []
    for y in yrows:
        dfl = facts[f"agg.deflator.{y}"]
        if dfl.value is None:
            continue
        out["real_years"].append(y)
        for key in ("receipts", "tme"):
            c = facts[f"agg.{key}.{y}"]
            if c.value is not None:
                facts.add(Fact(f"agg.real.{key}.{y}", c.value * 100 / dfl.value, "£bn (2025-26 prices)", y, "obr-prices", c.locator, "calculated",
                               formula=f"{c.id} × 100 ÷ {dfl.id}", inputs=[c.id, dfl.id]))
    for y in out["years"]:
        dfl, gdp = facts.get(f"agg.deflator.{y}"), facts.get(f"agg.gdpcash.{y}")
        for key in ("income_tax", "nics", "vat", "taxes"):
            c = facts[f"rec.{key}.{y}"]
            if dfl is not None and dfl.value is not None:
                facts.add(Fact(f"rec.real.{key}.{y}", c.value * 100 / dfl.value, "£bn (2025-26 prices)", y, "obr-prices", c.locator, "calculated",
                               formula=f"{c.id} × 100 ÷ {dfl.id}", inputs=[c.id, dfl.id]))
            if gdp is not None and gdp.value is not None:
                facts.add(Fact(f"rec.gdp.{key}.{y}", 100 * c.value / gdp.value, "% of GDP", y, "obr-prices", c.locator, "calculated",
                               formula=f"100 × {c.id} ÷ {gdp.id}", inputs=[c.id, gdp.id]))
    # Receipts as % of GDP, long history (outturn and forecast marked)
    rows = [[c.value for c in r] for r in wb["Aggregates (per cent of GDP)"].iter_rows()]
    head = [str(v).strip() if v else "" for v in rows[3]]
    yrows = {str(r[1]): i for i, r in enumerate(rows) if len(r) > 1 and r[1] and re.fullmatch(r"\d{4}-\d{2}", str(r[1]))}
    for key, label in (("receipts", "Public sector current receipts"), ("tme", "Total managed expenditure"), ("psnb", "Public sector net borrowing"), ("psnd", "Public sector net debt")):
        js = [j for j, h in enumerate(head) if h.startswith(label)]
        if not js:
            continue
        for y, i in yrows.items():
            facts.add(Fact(f"gdp.{key}.{y}", num(rows[i][js[0]]), "% of GDP", y, "obr", f"Aggregates (per cent of GDP)!{ref(i, js[0])}", status(y), note=head[js[0]]))
    out["gdp_years"] = list(yrows)
    return out


# ---------------------------------------------------------------- who pays

def who_pays(facts):
    sheets = ods("data/payers/raw/hmrc-table24-july2026.ods")
    rows = sheets["2_4_Taxpayer_share_tax"]
    head = rows[1]
    groups = {"top1": "Top 1% percentile group", "top10": "Top 10% percentile group", "top50": "Top 50% percentile group", "bottom50": "Bottom 50% percentile group"}
    out = {"hmrc_years": [], "hmrc": {}}
    for i, r in enumerate(rows[2:], start=2):
        if not r or not re.fullmatch(r"\d{4} to \d{4}", str(r[0])):
            continue
        y = str(r[0])
        start = int(y[:4])
        st = "projection" if start >= 2024 else "outturn"
        out["hmrc_years"].append(y)
        for key, label in groups.items():
            j = head.index(label)
            facts.add(Fact(f"hmrc.share.{key}.{y}", num(r[j]), "% of all Income Tax", y, "hmrc24", f"2_4_Taxpayer_share_tax!{ref(i, j)}", st))
        j = len(head) - 1
        facts.add(Fact(f"hmrc.total.{y}", num(r[j]), "£bn", y, "hmrc24", f"2_4_Taxpayer_share_tax!{ref(i, j)}", st))
    # income shares of the same groups, before tax
    rows = sheets["2_4_Taxpayer_share_inc_pretax"]
    for i, r in enumerate(rows[2:], start=2):
        if not r or not re.fullmatch(r"\d{4} to \d{4}", str(r[0])):
            continue
        y = str(r[0])
        st = "projection" if int(y[:4]) >= 2024 else "outturn"
        for key, label in groups.items():
            j = rows[1].index(label)
            facts.add(Fact(f"hmrc.income.{key}.{y}", num(r[j]), "% of all taxpayers' income", y, "hmrc24", f"2_4_Taxpayer_share_inc_pretax!{ref(i, j)}", st))
    rows = sheets["2_4_Taxpayer_inc_quantiles"]
    for i, r in enumerate(rows[2:], start=2):
        if r and str(r[0]) == "2023 to 2024":
            for key, label in (("top1", "Top 1% percentile group"), ("top10", "Top 10% percentile group"), ("top50", "Top 50% percentile group")):
                j = rows[1].index(label)
                facts.add(Fact(f"hmrc.threshold.{key}", num(r[j]), "£ a year", "2023 to 2024", "hmrc24", f"2_4_Taxpayer_inc_quantiles!{ref(i, j)}", "outturn"))
    out["hmrc_latest_outturn"] = "2023 to 2024"
    # ETB Table 2a: average household income and taxes for fifths of individuals,
    # ranked by equivalised household disposable income (ONS note 3)
    wb = xlsx("data/payers/raw/ons-etb-fye2024.xlsx")
    rows = [[c.value for c in r] for r in wb["Table 2a"].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r and any(str(v).strip() == "Bottom" for v in r if v))
    hdr = rows[hdr_i]
    qcols = {q: next(j for j, v in enumerate(hdr) if v and str(v).strip() == lab) for q, lab in
             (("q1", "Bottom"), ("q2", "2nd"), ("q3", "3rd"), ("q4", "4th"), ("q5", "Top"), ("all", "All individuals"))}

    def etb_row(label):
        for i, r in enumerate(rows):
            if len(r) > 1 and r[1] and str(r[1]).strip() == label:
                return i
        raise KeyError(label)
    out["etb"] = {}
    for key, label in (("gross", "Gross income"), ("direct", "Total direct taxes"), ("indirect", "Total indirect taxes"), ("disposable", "Disposable income"),
                       ("original", "Total original income"), ("benefits_cash", "Total cash benefits"), ("households", "Number of households in the population (thousands)")):
        i = etb_row(label)
        for q, j in qcols.items():
            unit = "thousands of households" if key == "households" else "£ a year per household"
            facts.add(Fact(f"etb.2a.{key}.{q}", num(rows[i][j]), unit, "2023/24", "etb", f"Table 2a!{ref(i, j)}", "outturn"))
    for q in qcols:
        d, ind = facts[f"etb.2a.direct.{q}"], facts[f"etb.2a.indirect.{q}"]
        facts.add(Fact(f"etb.2a.alltax.{q}", d.value + ind.value, "£ a year per household", "2023/24", "etb", f"{d.locator} + {ind.locator}",
                       "calculated", formula=f"{d.id} + {ind.id}", inputs=[d.id, ind.id]))
    # ETB Tables 3a (non-retired) and 4a (retired): same layout as Table 2a, but the
    # fifths are ranked within each group, so they do not line up with Table 2a's fifths.
    # "Retired" means living in a retired household (ONS note 12).
    for grp, sheet in (("nonret", "Table 3a"), ("ret", "Table 4a")):
        rows = [[c.value for c in r] for r in wb[sheet].iter_rows()]
        hdr = next(r for r in rows if r and any(str(v).strip() == "Bottom" for v in r if v))
        gcols = {q: next(j for j, v in enumerate(hdr) if v and str(v).strip() == lab) for q, lab in
                 (("q1", "Bottom"), ("q2", "2nd"), ("q3", "3rd"), ("q4", "4th"), ("q5", "Top"), ("all", "All individuals"))}

        def grp_row(label, rows=rows):
            for i, r in enumerate(rows):
                if len(r) > 1 and r[1] and " ".join(str(r[1]).split()) == label:
                    return i
            raise KeyError(label)
        for key, label, unit in (("gross", "Gross income", "£ a year per household"), ("direct", "Total direct taxes", "£ a year per household"),
                                 ("indirect", "Total indirect taxes", "£ a year per household"),
                                 ("people", "Number of individuals in the population (thousands)", "thousands of people"),
                                 ("households", "Number of households in the population (thousands)", "thousands of households")):
            i = grp_row(label)
            for q, j in gcols.items():
                facts.add(Fact(f"etb.{grp}.{key}.{q}", num(rows[i][j]), unit, "2023/24", "etb", f"{sheet}!{ref(i, j)}", "outturn"))
        for q in gcols:
            d, ind, g = facts[f"etb.{grp}.direct.{q}"], facts[f"etb.{grp}.indirect.{q}"], facts[f"etb.{grp}.gross.{q}"]
            facts.add(Fact(f"etb.{grp}.alltax.{q}", d.value + ind.value, "£ a year per household", "2023/24", "etb", f"{d.locator} + {ind.locator}",
                           "calculated", formula=f"{d.id} + {ind.id}", inputs=[d.id, ind.id]))
            facts.add(Fact(f"etb.{grp}.taxshare.{q}", 100 * (d.value + ind.value) / g.value, "% of gross household income", "2023/24", "etb",
                           f"{d.locator} + {ind.locator}, ÷ {g.locator}", "calculated",
                           formula=f"100 × ({d.id} + {ind.id}) ÷ {g.id}", inputs=[d.id, ind.id, g.id]))
        p, h = facts[f"etb.{grp}.people.all"], facts[f"etb.{grp}.households.all"]
        facts.add(Fact(f"etb.{grp}.hhsize.all", p.value / h.value, "people per household", "2023/24", "etb", f"{p.locator} ÷ {h.locator}",
                       "calculated", formula=f"{p.id} ÷ {h.id}", inputs=[p.id, h.id]))
    # ETB Table 8: taxes as a % of gross income / disposable income / expenditure
    rows = [[c.value for c in r] for r in wb["Table 8"].iter_rows()]
    hdr = rows[3]
    qcols = {q: next(j for j, v in enumerate(hdr) if v and str(v).strip() == lab) for q, lab in
             (("q1", "Bottom"), ("q2", "2nd"), ("q3", "3rd"), ("q4", "4th"), ("q5", "Top"), ("all", "All individuals"))}
    section = None
    for i, r in enumerate(rows):
        if r[0] and str(r[0]).startswith("Percentages of"):
            section = {"Percentages of gross income": "gross", "Percentages of disposable income": "disposable", "Percentages of expenditure": "spend"}[str(r[0]).strip()]
        if section is None:
            continue
        label = (r[2] or r[1])
        if not label:
            continue
        key = {"Direct taxes": "direct", "Income Tax": "income_tax", "National Insurance contributions": "nics",
               "Council Tax and Northern Ireland rates": "council", "Indirect taxes": "indirect", "Value Added Tax (VAT)": "vat",
               "All taxes": "all"}.get(str(label).strip())
        if not key:
            continue
        for q, j in qcols.items():
            facts.add(Fact(f"etb.t8.{section}.{key}.{q}", num(r[j]), "%", "2023/24", "etb", f"Table 8!{ref(i, j)}", "outturn"))
    return out


# ETB Tables 12a-12c: household types, figures adjusted for household size
# ("equivalised", ONS note 1). Table 16: people in households receiving more in
# benefits (cash and in kind) than they pay in taxes, 1977 to 2023/24.
HOUSEHOLD_TYPES = [
    # (key, sheet, column header, plain label, group)
    ("na1", "Table 12a", "1 adult (All)", "One adult, no children", "Working-age, no children"),
    ("na2", "Table 12a", "2 adults", "Two adults, no children", "Working-age, no children"),
    ("na3", "Table 12a", "More adults", "Three or more adults, no children", "Working-age, no children"),
    ("nc1", "Table 12b", "1 adult (with children)", "One adult with children", "Working-age, with children"),
    ("nc21", "Table 12b", "2 adults (1 child)", "Two adults, one child", "Working-age, with children"),
    ("nc22", "Table 12b", "2 adults (2 children)", "Two adults, two children", "Working-age, with children"),
    ("nc23", "Table 12b", "2 adults (3 children)", "Two adults, three children", "Working-age, with children"),
    ("nc3", "Table 12b", "3 adults (with children)", "Three adults with children", "Working-age, with children"),
    ("r1", "Table 12c", "1 adult (All)", "One retired adult", "Retired"),
    ("r2", "Table 12c", "More adults", "Two or more retired adults", "Retired"),
    ("all", "Table 12a", "All individuals", "Everyone", "Everyone"),
]


def household_types(facts):
    wb = xlsx("data/payers/raw/ons-etb-fye2024.xlsx")
    unit = "£ a year, adjusted for household size"
    sheets = {}
    for key, sheet, col, label, group in HOUSEHOLD_TYPES:
        if sheet not in sheets:
            sheets[sheet] = [[c.value for c in r] for r in wb[sheet].iter_rows()]
        rows = sheets[sheet]
        hdr_i = next(i for i, r in enumerate(rows) if r and any(v and str(v).strip() == "All individuals" for v in r))
        j = next(j for j, v in enumerate(rows[hdr_i]) if v and str(v).strip() == col)
        for m, label_text in (("gross", "Gross income"), ("direct", "less direct taxes"), ("indirect", "less indirect taxes"),
                              ("cash", "plus cash benefits"), ("inkind", "plus benefits in kind")):
            i = next(i for i, r in enumerate(rows) if any(v and str(v).strip() == label_text for v in r[:2]))
            facts.add(Fact(f"etb.t12.{key}.{m}", num(rows[i][j]), unit, "2023/24", "etb", f"{sheet}!{ref(i, j)}", "outturn"))
        d, ind, g = (facts[f"etb.t12.{key}.{m}"] for m in ("direct", "indirect", "gross"))
        facts.add(Fact(f"etb.t12.{key}.alltax", d.value + ind.value, unit, "2023/24", "etb", f"{d.locator} + {ind.locator}",
                       "calculated", formula=f"{d.id} + {ind.id}", inputs=[d.id, ind.id]))
        facts.add(Fact(f"etb.t12.{key}.taxshare", 100 * (d.value + ind.value) / g.value, "% of gross income", "2023/24", "etb",
                       f"{d.locator} + {ind.locator}, ÷ {g.locator}", "calculated",
                       formula=f"100 × ({d.id} + {ind.id}) ÷ {g.id}", inputs=[d.id, ind.id, g.id]))
    # Table 16
    rows = [[c.value for c in r] for r in wb["Table 16"].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "Year")
    hdr = [str(v).strip() if v else "" for v in rows[hdr_i]]
    cols = {"all": hdr.index("All individuals (%)"), "nonret": hdr.index("Non-retired individuals (%)"), "ret": hdr.index("Retired individuals (%)")}
    years = []
    for i in range(hdr_i + 1, len(rows)):
        y = str(rows[i][0]).strip() if rows[i][0] is not None else ""
        if not re.fullmatch(r"\d{4}(/\d{2})?", y):
            continue
        years.append(y)
        for k, j in cols.items():
            facts.add(Fact(f"etb.t16.{k}.{y}", num(rows[i][j]), "% of people", y, "etb", f"Table 16!{ref(i, j)}", "outturn"))
    return {"types": [(k, label, group) for k, _, _, label, group in HOUSEHOLD_TYPES], "t16_years": years}


# ---------------------------------------------------------------- life: work

def _q2(data, year):
    return data.get(f"{year} Q2")


def work(facts):
    out = {"rate": {}, "men": {}, "women": {}, "level": {}, "ft": {}, "pt": {}, "occ": {}}
    for key, sid, path, unit in (("rate", "ons-lf24", "data/fetched/ons/lf24.csv", "%"), ("men", "ons-mgsv", "data/fetched/ons/mgsv.csv", "%"),
                                 ("women", "ons-lf25", "data/fetched/ons/lf25.csv", "%"), ("level", "ons-mgrz", "data/fetched/ons/mgrz.csv", "thousands"),
                                 ("ft", "ons-ycbe", "data/fetched/ons/ycbe.csv", "thousands"), ("pt", "ons-ycbh", "data/fetched/ons/ycbh.csv", "thousands")):
        meta, data = ons_series(path)
        for y in YEARS:
            v = _q2(data, y)
            fid = f"work.{key}.{y}"
            facts.add(Fact(fid, v, unit, f"April to June {y}", sid, f"{meta.get('CDID')} row '{y} Q2'", "published",
                           note=meta.get("Title", "")))
            out[key][y] = fid
        if key == "rate" and _q2(data, YEARS[-1] + 1) is not None:
            # a newer quarter than the explorer's range, for the home page's latest figure
            y = YEARS[-1] + 1
            facts.add(Fact(f"work.rate.{y}", _q2(data, y), unit, f"April to June {y}", sid, f"{meta.get('CDID')} row '{y} Q2'", "published",
                           note=meta.get("Title", "")))
    for y in YEARS:
        ft, pt = facts[f"work.ft.{y}"], facts[f"work.pt.{y}"]
        if ft.value is not None and pt.value is not None:
            facts.add(Fact(f"work.ptshare.{y}", 100 * pt.value / (ft.value + pt.value), "%", f"April to June {y}", "ons-ycbh", pt.locator,
                           "calculated", formula=f"100 × {pt.id} ÷ ({ft.id} + {pt.id})", inputs=[pt.id, ft.id]))
    out["ptshare"] = {y: f"work.ptshare.{y}" for y in YEARS if f"work.ptshare.{y}" in facts}
    # Occupation shares from the Annual Population Survey (two classifications)
    out["occ_groups"] = {}
    for sid, path, codecol, namecol, scheme in (("aps2010", "data/life/sources/work-data/aps210-uk-calendar-annual.csv", "C_OCCPUK11H_0", "C_OCCPUK11H_0_NAME", "SOC2010"),
                                                ("aps2020", "data/life/sources/work-data/aps218-uk-calendar-annual.csv", "SOC2020_FULL", "SOC2020_FULL_NAME", "SOC2020")):
        rows = csv_rows(path)
        for line, r in enumerate(rows, start=2):
            if r["C_SEX_NAME"] != "All persons" or r["MEASURES_NAME"] != "Value":
                continue
            y = int(r["DATE_NAME"][-4:])
            code = r[codecol]
            name = re.sub(r"^\d\s*:?\s*", "", r[namecol]).strip()
            name = name[0].upper() + name[1:].lower()
            fid = f"work.occ.{scheme}.{code}.{y}"
            facts.add(Fact(fid, num(r["OBS_VALUE"]), "people", f"January to December {y}", sid, f"{path.split('/')[-1]} line {line}", "published"))
            out["occ_groups"].setdefault(scheme, {})[code] = name
        for y in sorted({int(r["DATE_NAME"][-4:]) for r in rows}):
            total = facts.get(f"work.occ.{scheme}.0.{y}")
            if not total:
                continue
            for code in out["occ_groups"][scheme]:
                if code == "0":
                    continue
                part = facts[f"work.occ.{scheme}.{code}.{y}"]
                facts.add(Fact(f"work.occshare.{scheme}.{code}.{y}", 100 * part.value / total.value, "% of people in work", f"January to December {y}", sid,
                               part.locator, "calculated", formula=f"100 × {part.id} ÷ {total.id}", inputs=[part.id, total.id]))
            out["occ"].setdefault(scheme, []).append(y)
    return out


# ---------------------------------------------------------------- life: earnings

def earnings(facts):
    rows = csv_rows("data/fetched/nomis/ashe-resident-uk-median-weekly.csv")
    meta, cpih = ons_series("data/fetched/ons/l522.csv")
    base_year = max(int(r["DATE_NAME"]) for r in rows)
    base = cpih[f"{base_year} APR"]
    facts.add(Fact(f"cpih.apr.{base_year}", base, "index (2015=100)", f"April {base_year}", "ons-l522", f"L522 row '{base_year} APR'"))
    groups = {"8": "ft", "9": "pt", "1": "ft_men", "3": "ft_women"}
    out = {"base_year": base_year, "series": {g: {} for g in groups.values()}, "real": {g: {} for g in groups.values()}}
    for line, r in enumerate(rows, start=2):
        g = groups.get(r["SEX"])
        if not g:
            continue
        y = int(r["DATE_NAME"])
        if y not in YEARS and y not in EARLY_YEARS:
            continue
        fid = f"earn.{g}.{y}"
        st = "published"  # ASHE 2025 is no longer provisional: ONS's October 2026 release kept it unchanged
        facts.add(Fact(fid, num(r["OBS_VALUE"]), "£ a week", f"April {y}", "nomis-ashe-resident", f"ashe-resident-uk-median-weekly.csv line {line}", st,
                       note=r["SEX_NAME"] + ", median gross weekly pay"))
        out["series"][g][y] = fid
        idx = cpih.get(f"{y} APR")
        facts.add(Fact(f"cpih.apr.{y}", idx, "index (2015=100)", f"April {y}", "ons-l522", f"L522 row '{y} APR'")) if f"cpih.apr.{y}" not in facts else None
        v = facts[fid].value
        rid = f"earn.real.{g}.{y}"
        facts.add(Fact(rid, None if v is None or idx is None else v * base / idx, f"£ a week, April {base_year} prices", f"April {y}", "nomis-ashe-resident",
                       facts[fid].locator, "calculated", formula=f"{fid} × cpih.apr.{base_year} ÷ cpih.apr.{y}", inputs=[fid, f"cpih.apr.{base_year}", f"cpih.apr.{y}"]))
        out["real"][g][y] = rid
    return out


# ---------------------------------------------------------------- life: nations, regions and age groups

NATIONS = [("uk", "United Kingdom"), ("england", "England"), ("wales", "Wales"), ("scotland", "Scotland"), ("ni", "Northern Ireland")]
REGIONS = [("ne", "North East", "E12000001"), ("nw", "North West", "E12000002"), ("yh", "Yorkshire and The Humber", "E12000003"),
           ("em", "East Midlands", "E12000004"), ("wm", "West Midlands", "E12000005"), ("east", "East of England", "E12000006"),
           ("london", "London", "E12000007"), ("se", "South East", "E12000008"), ("sw", "South West", "E12000009")]
NATION_CODES = {"K02000001": "uk", "E92000001": "england", "W92000004": "wales", "S92000003": "scotland", "N92000002": "ni"}
REGION_CODES = {code: key for key, _, code in REGIONS}


def _geo_key(r):
    """Map a Nomis row to one of our place keys, using each place once (countries, or English regions)."""
    code, gtype = r["GEOGRAPHY_CODE"], r["GEOGRAPHY_TYPE"]
    if gtype == "countries" and code in NATION_CODES:
        return NATION_CODES[code]
    if gtype == "regions" and code in REGION_CODES:
        return REGION_CODES[code]
    return None


def work_places(facts):
    """Employment rate, ages 16 to 64, by nation and English region (Annual Population Survey, January to December)."""
    path = "data/fetched/nomis/aps-employment-rate-nations-regions.csv"
    out = {}
    for line, r in enumerate(csv_rows(path), start=2):
        m = re.fullmatch(r"Jan (\d{4})-Dec (\d{4})", r["DATE_NAME"])
        if not m or r["MEASURES_NAME"] != "Variable" or r["VARIABLE_NAME"] != "Employment rate - aged 16-64":
            continue
        key, y = _geo_key(r), int(m.group(1))
        if key is None or y not in YEARS:
            continue
        fid = f"work.place.{key}.{y}"
        if fid in facts:
            continue
        facts.add(Fact(fid, num(r["OBS_VALUE"]), "%", f"January to December {y}", "nomis-aps-emp-places",
                       f"aps-employment-rate-nations-regions.csv line {line}", "published", note=f"{r['GEOGRAPHY_NAME']}, employment rate aged 16-64"))
        out.setdefault(key, {})[y] = fid
    return out


AGE_SERIES = [("18_24", "18 to 24", "ybud"), ("25_34", "25 to 34", "ybug"), ("35_49", "35 to 49", "ybuj"), ("50_64", "50 to 64", "lf2u"), ("65", "65 and over", "lfk6")]


def work_ages(facts):
    """Employment rate by age group, United Kingdom, Labour Force Survey, April to June."""
    out = {}
    for key, label, cdid in AGE_SERIES:
        meta, data = ons_series(f"data/fetched/ons/{cdid}.csv")
        for y in YEARS:
            fid = f"work.age.{key}.{y}"
            facts.add(Fact(fid, _q2(data, y), "%", f"April to June {y}", f"ons-{cdid}", f"{meta.get('CDID')} row '{y} Q2'", "published",
                           note=meta.get("Title", "")))
            out.setdefault(key, {})[y] = fid
    return out


def earnings_places(facts):
    """Median gross weekly pay of full-time employees by nation and English region, where they live (ASHE), cash and after inflation."""
    path = "data/fetched/nomis/ashe-resident-nations-regions-ft-median-weekly.csv"
    meta, cpih = ons_series("data/fetched/ons/l522.csv")
    rows = csv_rows(path)
    base_year = max(int(r["DATE_NAME"]) for r in rows)
    base = cpih[f"{base_year} APR"]
    out = {"cash": {}, "real": {}, "base_year": base_year}
    for line, r in enumerate(rows, start=2):
        if r["MEASURES_NAME"] != "Value" or r["SEX_NAME"] != "Full Time Workers":
            continue
        key, y = _geo_key(r), int(r["DATE_NAME"])
        if key is None or y not in YEARS or f"earn.place.{key}.{y}" in facts:
            continue
        fid = f"earn.place.{key}.{y}"
        st = "provisional" if y == base_year else "published"
        facts.add(Fact(fid, num(r["OBS_VALUE"]), "£ a week", f"April {y}", "nomis-ashe-places", f"ashe-resident-nations-regions-ft-median-weekly.csv line {line}", st,
                       note=f"{r['GEOGRAPHY_NAME']}, full-time employees living there, median gross weekly pay"))
        idx = cpih.get(f"{y} APR")
        v = facts[fid].value
        rid = f"earn.place.real.{key}.{y}"
        facts.add(Fact(rid, None if v is None or idx is None else v * base / idx, f"£ a week, April {base_year} prices", f"April {y}", "nomis-ashe-places",
                       facts[fid].locator, "calculated", formula=f"{fid} × cpih.apr.{base_year} ÷ cpih.apr.{y}", inputs=[fid, f"cpih.apr.{base_year}", f"cpih.apr.{y}"]))
        out["cash"].setdefault(key, {})[y] = fid
        out["real"].setdefault(key, {})[y] = rid
    return out


# ---------------------------------------------------------------- life: housing

def housing(facts):
    rows = ods("data/fetched/ehs/FT1101_Trends_in_tenure.ods")["FT1101"]
    pct_start = next(i for i, r in enumerate(rows) if len(r) > 8 and r[8] == "percentages")
    out = {"tenure": {}, "children": {}}
    cols = {"outright": 1, "mortgage": 2, "owners": 3, "social": 6, "private": 7}
    for i in range(pct_start, len(rows)):
        r = rows[i]
        if not r or not re.fullmatch(r"\d{4}-\d{2}", str(r[0])):
            continue
        survey = str(r[0])
        y = int(survey[:4])
        if y not in YEARS:
            continue
        for key, j in cols.items():
            facts.add(Fact(f"house.{key}.{y}", num(r[j]) if j < len(r) else None, "% of households", f"{survey} survey year", "ehs-ft1101",
                           f"FT1101!{ref(i, j)}", "published"))
        out["tenure"][y] = survey
    # Households with dependent children (FT1241). The table has separate blocks for
    # single lone parents, previously married lone parents and couples, in thousands.
    # We add the blocks together and calculate shares; the formula is recorded.
    sheets = ods("data/fetched/ehs/FT1241_Trends_in_tenure_households_with_dependent_children.ods")
    sname = next(iter(sheets))
    sheet = sheets[sname]
    pct_i = next(i for i, r in enumerate(sheet) if len(r) > 6 and r[6] == "percentages")
    blocks = {"single lone parent": "lone", "previously married lone parent": "lone", "couple with dependent child(ren)": "couple"}
    counts = {}
    current = None
    for i in range(pct_i):
        r = sheet[i]
        if r and isinstance(r[0], str) and r[0].strip() in blocks:
            current = r[0].strip()
            continue
        if current and r and re.fullmatch(r"\d{4}-\d{2}", str(r[0])):
            y = int(str(r[0])[:4])
            if y in YEARS:
                for key, j in (("owners", 3), ("social", 4), ("private", 5), ("all", 6)):
                    fid = f"house.kidsk.{blocks[current]}.{current[:6]}.{key}.{y}"
                    facts.add(Fact(fid, num(r[j]), "thousand households", f"{r[0]} survey year", "ehs-ft1241", f"{sname}!{ref(i, j)}", "published",
                                   note=current))
                    counts.setdefault((y, key), []).append(fid)
                out["children"][y] = str(r[0])
    for y in out["children"]:
        total_ids = counts[(y, "all")]
        total = sum(facts[i].value for i in total_ids)
        for key in ("owners", "social", "private"):
            ids = counts[(y, key)]
            if any(facts[i].value is None for i in ids):
                continue
            facts.add(Fact(f"house.kids.{key}.{y}", 100 * sum(facts[i].value for i in ids) / total, "% of households with dependent children",
                           f"{out['children'][y]} survey year", "ehs-ft1241", ", ".join(facts[i].locator for i in ids), "calculated",
                           formula=f"100 × ({' + '.join(ids)}) ÷ ({' + '.join(total_ids)})", inputs=ids + total_ids))
    return out


# Housing costs and space (England, English Housing Survey).

def _sheet_year(name):
    m = re.fullmatch(r"(\d{4})-\d{2}", name.strip())
    return int(m.group(1)) if m else None


def _row(rows, label):
    """Index of the first row whose first cell is exactly label (footnote digits allowed)."""
    for i, r in enumerate(rows):
        if r and isinstance(r[0], str) and re.fullmatch(re.escape(label) + r"\d?", r[0].strip()):
            return i
    raise KeyError(label)


def _col(rows, header):
    for r in rows[:8]:
        for j, v in enumerate(r):
            if isinstance(v, str) and v.replace("\n", " ").strip() == header:
                return j
    raise KeyError(header)


MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _cpih_survey_year(facts, cpih, y):
    """Average CPIH over a survey year, April y to March y+1 (calculated)."""
    fid = f"cpih.sy.{y}"
    if fid in facts:
        return fid
    ids = []
    for yy, mon in [(y, m) for m in MONTHS[3:]] + [(y + 1, m) for m in MONTHS[:3]]:
        mid = f"cpih.m.{yy}.{mon}"
        if mid not in facts:
            facts.add(Fact(mid, cpih.get(f"{yy} {mon}"), "index (2015=100)", f"{mon.title()} {yy}", "ons-l522", f"L522 row '{yy} {mon}'"))
        ids.append(mid)
    vals = [facts[i].value for i in ids]
    facts.add(Fact(fid, None if None in vals else sum(vals) / 12, "index (2015=100)", f"April {y} to March {y + 1}", "ons-l522",
                   ", ".join(facts[i].locator for i in ids), "calculated", formula=f"({' + '.join(ids)}) ÷ 12", inputs=ids))
    return fid


def housing_costs(facts):
    """Mean weekly rent (before housing support) and mortgage payment, cash and after inflation."""
    _, cpih = ons_series("data/fetched/ons/l522.csv")
    out = {"cash": {}, "years": []}
    # Rents: FA3201, one sheet per survey year, mean column.
    path = "data/fetched/ehs/FA3201_rent_before_housing_support.ods"
    for name, rows in ods(path).items():
        y = _sheet_year(name)
        if y not in YEARS:
            continue
        j = _col(rows, "mean")
        for key, label in (("social", "all social renters"), ("private", "all private renters")):
            i = _row(rows, label)
            facts.add(Fact(f"house.rent.{key}.{y}", num(rows[i][j]), "£ a week", f"{name} survey year", "ehs-fa3201", f"{name}!{ref(i, j)}", "published",
                           note=f"{label}, mean weekly rent before housing support"))
        out["years"].append(y)
    # Mortgage payments: FA2501 (2008-09 to 2021-22) and FA2555 (2022-23 onwards), mean payment column.
    for sid, path in (("ehs-fa2501", "data/fetched/ehs/FA2501_mortgage_payment_per_week_2021-22.ods"),
                      ("ehs-fa2555", "data/fetched/ehs/FA2555_mortgage_payment_per_week.ods")):
        for name, rows in ods(path).items():
            y = _sheet_year(name)
            if y not in YEARS:
                continue
            j = _col(rows, "mean payment")
            i = _row(rows, "all mortgage types")
            facts.add(Fact(f"house.mortpay.{y}", num(rows[i][j]), "£ a week", f"{name} survey year", sid, f"{name}!{ref(i, j)}", "published",
                           note="owners buying with a mortgage (including shared owners), mean weekly payment for all mortgage types (the row both tables share); the all-mortgagors row in the newer table gives a slightly lower mean"))
    latest = max(y for y in YEARS if f"house.rent.private.{y}" in facts)
    base = _cpih_survey_year(facts, cpih, latest)
    out["base"] = latest
    for key in ("rent.social", "rent.private", "mortpay"):
        for y in YEARS:
            fid = f"house.{key}.{y}"
            if fid not in facts:
                continue
            idx = _cpih_survey_year(facts, cpih, y)
            v, b, i = facts[fid].value, facts[base].value, facts[idx].value
            facts.add(Fact(f"house.real.{key}.{y}", None if None in (v, b, i) else v * b / i, f"£ a week, {latest}-{str(latest + 1)[2:]} prices",
                           facts[fid].period, facts[fid].source, facts[fid].locator, "calculated",
                           formula=f"{fid} × {base} ÷ {idx}", inputs=[fid, base, idx]))
    return out


def housing_space(facts):
    """Overcrowding by tenure (bedroom standard, three-year averages) and number of rooms."""
    out = {"crowd": {}, "rooms": {}}
    rows = ods("data/fetched/ehs/FT1421_Trends_in_overcrowding_by_tenure.ods")["FT1421"]
    cols = {"owners": 1, "social": 2, "private": 3, "all": 4}
    for i, r in enumerate(rows):
        if not r or not re.fullmatch(r"\d{4}-\d{2}", str(r[0])):
            continue
        y = int(str(r[0])[:4])
        if y not in YEARS:
            continue
        for key, j in cols.items():
            facts.add(Fact(f"house.crowd.{key}.{y}", num(r[j]), "% of households (three-year average)", f"{y - 2}-{str(y - 1)[2:]} to {r[0]} survey years",
                           "ehs-ft1421", f"FT1421!{ref(i, j)}", "published"))
        out["crowd"][y] = str(r[0])
    # FA1422 adds the three years to 2022-23, which FT1421 does not yet cover.
    sheets = ods("data/fetched/ehs/FA1422_overcrowding_and_under-occupation_by_tenure.ods")
    for name, rows in sheets.items():
        y = _sheet_year(name)
        if y not in YEARS or y in out["crowd"]:
            continue
        pct = next(i for i, r in enumerate(rows) if len(r) > 5 and r[5] == "percentages")
        for key, label in (("owners", "owner occupiers"), ("social", "social renters"), ("private", "private renters"), ("all", "all tenures")):
            i = _row(rows[pct:], label) + pct
            facts.add(Fact(f"house.crowd.{key}.{y}", num(rows[i][1]), "% of households (three-year average)", f"{y - 2}-{str(y - 1)[2:]} to {name} survey years",
                           "ehs-fa1422", f"{name}!{ref(i, 1)}", "published"))
        out["crowd"][y] = name
    # Rooms: FA1401, all tenures, percentage block. Five or more rooms = five + six + seven + eight or more.
    path = "data/fetched/ehs/FA1401_number_of_rooms_by_tenure.ods"
    bands = [("r12", "one or two"), ("r3", "three"), ("r4", "four"), ("r5", "five"), ("r6", "six"), ("r7", "seven"), ("r8", "eight or more")]
    for name, rows in ods(path).items():
        y = _sheet_year(name)
        if y not in YEARS:
            continue
        pct = next(i for i, r in enumerate(rows) if "percentages" in r)
        i = _row(rows[pct:], "all tenures") + pct
        ids = []
        for key, head in bands:
            j = _col(rows, head)
            fid = f"house.rooms.{key}.{y}"
            facts.add(Fact(fid, num(rows[i][j]), "% of households", f"{name} survey year", "ehs-fa1401", f"{name}!{ref(i, j)}", "published"))
            ids.append(fid)
        big = ids[3:]
        vals = [facts[f].value for f in big]
        facts.add(Fact(f"house.rooms5.{y}", None if None in vals else sum(vals), "% of households", f"{name} survey year", "ehs-fa1401",
                       ", ".join(facts[f].locator for f in big), "calculated", formula=" + ".join(big), inputs=big))
        out["rooms"][y] = name
    return out


# ---------------------------------------------------------------- life: holidays

def _ott_block_table(path, sheet, source):
    """Parse the 2009-2019 layout: region heading rows, then purpose rows with year columns."""
    ws = xlsx(path)[sheet]
    rows = [[c.value for c in r] for r in ws.iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r[2] is not None and str(r[2]).strip() == "2009")
    years = {j: int(str(v)) for j, v in enumerate(rows[hdr_i]) if v and re.fullmatch(r"\d{4}", str(v).strip())}
    region, out = None, {}
    for i in range(hdr_i + 1, len(rows)):
        r = rows[i]
        a = (str(r[0]).strip() if r[0] else "")
        if a and all(v is None for v in r[2:13]):
            region = a
            continue
        if not a or region is None:
            continue
        for j, y in years.items():
            out[(region, a, y)] = (num(r[j]), f"{sheet}!{ref(i, j)}", source, 1)
    return out


def _ott_wide_table(path, sheet, source):
    """Parse the 2019-2023 layout: region, purpose, then one column per year."""
    rows = [[c.value for c in r] for r in xlsx(path)[sheet].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).strip() == "Region of Visit")
    years = {j: int(str(v)) for j, v in enumerate(rows[hdr_i]) if v and re.fullmatch(r"\d{4}", str(v).strip())}
    out = {}
    for i in range(hdr_i + 1, len(rows)):
        r = rows[i]
        if not r[0] or not r[1]:
            continue
        for j, y in years.items():
            out[(str(r[0]).strip(), str(r[1]).strip(), y)] = (num(r[j]) / 1000 if num(r[j]) is not None else None, f"{sheet}!{ref(i, j)}", source, 0.001)
    return out


def _ott_annual(path, source, year):
    rows = [[c.value for c in r] for r in xlsx(path)["2"].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).strip() == "Region of Visit")
    out = {}
    for i in range(hdr_i + 1, len(rows)):
        r = rows[i]
        if r[0] and r[1]:
            v = num(r[2])
            out[(str(r[0]).strip(), str(r[1]).strip(), year)] = (v / 1000 if v is not None else None, f"2!{ref(i, 2)}", source, 0.001)
    rows1 = [[c.value for c in r] for r in xlsx(path)["1"].iter_rows()]
    for i, r in enumerate(rows1):
        if r[0] and str(r[0]).strip() in ("United Kingdom", "Great Britain"):
            out[("Residents total", str(r[0]).strip(), year)] = (num(r[1]) / 1000, f"1!{ref(i, 1)}", source, 0.001)
    return out


def holidays(facts):
    cells = {}
    cells.update(_ott_block_table("data/fetched/ott/section3-2009to2019.xlsx", "3.03", "ott-2009to2019"))
    newer = _ott_wide_table("data/fetched/ott/section3-2019to2023.xlsx", "2", "ott-2019to2023")
    # 2019 appears in both files: keep the later publication (2019-2023) for 2019
    cells.update(newer)
    for y, path, sid in ((2024, "data/fetched/ott/ukresidents2024annual.xlsx", "ott-2024"), (2025, "data/fetched/ott/ukresidents2025annual.xlsx", "ott-2025")):
        if (ROOT / path).exists():
            cells.update(_ott_annual(path, sid, y))
    regions = {"europe": ("Europe", "Europe"), "namerica": ("North America", "North America"), "other": ("Other Countries", "Other Countries"), "world": ("Total World", "Total World")}
    purposes = {"holiday": ("Holiday", "Holiday - All"), "vfr": ("Visiting friends or relatives", "Visit friends or relatives"),
                "business": ("Business", "Business"), "all": ("All visits", "All visits")}
    out = {"series": {}, "basis": {}}
    for y in YEARS:
        basis = "UK residents" if y <= 2023 else "Great Britain residents"
        out["basis"][y] = basis
        for rk, (old_r, new_r) in regions.items():
            for pk, (old_p, new_p) in purposes.items():
                key = None
                for cand in ((old_r, old_p, y), (new_r, new_p, y), ("Total World" if rk == "world" else new_r, new_p, y)):
                    if cand in cells:
                        key = cand
                        break
                fid = f"hol.{rk}.{pk}.{y}"
                if key is None:
                    facts.add(Fact(fid, None, "thousand visits", str(y), "ott-2019to2023" if y <= 2023 else "ott-2024", "not published", "missing",
                                   note="No estimate in the retained source for this year."))
                elif y in PART_YEAR_PURPOSES and pk != "all":
                    # ONS's 2020 purpose rows come only from the passenger survey, which stopped on
                    # 16 March 2020; the "All visits" total also uses other data for the rest of the year.
                    # So the purpose figures cover only part of 2020 and are not shown as the year's figure.
                    v, loc, sid, scale = cells[key]
                    facts.add(Fact(fid, None, "thousand visits", str(y), sid, loc, "missing",
                                   note=PART_YEAR_PURPOSES[y]))
                    facts.add(Fact(f"{fid}.part", v, "thousand visits", PART_YEAR_PERIOD[y], sid, loc, "published",
                                   note=f"{basis}; {key[0]}, {key[1]}; covers only {PART_YEAR_PERIOD[y]}: {PART_YEAR_PURPOSES[y]}"
                                   + ("; source counts visits, shown here in thousands" if scale != 1 else ""), scale=scale))
                else:
                    v, loc, sid, scale = cells[key]
                    facts.add(Fact(fid, v, "thousand visits", str(y), sid, loc, "published",
                                   note=f"{basis}; {key[0]}, {key[1]}" + ("; source counts visits, shown here in thousands" if scale != 1 else ""), scale=scale))
                out["series"].setdefault(rk, {}).setdefault(pk, {})[y] = fid
    for y in YEARS:
        h, a = facts[f"hol.world.holiday.{y}"], facts[f"hol.world.all.{y}"]
        if h.value is not None and a.value:
            facts.add(Fact(f"hol.holshare.{y}", 100 * h.value / a.value, "% of visits abroad", str(y), h.source, h.locator, "calculated",
                           formula=f"100 × {h.id} ÷ {a.id}", inputs=[h.id, a.id]))
            e = facts[f"hol.europe.holiday.{y}"]
            if e.value is not None:
                facts.add(Fact(f"hol.europeshare.{y}", 100 * e.value / h.value, "% of holiday visits", str(y), e.source, e.locator, "calculated",
                               formula=f"100 × {e.id} ÷ {h.id}", inputs=[e.id, h.id]))
    return out


# ONS's 2020 figures by purpose of visit come only from the International Passenger Survey,
# which was suspended on 16 March 2020, so they cover only the weeks before that date.
PART_YEAR_PURPOSES = {2020: "the survey stopped on 16 March 2020, so ONS's figures by purpose of visit cover only the weeks before that date, not the whole year"}
PART_YEAR_PERIOD = {2020: "January to mid-March 2020"}


# Countries: only single countries are ranked, never regions, groups or "other" rows
COUNTRY_RENAME = {"USA": "United States", "Czech Republic": "Czechia"}
NOT_A_COUNTRY = re.compile(r"^(Total|Other|Rest of|- of which|EU|Europe$|North America$|Fly|South and Central America)", re.I)


def _country_rows(rows, name_col, start, cols):
    """Yield (country name, row index) for single-country rows of a country table."""
    for i in range(start, len(rows)):
        r = rows[i]
        name = r[name_col]
        if not name or not isinstance(name, str):
            continue
        name = re.sub(r"\s*\[Note \d+\]", "", name).strip()
        if name in ("Total World",) or NOT_A_COUNTRY.match(name):
            continue
        if all(num(r[j]) is None and str(r[j]).strip() != "Not available" for j in cols):
            continue
        yield COUNTRY_RENAME.get(name, name), i


def _slug(name):
    return re.sub(r"[^a-z]+", "-", name.lower()).strip("-")


def holiday_countries(facts):
    """Visits abroad by main country visited. All purposes for every year; holidays only from 2024."""
    out = {"names": {}, "all": {}, "holiday": {}}

    def add(name, kind, y, v, sid, loc, scale, basis):
        s = _slug(name)
        out["names"][s] = name
        fid = f"hol.cty.{s}.{kind}.{y}"
        if v is None:
            return
        facts.add(Fact(fid, v, "thousand visits", str(y), sid, loc, "published",
                       note=f"{basis}; main country visited: {name}; {'all purposes' if kind == 'all' else 'holiday visits'}", scale=scale))
        out[kind].setdefault(y, []).append(s)

    # 2009 to 2018: Travel trends 2009-2019, table 3.10, thousands of visits
    rows = [[c.value for c in r] for r in xlsx("data/fetched/ott/section3-2009to2019.xlsx")["3.10"].iter_rows()]
    hdr = next(i for i, r in enumerate(rows) if r[2] == 2009)
    years = {j: int(v) for j, v in enumerate(rows[hdr]) if isinstance(v, int)}
    for name, i in _country_rows(rows, 0, hdr + 1, list(years)):
        for j, y in years.items():
            if y <= 2018:
                add(name, "all", y, num(rows[i][j]), "ott-2009to2019", f"3.10!{ref(i, j)}", 1, "UK residents")
    # 2019 to 2023: Travel trends 2019-2023, table 3.09, visits (shown in thousands)
    rows = [[c.value for c in r] for r in xlsx("data/fetched/ott/section3-2019to2023.xlsx")["9"].iter_rows()]
    hdr = next(i for i, r in enumerate(rows) if r[0] == "Region of Visit")
    years = {j: int(str(v)) for j, v in enumerate(rows[hdr]) if v and re.fullmatch(r"\d{4}", str(v).strip())}
    for name, i in _country_rows(rows, 1, hdr + 1, list(years)):
        for j, y in years.items():
            v = num(rows[i][j])
            add(name, "all", y, None if v is None else v / 1000, "ott-2019to2023", f"9!{ref(i, j)}", 0.001, "UK residents")
    # 2024 onwards: annual tables, table 7 (holiday visits and all purposes)
    for y, path, sid in ((2024, "data/fetched/ott/ukresidents2024annual.xlsx", "ott-2024"), (2025, "data/fetched/ott/ukresidents2025annual.xlsx", "ott-2025")):
        rows = [[c.value for c in r] for r in xlsx(path)["7"].iter_rows()]
        hdr = next(i for i, r in enumerate(rows) if r[0] == "Region of Visit")
        col = {}
        for j, v in enumerate(rows[hdr]):  # first column of each purpose is its visits column
            if v and str(v).split("\n")[-1].strip() == "Visits":
                col[str(v).split("\n")[0].strip()] = j
        hol_j, all_j = col["Holiday - all"], col["All Purposes"]
        for name, i in _country_rows(rows, 1, hdr + 1, [hol_j, all_j]):
            for kind, j in (("holiday", hol_j), ("all", all_j)):
                v = num(rows[i][j])
                add(name, kind, y, None if v is None else v / 1000, sid, f"7!{ref(i, j)}", 0.001, "Great Britain residents")
    return out


def holidays_gb(facts):
    """Holiday trips taken within Great Britain by GB residents (Great Britain Tourism Survey)."""
    out = {}
    entries = [
        # (year, source, locator, survey)
        (2019, "gbts-2019-gb-summary", "GB All Tourism!B5", "earlier"),
        (2022, "gbts-2022to2023-tables", "Britain trips!F9", "current"),
        (2023, "gbts-2024-q4-annual-tables", "2024_Britain trips!F9", "current"),
        (2024, "gbts-2024-q4-annual-tables", "2024_Britain trips!G9", "current"),
    ]
    files = {"gbts-2019-gb-summary": "data/fetched/gbts/gbts-2019-gb-summary.xlsx", "gbts-2022to2023-tables": "data/fetched/gbts/gbts-2022to2023-tables.xlsx",
             "gbts-2024-q4-annual-tables": "data/fetched/gbts/gbts-2024-q4-annual-tables.xlsx"}
    labels = {"GB All Tourism!B5": ("Holidays", "A5"), "Britain trips!F9": ("Total GB trips (million)", "A9"), "2024_Britain trips!F9": ("Total GB trips (million)", "A9"),
              "2024_Britain trips!G9": ("Total GB trips (million)", "A9")}
    for y, sid, loc, survey in entries:
        sheet, cellref = loc.rsplit("!", 1)
        ws = xlsx(files[sid])[sheet]
        want_label, label_ref = labels[loc]
        if str(ws[label_ref].value).strip() != want_label:
            raise ValueError(f"{sid} {sheet}!{label_ref}: expected '{want_label}', found '{ws[label_ref].value}'")
        v = num(ws[cellref].value)
        facts.add(Fact(f"hol.gb.holiday.{y}", v * 1000, "thousand trips", f"January to December {y}", sid, loc, "published",
                       note=f"GB residents' overnight trips in Great Britain whose main purpose was a holiday; adults and accompanying children each count as a trip; {survey} survey method; source in millions",
                       scale=1000))
        out[y] = survey
    loc = "p10 after 'Holidays Q4 2024' line 'Visits (million))' number 5"
    v = pdf_number("data/fetched/gbts/gbts-2025-toplines.pdf", loc)
    facts.add(Fact("hol.gb.holiday.2025", v * 1000, "thousand trips", "January to December 2025", "gbts-2025-toplines", loc, "published",
                   note="GB residents' overnight trips in Great Britain whose main purpose was a holiday; current survey method; published rounded to 0.1 million", scale=1000))
    out[2025] = "current"
    return out


def population(facts):
    """Mid-year population estimates, used to express trips per 100 residents."""
    for key, sid, path in (("uk", "ons-ukpop", "data/fetched/ons/ukpop.csv"), ("gb", "ons-gbpop", "data/fetched/ons/gbpop.csv")):
        meta, data = ons_series(path)
        for y in EARLY_YEARS + YEARS:
            v = data.get(str(y))
            if v is not None:
                facts.add(Fact(f"pop.{key}.{y}", v, "people", f"mid-{y}", sid, f"{meta.get('CDID')} row '{y}'", "published", note=meta.get("Title", "")))


def holiday_rates(facts, gb_survey):
    """Holiday trips per 100 residents: an average across everyone, including people who took none."""
    for y in YEARS:
        h = facts.get(f"hol.world.holiday.{y}")
        pop = facts.get(f"pop.{'uk' if y <= 2023 else 'gb'}.{y}")
        if h is not None and h.value is not None and pop is not None:
            facts.add(Fact(f"hol.abroad.per100.{y}", 100 * 1000 * h.value / pop.value, "holiday visits abroad per 100 residents", str(y), h.source, h.locator, "calculated",
                           formula=f"100 × 1000 × {h.id} ÷ {pop.id}", inputs=[h.id, pop.id]))
        g, gp = facts.get(f"hol.gb.holiday.{y}"), facts.get(f"pop.gb.{y}")
        if g is not None and gp is not None:
            facts.add(Fact(f"hol.gb.per100.{y}", 100 * 1000 * g.value / gp.value, "holiday trips in Great Britain per 100 GB residents", str(y), g.source, g.locator, "calculated",
                           formula=f"100 × 1000 × {g.id} ÷ {gp.id}", inputs=[g.id, gp.id]))


# ---------------------------------------------------------------- life: schools

def schools(facts):
    out = {"primary": {}, "secondary": {}, "over30_primary": {}}
    # January 2006 to January 2015: SFR16/2015 national tables, Table 6b
    path = "data/fetched/dfe/spc-2015-national-tables.xlsx"
    rows = [[c.value for c in r] for r in xlsx(path)["Table 6b"].iter_rows()]
    yr_i = next(i for i, r in enumerate(rows) if any(str(v).strip() == "2006" for v in r if v))
    ycols = {int(str(v).strip()): j for j, v in enumerate(rows[yr_i]) if v and re.fullmatch(r"\d{4}", str(v).strip())}
    prim = find_row(rows, "STATE-FUNDED PRIMARY")
    sec = find_row(rows, "STATE-FUNDED SECONDARY")
    avg_p = find_row(rows, "Average class size", start=prim)
    avg_s = find_row(rows, "Average class size", start=sec)
    for y, j in ycols.items():
        if y not in YEARS and y not in EARLY_YEARS:
            continue
        for phase, i in (("primary", avg_p), ("secondary", avg_s)):
            facts.add(Fact(f"school.{phase}.{y}", num(rows[i][j]), "pupils per class", f"January {y} census ({y - 1}/{str(y)[2:]} school year)",
                           "dfe-spc-2015-tables", f"Table 6b!{ref(i, j)}", "published"))
            out[phase][y] = f"school.{phase}.{y}"
    # January 2016 onwards: DfE statistics API, national level
    data = json.loads((ROOT / "data/life/sources/schools/dfe-national-class-sizes-1.0.json").read_text())
    phase_ids = {"5kyxd": "primary", "tfHTE": "secondary"}
    for k, r in enumerate(data["results"]):
        if r["filters"].get("cAd31") != "XdTUf":
            continue
        phase = phase_ids.get(r["filters"].get("5cGdi"))
        if not phase:
            continue
        period = r["timePeriod"]["period"]
        y = int(period[-4:])
        if y not in YEARS and y != YEARS[-1] + 1:  # keep a census newer than the explorer's range for the class sizes page
            continue
        v = round(float(r["values"]["Wc9V2"]), 1)
        facts.add(Fact(f"school.{phase}.{y}", v, "pupils per class", f"January {y} census ({period[:4]}/{period[-2:]} school year)", "dfe_api",
                       f"results[{k}] values.Wc9V2", "published", note="API gives unrounded value; rounded to 1 decimal place as in DfE publications."))
        out[phase][y] = f"school.{phase}.{y}"
    return out


def housing_regions(facts):
    """Share of homes (dwellings) by tenure in each English region, at 31 March (DLUHC live table 109)."""
    path = "data/fetched/dluhc/LiveTable109.ods"
    rows = ods(path)["LT_109a_proportion"]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Tenure")
    head = rows[hi]
    cols = {"england": 2}
    for key, name, _ in REGIONS:
        cols[key] = next(j for j, h in enumerate(head) if str(h).strip().lower() == name.lower())
    tenures = {"Owner occupied": "owner", "Rented privately or with a job or business": "private",
               "Rented from local authorities": "council", "Rented from private registered providers": "ha"}
    out = {}
    for i in range(hi + 1, len(rows)):
        r = rows[i]
        if not r or r[0] not in tenures or not isinstance(r[1], (int, float)):
            continue
        y, t = int(r[1]), tenures[r[0]]
        if y not in YEARS:
            continue
        note = str(r[12]) if len(r) > 12 and r[12] else ""
        for key, j in cols.items():
            facts.add(Fact(f"house.reg.{t}.{key}.{y}", None if num(r[j]) is None else 100 * num(r[j]), "% of homes", f"31 March {y}", "dluhc-lt109",
                           f"LT_109a_proportion!{ref(i, j)}", "provisional" if "[p]" in note else "published", scale=100))
            out.setdefault(key, set()).add(y)
    for key in out:
        for y in out[key]:
            a, b = facts[f"house.reg.council.{key}.{y}"], facts[f"house.reg.ha.{key}.{y}"]
            if a.value is not None and b.value is not None:
                facts.add(Fact(f"house.reg.social.{key}.{y}", a.value + b.value, "% of homes", f"31 March {y}", "dluhc-lt109", a.locator, "calculated",
                               formula=f"{a.id} + {b.id}", inputs=[a.id, b.id]))
    return {k: sorted(v) for k, v in out.items()}


def schools_wales(facts):
    """Average class size in Wales, infant and junior classes, January census (Welsh Government, table 16 and 17)."""
    path = "data/fetched/wg/schools-census-results-january-2025.ods"
    book = ods(path)
    out = {}
    for sheet, phase in (("Table_16", "infant"), ("Table_17", "junior")):
        rows = book[sheet]
        hi = next(i for i, r in enumerate(rows) if r and r[0] == "Measure")
        ri = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "Average class size")
        for j, h in enumerate(rows[hi]):
            m = re.fullmatch(r"(\d{4}) - number", str(h).strip())
            if not m:
                continue
            y = int(m.group(1))
            v = num(rows[ri][j])
            fid = f"school.wales.{phase}.{y}"
            facts.add(Fact(fid, v, "pupils per class", f"January {y} census ({y - 1}/{str(y)[2:]} school year)",
                           "wg-schools-census-2025", f"{sheet}!{ref(ri, j)}", "published", note="Unrounded in the source; shown to 1 decimal place."))
            out.setdefault(phase, {})[y] = fid
    return out


# ---------------------------------------------------------------- who pays: Income Tax by age

SPI_AGES = (("u20", "Under 20"), ("20_24", "20-24"), ("25_29", "25-29"), ("30_34", "30-34"), ("35_39", "35-39"), ("40_44", "40-44"),
            ("45_49", "45-49"), ("50_54", "50-54"), ("55_59", "55-59"), ("60_64", "60-64"), ("65_69", "65-69"), ("70_74", "70-74"),
            ("75plus", "75 and over"), ("all", "Totals"))


def income_tax_by_age(facts):
    """HMRC Survey of Personal Incomes 2023-24, Table 3.2: taxpayers, income and Income Tax by age range and sex."""
    path = "data/fetched/hmrc/spi-2023-24-tables-3-1-to-3-11.ods"
    rows = ods(path)["Table_3_2"]
    hdr_i = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "Age range")
    hdr = [str(v).strip() for v in rows[hdr_i]]
    cols = {"n": "Number of taxpayers", "medinc": "Median income before tax", "medtax": "Median tax",
            "meaninc": "Mean income before tax", "meantax": "Mean tax"}
    units = {"n": "thousand taxpayers", "medinc": "£ a year", "medtax": "£ a year", "meaninc": "£ a year", "meantax": "£ a year"}
    sexes = {"All": "all", "Male": "men", "Female": "women"}
    y = "2023 to 2024"
    labels = dict((lab, key) for key, lab in SPI_AGES)
    for i in range(hdr_i + 1, len(rows)):
        r = rows[i]
        if not r or len(r) < len(hdr):
            continue
        age, pop = str(r[0]).strip(), str(r[1]).strip()
        sex = sexes.get(pop) or ("all" if pop == "All age ranges" else "men" if pop == "All male age ranges" else "women" if pop == "All female age ranges" else None)
        if age not in labels or sex is None:
            continue
        for m, col in cols.items():
            j = hdr.index(col)
            facts.add(Fact(f"spi.age.{m}.{labels[age]}.{sex}", num(r[j]), units[m], y, "hmrc-spi-2324-tables", f"Table_3_2!{ref(i, j)}", "outturn"))
    # Totals of income and tax for each age range: number of taxpayers × mean. HMRC rounds both to
    # three significant figures, so these totals (and shares built from them) are approximate.
    ages = [k for k, _ in SPI_AGES if k != "all"]
    for sex in ("all", "men", "women"):
        for m, unit in (("inc", "£bn a year"), ("tax", "£bn a year")):
            for a in ages:
                n, mean = f"spi.age.n.{a}.{sex}", f"spi.age.mean{m}.{a}.{sex}"
                facts.add(Fact(f"spi.age.tot{m}.{a}.{sex}", facts[n].value * facts[mean].value / 1e6, unit, y, "hmrc-spi-2324-tables",
                               f"{facts[n].locator} × {facts[mean].locator}", "calculated",
                               formula=f"{n} × {mean} ÷ 1000000", inputs=[n, mean],
                               note="Number of taxpayers × mean, both rounded by HMRC to three significant figures, so approximate."))
            ids = [f"spi.age.tot{m}.{a}.{sex}" for a in ages]
            facts.add(Fact(f"spi.age.tot{m}.sum.{sex}", sum(facts[i].value for i in ids), unit, y, "hmrc-spi-2324-tables",
                           facts[ids[0]].locator, "calculated", formula=" + ".join(ids), inputs=ids,
                           note="Sum of the age ranges, each calculated from rounded figures."))
    ids = [f"spi.age.n.{a}.all" for a in ages]
    facts.add(Fact("spi.age.n.sum.all", sum(facts[i].value for i in ids), "thousand taxpayers", y, "hmrc-spi-2324-tables",
                   facts[ids[0]].locator, "calculated", formula=" + ".join(ids), inputs=ids,
                   note="Sum of the age ranges, so shares add up to 100%; HMRC's own rounded total may differ slightly."))
    for a in ages:
        for m, base in (("n", "spi.age.n.sum.all"), ("tax", "spi.age.tottax.sum.all"), ("inc", "spi.age.totinc.sum.all")):
            part = f"spi.age.n.{a}.all" if m == "n" else f"spi.age.tot{m}.{a}.all"
            facts.add(Fact(f"spi.age.share{m}.{a}", 100 * facts[part].value / facts[base].value, "% of all taxpayers" if m == "n" else f"% of all taxpayers' {'Income Tax' if m == 'tax' else 'income'}",
                           y, "hmrc-spi-2324-tables", facts[part].locator, "calculated", formula=f"100 × {part} ÷ {base}", inputs=[part, base]))
        facts.add(Fact(f"spi.age.rate.{a}", 100 * facts[f"spi.age.meantax.{a}.all"].value / facts[f"spi.age.meaninc.{a}.all"].value,
                       "% of the age range's total income", y, "hmrc-spi-2324-tables", facts[f"spi.age.meantax.{a}.all"].locator, "calculated",
                       formula=f"100 × spi.age.meantax.{a}.all ÷ spi.age.meaninc.{a}.all", inputs=[f"spi.age.meantax.{a}.all", f"spi.age.meaninc.{a}.all"],
                       note="Mean tax ÷ mean income: all Income Tax owed by the age range as a share of all its income."))
    # Broader groups for the headline: sums of the published age ranges.
    groups = {"u30": ("u20", "20_24", "25_29"), "30_64": ("30_34", "35_39", "40_44", "45_49", "50_54", "55_59", "60_64"),
              "65plus": ("65_69", "70_74", "75plus")}
    for g, members in groups.items():
        for m in ("n", "tax", "inc"):
            ids = [f"spi.age.share{m}.{a}" for a in members]
            facts.add(Fact(f"spi.age.share{m}.{g}", sum(facts[i].value for i in ids), facts[ids[0]].unit, y, "hmrc-spi-2324-tables",
                           facts[ids[0]].locator, "calculated", formula=" + ".join(ids), inputs=ids))
    return {"ages": [(k, lab) for k, lab in SPI_AGES if k != "all"], "year": y}


def build_all():
    facts = Facts()
    d = {
        "spending": spending(facts),
        "receipts": receipts(facts),
        "who": who_pays(facts),
        "who_types": household_types(facts),
        "who_age": income_tax_by_age(facts),
        "work": work(facts),
        "earnings": earnings(facts),
        "work_places": work_places(facts),
        "work_ages": work_ages(facts),
        "earn_places": earnings_places(facts),
        "housing": housing(facts),
        "housing_costs": housing_costs(facts),
        "housing_space": housing_space(facts),
        "holidays": holidays(facts),
        "countries": holiday_countries(facts),
        "gb_holidays": holidays_gb(facts),
        "schools": schools(facts),
        "housing_regions": housing_regions(facts),
        "schools_wales": schools_wales(facts),
    }
    from . import data_nations
    d["nations"] = data_nations.build(facts)
    from . import data_prod
    d["productivity"] = data_prod.build(facts)
    from . import data_taxhist
    d["tax_history"] = data_taxhist.build(facts)
    from . import data_spendhist
    d["spend_history"] = data_spendhist.build(facts)
    from . import data_taxmixhist
    d["tax_mix_history"] = data_taxmixhist.build(facts)
    d["households_years"] = data_taxmixhist.households(facts)
    from . import data_intl
    d["intl"] = data_intl.build(facts)
    from . import data_borrow
    d["borrow"] = data_borrow.build(facts)
    from . import data_life_extra
    d["life_extra"] = data_life_extra.build(facts)
    population(facts)
    holiday_rates(facts, d["gb_holidays"])
    d["history"] = history(facts)
    return facts, d


# ---------------------------------------------------------------- life: before 2008

def history(facts):
    """Figures from before 2008, where an official series reaches back that far.

    Work: Labour Force Survey, April to June, from 1971 (part-time and age groups from 1992).
    Housing: tenure in England from the Labour Force Survey, calendar years 1981 to 2008
    (FT1101 rows above the English Housing Survey's survey years).
    Travel: all visits abroad by UK residents, International Passenger Survey, 1980 to 2023.
    Earnings (from 2002) and class sizes (from 2006) are read by earnings() and schools().
    Only years with a published figure get a fact: nothing is filled in.
    """
    out = {"work": {}, "ages": {}, "tenure": {}, "travel": {}}
    for key, sid, path, unit in (("rate", "ons-lf24", "data/fetched/ons/lf24.csv", "%"), ("men", "ons-mgsv", "data/fetched/ons/mgsv.csv", "%"),
                                 ("women", "ons-lf25", "data/fetched/ons/lf25.csv", "%"), ("level", "ons-mgrz", "data/fetched/ons/mgrz.csv", "thousands"),
                                 ("ft", "ons-ycbe", "data/fetched/ons/ycbe.csv", "thousands"), ("pt", "ons-ycbh", "data/fetched/ons/ycbh.csv", "thousands")):
        meta, data = ons_series(path)
        for y in EARLY_YEARS:
            v = _q2(data, y)
            if v is None:
                continue
            fid = f"work.{key}.{y}"
            facts.add(Fact(fid, v, unit, f"April to June {y}", sid, f"{meta.get('CDID')} row '{y} Q2'", "published", note=meta.get("Title", "")))
            out["work"].setdefault(key, []).append(y)
    for y in out["work"].get("pt", []):
        ft, pt = facts.get(f"work.ft.{y}"), facts[f"work.pt.{y}"]
        if ft is not None:
            facts.add(Fact(f"work.ptshare.{y}", 100 * pt.value / (ft.value + pt.value), "%", f"April to June {y}", "ons-ycbh", pt.locator,
                           "calculated", formula=f"100 × {pt.id} ÷ ({ft.id} + {pt.id})", inputs=[pt.id, ft.id]))
            out["work"].setdefault("ptshare", []).append(y)
    for key, label, cdid in AGE_SERIES:
        meta, data = ons_series(f"data/fetched/ons/{cdid}.csv")
        for y in EARLY_YEARS:
            v = _q2(data, y)
            if v is not None:
                facts.add(Fact(f"work.age.{key}.{y}", v, "%", f"April to June {y}", f"ons-{cdid}", f"{meta.get('CDID')} row '{y} Q2'", "published",
                               note=meta.get("Title", "")))
                out["ages"].setdefault(key, []).append(y)
    # Tenure, England, Labour Force Survey calendar years. Row labels carry footnote
    # numbers ("19973" is 1997, note 3), so only the first four digits are the year.
    rows = ods("data/fetched/ehs/FT1101_Trends_in_tenure.ods")["FT1101"]
    pct_start = next(i for i, r in enumerate(rows) if len(r) > 8 and r[8] == "percentages")
    cols = {"outright": 1, "mortgage": 2, "owners": 3, "social": 6, "private": 7}
    for i in range(pct_start, len(rows)):
        r = rows[i]
        m = re.fullmatch(r"(\d{4})\d?", str(r[0]).strip()) if r and r[0] is not None else None
        if not m or not 1981 <= int(m.group(1)) <= 2008:
            continue
        y = int(m.group(1))
        survey = "DOE Labour Force Survey housing trailer" if y <= 1991 else "ONS Labour Force Survey"
        for key, j in cols.items():
            facts.add(Fact(f"house.lfs.{key}.{y}", num(r[j]), "% of households", f"{y} (calendar year)", "ehs-ft1101", f"FT1101!{ref(i, j)}", "published",
                           note=f"{survey}, England"))
        out["tenure"][y] = survey
    # Visits abroad by UK residents, all purposes (holidays, visiting family and friends, business and other).
    lines = list(csv.reader(io.StringIO((ROOT / "data/fetched/ott/ott-timeseries.csv").read_text(encoding="utf-8-sig"))))
    col = lines[1].index("GMAF")
    for r in lines:
        if r and re.fullmatch(r"\d{4}", r[0]) and r[col].strip():
            y = int(r[0])
            fid = f"hol.ips.all.{y}"
            facts.add(Fact(fid, num(r[col]), "thousand visits", str(y), "ons-ott-timeseries", f"CDID GMAF row '{y}'", "published",
                           note="UK residents' visits abroad, all purposes, not seasonally adjusted (International Passenger Survey)"))
            pop = facts.get(f"pop.uk.{y}")
            if pop is not None:
                facts.add(Fact(f"hol.ips.per100.{y}", 100 * 1000 * facts[fid].value / pop.value, "visits abroad per 100 residents", str(y), "ons-ott-timeseries",
                               facts[fid].locator, "calculated", formula=f"100 × 1000 × {fid} ÷ {pop.id}", inputs=[fid, pop.id]))
            out["travel"][y] = fid
    return out
