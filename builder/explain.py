"""Explanations quoted word for word from official publications.

The site's own text describes figures and does not say why they changed. Where
an official body (ONS, HMRC, a government department) has published its own
explanation, we quote it here, clearly attributed and linked, next to the
figures it explains.

Each quote must appear word for word in the publication's page, kept under
data/fetched/ (downloaded byte for byte by scripts/fetch_sources.py). The build
and builder.check both confirm this, so a quote cannot drift from its source.
"""
import html as _html
import re

from .html import esc
from .readers import ROOT

# id: question shown above the quote, source id (see sources.FETCHED), the
# publication's title and date, the passages quoted (each must appear in the
# source, and they are shown in this order), where it is shown, and for life
# topics the years it applies to on the year pages.
EXPLANATIONS = {
    # ------------------------------------------------------------ spending
    "covid-spending": dict(
        question="Why did spending jump in 2020-21?",
        source="explain-ons-psf-2021-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2021", date="23 April 2021",
        quote=["Central government tax and National Insurance receipts (combined) in the financial year ending (FYE) March 2021 (April 2020 to March 2021) fell by £34.9 billion (or 5.0%) compared with the same period a year earlier, while government support for individuals and businesses during the pandemic contributed to an increase of £203.2 billion (or 27.5%) in central government day-to-day (or current) spending.",
               "This substantial increase largely reflects the impact of the coronavirus pandemic on the public finances, with the furlough schemes alone adding £78.2 billion to borrowing in the FYE March 2021."]),
    "energy-2022": dict(
        question="Why did spending rise again in 2022-23?",
        source="explain-ons-psf-2023-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2023", date="25 April 2023",
        quote=["Central government current expenditure was £967.0 billion in the FYE 2023, an increase of £74.0 billion (8.3%) compared with FYE 2022, reflecting the impact of rising inflation and energy costs.",
               "the steady rise in receipts not enough to offset the £34.0 billion increase in interest payable on the government’s debt and the initally estimated £41.2 billion cost of the combined energy support schemes and other one-off costs."],
        gloss="“FYE 2023” means the financial year ending March 2023, which this site calls 2022-23. The second passage explains the gap between day-to-day spending and receipts that year."),
    "debt-interest-2022": dict(
        question="Why did interest on government debt rise in 2022-23?",
        source="explain-ons-psf-2023-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2023", date="25 April 2023",
        quote=["The interest payable on debt increased to £106.6 billion, £34.0 billion (46.9%) more compared with FYE 2022, as the rises in the Retail Prices Index have increased the interest payable on index-linked gilts."],
        gloss="Index-linked gilts are government bonds whose payments rise with the Retail Prices Index, a measure of inflation. ONS figures for debt interest are measured differently from the HM Treasury figures above, so the amounts differ."),
    # ------------------------------------------------------------ taxes
    "borrowing-records": dict(
        question="How did borrowing in 2020-21 compare with 2009-10, after the 2008 recession?",
        source="explain-ons-psf-2021-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2021", date="23 April 2021",
        quote=["Borrowing had generally been falling since its peak of £157.7 billion during the financial crisis in the FYE March 2010. However, largely as a result of the impact of the coronavirus pandemic, borrowing in the latest full financial year (April 2020 to March 2021) was nearly double this previous record.",
               "Expressed as a ratio of gross domestic product (GDP), public sector net borrowing (excluding public sector banks, PSNB ex) in the FYE March 2021 was 14.5%, the highest such ratio since the end of World War Two, when in FYE March 1946 it was 15.2%."]),
    "frozen-thresholds": dict(
        question="Why are more people paying Income Tax?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["The total number of Income Tax payers is projected to rise to 40.8 million in 2026 to 2027, mainly due to population and income growth combined with frozen Income Tax thresholds. The Personal Allowance is set at £12,570 in 2021 to 2022 through to 2030 to 2031, due to the extension of the freeze at Autumn Budget 2025."]),
    # ------------------------------------------------------------ who pays
    "top1-share": dict(
        question="Why does the top 1% share go up and down?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["The introduction of the additional rate in 2010 on taxable income over £150,000 led to a behavioural response by individuals bringing forward, or ‘forestalling’, income in 2009 to 2010.",
               "In April 2013, the additional rate was reduced from 50% to 45% which led to the deferral of income from the 2012 to 2013 tax year to the 2013 to 2014 tax year.",
               "The peak in shares of Income Tax liabilities at the top end of the distribution in 2021 to 2022, and subsequent fall in 2022 to 2023 onwards, is also due to the freeze in the higher rate threshold and Personal Allowance. This means there were more Income Tax payers overall in these years, changing the distribution among percentile groups."]),
    "retired-net": dict(
        question="Do retired households get back more than they pay in tax?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["For retired households, 90.1% were net recipients, largely reflecting the 10.1% uprating to state pensions and pension credits (classified as cash benefits)."],
        gloss="“Net recipients” are people in households that receive more in benefits, including services such as the NHS and education, than they pay in taxes."),
    # ------------------------------------------------------------ household tax
    "average-rates": dict(
        question="How much Income Tax do people at different incomes pay, as a share of their income?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["In 2023 to 2024, the average Income Tax rate was 4.8% for those with incomes from £15,000 to below £20,000, increasing to 9.0% for incomes from £20,000 to below £30,000 and 12.3% for incomes from £30,000 to below £50,000. For incomes within the higher rate tax band, the average Income Tax rate rose to 18.9% for individuals earning between £50,000 and £100,000 and then rose to 29.2% for individuals earning between £100,000 and £150,000."],
        gloss="These are averages for Income Tax payers in each income range, and cover Income Tax only, not National Insurance or taxes on spending."),
    "fiscal-drag": dict(
        question="Why did direct taxes rise in 2023/24?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["Income tax thresholds in FYE 2024 remained at 2022 levels, creating fiscal drag and so increasing households tax liabilities.",
               "Fiscal drag occurs when income tax thresholds are not adjusted in line with inflationary wage raises. As a result, taxpayers can be pushed into higher tax brackets, causing them to pay greater proportion of their income in taxes."]),
    "redistribution": dict(
        question="What do taxes and benefits do to the gap between richer and poorer households?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["The richest fifth of people's mean equivalised household income before taxes and benefits (£116,600) was 12.2 times larger than the poorest fifth (£9,600); however, this gap reduced to 3.3 times larger (£85,100 and £25,700, respectively) after all taxes and benefits."],
        gloss="“Equivalised” means adjusted for the size of the household. “After all taxes and benefits” includes the value of services such as the NHS and schools."),
    # ------------------------------------------------------------ life: work
    "recession-jobs": dict(
        topic="work", years=range(2008, 2014),
        question="What happened to jobs after the 2008 recession?",
        source="explain-ons-2008-recession", publisher="Office for National Statistics",
        title="The 2008 recession 10 years on", date="30 April 2018",
        quote=["As the economy got smaller, lots of people lost their jobs and employers stopped hiring. By the end of 2011, almost 2.7 million people were looking for work. The quarterly unemployment rate reached 8.4%, the highest rate since 1995."]),
    "lfs-quality": dict(
        topic="work", years=range(2023, 2026),
        question="How reliable are the latest employment figures?",
        source="explain-ons-lmo-latest", publisher="Office for National Statistics",
        title="Labour market overview, UK: October 2026", date="20 October 2026",
        quote=["As part of work to address quality concerns with the LFS, response levels and rates have shown clear improvement, with responses now close to their pre-coronavirus pandemic level.",
               "Estimates from January to March 2025 include the full effect of the improvements in LFS data collection and sampling methods introduced from January 2024 onwards."],
        gloss="The LFS is the Labour Force Survey, the source of the employment rates on this site."),
    # ------------------------------------------------------------ life: earnings
    "recession-pay": dict(
        topic="earnings", years=range(2008, 2018),
        question="Why did pay fall behind prices after 2008?",
        source="explain-ons-2008-recession", publisher="Office for National Statistics",
        title="The 2008 recession 10 years on", date="30 April 2018",
        quote=["Earnings have lagged behind prices for most of the decade since the start of the recession. In the public sector, a pay freeze (from 2011) and pay cap (from 2013) kept wage rises below inflation, while in the private sector wage growth was also slow."]),
    "pandemic-pay": dict(
        topic="earnings", years=range(2020, 2023),
        question="Can pay in 2020 and 2021 be compared with other years?",
        source="explain-ons-ashe-2022", publisher="Office for National Statistics",
        title="Employee earnings in the UK: 2022", date="26 October 2022",
        quote=["Over the coronavirus pandemic period, earnings estimates were affected by changes in composition of the workforce and the impact of the Coronavirus Job Retention Scheme (furlough) making interpretation difficult; also data collection disruption and lower response rates mean that, for 2020 and 2021, data were subject to more uncertainty and should be treated with caution; we would encourage users to focus on long-term trends rather than year-on-year changes."]),
    "pay-2022": dict(
        topic="earnings", years=(2022,),
        question="What happened to pay after inflation in 2022?",
        source="explain-ons-ashe-2022", publisher="Office for National Statistics",
        title="Employee earnings in the UK: 2022", date="26 October 2022",
        quote=["Median weekly pay for full-time employees was £640 in April 2022, which is a 5.0% increase over the £610 in 2021. In real terms (that is, adjusted for inflation) in April 2022, median weekly pay for full-time employees fell by 2.6% on the year."]),
    # ------------------------------------------------------------ life: housing
    "tenure-trend": dict(
        topic="housing", years=(),
        question="How have owning and renting changed over the longer run?",
        source="explain-ehs-2024-25-ch1", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 1: profile of households and dwellings", date="9 July 2026",
        quote=["Ownership rates were highest in 2003 at 71% of households but steadily declined post financial crisis in the early 2010’s to a low point in 2013-14 (63%).",
               "Throughout the 1980s and 1990s, the proportion of private rented households was relatively steady at between 9% to 11%. While the sector has doubled in size since the early 2000s, the rate has remained around 19% or 20% since 2013-14."]),
    "outright-owners": dict(
        topic="housing", years=(2024,),
        question="Why do more people now own their home outright?",
        source="explain-ehs-2024-25-ch1", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 1: profile of households and dwellings", date="9 July 2026",
        quote=["The increase in the number and proportion of outright owners is at least partly explained by population ageing, with large numbers of people reaching retirement age, paying off their mortgages and becoming outright owners"]),
    "long-mortgages": dict(
        topic="housing", years=(2024,),
        question="How are first-time buyers paying for their homes?",
        source="explain-ehs-2024-25-ch2", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 2: housing costs and affordability", date="9 July 2026",
        quote=["Compared to five years ago in 2019-20, the proportion of first time buyers with a mortgage of 30 years or more has increased significantly (from 47% in 2019-20 to 62% in 2024-25)"],
        gloss="First-time buyers here are households that bought their first home in the three years before the survey."),
    "rent-affordability": dict(
        topic="housing", years=(2023,),
        question="How much of their income do lower-income renters spend on rent?",
        source="explain-ehs-2023-24-rented-report", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2023 to 2024: rented sectors", date="17 July 2025",
        quote=["On average, 71% of private renters in the lowest two income quintiles spent more than 30% of their gross household income on rent, compared to 33% of mortgagors and 42% of social renters."],
        gloss="“The lowest two income quintiles” means the 40% of households with the lowest incomes. Mortgagors are people buying their home with a mortgage."),
    # ------------------------------------------------------------ life: holidays
    "pandemic-travel": dict(
        topic="holidays", years=(2020, 2021),
        question="What happened to travel abroad in 2020 and 2021?",
        source="explain-ons-travel-2021", publisher="Office for National Statistics",
        title="Travel trends: 2021", date="15 June 2022",
        quote=["Travel and tourism statistics are usually based on the results of the International Passenger Survey (IPS), but the survey was suspended on 16 March 2020 because of the coronavirus (COVID-19) pandemic. No IPS data were collected from this date until the survey restarted on 18 January 2021.",
               "UK residents made 19.1 million visits abroad in 2021, which was 20% less than the previous year and was because of the continued travel restrictions."]),
    "travel-2022": dict(
        topic="holidays", years=(2022,),
        question="Did holidays go back to normal in 2022?",
        source="explain-ons-travel-2022", publisher="Office for National Statistics",
        title="Travel trends: 2022", date="26 May 2023",
        quote=["The most frequent reason for visits was for holidays, both for UK residents visiting abroad and overseas residents visiting the UK; this has reverted to a more traditional reason after the coronavirus pandemic, when the most common reason for travel was to see friends and relatives."]),
    "travel-method-2024": dict(
        topic="holidays", years=(2024, 2025),
        question="Why can't 2024 be compared directly with earlier years?",
        source="explain-ons-travel-2024", publisher="Office for National Statistics",
        title="Travel trends: 2024", date="26 August 2025",
        quote=["Annual 2024 estimates consist of Quarter 1 (Jan to Mar) and Quarter 2 (Apr to June) 2024 data collected and produced under our previous International Passenger Survey (IPS) design, and Quarter 3 (July to Sept) and Quarter 4 (Oct to Dec) 2024 data collected and produced under our new design; there may be differences between these two halves and this affects how the estimates can be used."]),
    # ------------------------------------------------------------ life: schools
    "infant-limit": dict(
        topic="schools", years=range(2008, 2026),
        question="Is there a legal limit on class sizes?",
        source="dfe-spc-page", publisher="Department for Education",
        title="Schools, pupils and their characteristics: academic year 2025/26", date="4 June 2026",
        quote=["Large Classes - An infant class is described as ‘large’ when it exceeds the statutory limit of 30 pupils. There are no formal policy restrictions on any other class sizes."],
        gloss="Infant classes are reception, year 1 and year 2. The averages on this site cover all primary or all secondary classes, so they say nothing about the limit on their own."),
}

_text_cache = {}

QUOTE_MARKS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " ", "–": "-", "—": "-"})


def norm(s):
    """Collapse whitespace and typographic quotes and dashes so a quote can be matched in page text."""
    return re.sub(r"\s+", " ", s.translate(QUOTE_MARKS)).strip()


def page_text(path):
    """Visible text of a fetched HTML page, normalised."""
    if path not in _text_cache:
        raw = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
        _text_cache[path] = norm(_html.unescape(raw))
    return _text_cache[path]


def missing_quotes(sources):
    """List every quoted passage that cannot be found in its source file."""
    problems = []
    for key, e in EXPLANATIONS.items():
        s = sources.get(e["source"])
        if not s:
            problems.append(f"explanation {key}: source {e['source']} is not in the source registry")
            continue
        text = page_text(s["file"])
        for q in e["quote"]:
            if norm(q) not in text:
                problems.append(f"explanation {key}: quote not found in {s['file']}: {q[:80]!r}")
    return problems


def box(key, sources, up="", heading=None):
    """An attributed quote with its source. heading: an <h3>/<h4> level, or None for a bold question line."""
    e = EXPLANATIONS[key]
    s = sources[e["source"]]
    q = " … ".join(esc(p) for p in e["quote"])
    title = esc(e["question"])
    head = f'<{heading} class="q">{title}</{heading}>' if heading else f'<p class="q"><strong>{title}</strong></p>'
    return f'''<aside class="explain" aria-label="{esc(e['publisher'])} explanation">
{head}
<p class="who">In the words of the {esc(e['publisher'])}:</p>
<blockquote cite="{esc(s['page'])}"><p>“{q}”</p></blockquote>
{f'<p class="small">{esc(e["gloss"])}</p>' if e.get("gloss") else ""}
<p class="src">Quoted word for word from <a href="{esc(s['page'])}">{esc(e['title'])}</a> ({esc(e['date'])}). {esc(e.get('note', 'Figures inside the quote are as the publisher gave them at the time and may since have been revised.'))} <a href="{up}methods.html#src-{esc(e['source'])}">Source record</a>.</p>
</aside>'''


def for_year(topic, year, sources, up=""):
    """Quotes that apply to one topic in one year, for the year pages."""
    return "".join(box(k, sources, up) for k, e in EXPLANATIONS.items() if e.get("topic") == topic and year in e.get("years", ()))


def for_topic(topic, sources, up=""):
    """Every quote for a topic, folded away so the topic stays short on a phone."""
    keys = [k for k, e in EXPLANATIONS.items() if e.get("topic") == topic]
    if not keys:
        return ""
    return (f'<details class="explain-all"><summary>What official bodies say about these figures ({len(keys)})</summary>'
            + "".join(box(k, sources, up) for k in keys) + "</details>")
