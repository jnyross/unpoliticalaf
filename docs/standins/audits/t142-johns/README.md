# John's questions stand-in re-run (T142)

Re-run on the merged build after T142 (PR #224): each question on the Questions page links to the answer at the top of its page, and the Debt page leads with one debt measure.

- Site: `9317c4b` (the branch that merged as PR #224), built and served by `scripts/standins.py phone`.
- Readers: P3, P4, P8, P9, P10, drawn at random (seed 142). Five fresh subagents. Each answered the 78-question sheet without the site, then on the phone within 40 actions.
- Scoring: `scripts/standins.py` `score_johns`, unchanged. Output in [score-output.txt](score-output.txt).

## Result: FAIL

- 11 of 78 probes passed (4 or 5 of 5 right with the site). 67 failed. No open probes are counted as failures here; the scorer reports 18 open probes as gaps as well.
- Before T142 (T139 re-run, [t139-johns](../t139-johns/README.md)): 11 of 72 passed. The fix did not move the score.
- Readers answered "Not sure" on most probes. Their phone logs show the 40 actions go on scrolling and on pages that do not hold the answer, for example the Who pays and Tax and income pages when asked about topics on other pages.
- Recurring confusions: the Questions page is long; "46.0%" and "36.2%" on Who pays look like tax rates; the Debt page's opening sentence is dense; the HMRC and ONS sources note.

## Limits

- The stand-in measures reading within 40 actions. Most failing probes were not reached.
- Five readers, one run, simulated phone.
