"""Pages answering the four public-money questions."""
from .data import Fact
from .explain import box as explain
from .html import page, bars, change_bars, keyfigs, table, details_table, line_chart, source_line, fmt, esc


def derive(facts, fid, value, unit, period, source, inputs, formula, note=""):
    if fid not in facts:
        facts.add(Fact(fid, value, unit, period, source, facts[inputs[0]].locator, "calculated", note=note, formula=formula, inputs=list(inputs)))
    return fid


# ---------------------------------------------------------------- spending

def spending_page(facts, d, num, sources):
    sp = d["spending"]
    y = sp["latest"]
    years = sp["years"]
    first = years[0]
    ten = years[-11]
    funcs = [(k, s["name"]) for k, s in sp["views"]["cash"]["series"].items()
             if k not in ("services", "adjustments", "tme", "debt_interest", "transport", "eu")]
    per = sp["per100"]
    order = sorted(funcs, key=lambda kv: -facts[per[kv[0]]].value)
    top, second = order[0], order[1]
    adj = f"spend.cash.adjustments.{y}"
    body = [f"<h1>Where does public money go?</h1>"]
    body.append(keyfigs([(num(f"spend.cash.tme.{y}", "bn"), f"spent by the UK public sector in {y}", True),
                         (num(per[top[0]], "per100"), "of every £100 spent on services went on social protection, the largest area", False),
                         (num(per["debt_interest"], "per100"), "of every £100 went on interest on government debt", False)]))
    body.append(f'''<div class="answer"><p class="lede">In {y} the UK public sector spent {num(f"spend.cash.tme.{y}", "bn")} in total.</p>
<p>Of every £100 spent on public services, the largest share, {num(per[top[0]], "per100")}, went on <strong>social protection</strong>: mainly State Pension, other benefits and social care.
<strong>Health</strong> was next with {num(per[second[0]], "per100")}. Interest on government debt took {num(per["debt_interest"], "per100")}.</p></div>''')
    body.append(f'''<p>“Public sector” means central government, devolved governments, local councils and public corporations together. The financial year runs from April to March.</p>
<h2 id="per100">Out of every £100 spent on services, {y}</h2>''')
    items = [(esc(name), per[k], "") for k, name in order]
    body.append(bars(items, "per100", num, caption="Rounded to the nearest pound, so the amounts may not add up to exactly £100."))
    body.append(f'''<p class="small">Two items inside these areas are often asked about: interest on government debt ({num(per["debt_interest"], "per100")} of every £100) is part of “general public services”, and transport ({num(per["transport"], "per100")}) is part of “economic affairs”. State pensions alone cost {num(sp["oldage"], "bn")} in {y}, inside social protection.</p>''')
    body.append(explain("debt-interest-2022", sources))
    rows = []
    for k, name in order:
        rows.append([esc(name), num(f"spend.cash.{k}.{y}", "bn1"), num(per[k], "dp1")])
    rows.append(["<strong>Spending on services</strong>", num(f"spend.cash.services.{y}", "bn1"), "100.0"])
    rows.append(["Accounting adjustments (not split by area)", num(adj, "bn1"), "–"])
    rows.append(["<strong>Total managed expenditure</strong>", num(f"spend.cash.tme.{y}", "bn1"), "–"])
    body.append(details_table("Show these figures as a table", f"Public spending by area, {y}, £ billion (cash) and £ per £100 of spending on services",
                              ["Area", "£bn", "£ per £100"], rows))
    body.append(f'''<div class="limit"><p><strong>Limits.</strong> The £100 split uses spending on services ({num(f"spend.cash.services.{y}", "bn")}), not total spending. The difference, {num(adj, "bn")}, is accounting adjustments that HM Treasury does not divide between areas.
Areas follow the international COFOG classification. “Defence” here excludes military pensions, which count as social protection, so it differs from the NATO defence figure.</p></div>''')
    body.append(source_line(sources, ["pesa4", "pesa5"], f"Tables 4.2 and 5.2, outturn for {first} to {y}. Outturn figures can still be revised."))

    # change over time
    body.append(f'<h2 id="change">How has spending changed since {first}?</h2>')
    tme_real = [facts[f"spend.real.tme.{yy}"].value for yy in years]
    tme_gdp = [facts[f"spend.gdp.tme.{yy}"].value for yy in years]
    derive(facts, f"spend.realchange.tme.{first}.{y}", 100 * (tme_real[-1] / tme_real[0] - 1), "%", f"{first} to {y}", "pesa4",
           [f"spend.real.tme.{y}", f"spend.real.tme.{first}"], f"100 × (spend.real.tme.{y} ÷ spend.real.tme.{first} − 1)")
    body.append(f'''<div class="answer"><p>After adjusting for rising prices, total spending in {y} was {num(f"spend.realchange.tme.{first}.{y}", "pct0")} higher than in {first}.
As a share of the whole economy (GDP) it went from {num(f"spend.gdp.tme.{first}", "pct")} to {num(f"spend.gdp.tme.{y}", "pct")}.</p></div>''')
    body.append(line_chart("Total public spending after inflation", years, [("Total managed expenditure, £bn in 2025-26 prices", tme_real, "a")],
                           "£ billion, 2025-26 prices (adjusted with the GDP deflator)", breaks=[(years.index("2020-21"), "Covid")], desc=f"From {fmt(tme_real[0], 'bn')} in {first} to {fmt(tme_real[-1], 'bn')} in {y}."))
    body.append(line_chart("Total public spending as a share of GDP", years, [("Total managed expenditure, % of GDP", tme_gdp, "a")],
                           "Per cent of GDP", desc=f"From {tme_gdp[0]:.1f}% in {first} to {tme_gdp[-1]:.1f}% in {y}."))
    body.append(explain("covid-spending", sources))
    body.append(explain("energy-2022", sources))
    rows = [[yy, num(f"spend.cash.tme.{yy}", "bn1"), num(f"spend.real.tme.{yy}", "bn1"), num(f"spend.gdp.tme.{yy}", "pct")] for yy in years]
    body.append(details_table("Show total spending for every year", "Total managed expenditure, every year",
                              ["Year", "Cash £bn", "£bn, 2025-26 prices", "% of GDP"], rows))
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
    body.append(details_table("Show the amounts and shares of GDP", f"Spending by area, {ten} and {y}", ["Area", f"{ten} £bn*", f"{y} £bn*", "Change", f"{ten} % GDP", f"{y} % GDP"], rows))
    body.append('<p class="small">* £ billion in 2025-26 prices.</p>')
    # full history tables per view
    for view, label, kind in (("real", "£ billion, 2025-26 prices", "bn1"), ("gdp", "% of GDP", "pct"), ("cash", "£ billion, cash (not adjusted for inflation)", "bn1")):
        head = ["Year"] + [esc(n.split(" (")[0]) for _, n in order] + ["Total"]
        rows = [[yy] + [num(f"spend.{view}.{k}.{yy}", kind) for k, _ in order] + [num(f"spend.{view}.tme.{yy}", kind)] for yy in years]
        body.append(details_table(f"Every year by area: {label}", f"Spending by area, {first} to {y}, {label}", head, rows))
    body.append('''<div class="limit"><p><strong>Breaks in the figures.</strong> From 2011-12 the cost of student loans was removed from education, so education before and after that year is not directly comparable.
Network Rail is counted under transport only from 2015-16. Spending in 2020-21 and 2021-22 includes temporary Covid-19 measures. These notes come from HM Treasury's table footnotes.</p></div>''')
    body.append(source_line(sources, ["pesa4"], "Tables 4.2 (cash), 4.3 (real terms, GDP deflator from the ONS released 30 June 2026) and 4.4 (% of GDP)."))
    body.append('<p class="small">Other publications give slightly different totals for the same year because they are published at different times and use different scopes. For example, the OBR databank used on the <a href="taxes.html">taxes page</a> puts 2025-26 spending at £1,366bn.</p>')
    return page("spending.html", "Where does public money go?", "\n".join(body), "UK public spending by area, with history after inflation and as a share of GDP.")


# ---------------------------------------------------------------- taxes

def taxes_page(facts, d, num, sources):
    rc = d["receipts"]
    y = "2025-26"
    groups = rc["groups"]
    big3 = sum(facts[f"rec.{k}.{y}"].value for k in ("income_tax", "nics", "vat"))
    derive(facts, f"rec.big3share.{y}", 100 * big3 / facts[f"rec.taxes.{y}"].value, "% of all taxes", y, "obr",
           [f"rec.income_tax.{y}", f"rec.nics.{y}", f"rec.vat.{y}", f"rec.taxes.{y}"], f"100 × (rec.income_tax + rec.nics + rec.vat) ÷ rec.taxes, {y}")
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
    body.append('<p class="small">“All other taxes” includes business rates, vehicle and air passenger duties, insurance premium tax, environmental levies and others. Income Tax combines PAYE, self assessment and other Income Tax; Corporation Tax includes North Sea profits.</p>')
    body.append(f'''<h3>2. Other receipts (not taxes): {num(f"rec.nontax.{y}", "bn")}</h3>
<p>Interest and dividends the public sector receives, the operating surplus of public bodies, and similar income.</p>
<h3>3. Borrowing: {num(f"agg.psnb.{y}", "bn")}</h3>
<p>Borrowing is not income from tax. It is the gap between spending ({num(f"agg.tme.{y}", "bn")} on this basis) and receipts ({num(f"rec.total.{y}", "bn")}), and it adds to the national debt.</p>''')
    rows = [[esc(n), num(f"rec.{k}.{y}", "bn1")] for k, n in groups] + [["All other taxes", num(f"rec.othertax.{y}", "bn1")],
            ["<strong>All taxes</strong>", num(f"rec.taxes.{y}", "bn1")], ["Other receipts (not taxes)", num(f"rec.nontax.{y}", "bn1")],
            ["<strong>All receipts</strong>", num(f"rec.total.{y}", "bn1")], ["Borrowing (public sector net borrowing)", num(f"agg.psnb.{y}", "bn1")],
            ["<strong>Total spending (OBR basis)</strong>", num(f"agg.tme.{y}", "bn1")]]
    body.append(details_table("Show these figures as a table", f"Public sector receipts and borrowing, {y}, £ billion", ["Item", "£bn"], rows))
    body.append(f'''<h2 id="debt">Borrowing is not the same as debt</h2>
<p><strong>Borrowing</strong> is what the government adds in one year: {num(f"agg.psnb.{y}", "bn")} in {y}. <strong>Debt</strong> is the total still owed from all past years: {num(f"agg.psnd.{y}", "bn")} at the end of March 2026, equal to {num(f"gdp.psnd.{y}", "pct")} of a year's GDP (public sector net debt).</p>''')
    body.append(source_line(sources, ["obr"], f"Sheets “Receipts (£bn)” and “Aggregates (£bn)”. {y} is outturn and can still be revised; years from {rc['forecast_from']} are OBR forecasts."))

    # history as % of GDP
    gy = [g for g in rc["gdp_years"] if facts.get(f"gdp.receipts.{g}") and facts[f"gdp.receipts.{g}"].value is not None]
    fc = next((i for i, g in enumerate(gy) if g >= rc["forecast_from"]), None)
    body.append(f"<h2 id='history'>Receipts and spending since {gy[0]}</h2><p>As a share of GDP, so that years with very different prices and economies can be compared. Forecast years are shaded and dashed.</p>")
    body.append(line_chart("Receipts and spending as a share of GDP", gy,
                           [("Receipts, % of GDP", [facts[f"gdp.receipts.{g}"].value for g in gy], "a"),
                            ("Spending, % of GDP", [facts[f"gdp.tme.{g}"].value for g in gy], "b")],
                           "Per cent of GDP. Source: OBR public finances databank.", forecast_from=fc, ymin=0))
    body.append(explain("borrowing-records", sources))
    rows = [[g + (" (forecast)" if g >= rc["forecast_from"] else ""), num(f"gdp.receipts.{g}", "pct"), num(f"gdp.tme.{g}", "pct"), num(f"gdp.psnb.{g}", "pct"), num(f"gdp.psnd.{g}", "pct")] for g in gy]
    body.append(details_table("Show every year", f"Receipts, spending, borrowing and debt, % of GDP, {gy[0]} to {gy[-1]}", ["Year", "Receipts", "Spending", "Borrowing", "Debt"], rows))
    # taxes by type over time
    ty = rc["years"]
    body.append(f"<h3>Main taxes since {ty[0]}</h3><p>Cash amounts, not adjusted for inflation. Forecast years are labelled.</p>")
    rows = []
    for t in ty:
        rows.append([t + (" (forecast)" if t >= rc["forecast_from"] else "")] + [num(f"rec.{k}.{t}", "bn1") for k in ("income_tax", "nics", "vat", "corp", "council")] + [num(f"rec.taxes.{t}", "bn1")])
    body.append(details_table("Show main taxes for every year", f"Main taxes, £ billion cash, {ty[0]} to {ty[-1]}",
                              ["Year", "Income Tax", "National Insurance", "VAT", "Corporation Tax", "Council Tax", "All taxes"], rows))
    body.append(explain("frozen-thresholds", sources))
    body.append('<div class="limit"><p><strong>Limits.</strong> Forecasts are the OBR\'s October 2026 projections, not measurements. Debt and borrowing use the public sector definitions in the OBR databank; other published debt measures give different totals.</p></div>')
    body.append(source_line(sources, ["obr"], "Sheets “Aggregates (per cent of GDP)” and “Receipts (£bn)”."))
    return page("taxes.html", "Which taxes raise the money?", "\n".join(body), "UK tax receipts by tax, other receipts and borrowing, with history.")


# ---------------------------------------------------------------- who pays

QUINTS = [("q1", "Lowest-income fifth"), ("q2", "Second fifth"), ("q3", "Middle fifth"), ("q4", "Fourth fifth"), ("q5", "Highest-income fifth"), ("all", "Everyone")]


def who_pays_page(facts, d, num, sources):
    w = d["who"]
    y = w["hmrc_latest_outturn"]
    body = ["<h1>Who pays?</h1>"]
    body.append(keyfigs([(num(f"hmrc.share.top1.{y}", "pct"), f"of all Income Tax was paid by the top 1% of Income Tax payers, tax year {y.replace(' to ', '-')}", True),
                         (num("etb.2a.alltax.q5", "pounds"), "a year in all taxes, on average, by the households of the highest-income fifth of people, 2023/24", False),
                         (num("etb.2a.alltax.q1", "pounds"), "a year in all taxes, on average, by the households of the lowest-income fifth of people, 2023/24", False)]))
    body.append(f'''<div class="answer"><p class="lede">Higher-income people pay most Income Tax. In tax year {y.replace(" to ", "-")}, the top 1% of Income Tax payers paid {num(f"hmrc.share.top1.{y}", "pct")} of all Income Tax.</p>
<p>Counting all taxes, including VAT and other taxes on spending, people in the highest-income fifth lived in households that paid about {num("etb.2a.alltax.q5", "pounds")} a year on average, and people in the lowest-income fifth in households that paid about {num("etb.2a.alltax.q1", "pounds")}.</p>
<p>Households of retired people paid less tax on average than households of non-retired people. They also had lower average incomes and fewer people in them (<a href="#retired">see section 3</a>).</p></div>''')
    body.append("<p>Two official sources answer this in different ways. Keep them separate: they count different people and different taxes.</p>")
    # HMRC
    body.append(f'''<h2 id="income-tax">1. Income Tax, by person</h2>
<p>HM Revenue and Customs ranks everyone who owes Income Tax by their income, then adds up how much tax each group owes. People who owe no Income Tax are not included.</p>''')
    items = [("Top 1% of taxpayers", f"hmrc.share.top1.{y}", ""), ("Top 10% of taxpayers", f"hmrc.share.top10.{y}", ""), ("Top 50% of taxpayers", f"hmrc.share.top50.{y}", ""), ("Bottom 50% of taxpayers", f"hmrc.share.bottom50.{y}", "alt")]
    body.append(bars(items, "pct", num, maxval=100, caption=f"Share of all Income Tax owed, tax year {y}. The top groups overlap: the top 1% is part of the top 10%."))
    rows = []
    for key, label, thr in (("top1", "Top 1%", "hmrc.threshold.top1"), ("top10", "Top 10%", "hmrc.threshold.top10"), ("top50", "Top 50%", "hmrc.threshold.top50"), ("bottom50", "Bottom 50%", None)):
        rows.append([label, num(thr, "pounds") if thr else "below " + num("hmrc.threshold.top50", "pounds"), num(f"hmrc.income.{key}.{y}", "pct"), num(f"hmrc.share.{key}.{y}", "pct")])
    body.append(table(f"Income and Income Tax shares, tax year {y}", ["Group of taxpayers", "Income from", "Share of income", "Share of Income Tax"], rows))
    body.append('<p class="small">“Income from” is the income at which each group starts. Income here means income assessable for tax (earnings, pensions, savings and dividends) before allowances.</p>')
    hy = w["hmrc_years"]
    vals = [facts[f"hmrc.share.top1.{h}"].value for h in hy]
    fc = next((i for i, h in enumerate(hy) if int(h[:4]) >= 2024), None)
    body.append(line_chart("Share of Income Tax paid by the top 1% of taxpayers", [h[:4] + "-" + h[-2:] for h in hy],
                           [("Top 1% share of Income Tax", vals, "a"), ("Top 1% share of income", [facts[f"hmrc.income.top1.{h}"].value for h in hy], "b")],
                           "Per cent. Gap at 2008-09: HMRC has no figures for that year. Years from 2024-25 are HMRC projections.",
                           breaks=[(hy.index("2016 to 2017"), "Dividend rules changed")], forecast_from=fc, ymin=0))
    body.append(explain("top1-share", sources))
    rows = [[h + (" (projection)" if int(h[:4]) >= 2024 else ""), num(f"hmrc.share.top1.{h}", "pct"), num(f"hmrc.share.top10.{h}", "pct"), num(f"hmrc.share.bottom50.{h}", "pct")] for h in hy]
    body.append(details_table("Show every year", "Share of all Income Tax by group of taxpayers", ["Tax year", "Top 1%", "Top 10%", "Bottom 50%"], rows))
    body.append(f'''<div class="limit"><p><strong>Limits.</strong> This covers Income Tax only, which raised about {num("rec.income_tax.2025-26", "bn")} of the {num("rec.taxes.2025-26", "bn")} of all taxes in 2025-26. It leaves out people who owe no Income Tax. Rules for dividends changed in 2016-17, so years before and after are not directly comparable. There are no figures for 2008-09.</p></div>''')
    body.append(source_line(sources, ["hmrc24"], "Survey of Personal Incomes. 2023-24 is outturn; later years are projections."))
    # ETB
    body.append(f'''<h2 id="households">2. All taxes, by household income</h2>
<p>The Office for National Statistics ranks everyone in UK private households by their household's income, adjusted for household size, and splits them into five groups with the same number of people in each (“fifths”). For each fifth, it then estimates the average income and taxes of the households those people live in. Each fifth has the same number of people, but not the same number of households. This includes taxes on spending, such as VAT and fuel duty, but not taxes such as Corporation Tax that are not paid directly by households.</p>''')
    rows = []
    for q, label in QUINTS:
        rows.append([label, num(f"etb.2a.gross.{q}", "pounds"), num(f"etb.2a.direct.{q}", "pounds"), num(f"etb.2a.indirect.{q}", "pounds"), num(f"etb.2a.alltax.{q}", "pounds")])
    body.append(bars([(lab, f"etb.2a.alltax.{q}", "alt" if q == "all" else "") for q, lab in QUINTS], "pounds", num,
                     caption="Average taxes paid by the households that people in each fifth live in, £ a year, financial year ending 2024 (April 2023 to March 2024)."))
    body.append(table("Average household income and taxes, by fifth of people, £ a year, 2023/24", ["Fifth of people", "Gross income", "Direct taxes", "Indirect taxes", "All taxes"], rows))
    body.append('<p class="small">Direct taxes: Income Tax, employee National Insurance and Council Tax (after reductions). Indirect taxes: VAT, duties and taxes paid by businesses that are passed on in prices. Gross income includes cash benefits such as the State Pension.</p>')
    body.append('<p>For how big these taxes are compared with each group\'s income, see <a href="household-tax.html">how much of household income goes on tax</a>.</p>')
    body.append('<div class="limit"><p><strong>Limits.</strong> These are averages for groups of people, using the income and taxes of the household each person lives in, estimated from a survey; no single household is “typical”. Indirect taxes are modelled from what households report spending.</p></div>')
    body.append(source_line(sources, ["etb"], "Table 2a. Survey-based estimates for April 2023 to March 2024."))
    # ETB retired / non-retired
    body.append(f'''<h2 id="retired">3. All taxes, retired and non-retired people</h2>
<p>The same Office for National Statistics survey also splits people into two groups. People count as “retired” if they live in a household where more than half of the income comes from people who say they are retired and are over 50, or who are not working because of sickness or injury and are over State Pension age. Everyone else counts as “non-retired”. In 2023/24, {num("etb.ret.people.all", "millions_people")} people lived in retired households and {num("etb.nonret.people.all", "millions_people")} in non-retired households.</p>
<p>Non-retired households paid about {num("etb.nonret.alltax.all", "pounds")} a year in all taxes on average, and retired households about {num("etb.ret.alltax.all", "pounds")}. Retired households are smaller ({num("etb.ret.hhsize.all", "dp1")} people on average, against {num("etb.nonret.hhsize.all", "dp1")}) and have lower incomes. Compared with each group's income, the difference is much smaller: taxes took {num("etb.nonret.taxshare.all", "pct")} of gross household income for non-retired people and {num("etb.ret.taxshare.all", "pct")} for retired people.</p>''')
    groups = [("nonret", "Non-retired people"), ("ret", "Retired people")]
    body.append(bars([(lab, f"etb.{g}.alltax.all", "") for g, lab in groups], "pounds", num,
                     caption="Average taxes paid by the households that retired and non-retired people live in, £ a year, 2023/24."))
    rows = [[lab, num(f"etb.{g}.people.all", "millions_people"), num(f"etb.{g}.hhsize.all", "dp1"), num(f"etb.{g}.gross.all", "pounds"),
             num(f"etb.{g}.direct.all", "pounds"), num(f"etb.{g}.indirect.all", "pounds"), num(f"etb.{g}.alltax.all", "pounds"), num(f"etb.{g}.taxshare.all", "pct")]
            for g, lab in groups]
    body.append(table("Average household income and taxes, retired and non-retired people, 2023/24",
                      ["Group", "People", "People per household", "Gross income, £ a year", "Direct taxes, £ a year", "Indirect taxes, £ a year", "All taxes, £ a year", "All taxes as % of gross income"], rows))
    fifths = [("q1", "Lowest-income fifth"), ("q2", "Second fifth"), ("q3", "Middle fifth"), ("q4", "Fourth fifth"), ("q5", "Highest-income fifth")]
    rows = [[lab, num(f"etb.nonret.alltax.{q}", "pounds"), num(f"etb.nonret.taxshare.{q}", "pct"), num(f"etb.ret.alltax.{q}", "pounds"), num(f"etb.ret.taxshare.{q}", "pct")]
            for q, lab in fifths]
    body.append(details_table("Show by income fifth within each group", "All taxes by income fifth within each group, 2023/24. Each group is split into its own fifths, so these are not the same fifths as in section 2.",
                              ["Fifth within the group", "Non-retired: £ a year", "Non-retired: % of gross income", "Retired: £ a year", "Retired: % of gross income"], rows))
    body.append(explain("retired-net", sources))
    body.append('<div class="limit"><p><strong>Limits.</strong> These are averages per household, and retired and non-retired households differ in size, so the figures are not tax per person. Gross income includes cash benefits such as the State Pension. “Retired” describes the household, not each person in it. In the lowest-income fifths, a few people with large tax bills from earlier years can raise the average tax, which the Office for National Statistics warns about. Survey estimates for April 2023 to March 2024, for people in UK private households; care homes are not covered.</p></div>')
    body.append(source_line(sources, ["etb"], "Tables 3a (non-retired) and 4a (retired). Percentages calculated here as (direct + indirect taxes) ÷ gross income, the same method as ONS Table 8."))
    return page("who-pays.html", "Who pays?", "\n".join(body), "Who pays UK taxes: Income Tax shares by taxpayer group and all taxes by household income group.")


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
<p>That was {num("etb.t8.gross.direct.all", "pct")} in direct taxes, such as Income Tax, and {num("etb.t8.gross.indirect.all", "pct")} in indirect taxes, such as VAT. The share was similar for the lowest-income fifth of people ({num("etb.t8.gross.all.q1", "pct")}) and the highest-income fifth ({num("etb.t8.gross.all.q5", "pct")}), but for different reasons. The fifths each hold the same number of people, ranked by their household's income.</p></div>''')
    items = []
    for q, lab in QUINTS:
        items.append((lab, f"etb.t8.gross.all.{q}", "alt" if q == "all" else ""))
    body.append('<h2 id="by-income">Taxes as a share of gross income, by household income</h2>')
    body.append(bars(items, "pct", num, maxval=50, caption="All taxes as a percentage of gross household income, 2023/24."))
    rows = [[lab, num(f"etb.t8.gross.direct.{q}", "pct"), num(f"etb.t8.gross.indirect.{q}", "pct"), num(f"etb.t8.gross.all.{q}", "pct")] for q, lab in QUINTS]
    body.append(table("Taxes as a percentage of gross household income, 2023/24", ["Fifth of people", "Direct taxes", "Indirect taxes", "All taxes"], rows))
    body.append(f'''<p>For people in the highest-income fifth, most of their household's tax is direct: Income Tax alone was {num("etb.t8.gross.income_tax.q5", "pct")} of gross household income. For people in the lowest-income fifth, most is indirect ({num("etb.t8.gross.indirect.q1", "pct")} of gross household income), because their households spend a larger part of their income, and some spend savings or borrowed money as well.</p>''')
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
    body.append(explain("average-rates", sources))
    # illustration
    ill = rates["illustration"]
    body.append(f'''<aside class="illustration" aria-labelledby="ill-title">
<span class="tag">Illustration, not a statistic</span>
<h3 id="ill-title">Worked example: one made-up employee on £{ill["salary"]:,} a year</h3>
<p>This person is invented to show how the rules work. They are not a typical or average person, and this is not a measured figure.</p>
<p>Assumptions: tax year {esc(rates["year"])}; lives in England, Wales or Northern Ireland; employee in National Insurance category A; no other income, pension contributions or benefits.</p>
<ul>
<li>Income Tax: {ill["basic_rate"]*100:.0f}% of the £{ill["salary"] - ill["allowance"]:,} above the £{ill["allowance"]:,} Personal Allowance = <strong>£{ill["income_tax"]:,.0f}</strong></li>
<li>Employee National Insurance: {ill["ni_rate"]*100:.0f}% of weekly pay between £{ill["ni_lower"]} and £{ill["ni_upper"]}, for 52 weeks ≈ <strong>£{ill["ni"]:,.0f}</strong></li>
<li>Together: £{ill["total"]:,.0f}, which is {ill["average_rate"]:.0f}% of their pay. This is their <em>average</em> rate.</li>
<li>On each extra pound they earn, they would pay {ill["basic_rate"]*100:.0f}p Income Tax and {ill["ni_rate"]*100:.0f}p National Insurance: a <em>marginal</em> rate of {ill["marginal"]:.0f}%.</li>
</ul>
<p class="small">This leaves out VAT and other taxes on spending, employer National Insurance and Council Tax, which depend on circumstances. Rates from GOV.UK: <a href="methods.html#src-gov-income-tax-rates">Income Tax rates</a> and <a href="methods.html#src-gov-ni-rates">National Insurance rates</a>, retrieved {esc(rates["retrieved"])}.</p>
</aside>''')
    # denominators
    body.append('<h2 id="denominators">Why the same tax can look bigger or smaller</h2><p>The percentage depends on what you divide by. Indirect taxes look much heavier for the lowest-income fifth when compared with their income than when compared with their spending.</p>')
    rows = [[lab, num(f"etb.t8.gross.indirect.{q}", "pct"), num(f"etb.t8.disposable.indirect.{q}", "pct"), num(f"etb.t8.spend.indirect.{q}", "pct")] for q, lab in QUINTS]
    body.append(table("Indirect taxes compared with three different totals, 2023/24", ["Fifth of people", "% of gross income", "% of disposable income", "% of spending"], rows))
    body.append('<div class="limit"><p><strong>Limits.</strong> Survey estimates for April 2023 to March 2024, for people in private households in the UK. People are ranked by their household’s income, adjusted for household size, and split into fifths with equal numbers of people. Taxes paid by companies, such as Corporation Tax, are not allocated to households here.</p></div>')
    body.append(source_line(sources, ["etb", "obr"], "ETB Table 8; OBR receipts for the share of all taxes."))
    return page("household-tax.html", "How much of household income goes on tax?", "\n".join(body), "Taxes as a share of UK household income, and how this differs from tax rates and shares of revenue.")
