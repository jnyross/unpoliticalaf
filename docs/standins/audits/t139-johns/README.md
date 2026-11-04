# John's questions stand-in re-run (T139)

Re-run of John's-questions stand-in after the question pages were added to the menu and the home page (PR #218, merged as 9dcade5 on main).

- Site: `9dcade5`, built with `make build` and served by `scripts/standins.py phone`.
- Procedure: [docs/standins/README.md](../../README.md) step 4, phase 4 only. Five readers drawn at random from [profiles.md](../../prompts/profiles.md) (seed 139): P1, P5, P6, P8, P9. Each reader answered the 72-question sheet (`scripts/johns_questions.py sheet`) without the site, then with the phone tool within 40 actions in a fresh session.
- Readers were fresh subagents given only the sheet and the phone tool. They were not given the repository, the answer key or the answers of other readers.
- Scoring: `scripts/standins.py` `score_johns`, unchanged. Output in [score-output.txt](score-output.txt).

## Result: FAIL

- 11 of 72 answered probes passed (4 or 5 of 5 right with the site). 61 failed, and 18 probes are still open.
- Compared with the T133 re-run (audit 17, PR #217), which had 61 of 69 probes below 4 of 5, the number failing did not fall.
- The readers gave "Not sure" (E) on most probes: 54 to 61 of 72 per reader. They used 31 to 40 of their 40 actions and ran out before reaching most topic pages.
- Readers did find the new Questions list, but reported that it had many headings and that the Debt page was too long to get through on a phone.
- Recurring confusions: the Debt page gives IMF and OECD debt figures with a switch and does not say which to use; "46.0%" and "36.2%" on Who pays and Tax and income are easy to mistake for tax rates; the Work page only shows the 16 to 64 employment rate, not age groups.

## Limits

- The stand-in measures reading within 40 actions. Most failing probes were not reached, so the score measures findability and time more than the content.
- Five readers, one run, simulated phone.
