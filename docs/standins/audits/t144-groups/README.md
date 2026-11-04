# John's questions by topic group (T144)

Re-run of the John's-questions stand-in with the procedure changed to one fresh session per topic group (`docs/standins/README.md`, step 4). Each reader answers each group's sheet (`python scripts/johns_questions.py sheet <group>`) in its own 40-action phone session, so no group has to share its budget with the others. Groups: tax-and-spending, immigration, defence, high-earners-and-economy, manifesto, debt-history, welfare-housing-generations.

- Site: `b080c3f` (content as built on the T142 merge; the change in this audit is to the measurement, not the pages).
- Readers: P3, P4, P8, P9, P10, the same profiles as T142. Five subagents, each running seven group sessions. Answers in [readers/](readers/). Their state files and screenshots are not committed.
- Scoring: `scripts/standins.py` `score_johns`, unchanged, on the merged answers of the five readers. Output in [score-output.txt](score-output.txt).

## Result: FAIL, 56 of 82 probes passed

- 56 of 82 probes passed (4 or 5 of 5 right with the site). 26 failed. 12 open probes are reported as gaps too, so the scorer lists 38 gaps.
- T142 (single 40-action session over the whole sheet): 11 of 78 passed. The two are not the same test. Here every group has its own 40 actions, so this run measures what the pages hold, not what 40 actions can reach. Do not read the jump as the pages having improved on their own.
- Per group (probes passed of probes): tax-and-spending 12 of 14; immigration 8 of 8 (J2.4 and J2.5 are open); defence 8 of 8 (J5.2 open); high-earners-and-economy 9 of 12 (J8.1 to J8.3 fail); manifesto 10 of 10; debt-history 8 of 8; welfare-housing-generations 2 of 22 answered (see below).

## What fails

- **Content the site does not hold (open probes and their gaps).** J4.7, J2.4, J2.5, J5.2, J12.6, J12.7, J12.10, J12.11, J12.12, J11.6, J11.7, J11.8. Each has its gap written in the question file; they are not counted as passes.
- **Answered on the site, but the readers did not get them.** J4.6 and J4.8 (wealth tax yield, top 1% share of all taxes), J8.1 to J8.3 (OECD reform figures), J12.1 to J12.4, J12.8, J12.9, J11.1 to J11.5, J11.9 to J11.11 and all of J10 (0 of 5 on the welfare probes). Readers said they could not find these pages' answers and several stopped before their 40 actions were used (R3 used 33 on welfare, R8 used 33, R9 30, R10 29). So for welfare-housing-generations, the 0 of 5 result is partly the reader stopping, not the site lacking the answer. That group needs a re-run with a stop rule that does not end early before a fair search.

## Limits

- Five readers, one run, simulated phone, with the group split. The group split gives each group more budget than a single session would.
- Some with-site answers are arithmetic on figures the site shows (J6.5, J11.2, J12.4), not a stated answer. J7.2 and J7.9 were taken from summaries or cut-off text. A strict reading would fail some of these.
- The first run stopped before any phone session: the phone tool runs on the project's venv interpreter, not the system Python. The four readers that stopped were restarted; no answers from that first attempt are used.
