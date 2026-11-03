# Audit 12: fact-check of headline claims

Scope: the built pages in `site/` (`index.html`, `spending.html`, `taxes.html`, `who-pays.html`, `household-tax.html`, `life/index.html` and the topic pages under `life/`). I checked each claim against its record in `site/figures/` and `site/data/facts.json`, and against the publisher file kept in the repository (`data/raw`, `data/payers/raw`, `data/fetched`). I did not read `builder/`, any review of the site or git history.

The ids are in `ids.txt`, one per line, in the same order as the table below. Note that `hmrc.share.top1.2023 to 2024` contains spaces.

**Result:** I found no material errors among the 30 claims. Every value matches its publisher cell, and every calculated value recomputes from its inputs. Each "largest", "highest", "most" or "lowest" claim I tested holds against the full data, not only the items shown. The problems are all **minor**: wording, labels and figure-record documentation. They are listed after the table.

## The 30 claims

| # | id | Page | Claim as stated | Checks beyond the number | Verdict |
|---|---|---|---|---|---|
| 1 | spend.cash.tme.2025-26 | index, spending | "£1,360bn spent by the UK public sector in 2025-26" | PESA 2026 table 4.2 cell X27, Total Managed Expenditure, outturn. The page says the OBR databank gives £1,366bn for the same year. | OK |
| 2 | spend.per100.social.2025-26 | index, spending | "£33 of every £100 spent on services went on social protection, the largest area" | 407.3 ÷ 1,227.6. The base is spending on services (TME less £132.5bn accounting adjustments), and the page says so. Social protection (407.3) is larger than every other COFOG function; health (257.5) comes next. | OK |
| 3 | spend.per100.debt_interest.2025-26 | index, spending | "interest on government debt … £11 of every £100 spent on services … counts interest paid out" | 130.3 ÷ 1,227.6, from 4.2 row 9. PESA 5.2 note (2) says "Debt interest figures show gross payments to the private sector and overseas", so the page's gross-versus-net warning is correct. | OK |
| 4 | spend.realchange.tme.2003-04.2025-26 | spending | "After adjusting for rising prices, total spending in 2025-26 was 54% higher than in 2003-04" | 1,360.1 ÷ 882.0, both from table 4.3. PESA note (1) says 4.3 uses the GDP deflator in 2025-26 prices, which matches the page. | OK |
| 5 | spend.perhousehold.tme.2025-26 | spending | "about £46,895 per household" (29.0 million UK households, April to June 2025) | ONS families and households table 5, B21 = 29,003 thousand, labelled "All households" for 2025, UK, LFS. The page notes that this is an average across households that includes children. The period mismatch (a financial year divided by an April-to-June count) is disclosed. | OK |
| 6 | spend.oldage.2025-26 | spending | "Pensions in old age cost £155bn in 2025-26 … HM Treasury's 'old age: of which pensions' line" | PESA 5.2, G107 = 154,858 (£m), row label "of which: pensions" under 10.2 Old age. | OK |
| 7 | rec.taxes.2025-26 | index, taxes | "£1,105bn raised in taxes in 2025-26" | OBR databank, Receipts AH33, "National accounts taxes". Not to be confused with current receipts (£1,231bn), which the page keeps separate. | OK |
| 8 | rec.big3share.2025-26 | index, taxes | "Income Tax, National Insurance and VAT raised 65% of it" | (329.338 + 204.429 + 180.326) ÷ 1,104.686 = 64.6%. Income Tax is PAYE + SA + "other income tax" (−5.246), and the page says so. | OK |
| 9 | agg.psnb.2025-26 | index, taxes | "Borrowing covered another £134bn" | Aggregates O87. Equals TME 1,365.598 − receipts 1,231.312. | OK |
| 10 | gdp.psnd.2025-26 | taxes | "£2,917bn at the end of March 2026 … equal to 93.3% of a year's GDP" | 93.3 is OBR's own ratio (X82). See minor finding 7 on the wording "a year's GDP". | Minor |
| 11 | rec.gdp.taxes.2025-26 | taxes | "Taxes alone were 36.0% of GDP in 2025-26, a share news reports often call the 'tax burden'" | Recomputes as 1,104.686 ÷ 3,069.799 and matches OBR's own column "National account taxes" (Aggregates % GDP, I82 = 35.99). | OK |
| 12 | rec.othertax.2025-26 | taxes | "All other taxes £142bn" | The value is right: 1,104.686 less all 10 named taxes = 141.96. The figure record's input list names only 7 of the 10 taxes subtracted (stamp duties, alcohol and tobacco, and IHT are missing), so a recompute from the listed inputs gives £191.7bn. See minor finding 8. | Minor (record) |
| 13 | rec.sharechange.nics.1999-00.2025-26 | taxes | "The largest rise was in National Insurance contributions: 16.5% to 18.5%" (also "largest fall … Fuel duties") | Checked against all 11 categories. NICs +1.97 pts is the largest rise (then Income Tax +1.73, other +1.66, CGT +1.58). Fuel −4.32 pts is the largest fall (then alcohol and tobacco −2.35). | OK |
| 14 | rec.perhousehold.taxes.2025-26 | taxes | "about £38,089 per household" | 1,104.686bn ÷ 29.003m. The caveats (includes business taxes, not anyone's bill) are present. | OK |
| 15 | hmrc.share.top1.2023 to 2024 | index, who-pays | "27.2% of all Income Tax for the year was owed by the top 1% of Income Tax payers in 2023 to 2024" | HMRC Table 2.4 (July 2026), share_tax K27, row "2023 to 2024", which is outturn; later rows are projections. The population is Income Tax payers only, and the page says so. "High of 30.7% in 2021-22" and "lowest 20.8% (2003-04)" also check out. | OK |
| 16 | hmrc.threshold.top1 | who-pays | Top 1% "Income from £207,000" | 2.4 inc_quantiles K27 (2023 to 2024) = 207,000. This is income before tax, as the note says, and not a 2026-27 projection (£230,000). | OK |
| 17 | etb.2a.alltax.q5 | who-pays | "£51,903 a year in all taxes, on average, by the households of the highest-income fifth of people, 2023/24" | ETB FYE2024 Table 2a: G48 41,215 + G70 10,688. The table title confirms people are ranked into fifths and amounts are per household, as the page says. | OK |
| 18 | etb.t8.gross.all.all | index, household-tax | "33.6% of gross household income went on tax, on average across everyone, 2023/24" | Table 8 I15, all individuals. The 2017/18 break (households vs people, top-income adjustment) is disclosed and the series are not joined. The claims that the lowest fifth was below the highest in every year from 1977 to 1987 and above it from 1988 to 2017/18, and that the two have been within 5 points since 2018/19, all hold. | OK |
| 19 | etb.t16.all.2023/24 | who-pays | "53.3% of people lived in households that received more in benefits and services than they paid in taxes" | Table 16 is titled "percentage of individuals in households receiving more in benefits than they pay in taxes", so people (not households) is correct. The retired (90.1%) and non-retired (45.8%) shares are consistent. | OK |
| 20 | etb.ret.taxshare.all | who-pays | "The households that retired people live in paid less tax (£10,363 …) … taxes took 29.4% of their gross income" | (4,447 + 5,916) ÷ 35,290 from Table 4a. The table covers *retired households*, where more than 50% of income comes from retired members (ETB note 12). That is not the same as "households that retired people live in". See minor finding 4. | Minor (population wording) |
| 21 | spi.age.sharetax.30_64 | who-pays | "taxpayers aged 30 to 64 … owed about 79% of all Income Tax" | Sum of count × mean tax by age band, from SPI 2023-24 Table 3.2. The shares for the three age groups (8 + 79 + 13) add to 100. Base 36.7 million taxpayers (C19). | OK |
| 22 | work.rate.2026 | index, life/work | "75.1% of people aged 16 to 64 were in work, April to June 2026, UK" | LF24 row "2026 Q2". The 2025 dot (75.3%) is "higher than in 51 of the other 54 years", which recounts correctly. | OK |
| 23 | earn.real.ft.2021 | index, life/index, life/earnings | "April 2021 £761 → April 2025 £767 … both in April 2025 prices: about the same (+0.8%)" | 609.8 × CPIH 137.7 ÷ 110.4 (L522 rows "2021 APR" and "2025 APR"). The deflator is CPIH, as labelled. The comparison stays within the 2021–2025 SOC2020 stretch, so it does not cross a break. 2025 is provisional, and the page says so. | OK |
| 24 | house.owners.2024 | index, life/index, life/housing | "65% of households in England owned their home, 2024-25" | EHS FT1101 D103. "Higher than in 10 of the other 16 years measured the same way" recounts correctly (2020-21 at 64.86% is just above). See minor finding 1 on the chart label. | OK |
| 25 | house.rent.private.2024 | life/index, life/housing | "The average private rent was £250 a week … (cash, at the time)" | FA3201 2024-25 J12: all private renters, mean before housing support. The mortgage series joins FA2501 (to 2021-22) with FA2555; both include shared owners, so there is no hidden break. | OK |
| 26 | hol.world.holiday.2025 | index, life/index, life/holidays | "58.4 million holiday visits abroad by Great Britain residents in 2025" | ONS Travel trends 2025, Table 2 C48. The cover sheet confirms tables 2 to 16 cover GB only, so "Great Britain residents" is correct. The 2024 and 2025 method breaks are shown, and the 2019 UK figure (58.7m) is not compared with them. | OK |
| 27 | hol.abroad.per100.2025 | life/index, life/holidays | "about 86 for every 100 residents" | Divides by the GB population (GBPOP 2025, 67.56m), which matches the GB numerator. | OK |
| 28 | school.primary.2026 | index, life/schools | "26.1 pupils in the average state primary school class in England, January 2026" | DfE API, 2025/26 release. The trend wording ("rose until 2016, held level until 2019, then fell") matches the series. | OK |
| 29 | afford.ratio.ew.2025 | life/house-prices, life/housing | "the home cost 7.55 times a year's earnings, compared with 3.89 times in 1999 … The highest ratio was 8.95 times in 2021" | ONS 1c AE3. 295,000 ÷ 39,059 = 7.55. The earnings are workplace-based, and the page says "working there". 2021 is the series maximum. The 1997–98 break is disclosed. | OK |
| 30 | jobs.share.C.2026 | life/work, life/jobs-by-industry | "Manufacturing went from 24.9% of all jobs in June 1978 to 6.7% in June 2026 (provisional)" | 2,460 ÷ 36,734 (JOBS02 WFJ SA). Checked against all 20 industries: manufacturing is the largest fall (−18.3 pts), and health and social work is the largest rise (+6.6 pts, ahead of professional +6.0 and admin +4.1). | OK |

## Other "largest" and "highest" claims checked (not in ids.txt)

All of these hold:

- Employment rate in 2025: England highest (75.8%), Wales lowest (72.5%).
- Employment rate rise from 2008: Northern Ireland largest among nations (+6.3), London largest among regions (+5.8).
- Pay by nation, April 2025: Scotland highest (£776), Northern Ireland lowest (£716).
- Pay by region: London highest and North East lowest. East of England had the largest real rise and London the largest fall.
- Homes rented privately: London had the largest rise (+6.5 pts, ahead of the North West at +6.2).
- Holiday destinations: Spain, France and Greece were the top three.
- Professional occupations were the largest job group.
- Spending exceeded receipts in "68 of the 78 years" and "65 of the 71 years".
- Income Tax raised the most of the three main taxes in every year.
- Visits abroad per 100 people in 2023 were "higher than in 40 of the other 43 years".
- Primary class size in 2025 was "higher than in 4 of the other 19 years".

## Problems found

There are no material problems. All of the following are minor.

1. **Inconsistent housing chart label (minor).** On `life/index.html` the housing sparkline's axis ends "2025-26" and its caption reads "1981 to 2025-26", but the latest figure is 2024-25. `index.html` labels the same chart "1981 – 2024-25", and there is no 2025-26 EHS figure. A reader may think 2025-26 data exist.
2. **Contradictory "low" wording for men's employment (minor).** `life/work.html` says men's employment "fell from 91.7% in 1971 to a low of 75.4% in 2010" and then "lowest 75.1% (1993)". The 2010 figure is a local low, not the series low, so the sentence contradicts itself.
3. **"Largest rises, equal on the figures shown" (minor).** In `life/earnings.html`, England (£765→£770) and Wales (£714→£719) are called equal. Unrounded, Wales rose £5.2 and England £4.5. The text hedges with "on the figures shown", but the unrounded data have a clear order.
4. **Population wording for retired households (minor).** `who-pays.html` section 3 says "the households that retired people live in". ETB Tables 3a and 4a cover *retired households*: those where more than 50% of income comes from retired members (ETB note 12). Retired people living in non-retired households are in the "non-retired" figures.
5. **"Corporation Tax includes North Sea profits" (minor).** On `taxes.html` the figure is onshore plus offshore Corporation Tax. Two other North Sea taxes, the Energy Profits Levy (£2.8bn) and Petroleum Revenue Tax (−£0.4bn), sit in "All other taxes".
6. **Scotland's private-rent share includes job-tied tenancies (minor).** On `life/housing-places.html`, the source column is "Rented privately or with a job/business". The page's general caveat about each nation measuring housing its own way partly covers this.
7. **"93.3% of a year's GDP" (minor).** On `taxes.html`, 93.3 is OBR's published ratio. It does not equal £2,916.8bn divided by 2025-26 GDP (£3,069.8bn, 95.0%) or by the GDP centred on end-March (£3,134.7bn, 93.05%). Saying "of GDP (OBR measure)" would avoid implying a simple division.
8. **Incomplete input list in a figure record (minor, but it affects re-checking).** `rec.othertax.2025-26` in `figures/obr.html` and `facts.json` lists 7 inputs. The value subtracts all 10 named taxes. A recompute from the listed inputs gives £191.7bn, not £142.0bn. The published value itself is correct.
9. **Range of "kinds of household" (minor).** `who-pays.html` says taxes took "27% (one retired adult) to 36% (two adults, no children)". This uses the "1 adult (All)" columns. Table 12 also publishes single non-retired men (36.5%) and single retired women (26.6%), which lie outside the stated range.

## Not checked

- Whether ONS has published ETB for the year ending March 2025 since the site's retrieval. The site uses FYE2024, published 25 September 2025. If a newer edition exists, the "2023/24" headline figures on `index.html`, `who-pays.html` and `household-tax.html` would be one year out of date. This needs a live check by the Accuracy workflow.
- Quoted passages, other than the PESA debt-interest note, which I confirmed in the source file.
