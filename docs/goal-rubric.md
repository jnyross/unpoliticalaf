# Goal rubric (v3)

This is the rubric every goal audit uses. Results go in
[goal-scorecard.md](goal-scorecard.md). John approved v3 on 3 November 2026
([proposal](https://claude.ai/artifact/JMSoMh3zknfmPNcA7nVcbT)).

**What changed from v2.** The eleven dimensions and the 0 to 5 scale are the
same. v2 locked 15 of the 55 points behind four steps only people could do (an
informal phone check, the five-person phone test, a VoiceOver and TalkBack
test, and an outside review). v3 gives each of those steps an automated
stand-in, run by fresh Claude sessions, so audits can reach the target without
waiting for people. How to run the stand-ins is in
[standins/README.md](standins/README.md).

A result reached with the stand-ins is recorded as **"met (simulated)"**. That
is not the goal's own definition of success, which asks for five consenting UK
adults and outside checks, and it must never be presented publicly as that.

## How to score

Score each of the eleven dimensions from 0 to 5 using the descriptions below.
Pick the highest level whose description is fully true. If you are torn between
two levels, pick the lower one.

| Level | Meaning |
|---|---|
| 0 | Missing. |
| 1 | Present but broken, misleading or too thin to answer the question. |
| 2 | Works and is correct, but basic: a reader has to work hard, and a good public explainer would do clearly better. |
| 3 | Good. A newcomer can get the answer on a phone without help. Clearly behind the best benchmark in depth, design or clarity. |
| 4 | Very good. Comparable with the benchmarks below in depth and craft, with independent evidence for the claims it makes. |
| 5 | Best in class. Better than the benchmarks for a newcomer on a phone, and readers have shown they understand it. |

Evidence each level needs, whatever the page looks like:

- **Level 4** needs a recorded review of that dimension by a fresh Claude
  session that did not build the site, or a recorded side-by-side comparison
  with a named benchmark page ([benchmark-comparison.md](benchmark-comparison.md)).
  The auditor's own judgement alone stops at 3.
- **Level 5** needs that dimension's stand-in (table below) to have passed on
  the audited commit, with its evidence saved in the repository under
  `docs/standins/audits/`. Dimensions without their own stand-in (D1 to D6)
  need the reader stand-ins (the simulated phone test, the new-question test
  and the prior-knowledge check) to have passed, plus no reader confusion note
  about that dimension left unfixed.
- **Caps stay.** Any material factual error, misleading chart or partisan
  framing found anywhere, by the auditor or any stand-in, caps that dimension
  at 1 until it is fixed.

### Stand-ins

Each stand-in is a fresh Claude session that did not build the site and never
sees the code, the answer key or the other stand-ins' results. Where possible
the readers run on a smaller, less capable model than the reviewers, so they
behave more like a hurried newcomer than an expert.

| Human step in v2 | Stand-in | Pass bar | Counts for |
|---|---|---|---|
| Informal phone check | 3 simulated newcomers browse the site at 360 × 640 and write down what confused them. | Notes recorded; anything that blocks an answer is fixed. | D11 level 2 |
| Five-person phone test | 5 simulated readers, each with a different newcomer profile, answer the 12 questions in [user-test/](user-test/). They see only screenshots of the audited build in a 360 × 640 phone browser, can only tap, scroll and pick from lists, and get 40 actions (about 8 minutes). | The goal's own bar: at least 48 of 60, each at least 9 of 12 within the 40 actions, all three critical questions right. | D11 level 5, D1 to D6 level 5 |
| Same test, new questions | A separate session writes 24 new questions from the goal text alone, without seeing the site. Their hash is committed (sealed) before the readers start. The same 5 readers answer them. | At least 80% right. Stops the site being tuned to the 12 known questions. | D11 level 5, D1 to D6 level 5 |
| John's questions | John's own questions the site must answer, in [johns-questions/](johns-questions/). Each is tested by multiple-choice probes. The same 5 readers answer the probes the site already covers, with a fresh 40 actions, and first without the site. | Every probe has its answer on the site, and on each probe at least 4 of the 5 readers are right with the site. | Target (below); a failed probe is a gap |
| Prior-knowledge check | The same readers answer every question first without the site. | The group scores at least 20 of 60 higher on the 12 questions with the site than without it. Questions they get right without the site are not evidence. | D11 level 5, D1 to D6 level 5 |
| VoiceOver and TalkBack test | A reader gets only what a screen reader would announce (the accessibility tree in reading order) and answers the 12 questions. Automated checks: axe-core on every page at 360 px and 1100 px (`make a11y`), keyboard-trap check, chart text summaries. | 9 of 12 and all critical questions right within 40 actions, zero axe failures, no keyboard traps, every chart has a text summary. | D9 level 5 |
| Outside accuracy review | An adversarial fact-checker picks 30 headline claims from the rendered pages and traces each to the publisher's own file through the "Accuracy check" workflow. | No material errors. | D7 level 5, D10 level 5 (with the impartiality stand-in) |
| Outside impartiality review | Two red-team critics, one arguing the site leans left and one right, each list their strongest examples. A third neutral judge rules on each. Start years, chart scales and ordering are checked against the written rule in [standins/impartiality-rule.md](standins/impartiality-rule.md). | No upheld material finding left open. | D8 level 5, D10 level 5 (with the accuracy stand-in) |

**People tests are optional and override.** If the real five-person phone test
([user-test/](user-test/)) is ever run, or a person outside the project reviews
accuracy, impartiality or accessibility, that result replaces the stand-in for
the dimensions it covers, in either direction. A failed human test drops those
dimensions back and reopens the goal.

**Guarding against gaming.** Workers fixing the site may not see the readers'
answers, the new question set or the answer key's reasoning beyond what is
already public in `docs/user-test/`. They get only the readers' confusion notes
and the reviewers' findings. The new questions are written again for every
audit, and the reader profiles are drawn again too.

### Benchmarks

Compare against what these do well, not their exact style. Do not copy them.

- **USAFacts** (government money and life statistics, non-partisan, for newcomers).
- **Our World in Data** (charts, explorers, explaining definitions and gaps).
- **IFS TaxLab** and the **OBR "Brief guide to the public finances"** (tax and spending explainers).
- **ONS** articles and interactive tools, such as its personal inflation and household income tools.
- **Full Fact** (neutral, plain-English explanation of disputed numbers).

## Dimensions

Each dimension lists what level 3 and level 5 look like. Levels in between are
judged against those two.

### D1. Public money answers (the four questions)

- **3:** Each question has a correct headline answer, a clear chart, a full
  table, history, and its limits.
- **5:** Each answer also gives the scale people can relate to (per person, per
  household, per £100 of tax), shows how the mix changed over a long period,
  explains the big moves with attributed official explanations, lets the reader
  move between cash, real terms and share of GDP, and shows who pays across
  several kinds of group (income, age, retired or working, household type) where
  official data exists.

### D2. Everyday life: breadth and depth of evidence

- **3:** All five topics are covered with their core measure every year, with
  gaps and breaks shown.
- **5:** Each topic answers every part of the goal (for example housing tenure,
  costs and space; holidays by kind, place and frequency, at home and abroad),
  with several measures, the most useful group splits (age, sex, region or
  nation, income, tenure) and the longest reliable history, and covers all four
  UK nations or says clearly where data is for one nation only.

### D3. Everyday life: choosing a year and comparing periods

- **3:** A reader can pick any year and any two years without JavaScript, and
  changes are not calculated across breaks.
- **5:** Comparing two periods leads with the biggest changes in plain words,
  shows them visually, works comfortably one-handed on a phone, lets the reader
  compare ranges as well as single years, and explains each "not comparable"
  in one sentence where it appears.

### D4. Explanation and understanding

- **3:** Key terms are explained where they first appear, and the three easy
  mistakes (household averages versus personal tax rates versus shares of
  revenue; illustrations versus statistics; change versus cause) are warned
  about.
- **5:** Every page teaches: it starts with a question a newcomer would ask,
  builds understanding in short steps, gives context for big numbers, has a
  glossary, and a newcomer can explain the main point back in their own words.

### D5. Visual design and charts

- **3:** Clean, consistent and restrained, with charts that are readable on a
  phone and a full table beside each one.
- **5:** Charts are chosen for the question, directly labelled and annotated
  with the important events and breaks, readable at 360px without zooming, and
  the page has a clear visual hierarchy that makes the answer obvious at a
  glance, while keeping the white-and-grey, neutral treatment.

### D6. Phone experience and navigation

- **3:** Every page works at 360px without sideways scrolling, and navigation
  reaches every section.
- **5:** Pages are short enough to scan, with in-page navigation, sticky
  context where it helps, comfortable tap targets, fast loading on a slow
  connection, and a reader can answer a typical question in under a minute.

### D7. Accuracy and traceability

- **3:** Every figure is traced to an official file and cell, and an automated
  check re-reads them on every build.
- **5:** As 3, and an independent review (in v3, the fact-checker stand-in)
  has checked a sample of figures and every headline claim against the
  original publications, each figure can be
  traced from the page in one or two taps, and corrections are logged publicly.

### D8. Impartiality

- **3:** Neutral wording, no party or policy judgement, and fixed or explained
  choices of years and measures.
- **5:** As 3, and an independent review (in v3, the red-team critics and
  judge) has checked headline choices, framing,
  chart scales and ordering for bias, and the site explains how it chooses what
  to show.

### D9. Accessibility and working without JavaScript

- **3:** Zero automated WCAG 2.2 AA failures at 360px and 1100px with sections
  expanded, and the core answers and comparisons work without JavaScript.
- **5:** As 3, and a keyboard and screen-reader test (in v3, the
  screen-reader stand-in and keyboard-trap check; VoiceOver and TalkBack by a
  person override it) has found no blockers, and every chart has a useful
  text summary, not only a table.

### D10. Honesty about limits and continuity

- **3:** Missing years stay missing, breaks are marked, illustrations are
  labelled, and no change is shown across a break.
- **5:** As 3, and each limit is explained where it matters in one plain
  sentence, with the size of uncertainty (for example survey confidence
  intervals or revisions) shown for headline survey figures.

### D11. Reader evidence

- **0:** No reader testing.
- **2:** The informal stand-in (3 simulated newcomers) has run and its notes are
  recorded, or informal tests with a few people are recorded.
- **3:** A recorded run of the simulated phone test with the 12 questions, with
  the problems it found fixed.
- **5:** On the audited commit, the simulated phone test passed on the goal's
  bar (at least 48 of 60, each reader at least 9 of 12 within 40 actions, all
  three critical questions right), the new-question test passed (at least 80%)
  and the prior-knowledge check passed (at least 20 of 60 higher with the
  site). `python scripts/standins.py score AUDIT_DIR` applies these bars. A
  real five-person phone test, if run, replaces this in either direction.

## Target

The goal is **met (simulated)** when all of these are true on the same live
commit:

- Every dimension scores at least 4, and the total is at least 49 out of 55.
- D11 scores 5.
- Every one of John's questions passes ([johns-questions/](johns-questions/)):
  no probe is still open, and the readers answer each probe as above.
- No stand-in has an open material finding (accuracy, impartiality,
  accessibility or reader confusion that blocks an answer), and the build is
  reproducible (`make verify` passes and the "Live site matches main" check is
  green for that commit).

It becomes **met** in the goal's own sense only when the real five-person phone
test has passed and people outside the project have reviewed accuracy,
impartiality and accessibility with no unresolved material findings.

## What the stand-ins cannot prove

A pass under v3 means the site is clear and correct to a careful AI reader. It
does not prove that real newcomers understand it. Record these limits with
every "met (simulated)" result:

- **Claude is not a newcomer.** It reads every word, never gets bored, and
  already knows a lot about UK tax and spending. The prior-knowledge check
  removes some of this, not all.
- **Five profiles are not five people.** Simulated readers from the same model
  make the same mistakes together.
- **Screenshots are not a phone in the hand.** They miss small text, thumb
  reach, slow mobile data and real browser quirks.
- **An accessibility tree is not VoiceOver or TalkBack.** Real screen readers
  announce things differently and use gestures.
- **AI reviewers are not independent people.** The fact-checker and critics
  come from the same family of model that built the site and can share its
  blind spots.

## UX heuristic checks

Added by T128 on 4 November 2026, at John's request. They test the five product
principles John set for the interface: clarity and simplicity, consistency,
feedback and responsiveness, accessibility and inclusivity, and user control
and error prevention. They are **checks, not dimensions**. They do not change
the eleven dimensions, the 55-point total or the target. Each audit runs them
with `python scripts/ux_heuristics.py` (`--all` checks every page; the default
is a fixed sample of about 115 pages) and records the result in its scorecard
section. Items marked *judged* need a reviewer's reading and cannot be measured.

A check passes when no sampled page fails it. The standards and thresholds are
the ones in `scripts/ux_heuristics.py`, measured at 360 × 640 unless noted.
Changing a threshold is a rubric change and needs John's approval.

| Check | Standard |
|---|---|
| **1. Clarity and simplicity** | |
| C1 | One h1, within 200px of the top. |
| C2 | Heading levels never skip. |
| C3 | The first answer starts within two phone screens (1,280px). |
| C4 | No link reads only "here", "more" or similar. |
| C5 *judged* | Each page's visual hierarchy makes the answer the first thing read, with no decoration that does not help a newcomer. |
| **2. Consistency** | |
| K1 | Every page has the same main navigation (compared without relative paths). |
| K2 | Every page has a footer and a link home. |
| K3 *judged* | The same thing has the same name everywhere (navigation, page titles and charts). |
| **3. Feedback and responsiveness** | |
| F1 | Every closed section has a specific label and a visible marker. |
| F2 | A tap on the first visible chart with a readout updates the readout. Pages whose charts are all in closed sections are not tested. |
| F3 *judged* | Each action gives a visible result. The site loads no data after the page opens, so it needs no loading states. |
| **4. Accessibility and inclusivity** | |
| A1 | Every select and input has a label. |
| A2 | No sideways scrolling at 360px. |
| A3 | Paragraphs and list items are at least 16px. |
| A3b | Table cells, labels, captions and source lines are at least 13px. |
| A4 | Chart labels are at least 12px as drawn at 360px, after the SVG scale. |
| A5 | Contrast, focus style, Tab order and tap targets: `make a11y` passes (axe-core, the Tab walk and 24px targets). |
| **5. User control and error prevention** | |
| U1 | Pages taller than two screens have a back-to-top link. |
| U2 | Every form has a labelled control and a submit button, and uses GET, so the year picks work without JavaScript. |
| U3 | The h1 and the first answer show with JavaScript turned off. |
| U4 *judged* | Nothing on the site deletes or changes data, so no confirmation step is needed. Any future action that does must have a confirmation and an undo. |

A failed check is a gap, written in one sentence like any other gap, and it
is fixed in the same way: a worker changes the site, and the next audit runs the
checks again on the new build.

## Writing gaps

After scoring, list the gaps that would raise the lowest scores most, each in
one sentence, most valuable first. Each gap should be a piece of work one
worker can finish. A gap from a reader stand-in is written from the readers'
confusion notes only, never from their answers or the new questions.

John's questions are the exception, because John has asked for the site to
be tested against them openly. Every open probe and every probe the readers
failed is a gap, listed by `python scripts/standins.py score AUDIT_DIR` (or
`python scripts/johns_questions.py gaps` for the open ones). Copy each
probe's gap sentence as written. A worker who closes one takes the answer
from the official source, adds it to the probe in
`docs/johns-questions/questions.json`, and the next audit tests it.
