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

## Trace of failed probes (T144)

Checked against the phone state files (`scratchpad`, not committed) and the built pages.

- **J5.1 (defence, answer at the top of defence.html):** no reader opened defence.html. Each reader spent its budget on the earlier probes in sheet order (J1, J4, J2), and the sheet puts J5 at position 24 of 82. Readers opened 4 to 9 pages before running out.
- **J7.1 (manifesto):** no reader opened manifesto.html. It sits at position 47 on the sheet.
- **J13.1 (why-debt):** no reader opened why-debt.html. It sits at position 39.
- **Pages that were reached:** P3 reached immigration.html#answer on its last action and answered J2.1 correctly (C). P9 reached high-earners.html#answer on its last action and answered J6.1 and J6.2 correctly (B). The answers at the top of these pages work when readers reach them, so the failures are about reaching them within the budget.

Reader actions across the five: 21 to 28 scrolls and 10 to 16 taps each. A scroll costs one action, so long pages cost a lot of the budget.

The sheet has 82 probes across 14 evidence pages. Opening those 14 pages takes at least about 25 actions (two per page for the pages that are not in the menu: the Questions item, then the page), before any scrolling. The 40-action budget therefore cannot cover the sheet by construction, even if every answer sat at the top of its page.
