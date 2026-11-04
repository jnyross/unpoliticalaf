"""Ten ways to improve the UK economy, ranked on published estimates.

Every figure here is typed from the source named beside it. No build-time check
reads these sources, so each entry is a hand-entered citation. Conversions to
the common basis are shown on the page with their assumptions.

The ranking measure is the effect on the level of GDP after about ten years, as a
percentage of GDP. Budget effects are shown separately, because only some
options have one. An option with no comparable figure is listed without a rank.
"""
from .html import page

# Ranked on the 10-year GDP level (% of GDP).
RANKED = [
    {
        "name": "Planning reform, full expensing and access to finance",
        "row": "Capital deepening: planning reform, extension of full expensing, access to finance",
        "effect": "+2.1% of potential GDP after 10 years; +4.4% after 25 years.",
        "per_person": "Not given.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "conversion": "None: the OECD gives the 10-year figure directly.",
        "confidence": "Medium to low: a model simulation with many stated assumptions.",
    },
    {
        "name": "Net migration higher than the OBR's baseline",
        "row": "GDP 1.5 per cent higher in 2028-29",
        "effect": "+1.5% of GDP by 2028-29, with the same productivity as current residents.",
        "per_person": "Largely unchanged (the OBR's own figure).",
        "source": "OBR, Net migration forecast and its impact on the economy (online box).",
        "conversion": "The 2028-29 level is treated as the 10-year level. That is an assumption: the horizon is about four years, and the effect is a larger population, not more output per person.",
        "confidence": "Low: a horizon mismatch, and the per-person effect is zero.",
    },
    {
        "name": "Getting people on long-term sick leave back into work",
        "row": "Labour utilisation: activation of the long-term sick",
        "effect": "+1.4% of potential GDP after 10 years; +1.6% after 25 years.",
        "per_person": "Not given.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "conversion": "None: the OECD gives the 10-year figure directly.",
        "confidence": "Medium to low: a model simulation with many stated assumptions.",
    },
    {
        "name": "Ambitious alignment of rules with the EU (regulatory alignment)",
        "row": "ambitious regulatory alignment",
        "effect": "+0.6% of GDP by 2035, roughly ten years on.",
        "per_person": "Not given.",
        "source": "Resolution Foundation, The growth mindset (2024).",
        "conversion": "The 2035 level is treated as the 10-year level, roughly ten years from 2025.",
        "confidence": "Low to medium: one organisation's scenario, not the OECD model.",
    },
    {
        "name": "Lower trade barriers and more research and development support",
        "row": "Productivity: reduction in trade barriers, improved R&D support",
        "effect": "+0.5% of potential GDP after 10 years; +1.7% after 25 years.",
        "per_person": "Not given.",
        "source": "OECD Economic Surveys: United Kingdom 2026, Table 1.1 (2026).",
        "conversion": "None: the OECD gives the 10-year figure directly. Trade and R&D are estimated together.",
        "confidence": "Medium to low: a model simulation; the two are not separated.",
    },
    {
        "name": "More childcare that brings mothers back into work",
        "row": "up to £290 million of GDP for every 10,000 mothers",
        "effect": "Up to about 0.1% of GDP for every 100,000 mothers who return to work.",
        "per_person": "Not given.",
        "source": "CBI, Potential impact of childcare reform (draft; year not stated in the excerpt).",
        "conversion": "£290 million ÷ GDP of about £3 trillion ≈ 0.01% per 10,000 mothers; × 10 for 100,000. GDP of £3 trillion is a rounded assumption. The number of mothers who return is a scenario, not a forecast.",
        "confidence": "Low: a draft analysis, and the result depends on how many mothers return.",
    },
]

# Budget effects, shown separately. The triple lock is the only option with a
# sourced budget figure; the tax reliefs line is arithmetic, not an estimate.
BUDGET = [
    {
        "name": "Keeping the state pension triple lock (reforming it to earnings uprating)",
        "effect": "Saves about £16 billion a year against earnings uprating, about 0.5% of GDP a year. Keeping the triple lock to 2050 would cost about £20 billion a year in expectation (range £5 to £40 billion).",
        "conversion": "£16 billion ÷ GDP of about £3 trillion ≈ 0.5%. GDP is a rounded assumption. The saving ignores any change in behaviour.",
        "source": "IFS, What do you need to know about the triple lock?",
        "growth": "No GDP effect.",
        "confidence": "Medium: a fiscal estimate from one institute; the 2050 range is wide.",
    },
    {
        "name": "Reviewing tax reliefs",
        "effect": "Illustration only: the reliefs cost £207 billion in 2023-24, about 7.6% of GDP. Recovering 10% of that cost would be about 0.8% of GDP a year before any change in behaviour.",
        "conversion": "7.6% × 10% ≈ 0.8%. The 10% share is an illustration, not an estimate of what reform would raise.",
        "source": "Tax Expenditures in the United Kingdom: an International Perspective (2025); OECD Economic Surveys: United Kingdom 2026.",
        "growth": "Not estimated.",
        "confidence": "Low: no source gives the net gain from reform.",
    },
]

# Options without a comparable figure on either basis.
NOT_RANKED = [
    ("Property taxes",
     "The UK raises 3.7% of GDP from property taxes against an OECD average of 2% (2023). The Resolution Foundation's figure that Londoners under-pay by £3.1 billion is a regional redistribution, not a net gain to the Exchequer, so it cannot be ranked on either basis."),
    ("Faster electricity grid connection and energy reform",
     "The OECD recommends faster grid connection reform but gives no quantified effect in its survey. The energy shock that NIESR estimates is taking 0.3% off GDP growth this year is a cost of the shock, not an effect of reform, so it cannot be ranked."),
]

SOURCES = [
    ("OECD Economic Surveys: United Kingdom 2026, Table 1.1", "https://www.oecd.org/en/publications/oecd-economic-surveys-united-kingdom-2026_aa997c6e-en/full-report/strengthening-growth-while-ensuring-fiscal-sustainability_81c7c25f.html"),
    ("Resolution Foundation, The growth mindset (2024)", "https://www.resolutionfoundation.org/app/uploads/2024/09/Growth-Mindset.pdf"),
    ("OBR, Net migration forecast and its impact on the economy", "https://obr.uk/box/net-migration-forecast-and-its-impact-on-the-economy/"),
    ("OBR, Fiscal risks and sustainability, July 2023", "https://obr.uk/docs/dlm_uploads/Fiscal_risks_and_sustainability_report_July_2023.pdf"),
    ("CBI, Potential impact of childcare reform (draft)", "https://www.cbi.org.uk/media/iqzlrkfd/childcare-gdp-static-dynamic-estimates.pdf"),
    ("IFS, What do you need to know about the triple lock?", "https://ifs.org.uk/articles/what-do-you-need-know-about-triple-lock"),
    ("Tax Expenditures in the United Kingdom: an International Perspective (2025)", "https://www.taxexpenditures.org/2025/12/15/tax-expenditures-in-the-united-kingdom-an-international-perspective/"),
    ("Resolution Foundation, Broken housing taxes (press release)", "https://www.resolutionfoundation.org/press-releases/broken-housing-taxes-mean-londoners-are-under-paying-by-3-1-billion-with-the-rest-of-england-over-paying-in-return/"),
]


def _ranked_item(r):
    return (f"<li><h3>{r['name']}</h3>"
            f"<p><strong>Estimate:</strong> {r['effect']}</p>"
            f"<p><strong>Per person:</strong> {r['per_person']}</p>"
            f"<p><strong>Source:</strong> {r['source']} Wording in the source: {r['row']}.</p>"
            f"<p><strong>Conversion and assumptions:</strong> {r['conversion']}</p>"
            f"<p><strong>Confidence:</strong> {r['confidence']}</p></li>")


def options_page():
    ranked = "".join(_ranked_item(r) for r in RANKED)
    budget = "".join(
        f"<li><h3>{b['name']}</h3>"
        f"<p><strong>Budget:</strong> {b['effect']}</p>"
        f"<p><strong>Growth:</strong> {b['growth']}</p>"
        f"<p><strong>Conversion and assumptions:</strong> {b['conversion']}</p>"
        f"<p><strong>Source:</strong> {b['source']}</p>"
        f"<p><strong>Confidence:</strong> {b['confidence']}</p></li>"
        for b in BUDGET)
    not_ranked = "".join(f"<li><h3>{name}</h3><p>{why}</p></li>" for name, why in NOT_RANKED)
    sources = "".join(f'<li><a href="{url}">{title}</a></li>' for title, url in SOURCES)
    body = f"""
<h1>Ways to improve the UK economy: ten options</h1>
<p>Six options are ranked on one measure: the effect on the level of GDP after about ten years, as a percentage of GDP. The estimates come from different sources and models, so they are not like-for-like. The ranking shows the conversion for each. A second, separate list covers budget effects. Two options have no comparable figure on either basis and are not ranked.</p>
<p>The OECD measures each of its effects as a percentage of baseline potential GDP. Its full package, combining these reforms, gives +4.0% of potential GDP after 10 years and +7.7% after 25 years.</p>
<h2>Ranked: the GDP level after about ten years</h2>
<ol>{ranked}</ol>
<h2>Budget effects, shown separately</h2>
<ul>{budget}</ul>
<h2>Not ranked: no comparable estimate yet</h2>
<ul>{not_ranked}</ul>
<h2>How the ranking works</h2>
<ul>
<li>The ranking measure is the level of GDP after about ten years. Where a source gives a different horizon, the conversion is shown on that option.</li>
<li>Net migration ranks high on total GDP, but the OBR's own figure gives no change in GDP per person. A ranking by GDP per person would put it last.</li>
<li>&ldquo;Best&rdquo; depends on goals. Growth, fairness and the deficit can rank the options differently, and this page does not choose between them.</li>
</ul>
<h2>Sources</h2>
<ul>{sources}</ul>
"""
    return page("economy-options.html", "Ways to improve the UK economy: ten options", body,
                description="Ten options for improving the UK economy, ranked on one published measure, with conversions, sources and confidence.")
