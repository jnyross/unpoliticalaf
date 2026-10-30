# Extraction and implementation checks

## Scope and method

Only `research/payers/` contains outputs. No product code, tests, dependencies, credentials, services, Git operations or Boat environments were used.

Page reading used `c4a md --help`, then `c4a md --filter raw`. Direct HTTP retained original files. Python standard-library ZIP/XML inspection read ODS data. Installed `openpyxl` read XLSX data. No spreadsheet was resaved.

`source-register.json` records exact URLs, file lengths, SHA-256 hashes, retrieval date and release status. `snapshot-sha256.tsv` covers every retained snapshot. Markdown files are Crawl4AI renderings, not unchanged official response bytes. Original `.ods`, `.xlsx` and `.html` files are unchanged downloaded response bodies.

The initial June 2025 HMRC release was superseded. The collection page established a 15 July 2026 release. Use the July 2026 outturn, not the old projection for 2023/24. The ONS `/latest` bulletin resolves to `/2024`. The guessed ONS `/financialyearending2024` route returned a non-content page. Do not cite `ons-bulletin.md` as evidence.

## Exact numeric map

### HMRC July 2026 Table 2.4

All sheets use row 2 for column labels, row 27 for 2023/24 outturn, and rows 28–30 for 2024/25–2026/27 projections.

- `2_4_Taxpayer_share_tax!F27=9.9`, `G27=90.1`, `I27=59.1`, `K27=27.2`: bottom 50%, top 50%, top 10%, top 1% shares. Unit: percentage of all Income Tax liabilities.
- `2_4_Taxpayer_share_tax!L27=274`: total liability, £ billion, rounded.
- `2_4_Taxpayer_share_inc_pretax!F27=24.9,I27=34.0,K27=12.4`: corresponding shares of income before Income Tax. These are not tax shares.
- `2_4_Taxpayer_inc_quantiles!F27=29,700,I27=67,400,K27=207,000`: income breakpoints, £ per year.
- `Contents!A5`: outturn through 2023/24; projections thereafter.
- `Contents!A3` contains an outdated phrase that starts projections in 2023/24. The same file's `A5` and current commentary sections 1 and 4 establish 2023/24 as outturn. Do not repeat the outdated phrase.
- Collated July 2026 workbook: `2_1_IT_payers_by_demographic!A37` identifies 2023/24, `B37=36,700` gives taxpayers in thousands. `B3` gives its heading. The July 2026 supplementary state-pension sample changes coverage. See supporting documentation, “Methodological changes this year”.

The file `hmrc-cell-evidence.csv` retains selected current and prior-year cells as published text. Commas in ODS numeric text are thousands separators. A rounded `0.0` does not prove an exact zero.

### ONS FYE 2024

`Table 2b` columns `C:L` run from bottom to top decile. `M` covers all people. Row 6 gives labels; row 8 gives population, thousands. Row 9 gives households, thousands. These household counts are not equal across deciles.

- Row 16: original income.
- Row 40: cash benefits.
- Row 41: gross income, before direct taxes and including cash benefits.
- Row 48: total direct taxes.
- Row 49: disposable income, after direct taxes.
- Row 70: indirect taxes.
- Row 71: post-tax income, after indirect taxes.
- Rows 43–47: direct-tax components, including student loan repayments and Council Tax rebates.
- Rows 51–64: final-goods indirect taxes. Rows 65–69: intermediate-goods indirect taxes, including employers' NI at row 66.

All amounts above are rounded £ per year. They are unequivalised household amounts averaged across the individuals in each group. Do not present them as individual tax bills or as an equal-household-weight mean. Ranking uses equivalised household disposable income. See `Cover sheet!A6`, `Notes!B4,B6,B31` and `Table 2b!A1`.

`ons-deciles-derived.json` retains the 4 inputs and source cells for each group. Calculations:

- direct % gross = 100 × row 48 / row 41;
- indirect % gross = 100 × row 70 / row 41;
- combined % gross = 100 × (row 48 + row 70) / row 41;
- indirect % disposable = 100 × row 70 / row 49.

Round results to 1 decimal place. These are ratios of group means, not means of household tax percentages. They are **derived**, not ONS-published decile percentages. Rounding of inputs permits £1 residuals in the gross/direct/disposable identity. The extraction found only residuals from -£1 to £1.

### Prefer published percentages for the main display

`Table 8` has **quintiles, not deciles**. Columns `D:H` run from bottom to top fifth. `I` covers all people.

| Row and measure | Bottom | 2nd | 3rd | 4th | Top | All |
|---|---:|---:|---:|---:|---:|---:|
| 5, direct % gross | 15.7 | 15.7 | 18.2 | 21.3 | 28.8 | 22.9 |
| 9, indirect % gross | 21.0 | 15.1 | 11.9 | 10.4 | 7.5 | 10.7 |
| 15, combined % gross | 36.7 | 30.7 | 30.2 | 31.7 | 36.2 | 33.6 |
| 16, indirect % disposable | 24.9 | 17.9 | 14.6 | 13.2 | 10.5 | 13.9 |
| 22, indirect % expenditure | 16.5 | 17.4 | 17.2 | 16.6 | 15.4 | 16.4 |

Published rounded components need not sum to the published total. Do not overwrite row 15 with sums of rows 5 and 9.

A parent-side independent check can reopen both official workbooks and compare the cited cells. In this extraction, all 6 published direct/gross percentages and all 6 indirect/disposable percentages reproduced to 1 decimal place from `Table 2a`. This is a consistency check, not independent review.

## Required limitations

- HMRC uses individuals with positive Income Tax liability. ONS groups all people by household circumstances. These are not matching distributions.
- Both use the 2023/24 label. HMRC tax years run 6 April–5 April. ONS financial years run April–March. Do not imply identical collection windows or definitions.
- HMRC liabilities are estimated outturn, not a census or cash receipts. Projections use a different status label.
- ONS indirect taxes are allocated through consumption assumptions. The 2020 technical report, section 7, assumes full consumer incidence of final and intermediate taxes. Section 10, “1. General assumptions”, explains incidence assumptions and limitations. Do not claim the remitting business bears no economic burden as a universal fact.
- The 2020 technical report says student loan repayments were excluded at that time. The 2024 workbook explicitly includes them (`Table 2b!B45`, `Notes!B8`). Use the current workbook for current component scope.
- The older QMI, section 5, says Corporation Tax is not allocated. The current workbook has no Corporation Tax component. “All taxes” must mean only taxes covered by this ONS analysis.
- Deferred payments can place high-gross-income households in low disposable-income groups. See `Notes!B8,B9`. This is essential beside bottom-decile values.
- Spending can exceed current income through savings or borrowing. Temporary low income, measurement error and omitted one-off receipts also matter. See technical report section 7.
- ONS private-household survey coverage excludes institutional residents. Do not say every UK resident is directly surveyed or represented without qualification.
- The official workbook flags Table 2b for a future-publication review, not as withdrawn. Some component cells are suppressed. Do not fill them by inference. Total tax cells used here are numeric.
- Avoid trend comparisons without checking policy-induced income shifting, changing taxpayer populations, dividend methodology and source revisions.
