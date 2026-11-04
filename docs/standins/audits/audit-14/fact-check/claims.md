# Audit 14: adversarial fact-check

Fresh session. I read only the built pages in `site/`, the figure records in
`site/figures/` and `site/data/facts.json`, and the publisher files that those
records name (kept copies in `data/raw/`, `data/payers/raw/`,
`data/fetched/`, `data/life/sources/`). I did not read `builder/` or any
earlier review. Each figure below was traced to the cell the figure record
names and, for calculated figures, recomputed from the inputs. I also checked
the wording around each figure: the period, the population, the place, any
"largest", "highest" or rank, and any comparison across a break.

Verdicts: **correct**, **minor** (the wording or rounding is loose, but a
reader would not come away believing something false), **material** (a
reader would believe something false).

## Summary

- Material: **0**
- Minor: **6** (on claims 5, 7, 17, 26 and 28, plus one finding outside the 30 claims)
- Correct: 24 of the 30 claims have no problem.

The minor findings, most important first:

1. **Rounding of exact halves goes to the even digit** (claim 7). £132.5bn is
   shown as "£132bn" on the spending page, and 31,150 thousand visits is shown
   as "31.1 million" on the 1990 year page. Most readers would expect £133bn
   and 31.2 million.
2. **The words under the share-of-GDP spending chart skip the 2021-22 low**
   (claim 5). They say spending "rose to a high of 52.3% in 2020-21, then fell
   to 44.3% in 2025-26". In fact it fell to 43.4% in 2021-22 and then rose
   again. The chart's own title says this correctly.
3. **The home page calls the Table 8 figure "an average across households"**
   (claim 17). ONS Table 8 is for all individuals, and the Tax and income page
   describes it correctly as an average across people.
4. **The mortgage payment uses a different base from the other housing figures**
   (claim 26). The £242 is the "all mortgage types" row of FA2555, which covers
   7.06m households. The table's "all" row covers all 7.32m mortgagors and gives
   £236. Both rows are official; the page does not say which one it uses.
5. **House price period** (claim 28). "In 2025, the middle-priced home ... cost
   £295,000": the price is for the year ending September 2025. The chart says
   so, but the lead sentence does not.
6. **Also found, outside the 30 claims.** On the year pages, the private-renting
   small chart says "2008-09 to 2025-26" in its axis and caption, but the last
   figure is 2024-25 (see the 2020 page). On housing-places, the words "in
   Scotland, where homes that come with a job or business are counted with
   private renting" suggest that England is different. But DLUHC Live Table 109
   also counts England as "Rented privately or with a job or business". On the
   Tax and income page, "then fell until 2017/18" (older method) ignores the
   lower point of 33.1% in 2009/10, although the next sentence gives it.

---

## Claims

### 1. `spend.cash.tme.2025-26`: "£1,360bn spent by the UK public sector in 2025-26"
- Pages: index, spending.
- Source: HM Treasury, PESA 2026 Chapter 4, sheet 4_2, cell X27 ("Total
  Managed Expenditure", 2025-26 outturn) = 1360.1.
- Checks: services 1227.6 + accounting adjustments 132.5 = 1360.1. The period
  (2025-26 outturn, published July 2026) and the scope (whole public sector,
  UK) match. The page says that the OBR databank's £1,366bn differs, which is
  correct (OBR Aggregates D87 = 1365.598).
- Verdict: **correct**.

### 2. `spend.per100.social.2025-26`: "£33 of every £100 spent on services went on social protection, the largest area"
- Pages: index, spending.
- Source: PESA 4_2 X23 = 407.3, divided by X25 = 1227.6, = 33.18%.
- "Largest": yes. The next largest are health at 257.5 and general public
  services at 165.5. The page divides by spending on services, not by total
  spending, and says so.
- Verdict: **correct**.

### 3. `spend.per100.debt_interest.2025-26`: "£11 of every £100 spent on services is interest paid on debt, counted before interest received"
- Pages: index, spending.
- Source: PESA 4_2 X9 = 130.3, divided by 1227.6, = 10.61. The "of total
  spending" version is 130.3 ÷ 1360.1 = 9.58 (shown as £9.6).
- The gross versus net wording matches HM Treasury's definition, and the
  page explains why the OBR and IFS net figure is lower.
- Verdict: **correct**.

### 4. `spend.realchange.tme.2003-04.2025-26`: "After adjusting for rising prices, total spending in 2025-26 was 54% higher than in 2003-04"
- Page: spending.
- Source: PESA 4_3 (real terms, 2025-26 prices) TME: 2003-04 = 882.0, 2025-26 =
  1360.1. 1360.1 ÷ 882.0 − 1 = 54.2%. The same figures are in PESA 4_1.
- The deflator (GDP deflator) is named correctly, and the comparison is within
  one consistent series.
- Verdict: **correct**.

### 5. `spend.gdp.tme.2025-26`: "44.3% of GDP", and the words under the share-of-GDP chart
- Page: spending.
- Source: PESA 4_4 TME 2025-26 = 44.3. The other years match (2003-04 38.7,
  2009-10 46.0, 2018-19 39.1, 2019-20 39.1, 2020-21 52.3, 2021-22 43.4,
  2022-23 44.1, 2023-24 44.1, 2024-25 44.0).
- Problem: the description in words says "rose to a high of 52.3% in 2020-21,
  then fell to 44.3% in 2025-26". In fact the share fell to 43.4% in 2021-22
  and then rose to 44.3%. The chart title says this correctly ("then fell
  until 2021-22, then rose again by 2025-26"), but the sentence suggests a
  steady fall to the latest year.
- Verdict: **minor**. The number is right, but the description of the trend
  is incomplete.

### 6. `spend.perhousehold.tme.2025-26`: "about £46,895 per household"
- Page: spending.
- Inputs: TME £1,360.1bn ÷ 29,003 thousand UK households (ONS Families and
  households 2025, Table 5, B21 "All households", April to June 2025) =
  £46,895. Per person: ÷ 69,483,900 (UKPOP mid-2025) = £19,574.
- The population basis (private households, UK, LFS) is stated, and the page
  says it is an average, not a bill.
- Verdict: **correct**.

### 7. `spend.cash.adjustments.2025-26`: "the other £132bn is accounting adjustments"
- Page: spending.
- Source: PESA 4_2 X26 = 132.5.
- Problem: an exact .5 is rounded down to the even digit. The table on the
  same page shows £132.5bn, so a careful reader sees both. The same rule
  appears elsewhere: 31,150 thousand visits abroad in 1990 (ONS OTT GMAF) is
  shown as "31.1 million" on life/1990.html. Under ordinary rounding these
  would be £133bn and 31.2 million.
- Verdict: **minor** (a rounding convention, not a wrong figure).

### 8. `rec.taxes.2025-26`: "£1,105bn raised in taxes in 2025-26"
- Pages: index, taxes.
- Source: OBR Public finances databank, October 2026, "Receipts (£bn)" AH33
  ("National accounts taxes", GCSU) = 1104.686. All receipts AG33 = 1231.312.
- The figure is for 2025-26 outturn. The page says that other receipts of
  £127bn are not tax, which is correct (1231.312 − 1104.686).
- Verdict: **correct**.

### 9. `rec.big3share.2025-26`: "65% of all tax came from Income Tax, National Insurance and VAT"
- Pages: index, taxes.
- Inputs: Income Tax = PAYE Q33 280.513 + SA R33 54.071 + other S33 −5.246 =
  329.338. NICs AB33 = 204.429. VAT (net of refunds) C33 = 180.326. Their sum,
  714.093, ÷ 1104.686 = 64.64%.
- Related claims checked: "Income Tax raised the most of the three in every
  year from 1999-00 to 2025-26". I recomputed the shares for every year:
  Income Tax was always the largest, with a lowest share of 25.7% in 2017-18
  and a highest of 30.1% in 2024-25, as stated.
- Verdict: **correct**.

### 10. `agg.psnb.2025-26`: "£134bn borrowed to cover spending above receipts"
- Pages: index, taxes.
- Source: OBR "Aggregates (£bn)" O87 (PSNB) = 134.286. TME 1365.598 −
  receipts 1231.312 = 134.286.
- Related claim checked: "Spending was higher than receipts in 68 of the 78
  years from 1948-49 to 2025-26" and "in 65 of the 71 years from 1955-56". I
  counted from "Aggregates (per cent of GDP)" and got 68/78 and 65/71.
- Verdict: **correct**.

### 11. `gdp.psnd.2025-26`: "Debt ... £2,917bn at the end of March 2026, equal to 93.3% of GDP (the OBR's measure, using GDP centred on end-March)"
- Page: taxes.
- Source: OBR Aggregates (£bn) X87 = 2916.8. Aggregates (% of GDP) X82 =
  93.3.
- Note: 2916.8 ÷ the centred-GDP column (3134.69) is 93.05%, not 93.3%. The
  site copies the OBR's published ratio rather than recomputing it, which is
  the right choice. The OBR's ratio uses its own basis.
- Verdict: **correct** (it matches the publisher).

### 12. `rec.gdp.taxes.2025-26`: "Taxes alone were 36.0% of GDP in 2025-26"
- Page: taxes.
- Source: OBR Aggregates (% of GDP) I82 ("National account taxes") = 35.99.
- Related claims checked: receipts were at their lowest share in 1993-94
  (31.2%) and highest in 1949-50 (43.3%). Spending was at its lowest in
  1988-89 (34.4%) and highest in 2020-21 (52.3%). All match.
- Verdict: **correct**.

### 13. `rec.sharechange.nics.1999-00.2025-26`: "The largest rise was in National Insurance contributions: 16.5% to 18.5%"
- Page: taxes.
- Recomputed: NICs share of all tax, 56.935 ÷ 344.3 (1999-00) to 204.429 ÷
  1104.686 (2025-26) = +1.97 points. The next largest rises are Income Tax
  (+1.73), "All other taxes" (+1.66) and CGT (+1.58). So "largest" holds, but
  only narrowly.
- Verdict: **correct**.

### 14. `rec.sharechange.fuel.1999-00.2025-26`: "The largest fall was in Fuel duties: 6.5% of all tax in 1999-00, 2.2% in 2025-26"
- Page: taxes.
- Recomputed: −4.32 points. The next largest falls are alcohol and tobacco
  (−2.35) and Corporation Tax (−0.95). "Largest" holds.
- Verdict: **correct**.

### 15. `hmrc.share.top1.2023 to 2024`: "The top 1% of Income Tax payers owed 27.2% of all Income Tax in 2023 to 2024"
- Pages: index, who-pays.
- Source: HMRC Table 2.4 (July 2026), sheet 2_4_Taxpayer_share_tax, K27 =
  27.2.
- Population: Income Tax payers only, ranked by total income before tax. The
  page says this. Related trend claims checked against the same sheet: the
  1999-00 value was 21.3, the lowest was 20.8 in 2003-04, the 2015-16 value
  was 28.8, the high was 30.7 in 2021-22 and the 2026-27 projection is 26.6.
  The break at 2016-17 (dividend rules) and the missing 2008-09 are both
  disclosed.
- Verdict: **correct**.

### 16. `hmrc.income.top1.2023 to 2024`: "They had 12.4% of all Income Tax payers' income"
- Pages: index, who-pays.
- Source: HMRC Table 2.4, sheet 2_4_Taxpayer_share_inc_pretax, 2023 to 2024
  row, top 1% = 12.4 (income before tax). The claim "higher share of tax than
  of income in every year" holds in every year.
- Verdict: **correct**.

### 17. `etb.t8.gross.all.all`: "Taxes took 33.6% of gross household income on average in 2023/24"
- Pages: index, household-tax.
- Source: ONS ETB FYE2024 reference tables, Table 8, "All taxes", "All
  individuals" = 33.6. Direct 22.9, indirect 10.7.
- Problem: the home page says "That is an average across households". Table 8
  is for all individuals, ranked by equivalised household disposable income.
  The household-tax page words it correctly ("an average across all people,
  using the income and taxes of the household each person lives in").
- Related claim checked: "22.9% in 2023/24, down from 23.2% in 2022/23"
  (FYE2023 Table 8, direct taxes, all individuals = 23.2). Correct.
- Verdict: **minor** (the population wording on the home page).

### 18. `etb.t8.gross.all.q1`: "The lowest-income fifth paid 36.7% of its gross income in tax"; "most of it is indirect tax (21.0%)"
- Pages: index, household-tax, who-pays.
- Source: ETB FYE2024 Table 8, Bottom = 36.7. Indirect = 21.0 and direct =
  15.7, so "most is indirect" is true. Top fifth: 36.2, of which direct is
  28.8, so "most is direct" is true.
- Verdict: **correct**.

### 19. `etb.2a.alltax.q5`: "£51,903 a year in all taxes, on average, by the households of the highest-income fifth of people"
- Page: who-pays.
- Source: ETB FYE2024 Table 2a, Top: total direct taxes 41,215 + total
  indirect taxes 10,688 = 51,903. Bottom: 3,696 + 4,929 = 8,625. Correct.
- Verdict: **correct**.

### 20. `etb.t16.all.2023/24`: "In 2023/24, 53.3% of people lived in households that received more in benefits and services than they paid in taxes"
- Page: who-pays.
- Source: ETB FYE2024 Table 16, 2023/24 row: all 53.3, non-retired 45.8,
  retired 90.1. 1977: 37.0. "The share for retired people was higher than for
  non-retired in every year from 1977": checked for every row, and it holds.
  The break at 2001/02 (top-income adjustment) is disclosed.
- Verdict: **correct**.

### 21. `etb.ret.taxshare.all`: "taxes took 29.4% of retired households' gross income, against 34.0%"
- Pages: who-pays, who-pays-households.
- Recomputed: Table 4a (retired individuals): all taxes 10,363 ÷ gross income
  35,290 = 29.37%. Table 3a (non-retired): 25,652 ÷ 75,556 = 33.95%.
- Related claim checked: "Across the 10 kinds of household, taxes took 27%
  (one retired adult) to 36% (two adults, no children)". I counted the ten
  kinds as Tables 12a, 12b and 12c with the "1 adult (All)" columns. Then
  one retired adult is lowest at 26.9% and two adults with no children is
  highest at 35.8%. (If men and women were listed separately, one
  non-retired man would be 36.5%, but the page shows "All".)
- Verdict: **correct**.

### 22. `spi.age.sharetax.30_64`: "taxpayers aged 30 to 64 were 62% of all Income Tax payers and owed about 79% of all Income Tax"
- Pages: who-pays, who-pays-age.
- Recomputed from HMRC SPI 2023-24 Table 3.2 (number × mean tax by age band):
  61.7% of taxpayers and 79.2% of tax. 65 and over: 23.4% and 13.2%. Under 30:
  14.9% and 7.5%. The bands are rounded, so the page's "about" is the right
  word. The 36.7 million total (C19) is correct.
- Verdict: **correct**.

### 23. `work.rate.2025`: "In April to June 2025, 75.3% of people aged 16 to 64 were in work", "higher than in 51 of the other 54 years shown"
- Pages: life/index, life/work, year pages.
- Source: ONS LF24, row "2025 Q2" = 75.3. Three Q2 values are higher (2018
  75.4, 2019 76.1, 2020 75.4), so "higher than in 51 of the other 54" is
  correct. The range of 65.6 (1983) to 76.1 (2019) is correct. The gender gap
  "39 points in 1971 to 6 points in 2025" is correct (MGSV/LF25).
- Note: LF24's monthly row "2025 JUN" (also April to June) reads 75.2,
  because ONS adjusts its quarterly and three-month series for seasons
  separately. The site uses the quarterly row consistently.
- Verdict: **correct**.

### 24. `earn.real.ft.2021`: "After inflation, pay in April 2025 was about the same as in April 2021 (£761 → £767, +0.8%)"
- Pages: index, life/index, life/earnings.
- Recomputed: ASHE (Nomis NM_30_1, UK, full-time, median gross weekly)
  2021 = 609.8 × CPIH (L522) April 2025 137.7 ÷ April 2021 110.4 = 760.6.
  2025 = 766.6. Change +0.8%.
- "Highest of the 5 years measured the same way": the real values for
  2021-2025 are 760.6, 742.7, 737.3, 758.6 and 766.6, so this is correct. The
  break at 2021 (SOC 2020) is handled: there is no comparison across it.
  The gender gap of "£115 in 2021 to £105 in 2025" is correct (814.6 − 709.8
  = 104.8).
- Verdict: **correct**.

### 25. `house.owners.2024`: "65% of households in England owned their home, 2024-25", "higher than in 10 of the other 16 years measured the same way"
- Pages: index, life/index, life/housing.
- Source: EHS FT1101, D103 (2024-25) = 64.83. Of the EHS years 2008-09 to
  2023-24, ten are lower, so the count is correct. The range of 57% (1981)
  to 71% (2003) uses the LFS-based rows of the same table, and the break at
  2008-09 is shown.
- Verdict: **correct**.

### 26. `house.mortpay.2024`: "the average mortgage payment £242 (a week)"
- Pages: life/index, life/housing, life/2024.
- Source: EHS FA2555, 2024-25, I13 ("all mortgage types", mean) = 241.51.
- Problem: that row covers 7,060 thousand households. The same table's "all"
  rows (by age of HRP and by economic status) cover 7,318 thousand
  households, the full number of mortgagors in FT1101, and give a mean of
  £236.43. Both are EHS figures, and the table's footnote says the
  type-of-mortgage row includes people who did not know their type. The
  page does not say which base it uses.
- Verdict: **minor** (the two bases differ by about £5 a week).

### 27. `hol.abroad.per100.2025`: "In 2025, Great Britain residents made 58.4 million holiday visits abroad, about 86 for every 100 residents"
- Pages: index, life/index, life/holidays.
- Source: ONS Travel and tourism 2025 (published 16 October 2026), Table 2,
  C48 "Total World / Holiday - All" = 58,396,000. GB population mid-2025
  (GBPOP) = 67,555,500, giving 86.4. The numerator and denominator are both
  GB residents. The Europe share is 48,376 ÷ 58,396 = 82.8%. Top countries in
  2025 (Table 7): Spain 15.6m, France 5.9m, Greece 4.3m, then Italy 3.6m.
  Correct.
- Break handling: the 2019 UK-resident figure of 58.7m is shown but
  correctly "not compared". The per-100 series to 2023 (GMAF ÷ UKPOP: 2023 =
  125.7) has only 2017 (132.3), 2018 (136.6) and 2019 (139.7) above it, so
  "higher than in 40 of the other 43" is correct. GBTS 32.1m domestic holiday
  trips = toplines p10, Britain, Holidays 2025. Correct.
- Verdict: **correct**.

### 28. `afford.ratio.ew.2025`: "In 2025, the middle-priced home sold in England and Wales cost £295,000 ... 7.55 times a year's earnings ... highest 8.95 times in 2021"
- Page: life/house-prices.
- Source: ONS affordability (workplace-based) Table 1c, England and Wales:
  2025 = 7.55, 2021 = 8.95 (the series maximum), 1999 = 3.89. Table 1a 2025
  = £295,000 and Table 1b = £39,059. London 10.61 and North East 5.00, as
  stated.
- Problem: the price is the median for the year ending September 2025, and
  the earnings are for April 2025. The chart says this, but the lead
  sentence says only "In 2025".
- Verdict: **minor**.

### 29. `jobs.share.Q.2026`: "The industries with the most jobs were health and social work (13.7%), shops, wholesale and vehicle repair (12.5%) and professional, scientific and technical (9.5%)"
- Page: life/jobs-by-industry.
- Source: ONS JOBS02 (September 2026), "WFJ SA" row 198 (June 2026 (p)):
  Q = 5,028 ÷ all jobs 36,734 = 13.69%. The ranking of the next industries
  is G 12.51, M 9.54, P 8.51, N 8.09, so the top three are correct.
  Manufacturing: 6,732 ÷ 26,988 = 24.9% (June 1978) to 2,460 ÷ 36,734 = 6.7%.
  "Health rose most, manufacturing fell most" is correct (+6.6 points against
  professional +6.0; manufacturing −18.3). The June 2026 figure is labelled
  provisional.
- Verdict: **correct**.

### 30. `borrow.imf.GBR.2024`: "In 2024, UK government debt was 101.3% of GDP, the second lowest of the seven G7 countries"
- Page: borrowing.
- Source: IMF DataMapper GG_DEBT_GDP 2024: JPN 236.7, ITA 135.3, USA 120.8,
  FRA 113.1, CAN 110.8, GBR 101.3, DEU 63.9. The ranking and the order given
  ("lower than Japan, Italy, the United States, France and Canada and higher
  than Germany") are correct.
- Verdict: **correct**.

---

## Other claims checked (not in the 30)

- Spending by area, ten-year change after inflation (PESA 4_3): all ten areas
  match. Recreation falls 4%; housing rises 64%, the largest percentage rise.
- International: the UK's largest COFOG differences from the OECD average in
  2024 (health +1.77, economic affairs −0.99) are correct. UK tax was 34.4%
  of GDP and the OECD average 34.1% in 2024.
- Housing places: private renting was higher in 2025 than in 2008 in all 10
  areas (LT109). This is correct.
- The compare page says "the UK economy shrank by more than 6%" in 2008-09.
  This matches the wording of the ONS article.
- Worked example (£30,000, 2026-27): Income Tax £3,486, NICs (576.92 − 242)
  × 8% × 52 = £1,393, total 16%. The arithmetic is correct. It is labelled
  as an illustration.
- Class sizes: England primary 26.4 (January 2025), Wales infant 24.7
  (Table_16 F4) and Scotland 23.1 (Table 2.10, 2025 row) all match. The
  Scottish figure is for the September 2025 census and is labelled as such.
