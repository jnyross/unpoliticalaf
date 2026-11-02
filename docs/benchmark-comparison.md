# Benchmark comparison

This file records side-by-side comparisons of named benchmark pages against the
matching pages on this site. The [goal rubric](goal-rubric.md) lets a dimension
reach level 4 only with "a recorded independent review of that dimension or a
recorded side-by-side comparison with a named benchmark page". This is that
record for D1 (public money answers), D2 (life: breadth and depth) and D5
(visual design and charts), and, in [Part 2](#part-2-d3-d4-d6-d8-and-d10), for
D3 (comparing years), D4 (explanation), D6 (phone use), D8 (impartiality) and
D10 (honesty about limits), and, in [Part 3](#part-3-holidays-and-class-sizes-d2),
for holidays and class sizes (D2). It does not score anything: the next goal audit
decides what the evidence is worth.

## How this was done

- Date: 2 November 2026.
- Site version: `main` at `e907fc2` (after PR #97), built locally with
  `make build`, plus the one-sentence note on debt interest added in the same PR
  as this file.
- Benchmark pages: read on 2 November 2026 from the live web pages listed below.
  Figures quoted from them are as published on that date.
- Who did it: a Claude session that did not build the pages compared. It is the
  same kind of agent as the builders, so a strict auditor may treat this as the
  auditor's own judgement rather than independent evidence. The figure checks
  below are mechanical and can be repeated by anyone with the URLs.
- Method: for each pair, (1) compare the headline figures that both publish for
  the same year, and explain any difference; (2) list what the benchmark does
  that this site does not, and the reverse, for a newcomer on a phone.

## Pages compared

| # | Benchmark page | This site | Dimensions |
|---|---|---|---|
| 1 | OBR, [A brief guide to the public finances](https://obr.uk/forecasts-in-depth/brief-guides-and-explainers/public-finances/) (March 2026 forecast, updated 22 April 2026) | [Taxes](https://unpoliticalaf.vercel.app/taxes.html), [Spending](https://unpoliticalaf.vercel.app/spending.html) | D1, D5 |
| 2 | IFS TaxLab, [What does the government spend money on?](https://ifs.org.uk/taxlab/taxlab-key-questions/what-does-government-spend-money) (2022–23 figures) | [Spending](https://unpoliticalaf.vercel.app/spending.html) | D1, D5 |
| 3 | IFS TaxLab, [Where does the government get its money?](https://ifs.org.uk/taxlab/taxlab-key-questions/where-does-government-get-its-money) and [How have government revenues changed over time?](https://ifs.org.uk/taxlab/taxlab-key-questions/how-have-government-revenues-changed-over-time) (2023–24 forecast) | [Taxes](https://unpoliticalaf.vercel.app/taxes.html) | D1, D5 |
| 4 | ONS, [Effects of taxes and benefits on UK household income: FYE 2024](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024) (25 September 2025) | [Tax and income](https://unpoliticalaf.vercel.app/household-tax.html), [Who pays](https://unpoliticalaf.vercel.app/who-pays.html) | D1 |
| 5 | ONS, [Employee earnings in the UK: 2025](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025) (ASHE) | [Earnings](https://unpoliticalaf.vercel.app/life/earnings.html) | D2, D5 |
| 6 | ONS, [Housing affordability in England and Wales: 2025](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/bulletins/housingaffordabilityinenglandandwales/2025) | [House prices and earnings](https://unpoliticalaf.vercel.app/life/house-prices.html) | D2, D5 |
| 7 | Our World in Data, [Government Spending](https://ourworldindata.org/government-spending) topic page and its interactive charts | [Spending](https://unpoliticalaf.vercel.app/spending.html), the [life explorer](https://unpoliticalaf.vercel.app/life/index.html) | D5, D2 |

## 1. OBR brief guide against Taxes and Spending

### Figures

The OBR guide uses its March 2026 **forecast** for 2025-26. This site uses the
OBR's October 2026 databank, where 2025-26 is **outturn** (measured, still open
to revision). Small differences are therefore expected.

| 2025-26 | OBR guide (forecast) | This site (outturn) | Matches? |
|---|---|---|---|
| Public sector current receipts | £1,235bn, 40.4% of GDP | £1,231bn, 40.1% of GDP | Yes, within £4bn |
| Total managed expenditure | £1,368bn, 44.8% of GDP | £1,366bn (OBR basis), 44.5% of GDP; £1,360bn on HM Treasury's PESA basis | Yes; the site explains the two bases on the spending page |
| Borrowing (deficit) | £133bn | £134bn | Yes |
| Taxes as a share of receipts | "90 per cent" | £1,105bn of £1,231bn = 89.7% | Yes |
| Income Tax plus National Insurance | "around £535 billion" | £329bn + £204bn = £534bn | Yes |
| VAT | £181bn | £180bn | Yes |
| Public sector net debt | 94.3% of GDP, "around £2.9 trillion" | £2,917bn, 93.3% of GDP | Cash matches; the ratio is 1 point lower in outturn (GDP and debt revised since March) |
| Net debt interest | £110bn (interest paid minus interest received) | £130bn on the spending page | Different measure: HM Treasury's figure is gross. **Was unexplained; fixed in this PR** with a sentence in the spending page's limits box |

### What the OBR does that this site does not

- One short page answers income, spending, deficit and debt in order, each with
  a chart and per-household scale (£43,000 of receipts per household).
- Deficits shown back to 1900 and surpluses since 1948 ("only 10 years since
  1948"); this site's receipts and spending chart starts in 1948-49.
- Current budget, structural deficit and the fiscal targets explained.
- An international comparison (OECD) of receipts, spending, deficit and debt.

### What this site does that the OBR guide does not

- Splits money into taxes, other receipts and borrowing in three numbered
  blocks, and says plainly that borrowing is not tax and not the same as debt.
- Per-person scale with the population named, and a warning that it is not a
  tax bill.
- Every figure traces to a sheet and cell, with a full table beside each chart,
  and the page works without JavaScript.
- Spending split into the £100 of services by international purpose (COFOG),
  with 2015-16 to 2025-26 changes after inflation.

## 2. IFS TaxLab spending page against Spending

### Figures (2022-23)

| 2022-23 | IFS TaxLab | This site (PESA 2026) | Matches? |
|---|---|---|---|
| Total spending | "almost £1,200 billion", "around 45% of GDP" | £1,161bn, 44.1% of GDP | Close. IFS rounds and uses an earlier vintage; PESA 2026 includes later revisions |
| Health | £211.6bn, 18.3% of total | £212.7bn, 18.3% of total (£212.7bn ÷ £1,160.7bn) | Yes |
| Education | £105.5bn | £107.3bn | Yes, within 2% (revisions and scope) |
| Defence | £55.5bn | £55.5bn | Yes |
| Debt interest | £97.2bn **net** | £130.4bn gross | Different measure, now explained (see section 1) |

### What IFS does that this site does not

- History of total spending back to 1900-01 and of its components back to
  1955-56, with a stacked chart that switches between share of GDP, share of
  spending and £. This site's spending by area starts in 2003-04 and has three
  separate tables (cash, real, % of GDP) rather than one switch.
- Splits social security into pensioners and working-age people and children,
  and shows long-term care as its own line.
- A long view of health and defence as shares of spending.

### What this site does that IFS does not

- Latest outturn year (2025-26 against 2022-23) and per-person scale.
- Quoted official explanations of the big moves (for example why debt interest
  rose in 2022-23) and the breaks in HM Treasury's series listed in place.
- Real-terms change over ten years for each area.

## 3. IFS TaxLab revenue pages against Taxes

### Figures (2023-24)

The IFS pages still show the March 2023 **forecast** for 2023-24. This site
shows the outturn from the October 2026 OBR databank.

| 2023-24 | IFS TaxLab (forecast) | This site (outturn) | Comment |
|---|---|---|---|
| Total receipts | £1,057.6bn, 41% of GDP | £1,096.6bn | Outturn came in higher than the forecast IFS still shows |
| All taxes | £950.5bn | £976.1bn | As above |
| Income Tax | £268.0bn | £277.0bn | As above |
| National Insurance | £172.3bn | £179.1bn | As above |
| VAT | £162.2bn | £168.3bn | As above |
| Council Tax | £44.4bn | £44.5bn | Yes |
| Non-tax receipts | £107.1bn | £120.5bn | Different scope and vintage |

No figure on this site disagrees with an IFS figure for the same measure and
vintage. The differences are forecast against outturn.

### What IFS does that this site does not

- Revenue history from 1900 (total) and 1948-49 (by tax), with world wars
  marked; this site's tax mix starts in 1999-00 (receipts in total from 1948-49).
- A pie chart that switches between tax revenue and total revenue.
- International comparison of tax revenue.
- Per-adult scale (£17,200 per adult); this site gives per person, including
  children.

### What this site does that IFS does not

- Puts borrowing beside taxes and other receipts, so a reader sees all three
  ways spending is paid for.
- Latest outturn rather than an old forecast.
- Explains the debt/borrowing difference with the debt figure and per-person
  scale.

## 4. ONS taxes and benefits bulletin against Tax and income, and Who pays

### Figures

The site quotes the bulletin word for word: richest fifth £116,600 before taxes
and benefits, 12.2 times the poorest fifth (£9,600), falling to 3.3 times
(£85,100 and £25,700) after all taxes and benefits; and the "fiscal drag"
sentence. All match the bulletin as published on 25 September 2025. The
bulletin's own text gives no "share of gross income paid in tax" headline; the
site's 33.6% (all), 36.7% (lowest fifth) and 36.2% (highest fifth) come from
the reference tables (Table 8), which the bulletin links to.

### What ONS does that this site does not

- Shows income at each stage (original, gross, disposable, post-tax, final) by
  fifth in one range chart.
- The Gini coefficient over time (FYE 1995 to FYE 2024) and the share of people
  in households that receive more than they pay (53.3%).
- Downloadable data behind every chart.

### What this site does that ONS does not

- Answers the question a newcomer asks ("how much of household income goes on
  tax?") as one headline with direct and indirect taxes split.
- A section, "Three numbers that are easy to mix up", that separates household
  averages, personal tax rates and shares of total revenue. The ONS bulletin does
  not discuss personal tax rates at all.
- History back to 1977 with the ONS method change marked.
- Puts HMRC's Income Tax by person beside the ONS household view and says why
  they differ.

## 5. ONS earnings bulletin against Earnings

### Figures

| April 2025 | ONS ASHE 2025 | This site | Matches? |
|---|---|---|---|
| Median weekly pay, full-time employees | £766.60 | £767 | Yes (rounded) |
| Median annual pay, full-time employees | £39,039 | £39,059 on the house prices page (England and Wales by workplace, a different geography) | Consistent; different geography |

### What ONS does that this site does not

- Earnings by occupation with a search box, and a map of every local authority.
- Part-time pay and hourly pay alongside full-time weekly pay.

### What this site does that ONS does not

- Pay after inflation back to 2002, with the 2008 comparison in the first
  sentence ("about the same as in April 2008"). The ONS bulletin compares with
  the previous year only.
- Margins of error stated beside the headline.
- Pay spread (low and high earners), nations and regions on one page.

## 6. ONS housing affordability bulletin against House prices and earnings

### Figures

| 2025 | ONS | This site | Matches? |
|---|---|---|---|
| England, price to earnings ratio | 7.6 | 7.63 | Yes |
| Wales | 6.0 | 5.95 | Yes |
| London | 10.6 | 10.61 | Yes |
| North East | 5.0 | 5.00 | Yes |
| Peak year | ratios "peaked in 2021" | highest 8.95 (England and Wales) in 2021 | Yes |
| Series start | 1997 | 1997 | Yes |

### What ONS does that this site does not

- Local authority figures with an interactive map and a "your area" search.
- A sentence a newcomer can feel ("a further £279,000 would be required").

### What this site does that ONS does not

- Says plainly that Scotland and Northern Ireland are not covered and why.
- Puts the ratio on the same site as pay, tenure and housing costs, with links
  between them.

## 7. Our World in Data against charts and the life explorer

### What OWID does that this site does not

- Every chart has Chart, Table, Map and Sources tabs, a download button and a
  way to change the countries shown, plus a log/linear setting.
- Charts are the first thing on the page; text explains them.
- Definitions are explained in the page body as the reader meets them.

### What this site does that OWID does not

- A table alternative beside every chart that works without JavaScript, and a
  plain-English "What the chart shows" summary under each chart.
- Breaks and gaps drawn on the chart and explained ("amber dashed line marks a
  change"); the OWID government spending page does not discuss breaks.
- One-tap tracing of any figure to its source cell.
- UK-specific depth (purposes of spending, nations and regions) that OWID's
  cross-country pages do not have.

## Summary

**Figures.** Every headline figure in the tables above either matches the
benchmark, or differs only because the benchmark shows an earlier forecast or a
different vintage. One difference was a different measure that the site did not
explain: debt interest is gross on this site and net in the OBR and IFS pages.
This PR adds that explanation to the spending page.

**Where this site is comparable with the benchmarks:**

- Separating taxes, other receipts and borrowing (D1).
- Explaining household tax shares without confusing them with personal tax
  rates or shares of revenue (D1).
- Showing breaks, gaps and margins of error (D5, and D10 outside this record).
- Life measures that ONS publishes in separate bulletins (pay after inflation,
  affordability) on linked pages (D2).

**Where the benchmarks are clearly ahead:**

1. Long history: IFS and OBR show spending and revenue back to 1900, and the
   components of spending from 1955-56; this site starts spending by area in
   2003-04 and the tax mix in 1999-00 (D1).
2. One switch between cash, real terms and share of GDP (IFS, OWID); this site
   has three separate tables (D1, D5). This is already queued as a gap.
3. Local detail: ONS maps and "your area" search for pay and house prices
   (D2, D5).
4. International comparison (OBR, IFS, OWID) (D1).
5. Downloadable data behind each chart (ONS, OWID) (D5).

These are recorded as evidence for the next goal audit, not as new tickets.

---

## Part 2: D3, D4, D6, D8 and D10

Added for ticket T31 (gap 1 of Audit 5).

### How this was done

- Date: 2 November 2026.
- Site version: `main` at `1ba40fa` (after PR #101), built locally with
  `make build` (415 pages), plus the fixes in the same PR as this section.
  Phone measurements: Chromium at 360 × 640 pixels, sections folded as a reader
  first sees them, JavaScript on; "screens" = page height ÷ 640.
- Benchmark pages: read on 2 November 2026 from the live pages listed below.
  The cloud container cannot open these sites directly, so the pages were read
  through a web-reading tool that returns their text. That tool does not render
  layout, so benchmark lengths below are word counts, not screens, and chart
  controls that only exist in a browser could not be checked.
- Who did it: a Claude session that did not build the pages compared. As in
  Part 1, a strict auditor may treat this as the auditor's own judgement rather
  than independent evidence.

### Pages compared

| # | Benchmark page | This site | Dimensions |
|---|---|---|---|
| 8 | ONS, [How life has changed in Haringey: Census 2021](https://www.ons.gov.uk/visualisations/censusareachanges/E09000014/) (19 January 2023), one of the ONS's two-census comparison articles | [2009 compared with 2023](https://unpoliticalaf.vercel.app/life/compare/2009-2023.html) (the default comparison) and the [range comparisons](https://unpoliticalaf.vercel.app/life/compare/spans/index.html) | D3, D10 |
| 9 | Our World in Data, [Employment rate, United Kingdom](https://ourworldindata.org/grapher/employment-to-population-ratio?country=~GBR) (updated 27 July 2026) | [Work](https://unpoliticalaf.vercel.app/life/work.html) and the comparison pages | D3, D10 |
| 10 | Full Fact, [What is the UK's 'tax burden' – and how much tax is paid on workers' earnings?](https://fullfact.org/economy/tax-revenue-worker-explainer/) (23 September 2026) and [Is the 'tax burden' at the highest level in 70 years?](https://fullfact.org/politics/tax-burden-70-years/) (22 July 2024) | [Taxes](https://unpoliticalaf.vercel.app/taxes.html), [Tax and income](https://unpoliticalaf.vercel.app/household-tax.html), [Glossary](https://unpoliticalaf.vercel.app/glossary.html) | D4, D8 |
| 11 | OBR, [A brief guide to the public finances](https://obr.uk/forecasts-in-depth/brief-guides-and-explainers/public-finances/) (as served on 2 November 2026) | [Taxes](https://unpoliticalaf.vercel.app/taxes.html), [Spending](https://unpoliticalaf.vercel.app/spending.html) | D6, D4 |
| 12 | ONS, [Employee earnings in the UK: 2025](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025) (ASHE bulletin) | [Earnings](https://unpoliticalaf.vercel.app/life/earnings.html) | D6, D10, D4 |

### 8–9. Comparing years (D3): ONS census comparisons and OWID against the comparison pages

**What the ONS article does.** Each section has a headline that states the
change ("The rate of home ownership in Haringey decreased by 1.6 percentage
points"), a paragraph in plain words, and a chart with the same figures for
London and England beside the local ones, so the reader can tell whether a
change is local or national. It says once which measure it uses ("The
percentage point change is also used to show the difference between the 2011
and 2021 percentages"). It warns about timing in place: "Working hours may have
been affected by the coronavirus (COVID-19) pandemic", and "Caution should be
taken when making comparisons between 2011 and 2021 because of changes in
question wording". Topics with no comparable 2011 figure are left out and the
"About the data" section says so. Every chart has PNG and CSV downloads.

**What OWID does.** The chart page names its source and gives a "Sources and
processing" section with a definition break: "data using the newer definitions
is not fully comparable with data based on the 13th ICLS". It offers the full
data and the displayed data as CSV. Its year controls could not be checked in
the text copy (see "How this was done").

**What this site does that they do not.**

- Any two years from 2008 to 2025 (153 pages) and any two three-year ranges,
  not one fixed pair. The ONS article only compares the two censuses.
- "In brief" gives the same lead figure for every topic whichever way it moved,
  then the largest changes ranked by a fixed, stated rule. The ONS article orders
  topics "automatically based on how relevant they are for each area", which
  is less transparent.
- Each "not compared" reason is given where the figure would be, with the
  nearest comparable pair linked. The ONS states exclusions once, at the end.
- Margins of error beside survey changes, with a plain sentence on whether the
  change is bigger than sampling noise. The ONS article has none.

**What they do that this site did not.**

1. **Said when a compared year was unusual.** The ONS flags the pandemic where
   the reader meets the change. This site's comparison pages did not mention
   that 2009 was in the 2008 recession, so the default comparison (2009 against
   2023) started in a recession year without saying so. The pandemic was only
   mentioned inside folded topic notes about survey methods. **Fixed in this PR**
   (see "Fixes" below).
2. A wider-area benchmark beside each change (London and England in the ONS
   article). This site shows the UK and each nation in the topic sections, but
   the "In brief" figures have no UK-wide or long-run context. Not fixed; noted
   for the next audit.
3. Per-chart CSV downloads (ONS and OWID). Already queued as gap 4 of Audit 5.
4. Headlines that state the change. This site's section headings are topic
   names ("Work"); the change is in the first sentence below. Comparable, not
   fixed.

### 10. Explanation and framing (D4, D8): Full Fact against Taxes and Tax and income

**What Full Fact does.** The explainer (about 1,300 words, no charts) is
organised as four questions: "What is the 'tax burden'?", "How much tax is
paid on the average worker's earnings?", "How does the UK compare
internationally?" and "What don't these figures tell us?". It defines the term
first ("the amount of tax revenue collected by the government each year as a
percentage of gross domestic product (GDP)") and notes that it "looks at all
tax revenue collected by the government, including taxes paid by both people
... and businesses". The fact check gives the exact record ("the highest level
since 1949 ... and the second highest since records began in 1948"), keeps
outturn and forecasts apart, attributes each forecast to the OBR or the IFS
and the plans it assumes, and gives no causes. Neither page opens with the
answer: both start with the political claims being checked.

**What this site does that Full Fact does not.**

- Answers first: each page opens with the figure and a plain sentence, then
  explains. Full Fact opens with the political claims.
- Charts with a table and a plain "What the chart shows" summary; Full Fact's
  explainer has no chart.
- Separates household tax shares, personal tax rates and shares of revenue in
  a named section ("Three numbers that are easy to mix up"). Full Fact does not
  say outright that the tax burden is not an individual's tax bill; it says the
  measure is "not necessarily the most useful way" to judge what workers pay.
- Every figure traces to a cell; Full Fact links to its sources but not to cells.

**What Full Fact does that this site did not.**

1. **Explained the term "tax burden".** It is the phrase a newcomer is most
   likely to hear about tax, and this site never named it, because its own
   wording check treats "burden" as loaded. So a reader could not connect what
   they hear in the news with the "taxes as a share of GDP" figures here.
   **Fixed in this PR**: the taxes page names the term in quotation marks,
   gives this site's figure (taxes 36.0% of GDP in 2025-26) and says it is not
   anyone's tax bill; the glossary explains it. The wording check still fails
   any unquoted use.
2. **The OBR's own "tax burden" figure is a slightly different measure.** Full
   Fact quotes the OBR at 36.3% of GDP for 2022-23; this site's taxes total from
   the OBR receipts table gives 35.3% for the same year (£929.0bn ÷ £2,634.3bn,
   October 2026 vintage). The difference is most likely the measure (the OBR's
   figure counts taxes on the national accounts basis, which includes some
   items its receipts table treats differently) and the vintage; this record
   did not reconcile the two item by item. The glossary now says the two can
   differ by about one percentage point. This site does not claim a record.
3. An international comparison (OECD tax wedge). Already noted in Part 1 as a
   gap for D1.
4. A heading that asks "What don't these figures tell us?". This site's
   "Limits" boxes do the same job under a less inviting name. Comparable.

### 11–12. Phone reading (D6): OBR guide and ONS bulletin against the money pages and Earnings

| Page | Words (main text) | Contents list | Answer first? |
|---|---|---|---|
| OBR brief guide | about 2,000 | No | No: opens "The independent Office for Budget Responsibility was established in 2010..." |
| ONS ASHE 2025 bulletin | about 2,000 to 2,500 | Yes, numbered, above "Main points" | Yes: "Main points" list |
| Full Fact explainer | about 1,300 | No | No |
| This site: Taxes | 917 | Yes | Yes (figure cards, then three sentences) |
| This site: Spending | 887 | Yes | Yes |
| This site: Who pays | 1,426 | Yes | Yes |
| This site: Earnings | 1,532 | Yes | Yes |
| This site: Housing | 1,825 | Yes | Yes |
| This site: 2009 compared with 2023 | 1,392 | Yes, after "In brief" | Yes |

Measured at 360px with sections folded, this site's pages are 8 to 17 screens
(Taxes 9.4, Spending 10.6, Who pays 14.3, Earnings 12.7, Housing 17.4, the
default comparison 14.3). The benchmark pages could not be measured in screens.
On words alone, every page here is shorter than the OBR guide and the ONS
bulletin, and the long screen counts come from tables, bars and folded
sections rather than prose. Both points need a real phone check; the page
length work (gap 3 of Audit 5) is with another ticket.

What the benchmarks do that this site does not: the ONS bulletin's chart
titles state the finding ("Median weekly earnings for full-time employee jobs
was £766.60 in April 2025"), where this site's chart titles name the measure
and put the finding in a summary under the chart. What this site does that
they do not: contents on every page, answers before detail, and no sideways
scrolling at 360px.

### 12 (continued). Honesty about limits (D10): ONS ASHE against Earnings

**What the ONS bulletin says.** "All estimates for 2025 are provisional";
"Estimates for 2024 have been revised"; "Data for 2020 and 2021 are subject to
more uncertainty and should be treated with caution"; and: "In 2024, we
introduced changes to the way we validated data, particularly higher earners'
returns ... these changes have not been applied to our back series and
comparisons between 2022 and 2023 data should be treated with caution." Its
"Uncertainty" section is one sentence: "Sampling variability for ASHE
estimates are provided in our accompanying datasets."

**This site against that.** The earnings page already said 2025 is provisional,
quoted the ONS on 2020 and 2021, marked the 2011 and 2021 coding breaks, and
shows margins of error beside the headline and every comparison, which the
bulletin leaves to its datasets. **It did not mention the 2022 to 2023 caution.**
That matters most for the pay spread (high earners). **Fixed in this PR**: the
earnings limits now say so in one sentence.

### Fixes made in this PR

1. **Timing note on comparison pages (D3, D8, D10).** When either year compared
   was in the 2008 recession (2008, 2009) or the coronavirus pandemic (2020,
   2021), or a compared range includes one of those years, a "Timing matters"
   box under the largest changes says so in one sentence each, with the ONS
   source, and says that a comparison starting or ending in an unusual year can
   show a bigger or smaller change than the years around it. It appears on 62 of
   153 two-year pages and on range pages that include those years. It describes
   timing, not cause, and is shown whichever way the figures moved.
2. **"Tax burden" named and explained (D4, D8).** One sentence on the taxes
   page with this site's figure, a glossary entry, and a narrow exception in the
   wording check (only the quoted term “tax burden”).
3. **ONS caution on comparing pay in 2022 and 2023 (D10).** Added to the
   earnings limits shown on the topic, year and comparison pages.

### Summary for Part 2

**Comparable with or ahead of the benchmarks:** choosing and comparing any
years and ranges with a fixed rule for what is shown first (D3); answers before
detail and shorter pages in words (D4, D6); "not compared" reasons and margins
of error where the reader meets the figure (D10); a stated rule for choosing
default years and no record claims (D8).

**Where the benchmarks are still ahead:**

1. A wider-area or long-run benchmark beside each headline change (ONS) (D3).
2. Per-chart downloads (ONS, OWID) (D3, D5). Queued as gap 4.
3. Chart titles that state the finding (ONS) (D4, D5).
4. International comparison (Full Fact, OBR) (D1, D4).
5. Neither benchmark set has been checked by a person outside the project, and
   neither has this site; on the strict reading, D8 and D10 still need that.

These are recorded as evidence for the next goal audit, not as new tickets.

---

## Part 3: holidays and class sizes (D2)

Added for ticket T35 (gap 5 of Audit 5): "Add the official share of people who
took a holiday, or record which official source comes closest and why none is
yearly, and add class-size and holiday benchmark comparisons."

### How this was done

- Date: 2 November 2026.
- Site version: `main` at `e1cf7dd` (after PR #103), built locally with
  `make build`, plus the changes in the same PR as this section.
- Benchmark pages: read on 2 November 2026 through a web-reading tool that
  returns page text (the cloud container cannot open these sites directly), so
  charts and layout could not be checked. Figures quoted are as published.
- Who did it: a Claude session that did not build the pages compared. As in
  Parts 1 and 2, a strict auditor may treat this as the auditor's own judgement.

### Pages compared

| # | Benchmark page | This site | Dimensions |
|---|---|---|---|
| 13 | ONS, [Travel trends: 2025](https://www.ons.gov.uk/peoplepopulationandcommunity/leisureandtourism/articles/traveltrends/2025) (16 October 2026, official statistics in development) | [Holidays](https://unpoliticalaf.vercel.app/life/holidays.html) | D2, D10 |
| 14 | DfE, [Schools, pupils and their characteristics: academic year 2025/26](https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics/2025-26) (4 June 2026, updated 16 October 2026), "Class size" section | [Class sizes](https://unpoliticalaf.vercel.app/life/schools.html) | D2, D10 |
| 15 | Eurostat, EU-SILC table [ilc_mdes02](https://ec.europa.eu/eurostat/databrowser/view/ilc_mdes02/default/table) "Inability to afford paying for one week annual holiday away from home" (updated 20 October 2026) | New section on [Holidays](https://unpoliticalaf.vercel.app/life/holidays.html#holidays-afford) | D2 |

### 13. ONS Travel trends against Holidays

**Figures.**

| 2025, Great Britain residents | ONS Travel trends 2025 | This site | Matches? |
|---|---|---|---|
| Visits abroad | 95.5 million | 95.5 million (95,453 thousand) | Yes |
| Most visited country | Spain, 19.1 million | Spain, 19.1 million | Yes |
| Second and third | France 9.1 million, Italy 5.7 million | France 9.1 million, Italy 5.7 million | Yes |
| Holiday visits | Not in the bulletin text (in the linked datasets) | 58.4 million, 61% of visits | Not comparable on the page; the site's figure is from the ONS dataset |
| UK residents (including Northern Ireland) | 99.9 million | Not shown for 2025; the site uses Great Britain residents from 2024, as the ONS tables by purpose do | Different coverage, stated on the page |

**What ONS does that this site does not.**

- Spending abroad (£83.9 billion by GB residents in 2025) and nights away.
- Quarterly figures, and visits to the UK by overseas residents.
- A PDF download and four linked datasets.

**What this site does that ONS does not.**

- Puts holidays abroad, holidays within Great Britain (VisitBritain's survey)
  and the main countries on one page, with per-100-residents rates and the
  2009 and 2019 rankings beside the latest year.
- Shows the 2024 method change as a split line and never compares across it.
  The ONS article warns that "Comparisons between 2024 and 2025 require
  caution because the annual 2024 estimates combine two survey
  methodologies". This site quoted the ONS 2024 article on the mixed year, but
  its comparison pages still compared 2024 with 2025 as one method (for
  example "Holiday visits abroad" 56.0 million to 58.4 million). **Fixed in
  this PR**: 2024 is now its own basis ("GB, mixed methods"), so it is compared
  with neither earlier years nor 2025, the chart marks a second break at 2025,
  and the limits say why.
- Says on the page that these are counts of trips, not people. ONS says so only
  in its glossary ("The figures for visits relate to the number of completed
  visits, not the number of visitors").

**The share of people who took a holiday.** Neither the ONS bulletin nor its
datasets give the number or share of people who travelled: both surveys count
trips. No official source found publishes a yearly UK share of people who took
a holiday. The closest official yearly measure is a different question asked
of households: could they afford a week's holiday away from home?

- **Eurostat EU-SILC, table ilc_mdes02** (the survey was run in the UK by
  ONS): UK figures for the 2005 to 2018 surveys, with series breaks marked in
  2012 and 2017. The UK stopped supplying them after leaving the EU, so there
  are no later UK years. **Added to the holidays page in this PR**, for
  everyone, low-income and other households, and households with and without
  dependent children, with its limits (it is not the share who went; one answer
  covers the household; breaks).
- **DWP Family Resources Survey** (Households Below Average Income): asks a
  similar question each year, but DWP publishes it only inside combined
  material deprivation measures for children and pensioners. Its questions
  changed in 2010-11, 2011-12 and 2023-24, and DWP advises against comparing
  across the pandemic years. Not shown; the holidays page says why.

### 14. DfE class size statistics against Class sizes

**Figures.**

| England, state-funded | DfE 2025/26 release | This site before this PR | This site after |
|---|---|---|---|
| Primary average, January 2026 | 26.1 ("decreased slightly by 0.3") | Not shown (latest was January 2025: 26.4) | 26.1 |
| Secondary average, January 2026 | 22.6 ("increased slightly by 0.1") | Not shown (January 2025: 22.5) | 22.6 |
| Infant classes (reception to year 2) | 25.9 | Not shown | Not shown |
| Key stage 2 (years 3 to 6) | 27.6 | Not shown | Not shown |
| Infant pupils in classes over the legal limit of 30 | 39,500, 2.7% | Not shown | Not shown |

The January 2025 figures match DfE's (26.1 + 0.3 = 26.4; 22.6 − 0.1 = 22.5).
**This site was a year behind**: the DfE data set already in the repository
held January 2026, but the year explorer stops at 2025, so the class sizes
page dropped it. **Fixed in this PR**: the class sizes page now shows January
2026 in its answer, chart and table, and says that it appears on that page
only, because the other topics have no 2026 figures yet.

**What DfE does that this site does not.**

- Infant and key stage 2 averages, and the number and share of pupils in
  large classes (infant classes over the statutory limit of 30; key stage 2
  classes of 31 or more: 413,900, 18.8%). This site quotes the legal limit but
  shows no large-class figures.
- Downloadable data and a table builder.

**What this site does that DfE does not.**

- A series from January 2006 to January 2026 on one chart and table. The DfE
  page compares with the previous year only and says the infant figure is "the
  lowest infant class size since 2008/09".
- Wales and Scotland beside England, with the reason they are not compared,
  and a note that Northern Ireland publishes no average class size. The DfE
  page covers England only and does not say so on the page.
- States the definition (classes taught by one teacher, January census) with
  every figure. DfE gives this as a note under its tables.

### Summary for Part 3

**Comparable with or ahead of the benchmarks:** headline figures match ONS
and DfE exactly; trips are labelled as trips, not people, where the reader
meets them; the 2024 travel method change is never crossed; class sizes have a
20-year series and other nations.

**Where the benchmarks are still ahead:**

1. Large classes and infant / key stage 2 averages (DfE) (D2).
2. Spending and nights abroad (ONS) (D2).
3. No official yearly share of people who took a holiday exists; the nearest
   (could not afford a week away) stops in 2018 for the UK (D2, D10).
4. Downloads (both). Queued as gap 4 of Audit 5.

These are recorded as evidence for the next goal audit, not as new tickets.
