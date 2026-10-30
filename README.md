# UnpoliticalAF

A new, separate project to make it easy to understand **where UK public money is
spent and how taxes are raised**. It inherits evidence and principles from
Un-political, not a mandate to reuse its implementation. The current delivery is
an honest static setup baseline, not the fiscal application.
No autonomous factory, deployed site or completed product is claimed.

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
for UnpoliticalAF**. The current user authorizes a dependency-light static
baseline for import into
Vercel. This does not select the future fiscal application stack, database or any
paid service. Prefer small, reversible decisions after checking the delivery brief.

`/home/john/projects/un-political/CLAUDE.md` contains that repository's direct-to-main
commit/push policy and verification rules. Its permissions do **not** transfer
here. The current user independently authorizes
initializing this project, adding exactly `https://github.com/jnyross/unpoliticalaf`,
and committing/pushing the reviewed static baseline to `main` without force.
Do not modify the sister repository. Inherit its raw-source discipline and
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
Static-baseline checks are not evidence that these fiscal-product gates passed.
No completed fiscal app, deployment or running factory is claimed here.

## Current authorization and delivery boundary

The current user request supersedes earlier readiness-only prohibitions for this
bounded baseline. Initialize only if needed, inspect existing history/remotes,
fetch remote history if any, and publish a reviewed baseline without overwriting
unexpected work. The repository must remain private. Report the actual pushed SHA
and compare it with remote `main`; documentation is not proof of publication.

John handles the Vercel project connection in his existing signed-in browser and
separately verifies the native Claude route. Do not request Vercel CLI/login,
deploy, install/bootstrap/activate the factory, change providers/billing/defaults,
purchase anything or start direct Anthropic calls in this baseline task. All
Claude calls must use CLIProxy; ordinary delegates must use configured available
proxy models, not senior-dev's unconfigured `z-ai/glm-5.1` default.

The product brief and independent fiscal acceptance gates above remain in force.
`AUTONOMOUS-BRIEF.md` describes the later fiscal product, not a claim that the
static setup baseline satisfies it; its older readiness-only approval wording is
superseded only to the extent explicitly authorized here. Keep raw/private source
snapshots, runtime configuration, credentials and notes out of the published build.

## Static baseline: local commands and Vercel import

Prerequisites: Python 3.10 or later and GNU Make. There is no Node/npm requirement,
package installation, application framework or database. Standard-library Python
keeps the baseline small and reproducible; this is not a decision to reuse the
sister project's spreadsheet pipeline or select the future fiscal app stack.

Run from this checkout's root:

```sh
make setup
make build
make verify
make smoke
```

`make setup` checks prerequisites without installing packages. `make build`
(`make site` is an alias) writes deterministic output to ignored `site/`.
`make verify` runs the baseline integrity tests; `make smoke` checks the built
site over local HTTP. These are commands to run, not a claim of passing results
in this documentation. Review and execution evidence must name the exact candidate.
Only `static/index.html` and `static/styles.css` belong in the published output;
root instructions, source snapshots, tests and private/runtime files do not.

For the user's existing Vercel Git import:

| Setting | Value |
| --- | --- |
| Repository / branch | `jnyross/unpoliticalaf` (private), `main` |
| Root directory | Repository root (`.`) |
| Framework preset | Other |
| Install command | `make setup` (no packages) |
| Build command | `make build` |
| Output directory | `site` |

The relative output is `site/`; its absolute path is the current checkout root
plus `/site` (run `pwd` at the root). In this assigned worker checkout that is
`/home/john/.codeaf/v3/projects/-home-john/672c0985f766aca6/trees/7/site`.
The coordinator must report the actual final checkout's absolute output path,
not mistake this isolated task path for a deployment path.

The factory guide's `make setup`, generation and verification examples must be
adapted to these real commands if activation is later authorized and verified.
No factory configuration is created here. The baseline output does not contain
financial datasets or prove product, browser-accessibility or live-deployment gates.
