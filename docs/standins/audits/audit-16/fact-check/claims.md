# Fact-check: 30 headline claims (audit 16)

Site checked: `site/` as built at commit d72127d. I read the built HTML pages, the figure records (`site/figures/`, `site/data/facts.json`) and, where it helped, the publisher's own page on the web. I did not read `builder/` or any review of the site.

For each claim I checked these things, which a number check cannot catch: the period, the population or place, the units, whether a "largest" or "highest" really is the largest, any comparison across a series break, and whether every calculated value matches its stated formula and inputs. Every calculated value I tested matched its inputs to the rounding shown. Ids are listed in the same order as `ids.txt`.

## Findings

**Material: 0. Minor: 3.**

### Minor 1: the top 1% share is shown for 2023-24 without HMRC's caveat about that year
- **Ids:** `hmrc.share.top1.2023 to 2024`, `hmrc.income.top1.2023 to 2024`
- **Pages:** home page and who-pays.html
- **Evidence:** HMRC's commentary (Income Tax liabilities statistics, 15 July 2026, section 4.3 "Additional rate impacts") says this about the April 2023 cut in the additional rate threshold from £150,000 to £125,140: it "is estimated to have led to a small amount of forestalled income into 2022 to 2023". HMRC says the share of income for higher-rate taxpayers near the new threshold was "artificially high in 2022 to 2023" and "artificially low in 2023 to 2024".
- **The gap:** the site's box "Why does the top 1% share go up and down?" quotes HMRC on the forestalling in 2009-10 and 2013-14, and on the threshold freezes. It leaves out this 2022-23/2023-24 effect. The chart text says the share "fell to 27.2% in 2023-24" (from 28.5%).
- **Why minor:** the numbers (27.2% and 12.4%) match HMRC exactly. HMRC calls the effect "small", and the gap is missing context rather than a false figure.

### Minor 2: "Scotland had the highest median pay of the four nations" is within the margin of error
- **Id:** `earn.place.real.scotland.2025`
- **Page:** life/earnings.html
- **Evidence:** Scotland is £776 a week, with a margin of ±£9 (`moe.earn.place.real.scotland.2025`). England is £770, ±£3. The site's own figures put the two ranges in heavy overlap.
- **The gap:** the ranking is stated flatly, with no note that it could be sampling noise. The country table on the holidays page does carry that warning.
- **Why minor:** the point estimates are right.

### Minor 3: "Spain in every year" sits beside a range that starts in 1971
- **Page:** life/index.html, the line "Most visited country abroad: Spain, counting visits for any purpose, in every year with figures by country"
- **Evidence:** this is true for the years in the site's own tables: 2009 to 2019 and 2021 to 2025, which I checked in facts.json. The page, though, invites readers to pick any year from 1971.
- **The gap:** ONS Travel Trends has country figures for earlier years, and France appears to have led in the late 1990s (about 11 million visits against Spain's 9 million in 1999). I only saw that figure in a secondary reproduction of the ONS 1979–1999 series, so it needs confirming against ONS.
- **Why minor:** the wording is technically scoped to "years with figures by country", but a reader could take it to mean every year since 1971.

### Notes, not counted as findings
- **ASHE 2025 pay (`earn.ft.2025`):** the site uses £766.6, the provisional figure. The site says itself that ONS has since published April 2026 pay, and that release normally revises the 2025 figure too. The auditor's re-download will show whether £766.6 still stands.
- **HMRC source file:** the GOV.UK page for these statistics (updated 30 September 2026) now lists a single "Collated Tables 2.1 to 2.6" file. The site's source link points to a separate Table 2.4 .ods file (asset id 6a54e2b7…). If that link no longer resolves, the source needs updating.
- **Figures confirmed against the publisher or a reproduction of it:**
  - HMRC 2023-24: 27.2%, 12.4%, 59.1% and 9.9% (HMRC commentary).
  - GB residents in 2025, with Spain 19.1m and France 9.1m (ONS Travel trends 2025).
  - DfE class sizes: 26.1 (primary) and 22.6 (secondary) in January 2026, 26.4 and 22.5 in 2025, and 2.7% of infant pupils in large classes.
  - Scotland primary classes: 23.1 (2025 pupil census).
  - PESA 2026 total managed expenditure: £1,360.1bn (third-party reproduction).
  - ETB financial year ending 2024 is still the latest release. FYE2025 is announced for December 2026.

## The 30 claims

| # | Id | Claim as the page states it | Page | What I checked, beyond the number |
|---|----|------------------------------|------|-----------------------------------|
| 1 | spend.cash.tme.2025-26 | "£1,360bn spent by the UK public sector in 2025-26" | index, spending | **Period:** PESA 2026 Table 4.2, 2025-26 outturn. **Population:** whole UK public sector. A third party gives the same £1,360.1bn. No problem. |
| 2 | spend.per100.social.2025-26 | "£33 of every £100 spent on services went on social protection, the largest area" | index, spending | 407.3 ÷ 1,227.6 = 33.2. **Base:** spending on services, not total spending, and the page says so. "Largest" is true: health is next at £21, and social protection is largest in every year back to 2003-04. No problem. |
| 3 | spend.per100.debt_interest.2025-26 | "£11 of every £100 spent on services" is interest on debt | index, spending | Formula is debt interest ÷ services = 10.6. The page also gives £9.6 per £100 of total spending. It is labelled as gross interest paid ("before interest received"), and the page explains why the OBR/IFS net figures are lower. No problem. |
| 4 | spend.perhousehold.tme.2025-26 | "about £46,895 per household" | spending | 1,360.1bn ÷ 29.003m households (LFS, Apr–Jun 2025). The page calls it an average, not anyone's bill, and dates the households correctly. No problem. |
| 5 | spend.realchange.tme.2003-04.2025-26 | "total spending in 2025-26 was 54% higher than in 2003-04" after inflation | spending | 1,360.1 ÷ 882.0 − 1 = 54.2% (GDP deflator, as the page states). Total managed expenditure is not hit by the area breaks (student loans, Network Rail). No problem. |
| 6 | spend.gdp.tme.2025-26 | "44.3% of GDP" | spending | PESA basis. The OBR basis on the taxes page gives 44.5%. The site notes that different publications give different totals. No problem. |
| 7 | spend.realchange.health.2015-16.2025-26 | Health spending "34% rise" after inflation, 2015-16 to 2025-26 | spending | 257.5 ÷ 192.1 = 1.340. Economic affairs is compared only from 2015-16, which is right given the Network Rail break. **"Largest rise" claims:** on spending-areas.html, health is the largest % rise since 2003-04 in cash (243.8% against general public services' 239.8%) and in real terms (92.7% against 90.7%), and the largest rise in % of GDP points. It is not the largest absolute £ rise, where social protection leads, but the site's claim is stated in %. No problem. |
| 8 | rec.taxes.2025-26 | "£1,105bn raised in taxes in 2025-26" | index, taxes | OBR databank (October 2026), 2025-26 outturn. Tax is kept separate from the £1,231bn of all receipts. No problem. |
| 9 | rec.big3share.2025-26 | "65% of all tax came from Income Tax, National Insurance and VAT" | index, taxes | (329.3 + 204.4 + 180.3) ÷ 1,104.7 = 64.6%. No problem. |
| 10 | agg.psnb.2025-26 | "£134bn borrowed to cover spending above receipts (not tax)" | index, taxes | 1,365.6 − 1,231.3 = 134.3. Every year agrees in sign: spending above receipts in 68 of 78 years, and 65 of 71 in the after-inflation view, both recomputed. No problem. |
| 11 | gdp.psnd.2025-26 | Debt "£2,917bn at the end of March 2026 … equal to 93.3% of GDP" | taxes | Public sector net debt on the OBR measure, with GDP centred on end-March, as stated. No problem. |
| 12 | rec.perhousehold.taxes.2025-26 | "about £38,089 per household" | taxes | 1,104.7bn ÷ 29.003m. The page says this includes tax paid by businesses and is not anyone's bill. No problem. |
| 13 | rec.share.income_tax.2025-26 | "Income Tax 30%" of taxes | index | 329.3 ÷ 1,104.7 = 29.8%. The taxes page gives 29.8%, so the home page's 30% is consistent. (National Insurance at 18.5% shows as 19% on the home page, which is correct rounding.) No problem. |
| 14 | rec.sharechange.nics.1999-00.2025-26 | "The largest rise was in National Insurance contributions: 16.5% to 18.5%" (+2.0 points) | taxes | The next largest rises are Income Tax (+1.7), all other taxes (+1.7) and Capital Gains Tax (+1.6), so "largest" is true. **Period:** 1999-00 is the first year in the OBR databank, as stated. No problem. |
| 15 | hmrc.share.top1.2023 to 2024 | "27.2% of all Income Tax … owed by the top 1% of Income Tax payers, tax year 2023-2024" | index, who-pays | Confirmed by HMRC's commentary. **Population:** Income Tax payers only, as stated. See **Minor 1** (HMRC's caveat about 2022-23/2023-24 is left out). |
| 16 | hmrc.income.top1.2023 to 2024 | "They had 12.4% of all Income Tax payers' income" | index, who-pays | Confirmed by HMRC (income before tax, taxpayers only). See **Minor 1**. |
| 17 | etb.2a.taxshare.q5 | "46.0% of all taxes paid by UK households in 2023/24 were paid by the richest fifth" | who-pays | Calculated by the site: average tax per household × households in each fifth. The method is stated, and it covers household taxes, not all revenue. The fifths are fifths of people, so "paid by the richest fifth" means the households of the richest fifth of people. The page explains this. No problem. |
| 18 | etb.2a.alltax.q1 | "£8,625 a year in all taxes … by the households of the lowest-income fifth of people (36.7% of their gross income)" | who-pays | Direct £3,696 + indirect £4,929. 8,625 ÷ 23,495 = 36.7%. No problem. |
| 19 | etb.t8.gross.all.all | "33.6% of gross household income went on tax … An average, not anyone's tax rate" | index, household-tax | ETB FYE2024 Table 8, all individuals. This is still the latest ETB (FYE2025 is due December 2026). The method break at 2018/19 is handled: the chart's two methods are never joined. No problem. |
| 20 | etb.t8.gross.indirect.q1 | Lowest fifth: indirect taxes "21.0% of gross household income" | index, household-tax | The same tax is also shown as 24.9% of disposable income and 16.5% of spending, with the reason given. No problem. |
| 21 | etb.t16.all.2023/24 | "53.3% of people lived in households that received more in benefits and services than they paid in taxes" | who-pays | **Population:** people, not households. Benefits include services in kind, as stated. The 2001/02 adjustment for top incomes is disclosed. No problem. |
| 22 | work.rate.2026 | "75.1% of people aged 16 to 64 were in work, April to June 2026, UK" | index, work | LF24, 2026 Q2, ages 16–64. The site says this is newer than its year pages. No problem. |
| 23 | earn.real.ft.2021 | "April 2021 £761 → April 2025 £767" (after inflation, "about the same, +0.8%") | index, earnings | 610 × CPIH(April 2025) ÷ CPIH(April 2021). **Breaks:** comparison starts at the SOC2020 recoding in 2021, correctly. Not compared across the 2011 or 2021 breaks. No problem. |
| 24 | earn.ft.2025 | Cash weekly pay "£767" in April 2025 | index, earnings | Nomis ASHE resident analysis gives 766.6 (UK, full-time median). Provisional 2025 value; see notes. |
| 25 | earn.place.real.scotland.2025 | "full-time employees living in Scotland had the highest median pay of the four nations (£776 a week)" | earnings | "Highest" on point estimates, but within the margin of error. See **Minor 2**. |
| 26 | house.owners.2024 | "65% of households in England owned their home, 2024-25" | index, life/index, housing | EHS FT1101 gives 64.83%. **Place:** England only, as stated. The chart is not joined across the switch from LFS to EHS in 2008-09. No problem. |
| 27 | hol.world.holiday.2025 | "58.4 million holiday visits abroad by Great Britain residents in 2025" | index, holidays | **Population:** GB residents under the new ONS method, as stated. ONS confirms that the 2025 figures are for GB residents. It is correctly not compared with 2019 (UK residents, old method) or with 2024 (mixed methods). The home page's small chart is a different measure (all purposes, UK residents, to 2023), and it is labelled as such. No problem. |
| 28 | hol.abroad.per100.2025 | "about 86 for every 100 residents" | holidays | 58.396m ÷ GB population (GBPOP), not the UK population, which matches the population counted. No problem. |
| 29 | school.primary.2026 | "26.1 pupils in the average state primary school class in England, January 2026" | index, schools | Confirmed by DfE "Schools, pupils and their characteristics 2025/26" (primary 26.1, secondary 22.6, 2.7% of infant pupils in classes over 30). No problem. |
| 30 | jobs.share.C.2026 | "Manufacturing went from 24.9% of all jobs in June 1978 to 6.7% in June 2026 (provisional)" | work, jobs-by-industry | 2,460k ÷ 36,734k workforce jobs (seasonally adjusted). "Health and social work rose most" (+6.6 points against professional/scientific's +6.0) and "manufacturing fell most" (−18.3) both check out across all 20 sections. No problem. |
