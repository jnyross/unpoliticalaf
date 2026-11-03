"""Plain-English glossary, and links from terms on other pages to it.

Each term is explained once on glossary.html. On every other page, the first
time a term appears in ordinary text it becomes a link to its explanation, so
a newcomer can look a word up where they meet it. Headings, existing links,
figures, tables, charts and summaries are never changed.
"""
import re

from .html import page, esc, jump

# (group id, group heading, terms). Each term: (anchor, name, explanation html, words that link to it).
# Explanations describe how the word is used on this site and by the official sources it uses.
GROUPS = [
    ("public-money", "Public money", [
        ("public-sector", "Public sector",
         "Central government, the devolved governments in Scotland, Wales and Northern Ireland, local councils and public corporations, counted together.",
         ["public sector"]),
        ("financial-year", "Financial year",
         "The government's accounting year, from 1 April to 31 March. “2025-26” means April 2025 to March 2026.",
         ["financial year"]),
        ("tax-year", "Tax year",
         "The year used for Income Tax, from 6 April to 5 April. HM Revenue and Customs writes it as “2023 to 2024”.",
         ["tax year"]),
        ("tme", "Total managed expenditure",
         "HM Treasury's name for all spending by the public sector in a year, including accounting adjustments that are not split between areas.",
         ["total managed expenditure"]),
        ("cofog", "Spending areas (COFOG)",
         "The international Classification of the Functions of Government, used to group spending by what it is for, such as health, education or defence. "
         "It groups spending by purpose, not by which department spends it.",
         ["COFOG"]),
        ("social-protection", "Social protection",
         "The spending area that covers the State Pension, other benefits and tax credits, and personal social care.",
         ["social protection"]),
        ("debt-interest", "Debt interest",
         "The interest the government pays on what it has borrowed in the past. It counts as spending, inside “general public services”.",
         ["interest on government debt", "debt interest"]),
        ("outturn", "Outturn",
         "What was actually spent or received, as opposed to a plan or a forecast. Recent outturn figures can still be revised as more information comes in.",
         ["outturn"]),
        ("forecast", "Forecast and projection",
         "An estimate of a future or not-yet-measured year, such as the Office for Budget Responsibility's forecasts of tax receipts or HM Revenue and Customs' projections. "
         "Forecasts are labelled on this site and are not measurements.",
         ["forecast", "forecasts", "projection", "projections"]),
    ]),
    ("taxes", "Taxes and borrowing", [
        ("receipts", "Receipts",
         "All the money the public sector takes in during a year: taxes plus other receipts. Borrowing is not a receipt.",
         ["receipts"]),
        ("other-receipts", "Other receipts",
         "Money the public sector receives that is not tax, such as interest and dividends it earns and the surplus of public bodies.",
         ["other receipts"]),
        ("borrowing", "Borrowing",
         "The gap between what the public sector spends in a year and what it receives. Its official name is public sector net borrowing. Each year's borrowing adds to the debt.",
         ["borrowing", "public sector net borrowing"]),
        ("debt", "Debt",
         "The total still owed from all past borrowing, less some cash and other liquid assets the government holds. Its official name is public sector net debt. "
         "Debt is a stock built up over many years; borrowing is the amount added in one year.",
         ["public sector net debt", "national debt"]),
        ("income-tax", "Income Tax",
         "A tax on earnings, pensions, savings interest, dividends and other income above a tax-free amount.",
         ["Income Tax"]),
        ("national-insurance", "National Insurance",
         "A tax on earnings paid by employees, employers and the self-employed. Contributions from employees and the self-employed build up entitlement to some benefits, including the State Pension.",
         ["National Insurance"]),
        ("vat", "VAT",
         "Value Added Tax: a tax added to the price of most goods and services. The shop or business collects it, but the cost is mostly passed on in prices.",
         ["VAT"]),
        ("corporation-tax", "Corporation Tax",
         "A tax on company profits. It is paid by companies, so the household figures on this site do not include it.",
         ["Corporation Tax"]),
        ("council-tax", "Council Tax",
         "A tax on homes in England, Scotland and Wales, set by local councils and based on the value band of the home. Northern Ireland has domestic rates instead.",
         ["Council Tax"]),
        ("direct-tax", "Direct taxes",
         "Taxes taken from income or charged on a household directly. In the household figures this means Income Tax, employee National Insurance and Council Tax.",
         ["direct taxes", "direct tax"]),
        ("indirect-tax", "Indirect taxes",
         "Taxes included in the prices of things people buy, such as VAT, fuel duty and alcohol and tobacco duties, plus some business taxes passed on in prices.",
         ["indirect taxes", "indirect tax"]),
        ("personal-allowance", "Personal Allowance",
         "The amount of income a person can have each tax year before they pay any Income Tax.",
         ["Personal Allowance"]),
        ("tax-band", "Tax band and tax rate",
         "Income Tax is charged in bands. Each rate applies only to the part of income inside its band, so someone in the higher-rate band still pays the basic rate on the income below it.",
         ["basic rate", "tax band", "tax bands"]),
        ("average-rate", "Average tax rate",
         "A person's total tax divided by their income. It is lower than the rate of their top band, because lower bands and the Personal Allowance are taxed less.",
         ["average rate"]),
        ("marginal-rate", "Marginal tax rate",
         "The share of the next pound earned that goes in tax. It is usually higher than the average rate.",
         ["marginal rate"]),
    ]),
    ("households", "People, households and income", [
        ("household", "Household",
         "One person living alone, or a group of people (not necessarily related) who live at the same address and share cooking facilities and a living room, sitting room or dining area. "
         "The household surveys used here cover private homes, not care homes, student halls or other shared institutions.",
         ["private households", "private household"]),
        ("gross-income", "Gross income",
         "Income before any tax is taken off: earnings, pensions, investment income and cash benefits such as the State Pension.",
         ["gross income", "gross household income"]),
        ("disposable-income", "Disposable income",
         "Income after direct taxes, the money a household has left to spend or save.",
         ["disposable income"]),
        ("equivalised", "Adjusted for household size",
         "To compare households of different sizes, the Office for National Statistics adjusts income for the number of adults and children in the household (“equivalisation”). "
         "A couple needs more than a single person to have the same standard of living, but not twice as much.",
         ["equivalised", "adjusted for household size"]),
        ("fifths", "Fifths (quintiles)",
         "Everyone is lined up from lowest to highest income and split into five groups with the same number of people in each. "
         "The “lowest-income fifth” is the bottom 20% of people. On this site the fifths hold equal numbers of people, not of households.",
         ["fifths", "fifth of people", "quintiles"]),
        ("top-1", "Top 1% of taxpayers",
         "If everyone who owes Income Tax were lined up by income, the top 1% are the highest-income one in every hundred. People who owe no Income Tax are not counted.",
         ["top 1%"]),
        ("retired-household", "Retired household",
         "In the Office for National Statistics household figures, a household where more than half of the income comes from people who are retired. Everyone living in it counts as “retired”.",
         ["retired households", "retired household"]),
        ("average-mean", "Average (mean)",
         "Add everyone's figures together and divide by the number of people or households. A few very large values can pull a mean up.",
         ["on average"]),
        ("median", "Median",
         "The middle value: half are above it and half below. Pay figures on this site use the median because very high earners pull the mean up.",
         ["median"]),
    ]),
    ("change", "Measuring change", [
        ("cash-terms", "Cash terms",
         "Money as it was at the time, not adjusted for rising prices. £100 in 2008 bought more than £100 does today.",
         ["cash terms", "cash amounts"]),
        ("real-terms", "After inflation (real terms)",
         "Money adjusted for changes in prices, so amounts from different years can be compared. Each figure says which year's prices it is in.",
         ["after inflation", "real terms", "adjusting for inflation", "adjusting for rising prices"]),
        ("inflation", "Inflation",
         "The rate at which prices rise over time. As prices rise, the same amount of money buys less.",
         ["inflation"]),
        ("cpih", "CPIH",
         "The Consumer Prices Index including owner occupiers' housing costs: the Office for National Statistics' main measure of how prices paid by households change. "
         "This site uses it to adjust pay and housing costs for inflation.",
         ["CPIH"]),
        ("gdp", "GDP",
         "Gross domestic product: the total value of everything produced in the UK economy in a year. Showing spending or tax as a share of GDP compares them with the size of the economy.",
         ["GDP"]),
        ("tax-burden", "“Tax burden”",
         "A name often used in news and politics for tax revenue as a share of GDP. It compares all taxes, paid by people and businesses, with the size of the whole economy. "
         "This site does not use the name itself, but shows the same kind of figure on the <a href=\"taxes.html#history\">taxes page</a>. "
         "It is not what any one person or household pays: when this share goes up, it does not mean everyone pays more, and when it goes down, it does not mean everyone pays less. "
         "The Office for Budget Responsibility publishes its own version, which counts slightly different items from the tax totals on this site, so the two can differ by about one percentage point. "
         "For what households pay, see <a href=\"household-tax.html\">tax and income</a>.",
         ["tax burden"]),
        ("gdp-deflator", "GDP deflator",
         "A measure of price changes across the whole economy, used by HM Treasury to put public spending into today's prices.",
         ["GDP deflator"]),
        ("percentage-points", "Percentage points",
         "The difference between two percentages. A rise from 20% to 25% is 5 percentage points, which is also a 25% increase. This site shows changes in shares in percentage points.",
         ["percentage points", "percentage point"]),
        ("survey-estimate", "Survey estimate",
         "A figure worked out from a sample of people rather than everyone. It has a margin of error, so small differences between years or groups may not be real.",
         ["survey estimates", "survey estimate", "estimated from a survey"]),
        ("margin-of-error", "Margin of error",
         "How far a survey estimate could be from the true figure just because of who happened to be in the sample. This site shows 95% margins, written as ±: "
         "about 19 times in 20, the range from the estimate minus the margin to the estimate plus the margin contains the true value. "
         "It does not cover other problems, such as people declining to take part. See <a href=\"uncertainty.html\">how sure the figures are</a>.",
         ["margin of error", "margins of error", "confidence interval", "confidence intervals"]),
        ("coefficient-of-variation", "Coefficient of variation",
         "A survey estimate's standard error as a percentage of the estimate. The smaller it is, the more precise the estimate. The margin of error is about 1.96 times the standard error.",
         ["coefficient of variation", "coefficients of variation"]),
        ("sampling-noise", "Sampling noise",
         "Differences between survey figures that come only from asking different samples of people, not from a real change.",
         ["sampling noise", "sampling error"]),
        ("definition-break", "Definition change (break in the series)",
         "When a source changes how it measures or groups something, figures before and after the change are not directly comparable. "
         "This site shows these breaks and does not calculate changes across them.",
         ["definition changed", "not comparable", "not directly comparable"]),
        ("not-cause", "Change is not cause",
         "Two things changing at the same time does not show that one caused the other. This site shows what changed, not why.",
         ["change is not cause"]),
        ("illustration", "Illustration",
         "A made-up example used to show how a rule works. It is not a measured statistic and does not describe a typical person or household.",
         ["illustration, not a statistic"]),
    ]),
    ("life", "Everyday life", [
        ("employment-rate", "Employment rate",
         "The share of people in an age group, here 16 to 64, who did at least one hour of paid work in the survey week or had a job they were temporarily away from. Part-time work counts.",
         ["employment rate"]),
        ("soc", "Job types (SOC)",
         "The Standard Occupational Classification, used to group jobs into types such as managers or caring and leisure work. It was revised in 2021 (SOC2010 to SOC2020).",
         ["SOC2010", "SOC2020"]),
        ("tenure", "Tenure",
         "Whether a household owns its home (outright or with a mortgage), rents from a private landlord, or rents from a council or housing association (social renting).",
         ["tenure"]),
        ("owner-occupier", "Owner occupiers",
         "Households that own the home they live in, either outright or with a mortgage.",
         ["owner occupiers", "owner occupier"]),
        ("social-renting", "Social renting",
         "Renting from a local council or a housing association, usually at below-market rents.",
         ["social renters", "social renting"]),
        ("bedroom-standard", "Overcrowding (bedroom standard)",
         "A household is overcrowded if it has fewer bedrooms than the bedroom standard says its members need, based on their ages, sexes and relationships.",
         ["bedroom standard", "overcrowded", "overcrowding"]),
        ("class-size", "Class size",
         "The number of pupils in a class taught by one teacher, from the school census each January. Primary and secondary schools are shown separately, for England.",
         ["class size", "class sizes"]),
    ]),
]

TERMS = {anchor: (name, words) for _, _, terms in GROUPS for anchor, name, _, words in terms}


def glossary_page():
    body = ["<h1>What do these words mean?</h1>",
            '<div class="answer"><p class="lede">Plain-English explanations of the words used on this site.</p>'
            "<p>Words in the text of other pages that are explained here are underlined with dots. Tap one to jump to its explanation, then use your browser's back button to return.</p></div>"]
    # A long page on a phone: let readers go straight to a group or a word.
    every = sorted(((a, n) for _, _, terms in GROUPS for a, n, _, _ in terms), key=lambda t: _sort_key(t[1]))
    az = ('<details class="az" id="a-to-z"><summary>Find a word: all ' + str(len(every)) + ' words, A to Z</summary><ul class="az">'
          + "".join(f'<li><a href="#{a}">{esc(n)}</a></li>' for a, n in every) + "</ul></details>")
    body.append(jump("Jump to", [(f"#{gid}", heading) for gid, heading, _ in GROUPS]).replace('<p>Jump to:</p>', az + '<p>Or jump to a group:</p>', 1))
    for gid, heading, terms in GROUPS:
        body.append(f'<h2 id="{gid}">{esc(heading)}</h2>\n<dl class="glossary">')
        for anchor, name, text, _ in terms:
            body.append(f'<dt id="{anchor}">{esc(name)}</dt>\n<dd>{text}</dd>')
        body.append("</dl>")
        body.append('<p class="totop"><a href="#a-to-z">Find another word</a></p>')
    return page("glossary.html", "What do these words mean?", "\n".join(body),
                "Plain-English explanations of the words used on Unpolitical: tax, spending, households, inflation and more.", contents=False)


def _sort_key(name):
    """Alphabetical, ignoring quotation marks and case."""
    return re.sub(r"^[^\w]+", "", name).lower()


# ------------------------------------------------------------------ linking

# Tags whose text is never turned into a glossary link.
SKIP = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "data", "summary", "caption", "table", "svg", "script", "style",
        "nav", "header", "footer", "label", "select", "option", "button", "dt", "figcaption", "span", "strong", "em", "abbr"}
# Only text directly inside these tags is linked.
LINKABLE = {"p", "li", "dd"}


def _patterns():
    pats = []
    for anchor, (_, words) in TERMS.items():
        for w in words:
            # Proper names and abbreviations must match case; ordinary words need not.
            flags = 0 if any(c.isupper() for c in w) else re.I
            pats.append((len(w), anchor, re.compile(r"(?<![\w%-])" + re.escape(w) + r"(?![\w-])", flags)))
    pats.sort(key=lambda p: -p[0])  # longer phrases first, so "gross household income" wins over "gross income"
    return [(a, p) for _, a, p in pats]


PATTERNS = _patterns()
TOKEN = re.compile(r"(<!--.*?-->|<[^>]+>)", re.S)
TAGNAME = re.compile(r"<\s*(/)?\s*([a-zA-Z0-9]+)")
VOID = {"br", "img", "input", "meta", "link", "hr", "wbr", "source", "col", "area", "base", "embed", "param", "track"}


def link_terms(html, path, limit=12):
    """Link the first use of each glossary term in a page's main text to its explanation.

    At most `limit` links per page, so long pages are not covered in underlines.
    """
    if path == "glossary.html":
        return html
    start, end = html.find('<main id="main"'), html.find("</main>")
    if start < 0 or end < 0:
        return html
    up = "../" * path.count("/")
    head, main, tail = html[:start], html[start:end], html[end:]
    done, out, stack = set(), [], []
    for part in TOKEN.split(main):
        if not part:
            continue
        if part.startswith("<"):
            out.append(part)
            m = TAGNAME.match(part)
            if not m or part.startswith("<!--"):
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if tag in VOID or part.endswith("/>"):
                continue
            if closing:
                if tag in (t for t, _ in stack):
                    while stack and stack.pop()[0] != tag:
                        pass
            else:
                # Text hidden from screen readers must not hold links, so it is skipped too.
                stack.append((tag, bool(re.search(r'aria-hidden=["\']?true', part))))
            continue
        if (len(done) >= limit or not stack or stack[-1][0] not in LINKABLE
                or any(t in SKIP or hidden for t, hidden in stack)):
            out.append(part)
            continue
        out.append(_link_text(part, done, up, limit))
    return head + "".join(out) + tail


def _link_text(text, done, up, limit):
    taken = []  # (start, end, anchor) already linked in this piece of text
    for anchor, pat in PATTERNS:
        if anchor in done or len(done) >= limit:
            continue
        for m in pat.finditer(text):
            if any(m.start() < e and s < m.end() for s, e, _ in taken):
                continue
            taken.append((m.start(), m.end(), anchor))
            done.add(anchor)
            break
    if not taken:
        return text
    taken.sort()
    res, pos = [], 0
    for s, e, anchor in taken:
        res.append(text[pos:s])
        res.append(f'<a class="term" href="{up}glossary.html#{anchor}">{text[s:e]}</a>')
        pos = e
    res.append(text[pos:])
    return "".join(res)
