# Welfare, housing and generations: re-run at badb1ba (T146)

The T146 fixes (the per-person welfare figure in the lede, and the seven misses from the T145 run) were re-tested with five fresh phone readers, each with the full 40 actions, on the built site at `badb1ba`.

- Question sheet: the 22 John's questions in the welfare group (the same sheet as T145).
- Profiles, drawn at random: R3 = P9 (care worker, dyslexic), R4 = P5 (warehouse worker, English second language), R8 = P4 (retired shop manager), R9 = P1 (café worker, 19), R10 = P8 (taxi driver).
- Actions used: R3 34, R4 38, R8 37, R9 30, R10 32 (budget 40 each).
- R3's sub-agent ended without sending its hand-back message, but its state file and answer file were both written and checked (22 answers, 34 actions).

## Result: 22 of 22 pass (4 of 5 right or better)

[score-output.txt](score-output.txt) lists each probe. Compared with the T145 run (15 of 22):

- J10.4 (per-person welfare): 5/5, was 0/5 in the T146 run before the lede change.
- J11.2 (deposit in years of pay), J11.3 (mortgage payment after inflation), J11.4 (new-buyer weekly cost), J10.6 and J10.7 (DWP split): all 5/5, were 3/5.
- J11.9 (ownership by age): 4/5, was 3/5.
- J12.8 (tuition fees 1998 vs 2025): 4/5, was 3/5.

Still at 4/5 rather than 5/5: J11.5, J11.11, J12.1, J12.2, J12.9. Each has one reader choosing E. These are above the 80% bar.

Readers' answers and phone state files are in [readers/](readers/).
