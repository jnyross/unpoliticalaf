# Audit 13: fact-check claims

Built site checked: `site/` at version 7ab0f27. Each claim was checked against its figure record in `site/figures/` and `site/data/facts.json`, and against the publisher's file kept in the repository (`data/raw/`, `data/payers/raw/`, `data/fetched/`). I recalculated every derived figure from its inputs. I did not read `builder/`, `scripts/` or any other part of `docs/`.

**Result: 1 material problem and 6 minor problems.** The 30 ids are in `ids.txt`. Problems are listed in full at the end.

## The 30 claims

| # | id | Page(s) | Claim as stated | Context checks (period, population, units, "largest", breaks) | Verdict |
|---|----|---------|-----------------|------------------------------------------------------------|---------|
| 1 | spend.cash.tme.2025-26 | index, spending | "£1,360bn spent by the (UK) public sector in 2025-26" | PESA 2026 Table 4.2 X27, TME 1,360.1, outturn. UK, whole public sector. The taxes page gives £1,366bn from OBR and says why the two differ. | OK |
| 2 | spend.per100.social.2025-26 | index, spending | "Of every £100 spent on services … social protection … £33, the largest area" | 407.3 ÷ 1,227.6 = 33.2. The base is spending on services, not TME, and the page says so. Social protection is the largest COFOG function in 4_2. | OK |
| 3 | spend.per100.health.2025-26 | index, spending | "health, the next largest: £21" | 257.5 ÷ 1,227.6 = 21.0. Health is second, ahead of general public services (13.5). | OK |
| 4 | spend.per100.debt_interest.2025-26 | index, spending | "debt interest (£11 of the £13)" | 4_2 row 9 "of which: public sector debt interest" 130.3 ÷ 1,227.6 = 10.6. This is gross interest, and the page says so. | OK |
| 5 | spend.realchange.tme.2003-04.2025-26 | spending | "After adjusting for rising prices, total spending in 2025-26 was 54% higher than in 2003-04" | PESA Table 4.3 (2025-26 prices): 1,360 ÷ 882 − 1 = 54.2%. GDP deflator, labelled. | OK |
| 6 | spend.perhousehold.tme.2025-26 | spending | "about £46,895 per household" | 1,360.1bn ÷ 29,003k. The household count is ONS Families and Households Table 5 B21 (UK private households, April to June 2025), checked in the xlsx. The page explains it is an average. | OK |
| 7 | spend.realchange.health.2015-16.2025-26 | spending | "Health 34% rise" over ten years, after inflation | 192.1 → 257.5 = +34.0%. A fixed ten-year window, in PESA real terms. | OK |
| 8 | spend.oldage.2025-26 | spending | "Pensions in old age cost £155bn in 2025-26" | PESA 5.2 G107 is "of which: pensions" under "10.2 Old age" (154,858 £m), checked in the xlsx. The page notes that it covers more than the State Pension. | OK |
| 9 | rec.taxes.2025-26 | index, taxes, who-pays | "£1,105bn raised in taxes in 2025-26" | OBR databank, Receipts (£bn) AH33 "National accounts taxes" 1,104.7. See minor problem M2 on how the parts are grouped. | OK (minor M2) |
| 10 | rec.big3share.2025-26 | index, taxes | "Income Tax, National Insurance and VAT raised 65% of it" | (329.3 + 204.4 + 180.3) ÷ 1,104.7 = 64.6%. VAT is net of the £30.5bn of VAT refunds (see M2). | OK (minor M2) |
| 11 | agg.psnb.2025-26 | index, taxes | "Borrowing covered another £134bn" | Aggregates (£bn) O87, PSNB 134.3. Equals TME 1,365.6 − receipts 1,231.3. | OK |
| 12 | rec.gdp.taxes.2025-26 | taxes | "Taxes alone were 36.0% of GDP … the 'tax burden'" | Matches the OBR "National account taxes" % of GDP column (35.99) in the raw xlsx. | OK |
| 13 | gdp.psnd.2025-26 | taxes | "93.3% of GDP (the OBR's measure, … GDP centred on end of March)" | Aggregates (% GDP) X82. Centred GDP is correctly described. | OK |
| 14 | agg.perhousehold.psnd.2025-26 | taxes | "about £100,569 per household" of debt | 2,916.8bn ÷ 29,003k. The page says it is owed by the public sector, not by households. | OK |
| 15 | rec.sharechange.nics.1999-00.2025-26 | taxes | "The largest rise was in National Insurance: 16.5% to 18.5%" (+2.0 pts) | Recomputed every category. Income Tax and "all other" are +1.7 and CGT is +1.6, so NICs is the largest. Endpoint comparison only; 2024-25 was 16.9%. | OK |
| 16 | rec.sharechange.fuel.1999-00.2025-26 | taxes | "The largest fall was in Fuel duties: 6.5% to 2.2%" | −4.3 pts, against alcohol and tobacco −2.4 and corporation tax −1.0. It is the largest. | OK |
| 17 | hmrc.share.top1.2023 to 2024 | index, who-pays | "27.2% of all Income Tax … owed by the top 1% of Income Tax payers, 2023-24" | HMRC Table 2.4 (July 2026), sheet "…share_tax" K27, outturn. The population is taxpayers only, and the page says so. | OK |
| 18 | hmrc.income.top1.2023 to 2024 | index, who-pays | "They had 12.4% of all Income Tax payers' income" | Sheet "…share_inc_pretax" K27: pre-tax income of taxpayers. | OK |
| 19 | etb.2a.alltax.q5 | who-pays | "£51,903 a year in all taxes … highest-income fifth of people (36.2% of their gross income)" | ETB FYE2024 Table 2a: G48 41,215 + G70 10,688 = 51,903. 51,903 ÷ 143,345 = 36.2%, consistent with Table 8. | OK |
| 20 | etb.t8.gross.all.all | index, household-tax | "33.6% of gross household income … 2023/24" | Table 8 I15 = 33.6, checked in the xlsx. All individuals, UK private households. | OK |
| 21 | etb.t8.gross.all.q1 | index, who-pays, household-tax | "Lowest-income fifth 36.7%" | Table 8 D15 = 36.7. | OK |
| 22 | etb.t8.gross.indirect.q1 | index, household-tax | "most of this is indirect tax such as VAT (21.0% of income, or 16.5% of their spending)" | Table 8 rows 9 and 22 = 21.0 and 16.5. 21.0 of 36.7 is a majority. | OK |
| 23 | etb.t8.gross.direct.all | household-tax | "22.9% in direct taxes, such as Income Tax" | Table 8 I5 = 22.9. The number is right, but the section heading "Why did direct taxes rise in 2023/24?" contradicts it (see P1). | **Material P1** |
| 24 | etb.ret.taxshare.all | who-pays | "taxes took 29.4% of [retired households'] gross income, against 34.0%" | Table 4a (4,447 + 5,916) ÷ 35,290 = 29.4%; Table 3a gives 34.0%. The page says retired households are those where retired people bring in "over half" the income. See M5. | OK (minor M5) |
| 25 | etb.t16.all.2023/24 | who-pays | "53.3% of people lived in households that received more in benefits and services than they paid in taxes" | Table 16 B51 = 53.3, retired 90.1, non-retired 45.8. Checked "retired higher than non-retired in every year 1977 to 2023/24": true in every row. | OK |
| 26 | earn.real.ft.2021 | index, life | "April 2021 £761 → April 2025 £767 … in April 2025 prices: about the same (+0.8%)" | 609.8 × CPIH(Apr25)/CPIH(Apr21). 2021 is the SOC2020 coding break, so the comparison stays within one stretch. "Highest of the 5 years measured the same way" is checked and true. 2025 ASHE is provisional, which the page does not flag (minor). | OK |
| 27 | work.rate.2026 | index, life/work | "75.1% of people aged 16 to 64 were in work, April to June 2026, UK" | LF24 2026 Q2 = 75.1. life/index headlines 2025 (75.3%) instead (see M4). Checked "2025 higher than in 51 of the other 54 years": true (only 2018, 2019 and 2020 were higher). | OK |
| 28 | house.owners.2024 | index, life | "65% of households in England owned their home, 2024-25" | FT1101 D103 = 64.83, England only, labelled. "Higher than in 10 of the other 16 years" holds only on unrounded values (see M3). | OK (minor M3) |
| 29 | hol.abroad.per100.2025 | life | "58.4 million holiday visits abroad [by GB residents], about 86 for every 100 residents" | 58,396k ÷ GB population 67.56m = 86.4. The population base is correctly GB, not UK. The OTT 2025 source record still says "UK residents" (see M6). | OK (minor M6) |
| 30 | school.primary.2026 | index, life/schools | "26.1 pupils in the average state primary school class in England, January 2026" | DfE API, England, state-funded, one-teacher classes. life/index headlines January 2025 (26.4) instead (see M4). | OK |

### Other claims checked (not among the 30 ids)

- **"Spending was higher than receipts in 68 of the 78 years" (taxes).** Recounted from the raw OBR "% of GDP" sheet: 68 is correct. Three years (1957-58, 1989-90 and 1998-99) are deficits by less than 0.03% of GDP, so they look like ties in the published CSV. The figure of 65 of 71 years from 1955-56 is also correct.
- **Second-lowest G7 debt in 2024, on both IMF and OECD measures; highest G7 10-year yield (borrowing).** Consistent with the tables shown.
- **"Higher in 2025 than 2008 in all 10 areas; largest rise London" (housing-places).** Recomputed: London +6.5 against North West +6.2. True.
- **"Lowest fifth below highest fifth 1977–1987, above 1988–2017/18" (household-tax).** Recomputed from every row. True.
- **"Within five percentage points" on the current method.** Largest gap is 4.5, in 2018/19. True.
- **Worked example.** £242 and £967 NI thresholds; £3,486 + £1,393 = £4,879, which is 16% of £30,000. Arithmetic correct.

## Problems

### Material

**P1. household-tax.html: the heading "Why did direct taxes rise in 2023/24?" is contradicted by the page's own figures and by the ONS.**

- **What the page shows.** Under the heading, the page quotes ONS on fiscal drag "causing them to pay greater proportion of their income in taxes".
- **What the page's own data says.** In its own direct and indirect taxes table, direct taxes as a share of gross income *fell*, from 23.2% (2022/23) to 22.9% (2023/24). The id is `etb.t8.gross.direct.all`, the headline 22.9% at the top of the same page.
- **What the ONS says.** The bulletin the quote comes from (FYE 2024, `data/payers/raw/ons-bulletin-2024.html.json`) says direct taxes rose only in cash (+2.6% nominal; Table 2a: £15,351 → £15,743). It also says: "After accounting for the effects of inflation, direct taxes effectively decreased for the average UK household between FYE 2023 and FYE 2024 (a real-terms decrease of 2.9%)", and that for the richest fifth "direct taxes also reduced nominally 1.4%".
- **Why it is material.** A reader of a page about shares of income comes away believing households paid more of their income in direct tax in 2023/24. They paid less, both as a share and after inflation.
- **Fix.** Retitle the heading to say "in cash" or "after fiscal drag", or replace the quote with the ONS's real-terms sentence.

### Minor

- **M1. Narrative glosses over the rise since 2021-22 (spending.html and taxes.html).** Both share-of-GDP narratives say spending "rose to a high of 52.3% in 2020-21, then fell to 44.3%/44.5% in 2025-26". On spending.html the chart title adds "then fell back part of the way". In fact the share bottomed at 43.4% (PESA) or 43.3% (OBR) in 2021-22 and has risen since. The endpoints are correct, but the wording hides the recent upward move.
- **M2. "All other taxes" quietly includes the £30.5bn of VAT refunds (taxes.html).** OBR Receipts (£bn) column D33 is "VAT refunds", 30.5. The page shows VAT as £180bn (net) and says "All other taxes includes business rates, vehicle and air passenger duties, …", without mentioning the VAT refunds. If gross VAT (£210.8bn) were used, VAT would be 19.1% of taxes, not 16.3%. This is a defensible OBR presentation, but the note should say it.
- **M3. "Higher than" on survey differences of a few hundredths of a point (life/index housing).** The page says 2024-25 home ownership (64.83%) is "higher than in 10 of the other 16 years". Three of those years were 64.76–64.86%, all displayed as "65%", and the differences are far inside EHS sampling error. Readers see 65% being "higher than" 65%.
- **M4. Latest year differs between the home page and life/index.** The home page headlines April to June 2026 employment (75.1%) and January 2026 class size (26.1). life/index headlines 2025 (75.3% and 26.4) and calls 2025 the "dark dot". Both are labelled and topic pages explain why, but readers moving between the two pages see two different "latest" figures.
- **M5. Small definitional and labelling slips.** The definition of retired households says "over half" or "more than half" of income; the ONS definition is "at least half". ASHE 2025 (£767) is provisional in the record but not flagged on the page. The who-pays Limits note sets the 2023-24 Income Tax distribution beside the 2025-26 Income Tax total (£329bn of £1,105bn) without stating the year gap in the sentence.
- **M6. The OTT 2025 figure record contradicts the page on population.** The ott-2025 source metadata ("Population: Visits abroad by UK residents"; "Where: United Kingdom residents") says UK, while the figure notes and pages correctly say Great Britain residents from 2024. Only the record is affected; the page is right.
