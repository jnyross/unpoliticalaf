# Goal scorecard

This file scores the live site against every item in the project goal. Each
goal audit adds a new dated section at the top, so later audits can see what
changed. Older sections stay as they were.

Statuses: **Met**, **Partly met**, **Not met**, **Human step** (needs real
people and cannot be done by a code change).

---

## Audit 1: 2 November 2026

- Commit audited: `3b9d2e1` on `main` (PR #69).
- Live site: https://unpoliticalaf.vercel.app/ served the same home page text
  as the local build of that commit when fetched on 2 November 2026.
- How it was checked: `make verify` (build, re-read of 3,776 figures from their
  source cells, 513 recalculations, 13,895 page numbers on 180 pages, unit
  tests: all passed); axe-core with WCAG 2.0/2.1/2.2 A and AA rules on ten key
  pages at 360px with every `<details>` opened (0 violations, no sideways
  scrolling); reading every top-level page, the life index, a year page (2019)
  and a comparison page across a definition break (2019 vs 2024).

**Summary:** 17 met, 2 partly met, 1 not met, 1 human step (21 items).

### Public money

| # | Goal item | Status | Evidence |
|---|---|---|---|
| 1 | Where does public money go? Total, main purposes, change over time | Met | `spending.html`: £1,360bn total 2025-26, £ per £100 by COFOG area with a full table, every year 2003-04 to 2025-26 in cash, real terms and % of GDP, ten-year change by area, PESA breaks listed. |
| 2 | Which taxes raise the money? Taxes, other receipts and borrowing kept apart | Met | `taxes.html`: three numbered blocks (taxes £1,105bn, other receipts £127bn, borrowing £134bn), borrowing vs debt explained, receipts and spending as % of GDP since 1948-49 with forecasts marked. |
| 3 | Who pays? Official evidence across people and household groups | Met | `who-pays.html`: HMRC Income Tax shares by taxpayer percentile (1999-00 onwards, 2008-09 gap and 2016-17 dividend break shown) and ONS all taxes by household income fifth, kept separate with their limits. Only income-based groupings are shown (gap 5), and the household wording needs correcting (gap 6). |
| 4 | How much household income goes on tax? Direct, indirect, combined, without mixing averages, personal rates and revenue shares | Met | `household-tax.html`: direct/indirect/all taxes as % of gross income by fifth, a "three numbers that are easy to mix up" box, and the effect of the denominator (gross income, disposable income, spending). |

### Everyday life explorer

| # | Goal item | Status | Evidence |
|---|---|---|---|
| 5 | Work: employment and kinds of jobs | Met | Employment rate 16-64 (men, women), people in work, part-time share, 2008-2025; job types by SOC major group 2011-2025 with the SOC2010→SOC2020 break in 2021 shown on both bases. |
| 6 | Earnings after inflation | Met | ASHE median weekly pay in cash and April 2025 prices (CPIH), full-time men and women, part-time, 2008-2025; coding breaks, furlough years and provisional 2025 noted. |
| 7 | Housing: tenure, costs, home size or other directly measured conditions | Partly met | Tenure for England 2008-09 to 2024-25 and families with children renting privately. No housing costs and no home size or overcrowding, although `data/fetched/ehs/FT1421_Trends_in_overcrowding_by_tenure.ods` is already fetched and unused. |
| 8 | Holidays: kinds, where people go and how often | Partly met | Visits abroad by purpose and by Europe / North America / rest of world, 2009-2025, with the 2024 UK→GB method break and 2020 gap shown. Missing: how often people take holidays, holidays within the UK, and destinations finer than three regions. |
| 9 | Schools: class sizes, nation and phase clearly identified | Met | Average class size, state-funded primary and secondary, England, January census 2008-2025; "England only" and the school year shown with every figure. |
| 10 | Choose a year | Met | `life/2008.html` to `life/2025.html`, each with every topic and its own period. |
| 11 | Compare two periods | Met | 153 pair pages under `life/compare/`; a form plus a no-JavaScript list of every pair. |
| 12 | Understand both the change and its limits | Met | Comparison pages give percentage-point or percent change, write "not comparable: definition changed" across breaks, and carry a "Change is not cause" box. |
| 13 | Important differences between groups where evidence supports them | Met | Sex for employment and pay, full-time vs part-time, families with children for tenure, destination for holidays, phase for class sizes. |

### Product principles

| # | Goal item | Status | Evidence |
|---|---|---|---|
| 14 | Answers first, methods close by | Met | Every page opens with a plain-English answer; tables sit in `<details>` under each chart; limits and source follow each section. |
| 15 | Evidence, not persuasion | Met | Neutral wording; the ten-year comparison window is fixed and says so; no party or policy commentary found. |
| 16 | No invented continuity | Met | Missing years shown as "not available", charts break at gaps and definition changes (unit tests cover both), no change calculated across breaks. |
| 17 | No fictional "typical family" as fact | Met | The single worked example on `household-tax.html` is headed "Illustration, not a statistic" and kept apart from measured figures. |
| 18 | Traceable claims | Met | Every displayed number is a `data-fact` tied to `data/facts.json` (sheet and cell, or calculation and inputs); each section links to its source entry on `methods.html` with period, population, geography, file and SHA-256; `make build && make check` reproduces it. |
| 19 | Simple and accessible: plain English, white and grey, readable charts, complete tables, core answers and comparisons without JavaScript | Met | Only `life/index.html` has a script and it has a no-JS fallback; full table beside every chart; axe found 0 WCAG 2.2 A/AA violations at 360px with tables expanded. |

### Definition of success

| # | Goal item | Status | Evidence |
|---|---|---|---|
| 20 | Five consenting UK adults on phones: at least 48/60 overall, each at least 9/12 in 8 minutes, all three critical questions right | Human step | Not run. There is also no ready-to-use test pack in the repository (12 questions, the 3 critical ones, answer key, timing and marking sheet); see gap 3. |
| 21 | Independent checks for factual accuracy, impartiality, accessibility and reproducibility, with no unresolved material findings | Not met | Only the site's own automated checks have run. No independent review of the delivered version is recorded. |

### Gaps

1. Housing shows tenure only, so add directly measured housing costs and home size or overcrowding for England (the overcrowding table FT1421 is already fetched), by tenure where the source supports it.
2. Holidays cover only trips abroad by purpose and three broad regions, so add how often people go on holiday, holidays within the UK, and the main destination countries, keeping the 2024 method break.
3. There is no phone test pack for the five-person test, so write the 12 questions (including the three critical ones on tax interpretation, illustrative households and causation), answer key, timing and marking sheet and consent note against the live site.
4. No independent review of the delivered site exists, so run and record separate accuracy, impartiality, accessibility and reproducibility reviews of the live commit and fix any material findings.
5. "Who pays" groups households only by income, so add other official splits where reliable, such as retired and non-retired people from ONS Tables 3a and 4a of the same file.
6. `who-pays.html` and `household-tax.html` say the ONS fifths are "equal-sized groups" of households and give "average taxes paid per household", but ONS Tables 2a and 8 are fifths of individuals ranked by their household's income, so the wording should say that.

Human-only step still open: the five-person phone test itself.
