# Fact-check, audit 10: 30 headline claims

Scope: built pages in `site/` (site version 10255dc). For each claim I checked the figure record (`site/data/facts.json`, the data behind `site/figures/`) and, where possible, the official file it points to (`data/raw/`, `data/fetched/`, `data/payers/raw/`). I recomputed every calculated figure from its inputs. I did not read `builder/`, `docs/` or any review.

Severity: **material** means a reader would come away believing something false. **Minor** means imprecise or inconsistent but not misleading on the main point.

## The 30 claims

| # | Fact id | Page | Claim as stated | Checks beyond the number | Result |
|---|---|---|---|---|---|
| 1 | spend.cash.tme.2025-26 | index, spending | "£1,360bn spent by the UK public sector in 2025-26" | PESA 2026 Table 4.2, cell X27 = 1,360.1, labelled outturn. Period and scope (TME, UK public sector) are right. | OK |
| 2 | spend.per100.social.2025-26 | index, spending | "£33 of every £100 spent on services went on social protection, the largest area" | 407.3 ÷ 1,227.6 = 33.2. It is the largest COFOG area in every year (also checked 2020-21: 299.3 against health 218.6). The denominator is services, not TME, and the page says so. | OK |
| 3 | spend.per100.debt_interest.2025-26 | index, spending | "£11 of every £100 went on debt interest" | 130.3 ÷ 1,227.6 = 10.6, which rounds to £11. In the hero box the denominator is dropped ("of every £100"); measured against TME it is £9.6. Gross, not net, interest; the page explains this. | Minor (m6) |
| 4 | spend.perhousehold.tme.2025-26 | spending | "about £46,895 per household" | 1,360.1bn ÷ 29.003m households (LFS, April to June 2025, UK) = £46,895. Population and period are labelled, and the page says it is an average. | OK |
| 5 | spend.realchange.tme.2003-04.2025-26 | spending | "total spending in 2025-26 was 54% higher than in 2003-04" after inflation | 1,360.1 ÷ 882.0 = 1.542 (PESA 4.3, GDP deflator). TME includes Network Rail in every year (PESA note 3), so there is no break. | OK |
| 6 | spend.oldage.2025-26 | spending | "Pensions in old age cost £155bn in 2025-26" | PESA 5.2, G107 "of which: pensions" = £154,858m. The page says it covers more than the State Pension. | OK |
| 7 | spend.gdp.order.2025-26 | spending-areas | "the largest fall [as a share of GDP, 2003-04 to 2025-26] was Public order and safety (2.1% to 1.8%)" | Recreation, culture and religion also fell 0.3 points (0.8% to 0.5%, PESA 4.4), and fell more in proportional terms (−38% against −14%). This "largest" is a tie, not a single largest. | Minor (m2) |
| 8 | rec.taxes.2025-26 | index, taxes | "£1,105bn raised in taxes in 2025-26" | OBR databank October 2026, Receipts AH33 "National accounts taxes" = 1,104.686. The OBR marks 2025-26 as outturn. | OK |
| 9 | rec.big3share.2025-26 | index, taxes | "Income Tax, NI and VAT raised 65% of all tax" | (329.3 + 204.4 + 180.3) ÷ 1,104.7 = 64.6%. Income Tax is the sum of PAYE, self assessment and other Income Tax (Q+R+S). VAT is net of refunds. | OK |
| 10 | agg.psnb.2025-26 | index, taxes | "Borrowing covered another £134bn" | Aggregates O87 = 134.3. It equals TME (1,365.6) minus receipts (1,231.3). | OK |
| 11 | gdp.psnd.2025-26 | taxes | "£2,917bn ... equal to 93.3% of a year's GDP" | £2,917bn ÷ 2025-26 GDP (£3,070bn) would be 95.0%. The OBR's 93.3% uses GDP centred on end-March (note 2 on the sheet), so the published figure is right as quoted. | OK |
| 12 | rec.gdp.taxes.2025-26 | taxes | "Taxes alone were 36.0% of GDP ... the 'tax burden'" | 1,104.686 ÷ 3,069.8 = 35.99%. This matches column I (National accounts taxes) of the OBR "per cent of GDP" sheet. | OK |
| 13 | rec.share.nics.2025-26 | index, taxes | "The largest rise [in share of all tax, 1999-00 to 2025-26] was in National Insurance: 16.5% to 18.5%" | I recomputed every group: NICs +1.97, Income Tax +1.73, other taxes +1.66, CGT +1.58, council tax +0.78. Fuel duty, −4.32, is the largest fall. Both "largest" claims hold. | OK |
| 14 | thist.sharechange.nics.1999-00.2022-23 | tax-history | "The largest rise was in National Insurance (+2.5 points)" in share of all receipts | The "Everything else" group rose more, from 19.3% to 22.3% (+3.0 points). It is charted on the same page and left out of this ranking without a word. The share-of-GDP view on the same page names "Everything else" as the largest rise. The NICs narrative also says the high was 17.1% in 2009-10, but the series peaked at 18.2% in 2020-21. | Minor (m3, m4) |
| 15 | hmrc.share.top1.2023 to 2024 | index, who-pays | "27.2% of all Income Tax was paid by the top 1% of Income Tax payers in 2023 to 2024" | HMRC Table 2.4 (July 2026) K27 = 27.2. The population is taxpayers only, as stated. 2023-24 is outturn and later years are projections, as stated. | OK |
| 16 | hmrc.income.top1.2023 to 2024 | index, who-pays | "They had 12.4% of all Income Tax payers' income" | HMRC Table 2.4. The top-1% threshold of £207,000 and the bottom-50% threshold of £29,700 also match. | OK |
| 17 | etb.2a.alltax.q5 | who-pays | "£51,903 a year in all taxes, on average, by the households of the highest-income fifth of people, 2023/24" | ETB FYE2024 Table 2a: 41,215 + 10,688. The table covers fifths of individuals, and the wording ("households of ... people") is right. | OK |
| 18 | etb.t8.gross.all.all | index, household-tax | "33.6% of gross household income, on average across everyone, in 2023/24" | Table 8, I15 = 33.6. The page says it is not a tax rate. | OK |
| 19 | etb.t8.gross.all.q1 | index, household-tax | lowest fifth 36.7% against highest 36.2%; "most of this is indirect tax" | Table 8: indirect 21.0 out of 36.7. The page also claims "within five points on the current method": I checked every year from 2017/18 to 2023/24 (largest gap 4.5 points, in 2018/19). On the older method, the lowest fifth was below the highest in 1977 to 1987 and above it from 1988 to 2017/18, as stated. | OK |
| 20 | etb.t16.all.2023/24 | who-pays | "53.3% of people lived in households that received more in benefits and services than they paid in taxes" | Table 16 = 53.3. "Retired higher than non-retired in every year since 1977" holds. | OK |
| 21 | etb.ret.taxshare.all | who-pays, who-pays-households | "taxes took 29.4% of [retired households'] gross income, against 34.0%" | Table 4a: (4,447 + 5,916) ÷ 35,290 = 29.4%. Table 3a gives 34.0%. Household size: 7,199k households for 11,154k people = 1.5. | OK |
| 22 | spi.age.sharetax.30_64 | who-pays, who-pays-age | "aged 30 to 64 were 62% of all Income Tax payers and owed about 79%" | SPI 2023-24 Table 3.2: 22,630k ÷ 36,700k taxpayers = 61.7%. Tax shares add to 79.2%; 65+ = 23% of taxpayers and 13% of tax; under 30 = 15% and 8%. All check. | OK |
| 23 | borrow.imf.GBR.2024 | borrowing | "UK debt 101.3% of GDP, the second lowest of the seven G7 countries" | IMF GG_DEBT_GDP 2024. Order: Japan, Italy, US, France, Canada, UK, Germany. Calendar year, general government, as stated. | OK |
| 24 | borrow.yieldm.GBR.2026-09 | borrowing | "In September 2026 ... 5.24%, the highest of the G7"; "over 2025 it averaged 4.58%, the highest" | OECD monthly averages: UK 5.24, US 4.99 and lower for the rest. The 2025 annual average (UK 4.58, US 4.29) also holds. | OK |
| 25 | borrow.int.GBR.2024 | borrowing | "2.2% of GDP, the third highest of the G7"; "higher than the OECD average in every year from 2007 to 2024" | Checked every year. The closest is 2009 (1.58 against 1.54), and it still holds. | OK |
| 26 | intl.tax.GBR.2024 | international | "34.4% of GDP, close to the OECD average of 34.1%"; "Of the 36 countries ... 21 collected a larger share" | Counted 21 above the UK. Hungary is 34.354 against the UK's 34.367, so it is correctly below. The UK was above the average in 35 of 60 years, which checks. | OK |
| 27 | intl.spend.GBR.2024 | international | "46.2% ... above the average of 44.5%"; "16 [of 37] spent a larger share"; "fourth highest of the G7" | Counted 16 above the UK; Turkey is missing, which the page says. Above the average in 11 of the 18 years from 2007 to 2024, which checks. | OK |
| 28 | hol.abroad.per100.2025 | life/index, holidays | "Great Britain residents made 58.4 million holiday visits abroad, about 86 for every 100 residents" | OTT 2025 Table 2 covers GB residents (not UK); the denominator is the GB population (67.56m), so they match. 2019 (88) used UK residents and the UK population, and the pages mark the break and do not compare the two. 2025 is a full year (survey published 16 October 2026). | OK |
| 29 | earn.ft.2025 | index, life/earnings | "£767 a week ... about the same as in April 2021 (£761 in April 2025 prices)"; "highest of the 5 years measured the same way" | Nomis ASHE resident analysis gives 766.6. CPIH April 2025 ÷ April 2021 = 137.7 ÷ 110.4. The SOC break in 2021 is respected. The +1.0% change from 2011 to 2020 and +1.1% from 2006 to 2010 also check. | OK |
| 30 | school.large.primary.2026 | life/schools | "The share of primary pupils in classes of more than 30 fell until January 2011, rose until January 2020, fell in January 2021, then rose"; narrative: "rose to a high of 13.1% in January 2020 ... then rose to 12.6% in January 2026" | **False shape.** DfE class-size API (the file the record cites): 13.06% in 2020, 13.14% in 2024, **13.31% in January 2025** (the highest since 2008), then **12.65% in January 2026**. So 2020 was not the high, and the latest movement is a fall of 0.7 points, not a rise. | **Material (M1)** |

## Findings

### Material

**M1. The life/schools chart describes the primary large-class share as rising since 2021 with a 2020 peak, but it peaked in January 2025 and fell in January 2026.**
- Page: `life/schools.html`, section "How many pupils are in classes of more than 30?": the chart headline and the text summary.
- Evidence, from `data/life/sources/schools/dfe-national-class-sizes-1.0.json` as the figure records compute it: primary pupils in classes of 31+ as a share of all primary pupils were
  - 2019: 13.00%
  - 2020: 13.06%
  - 2021: 11.55%
  - 2022: 11.86%
  - 2023: 12.63%
  - 2024: 13.14%
  - 2025: 13.31%
  - 2026: 12.65% (510,316 + 33,490 out of 4,084,205 pupils in 2025; 470,774 + 31,820 out of 3,974,132 in 2026).
- What the page gets wrong:
  - The summary names 13.1% (2020) as "a high", but 2024 and 2025 were both higher.
  - It ends "then rose to 12.6%", which hides the 2026 fall.
  - The headline says the share "then rose", so a reader concludes the share is still going up, when the newest figure fell by 0.7 points.
- The secondary series (rising to 16.4%) is described correctly.

### Minor

- **m1. "Latest figure" on the home page is not the latest.** The home page says "Each topic shows the latest figure", then shows:
  - work for April to June 2025 (75.3%), although `ons/lf24.csv` holds 2026 Q2 (75.1%);
  - class sizes for January 2025 (26.4), although the DfE file holds January 2026 (26.1), which `life/schools.html` itself shows.

  This is consistent with the "year by year to 2025" framing, but the word "latest" is wrong.
- **m2. A "largest fall" that is a tie** (claim 7). On the spending-areas page (share of GDP), public order and safety and recreation, culture and religion both fell 0.3 points. The page names only one of them.
- **m3. tax-history leaves "Everything else" out of the "largest rise" ranking** (claim 14). Everything else rose 3.0 points, more than NICs (2.5), and the same page's GDP view names it as the largest rise.
- **m4. tax-history's NICs narrative misses the 2020-21 peak.** It names 17.1% in 2009-10 as the high, but the series peaked at 18.2% in 2020-21 and has since fallen to 17.5%. Elsewhere the narratives add "In between: highest ..." for such cases; here they do not.
- **m5. tax-history's GDP headline says Income Tax was "between 9% and 10% of GDP in every year from 1999-00 to 2022-23".** In 2012-13 to 2019-20 it was 8.55% to 8.84%. This is true only after rounding to whole percent.
- **m6. The spending hero box drops the denominator** (claim 3). It says "£11 of every £100 went on debt interest"; this is £11 per £100 spent on services, and per £100 of total spending it is £9.6.
- **m7. household-tax gives the method change in two different ways.** One sentence says households were ranked "to 2017/18" and another says people were ranked "from 2017/18". The chart, the series and the 2017/18 bridge sentence treat 2017/18 as the last older-method year and 2018/19 as the first current-method year.
- **m8. Compare pages say the employment rate "1971 to 2025, same method".** The work page itself says the LFS began in 1973, was not quarterly before 1992, and that 1971 and 1972 come before the survey existed.
- **m9. spending-history and the spending page report debt interest on different bases.** spending-history gives debt interest as 2.0% of GDP in 2021-22 (£47.6bn, OBR historical database column "Debt Interest", ONS code NMFX) and says its 2020-21 and 2021-22 figures come from PESA. PESA 2026 (spending page) has gross debt interest of £72.7bn (3.0% of GDP) for 2021-22, and £42.3bn against £25.1bn for 2020-21. The historical series is a different, apparently net, measure. The page labels it only "interest on government debt", so a reader comparing the two pages sees a 1-point gap with no explanation beyond "can differ".
- **m10. life/earnings calls an unchanged figure a fall.** "the largest fall was Northern Ireland (£716 to £716)". The unrounded values differ slightly, but as shown it reads as no change, labelled a fall.

## Checked and found correct (beyond the 30)

- Tax and borrowing per person and per household on the taxes page.
- Spending per £100 for every area.
- All ten-year real changes by area.
- The deficit-year counts (68 of 78, and 65 of 71).
- The older-method household-tax turning points.
- Retired and household-type tax shares (Table 12a/b/c column mapping checked).
- Workforce-jobs and regional private-renting "largest" claims.
- House price ratios, including Wales's 2007 peak (6.59 against 6.57 in 2021).
- Spain as the most visited country in every year.
- GBTS 2025 holiday trips (32.1m for Britain, toplines page 10).
- The NI and Income Tax worked example for 2026-27 (£242 and £967 thresholds, as on the GOV.UK page).
- The "higher than in N of the other years" counts in the sparklines: work 2025 (14 of 17), work 2020 (15 of 17), private renting (9 of 16), primary class size (2 of 17).

Material findings: 1
