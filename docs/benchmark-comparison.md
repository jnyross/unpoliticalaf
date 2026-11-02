# Benchmark comparison

This file records side-by-side comparisons of named benchmark pages against the
matching pages on this site. The [goal rubric](goal-rubric.md) lets a dimension
reach level 4 only with "a recorded independent review of that dimension or a
recorded side-by-side comparison with a named benchmark page". This is that
record for D1 (public money answers), D2 (life: breadth and depth) and D5
(visual design and charts). It does not score anything: the next goal audit
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
