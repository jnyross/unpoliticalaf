"""Margins of error for survey figures, only where the publisher gives them.

Most everyday-life figures come from sample surveys, so they are estimates. A
margin of error says how far the survey figure could be from the true value
just because a sample was asked (95% confidence). This module reads the
margins the publishers themselves give and never makes one up:

- Labour Force Survey: ONS table A11 gives the margin for the latest period
  only, for the UK employment rate and for its change over a year.
- Annual Population Survey (employment rate by nation and region): Nomis
  gives each figure's margin in percentage points ("Confidence").
- Annual Survey of Hours and Earnings: Nomis gives each figure's coefficient
  of variation (CV). Following the ONS guide, the margin of error is
  1.96 × standard error = 1.96 × CV ÷ 100 × estimate (our calculation).
- International Passenger Survey (trips abroad): ONS gives 95% intervals for
  visits by country (a relative interval up to 2023) and, from 2024, for
  holiday visits as a whole.

Surveys whose tables give no margin are listed as such on the page; their
figures are shown without one.
"""
import re

from .data import Fact, NATIONS, REGIONS, YEARS, num as cellnum, _geo_key, _slug, COUNTRY_RENAME
from .readers import ROOT, csv_rows, ref
import openpyxl

Z = 1.96  # 95% confidence, as in the ONS guide

# fact id -> (margin fact id, display kind). Filled by add_facts().
MARGINS = {}
# Extra details for the page.
INFO = {}

ASHE_GROUPS = {"8": "ft", "9": "pt", "1": "ft_men", "3": "ft_women"}


def _rows(path, sheet):
    ws = openpyxl.load_workbook(ROOT / path, data_only=True)[sheet]
    return [[c.value for c in r] for r in ws.iter_rows(min_row=1, min_col=1)]


def _calc_moe(facts, base_id, cv_id, moe_id):
    """Margin of error in the estimate's own units from its CV: estimate × 1.96 × CV ÷ 100."""
    b, cv = facts[base_id], facts[cv_id]
    v = None if b.value is None or cv.value is None else b.value * Z * cv.value / 100
    facts.add(Fact(moe_id, v, "± " + b.unit, b.period, cv.source, cv.locator, "calculated",
                   note="95% margin of error, from the published coefficient of variation",
                   formula=f"{base_id} × 1.96 × {cv_id} ÷ 100", inputs=[base_id, cv_id]))
    MARGINS[base_id] = (moe_id, "pm_pounds")


def lfs(facts):
    """ONS A11: margin for the latest UK employment rate and its change on a year."""
    path = "data/fetched/ons/lfs-sampling-variability-a11.xlsx"
    rows = _rows(path, "UK")
    period = next(v for v in rows[2] if isinstance(v, str) and re.fullmatch(r"\w+ to \w+ \d{4}", v.strip())).strip()
    i = next(k for k, r in enumerate(rows) if isinstance(r[1], str) and r[1].startswith("Employment rate (aged 16 to 64)"))
    head = next(r for r in rows[:i] if "Level" in r)
    col = {h: j for j, h in enumerate(head) if isinstance(h, str)}
    j_est, j_lvl, j_yr = col["Level"], col["Sampling variability of level (*)"], col["Sampling variability of change on year (*)"]
    src = "ons-lfs-a11"
    facts.add(Fact("lfs.rate.latest", cellnum(rows[i][j_est]), "%", period, src, f"UK!{ref(i, j_est)}", "published",
                   note="Employment rate, aged 16 to 64, not seasonally adjusted"))
    facts.add(Fact("moe.lfs.rate.latest", cellnum(rows[i][j_lvl]), "± percentage points", period, src, f"UK!{ref(i, j_lvl)}", "published",
                   note="95% confidence interval of the employment rate"))
    facts.add(Fact("moe.lfs.rate.change_year", cellnum(rows[i][j_yr]), "± percentage points", period, src, f"UK!{ref(i, j_yr)}", "published",
                   note="95% confidence interval of the change in the employment rate over a year"))
    INFO["lfs_period"] = period


def aps(facts):
    """Nomis APS: margin (±, percentage points) for each employment rate by nation and region."""
    path = "data/fetched/nomis/aps-employment-rate-nations-regions-ci.csv"
    rows = csv_rows(path)
    est = {}
    for line, r in enumerate(rows, start=2):
        m = re.fullmatch(r"Jan (\d{4})-Dec (\d{4})", r["DATE_NAME"])
        if not m or r["VARIABLE_NAME"] != "Employment rate - aged 16-64":
            continue
        key, y = _geo_key(r), int(m.group(1))
        if key is None or y not in YEARS:
            continue
        if r["MEASURES_NAME"] == "Variable":
            est.setdefault((key, y), cellnum(r["OBS_VALUE"]))
            continue
        if r["MEASURES_NAME"] != "Confidence":
            continue
        base = f"work.place.{key}.{y}"
        mid = f"moe.{base}"
        if mid in facts or base not in facts:
            continue
        # Attach the margin only to the same estimate it was published with.
        if est.get((key, y)) != facts[base].value:
            continue
        facts.add(Fact(mid, cellnum(r["OBS_VALUE"]), "± percentage points", f"January to December {y}", "nomis-aps-emp-places-ci",
                       f"aps-employment-rate-nations-regions-ci.csv line {line}", "published",
                       note=f"{r['GEOGRAPHY_NAME']}, 95% confidence interval of the employment rate aged 16-64"))
        MARGINS[base] = (mid, "pm_pp")


def ashe(facts):
    """ASHE coefficients of variation, UK groups and nations/regions, turned into margins in pounds."""
    rows = csv_rows("data/fetched/nomis/ashe-resident-uk-median-weekly-cv.csv")
    vals = {}
    for line, r in enumerate(rows, start=2):
        g = ASHE_GROUPS.get(r["SEX"])
        if not g:
            continue
        y = int(r["DATE_NAME"])
        if y not in YEARS:
            continue
        if r["MEASURES_NAME"] == "Value":
            vals[(g, y)] = cellnum(r["OBS_VALUE"])
            continue
        base = f"earn.{g}.{y}"
        if r["MEASURES_NAME"] != "Confidence" or base not in facts or vals.get((g, y)) != facts[base].value:
            continue
        cv = f"cv.earn.{g}.{y}"
        facts.add(Fact(cv, cellnum(r["OBS_VALUE"]), "% (coefficient of variation)", f"April {y}", "nomis-ashe-resident-cv",
                       f"ashe-resident-uk-median-weekly-cv.csv line {line}", "published", note=r["SEX_NAME"] + ", median gross weekly pay"))
        _calc_moe(facts, base, cv, f"moe.{base}")
        _calc_moe(facts, f"earn.real.{g}.{y}", cv, f"moe.earn.real.{g}.{y}")
    rows = csv_rows("data/fetched/nomis/ashe-resident-nations-regions-ft-median-weekly.csv")
    for line, r in enumerate(rows, start=2):
        if r["MEASURES_NAME"] != "Confidence" or r["SEX_NAME"] != "Full Time Workers":
            continue
        key, y = _geo_key(r), int(r["DATE_NAME"])
        base = f"earn.place.{key}.{y}"
        cv = f"cv.{base}"
        if key is None or y not in YEARS or base not in facts or cv in facts:
            continue
        facts.add(Fact(cv, cellnum(r["OBS_VALUE"]), "% (coefficient of variation)", f"April {y}", "nomis-ashe-places",
                       f"ashe-resident-nations-regions-ft-median-weekly.csv line {line}", "published",
                       note=f"{r['GEOGRAPHY_NAME']}, full-time employees living there, median gross weekly pay"))
        _calc_moe(facts, base, cv, f"moe.{base}")
        _calc_moe(facts, f"earn.place.real.{key}.{y}", cv, f"moe.earn.place.real.{key}.{y}")


def _rel_from_limits(facts, prefix, period, src, sheet, i, j_est, j_lo, j_hi, rows, note):
    """Facts for a published estimate and its lower and upper limits, plus the relative margin (%)."""
    ids = []
    for suffix, j in (("est", j_est), ("lo", j_lo), ("hi", j_hi)):
        fid = f"{prefix}.{suffix}"
        facts.add(Fact(fid, cellnum(rows[i][j]) / 1000, "thousand visits", period, src, f"{sheet}!{ref(i, j)}", "published",
                       note=note + {"est": ", estimate used for the interval", "lo": ", lower 95% limit", "hi": ", upper 95% limit"}[suffix], scale=0.001))
        ids.append(fid)
    est, lo, hi = (facts[x].value for x in ids)
    rid = f"{prefix}.rel"
    facts.add(Fact(rid, 100 * (hi - lo) / 2 / est, "± % of the estimate", period, src, facts[ids[0]].locator, "calculated",
                   note=note + ", half the width of the 95% interval as a share of the estimate",
                   formula=f"100 × ({ids[2]} − {ids[1]}) ÷ 2 ÷ {ids[0]}", inputs=ids))
    return rid


def holidays(facts, countries):
    """IPS 95% intervals: holiday visits (2024 on), and visits by main country visited (every year with figures)."""
    names = countries["names"]
    for y, src in ((2024, "ott-2024"), (2025, "ott-2025")):
        path = f"data/fetched/ott/ukresidents{y}annual.xlsx"
        rows = _rows(path, "15")
        h = next(k for k, r in enumerate(rows) if r[:3] == ["Table", "Headline measure", "Purpose of visit "])
        col = {str(v).strip(): j for j, v in enumerate(rows[h]) if v}
        i = next(k for k in range(h + 1, len(rows)) if rows[k][1] == "Visits" and str(rows[k][2]).strip() == "Holiday - All")
        rid = _rel_from_limits(facts, f"ci.hol.holiday.{y}", str(y), src, "15", i, col["Estimate"], col["Lower CI limit"], col["Upper CI limit"], rows,
                               "Holiday visits abroad by Great Britain residents")
        MARGINS[f"hol.world.holiday.{y}"] = (rid, "pm_pct")
        MARGINS[f"hol.abroad.per100.{y}"] = (rid, "pm_pct")
        # By country (all purposes)
        rows = _rows(path, "16")
        h = next(k for k, r in enumerate(rows) if r[0] == "Table" and r[2] == "Main Country Visited")
        col = {str(v).strip(): j for j, v in enumerate(rows[h]) if v}
        for i in range(h + 1, len(rows)):
            name = rows[i][2]
            if not isinstance(name, str):
                continue
            s = _slug(COUNTRY_RENAME.get(name.strip(), name.strip()))
            base = f"hol.cty.{s}.all.{y}"
            if s in NO_MARGIN or base not in facts or cellnum(rows[i][col["Number of visits"]]) is None:
                continue
            rid = _rel_from_limits(facts, f"ci.hol.cty.{s}.{y}", str(y), src, "16", i, col["Number of visits"], col["Number of visits lower CI limit"],
                                   col["Number of visits upper CI limit"], rows, f"Visits to {names[s]} (all purposes)")
            MARGINS[base] = (rid, "pm_pct")
    # 2009 to 2018: table 3.17, relative 95% interval beside each estimate
    path, src = "data/fetched/ott/section3-2009to2019.xlsx", "ott-2009to2019"
    rows = _rows(path, "3.17")
    yr = next(k for k, r in enumerate(rows) if 2009 in r)
    years = {j: v for j, v in enumerate(rows[yr]) if isinstance(v, int)}
    for i in range(yr + 3, len(rows)):
        name = rows[i][0]
        if not isinstance(name, str):
            continue
        s = _slug(COUNTRY_RENAME.get(name.strip(), name.strip()))
        for j, y in years.items():
            _rel_cell(facts, s, y, src, f"3.17!{ref(i, j + 1)}", rows[i][j + 1], names) if y <= 2018 else None
    # 2019 to 2023: table 3.16 (sheet "16"), relative 95% interval beside each estimate
    path, src = "data/fetched/ott/section3-2019to2023.xlsx", "ott-2019to2023"
    rows = _rows(path, "16")
    h = next(k for k, r in enumerate(rows) if r[0] == "Region of Visit")
    for j, v in enumerate(rows[h]):
        m = re.search(r"95% CI (\d{4})", str(v or ""))
        if not m:
            continue
        y = int(m.group(1))
        for i in range(h + 1, len(rows)):
            name = rows[i][1]
            if isinstance(name, str):
                _rel_cell(facts, _slug(COUNTRY_RENAME.get(name.strip(), name.strip())), y, src, f"16!{ref(i, j)}", rows[i][j], names)


# ONS calculates these intervals from the passenger survey alone, while the
# published estimates for Ireland add visits across the Irish land border, so
# the interval does not describe the figure we show. Ireland gets no margin.
NO_MARGIN = {"republic-of-ireland", "irish-republic"}


def _rel_cell(facts, s, y, src, loc, cell, names):
    if s in NO_MARGIN:
        return
    base = f"hol.cty.{s}.all.{y}"
    rid = f"ci.hol.cty.{s}.{y}.rel"
    v = cellnum(cell)
    if base not in facts or v is None or rid in facts:
        return
    facts.add(Fact(rid, v * 100, "± % of the estimate", str(y), src, loc, "published",
                   note=f"Visits to {names[s]} (all purposes), relative 95% confidence interval", scale=100))
    MARGINS[base] = (rid, "pm_pct")


def add_facts(facts, d):
    MARGINS.clear()
    INFO.clear()
    lfs(facts)
    aps(facts)
    ashe(facts)
    holidays(facts, d["countries"])


# ---------------------------------------------------------------- display helpers

def has(fid):
    return fid in MARGINS


def pm(num, fid, cls="moe"):
    """'±0.4 points' after a figure, or '' when no margin is published."""
    if fid not in MARGINS:
        return ""
    mid, kind = MARGINS[fid]
    if num.facts[mid].value is None:
        return ""
    return f' <span class="{cls}" title="95% margin of error">{num(mid, kind)}</span>'


def margin_value(facts, fid):
    """The margin in the figure's own units, or None."""
    if fid not in MARGINS:
        return None
    mid, kind = MARGINS[fid]
    m, v = facts[mid].value, facts[fid].value
    if m is None or v is None:
        return None
    return v * m / 100 if kind == "pm_pct" else m


def change_check(facts, a_id, b_id):
    """Compare a change with the two years' margins combined: √(a² + b²).

    Returns (change, combined margin) in the figures' units, or None. The two
    samples are treated as independent; the surveys re-interview some of the
    same people, which makes this check cautious rather than generous.
    """
    ma, mb = margin_value(facts, a_id), margin_value(facts, b_id)
    if ma is None or mb is None:
        return None
    return facts[b_id].value - facts[a_id].value, (ma ** 2 + mb ** 2) ** 0.5


# ---------------------------------------------------------------- page text

PAGE = "uncertainty.html"


def how_sure_link(up):
    return f'<a href="{up}{PAGE}">How sure are these figures?</a>'


def _range(num, ids, kind):
    """'from ±a to ±b' across several figures' margins, smallest first, with traced numbers."""
    ms = sorted((num.facts[MARGINS[f][0]].value, MARGINS[f][0]) for f in ids if f in MARGINS and num.facts[MARGINS[f][0]].value is not None)
    if not ms:
        return None
    return f"from {num(ms[0][1], kind)} to {num(ms[-1][1], kind)}"


def topic_line(num, topic, last, up="../"):
    """One short paragraph under a topic's answer: how sure the figures are."""
    link = how_sure_link(up)
    if topic == "work":
        places = [f"work.place.{k}.{last}" for k, _ in NATIONS[1:]] + [f"work.place.{k}.{last}" for k, _, _ in REGIONS]
        rng = _range(num, places, "pm_pp")
        s = (f"These are survey estimates. For {esc_(INFO['lfs_period'])}, the margin of error on the UK rate was "
             f"{num('moe.lfs.rate.latest', 'pm_pp')}, and {num('moe.lfs.rate.change_year', 'pm_pp')} on its change over a year, so a smaller change could be sampling noise.")
        if rng:
            s += f" Rates for each nation and region in {last} have margins {rng}."
    elif topic == "earnings":
        places = [f"earn.place.{k}.{last}" for k, _ in NATIONS[1:]] + [f"earn.place.{k}.{last}" for k, _, _ in REGIONS]
        rng = _range(num, places, "pm_pounds")
        s = (f"These are survey estimates from a 1% sample of employee jobs. The UK full-time figure for April {last} has a margin of error of "
             f"{num(MARGINS[f'earn.ft.{last}'][0], 'pm_pounds')} a week.")
        if rng:
            s += f" Figures for each nation and region are less precise, with margins {rng} a week."
    elif topic == "housing":
        s = "These are survey estimates; the English Housing Survey tables used here publish no margins of error and leave out figures from very small samples."
    elif topic == "holidays":
        y = max(y for y in (2024, 2025) if f"hol.world.holiday.{y}" in MARGINS)
        s = (f"Trips abroad come from a survey of passengers, with a margin of error of {num(MARGINS[f'hol.world.holiday.{y}'][0], 'pm_pct')} "
             f"for holiday visits abroad in {y}; single countries have wider margins. The survey of holidays within Great Britain publishes none in the tables used here.")
    elif topic == "schools":
        s = "The school census counts every class in every state school, not a sample, so there is no sampling margin of error."
    else:
        return ""
    return f'<p class="sure"><strong>How sure?</strong> {s} {link}</p>'


def esc_(s):
    from .html import esc
    return esc(s)


def combined(facts, a_id, b_id, style):
    """The combined margin for a change, in the change's own style (points, per cent of the earlier year, or units)."""
    r = change_check(facts, a_id, b_id)
    if r is None:
        return None
    ch, m = r
    return ch, (100 * m / facts[a_id].value if style == "pct" else m)


def combined_cell(facts, a_id, b_id, style):
    """A checkable <data> element for the combined margin of a change between two figures."""
    from .html import esc
    r = combined(facts, a_id, b_id, style)
    if r is None:
        return None
    v = r[1]
    text = f"±{v:.1f} points" if style == "pp" else (f"±{v:.1f}%" if style == "pct" else f"±{v:.1f}")
    return (f'<data value="{v!r}" data-margin="{style}" data-from="{esc(a_id)}" data-to="{esc(b_id)}" '
            f'data-ma="{esc(MARGINS[a_id][0])}" data-mb="{esc(MARGINS[b_id][0])}" data-ka="{MARGINS[a_id][1]}" data-kb="{MARGINS[b_id][1]}">{esc(text)}</data>')


def check_sentence(facts, num, a_id, b_id, style, labels=("earlier", "later"), up="../../"):
    """Plain sentence: is a change bigger than the two years' margins of error combined?"""
    cell = combined_cell(facts, a_id, b_id, style)
    if cell is None:
        return ""
    ch, m = change_check(facts, a_id, b_id)
    if abs(ch) > m:
        verdict = f"bigger than both margins combined ({cell}), so it is unlikely to be sampling noise alone"
    else:
        verdict = f"within both margins combined ({cell}), so it could be sampling noise"
    return (f'<p class="small sure-check">Margins of error: {esc_(labels[0])} {pm(num, a_id, "moe-in").strip()}, {esc_(labels[1])} {pm(num, b_id, "moe-in").strip()}. '
            f'The change is {verdict}. <a href="{up}{PAGE}#compare">How this is checked</a></p>')


def uncertainty_page(facts, d, num, sources, last):
    from .html import page, table, details_table, source_line, esc
    up = ""
    gb_last = max(y for y in (2024, 2025) if f"hol.world.holiday.{y}" in MARGINS)
    ex_w = f"work.place.wales.{last}"
    body = ["<h1>How sure are these figures?</h1>"]
    body.append(f'''<div class="answer"><p>Many figures on this site come from surveys that ask a sample of people, not everyone. A survey figure is an estimate. Its <strong>margin of error</strong> shows how far it could be from the true figure just because of who happened to be asked.</p>
<p>Where the publisher gives a margin of error, we show it after the figure. For example, {num(ex_w, "pct")}{pm(num, ex_w)} of people aged 16 to 64 in Wales were in work in {last}. Where the publisher gives none, we say so and show none: we never make one up.</p></div>''')
    body.append('<h2 id="read">How to read a margin of error</h2>')
    body.append('<p>The margins on this site are 95% margins. If the same survey were run again and again with new samples, about 19 times in 20 the range “figure plus or minus margin” would contain the true value. A smaller margin means a more precise figure.</p>')
    body.append('<p>A margin of error only covers the luck of the sample. It does not cover people who decline to take part, wrong answers, or changes in how a survey is run, which can matter more. The Labour Force Survey, for example, has had falling response rates since 2020.</p>')
    body.append('<p>Where ONS publishes a coefficient of variation instead (the standard error as a percentage of the figure), we turn it into a margin using the method in the ONS guide: margin of error = 1.96 × standard error = 1.96 × coefficient of variation × figure.</p>')
    body.append('<h2 id="compare">Is a change bigger than the margin of error?</h2>')
    body.append('<p>When two figures differ by less than their margins of error combined, the difference could be sampling noise. On comparison pages we make a rough check: we combine the two margins as the square root of the sum of their squares, √(a² + b²), and say whether the change is bigger.</p>')
    body.append(f'<p>This treats the two years’ samples as separate. These surveys interview some of the same people or jobs in more than one year, which makes the real margin on a change smaller, so our check is cautious: it can miss a small real change, but it rarely calls noise a change. For the UK employment rate, ONS publishes the margin on a change over a year directly ({num("moe.lfs.rate.change_year", "pm_pp")} for {esc(INFO["lfs_period"])}).</p>')
    body.append('<p class="note">A change bigger than the margin of error is unlikely to be sampling noise. That still does not say what caused it.</p>')

    # Which figures have a margin
    body.append('<h2 id="which">Which figures have a margin of error</h2>')
    wplaces = [f"work.place.{k}.{last}" for k, _ in NATIONS] + [f"work.place.{k}.{last}" for k, _, _ in REGIONS]
    eplaces = [f"earn.place.{k}.{last}" for k, _ in NATIONS[1:]] + [f"earn.place.{k}.{last}" for k, _, _ in REGIONS]
    rows = [
        ["Employment rate, UK (Year by year: work)", "Labour Force Survey, a sample survey of households",
         f"{num('moe.lfs.rate.latest', 'pm_pp')} for the latest period ONS publishes ({esc(INFO['lfs_period'])}); {num('moe.lfs.rate.change_year', 'pm_pp')} on a change over a year. "
         "ONS publishes these for the latest period only, so April to June figures for earlier years are shown without one."],
        ["Employment rate by nation and region", "Annual Population Survey, a larger sample survey over a whole year",
         f"Published for every year. In {last}: {_range(num, wplaces, 'pm_pp')}."],
        ["Pay (median weekly pay)", "Annual Survey of Hours and Earnings, a 1% sample of employee jobs from HM Revenue and Customs PAYE records",
         f"Published for every year as a coefficient of variation, turned into a margin as above. UK full-time employees, April {last}: {num(MARGINS[f'earn.ft.{last}'][0], 'pm_pounds')} a week; "
         f"each nation and region: {_range(num, eplaces, 'pm_pounds')}."],
        ["Holidays and visits abroad", "International Passenger Survey, interviews with passengers at ports and airports",
         f"Holiday visits: {num(MARGINS['hol.world.holiday.2024'][0], 'pm_pct')} in 2024 and {num(MARGINS[f'hol.world.holiday.{gb_last}'][0], 'pm_pct')} in {gb_last}; ONS gives none for holidays alone before 2024. "
         "Visits by country: every year except 2020, when the survey was paused. Ireland is shown without one, because ONS’s interval leaves out trips across the Irish land border that the figure includes."],
        ["Holidays within Great Britain", "Great Britain Tourism Survey",
         "None in the tables used here. The survey’s own guidance says results from 30 to 100 people should be treated as indicative only, and fewer than 30 not used."],
        ["Housing", "English Housing Survey, a sample survey of households in England",
         "None in the tables used here. The tables leave out figures based on very small samples, and some mark small-sample figures as indicative only."],
        ["Class sizes", "School census: every class in every state school", "None needed: this is a count, not a sample."],
        ["Who pays: taxes and benefits by household income", "Effects of taxes and benefits on household income, based on a household survey",
         "None in the tables used here."],
        ["Who pays: shares of Income Tax", "HM Revenue and Customs Survey of Personal Incomes, a sample of tax records", "None in the table used here."],
        ["Spending, tax receipts and borrowing", "Government accounts, not a sample", "No sampling margin. Recent years can still be revised."],
    ]
    body.append(table("Margins of error by topic", ["Figures", "How they are measured", "Margin of error (95%)"], rows))

    # Work
    body.append(f'<h2 id="work">Employment rate by nation and region, {last}</h2>')
    body.append('<p>The Annual Population Survey asks fewer people in smaller places, so their margins are wider. A gap between two places smaller than their margins combined could be sampling noise.</p>')
    prow = []
    for k, n in [(k, n) for k, n in NATIONS] + [(k, n) for k, n, _ in REGIONS]:
        f = f"work.place.{k}.{last}"
        prow.append([esc(n), num(f, "pct"), num(MARGINS[f][0], "pm_pp") if f in MARGINS else '<span class="missing">not published</span>'])
    body.append(table(f"Employment rate, ages 16 to 64, January to December {last}, with 95% margin of error", ["Place", "Employment rate", "Margin of error"], prow))
    body.append(source_line(sources, ["nomis-aps-emp-places-ci", "ons-lfs-a11"], up=up))

    # Earnings
    body.append('<h2 id="earnings">Median weekly pay</h2>')
    body.append('<p>Pay comes from a large sample, so UK figures are precise to within a few pounds. Part-time pay and figures for each nation and region are less precise.</p>')
    erow = []
    for y in YEARS:
        r = [str(y)]
        for g in ("ft", "ft_men", "ft_women", "pt"):
            f = f"earn.{g}.{y}"
            r.append(num(f, "pounds") + pm(num, f) if f in facts else '<span class="missing">not available</span>')
        erow.append(r)
    body.append(details_table("Show pay with margins of error for every year", "Median gross weekly pay, United Kingdom, April each year, cash, with 95% margin of error",
                              ["Year", "Full-time", "Full-time men", "Full-time women", "Part-time"], erow))
    prow = []
    for k, n in [(k, n) for k, n in NATIONS] + [(k, n) for k, n, _ in REGIONS]:
        f = f"earn.place.{k}.{last}"
        prow.append([esc(n), num(f, "pounds"), num(f"cv.{f}", "pct") if f"cv.{f}" in facts else "", num(MARGINS[f][0], "pm_pounds") if f in MARGINS else ""])
    body.append(table(f"Median weekly pay of full-time employees by where they live, April {last}, cash", ["Place", "Median pay", "Coefficient of variation", "Margin of error"], prow))
    body.append(source_line(sources, ["nomis-ashe-resident-cv", "nomis-ashe-places", "nomis-ashe-article"], up=up))

    # Holidays
    body.append('<h2 id="holidays">Holidays abroad</h2>')
    body.append('<p>ONS calculates its intervals from the passenger survey alone, so its own estimate can differ slightly from the published total; we show the margin as a share of the figure.</p>')
    hrow = []
    for y in (2024, 2025):
        rid = MARGINS[f"hol.world.holiday.{y}"][0]
        p = rid[:-4]
        hrow.append([str(y), num(f"hol.world.holiday.{y}", "millions"), num(f"{p}.est", "millions"), num(f"{p}.lo", "millions"), num(f"{p}.hi", "millions"), num(rid, "pm_pct")])
    body.append(table("Holiday visits abroad by Great Britain residents, with ONS 95% confidence interval",
                      ["Year", "Published figure", "Estimate used for the interval", "Lower limit", "Upper limit", "Margin of error"], hrow))
    names = d["countries"]["names"]
    top = sorted(d["countries"]["all"].get(last, []), key=lambda s: -facts[f"hol.cty.{s}.all.{last}"].value)[:10]
    crow = [[esc(names[s]), num(f"hol.cty.{s}.all.{last}", "millions"), num(MARGINS[f"hol.cty.{s}.all.{last}"][0], "pm_pct") if f"hol.cty.{s}.all.{last}" in MARGINS else '<span class="missing">not shown</span>'] for s in top]
    body.append(table(f"Most visited countries, {last}: visits (all purposes), with 95% margin of error", ["Country", "Visits", "Margin of error"], crow))
    body.append('<p class="small">Where two countries’ ranges overlap, their order in the ranking could be sampling noise.</p>')
    body.append(source_line(sources, ["ott-2024", "ott-2025", "ott-2019to2023", "ott-2009to2019"], up=up))
    body.append(f'<p class="src">How margins of error work: <a href="{up}figures/ons-uncertainty-guide.html">Office for National Statistics: Uncertainty and how we measure it for our surveys</a>.</p>')
    return page(PAGE, "How sure are these figures?", "\n".join(body),
                "Margins of error for the survey figures on Unpolitical, where the publisher gives them, and how to read them.")
