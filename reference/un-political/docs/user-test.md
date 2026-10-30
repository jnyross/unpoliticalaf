# Comprehension user test

This is the ready-to-run protocol for Comprehension level 4 in [the rubric](rubric.md).
No sessions have been run or passed by writing this document.

## Recruit and prepare

Recruit at least five adults who say they do not follow politics. Use a general
community or acquaintance invitation, rather than a political group. Ask:
"Do you regularly follow political news, campaigns or party debates?" Include
people who answer no; do not test site contributors or people who have already
seen its answers. Aim for varied experience of using websites. Do not ask for
party preference or record names, contact details, demographics or other personal
data in the results.

Explain that participation is voluntary, they can stop at any time, and only
anonymous scores, times and usability notes will be recorded. Obtain agreement
before starting. Assign codes P01 to P05 (and continue for any additional people).
Arrange recruitment privately; keep no identifying code key in this repository.
Do not record audio, video or screenshots containing personal data.

Use the same site version for the whole round. Complete this run record first:

| Round | Site URL or local build | Evaluated commit (from controller) | Data release | Facilitator code | Device/browser | Date |
|---|---|---|---|---|---|---|
| To fill | | | | | | |

Check all answer-key links below against that build before any participant sees
it. If a link, figure, year or definition has changed, resolve the key for the new
version and record that revision before testing. Do not change the key mid-round.
Keep the key out of participants' view. Start each person on the home page at the
top, with default views, closed answers and no previous browser search. Let them
use their usual input method and accessibility tools; record the setup without
identifying them. Have a stopwatch and the eight questions ready.

## Facilitator script and timing

Read this before the timer starts:

> We are testing the website, not you. Use only this website to answer eight
> questions. You may open answers, change views, use tables and follow source
> links. You can answer in your own words or point to an answer. I cannot show you
> where to go or say whether an answer is right. You can skip a question and come
> back. You have five minutes in total for all eight questions. You may stop
> whenever you wish. Tell me when you have finished.

Give the participant all eight questions below, in order, without the answer
columns. Say "Start" and start timing as the questions become available. The
five-minute limit includes reading the questions, navigating and giving answers.
Do not pause for reading, hesitation or navigation. Avoid requiring think-aloud
commentary during the timed task. If asked for help, say only "Use the website
as you normally would; you can skip this question." Do not paraphrase a question,
hint, teach the controls or reveal correctness.

Record the final answer to each question and its location using the participant
code only. Stop at their "finished" or at 5:00, whichever comes first. At 5:00,
say "Time is up"; unanswered questions score zero and later answers do not count.
Record elapsed seconds, not a rounded number of minutes. An interrupted session
is incomplete, not a pass; retain that row and explain the interruption without
personal details. After timing, optionally ask "What was hard to find or
understand?" and record a short anonymous usability note.

## Questions and facilitator answer key

The question column reproduces the rubric verbatim. Award one point per correct
answer, with no half points. Accept equivalent plain wording and the site's
displayed rounding. The amounts below describe the pinned build's 2025-26 data;
they are an answer key, not new product figures.

| No. | Question (read verbatim) | Correct answer / marking rule | Answer source (section id) |
|---|---|---|---|
| 1 | What does the government spend the most on? | Pensions, benefits and social care (the combined area; "pensions" alone is insufficient). | [index.html#hundred](../site/index.html#hundred), also [#answers](../site/index.html#answers). |
| 2 | Out of every £100 of spending on services, how much goes on health? | £21 per £100 (about 21%). A plain "£21" is sufficient because the question supplies the denominator; an explicitly contradictory denominator is incorrect. | [index.html#hundred](../site/index.html#hundred); PESA Table 4.2, X20 divided by X25. |
| 3 | How much was spent on paying interest on government debt in 2025-26? | £130bn (or £130.3bn), the Treasury debt-interest line. £96.9bn alone is only central-government loan interest and is insufficient. | [index.html#debt](../site/index.html#debt), also [#answers](../site/index.html#answers); PESA Table 4.2, X9, with the breakdown from Table 5.2. |
| 4 | Has health spending gone up or down in the last ten years once inflation is taken into account? | Up, comparing 2015-16 with 2025-26 in inflation-adjusted prices. No percentage calculation is required. | [index.html#answers](../site/index.html#answers) and [#area-health](../site/index.html#area-health); PESA Table 4.3, N20 and X20. |
| 5 | Is total spending a bigger or smaller share of the economy than ten years ago? | Bigger. The Treasury comparison is 44.3% in 2025-26 versus 40.8% in 2015-16; figures are not required for the point. | [index.html#total](../site/index.html#total), also [#answers](../site/index.html#answers); PESA Table 4.1, O46 and O36. |
| 6 | How much goes on pensions paid in old age, compared with defence? | Both amounts: about £155bn on old-age pensions and £65.4bn on defence in 2025-26 (equivalently £154.9bn and £65.4bn). "More" alone is insufficient; military defence alone is not the whole defence area. | [index.html#answers](../site/index.html#answers); [#items](../site/index.html#items) for pensions and [#area-defence](../site/index.html#area-defence) for defence. PESA Table 5.2, G107 and Table 4.2, X10. |
| 7 | Which numbers on the page are forecasts rather than actual spending? | Total spending for years after 2025-26. That identification is sufficient for the point. Forecast labels in text/tables, the dashed line and grey background are optional supporting cues, not extra scoring requirements. | [index.html#total](../site/index.html#total) and [#answers](../site/index.html#answers). |
| 8 | Where can I check this number myself? | Choose the health £21 from question 2 as the same referent for everyone, without pointing to its location. Participant explains or demonstrates opening a number's source note to find its table/cell, then using the methods page's source-file links to check the official file. A generic "on the internet" is insufficient. | [index.html#answers](../site/index.html#answers), source note [#tip](../site/index.html#tip), and source-files table within [methods.html#main](../site/methods.html#main). |

For question 8, tell everyone before "Start": "For the last question, 'this number'
means the health amount in question 2." This supplies a fixed referent without
changing the question or showing where to find the answer.

## Results and decision

Fill actual date, score out of eight, elapsed seconds and notes for every session.
In notes record Q1–Q8 as correct/incorrect (or unanswered), brief anonymous final
answers and any usability problem. Never enter personal information or a
participant's political opinions.

| Participant code | Date | Score (/8) | Time (seconds) | Notes |
|---|---|---|---|---|
| P01 | Not run | — | — | |
| P02 | Not run | — | — | |
| P03 | Not run | — | — | |
| P04 | Not run | — | — | |
| P05 | Not run | — | — | |

A round passes only when at least five eligible participants complete it and
**every participant in that round gets at least 7/8 correct in under 300 seconds
(under five minutes)**. A time of exactly 300 seconds fails. Do not use an average,
discard a low score or replace a failing participant to manufacture a pass.
Retain failures and incomplete sessions. After fixes, run a new labelled round on
one recorded version with at least five fresh eligible participants; preserve
the earlier results.

Record the round decision, evidence location and any fixes here: **Not run.**
Only completed human results can support Comprehension 4. Any later rubric score
must identify the evaluated commit, date and results and satisfy the lower levels.
