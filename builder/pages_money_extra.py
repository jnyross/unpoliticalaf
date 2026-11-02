"""Extra sections for the money pages: how the tax mix has changed, and who pays
by type of household (scorecard gap 6).

Kept in their own module so the main page functions only gain one call each.
"""
from .html import FOLD, bars, change_bars, details_table, line_chart, small_multiples, source_line, table, esc
from .pages_money import derive
from .explain import box as explain

# Taxes shown one by one in the tax-mix section, in the order of the main taxes page.
MIX_LINES = (("income_tax", "Income Tax", "a"), ("nics", "National Insurance", "b"), ("vat", "VAT", "c"))


def _outturn_years(rc):
    return [y for y in rc["years"] if y < rc["forecast_from"]]


def tax_mix_section(facts, d, num, sources):
    """Share of all taxes raised by each main tax, first year to latest outturn year."""
    rc = d["receipts"]
    years = _outturn_years(rc)
    first, last = years[0], years[-1]
    keys = [(k, n) for k, n in rc["groups"]] + [("othertax", "All other taxes")]
    # Every year for the three charted taxes; first and last year for the rest
    # (the per-source figure record page has a size limit).
    lines = {k for k, _, _ in MIX_LINES}
    for y in years:
        for k, _ in keys:
            if k not in lines and y not in (first, last):
                continue
            derive(facts, f"rec.share.{k}.{y}", 100 * facts[f"rec.{k}.{y}"].value / facts[f"rec.taxes.{y}"].value, "% of all taxes", y, "obr",
                   [f"rec.{k}.{y}", f"rec.taxes.{y}"], f"100 × rec.{k}.{y} ÷ rec.taxes.{y}")
    for k, _ in keys:
        derive(facts, f"rec.sharechange.{k}.{first}.{last}",
               facts[f"rec.share.{k}.{last}"].value - facts[f"rec.share.{k}.{first}"].value, "percentage points", f"{first} to {last}", "obr",
               [f"rec.share.{k}.{last}", f"rec.share.{k}.{first}"], f"rec.share.{k}.{last} − rec.share.{k}.{first}")
    big3 = lambda y: sum(facts[f"rec.share.{k}.{y}"].value for k in ("income_tax", "nics", "vat"))
    for y in (first, last):
        derive(facts, f"rec.big3sharemix.{y}", big3(y), "% of all taxes", y, "obr",
               [f"rec.share.income_tax.{y}", f"rec.share.nics.{y}", f"rec.share.vat.{y}"],
               f"rec.share.income_tax.{y} + rec.share.nics.{y} + rec.share.vat.{y}")
    moves = sorted(keys, key=lambda kv: facts[f"rec.sharechange.{kv[0]}.{first}.{last}"].value)
    fell, rose = moves[0], moves[-1]
    out = [f"<h2 id='mix'>How the mix of taxes has changed since {first}</h2>"]
    out.append(f'''<p>Total tax raised has grown a lot in cash terms, so a like-for-like way to see the mix is each tax's <strong>share of all taxes</strong> in each year.
The comparison runs from {first}, the first year in the OBR databank, to {last}, the latest year that has been measured rather than forecast.</p>
<div class="answer"><p class="lede">The three biggest taxes, Income Tax, National Insurance and VAT, raised {num(f"rec.big3sharemix.{first}", "pct0")} of all tax in {first} and {num(f"rec.big3sharemix.{last}", "pct0")} in {last}.</p>
<p>The largest fall was in <strong>{esc(fell[1])}</strong>: {num(f"rec.share.{fell[0]}.{first}", "pct")} of all tax in {first}, {num(f"rec.share.{fell[0]}.{last}", "pct")} in {last}.
The largest rise was in <strong>{esc(rose[1])}</strong>: {num(f"rec.share.{rose[0]}.{first}", "pct")} to {num(f"rec.share.{rose[0]}.{last}", "pct")}.
A smaller share does not have to mean less money: it can also mean other taxes grew faster.</p></div>''')
    out.append(line_chart(f"Share of all taxes, {first} to {last}", years,
                          [(n, [facts[f"rec.share.{k}.{y}"].value for y in years], st) for k, n, st in MIX_LINES],
                          "Per cent of all taxes raised in each year. Source: OBR public finances databank.", ymin=0,
                          desc=f"Income Tax {facts[f'rec.share.income_tax.{first}'].value:.1f}% in {first} and {facts[f'rec.share.income_tax.{last}'].value:.1f}% in {last}; "
                               f"National Insurance {facts[f'rec.share.nics.{first}'].value:.1f}% and {facts[f'rec.share.nics.{last}'].value:.1f}%; "
                               f"VAT {facts[f'rec.share.vat.{first}'].value:.1f}% and {facts[f'rec.share.vat.{last}'].value:.1f}%."))
    items = [(esc(n), f"rec.sharechange.{k}.{first}.{last}",
              f'{num(f"rec.share.{k}.{first}", "pct")} of all tax in {first}, {num(f"rec.share.{k}.{last}", "pct")} in {last}') for k, n in moves[::-1]]
    out.append(change_bars(items, "pts", num, caption=f"Change in each tax's share of all taxes, {first} to {last}, in percentage points. "
                           "A percentage point is the simple difference between two percentages: from 6% to 2% is a fall of 4 points."))
    head = ["Year"] + [esc(n) for _, n, _ in MIX_LINES] + ["Three together"]
    for y in years:
        if y not in (first, last):
            derive(facts, f"rec.big3sharemix.{y}", big3(y), "% of all taxes", y, "obr",
                   [f"rec.share.income_tax.{y}", f"rec.share.nics.{y}", f"rec.share.vat.{y}"],
                   f"rec.share.income_tax.{y} + rec.share.nics.{y} + rec.share.vat.{y}")
    rows = [[y] + [num(f"rec.share.{k}.{y}", "pct") for k, _, _ in MIX_LINES] + [num(f"rec.big3sharemix.{y}", "pct")] for y in years]
    out.append(details_table("Show the chart's figures for every year", f"Share of all taxes, Income Tax, National Insurance and VAT, {first} to {last}, per cent", head, rows))
    out.append(f'<p class="small">Cash amounts for the main taxes in every year are in the “main taxes” table above. Each tax\'s share in {first} and {last} is shown under its bar.</p>')
    out.append(f'''<div class="limit"><p><strong>Limits.</strong> Shares are calculated here from the OBR's cash figures (each tax ÷ all taxes in the same year), so they are not affected by inflation.
They show what the tax system raised, not why it changed: tax rates, prices, wages, house prices and spending patterns all move the shares. The OBR groups some taxes differently from HMRC; “all other taxes” is what is left after the named taxes.
{last} figures can still be revised.</p></div>''')
    out.append(source_line(sources, ["obr"], "Sheet “Receipts (£bn)”. Shares calculated here."))
    return "\n".join(out)


def household_types_section(facts, d, num, sources):
    """ETB Tables 12a-12c (household types) and Table 16 (benefits more than taxes)."""
    w = d["who_types"]
    types = [t for t in w["types"] if t[0] != "all"]
    out = [f'''<h2 id="household-type">4. All taxes, by type of household</h2>
<p>The same Office for National Statistics survey also groups people by the kind of household they live in. Here every figure is <strong>adjusted for household size</strong>
(the ONS calls this “equivalised”), so a large household and a single person can be compared fairly. The adjustment counts the first adult as 1, each other person aged 14 or over as 0.5 and each younger child as 0.3,
then rescales to a household of two adults. The amounts are therefore not the bill any household receives.</p>''']
    lone, couple2, ret1 = "nc1", "nc22", "r1"
    by_share = sorted(types, key=lambda t: facts[f"etb.t12.{t[0]}.taxshare"].value)
    lo, hi = by_share[0], by_share[-1]
    out.append(f'''<div class="answer"><p class="lede">After adjusting for household size, taxes took between {num(f"etb.t12.{lo[0]}.taxshare", "pct0")} ({esc(lo[1].lower())}) and {num(f"etb.t12.{hi[0]}.taxshare", "pct0")} ({esc(hi[1].lower())}) of gross income, depending on the kind of household.</p>
<p>The amounts differ more, because incomes differ. Adjusted for size, people in households of two working-age adults with two children paid about {num(f"etb.t12.{couple2}.alltax", "pounds")} a year in all taxes, people in one-adult households with children about {num(f"etb.t12.{lone}.alltax", "pounds")},
and single retired people about {num(f"etb.t12.{ret1}.alltax", "pounds")}.</p></div>''')
    items = [(esc(label), f"etb.t12.{k}.alltax", "alt" if g == "Retired" else "") for k, label, g in types]
    items.append(("Everyone", "etb.t12.all.alltax", "alt"))
    out.append(bars(items, "pounds", num, caption="All taxes (direct and indirect), £ a year, adjusted for household size, 2023/24. Grey bars: retired households and everyone."))
    rows = []
    for k, label, g in types + [("all", "Everyone", "Everyone")]:
        rows.append([esc(label), esc(g), num(f"etb.t12.{k}.gross", "pounds"), num(f"etb.t12.{k}.direct", "pounds"), num(f"etb.t12.{k}.indirect", "pounds"),
                     num(f"etb.t12.{k}.alltax", "pounds"), num(f"etb.t12.{k}.taxshare", "pct")])
    out.append(table("Income and taxes by type of household, £ a year adjusted for household size, 2023/24",
                     ["Household", "Group", "Gross income", "Direct taxes", "Indirect taxes", "All taxes", "All taxes as % of gross income"], rows))
    out.append('<p class="small">“Working-age” here means a non-retired household, as defined in section 3. Children are under 16, or 16 to 19 if unmarried, living with a parent and in non-advanced further education or unwaged government training. The ONS publishes these groups only for 2023/24 in this table.</p>')
    out.append('<div class="limit"><p><strong>Limits.</strong> Averages for groups of people, adjusted for household size, from a survey of private households; care homes are not covered. Smaller groups rest on fewer survey responses, so their figures are less certain. ONS also publishes figures by tenure and by region, but marks those tables as under review, so they are not shown here.</p></div>')
    out.append(source_line(sources, ["etb"], "Tables 12a (non-retired, no children), 12b (non-retired, with children) and 12c (retired). Percentages calculated here as (direct + indirect taxes) ÷ gross income."))

    # Table 16
    ys = w["t16_years"]
    first, last = ys[0], ys[-1]
    out.append(f'''<h2 id="net">5. Who receives more in benefits than they pay in taxes?</h2>
<p>The ONS also estimates how many people live in households that receive more in benefits than they pay in taxes in a year. Here “benefits” include
cash benefits such as the State Pension and Universal Credit, <strong>and</strong> the estimated value of public services used, such as state schooling and the NHS. “Taxes” are the direct and indirect taxes in sections 2 to 4.</p>
<div class="answer"><p class="lede">In {last}, {num(f"etb.t16.all.{last}", "pct")} of people lived in households that received more in benefits and services than they paid in taxes.</p>
<p>That was {num(f"etb.t16.ret.{last}", "pct")} of people in retired households and {num(f"etb.t16.nonret.{last}", "pct")} in non-retired households.
The share for everyone was {num(f"etb.t16.all.{first}", "pct")} in {first}, the first year of the series.</p></div>''')
    fy = next(i for i, y in enumerate(ys) if "/" in y)
    out.append(line_chart(f"People in households receiving more in benefits than they pay in taxes, {first} to {last}", ys,
                          [("Retired", [facts[f"etb.t16.ret.{y}"].value for y in ys], "b"),
                           ("Non-retired", [facts[f"etb.t16.nonret.{y}"].value for y in ys], "a")],
                          "Per cent of people. Calendar years to 1993, then financial years (April to March) from 1994/95.",
                          breaks=[(fy, "Financial years")], ymin=0, ymax=100,
                          desc=f"Retired: {facts[f'etb.t16.ret.{first}'].value:.1f}% in {first}, {facts[f'etb.t16.ret.{last}'].value:.1f}% in {last}. "
                               f"Non-retired: {facts[f'etb.t16.nonret.{first}'].value:.1f}% in {first}, {facts[f'etb.t16.nonret.{last}'].value:.1f}% in {last}. The figures for everyone are in the table."))
    rows = [[y, num(f"etb.t16.all.{y}", "pct"), num(f"etb.t16.nonret.{y}", "pct"), num(f"etb.t16.ret.{y}", "pct")] for y in ys]
    out.append(details_table("Show every year", f"Share of people in households receiving more in benefits than they pay in taxes, {first} to {last}",
                             ["Year", "Everyone", "Non-retired", "Retired"], rows))
    out.append('''<div class="limit"><p><strong>Limits.</strong> This is one year at a time. It does not follow people through their lives, and the same person can be on either side at different times, for example while at school, working or retired.
Households with children count the value of their state schooling as a benefit. Taxes paid by companies, such as Corporation Tax, and some other taxes are not counted against any household, while not every public service is counted as a benefit, so the two sides do not add up to the government's totals.
From 2001/02 the ONS adjusts for top earners being under-recorded in the survey, which makes earlier and later years less directly comparable.</p></div>''')
    out.append(source_line(sources, ["etb"], "Table 16. Benefits are cash benefits plus benefits in kind; taxes are direct plus indirect taxes (ONS note 16)."))
    return "\n".join(out)


def income_tax_age_section(facts, d, num, sources):
    """HMRC Survey of Personal Incomes Table 3.2: Income Tax payers, income and tax by age (review gap 4)."""
    w = d["who_age"]
    ages = w["ages"]
    yr = w["year"].replace(" to ", "-")[:5] + w["year"][-2:]
    lab = {k: (v if k in ("u20", "75plus") else v.replace("-", " to ")) for k, v in ages}
    q = sources["explain-hmrc-spi-quality"]["page"]
    top = max((k for k, _ in ages), key=lambda k: facts[f"spi.age.meantax.{k}.all"].value)
    out = [f'''<h2 id="age">6. Income Tax, by age</h2>
<p>HM Revenue and Customs also publishes Income Tax by age, from the same survey of tax records as section 1. It covers only people who owe some Income Tax, about {num("spi.age.n.all.all", "millions_people")} people in tax year {yr}.
It says nothing about people who owe none, so it cannot show what share of each age group pays Income Tax.</p>
<div class="answer"><p class="lede">In tax year {yr}, taxpayers aged 30 to 64 were {num("spi.age.sharen.30_64", "pct0")} of all Income Tax payers and owed about {num("spi.age.sharetax.30_64", "pct0")} of all Income Tax.
Taxpayers aged 65 and over were {num("spi.age.sharen.65plus", "pct0")} of taxpayers and owed about {num("spi.age.sharetax.65plus", "pct0")}; those under 30 were {num("spi.age.sharen.u30", "pct0")} and owed about {num("spi.age.sharetax.u30", "pct0")}.</p>
<p>The age groups that owed the most tax per taxpayer also had the highest incomes. The highest average (mean) Income Tax was {num(f"spi.age.meantax.{top}.all", "pounds")} a year for taxpayers aged {lab[top]}, on an average income of {num(f"spi.age.meaninc.{top}.all", "pounds")}.
The middle (median) taxpayer in that group owed much less, {num(f"spi.age.medtax.{top}.all", "pounds")}: a small number of taxpayers with very high incomes and tax bills raise the mean.</p></div>''']
    items = [(esc(lab[k]), f"spi.age.meantax.{k}.all", "alt" if k in ("65_69", "70_74", "75plus") else "") for k, _ in ages]
    out.append(bars(items, "pounds", num, caption=f"Average (mean) Income Tax owed per taxpayer, by age, £ a year, tax year {yr}. Grey bars: ages 65 and over. Taxpayers only."))
    items = [(esc(lab[k]), f"spi.age.sharetax.{k}", "alt" if k in ("65_69", "70_74", "75plus") else "") for k, _ in ages]
    out.append(bars(items, "pct", num, caption=f"Share of all Income Tax owed by each age range, per cent, tax year {yr}. Calculated here from HMRC's rounded figures, so approximate."))
    rows = [[esc(lab[k]), num(f"spi.age.n.{k}.all", "millions_people"), num(f"spi.age.sharen.{k}", "pct"), num(f"spi.age.sharetax.{k}", "pct"),
             num(f"spi.age.medinc.{k}.all", "pounds"), num(f"spi.age.medtax.{k}.all", "pounds"), num(f"spi.age.meaninc.{k}.all", "pounds"),
             num(f"spi.age.meantax.{k}.all", "pounds"), num(f"spi.age.rate.{k}", "pct")] for k, _ in ages]
    rows.append(["All ages", num("spi.age.n.all.all", "millions_people"), "100%", "100%", num("spi.age.medinc.all.all", "pounds"), num("spi.age.medtax.all.all", "pounds"),
                 num("spi.age.meaninc.all.all", "pounds"), num("spi.age.meantax.all.all", "pounds"), ""])
    out.append(details_table("Show the full table: taxpayers, income and tax by age", f"Income Tax payers, income and Income Tax by age, tax year {yr}",
                     ["Age", "Taxpayers", "Share of taxpayers", "Share of all Income Tax", "Median income", "Median tax", "Mean income", "Mean tax", "Tax as % of the group's income"], rows))
    out.append(f'''<p class="small">Income is total income before tax for the year: earnings, self-employment profits, pensions (including the State Pension), property, savings and dividends.
“Median” is the middle taxpayer in each age range. “Mean” is the total divided by the number of taxpayers. Shares and “tax as % of the group's income” are calculated here: number of taxpayers × mean, and mean tax ÷ mean income.
Added up this way, all ages come to {num("spi.age.tottax.sum.all", "bn")} of Income Tax on {num("spi.age.totinc.sum.all", "bn")} of income.</p>''')
    rows = []
    for k, _ in ages:
        rows.append([esc(lab[k]), num(f"spi.age.n.{k}.men", "millions_people"), num(f"spi.age.medtax.{k}.men", "pounds"), num(f"spi.age.meantax.{k}.men", "pounds"),
                     num(f"spi.age.n.{k}.women", "millions_people"), num(f"spi.age.medtax.{k}.women", "pounds"), num(f"spi.age.meantax.{k}.women", "pounds")])
    out.append(details_table("Show men and women separately", f"Income Tax payers and Income Tax by age and sex, tax year {yr}",
                             ["Age", "Men: taxpayers", "Men: median tax", "Men: mean tax", "Women: taxpayers", "Women: median tax", "Women: mean tax"], rows))
    out.append(explain("taxpayers-age", sources))
    out.append(f'''<div class="limit"><p><strong>Limits.</strong> One tax year only: this is a snapshot of different people at different ages, not one person's tax over their life, and it does not say why the groups differ.
Income Tax only: it leaves out National Insurance, which people do not pay on earnings once they reach State Pension age, and taxes on spending such as VAT. People who owe no Income Tax are not counted.
The figures are estimates from a sample of about 1 million tax records. HMRC does not publish margins of error for this table, so small differences between neighbouring age ranges may not be meaningful (see HMRC's <a href="{esc(q)}">background quality report</a>).
HMRC rounds numbers to three significant figures, so shares calculated here can be slightly out. A change in how the survey samples State Pension recipients in {yr} means older age groups are not directly comparable with earlier years.</p></div>''')
    out.append(source_line(sources, ["hmrc-spi-2324-tables"], f"Table 3.2, tax year {yr} (UK taxpayers only). Totals and shares calculated here."))
    return "\n".join(out)


FIFTHS = (("q1", "Lowest-income fifth"), ("q2", "Second fifth"), ("q3", "Middle fifth"), ("q4", "Fourth fifth"), ("q5", "Highest-income fifth"))


def tax_history_section(facts, d, num, sources):
    """Taxes as a share of gross household income, 1977 to the latest year (scorecard gap 4).

    Two ONS methods, never joined: households ranked (1977 to 2017/18) and people ranked
    (2017/18 on, with top incomes adjusted from 2018/19). See builder/data_taxhist.py.
    """
    from .data_taxhist import key
    t = d["tax_history"]
    hh, pp = t["households"], t["people"]
    first, ov, last, adj = hh[0], t["overlap"], pp[-1], t["top_adjusted_from"]
    labels = hh + pp[1:]
    cut = labels.index(adj)

    def fid(m, p, q):
        """Share of gross income: households method up to the overlap year, people method after it."""
        if labels.index(p) < cut:
            return f"etbh.p{m}.{key(p)}.{q}" if m != "all" else f"etbh.pall.{key(p)}.{q}"
        return f"etbp.{m}.{key(p)}.{q}"

    def series_ids(q, m="all"):
        return [fid(m, p, q) for p in labels]

    def vals(ids):
        return [facts[i].value for i in ids]

    pl = [p if "/" in p else f"{p} (calendar year)" for p in labels]
    hall, oall = f"etbh.pall.{key(first)}.all", f"etbh.pall.{key(ov)}.all"
    out = [f'''<h2 id="over-time">How has this changed since {first}?</h2>
<div class="answer"><p class="lede">On the ONS’s older method, taxes took {num(hall, "pct")} of gross household income in {first} and {num(oall, "pct")} in {ov}. On its current method, they took {num(f"etbp.all.{key(adj)}.all", "pct")} in {adj} and {num(f"etbp.all.{key(last)}.all", "pct")} in {last}.</p>
<p>The two methods give different figures for the same year, so they are shown as separate lines and not joined. The older method put households into fifths; the current one puts people into fifths and, from {adj}, adds an estimate of income that very high earners do not report in the survey.
For {ov}, the one year published both ways, the share for everyone was {num(oall, "pct")} on the older method and {num(f"etbp.all.{key(ov)}.all", "pct")} on the current way of ranking, before the top-income adjustment.</p></div>''']
    out.append(line_chart(f"All taxes as a share of gross household income, UK, {first} to {last}", labels,
                          [("Everyone", vals(series_ids("all")), "a")],
                          f"Per cent of gross household income, average across all households to {ov} and across all people from {adj}. Calendar years to 1993, then financial years (April to March).",
                          breaks=[(cut, "Method changed")], split_breaks=True, ymin=0, ymax=50,
                          events=[(labels.index("2020/21"), "Covid")] if "2020/21" in labels else (),
                          kind="pct", ids=[series_ids("all")], num=num, point_labels=pl))
    out.append(FOLD)  # keep the main chart in view on phones
    out.append(f'''<p>On the older method, the share for the lowest-income fifth was below the share for the highest-income fifth in every year from 1977 to 1987, and above it in every year from 1988 to 2017/18. On the current method the two have been within five percentage points of each other, with the order changing from year to year. The make-up differs: for the lowest-income fifth most tax is indirect, such as VAT, and for the highest-income fifth most is direct, such as Income Tax. The panels below show each fifth on the same scale.</p>''')
    out.append(small_multiples(f"All taxes as a share of gross household income, by fifth, UK, {first} to {last}", labels,
                               [(lab, vals(series_ids(q))) for q, lab in FIFTHS],
                               "Per cent of gross household income. Fifths of households to 2017/18; fifths of people from 2018/19.", "pct",
                               ids=[series_ids(q) for q, _ in FIFTHS], num=num, breaks=[(cut, "Method changed")], split_breaks=True,
                               ymin=0, point_labels=pl))
    # every year, both methods, including the overlap year on the people method
    rows = []
    for p in hh:
        rows.append([esc(p), "Households"] + [num(f"etbh.pall.{key(p)}.{q}", "pct") for q, _ in FIFTHS] + [num(f"etbh.pall.{key(p)}.all", "pct")])
    for p in pp:
        how = "People, top incomes adjusted" if labels.index(p) >= cut else "People, no top-income adjustment"
        rows.append([esc(p), how] + [num(f"etbp.all.{key(p)}.{q}", "pct") for q, _ in FIFTHS] + [num(f"etbp.all.{key(p)}.all", "pct")])
    out.append(details_table("Show every year, by fifth", f"All taxes as a percentage of gross household income, {first} to {last}",
                             ["Year", "Method", "Lowest fifth", "Second", "Middle", "Fourth", "Highest fifth", "Everyone"], rows))
    rows = []
    for p in hh:
        rows.append([esc(p), "Households"] + [num(f"etbh.p{m}.{key(p)}.all", "pct") for m in ("direct", "indirect")] + [num(f"etbh.pall.{key(p)}.all", "pct")])
    for p in pp:
        how = "People, top incomes adjusted" if labels.index(p) >= cut else "People, no top-income adjustment"
        rows.append([esc(p), how] + [num(f"etbp.{m}.{key(p)}.all", "pct") for m in ("direct", "indirect", "all")])
    out.append(details_table("Show direct and indirect taxes, every year", f"Direct and indirect taxes as a percentage of gross household income, everyone, {first} to {last}",
                             ["Year", "Method", "Direct taxes", "Indirect taxes", "All taxes"], rows))
    out.append(f'''<div class="limit"><p><strong>Limits.</strong> These are survey estimates for private households in the UK, and a share of income, not anyone’s tax rate.</p>
<ul>
<li><strong>Two methods, not joined.</strong> To {ov}, households were ranked by their income adjusted for household size and split into fifths with equal numbers of households; “everyone” is the average household. From {ov}, people are ranked by their household’s adjusted income and split into fifths with equal numbers of people; “everyone” is the average across people.</li>
<li><strong>Top incomes.</strong> From {adj}, the ONS adjusts for very high earners being missing or under-recorded in the survey (from {adj} tables onwards, applied back to 2001/02 in its own time series). The older tables used here were published before that change and do not include it.</li>
<li><strong>Deferred tax payments.</strong> From {t["lump_sums_from"]}, direct taxes include lump-sum payments of tax put off from earlier years. The ONS warns this can make direct taxes look high for the lowest-income fifths.</li>
<li><strong>Years and taxes change.</strong> Figures are for calendar years to 1993 and financial years (April to March) from 1994/95. Local taxes changed from domestic rates to the community charge to Council Tax, and in some years the older tables count water charges with local taxes.</li>
<li><strong>Not counted.</strong> Taxes paid by companies, such as Corporation Tax, are not allocated to households. Some taxes paid by businesses are counted as indirect taxes passed on in prices.</li>
</ul></div>''')
    out.append(source_line(sources, ["etb-hist-quintile-all", "etb-hist-quintile-all-2", "etb-fye2018", "etb-fye2019", "etb-fye2020", "etb-fye2021", "etb-fye2022", "etb-fye2023", "etb"],
                           f"Older method: historical tables, one sheet per year; shares calculated here as (total direct taxes + total indirect taxes) ÷ gross income. Current method: Table 8 of each year’s reference tables, all individuals."))
    return "\n".join(out)
