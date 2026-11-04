"""Did Labour keep its 2024 manifesto? A sourced tracker of its public-money and everyday-cost pledges.

Each pledge is quoted from the manifesto, then what has happened is set out with dates and the official
source, then a rating from fixed definitions. Where the wording allows more than one reading, every reading
is shown with its own result. The text is written by hand because the pledges are wording, not series.
"""
from .html import page

CHECKED = "4 November 2026"

RATINGS = [
    ("Kept", "The pledge has been carried out as worded."),
    ("Kept so far", "The pledge runs for longer than the evidence so far, and what has happened is in line with it."),
    ("Partly kept", "Met on one reasonable reading of the wording and not on another, or met for only part of what the pledge covers."),
    ("Not kept", "The evidence shows the plain wording of the pledge has been broken."),
    ("Not yet testable", "The deadline has not come, or no official measure exists yet. We say how things look so far."),
]

PLEDGES = [
    ("working-people", "Will not increase taxes on working people", "Not kept on the plain wording; readings differ"),
    ("national-insurance", "Will not increase National Insurance", "Partly kept; readings differ"),
    ("income-tax", "Will not increase the basic, higher or additional rates of Income Tax", "Partly kept; readings differ"),
    ("vat-rate", "Will not increase VAT", "Kept so far"),
    ("private-schools", "Will end the VAT exemption and business rates relief for private schools", "Kept"),
    ("fiscal-rules", "Will balance the current budget and make debt fall as a share of the economy", "Not yet testable; on course in the latest forecast"),
    ("defence", "Will set out the path to spending 2.5% of GDP on defence", "Kept so far; readings differ"),
    ("housing", "Will build 1.5 million new homes over the next parliament", "Not yet testable; behind the pace needed so far"),
    ("nhs", "Will meet the 18-week standard and deliver two million more NHS operations, scans and appointments a year", "Not yet testable; below the 92% standard so far"),
    ("warm-homes", "Will upgrade five million homes to cut bills", "Not yet testable"),
]


def _summary_table():
    # A plain list, not a table: reading pages need a CSV download beside every table, and this is a list of ratings.
    rows = "".join(
        f'<li><a href="#{anchor}">{text}</a>: <strong>{rating}</strong></li>'
        for anchor, text, rating in PLEDGES)
    return f'<p><strong>Ten pledges on public money and everyday costs, rated {CHECKED}</strong></p><ul class="ratings">{rows}</ul>'


def _ratings():
    items = "".join(f"<dt>{name}</dt><dd>{meaning}</dd>" for name, meaning in RATINGS)
    return f"<dl>{items}</dl>"


BODY = f"""
<h1>Did Labour keep its 2024 manifesto?</h1>
<p>Partly, and most of it cannot be judged yet. We checked ten pledges on public money and everyday costs from Labour’s 2024 manifesto, using budgets, laws and official figures published up to 15 October 2026. Three are kept: one is complete and two are on track so far. Two are partly kept, because the wording allows more than one reading. One is not kept on its plain wording. Four cannot be tested until their deadlines or measures arrive.</p>
<p>The table lists each pledge with its rating. Tap a pledge to see the quote, what has happened and the sources. Last checked {CHECKED}.</p>
{_summary_table()}

<h2 id="who-governed">Who has governed</h2>
<p>Labour has governed since July 2024. Keir Starmer led the government until 20 July 2026, when Andy Burnham became prime minister (<a href="https://www.gov.uk/government/speeches/andy-burnhams-first-speech-as-prime-minister-20-july-2026">GOV.UK, speech of 20 July 2026</a>). The pledges belong to the party, so each one is tested across both leaders. As of this check, the latest Budget we found is Budget 2025, on 26 November 2025.</p>

<h2 id="ratings">How we rated them</h2>
{_ratings()}
<p>Where a pledge’s wording allows more than one reading, we show each reading and its result. We do not choose one reading as the correct one. Pledges with no measure to test, such as “We will bring down the cost of energy”, are not rated.</p>

<h2 id="working-people">Will not increase taxes on working people</h2>
<p><strong>Not kept on the plain wording.</strong> The government reads the pledge as covering tax rates only.</p>
<blockquote>“Labour will not increase taxes on working people, which is why we will not increase National Insurance, the basic, higher, or additional rates of Income Tax, or VAT.” <cite>Labour Party manifesto 2024, page 21.</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>In the Budget of 30 October 2024 the chancellor said extending the threshold freeze “would hurt working people. It would take more money out of their payslips.” She also said: “I am keeping every single promise on tax that I made in our manifesto, so there will be no extension of the freeze in income tax and national insurance thresholds.” (quoted by Full Fact, 26 November 2025).</li>
<li>Budget 2025, on 26 November 2025, extended the freeze on income tax and National Insurance thresholds for three more years, to April 2031. It had been due to end in April 2028 (<a href="https://www.gov.uk/government/speeches/budget-2025-speech">Budget 2025 speech, GOV.UK</a>).</li>
<li>The chancellor said the extension “will mean that working people pay a bit more” (quoted by Full Fact, 28 November 2025).</li>
</ul>
<h3>Why it is rated this way</h3>
<p>A frozen threshold does not change a tax rate. But as wages rise, more of each pay packet falls above the threshold, so people pay more tax without any rate change. This is called fiscal drag. The government says the pledge covers rates. Full Fact rates the pledge “Not kept” because the freeze means working people pay more than they otherwise would. Both points are stated here, so readers can weigh them.</p>

<h2 id="national-insurance">Will not increase National Insurance</h2>
<p><strong>Partly kept.</strong> Readings differ.</p>
<p>The manifesto mentions National Insurance once, in the sentence quoted above. It does not say whether the pledge covers employer contributions as well as employee ones (Full Fact, 14 October 2024).</p>
<h3>Two readings</h3>
<dl>
<dt>Employee contributions only, which is the government’s reading</dt>
<dd>Kept on rates. The main employee rates of 8% and 2% have not changed. The threshold freeze still means more is paid, which some count as a breach.</dd>
<dt>All National Insurance, including employer contributions</dt>
<dd>Not kept. The October 2024 Budget raised the employer rate from 13.8% to 15% from April 2025 and lowered the secondary threshold from £9,100 to £5,000 (<a href="https://www.gov.uk/government/publications/autumn-budget-2024/autumn-budget-2024-html">Autumn Budget 2024, GOV.UK</a>). Budget 2025 extended the threshold freeze and capped the pension contributions that can be made through salary sacrifice without National Insurance. The Institute for Fiscal Studies says the freeze and the cap breach the pledge.</dd>
</dl>
<h3>What has happened</h3>
<ul>
<li>Employer National Insurance rose from April 2025, as set out above.</li>
<li>The threshold freeze now runs to April 2031.</li>
</ul>
<p>In October 2024 the business secretary said the pledge referred to “taxes on working people”, meaning employees (quoted by Full Fact, 14 October 2024). Full Fact rates the pledge “Not kept”, because the manifesto does not say which contributions it covers and the changes mean many working people pay more National Insurance.</p>

<h2 id="income-tax">Will not increase the basic, higher or additional rates of Income Tax</h2>
<p><strong>Partly kept.</strong> Readings differ.</p>
<p>The manifesto names the basic, higher and additional rates. It does not mention savings, dividend or property income, or the thresholds at which the rates apply.</p>
<h3>Two readings</h3>
<dl>
<dt>The basic, higher and additional rates on earnings</dt>
<dd>Kept. The basic, higher and additional rates on earnings are still 20%, 40% and 45%, and they have not changed since Labour took office.</dd>
<dt>Every rate of income tax, including on savings, dividends and property</dt>
<dd>Not kept. Budget 2025 raised the dividend rates by 2 percentage points from April 2026, to 10.75% (ordinary) and 35.75% (upper). It raises the savings and property rates from April 2027 to 22% (basic), 42% (higher) and 47% (additional). HMRC says the aim is “to ensure income from assets is taxed more fairly” (<a href="https://www.gov.uk/government/publications/income-tax-changes-to-tax-rates-for-property-savings-and-dividend-income/income-tax-changes-to-tax-rates-for-property-savings-and-dividend-income">HMRC policy paper, Budget 2025</a>).</dd>
</dl>
<h3>What has happened</h3>
<ul>
<li>Dividend rates rose from April 2026, and savings and property rates rise from April 2027.</li>
<li>The threshold freeze, described above, also applies to income tax.</li>
</ul>
<p>Full Fact rates this pledge “Unclear or disputed”, because its scope is unclear: the rate changes apply to other income, while the threshold freeze affects earnings.</p>

<h2 id="vat-rate">Will not increase VAT</h2>
<p><strong>Kept so far.</strong> The pledge runs for the whole parliament, so the rating can change.</p>
<p>The standard rate of VAT is still 20%. Budget 2024 and Budget 2025 changed some reliefs and the rules for private school fees, but not the standard rate (Full Fact, 28 November 2025). The rate is set out on <a href="https://www.gov.uk/how-vat-works/how-much-vat-you-must-charge">GOV.UK</a>.</p>

<h2 id="private-schools">Will end the VAT exemption and business rates relief for private schools</h2>
<p><strong>Kept.</strong></p>
<blockquote>“Labour will end the VAT exemption and business rates relief for private schools to invest in our state schools.” <cite>Labour Party manifesto 2024, page 82.</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>VAT at the standard rate of 20% has applied to private school fees since 1 January 2025.</li>
<li>Charitable business rates relief for private schools in England ended from 1 April 2025. The law was passed on 3 April 2025 and backdated.</li>
<li>Some schools that are wholly or mainly for children with Education, Health and Care plans may keep charitable relief, the government has said (Full Fact, 28 May 2026).</li>
</ul>

<h2 id="fiscal-rules">Will balance the current budget and make debt fall as a share of the economy</h2>
<p><strong>Not yet testable.</strong> On course in the latest forecast.</p>
<blockquote>“Our fiscal rules are non-negotiable and will apply to every decision taken by a Labour government. This means that the current budget must move into balance, so that day-to-day costs are met by revenues and debt must be falling as a share of the economy by the fifth year of the forecast.” <cite>Labour Party manifesto 2024, page 126.</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>The test falls in 2029-30. The OBR’s March 2026 forecast has the current budget in surplus by 0.7% of GDP in 2029-30 (<a href="https://assets.publishing.service.gov.uk/media/69a6d7b62e1f4fbda4252208/economic-and-fiscal-outlook-march-2026-web-accessible.pdf">OBR, Economic and fiscal outlook, March 2026</a>).</li>
<li>The government’s debt measure, public sector net financial liabilities, is forecast at 82.4% of GDP in 2025-26. It peaks at 82.9% in 2027-28 and falls to 81.1% by 2030-31.</li>
<li>At Budget 2025 the OBR put the chancellor’s headroom against the rules at £21.7 billion.</li>
<li>The government now assesses the rules once a year, at Budgets, so the March 2026 forecast gives no verdict on them.</li>
</ul>
<h3>Readings</h3>
<p>The manifesto does not name a debt measure. In October 2024 the government chose public sector net financial liabilities, which includes the Bank of England and public sector pensions. The measure used before was public sector net debt, which is narrower. This page uses the government’s measure. The OBR describes “significant risks” around its central forecast, with outcomes both above and below it, so the forecast is not a result.</p>

<h2 id="defence">Will set out the path to spending 2.5% of GDP on defence</h2>
<p><strong>Kept so far.</strong> Readings differ.</p>
<blockquote>“...Labour will conduct a Strategic Defence Review within our first year in government, and we will set out the path to spending 2.5 per cent of GDP on defence.” <cite>Labour Party manifesto 2024, “Strong foundations” (pages 14 to 22).</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>On 25 February 2025 the prime minister set out 2.5% of GDP on defence from April 2027 (<a href="https://www.gov.uk/government/speeches/prime-ministers-oral-statement-to-the-house-of-commons-25-february-2025">GOV.UK, statement of 25 February 2025</a>).</li>
<li>The government widened the definition of defence spending to include some intelligence and security spending. On that wider definition the total is 2.6% of GDP in 2027.</li>
<li>NATO’s 2026 estimate for the UK is 2.56% of GDP, up from 2.32% in 2025 (<a href="https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2026-en.pdf">NATO defence expenditure estimates, 2026</a>). NATO’s figures for the current year are estimates and can be revised.</li>
</ul>
<h3>Readings</h3>
<p>Some critics call the wider definition “creative accounting”. Full Fact notes that Labour itself criticised a similar change a decade earlier. The Ministry of Defence has confirmed that its 2026-27 figures include security and intelligence spending (Full Fact, 12 October 2026). Whether that counts as meeting the pledge is the reading that differs.</p>

<h2 id="housing">Will build 1.5 million new homes over the next parliament</h2>
<p><strong>Not yet testable.</strong> Behind the pace needed so far.</p>
<blockquote>“Labour will get Britain building again, creating jobs across England, with 1.5 million new homes over the next parliament.” <cite>Labour Party manifesto 2024, page 36.</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>Official net additional dwellings in England were 221,410 in 2023-24 and 208,600 in 2024-25 (<a href="https://www.gov.uk/government/statistics/housing-supply-net-additional-dwellings-england-2024-to-2025/housing-supply-net-additional-dwellings-england-2024-to-2025">GOV.UK, November 2025</a>).</li>
<li>The government estimates 437,900 net additional homes in England between 9 July 2024 and 20 September 2026: 29% of the 1.5 million target. This estimate uses new energy performance certificates, so it is not the official count (<a href="https://www.gov.uk/government/statistics/housing-supply-indicators-of-new-supply-england-april-to-june-2026/housing-supply-indicators-of-new-supply-england-april-to-june-2026">GOV.UK, housing supply indicators, April to June 2026</a>).</li>
<li>On 13 September 2026 the housing secretary called the target a “stretch target” and said there was a “slim chance” of meeting it (quoted by Full Fact, 9 October 2026).</li>
</ul>
<h3>Readings</h3>
<p>The government says the target counts net additional dwellings in England, not starts. The next general election must be held by August 2029, so the parliament is not yet over. Full Fact rates the pledge “appears off track”.</p>

<h2 id="nhs">Will meet the 18-week standard and deliver two million more NHS operations, scans and appointments a year</h2>
<p><strong>Not yet testable.</strong> Below the 92% standard so far.</p>
<blockquote>“...patients should expect to wait no longer than 18 weeks from referral for consultant-led treatment of non-urgent health conditions. This standard was achieved with the last Labour government and will be again under the next.” <cite>Labour Party manifesto 2024, “Build an NHS fit for the future” (pages 91 to 104).</cite> The same section says: “we will deliver an extra two million NHS operations, scans, and appointments every year; that is 40,000 more appointments every week.”</blockquote>
<h3>What has happened</h3>
<ul>
<li>In August 2026, 65.2% of the 7.4 million waiting pathways for consultant-led treatment had waited up to 18 weeks. The NHS standard is 92% (<a href="https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/10/Aug26-RTT-statistical-press-notice-PDF-389K-vjgRdG.pdf">NHS England, RTT statistical press notice, published 8 October 2026</a>). A pathway is one waiting episode, and some patients are on more than one. These figures include estimates for four trusts that did not report.</li>
<li>In August 2025 the share was 61.0%, so it has risen by 4.2 percentage points in a year.</li>
<li>The number of waiting pathways fell by 33,512 (0.5%) over the year to August 2026.</li>
<li>We did not find an official count of the two million extra operations, scans and appointments, so that part is not rated separately.</li>
</ul>
<h3>Readings</h3>
<p>The manifesto says patients should wait “no longer than 18 weeks”, which some read as applying to every patient. The NHS standard instead sets a share of patients to be treated within 18 weeks, currently 92%. The manifesto gives no date, and says the standard will be met “under the next” Labour government.</p>

<h2 id="warm-homes">Will upgrade five million homes to cut bills</h2>
<p><strong>Not yet testable.</strong></p>
<blockquote>“Labour will invest an extra £6.6 billion over the next parliament, doubling the existing planned government investment, to upgrade five million homes to cut bills for families.” <cite>Labour Party manifesto 2024, “Make Britain a clean energy superpower” (pages 47 to 60).</cite></blockquote>
<h3>What has happened</h3>
<ul>
<li>The government published the Warm Homes Plan in January 2026. It commits £15 billion of public investment over this parliament to “upgrade up to 5 million homes and lift up to a million families out of fuel poverty by 2030” (<a href="https://www.gov.uk/government/publications/warm-homes-plan/warm-homes-plan-html">GOV.UK, Warm Homes Plan</a>).</li>
<li>We did not find an official count of homes upgraded so far, so this pledge is not rated on results.</li>
</ul>
<h3>Readings</h3>
<p>The manifesto says “five million homes” and gives no date. The plan says “up to 5 million” by 2030. The two wordings differ, so the plan’s target is not a direct copy of the pledge.</p>

<h2 id="sources">Sources</h2>
<ul>
<li>Labour Party, <a href="https://labour.org.uk/wp-content/uploads/2024/06/Labour-Party-manifesto-2024.pdf">Change: Labour Party manifesto 2024</a>. Page numbers are the PDF pages.</li>
<li>Full Fact government tracker: <a href="https://fullfact.org/government-tracker/budget-fiscal-rules/">fiscal rules</a> (updated 15 October 2026); <a href="https://fullfact.org/government-tracker/defence-spending-2-5-percent-2027/">defence</a> (12 October 2026); <a href="https://fullfact.org/government-tracker/1-5-million-homes/">1.5 million homes</a> (9 October 2026); <a href="https://fullfact.org/government-tracker/vat-business-rates-private-schools/">private schools</a> (28 May 2026); <a href="https://fullfact.org/politics/government-tracker-budget-updates/">tax verdict</a> (28 November 2025); <a href="https://fullfact.org/politics/budget-2025-manifesto-impact/">Has the chancellor kept Labour’s manifesto commitments on tax?</a> (26 November 2025); <a href="https://fullfact.org/politics/labour-national-insurance-working-people/">What exactly did Labour’s manifesto say about National Insurance?</a> (14 October 2024).</li>
<li>Office for Budget Responsibility, <a href="https://assets.publishing.service.gov.uk/media/69a6d7b62e1f4fbda4252208/economic-and-fiscal-outlook-march-2026-web-accessible.pdf">Economic and fiscal outlook, March 2026</a>.</li>
<li>GOV.UK: <a href="https://www.gov.uk/government/speeches/budget-2025-speech">Budget 2025 speech</a>; <a href="https://www.gov.uk/government/publications/autumn-budget-2024/autumn-budget-2024-html">Autumn Budget 2024</a>; <a href="https://www.gov.uk/government/publications/income-tax-changes-to-tax-rates-for-property-savings-and-dividend-income/income-tax-changes-to-tax-rates-for-property-savings-and-dividend-income">HMRC, changes to tax rates for property, savings and dividend income</a>; <a href="https://www.gov.uk/government/speeches/prime-ministers-oral-statement-to-the-house-of-commons-25-february-2025">prime minister’s statement on defence, 25 February 2025</a>; <a href="https://www.gov.uk/government/publications/warm-homes-plan/warm-homes-plan-html">Warm Homes Plan</a>; <a href="https://www.gov.uk/government/statistics/housing-supply-net-additional-dwellings-england-2024-to-2025/housing-supply-net-additional-dwellings-england-2024-to-2025">net additional dwellings, England, 2024 to 2025</a>; <a href="https://www.gov.uk/government/statistics/housing-supply-indicators-of-new-supply-england-april-to-june-2026/housing-supply-indicators-of-new-supply-england-april-to-june-2026">housing supply indicators, April to June 2026</a>.</li>
<li>NHS England, <a href="https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/10/Aug26-RTT-statistical-press-notice-PDF-389K-vjgRdG.pdf">Referral to treatment waiting times, August 2026</a>.</li>
<li>NATO, <a href="https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2026-en.pdf">defence expenditure estimates, 2026</a>.</li>
</ul>
<p>Any change to a rating is dated here when it is made. If you think a rating is wrong, the sources above say what was checked.</p>
"""


def manifesto_page():
    return page(
        "manifesto.html",
        "Did Labour keep its 2024 manifesto?",
        BODY,
        "Ten public-money and everyday-cost pledges from Labour’s 2024 manifesto, each quoted, with what has happened, a rating and every reading where the wording allows more than one.",
    )
