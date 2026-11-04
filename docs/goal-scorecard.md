# Goal scorecard

This file scores the live site against the project goal. Each goal audit adds a
new dated section at the top, so later audits can see what changed. Older
sections stay as they were.

From Audit 2 onwards, audits use [goal-rubric.md](goal-rubric.md): eleven
dimensions scored 0 to 5 against named benchmarks and reader evidence. Audit 1
used a checklist that only asked whether each feature existed, and it was too
generous. From Audit 9, audits use rubric v3, where Claude stand-ins replace
the people tests ([standins/README.md](standins/README.md)); a pass under v3 is
recorded as "met (simulated)".

## Audit 15: 4 November 2026 (rubric v3, after the audit 14 fixes #163 to #170)

- Commit audited: `4cb1bcc` on `main` (T94, #170). The "Live site matches main" check for it is green ([run 41767745611](https://github.com/jnyross/unpoliticalaf/actions/runs/41767745611)). The live site cannot be fetched from the audit container (proxy returns 403), so that check rests on CI.
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure [standins/README.md](standins/README.md). All evidence is in [standins/audits/audit-15/](standins/audits/audit-15/).
- Stand-ins, each a fresh session that did not build the site: a question writer (24 new questions, sealed before any phone reader started, `new-questions.sha256`); a site check of the sealed questions, where every question has one supported answer that matches the writer's key (Q4, Q12, Q15 and Q16 rest on a glossary definition or on derived wording); 3 informal readers (P5, P1, P8); 5 phone readers (P2, P6, P3, P10, P9, drawn at random); a screen-reader reader; an adversarial fact-checker (30 claims); a left and a right critic; a judge.
- Procedure notes. R4 and R5 first answered the 24 new questions from pages they had already seen, which the procedure does not allow, so those answers were voided. Each re-ran that phase in a fresh session ([R4-newfix.json](standins/audits/audit-15/readers/R4-newfix.json), [R5-newfix.json](standins/audits/audit-15/readers/R5-newfix.json)), and the scores use the re-runs. I2 could not start the first time because playwright was missing from its shell; it was re-run with the project's virtualenv. The first attempt is not counted.
- Automated checks: keyboard check finds no traps; all 1,327 charts have a text summary with figures; `make a11y` locally reports who-pays at 8.6 phone screens against an 8.5 limit, the local offset noted in audit 14, and CI passed on the same commit ([accessibility.txt](standins/audits/audit-15/accessibility.txt)).

**Total: 44 out of 55. Target not met (simulated).** Audit 14: 44. The simulated phone test did not pass: 57 of 60 overall, but R4 (11 of 12) and R5 (10 of 12) both missed critical question 12 (what the richest fifth's share of all tax paid measures). John's questions J1.1 and J1.4 each passed 3 of 5, below the bar of 4. Every new question passed, and the prior-knowledge, screen-reader and fact-check stand-ins pass with no material finding.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 57/60: R1 12, R2 12, R3 12, R4 11, R5 10; R4 and R5 missed critical Q12 | 48/60, each reader 9/12, all critical right | No |
| New questions (24, sealed) | 117/120 with the site (98%), 50 without | 80% | Yes |
| Prior-knowledge check | 5/60 without the site, 57 with it (+52) | +20 | Yes |
| John's questions | J1.1 3/5 and J1.4 3/5; J1.2, J1.3, J1.5, J1.6 and J1.7 5/5 (J1.2 4/5); 0 without the site | every probe answered, 4 of 5 right | No |
| Informal check | P5, P1 and P8 all found answers to the three questions; one blocking note, that the pay chart starts in 2002 and so cannot answer "how has it changed since I was young" | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 17 actions, critical right; the single-year picker for class sizes is hidden in a collapsed group; home cards read as one long link | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 0 material, 5 minor ([claims.md](standins/audits/audit-15/fact-check/claims.md)); one spending quote could not be checked word for word | no material errors | Yes |
| Impartiality critics and judge | 0 material open; 4 critic points and 1 judge point upheld as minor, 15 rejected ([judgement.md](standins/audits/audit-15/impartiality/judgement.md)) | no upheld material finding | Yes |

The accuracy workflow has not yet run for this audit's sample. It runs when the sample reaches `main`, so its result is not in these scores.

### Material findings

None. The fact-checker and the judge upheld no material finding.

### Minor findings (kept, not capped)

- Fact-checker: F1, the earnings pages still call 2025 provisional, although ONS published 2026 earnings (April 2026 at £811.20) on about 22 October 2026, and the 2026 figure is not used for the pay-after-inflation headline; F2, "series ends in 2023" for holidays, when ONS still publishes UK-resident totals under the new method; F3, a source record names the wrong population for the holiday figures (Great Britain residents, not UK); F4, the direct-taxes description leaves out student loan repayments; F5, "rose until 2019" on the holidays page hides falls before 2019, and the class-size wording smooths over a small rise in 2022-23.
- Judge: the 36.7% against 36.2% pair appears on the home page and who-pays without the lowest-fifth caveats that sit on the household-tax page; the poverty and hardship exclusion is worded as "not measured here", although the site's own rule would admit the official low-income series; spending growth is shown in total rather than per person, which overstates growth as population rose; the "largest rise" in spending by area ranks by pounds rather than per cent; the first G7 section on international.html shows four of seven countries with no selection rule.

### Gaps, most valuable first

Written from the readers' notes, the critical misses and the findings.

1. Make the richest fifth's share of all tax paid findable and explain it in plain words beside the chart: R4 and R5 both missed critical question 12, and the site check could find only a glossary definition of that share, not the chart the question describes.
2. Bring the G7 tax comparison into view: J1.1 and J1.4 each passed 3 of 5, because readers found the tax chart inside a closed "More on" box and the visible G7 section shows only four countries with no rule for choosing them.
3. Shorten the routes for a phone reader: R4 and R5 ran out of 40 actions before women's employment; the menu becomes a Menu button after scrolling and its numbers shift between pages; and the single-year picker for class sizes is hidden in "Find one year's figure".
4. Say what the earnings chart cannot show before 2002, in the place a reader looks for "how has it changed since I was young", since informal reader I3 found no answer.
5. Fix the fact-checker's minor items F1 to F5, starting with the provisional 2025 earnings label and the missing 2026 figure.
6. Fix the judge's minor points: the lowest-fifth caveat beside the 36.7% and 36.2% pair, the wording of the poverty exclusion, per-person spending growth, the largest-rise ranking by pounds, and the rule for the G7 selection.
7. Check the one spending quote word for word against ONS (the fact-checker could not reach the bulletin).
8. Confirm the accuracy workflow commits `fact-check/results.json` once this audit's sample is on `main`, and record it in the next audit.

Gaps 1 and 2 block a level-5 result for D1 to D6. Gap 3 is what cost R4 and R5 their critical question 12 by running out of actions.

### Dimension scores

Rubric v3 caps D1 to D6 at 4 when the simulated phone test has not passed, because level 5 needs it.

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | Every public-money question was answered by readers who reached it; J1.1 and J1.4 (G7 tax comparison) failed; the phone test did not pass. |
| D2 Life: breadth and depth | 4 | All five topics are on the site; R4 and R5 ran out of actions before women's employment. |
| D3 Life: choosing and comparing | 4 | The class-size single-year picker is hidden; the year finder and compare work but need Go or extra taps. |
| D4 Explanation and understanding | 4 | Critical question 12 was missed twice; a reader confused gross and disposable income on the tax share. |
| D5 Visual design and charts | 4 | Charts start at zero and are captioned; the G7 chart is hidden in a closed box and shows only four of seven countries. |
| D6 Phone experience and navigation | 4 | No sideways scrolling; the menu changes after scrolling and its numbers shift; readers used 33 to 40 of 40 actions. |
| D7 Accuracy and traceability | 4 | 0 material findings from the 30-claim check; 5 minor items; the accuracy workflow result is still to come. |
| D8 Impartiality | 5 | The judge upheld no material finding and checked the rule; 5 minor points upheld. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocker, no keyboard traps, every chart has a text summary, axe checks in CI. |
| D10 Honesty about limits and continuity | 4 | Breaks are marked; the 2002 start of pay and the "rose until 2019" wording are not yet fully explained. |
| D11 Reader evidence | 2 | Informal, phone, new-question, prior-knowledge and screen-reader runs are recorded. The phone test did not pass and its problems are open, so D11 is 2, as in audit 14. |
| **Total** | **44 / 55** | |

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are not five people; screenshots are not a phone in the hand; an accessibility tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 14: 4 November 2026 (rubric v3, after the audit 13 fixes #156 to #161)

- Commit audited: `c2c044e` on `main` (T88, #161). The "Live site matches main" check for it is green
  ([run 41751432312](https://github.com/jnyross/unpoliticalaf/actions/runs/41751432312)). CI on #161 passed before it merged, which includes the phone-length and axe checks.
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure [standins/README.md](standins/README.md). All evidence is in [standins/audits/audit-14/](standins/audits/audit-14/).
- Stand-ins run, each a fresh session that did not build the site: a question writer (24 new questions, sealed before any phone reader started, `new-questions.sha256`; Q18 and Q19 were replaced after a site check found no single clear answer); 3 informal readers (P3, P9, P8); 5 phone readers (P2, P7, P10, P5, P1, drawn at random); a screen-reader reader; an adversarial fact-checker; a left critic, a right critic and a judge. Readers ran on a smaller model than the reviewers.
- Automated checks: keyboard check finds no traps on the main pages ([keyboard.txt](standins/audits/audit-14/keyboard.txt)); all 1,327 charts have a text summary with figures ([summaries.txt](standins/audits/audit-14/summaries.txt)). A local `make a11y` stopped on two phone-length warnings, who-pays (8.6 screens against 8.5) and holidays (9.1 against 8.8). Local reads run 0.2 to 0.3 screens longer than CI, as noted before, and CI passed on #161 ([accessibility.txt](standins/audits/audit-14/accessibility.txt)). Keep those two pages under their limits.
- Who scored it: a Claude session that did not build the site.

**Total: 44 out of 55. Target not met (simulated).** Audit 13: 45. The simulated phone test did not pass: 53 of 60 overall, but one reader (R2, profile P7) got only 6 of 12 and missed critical question 12 (change against cause, near women's employment). That run used all 40 actions before reaching pay, class size, holidays, renting and women's employment. Every John's question now passes 5 of 5, and the new-question, prior-knowledge and screen-reader stand-ins pass. No material accuracy or impartiality finding is open.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 53/60: R1 12, R2 6, R3 12, R4 11, R5 12; R2 missed critical Q12 and used 40 of 40 actions | 48/60, each reader 9/12, all critical right | No |
| New questions (24, sealed) | 108/120 with the site (90%), 32 without | 80% | Yes |
| Prior-knowledge check | 3/60 without the site, 53 with it (+50) | +20 | Yes |
| John's questions | J1.1 to J1.7 all 5 of 5 with the site, 0 without (J1.2 now passes after #159) | every probe answered, 4 of 5 right | Yes |
| Informal check | 3 readers (P3, P9, P8); all found an answer to all three questions; nothing blocking | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 14 actions, critical right; no blocking barrier, but the "Find one year's figure" expander renumbers its links and cost about 3 actions | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 0 material, 6 minor ([claims.md](standins/audits/audit-14/fact-check/claims.md)); the "Accuracy check" workflow re-reads the publishers' files once this PR is on `main` | no material errors | Yes (minor items below) |
| Impartiality critics and judge | 0 material open; 5 minor upheld, 15 critic examples rejected ([judgement.md](standins/audits/audit-14/impartiality/judgement.md)) | no upheld material finding | Yes |

Three new questions were answered "not sure" by several readers: Q15 (why the poorest fifth's indirect taxes look high against their income) and Q17 (cash pay up 50% against prices up 40%) were not found on the site by three readers; Q18 (real pay 2008 to 2014) was read from chart lines that break at 2011 by two readers.

### Material findings

None. The fact-checker and the judge both upheld no material finding.

### Minor findings (kept, not capped)

- Fact-checker: the site rounds exact halves down (£132.5bn shows as £132bn; 31,150 thousand visits shows as 31.1 million); the words under the share-of-GDP spending chart skip the 2021-22 low of 43.4%; the home page calls ONS Table 8's 33.6% an average across households, but it covers individuals; the £242 a week mortgage payment uses the "all mortgage types" row rather than all mortgagors (£236); house prices say "In 2025" for the year to September 2025; the private-renting chart on year pages runs to 2025-26 though its last figure is 2024-25; the housing-places page implies only Scotland counts tied homes as private renting; the Tax and income page says the older-method share "fell until 2017/18" (its lowest point was 2009/10).
- Judge: "rising in most years" for spending passes over the flat run from £1,116bn (2010-11) to £1,132bn (2019-20); the retired-households explanation ("smaller and have lower incomes") is one-sided; the 2016 ONS quote the latest bulletin dropped is still used; no rule is stated for choosing the everyday-life topics, and none measures hardship; the first G7 chart on international.html compares the UK with France and the US but leaves out Japan, the lowest.

### Gaps, most valuable first

Written from the findings and the readers' notes only.

1. Make the Work page's women's employment figures and its change-is-not-cause note easy to find: R2 missed the critical question 12, and R3 answered from the generic box without seeing the women's figures.
2. Shorten the routes to the figures for a phone reader: R2 spent all 40 actions without reaching pay, class size, holidays, renting or women's employment, because figures sit in "More on" boxes, the year dropdown needs Go, and menu numbers shift after scrolling.
3. Say in words on the earnings page that real pay fell between 2008 and 2014 (median full-time pay, after inflation, £771 in 2008 and £717 in 2014 in 2025 prices), so the chart's break at 2011 does not hide it.
4. Explain on the household-tax page why the poorest fifth's indirect taxes look high against their income, and give the cash-against-prices arithmetic once with a worked example, since three readers found neither (new Q15 and Q17).
5. Make the holidays headline (58.4 million visits) and its chart agree on the years they cover: informal readers I1 and I2 saw a 2025 headline above a chart that ends in 2023.
6. Fix the fact-checker's minor items: half-way rounding, the spending-share wording that skips the 2021-22 low, "average across households" for ONS individuals, the mortgage payment row, the house-price year, the private-renting chart's last year, the tied-homes sentence and the "fell until 2017/18" wording.
7. Fix the judge's minor items: "rising in most years" for spending, the one-sided retired-households explanation, the dropped 2016 ONS quote, the stated rule for choosing topics, and the missing Japan bar on the first G7 chart (or a sentence saying why it is left out).
8. Keep the "Find one year's figure" links numbered the same when the expander opens (screen-reader reader lost about 3 actions), and keep the who-pays and holidays pages under their phone-length limits.

Gap 1 and gap 2 block a level-5 phone result for D1 to D6. Gaps 3 and 4 are the new-question misses. The accuracy workflow result (`fact-check/results.json`) arrives on `main` after this PR merges and is not yet in the scores.

### Dimension scores

Rubric v3 caps D1 to D6 at 4 when the simulated phone test has not passed, because level 5 needs it.

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | All four public-money questions answered by every reader who reached them; not 5 because the phone test did not pass and minor wording remains (spending share, the judge's G7 point). |
| D2 Life: breadth and depth | 4 | All five topics are on the site, but R2 could not reach pay, class size, holidays, renting or women's employment in its budget; not 5 without a passed phone test. |
| D3 Life: choosing and comparing | 4 | Compare and year-finder work without JavaScript; the dropdown needs Go, the finder's links renumber, and the 2008 to 2014 pay change is read from breaks. |
| D4 Explanation and understanding | 4 | Critical questions right; informal readers still stumble on OBR and IFS terms, "before interest received", and the lowest fifth paying a higher tax share than the highest before the explanation. |
| D5 Visual design and charts | 4 | Charts start at zero and are captioned; the holidays headline still sits above a chart that ends in 2023 (gap 5). |
| D6 Phone experience and navigation | 4 | No sideways scrolling; readers used 36 to 40 of 40 actions and overshot sections; the menu numbers shift. |
| D7 Accuracy and traceability | 4 | 0 material findings from the 30-claim check; 6 minor items; the accuracy workflow result is still to come. |
| D8 Impartiality | 5 | The judge upheld no material finding and checked the rule; 5 minor points upheld. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocker, no keyboard traps, every chart has a text summary, axe checks in CI. |
| D10 Honesty about limits and continuity | 4 | Breaks are marked and no change is taken across a marked break; not 5 because the 2021-22 spending low is misdescribed and uncertainty for headline survey figures is not shown. |
| D11 Reader evidence | 2 | Informal, phone, new-question, prior-knowledge and screen-reader runs are recorded. The phone test did not pass and its problems are open, so by the rule that a level-3 run needs its problems fixed, and that a torn score takes the lower level, D11 is 2. |
| **Total** | **44 / 55** | |

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are not five people; screenshots are not a phone in the hand; an accessibility tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 13: 3 November 2026 (rubric v3, after the audit 12 fixes #150 to #154)

- Commit audited: `7ab0f27` on `main` (site build). The "Live site matches
  main" check for it is green
  ([run 41722006701](https://github.com/jnyross/unpoliticalaf/actions/runs/41722006701)).
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure
  [standins/README.md](standins/README.md). All evidence is in
  [standins/audits/audit-13/](standins/audits/audit-13/).
- Stand-ins run, each a fresh session that did not build the site: a question
  writer (24 new questions, sealed in `c6dd96b` before any phone reader
  started; three were replaced before sealing because the site had no single
  clear answer: the statutory VAT rate, the largest single benefit and the
  services share of jobs); 3 informal readers (profiles P2, P6, P3); 5 phone
  readers (P9, P4, P1, P8, P10, drawn at random); a screen-reader reader; an
  adversarial fact-checker; a left critic, a right critic and a judge. Readers
  ran on a smaller model than the reviewers.
- **Phone test run twice.** In the first run every phone reader's session
  froze after opening the Menu button: the phone tool replayed the menu tap
  before restoring the scroll, when the floating menu added in #153 is hidden.
  A real browser opens the menu and follows its links normally (checked by the
  auditor), so this was a fault in the test tool, not the site. The tool now
  replays each tap at the scroll position where it was made, and a failed
  replay no longer locks the session (`scripts/standins.py`). The first run is
  kept in [void-run/](standins/audits/audit-13/void-run/) and not scored; all
  five readers were run again as fresh sessions with the same profiles.
- Automated checks: no keyboard traps on the 9 main pages; all 1,326 charts
  have a text summary with figures; axe (`make a11y`) runs in CI on this PR.
- Who scored it: a Claude session that did not build the site.

**Total: 45 out of 55. Target not met (simulated).** Audit 12: 46. For the
first time the simulated phone test passes (58 of 60, every reader 11 or 12,
every critical question right), and the four debt and borrowing-costs probes
that failed last time now pass 5 of 5. Two things stop the target: one
material accuracy finding on the tax and income page, which caps D7 at 1, and
John's probe J1.2 (UK spending against the United States and France), which
only 2 of 5 readers answered right.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 58/60; R1 11, R2 12, R3 11, R4 12, R5 12; every critical question right; actions 35 to 40 | 48/60 and each reader 9/12 with the critical questions | Yes |
| New questions (24, sealed) | 119/120 with the site (99%), 48 without | 80% | Yes |
| Prior-knowledge check | 5/60 without the site, 58 with it (+53) | +20 | Yes |
| John's questions | J1.1 and J1.3 to J1.7 5 of 5; J1.2 2 of 5 (three readers said UK spending was lower than the United States and higher than France) | every probe answered, 4 of 5 right | No (J1.2) |
| Informal check | 3 readers; all found an answer to all three questions, nothing blocking | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 11/12 in 13 actions, critical questions right; no blocking barrier (missed the 2015 against 2025 holiday question) | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 1 material, 6 minor ([claims.md](standins/audits/audit-13/fact-check/claims.md)) | no material errors | No |
| Impartiality critics and judge | 0 material, 4 critic examples upheld as minor, 16 rejected; the judge found 4 more minor breaches ([judgement.md](standins/audits/audit-13/impartiality/judgement.md)) | no upheld material finding | Yes |

Four of the five phone readers used only 1 to 8 actions on the 24 new
questions and answered most of them from what they had already seen, so the
99% says more about understanding than about finding. The fact-checker's 30
figures (`fact-check/sample.json`) are re-downloaded from the publishers by the
"Accuracy check" workflow when this PR lands on `main`.

### Material findings (cap their dimensions at 1)

1. **"Why did direct taxes rise in 2023/24?" (fact-checker, confirmed by the
   auditor).** The tax and income page asks why direct taxes rose and answers
   with the ONS's fiscal-drag quote ("pay greater proportion of their income
   in taxes"). The page's own table shows direct taxes fell as a share of gross
   income, from 23.2% in 2022/23 to 22.9% in 2023/24 (`etb.t8.gross.direct.all`);
   the ONS bulletin says they rose only in cash and fell after inflation. A
   reader comes away believing households paid a larger share of income in
   direct tax. D7.

### Scores

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | The phone test passed and the debt probes now pass. Not 5: three readers misread how UK spending compares with the United States and France (J1.2), and minor points remain (spending as a share of GDP said to have "fell" since 2020-21 when it bottomed in 2021-22 and rose; £30.5bn of VAT refunds inside "all other taxes" unexplained; the home "Who pays?" card gives only the top 1%'s share of Income Tax). |
| D2 Life: breadth and depth | 5 | Phone test passed with every life question right but two, no informal reader was blocked, the longest history is shown first, and nations and phases are named. |
| D3 Life: choosing and comparing | 4 | Not 5: four of the five phone readers and the screen-reader reader could not find a single year's class size (2019) on the schools page and guessed or went through the compare pages; "not compared" still puzzled three readers and the screen-reader reader missed the 2015 against 2025 holiday question. |
| D4 Explanation and understanding | 4 | Every critical question right. Not 5: all three informal readers stumbled on the home cards (the £1,360bn against £1,228bn "accounting entries" sentence, 36.7% for the lowest fifth against 36.2% for the highest before the explanation, pay "about the same" beside a cash rise), and the ONS explanation of why the shares differ sits in a collapsed panel. |
| D5 Visual design and charts | 4 | Bars start at zero, above-zero axes are captioned, panels share a scale. Not 5: the home and holidays headlines give 58.4 million visits in 2025 above a chart of visits per 100 residents that ends in 2023 (all three informal readers). |
| D6 Phone experience | 4 | No sideways scrolling and the floating menu works. Not 5: readers used 35 to 40 of their 40 actions, overshot figures when scrolling long pages, and found the glossary (22 screens) and year-by-year page long. |
| D7 Accuracy and traceability | 1 | Capped by the direct-taxes heading. The other 29 claims matched their records and source files. |
| D8 Impartiality | 5 | The judge upheld no material finding; start years, scales and group order mostly follow the rule, and the methods page explains how the site chooses what to show. Minor points listed below. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 11/12 with no blocking barrier, no keyboard traps, every chart has a text summary; axe in CI. |
| D10 Honesty about limits | 4 | No change is calculated across a marked break. Not 5: the holidays lead gives 2025 (Great Britain residents, new method) straight after 2019 (UK residents, old method) without saying the two are not comparable. |
| D11 Reader evidence | 5 | On this commit the simulated phone test, the new-question test and the prior-knowledge check all passed (`standins.py score`). |
| **Total** | **45 / 55** | |

### Gaps, most valuable first

Written from the findings and the readers' confusion notes only.

1. Fix the tax and income page's "Why did direct taxes rise in 2023/24?": the page's own figures show direct taxes fell as a share of gross income (23.2% to 22.9%) and the ONS says they rose only in cash, so say what rose and what fell before quoting the fiscal-drag explanation.
2. Make the G7 spending comparison as easy to read as the tax one: three of five readers got UK government spending against the United States and France wrong (John's J1.2), and one could not tell how to switch from taxes to spending.
3. Let readers find a single year's figure on a topic page without the compare pages: four phone readers and the screen-reader reader could not find the 2019 primary class size (and which nation it covers) on the schools page.
4. On the holidays page and its home card, do not set 2025 (Great Britain, new method) straight after 2019 (UK, old method) without saying they are not comparable, explain "not compared" where the 2015 against 2025 comparison appears, and stop the 2025 headline sitting above a chart that ends in 2023.
5. Make the home cards answer first in plain words: the £1,360bn against £1,228bn "accounting entries" sentence, 36.7% against 36.2% before its explanation, and pay "about the same" beside a cash rise confused all three informal readers.
6. Fix the smaller points: spending as a share of GDP "fell" from 2020-21 when it bottomed in 2021-22 and rose; VAT refunds inside "all other taxes"; "higher than in 10 of the other 16 years" for home ownership with ties; the home page's 2026 work and class-size figures against the year-by-year page's 2025 without a note; retired households "over half" (ONS: at least half); 2025 pay not flagged provisional; a who-pays note setting 2023-24 Income Tax beside 2025-26 totals; the holidays source record's "UK residents"; the judge's minor points (the household-tax ONS explanation collapsed, housing pages comparing only private renting with 2008-09, the 53.3% net-recipients caveat collapsed, the who-pays tiles putting the highest-income fifth first, the schools lead starting at 2008 not 2006); and the 22-screen glossary.

John's questions: J1.2 failed on reading the G7 spending chart; none is open.

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are
not five people; screenshots are not a phone in the hand; an accessibility
tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 12: 3 November 2026 (rubric v3, after the audit 11 fixes #141 to #148)

- Commit audited: `1f64e04` on `main` (site build). The "Live site matches
  main" check for it is green
  ([run 41698025008](https://github.com/jnyross/unpoliticalaf/actions/runs/41698025008)).
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure
  [standins/README.md](standins/README.md). All evidence is in
  [standins/audits/audit-12/](standins/audits/audit-12/).
- Stand-ins run, each a fresh session that did not build the site: a question
  writer (24 new questions, sealed in `c6aeb6d` before any reader started; two
  were replaced before sealing because the site had no single clear answer: a
  statutory VAT rate and the shape of real pay around 2008); 3 informal readers
  (profiles P7, P2, P9); 5 phone readers (P6, P10, P5, P3, P8, drawn at
  random); a screen-reader reader; an adversarial fact-checker; a left critic,
  a right critic and a judge. Readers ran on a smaller model than the reviewers.
- Automated checks: no keyboard traps on the 9 main pages; all 1,324 charts
  have a text summary with figures; axe (`make a11y`) runs in CI on this PR.
- Who scored it: a Claude session that did not build the site.

**Total: 46 out of 55. Target not met (simulated).** Audit 11: 35. For the
first time no stand-in found a material problem: the fact-checker, the judge
and the critics all came back with minor points only, and every audit 11 cap is
gone. Two things still fail the target: one phone reader (R4) used up the
budget and missed critical question 12 on change and cause, and four of the
five readers could not find the debt and borrowing-costs page, so four of
John's probes failed.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 51/60; R1 9, R2 12, R3 11, R4 8, R5 11; R4 missed critical question 12 (marked not sure) | 48/60 and each reader 9/12 with the critical questions | No (R4) |
| New questions (24, sealed) | 108/120 with the site (90%), 49 without | 80% | Yes |
| Prior-knowledge check | 4/60 without the site, 51 with it (+47) | +20 | Yes |
| John's questions | J1.1, J1.2, J1.4 pass (4 or 5 of 5); J1.3, J1.5, J1.6, J1.7 1 of 5 each: four readers never reached `borrowing.html` | every probe answered, 4 of 5 right | No |
| Informal check | 3 readers; all found an answer to all three questions, nothing blocking (audit 11: all three blocked on change since they were young) | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 15 actions; no blocking barrier (long 55-year selects, long home card links) | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 0 material, 9 minor ([claims.md](standins/audits/audit-12/fact-check/claims.md)) | no material errors | Yes |
| Impartiality critics and judge | 0 material, 5 critic examples upheld as minor, 15 rejected; the judge found 2 more minor breaches ([judgement.md](standins/audits/audit-12/impartiality/judgement.md)) | no upheld material finding | Yes |

The fact-checker's 30 figures (`fact-check/sample.json`) are re-downloaded from
the publishers by the "Accuracy check" workflow when this PR lands on `main`,
which commits `fact-check/results.json`. Every value the fact-checker
recalculated from the repository's copies of the source files matched. A
mismatch there would reopen D7.

### Material findings

None.

### Scores

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | No finding against the answers. Not 5: the phone test did not pass, and four readers could not find how UK debt, borrowing costs and debt interest compare with the G7, which sits on a page linked only from the home page and the end of the countries page. |
| D2 Life: breadth and depth | 4 | The longest history now comes first and no informal reader was blocked. Not 5: the phone test did not pass. |
| D3 Life: choosing and comparing | 4 | Not 5: three readers missed the 2015 against 2025 holiday question because they could not find or understand "not compared", and readers found the year-by-year page a long scroll with one year at a time. |
| D4 Explanation and understanding | 4 | Every reader who reached them got the household-average and illustration questions right. Not 5: R4 marked the change-and-cause question not sure, and two readers nearly mixed up 33.6%, 27.2% and 36.7%. |
| D5 Visual design and charts | 4 | Audit 11's holiday title is fixed; bars start at zero, above-zero axes are captioned, panels share a scale. Not 5: the taxes page's after-inflation chart labels its axis from 1948-49 when its data start in 1955-56, and the phone test did not pass. |
| D6 Phone experience | 4 | No sideways scrolling and the "Top and menu" button no longer covers text. Not 5: three readers still lost the menu once they had scrolled, and long country lists tired four readers. |
| D7 Accuracy and traceability | 5 | The fact-checker found no material error in 30 headline claims, every recalculated figure matched, and corrections are logged. Its 9 minor points are listed below. |
| D8 Impartiality | 5 | The judge upheld no material finding; start years, scales and group order follow the rule, and the methods page explains how the site chooses what to show. Minor points listed below. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocking barrier, no keyboard traps, every chart has a text summary; axe in CI. |
| D10 Honesty about limits | 4 | No change is shown across a marked break. Not 5: the who-pays net-recipients chart (1977 to 2023/24) does not mark the ONS's 2001/02 top-income adjustment that its own Limits note mentions. |
| D11 Reader evidence | 3 | The simulated phone test is recorded and audit 11's reader problems are fixed. Not 5: the phone test and John's questions did not pass. |
| **Total** | **46 / 55** | |

### Gaps, most valuable first

Written from the findings and the readers' confusion notes only.

1. Make the debt and borrowing-costs page easy to find: readers looking for how UK debt, 10-year borrowing costs and debt interest compare with the G7 went to the countries page, the glossary or the taxes and spending pages and never reached it (4 of 5 readers, John's J1.3, J1.5, J1.6, J1.7).
2. Make the year-by-year route answer the questions readers bring to it: they arrive there for class sizes, holidays and employment and miss the infant class legal limit (3 readers), the most visited country for holidays (4 readers), the change-is-not-cause note (one critical miss) and a 2015 against 2025 holiday comparison, because the page is a long scroll of one year at a time.
3. Explain "not compared" in plain words where a comparison crosses the 2024 holiday method break (and for pay and housing), so readers can tell that the site deliberately does not compare those years (3 readers missed the 2015 against 2025 holiday question).
4. Keep a way to the menu within reach once a reader has scrolled down a long page, and shorten or collapse the long G7 and OECD country lists so readers do not lose the UK row (three and four readers).
5. Fix the smaller points: the housing mini-chart's "2025-26" when the latest is 2024-25; men's employment "low of 75.4% in 2010" beside a lowest of 75.1% in 1993; England and Wales pay rises called "equal"; "households that retired people live in" for ONS retired households; "Corporation Tax includes North Sea profits" when the Energy Profits Levy sits in other taxes; Scotland's private renting including tied homes; the `rec.othertax.2025-26` figure record listing 7 of the 10 taxes it subtracts; the "27% to 36%" range on household types; the class sizes comparison starting at 2008 when the series starts in 2006; the unmarked 2001/02 adjustment on the net-recipients chart; the taxes after-inflation axis labelled from 1948-49; and the judge's minor framing points (home card tax shares without their denominator note, borrowing page without the OECD average, Corporation Tax incidence in the glossary, who-pays cash amounts without shares, the default 2011 against 2019 comparison).

John's questions: J1.3, J1.5, J1.6 and J1.7 failed on findability (the answers are on `borrowing.html`); none is open.

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are
not five people; screenshots are not a phone in the hand; an accessibility
tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 11: 3 November 2026 (rubric v3, after the audit 10 fixes #133 to #139)

- Commit audited: `b08069b` on `main` (site build). The "Live site matches
  main" check for it is green
  ([run 41663115893](https://github.com/jnyross/unpoliticalaf/actions/runs/41663115893)).
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure
  [standins/README.md](standins/README.md). All evidence is in
  [standins/audits/audit-11/](standins/audits/audit-11/).
- Stand-ins run, each a fresh session that did not build the site: a question
  writer (24 new questions, sealed in `0e112f3` before any phone reader started;
  three were replaced before sealing because the site had no single clear
  answer); 3 informal readers (profiles P9, P7, P8); 5 phone readers (P8, P5,
  P9, P7, P2, drawn at random); a screen-reader reader; an adversarial
  fact-checker; a left critic, a right critic and a judge. Readers ran on a
  smaller model than the reviewers.
- Automated checks: no keyboard traps on the 9 main pages; all 1,324 charts
  have a text summary with figures; axe (`make a11y`) runs in CI on this PR.
- Who scored it: a Claude session that did not build the site.

**Total: 35 out of 55. Target not met (simulated).** Audit 10: 38. Audit 10's
class-size title is fixed and the readers did better than ever (59 of 60, 112
of 120 new questions), but two new material findings, both on the holidays
page, cap three dimensions at 1, and one reader missed the critical question
on change and cause.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 59/60; R1 12, R2 11, R3 12, R4 12, R5 12; R2 missed critical question 12 (could not find it) | 48/60 and each reader 9/12 with the critical questions | No (R2) |
| New questions (24, sealed) | 112/120 with the site (93%), 60 without | 80% | Yes |
| Prior-knowledge check | 10/60 without the site, 59 with it (+49) | +20 | Yes |
| John's questions | J1.1 to J1.7 all answered on the site; 4 or 5 of 5 readers right on every probe | every probe answered, 4 of 5 right | Yes |
| Informal check | 3 readers; all three marked "how has it changed since I was young" as partly blocking, because the charts they saw start in 2008 | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 15 actions; no blocking barrier | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 1 material, 5 minor ([claims.md](standins/audits/audit-11/fact-check/claims.md)) | no material errors | No |
| Impartiality critics and judge | 0 critic examples upheld as material, 3 minor, 17 rejected; the judge found 1 material and 4 minor breaches the critics missed ([judgement.md](standins/audits/audit-11/impartiality/judgement.md)) | no upheld material finding | No |

The fact-checker's 30 figures (`fact-check/sample.json`) are re-downloaded from
the publishers by the "Accuracy check" workflow when this PR lands on `main`,
which commits `fact-check/results.json`. Every value the fact-checker
recalculated from the repository's copies of the source files matched.

### Material findings (cap their dimensions at 1)

1. **Holiday chart title compares across a break (judge, confirmed by the
   auditor).** The holidays page's chart title says visits "rose back to about
   the 2019 level". The 2025 figure (58.4 million, new method, Great Britain
   residents) is set against 2019 (58.7 million, old method, UK residents),
   across the break the chart's own text says is not compared. The 1980-onwards
   chart uses the same words for 126 per 100 residents in 2023 against 140 in
   2019. D5, D10.
2. **Holiday page gives all-purpose visits as if they were holidays
   (fact-checker, confirmed by the auditor).** In a lead paragraph about
   holiday visits, "In 2025 Spain had 19.1 million visits, then France (9.1
   million) and Italy (5.7 million)" are visits for any purpose; the holiday
   figures in the same table are 15.6, 5.9 and 3.6 million. D7.

### Scores

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | No material finding; the critics' points on who pays and debt interest were rejected or minor. Not 5: the phone test did not pass. |
| D2 Life: breadth and depth | 4 | No finding against the evidence itself. Not 5: the phone test did not pass, and all three informal readers could not see change since they were young because the charts they reached start in 2008. |
| D3 Life: choosing and comparing | 4 | Audit 10's "not compared" and single-year points are fixed. Readers still struggled to find a 2015 against 2025 comparison, and the compare grid moved under one reader's tap. Not 5: phone test. |
| D4 Explanation and understanding | 4 | Only one critical miss, and that reader could not find the point rather than misread it; every reader answered the household-average and illustration questions right, though two noted they nearly mixed up the top 1%'s 27.2% with a tax rate or the 33.6% household figure. Not 5: phone test. |
| D5 Visual design and charts | 1 | Capped by the holiday chart title. Otherwise 4: the judge found bars start at zero, above-zero axes are captioned and panels share a scale. |
| D6 Phone experience | 4 | No sideways scrolling; back to top is on every page. Not 5: four readers said the floating "Back to top" button covered text or a table row, and the menu is still only at the top. |
| D7 Accuracy and traceability | 1 | Capped by the holiday countries figure. The other 29 claims matched their records and source files. |
| D8 Impartiality | 4 | The judge upheld none of the critics' 20 examples as material. Not 5: the judge's own material breach (the holiday title) leaves the stand-in failed, and its minor points are open. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocking barrier, no keyboard traps, every chart has a text summary; axe in CI. |
| D10 Honesty about limits | 1 | Capped by the holiday title, which shows a change across a marked break. |
| D11 Reader evidence | 3 | The simulated phone test is recorded and audit 10's reader problems are fixed. Not 5: the phone test did not pass. |
| **Total** | **35 / 55** | |

### Gaps, most valuable first

Written from the findings and the readers' confusion notes only.

1. Fix the holidays page: describe each side of the 2024 method break separately in both chart titles (no "back to about the 2019 level"), give holiday visits (not all-purpose visits) for Spain, France and Italy in the holiday paragraph or label them clearly, and make the trend-title check fail any title that compares across a marked break.
2. Put the "change is not cause" point next to the employment figures for women and men on the work page and the year pages, where a reader looking for why a rate changed will see it (one phone reader and the screen-reader reader could not find it).
3. Show the longest history first on the topic pages and home cards, so a reader looking for change since the 1980s or 1990s sees it without hunting (all three informal readers stopped at charts that start in 2008).
4. Stop the floating "Back to top" button covering text and table rows, and give a quick way to the menu without scrolling to the top (four readers).
5. Make comparing two years easier: a clear route from a topic to a 2015 against 2025 style comparison, a compare grid that does not move under a tap, and compare selects that confirm the choice to a screen reader and come before the long list of year links.
6. Make three things findable near the top of their pages, which several readers could not find: the legal limit for infant class sizes, how manufacturing's share of jobs has changed, and the most visited countries.
7. Fix the smaller points: the top 1% "paid" versus "owed" Income Tax; "primary class sizes rose until 2016, then fell" when they were flat from 2016 to 2019; "paid an average of 4.58% to borrow" for a market yield; "retired households" for retired individuals; the pay-freeze quote on the 2008 to 2010 year pages; the who-pays chart showing tax shares without income shares; home-page debt interest on the gross basis only; work's 2025 headline against the home page's 2026 and the schools page's "no 2026 figures"; spending history's 1955-56 against 2021-22 across breaks and "a great deal"; the borrowing page's own-words cause for 2022 and its own-words explanation of yield gaps; and the home page's £1,228bn against £1,360bn and debt interest £11 against general public services £13.

John's questions: none open, and every probe passed.

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are
not five people; screenshots are not a phone in the hand; an accessibility
tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 10: 3 November 2026 (rubric v3, after the audit 9 fixes #126 to #131)

- Commit audited: `10255dc` on `main` (site build). The "Live site matches
  main" check for it is green
  ([run 41630480388](https://github.com/jnyross/unpoliticalaf/actions/runs/41630480388)).
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure
  [standins/README.md](standins/README.md). All evidence is in
  [standins/audits/audit-10/](standins/audits/audit-10/).
- Stand-ins run, each a fresh session that did not build the site: a question
  writer (24 new questions, sealed in `f733501` before any reader started; three
  were replaced before sealing because the site had no single clear answer); 3
  informal readers (profiles P1, P7, P9); 5 phone readers (P2, P4, P5, P8, P7,
  drawn at random); a screen-reader reader; an adversarial fact-checker; a left
  critic, a right critic and a judge. Readers ran on a smaller model than the
  reviewers.
- Automated checks: no keyboard traps on the 9 main pages; all 1,321 charts
  have a text summary with figures; axe (`make a11y`) runs in CI on this PR.
- Who scored it: a Claude session that did not build the site.

**Total: 38 out of 55. Target not met (simulated).** Audit 9: 24. All six of
audit 9's material findings are fixed, the judge upheld no material finding,
and the site now answers every one of John's questions. Two things hold it
back: one misleading chart title on class sizes (the only material finding),
and two readers who each missed one critical question.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 56/60; R1 11, R2 12, R3 10, R4 12, R5 11; R3 missed critical question 12 and R5 critical question 7 | 48/60 and each reader 9/12 with the critical questions | No (R3, R5) |
| New questions (24, sealed) | 101/120 with the site (84%), 41 without | 80% | Yes |
| Prior-knowledge check | 9/60 without the site, 56 with it (+47) | +20 | Yes |
| John's questions | J1.1 to J1.7 all answered on the site; 4 or 5 of 5 readers right on every probe | every probe answered, 4 of 5 right | Yes |
| Informal check | 3 readers; I3 marked finding a clear before-and-after pay figure as blocking | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 22 actions; no blocking barrier | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 1 material, 10 minor ([claims.md](standins/audits/audit-10/fact-check/claims.md)) | no material errors | No |
| Impartiality critics and judge | 0 upheld material, 6 minor, 14 rejected, 5 minor breaches found by the judge ([judgement.md](standins/audits/audit-10/impartiality/judgement.md)) | no upheld material finding | Yes |

The fact-checker's 30 figures (`fact-check/sample.json`) are re-downloaded from
the publishers by the "Accuracy check" workflow when this PR lands on `main`,
which commits `fact-check/results.json`. The fact-checker used the
repository's copies of the source files.

### Material finding (caps its dimensions at 1)

1. **Primary classes of more than 30 (fact-checker, confirmed by the auditor).**
   The schools page's chart title reads "rose until January 2020, fell in
   January 2021, then rose". The figures on the same page show the primary
   share peaked at 13.3% in January 2025 and fell to 12.6% in January 2026, so
   the title and summary describe the latest move as a rise. D5, D7.

### Scores

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 4 | Audit 9's caps (changes across breaks in spending areas and tax history) are fixed; judge and fact-checker found only minor points. Not 5: the phone test did not pass. |
| D2 Life: breadth and depth | 4 | No finding against it. Not 5: the phone test did not pass. |
| D3 Life: choosing and comparing | 4 | Cap from audit 9 fixed: no change is worked out across a break. Readers still found "not compared" lines unclear and could not compare from a single-year page. Not 5: phone test. |
| D4 Explanation and understanding | 3 | Two readers each missed a critical understanding question (the illustrated £30,000 employee, and change versus cause), and readers mixed up 27.2%, 33.6% and 30%. Torn between 3 and 4, so 3. |
| D5 Visual design and charts | 1 | Capped by the class-size title. Otherwise 4: above-zero axes are now captioned and the judge found scales and ordering follow the rule. |
| D6 Phone experience | 4 | No page scrolls sideways. Not 5: readers spent many actions scrolling long pages back to the menu, and the international page puts the G7 table after a 36-country list. |
| D7 Accuracy and traceability | 1 | Capped by the class-size title. The other 29 claims matched their records and source files. |
| D8 Impartiality | 5 | The red team and judge upheld no material finding; start years, scales and group order follow the written rule; the methods page explains how the site chooses what to show. Minor points listed below. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocking barrier, no keyboard traps, every chart has a text summary; axe in CI. |
| D10 Honesty about limits | 4 | Audit 9's caps (partial 2020 holidays, changes across breaks) are fixed. Not 5: the accuracy stand-in did not pass. |
| D11 Reader evidence | 3 | The simulated phone test is recorded and the problems audit 9's readers found are fixed. Not 5: the phone test did not pass. |
| **Total** | **38 / 55** | |

### Gaps, most valuable first

Written from the findings and the readers' confusion notes only.

1. Fix the schools page's "classes of more than 30" chart title and summary so they name the January 2025 peak and the fall to January 2026, show 2026 as the latest year for class sizes and work where the downloaded files have it, and make the trend-title check catch a last-year turn like this.
2. Make the illustrated £30,000 employee easy to find from the "Tax and income" link and page, and keep it visibly separate from the taxes page (three phone readers could not find it, one gave up).
3. On the year-comparison pages, explain each "not compared" line in one short sentence with a link to the nearest comparable figures, and add a way to compare from a single-year page.
4. Put the G7 table first on the international comparison page, before the full list of countries (four phone readers scrolled past it).
5. Give long pages a quick way back to the menu or the page's sections, and bring the spending page's "Share of GDP" view up where readers look for it.
6. Give the earnings page and the home card a clear before-and-after pay figure after inflation that a reader can find quickly (an informal reader marked this blocking).
7. Fix the fact-checker's and judge's smaller points: "£11 of every £100" needs its base; tied and missing "largest" claims on spending areas and tax history; National Insurance's 2020-21 peak; "between 9% and 10%" for Income Tax; the household tax method-change year; "same method" for employment from 1971; debt interest on two bases between spending pages; Northern Ireland's "largest fall" at £716 both years; the borrowing page's one-month yield lead and unattributed explanation of yields; the house-price ratio from 1997 across its marked break; the 2011 vs 2019 suggested comparison; and the 1995 page's comparison table, whose Change column is off screen with no sign it scrolls.

John's questions: none open, and every probe passed.

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are
not five people; screenshots are not a phone in the hand; an accessibility
tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 9: 3 November 2026 (first audit under rubric v3, with stand-ins)

- Commit audited: `6b3257e` on `main` (site build). `main` then moved to
  `9429ae6` (#124, a workflow change only); the "Live site matches main"
  check for `9429ae6` is green
  ([run 41607707059](https://github.com/jnyross/unpoliticalaf/actions/runs/41607707059)).
- Rubric: [goal-rubric.md](goal-rubric.md) v3, procedure
  [standins/README.md](standins/README.md). All evidence is in
  [standins/audits/audit-9/](standins/audits/audit-9/).
- Stand-ins run, each a fresh session that did not build the site:
  a question writer (24 new questions, sealed in `5369747` before any reader
  started); 3 informal readers (profiles P3, P7, P5); 5 phone readers (P1, P4,
  P6, P8, P10, drawn at random); a screen-reader reader; an adversarial
  fact-checker; a left critic, a right critic and a judge. Readers ran on a
  smaller model than the reviewers.
- Automated checks: no keyboard traps on the 9 main pages; all 1,511 charts
  have a text summary with figures; axe (`make a11y`) runs in CI on this PR.
- Who scored it: a Claude session that did not build the site.

**Total: 24 out of 55. Target not met (simulated).** Audit 8 (rubric v2):
40. The fall is not the site getting worse. v3's stand-ins are the first
independent reviewers to look, and they upheld 7 material findings. The rubric
caps every dimension with an open material finding at 1 until it is fixed.

### Stand-in results

| Stand-in | Result | Bar | Pass |
|---|---|---|---|
| Simulated phone test (12 questions) | 50/60; R1 9, R2 10, R3 7, R4 12, R5 12; all critical questions right except R3's | 48/60 and each reader 9/12 with the critical questions | No (R3) |
| New questions (24, sealed) | 108/120 with the site (90%), 59 without | 80% | Yes |
| Prior-knowledge check | 6/60 without the site, 50 with it (+44) | +20 | Yes |
| John's questions | J1.1 and J1.2 5/5 readers right; J1.3 to J1.7 still open | every probe answered, 4 of 5 right | No (5 open) |
| Informal check | 3 readers found all three answers; no blocking notes | notes recorded | Yes (D11 level 2) |
| Screen-reader reader | 12/12 in 15 actions; no blocking barrier | 9/12, critical right | Yes |
| Fact-checker (30 headline claims) | 1 material, 8 minor ([claims.md](standins/audits/audit-9/fact-check/claims.md)) | no material errors | No |
| Impartiality critics and judge | 6 upheld material, 3 minor, 14 rejected ([judgement.md](standins/audits/audit-9/impartiality/judgement.md)) | no upheld material finding | No |

The fact-checker's 30 figures (`fact-check/sample.json`) are re-downloaded from
the publishers by the "Accuracy check" workflow when this PR lands on `main`
(the workflow cannot be started by hand from this session); it commits
`fact-check/results.json`. The fact-checker could not reach the publishers'
sites and used the repository's copies of the source files.

R5's first phone session froze when the phone tool offered a tap on a control
inside a closed fold, so R5 repeated the 12-question part in a fresh session
with the fixed tool (both runs are kept). The scorer also counted the readers'
session files as extra readers. Both tool faults are fixed in this PR, with a
test. The screen-reader reader's note about "unlabelled links" came from the
same fault (hidden controls have no text); the built pages have no control
without a name.

### Material findings (each caps its dimensions at 1)

1. **Holiday visits in 2020 (fact-checker).** "In 2020 this fell to 4.4
   million", the chart and the 7 per 100 residents sparkline show a partial
   year (the survey stopped on 16 March 2020) as the full year. D7, D10.
2. **Earnings changes across the 2011 and 2021 coding breaks (judge, L3).**
   "About the same as 2008", 2006 to 2025 +1.5%, the 10th and 90th percentile
   changes and the nation and region change table are worked out across
   breaks the page itself marks; the 2009 vs 2023 comparison calls 2006 to
   2025 "same method". D3, D10, D8.
3. **Spending areas 2003-04 to 2025-26 across the education student-loan and
   Network Rail breaks (judge, M2).** The summary names education's 4.8% to
   4.1% as the largest fall, partly an accounting change. D1, D10.
4. **Tax shares 1948-49 to 2022-23 across the marked breaks (judge, M3)** on
   the tax history page, including the percentage-point bar chart. D1, D10.
5. **A cause in the site's own words (judge, R4).** Household tax: the lowest
   fifth's share is explained as "because their households spend more of
   their income, some of it from savings or borrowing", not as an attributed
   ONS explanation. D8.
6. **Line charts that start above zero without saying so (judge, R8 and M1):**
   spending as a share of GDP (35 to 55), earnings (from £600) and work (from
   50, 60 or 65), including the nation and region panels. D5, D8.

### Scores

| Dimension | Score | Why |
|---|---|---|
| D1 Public money answers | 1 | Capped by findings 3 and 4. Otherwise 4: every reader got the spending and tax questions right. |
| D2 Life: breadth and depth | 4 | No finding against it. Not 5: the phone test failed. |
| D3 Life: choosing and comparing | 1 | Capped by finding 2 (the comparison page calls a change across breaks "same method"). Readers also struggled to pick a year (R4, R5). |
| D4 Explanation and understanding | 3 | All three informal readers nearly misread the lowest fifth paying 36.7% against the highest's 36.2% on the home card, and "Who pays" versus "Tax and income" sent four phone readers to the wrong page. Torn between 3 and 4, so 3. |
| D5 Visual design and charts | 1 | Capped by finding 6. Readers also noted overlapping "Coding change" labels on earnings. |
| D6 Phone experience | 4 | No page scrolls sideways, pages stay under 8.8 screens. Not 5: readers ran out of actions on the year-by-year hub and the 18-screen glossary. |
| D7 Accuracy and traceability | 1 | Capped by finding 1. The other 29 claims matched their records and source files. |
| D8 Impartiality | 1 | Capped by findings 2, 5 and 6. Group order, shared scales, zero-based bars and start years all follow the rule. |
| D9 Accessibility and no JavaScript | 5 | Screen-reader reader 12/12 with no blocking barrier, no keyboard traps, every chart has a text summary; axe in CI. |
| D10 Honesty about limits | 1 | Capped by findings 1 to 4: changes shown across breaks and a partial year shown as a full one. |
| D11 Reader evidence | 2 | Informal check and phone test recorded. Not 3 until the problems the readers found are fixed; not 5 until the phone test passes. |
| **Total** | **24 / 55** | |

### Gaps, most valuable first

Written from the findings and the readers' confusion notes only.

1. Stop working out pay changes across the 2011 and 2021 coding breaks on the earnings page and the comparison pages (headline "about the same as 2008", 2006 to 2025, percentiles, nations and regions), or show each as two separate same-method changes.
2. On the spending areas page, stop comparing 2003-04 with 2025-26 across the education student-loan and Network Rail breaks, or show those areas' changes only within same-basis years.
3. On the tax history page, stop working out 1948-49 to 2022-23 changes in each tax's share across the breaks the page marks, including the percentage-point bar chart.
4. Mark 2020 holiday visits as a partial year (survey stopped 16 March) wherever it appears (holidays headline, chart title and data, per 100 residents, life hub sparkline), not as the full-year low.
5. Say in the caption of every line chart whose axis starts above zero that it does (spending share of GDP, earnings, work, and their nation and region panels), and add a check so new ones cannot miss it.
6. Replace the household tax page's own explanation of why the lowest fifth pays a high share with an attributed ONS explanation, drop "the largest share" for a 0.5-point gap, and say on the home card in one plain line that the lowest fifth's share is mostly indirect tax such as VAT.
7. Make the household tax answer easy to find from "Who pays" (four phone readers looked there first), and give the year-by-year hub and the glossary a way to jump straight to a topic, year or term.
8. Fix the smaller points readers and the fact-checker raised: overlapping "Coding change" labels and unexplained "coding change" and "CPIH" on earnings; the home card's "£33 of every £100 spent on services" base and debt interest inside "general public services"; "Every topic has figures from 2008" (holidays start in 2009); "State pensions alone"; the two dates for the top-income adjustment; the mixed periods on the work page; and a "not anyone's bill" note on debt per household.

John's questions (copied from the probes):

- J1.3: The site has no international comparison of government debt, so it cannot say how UK debt as a share of GDP compares with the other G7 countries and the OECD average.
- J1.4: The international page ranks the UK among all 38 OECD countries but never picks out the G7 (major economies), so a reader has to find six countries in two long bar lists to answer 'compared with other major nations'.
- J1.5: The site does not show government borrowing costs (10-year government bond yields) for the UK beside the other G7 countries, or how they have changed over time.
- J1.6: The site does not compare the UK's debt interest payments, as a share of GDP or of revenue, with other G7 countries.
- J1.7: The site does not explain, in neutral terms with official sources, what moves government bond yields (central bank rates, expected inflation, the amount borrowed, investors' view of risk), so a reader could take a yield gap as a simple verdict on how a country is run.

### What these results cannot prove

As the rubric says: Claude is not a newcomer; five profiles from one model are
not five people; screenshots are not a phone in the hand; an accessibility
tree is not VoiceOver or TalkBack; and AI reviewers are not independent people.

---

## Audit 8: 2 November 2026 (confirming re-score after PRs #118 and #119)

- Commit audited: `fded452` on `main` (after #118 chart titles that name
  every big rise and fall, with a check, and #119 topic pages, taxes and the
  default comparison shortened to about 8 phone screens).
- Rubric: [goal-rubric.md](goal-rubric.md), strict reading as in Audits 4 to
  7. Level 5 needs real readers, so 4 is the highest any dimension can reach
  until people test the site.
- How it was checked: a fresh build (1,762 pages, 5,851 CSV downloads, every
  chart and table still has one); `make check` (174,539 numbers re-read, 50
  finding-led headings, 12 trend headings checked against every big rise and
  fall of their line) and the 124 unit tests pass; 18 pages measured at
  360 × 640 with and without JavaScript; every chart title on the money
  pages, the life hub and each topic page read against the chart's own CSV,
  including the two titles Audit 7 found misleading. CI (build and checks,
  including `make a11y` with the new screen limits) and the "Live site
  matches main" check are both green for `fded452`.
- Who scored it: a Claude session that did not build the site.

**Total: 40 out of 55** on both the strict and lenient readings. Audit 7: 37
strict, 40 lenient. Target: at least 49, every dimension at least 4, and the
phone test passed. Not met, and no longer reachable by building alone.

Both gaps from Audit 7 are closed:

- Chart titles (#118). The holiday visits title now reads "rose until 2019,
  fell in 2020, then rose back to about the 2019 level" (41.2 million in 2009,
  58.7 million in 2019, 4.4 million in 2020, 58.4 million in 2025), and the
  spending share of GDP title reads "rose until 2009-10, fell until 2018-19,
  rose until 2020-21, then fell back part of the way" (46.0%, 39.1%, 52.3%,
  44.3%). Both match their CSVs. Visits per 100 residents now names the
  2020-21 fall. A check fails the build if a trend title leaves out a big
  move, and the fix is logged on the corrections page.
- Page length (#119). Measured with JavaScript off: work 7.7, earnings 7.7,
  housing 8.4, holidays 8.4, class sizes 8.0, taxes 8.2, the default 2009 vs
  2023 comparison 8.3 screens (were 10.0 to 11.3). Spending 7.8, who pays
  7.9, household tax 7.7, life hub 8.2, home 8.1, OECD 8.7. CI holds them
  under 8.5 or 8.8. No page scrolls sideways. The comparison page still
  carries the "not comparable: definition changed" wording that user-test
  question 10 relies on.

| Dimension | Strict | Lenient | Why |
|---|---|---|---|
| D1 Public money answers | 4 | 4 | Unchanged from Audit 7. Not 5: no reader evidence. |
| D2 Life: breadth and depth | 4 | 4 | Unchanged. The charts #119 moved into folds are still on the page and in the CSVs. Not 5: no reader evidence; housing costs and space are England only. |
| D3 Life: choosing and comparing | 4 | 4 | The default comparison is now 8.3 screens instead of 10.5, with the lead figures and the longer run in view and the rest in folds. Not 5: no reader evidence. |
| D4 Explanation and understanding | 4 | 4 | The two titles that taught the wrong trend are fixed. Not 5: no evidence that a newcomer can explain a point back. |
| D5 Visual design and charts | 4 | 4 | Up from 1 strict. No chart title misstates its line: every trend title on the key pages was read against its CSV, and CI now checks it. Some multi-turn titles are long (the housing rent and mortgage title is 31 words), which is a readability point, not a misleading one. Not 5: no reader evidence. |
| D6 Phone experience | 4 | 4 | Every page Audit 7 named is now 7.7 to 8.4 screens and held there by CI. Not 5: nothing measures "answer in under a minute" with real people. |
| D7 Accuracy and traceability | 4 | 4 | Unchanged (50 of 50 random figures match the publishers' files, #110). Not 5: no review by a person outside the project. |
| D8 Impartiality | 4 | 4 | The spending share title no longer hides the 2010s fall, which was Audit 7's one impartiality risk. Not 5: no outside review. |
| D9 Accessibility and no JavaScript | 4 | 4 | Unchanged. Known and recorded trade-off: one figure's source panel opens by tap or click only; keyboard users reach the same record through each section's Sources line (benchmark-comparison.md, item 4; neither benchmark has the feature). Not 5: no VoiceOver or TalkBack test by a person. |
| D10 Honesty about limits | 4 | 4 | Unchanged. Not 5: no outside review. |
| D11 Reader evidence | 0 | 0 | Nobody has used the site in a test. |
| **Total** | **40 / 55** | **40 / 55** | |

### Gaps that a worker can do

None that move the score. Every dimension except D11 is at 4, the most the
rubric allows without real readers. Optional polish that would not change a
score: shorter wording for the longest multi-turn chart titles (housing costs,
classes over 30), and a keyboard way to open one figure's source panel.

### Human-only steps (all that remain)

1. A quick informal test with two or three people on phones (D11 to 2).
2. The five-person phone test with the pack in `docs/user-test/` (D11 to 5;
   required for the goal).
3. A VoiceOver (iPhone) and TalkBack (Android) test (D9 to 5).
4. A review of accuracy and impartiality by a person outside the project (D7,
   D8, D10 to 5).

Reaching 49 needs D11 at 5 (45) and at least four other dimensions at 5,
which these steps make possible: for example D7, D8, D9 and D10.

---

## Audit 7: 2 November 2026 (strict re-score after PRs #110 to #116)

- Commit audited: `871f814` on `main` (after #110 a 50-figure random accuracy
  check against the publishers' own files, #111 shorter phone pages and a
  split Sources page, #112 chart titles that state the finding and summaries
  that describe the trend, #113 an accessibility side-by-side with GOV.UK and
  ONS and its fixes, #114 large classes, infant and key stage 2 class sizes,
  and holiday spending and nights abroad, #115 longer-run context beside each
  headline change on comparison pages, #116 UK tax and spending against every
  OECD country).
- Rubric: [goal-rubric.md](goal-rubric.md). Strict reading, as in Audits 4 to
  6: a dimension reaches 4 only with a recorded side-by-side comparison with a
  named benchmark page ([benchmark-comparison.md](benchmark-comparison.md)) or
  a recorded check, and a page that is in fact comparable. Level 5 needs real
  readers, so 4 is the highest any dimension can reach until people test the
  site.
- How it was checked: a fresh build (1,762 pages, 6,573 CSV files); 27 pages
  measured at 360 × 640 with and without JavaScript (page length, sideways
  scrolling, where the first chart starts, words); the home page, all money
  pages, the new OECD page, the life hub, every topic page and the default
  2009 vs 2023 comparison read in full; the OECD ranking counted by hand ("21
  of 36 countries collected a larger share"); every finding-led chart title on
  the key pages checked against the chart's own CSV. CI (build and checks) was
  green for #113; for `871f814` it and the live-site check were still running
  when this was written (this container cannot reach the live site).
- Who scored it: a Claude session that did not build the site.

**Total: 37 out of 55** on the strict reading (40 lenient). Audit 6: 36
strict, 39 lenient. Target: at least 49, every dimension at least 4, and the
phone test passed. Not met.

All seven gaps from Audit 6 were closed. Every dimension except D11 now
reaches 4 on the lenient reading, which is the most the site can score
without real readers. One problem holds the strict total back: the rule that
writes chart titles describes a line with only one turning point, so two
titles state a trend the data does not show. That is a misleading chart under
the rubric, which caps D5 at 1 until it is fixed.

**Misleading chart titles found (D5 capped at 1 until fixed):**

- Holidays: "Holiday visits abroad by UK residents fell until 2020, then rose
  above the 2009 level". The chart's own figures rose from 41.2 million (2009)
  to 58.7 million (2019) before the 2020 fall to 4.4 million. A reader asked
  "did holidays abroad rise or fall in the 2010s?" would answer wrongly from
  the title. The "in words" summary has the same shape ("fell from 41.2
  million in 2009 to a low of 4.4 million in 2020"), with the 2019 high only
  in a side note.
- Spending: "As a share of GDP, total public spending rose until 2020-21, then
  fell back part of the way". The share fell from 46.0% (2009-10) to 39.1%
  (2018-19 and 2019-20) before rising to 52.3% in 2020-21. Hiding a ten-year
  fall in a contested period is also an impartiality risk, though the rule is
  applied the same way to every chart and is not partisan.
- Cause: `builder/findings.py` `shape()` picks either a peak or a low and
  ignores any other large move. The same rule gives the weaker "Visits abroad
  per 100 residents rose between 1980 and 2023" (true, but silent about the
  2020-21 fall to 29). Other titles on the key pages were checked and match
  their data.

| Dimension | Strict | Lenient | Why |
|---|---|---|---|
| D1 Public money answers | 4 | 4 | The last benchmark gap is closed: a new page puts UK tax (34.4% of GDP in 2024, OECD average 34.1%) and spending (46.2%, average 44.5%) beside every OECD country, over time from 1965, and by kind of tax and area of spending, with missing countries named (#116). Per person, per household, long history, attributed explanations, the cash / after inflation / share of GDP switch and several kinds of group were already in place. Not 5: no reader evidence. |
| D2 Life: breadth and depth | 4 | 4 | Class sizes now have the share in classes over 30 from 2006 and infant and key stage 2 figures (#114); holidays have spending, spending per visit after inflation and nights per visit from 2009 (#114). Not 5: no reader evidence; housing costs and space are England only; no local-area detail. |
| D3 Life: choosing and comparing | 4 | 4 | Each lead change on a comparison page now has the longer run beside it (first to latest year on the same method, lowest and highest year, link to every year) (#115), which was the ONS feature it lacked. Not 5: no reader evidence; the default comparison is 10.5 phone screens. |
| D4 Explanation and understanding | 4 | 4 | Up from 3. Every reason Audit 6 held it back is fixed: titles state findings (#112), the four long money and hub pages are about 8 screens (#111), and big numbers now have international context (#116); the Full Fact side-by-side (#103) is the recorded comparison. Not 5: no evidence that a newcomer can explain a point back; the two misleading titles above also teach the wrong trend until fixed. |
| D5 Visual design and charts | 1 | 4 | Lenient 4: finding-led titles and trend summaries (#112), a chart within about two screens on every key page (0.9 to 2.0 measured), a CSV beside every chart. Strict 1: two titles misstate the trend of their own chart (see above), and the rubric caps a dimension with a misleading chart at 1 until it is fixed. |
| D6 Phone experience | 4 | 4 | Up from 3. The four pages Audit 6 named are now 8.0 to 8.2 screens (spending 8.1, who pays 8.2, household tax 8.0, life hub 8.2) and CI keeps them there (#111); Sources is 2.8 screens instead of 118; no page scrolls sideways with or without JavaScript; the OBR and ONS phone side-by-side (#103) found the site shorter in words. Not 5: topic pages are 10 to 11.3 screens (holidays 11.0 and class sizes 11.3 grew with #114), taxes 10.2, the default comparison 10.5; nothing measures "answer in under a minute". |
| D7 Accuracy and traceability | 4 | 4 | Up from 3. A recorded random-sample check traced 50 figures (40 random from 9,723 shown, 10 from headline pages; 94 input cells from 29 sources) to fresh downloads from the publishers, with a checker that imports nothing from the builder: 50 of 50 match, and the one problem found (occupation sources linking to the wrong Nomis slice) was fixed and logged (#110). Not 5: no review by a person outside the project. |
| D8 Impartiality | 4 | 4 | Unchanged. The OECD page ranks every country by value with the UK and the average marked, and calls the average "not a country". The spending-share title above hides a ten-year fall; it is counted under D5, and does not look partisan because the same rule writes every title, but it should be fixed. Not 5: no outside review. |
| D9 Accessibility and no JavaScript | 4 | 4 | Up from 3. The GOV.UK and ONS side-by-side (#113) measured keyboard stops, focus styles, skip links, chart accessibility trees and tap targets on 10 pages against 6 benchmark pages: comparable or ahead on each, with the problems found fixed and kept by CI; chart summaries now describe the trend (#112). Not 5: no VoiceOver or TalkBack test by a person. |
| D10 Honesty about limits | 4 | 4 | Unchanged. New figures keep the 2024 travel method change and the 2020 gap visible, and the OECD page names missing countries and explains that the early average covers fewer countries. Not 5: no outside review; margins are shown for pay and holidays abroad but not for most other survey figures. |
| D11 Reader evidence | 0 | 0 | Nobody has used the site in a test. |
| **Total** | **37 / 55** | **40 / 55** | |

### Gaps that a worker can do

1. Fix the chart-title and "in words" rule in `builder/findings.py` so a line with more than one large turn is described by all of them (for example "rose until 2019, fell sharply in 2020, then rose again"), correct the holiday visits and spending share-of-GDP titles, and add a check that fails when a title omits a move of at least 30% of the line's range (D5, D4, D8).
2. Bring the topic pages (work 10.1, earnings 10.3, housing 10.0, holidays 11.0, class sizes 11.3 screens), taxes (10.2) and the default comparison (10.5) to about 8 phone screens folded, and add them to the CI screen limits (D6).

Once gap 1 is fixed, every dimension except D11 is at 4, the most possible
without real readers. The remaining distance to 49 is only reachable through
the human-only steps below.

### Human-only steps (unchanged)

1. A quick informal test with two or three people on phones (D11 to 2).
2. The five-person phone test with the pack in `docs/user-test/` (D11 to 5; required for the goal).
3. A VoiceOver (iPhone) and TalkBack (Android) test (D9 to 5).
4. A review of accuracy and impartiality by a person outside the project (D7, D8, D10 to 5).

---

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
