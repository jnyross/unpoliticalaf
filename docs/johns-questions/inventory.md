# Recorded probe evidence inventory

Reconciled 10 November 2026. `baseline.json` is an extract of the immutable
baseline commit named there, not a new question set. All 12 original questions,
94 probe IDs and verbatim `asked`/`also_asked` entries remain. Current
`questions.json` holds exact evidence sentences, options, answer and explanation
for all 94; no probe is open. The original 84 and the 10 formerly open probes
are checked together against one build, not combined from historical results.

## Probe → page → source

Inclusive ranges below account for every ID. Source families name the cited
publications, including the explicitly secondary manifesto tracker. Registered
facts link through `figures/<source-id>.html` to locators, period, status,
formula/operands and original hash/download. Narrative citations can instead
link through `sources.html` or directly to the publisher. In particular, the
economy-options page uses hand-entered citations, not independently checked Fact
records. Its J8 OECD Table 1.1 figures were reopened against the publisher for
this reconciliation; that is not automated coverage of every option.
Registry sources and receipts remain in `builder/sources.py` and
`data/fetched/receipts.json`; this map does not replace those records.

| Probes | Evidence page | Source and scope |
| --- | --- | --- |
| J1.1–2, J1.4 | international.html | OECD tax/revenue and government spending, 2024; missing Japan tax remains missing |
| J1.3, J1.5–7 | borrowing.html | IMF gross debt, OECD yields/net interest; DMO and OBR explanations, not a confidence score |
| J4.1–2 | who-pays.html | HMRC Income Tax liabilities and income shares, not all taxes |
| J4.3 | who-pays.html | ONS ETB Table 2a, C:H counts/tax means and Notes; unsupported aggregate withdrawn |
| J4.4–5 | household-tax.html | ONS ETB 2023/24 Table 8: published taxes as a percentage of gross household income, people ranked by equivalised household disposable income |
| J4.6, J4.8 | who-pays.html | Explicit limits: no proposal yield estimate, no all-tax top-1% total; HMRC/ONS population distinctions |
| J4.7 | international.html | OECD 2025 top statutory income-tax rates, not effective rates |
| J2.1–4, J2.6–8 | immigration.html | OBR fiscal scenarios, MAC evidence and ONS migration/GDP; retained-source public-service-use limit, not universal unavailability |
| J2.5 | immigration.html | NHS HCHS August 2026 Table 14 and quality annex; Skills for Care 2026 Table 4.7.1, method and report; England people/posts kept distinct |
| J8.1–3 | economy-options.html | OECD Economic Surveys: United Kingdom 2026, Table 1.1; modelled potential-GDP effects, not observed causal gains. Other ranked options use other stated sources |
| J5.1–2, J5.4–5 | defence.html | PESA 2026 spending functions and compatible OBR nominal GDP; defence per £100 of services, not total expenditure |
| J5.3, J5.9 | defence.html | NATO spending definitions and GDP shares; not the PESA denominator |
| J5.6–8 | defence.html | OBR fiscal forecast, uncertainty and stated trade-offs; no affordability verdict |
| J12.1–2 | life/generations.html | ONS LFS employment by age/work pattern; fixed 1992/2025 comparison |
| J12.3 | life/generations.html | ONS house-price/earnings affordability, not take-home affordability |
| J12.4, J12.6 | life/generations.html | EHS household-reference-person ownership; 1991 LFS head-of-household figures in EHS 2008-09 Annex Table 1.4; exact-age-30 ownership not measured |
| J12.5 | life/generations.html | DfE class sizes, England state-funded primary classes taught by one teacher, 2006/2025 |
| J12.7 | life/generations.html | ASHE Table 6.1a full-time median, age 30–39 not exact 30; CPIH April values; no cross-method single change |
| J12.8 | life/generations.html | Commons Library briefing CBP 10155 and 1998 Hansard; tuition-fee rules, jurisdiction and period stated |
| J12.9 | life/generations.html | DWP State Pension age timetable, not pension adequacy |
| J12.10 | life/generations.html | ONS UK single-year life tables, age-30 ex, 1994/2024; period remaining years not a forecast |
| J12.11 | life/generations.html; life/tax-comparison.html | HMRC historical/current Income Tax, Hansard historical employee NI, employee thresholds in HMRC's employer guidance, CPIH; employer NI excluded from the equal-real-pay illustration |
| J12.12 | life/generations.html | YBUG employment not job security; RED02 age rates start 2009; EMP07 has no age split; no supported 1992 job-security change |
| J13.1–8 | why-debt.html | OBR historical debt/borrowing and fiscal risks; ONS public sector finances April 2021/2023 explanations (J13.4/7); stock, flows, inflation and GDP distinguished |
| J7.1–10 | manifesto.html | Retained manifesto and Full Fact secondary promise tracker (including J7.2/5/6/7), with official Budget/NHS/housing measures where cited; status dates and unmeasured promises stated |
| J11.1–2 | life/house-prices.html | ONS affordability and ASHE earnings; deposit illustration identified |
| J11.3–7, J11.9–10 | life/house-prices.html | EHS and FC2101; 1991 LFS head vs later HRP, six age bands; mortgage/gross income not take-home |
| J11.8 | life/house-prices.html | BoE IUMBV34 quoted 75%-LTV two-year fixed monthly rates, metadata/method changes |
| J11.11 | life/house-prices.html | BoE CFMZ6JM new-business effective rate from 2016, not the quoted product |
| J9.1–3 | productivity.html | ONS international productivity levels/trends; retained series ends 2021, discontinued 2024 |
| J10.1–5 | welfare.html | OBR historical social security, GDP deflator and ONS population; pensioner/non-pensioner not benefit-type split |
| J10.6–7 | welfare.html | DWP Spring Forecast 2026 Table 1a plus Non-DWP Welfare for 2021-22; mixed UK/GB coverage; 1955-56 Table 1a alone is different |
| J6.1–8 | high-earners.html | HMRC SPI Table 3.3, OBR behaviour/costing and forecast evaluation; leaver arithmetic is hypothetical, not a forecast |

## Corrections and verification boundary

J4.3 preserves the former 46.0% premise in withdrawn history and tests the
prominent sourced limitation. No 44.93% replacement is established. J11.9
retains its original people-age wording in history and corrects it to the EHS
household population. J10.6–7 now name non-DWP welfare in the denominator,
without changing amounts or rankings, with a dated public correction.
J2.4's option now says “the official sources the site uses”, not all possible
official sources. J12's reading explicitly permits sourced limitations under
the approved scope; its original job-security question remains unchanged.

Relevant existing independent source regressions include
`test_household_shares.py`, `test_fiscal_conformance.py`,
`test_nationality.py`, `test_defence_comparison.py`,
`test_housing_history.py`, `test_age_pay_security.py`,
`test_life_expectancy.py`, `test_tax_comparison.py` and the source/calculation
checks in `make verify`. `test_johns_questions.py` adds baseline reconciliation,
history requirements, zero-open inventory and nonblank-evidence negatives.
`test_answer_navigation.py` covers recent navigation repairs.

Run `johns_questions.py check`, `gaps`, `pack` and `groups` on the same built
candidate. These establish inventory and text consistency, not comprehension.
Fresh independent final reader sessions, source/adversarial checks and live
qualification remain required. Agent results are simulated, not human evidence.
