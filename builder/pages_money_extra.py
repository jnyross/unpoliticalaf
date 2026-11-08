"""Extra sections for the money pages: how the tax mix has changed, and who pays
by type of household (scorecard gap 6).

Kept in their own module so the main page functions only gain one call each.
"""

from .html import (
    FOLD,
    NOFOLD,
    bars,
    change_bars,
    details_table,
    line_chart,
    small_multiples,
    source_line,
    table,
    esc,
)
from .pages_money import derive
from . import findings as F
from .explain import box as explain


def _plain_years(rule):
    """A title rule that names years without the "(calendar year)" note the readout uses."""
    return F.describes(
        lambda labels, series, stretches: rule(
            [lab.replace(" (calendar year)", "") for lab in labels], series, stretches
        ),
        lambda st: F.lines_of(rule, st),
    )


# Taxes shown one by one in the tax-mix section, in the order of the main taxes page.
MIX_LINES = (
    ("income_tax", "Income Tax", "a"),
    ("nics", "National Insurance", "b"),
    ("vat", "VAT", "c"),
)


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
            derive(
                facts,
                f"rec.share.{k}.{y}",
                100 * facts[f"rec.{k}.{y}"].value / facts[f"rec.taxes.{y}"].value,
                "% of all taxes",
                y,
                "obr",
                [f"rec.{k}.{y}", f"rec.taxes.{y}"],
                f"100 × rec.{k}.{y} ÷ rec.taxes.{y}",
            )
    for k, _ in keys:
        derive(
            facts,
            f"rec.sharechange.{k}.{first}.{last}",
            facts[f"rec.share.{k}.{last}"].value - facts[f"rec.share.{k}.{first}"].value,
            "percentage points",
            f"{first} to {last}",
            "obr",
            [f"rec.share.{k}.{last}", f"rec.share.{k}.{first}"],
            f"rec.share.{k}.{last} − rec.share.{k}.{first}",
        )
    big3 = lambda y: sum(facts[f"rec.share.{k}.{y}"].value for k in ("income_tax", "nics", "vat"))
    for y in (first, last):
        derive(
            facts,
            f"rec.big3sharemix.{y}",
            big3(y),
            "% of all taxes",
            y,
            "obr",
            [f"rec.share.income_tax.{y}", f"rec.share.nics.{y}", f"rec.share.vat.{y}"],
            f"rec.share.income_tax.{y} + rec.share.nics.{y} + rec.share.vat.{y}",
        )
    moves = sorted(keys, key=lambda kv: facts[f"rec.sharechange.{kv[0]}.{first}.{last}"].value)
    fell, rose = moves[0], moves[-1]
    out = [f"<h2 id='mix'>How the mix of taxes has changed since {first}</h2>"]
    out.append(
        f"""<p>Each tax's <strong>share of all taxes</strong>, a like-for-like measure when cash totals grow, from {first} (the first year in the OBR databank) to {last}, the latest measured year.
For the mix since 1948-49, see <a href="tax-history.html">which taxes raised the money since 1948</a>.</p>
<div class="answer"><p class="lede">The three biggest taxes, Income Tax, National Insurance and VAT, raised {num(f"rec.big3sharemix.{first}", "pct0")} of all tax in {first} and {num(f"rec.big3sharemix.{last}", "pct0")} in {last}.</p>
<p>The largest fall was in <strong>{esc(fell[1])}</strong>: {num(f"rec.share.{fell[0]}.{first}", "pct")} of all tax in {first}, {num(f"rec.share.{fell[0]}.{last}", "pct")} in {last}.
The largest rise was in <strong>{esc(rose[1])}</strong>: {num(f"rec.share.{rose[0]}.{first}", "pct")} to {num(f"rec.share.{rose[0]}.{last}", "pct")}.
A smaller share does not have to mean less money: it can also mean other taxes grew faster.</p></div>"""
    )
    out.append(
        line_chart(
            f"Share of all taxes, {first} to {last}",
            years,
            [(n, [facts[f"rec.share.{k}.{y}"].value for y in years], st) for k, n, st in MIX_LINES],
            "Per cent of all taxes raised in each year. Source: OBR public finances databank.",
            ymin=0,
            kind="pct",
            num=num,
            ids=[[f"rec.share.{k}.{y}" for y in years] for k, _, _ in MIX_LINES],
            finding=F.leader("{name} raised a larger share of all tax than the other two {span}"),
            desc=f"Income Tax {facts[f'rec.share.income_tax.{first}'].value:.1f}% in {first} and {facts[f'rec.share.income_tax.{last}'].value:.1f}% in {last}; "
            f"National Insurance {facts[f'rec.share.nics.{first}'].value:.1f}% and {facts[f'rec.share.nics.{last}'].value:.1f}%; "
            f"VAT {facts[f'rec.share.vat.{first}'].value:.1f}% and {facts[f'rec.share.vat.{last}'].value:.1f}%.",
        )
    )
    # The answer gives the shares; on a phone the chart waits in the fold, and
    # tax-history.html has the mix back to 1948-49 as a chart.
    out.append("<!--keepfold-->")
    items = [
        (
            esc(n),
            f"rec.sharechange.{k}.{first}.{last}",
            f'{num(f"rec.share.{k}.{first}", "pct")} of all tax in {first}, {num(f"rec.share.{k}.{last}", "pct")} in {last}',
        )
        for k, n in moves[::-1]
    ]
    out.append(
        change_bars(
            items,
            "pts",
            num,
            caption=f"Change in each tax's share of all taxes, {first} to {last}, in percentage points. "
            "A percentage point is the simple difference between two percentages: from 6% to 2% is a fall of 4 points.",
        )
    )
    head = ["Year"] + [esc(n) for _, n, _ in MIX_LINES] + ["Three together"]
    for y in years:
        if y not in (first, last):
            derive(
                facts,
                f"rec.big3sharemix.{y}",
                big3(y),
                "% of all taxes",
                y,
                "obr",
                [f"rec.share.income_tax.{y}", f"rec.share.nics.{y}", f"rec.share.vat.{y}"],
                f"rec.share.income_tax.{y} + rec.share.nics.{y} + rec.share.vat.{y}",
            )
    rows = [
        [y]
        + [num(f"rec.share.{k}.{y}", "pct") for k, _, _ in MIX_LINES]
        + [num(f"rec.big3sharemix.{y}", "pct")]
        for y in years
    ]
    out.append(
        details_table(
            "Show the chart's figures for every year",
            f"Share of all taxes, Income Tax, National Insurance and VAT, {first} to {last}, per cent",
            head,
            rows,
        )
    )
    out.append(
        f'<p class="small">Cash amounts for the main taxes in every year are in the “main taxes” table above. Each tax\'s share in {first} and {last} is shown under its bar.</p>'
    )
    out.append(
        f"""<div class="limit"><p><strong>Limits.</strong> Shares are calculated here from the OBR's cash figures (each tax ÷ all taxes in the same year), so they are not affected by inflation.
They show what the tax system raised, not why it changed: tax rates, prices, wages, house prices and spending patterns all move the shares. The OBR groups some taxes differently from HMRC; “all other taxes” is what is left after the named taxes.
{last} figures can still be revised.</p></div>"""
    )
    out.append(source_line(sources, ["obr"], "Sheet “Receipts (£bn)”. Shares calculated here."))
    return "\n".join(out)


HOUSEHOLDS_PAGE = "who-pays-households.html"


def retired_section(facts, d, num, sources):
    """ETB Tables 3a and 4a: all taxes for retired and non-retired people."""
    out = []
    retired_def = f"""<p>Who counts as retired: people who live in a household where more than half of the income comes from people who say they are retired and are over 50, or who are not working because of sickness or injury and are over State Pension age. Everyone else counts as “non-retired”. In 2023/24, {num("etb.ret.people.all", "millions_people")} people lived in retired households and {num("etb.nonret.people.all", "millions_people")} in non-retired households.</p>"""
    out.append(
        f"""<h2 id="retired">Retired and non-retired people</h2>
<p>From the same survey: retired households (where more than half the income comes from retired people) paid less tax on average, in cash, than non-retired households. They also had less income: average gross income was {num("etb.ret.gross.all", "pounds")} a year, against {num("etb.nonret.gross.all", "pounds")}, and {num("etb.ret.hhsize.all", "dp1")} people per household, against {num("etb.nonret.hhsize.all", "dp1")}. Gross income includes cash benefits such as the State Pension. Measured against each group's own gross income, taxes took {num("etb.ret.taxshare.all", "pct")} for retired households and {num("etb.nonret.taxshare.all", "pct")} for non-retired households. Both measures matter: the cash gap reflects income and household size, and the share shows the tax paid relative to income.</p>"""
    )
    groups = [("nonret", "Non-retired households"), ("ret", "Retired households")]
    out.append(
        bars(
            [(lab, f"etb.{g}.alltax.all", "") for g, lab in groups],
            "pounds",
            num,
            caption="Average taxes paid by retired and non-retired households, £ a year, 2023/24. Retired people who live in a non-retired household are counted as non-retired.",
        )
    )
    out.append(FOLD)
    out.append(retired_def)
    out.append(
        f'<p>Averaged over people, non-retired households paid about {num("etb.nonret.alltax.all", "pounds")} a year in all taxes, and retired households about {num("etb.ret.alltax.all", "pounds")}. '
        f'Retired households had {num("etb.ret.hhsize.all", "dp1")} people on average, against {num("etb.nonret.hhsize.all", "dp1")}.</p>'
    )
    rows = [
        [
            lab,
            num(f"etb.{g}.people.all", "millions_people"),
            num(f"etb.{g}.hhsize.all", "dp1"),
            num(f"etb.{g}.gross.all", "pounds"),
            num(f"etb.{g}.direct.all", "pounds"),
            num(f"etb.{g}.indirect.all", "pounds"),
            num(f"etb.{g}.alltax.all", "pounds"),
            num(f"etb.{g}.taxshare.all", "pct"),
        ]
        for g, lab in groups
    ]
    out.append(
        table(
            "Average household income and taxes, retired and non-retired households, 2023/24",
            [
                "Group",
                "People",
                "People per household",
                "Gross income, £ a year",
                "Direct taxes, £ a year",
                "Indirect taxes, £ a year",
                "All taxes, £ a year",
                "All taxes as % of gross income",
            ],
            rows,
        )
    )
    fifths = [
        ("q1", "Lowest-income fifth"),
        ("q2", "Second fifth"),
        ("q3", "Middle fifth"),
        ("q4", "Fourth fifth"),
        ("q5", "Highest-income fifth"),
    ]
    rows = [
        [
            lab,
            num(f"etb.nonret.alltax.{q}", "pounds"),
            num(f"etb.nonret.taxshare.{q}", "pct"),
            num(f"etb.ret.alltax.{q}", "pounds"),
            num(f"etb.ret.taxshare.{q}", "pct"),
        ]
        for q, lab in fifths
    ]
    out.append(
        details_table(
            "Show by income fifth within each group",
            "All taxes by income fifth within each group, 2023/24. Each group is split into its own fifths, so these are not the same fifths as in section 2 of who pays.",
            [
                "Fifth within the group",
                "Non-retired: £ a year",
                "Non-retired: % of gross income",
                "Retired: £ a year",
                "Retired: % of gross income",
            ],
            rows,
        )
    )
    out.append(explain("retired-net", sources))
    out.append(
        '<div class="limit"><p><strong>Limits.</strong> These are averages over people of the taxes paid by the households they live in (each person counts once, so larger households count more), and retired and non-retired households differ in size, so the figures are not tax per person. Gross income includes cash benefits such as the State Pension. “Retired” describes the household, not each person in it. In the lowest-income fifths, a few people with large tax bills from earlier years can raise the average tax, which the Office for National Statistics warns about. Survey estimates for April 2023 to March 2024, for people in UK private households; care homes are not covered.</p></div>'
    )
    out.append(
        source_line(
            sources,
            ["etb"],
            "Tables 3a (non-retired) and 4a (retired). Percentages calculated here as (direct + indirect taxes) ÷ gross income, the same method as ONS Table 8.",
        )
    )
    return "\n".join(out)


def household_types_section(facts, d, num, sources):
    """ETB Tables 12a-12c: all taxes by type of household."""
    w = d["who_types"]
    types = [t for t in w["types"] if t[0] != "all"]
    out = [
        """<h2 id="household-type">By type of household</h2>
<p>The same survey also groups people by the kind of household they live in. Every figure here is <strong>adjusted for household size</strong>, so the amounts are not the bill any household receives.</p>"""
    ]
    lone, couple2, ret1 = "nc1", "nc22", "r1"
    by_share = sorted(types, key=lambda t: facts[f"etb.t12.{t[0]}.taxshare"].value)
    lo, hi = by_share[0], by_share[-1]
    out.append(
        f"""<div class="answer"><p class="lede">After adjusting for household size, taxes took between {num(f"etb.t12.{lo[0]}.taxshare", "pct0")} ({esc(lo[1].lower())}) and {num(f"etb.t12.{hi[0]}.taxshare", "pct0")} ({esc(hi[1].lower())}) of gross income, depending on the kind of household (the {len(types)} kinds shown here). The ONS also splits one-adult households by sex, and some of those narrower groups fall a little outside this range.</p>
<p>The amounts differ more, because incomes differ (see the bars below).</p></div>"""
    )
    amounts = (
        f'<p>Adjusted for size, people in households of two working-age adults with two children paid about {num(f"etb.t12.{couple2}.alltax", "pounds")} a year in all taxes, people in one-adult households with children about {num(f"etb.t12.{lone}.alltax", "pounds")}, '
        f'and single retired people about {num(f"etb.t12.{ret1}.alltax", "pounds")}.</p>'
    )
    items = [
        (esc(label), f"etb.t12.{k}.alltax", "alt" if g == "Retired" else "")
        for k, label, g in types
    ]
    items.append(("Everyone", "etb.t12.all.alltax", "alt"))
    out.append(
        bars(
            items,
            "pounds",
            num,
            caption="All taxes (direct and indirect), £ a year, adjusted for household size, 2023/24. Grey bars: retired households and everyone.",
        )
    )
    out.append(FOLD)
    out.append(amounts)
    out.append(
        "<p>How the size adjustment works: the ONS calls it “equivalised”, so that a large household and a single person can be compared fairly. "
        "It counts the first adult as 1, each other person aged 14 or over as 0.5 and each younger child as 0.3, then rescales to a household of two adults.</p>"
    )
    rows = []
    for k, label, g in types + [("all", "Everyone", "Everyone")]:
        rows.append(
            [
                esc(label),
                esc(g),
                num(f"etb.t12.{k}.gross", "pounds"),
                num(f"etb.t12.{k}.direct", "pounds"),
                num(f"etb.t12.{k}.indirect", "pounds"),
                num(f"etb.t12.{k}.alltax", "pounds"),
                num(f"etb.t12.{k}.taxshare", "pct"),
            ]
        )
    out.append(
        table(
            "Income and taxes by type of household, £ a year adjusted for household size, 2023/24",
            [
                "Household",
                "Group",
                "Gross income",
                "Direct taxes",
                "Indirect taxes",
                "All taxes",
                "All taxes as % of gross income",
            ],
            rows,
        )
    )
    out.append(
        '<p class="small">“Working-age” here means a non-retired household, as defined above. Children are under 16, or 16 to 19 if unmarried, living with a parent and in non-advanced further education or unwaged government training. The ONS publishes these groups only for 2023/24 in this table.</p>'
    )
    out.append(
        '<div class="limit"><p><strong>Limits.</strong> Averages for groups of people, adjusted for household size, from a survey of private households; care homes are not covered. Smaller groups rest on fewer survey responses, so their figures are less certain. ONS also publishes figures by tenure and by region, but marks those tables as under review, so they are not shown here.</p></div>'
    )
    out.append(
        source_line(
            sources,
            ["etb"],
            "Tables 12a (non-retired, no children), 12b (non-retired, with children) and 12c (retired). Percentages calculated here as (direct + indirect taxes) ÷ gross income.",
        )
    )

    return "\n".join(out)


def net_section(facts, d, num, sources):
    """ETB Table 16: people in households receiving more in benefits than they pay in taxes."""
    w = d["who_types"]
    out = []
    ys = w["t16_years"]
    first, last = ys[0], ys[-1]
    out.append(
        f"""<h2 id="net">4. Who receives more in benefits than they pay in taxes?</h2>
<p>Here “benefits” include cash benefits such as the State Pension, <strong>and</strong> the estimated value of public services used, such as state schools and the NHS.</p>
<div class="answer"><p class="lede">In {last}, {num(f"etb.t16.all.{last}", "pct")} of people lived in households that received more in benefits and services than they paid in taxes.</p>
<p>That was {num(f"etb.t16.ret.{last}", "pct")} of people in retired households and {num(f"etb.t16.nonret.{last}", "pct")} in non-retired households. One year at a time.</p></div>"""
    )
    fy = next(i for i, y in enumerate(ys) if "/" in y)
    out.append(
        line_chart(
            f"People in households receiving more in benefits than they pay in taxes, {first} to {last}",
            ys,
            [
                ("Retired", [facts[f"etb.t16.ret.{y}"].value for y in ys], "b"),
                ("Non-retired", [facts[f"etb.t16.nonret.{y}"].value for y in ys], "a"),
            ],
            "Per cent of people. Calendar years to 1993, then financial years (April to March) from 1994/95. Second dashed line: top incomes adjusted from 2001/02.",
            breaks=[(fy, "Financial years")]
            + (
                [(ys.index("2001/02"), "Top incomes adjusted from here")] if "2001/02" in ys else []
            ),
            ymin=0,
            ymax=100,
            finding=F.gap(
                "The share for people in retired households", "for people in non-retired households"
            ),
            desc=f"Retired: {facts[f'etb.t16.ret.{first}'].value:.1f}% in {first}, {facts[f'etb.t16.ret.{last}'].value:.1f}% in {last}. "
            f"Non-retired: {facts[f'etb.t16.nonret.{first}'].value:.1f}% in {first}, {facts[f'etb.t16.nonret.{last}'].value:.1f}% in {last}. The figures for everyone are in the table. Years before 2001/02 are less directly comparable with later years.",
        )
    )
    out.append(FOLD)
    out.append(
        f'<p>The share for everyone was {num(f"etb.t16.all.{first}", "pct")} in {first}, the first year of the series, before the 2001/02 change (see Limits).</p>'
    )
    out.append(
        "<p>What is counted: the ONS estimates, one year at a time, how many people live in households that receive more in benefits than they pay in taxes. "
        "Benefits are cash benefits such as the State Pension and Universal Credit plus the estimated value of public services used. "
        "“Taxes” are the direct and indirect taxes in sections 2 and 3.</p>"
    )
    rows = [
        [
            y,
            num(f"etb.t16.all.{y}", "pct"),
            num(f"etb.t16.nonret.{y}", "pct"),
            num(f"etb.t16.ret.{y}", "pct"),
        ]
        for y in ys
    ]
    out.append(
        details_table(
            "Show every year",
            f"Share of people in households receiving more in benefits than they pay in taxes, {first} to {last}",
            ["Year", "Everyone", "Non-retired", "Retired"],
            rows,
        )
    )
    out.append(
        """<div class="limit"><p><strong>Limits.</strong> This is one year at a time. It does not follow people through their lives, and the same person can be on either side at different times, for example while at school, working or retired.
Households with children count the value of their state schooling as a benefit. Taxes paid by companies, such as Corporation Tax, and some other taxes are not counted against any household, while not every public service is counted as a benefit, so the two sides do not add up to the government's totals.
The ONS began adjusting for top earners being under-recorded in the survey in its 2018/19 tables, and applied the adjustment to this series back to 2001/02. So years before and after 2001/02 are less directly comparable.</p></div>"""
    )
    out.append(
        source_line(
            sources,
            ["etb"],
            "Table 16. Benefits are cash benefits plus benefits in kind; taxes are direct plus indirect taxes (ONS note 16).",
        )
    )
    return "\n".join(out)


AGE_PAGE = "who-pays-age.html"


def income_tax_age_section(facts, d, num, sources, full=False):
    """HMRC Survey of Personal Incomes Table 3.2: Income Tax payers, income and tax by age (review gap 4).

    The who pays page shows the short version (heading, answer and a link); the
    full version, with the bars and tables, is a page of its own so that who
    pays stays short on a phone.
    """
    w = d["who_age"]
    ages = w["ages"]
    yr = w["year"].replace(" to ", "-")[:5] + w["year"][-2:]
    lab = {k: (v if k in ("u20", "75plus") else v.replace("-", " to ")) for k, v in ages}
    q = sources["explain-hmrc-spi-quality"]["page"]
    top = max((k for k, _ in ages), key=lambda k: facts[f"spi.age.meantax.{k}.all"].value)
    head = (
        '<h2 id="age">5. Income Tax, by age</h2>'
        if not full
        else '<h2 id="by-age">Income Tax at each age</h2>'
    )
    where = 'section 1 of <a href="who-pays.html">who pays</a>' if full else "section 1"
    out = [
        head
        + f"""
<p>From the same HMRC records as {where}: only the {num("spi.age.n.all.all", "millions_people")} people who owed some Income Tax in tax year {yr}.</p>
<div class="answer"><p class="lede">In tax year {yr}, taxpayers aged 30 to 64 were {num("spi.age.sharen.30_64", "pct0")} of all Income Tax payers and owed about {num("spi.age.sharetax.30_64", "pct0")} of all Income Tax.
Taxpayers aged 65 and over were {num("spi.age.sharen.65plus", "pct0")} of taxpayers and owed about {num("spi.age.sharetax.65plus", "pct0")}; those under 30 were {num("spi.age.sharen.u30", "pct0")} and owed about {num("spi.age.sharetax.u30", "pct0")}.</p>
<p>The age groups that owed the most tax per taxpayer also had the highest incomes. The highest average (mean) Income Tax was {num(f"spi.age.meantax.{top}.all", "pounds")} a year for taxpayers aged {lab[top]}, on an average income of {num(f"spi.age.meaninc.{top}.all", "pounds")}.
The middle (median) taxpayer in that group owed much less, {num(f"spi.age.medtax.{top}.all", "pounds")}: a small number of taxpayers with very high incomes and tax bills raise the mean.</p></div>"""
    ]
    if not full:
        short = out[0].split("<p>The age groups that owed the most")[0].rstrip() + "</div>"
        return short + (
            f'\n{NOFOLD}<p class="more-link"><a href="{AGE_PAGE}">Income Tax by age</a>: the average tax per taxpayer at each age, '
            "the median beside the mean, men and women separately, and the full table.</p>"
        )
    items = [
        (
            esc(lab[k]),
            f"spi.age.meantax.{k}.all",
            "alt" if k in ("65_69", "70_74", "75plus") else "",
        )
        for k, _ in ages
    ]
    out.append(
        bars(
            items,
            "pounds",
            num,
            caption=f"Average (mean) Income Tax owed per taxpayer, by age, £ a year, tax year {yr}. Grey bars: ages 65 and over. Taxpayers only.",
        )
    )
    out.append(FOLD)
    out.append(
        "<p>Because people who owe no Income Tax are not in these records, they cannot show what share of each age group pays Income Tax.</p>"
    )
    items = [
        (esc(lab[k]), f"spi.age.sharetax.{k}", "alt" if k in ("65_69", "70_74", "75plus") else "")
        for k, _ in ages
    ]
    out.append(
        bars(
            items,
            "pct",
            num,
            caption=f"Share of all Income Tax owed by each age range, per cent, tax year {yr}. Calculated here from HMRC's rounded figures, so approximate.",
        )
    )
    rows = [
        [
            esc(lab[k]),
            num(f"spi.age.n.{k}.all", "millions_people"),
            num(f"spi.age.sharen.{k}", "pct"),
            num(f"spi.age.sharetax.{k}", "pct"),
            num(f"spi.age.medinc.{k}.all", "pounds"),
            num(f"spi.age.medtax.{k}.all", "pounds"),
            num(f"spi.age.meaninc.{k}.all", "pounds"),
            num(f"spi.age.meantax.{k}.all", "pounds"),
            num(f"spi.age.rate.{k}", "pct"),
        ]
        for k, _ in ages
    ]
    rows.append(
        [
            "All ages",
            num("spi.age.n.all.all", "millions_people"),
            "100%",
            "100%",
            num("spi.age.medinc.all.all", "pounds"),
            num("spi.age.medtax.all.all", "pounds"),
            num("spi.age.meaninc.all.all", "pounds"),
            num("spi.age.meantax.all.all", "pounds"),
            "",
        ]
    )
    out.append(
        details_table(
            "Show the full table: taxpayers, income and tax by age",
            f"Income Tax payers, income and Income Tax by age, tax year {yr}",
            [
                "Age",
                "Taxpayers",
                "Share of taxpayers",
                "Share of all Income Tax",
                "Median income",
                "Median tax",
                "Mean income",
                "Mean tax",
                "Tax as % of the group's income",
            ],
            rows,
        )
    )
    out.append(
        f"""<p class="small">Income is total income before tax for the year: earnings, self-employment profits, pensions (including the State Pension), property, savings and dividends.
“Median” is the middle taxpayer in each age range. “Mean” is the total divided by the number of taxpayers. Shares and “tax as % of the group's income” are calculated here: number of taxpayers × mean, and mean tax ÷ mean income.
Added up this way, all ages come to {num("spi.age.tottax.sum.all", "bn")} of Income Tax on {num("spi.age.totinc.sum.all", "bn")} of income.</p>"""
    )
    rows = []
    for k, _ in ages:
        rows.append(
            [
                esc(lab[k]),
                num(f"spi.age.n.{k}.men", "millions_people"),
                num(f"spi.age.medtax.{k}.men", "pounds"),
                num(f"spi.age.meantax.{k}.men", "pounds"),
                num(f"spi.age.n.{k}.women", "millions_people"),
                num(f"spi.age.medtax.{k}.women", "pounds"),
                num(f"spi.age.meantax.{k}.women", "pounds"),
            ]
        )
    out.append(
        details_table(
            "Show men and women separately",
            f"Income Tax payers and Income Tax by age and sex, tax year {yr}",
            [
                "Age",
                "Men: taxpayers",
                "Men: median tax",
                "Men: mean tax",
                "Women: taxpayers",
                "Women: median tax",
                "Women: mean tax",
            ],
            rows,
        )
    )
    out.append(explain("taxpayers-age", sources))
    out.append(
        f"""<div class="limit"><p><strong>Limits.</strong> One tax year only: this is a snapshot of different people at different ages, not one person's tax over their life, and it does not say why the groups differ.
Income Tax only: it leaves out National Insurance, which people do not pay on earnings once they reach State Pension age, and taxes on spending such as VAT. People who owe no Income Tax are not counted.
The figures are estimates from a sample of about 1 million tax records. HMRC does not publish margins of error for this table, so small differences between neighbouring age ranges may not be meaningful (see HMRC's <a href="{esc(q)}">background quality report</a>).
HMRC rounds numbers to three significant figures, so shares calculated here can be slightly out. A change in how the survey samples State Pension recipients in {yr} means older age groups are not directly comparable with earlier years.</p></div>"""
    )
    out.append(
        source_line(
            sources,
            ["hmrc-spi-2324-tables"],
            f"Table 3.2, tax year {yr} (UK taxpayers only). Totals and shares calculated here.",
        )
    )
    return "\n".join(out)


FIFTHS = (
    ("q1", "Lowest-income fifth"),
    ("q2", "Second fifth"),
    ("q3", "Middle fifth"),
    ("q4", "Fourth fifth"),
    ("q5", "Highest-income fifth"),
)


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
    out = [
        f"""<h2 id="over-time">How has this changed since {first}?</h2>
<div class="answer"><p class="lede">On the ONS’s older method, taxes took {num(hall, "pct")} of gross household income in {first} and {num(oall, "pct")} in {ov}. On its current method, they took {num(f"etbp.all.{key(adj)}.all", "pct")} in {adj} and {num(f"etbp.all.{key(last)}.all", "pct")} in {last}.</p>
<p>The two methods give different figures for the same year, so they are not joined.</p></div>"""
    ]
    out.append(
        line_chart(
            f"All taxes as a share of gross household income, UK, {first} to {last}",
            labels,
            [("Everyone", vals(series_ids("all")), "a")],
            f"Per cent of gross household income, average across all households to {ov} and across all people from {adj}. Calendar years to 1993, then financial years (April to March).",
            breaks=[(cut, "Method changed")],
            split_breaks=True,
            ymin=0,
            ymax=50,
            finding=_plain_years(
                F.both(
                    F.trend("On the older method, the share", which="first"),
                    F.trend("on the current method it", which="last"),
                )
            ),
            events=[(labels.index("2020/21"), "Covid")] if "2020/21" in labels else (),
            kind="pct",
            ids=[series_ids("all")],
            num=num,
            point_labels=pl,
        )
    )
    out.append(FOLD)  # keep the main chart in view on phones
    out.append(
        f"""<p>The older method put households into fifths; the current one puts people into fifths and, from {adj}, adds an estimate of income that very high earners do not report in the survey.
For {ov}, the one year published both ways, the share for everyone was {num(oall, "pct")} on the older method and {num(f"etbp.all.{key(ov)}.all", "pct")} on the current way of ranking, before the top-income adjustment.</p>"""
    )
    out.append(
        """<p>On the older method, the share for the lowest-income fifth was below the share for the highest-income fifth in every year from 1977 to 1987, and above it in every year from 1988 to 2017/18. On the current method the two have been within five percentage points of each other, with the order changing from year to year. The make-up differs: for the lowest-income fifth most tax is indirect, such as VAT, and for the highest-income fifth most is direct, such as Income Tax. The panels below show each fifth on the same scale.</p>"""
    )
    out.append(
        small_multiples(
            f"All taxes as a share of gross household income, by fifth, UK, {first} to {last}",
            labels,
            [(lab, vals(series_ids(q))) for q, lab in FIFTHS],
            "Per cent of gross household income. Fifths of households to 2017/18; fifths of people from 2018/19.",
            "pct",
            ids=[series_ids(q) for q, _ in FIFTHS],
            num=num,
            breaks=[(cut, "Method changed")],
            split_breaks=True,
            finding=F.leader(
                "Taxes took the largest share of income for the {lname} {span}",
                which="last",
                close=1.0,
                close_template="Taxes took a similar share of income for the {lname} and the {lsecond} {span}, less than one percentage point apart",
            ),
            ymin=0,
            point_labels=pl,
        )
    )
    # every year, both methods, including the overlap year on the people method
    rows = []
    for p in hh:
        rows.append(
            [esc(p), "Households"]
            + [num(f"etbh.pall.{key(p)}.{q}", "pct") for q, _ in FIFTHS]
            + [num(f"etbh.pall.{key(p)}.all", "pct")]
        )
    for p in pp:
        how = (
            "People, top incomes adjusted"
            if labels.index(p) >= cut
            else "People, no top-income adjustment"
        )
        rows.append(
            [esc(p), how]
            + [num(f"etbp.all.{key(p)}.{q}", "pct") for q, _ in FIFTHS]
            + [num(f"etbp.all.{key(p)}.all", "pct")]
        )
    out.append(
        details_table(
            "Show every year, by fifth",
            f"All taxes as a percentage of gross household income, {first} to {last}",
            [
                "Year",
                "Method",
                "Lowest fifth",
                "Second",
                "Middle",
                "Fourth",
                "Highest fifth",
                "Everyone",
            ],
            rows,
        )
    )
    rows = []
    for p in hh:
        rows.append(
            [esc(p), "Households"]
            + [num(f"etbh.p{m}.{key(p)}.all", "pct") for m in ("direct", "indirect")]
            + [num(f"etbh.pall.{key(p)}.all", "pct")]
        )
    for p in pp:
        how = (
            "People, top incomes adjusted"
            if labels.index(p) >= cut
            else "People, no top-income adjustment"
        )
        rows.append(
            [esc(p), how]
            + [num(f"etbp.{m}.{key(p)}.all", "pct") for m in ("direct", "indirect", "all")]
        )
    out.append(
        details_table(
            "Show direct and indirect taxes, every year",
            f"Direct and indirect taxes as a percentage of gross household income, everyone, {first} to {last}",
            ["Year", "Method", "Direct taxes", "Indirect taxes", "All taxes"],
            rows,
        )
    )
    out.append(
        f"""<div class="limit"><p><strong>Limits.</strong> These are survey estimates for private households in the UK, and a share of income, not anyone’s tax rate.</p>
<ul>
<li><strong>Two methods, not joined.</strong> To {ov}, households were ranked by their income adjusted for household size and split into fifths with about the same number of households in each; “everyone” is the average household. From {adj} in the chart and tables ({ov} is also published this way, as a bridge), people are ranked by their household’s adjusted income and split into fifths with about the same number of people in each; “everyone” is the average across people.</li>
<li><strong>Top incomes.</strong> The ONS began adjusting for very high earners being missing or under-recorded in the survey in its {adj} tables, and applied the adjustment back to 2001/02 in its own time series. The yearly tables used here include it from {adj}; the older ones were published before that change and do not.</li>
<li><strong>Deferred tax payments.</strong> From {t["lump_sums_from"]}, direct taxes include lump-sum payments of tax put off from earlier years. The ONS warns this can make direct taxes look high for the lowest-income fifths.</li>
<li><strong>Years and taxes change.</strong> Figures are for calendar years to 1993 and financial years (April to March) from 1994/95. Local taxes changed from domestic rates to the community charge to Council Tax, and in some years the older tables count water charges with local taxes.</li>
<li><strong>Not counted.</strong> Taxes paid by companies, such as Corporation Tax, are not allocated to households. Some taxes paid by businesses are counted as indirect taxes passed on in prices.</li>
</ul></div>"""
    )
    out.append(
        source_line(
            sources,
            [
                "etb-hist-quintile-all",
                "etb-hist-quintile-all-2",
                "etb-fye2018",
                "etb-fye2019",
                "etb-fye2020",
                "etb-fye2021",
                "etb-fye2022",
                "etb-fye2023",
                "etb",
            ],
            "Older method: historical tables, one sheet per year; shares calculated here as (total direct taxes + total indirect taxes) ÷ gross income. Current method: Table 8 of each year’s reference tables, all individuals.",
        )
    )
    return "\n".join(out)


def income_tax_age_page(facts, d, num, sources):
    """Income Tax by age on a page of its own, linked from section 6 of who pays."""
    from .html import page

    body = [
        '<p class="small"><a href="who-pays.html">Who pays?</a></p>',
        "<h1>How much Income Tax do people of different ages pay?</h1>",
        income_tax_age_section(facts, d, num, sources, full=True),
    ]
    return page(
        AGE_PAGE,
        "Income Tax by age",
        "\n".join(body),
        "Income Tax payers, income and Income Tax by age group in the UK, from HMRC's Survey of Personal Incomes.",
    )


def households_short(facts, d, num):
    """Section 3 of who pays: the answer for retired people and types of household, with a link to the full page."""
    types = [t for t in d["who_types"]["types"] if t[0] != "all"]
    by_share = sorted(types, key=lambda t: facts[f"etb.t12.{t[0]}.taxshare"].value)
    lo, hi = by_share[0], by_share[-1]
    return f"""<h2 id="household-type">3. Retired people and other kinds of household</h2>
<div class="answer"><p class="lede">Retired households (where retired people bring in at least half the income) paid less tax in cash ({num("etb.ret.alltax.all", "pounds")} a year, against {num("etb.nonret.alltax.all", "pounds")}), but also had less income ({num("etb.ret.gross.all", "pounds")} gross, against {num("etb.nonret.gross.all", "pounds")}). Taxes took {num("etb.ret.taxshare.all", "pct")} of their gross income, against {num("etb.nonret.taxshare.all", "pct")}.</p>
<p>Across the {len(types)} kinds of household shown, adjusted for size, taxes took {num(f"etb.t12.{lo[0]}.taxshare", "pct0")} ({esc(lo[1].lower())}) to {num(f"etb.t12.{hi[0]}.taxshare", "pct0")} ({esc(hi[1].lower())}) of gross income.</p></div>
{NOFOLD}<p class="more-link"><a href="{HOUSEHOLDS_PAGE}">Retired people and kinds of household</a>: the taxes each group pays, who counts as retired, families with and without children, and the full tables.</p>"""


def households_page(facts, d, num, sources):
    """Retired people and types of household on a page of their own, linked from section 3 of who pays."""
    from .html import page

    body = [
        '<p class="small"><a href="who-pays.html">Who pays?</a></p>',
        "<h1>How much tax do retired people and different kinds of household pay?</h1>",
        '<p>From the Office for National Statistics survey used in section 2 of <a href="who-pays.html#households">who pays</a>: the taxes paid by the households people live in, including VAT and other taxes on spending.</p>',
        (
            f'<div class="answer"><p class="lede">In 2023/24, retired households paid about {num("etb.ret.alltax.all", "pounds")} a year in all taxes on average, '
            f'and non-retired households about {num("etb.nonret.alltax.all", "pounds")}. Measured against their own gross income, taxes took {num("etb.ret.taxshare.all", "pct")} '
            f'for retired households and {num("etb.nonret.taxshare.all", "pct")} for non-retired households. Retired households also had less income, so both measures matter.</p></div>'
        ),
        retired_section(facts, d, num, sources),
        household_types_section(facts, d, num, sources),
    ]
    return page(
        HOUSEHOLDS_PAGE,
        "Taxes by kind of household",
        "\n".join(body),
        "All taxes paid by retired and non-retired households and by type of household in the UK, from the ONS effects of taxes and benefits survey.",
    )
