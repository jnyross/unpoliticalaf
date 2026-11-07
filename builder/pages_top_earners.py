"""What if high earners left the UK? (John's question J6)

Answers first: how much Income Tax the highest earners pay, what a stated number of leavers would take
with them (mechanically), what counts as meaningful (a judgement, with yardsticks), and what the OBR has
said about how high earners respond to tax rates. Figures come from HMRC's Survey of Personal Incomes
(data_top_earners.py) and the receipts already on the site.
"""

from .html import page, keyfigs, bars, table, details_table, source_line

PAGE = "high-earners.html"
FORECAST_EVAL = "https://assets.publishing.service.gov.uk/media/6a1ea800c7335e2ca6daadfc/Forecast-evaluation-report-June-2026.pdf"
BOX_2012 = "https://obr.uk/box/the-additional-rate-of-income-tax/"
BOX_2014 = "https://obr.uk/box/effect-of-the-additional-rate-of-income-tax-on-receipts/"


def what_if_rows(num, leavers):
    """One row per number of leavers: tax lost from each group, and as shares of Income Tax and receipts.

    A group that does not have that many people shows a dash, not a figure.
    """
    rows = []
    for label, key in leavers:
        row = [label]
        for g in ("ge1m", "ge150k"):
            if key is not None and not key.get(g):
                row += ["–", "–", "–"]
                continue
            k = key[g]
            row += [
                num(f"wif.{g}.{k}.bn", "bn1"),
                num(f"wif.{g}.{k}.pct_tax", "pct2"),
                num(f"wif.{g}.{k}.pct_rec", "pct2"),
            ]
        rows.append(row)
    return rows


def high_earners_page(facts, d, num, sources):
    body = [
        '<p class="small"><a href="who-pays.html">Who pays?</a></p>',
        "<h1>What if high earners left the UK?</h1>",
    ]

    body.append(
        f"""<div class="answer"><p class="lede">In 2023-24, {num("wif.ge1m.all.n", "int")} taxpayers had total income of £1 million or more. Together they paid {num("spi.ge1m.taxbn", "bn1")} of Income Tax, {num("spi.ge1m.sh_tax", "pct")} of the total. On average each paid {num("spi.ge1m.avgtax", "pounds")} a year.</p>
<p>If some of them left and nothing else changed, the Treasury would lose the tax they paid. For example, 1,000 leavers from this group would take {num("wif.ge1m.s1000.bn", "bn1")} of tax with them, {num("wif.ge1m.s1000.pct_tax", "pct2")} of all Income Tax. Whether that is “meaningful” is a judgement, so the page gives yardsticks rather than a verdict.</p></div>"""
    )

    body.append(
        keyfigs(
            [
                (
                    num("wif.ge1m.all.n", "int"),
                    "taxpayers with total income of £1 million or more",
                    False,
                ),
                (
                    num("spi.ge1m.sh_tax", "pct"),
                    "of all Income Tax, paid by those taxpayers",
                    False,
                ),
                (
                    num("wif.yard.bn", "bn1"),
                    "one per cent of public sector receipts, 2023-24: the yardstick in section 3",
                    False,
                ),
            ]
        )
    )

    # 1. Who pays the most Income Tax
    body.append('<h2 id="who">1. Who pays the most Income Tax?</h2>')
    body.append(
        "<p>HMRC's Survey of Personal Incomes groups taxpayers by income. Income here is total income before tax: earnings, pensions, savings and dividends, before deductions and allowances. The survey covers taxpayers only, so people who pay no Income Tax are not counted.</p>"
    )
    body.append(
        bars(
            [
                ("Top 1% of taxpayers", "hmrc.share.top1.2023 to 2024", ""),
                ("£150,000 and over", "spi.ge150k.sh_tax", ""),
                ("£500,000 and over", "spi.ge500k.sh_tax", ""),
                ("£1 million and over", "spi.ge1m.sh_tax", ""),
            ],
            "pct",
            num,
            maxval=40,
            caption="Share of all Income Tax paid, 2023-24, by income group. The groups overlap: the top 1% includes some people with £150,000 and over, and the £150,000 group includes the £1 million group.",
        )
    )
    grp_rows = []
    for key, label in (
        ("ge150k", "£150,000 and over"),
        ("ge500k", "£500,000 and over"),
        ("ge1m", "£1 million and over"),
    ):
        grp_rows.append(
            [
                label,
                num(f"spi.{key}.n", "int"),
                num(f"spi.{key}.sh_n", "pct2"),
                num(f"spi.{key}.taxbn", "bn1"),
                num(f"spi.{key}.sh_tax", "pct"),
                num(f"spi.{key}.avgtax", "pounds"),
            ]
        )
    body.append(
        table(
            "Income groups, 2023-24: taxpayers, Income Tax and average Income Tax per taxpayer",
            [
                "Total income",
                "Taxpayers (thousands)",
                "Share of taxpayers",
                "Income Tax",
                "Share of Income Tax",
                "Average Income Tax each",
            ],
            grp_rows,
        )
    )
    band_rows = []
    for lo, label in (
        (12570, "£12,570 to £15,000"),
        (15000, "£15,000 to £20,000"),
        (20000, "£20,000 to £30,000"),
        (30000, "£30,000 to £40,000"),
        (40000, "£40,000 to £50,000"),
        (50000, "£50,000 to £70,000"),
        (70000, "£70,000 to £100,000"),
        (100000, "£100,000 to £150,000"),
        (150000, "£150,000 to £200,000"),
        (200000, "£200,000 to £300,000"),
        (300000, "£300,000 to £500,000"),
        (500000, "£500,000 to £1 million"),
        (1000000, "£1 million and over"),
    ):
        band_rows.append(
            [
                label,
                num(f"spi.band.{lo}.n", "int"),
                num(f"spi.band.{lo}.tax", "int"),
                num(f"spi.band.{lo}.sh_tax", "pct"),
                num(f"spi.band.{lo}.avgtax", "pounds"),
            ]
        )
    body.append(
        details_table(
            "Show every income band",
            "Taxpayers, Income Tax and average Income Tax by band of total income, 2023-24",
            [
                "Total income",
                "Taxpayers (thousands)",
                "Income Tax (£ million)",
                "Share of Income Tax",
                "Average Income Tax each",
            ],
            band_rows,
        )
    )

    # 2. What if some of them left?
    body.append(
        f"""<h2 id="leavers">2. What would leavers take with them?</h2>
<div class="answer"><p class="lede">Each leaver is counted at the average Income Tax of their group. Losing all {num("wif.ge1m.all.n", "int")} taxpayers in the £1 million group would take {num("wif.ge1m.all.bn", "bn1")}, {num("wif.ge1m.all.pct_tax", "pct")} of all Income Tax.</p></div>"""
    )
    rows = what_if_rows(
        num,
        [
            ("1,000 leavers", {"ge1m": "s1000", "ge150k": "s1000"}),
            ("10,000 leavers", {"ge1m": "s10000", "ge150k": "s10000"}),
            ("100,000 leavers", {"ge150k": "s100000"}),
            ("Every taxpayer in the £1 million group", {"ge1m": "all"}),
            ("Every taxpayer in the £150,000 group", {"ge150k": "all"}),
        ],
    )
    body.append(
        table(
            "Tax lost if a stated number of leavers, 2023-24, mechanically, before any other change: £1 million and over, and £150,000 and over",
            [
                "Leavers",
                "£1 million and over: tax lost",
                "Share of Income Tax",
                "Share of receipts",
                "£150,000 and over: tax lost",
                "Share of Income Tax",
                "Share of receipts",
            ],
            rows,
        )
    )
    body.append(
        '<p class="small">A dash means that group has fewer taxpayers than the number of leavers shown. Share of receipts: public sector current receipts in 2023-24.</p>'
    )

    # 3. Yardsticks
    body.append(
        f"""<h2 id="meaningful">3. What counts as “meaningful”?</h2>
<p>The site does not set a threshold. What matters depends on what the reader wants receipts to pay for, and how a loss would be covered: by spending cuts, other taxes or borrowing. Three yardsticks help:</p>
<ul>
<li><strong>One per cent of receipts</strong> was {num("wif.yard.bn", "bn1")} in 2023-24. That is the tax of about {num("wif.yard.ge1m.n", "int")} leavers from the £1 million group ({num("wif.yard.ge1m.share", "pct0")} of it), or about {num("wif.yard.ge150k.n", "int")} from the £150,000 group ({num("wif.yard.ge150k.share", "pct0")} of it).</li>
<li><strong>Forecast errors.</strong> The OBR's June 2026 evaluation found that 2024-25 receipts were £35 billion (3.2%) higher than its March 2023 forecast made two years before (<a href="{FORECAST_EVAL}">OBR, Forecast evaluation report, June 2026, paragraph 3.18</a>). A gap of that size shows how far receipts can move from a forecast, whatever the cause.</li>
<li><strong>Size of the group.</strong> The £1 million group has {num("wif.ge1m.all.n", "int")} taxpayers. Losing a large share of it would be a change in who pays, not just in the total.</li>
</ul>"""
    )

    # 4. What forecasters say about behaviour
    body.append(
        f"""<h2 id="behaviour">4. What has the OBR said about high earners' behaviour?</h2>
<p>The clearest official example is the 50p rate on incomes over £150,000, introduced in April 2010 and cut to 45p from April 2013. Before it started, the Treasury's costing allowed for people changing their behaviour. The OBR later reviewed that costing.</p>
<blockquote><p>“It assumed that the 300,000 individuals likely to be affected would be liable to an extra £7.5 billion in tax in the absence of any change in behaviour, but that £4.9 billion of this would never materialise as they took steps to reduce their taxable income. These steps might include labour supply responses (e.g. working less, taking a lower paid job, retiring early, or leaving the country) or greater recourse to tax planning, avoidance and evasion.”</p>
<p class="small">Office for Budget Responsibility, <a href="{BOX_2012}">The additional rate of income tax</a>, March 2012.</p></blockquote>
<blockquote><p>“This concluded that the behavioural response to the increase in the additional rate had been greater than originally assumed by the previous Government.”</p>
<p>“The estimated underlying yield for 2012-13 from the introduction of the 50p tax rate was also reduced from £2.6 billion to £0.6 billion.”</p>
<p class="small">Office for Budget Responsibility, <a href="{BOX_2014}">Effect of the additional rate of income tax on receipts</a> (Box 3.2 of the Forecast evaluation report, 2014).</p></blockquote>
<p>The OBR also said that this kind of estimate is hard to make: “To calculate the effect of the 50p rate requires a counterfactual, i.e. what would have happened in the absence of its introduction. That will always be very difficult to estimate because the 50p rate was pre-announced, leading to substantial forestalling.”</p>"""
    )

    # Limits
    body.append(
        """<div class="limit"><p><strong>Limits.</strong> The leavers arithmetic is mechanical. It assumes each leaver takes the average Income Tax of their group, that the tax would otherwise have been paid in full, and that nothing else changes. It does not model who would leave, where they would go, whether they would still pay UK tax on UK income, or how others would change their behaviour. The OBR's 50p review shows those responses can be large. The figures are for 2023-24, the latest full survey year, and cover taxpayers only.</p></div>"""
    )

    body.append(
        source_line(
            sources,
            ["hmrc-spi-2324-tables", "hmrc24", "obr"],
            "Receipts are public sector current receipts from the OBR. The OBR quotations are from its published boxes, linked above.",
        )
    )
    return page(
        PAGE,
        "What if high earners left the UK?",
        "\n".join(body),
        "How much Income Tax the highest earners pay, what a stated number of leavers would take with them, and what the OBR has said about how high earners respond to tax.",
    )
