# Audit 11 – fact check: 30 headline claims

Method: read the built pages in `site/`, picked 30 headline claims (top-of-page
numbers, "largest"/"highest" claims, after-inflation figures, shares and
per-household figures, calculated values preferred). For each, checked the
figure record in `site/data/facts.json` / `site/figures/` and the downloaded
source copy it cites (`data/raw/`, `data/payers/raw/`, `data/fetched/`), looking
for problems a number check cannot catch: period, population/place, units,
"largest" claims, comparisons across breaks. ODS sources were converted to xlsx
locally to read them.

Summary: **1 material problem, 5 minor problems.** All 30 ids resolve to a fact
record; the values I recomputed from the source files match the page.

## Claims

| # | id | Page | Claim as stated | Context check | Result |
|---|----|------|-----------------|---------------|--------|
| 1 | spend.cash.tme.2025-26 | index, spending | £1,360bn spent by the UK public sector in 2025-26 | PESA 2026 Table 4.2 row 27 (TME), 2025-26 outturn = 1360.1. UK, whole public sector, cash. Page notes OBR databank gives £1,366bn on its own basis. | OK |
| 2 | spend.per100.social.2025-26 | index, spending | £33 of every £100 spent on services went on social protection, the largest area | 407.3 ÷ 1227.6 (services, not TME — page says so). Social protection is the largest of the 10 COFOG functions in 4_2 col X. | OK |
| 3 | spend.per100.health.2025-26 | spending | £21 on health, "the next largest" | 257.5 ÷ 1227.6; health is second (next is GPS 165.5). | OK |
| 4 | spend.per100.debt_interest.2025-26 | index, spending | Debt interest £11 of every £100, inside general public services | 4_2!X9 130.3 ÷ 1227.6. Gross interest paid, correctly flagged as not the OBR/IFS net figure. | OK |
| 5 | spend.realchange.tme.2003-04.2025-26 | spending | After inflation, total spending 54% higher than in 2003-04 | 4_3 (GDP-deflator real terms, 2025-26 prices) 1360.1 ÷ 882.0. TME includes Network Rail in all years (PESA fn 3), so no break at total level. | OK |
| 6 | spend.perhousehold.tme.2025-26 | spending | About £46,895 per household (29.0m UK households, Apr–Jun 2025) | 1360.1bn ÷ 29.003m (ONS families & households Table 5, LFS). Financial-year spending over a quarter's household count – labelled as an average across everyone. | OK |
| 7 | spend.realchange.health.2015-16.2025-26 | spending | Health 34% rise after inflation, 2015-16 to 2025-26 | 4_3 192.1 → 257.5. Ten-year window lies after the 2011-12 (education) and 2015-16 (Network Rail) breaks. | OK |
| 8 | rec.taxes.2025-26 | index, taxes | £1,105bn raised in taxes in 2025-26 | OBR databank Receipts!AH33 "National accounts taxes" (GCSU) 1104.686; includes NICs; non-tax receipts (interest/dividends, GOS) excluded. | OK |
| 9 | rec.big3share.2025-26 | index, taxes | Income Tax, NI and VAT raised 65% of all tax | (329.338 + 204.429 + 180.326) ÷ 1104.686. Income Tax = PAYE + SA + other; VAT is OBR's "VAT (net of VAT refunds)" with refunds in "other". | OK |
| 10 | agg.psnb.2025-26 | index, taxes | Borrowing covered another £134bn | Aggregates!O87 PSNB = TME 1365.6 − receipts 1231.3. | OK |
| 11 | rec.gdp.taxes.2025-26 | taxes | Taxes alone were 36.0% of GDP ("tax burden") | 1104.686 ÷ nominal GDP 3069.8; matches the databank's own "Aggregates (per cent of GDP)" sheet, 2025-26 national accounts taxes 35.99. | OK |
| 12 | agg.perhousehold.psnd.2025-26 | taxes | Debt £2,917bn, ≈£100,569 per household | Aggregates!X87 PSND 2916.8 ÷ 29.003m. Page says it is owed by the public sector, not households. | OK |
| 13 | rec.perhousehold.taxes.2025-26 | taxes | Tax ≈ £38,089 per household | 1104.686bn ÷ 29.003m; page says it includes tax paid by businesses. | OK |
| 14 | rec.sharechange.fuel.1999-00.2025-26 | taxes | Largest fall in share was fuel duties, 6.5% → 2.2% | 22.515/344.323 → 24.559/1104.686 = −4.3 pts; next largest fall alcohol & tobacco −2.4. "Largest" holds. | OK |
| 15 | hmrc.share.top1.2023 to 2024 | index, who-pays | 27.2% of all Income Tax was **paid** by the top 1% | HMRC Table 2.4 is Income Tax **liabilities** (owed); who-pays body text says "owed", headline/home say "paid". | Minor (m2) |
| 16 | hmrc.income.top1.2023 to 2024 | index, who-pays | Top 1% had 12.4% of taxpayers' income | Table 2.4 pre-tax income share; population is taxpayers only (stated). Threshold £207,000 matches 2_4_Taxpayer_inc_quantiles!K27. | OK |
| 17 | etb.2a.alltax.q5 | who-pays | £51,903 a year in all taxes, households of highest-income fifth of people, 2023/24 | ETB FYE2024 Table 2a (direct + indirect). Wording correctly says "households of … fifth of people". | OK |
| 18 | etb.t16.all.2023/24 | who-pays | 53.3% of people lived in households receiving more in benefits than they paid in taxes | Table 16 "All individuals (%)" 2023/24 = 53.3. Population is individuals – matches. Break at 2001/02 (top-income adjustment) is disclosed. | OK |
| 19 | etb.ret.taxshare.all | who-pays | Taxes took 29.4% of retired people's gross income vs 34.0% | Table 4a (retired **individuals**, household averages) (4447+5916)/35290. Page heads this "Retired households paid less tax"; Table 4a's unit is retired individuals ranked by quintile, so "retired households" is loose. | Minor (m5) |
| 20 | spi.age.sharetax.30_64 | who-pays | Taxpayers aged 30–64 owed about 79% of Income Tax, 2023-24 | SPI Table 3.2 count × mean tax, summed over age bands; shares sum to 99.9%. | OK |
| 21 | etb.t8.gross.all.all | index, household-tax | 33.6% of gross household income went on tax, 2023/24 | Table 8!I15 "All individuals". Labelled as an average, not a tax rate. | OK |
| 22 | etb.t8.gross.indirect.q1 | index, household-tax | Lowest fifth: indirect tax 21.0% of gross income (most of its 36.7%) | Table 8!D9 21.0 of D15 36.7; highest fifth direct 28.8 of 36.2. | OK |
| 23 | work.rate.2026 | index | 75.1% of people aged 16–64 in work, Apr–Jun 2026, UK | LF24 "2026 Q2". Seasonally adjusted LFS. | OK |
| 24 | earn.real.ft.2021 | index, life, earnings | Middle full-time pay £761 (Apr 2021) → £767 (Apr 2025), April 2025 prices, "about the same" | 609.8 × CPIH(Apr 25 137.7) ÷ CPIH(Apr 21 110.4). Compared within the SOC2020 stretch only (2021 recoding). 2025 is provisional. | OK |
| 25 | house.owners.2024 | index, life, housing | 65% of households in England owned their home, 2024-25 | EHS FT1101 row 103 col D 64.83 (owner occupiers, all). England only, households – stated. | OK |
| 26 | afford.ratio.ew.2025 | house-prices | Home cost 7.55× a year's earnings in 2025 vs 3.89 in 1999; highest 8.95 in 2021 | 2021 is the max of the E&W series (8.95). 1999 start is disclosed as first year on same earnings basis; price is year to September. | OK |
| 27 | hol.world.holiday.2025 | index, life, holidays | 58.4 million holiday visits abroad by **Great Britain** residents, 2025 | OTT 2025 Table 2!C48 "Total World, Holiday – All" 58,396,000. Coverage is GB from 2024 (NI now NISRA) – page says GB. | OK |
| 28 | hol.abroad.per100.2025 | life, holidays | About 86 holiday visits for every 100 residents | 58.396m ÷ GB mid-2025 population (consistent GB numerator and denominator). | OK |
| 29 | hol.cty.spain.all.2025 | holidays | "Spain has been the most visited country … In 2025 Spain had 19.1 million visits, then France (9.1m) and Italy (5.7m)" | The paragraph is about holiday visits, but these are **all-purpose** visits (OTT 2025 Table 7 col R). Holiday-only visits: Spain 15.6m, France 5.9m, Italy 3.6m (Table 7 col C rows 38, 22, 27). | **Material (M1)** |
| 30 | school.primary.2026 | index, schools | 26.1 pupils in the average state primary class in England, January 2026 | DfE class-size API, AY 2025/26 national primary. Chart text "rose until 2016, then fell" – see m3. | OK (m3 on wording) |

## Problems

### Material

**M1 – Holidays page: country figures are all-purpose visits presented as holidays.**
`life/holidays.html`, lead paragraph. Every other number in the paragraph is a
holiday visit (58.4m holiday visits, 83% in Europe, 58.7m in 2019, 8.9m in
2021), then: "Spain has been the most visited country in every year with
figures by country. In 2025 Spain had 19.1 million visits, then France (9.1
million) and Italy (5.7 million)." The ids `hol.cty.spain.all.2025`,
`hol.cty.france.all.2025`, `hol.cty.italy.all.2025` are "main country visited;
all purposes" (OTT 2025 Table 7, column R "All Purposes Visits"). The holiday
column of the same table (column C) gives Spain 15,577,000, France 5,869,000,
Italy 3,643,000. A reader will take Spain as having 19.1 million of the 58.4
million holidays (33%), when the holiday figure is 15.6 million (27%); France's
is overstated by more than half. The ranking (Spain, France, Italy) is the same
on either measure, so "most visited" itself holds. A number check passes
because 19,067,000 is in the source. The table further down the page does split
"All visits" from "Of which holidays", so the fix is to the lead sentence only
(say "visits for any purpose" or use the holiday column).

### Minor

**m1 – Holidays: a comparison across a break in the chart headline.** The
holiday chart is headed "Holiday visits abroad by UK residents rose until 2019,
fell in 2021, then rose back to about the 2019 level". The latest point (2025,
58.4m) is GB residents on the new method, and the 2019 point (58.7m) is UK
residents on the IPS. The chart note says the lines break at 2024 and 2025 "so
values either side are not compared", yet the headline compares them, and
calls the series "UK residents" although it includes GB-only years. A second
headline, for the IPS chart since 1980, says visits "rose back to about the 2019
level" when 2023 was 126 per 100 against 140 in 2019 (about 10% lower).

**m2 – Who pays: "paid" vs "owed".** The home page and the who-pays headline say
27.2% of Income Tax "was paid by" the top 1%. HMRC Table 2.4 is Income Tax
liabilities (owed for the year). The who-pays body says "owed", so the two
statements are inconsistent. The number is unaffected.

**m3 – Class sizes: "rose until 2016, then fell".** English primary class sizes
were 27.1 in every year from 2016 to 2019 and began to fall in 2020 (27.0). The
heading and the chart text ("to a high of 27.1 in 2016, then fell") suggest the
fall began after 2016. Likewise secondary's "low of 20.1 in 2014" is tied with
2015.

**m4 – Borrowing page: market yield described as what the government paid.**
`borrowing.html`: "the UK government paid an average of 4.58% a year to borrow
for 10 years" uses the OECD long-term interest rate (10-year gilt yield, yearly
average). That is the market rate on 10-year gilts in 2025, not the average rate
the government paid on its borrowing. Reading it as the cost of the debt would
overstate it. The G7 ranking (UK highest) is correct on the data.

**m5 – Who pays, section 3: "retired households".** The £10,363 vs £25,652 and
29.4% vs 34.0% come from ETB Tables 4a/4b, which are for retired and non-retired
*individuals*, averaging the households they live in. The page says "Retired
households paid less tax … they are smaller". That is loose rather than wrong:
the figures are person-weighted household averages, not a count of households.

## Checked and found sound (not counted as problems)

- "Spending was higher than receipts in 68 of the 78 years" (1948-49 to
  2025-26) and "65 of the 71 years" (real, from 1955-56) both recompute from the
  fact records.
- Spending-areas: Education (2011-12 student-loan break) and Economic affairs
  (Network Rail from 2015-16) are correctly excluded from 2003-04 comparisons.
- Household-tax: the lowest-income fifth's share was below the highest-income
  fifth's in 1977–1987 and above it in 1988–2017/18 on the old method; within
  5 points with order changing on the new method. True on the data.
- Work: 75.3% (2025) "higher than in 14 of the other 17 years"; men/women gap
  11.9 → 6.0 points and 39 → 6 points. True.
- Earnings by nation/region "largest rise/fall" statements, the employment by
  nation "highest England, lowest Wales" and "largest rise NI / London". True.
- Jobs by industry: health and social work, retail/wholesale and professional
  are the top three in June 2026; health rose most and manufacturing fell most
  since 1978 across all 20 sections. True.
- International/borrowing G7 rankings (tax 5th of 6, spending 4th of 7, IMF debt
  second lowest, 10-year yield highest). True on the data.
- Worked example (£30,000, 2026-27): £3,486 Income Tax + £1,393 NI = £4,879, 16%,
  28% marginal. Arithmetic correct.
