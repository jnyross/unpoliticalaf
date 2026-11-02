"""Extra sections for the money pages: how the tax mix has changed, and who pays
by type of household (scorecard gap 6).

Kept in their own module so the main page functions only gain one call each.
"""
from .html import bars, change_bars, details_table, line_chart, source_line, table, esc
from .pages_money import derive

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
    for y in years:
        for k, _ in keys:
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
    out.append(f'''<p>Total tax raised has grown a lot in cash terms, so the fairest way to see the mix is each tax's <strong>share of all taxes</strong> in each year.
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
    head = ["Year"] + [esc(n) for _, n in keys]
    rows = [[y] + [num(f"rec.share.{k}.{y}", "pct") for k, _ in keys] for y in years]
    out.append(details_table("Show each tax's share for every year", f"Share of all taxes by tax, {first} to {last}, per cent", head, rows))
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
