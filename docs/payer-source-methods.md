# Extraction and implementation checks

## Scope and method

The retained source register is `data/payers/sources.json`. It lists exactly
seven official response bodies, their URLs, publication/update dates, retrieval
date, status and original SHA-256 hashes and lengths. ODS/XLSX workbooks retain
the original bytes. Each HTML body is stored in a lossless ASCII JSON envelope:
UTF-8 encode `original_response` to recover the complete original body. The
register also records the envelope's stored hash and length. No upstream
whitespace is removed. Research-only renderings and other acquisitions are not
retained evidence in this checkout.

The original research used Crawl4AI page readings, direct HTTP acquisition,
standard-library ZIP/XML inspection of ODS and installed `openpyxl` for XLSX.
That acquisition history is distinct from this bounded source-editing role,
which runs no programs. No workbook is resaved by the source checker.

Readable extracts are `data/payers/audit/hmrc-cells.csv` and `ons-cells.csv`.
`scripts/check_payer_sources.py` independently reopens the originals and checks
all 793 selected cells, including labels and notes, against these extracts.
The extracts and their mutable hash index are not source truth. Runtime results
remain pending the controller's checks; see `payer-source-verification.md`.

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
- The collated July 2026 workbook and its supporting documentation were explored
  during research but are not retained here. Their taxpayer-count and Scottish
  classification cells cannot support a public claim from this seed. In
  particular, do not display the 36.7-million taxpayer count.

`data/payers/audit/hmrc-cells.csv` retains selected current and prior-year
cells. After CSV parsing, JSON-decode `published_text_json` to obtain the exact
published text. Preserve explicit ODF spaces, tabs, line breaks, paragraph
separators and trailing spaces; equality is exact. Commas in ODS numeric text
are thousands separators. A rounded `0.0` does not prove an exact zero.

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

The earlier research explored the following decile calculations. Its
`ons-deciles-derived.json` is not retained here and is not an accepted dataset.
These formulas explain that exploration; they do not authorize a decile UI:

- direct % gross = 100 × row 48 / row 41;
- indirect % gross = 100 × row 70 / row 41;
- combined % gross = 100 × (row 48 + row 70) / row 41;
- indirect % disposable = 100 × row 70 / row 49.

Such results are ratios of group means, not means of household tax percentages.
They would be **derived**, not ONS-published decile percentages. The earlier
research reported one-decimal rounding and gross/direct/disposable residuals
from -£1 to £1; those calculations are not established by the source-cell
checker. The proposed first display uses published quintile percentages only.

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

The earlier research reported that the six direct/gross and six
indirect/disposable percentages reproduced to one decimal place from `Table 2a`.
That is a reported consistency check, not complete independent verification.
The source checker compares retained cell values only; it grants no fiscal or
renderer acceptance.

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
