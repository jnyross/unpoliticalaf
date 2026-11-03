# Running the rubric v3 stand-ins

[goal-rubric.md](../goal-rubric.md) (v3) replaces the four people tests with
stand-ins run by fresh Claude sessions. This page is the procedure. The goal
auditor runs it on one commit of `main` and saves everything in
`docs/standins/audits/<audit>/`, for example `docs/standins/audits/audit-9/`.

The tools are in [`scripts/standins.py`](../../scripts/standins.py). They serve
the built `site/` folder on a local port, because the build container cannot
reach the live site. That is the same site: the "Live site matches main" check
confirms the live site is byte-identical to the build of `main`. Record that
check's run for the audited commit.

## Rules for every stand-in session

- Start each stand-in as a **fresh session** (a new subagent) that did not build
  the site. Give it only its prompt from [prompts/](prompts/) and the files the
  prompt names. Never give it the code, `docs/user-test/answer-key.md`, the
  `answer` or `why` fields of `questions.json`, the scorecard or another
  stand-in's results.
- Use a smaller model for readers where one is available (for example Haiku or
  Sonnet), and the strongest model for the fact-checker, critics and judge.
- Readers write answers only as letters. The auditor marks them with the
  script, not by eye.
- Workers who fix the site afterwards see only the confusion notes and
  findings, never the readers' answers or the new questions.

## Steps

1. **Build and record the commit.** `make setup-dev && make build`. Note the
   commit in `site/build.json`, and the "Live site matches main" run for it.

2. **Write and seal the new questions.** Start the question writer with
   [prompts/question-writer.md](prompts/question-writer.md). It writes 24
   questions from the goal text alone, in the same JSON shape as
   `docs/user-test/questions.json`. Save its file **outside the repository**,
   then run

   ```
   python scripts/standins.py seal /path/to/new-questions.json docs/standins/audits/<audit>
   ```

   and commit `new-questions.sha256` (and nothing else from this step) before
   any reader starts. Check each question has one right answer on the built
   site; if one does not, the writer replaces it and you seal again before the
   readers start.

3. **Informal check (D11 level 2).** Three readers with
   [prompts/informal-reader.md](prompts/informal-reader.md). Each gets its own
   state file, `docs/standins/audits/<audit>/informal/I1.json` and so on. Save
   their confusion notes beside them.

4. **Simulated phone test, new questions and prior knowledge.** Five readers
   R1 to R5 with [prompts/phone-reader.md](prompts/phone-reader.md), each given
   a different profile from [prompts/profiles.md](prompts/profiles.md). Each
   reader, in this order:
   1. answers the 12 questions and the 24 new questions **without the site**;
   2. answers the 12 questions using only the phone tool, within 40 actions;
   3. starts a fresh phone session (`--state R1-new.json`) and answers the 24
      new questions within 40 actions.

   Give the questions without their answers: the question sheet
   `docs/user-test/question-sheet.md`, and the new questions with the
   `answer` and `why` fields removed. Save each reader's answer file as
   `docs/standins/audits/<audit>/readers/R1.json` (format below), and keep the
   phone state files (`R1-phone.json`, `R1-new.json`) beside them. They hold
   every action. Screenshots stay out of the repository.

5. **Screen-reader reader (D9).** One reader with
   [prompts/screen-reader.md](prompts/screen-reader.md), using
   `python scripts/standins.py sr ...`. Save `readers/SR.json`. Then run the
   automated checks and save their output in `accessibility.txt`:

   ```
   make a11y                                   # or use the CI run for the commit
   python scripts/standins.py keyboard
   python scripts/standins.py summaries
   ```

6. **Fact-checker (D7).** Start it with
   [prompts/fact-checker.md](prompts/fact-checker.md). It lists 30 figure ids
   in `fact-check/ids.txt` and its reasoning in `fact-check/claims.md`. Then

   ```
   python scripts/accuracy_check.py sample --ids docs/standins/audits/<audit>/fact-check/ids.txt --dir docs/standins/audits/<audit>/fact-check
   ```

   Pushing `fact-check/sample.json` to `main` runs the "Accuracy check"
   workflow, which downloads each source again from the publisher and commits
   `fact-check/results.json`. (It can also be started by hand with the folder
   as its `dir` input.) Any mismatch is a material finding until explained.

7. **Impartiality red team (D8).** Start the two critics with
   [prompts/critic.md](prompts/critic.md), one told "left" and one "right".
   Then start the judge with [prompts/judge.md](prompts/judge.md), giving it
   both lists and [impartiality-rule.md](impartiality-rule.md). Save
   `impartiality/critic-left.md`, `critic-right.md` and `judgement.md`.

8. **Unseal and score.** Copy the new questions into the audit folder as
   `new-questions.json` and run

   ```
   python scripts/standins.py score docs/standins/audits/<audit>
   ```

   It checks the file still matches its seal, applies every pass bar and
   writes `reader-scores.json`. Score the dimensions with
   [goal-rubric.md](../goal-rubric.md) and add the audit to
   [goal-scorecard.md](../goal-scorecard.md). If the target is reached, record
   it as "met (simulated)" with the limits listed in the rubric.

## Reader answer file

```json
{
  "reader": "R1",
  "profile": "P3",
  "site_commit": "fded452",
  "budget": 40,
  "actions_used": 34,
  "new_actions_used": 38,
  "without_site": {"1": "B", "2": "C"},
  "with_site": {"1": "A", "2": "C"},
  "new_without_site": {"1": "E"},
  "new_with_site": {"1": "B"},
  "confusions": ["On the taxes page I could not tell whether £1,105bn was all money raised or only taxes."]
}
```

Keys are question numbers; values are letters, with `E` for "Not sure".
`actions_used` comes from the state file. A reader over budget fails.

## The phone tool

```
python scripts/standins.py phone start  --state R1-phone.json --shots /tmp/shots
python scripts/standins.py phone scroll --state R1-phone.json down
python scripts/standins.py phone tap    --state R1-phone.json 7
python scripts/standins.py phone choose --state R1-phone.json 6 1990
python scripts/standins.py phone back   --state R1-phone.json
```

Each call is one action (start is free) and prints the page, the actions used,
the screen number, the path of a 360 × 640 screenshot and a numbered list of
what can be tapped on that screen, matching yellow numbers drawn on the
screenshot. The reader must open the screenshot to read the page: the tool does
not print page text. `sr` works the same way but prints the accessibility tree
of the whole page instead of a screenshot, and has no scroll.
