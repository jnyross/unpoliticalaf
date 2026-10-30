# UnpoliticalAF product specification

## Outcome and authority

Build and deploy a complete, plain-English and impartial account of UK public
spending, taxation, borrowing, debt and party proposals. John authorised this
full product build on 30 October 2026, replacing the earlier placeholder-only
scope. Use the existing static Python pipeline and factory, and reuse verified
product material before writing replacements.

The source of this specification is `jnyross/un-political` at immutable commit
`8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713`, especially
[`docs/rubric.md`](https://github.com/jnyross/un-political/blob/8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713/docs/rubric.md)
and its README. The archived reference files and their hashes are in
`reference/un-political/SOURCE.json`. They are evidence and reusable source,
not another application or factory. The original repository stays read-only.
Its historical 18/32 assessment is not a score for this new site.

## Target and improvement loop

John's acceptance target is **at least 9.5/10**, using the original eight-dimension
rubric unchanged. Compute the normalized score as `total / 32 * 10`; because the
source rubric uses integer levels, the target is **at least 31/32**. Do not round
30/32 up, change the weights, relax a criterion or award partial levels to reach it.

After each delivery wave, an independent assessor scores the actual deployed
revision against every level, using dated checks and source evidence. Each level
requires all levels below it. Record the commit, live URL, per-dimension score,
evidence, unmet criteria, total and normalized score. Unknown or unperformed
evidence earns no point. Link the assessment from the product epic.

Below target, the rubric steward creates or updates dependency-ordered tickets
for the concrete deficits, avoiding duplicates and preserving current claims.
The existing factory builds, reviews, tests and deploys them, then assessment
runs again. Keep the goal active until a verified score reaches 31/32. If progress
needs real people or an owner's decision, surface the exact human-gate issue and
resume after evidence arrives; do not invent a pass, endlessly repeat the same
assessment, or mark the overall product complete.

## Product requirements

1. **Spending.** Explain the latest compatible fiscal year's public spending by
   area, spending on services, debt interest, pensions and defence. Show meaningful
   shares such as health out of each £100 of spending on services. Name the
   denominator and accounting scope; do not equate different spending totals.
2. **Income.** Show the actual tax-type breakdown, non-tax receipts, borrowing
   and debt. Reuse the archived OBR receipt sheets before seeking new datasets.
   Explain that borrowing is not tax, receipts are not all tax, and debt is a stock
   rather than annual borrowing. Reconcile only compatible accounting bases.
3. **History.** Include at least 20 years of total and functional spending history
   and fixed ten-year comparisons back to 1945-46 wherever data exists. Show missing
   years and definition breaks explicitly. Never invent values or cherry-pick years.
4. **Honest context.** Provide cash, inflation-adjusted and GDP-share views where
   comparable data supports them. Name the deflator, base year and source. Label
   actuals, estimates and forecasts with the source's own vintage. Keep forecast
   styling distinct. Put important scope and definition notes beside the chart.
   Each section shows publication/as-of dates and the next announced release date,
   or explicitly says that no next release date is announced.
5. **Party proposals.** Cover every party represented in the House of Commons at
   a dated roster snapshot. Apply identical fields, order, length limits and visual
   treatment. Use neutral alphabetical ordering and no party colours or editorial
   ratings. Separate official party claims from independent assessments. Policy
   judgements must be linked, attributed quotations from IFS, OBR, Resolution
   Foundation, Full Fact or NAO. Missing costings or assessments are stated as
   unavailable, not manufactured. Record proposal scope, baseline, year and status.
6. **Evidence.** Every displayed number resolves to a retained official source,
   file hash, publication, exact table/sheet/cell or series locator, fiscal year,
   unit, geography, accounting scope and actual/estimate/forecast status. Derived
   numbers name the formula and operands. Missing is not zero. Checks reopen raw
   data independently, reject changed hashes, and enforce source-justified rounding
   and reconciliation tolerances. One command rebuilds data and pages reproducibly.
7. **Plain language.** The following eight source-rubric questions are answerable
   within two clicks and without passing a screen of unrelated content:
   - What does government spend the most on?
   - Of every £100 spent on services, how much goes on health?
   - How much debt interest was paid in 2025-26, with its status labelled?
   - Has real health spending risen or fallen over the latest ten comparable years?
   - Is spending a larger or smaller share of GDP than ten comparable years ago?
   - How do old-age pensions compare with defence?
   - Which numbers are forecasts?
   - Where can I check this number?
   Add equally clear answers for the main taxes, receipts, borrowing and debt.
   Enforce the source's documented reading-grade approximation at grade 7 or below.
8. **Impartiality.** Enforce the source's published banned evaluative-word list
   and neutral palette. Apply any government annotations consistently to every
   government. Preserve an append-only corrections log with date, page, error and
   correction, and provide the same evidence standard for every party.
9. **Accessibility.** Full core content works without JavaScript. Every chart has
   a semantic table alternative; colour never carries meaning alone. At 360px there
   is no lost content or unusable navigation. Each HTML page is below 500KB. Check
   all pages and expanded states with zero WCAG 2.2 AA axe violations at mobile and
   desktop widths, including contrast. Also record keyboard and screen-reader checks.
10. **Openness.** Publish methods, definitions, limitations, OGL attribution on every
    page, downloadable open datasets, raw-source references and a reproducible README.
    Name the operator, state verified funding information and provide a working public
    error-reporting route. Keep the repository private until John explicitly approves
    public source publication; do not treat a private GitHub issue link as a public
    reporting route. Do not invent funding or contact details.
11. **Freshness.** Provide a documented one-command refresh with validation, a
    reviewable version/diff report and safe retention of the last good data on errors.
    Attach source-release detection to the existing owning factory schedule, rather
    than a second independent scheduler. Cover each data family and party roster/plan
    sources. Prove a real scheduled check and deduplicated update reporting.
12. **Live completion.** Run the declared build, data, reconciliation, browser and
    accessibility gates on the exact candidate; independently review fiscal claims
    and the product. Deploy through the existing factory to
    `https://unpoliticalaf.vercel.app` and compare live bytes with the committed output.
    Record revision, source vintages, review findings, checks and deployment receipts.
    Append evidence-backed rubric assessments rather than rewriting history.

## Reuse and source boundaries

`data/raw/` and `data/sources.json` are a hash-verified seed from the pinned source.
The reference scripts, asset, requirements and human-check protocols can be adapted
into the new product by tickets. Do not copy the old factory, credentials, CI,
agent instructions, deployment bindings or operational state. Preserve the new
repository's setup/build/verify interface and current factory safety checks.

The OBR October 2026 workbook has `Receipts (£bn)` and compatible aggregates;
the historical workbook has `Receipts (£m)` and `Receipts (per cent of GDP)`.
Those sheets were not used by the old renderer. Their actual/forecast notes must
be checked per series; the old site's March 2026 forecast note is not a universal
description of the newer receipt data.

## Evidence the factory cannot fabricate

Software delivery and external evidence are tracked separately. Five eligible
people must actually answer at least seven of the eight questions correctly in
under five minutes. Two independent people with opposing self-described political
leanings must consent to and perform the impartiality reviews. Manual keyboard
and screen-reader checks need observed results. Public source visibility and a
public error-reporting route need John's decision. A full year of timely updates
requires a real year of history. These remain explicit acceptance tickets;
unperformed work must not be scored as passed.

The source's 31/32 aspiration needs all applicable lower levels plus the human
evidence. Freshness level 4 cannot be claimed until the required year exists.

## Delivery order

The [GitHub product epic](https://github.com/jnyross/unpoliticalaf/issues/2) links the executable tickets. Start by porting the verified
spending product, then strengthen provenance, add receipts and history, add parties,
finish accessibility/accountability and refresh tooling, and perform final live
qualification. Dependency declarations use `Blocked by: #N` so the existing
factory can run eligible tickets in order. Human-gate issues are not executable
model tickets. The factory's current qualification issue must succeed first.
