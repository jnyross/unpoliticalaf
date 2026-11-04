# Welfare, housing and generations: full-budget re-runs (T145)

Coordinator asked for the welfare-housing-generations group to be re-run with every reader using its full 40 actions, and the pages fixed if the score stayed low.

## Runs

1. **Before the fix** (site `20732c7`, the T144 build): 1 of 22 probes pass. All five readers used 40 actions. welfare.html was not on the menu or the Questions list, and the Questions list had no welfare, mortgage or generations questions.
2. **Fix 1**: the Questions list gets three entries (welfare spending, house prices, the generations page), and their answer boxes get the `#answer` anchor. Re-run: 11 of 22 pass (four readers; R10 was not yet in).
3. **Fix 2**: the top answer boxes of life/generations.html and life/house-prices.html now give the figures the welfare questions ask for (18 to 24 employment, England home ownership, tuition fees, State Pension age, mortgage share of income, ownership by age). Final run, five readers: **15 of 22 pass** ([score-output.txt](score-output.txt), readers in [readers/](readers/)).

## Still failing (3 or 4 of 5 right, so below the 80% bar)

- J12.8 tuition fees 1998 vs 2025 (3 of 5).
- J11.2 deposit in years of pay (3 of 5). The figure (0.76) is on the house-prices page but not in the top answer box.
- J11.3 mortgage payment after inflation, 2008-09 to 2024-25 (3 of 5). Not in the top answer.
- J11.4 whether the mortgage figures show a weekly cost for a new buyer (3 of 5). The answer is "no, they show existing loans", which readers found only in a sentence further down.
- J11.9 home ownership at 25-34 and 75+ (3 of 5). Now in the top answer box, but readers ran out of actions on the cut-off lines.
- J10.6 and J10.7 DWP benefit breakdown (3 of 5). Readers reached the welfare page, but the DWP section is far down it.

## Limits

- The final run used five readers at 40 actions each. The site was rebuilt during the second and third runs while readers were running (make check), so some phone sessions saw "No built site" and one or two 404s. The 404s do not reproduce: the built pages in the final build have no broken internal links among the welfare, generations, house-price and Questions pages.
- Some readers chose E where a sentence was cut off between screens, so the score is partly the phone's scroll, not only the wording.
