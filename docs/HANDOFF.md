# Handoff: Unpolitical

This file is for the next agent taking over the project. It sets out the goal,
what success means, where the work stands, what is still open, the constraints
that have bitten before, and how the project was run. The project goal text is
copied verbatim from the project brief.

## Project goal

> Build Unpolitical from scratch: an independent, impartial website that helps someone who does not follow politics understand where UK public money goes, who pays for it, and how everyday life has changed over time.
>
> The experience should work especially well on a phone. It should make complicated information understandable without simplifying it into something misleading.
>
> What people should understand
>
> Public money
>
> Give clear, visual answers to four questions:
>
> Where does public money go? Show total spending, its main purposes and how they have changed.
>
> Which taxes raise the money? Explain the main revenue sources, distinguishing taxes, other receipts and borrowing.
>
> Who pays? Show what official evidence says about contributions across people and household groups.
>
> How much household income goes towards tax? Explain direct, indirect and combined taxes without confusing household averages, personal tax rates and shares of total tax revenue.
>
> Everyday life
>
> Provide a year-by-year explorer covering:
>
> Work: employment and the kinds of jobs people do.
>
> Earnings: how pay has changed after inflation.
>
> Housing: tenure, costs, home size or other directly measured housing conditions.
>
> Holidays: the kinds of holidays people take, where they go and how often.
>
> Schools: children’s class sizes, with the relevant nation and school phase clearly identified.
>
> People should be able to choose a year, compare two periods and understand both the change and its limits. Show important differences between groups where reliable evidence supports them.
>
> Product principles
>
> Answers first, methods close by. Start with understandable findings and useful comparisons, not a wall of links or caveats.
>
> Evidence, not persuasion. Use neutral language and visual treatment. Do not select dates or statistics to favour a party or political argument.
>
> No invented continuity. Show missing years, incompatible definitions and classification changes explicitly. Never substitute zero, interpolate silently or join unrelated categories.
>
> No fictional “typical family” presented as fact. Any household illustration must be clearly labelled and kept separate from measured statistics.
>
> Traceable claims. Every quantitative claim must lead to an official source, its period, population, geography, units and a reproducible calculation where applicable.
>
> Simple and accessible. Use plain English, restrained white-and-grey styling, readable charts and complete table alternatives. Core answers and year comparisons must work without JavaScript.
>
> Definition of success
>
> Success means people understand the subject more accurately, not merely that the website builds or looks finished.
>
> Five consenting UK adults who do not follow politics closely must test the same delivered version on phones. Together, they must answer at least 48 of 60 questions correctly. Each person must answer at least 9 of 12 correctly within eight minutes, including all three critical questions about tax interpretation, illustrative households and causation.
>
> The delivered website must also pass independent checks for factual accuracy, impartiality, accessibility and reproducibility, with no unresolved material findings.
>
> The finished product should leave a newcomer better informed—not told what to think.

Repository: https://github.com/jnyross/unpoliticalaf (public). Live site:
https://unpoliticalaf.vercel.app/

## Status at handoff (4 November 2026)

- **Goal: not met.** The latest audit (Audit 17 re-run, rubric v3) scored the
  site 43 out of 55, recorded as "met (simulated)" for the reader stand-ins. The
  goal needs more than that. See [goal-scorecard.md](goal-scorecard.md).
- **John's questions:** 56 of 82 answered correctly at the last count (John's
  questions sheet: [johns-questions/README.md](johns-questions/README.md)). The
  welfare group is now 22 of 22. Most failures in the last audit were about
  reach: readers could not get to immigration, defence or the manifesto page from
  the menu, and the action budget ran out before they reached many probes.
- **Phone user test (five real UK adults):** not run. It needs real people. The
  stand-in readers (simulated, rubric v3) are a substitute, not the test. The
  test is still required before the goal can be called met.
- **Blocked:** T108, April 2026 pay. The official ONS/nomis series used for pay
  ends in April 2025, so the April 2026 figure cannot be shown from a source
  already in the repo. It needs a new official file, which the fetch workflow
  can download.
- **Recently merged work:** the phone header stays in view while scrolling
  (T102, #206); the question pages are reachable from the menu (T139, #218) and
  question answers in a few taps (T142, #224); a labelled self-employed tax
  example (T138, #214); housing and work pages brought under the phone length
  limit (T131, #210); welfare-group figures at the top of their pages (T145, #227).
- **Still in flight when the handoff was written:** PRs #222 and #225, which
  their own threads were merging. Check `git log origin/main` and the open PR
  list before starting any work, in case they have already merged.

## Principles John has set

- **Fully autonomous.** John only suggests ideas, goals and features. He does
  not review or merge PRs. Workers merge their own PRs once every required check
  passes and their self-review finds no open problem.
- **No cap on concurrent work.** Run everything that is not blocked in parallel;
  do not queue. (This overrode an earlier limit of three workers.)
- **Merge conflicts are the worker's job.** Merge the latest `main`, re-run the
  checks, and merge once green, as soon as a conflict appears.
- **Never leave a thread waiting on John.** If a worker has a decision to make,
  tell it to go ahead with its own recommendation.
- **High bar.** John has said the site is "still very basic". Do not ship
  something that only looks finished.
- **Five UX principles are audit checks** (T128, #207/#208,
  `scripts/ux_heuristics.py`). Secondary text stays at 14 to 15px. At audit 17,
  the A3 check (prose at least 16px) still fails on most pages, at 14.4 to 15px.
  Going to 16px breaks the phone length limits. This was a coordinator decision
  (T128); do not re-ticket it.
- **John's questions are requirements.** When John sends a question the site
  must answer, add it to `docs/johns-questions/questions.json` (a small ticket,
  then a worker). Open probes count as gaps in the next audit.

## How the work is run

- **Goal audits (R2).** After each merged feature PR, and on a daily schedule,
  an audit scores the live site against every item in the goal (see
  [goal-rubric.md](goal-rubric.md), eleven dimensions scored 0 to 5). Its gaps
  become tickets. Audits stop once the goal is met, apart from the five-person
  phone test. **Both automatic audit triggers were switched off at handoff,
  because John asked for no further automatic work.** Re-enable them only if the
  new agent's instructions say so.
- **Stuck-work watchdog.** An hourly scheduled task nudged stalled threads. It
  was also switched off at handoff.
- **Auto-merge workflow.** `.github/workflows/auto-merge.yml` squash-merges any
  open, non-draft PR from a `claude/` branch once every check on its latest commit
  has passed. It runs when "Build and check" finishes and every five minutes. A
  draft PR, a `hold` label or a title starting with WIP keeps a PR open. This
  workflow was left on.
- **Stand-ins.** Rubric v3 uses Claude stand-in readers instead of people, and
  records a pass as "met (simulated)". See [standins/README.md](standins/README.md).
  The stand-in result is not the five-person test.
- **Older process docs.** [AGENTS.md](../AGENTS.md),
  [AUTONOMOUS-BRIEF.md](../AUTONOMOUS-BRIEF.md) and [START.md](../START.md)
  describe an earlier software-factory process (GitHub issues as the ledger,
  direct-main publication through a controller). They are out of date. The
  current process is in this file.

## Constraints that have bitten before

- **Vercel free plan: 100 deployments a day.** Only `main` deploys. Other
  branches make no deployment, so do not push to `main` more often than needed.
- **Page length limits.** Each page has a phone length limit, checked by CI. The
  work and housing pages are close to the limit (8.5 and 8.6 of 8.8 after #210).
  `spending-history.html` is about 259.9k of a 260k byte limit. Check the limit
  before adding text to a page.
- **Cloud container cannot reach ONS, GOV.UK, OBR or nomis.** New official
  sources go in `sources/manifest.json`. Pushing runs
  `.github/workflows/fetch-sources.yml`, which downloads them on GitHub and
  commits them to `data/fetched/` with `receipts.json`.
- **Hashes stop the build.** If a source file changes without its recorded
  SHA-256 being updated, the build stops. This is deliberate.
- **Breaks are shown, never bridged.** SOC2010 to SOC2020 (2021), holiday
  surveys (the method changed in 2024; GB residents and UK residents are not
  comparable), the HMRC 2016-17 dividend break, and housing data ending at
  2024-25 are all shown as breaks.
- **Holiday data.** VisitBritain GBTS 2019 and 2022 onward are not comparable.
  The 2025 figure is read from a PDF with pypdf, using locators recorded in the
  build.
- **Corrections.** Add an entry to `CORRECTIONS` in `builder/trace.py` whenever a
  published mistake is fixed. It appears on `corrections.html`.

## CI checks that will fail a PR

- Chart fits within two phone screens; page length limits.
- Chart findings and no loaded words in chart text.
- Accuracy check (runs on `main` only).
- Accessibility regressions (`make a11y`, axe at 360px and 1100px).
- Trend titles; non-zero axis captions; no titles across marked breaks.
- `scripts/ux_heuristics.py` (the five UX principles).

Run `make verify` (build, check, test) before pushing. Run `make setup-dev && make a11y`
when a page template changes.

## Where to start

1. Read [product-spec.md](product-spec.md) and [design.md](design.md).
2. Read [goal-rubric.md](goal-rubric.md) and the top of
   [goal-scorecard.md](goal-scorecard.md) for the latest audit.
3. Read [johns-questions/README.md](johns-questions/README.md) for the open probes.
4. Run `make setup && make verify` to confirm a clean starting point.
5. Check the open PRs and the T108 blocker before choosing work.

The repository's own rules for figures and wording are in [README.md](../README.md).
