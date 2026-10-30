# What "working well" means

Un-political is working well when anyone in the UK can open it, understand where public
money goes and what each party proposes, check every number against the official source,
and find no sign of which side the site is on.

This rubric scores the product against that goal. There are eight dimensions, each scored
0 to 4. Every level is a check that someone else can run and get the same answer. A level
counts only if every level below it is also met.

Maximum score: 32. A score is only valid with the date, the commit and the evidence for
each line.

## 1. Accuracy and traceability

| Level | Check |
|---|---|
| 0 | Numbers are typed by hand or have no stated source. |
| 1 | Every page names its source publication. |
| 2 | Every figure shown resolves to a source file, table, row label and year, and the raw source files are kept in the repo with their download URL, date and SHA-256 hash. |
| 3 | The build fails if the data does not reconcile: parts add up to their published totals within rounding, cross-table totals agree, and real-terms figures equal nominal figures in the base year. |
| 4 | Each figure on the page is regenerated from the raw files by one command, and a check confirms the published page matches the regenerated output exactly. |

## 2. Impartiality

| Level | Check |
|---|---|
| 0 | The site contains opinion, evaluative adjectives or party-coloured framing. |
| 1 | A published list of banned evaluative words ("massive", "slashed", "soaring", "savage", "generous", "reckless" and others) is checked automatically and none appear in page copy. |
| 2 | Charts never use party colours, and every year axis is shown without highlighting which party was in government unless every government is shown the same way. |
| 3 | Every party's offer is shown using the same template, with the same fields in the same order, and the same length limits. Judgements on whether a policy is good appear only as attributed quotes from named independent bodies (IFS, OBR, Resolution Foundation, Full Fact, NAO), with links. |
| 4 | A public corrections log exists, and a reviewer from each of at least two opposing political leanings has read the site and their comments, and the site's responses, are published. |

## 3. Plain-language comprehension

A fixed set of test questions, each with an answer that comes straight from the data.
Comparisons step back from the latest year in tens of years (ten years ago, twenty years ago, and so on back
to 1945-46), never chosen by hand:

1. What does the government spend the most on?
2. Out of every £100 of spending on services, how much goes on health?
3. How much was spent on paying interest on government debt in 2025-26?
4. Has health spending gone up or down in the last ten years once inflation is taken into account?
5. Is total spending a bigger or smaller share of the economy than ten years ago?
6. How much goes on pensions paid in old age, compared with defence?
7. Which numbers on the page are forecasts rather than actual spending?
8. Where can I check this number myself?

| Level | Check |
|---|---|
| 0 | The questions cannot be answered from the site. |
| 1 | All eight answers are on the site. |
| 2 | Each answer is reachable in two clicks or fewer from the home page, without scrolling past more than one screen of unrelated content. |
| 3 | Page copy scores at a reading age of 12 or lower (Flesch-Kincaid grade 7 or lower), checked automatically. |
| 4 | At least five people who do not follow politics answer at least seven of the eight correctly in under five minutes, and the results are recorded. |

## 4. Honest context

| Level | Check |
|---|---|
| 0 | Money figures appear with no adjustment or context. |
| 1 | Every money-over-time chart can show cash, inflation-adjusted and share-of-the-economy views, and says which one is shown. |
| 2 | Forecasts look different from actual figures (for example, dashed lines) and are labelled as forecasts with their source and date. |
| 3 | Breaks in a data series and definitions that differ from common use (for example, how defence spending is counted differently from NATO's measure) are flagged on the chart they affect, not only in a footnote. |
| 4 | Each section shows the date of the data and the next scheduled update, and the site never shows data that has since been revised without saying so. |

## 5. Coverage

| Level | Check |
|---|---|
| 0 | Nothing published. |
| 1 | Where the money goes in the latest year. |
| 2 | Plus the history of spending, overall and by area, over at least 20 years. |
| 3 | Plus where the money comes from (taxes and borrowing) and how much debt the country has. |
| 4 | Plus every party with MPs in the House of Commons, shown in the same template, with independent assessments of their costed plans. |

## 6. Freshness

| Level | Check |
|---|---|
| 0 | No data date shown. |
| 1 | Every page shows the publication and date of its data. |
| 2 | Refreshing the data for a new release is one command, documented in the README. |
| 3 | A scheduled check notices new releases of each source and opens an update for review. |
| 4 | Over the past year, every update went live within four weeks of its source being published. |

## 7. Accessibility and reach

| Level | Check |
|---|---|
| 0 | The content needs JavaScript or is unusable on a phone. |
| 1 | Every chart has a data table next to it, and the full content works with JavaScript turned off. |
| 2 | The page works on a 360-pixel-wide screen and each page is under 500 KB. |
| 3 | An automated WCAG 2.2 AA check passes with no errors, including colour contrast. |
| 4 | Checked by hand with a screen reader and keyboard only, with the results recorded. |

## 8. Openness

| Level | Check |
|---|---|
| 0 | No information on how the site works or who runs it. |
| 1 | A methods page explains where the data comes from and how it is processed, and the required Open Government Licence attribution appears on every page. |
| 2 | All data behind the site can be downloaded in an open format. |
| 3 | The page states who runs the site, how it is funded and how to report an error. |
| 4 | The code and data pipeline are public, and anyone can rebuild the site from them. |

## Scores

Record a new row each time the site is scored. Never overwrite earlier rows.

| Date | Commit | Accuracy | Impartiality | Comprehension | Context | Coverage | Freshness | Access | Openness | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-29 | 3e7fec2 (baseline) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/32 |
| 2026-10-29 | first-slice | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | ten-year history | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | fcbadfc + CI setup (working tree) | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | b4e1f5c + native factory adoption (working tree) | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | native source inspection correction | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | T3 agent-box operator checklist (setup only) | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | operator guide clarification | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | About and corrections log (ticket #9, source only) | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |
| 2026-10-29 | WCAG gate (ticket #10, conditional on candidate passing make verify) | 3 | 2 | 3 | 3 | 2 | 1 | 3 | 2 | 19/32 |
| 2026-10-29 | Human-check protocols (ticket #19, docs only; same conditional WCAG score) | 3 | 2 | 3 | 3 | 2 | 1 | 3 | 2 | 19/32 |
| 2026-10-30 | a7e4b2fa9e6f10032443206e3f2473167d8f205f (#25 evidence rescore) | 3 | 2 | 3 | 3 | 2 | 1 | 2 | 2 | 18/32 |

### Evidence for 2026-10-29, first-slice

Checked with `make verify`, headless Chromium screenshots at 1100 px and 360 px wide, and a
headless Chromium test of the view buttons and the tap-for-source note.

- **Accuracy 3.** `check_site.py` reopens the raw spreadsheets and confirms all 901 figures on
  the home page match the cell they name, including calculated shares and changes. The build
  fails unless seven reconciliation checks pass (listed on the methods page). Level 4 is not
  met: `make verify` confirms the committed site matches a fresh build, but the site is not
  published anywhere yet.
- **Impartiality 2.** No banned words; the colour check allows only greys. The site's icon
  was amber, which reads as a party colour, and is now dark grey. Level 3 needs party pages.
- **Comprehension 3.** All eight answers are in "Quick answers" at the top of the home page,
  one click each. Reading grade 2.7 (home) and 3.8 (methods). The grade uses a simple
  syllable counter, and leaves out official names and the licence line. Level 4 needs
  testing with real people.
- **Context 3.** Each line chart has inflation-adjusted, cash and share-of-GDP views.
  Forecasts are dashed, shaded and sourced to the OBR forecast of 3 March 2026. Breaks for
  student loans (2011-12) and Network Rail (2015-16) are marked on their charts, and the
  defence definition note sits directly under the defence chart. Level 4 needs the next
  update date on each section.
- **Coverage 2.** Spending by area for 2025-26, totals since 1985-86 and each area since
  2003-04. Level 3 needs taxes, borrowing and debt.
- **Freshness 1.** The data date is on every page. Level 2 is not met: a new release needs
  four manual steps (README), not one command.
- **Access 2.** Every chart has a table, and the page works without JavaScript (shows the
  inflation-adjusted view). It reads at 360 px wide; the home page is 226 KB. Level 3 needs
  an automated WCAG check, which has not been run.
- **Openness 2.** The methods page, the licence line on every page and a JSON download are
  in place. Level 3 needs who runs the site, how it is funded and how to report an error.

### Evidence for 2026-10-29, ten-year history

Adds the OBR public finances databank (October 2026) and the OBR historical public
finances database. All comparisons now step back in tens of years. The new section shows
spending, income, borrowing and debt every ten years from 1945-46 to 2025-26, and five
areas every ten years from 1945-46 to 2015-16.

- All 989 figures match their source cells. Three new build checks: borrowing equals
  spending minus income in every year since 1900-01; the OBR history's five areas plus
  "other" add up to its total; and the OBR and Treasury totals for 2025-26 are within 0.5
  points (44.5% and 44.3%, both shown on the page with the reason they differ).
- No score changed. The history was already enough for Coverage level 2. Coverage level 3
  still needs the split by tax: total income, borrowing and debt are shown, but not which
  taxes the money comes from.
- Known limits, shown on the page: the OBR history is not National Statistics; it has no
  health or education figures for 1945-46; it ends in 2022-23, so its latest ten-year point
  is 2015-16; the databank has no borrowing figure for 1975-76.


### Evidence for 2026-10-29, CI setup only

This setup-only task adds continuous verification, not a product improvement. The
product score stays **18/32**, with all eight scores unchanged from the previous
row; existing product evidence and limitations still apply.

Local evidence on Python 3.12.3: `make setup`, `make verify`, `git diff --check`,
and `git diff --exit-code HEAD -- data/spending.json site/` all passed before
this row was appended. The verifier checked 989 figures against source cells,
and the rebuilt data and site matched HEAD. These are local results, not hosted
CI results. The new Verify workflow has not yet run on GitHub; no hosted CI pass
is claimed.


### Evidence for 2026-10-29, T3 agent-box factory integration

This infrastructure setup moves the runner to Cursor API v1 and checks the live
model catalogue before each launch. T3 on agent-box owns the signed GitHub issue
webhook, the 15-minute fallback and the 03:00 nightly Boat sweep.

The product score stays **18/32**, with all eight product scores unchanged.
Verification before publication: 21 factory tests, the 989-figure source-cell check,
a repeatable site rebuild, all five Boat gate shards on the baseline, and the
three production sweep shards launched through T3 passed. A real ticket through
the updated Cursor integration is a separate live check, not claimed by these tests.

### Evidence for 2026-10-29, native factory adoption preparation

This infrastructure-only change delegates the project entrypoints to the shared
OpenAI, Claude and Meta subscription factory on agent-box. It changes no product
page, source data or build calculation, so the product score remains **18/32**
using the existing product evidence. Earlier rows and their limits still apply.

This row records preparation, not a new verification result. The maintainer must
run the declared Boat checks and `make verify` before publication, then qualify a
real native-role ticket through deployment and live read-back. No host test,
publication, native provider run or production effect is claimed here.

### Setup-only correction, native source inspection

Permit read-only source inspection commands for native harnesses without a
file-reading tool. Tests and generated programs remain confined to Boat. This
changes no product content or score and does not claim a completed native ticket.

### Evidence for 2026-10-29, T3 agent-box operator checklist (setup only)

This documentation-only update replaces the retired Cursor model/run policy
with the configured OpenAI, Claude and Meta roles and records the agent-box
operator checklist, exact-candidate checks, publication and pause/recovery
workflow. Only `docs/factory.md` and this rubric change.

The product score remains **18/32**: Accuracy 3, Impartiality 2, Comprehension 3,
Context 3, Coverage 2, Freshness 1, Access 2 and Openness 2. All prior rows,
evidence and product limitations remain applicable.

Evidence is source inspection and documentation editing only. The model role
did not run the factory, programs or tests. The controller must run its Boat
checks, including `make setup`, `make verify` and wrapper tests. No new passing
check, live native-role run, deployment, recovery or hosted CI result is claimed.

### Setup-only evidence, operator guide clarification

Show the installed guide as a host-local path rather than a broken GitHub link,
and name the manual tick and smoke commands. Product content, calculations and
all eight dimension scores are unchanged; the prior evidence remains intact.

### Evidence for 2026-10-29, About and corrections log (ticket #9)

Source inspection shows that the site builder adds an About section naming
John Ross and a Corrections section on the existing methods page. The log reads
`data/corrections.json`, with date, page, what was wrong and what changed for
each entry. An empty list shows “No corrections yet.” The shared footer links
to both sections, and the site checker rejects a methods page missing either
section id. The README now gives clone, setup and rebuild steps, names the four
raw files and `data/sources.json`, and explains the clean diff check.

No score changes: the total stays **18/32**, with all eight scores unchanged.
Openness stays at 2: level 3 still needs funding details and a public way to
report an error. No funding or contact wording has been added. The corrections
log contributes to Impartiality level 4, which still needs published reviews
and responses from people with opposing political leanings; level 3 also still
needs party pages.

Evidence here is source inspection and file editing only. No program, test,
rebuild or live check was run by this role. The controller must generate the
site and run its isolated checks for figures, banned words, the neutral
palette, the 500 KB limit, reading grade 7 and a repeatable rebuild. No new
passing check or published result is claimed.

### Evidence for 2026-10-29, WCAG gate (ticket #10)

Access **3** and the resulting **19/32** total are conditional on this candidate
passing the controller's `make verify` gate. The other seven scores are unchanged.
This role inspected and edited source only; it did not run programs, rebuild the
site, install dependencies or claim a passing check.

`make setup` installs pinned `axe-playwright-python` (which bundles axe-core) and
Playwright. `make a11y` serves the built `site/` on loopback and audits every
`site/*.html` page in headless Chrome/Chromium at 360 px and 1100 px. It checks
both the default page and opened details, including the data tables and quick
answers. The selected tags are `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` and
`wcag22aa`, with colour contrast explicitly enabled. Missing Chromium, missing
bundled JavaScript, unsupported tags, audit errors or any violation fail the
check; there is no silent skip or check-time download. Each violation names
its rule, page, width, state and selector.

`make verify` now requires this zero-violation check alongside the existing
figure and rebuild checks. Muted text and chart greys are darker, keyboard focus
has an explicit outline, the chart controls have a navigation landmark, and a
skip link leads to the main content. Source notes can be opened with Enter or
Space and dismissed with Escape. Existing named view buttons, scoped table
headers and page language remain in place.

Access 3 is claimed solely on a successful zero-violation gate for this
candidate; it is not evidence of manual WCAG conformance or Access 4. Keyboard
and screen-reader review still needs to be recorded for that level.


### Evidence for 2026-10-29, human-check protocols (ticket #19)

Adds ready-to-run protocols for [comprehension user testing](user-test.md),
[manual accessibility checks](a11y-manual.md) and
[independent impartiality reviews](reviewers.md). They include the fixed eight
questions and section-linked answer key, recruitment and strict per-participant
timing/pass rules, full page/control coverage across keyboard and screen-reader
environments, and opposing-leaning review records with a planned publication
section on methods.html.

No scores change from the preceding row: Accuracy 3, Impartiality 2,
Comprehension 3, Context 3, Coverage 2, Freshness 1, Access 3 and Openness 2;
the total remains **19/32**. Access 3 retains the preceding row's condition that
the controller's candidate passes the WCAG gate. These documents supply no new
passing accessibility evidence and do not resolve that condition.

All human result tables are explicitly pending. No participants were tested,
no keyboard or screen-reader pass was performed, and no opposing-leaning
reviewers were recruited or published. Comprehension 4, Access 4 and
Impartiality 4 remain unclaimed; all lower-level requirements still apply,
including party-page requirements for Impartiality 3. The planned
methods.html#independent-reviews section has not been added by this docs-only
change.

Evidence is source inspection and documentation editing/read-back only. This
role ran no programs, tests, rebuilds or live checks; controller checks remain
pending. No product pages, data, calculations or earlier rubric rows changed.

### Evidence for 2026-10-30, final rescore for issue #8 (ticket #25)

**Recorded score: 18/32. The target of at least 31/32 is not met.** This
assessment identifies the supplied pinned base
`a7e4b2fa9e6f10032443206e3f2473167d8f205f`; the only change in this ticket is
this rubric entry. No future candidate commit or passing run is assumed.

Evidence was inspected through workspace file reads only. No programs, tests,
gate, live check, scheduled job or human session were run for this rescore.
The earlier first-slice, ten-year-history and CI-setup sections above record
observed checks; the supported lower scores below carry forward those recorded
results alongside the current source inspection. They are historical evidence,
not a new exact-candidate pass. The conditional Access 3 in the two preceding
rows has no recorded passing candidate result in the inspected evidence, so
Access returns to the evidenced level 2. Earlier rows remain unchanged.

#### Required evidence and observed status

| Check or artifact | Repository evidence inspected | Observed result / blocker |
|---|---|---|
| Gate pass for the candidate | [Makefile](../Makefile), [site checker](../scripts/check_site.py), [accessibility checker](../scripts/a11y_check.py), [factory checks description](factory.md#checks-review-and-publication); earlier rubric results above | The checks are implemented, and historical local/build checks are recorded above. No completed gate receipt tied to this candidate is recorded in these evidence documents. A command definition or an earlier baseline pass does not establish a candidate pass, including zero axe violations. |
| Live-check run | [factory publication and recovery procedure](factory.md#checks-review-and-publication); earlier Accuracy evidence above | The procedure requires Vercel status and exact-file live smoke. No dated live-check result, evaluated commit, public site URL and exact-file comparison result are recorded in the inspected evidence. Accuracy 4 remains unclaimed. |
| Scheduled source-watcher run | [README update procedure](../README.md#updating-for-a-new-pesa-release), [Makefile](../Makefile), [factory owning runtime](factory.md#owning-runtime-and-intake) | Updating still has four manual steps. No source-release watcher or completed scheduled run detecting each source and opening an update for review is recorded. The factory ticket fallback/nightly production sweep does not demonstrate source-release watching. |
| Comprehension user-test results | [user-test results and decision](user-test.md#results-and-decision) | P01–P05 are all “Not run”; round decision is “Not run”, with no evaluated commit or timings. No Comprehension 4 evidence. |
| Manual accessibility results | [manual coverage, findings and retest record](a11y-manual.md#coverage-findings-and-retest-record) | Coverage and results are “Not run”; the record says “No human checks recorded”. No Access 4 evidence. |
| Reviewer page and responses | [review publication record](reviewers.md#publish-and-decide), [methods page](../site/methods.html) | R01/R02 and comments remain pending; publication is “Not published”. The actual methods page has a corrections log but no `#independent-reviews` section. No completed opposing-leaning reviews or public responses. |
| Party pages | [methods omissions](../site/methods.html), [site builder](../scripts/build_site.py), inspected `site/` listing | The only HTML pages are `index.html` and `methods.html`; methods explicitly lists party plans as not covered. No equal-template party pages or linked assessments of costed plans. |
| Repository public status | [README rebuild instructions](../README.md#rebuild-from-scratch), [source manifest](../data/sources.json) | A GitHub clone URL and rebuild instructions are recorded. No dated observation of public visibility or successful unauthenticated clone/rebuild is recorded in the inspected evidence. Public status is unverified; no external lookup was performed. |

Controller receipts outside permitted evidence were not accessed. Missing
results are blockers, not inferred passes. Completion of dependency tickets
#20–#24 is not established by their ticket numbers or by protocols alone.

#### Evidence for each dimension

| Dimension | Score | Specific recorded check and current source observation |
|---|---|---|
| Accuracy and traceability | 3 | The ten-year-history evidence above records 989 figures matching source cells and the added reconciliation checks; CI-setup evidence records `make verify` and a matching rebuild. [Source metadata](../data/sources.json) records file names, publication/download dates, URLs and hashes. [Methods](../site/methods.html) lists the reconciliation rules; figures in [home](../site/index.html) retain table/cell references. Raw files were not reopened in this role. No candidate gate or published-page comparison result is available here for level 4. |
| Impartiality | 2 | First-slice evidence records the banned-word and neutral-colour checks passing; [the checker](../scripts/check_site.py) retains the word list and grey palette. [Home](../site/index.html) uses ten-year steps without highlighting governments. Party pages are absent, and [review records](reviewers.md) are pending; the [corrections log](../site/methods.html#corrections) alone does not establish levels 3 or 4. |
| Plain-language comprehension | 3 | First-slice evidence records all eight answers one click from home and automatic reading grades 2.7 (home) and 3.8 (methods), below grade 7. [Quick answers](../site/index.html#answers) still precede the spending sections and contain the eight answers; [the checker](../scripts/check_site.py) enforces grade 7. [User-test results](user-test.md#results-and-decision) remain unrun. Those historical grades are not a newly measured candidate result. |
| Honest context | 3 | First-slice evidence records testing of the money-view controls, dashed/shaded forecasts with the OBR source/date, and chart-local breaks and defence definitions. [Home](../site/index.html#total) retains the three labelled views and forecast note; [area notes](../site/index.html#areas) retain student-loan, Network Rail and NATO-definition warnings. Per-section next-update dates and an observed revision check are missing for level 4. |
| Coverage | 2 | Ten-year-history evidence records the source-cell check and history additions. [Home](../site/index.html#hundred) shows the latest spending split, [total spending](../site/index.html#total) runs from 1985 and [area histories](../site/index.html#areas) from 2003. [Methods](../site/methods.html) still lists the tax breakdown and party plans as omissions. Aggregate income, borrowing and debt do not fill the missing tax breakdown required by the earlier Coverage assessment. |
| Freshness | 1 | Publication dates are visible in both page footers and in the [source manifest](../data/sources.json). The [README](../README.md#updating-for-a-new-pesa-release) still requires a manual update sequence. There is no recorded scheduled source-watcher result or year-long update history. Freshness is capped at 3 until a year of on-time updates is evidenced; the cap itself does not award level 3. |
| Accessibility and reach | 2 | First-slice evidence records 360-pixel Chromium inspection, adjacent chart tables and usable content without JavaScript. The current [home page](../site/index.html) retains native table disclosures and the default inflation-adjusted view; inspected HTML file lengths are below 500 KB. [The automated audit](../scripts/a11y_check.py) is implemented, but no completed candidate zero-violation result is recorded. [Manual results](a11y-manual.md#coverage-findings-and-retest-record) are unrun. |
| Openness | 2 | [Methods](../site/methods.html) explains processing and checks; both page footers contain the OGL attribution and link to the JSON download present at `site/data/spending.json`. About names John Ross, but funding is unstated and “A way to report errors is coming soon” supplies no reporting route. [README](../README.md#rebuild-from-scratch) documents rebuilding, without an observed public-access result. |

#### Every unmet level and what it needs

Higher levels also require every lower level. These are all 14 unearned
levels; reaching 31/32 needs all except Freshness 4.

| Dimension / unmet level | Evidence or work still needed |
|---|---|
| Accuracy 4 | Record a passing one-command regeneration/check for the exact candidate and a dated live check showing the published files match that regenerated output exactly, with the evaluated commit and public URL. |
| Impartiality 3 | Publish every party offer in the same fields, order and length limits, with policy judgements only as linked, attributed quotes from the named independent bodies; record the template/content checks. |
| Impartiality 4 | After level 3, publish two independent opposing-leaning reviews and the site's responses alongside the corrections log. Complete the consent, coverage and publication record in [reviewers.md](reviewers.md). |
| Comprehension 4 | Complete [user-test.md](user-test.md) on one recorded build: at least five eligible people, each scoring at least 7/8 in under 300 seconds, with actual answers, times and round decision. |
| Context 4 | Show the data date and next scheduled update in each section, and record a source/revision check demonstrating that revised data is updated or explicitly flagged. A last-built footer alone is insufficient. |
| Coverage 3 | Add and verify the split by tax alongside the existing income, borrowing and debt figures. |
| Coverage 4 | After level 3, publish every party with Commons MPs in the same template, with independent assessments of their costed plans; record the dated completeness check and assessment links. |
| Freshness 2 | Provide and document one command that refreshes a new release, with an observed successful refresh result; the current four-step instructions do not qualify. |
| Freshness 3 | After level 2, record an actual scheduled watcher run covering each source and opening an update for review when a new release appears, with date and outcome. Scheduler configuration alone is insufficient. |
| Freshness 4 | Retain publication and go-live dates for every release over a full year, proving all went live within four weeks. Keep this level unclaimed until that year exists. |
| Access 3 | Record a completed zero-error WCAG 2.2 AA audit, including contrast, for every candidate HTML page and required audit state/width. Tie the passing gate result to the evaluated candidate; implemented audit code is insufficient. |
| Access 4 | After level 3, complete and record the keyboard and screen-reader coverage, findings and successful retests in [a11y-manual.md](a11y-manual.md), identifying build, date and environments. |
| Openness 3 | Publish funding details and a usable public error-reporting route alongside the named operator. |
| Openness 4 | After level 3, record a dated observation that code and pipeline are publicly accessible and an unauthenticated clean rebuild succeeds from the published repository, including source availability and matching output. |

The score sums to **3 + 2 + 3 + 3 + 2 + 1 + 2 + 2 = 18/32**.
Missing observed gate/live/watcher results, unperformed human checks, absent
party/tax coverage, missing update metadata and incomplete openness evidence
prevent the target score. Record later results in a new row; do not replace this
assessment or turn pending checks into completed observations.
