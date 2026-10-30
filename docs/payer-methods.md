# Payer page integration and methods

## Status and boundary

This is an unpublished UI candidate. Source preparation does not approve its
renderer. The controller must adopt the normal UI ticket only after source #35
and tax #34 succeed. This document records the integration; it does not claim a
build, review, browser check or deployment passed.

The public allowlist is exactly eight files: `index.html`, `taxes.html`,
`who-pays.html`, `methods.html`, `icon.svg`, `data/spending.json`,
`data/taxes.json` and `data/payers.json`. Source snapshots, registers, audits,
private receipt data, scripts, tests and this document stay outside `site/`.
No new private generated payer dataset is needed. Public JSON contains only the
producer's selected values, provenance and source notes, never full responses.
The existing atomic-write, regular-file, root, symlink and exact-manifest guards
remain in force.

## Two separate official views

HMRC Table 2.4 supplies estimated-outturn Income Tax liability shares for
2023/24. Its population is UK individuals with positive Income Tax liability.
People with no bill are excluded. The rank uses income assessable for tax before
deductions and allowances, not wealth or all income. Shares use total Income Tax
liabilities as their denominator. They are neither cash receipts nor all-tax
burden. The top 1% sits inside the top 10%, which sits inside the top 50%. The bottom
50% is separate from the displayed top 10% and top 1% groups. The selected shares must not be added. The current Contents
outturn note governs the selected year; projection rows are excluded. The
uncollated taxpayer count is not displayed.

ONS Table 8 supplies published percentages for the completed 2023/24 financial
year. These are survey/model estimates, not forecasts. The population is people
in UK private households. The rank uses equivalised household disposable income:
income after direct taxes, adjusted for household size and needs. The fifths
contain about equal numbers of people, not households. They are not HMRC groups.
The displayed amounts are not equivalised merely because the ranking is.

Direct, indirect and published combined percentages use gross household income,
which includes cash benefits. Disposable income subtracts direct taxes. Combined
values come from the published combined row, not sums of rounded parts. The
second denominator is household expenditure for the same indirect taxes.
Deferred lump-sum direct-tax payments can place high-gross-income people in low
disposable-income groups. Savings, borrowing, temporary low income, sampling and
measurement also affect interpretation. An income ratio is not a purchase tax
rate or a lifetime burden. These warnings must remain beside the bottom-group
result, not only in source disclosures.

Remitting tax differs from bearing its economic cost. ONS assigns final and
intermediate indirect taxes fully to consumers in this model, including employer
National Insurance. Employee and self-employed National Insurance are direct.
The OBR combined receipts total cannot be assigned wholly to either category.
Actual costs can fall on producers, workers, buyers and others. The FYE 2019
technical report, published 25 June 2020, explains assumptions in sections 7 and
10. The QMI is dated 15 June 2018. Their age stays visible; current workbook notes
take priority. Direct taxes currently include student-loan repayments.
Corporation Tax is not allocated to households. Suppression stays suppression.
Neither panel is complete all-UK-tax incidence. Do not join them into one burden,
an average or a reconciliation to receipts.

## Official URLs and versions

- HMRC release, 15 July 2026:
  https://www.gov.uk/government/statistics/income-tax-liabilities-statistics-tax-year-2023-to-2024-to-tax-year-2026-to-2027
- HMRC Table 2.4 ODS, 15 July 2026:
  https://assets.publishing.service.gov.uk/media/6a54e2b72467584757371e1a/Table_2.4_Shares_of_total_Income_Tax_liability.ods
- ONS bulletin, 25 September 2025:
  https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024
- ONS dataset, 25 September 2025:
  https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/theeffectsoftaxesandbenefitsonhouseholdincomefinancialyearending2014
- ONS workbook, 25 September 2025:
  https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/theeffectsoftaxesandbenefitsonhouseholdincomefinancialyearending2014/financialyearending2024/etbreferencetablesfye202324final.xlsx
- ONS QMI, 15 June 2018:
  https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/methodologies/theeffectsoftaxesandbenefitsonukhouseholdincome
- ONS technical report for FYE 2019, 25 June 2020:
  https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/articles/theeffectsoftaxesandbenefitsonhouseholdincome/financialyearending2019

The selected JSON and `methods.html#payer-methods` expose the source versions.
No next release date is recorded. The existing operator, funding, error-reporting
and private-repository decisions are unchanged.

## Integration and checks to run

`build.py` calls `project(ROOT)`, then `validate_data(ROOT, data)`, before any
write. It passes the approved data to `render(data, build_site.page)` and checks
`validate_page(ROOT, data, html)` before publication. JSON uses deterministic
producer insertion order, UTF-8, finite numbers and a final newline. Preserve
source-cell insertion order: source-note rendering and the independent checker
compare the ordered notes. Alphabetically sorting only serialized dictionary
keys would change note order after reloading.

`verify.py` and `check_site.py` independently check the published payer JSON and
HTML against reopened source files, not just regenerated output. Duplicate JSON
keys and non-finite values are rejected. Payer figures cannot acquire legacy or
tax identities or appear on another page. Palette, reading grade, page size and
unmarked forecast-date rules still apply to the payer page. No broad exemption
was added. New prose markers, if later needed, require exact independent checker
support and negative tests before adoption.

The shared page callback supplies Spending / Taxes / Who pays / Methods and a
current-page indicator. It retains the tax checker's exact scope paragraph and
adds a separate onward link. Shared tables have labelled, keyboard-focusable
scroll regions. The payer module supplies its existing monochrome bars and
always-visible tables. Correction `a65e255` removes its duplicate inner page
navigation and binds adjacent source links to their context. The shared callback
removes the exact module OGL paragraph and retains one attribution footer. An
unexpected licence paragraph fails closed rather than silently duplicating it.

The controller must run the payer-module tests first, then `make setup build
verify smoke` and the full accessibility gate on the combined candidate. Confirm
all four pages in default and expanded states at 360px and 1100px, no document
overflow, labelled table scroll access, controls at least 44px, native keyboard
disclosures and no-JavaScript core content. Keep grade 7 as the limit. If a source
note makes prose too hard, fix presentation without hiding core limits or
exempting ordinary prose. The published source paragraphs and download links
need context-specific mutation checks so duplicate footer links cannot hide a
broken primary source link.

Public contract tests cover eight files, local HTTP bytes and new private-path
404s. Safety tests retain prior last-good publication checks and add payer source
failure, explicit-root and published JSON/HTML mutation cases. Independent fiscal
and product review, council review and exact live-byte confirmation remain
controller-owned gates. No check result is claimed here.
