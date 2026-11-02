# Goal scorecard

This file scores the live site against the project goal. Each goal audit adds a
new dated section at the top, so later audits can see what changed. Older
sections stay as they were.

From Audit 2 onwards, audits use [goal-rubric.md](goal-rubric.md): eleven
dimensions scored 0 to 5 against named benchmarks and reader evidence. Audit 1
used a checklist that only asked whether each feature existed, and it was too
generous.

## Audit 6: 2 November 2026 (strict re-score after PRs #102 to #108)

- Commit audited: `fe0f5c2` on `main` (after #102 a chart within two phone
  screens, #103 benchmark side-by-sides for D3, D4, D6, D8 and D10, #104
  shorter phone pages, #105 holiday affordability and holiday and class-size
  benchmarks, #106 a CSV download beside every chart and table, #107
  comparisons between years before 2008 and fixed "since 2008" wording, #108
  taxes by type since 1948-49 and per-household amounts).
- Rubric: [goal-rubric.md](goal-rubric.md). Strict reading, as in Audits 4 and
  5: a dimension reaches 4 only with a recorded side-by-side comparison with a
  named benchmark page ([benchmark-comparison.md](benchmark-comparison.md)) or
  an independent review, and a page that is in fact comparable. The
  side-by-side record now covers D1 to D6, D8 and D10. It does not cover D7
  (beyond headline figures) or D9.
- How it was checked: a fresh build (1,755 pages, 6,558 CSV files); the home
  page, all money pages including the new taxes-since-1948 page, the life hub,
  every topic page, a recent and an early year page, the default 2009 vs 2023
  comparison and an early (1981 vs 2001) comparison measured at 360 × 640 with
  and without JavaScript (page length, sideways scrolling, where the first
  chart starts, small tap targets); per-person and per-household figures
  recomputed by hand; a scan of every reading page for causal or loaded words
  (every hit was inside a quoted, attributed official explanation or the
  site's own "not what it caused" notes); CI on `main` (build and checks)
  green for `fe0f5c2`. The live-site check for `fe0f5c2` was still running
  when this was written (this container cannot reach the live site), and it
  passed for #107.
- Who scored it: a Claude session that did not build the site.

**Total: 36 out of 55** on the strict reading (39 lenient). Audit 5: 31
strict, 37 lenient. Target: at least 49, every dimension at least 4, and the
phone test passed. Not met.

All seven gaps from Audit 5 were closed. The new benchmark records let five
dimensions reach 4 on the strict reading. What holds the rest back is now
smaller craft work (finding-led chart titles, chart summaries in words,
shorter pages), two dimensions with no recorded check (D7, D9), and evidence
only people can give (D11, the screen-reader test and outside review).

| Dimension | Strict | Lenient | Why |
|---|---|---|---|
| D1 Public money answers | 4 | 4 | The two benchmark gaps that counted most are closed: taxes by type since 1948-49 with each replacement of a tax marked (#108), and spending and tax per household beside per person (#108; checked: £1,360bn ÷ 29.0 million households ≈ £46,900). Who pays covers income, age, retired or working and household type. Not 5: no international comparison (OBR, IFS and OWID all give one); no reader evidence. |
| D2 Life: breadth and depth | 4 | 4 | Up from 3. Holidays now show the closest official measure to "who took a holiday" (could not afford a week away, EU-SILC 2005 to 2018) and say why no yearly share exists (#105); holidays and class sizes now have recorded side-by-sides, which found matching figures and fixed two problems (2024 travel method, class sizes a year behind). With work from 1971, pay spread, tenure from 1981 and affordability, this is comparable with the ONS and DfE pages. Not 5: DfE's large-class figures and infant / key stage 2 averages, ONS spending and nights abroad, and local-area detail are missing; housing costs and space are England only. |
| D3 Life: choosing and comparing | 4 | 4 | Up from 3. Any two years from 1971 can now be compared (#107, 1,487 comparison pages), changes only within one method, with the nearest comparable pair linked; the side-by-side with ONS census comparisons and OWID (#103) found this comparable or ahead, and added "Timing matters" notes for recession and pandemic years. Not 5: no wider-area or long-run context beside each headline change (ONS has it); the default comparison is 10 phone screens; no reader evidence of one-handed use. |
| D4 Explanation and understanding | 3 | 4 | Better: the Full Fact side-by-side (#103) found answers come before detail, and "tax burden" is now named and explained. Held at 3 (torn): chart titles describe rather than state the finding (for example "Public receipts by type, 1948-49 to 2022-23"), which the ONS benchmark does better; who pays, household tax and spending are still 10.5 to 10.6 phone screens; no international context for big numbers; no evidence a newcomer can explain a point back. |
| D5 Visual design and charts | 4 | 4 | Up from 3. Both things the OWID side-by-side found clearly ahead are fixed: a chart now starts within about two phone screens on every key page (CI enforces it, #102; measured 0.9 to 2.1 screens), and every chart and table has its own CSV (#106). Small multiples share scales and mark breaks. Not 5: titles do not state the finding; some chart summaries in words only list the break lines (taxes since 1948); no reader evidence. |
| D6 Phone experience | 3 | 4 | Shorter pages (#104): topic pages 7.6 to 10 screens, the default comparison 10, down from 12 to 15; no page scrolls sideways; the OBR and ONS side-by-side (#103) found this site shorter in words. Held at 3 (torn): Audit 5's target of about 8 screens is not met (spending 10.6, who pays 10.6, household tax 10.5, life hub 10.4); Sources is 118 screens and the glossary 18; nothing measures "answer in under a minute". |
| D7 Accuracy and traceability | 3 | 4 | Every figure re-read from its cell on every build; one-tap tracing; corrections log; headline figures match OBR, IFS, ONS and DfE (#100, #105). Strict 3: those checks cover headline figures only, and no recorded check takes a random sample of figures from the pages back to the original publications. |
| D8 Impartiality | 4 | 4 | Up from 3. The Full Fact side-by-side (#103) found framing comparable, with a stated rule for default years and no record claims; this audit's scan found no loaded or causal wording outside quoted, attributed official explanations. Not 5: no review by a person outside the project. |
| D9 Accessibility and no JavaScript | 3 | 3 | axe WCAG 2.2 AA passes in CI; every page measured works without JavaScript at 360px with the same content. Held at 3: no VoiceOver or TalkBack test, no recorded side-by-side, and some chart summaries in words describe only the breaks, not the trend. |
| D10 Honesty about limits | 4 | 4 | Up from 3. The ONS ASHE and Travel trends side-by-sides (#103, #105) found limits comparable and fixed two (2022 vs 2023 pay, 2024 mixed travel methods); early comparisons never cross a survey change (#107). Not 5: confidence intervals are shown for pay but not for most other headline survey figures; no outside review. |
| D11 Reader evidence | 0 | 0 | Nobody has used the site in a test. |
| **Total** | **36 / 55** | **39 / 55** | |

### Gaps that a worker can do (largest score effect first)

1. Rewrite every chart title on the money, topic and year pages to state what the chart shows (for example "Income Tax has raised about a quarter of receipts since 1948"), in neutral words, and make each chart's "in words" summary describe the trend as well as the breaks (D4, D5, D9).
2. Shorten spending, who pays, household tax and the life hub from about 10.5 to about 8 phone screens folded, and split or index the 118-screen Sources page, keeping every section reachable (D6, D4).
3. Record a random-sample accuracy check: trace at least 40 figures from the pages back to the original published tables (not the repository's own copy), record each result, and fix any mismatch (D7).
4. Record an accessibility side-by-side against GOV.UK and ONS pages: keyboard-only walk-through, the browser accessibility tree for each chart type, and tap target sizes, and fix what it finds (D9).
5. Add an international comparison of tax and spending as a share of GDP from an official source (OECD or Eurostat), with definitions and the year shown, or record why no comparable official source can be used (D1, D4).
6. Add DfE large-class figures and infant / key stage 2 averages to class sizes, and ONS spending and nights abroad to holidays (D2).
7. Show a longer-run or UK-wide reference beside each headline change on comparison pages (for example the change over the previous ten years), as the ONS comparisons do (D3).

### Human-only steps (unchanged)

1. A quick informal test with two or three people on phones (D11 to 2).
2. The five-person phone test with the pack in `docs/user-test/` (D11 to 5; required for the goal).
3. A VoiceOver (iPhone) and TalkBack (Android) test (D9 to 5).
4. A review of accuracy and impartiality by a person outside the project (D7, D8, D10 to 5).

---

## Audit 5: 2 November 2026 (strict re-score after PRs #92 to #100)

- Commit audited: `4b60492` on `main` (after #92 live-site check, #93 one page
  per life topic, #94 charts in view and home visuals, #95 household tax since
  1977, #96 life figures back to 1971, #97 pay spread, house prices and jobs by
  industry, #98 cash / after inflation / share of GDP switch and spending since
  1900, #99 comparing sets of years, #100 benchmark side-by-sides).
- Rubric: [goal-rubric.md](goal-rubric.md). Strict reading, as in Audit 4: an
  AI review is not independent, so a dimension reaches 4 only with a recorded
  side-by-side comparison with a named benchmark page
  ([benchmark-comparison.md](benchmark-comparison.md)) and a page that is in
  fact comparable. The side-by-side record covers D1, D2 and D5 only.
- How it was checked: a fresh build (415 pages); the home page, all four money
  pages, spending since 1900, the life hub, every topic page, a year page, the
  default 2009 vs 2023 comparison and a span comparison read at 360px with and
  without JavaScript; page lengths and sideways scrolling measured; a scan of
  every reading page for causal or loaded words; CI on `main` (build, checks,
  axe) confirmed green. The live-site check passed for #98; for #100 it was
  still running when this was written (this container cannot reach the live
  site directly).
- Who scored it: a Claude session that did not build the site.

**Total: 31 out of 55** on the strict reading (37 lenient). Audit 4: 30 strict,
33 lenient. Target: at least 49, every dimension at least 4, and the phone test
passed. Not met.

The work since Audit 4 closed all ten of its gaps. Most of it widened and
deepened what was already at level 3; only D1 has both the depth and the
recorded benchmark evidence to reach 4 on the strict reading. Most of the
remaining distance is now evidence that only people can give (D11, and outside
review for D7 to D10), plus side-by-side records for the dimensions that have
none (D3, D4, D6, D8 to D10).

| Dimension | Strict | Lenient | Why |
|---|---|---|---|
| D1 Public money answers | 4 | 4 | Up from 3. Since Audit 4: household tax as a share of income from 1977 (#95), one switch between cash, after inflation and share of GDP that works without JavaScript (#98), spending by purpose since 1900 on its own page (#98), and the recorded side-by-side (#100) found every headline figure matches the OBR, IFS and ONS for the same measure and vintage, with the one unexplained difference (gross against net debt interest) now explained. The two biggest gaps that record lists (long history, one switch) were closed by #98. Not 5: tax by type starts in 1999-00 (IFS from 1948-49); scale is per person only (the OBR also gives per household); no international comparison; no reader evidence. |
| D2 Life: breadth and depth | 3 | 4 | Much deeper: work from 1971 and jobs by industry from 1978, tenure from 1981, pay spread, house prices against earnings. The side-by-side covers earnings and affordability only. Held at 3 (torn, so the lower level): holidays still have no share of people who took a holiday; class sizes, holidays and work have no benchmark comparison; housing costs and space are England only; ONS offers local-area detail the site lacks. |
| D3 Life: choosing and comparing | 3 | 4 | Ranges can now be compared (91 span pages, #99) and the default pair (2009 vs 2023) fills all five topics, leading with "In brief" bars. Strict 3: no side-by-side or independent review of comparisons recorded. Smaller problems: the home page still says "Pick any year from 2008 to 2025" and the life hub asks "since 2008?" although year pages now reach back to 1971; years before 2008 cannot be compared with each other. |
| D4 Explanation and understanding | 3 | 3 | Question headings, answer boxes, glossary, quoted explanations, and home-page visuals. Held at 3: who pays is still 12.4 screens at 360px; topic pages run 7 to 15 screens; no evidence a newcomer can explain a point back; no benchmark record for explanation (Full Fact, ONS explainers). |
| D5 Visual design and charts | 3 | 4 | Home cards have sparklines and bars (#94), small multiples share scales, the switch works without JavaScript. The OWID side-by-side lists charts-first pages and per-chart downloads as clearly ahead. Held at 3 (torn): on spending, taxes, who pays, the life hub, holidays, housing and year pages the first two phone screens hold no chart; the only download is one 6.6MB `facts.json` linked from Sources. |
| D6 Phone experience | 3 | 3 | The menu now fits at 360px in two rows (#94); no page scrolls sideways; the life explorer is split into topic pages (#93), the largest reading page is about 240KB. Held at 3: housing is 15 screens, who pays and the default comparison 12.4, Sources 97; no benchmark or reader timing for "answer in under a minute". |
| D7 Accuracy and traceability | 3 | 4 | Every figure re-read from its cell on every build; one-tap tracing; corrections log; headline figures match OBR, IFS and ONS publications (#100). Strict 3: those checks were made by an AI session; no non-AI check. |
| D8 Impartiality | 3 | 4 | Default comparison years are now picked by a fixed, stated rule (#99), and a scan of every reading page found no loaded or causal wording in the site's own words. Strict 3: no outside review; no side-by-side with a neutral benchmark such as Full Fact. |
| D9 Accessibility and no JavaScript | 3 | 3 | axe WCAG 2.2 AA passes in CI on `main`; the new switch and span pages work without JavaScript. Held at 3: no VoiceOver or TalkBack test. |
| D10 Honesty about limits | 3 | 4 | Breaks are explained where they occur, including the new pre-2008 series (the Labour Force Survey's early years, the change from the older housing surveys to the English Housing Survey); span averages are made only when every year is measured the same way. Strict 3: no independent check. |
| D11 Reader evidence | 0 | 0 | Nobody has used the site in a test. |
| **Total** | **31 / 55** | **37 / 55** | |

### Gaps that a worker can do (largest score effect first)

1. Record side-by-side comparisons for the dimensions that have none: comparing periods against the ONS and OWID explorers (D3), explanation against Full Fact and ONS explainers (D4), phone reading against the OBR guide and ONS bulletins at 360px (D6), and framing and limits against Full Fact and the ONS (D8, D10), and fix what they find.
2. Put a chart within the first two phone screens of the spending, taxes, who pays, life hub, housing, holidays and year pages, so each page shows its answer visually before the reader scrolls (D5).
3. Shorten the longest reading pages at 360px (housing 15 screens, who pays 12.4, the default comparison 12.4) to about 8 screens folded, keeping every section reachable (D6, D4).
4. Add a "download this data" CSV link beside every chart and table, built from the same checked facts (D5).
5. Add the official share of people who took a holiday, or record which official source comes closest and why none is yearly, and add class-size and holiday benchmark comparisons (D2).
6. Make the year wording match the data: the home page, life hub and topic headings still say "since 2008" or "2008 to 2025" where year pages reach back to 1971, and let readers compare two earlier years where figures exist (D3).
7. Extend the tax mix by type back to 1948-49 from the OBR historical database, and add per-household scale beside per-person scale on the money pages (D1).

### Human-only steps (unchanged)

1. A quick informal test with two or three people on phones (D11 to 2).
2. The five-person phone test with the pack in `docs/user-test/` (D11 to 5; required for the goal).
3. A VoiceOver (iPhone) and TalkBack (Android) test (D9 above 3).
4. A review of accuracy and impartiality by a person outside the project (D7, D8, D10 to 4 on the strict reading).

---

## Audit 4: 2 November 2026 (strict re-score after PRs #87 to #90)

- Commit audited: `192539d` on `main` (after #87 shorter phone pages, #88 Income
  Tax by age, #89 tenure and class sizes for the other nations, #90 small-multiple
  charts).
- Rubric: [goal-rubric.md](goal-rubric.md).
- How it was checked: a fresh build (259 pages); every main page, the life
  explorer, a year page and the 2010 vs 2025 comparison read at 360px with and
  without JavaScript, both folded (as a reader first sees them) and with every
  section open; page sizes and screen counts measured; the live site fetched and
  compared with `main`; CI on `main` (build, checks, axe) confirmed green.
- Who scored it: a Claude session that did not build the site. It is the same kind
  of agent as the builders and as the Audit 3 reviewer.

**How strict this is.** John asked for a stricter score. The rubric lets a
dimension reach 4 only with a recorded independent review or a recorded
side-by-side comparison with a named benchmark page. The only review so far was
done by another Claude session, so this audit does not count it as independent:
every dimension it lifted to 4 is scored 3 here. No side-by-side benchmark
comparison has been recorded yet. Where the strict and lenient readings differ,
both are shown.

**Total: 30 out of 55** on the strict reading (33 on the lenient reading that
Audit 3 used; Audit 3 gave 34, or 30 strict). Target: at least 49, every
dimension at least 4, and the phone test passed. Not met.

PRs #87 to #90 improved breadth (other nations), charts (no hidden groups) and
page length, but none of them moved a dimension up a whole level, and the live
site does not yet show them (see "Live site" below).

| Dimension | Strict | Lenient | Why |
|---|---|---|---|
| D1 Public money answers | 3 | 3 | Correct, sourced answers with per-person scale, the tax mix since 1999-00, quoted official explanations and who pays by income, retired or not, household type and now age. Lenient score drops from 4: measured against the OBR's brief guide and IFS TaxLab, "how much household income goes on tax" is a single year (2023/24) with no history, although ONS publishes the series back to 1977; spending by purpose starts only in 2003-04; there is no single switch between cash, real terms and share of GDP; and on a phone the over-time charts are folded away under "More", so the reader sees a sentence, not the trend. |
| D2 Life: breadth and depth | 3 | 3 | Better: tenure for all four nations, Scotland's and Wales's class sizes, regions and nations for work and pay. Still well short of 5: every topic starts in 2008 although longer reliable series are already in the repository (the employment rate in `data/fetched/ons/lf24.csv` goes back to 1971; `FT1101_Trends_in_tenure.ods` is a long trends table); pay has no spread (low and high earners), housing has no house prices or affordability, work has occupation but not industry, and there is no official yearly share of people who took a holiday (the page says so). |
| D3 Life: choosing and comparing | 3 | 3 | Comparison pages now lead with "In brief" bars and explain each "not comparable" in place. Held at 3: ranges cannot be compared; the default pair (2010 vs 2025) leaves housing and holidays uncompared because 2025 has no comparable figure, so a newcomer's first comparison shows two of five topics as "not compared"; the year chooser is a grid of 18 links with no preview of what each year holds. |
| D4 Explanation and understanding | 3 | 3 | Question headings, answer boxes, glossary links and quoted explanations work well. Held at 3: who pays is still about 12 screens of mostly prose when folded; the home page and life explorer give answers only as text; no evidence a newcomer can explain the point back. |
| D5 Visual design and charts | 3 | 3 | Small multiples (#90) fixed hidden groups, with a shared scale, faint context lines and a summary. Held at 3: on a phone almost every chart is folded under "More on ...", so the first view of the life explorer, the year pages, the home page and most money sections is text only; the home page has no visual at all; small-multiple panels are about 150px wide with tiny axis text; the best explainers lead with the chart. |
| D6 Phone experience | 3 | 3 | Folding (#87) cut pages to 6 to 12 screens at 360px (who pays 11.6, taxes 8.5, life explorer 7.7). Held at 3: the menu still runs off the right edge (the "Tax and income" item is cut off and later items are hidden); `life/index.html` is 443KB, the heaviest page, near the 475KB build limit and slow on a weak connection; opened fully the life explorer is about 100 screens. |
| D7 Accuracy and traceability | 3 | 4 | Every figure re-read from its cell on every build; one-tap tracing; corrections log; an AI review found no errors. Strict 3: no independent (non-AI) check against the original publications. |
| D8 Impartiality | 3 | 4 | Neutral wording, fixed windows, a page explaining choices, and no loaded words found in this audit. Strict 3: no review by a person outside the project; content added since the review (#88 to #90) has had no impartiality check beyond this audit. |
| D9 Accessibility and no JavaScript | 3 | 3 | axe WCAG 2.2 AA runs in CI and passes on `main`; core answers and comparisons work without JavaScript (checked at 360px with JavaScript off). Held at 3: no VoiceOver or TalkBack test. |
| D10 Honesty about limits | 3 | 4 | Breaks, gaps, margins of error and "not compared" reasons are a strength, and the small multiples split job types at the 2021 change. Strict 3: same reason as D7 and D8. |
| D11 Reader evidence | 0 | 0 | Nobody has used the site in a test. |
| **Total** | **30 / 55** | **33 / 55** | |

### Live site

The live site is behind `main`. On 2 November 2026 (checked at 15:47 and again
at 15:53 UTC) the live `who-pays.html` had five sections; `main` has six (Income
Tax by age, #88, is missing), although a preview deployment of this audit's own
branch built successfully at 15:52. The repository has no `vercel.json`, so every
pushed branch makes a Vercel preview deployment, and the account's
100-deployments-a-day limit was hit today. The goal is judged on the live site,
and the phone test must use the same live commit as the reviews, so this has to
be fixed before any test.

### Gaps that a worker can do (largest score effect first)

1. Make the live site match `main`: find out why production is not updating while previews deploy (production branch setting, failed production builds or the daily cap), add a `vercel.json` that stops preview deployments for other branches so they cannot use up the cap, and add a check that the live pages match the latest build. Needed before any reader test or review.
2. Split the life explorer (`life/index.html`, 443KB) into one page per topic (work, earnings, housing, holidays, class sizes) under a short hub, each well under 150KB, with links, contents and comparisons updated (D6, D5).
3. Show the key chart in view, not folded: on every money page, topic page and year page keep each section's main chart under its answer and fold only tables, limits and sources; give each home-page card a small visual (D5, D1, D4).
4. Show how much household income goes on tax over time: direct, indirect and all taxes as a share of gross income by income fifth from ONS's historical tables since 1977, with breaks marked (D1).
5. Extend the life explorer back before 2008 where reliable series exist (employment rate from 1971 is already fetched; tenure trends; pay from 1997; class sizes), with breaks shown and the year chooser widened (D2, D3).
6. Add the missing core measures: pay spread (10th and 90th percentile, ASHE), house prices against earnings (ONS affordability ratio), and jobs by industry (D2).
7. Add one cash / real terms / share of GDP switch to the money charts that works without JavaScript, and a longer history of spending by purpose where an official series exists (D1).
8. Improve comparisons: let readers compare ranges (for example 2010-12 against 2022-24), and make the default and suggested pairs ones where every topic has comparable figures (D3).
9. Fix the menu at 360px so every section is visible without sideways scrolling (two rows or a "Menu" disclosure) (D6).
10. Record side-by-side comparisons of named benchmark pages (OBR brief guide, IFS TaxLab, Our World in Data, ONS) against the matching pages here, so level 4 can be judged on evidence (D1, D2, D5).

### Human-only steps

1. A quick informal test with two or three people on phones (lifts D11 to 2 and finds problems cheaply).
2. The five-person phone test with the pack in `docs/user-test/` (D11 to 5; required for the goal).
3. A VoiceOver (iPhone) and TalkBack (Android) test (D9 above 3).
4. A review of accuracy and impartiality by a person outside the project (D7, D8, D10 to 4 on the strict reading).

---

## Audit 3: 2 November 2026 (after the independent review)

- Commit audited: `b3dd569` on `main` (after PRs #74 to #85), plus the small
  fixes made by the review in the same PR as this section.
- Rubric: [goal-rubric.md](goal-rubric.md).
- How it was checked: the [independent review](independent-review.md) of
  accuracy, impartiality, accessibility and reproducibility, phone screenshots at
  360px, and a reading of every main page against the benchmarks.
- Who scored it: the same reviewer, a Claude session that did not build the site.
  Level 4 is given only where that review checked the dimension and found no open
  material problem. Because the reviewer is the same kind of agent as the
  builders, a stricter reader can treat those 4s as 3s; the total would then be
  30, not 34.

**Total: 34 out of 55** (Audit 2: 29). Target: at least 49, every dimension at
least 4, and the phone test passed. Not met. Nothing can score 5 until real
readers have tested the site.

| Dimension | Score | Change | Why |
|---|---|---|---|
| D1 Public money answers | 4 | +1 | All four answers now give per-person scale, the tax mix since 1999-00, quoted official explanations of the big moves, cash, real-terms and share-of-GDP tables, and who pays by income, retired or not, and household type. Headline figures were checked against the source tables. Missing for 5: Income Tax by age, a single switch between cash, real terms and % of GDP, and reader evidence. |
| D2 Life: breadth and depth | 3 | +1 | Housing now has costs, rooms and overcrowding; holidays have frequency, destinations and trips in Great Britain; work and pay have nations, regions, ages and sex. Still behind: housing and most school figures are England only, there are few income or age splits outside work, and holiday frequency is an average per resident, not the share of people who went away. |
| D3 Life: choosing and comparing | 3 | +1 | Comparisons lead with fixed key measures, rank the largest changes, show bars, explain each "not comparable" in place, and say when a change is within the margin of error. Held at 3: the first phone screen of a comparison is the chooser and contents list, not the answer; pages run to about 18 screens; and ranges (several years together) cannot be compared. |
| D4 Explanation and understanding | 3 | +1 | Glossary links on first use, question headings, per-person scale, and quoted explanations. Held at 3: pages are long and dense for a newcomer (who pays is about 19 screens), and there is no evidence yet that a newcomer can explain the main point back. |
| D5 Visual design and charts | 3 | +1 | Charts are labelled at the line ends, annotated with breaks and events, summarised in words and readable by tap. The review found a chart that hid the two largest age groups under a general title and a label cut off on phones (both fixed). Held at 3: nearly every chart is a line chart with up to three series, and labels can sit on top of lines. |
| D6 Phone experience | 3 | 0 | No sideways scrolling, a one-row menu, in-page contents, 44px menu targets. Held at 3: pages are 10 to 29 screens long at 360px, and the menu scrolls sideways, so some sections are hidden off the right edge. |
| D7 Accuracy and traceability | 4 | +1 | Independent review: all source hashes match, 40 random cells were the right row and column, all 2,009 derived figures recomputed with no mismatch, and headline claims match the source tables. Any figure traces in one tap, and corrections are logged. Not 5: no reader evidence, and the originals were not re-downloaded. |
| D8 Impartiality | 4 | +1 | Independent review of headlines, windows, quotes, chart scales and wording. It found three small framing problems (fixed) and none open. The sources page now explains how years, headline measures and scales are chosen. Not 5: no reader evidence or review by a person outside the project. |
| D9 Accessibility and no JavaScript | 3 | 0 | Zero WCAG 2.2 AA failures on 18 pages at 360px and 1100px with every section open (after fixing one), keyboard path and no-JavaScript answers work, and the check now runs in CI. Held at 3: no manual VoiceOver or TalkBack test. |
| D10 Honesty about limits | 4 | +1 | Margins of error on survey figures, breaks shown on charts and in comparisons, limits in plain sentences next to each section, projections labelled as projections. The review found one causal sentence in the site's own words (fixed). Not 5: no reader evidence. |
| D11 Reader evidence | 0 | 0 | The test pack is ready, but nobody has used the site in a test. |
| **Total** | **34 / 55** | **+5** | |

### Gaps (most valuable first)

1. Run the five-person phone test with the pack in `docs/user-test/` (a human step: John).
2. Before that, record a quick informal test with two or three people on phones, to find problems while they are cheap to fix (a human step).
3. Make every long page answer first on a phone: put the comparison summary above the year chooser, and fold secondary sections on who pays, the life index and comparison pages so each page is a few screens before the details.
4. Widen life evidence beyond England where publishers allow (tenure and class sizes for Scotland, Wales and Northern Ireland, or a clear note where they do not), and add the share of people who took a holiday.
5. Add Income Tax by age and sex from HMRC to "who pays".
6. Replace crowded multi-line charts with small multiples where more than three groups matter (age groups, nations, regions), so no chart hides groups.
7. Get a manual screen-reader test (VoiceOver and TalkBack) and a review of accuracy and impartiality by a person outside the project (human steps).

---

## Audit 2: 2 November 2026 (stricter rubric)

- Commit audited: `3831fc0` on `main` (after PR #71).
- Rubric: [goal-rubric.md](goal-rubric.md), first use.
- How it was checked: the evidence from Audit 1, plus phone screenshots at
  390px of the home, spending, life and comparison pages, and a comparison of
  what the site offers with the benchmarks named in the rubric.

**Total: 29 out of 55.** Target: at least 49, every dimension at least 4, and
the phone test passed. No dimension can score above 3 yet, because no
independent review or reader test exists.

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 3 | Correct, clear answers with history and limits. Missing: per-person and per-household scale, how the tax mix changed over time, attributed explanations of big moves (2008-09, 2020-21), and any "who pays" split other than income. |
| D2 Life: breadth and depth | 2 | Five topics, but about five measures each. Housing is tenure only (no costs or space), holidays are abroad only with three regions and no frequency, housing and schools are England only, and there are no age, region or income splits. |
| D3 Life: choosing and comparing | 2 | Every year and pair works without JavaScript and breaks are respected, but comparisons are long tables of numbers on a phone, with no "what changed most" summary, no visual comparison and no ranges. Comparing 2010 with 2025 shows nine rows of "not available" for job types. |
| D4 Explanation and understanding | 2 | Good warnings about the three easy mistakes, but little teaching: no glossary, few explanations of terms, little context for big numbers, and pages start with figures rather than a question a newcomer would ask. |
| D5 Visual design and charts | 2 | Clean and neutral, but basic: simple bars and small line charts, few annotations, and tables dominate. Far behind the benchmarks for showing the answer at a glance. |
| D6 Phone experience | 3 | No sideways scrolling and readable text, but pages are very long, the navigation takes two rows, there is no in-page navigation, and comparison tables are tall and cramped at 390px. |
| D7 Accuracy and traceability | 3 | Every figure is re-read from its source cell on every build. Capped at 3: no independent check against the original publications, and a figure is traced through the section's source line rather than from the figure itself. |
| D8 Impartiality | 3 | Neutral wording and fixed comparison years. Capped at 3: no independent review of framing, headline choices or chart scales. |
| D9 Accessibility and no JavaScript | 3 | Zero axe WCAG 2.2 AA violations at 360px with sections expanded, and no-JavaScript fallbacks. Capped at 3: no manual screen-reader or keyboard test. |
| D10 Honesty about limits | 3 | Gaps, breaks and the illustration label are handled well. Capped at 3: no survey uncertainty shown, and no independent check. |
| D11 Reader evidence | 0 | No testing with real people of any kind. |
| **Total** | **29 / 55** | |

### What is stopping a far better product

1. **We were measuring the wrong thing.** The old checklist rewarded features
   existing, so every audit would have said "nearly done". The new rubric scores
   quality against benchmarks and needs outside evidence for high scores.
2. **Nobody has designed the experience.** The site was built data first: a
   checked number pipeline, then pages to show the numbers. No one has designed
   the reading journey, the charts or the phone layout as a product, or studied
   how the best explainers do it.
3. **The rules have been read as "show less".** Principles like no persuasion,
   no causation and no invented households are being met by saying very little.
   Official bodies (OBR, ONS, HM Treasury) publish their own explanations of big
   changes, and quoting them, clearly attributed, would add context without
   breaking any rule. "Works without JavaScript" has also been read as "no
   interactivity", when interactive charts can be added on top of the no-JS
   tables.
4. **Thin data.** Each life topic has a handful of measures, mostly for one
   nation and with few group splits. Adding data is slow because this
   environment cannot download from ONS or GOV.UK directly; every new source
   has to go through the GitHub fetch workflow.
5. **No outside eyes.** The same kind of agent built, checked and scored the
   site. There has been no independent review and no reader of any kind.
6. **The phone test needs real people.** Only John can arrange it, and there is
   no test pack yet to make it easy.

### Gaps (most valuable first)

1. Commission a design pass that studies the benchmarks and produces a new phone-first layout, chart style and page structure for the money pages and the life explorer, then apply it page by page.
2. Rebuild the two-year comparison so it leads with the biggest changes in plain words and charts, shortens the table, hides rows with no data for either year, and explains each "not comparable" in place.
3. Add teaching to every page: start from the newcomer's question, explain terms where they appear, add a glossary, and give relatable scale such as per person and per household.
4. Add attributed official explanations for the big moves (for example 2008-09, 2020-21, the 2022 energy support) next to the charts, quoted from OBR, ONS or HM Treasury.
5. Widen the life evidence: housing costs and space, holidays at home and abroad with frequency, age and region splits, and other UK nations or a clear "England only" reason.
6. Widen "who pays" with official splits by age, retired or working, and household type, and show how the tax mix has changed over time.
7. Upgrade the charts: direct labels, annotations for events and breaks, interactive versions on top of the no-JS tables, and a short text summary for each chart.
8. Shorten pages for phones: in-page navigation, a one-row menu, and collapsing secondary detail.
9. Write the phone test pack (12 questions with the three critical ones, answer key, marking sheet, consent note) and run a small informal test to find problems early.
10. Run independent accuracy, impartiality and accessibility reviews (including a manual screen-reader test) and log the findings, so dimensions can score above 3.

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
