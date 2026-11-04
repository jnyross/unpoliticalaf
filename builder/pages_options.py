"""Ten ways to improve the UK economy, ranked on published estimates.

Every figure here is typed from the source named beside it (no build-time
check reads these sources, so each entry is a hand-entered citation).
The ranking uses one measure only: the published estimate of the effect on the
level of GDP after about ten years. Options without a comparable figure are
listed without a rank rather than ranked on a guess.
"""
from .html import page

RANKED = [
    {
        "name": "Planning reform, full expensing and access to finance",
        "quote": "Capital deepening: planning reform, extension of full expensing, access to finance",
        "estimate": "+2.1% of potential GDP after 10 years; +4.4% after 25 years.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "confidence": "Medium to low: a model simulation with many stated assumptions.",
    },
    {
        "name": "Getting people on long-term sick leave back into work",
        "quote": "Labour utilisation: activation of the long-term sick",
        "estimate": "+1.4% of potential GDP after 10 years; +1.6% after 25 years.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "confidence": "Medium to low: a model simulation with many stated assumptions.",
    },
    {
        "name": "Ambitious alignment of rules with the EU (regulatory alignment)",
        "quote": "ambitious regulatory alignment",
        "estimate": "+0.6% of GDP by 2035, roughly ten years on.",
        "source": "Resolution Foundation, The growth mindset (2024).",
        "confidence": "Low to medium: one organisation's scenario, not the OECD model.",
    },
    {
        "name": "Lower trade barriers and more research and development support",
        "quote": "Productivity: reduction in trade barriers, improved R&D support",
        "estimate": "+0.5% of potential GDP after 10 years; +1.7% after 25 years.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "confidence": "Medium to low: a model simulation; trade and R&D are estimated together.",
    },
]

NOT_RANKED = [
    ("Higher net migration",
     "The OBR's analysis gives GDP 1.5% higher in 2028-29 with the same productivity, but GDP per person largely unchanged. It is a different horizon and measure, so it is not ranked. Its budget effect is 1.1% of GDP lower primary deficit by 2072-73 in a 2023 OBR scenario (245,000 net migrants a year, against 129,000)."),
    ("Childcare that brings mothers back to work",
     "A CBI draft gives up to £290 million of GDP for every 10,000 mothers who return to work. It has no national total, so it cannot be ranked."),
    ("Keeping the state pension triple lock",
     "No GDP estimate. The IFS says the triple lock adds about £16 billion a year to state pension spending against earnings uprating, and keeping it to 2050 would cost about £20 billion a year in expectation (range £5 to £40 billion). Rounded against GDP of about £3 trillion, that is about 0.5% of GDP a year. This is a budget effect, not a growth effect."),
    ("Reviewing tax reliefs",
     "The reliefs cost £207 billion, about 7.6% of GDP, in 2023-24 (taxexpenditures.org, 2025). No source gives the net gain from removing them, so it cannot be ranked."),
    ("Property taxes",
     "The UK raises 3.7% of GDP from property taxes against an OECD average of 2% (2023). No source gives the effect of reforming them, so it cannot be ranked."),
    ("Faster electricity grid connection and energy reform",
     "The OECD recommends faster grid connection reform but gives no quantified effect in its survey, so it cannot be ranked."),
]

SOURCES = [
    ("OECD Economic Surveys: United Kingdom 2026, Table 1.1", "https://www.oecd.org/en/publications/oecd-economic-surveys-united-kingdom-2026_aa997c6e-en/full-report/strengthening-growth-while-ensuring-fiscal-sustainability_81c7c25f.html"),
    ("Resolution Foundation, The growth mindset (2024)", "https://www.resolutionfoundation.org/app/uploads/2024/09/Growth-Mindset.pdf"),
    ("OBR, Net migration forecast and its impact on the economy", "https://obr.uk/box/net-migration-forecast-and-its-impact-on-the-economy/"),
    ("OBR, Fiscal risks and sustainability, July 2023", "https://obr.uk/docs/dlm_uploads/Fiscal_risks_and_sustainability_report_July_2023.pdf"),
    ("CBI, Potential impact of childcare reform (draft)", "https://www.cbi.org.uk/media/iqzlrkfd/childcare-gdp-static-dynamic-estimates.pdf"),
    ("IFS, What do you need to know about the triple lock?", "https://ifs.org.uk/articles/what-do-you-need-know-about-triple-lock"),
    ("Tax Expenditures in the United Kingdom: an International Perspective (2025)", "https://www.taxexpenditures.org/2025/12/15/tax-expenditures-in-the-united-kingdom-an-international-perspective/"),
]


def options_page():
    ranked = "".join(
        f"<li><h3>{r['name']}</h3>"
        f"<p><strong>Estimate:</strong> {r['estimate']}</p>"
        f"<p><strong>Source:</strong> {r['source']} Wording in the source: {r['quote']}.</p>"
        f"<p><strong>Confidence:</strong> {r['confidence']}</p></li>"
        for r in RANKED)
    not_ranked = "".join(f"<li><h3>{name}</h3><p>{why}</p></li>" for name, why in NOT_RANKED)
    sources = "".join(f'<li><a href="{url}">{title}</a></li>' for title, url in SOURCES)
    body = f"""
<h1>Ways to improve the UK economy: ten options</h1>
<p>Each option is ranked by one measure: the published estimate of how much it raises the level of GDP after about ten years, as a percentage of GDP. The estimates come from different sources and models, so they are not like-for-like. Where a source gives no comparable figure, the option is listed without a rank.</p>
<h2>Ranked: the GDP level after about ten years</h2>
<p>The OECD measures each of its effects as a percentage of baseline potential GDP. Its full package, combining these reforms, gives +4.0% of potential GDP after 10 years and +7.7% after 25 years.</p>
<ol>{ranked}</ol>
<h2>Not ranked: no comparable estimate yet</h2>
<ul>{not_ranked}</ul>
<h2>How the ranking works</h2>
<ul>
<li>The measure is the level of GDP after about ten years. A 2035 estimate is treated as about ten years on from 2025.</li>
<li>The OECD figures are relative to baseline potential GDP. Other figures are not on the same basis.</li>
<li>A second ranking, by effect on the budget balance, could not be made from these sources. Only the triple lock has a budget figure.</li>
<li>&ldquo;Best&rdquo; depends on goals. Growth, fairness and the deficit can rank the options differently, and this page does not choose between them.</li>
</ul>
<h2>Sources</h2>
<ul>{sources}</ul>
"""
    return page("economy-options.html", "Ways to improve the UK economy: ten options", body,
                description="Ten options for improving the UK economy, ranked on one published measure, with sources and confidence.")
