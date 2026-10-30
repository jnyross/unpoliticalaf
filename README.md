# UnpoliticalAF

A new, separate project to make it easy to understand **where UK public money is
spent and how taxes are raised**. It inherits evidence and principles from
Un-political, not a mandate to reuse its implementation. This workspace is for
build readiness; this README does not mean an app or an autonomous team is running.

## Verified inheritance

Read-only inspection on 2026-10-30 of `/home/john/projects/un-political` found:

| Foundation / current coverage | Absolute source and evidence |
| --- | --- |
| Plain English, impartial presentation, official figures and source-cell traceability | `/home/john/projects/un-political/README.md`; `/home/john/projects/un-political/docs/rubric.md`, accuracy, impartiality and comprehension sections |
| Fail on unreconciled data; keep source files, URLs, dates and hashes | `/home/john/projects/un-political/scripts/build_data.py`, `reconcile()` and module description; `/home/john/projects/un-political/data/sources.json` |
| Distinguish actuals from forecasts; explain inflation-adjusted/cash/GDP comparisons and definition breaks | `/home/john/projects/un-political/docs/rubric.md`, honest context; `/home/john/projects/un-political/scripts/build_site.py`, forecast styling, view controls and methods |
| Accessible/mobile content, chart tables and no-JavaScript fallback | `/home/john/projects/un-political/docs/rubric.md`, accessibility criteria and recorded level-2 evidence; `/home/john/projects/un-political/scripts/build_site.py`, tables and viewport |
| Spending by area plus historic total income, borrowing and debt already exist | `/home/john/projects/un-political/scripts/build_site.py`, history section; `/home/john/projects/un-political/scripts/build_data.py`, OBR aggregate definitions |
| **Tax-by-tax revenue breakdown remains a gap** | `/home/john/projects/un-political/docs/rubric.md`, ten-year history evidence explicitly says coverage level 3 still needs the split by tax; `/home/john/projects/un-political/scripts/build_site.py`, methods “What this site does not cover yet” |

The rubric records an 18/32 score, not completion of all its aspirations. Its
recorded evidence includes 989 checked figures, but that verifier was **not rerun**
for this setup. Automated WCAG and manual screen-reader checks were not established
by this inspection; recorded mobile/no-JavaScript evidence is not full accessibility
certification. Source metadata is inherited evidence, not a fresh external audit of
publication dates or a claim that these are still the latest releases.

## Historical stack, not a new stack decision

The sister README documents Python (CI uses 3.12), `openpyxl`, Make, spreadsheet-to-JSON
processing, generated static HTML and a site that opens without a server. Its
`scripts/build_data.py`, `scripts/build_site.py` and `scripts/check_site.py` implement
that pipeline. These are historical implementation facts, **not an approved stack
for UnpoliticalAF**. No framework, hosting, database or paid service is selected here.
Prefer small, reversible decisions after checking the delivery brief.

`/home/john/projects/un-political/CLAUDE.md` contains that repository's direct-to-main
commit/push policy and verification rules. Its commit/push permission does **not**
transfer here: no commits, remotes, publication or deployment are authorized by this
setup. Do not modify the sister repository. Inherit its raw-source discipline and
append-only evidence history, not its repository-specific workflow permissions.

## Bounded first usable version — proposed delivery scope

These are working assumptions for the team to validate, not invented user decisions:

- One UK-wide overview for one clearly labelled common fiscal year, selected only
  after confirming compatible official spending and receipts coverage. Do not assume
  the sister's 2025-26 outturn designation is valid for every new tax source.
- Show spending by understandable functional area, with official labels available,
  plus major tax revenue categories and explicitly identified remaining taxes and
  non-tax receipts. Explain income tax, National Insurance and VAT in plain English
  where the selected official classification supports those categories. Never
  label total public receipts as entirely tax or borrowing as tax revenue.
- Show the relevant published totals and explain the spending/receipts gap as
  borrowing only on a compatible accounting basis. Separate debt (a stock) from
  borrowing (a flow). Distinguish spending on services from Total Managed Expenditure;
  expose accounting adjustments, not a forced equality between unlike totals.
- Every displayed number must resolve to publisher, publication, source URL, release
  date, stored raw-file hash, table/sheet/cell or equivalent locator, fiscal year,
  unit/scale, geography/accounting scope and actual/estimate/forecast status. Derived
  figures need formulas and input references; missing figures are not zero.
- Reconcile non-overlapping categories to their stated totals with explicit,
  source-justified rounding tolerances. Reconcile receipts composition and, where
  definitions permit, spending minus receipts to borrowing. Document definition
  bridges and residuals; fail unexplained mismatches rather than hide them.
- Include a modest time comparison only where comparable series exist, with cash,
  inflation-adjusted (named deflator/base year) and GDP-share context. Mark revisions,
  forecasts and series breaks visibly. No cherry-picked comparison years.
- Provide plain-English answers to “where does most money go?”, “which taxes raise
  it?”, “which year/status is this?” and “where can I check it?”. Neutral presentation,
  readable source notes, downloadable data, methods and licence attribution belong
  in the first slice, not just charts.
- Make the complete core content usable at 360px, by keyboard and without JavaScript;
  pair charts with semantic tables and test WCAG 2.2 AA automatically plus manual
  keyboard/screen-reader use. Do not claim compliance before recording evidence.

Party policy comparisons, tax calculators, exhaustive historical coverage, accounts,
paid integrations and public deployment are outside this initial slice. An incompatible
source/year or material scope expansion must be surfaced rather than silently guessed.

## Completion evidence required from the build team

Readiness documents are not product completion. A delivered first slice needs a
reproducible raw-data-to-rendered-page command; passing hash/provenance and reconciliation
checks (including negative tests for broken totals, missing values and wrong units);
and real browser end-to-end checks of spending, tax, source links, year/status labels
and mobile/keyboard navigation. Check rendered values against raw sources independently
of the renderer, including derived values and units. Record browser accessibility and
manual checks, test commands and results, source release dates and unresolved limits.
An independent QA/data reviewer must verify fiscal definitions, totals, provenance,
neutral copy and the end-to-end evidence before the delivery lead accepts completion.
No app, test pass, independent review, deployment or running AI team is claimed here.
