# Independent review: accuracy, impartiality, accessibility, reproducibility

- Date: 2 November 2026
- Commit reviewed: `b3dd569` on `main` (after PRs #81 to #85).
- Reviewer: a separate Claude session that did not build any part of the site. It
  used its own scripts (not the site's `builder/` code) to re-read source files,
  recalculate figures and run accessibility tests.
- Standard: [goal-rubric.md](goal-rubric.md). The new score is in
  [goal-scorecard.md](goal-scorecard.md) (Audit 3).

**How independent is this?** The reviewer is independent of the build process, but
it is the same kind of AI agent that built the site. It meets the rubric's wording
("a recorded independent review") but not the full spirit of the goal's
"independent checks". Before the goal is declared met, a person outside the
project should repeat the accuracy and impartiality checks, and someone should
test the site with VoiceOver and TalkBack on real phones.

## Summary

| Area | Result | Material findings open |
|---|---|---|
| Accuracy | No factual errors found. 68 of 68 source files match their recorded SHA-256. 40 randomly sampled figures read the right row and column. All 2,009 derived figures recomputed independently with 0 mismatches. Headline claims checked against the source tables. | None |
| Impartiality | Wording is neutral. One headline lacked context, one sentence stated a cause in the site's own words, and one word ("fairest") made a judgement. All three fixed. | None |
| Accessibility | One WCAG 2.2 AA failure (tap targets in folded source lists), hidden because the site's own check never opened folded sections. Fixed, and the check now opens them and runs in CI. Keyboard and no-JavaScript paths work. No screen-reader test was possible. | Screen-reader test not done (human step) |
| Reproducibility | A fresh clone builds and passes every check. Two builds give byte-identical output (253 files). | None |

## 1. Accuracy

What was checked:

1. **Source files.** Every file listed in `site/data/facts.json` exists and its
   SHA-256 matches the recorded hash (68 of 68).
2. **Right cell, not only the same number.** The site's own check confirms each
   figure equals the value in its recorded cell. That cannot catch a figure read
   from the wrong row or column. For 40 random figures, the reviewer opened the
   cell with pandas and read the row label and column header around it. All 40
   were the measure, group and year the site says they are (for example
   `hmrc.income.top50.2012 to 2013` is the "Top 50% percentile group" column of the
   "2012 to 2013" row; `etb.t16.ret.1996/97` is "Retired individuals (%)" for
   1996/97).
3. **Derived figures.** All 2,044 calculated figures were recomputed from their
   formula and inputs by a separate script. 2,009 matched to within 1 part in a
   million, none differed, and 35 have prose formulas (for example "sum of the
   named taxes") that the script could not evaluate. The site's own check covers
   those.
4. **Headline claims against the publications' own tables.**
   - Top 1% paid 27.2% of Income Tax in 2023-24 and had 12.4% of income: HMRC
     Table 2.4, row "2023 to 2024". 2024-25 onwards are HMRC projections and are
     labelled as such.
   - 53.3% of people lived in households receiving more in benefits than they
     paid in taxes in 2023/24; 90.1% retired, 45.8% non-retired; 37.0% in 1977:
     ONS ETB Table 16, all match.
   - The site's definition of a retired household matches the ETB "Notes" sheet
     (more than 50% of income from people who are retired and over 50, or
     sick/injured and over State Pension age).
   - Receipts 42.9% and spending 38.6% of GDP in 1948-49 are consistent with the
     OBR's net borrowing of -4.3% of GDP that year (a surplus).
   - The worked example (employee on £30,000, 2026-27) recalculates: Income Tax
     £3,486, National Insurance £1,393, total £4,879, 16% average and 28%
     marginal.
   - The £1,360bn (PESA) and £1,366bn (OBR) totals differ, and both pages explain
     why.
5. **Quotes.** The build already matches all 23 quoted explanations word for word
   against stored copies of the publications.

Not done: the reviewer could not download the original publications from ONS,
GOV.UK or the OBR in this environment, so headline claims were checked against
the stored copies of the official tables, not against freshly downloaded files.

Minor, not fixed (judgement calls):

- Rounded changes can look off by 0.1: "27.0% to 25.1%, -2.0 points" is
  calculated from unrounded figures (27.03% to 25.07%). That is standard practice,
  but a newcomer may notice it.

## 2. Impartiality

What was checked: headline choice on every money page and the home page; the
choice of years and windows; question headings; every attributed quote's
framing; chart scales; and a scan of every main page for loaded words (soar,
plummet, burden, fair, cuts, austerity, record, only, just, better, worse and
others), excluding quotes.

Findings and fixes:

| # | Finding | Fix |
|---|---|---|
| I1 | The home page and "Who pays?" led with "the top 1% paid 27.2% of all Income Tax" without saying that they also had 12.4% of the income. On its own, that headline matches one side of a familiar political argument. | Both now give the income share next to the tax share. |
| I2 | The life page said "The pandemic cut holidays abroad to 4.4 million in 2020". The site's own rule is that it never states a cause in its own words. | Now: "In 2020, the first year of the Covid-19 pandemic, holidays abroad fell to 4.4 million." |
| I3 | The taxes page called shares of all tax "the fairest way" to see the mix. | Now "a like-for-like way". |
| I4 | The site did not explain how it chooses years, headline measures and chart scales (rubric D8 level 5). | The sources page now has a "How we choose what to show" principle. |

No partisan framing, party references or policy judgements were found. Ten-year
and first-to-latest windows are fixed and say so. The comparison pages lead with
the same measure for each topic whichever way it moved. Quotes come from ONS and
HMRC statistical commentary, not ministers or campaigners. Line charts do not
always start at zero; their axes are labelled, and bars always start at zero.

## 3. Accessibility

What was checked:

- axe-core with only the WCAG 2.0, 2.1 and 2.2 A/AA rules, every impact level,
  at 360px and 1100px, with every folded section opened, on 14 pages: home, the
  four money pages, life index, a year page, two comparison pages, the compare
  chooser, glossary, uncertainty, corrections, sources and a figure record page.
- Keyboard: tabbing through the spending page (skip link first, visible 3px focus
  ring on every stop, menu links 44px tall), and charts are focusable with a text
  label.
- JavaScript turned off: home, who pays, household tax, a comparison page, the
  life index and the compare chooser all show their answers.
- Sideways scrolling at 360px: none.

Findings and fixes:

| # | Finding | Fix |
|---|---|---|
| A1 | WCAG 2.5.8 (target size) failed at 1100px on life pages and the uncertainty page: links in the folded "Sources" lists were 16px tall. The site's own axe check did not catch it because it never opened folded sections and ignored "moderate" results. | Source-list links now have 24px tap height. `make a11y` now opens every folded section and fails on any WCAG violation; it also covers 3 more pages (18 in all). |
| A2 | `make a11y` did not run in CI, so accessibility could regress unseen. | New `accessibility` job in `.github/workflows/check.yml`. |
| A3 | Without JavaScript, the Compare button reloaded the chooser at the top of the page with no visible change. | The button now lands on the list of every comparison (`#all`), as the life page already promised. |
| A4 | The "Who pays" chart label "Dividend rules changed" was cut off at the right edge on a phone. | Labels that would overflow are now right-aligned. |
| A5 | The chart titled "Employment rate by age" showed three of the five age groups. The two missing groups were the largest. | Retitled "Employment rate, ages 18 to 24, 50 to 64 and 65 and over", with a note that the other two groups are in the table. |

Open (needs a person):

- No manual screen-reader test (VoiceOver on iOS, TalkBack on Android) has been
  done. The rubric needs one for D9 above 3.

## 4. Reproducibility

- `git clone` of the commit, `make setup`, `make verify`: all checks passed
  ("Re-read 8,215 figures from source files; recalculated 2,009 derived figures.
  Checked 60,901 numbers on 251 pages", 62 unit tests OK).
- Two consecutive builds produce byte-identical output for all 253 files.
- Every source records its publisher, title, URL, file and hash. Fetched files
  also have a download receipt (`data/fetched/receipts.json`).

Limit: the reviewer could not re-download the sources from their publishers in
this environment, so it checked that the stored files match their hashes, not
that they still match what the publishers serve today.

## 5. Larger issues for the coordinator

These are too big to fix in a review and are listed as gaps in the scorecard:

1. Pages are very long on a phone: who pays is about 19 screens at 360px, the
   life index 29, each comparison page 18. The first screen of a comparison page
   is the year chooser and the contents list, not the answer.
2. Life evidence is still mainly England or UK only for housing and schools, with
   few splits by age, income or region beyond work and pay.
3. Charts are almost all line charts with up to three series. Questions with more
   groups (age, nations, regions) need small multiples or a different form.
4. "Who pays" has no split by age, though HMRC publishes Income Tax by age.
5. Human steps: the five-person phone test, a manual screen-reader test, and a
   review by someone outside the project.
