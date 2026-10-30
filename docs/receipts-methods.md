# Receipt and debt data contract

The receipt data is a separate, private working dataset. The controller's
`make build` creates `data/receipts.json`; `make verify` independently checks
it against the pinned workbooks and compares two regenerated copies byte for
byte. Workers edit source only. No generated receipt file, passing check,
independent fiscal approval or deployed receipt feature is claimed by these
source edits. The four public files and spending data contract remain unchanged.
Receipt presentation belongs to the separate renderer ticket.

## Source identity and value records

Seven tables retain all financial years in the selected receipt and aggregate
sheets. The October 2026 databank receipt table runs from 1999-00 through
**2031-32**, including row 39. Historical receipt tables run from 1700-01 through
2022-23. Historical aggregates match the year labels two rows below the receipt
tables. Current aggregate cash and GDP tables also match years by their labels;
their row offsets differ.

A value resolves through its table's source ID/sheet, source catalogue entry
(file, hash, publication, publication/retrieval dates and licence), series
label/code/unit/role and its own fiscal year, exact value/year cells, accounting
basis, scope, geography and status. Notes retain their exact cell locators,
text, type, number format and formula. Numeric source strings preserve stored
precision alongside the numeric working value. Blank, literal dash, numeric
zero, negative value and formula remain distinct. Missing operands produce
null calculations and a list of their cells.

Units stay in the original table units: GBP billion, GBP million or percent
GDP. No rounding or currency scaling enters the calculations. The GDP columns
inside the aggregate percent tables remain currency values: current AE/AF are
GBP billion; historical E/F are GBP million. The inherited series unit applies
to every value, including missing values.

For current receipts, `C40:C41` supplies outturn through 2025-26 and October
2026 forecasts from 2026-27. Aggregate cash `C94:C95` and GDP `C91:C92` supply
their own corresponding notes. The GDP vintage note `C89` is retained too.
These labels do not come from the older mixed-vintage long-run spending sheet.
Historical `Contents!D34,D73:D74` identifies May 2023 source vintages, while the
catalogue publication date is the retained HTTP date, 3 August 2023. Neither
turns this into an October 2026 forecast. Historical actual/estimate status stays
uncertain. No next release date is established by these retained sources.

## Categories and formulas

All original receipt columns are retained, including nested totals, refunds
and mixed residuals. Direct source columns are not a flat additive partition.
The six derived groups are a non-overlapping arithmetic partition under the
National Accounts tax total, with the following exact operands:

| Group | Current receipt columns | Historical receipt columns |
| --- | --- | --- |
| Income tax | Q + R + S (PAYE, self-assessed, other) | C |
| National Insurance | AB | D |
| VAT including government refunds | C + D | Q |
| Corporation tax, as defined in source | U + V | I |
| Other National Accounts taxes, residual | AH - Q - R - S - AB - C - D - U - V | Z - C - D - Q - I |
| Receipts outside National Accounts taxes | AG - AH | Y - Z |

Each result retains its ordered source-cell operands and coefficients as
`linear_combination`, the original unit and fiscal context. "Other taxes" and
"non-tax" are explicit differences, not separately observed source categories.
Their arithmetic partition is not independent evidence for the classification
of every small receipt or refund. The retained source notes do not independently
establish refund classification within National Accounts taxes; that limit must
stay beside any future display.

Current U includes the Bank Surcharge, Electricity Generator Levy and the
additional taxes in `C42`; it must not be described as a narrower pure
corporation-tax measure. W (petroleum revenue tax) and X (energy profits levy)
remain separate original lines, included in the residual group rather than
added again to corporation tax. Current D is a separate positive refund line;
adding it to net VAT C matches the historical VAT definition in
`Contents!D39`. Both raw lines remain available, including negative receipts.

Current AF and historical U/X are explicitly mixed tax/receipt residuals.
They are never relabelled wholly non-tax. Historical B/G/P/V are nested
subtotals; adding them to all their own components would double-count.
Historical Q includes purchase tax before 1973. Historical I includes profits
taxes before 1966-67. These are source-defined series, not unchanged modern taxes
back to 1700.

## Reconciliation and incompatible bases

Current receipt components C:AF reconcile to PSCR AG, including D refunds.
AF is itself source-coded as a residual (`Receipts (£bn)!AF5`), so this
closure is largely definitional. It checks retained source binding and storage
arithmetic, not independent fiscal accuracy of the component values. It is
distinct from the derived tax partition above, which also closes by construction.
Current aggregate spending D minus receipts C reconciles with
annual borrowing O within the same source table and year, in cash units and
GDP shares. `Aggregates (£bn)!O7` supplies the explicit b-a derivation.
This does not establish compatibility with PESA spending or another workbook's
May 2023 history. No cross-vintage subtraction is asserted.

Each report records the exact signed operands, independently recomputed
residual, missing operands and outcome. For a complete identity the budget is
four times the sum of each operand's binary64 spacing (`math.ulp`), weighted
by the absolute coefficient. This covers storage/arithmetic effects only; it
is not a fiscal/source error bound. The one-decimal Excel display format is
not used as an error allowance. A current identity outside that budget stops
the build.

Historical personal (C:F to B), business (H:O to G), consumption (Q:R:S to P),
central (B:G:P:T:U to V) and public (V:W:X to Y) relationships are all reported.
The source definitions `U6 = v-b-g-p-t` and `X6 = y-w-v` make the
central/public closures largely definitional too. Neither these residual-based
closures nor a small arithmetic residual independently validates fiscal accuracy
or classification. An incomplete sum is `not_testable_missing`, never zero or a
pass. Differences
beyond storage arithmetic remain `unresolved_source_difference`; no convenient
source tolerance is invented.

The central relationship is materially inconsistent before the cash/accrual
break: at 1998-99, `Receipts (£m)!B305+G305+P305+T305+U305-V305` is **2179
million pounds**, the separately listed licence-fee amount T305. The retained
`U6` derivation says v-b-g-p-t, but the cached source values can include that
licence fee in U already. The evidence does not explain the overlap.
Source totals are preserved; the report must not be described as reconciled.
This limitation is retained for the corresponding GDP-share table as well.

Historical receipts are cash through 1998-99 and accruals thereafter
(`Contents!D35`). No growth comparison or cross-break splice is calculated.
Historical borrowing's accounting basis remains uncertain: D35 applies to
receipts, while `Contents!D62` describes borrowing sources and a central-
government proxy before 1900-01. That proxy scope is machine-readable.
Geography follows `D64`; its overlapping 1800-01 boundary is marked uncertain,
rather than silently choosing one geography.

## Debt stock and GDP denominators

Debt is a cash stock at end March; borrowing is an annual accrual flow in the
current databank (`Glossary!C11,C14:C15`). Changes in debt need not equal
borrowing. No debt accumulation formula is asserted. Historic borrowing retains
the more conservative accounting status described above.

Published debt GDP shares are retained separately. Debt uses March-centred GDP
(current AF, historical F), whereas annual borrowing uses financial-year GDP
(AE/E). `Aggregates (per cent of GDP)!C90` states the current debt convention.
Separately retained actuals can disagree with the cash ratio: current 2025-26
cash debt X87 is 2916.8 GBP billion and March-centred GDP AF87 is 3134.687725,
while the published GDP share X82 is 93.3 percent. No source error bound is
established and the extractor does not silently replace the published share
with a calculated ratio.

## Independent checks and remaining gates

`scripts/check_receipts.py` reopens the two workbooks with openpyxl and pins
their hashes separately. It does not import the producer, audit exporter or
producer mapping. It reopens and binds all seven table selections, fiscal
years, labels/codes, units, declared roles, statuses, accounting bases,
geographies, scopes, ordered operands, missingness, residuals and budgets.
The checker transcribes the producer's classification and context rules,
including VAT C+D, corporation tax U+V, residual other taxes and AG-AH non-tax.
It can detect a product that departs from those rules; it does not independently
justify the rules themselves. Fiscal review must assess those choices against
the pinned source notes and populated calculations.
Unknown fields, duplicate JSON keys, omissions and duplicate reports fail.
The existing receipt audit gate continues checking the full TSV evidence.

Product corruption cases in `tests/test_fiscal_data.py` cover equal-number wrong
cells, altered raw/product numbers, units, scope/status/basis, missing years,
dash-to-zero substitution, overlapping operands, changed derived values,
inflated budgets, omitted/duplicate reports and falsely passed historical
differences. They also retain the source's final forecast year, GDP-unit
exceptions, debt stock distinction and early borrowing/geography limitations.

These checks verify the implementation and retained evidence. The controller
must still generate the data, validate its permitted artifact/review payload,
run setup/build/verify/smoke on the exact candidate, obtain the required
independent fiscal and product reviews, deploy and compare canonical live bytes.
No reviewer should approve the residual tax classification or historical
limitations merely because arithmetic checks pass. Original #5 and successor
acceptance remain open until their actual controller evidence exists.
