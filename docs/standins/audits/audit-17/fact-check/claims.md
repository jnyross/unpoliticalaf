# Audit 17: adversarial fact-check

Built site: `site/` at commit f113d8a. Evidence comes from the built HTML, `site/data/facts.json`, the figure records in `site/figures/`, and the local copies of source files those records name. Each record gives a SHA-256 for its copy: `data/raw/OBR_Historical_public_finances_database.xlsx`, `data/fetched/ons/icproductivityupdated.xlsx`, `data/payers/raw/ons-etb-fye2024.xlsx` and `data/fetched/ott/ukresidents2025annual.xlsx`. I did not use the web. No build was run.

Coverage note: four of the eight new pages have no `data-fact` markup at all: immigration.html, leaving-uk.html, manifesto.html and economy-options.html. They are made of quotations and plain text, so none of their claims can go into ids.txt or into the accuracy workflow. I checked them by hand below. 13 of the 30 ids come from the new pages that do have markup: defence, high-earners, productivity and welfare.

Summary: **1 material, 13 minor**. One further item cannot be checked.

## The 30 claims (ids.txt order)

| # | id | Page | Claim as stated | Context check (things a number check cannot catch) |
|---|----|------|-----------------|------------------------------------------------------|
| 1 | defence.1pct.2025-26 | defence | "Each extra 1% of GDP … about £30.7bn a year at 2025-26 levels" | It is 1% of OBR nominal GDP of £3,069.8bn, from the October 2026 databank. Period and units are right. OK |
| 2 | defence.1pct.taxshare.2025-26 | defence | "about 2.8% of all tax receipts" | The denominator is national accounts taxes (£1,104.7bn), not public sector current receipts. high-earners uses current receipts for its "share of receipts", so the two pages use different denominators. Each is labelled correctly. OK |
| 3 | defence.realchange.2010 | defence | "After inflation the rise was 10.8%, from £59.0bn to £65.4bn" | Both figures are PESA 4_3 at 2025-26 prices, so the base is consistent. The calculation (65.4/59.0−1) is right. OK |
| 4 | intl.fn.GF02.GBR.2024 | defence | "2.3% of GDP on the OECD's measure, the second highest of the 6 G7 countries with a figure" | This is calendar 2024 on the COFOG measure, while the PESA figures above are for financial years. The page says so. Canada is missing and the page says so. The ranking matches the bars. OK |
| 5 | spi.ge1m.taxbn | high-earners | "26,000 taxpayers had total income of £1 million or more … paid £27.7bn of Income Tax, 10.1% of the total" | Source is SPI 2023-24, Table 3.3, covering taxpayers only. The page says this. OK |
| 6 | spi.ge1m.avgtax | high-earners | "On average each paid £1,065,385 a year" | **Minor: false precision.** This is £27,700m divided by 26 thousand, and both inputs are published rounded. If the count were anywhere from 25,500 to 26,500, the average would run from about £1.045m to £1.086m. Showing it to the pound overstates how precise it is. The same applies to £530,000 and £136,297 |
| 7 | wif.yard.bn | high-earners | "One per cent of receipts was £11.0bn in 2023-24 … about 10,000 leavers (40%) … about 80,000 from the £150,000 group (12%)" | The arithmetic checks: 11.0/1.065 is about 10,300, and 11.0/0.136 is about 80,700. OK. See finding m2 for the overlap wording on the same page |
| 8 | prod.change.GBR.2021 | productivity | "UK output per hour rose by 3.9% between 2008 and 2021" | This is the CVM index (Table_7) rebased to 2008. Table_7 is headed 2019=100. OK |
| 9 | prod.change.avg5.2021 | productivity | "The other five G7 countries … rose by 10.3% on average" | Japan is excluded from the average in every year (the 2020 formula checked as well), so the group stays the same over time. It is a simple average and the page says so. OK. See finding m9 for the source label |
| 10 | wel.real.social.2021-22 | welfare | "£31.7bn in 1955-56 and £307bn in 2021-22, both after inflation" | **Minor (m3):** the headline compares two years that sit either side of the 2020-21 break the page draws, although the page says "values either side are not compared". The OBR notes also show that the break is misdescribed (see m3) |
| 11 | wel.gdp.social.2012-13 | welfare | "peaked at 12.4% in 2012-13" | Within 1955-56 to 2019-20, 12.4% is the highest value, so "peaked" holds. 2020-21 is 12.0%. OK |
| 12 | wel.penssh.2021-22 | welfare | "Pensioners received 54% … in 2021-22, against 59% in 1978-79" | The pensioner and non-pensioner split is IFS data throughout (OBR notes), so this comparison does not cross a source change. OK |
| 13 | wel.real.social.2007-08 | welfare (table) | £283.7bn in 2007-08, after £249.2bn in 2006-07 | **Minor (m4):** an unflagged step in the series. See m4 |
| 14 | spend.cash.tme.2025-26 | index, spending | "£1,360bn … in 2025-26" | This is PESA TME. taxes.html uses OBR TME of £1,366bn "on this basis". Both are labelled. OK |
| 15 | spend.per100.social.2025-26 | index, spending | "£33 of every £100 spent on services … the largest area" | The share is of £1,227.6bn of spending split by function, not of TME. It is the largest of the 10 COFOG areas. OK |
| 16 | spend.per100.debt_interest.2025-26 | index, spending | "£11 [of £13 general public services] is interest paid on debt" | Gross interest, inside general public services in PESA. The page explains that net interest is lower. OK |
| 17 | spend.perhousehold.social.2025-26 | spending | "£14,043 per household" | The denominator is 29.0m UK private households (LFS, April to June 2025). Spending covers everyone, including people not in private households. This is noted. OK |
| 18 | rec.taxes.2025-26 | index, taxes | "Taxes raised £1,105bn in 2025-26" | National accounts taxes, OBR October 2026. 2025-26 is marked outturn. OK |
| 19 | rec.big3share.2025-26 | index, taxes | "Income Tax, NI and VAT raised 65%" | 64.6%, which rounds to 65%. The bars show 30, 19 and 16, which also sum to 65. OK |
| 20 | agg.psnb.2025-26 | index, taxes | "Borrowing added another £134bn" | PSNB from the OBR databank. OK |
| 21 | hmrc.share.top1.2023 to 2024 | index, who-pays | "The top 1% … owed 27.2% of all Income Tax in 2023 to 2024" | HMRC Table 2.4 (July 2026), taxpayers only. 2023-24 is outturn and later years are projections. OK. See m5 for the time-series claim on who-pays |
| 22 | etb.t8.gross.all.all | index, household-tax | "Taxes took 33.6% of gross household income on average in 2023/24" | ETB FYE2024 Table 8, covering individuals in private households. OK |
| 23 | etb.2a.alltax.q1 | who-pays | "£8,625 a year in all taxes, on average, for the lowest-income fifth of people" | **Minor (m6):** this is a household-level amount. The ETB Table 2a title reads "Average household … taxes … of all individuals", and the fact's unit is "£ a year per household". The headline tile reads as if it were per person |
| 24 | etb.2a.taxshare.q5 | who-pays | "46.0% share of all taxes paid by UK households … the richest fifth paid it" | **Minor (m7):** the method mixes weights. See m7 |
| 25 | borrow.imf.GBR.2024 | borrowing, defence | "101.3% of GDP, the second lowest of the seven G7" | IMF WEO 2024. Only Germany (63.9%) is lower. OK |
| 26 | borrow.yield.GBR.2025 | borrowing | "averaged 4.58% … the highest of the G7"; Sept 2026 5.24%, "the highest" | I checked against the other six G7 countries' facts: the US is next at 4.29% (2025) and 4.99% (Sept 2026). OK |
| 27 | earn.real.ft.2021 | index, life/earnings | "After inflation, pay in April 2025 was about the same as in April 2021" (£761 against £767) | CPIH-deflated. The comparison stays inside the SOC2020 stretch. OK |
| 28 | house.owners.2024 | index, life | "65% of households in England owned their home, 2024-25" | EHS, England only, labelled correctly. OK |
| 29 | hol.abroad.per100.2025 | life | "58.4 million holiday visits abroad, about 86 for every 100 residents" | Table 2 of the OTT 2025 file covers GB residents. The denominator is GB mid-2025 population (67.56m), so place and population match. The small chart uses UK residents up to 2023, and the page says so. OK |
| 30 | afford.ratio.ew.2025 | life/house-prices, generations | "7.55 times a year's earnings, compared with 3.89 in 1999, the first year measured the same way" | The 1997–98 ratios use annualised weekly pay, and the page breaks the line at 1999. Workplace-based earnings for England and Wales. OK |

## Findings

### Material

**M1. economy-options.html: the triple lock entry contradicts itself.** The option is titled "Keeping the state pension triple lock (reforming it to earnings uprating)". Its budget line says "Saves about £16 billion a year against earnings uprating", and the next sentence says keeping the triple lock "would cost about £20 billion a year". The title names both keeping and reforming. The saving is then measured "against earnings uprating", so it reads as if keeping the triple lock saves £16bn. Read the other way, moving to earnings uprating would be what saves money. A reader can come away with the direction of the effect reversed. Nothing on the page is marked up and there is no figure record for the IFS source, so the £16bn and £20bn figures themselves cannot be checked here.

### Minor

**m1. economy-options.html: the title says "ten options" but the page lists 11.** It has 6 ranked options, 4 budget items (triple lock, property levy, stamp duty abolition, tax reliefs) and 1 unranked item (grid). Two sources in the list are never used in the body: "OBR, Fiscal risks and sustainability, July 2023" and "Resolution Foundation, Broken housing taxes".

**m2. high-earners.html: "the top 1% includes some people with £150,000 and over".** On the same site, who-pays.html gives the top 1% threshold for 2023-24 as £207,000 (hmrc.threshold.top1, Table 2.4). The £150,000+ group is 1.87% of taxpayers (spi.ge150k.sh_n). So the top 1% is almost entirely inside the £150,000+ group, not just "some" of it. The wording understates how much the two groups overlap. The two HMRC tables use slightly different income definitions, so the overlap is close to complete rather than exact.

**m3. welfare.html: the source break is misdescribed, and the headline crosses it.** The page splits every line at 2020-21 with the label "Source changes to HM Treasury PESA", and its limits say "IFS figures from 1955-56 and HM Treasury figures from 2020-21". The OBR database notes (Contents sheet) say instead: "Social Security uses IFS data from 1955-56 to 2021-22". Pensioner and non-pensioner figures are IFS from 1978-79 to 2021-22. Total public sector spending switches from IFS to *OBR* data, not PESA, from 2020-21. So for the amount, per-person and GDP-share views of social security, there is no source change at 2020-21. Only the "share of all spending" denominator changes, and it changes to OBR, not to HM Treasury. The page's opening summary also compares 1955-56 with 2021-22 (£31.7bn against £307bn, 13.6% against 24.3%) across the very break it tells readers not to compare across.

**m4. welfare.html: an unflagged step in 2007-08.** In the source (`Spending (£m)` col I, rows 313–314), social security rises in cash from £152.3bn (2006-07) to £176.7bn (2007-08), +16%. In the same year "Other public sector spending" falls from £210.5bn to £205.2bn. On the page that is +13.8% after inflation in one year (£249.2bn to £283.7bn), then a fall to £272.1bn in 2008-09. Share of GDP goes from 10.2% to 11.3% to 11.1%. The pattern (a jump, then a partial fall back, with an offsetting move in the residual) looks like a change of coverage or classification inside the IFS series, not a real change in spending. The page gives the series as continuous ("rising in most years") up to 2019-20. It needs checking against the IFS spending-composition notes. I rate it minor only because I cannot prove a break from the files I can read.

**m5. who-pays.html: "higher than their share of income in every year from 1999-00 to 2023-24".** The same chart says "No figure for 2008-09". "Every year" should be "every year with a figure".

**m6. who-pays.html: the £8,625 tile reads as per person.** The tile says "£8,625 a year in all taxes, on average, for the lowest-income fifth of people". It is the average *household's* taxes for people in that fifth (ETB Table 2a, "Average household incomes, taxes and benefits … of all individuals"). The table further down labels it correctly. The headline tile does not.

**m7. who-pays.html: the 46.0% share mixes person and household weights.** Table 2a averages are taken across individuals: each person carries their household's tax. The site multiplies that average by the *number of households* in each fifth (fact note on etb.2a.hhtax.q5). Because larger households are over-weighted in an average taken across people, the product is not a household total. Weighting by people instead (each fifth holds about 13.4m) gives 51,903 / 115,526 = 44.9%. Both methods give "about 45–46%", but the method is internally inconsistent. The page explains the method, so this is minor.

**m8. household-tax.html: stray text.** The "Why the same tax can look bigger or smaller" section contains "Cash and prices: pay up 50%, prices up 40%, buys about 7% more (1.50 ÷ 1.40 ≈ 1.07), not 10%. Made-up numbers." It has nothing to do with indirect taxes and looks like a misplaced snippet.

**m9. productivity.html: the source label.** The page and the figure record call the dataset "final estimates", but its URL path is `internationalcomparisonsofproductivityfirstestimates`. Its cover sheet gives publication on 11 January 2023 with "Next release: TBC". Separately, levels come from Table_9, which uses "component" hours. The workbook's Guidance says the UK takes OECD hours, with growth from the UK LFS for 2020 and 2021. The page instead says UK hours come "from the EU Labour Force Survey". That wording is not supported by anything in the workbook I could read.

**m10. economy-options.html: the net migration entry is inconsistent.** Per person is given as "Largely unchanged (the OBR's own figure)". The confidence line says "the per-person effect is zero", and "How the ranking works" says the OBR figure "gives no change in GDP per person. A ranking by GDP per person would put it last". immigration.html quotes the OBR (March 2026) saying the per-person effect was "either slightly positive or slightly negative". Every other ranked option has "Per person: Not given", so the claim that it would rank "last" on GDP per person is unsupported.

**m11. leaving-uk.html: "Income Tax paid by that group rose".** The HMRC figure quoted (£9.7bn, +6%) is for "non-domiciled *and deemed domiciled* taxpayers". The summary bullet treats it as the non-dom group alone.

**m12. manifesto.html: the debt rule year is not shown.** The rating "on course" for debt falling as a share of GDP rests on the rule year, 2029-30, as the page states. But the page quotes PSNFL only for 2025-26, the 2027-28 peak and 2030-31. It does not give the 2029-30 figure the rule depends on.

**m13. Coverage gap: four new pages have no data markup.** immigration.html, leaving-uk.html, manifesto.html and economy-options.html contain many figures (642,000 emigrants, 171,000 net migration, 65.2% within 18 weeks, 437,900 homes, £207bn of reliefs and others) with no `data-fact` id. They cannot be re-downloaded and compared by the accuracy workflow. Only manifesto and economy-options have no figure records at all. The ONS, MAC, OBR and HMRC quotations on the other two pages do cite source records.

### Not checkable

- immigration.html says "The £40 figure comes from the OBR's central forecast with about 350,000 more net migration by 2028-29". The 350,000 is not in the quoted OBR text, and I could not reach the box itself through the figure records offline. It may be a gloss with no source.
- manifesto.html: the pledge ratings, the NATO 2.56% and 2.32% figures, NHS RTT 65.2% and 61.0%, 437,900 homes, £21.7bn headroom, the change of prime minister on 20 July 2026, and the dividend, savings and property rates. None has a figure record. Internal arithmetic checks: 437.9k/1.5m = 29%, 65.2−61.0 = 4.2pp, and the counts 3 kept + 2 partly + 1 not kept + 4 untestable = 10.
- economy-options.html: the OECD, Resolution Foundation, CBI and IFS figures have no figure records. Internal arithmetic checks: 2.1+1.4+0.5 = 4.0, and £290m/£3tn × 10 is about 0.1%.
