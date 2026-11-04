"""Pages answering the four public-money questions."""
from .data import Fact
from .explain import box as explain
from .html import FOLD, before_toc, page, bars, change_bars, keyfigs, table, details_table, line_chart, small_multiples, switch, view_link, source_line, fmt, esc
from . import findings as F

# What each way of showing money means, in one sentence, shown with every cash / real / GDP switch.
VIEW_NOTES = {
    "cash": "Pounds as they were at the time. Not adjusted for rising prices, so earlier years look smaller partly because prices were lower.",
    "real": "Adjusted to 2025-26 prices with the GDP deflator, a measure of prices across the whole economy (not the prices households pay), so different years can be compared.",
    "gdp": "As a share of GDP, the value of everything produced in the UK that year. A share can fall while the amount rises, if the economy grows faster.",
}
VIEW_LABELS = {"cash": "Cash", "real": "After inflation", "gdp": "Share of GDP"}
VIEW_LEGEND = "Show amounts as"


def views(make, order=("cash", "real", "gdp"), default="real", notes=None, anchor=None):
    """A cash / real terms / % of GDP switch. make(view) returns the chart for that view."""
    notes = notes or {}
    return switch(VIEW_LEGEND, [(VIEW_LABELS[v], notes.get(v, VIEW_NOTES[v]), make(v)) for v in order], default=list(order).index(default), anchor=anchor)


def derive(facts, fid, value, unit, period, source, inputs, formula, note=""):
    if fid not in facts:
        facts.add(Fact(fid, value, unit, period, source, facts[inputs[0]].locator, "calculated", note=note, formula=formula, inputs=list(inputs)))
    return fid


def per_person(facts, fid, pop, prefix, period, source):
    """£ billion spread across every UK resident: an average, not anyone's bill."""
    out = derive(facts, f"{prefix}.{period}", facts[fid].value * 1e9 / facts[pop].value, "£ per person", period, source,
                 [fid, pop], f"{fid} × 1000000000 ÷ {pop}",
                 note="Average across the whole UK population, including children; mid-year population estimate.")
    derive(facts, f"{out}.week", facts[out].value / 52, "£ per person per week", period, source, [out], f"{out} ÷ 52",
           note="A year counted as 52 weeks.")
    return out


def per_household(facts, fid, hh, prefix, period, source):
    """£ billion spread across every UK household: an average, not any household's bill."""
    out = derive(facts, f"{prefix}.{period}", facts[fid].value * 1e9 / facts[hh].value, "£ per household", period, source,
                 [fid, hh], f"{fid} × 1000000000 ÷ {hh}",
                 note="Average across all UK private households (ONS, April to June), whatever their size or income.")
    derive(facts, f"{out}.week", facts[out].value / 52, "£ per household per week", period, source, [out], f"{out} ÷ 52",
           note="A year counted as 52 weeks.")
    return out


def households_for(period):
    """The household count inside a financial year: April to June of its first calendar year."""
    return f"hh.uk.{period[:4]}"


def scale_box(num, fid, pop, what, extra="", hid=None, hh=None):
    """A sense of scale for a national total, labelled as an average across everyone (and every household)."""
    house = ""
    if hid:
        house = (f' Shared across the {num(hh, "millions_raw")} households in the UK (April to June {hh.rsplit(".", 1)[-1]}), it is about '
                 f'{num(hid, "pounds")} per household, or {num(hid + ".week", "pounds")} a week.')
    return (f'<p class="scale"><strong>For scale:</strong> {what} works out at about {num(fid, "pounds")} for every person living in the UK '
            f'({num(pop, "millions_raw")} people in mid-{fid.rsplit(".", 1)[-1][:4]}), or about {num(fid + ".week", "pounds")} a week.{house}{extra}</p>')


# ---------------------------------------------------------------- spending

def spending_page(facts, d, num, sources):
    sp = d["spending"]
    y = sp["latest"]
    years = sp["years"]
    first = years[0]
    ten = years[-11]
    per = sp["per100"]
    order = _areas(facts, sp)
    top, second = order[0], order[1]
    adj = f"spend.cash.adjustments.{y}"
    pop = f"pop.uk.{y[:4]}"  # mid-year population, 30 June, inside the financial year
    pp = per_person(facts, f"spend.cash.tme.{y}", pop, "spend.perperson.tme", y, "pesa4")
    hh = households_for(y)
    ph = per_household(facts, f"spend.cash.tme.{y}", hh, "spend.perhousehold.tme", y, "pesa4")
    body = [f"<h1>Where does public money go?</h1>"]
    body.append(keyfigs([(num(f"spend.cash.tme.{y}", "bn"), f"spent by the UK public sector in {y}", True),
                         (num(per[top[0]], "per100"), "of every £100 spent on services went on social protection, the largest area", False),
                         (num(per[second[0]], "per100"), "of every £100 spent on services went on health, the next largest", False)]))
    di_tme = derive(facts, f"spend.per100tme.debt_interest.{y}", 100 * facts[f"spend.cash.debt_interest.{y}"].value / facts[f"spend.cash.tme.{y}"].value,
                    "£ per £100", y, "pesa4", [f"spend.cash.debt_interest.{y}", f"spend.cash.tme.{y}"],
                    f"100 × spend.cash.debt_interest.{y} ÷ spend.cash.tme.{y}")
    body.append(f'''<div class="answer"><p class="lede">In {y} the UK public sector spent {num(f"spend.cash.tme.{y}", "bn")} in total, {num(f"spend.gdp.tme.{y}", "pct")} of GDP.</p>
<p>Of every £100 spent on services, the largest share, {num(per[top[0]], "per100")}, went on <strong>social protection</strong>: mainly State Pension, other benefits and social care.
<strong>Health</strong> was next with {num(per[second[0]], "per100")}.</p>
<p>See it {view_link("as a share of GDP over time", "tme-views", 2)} or <a href="international.html">beside other countries</a>.</p></div>''')
    body.append(f'<h2 id="per100">Out of every £100 spent on services, {y}</h2>')
    items = [(esc(name), per[k], "") for k, name in order]
    body.append(bars(items, "per100", num, caption=f"Rounded to the nearest pound, so the amounts may not add up to exactly £100. General public services includes interest on government debt, {num(per['debt_interest'], 'per100')} of every £100 spent on services. The split is of the {num(f'spend.cash.services.{y}', 'bn')} spent on services; the other {num(adj, 'bn')} is accounting adjustments."))
    # The chart comes first on a phone; scale and definitions follow it.
    body.append(before_toc(scale_box(num, pp, pop, f"spending in {y}", hid=ph, hh=hh, extra=" These are averages across everyone, including children, not the amount spent on any one person or household.")
                           + "<p>“Public sector” means central government, devolved governments, local councils and public corporations together. The financial year runs from April to March.</p>"))
    body.append(FOLD)
    body.append(f'''<p class="small">Two items inside these areas are often asked about: interest on government debt ({num(per["debt_interest"], "per100")} of every £100 spent on services, or {num(di_tme, "per100dp1")} of every £100 of total spending) is part of “general public services”; this counts interest paid out, and the “net” figure the OBR and IFS often quote, which subtracts interest received, is lower (<a href="borrowing.html#interest">debt interest beside other countries</a>). Transport ({num(per["transport"], "per100")}) is part of “economic affairs”. Pensions in old age cost {num(sp["oldage"], "bn")} in {y}, inside social protection. This is HM Treasury’s “old age: of which pensions” line, which covers more than the State Pension alone.</p>''')
    body.append(explain("debt-interest-2022", sources))
    rows = []
    for k, name in order:
        rows.append([esc(name), num(f"spend.cash.{k}.{y}", "bn1"), num(per[k], "dp1"),
                     num(per_person(facts, f"spend.cash.{k}.{y}", pop, f"spend.perperson.{k}", y, "pesa4"), "pounds"),
                     num(per_household(facts, f"spend.cash.{k}.{y}", hh, f"spend.perhousehold.{k}", y, "pesa4"), "pounds")])
    rows.append(["<strong>Spending on services</strong>", num(f"spend.cash.services.{y}", "bn1"), "100.0",
                 num(per_person(facts, f"spend.cash.services.{y}", pop, "spend.perperson.services", y, "pesa4"), "pounds"),
                 num(per_household(facts, f"spend.cash.services.{y}", hh, "spend.perhousehold.services", y, "pesa4"), "pounds")])
    rows.append(["Accounting adjustments (not split by area)", num(adj, "bn1"), "–", "–", "–"])
    rows.append(["<strong>Total managed expenditure</strong>", num(f"spend.cash.tme.{y}", "bn1"), "–", num(pp, "pounds"), num(ph, "pounds")])
    body.append(details_table("Show these figures as a table", f"Public spending by area, {y}, £ billion (cash), £ per £100 of spending on services, £ per UK resident and £ per UK household",
                              ["Area", "£bn", "£ per £100", "£ per person*", "£ per household*"], rows))
    body.append(f'<p class="small">* Spending divided by the UK population in mid-{y[:4]} ({num(pop, "millions_raw")}), including children, or by the {num(hh, "millions_raw")} UK households in April to June {y[:4]}. Averages across everyone, not what is spent on any one person or household.</p>')
    body.append(f'''<div class="limit"><p><strong>Limits.</strong> The £100 split uses spending on services ({num(f"spend.cash.services.{y}", "bn")}), not total spending. The difference, {num(adj, "bn")}, is accounting adjustments that HM Treasury does not divide between areas.
Areas follow the international COFOG classification. “Defence” here excludes military pensions, which count as social protection, so it differs from the NATO defence figure.
Interest on government debt here is the interest paid out (HM Treasury: “gross payments to the private sector and overseas”). The OBR and the IFS often quote “net” debt interest, which subtracts interest the public sector receives, so their figure for the same year is lower.</p></div>''')
    body.append(source_line(sources, ["pesa4", "pesa5"], f"Tables 4.2 and 5.2, outturn for {first} to {y}. Outturn figures can still be revised."))

    # change over time
    body.append(f'<h2 id="change">How has spending changed since {first}?</h2>')
    tme_real = [facts[f"spend.real.tme.{yy}"].value for yy in years]
    tme_gdp = [facts[f"spend.gdp.tme.{yy}"].value for yy in years]
    derive(facts, f"spend.realchange.tme.{first}.{y}", 100 * (tme_real[-1] / tme_real[0] - 1), "%", f"{first} to {y}", "pesa4",
           [f"spend.real.tme.{y}", f"spend.real.tme.{first}"], f"100 × (spend.real.tme.{y} ÷ spend.real.tme.{first} − 1)")
    # Per person (audit 15 judge, R4): the same real totals divided by the mid-year population of each year.
    for yy in years:
        derive(facts, f"spend.realpp.tme.{yy}", facts[f"spend.real.tme.{yy}"].value * 1e9 / facts[f"pop.uk.{yy[:4]}"].value,
               "£ per person, 2025-26 prices", yy, "pesa4", [f"spend.real.tme.{yy}", f"pop.uk.{yy[:4]}"],
               f"spend.real.tme.{yy} × 1,000,000,000 ÷ pop.uk.{yy[:4]}")
    pp_real = {yy: facts[f"spend.realpp.tme.{yy}"].value for yy in years}
    derive(facts, f"spend.realppchange.tme.{first}.{y}", 100 * (pp_real[y] / pp_real[first] - 1), "%", f"{first} to {y}", "pesa4",
           [f"spend.realpp.tme.{y}", f"spend.realpp.tme.{first}"], f"100 × (spend.realpp.tme.{y} ÷ spend.realpp.tme.{first} − 1)")
    derive(facts, f"pop.uk.change.{first}.{y}", 100 * (facts[f"pop.uk.{y[:4]}"].value / facts[f"pop.uk.{first[:4]}"].value - 1), "%", f"{first} to {y}", "ons-ukpop",
           [f"pop.uk.{y[:4]}", f"pop.uk.{first[:4]}"], f"100 × (pop.uk.{y[:4]} ÷ pop.uk.{first[:4]} − 1)")
    body.append(f'''<div class="answer"><p>After adjusting for rising prices, total spending in {y} was {num(f"spend.realchange.tme.{first}.{y}", "pct0")} higher than in {first}.
As a share of the whole economy (GDP) it went from {num(f"spend.gdp.tme.{first}", "pct")} to {num(f"spend.gdp.tme.{y}", "pct")}. <a href="international.html">How this compares with other countries</a>.</p>
<p>Per person, after inflation, it was {num(f"spend.realppchange.tme.{first}.{y}", "pct0")} higher than in {first}. The population grew {num(f"pop.uk.change.{first}.{y}", "pct0")} over the same years, so the total overstates how much spending per person has grown.</p></div>''')
    covid = [(years.index("2020-21"), "Covid")]
    tme_kind = {"cash": "bn", "real": "bn", "gdp": "pct"}
    tme_unit = {"cash": "£ billion, cash", "real": "£ billion, 2025-26 prices (adjusted with the GDP deflator)", "gdp": "Per cent of GDP"}
    tme_title = {"cash": "Total public spending in cash", "real": "Total public spending after inflation", "gdp": "Total public spending as a share of GDP"}

    def tme_chart(v):
        vals = [facts[f"spend.{v}.tme.{yy}"].value for yy in years]
        return line_chart(tme_title[v], years, [("Total managed expenditure", vals, "a")], tme_unit[v], events=covid,
                          finding=F.trend({"cash": "Total public spending in cash", "real": "After inflation, total public spending",
                                           "gdp": "As a share of GDP, total public spending"}[v]),
                          desc=f"From {fmt(vals[0], tme_kind[v])} in {first} to {fmt(vals[-1], tme_kind[v])} in {y}.",
                          kind=tme_kind[v], num=num, ids=[[f"spend.{v}.tme.{yy}" for yy in years]], ymin=0 if v != "gdp" else None)
    body.append(views(tme_chart, anchor="tme-views"))
    body.append(FOLD)
    body.append(explain("covid-spending", sources))
    body.append(explain("energy-2022", sources))
    rows = [[yy, num(f"spend.cash.tme.{yy}", "bn1"), num(f"spend.real.tme.{yy}", "bn1"), num(f"spend.realpp.tme.{yy}", "pounds"), num(f"spend.gdp.tme.{yy}", "pct")] for yy in years]
    body.append(details_table("Show total spending for every year", "Total managed expenditure, every year",
                              ["Year", "Cash £bn", "£bn, 2025-26 prices", "£ per person, 2025-26 prices", "% of GDP"], rows))
    # ten-year change by area
    body.append(f"<h2 id='by-area'>Change by area over ten years: {ten} to {y}</h2><p>After adjusting for inflation. The two years are a fixed ten years apart, not chosen for the result.</p>")
    rows, citems = [], []
    for k, name in order:
        a, b = facts[f"spend.real.{k}.{ten}"].value, facts[f"spend.real.{k}.{y}"].value
        cid = derive(facts, f"spend.realchange.{k}.{ten}.{y}", 100 * (b / a - 1), "%", f"{ten} to {y}", "pesa4",
                     [f"spend.real.{k}.{y}", f"spend.real.{k}.{ten}"], f"100 × (spend.real.{k}.{y} ÷ spend.real.{k}.{ten} − 1)")
        citems.append((esc(name), cid, f'{num(f"spend.real.{k}.{ten}", "bn1")} to {num(f"spend.real.{k}.{y}", "bn1")}'))
        rows.append([esc(name), num(f"spend.real.{k}.{ten}", "bn1"), num(f"spend.real.{k}.{y}", "bn1"), num(cid, "pct0"),
                     num(f"spend.gdp.{k}.{ten}", "pct"), num(f"spend.gdp.{k}.{y}", "pct")])
    body.append(change_bars(citems, "pct0", num, caption=f"Change in spending after inflation, {ten} to {y}. Bars to the right are rises, to the left falls. Under each area: £ billion in 2025-26 prices, then and now."))
    body.append(f'<p class="more-link"><a href="{AREAS_PAGE}">Each area, every year from {first} to {y}</a>: one small chart per area, in cash, after inflation or as a share of GDP, with the full tables.</p>')
    body.append(FOLD)
    body.append(details_table("Show the amounts and shares of GDP", f"Spending by area, {ten} and {y}", ["Area", f"{ten} £bn*", f"{y} £bn*", "Change", f"{ten} % GDP", f"{y} % GDP"], rows))
    body.append('<p class="small">* £ billion in 2025-26 prices.</p>')
    body.append('<p class="small">Other publications give slightly different totals for the same year because they are published at different times and use different scopes. For example, the OBR databank used on the <a href="taxes.html">taxes page</a> puts 2025-26 spending at £1,366bn.</p>')
    return page("spending.html", "Where does public money go?", "\n".join(body), "UK public spending by area, with history after inflation and as a share of GDP.", toc_after_first=True)


AREAS_PAGE = "spending-areas.html"

# (area, first year on the new basis, why), from HM Treasury's PESA table footnotes.
AREA_BREAKS = [
    ("education", "2011-12", "student loans were removed from education from 2011-12"),
    ("economic", "2015-16", "Network Rail spending is counted here, under transport, only from 2015-16"),
]


def _areas(facts, sp):
    """Spending areas, largest share of spending on services first."""
    funcs = [(k, s["name"]) for k, s in sp["views"]["cash"]["series"].items()
             if k not in ("services", "adjustments", "tme", "debt_interest", "transport", "eu")]
    return sorted(funcs, key=lambda kv: -facts[sp["per100"][kv[0]]].value)


def spending_areas_page(facts, d, num, sources):
    """Every area, every year: small multiples and full tables, linked from the spending page."""
    sp = d["spending"]
    y, years = sp["latest"], sp["years"]
    first = years[0]
    order = _areas(facts, sp)
    body = ['<p class="small"><a href="spending.html">Where does public money go?</a></p>',
            f"<h1>Spending on each area, every year from {first} to {y}</h1>"]
    body.append(f'<p>One small chart for each area of <a href="spending.html">public spending</a>, so you can see when each one rose or fell. Switch between cash, after inflation and share of GDP. '
                f'For spending on health, education, defence, social security and debt interest back to 1900, see <a href="spending-history.html">spending by purpose over 100 years</a>. For welfare (social security) over the last 50 years, see <a href="welfare.html">welfare spending over 50 years</a>.</p>')
    area_kind = {"cash": "bn", "real": "bn", "gdp": "pct"}
    area_unit = {"cash": "£ billion, cash", "real": "£ billion, 2025-26 prices", "gdp": "Per cent of GDP"}

    # HM Treasury's footnotes: these areas are not directly comparable across these years,
    # so their lines break there and their changes are read only from the break on.
    keys = [k for k, _ in order]
    area_breaks = {keys.index(k): [(years.index(yy), why)] for k, yy, why in AREA_BREAKS if k in keys and yy in years[1:]}

    def area_chart(v):
        return small_multiples(f"Spending by area, {first} to {y}", [yy[:4] for yy in years], [(n.split(" (")[0], [facts[f"spend.{v}.{k}.{yy}"].value for yy in years]) for k, n in order],
                               area_unit[v] + ". Axis years are financial years starting in April of the year shown.", area_kind[v], point_labels=years, ids=[[f"spend.{v}.{k}.{yy}" for yy in years] for k, _ in order], num=num,
                               summary_note="The tables below give every area's figure for every year.", ymin=0 if v != "gdp" else None,
                               finding=F.leader("{name} was the largest area of spending {span}"),
                               group_breaks=area_breaks, pct_change=(v != "gdp"))
    body.append(views(area_chart))
    # full history tables per view
    for view, label, kind in (("real", "£ billion, 2025-26 prices", "bn1"), ("gdp", "% of GDP", "pct"), ("cash", "£ billion, cash (not adjusted for inflation)", "bn1")):
        head = ["Year"] + [esc(n.split(" (")[0]) for _, n in order] + ["Total"]
        rows = [[yy] + [num(f"spend.{view}.{k}.{yy}", kind) for k, _ in order] + [num(f"spend.{view}.tme.{yy}", kind)] for yy in years]
        body.append(details_table(f"Every year by area: {label}", f"Spending by area, {first} to {y}, {label}", head, rows))
    body.append('''<div class="limit"><p><strong>Breaks in the figures.</strong> From 2011-12 the cost of student loans was removed from education, so education before and after that year is not directly comparable.
Network Rail is counted under transport, part of economic affairs, only from 2015-16. Their lines break at those years, and their changes are worked out only from then on. Spending in 2020-21 and 2021-22 includes temporary Covid-19 measures. These notes come from HM Treasury's table footnotes.</p></div>''')
    body.append(source_line(sources, ["pesa4"], "Tables 4.2 (cash), 4.3 (real terms, GDP deflator from the ONS released 30 June 2026) and 4.4 (% of GDP)."))
    return page(AREAS_PAGE, "Spending on each area, every year", "\n".join(body),
                "UK public spending on each area every year, in cash, after inflation and as a share of GDP.", contents=False, folded=False)


# ---------------------------------------------------------------- taxes

def taxes_page(facts, d, num, sources):
    rc = d["receipts"]
    y = "2025-26"
    groups = rc["groups"]
    big3 = sum(facts[f"rec.{k}.{y}"].value for k in ("income_tax", "nics", "vat"))
    derive(facts, f"rec.big3share.{y}", 100 * big3 / facts[f"rec.taxes.{y}"].value, "% of all taxes", y, "obr",
           [f"rec.income_tax.{y}", f"rec.nics.{y}", f"rec.vat.{y}", f"rec.taxes.{y}"], f"100 × (rec.income_tax + rec.nics + rec.vat) ÷ rec.taxes, {y}")
    pop = f"pop.uk.{y[:4]}"
    tpp = per_person(facts, f"rec.taxes.{y}", pop, "rec.perperson.taxes", y, "obr")
    bpp = per_person(facts, f"agg.psnb.{y}", pop, "agg.perperson.psnb", y, "obr")
    dpp = per_person(facts, f"agg.psnd.{y}", pop, "agg.perperson.psnd", y, "obr")
    hh = households_for(y)
    tph = per_household(facts, f"rec.taxes.{y}", hh, "rec.perhousehold.taxes", y, "obr")
    bph = per_household(facts, f"agg.psnb.{y}", hh, "agg.perhousehold.psnb", y, "obr")
    dph = per_household(facts, f"agg.psnd.{y}", hh, "agg.perhousehold.psnd", y, "obr")
    body = ["<h1>Which taxes raise the money?</h1>"]
    body.append(keyfigs([(num(f"rec.taxes.{y}", "bn"), f"raised in taxes in {y}", True),
                         (num(f"rec.big3share.{y}", "pct0"), "of all tax came from Income Tax, National Insurance and VAT", False),
                         (num(f"agg.psnb.{y}", "bn"), "borrowed to cover spending above receipts (not tax)", False)]))
    body.append(f'''<div class="answer"><p class="lede">In {y} the UK public sector received {num(f"rec.total.{y}", "bn")}. Most of it, {num(f"rec.taxes.{y}", "bn")}, was tax.</p>
<p>Three taxes raised {num(f"rec.big3share.{y}", "pct0")} of all tax: Income Tax ({num(f"rec.income_tax.{y}", "bn")}), National Insurance ({num(f"rec.nics.{y}", "bn")}) and VAT ({num(f"rec.vat.{y}", "bn")}).
Spending was higher than receipts, so the government borrowed {num(f"agg.psnb.{y}", "bn")} to cover the gap.</p></div>''')
    body.append(f'<h2 id="where">Where the {y} money came from</h2><p>Three different kinds of money pay for public spending. Only the first is tax.</p>')
    items = [(esc(n), f"rec.{k}.{y}", "") for k, n in groups] + [("All other taxes", f"rec.othertax.{y}", "")]
    top = facts[f"rec.income_tax.{y}"].value
    body.append(f"<h3>1. Taxes: {num(f'rec.taxes.{y}', 'bn')}</h3>")
    body.append(bars(items, "bn", num, maxval=top))
    # The chart comes first on a phone; the per-person scale follows the section.
    body.append(before_toc(scale_box(num, tpp, pop, f"tax raised in {y}", hid=tph, hh=hh,
                                     extra=f" Borrowing was {num(bpp, 'pounds')} per person, or {num(bph, 'pounds')} per household. These divide all tax, including tax paid by businesses, by everyone, including children and people who pay little or no tax, so they are not anyone's tax bill: see <a href=\"who-pays.html\">who pays</a>.")
                           # Readers looked here for the £30,000 employee (audit 10 gap 2); it lives on Tax and income, apart from these measured totals.
                           + '<p>What one employee pays is on Tax and income: a <a href="household-tax.html#worked-example">worked example of a made-up employee on £30,000</a> (an illustration, not a statistic).</p>'))
    body.append(f'''<h3>2. Other receipts (not taxes): {num(f"rec.nontax.{y}", "bn")}</h3>
<p>Interest and dividends the public sector receives, the operating surplus of public bodies, and similar income.</p>
<h3>3. Borrowing: {num(f"agg.psnb.{y}", "bn")}</h3>
<p>Borrowing is not income from tax. It is the gap between spending ({num(f"agg.tme.{y}", "bn")} on this basis) and receipts ({num(f"rec.total.{y}", "bn")}), and it adds to the national debt.</p>''')
    body.append(FOLD)
    body.append(f'<p class="small">“All other taxes” includes business rates, vehicle and air passenger duties, insurance premium tax, environmental levies and others. Income Tax combines PAYE, self assessment and other Income Tax; Corporation Tax includes Corporation Tax on North Sea profits; the other North Sea taxes (the Energy Profits Levy and Petroleum Revenue Tax) are in “All other taxes”. The VAT line is already net of refunds, but “All other taxes” is all taxes less the named ones, so it includes the {num(f"rec.vatrefunds.{y}", "bn1")} of VAT refunds in {y}.</p>')
    rows = [[esc(n), num(f"rec.{k}.{y}", "bn1")] for k, n in groups] + [["All other taxes", num(f"rec.othertax.{y}", "bn1")],
            ["<strong>All taxes</strong>", num(f"rec.taxes.{y}", "bn1")], ["Other receipts (not taxes)", num(f"rec.nontax.{y}", "bn1")],
            ["<strong>All receipts</strong>", num(f"rec.total.{y}", "bn1")], ["Borrowing (public sector net borrowing)", num(f"agg.psnb.{y}", "bn1")],
            ["<strong>Total spending (OBR basis)</strong>", num(f"agg.tme.{y}", "bn1")]]
    body.append(details_table("Show these figures as a table", f"Public sector receipts and borrowing, {y}, £ billion", ["Item", "£bn"], rows))
    body.append(f'''<h2 id="debt">Borrowing is not the same as debt</h2>
<p><strong>Borrowing</strong> is what the government adds in one year: {num(f"agg.psnb.{y}", "bn")} in {y}. <strong>Debt</strong> is the total still owed from all past years: {num(f"agg.psnd.{y}", "bn")} at the end of March 2026 (public sector net debt), equal to {num(f"gdp.psnd.{y}", "pct")} of GDP (the OBR's measure, which uses GDP for the year centred on the end of March), or about {num(dpp, "pounds")} per person ({num(dph, "pounds")} per household). That is the debt divided by everyone, an average, not anyone’s bill: it is owed by the public sector, not by people or households. <a href="borrowing.html">Compare UK debt with the G7</a>.</p>''')
    body.append(source_line(sources, ["obr"], f"Sheets “Receipts (£bn)” and “Aggregates (£bn)”. {y} is outturn and can still be revised; years from {rc['forecast_from']} are OBR forecasts."))

    # history as % of GDP
    gy = [g for g in rc["gdp_years"] if facts.get(f"gdp.receipts.{g}") and facts[f"gdp.receipts.{g}"].value is not None]
    fc = next((i for i, g in enumerate(gy) if g >= rc["forecast_from"]), None)
    body.append(f"<h2 id='history'>Receipts and spending since {gy[0]}</h2>")
    body.append(f"<p>Taxes alone were {num(f'rec.gdp.taxes.{y}', 'pct')} of GDP in {y}, a share news reports often call the <a href='glossary.html#tax-burden'>“tax burden”</a>. "
                "It compares all tax, paid by people and businesses, with the size of the economy, so it is not anyone's tax bill: "
                "<a href='household-tax.html'>tax and income</a> shows what households pay. "
                "<a href='international.html'>How the UK compares with other countries</a> uses the OECD's measure, the same for every country.</p>")
    rec_title = {"cash": "Receipts and spending in cash", "real": "Receipts and spending after inflation", "gdp": "Receipts and spending as a share of GDP"}
    rec_unit = {"cash": "£ billion, cash. Source: OBR public finances databank.", "real": "£ billion, 2025-26 prices (OBR GDP deflator). Source: OBR public finances databank.",
                "gdp": "Per cent of GDP. Source: OBR public finances databank."}
    rec_ids = {"cash": ("agg.receipts", "agg.tme"), "real": ("agg.real.receipts", "agg.real.tme"), "gdp": ("gdp.receipts", "gdp.tme")}

    def rec_chart(v):
        a, b = rec_ids[v]
        # Start the axis at the first year with figures, so the after-inflation view is not labelled from a year it has no data for.
        k = next(i for i, g in enumerate(gy) if f"{a}.{g}" in facts or f"{b}.{g}" in facts)
        ys = gy[k:]
        ids = [[f"{a}.{g}" if f"{a}.{g}" in facts else None for g in ys], [f"{b}.{g}" if f"{b}.{g}" in facts else None for g in ys]]
        vals = [[facts[i].value if i else None for i in row] for row in ids]
        return line_chart(rec_title[v], ys, [("Receipts", vals[0], "a"), ("Spending", vals[1], "b")], rec_unit[v], forecast_from=None if fc is None else fc - k, ymin=0,
                          finding=F.gap("Spending", "receipts", si=1, sj=0),
                          kind="pct" if v == "gdp" else "bn", num=num, ids=ids)
    first_real = rc["real_years"][0]
    body.append(views(rec_chart, order=("gdp", "real"), default="gdp",
                      notes={"real": VIEW_NOTES["real"] + f" The OBR's deflator starts in {first_real}, so this view starts there."}))
    body.append(FOLD)
    body.append('<p class="small">Cash amounts are not shown for this long period because prices rose many times over, so they cannot be compared across the years. Cash figures for each tax since 1999-00 are below.</p>')
    body.append(explain("borrowing-records", sources))
    rows = [[g + (" (forecast)" if g >= rc["forecast_from"] else ""), num(f"gdp.receipts.{g}", "pct"), num(f"gdp.tme.{g}", "pct"), num(f"gdp.psnb.{g}", "pct"), num(f"gdp.psnd.{g}", "pct")] for g in gy]
    body.append(details_table("Show every year", f"Receipts, spending, borrowing and debt, % of GDP, {gy[0]} to {gy[-1]}", ["Year", "Receipts", "Spending", "Borrowing", "Debt"], rows))
    rg = [g for g in gy if f"agg.real.receipts.{g}" in facts]
    rows = [[g + (" (forecast)" if g >= rc["forecast_from"] else ""), num(f"agg.real.receipts.{g}", "bn1"), num(f"agg.real.tme.{g}", "bn1")] for g in rg]
    body.append(details_table("Show every year after inflation", f"Receipts and spending, £ billion in 2025-26 prices, {rg[0]} to {rg[-1]}",
                              ["Year", "Receipts", "Spending"], rows))
    body.append(f'<p class="small">After-inflation amounts = cash × 100 ÷ GDP deflator (2025-26 = 100). The cash amounts and the deflator for every year are in the source record linked from each figure. The deflator in this databank starts in {first_real}. It measures prices across the whole economy, not only what households buy. Forecast years use OBR forecasts of prices and GDP.</p>')
    # taxes by type over time
    ty = rc["years"]
    body.append(f"<h3>The three largest taxes since {ty[0]}</h3><p>Income Tax, National Insurance and VAT. Forecast years are shaded and dashed.</p>")
    tfc = next((i for i, t in enumerate(ty) if t >= rc["forecast_from"]), None)
    big = [("income_tax", "Income Tax", "a"), ("nics", "National Insurance", "b"), ("vat", "VAT", "c")]
    tax_pre = {"cash": "rec", "real": "rec.real", "gdp": "rec.gdp"}
    tax_unit = {"cash": "£ billion, cash", "real": "£ billion, 2025-26 prices (OBR GDP deflator)", "gdp": "Per cent of GDP (cash receipts ÷ nominal GDP for the same year)"}

    def tax_chart(v):
        ids = [[f"{tax_pre[v]}.{k}.{t}" for t in ty] for k, _, _ in big]
        return line_chart(f"Income Tax, National Insurance and VAT, {VIEW_LABELS[v].lower()}", ty,
                          [(n, [facts[i].value for i in row], st) for (k, n, st), row in zip(big, ids)], tax_unit[v], forecast_from=tfc, ymin=0,
                          finding=F.leader("{name} raised the most of the three {span}"),
                          kind="pct" if v == "gdp" else "bn", num=num, ids=ids)
    body.append(views(tax_chart))
    rows = [[t + (" (forecast)" if t >= rc["forecast_from"] else "")] + [num(f"rec.real.{k}.{t}", "bn1") for k, _, _ in big] + [num(f"rec.gdp.{k}.{t}", "pct") for k, _, _ in big] for t in ty]
    body.append(details_table("Show these three taxes after inflation and as a share of GDP", f"Income Tax, National Insurance and VAT, {ty[0]} to {ty[-1]}: £ billion in 2025-26 prices, and % of GDP",
                              ["Year", "Income Tax £bn*", "NI £bn*", "VAT £bn*", "Income Tax % GDP", "NI % GDP", "VAT % GDP"], rows))
    body.append('<p class="small">* £ billion in 2025-26 prices, using the OBR\'s GDP deflator (2025-26 = 100). Forecast years use the OBR\'s forecast deflator and GDP.</p>')
    body.append("<p>Every main tax in cash, as published:</p>")
    rows = []
    for t in ty:
        rows.append([t + (" (forecast)" if t >= rc["forecast_from"] else "")] + [num(f"rec.{k}.{t}", "bn1") for k in ("income_tax", "nics", "vat", "corp", "council")] + [num(f"rec.taxes.{t}", "bn1")])
    body.append(details_table("Show main taxes for every year", f"Main taxes, £ billion cash, {ty[0]} to {ty[-1]}",
                              ["Year", "Income Tax", "National Insurance", "VAT", "Corporation Tax", "Council Tax", "All taxes"], rows))
    body.append(explain("frozen-thresholds", sources))
    body.append('<div class="limit"><p><strong>Limits.</strong> Forecasts are the OBR\'s October 2026 projections, not measurements. Debt and borrowing use the public sector definitions in the OBR databank; other published debt measures give different totals.</p></div>')
    body.append(source_line(sources, ["obr", "obr-prices"], "Sheets “Aggregates (per cent of GDP)”, “Aggregates (£bn)” (including GDP and the GDP deflator) and “Receipts (£bn)”."))
    from .pages_money_extra import tax_mix_section  # local import: that module imports derive from here
    body.append(tax_mix_section(facts, d, num, sources))
    return page("taxes.html", "Which taxes raise the money?", "\n".join(body), "UK tax receipts by tax, other receipts and borrowing, with history.", toc_after_first=True)


# ---------------------------------------------------------------- who pays

def fifth_indirect_caveat(facts, num):
    """The lowest fifth's indirect tax as a share of its spending, beside the other fifths' range (audit 15 judge, L1).

    Returns (lowest-fifth figure, lowest other figure, highest other figure) as formatted text, so the
    home page and who-pays give the same caveat as household tax, with its figures read from the source.
    """
    others = [f"etb.t8.spend.indirect.q{i}" for i in range(2, 6)]
    lo_id = min(others, key=lambda i: facts[i].value)
    hi_id = max(others, key=lambda i: facts[i].value)
    return num("etb.t8.spend.indirect.q1", "pct"), num(lo_id, "pct"), num(hi_id, "pct")


QUINTS = [("q1", "Lowest-income fifth"), ("q2", "Second fifth"), ("q3", "Middle fifth"), ("q4", "Fourth fifth"), ("q5", "Highest-income fifth"), ("all", "Everyone")]


FIFTHS = [q for q, _ in QUINTS if q != "all"]


def household_tax_shares(facts):
    """Each fifth's share of all taxes paid by UK households (ONS Table 2a).

    Average taxes per household × number of households in the fifth, divided by the
    total of the five fifths. It is a share of household taxes, not of government revenue.
    """
    for q in FIFTHS:
        derive(facts, f"etb.2a.hhtax.{q}", facts[f"etb.2a.alltax.{q}"].value * facts[f"etb.2a.households.{q}"].value / 1e6,
               "£ billion", "2023/24", "etb", [f"etb.2a.alltax.{q}", f"etb.2a.households.{q}"],
               f"etb.2a.alltax.{q} × etb.2a.households.{q} ÷ 1000000",
               note="Average taxes per household × households in the fifth, £ billion. Taxes are ONS estimates for households, including indirect taxes.")
    total = sum(facts[f"etb.2a.hhtax.{q}"].value for q in FIFTHS)
    derive(facts, "etb.2a.hhtax.total", total, "£ billion", "2023/24", "etb", [f"etb.2a.hhtax.{q}" for q in FIFTHS],
           " + ".join(f"etb.2a.hhtax.{q}" for q in FIFTHS), note="Sum of the five fifths.")
    for q in FIFTHS:
        derive(facts, f"etb.2a.taxshare.{q}", 100 * facts[f"etb.2a.hhtax.{q}"].value / total, "% of all household taxes", "2023/24", "etb",
               [f"etb.2a.hhtax.{q}", "etb.2a.hhtax.total"], f"100 × etb.2a.hhtax.{q} ÷ etb.2a.hhtax.total")


def who_pays_page(facts, d, num, sources):
    w = d["who"]
    household_tax_shares(facts)
    y = w["hmrc_latest_outturn"]
    body = ["<h1>Who pays?</h1>"]
    cav = fifth_indirect_caveat(facts, num)
    body.append(keyfigs([(num(f"hmrc.share.top1.{y}", "pct"), f"of all Income Tax for the year was owed by the top 1% of Income Tax payers, tax year {y.replace(' to ', '-')}", True),
                         (num("etb.2a.alltax.q1", "pounds"), f'a year in all taxes, on average, for the lowest-income fifth of people: {num("etb.t8.gross.all.q1", "pct")} of their gross income (share of income), 2023/24', False),
                         (num("etb.2a.taxshare.q5", "pct"), "share of all taxes paid by UK households (a share of the total, not of income), 2023/24: the richest fifth paid it", False)]))
    body.append(f'''<div class="answer"><p class="lede">Higher-income people pay most Income Tax. In tax year {y.replace(" to ", "-")}, the top 1% of Income Tax payers owed {num(f"hmrc.share.top1.{y}", "pct")} of all Income Tax, and had {num(f"hmrc.income.top1.{y}", "pct")} of all Income Tax payers' income.</p>
</div>''')
    # HMRC. The chart comes first on a phone; how it is counted follows it.
    body.append('<h2 id="income-tax">1. Income Tax, by person</h2>')
    # Show each group's share of income beside its share of tax, as HMRC does (audit 11 judge, R1).
    items = []
    for key, lab in (("top1", "Top 1%"), ("top10", "Top 10%"), ("top50", "Top 50%"), ("bottom50", "Bottom 50%")):
        items += [(f"{lab}: share of Income Tax", f"hmrc.share.{key}.{y}", ""), (f"{lab}: share of income", f"hmrc.income.{key}.{y}", "alt")]
    body.append(bars(items, "pct", num, maxval=100, caption=f"Share of all Income Tax owed, and share of all Income Tax payers' income, for each group of taxpayers, tax year {y}. The top groups overlap: the top 1% is part of the top 10%."))
    body.append(before_toc("<p>Two official sources answer who pays: HM Revenue and Customs (section 1) and the Office for National Statistics (section 2). They count different people and taxes, so keep them apart.</p>"))
    body.append(FOLD)
    body.append('''<p>HM Revenue and Customs ranks everyone who owes Income Tax by income and adds up the tax each group owes. People who owe no Income Tax are not included.</p>''')
    rows = []
    for key, label, thr in (("top1", "Top 1%", "hmrc.threshold.top1"), ("top10", "Top 10%", "hmrc.threshold.top10"), ("top50", "Top 50%", "hmrc.threshold.top50"), ("bottom50", "Bottom 50%", None)):
        rows.append([label, num(thr, "pounds") if thr else "below " + num("hmrc.threshold.top50", "pounds"), num(f"hmrc.income.{key}.{y}", "pct"), num(f"hmrc.share.{key}.{y}", "pct")])
    body.append(table(f"Income and Income Tax shares, tax year {y}", ["Group of taxpayers", "Income from", "Share of income", "Share of Income Tax"], rows))
    body.append('<p class="small">“Income from” is the income at which each group starts. Income here means income assessable for tax (earnings, pensions, savings and dividends) before allowances.</p>')
    hy = w["hmrc_years"]
    vals = [facts[f"hmrc.share.top1.{h}"].value for h in hy]
    fc = next((i for i, h in enumerate(hy) if int(h[:4]) >= 2024), None)
    body.append(line_chart("Share of Income Tax owed by the top 1% of taxpayers", [h[:4] + "-" + h[-2:] for h in hy],
                           [("Top 1% share of Income Tax", vals, "a"), ("Top 1% share of income", [facts[f"hmrc.income.top1.{h}"].value for h in hy], "b")],
                           "Per cent. Gap at 2008-09: HMRC has no figures for that year. Years from 2024-25 are HMRC projections.",
                           breaks=[(hy.index("2016 to 2017"), "Dividend rules changed")], forecast_from=fc, future="projection", ymin=0,
                           finding=F.gap("The top 1%'s share of Income Tax", "their share of income"),
                           kind="pct", num=num, ids=[[f"hmrc.share.top1.{h}" for h in hy], [f"hmrc.income.top1.{h}" for h in hy]]))
    body.append(explain("top1-share", sources))
    rows = [[h + (" (projection)" if int(h[:4]) >= 2024 else ""), num(f"hmrc.share.top1.{h}", "pct"), num(f"hmrc.share.top10.{h}", "pct"), num(f"hmrc.share.bottom50.{h}", "pct")] for h in hy]
    body.append(details_table("Show every year", "Share of all Income Tax by group of taxpayers", ["Tax year", "Top 1%", "Top 10%", "Bottom 50%"], rows))
    oy = y[:4] + "-" + y[-2:] if " to " in y else y  # the same tax year as the figures above, on the OBR's basis (2023-24 is not 2025-26)
    body.append(f'''<div class="limit"><p><strong>Limits.</strong> This covers Income Tax only, which raised about {num(f"rec.income_tax.{oy}", "bn")} of the {num(f"rec.taxes.{oy}", "bn")} of all taxes in {oy} (OBR). It leaves out people who owe no Income Tax. Rules for dividends changed in 2016-17, so years before and after are not directly comparable. There are no figures for 2008-09.</p></div>''')
    body.append(source_line(sources, ["hmrc24"], "Survey of Personal Incomes. 2023-24 is outturn; later years are projections."))
    # ETB
    body.append(f'''<h2 id="households">2. All taxes, by household income</h2>
<p>Fifths are five equal groups of people, ranked by household income.</p>''')
    rows = []
    for q, label in QUINTS:
        share = num(f"etb.2a.taxshare.{q}", "pct") if q != "all" else "100%"
        rows.append([label, num(f"etb.2a.gross.{q}", "pounds"), num(f"etb.2a.direct.{q}", "pounds"), num(f"etb.2a.indirect.{q}", "pounds"), num(f"etb.2a.alltax.{q}", "pounds"), share])
    body.append(f'''<h3 id="richest-share">The richest fifth's share of all taxes paid</h3>
<div class="answer"><p class="lede">In 2023/24 the richest fifth of people paid {num("etb.2a.taxshare.q5", "pct")} of all taxes paid by UK households.</p>
<p>A share of the total, not the share of income that goes on tax ({num("etb.t8.gross.all.q5", "pct")}, see <a href="household-tax.html">Tax and income</a>). It covers household taxes, not all government revenue.</p>
</div>''')
    body.append(bars([(lab, f"etb.2a.taxshare.{q}", "") for q, lab in QUINTS if q != "all"], "pct", num, maxval=100,
                     caption="Share of all taxes paid by UK households, by fifth of people, 2023/24, per cent (ONS Table 2a)."))
    body.append(FOLD)
    body.append("<p>How the fifths are made: everyone is ranked by their household's income, adjusted for household size, and split into five groups with the same number of people in each. "
                "For each fifth, the ONS then estimates the average income and taxes of the households those people live in. Each fifth has the same number of people, but not the same number of households. "
                "This includes taxes on spending, such as VAT and fuel duty, but not taxes such as Corporation Tax that are not paid directly by households.</p>")
    body.append(table("Average household income and taxes, by fifth of people, £ a year, 2023/24, and each fifth's share of all household taxes", ["Fifth of people", "Gross income", "Direct taxes", "Indirect taxes", "All taxes", "Share of all household taxes"], rows))
    body.append('<p class="small">Direct taxes: Income Tax, employee National Insurance, student loan repayments and Council Tax (after reductions). Indirect taxes: VAT, duties and taxes paid by businesses that are passed on in prices. Gross income includes cash benefits such as the State Pension. Share of all household taxes: each fifth’s average tax per household × its number of households, divided by the total for the five fifths.</p>')
    body.append(f'<div class="limit"><p><strong>Limits.</strong> These are averages for groups of people, using the income and taxes of the household each person lives in, estimated from a survey; no single household is “typical”. Indirect taxes are charged on spending: the lowest fifth paid {cav[0]} of its spending in indirect taxes, close to the other fifths ({cav[1]} to {cav[2]}). ONS warns that lump sums of deferred tax can make its direct taxes look high.</p></div>')
    body.append(source_line(sources, ["etb"], "Table 2a. Survey-based estimates for April 2023 to March 2024."))
    from .pages_money_extra import households_short, net_section, income_tax_age_section
    body.append(households_short(facts, d, num))
    body.append(net_section(facts, d, num, sources))
    body.append(income_tax_age_section(facts, d, num, sources))
    return page("who-pays.html", "Who pays?", "\n".join(body), "Who pays UK taxes: Income Tax shares by taxpayer group and all taxes by household income group.", toc_after_first=True)


# ---------------------------------------------------------------- household tax

def household_tax_page(facts, d, num, sources, rates):
    y = "2025-26"  # latest outturn year in the OBR databank
    derive(facts, f"rec.incomesharetaxes.{y}", 100 * facts[f"rec.income_tax.{y}"].value / facts[f"rec.taxes.{y}"].value, "%", y, "obr",
           [f"rec.income_tax.{y}", f"rec.taxes.{y}"], "100 × Income Tax ÷ all taxes")
    body = ["<h1>How much of household income goes on tax?</h1>"]
    body.append(keyfigs([(num("etb.t8.gross.all.all", "pct"), "of gross household income went on tax, on average across everyone, 2023/24. An average, not anyone's tax rate", True),
                         (num("etb.t8.gross.direct.all", "pct"), "in direct taxes, such as Income Tax", False),
                         (num("etb.t8.gross.indirect.all", "pct"), "in indirect taxes, such as VAT", False)]))
    body.append(f'''<div class="answer"><p class="lede">Across everyone in UK private households, taxes took {num("etb.t8.gross.all.all", "pct")} of gross household income in 2023/24.</p>
<p>The share was similar for the lowest-income fifth of people ({num("etb.t8.gross.all.q1", "pct")}) and the highest-income fifth ({num("etb.t8.gross.all.q5", "pct")}), but it was made up of different taxes.</p></div>''')
    # Readers looking for "what one person pays" could not find the worked example (audit 10 gap 2).
    body.append(f'<p>Looking for what one person pays? See the <a href="#worked-example">worked example of a made-up employee on £{rates["illustration"]["salary"]:,}</a> and the <a href="#worked-example-self-employed">worked example of a made-up self-employed person with £{rates["self_employed"]["profit"]:,} profit</a>. They are illustrations of the tax rules, not measured statistics.</p>')
    items = []
    for q, lab in QUINTS:
        items.append((lab, f"etb.t8.gross.all.{q}", "alt" if q == "all" else ""))
    body.append('<h2 id="by-income">Taxes as a share of gross income, by household income</h2>')
    body.append(bars(items, "pct", num, maxval=50, caption="All taxes as a percentage of gross household income, 2023/24. Each fifth holds the same number of people, ranked by their household's income."))
    body.append(f'''<p>For people in the highest-income fifth most tax is direct: Income Tax alone was {num("etb.t8.gross.income_tax.q5", "pct")} of gross household income. For people in the lowest-income fifth, most is indirect, such as VAT: {num("etb.t8.gross.indirect.q1", "pct")} of gross household income.</p>''')
    # The same tax measured against different totals: the short explanation stays open beside the headline shares.
    body.append('<h3 id="denominators">Why the same tax can look bigger or smaller</h3>'
                f'<p>Indirect taxes are charged on spending. The lowest fifth paid {num("etb.t8.gross.indirect.q1", "pct")} of gross income but {num("etb.t8.spend.indirect.q1", "pct")} of spending, because spending was above income. <strong>Cash and prices:</strong> pay up 50%, prices up 40%, buys about 7% more (1.50 ÷ 1.40 ≈ 1.07), not 10%. Made-up numbers.</p>')
    body.append(FOLD)
    body.append(explain("indirect-spending", sources))
    rows = [[lab, num(f"etb.t8.gross.direct.{q}", "pct"), num(f"etb.t8.gross.indirect.{q}", "pct"), num(f"etb.t8.gross.all.{q}", "pct")] for q, lab in QUINTS]
    body.append(table("Taxes as a percentage of gross household income, 2023/24", ["Fifth of people", "Direct taxes", "Indirect taxes", "All taxes"], rows))
    rows = [[lab, num(f"etb.t8.gross.indirect.{q}", "pct"), num(f"etb.t8.disposable.indirect.{q}", "pct"), num(f"etb.t8.spend.indirect.{q}", "pct")] for q, lab in QUINTS]
    body.append(table("Indirect taxes compared with three different totals, 2023/24", ["Fifth of people", "% of gross income", "% of disposable income", "% of spending"], rows))
    body.append(explain("fiscal-drag", sources))
    body.append(explain("redistribution", sources))
    body.append(source_line(sources, ["etb"], "Table 8, all individuals, grouped by equivalised household disposable income."))
    # three numbers
    body.append(f'''<h2 id="three-numbers">Three numbers that are easy to mix up</h2>
<ol>
<li><p><strong>A household average share.</strong> “Taxes took {num("etb.t8.gross.all.all", "pct")} of gross household income” is an average across all people, using the income and taxes of the household each person lives in. It is not the tax rate any one person pays.</p></li>
<li><p><strong>A personal tax rate.</strong> The basic rate of Income Tax is {esc(rates["basic"])}. It applies only to the part of someone's income inside that band, after the tax-free Personal Allowance of {esc(rates["allowance"])}. So a person's tax bill as a share of their pay is lower than the rate of their top band.</p></li>
<li><p><strong>A share of all tax raised.</strong> “Income Tax raised {num(f"rec.incomesharetaxes.{y}", "pct0")} of all taxes in {y}” is about the government's total income. It says nothing about any household's bill.</p></li>
</ol>''')
    # illustration
    ill = rates["illustration"]
    body.append(f'''<aside class="illustration" aria-labelledby="worked-example">
<span class="tag">Illustration, not a statistic</span>
<h2 id="worked-example">Worked example: one made-up employee on £{ill["salary"]:,} a year</h2>
<p>This person is invented to show how the rules work. They are not a typical or average person, and this is not a measured figure.</p>
<p>Assumptions: tax year {esc(rates["year"])}; lives in England, Wales or Northern Ireland; employee in National Insurance category A; no other income, pension contributions or benefits.</p>
<ul>
<li>Income Tax: {ill["basic_rate"]*100:.0f}% of the £{ill["salary"] - ill["allowance"]:,} above the £{ill["allowance"]:,} Personal Allowance = <strong>£{ill["income_tax"]:,.0f}</strong></li>
<li>Employee National Insurance: {ill["ni_rate"]*100:.0f}% of weekly pay between £{ill["ni_lower"]} and £{ill["ni_upper"]}, for 52 weeks ≈ <strong>£{ill["ni"]:,.0f}</strong></li>
<li>Together: £{ill["total"]:,.0f}, which is {ill["average_rate"]:.0f}% of their pay. This is their <em>average</em> rate.</li>
<li>On each extra pound they earn, they would pay {ill["basic_rate"]*100:.0f}p Income Tax and {ill["ni_rate"]*100:.0f}p National Insurance: a <em>marginal</em> rate of {ill["marginal"]:.0f}%.</li>
</ul>
</aside>''')
    # Self-employed illustration (T138): same Income Tax, Class 4 instead of employee National Insurance.
    se = rates["self_employed"]
    body.append(f'''<aside class="illustration" aria-labelledby="worked-example-self-employed">
<span class="tag">Illustration, not a statistic</span>
<h2 id="worked-example-self-employed">Worked example: one made-up self-employed person with £{se["profit"]:,} profit</h2>
<p>This person is invented to show how the rules work. They are not a typical or average person, and this is not a measured figure.</p>
<p>Assumptions: tax year {esc(rates["year"])}; profit is income from self-employment after allowable expenses; lives in England, Wales or Northern Ireland; no employees, no other income and no pension contributions.</p>
<ul>
<li>Income Tax: {se["basic_rate"]*100:.0f}% of the £{se["profit"] - se["allowance"]:,} above the £{se["allowance"]:,} Personal Allowance = <strong>£{se["income_tax"]:,.0f}</strong></li>
<li>Class 4 National Insurance: {se["class4_rate"]*100:.0f}% of profits between £{se["class4_lower"]} and £{se["class4_upper"]} = <strong>£{se["class4"]:,.0f}</strong>. No Class 2 contributions are due at these profits.</li>
<li>Together: £{se["total"]:,.0f}, which is {se["average_rate"]:.0f}% of their profit. This is their <em>average</em> rate.</li>
<li>On each extra pound of profit, they would pay {se["basic_rate"]*100:.0f}p Income Tax and {se["class4_rate"]*100:.0f}p Class 4 National Insurance: a <em>marginal</em> rate of {se["marginal"]:.0f}%.</li>
<li>The employee on £{ill["salary"]:,} above pays the same Income Tax, £{ill["income_tax"]:,.0f}, and £{ill["ni"]:,.0f} of employee National Insurance. Employer National Insurance is not counted for either person.</li>
</ul>
</aside>''')
    body.append(f'<p class="small">The self-employed example uses rates from GOV.UK: <a href="sources.html#src-gov-self-employed-ni">Self-employed National Insurance rates</a>, retrieved {esc(se["retrieved"])}, and the Income Tax rates above.</p>')
    body.append(FOLD)
    body.append(f'<p class="small">The worked example uses rates from GOV.UK: <a href="sources.html#src-gov-income-tax-rates">Income Tax rates</a> and <a href="sources.html#src-gov-ni-rates">National Insurance rates</a>, retrieved {esc(rates["retrieved"])}. VAT, employer National Insurance and Council Tax depend on circumstances, so they are left out.</p>')
    body.append(explain("average-rates", sources))
    body.append('<div class="limit"><p><strong>Limits.</strong> Survey estimates for April 2023 to March 2024, for people in private households in the UK. People are ranked by their household’s income, adjusted for household size, and split into fifths with equal numbers of people. Taxes paid by companies, such as Corporation Tax, are not allocated to households here.</p></div>')
    body.append(source_line(sources, ["etb", "obr"], "ETB Table 8; OBR receipts for the share of all taxes."))
    from .pages_money_extra import tax_history_section
    body.append(tax_history_section(facts, d, num, sources))
    return page("household-tax.html", "How much of household income goes on tax?", "\n".join(body), "Taxes as a share of UK household income, and how this differs from tax rates and shares of revenue.")
