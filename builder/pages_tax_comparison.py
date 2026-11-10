"""Answer J12.11 separately from observed household incidence and affordability."""

from .html import FOLD, page, source_line, table

PAGE = "life/tax-comparison.html"


def comparison_page(num, sources):
    rows = []
    for key, label, kind in [
        ("gross", "Gross annual pay (same April-price purchasing power)", "pounds"),
        ("weekly", "Gross weekly pay", "pounds2"),
        ("pa", "Annual Personal Allowance", "pounds"),
        ("taxable", "Annual taxable pay", "pounds"),
        ("it", "Income Tax", "pounds"),
        ("ni", "Employee National Insurance, 52 weeks", "pounds"),
        ("total", "Income Tax + employee NI", "pounds"),
        ("share", "Combined share of gross pay", "pct"),
    ]:
        rows.append([label] + [num(f"tax.example.{key}.{year}", kind) for year in (1992, 2025)])
    body = (
        '<p class="small"><a href="generations.html">Did parents have it easier?</a></p>'
        '<h1 id="key-answer">Tax at the same real pay: 1992-93 and 2025-26</h1>'
        '<div class="answer"><p><strong>One hypothetical employee, not an observed average.</strong> '
        f'In this example, Income Tax plus employee National Insurance takes {num("tax.example.share.1992", "pct")} '
        f'of gross pay in 1992-93 and {num("tax.example.share.2025", "pct")} in 2025-26: a smaller share in 2025-26. '
        f'Gross annual pay is {num("tax.example.gross.1992", "pounds")} then and '
        f'{num("tax.example.gross.2025", "pounds")} later, at the same real income using April CPIH.</p></div>'
        '<div class="limit"><p>This is not everyone’s tax rate or a verdict that one generation had it easier. '
        "It is not observed household tax incidence, all taxes combined, or mortgage affordability after tax.</p></div>"
        '<h2 id="comparison">The fixed example</h2>'
        + table(
            "Hypothetical employee in England, annual cash amounts, calculated",
            ["Measure", "1992-93", "2025-26"],
            rows,
        )
        + "<p>Amounts are rounded to the nearest pound for display, weekly pay to the nearest penny, "
        "and shares to one decimal place. The calculation retains full precision between steps.</p>"
        + FOLD
        + '<h2 id="assumptions">Who and what this assumes</h2>'
        "<p>An employee aged 30 in each example, resident in England for the whole tax year, single, "
        "with salary only, no pension contributions or salary sacrifice and no other allowances or reliefs. "
        "Ordinary under-65 Personal Allowance in 1992-93; standard Personal Allowance in 2025-26. "
        "Not contracted out in 1992-93; standard category A employee NI in 2025-26. Not a company director.</p>"
        "<p>There are exactly 52 equal weekly payments, no bonuses, gaps or 53rd payday. "
        "Income Tax uses the annual legal allowance and bands, not a tax code or weekly PAYE tables. "
        "NI uses weekly limits on each payment, then multiplies by 52, not annual or monthly limits. "
        "This is an analytical illustration: fractional pennies are retained in pay and NI until display. "
        "Actual payroll penny rounding and tax-code deductions may differ slightly. This is not a payslip or a general tax calculator.</p>"
        "<p>Excluded: employer NI, VAT, council tax (and 1992-93 community charge), duties, "
        "other taxes, student loan repayments, benefits and tax credits. No household composition or spending is assumed.</p>"
        '<h2 id="price-base">Same real gross pay, not the same rank in earnings</h2>'
        f"<p>The starting salary is an assumption, not an official average. ONS CPIH L522 is "
        f'{num("cpih.apr.1992", "dp1")} in April 1992 and {num("cpih.apr.2025", "dp1")} in April 2025 (2015 = 100). '
        f'Later gross pay = {num("tax.example.gross.1992", "pounds")} × {num("cpih.apr.2025", "dp1")} ÷ {num("cpih.apr.1992", "dp1")}. This uses April prices at the start of each tax year, '
        "not a tax-year average or April 2026 prices. Early CPIH is a historical estimate, not a household’s personal inflation rate. "
        "Equal CPIH-adjusted pay need not buy the same home or occupy the same place in the earnings distribution.</p>"
        '<h2 id="steps">Rules and steps</h2>'
        "<p><strong>1992-93:</strong> £15,600 − £3,445 allowance = £12,155 taxable. "
        "First £2,000 × 20% plus remaining £10,155 × 25% = £2,938.75 Income Tax. "
        "The 25% band ends at £23,700 taxable; above that the rate is 40%, not reached here. "
        "Weekly NI = £54 × 2% + (£300 − £54) × 9% = £23.22; × 52 = £1,207.44. "
        "Below £54 weekly there is no contribution; at £54 the initial 2% charge applies; "
        "the 9% slice stops at £405, with no further employee charge above it.</p>"
        "<p>The November 1992 Hansard answer discusses proposals effective April 1993, "
        "but explicitly identifies the <em>current</em> weekly limits as £54 and £405. "
        "The proposed £56 and £420 limits are not used for 1992-93.</p>"
        "<p><strong>2025-26:</strong> subtract the £12,570 annual allowance from the unrounded later gross pay; "
        "all remaining pay is within the £37,700 taxable basic band at 20%. "
        "Category A weekly NI is zero up to £242 (the £125 lower earnings limit is not the payment threshold), "
        "8% above £242 up to £967, then 2% above £967. Only the 8% slice is reached here. "
        "Multiply that weekly amount by 52. Add Income Tax and employee NI, divide by annual gross pay, "
        "then multiply by 100 for each combined share.</p>"
        + source_line(
            sources,
            [
                "hmrc-historic-allowances",
                "hmrc-historic-rates",
                "hansard-ni-1992",
                "gov-employer-rates-2025",
                "ons-l522",
            ],
            up="../",
        )
        + '<p><a href="../household-tax.html">Observed household tax-to-income measures are a different question</a>. '
        '<a href="../data/facts.json">Download all figure records (JSON)</a>.</p>'
    )
    return page(
        PAGE,
        "Tax at the same real pay",
        body,
        "One hypothetical England employee, 1992-93 and 2025-26, not an observed average.",
    )
