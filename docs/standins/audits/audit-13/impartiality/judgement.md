# Impartiality judgement, audit 13

Judge: neutral, did not build the site. Inputs: `critic-left.md`, `critic-right.md`,
`docs/standins/impartiality-rule.md`. Every example was checked against the built
pages in `site/` (site version 7ab0f27): the visible text, the collapsed "More on…"
panels, the chart SVGs (axis ticks, titles, captions) and the published CSVs.
`builder/`, `scripts/` and other audits were not read.

Several examples from the two critics are the same choice read in opposite
directions: L1 / R6 / R7 (tax by income fifth), L4 / R10 ("tax burden"),
L5 / R3 (debt per person), L6 / R5 (the "spending was higher than receipts" title)
and L8 / R8 (debt interest). Where the choice follows the rule and both readings
are possible, it is rejected for both.

## Rulings

| # | Example | Ruling | Why |
|---|---------|--------|-----|
| L1 | "Poor pay as much tax as the rich" (36.7% v 36.2%) leads on three pages | **Upheld, minor** | The figure is ONS's own main measure, the wording ("similar share", "made up of different taxes") is neutral, and the home card gives the 16.5%-of-spending figure in visible text. But on `household-tax.html`, the page that leads with the figure, the ONS explanation, the denominator table and the ONS 12.2×→3.3× quote are all in a collapsed panel. A real but small imbalance. Not material, because the official figures support the headline. |
| L2 | ONS caveat quoted, then "undercut" by its date note | Rejected | The note is an accurate statement of the quote's date, as the site's quoting rule requires, and it makes no claim that the explanation has lapsed. |
| L3 | 1977–1987 / 1988–2017/18 crossover sentence | Rejected | Checked against the table. The sentence is accurate, stays within one method (no break crossed), uses neutral verbs and names no government, and it sits in a collapsed panel beside per-fifth panels on one scale. |
| L4 | "Tax burden" in quotation marks and not ranked historically | Rejected | The quotation marks attribute a term the site does not use itself, which the neutral-wording rule calls for. The rule does not require a historical rank, and the long series is charted. R10 objects to the same sentence from the other side. |
| L5 | Debt per person "not anyone's bill" | Rejected | This is a factual definition (PSND is owed by the public sector), given beside the per-person figure in the same neutral form that the tax and spending per-head figures use. |
| L6 | Deficits shown as normal ("68 of the 78 years") | Rejected | The count is accurate (65 years are higher on the rounded table and 3 are tied at 0.1% of GDP, but the after-inflation table shows spending higher in all three) and the verb is neutral. The chart shows the whole path, including forecasts. R5 reads the same title the opposite way. |
| L7 | Social protection "mainly State Pension, other benefits and social care" | Rejected | "Mainly" covers all three items listed, which together make up nearly the whole category. The page also gives the £155bn pensions line and says it is wider than the State Pension. |
| L8 | Debt interest "played down" (gross/net note, RPI box) | Rejected | The gross figure is the publisher's (HM Treasury PESA) measure, the net figure is flagged and linked, and the box is an attributed ONS quote. The page has similar boxes for 2020-21 and 2022-23 spending. R8 reads the same choice the opposite way. |
| L9 | Housing tile compares only private renting with 2008-09 | **Upheld, minor** | On `life/index.html` and `life/housing.html` the lead figure is home ownership (65%), but the only back-comparison given is private renting (14% → 19%). That does not follow the methods-page promise of "the same lead figure on every comparison page". The chart and the collapsed panels do show the ownership series. |
| L10 | Pay "about the same" from 2021 | Rejected | The 2021 start is forced by the 2021 coding break (rule: no change across a break), "about the same" is an allowed neutral phrase, the +0.8% is given, and `life/earnings.html` also shows the earlier stretches. |
| R1 | "Who pays?" leads with the top 1%'s share of Income Tax | **Upheld, minor** | The home "Who pays?" card answers with one tax that raises about 30% of the total. On `who-pays.html` the all-tax household tiles share the hero, and the next home card gives all taxes by fifth, so the imbalance is small. |
| R2 | Net-recipient framing (53.3%) | **Upheld, minor** | The definition, which counts the NHS and schools as benefits, is visible before the figure, and the chart splits retired from non-retired. But the "one year at a time" caveat, which is needed to read the figure, is only in the collapsed Limits panel. |
| R3 | Debt and spending turned into per-household bills; share-of-GDP axis from 35 | Rejected | The per-head figures carry an "average, not anyone's bill" caveat in the same sentence. The line chart's axis is labelled "starts at 35, not at zero", as the rule allows. The share of GDP (38.7% → 44.3%) is given in the sentence right after the 54%. |
| R4 | Ten-year spending window starts in 2015-16 | Rejected | The rule fixes a ten-year window for spending by area, so the start is not chosen for its result. The same section links every year from 2003-04 for each area, and the full total table shows 2010-11 to 2013-14. |
| R5 | Spending as the subject of the deficit title | Rejected | "Higher than" is a neutral comparison, and swapping the subject would be no more neutral. L6 reads the same title as left-leaning. |
| R6 | Hero cards compare cash tax bills | Rejected | Each cash figure has its share of income (36.2% / 36.7%) in the same tile. The bars are labelled as pounds and start at zero, and the share view is one link away. (The tiles' order is a separate breach: see below.) |
| R7 | Second denominator softens indirect tax on the poorest | Rejected | Gross income (21.0%) is given first and stays the basis. The spending figure is an ONS-supported caveat, and the household-tax page shows it for every fifth. L1 says the same caveat is too weak. |
| R8 | Debt interest shown gross, at the larger figure | Rejected | It is the publisher's own measure, used on the same basis as every other area, and the net figure is flagged with a link to OECD net interest on `borrowing.html`. |
| R9 | "Everyday life" default pair 2011 v 2019 and positive indicators | Rejected | The page gives the rule-based reason for the pair, says it covers only the stretch between the recession and the pandemic, and links 2022 v 2025. Each tile uses the same "higher than in N of M years" form whichever way the figure moved. Pay below 2008 cannot be stated without crossing the 2011 and 2021 breaks. |
| R10 | "Tax burden" and threshold-freeze quotes | Rejected | The term is attributed, not adopted. The forecasts are labelled OBR forecasts, and both quotes are attributed official explanations, as the rule requires. |

Totals: upheld material 0; upheld minor 4 (L1, L9, R1, R2); rejected 16.

## Breaches the critics missed

These come from a sweep of the main pages (`index`, `spending`, `spending-areas`,
`spending-history`, `taxes`, `tax-history`, `who-pays`, `who-pays-age`,
`who-pays-households`, `household-tax`, `borrowing`, `international`, `life/index`
and the `life/*` topic pages). The sweep checked the start years of comparisons,
the scale of every SVG chart (the first axis tick, and a "not at zero" caption
where the axis does not start at zero), the claims that small panels share one
scale, and the order of the regions, nations, ages, fifths and tenures.

1. **Group order, `who-pays.html` hero (minor).** The two household tiles list
   the highest-income fifth before the lowest-income fifth. The rule says groups
   keep their official order (lowest first), and every other fifth display on
   the site follows it.
2. **Start year, `life/schools.html` lead (minor).** The page compares January
   2025 with January 2008 (26.2 and 20.9), not with the first year of the series,
   January 2006 (26.3 and 21.5). The chart, the "since 2006" title and
   `life/index.html` all use 2006. This breaks "first and latest year of each
   series". The effect on the result is small.
3. **Start year and series break, `life/holidays.html` lead (minor).** The 2025
   figure (58.4m, Great Britain residents, new method from 2024) sits beside
   2019, "before the pandemic" (58.7m, UK residents, old method). That year is
   neither the first year of the series nor on the same basis. No change is
   worked out, but the two are set side by side for comparison across the
   method break.
4. **Latest year, `life/index.html` tiles (minor).** The Work and Class sizes
   tiles headline 2025 (75.3%, 26.4) while the home page shows the newer 2026
   figures (75.1%, 26.1). The topic pages explain that the year pages stop at
   2025, but `life/index.html` does not, so two pages headline different years
   for the same measure.

No breaches were found in chart scales: every bar chart starts at zero, every
line chart whose axis starts above zero says so in its caption, and every
small-multiple set states and uses one shared scale. Regions and nations are in
official order throughout. No party or politician is named, and no judging
words were found.

Open material findings: 0
