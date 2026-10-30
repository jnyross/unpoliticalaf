# Fiscal schema and recovery implementation

Issue #20 extends the partial issue #4 seed. This document describes source
changes, not an independent fiscal approval, passing check receipt or deployment.
Original issue #4 remains incomplete until the controller's required gates and
canonical live verification are evidenced.

## Resolving a value

Schema version 2 preserves the existing `v` and `ref` leaf fields and adds a
stable `value_id`. It resolves through these public JSON records:

| Record | Meaning |
| --- | --- |
| `provenance[value_id]` | Exact cell, source ID, fiscal period, series identity, displayed unit, source-to-output scale, geography, accounting scope, price basis, precision, missingness, status and source transformation. |
| `sources[source_id]` | Retained file, full SHA-256, publication, publication date, retrieval date, publisher and source URLs. The immutable original catalogue is unchanged. OBR publication-date qualifications remain in `published_note`. |
| `sheet_sources` | Explicit workbook ownership for each sheet, including historical `Contents` notes. |
| `source_cells[ref]` | Original XML numeric text, blank/text/dash kind, cached value, formula and number format for used cells, labels, periods, units, notes and reconciliation operands. Numeric XML text is not rounded. |
| `status_definitions` | Actual/outturn, forecast, estimate or explicit uncertainty; uncertainty lists the possible actual/estimate classifications. |
| `formulae` | Defined arithmetic operations; source transformations state scale and decimal places. |
| `derived` | Each rendered share or change, its ordered value IDs, formula, result, periods, units, scale, geography, scopes and operand statuses. |
| `reconciliations` | Signed, scaled raw operands, source quantisation steps, residuals, budgets, exclusions, missing operands, period, geography, source statuses and accounting basis. |

A source cell is `sheet!coordinate`. The explicit `sheet!@sheet` marker means
the workbook worksheet title, not a fictitious Excel cell; this is the historical
sheet's retained percentage unit. The databank's percentage unit is at `C5`.
All monetary displayed values are GBP billion. PESA Table 5.2 source operands
are GBP million and use scale 0.001. GDP percentages are percentage points,
with scale 1, not monetary values.

Every contract also identifies the source's label, period and unit evidence.
Fixed source coordinates are bound to the product's meaning, rather than accepted
because their numbers happen to agree. For example, base-year cash and real
health values are equal, but their cells and price bases are not interchangeable.
A missing category, duplicate category, wrong year, extra value or overlapping
parent/subcategory cannot silently alter a product partition.

`data/audit/pinned-source.json` is the permitted byte-identical copy of the
protected pinned manifest. Its identity and the eight readable extracts remain
the seed's evidence boundary; no raw/reference input is modified.

## Missingness, formulas and status

Blank, empty text, literal dash and numeric zero are separate source states.
A numeric zero remains present even when its Excel format displays a dash.
PESA's retained notes do not establish the meaning of every literal dash, so
those dashes remain unavailable/unspecified, never zero. Historical functional
notes describe coverage gaps at Contents D50/D52/D53/D56. Missing historical
operands produce a named `not_testable_missing` ledger entry, never a filled-in
sum. Missing required PESA values/operands stop construction and verification.

The retained source-cell formulas are preserved independently of source cached
values. These eight extracts contain no Excel formulas; the historical residual
derivations instead appear as text at E6 and N6 and in Contents D49/D58. The
ledger names those derivations and operands. It does not manufacture Excel
formulas. The E6/N6 source derivation text is retained with the ledger's evidence.
The source's historical “other” residual is explicitly distinguished
from an independent accuracy check.

PESA status is outturn through 2025-26 (4_1 B3), with subsequent aggregate years
forecast. Tables 4.2–4.4 say outturn at B4; Table 5.2 uses the year/outturn headers.
Price and forecast notes at 4_1 B51/B52 retain the 2025-26 base, ONS June release
and 3 March 2026 OBR forecast provenance.

OBR historical databank values are **uncertain actual/estimate status**, not a
uniform observed series. Each value retains B2/B139/B144/B148, and the relevant
numerator and denominator update notes. Numerator B142 covers 1945-46 and earlier
(1973-74 and earlier for debt); B143 applies later through 2025-26. Denominator
B146 covers through 1947-48; B147 covers later through 2025-26. These different
update ranges and the contradictory March/October forecast wording remain
visible. Future raw databank identity checks are labelled forecast with unresolved
vintage, rather than historical outturn.

Historical functional values use joined-source uncertainty, their individual
Contents D51/D52/D53/D56/D57 notes and D31/D64 period/geography notes. The fixed
displayed decades end at 2015-16. D51:D56's 2022-23 extrapolations are explicitly
estimates and do not extend the displayed decades as observed data. Historical
reconciliation records preserve changing geographic coverage rather than
assigning modern UK boundaries to all years. The 2022-23 function reconciliation
explicitly includes extrapolated components alongside the joined historical
series; its status is not uniformly observed or historical outturn.

Shares use same-period TES as denominator; changes use the same series, unit,
price basis and geography at two periods. They use the published operand values,
so a reader can reproduce the displayed result. Both operands and the formula
are retained; missing or zero denominators yield no calculation.

## Source-specific consistency budgets

These are arithmetic consistency checks of the retained snapshot, **not
statistical or measurement error bounds**. They do not establish the accuracy of
a source, explain revisions or equate different accounting bases.

| Comparison | Budget and evidence |
| --- | --- |
| PESA functions, TES/adjustments/TME and aggregate/base-price identities | The retained Chapter 4 monetary operands are stored on a 0.1-billion grid. Verify that grid first. The nearest-rounding consistency budget is the sum of half a grid step for every signed operand, including the total. Thus 11 functions plus TES have a 0.6-billion budget; TES plus adjustments minus TME has 0.15 billion. These budgets test consistency under the stated rounding model, not unobserved precision. |
| Table 5.2 totals versus Table 4.2 | Chapter 5 operands are stored in integer million; verify that grid before scaling. One 0.001-billion operand and one 0.1-billion operand give 0.0505 billion. |
| Five debt components versus their Table 5.2 total | Use original integer-million operands, not the site's rounded tenths of a billion. Six signed operands give 0.003 billion. No plug or balancing component is added. |
| OBR borrowing and historical residual identities | Use the retained full numeric ratios, not the one-decimal display format. No source rounding allowance is inferred from that format. A 1e-9 percentage-point numerical allowance covers finite-precision arithmetic; incompatible source identities fail rather than receiving an invented fiscal error budget. |
| Newer OBR versus PESA spending/GDP | Report the signed raw difference. Mark `not_comparable`, with no budget or proximity pass. The former 0.5-point threshold is removed; different vintages and GDP bases do not establish an error bound. |

The ledger retains signed residuals, even when they are nonzero but within the
stated grid consistency model. PESA accounting adjustments are explicit operands.
Selected items are subsets, never extra functions. Historical pensioner and
non-pensioner subsets J/K are excluded from the five-area-plus-other sum.
Missing historical components are named individually. Methods shows a table of
latest-year and selected historical residuals; the download contains all records.

## Verification boundary and controller handoff

`fiscal_contract.py` is the declarative semantic schema. `fiscal_schema.py`
constructs metadata and the ledger from readable, hashed extracts.
`check_fiscal.py` does not call the producer's metadata, reconciliation,
partition or context constructors, renderer or audit reader:
it reopens retained raw workbooks with openpyxl, checks source identities and
labels/units/periods, separately derives metadata and reconciliation operands
(including raw-label and period lookups), recomputes numeric transformations,
derived arithmetic and residuals, and compares every retained raw operand.
The checker shares declarative series/status/formula policy with the producer;
this is not independent model review or fiscal interpretation approval.

The existing separate ZIP/XML exporter versus openpyxl audit check remains in
`make verify`. Fiscal corruption tests additionally cover equal-valued wrong
cells, units/scales/scopes/status/periods, missing required values, duplicate and
missing categories, overlapping totals, broken raw identities, changed budgets,
wrong derived operand order, fabricated missing values and changed source metadata.
Producer-mutation tests also prove that wrong producer metadata and an
equal-valued cash/real ledger-cell substitution fail separate checker expectations.

The original worker timed out before executing checks; its partial work and
failure evidence are preserved. The bounded integration repair moves enrichment
from the aggregate-list parser to the completed dataset, separates verifier
expectations, and regenerates `data/spending.json` and `site/` in credential-free
Boat. Exact-seed execution receipts belong in the private recovery handoff,
not in public output. Product programs and tests are never run on the host.

The existing controller must still obtain independent product/fiscal review,
repeat its exact-candidate gates, and verify the deployed bytes at
https://unpoliticalaf.vercel.app. Passing seed checks cannot close #20 or #4.
Human reviews, source-publication approval, a year of freshness history and
rubric scores remain unobserved until their owning gates supply evidence.
