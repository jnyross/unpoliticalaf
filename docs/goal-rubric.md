# Goal rubric

This is the rubric every goal audit uses. Results go in
[goal-scorecard.md](goal-scorecard.md).

It replaces the checklist used in Audit 1. That checklist asked whether each
feature existed. Almost everything existed, so almost everything scored "met",
even though the site is still a plain set of text pages and tables. This rubric
asks how good each part is compared with the best public explainers, and
whether readers actually understand it.

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
| 5 | Best in class. Better than the benchmarks for a newcomer on a phone, and real readers have shown they understand it. |

Caps that apply whatever the page looks like:

- No dimension scores above 3 on the auditor's own judgement alone. Level 4 needs
  a recorded independent review of that dimension or a recorded side-by-side
  comparison with a named benchmark page.
- Level 5 needs evidence from real readers (the five-person phone test, or a
  recorded smaller test with real people).
- Any material factual error, misleading chart or partisan framing found
  anywhere caps that dimension at 1 until it is fixed.

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
- **5:** As 3, and an independent review has checked a sample of figures and
  every headline claim against the original publications, each figure can be
  traced from the page in one or two taps, and corrections are logged publicly.

### D8. Impartiality

- **3:** Neutral wording, no party or policy judgement, and fixed or explained
  choices of years and measures.
- **5:** As 3, and an independent review has checked headline choices, framing,
  chart scales and ordering for bias, and the site explains how it chooses what
  to show.

### D9. Accessibility and working without JavaScript

- **3:** Zero automated WCAG 2.2 AA failures at 360px and 1100px with sections
  expanded, and the core answers and comparisons work without JavaScript.
- **5:** As 3, and a manual keyboard and screen-reader test (VoiceOver on iOS
  and TalkBack on Android) has found no blockers, and every chart has a useful
  text summary, not only a table.

### D10. Honesty about limits and continuity

- **3:** Missing years stay missing, breaks are marked, illustrations are
  labelled, and no change is shown across a break.
- **5:** As 3, and each limit is explained where it matters in one plain
  sentence, with the size of uncertainty (for example survey confidence
  intervals or revisions) shown for headline survey figures.

### D11. Reader evidence

- **0:** No reader testing.
- **2:** Informal tests with a few people, recorded.
- **3:** A recorded test with real people using the goal's 12-question task set,
  with problems fixed.
- **5:** The goal's five-person phone test passed: at least 48/60, each person
  at least 9/12 within eight minutes, and all three critical questions right.

## Target

The goal is met when all of these are true on the same live commit:

- Every dimension scores at least 4, and the total is at least 49 out of 55.
- D11 scores 5 (the five-person phone test has passed).
- Independent accuracy, impartiality, accessibility and reproducibility reviews
  have no unresolved material findings.

## Writing gaps

After scoring, list the gaps that would raise the lowest scores most, each in
one sentence, most valuable first. Each gap should be a piece of work one
worker can finish.
