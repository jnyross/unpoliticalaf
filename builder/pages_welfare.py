"""Welfare spending over 50 years: social security (benefits and the State Pension), from the OBR's historical database."""

from .html import FOLD, page, details_table, line_chart, switch, source_line, esc, bars
from . import findings as F

SOURCES_USED = ["obrhist-amounts", "obrhist", "obr-prices", "ons-ukpop", "dwp-benefit-exp-sf2026"]

# view key: (tab label, unit on the chart, number format, what the view means)
VIEWS = {
    "real": (
        "After inflation",
        "£ billion, 2025-26 prices",
        "bn",
        "Cash amounts adjusted to 2025-26 prices with the GDP deflator, a measure of prices across the whole economy (not the prices households pay), so different years can be compared.",
    ),
    "pp": (
        "Per person",
        "£ per person, 2025-26 prices",
        "pounds",
        "The after-inflation amount divided by the UK population in mid-year. It averages everyone, including children and pensioners, so it is not what any one person received.",
    ),
    "gdp": (
        "Share of GDP",
        "Per cent of GDP",
        "pct",
        "The amount as a share of everything produced in the UK that year (GDP). A share can fall while the amount rises, if the economy grows faster.",
    ),
    "share": (
        "Share of all spending",
        "Per cent of all public sector spending",
        "pct",
        "The amount as a share of all public sector spending that year, including debt interest and everything else the state spends.",
    ),
}
# key in the data, name in the chart, line style (a dark, b grey, c thin)
ALL = ("social", "All social security", "a")
PENS = ("pensioners", "Pensioners", "b")
NONPENS = ("nonpensioners", "Non-pensioners", "c")


def _years_for(facts, view, years):
    """Only the years with a figure for this view: per person needs a population estimate."""
    return [
        y
        for y in years
        if f"wel.{view}.{ALL[0]}.{y}" in facts
        and facts[f"wel.{view}.{ALL[0]}.{y}"].value is not None
    ]


def _chart(facts, num, view, items, years, rule):
    label, unit, kind, _ = VIEWS[view]
    yrs = _years_for(facts, view, years) if view == "pp" else years
    ids = [
        [
            (
                f"wel.{view}.{k}.{y}"
                if f"wel.{view}.{k}.{y}" in facts and facts[f"wel.{view}.{k}.{y}"].value is not None
                else None
            )
            for y in yrs
        ]
        for k, _, _ in items
    ]
    series = [
        (name, [facts[i].value if i else None for i in row], style)
        for (_, name, style), row in zip(items, ids)
    ]
    breaks = (
        [(yrs.index("2020-21"), "Source changes to HM Treasury PESA")] if "2020-21" in yrs else []
    )
    return line_chart(
        f"{label}, {yrs[0]} to {yrs[-1]}",
        yrs,
        series,
        unit,
        breaks=breaks,
        ymin=0,
        kind=kind,
        ids=ids,
        num=num,
        point_labels=yrs,
        finding=rule,
        split_breaks=True,
    )


def _tabs(facts, num, views, items, years, rule):
    tabs = [(VIEWS[v][0], VIEWS[v][3], _chart(facts, num, v, items, years, rule)) for v in views]
    return switch("Show amounts as", tabs, default=0)


def welfare_page(facts, d, num, sources):
    w = d["welfare"]
    years, pens_years = w["years"], w["pensioner_years"]
    first, last = years[0], years[-1]
    pesa = "2020-21"
    before, after = (
        years[years.index(pesa) - 1],
        pesa,
    )  # the stretches either side of the PESA source change

    def f(fid):
        return facts[fid].value if fid in facts else None

    def cell(fid, kind):
        return num(fid, kind) if f(fid) is not None else "not available"

    peak = max(years, key=lambda y: f(f"wel.gdp.social.{y}") or 0)
    all_rule = F.both(
        F.trend("Welfare spending", si=0, which="first"),
        F.trend("Welfare spending", si=0, which="last"),
    )
    pens_rule = F.trend("Welfare spending", si=0, which="first")

    body = ["<h1>Welfare spending over 50 years</h1>"]
    body.append(
        f"""<div class="answer"><p class="lede">Welfare spending, measured as social security (benefits and the State Pension), was {num(f"wel.real.social.{first}", "bn")} in {first} and {num(f"wel.real.social.{last}", "bn")} in {last}, both after inflation. In 2021-22 the State Pension was {num("dwp.share.sp.2021-22", "pct")} of DWP benefit spending, and Universal Credit was the largest of the other benefits, at {num("dwp.share.uc.2021-22", "pct")}. Per person, after inflation, welfare spending was {num(f"wel.pp.social.{last}", "pounds")} in {last}.</p>
<p>As a share of GDP it was {num(f"wel.gdp.social.{first}", "pct")} in {first}, peaked at {num(f"wel.gdp.social.{peak}", "pct")} in {peak}, and was {num(f"wel.gdp.social.{last}", "pct")} in {last}. As a share of all public spending it was {num(f"wel.share.social.{first}", "pct")} in {first} and {num(f"wel.share.social.{last}", "pct")} in {last}.</p>
<p>Per person, after inflation, it was {num(f"wel.pp.social.1978-79", "pounds")} in 1978-79 and {num(f"wel.pp.social.{last}", "pounds")} in {last}. Pensioners received {num(f"wel.penssh.{last}", "pct0")} of social security in {last}, against {num(f"wel.penssh.1978-79", "pct0")} in 1978-79.</p>
<p>The figures stop at {last}. The split by benefit for 2021-22 is in <a href="#benefits">the section below</a>.</p></div>"""
    )

    body.append('<h2 id="define">What counts as welfare here</h2>')
    body.append(
        """<p>“Welfare” means different things in different conversations, so this page uses one measure and says what it includes.</p>
<ul>
<li><strong>All social security</strong> is the OBR's social security line: cash benefits, including the State Pension. It is the measure used for every chart on this page.</li>
<li><strong>Without pensions</strong> means the non-pensioner figure: benefits paid to people who are not pensioners, such as those for children, people of working age and disabled people. The OBR and IFS split social security this way from 1978-79.</li>
<li><strong>Not included</strong> are health, education, social care and other public services. The main <a href="spending-areas.html">spending areas</a> page uses a wider “social protection” area that also includes social care, from different figures, so the two are not joined here.</li>
</ul>"""
    )
    body.append('<h2 id="total">All welfare spending, %s to %s</h2>' % (first, last))
    body.append(
        "<p>Each view shows the same measure. The line is split where the source changes (the dashed grey marker), so the two sources are not compared as one.</p>"
    )
    body.append(_tabs(facts, num, ["real", "pp", "gdp", "share"], [ALL], years, all_rule))
    body.append(FOLD)
    body.append(f'<h2 id="pensions">With and without pensions, {pens_years[0]} to {last}</h2>')
    body.append(
        f'<p>The OBR and IFS split the same total into pensioners and non-pensioners from {pens_years[0]}. Pensioners received {num(f"wel.penssh.{last}", "pct0")} of the total in {last}; in {pens_years[0]} they received {num(f"wel.penssh.{pens_years[0]}", "pct0")}.</p>'
    )
    body.append(
        _tabs(facts, num, ["real", "pp", "gdp"], [ALL, PENS, NONPENS], pens_years, pens_rule)
    )
    body.append(FOLD)

    head = [
        "Year",
        "All social security, £ billion (2025-26 prices)",
        "Per person, £ (2025-26 prices)",
        "% of GDP",
        "% of all public spending",
        "Pensioners, £ billion (2025-26 prices)",
        "Non-pensioners, £ billion (2025-26 prices)",
    ]
    rows = [
        [
            y,
            cell(f"wel.real.social.{y}", "bn1"),
            cell(f"wel.pp.social.{y}", "pounds"),
            cell(f"wel.gdp.social.{y}", "pct"),
            cell(f"wel.share.social.{y}", "pct"),
            cell(f"wel.real.pensioners.{y}", "bn1"),
            cell(f"wel.real.nonpensioners.{y}", "bn1"),
        ]
        for y in years
    ]
    body.append(
        details_table(
            "Show every year", f"Welfare spending (social security), {first} to {last}", head, rows
        )
    )
    body.append(
        '<p class="small">After-inflation amounts = cash amount × 100 ÷ GDP deflator (2025-26 = 100). Per person = after-inflation amount ÷ UK population in mid-year. Tap any figure to see the cash amount it was calculated from.</p>'
    )

    # ------------------------------------------------------------- by benefit, 2021-22
    dy = "2021-22"
    body.append('<h2 id="benefits">Which benefits made up welfare in %s?</h2>' % dy)
    body.append(
        f"""<div class="answer"><p>In {dy} the State Pension was {num(f"dwp.share.sp.{dy}", "pct")} of DWP benefit spending: {num(f"dwp.cash.sp.{dy}", "bn1")} out of {num(f"dwp.cash.dwptotal.{dy}", "bn1")}. Universal Credit was {num(f"dwp.share.uc.{dy}", "pct")}, housing benefit (not Universal Credit) {num(f"dwp.share.hb.{dy}", "pct")}, disability and carers' benefits {num(f"dwp.share.disability.{dy}", "pct")}, tax credits {num(f"dwp.share.tc.{dy}", "pct")} and Child Benefit {num(f"dwp.share.cb.{dy}", "pct")}.</p></div>"""
    )
    rows = [
        ("State Pension", "sp"),
        ("Universal Credit", "uc"),
        ("Housing benefit (not Universal Credit)", "hb"),
        ("Employment and Support Allowance", "esa"),
        ("Disability and carers' benefits", "disability"),
        ("Pension Credit", "pc"),
        ("Tax credits", "tc"),
        ("Child Benefit", "cb"),
        ("Other benefits", "other"),
    ]
    rows.sort(key=lambda r: -facts[f"dwp.share.{r[1]}.{dy}"].value)
    items = [
        (
            f"<strong>{esc(n)}</strong>" if k == "sp" else esc(n),
            f"dwp.share.{k}.{dy}",
            "" if k == "sp" else "alt",
        )
        for n, k in rows
    ]
    body.append(
        bars(
            items,
            "pct",
            num,
            maxval=facts[f"dwp.share.sp.{dy}"].value * 1.1,
            caption=f"Share of DWP benefit spending by benefit, {dy}. DWP tables, cash terms. The State Pension has a darker bar.",
        )
    )
    body.append(
        f"<p>The State Pension was {num('dwp.share.sp.1955-56', 'pct')} of DWP benefit spending in 1955-56, the first year of this page's series. In 1955-56 the DWP's main table is the only one with figures for that year, so the share uses it alone.</p>"
    )
    body.append(FOLD)
    body.append(
        f"""<div class="limit"><p><strong>Why one year.</strong></p><ul>
<li>The split is for {dy}, the last year on the OBR series. The DWP tables report tax credits in a separate table from 1999-00, and that table is Great Britain only, while the other benefits are UK figures. A split across all the years would join figures measured on different bases, so it is not shown.</li>
<li>Shares are of the DWP total: the main table's total benefit expenditure plus the separate table's total. The DWP total for {dy} is {num(f"dwp.cash.dwptotal.{dy}", "bn1")}, which is not the same as the OBR's social security figure for that year, because the two publications count some items differently.</li>
<li>“Other benefits” is the DWP total minus the benefits named here, so it includes the smaller benefits, such as Winter Fuel Payments and statutory maternity and sick pay.</li>
</ul></div>"""
    )
    body.append(
        source_line(
            sources,
            ["dwp-benefit-exp-sf2026"],
            f"Table 1a (expenditure by benefit) and sheet “Non-DWP Welfare”, £ million, nominal, {dy} and 1955-56 outturn. Shares are calculated on this page.",
        )
    )
    body.append(
        f"""<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>The series stop at {last}. For 2022-23 the OBR grew social security from the previous year's figure instead of measuring it.</li>
<li>The OBR joined several sources to make the long series: IFS figures from 1955-56 and HM Treasury figures from 2020-21. The OBR says these are not National Statistics and that it made judgements to keep the figures consistent. The database was last updated in July 2023, so later revisions are not included.</li>
<li>The pensioner split starts in 1978-79. Per-person figures start in 1971-72, the first year with a mid-year population estimate in the data used.</li>
<li>Per-person figures are averages across the whole population, including children and people who receive little or nothing, so they are not what any one person or household received.</li>
</ul></div>"""
    )
    body.append(
        source_line(
            sources,
            SOURCES_USED,
            "Sheets “Spending (per cent of GDP)” and “Spending (£m)” of the historical database; the GDP deflator from the October 2026 databank; mid-year population from the ONS.",
        )
    )
    return page(
        "welfare.html",
        "Welfare spending over 50 years",
        "\n".join(body),
        "UK welfare spending (social security: benefits and the State Pension) since 1955-56, after inflation, per person, as a share of GDP and of all public spending, with and without pensions.",
    )
