# Final corrections and delivery subset

## Documented citation corrections, 30 October 2026

The reviewer requested corrections to technical-report section numbers. `METHODS.md` and `EXPLANATIONS.md` now cite the correct headings. The report is **FYE 2019**, published **25 June 2020**. Its body retains older examples. Do not treat those examples as current data.

- Incidence and spending relative to income: **section 7, Post-tax income**, anchor `#post-tax-income`.
- Alternative incidence assumptions: **section 10, Background notes**, subsection **1. General assumptions**, anchor `#background-notes`.
- There is no section 13 in this report.

### Exact short official caveats

Technical report section 7:

> “Throughout this analysis we assume that the incidence of intermediate taxes is born by the consumer who purchases the final good (in this case, households).”

> “Taxes levied on final goods and services are assumed to be fully incident on the consumer”

> “For such households, the most common source of funds was savings, followed by credit or store cards and loans.”

The last quote refers to households whose expenditure was at least twice disposable income. The same paragraph says low-income groups can include temporarily low earners, students and self-employed people. Measurement and sampling error also matter. It says expenditure tends to be measured more accurately than income at the lower end.

Technical report section 10, subsection 1:

> “the incidence of the tax is spread by pricing policies and probably falls in varying proportions on the producers of a good or service, on their employees, on the buyer, and on the producers and consumers of other goods and services.”

This qualifies the model's consumer-incidence assumption. The preceding paragraph states the model assumes direct taxes fall on the person from whose income the tax is deducted.

### Explicit ONS note evidence

`Table 8!A2` cites notes 3, 5, 6, 11 and **13**. This cell already appears in `ons-cell-evidence.csv`. Added `Notes!A16,B16` explicitly:

> “Expenditure has been calculated to be consistent with disposable income. Data not available prior to 1995/96.”

For the main UI, preserve published `Table 8!D22:I22`: **16.5, 17.4, 17.2, 16.6, 15.4, 16.4**. These are indirect taxes as percentages of expenditure. The last column covers all people. These are quintiles, not deciles.

Do not describe the bottom quintile's high indirect/gross ratio as its tax rate on purchases or its lifetime tax burden. Show expenditure as an alternative denominator. Retain notes 5 and 6 on deferred direct-tax payments and low disposable-income ranking.

### Explicit HMRC note evidence

`2_1_IT_payers_by_demographic!A37` reads **2023 to 2024 [note 9]**. This is not an outturn-status note. The footnote appears in `2_1_Footnotes!A11,B11`, now retained in `hmrc-cell-evidence.csv`.

Note 9 explains how HMRC groups Scottish starter/intermediate-rate taxpayers into the UK summary classifications. It describes non-savings/non-dividend and savings/dividend treatment. Do not silently treat note 9 as a forecast marker. The outturn status comes from the workbook description and release commentary.

### Employee and employer National Insurance

ONS treats employee/self-employed contributions as direct taxes. See technical report **section 5, Disposable income**, and current `Table 2b!B44,C44:L44`.

ONS places **employers' NI contributions** among intermediate indirect taxes. See `Table 2b!A65,B66,C66:L66`. All these cited numeric cells appear in `ons-cell-evidence.csv`.

A receipts series that combines National Insurance contributions must not be mapped wholly to either ONS category. The controller reports its OBR AB series is combined. This research did not independently inspect that OBR series. Keep any OBR-specific assertion conditional until its own provenance confirms the definition.

## Recommended delivery subset

The requested first-source subset contains complete unchanged responses:

| File in snapshots/ | Bytes |
|---|---:|
| hmrc-table24-july2026.ods | 18,791 |
| ons-etb-fye2024.xlsx | 247,472 |
| hmrc-latest-release.html | 76,341 |
| ons-technical-2019.html | 176,769 |
| ons-qmi.html | 122,882 |
| **Total** | **642,255** |

This leaves **357,745 bytes** under the 1,000,000-byte cap before metadata, code and diff overhead. Use the Table 8 quintiles in the first UI. The decile evidence can remain research-only.

The full HMRC supporting response is **487,353 bytes**. Stage it separately if needed. The collated workbook is **93,036 bytes**. Add it only if the first page includes the 36.7-million taxpayer count, whose exact cell is in that workbook. The Table 2.4 ODS alone supports the percentile shares and breakpoints.

A separate explanatory-guidance delivery can contain the 6 complete sources below. It is **476,447 bytes** before metadata/code:

- basics-income-tax.html: 86,695;
- basics-national-insurance.html: 95,069;
- basics-vat.html: 87,451;
- basics-paye-remitter.html: 101,690;
- basics-scottish-powers.html: 32,915;
- basics-welsh-income-tax.html: 72,627.

The register's `minimum_delivery` flag describes the earlier all-in-one numeric-plus-explanatory option: **919,479 source bytes**. This staged recommendation supersedes that option for the first delivery. Do not copy all 41 research snapshots into a product review.

The source register records every source URL, size, date/status and SHA-256. All 41 retained hashes were checked after extraction. No official snapshot was changed. No product files, factory state, Git history or services were changed.
