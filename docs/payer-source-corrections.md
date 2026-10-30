# Final corrections and delivery subset

## Documented citation corrections, 30 October 2026

The research review corrected earlier technical-report section citations. The
retained `payer-source-methods.md` uses the corrected headings below. The report
is **FYE 2019**, published **25 June 2020**. Its body retains older examples.
Do not treat those examples as current data.

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

`Table 8!A2` cites notes 3, 5, 6, 11 and **13**. The retained `data/payers/audit/ons-cells.csv` includes this cell and
`Notes!A16,B16`, which identify note 13 and its expenditure definition:

> “Expenditure has been calculated to be consistent with disposable income. Data not available prior to 1995/96.”

For the main UI, preserve published `Table 8!D22:I22`: **16.5, 17.4, 17.2, 16.6, 15.4, 16.4**. These are indirect taxes as percentages of expenditure. The last column covers all people. These are quintiles, not deciles.

Do not describe the bottom quintile's high indirect/gross ratio as its tax rate on purchases or its lifetime tax burden. Show expenditure as an alternative denominator. Retain notes 5 and 6 on deferred direct-tax payments and low disposable-income ranking.

### Explicit HMRC note evidence

The earlier research reported **2023 to 2024 [note 9]** in the collated
workbook's `2_1_IT_payers_by_demographic!A37`, with the footnote in
`2_1_Footnotes!A11,B11`. That workbook and those cells are not retained in this
seven-source seed or its HMRC CSV. This is a historical citation correction,
not independently reopened evidence from the retained Table 2.4 ODS.

The research identified note 9 as Scottish starter/intermediate-rate
classification, covering non-savings/non-dividend and savings/dividend treatment,
rather than an outturn-status or forecast marker. Do not reuse it as status
proof. In the retained Table 2.4 ODS, `Contents!A5` identifies years through
2023/24 as outturn and later years as projected; preserve the conflicting older
wording in `Contents!A3` rather than editing the official text.

### Employee and employer National Insurance

ONS treats employee/self-employed contributions as direct taxes. See technical report **section 5, Disposable income**, and current `Table 2b!B44,C44:L44`.

ONS places **employers' NI contributions** among intermediate indirect taxes. See `Table 2b!A65,B66,C66:L66`. All these cited numeric cells appear in `data/payers/audit/ons-cells.csv`.

A receipts series that combines National Insurance contributions must not be mapped wholly to either ONS category. The controller reports its OBR AB series is combined. This research did not independently inspect that OBR series. Keep any OBR-specific assertion conditional until its own provenance confirms the definition.

## Retained delivery subset

The earlier research considered five-source, numeric-plus-guidance and separate
guidance bundles. Those recommendations are superseded by the exact seven-source
register at `data/payers/sources.json`. Only its listed sources are retained:

- HMRC July 2026 release page and unchanged Table 2.4 ODS;
- ONS FYE 2024 bulletin, dataset page and unchanged XLSX;
- ONS QMI and FYE 2019 technical report.

The seven original response bodies total 818,297 bytes. The workbooks plus
lossless ASCII JSON HTML envelopes total 844,138 stored bytes, before audit CSVs,
documentation and checker/test code. These are source sizes, not a measurement
of the controller's complete review payload. The register records both original
and stored hashes/lengths for each HTML envelope. After JSON decoding, UTF-8
encode `original_response` to recover the complete official body; do not trim
upstream whitespace.

The collated HMRC workbook, supplementary supporting response, guidance
responses, research renderings and broader research extracts are absent.
The 36.7-million taxpayer count therefore remains outside the first UI scope.
Use only HMRC positive-liability Income Tax shares and the separately scoped
ONS published quintile percentages proposed in `payer-source-seed.md`.

The three council reviews accepted that narrow interpretation with limits;
they did not approve implementation or publication and could not reopen the
binary workbooks. Earlier parent checks covered seven hashes, three HMRC and
20 ONS cells, not all 793 audit cells. No full-source verification result is
claimed here. The independent checker, negative tests, exact-candidate review,
unchanged four public artifacts and canonical live checks remain controller
gates. The separate renderer's publication hold and preserved predecessor
failure remain in force.
