# Phone user-test pack

Everything needed to run the five-person phone test in the project goal's
definition of success:

> Five consenting UK adults who do not follow politics closely must test the same
> delivered version on phones. Together, they must answer at least 48 of 60
> questions correctly. Each person must answer at least 9 of 12 correctly within
> eight minutes, including all three critical questions about tax interpretation,
> illustrative households and causation.

Under rubric v3 this test is optional: simulated readers run the same 12
questions ([../standins/README.md](../standins/README.md)). If people do take
it, their result overrides the simulated one in either direction.

| File | Who uses it |
|---|---|
| [consent.md](consent.md) | Each participant, before they start |
| [question-sheet.md](question-sheet.md) | Each participant, printed (one copy each) |
| [answer-key.md](answer-key.md) | Moderator and marker only, with where the site says each answer |
| [marking-sheet.md](marking-sheet.md) | Marker: one per person, plus the group result |
| [results-template.csv](results-template.csv) | Marker: one row per person, for the scoring script |
| [questions.json](questions.json) | Source for all of the above |

The three critical questions are **5** (tax interpretation), **7** (illustrative
households) and **12** (causation). The 12 questions also cover each of the four
public money questions, and the year-by-year explorer: work, earnings, housing,
holidays and class sizes, choosing a year and comparing two.

## Before the test

1. **Fix the version.** Pick the deployed commit everyone will test and write its
   short commit id on every marking sheet. The live commit is shown as "Site
   version" at the foot of every page; `make live` confirms the live site is
   exactly that build. Don't merge or deploy anything until all
   five people have finished. If the site changes, start again with the new version.
2. **Check the answer key against that version.** Run `make build` and
   `python scripts/user_test.py check` on that commit. It confirms every answer is
   still stated on the built pages (it also runs in `make test`). Then open the live
   site on a phone and spot-check two or three answers.
3. **Find five people.** Each person must:
   - be 18 or over and live in the UK;
   - answer "not very closely" or "not at all" to *"How closely do you follow news
     about politics and government?"* (options: very closely, fairly closely, not
     very closely, not at all);
   - not have worked on the site or seen these questions before.

   Record "eligible: yes" only when all three are true.

## Running each session (about 15 minutes)

1. Give the consent note. Start only after consent is recorded.
2. The person uses **their own phone** and its usual browser. Load the site's home
   page for them; it should not already be open on the page with an answer.
3. Hand over the printed question sheet and a pen. Say: *"Use the website to answer.
   You can go to any page on it. Please don't use other websites. If you don't know,
   circle E."*
4. Start the timer when they first look at the questions. At **8:00**, say stop and
   take the sheet. Anything written after that counts as wrong.
5. Don't hint, point at the screen, or say whether an answer is right. If asked,
   reply *"Whatever the website tells you."*
6. Afterwards, you can note anything they found confusing. Those notes help improve
   the site but don't change the score.

## Marking

Mark each sheet against the answer key. Only the exact right letter scores 1;
E (not sure), blanks, two letters and late answers score 0.

A person passes when they score at least 9 of 12, get questions 5, 7 and 12 all
right, and finish within 8 minutes. The test is met when all five pass on the same
version and the five totals add up to at least 48 of 60.

To apply these rules automatically, copy `results-template.csv`, add one row per
person (`consent` and `eligible` are `yes`/`no`, `seconds_taken` is a number,
`q1`-`q12` are the letters circled, blank if none), then run:

```
python scripts/user_test.py score my-results.csv
```

It prints each person's score, why anyone didn't pass, the total, and
`Result: MET` or `Result: NOT MET`. Record the result, the commit tested and the
date in `docs/goal-scorecard.md`. Don't commit the filled-in CSV if it holds
anything that could identify a person.

## Changing the questions

Edit `questions.json`, then run `python scripts/user_test.py render` to rewrite the
sheets. Each question lists the page and exact words that support its answer, and
`make test` fails if a page stops saying them, so a change to the site that alters an
answer is caught before anyone is tested on the old key.
