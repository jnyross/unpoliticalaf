# Issue #4 evidence recovery seed

This is a bounded seed for a new recovery ticket, not completion or a retry of
original issue #4. Base: `bbb0d143ad09df9ef684192babe0a14a251eb7ed`.
The stopped original attempt `1793363840763660661` made no changes and had no
candidate. Its controller receipt SHA-256 is
`21f4b94942e41e98046e1a88ceafee06d1fd2d90c4bee670a0eae2d9422c8832`.
Its final blocker was missing readable, hash-bound source evidence: normal roles
cannot inspect protected `data/raw/` and `reference/`. Those protections remain.

The repair supplies [scoped readable extracts](../data/audit/README.md) under an
allowed product path and a separate raw-workbook checker. The selected source
manifest is copied verbatim there. The seed needs no controller or installed
software-factory change. It does not change original sessions, tracker state,
claims, configuration, raw snapshots, source catalogue, output allowlist or
deployment. Issue #3/#19 work is preserved.

The small product changes resolve queued advisories: selected-item caption;
PESA outturn boundary and forecast/price notes read and checked against the raw
workbook; total-history start/end labels derived from the actual series; prose
line breaks; the previously recorded Vercel contract restored with its evidence
and live-verification limit. The generated seed output is rebuilt on Boat.

## Interpretation that must remain open

The OBR databank worksheet is internally inconsistent. `Public finances since
1900!B2` says March 2026 forecasts/latest outturn 21 July; `B139` says October
2026 forecast years from 2026-27; `B143` names a 22 September 2026 numerator
update through 2025-26; `B144` and `B148` combine October updates with March
forecast wording. Retain and cite the series-specific notes; do not claim that
all October-workbook sheets have the same unambiguous status or forecast date.
The current displayed decade totals stop at 2025-26, but a complete per-cell
status policy still needs independent fiscal review.

Historical functional series are joined sources, not National Statistics.
`Contents!D51:D56` describe extrapolated 2022-23 values for several functions.
The current decade selection ends at 2015-16 for those functions. Do not extend
the displayed series and silently describe extrapolations as observed values.

Literal dashes, blanks, numeric zeros, exact numeric precision and workbook
formats are retained separately. The extracts do not establish a general dash
definition, a statistical error bound, or a rounding-based justification for
the existing cross-vintage OBR/PESA 0.5-point comparison tolerance.

## Original acceptance still required from the recovery ticket

All original #4 acceptance remains unchanged. This seed supplies auditable
inputs and focused source-note checks; it does **not** claim all of the following:

- A complete per-value schema binding source ID/file/hash, publication/retrieval,
  exact label/cell or series, period, unit/scale, geography, accounting scope and
  actual/estimate/forecast status. The existing `v`/`ref` format is still partial.
- A complete formula-and-operands schema for every derived figure, with reviewed
  table-specific missing/dash semantics and the OBR status conflicts resolved or
  explicitly represented as uncertainty.
- Fiscal tests that reject equal-valued wrong semantic cells, wrong fiscal units,
  missing required data, duplicate categories, overlapping totals and broken
  reconciliation. Seed tests reject such corruption at the **audit-cell** boundary;
  that does not establish the broader fiscal-schema checks.
- Source-justified tolerance budgets and recorded residuals/exclusions for each
  reconciliation; the seed preserves the current arithmetic/tolerances, without
  forced balancing or claiming the existing 0.5-point vintage check is a source
  error bound.
- Independent fiscal/product review, exact-candidate factory acceptance and
  canonical live verification. No self-review, human study, score or deployment
  is invented by this seed.

Passing `make setup build verify smoke` on the exact seed is software evidence
for this boundary. The parent/controller must bind its exact reviewed seed SHA
to the new recovery ticket through the approved interface and run the remaining
work through existing independent factory gates. Original #4 stays incomplete.
