# Receipt source evidence

This is a separate, private evidence selection used by the receipt implementation.
`scripts/build_receipts.py` now creates `data/receipts.json`, and
`scripts/check_receipts.py` independently reopens the retained workbooks to check
source binding and declared arithmetic. See [the current receipt methods](../../../docs/receipts-methods.md)
for categories, operands, reconciliation reports and limitations. These artifacts
do **not** complete issue #5 or establish independent fiscal approval. Nothing
here is copied to `site/`.

`index.json` binds every TSV to the retained workbook hash, pinned source manifest,
unchanged source catalogue metadata, exact sheet/ranges, cell count, number-format
dictionary and TSV SHA-256. Numeric strings retain the original stored precision;
blanks, literal dashes, negative numbers, labels, formula expressions and cached
values remain distinct. A numeric zero formatted as a dash stays a numeric zero.
Publication/retrieval dates are copied from `data/sources.json`, not inferred from
worksheet titles. The historical catalogue publication date is the retained HTTP
Last-Modified date, not an October 2026 forecast vintage.

The explicit scope is `scripts/receipt_audit_scope.py`. It includes the complete
meaningful receipt tables through column AH (databank) and Z (history), all data
years and trailing receipt notes, compatible aggregate tables and their notes,
the databank glossary and historical Contents notes. Historical chart helper
columns beyond Z contain Excel errors and are outside this selection; in-scope
errors or unsupported shared/array formulas fail closed. No undocumented worksheet
or formula result is silently substituted. The spending scope in
`scripts/audit_scope.py`, its eight-sheet index and its extractor/checker remain
unchanged; these new worksheets must not be appended to that index.

Run only in a credential-free check environment:

```sh
.venv/bin/python scripts/extract_receipt_audit.py
.venv/bin/python scripts/check_receipt_audit.py
make verify
```

The exporter reads bounded ZIP/XML cells; the checker independently reopens the
workbooks with openpyxl, without importing the exporter or its cell decoder.
`make verify` requires both the original spending audit and this receipt audit.
Rehashing an altered TSV does not make it match the workbook.

## Evidence used by the product dataset

The following are source-cell pointers, not an approved fiscal classification:

| Source/sheet | Exact cells | Meaning retained / work still needed |
| --- | --- | --- |
| Databank `Receipts (£bn)` | `C4:D5` | VAT net of refunds and VAT refunds are separate lines; C+D retains both once, as explained in the methods. Fiscal classification remains subject to review. |
| Databank `Receipts (£bn)` | `Q4:S5`, `U4:X5`, `AB4` | PAYE, self-assessed and other income tax; onshore/offshore corporation tax and related oil/gas lines; NICs. The methods name the implemented non-overlapping operands and limitations. |
| Databank `Receipts (£bn)` | `AD4:AH5` | Interest/dividends, gross operating surplus, mixed other taxes/receipts, PSCR and National Accounts taxes. PSCR is not income tax or all tax; the mixed residual cannot simply be relabelled non-tax. |
| Databank `Receipts (£bn)` | `B7:B39`, `C40:C43` | Financial-year rows from 1999-00 through 2031-32 and series-specific September/October 2026 source notes; forecast starts in 2026-27. Do not reuse the mixed-vintage March note on `Public finances since 1900`. |
| Databank `Aggregates (£bn)` | `C1`, `C4:AH7`, `C94:C97` | Cash-unit labels, receipts/expenditure/borrowing/debt/GDP columns and derivation/status notes. Verify year alignment and rounding before reconciling. |
| Databank `Aggregates (per cent of GDP)` | `C1`, `C89:C94` | GDP vintage and separate end-March denominator for debt, plus series status notes. GDP-denominated borrowing is not debt accumulation. |
| Databank `Glossary` | `B5:E6`, `B11:E15` | Receipts and TME scope, annual accrual borrowing, cash debt stock and cash-requirement distinction. |
| History `Receipts (£m)` | `B1:Z6`, `B332:I332` | Nested totals, residual derivations, units, series codes and trailing source notes. Do not add subtotals to their components. |
| History `Receipts (per cent of GDP)` | `B1:Z5`, `B332:I332` | Corresponding GDP-share labels and source notes; no currency-unit conversion of this table. |
| History `Contents` | `D4`, `D31`, `D34:D43`, `D61:D64`, `D67:D74` | Joined series, interpolation, May 2023 source vintage, cash through 1998-99/accruals thereafter, VAT inclusive of refunds, mixed residuals and changing geography. |
| History `Aggregates (£m)` / `Aggregates (per cent of GDP)` | `B6:F7`, `B9:F331` | Borrowing and debt series, financial-year and March-centred GDP. Rows are offset by two from the receipt tables: match year labels, never row numbers alone. |

The methods document explains the implemented VAT C+D, income-tax Q+R+S,
corporation-tax U+V, residual other-tax and non-tax groups. These choices still
require independent fiscal review; residual-defined closure is not independent
accuracy evidence. The unchanged four-times-weighted-ULP budget is a chosen
empirical storage-arithmetic allowance, not a derived source error bound.

Historical debt remains a stock. `Contents!D63` names Bank of England (2017)
through 1899-00 and OBR (2023) from 1900-01, without establishing accounting basis
or scope for either regime. The private values record both as uncertain; the
October 2026 glossary is not transferred to the historical series.

Literal dashes stay missing, even where a subtotal suggests nil. For example,
2022-23 business operands K329/L329/N329 are dashes, so that identity is
`not_testable_missing`; other taxes are null wherever any required C/D/Q/I
operand is missing. Published totals and negative values are still retained.
The 1998-99 central receipt discrepancy of 2179 million pounds remains unresolved;
neither a zero substitution nor a wider allowance is used to close it.

## Remaining issue #5 acceptance

The product extraction, raw-source/operand checks and reconciliation reports now
exist, with wrong-cell, unit, missingness, overlap and reconciliation corruption
tests. All original acceptance remains open until the factory successor obtains
independent fiscal/product review of the populated mappings, refunds, non-tax
partition, status/vintage, historical uncertainty and reconciliation limitations,
and completes the official exact-candidate checks and live verification.

The audit tests here verify source fidelity; product checks verify declared
arithmetic and bindings, not independent fiscal correctness. Factory independent
fiscal/product review, official exact-candidate
checks and controller deployment/live verification remain mandatory. No review,
human evidence, extraction acceptance or deployed effect is claimed by this seed.
