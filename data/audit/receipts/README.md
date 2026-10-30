# Receipt source evidence

This is a separate, private evidence selection for receipt implementation. It
removes the unreadable-source prerequisite for issue #5; it does **not** complete
that issue, ingest a product receipt dataset, reconcile fiscal series or establish
independent fiscal approval. Nothing here is copied to `site/`.

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

## Evidence to interpret before building a product dataset

The following are source-cell pointers, not an approved fiscal classification:

| Source/sheet | Exact cells | Meaning retained / work still needed |
| --- | --- | --- |
| Databank `Receipts (£bn)` | `C4:D5` | VAT net of refunds and VAT refunds are separate lines; choose and explain the reconciliation treatment, without double counting. |
| Databank `Receipts (£bn)` | `Q4:S5`, `U4:X5`, `AB4` | PAYE, self-assessed and other income tax; onshore/offshore corporation tax and related oil/gas lines; NICs. Define explicit non-overlapping groupings. |
| Databank `Receipts (£bn)` | `AD4:AH5` | Interest/dividends, gross operating surplus, mixed other taxes/receipts, PSCR and National Accounts taxes. PSCR is not income tax or all tax; the mixed residual cannot simply be relabelled non-tax. |
| Databank `Receipts (£bn)` | `B7:B38`, `C40:C42` | Financial-year rows and series-specific September/October 2026 source notes; forecast starts in 2026-27. Do not reuse the mixed-vintage March note on `Public finances since 1900`. |
| Databank `Aggregates (£bn)` | `C1`, `C4:AH7`, `C94:C97` | Cash-unit labels, receipts/expenditure/borrowing/debt/GDP columns and derivation/status notes. Verify year alignment and rounding before reconciling. |
| Databank `Aggregates (per cent of GDP)` | `C1`, `C89:C94` | GDP vintage and separate end-March denominator for debt, plus series status notes. GDP-denominated borrowing is not debt accumulation. |
| Databank `Glossary` | `B5:E6`, `B11:E15` | Receipts and TME scope, annual accrual borrowing, cash debt stock and cash-requirement distinction. |
| History `Receipts (£m)` | `B1:Z6`, `B332:I332` | Nested totals, residual derivations, units, series codes and trailing source notes. Do not add subtotals to their components. |
| History `Receipts (per cent of GDP)` | `B1:Z5`, `B332:I332` | Corresponding GDP-share labels and source notes; no currency-unit conversion of this table. |
| History `Contents` | `D4`, `D31`, `D34:D43`, `D61:D64`, `D67:D74` | Joined series, interpolation, May 2023 source vintage, cash through 1998-99/accruals thereafter, VAT inclusive of refunds, mixed residuals and changing geography. |
| History `Aggregates (£m)` / `Aggregates (per cent of GDP)` | `B6:F7`, `B9:F331` | Borrowing and debt series, financial-year and March-centred GDP. Rows are offset by two from the receipt tables: match year labels, never row numbers alone. |

## Remaining issue #5 acceptance

All original acceptance remains open for the factory successor: implement
`data/receipts.json` with exact source-cell semantics and non-overlapping actual
source categories (including income tax, NICs, VAT, corporation tax, other tax and
non-tax separately where supported); preserve totals, refunds/negatives,
missingness, true per-series status and vintage boundaries; independently verify
all formula operands and source-justified reconciliation tolerances; reconcile
spending minus receipts to borrowing only on compatible bases or document the
bridge/limitation; distinguish debt stock from borrowing flow. Add product-level
wrong-cell, unit, missingness, overlap and reconciliation corruption tests.

The audit tests here verify source fidelity, not those unimplemented fiscal
calculations. Factory independent fiscal/product review, official exact-candidate
checks and controller deployment/live verification remain mandatory. No review,
human evidence, extraction acceptance or deployed effect is claimed by this seed.
