# Impartiality judgement: audit 12

Judge's inputs: `critic-left.md`, `critic-right.md` and `docs/standins/impartiality-rule.md`.
I checked every example against the built pages in `site/` (site version 1f64e04):
`index.html`, `spending.html`, `spending-areas.html`, `taxes.html`, `who-pays.html`,
`who-pays-households.html`, `who-pays-age.html`, `household-tax.html`, `international.html`,
`borrowing.html`, `glossary.html`, `methods.html`, `life/index.html`, `life/housing.html`,
`life/earnings.html`, `life/work.html`, `life/schools.html`, `life/holidays.html`, `life/2025.html` and
`life/compare/2011-2019.html`.

Several examples come in opposing pairs: both critics attack the same text from
opposite sides. Examples are L1/L6 against R1/R2 (who-pays cards), L3 against R7 (debt per household),
L9 against R9 (everyday-life indicators) and L7 against R3 (net recipients). Where
that happens and the page follows the rule, I rejected both sides.

## Rulings

| # | Example (short) | Ruling | Reason |
|---|---|---|---|
| L1 | Home "tax and income" card gives 36.7% for the lowest fifth with no caveat about gross income or spending above income | **Upheld, minor** | The figure is the ONS's own main measure and the card says "not anyone's tax rate". But the homepage gives no hint that the lowest fifth's indirect-tax share depends on the denominator (21.0% of income, 16.5% of spending). The inner page explains this, so it is not material. |
| L2 | "Tax burden" put in quotation marks and explained away | Rejected | "Burden" is a word that judges a figure, which the rule forbids the site to use in its own voice. The glossary caveat runs both ways ("goes up … goes down") and names the OBR's version. |
| L3 | Debt "owed by the public sector, not by people or households" | Rejected | The sentence is accurate. Tax per household gets the matching caveat "not anyone's tax bill", so the caveats are symmetric. |
| L4 | G7 chosen as the peer group to make the UK look low-tax and low-debt | **Upheld, minor** (borrowing page only) | `international.html` leads with the OECD average (34.4% against 34.1%), so the claim fails there. `borrowing.html` leads with "second lowest of the G7" and never says the UK is above the OECD average (92.5% against 77.1%). Its next sentence ("highest yields of the G7") cuts the other way, so this is minor. |
| L5 | Corporation Tax treated as falling on nobody, while VAT is "passed on" | **Upheld, minor** | The glossary states where VAT's cost falls but not where Corporation Tax's falls. "It is paid by companies, so…" presents an ONS counting choice as a fact. The household pages do say it is "not allocated to households", so the effect is small. |
| L6 | Who-pays card qualified, tax-and-income card not | Rejected | Each card carries one qualifier: "Every household also pays taxes on spending" and "not anyone's tax rate". The tax-and-income card also says the lowest fifth's tax is mostly VAT. |
| L7 | Net-recipient figure steered towards pensioners | Rejected | The retired/non-retired split is the ONS's own Table 16 breakdown. The 1977 figure (37.0%) is stated in the section. "Social protection" is the COFOG area and the label gives its contents. |
| L8 | Year-page private-renting chart starts at its lowest point, axis not zeroed | Rejected | 2008-09 is the first year after the series break (Labour Force Survey to English Housing Survey), so it is the rule's "first year". The line chart states its non-zero scale, as the rule allows. |
| L9 | Everyday life leans on hardship and inequality measures | Rejected | The right critic argues the opposite about the same set. The topics are mixed, and ratios such as house price to earnings are standard official measures. |
| L10 | "Gap between richer and poorer" framing of the ONS quote | Rejected | The question repeats the ONS's own word ("this gap"), and the quote can support either side. |
| R1 | "Who pays?" opens with the top 1%'s share of Income Tax | Rejected | The figure is labelled as Income Tax only. It sits next to the 1%'s 12.4% income share and two all-taxes figures. On the homepage it is paired with the near-flat all-taxes shares. |
| R2 | Who-pays hero shows cash (£51,903 against £8,625), not shares | **Upheld, minor** | The hero gives a roughly sixfold cash gap without the near-equal shares (36.2% against 36.7%). Those shares are only behind a link. The link is in the lede, so this is not material. |
| R3 | 53.3% "net recipients" framing | Rejected | The definition, which counts the NHS and schools as benefits, is given in the first sentence, before the number. The series is an official ONS table, and the lifetime caveat is in Limits. |
| R4 | Default comparison 2011 against 2019, with "2011 came soon after a recession" | **Upheld, minor** | The default is not the rule's first-and-latest window. The stated reason, that only these years have all five topics comparable across the pay-coding breaks, is real and shown on the page. Every compare page also gives the longer first-to-latest run. The one preset still brackets a single era, and the "after a recession" line frames the start year. |
| R5 | Ten-year spending window starts at the 2015-16 trough | Rejected | The ten-year window is fixed by the published rule and explained on the page. The same section gives shares of GDP (some fell), and the full 2003-04 to 2025-26 series is one click away. |
| R6 | ONS 2017 lifetime-consumption quote softens the VAT finding | Rejected | The quote is attributed, dated and openly flagged as not repeated in the latest bulletin. It opens with the plain point that indirect tax follows spending, not income. |
| R7 | Debt, borrowing and tax per household | Rejected | Each figure carries an explicit "not anyone's bill" caveat and says business taxes are included. Spending per household gets the same treatment (L3 argues the opposite). |
| R8 | "Spending was higher than receipts in 68 of the 78 years" | Rejected | This is a factual count describing the two lines, in neutral words. The chart text also gives the 1949-50 receipts high and the 2031-32 forecast. |
| R9 | Everyday life measured with upbeat indicators and near-record ranks | Rejected | The "higher than in N of the other years" phrasing is applied to every series, including class sizes ("4 of 19"). The left critic argues the same set leans the other way. The compare page shows the house price to earnings ratio. |
| R10 | Gross debt interest put up front | Rejected | Gross is HM Treasury's (the publisher's) own measure, as the rule requires. The page says the OBR/IFS net figure is lower. Pensions also get their own figure (£155bn). |

Upheld, material: 0. Upheld, minor: 5 (L1, L4, L5, R2, R4). Rejected: 15.

## Breaches the critics missed (my own checks of start years, scales and group order)

Group order: nations (England, Wales, Scotland, Northern Ireland), English regions (North East to
South West), age bands, income fifths and tenures all keep their official order on every main page.
Charts ranked by size (G7 and OECD bars) say they are rankings. One-year categories (spending areas,
taxes) run largest first. Bar charts start at zero. Small multiples state "All panels use the same scale".
Every line chart I found with a non-zero axis says so in its caption or on the axis. I found no named
party or politician and no judging verbs in the site's own words.

1. **Start year, minor: class sizes on `life/index.html`.** "In January 2008 the figures were 26.2 and
   20.9" compares the latest year with 2008. The same-definition series starts in January 2006 (26.3 and 21.5;
   `life/schools.html` says 2006 and 2007 are "on the same definition"). This breaks "the first and latest
   year of each series". It also overstates the secondary rise (+1.6 pupils from 2008 against +1.0 from 2006).
2. **Break not marked, minor: `who-pays.html` section 4 chart, 1977 to 2023/24.** The ONS top-income
   adjustment from 2001/02 (which Limits says makes years before and after "less directly comparable") is
   not marked on the chart. The household-tax and tenure charts do mark their breaks. The section also puts
   the 1977 figure (37.0%) beside 2023/24 (53.3%) without a break warning next to it. No change is calculated,
   so this is not material.

Not bias, noted for the build: the after-inflation receipts and spending chart on `taxes.html` labels its
axis from 1948-49, although its data start in 1955-56.

Open material findings: 0
