# Life-topic source and period inventory

Checked 10 November 2026 against the retained official files, after the 2026
explorer and question integrations. No dataset, vintage, fact ID or observation
was replaced in this check. Missing denominators now leave occupation and
child-household shares missing rather than crashing or treating a gap as zero.

## Retained coverage

Years below are observation keys, not a claim that every series is annual or
complete. England housing keys name the **start** of the survey year.

| Topic and series | Coverage and splits retained | Meaning and boundaries |
| --- | --- | --- |
| Work, `work.rate/men/women/level` | 1971–2026; total and sex rates, people employed | UK LFS, April–June. Rates: ages 16–64; level: ages 16+. |
| Work, `work.ft/pt/ptshare/age` | 1992–2026; full/part-time and ages 18–24, 25–34, 35–49, 50–64, 65+ | UK LFS, April–June; part-time share uses full-time plus part-time people, not jobs. |
| Work, `work.occ/occshare` | SOC2010 and SOC2020, nine major groups plus total; displayed from 2011 | APS calendar years, not the UK quarterly rate. 2021 appears on both classifications; no cross-classification change. No 2026 rows. |
| Work, `work.place` | 2008–2025; UK, four nations and nine English regions | APS calendar years; no 2026 fill. Recent LFS/APS response/sample uncertainty stays explicit. |
| Industry, `jobs.total/ind/share/people/gap` | 1978–2026; 20 SIC2007 sections A–T | June UK workforce jobs, seasonally adjusted; industry shares divide by jobs, not people. LFS people are separately labelled; the difference is not a count of second-job holders. |
| Housing tenure, `house.outright/mortgage/owners/social/private` | 2008–09 to 2024–25; England households | EHS, not individual ownership. Historical LFS 1981–2008 retains only 21 observed years and its separate calendar-year/survey basis. |
| Housing with children, `house.kids/kidsk` | 2008–09 to 2024–25; owners/social/private and underlying counts | Adds couples, single lone parents and previously married lone parents with dependent children; denominator is those households, not all people or all households. |
| Housing costs, `house.rent/mortpay/real` | 2008–09 to 2024–25; social/private rent and mortgage payments | Paying-household means, rent before housing support; mortgage row is all mortgage types including shared owners. Real values use mean April–March CPIH, 2024–25 prices, not April earnings CPIH. |
| Housing space, `house.crowd/rooms/rooms5` | Overcrowding endpoints 2008–09 to 2022–23; rooms 2008–09 to 2024–25 | Bedroom-standard overcrowding is a three-survey-year average for owners/social/private/all, never an annual point or a second average. Seven room bands; utility-room definition changes in 2011–12. |
| Housing place/nation, `house.reg/nat` | England/regions and Wales/Scotland through 2025; NI 2012–2024 | England/regions: dwellings at 31 March. Other nations keep their own counts, dates and definitions; not spliced into a UK household series. |
| Affordability, `afford.price/earn/ratio/deposit/depamt` | 1997–2025; England, Wales, combined area and English regions | Year-ending-September prices / April workplace full-time gross annual pay. 1997–98 annualised-weekly basis is separate. Ten-percent deposit is an illustration, not observed saving time. |
| Housing buyers and mortgages | Existing first-buyer age, owner-age bands, mortgage-income share, effective and quoted rates retained | HRP household age is not exact-age personal ownership; 1991 household-head LFS differs from EHS. Mortgage share is gross income from 2010–11, not take-home or 2008–09. Quoted IUMBV34 from 2008 and effective CFMZ6JM from 2016 are distinct. See `tests/test_housing_history.py`. |
| Overseas visits, `hol.world/europe/namerica/other` | 2009–2025; holiday, family/friends, business, all purposes | Thousands of visits, not people. 2020 individual-purpose counts are January–mid-March `.part` records only; annual values for those purposes stay missing, but the annual all-purpose total is published. Historical `hol.ips.all/per100` preserves all-purpose 1980–2023. |
| Overseas countries, `hol.cty` | Existing country detail, all-purpose 2009–2025 except 2020; holiday-only 2024–2025 | All-purpose ranking is not holiday-only ranking. UK residents through 2023; GB residents from 2024. Mixed-method 2024 is compared with neither earlier years nor 2025. |
| Domestic, `hol.gb.holiday/per100` | 2019, 2022–2025 | GB overnight holiday trips, not people; 2019 survey method kept separate. No full-year 2020/2021. Overseas per100 uses the matching UK/GB population. |
| Holiday cost/nights, `hol.spend/nights/spendper/real/stay` | 2009–2025, excluding full-year 2020 | Per-visit averages, not typical holidays. Source 2020 cells explicitly say “Not available”. Calendar-year CPIH, 2025 prices; not exchange-rate-adjusted foreign prices. |
| Holiday affordability, `holafford` | 2005–2018; all, low/other income, with/without dependent children | EU-SILC share of people whose household cannot afford a week away, not a traveller participation rate. Publisher break flags and UK end date retained. |
| England classes, `school.primary/secondary/large` | January 2006–2026 | State-funded classes taught by one teacher. 2006–2015 large-class shares add rounded DfE percentages; 2016 onwards use pupil counts. |
| England phases/bands, `school.infant/ks2/pupils` | January 2016–2026; infant, KS2, primary, secondary; ≤30, 31–35, 36+, total and calculated over 30 | Average = pupils/classes; large-class share = pupils in large classes / all pupils, not share of classes. All 176 retained phase-band rows are reopened and checked. Over-30 infant classes are not necessarily unlawful. |
| Nations' classes | Wales infant/junior January 2023–2025; Scotland primary September 2008–2025 | Distinct scopes and census dates; no fabricated NI, Scotland secondary or UK-wide average. |

## Selected 2026 observations and gaps

The eleven retained LFS Q2 series support total/sex, people/full/part-time and all
five existing age bands. Examples: LF24 = 75.1%, MGRZ = 34,469 thousand people,
YCBH = 8,724 thousand. DfE 2025/2026 rows support January 2026 primary 26.1,
secondary 22.6, infant 25.9 and KS2 27.6 pupils per class and all existing bands.
June industry jobs remain at their real period and provisional status.

The integrated 2026 ASHE UK pay and spread keep their provisional status and
April 2026 CPIH base. Places remain at April 2025 provisional. No 2026 APS
occupation/place, housing survey, overseas or domestic full-year total is copied
forward. Annual, pair and range pages retain explicit gaps and method limits,
as tested in `tests/test_year_range.py`.

## Earnings publication-route join

The earnings page links the ONS Table 1 and Nomis dataset descriptions and
explains their common ASHE employee-job population, April gross weekly-pay
measure and matching sex/work-pattern groups. It does not claim household
income or a new survey. This documents the lineage basis rather than claiming a
retained Table 1 2024 pack. The retained ONS 2025 Figure 1 CSV independently
matches Nomis's 2024 revised and 2025 provisional all/full/part-time medians at
Nomis's 10p precision. The current 2025 UK series instead uses the later revised
pack. The existing method/coding cautions still prevent incompatible growth.

## Independent regression population

`tests/test_life_conformance.py` reopens **6,142 nonmissing direct observations**
across work, housing, schools, holidays, industry, affordability and holiday
affordability, using the independent checker, source scale and DfE rounding.
It also checks all 176 DfE rows using pupils and classes, the eleven LFS 2026
rows, the earnings overlap, missing denominators and 2020 travel gaps.
Existing builder, housing-history, earnings and year/range tests cover the
remaining calculations, age/HRP/mortgage definitions, breaks and rendered gaps.
This is retained-source checking, not a claim of a fresh network refresh.
