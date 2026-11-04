# Fact-check: 30 headline claims (audit-15)

Checker: independent fact-checker, 2026-11-04. Read only the built pages in `site/`, the figure records in `site/figures/`, and official sources (fetched via the web; direct downloads from ons.gov.uk, gov.uk and similar were blocked in this environment, so sources were read through a web-scraping service, mostly the publishers' HTML bulletins and PDFs rather than the spreadsheets).

Ids are in `ids.txt` (one per line, same order as below). "Record" = the page in `site/figures/`. "Source check" = what the official publication says.

**Summary: 0 material findings, 5 minor findings** (listed at the end, F1 to F5).

---

## Public money

1. **`spend.cash.tme.2025-26`**: "£1,360bn spent by the UK public sector in 2025-26" (index.html, spending.html).
   Record: PESA 2026 Ch.4, sheet 4_2 X27, £1,360.1bn. The PESA 2026 page (16 July 2026) links the same Chapter 4 file. Period and population are right (UK, whole public sector). The taxes page uses the OBR's different TME (£1,366bn) and says "on this basis". No issue.

2. **`spend.per100.social.2025-26`**: "Social protection takes the largest share: £33 of every £100 spent on services" (index, spending).
   407.3 ÷ 1,227.6 = 33.18. It is the largest of the ten areas in the table, and spending-areas.html says it was largest in every year from 2003-04, which matches its panel. The denominator is services (£1,228bn), not total spending, and the pages say so. No issue.

3. **`spend.per100.health.2025-26`**: "Health £21 of every £100 … the next largest" (spending).
   257.5 ÷ 1,227.6 = 20.98. It is second in the table. No issue.

4. **`spend.per100.debt_interest.2025-26`**: "£11 of every £100 is interest paid on debt, counted before interest received" (index, spending).
   Record: debt interest ÷ services = 10.61, so about £130bn. The page also gives £9.6 per £100 of total spending and makes clear it is gross, not the net OBR/IFS figure. No issue.

5. **`spend.perhousehold.tme.2025-26`**: "£46,895 per UK household" (spending table).
   1,360.1bn ÷ 29.003m households (LFS, April to June 2025, record hh.uk.2025) = £46,896. It is labelled "not anyone's bill". No issue.

6. **`rec.taxes.2025-26`**: "£1,105bn raised in taxes in 2025-26" (index, taxes).
   Record: OBR databank Oct 2026, Receipts AH33, £1,104.686bn. The named lines plus "all other taxes" add up to £1,104.7bn, and adding non-tax receipts gives £1,231.3bn. No issue.

7. **`rec.big3share.2025-26`**: "Income Tax, NI and VAT raised 65% of all tax" (index, taxes).
   (329.3 + 204.4 + 180.3) ÷ 1,104.7 = 64.6%. The rounded shares 30/19/16 are also right (29.8, 18.50, 16.3). No issue.

8. **`agg.psnb.2025-26`**: "Borrowing added another £134bn" (index, taxes).
   Record: OBR, £134.286bn. ONS PSF September 2026 says "The public sector borrowed £134.2 billion in the financial year ending March 2026". Spending £1,365.6bn minus receipts £1,231.3bn = £134.3bn. No issue.

9. **`agg.psnd.2025-26`**: "Debt … £2,917bn at the end of March 2026" (taxes).
   Record: OBR, £2,916.8bn. It is consistent with ONS PSF September 2026 (£3,005.0bn at end September 2026, £91.7bn more than a year earlier). No issue.

10. **`gdp.psnd.2025-26`**: "equal to 93.3% of GDP (the OBR's measure, GDP centred on end-March)" (taxes).
    Record: OBR Aggregates (% GDP) X82, 93.3. The measure is explained correctly on the page. No issue.

11. **`rec.perhousehold.taxes.2025-26`**: "about £38,089 per household, or £732 a week" (taxes).
    1,104.686bn ÷ 29.003m = £38,089, and ÷ 52 = £732. The page says clearly that this is not anyone's tax bill and includes business taxes. No issue.

12. **`rec.gdp.taxes.2025-26`**: "Taxes alone were 36.0% of GDP in 2025-26, a share news reports often call the 'tax burden'" (taxes).
    Record: rec.taxes ÷ OBR cash GDP = 35.99%. No issue.

13. **`hmrc.share.top1.2023 to 2024`**: "The top 1% of Income Tax payers owed 27.2% of all Income Tax in 2023 to 2024" (index, who-pays).
    HMRC Income Tax liabilities commentary (published 15 July 2026): "the top 1% were liable for around 27.2%". It covers taxpayers only, which the page says. The page's 2021-22 peak of 30.7%, the 2026-27 projection of 26.6% and the quoted explanation all match the commentary. No issue.

14. **`hmrc.income.top1.2023 to 2024`**: "They had 12.4% of all Income Tax payers' income" (index, who-pays).
    HMRC: "the top 1% accounted for 12.4%". Note: HMRC's own commentary also says the top 1% income share "decreases by 0.3 percentage points to 12.8%" by 2026-27, which contradicts its 12.4%. The site's figures (12.4% for 2023-24, 12.8% projected) follow the tables. The inconsistency is HMRC's, not the site's. No issue.

15. **`etb.t8.gross.all.all`**: "Taxes took 33.6% of gross household income on average in 2023/24 … an average across all people, not anyone's tax rate" (index, household-tax).
    Record: ETB FYE2024 Table 8 I15. The population (people in UK private households, ranked into fifths of people) is stated correctly. The year-on-year comparison on household-tax.html (direct taxes 22.9% vs 23.2% in 2022/23) uses the same people-based method (etbp series), so it is not a comparison across the 2018/19 break. No issue.

16. **`etb.t8.gross.all.q1`**: "The lowest-income fifth paid 36.7% of its gross income in tax" (index, household-tax, who-pays).
    Record: Table 8 D15. The page's explanation that indirect tax (21.0%) makes up most of it is consistent with Table 8 (direct 15.7%). No issue.

17. **`etb.t8.gross.all.q5`**: "the highest-income fifth paid 36.2%" (index, household-tax).
    Record: Table 8 H15. The claim "less than one percentage point apart" (36.7 vs 36.2) is right. No issue.

18. **`etb.t16.all.2023/24`**: "In 2023/24, 53.3% of people lived in households that received more in benefits and services than they paid in taxes" (who-pays).
    The ONS FYE2024 bulletin says "53.3% of people lived in households that were net recipients". The page's 90.1% (retired) and 45.8% (non-retired) also match. See F4 for a separate definitional point. No issue with this number.

## Everyday life

19. **`work.rate.2026`**: "75.1% of people aged 16 to 64 were in work, April to June 2026, UK" (index, life/work).
    ONS LF24 series: 2026 Q2 = 75.1. The period is labelled. (A later rolling quarter, June to August 2026, at 75.3%, was published on 20 October 2026. The site uses April to June consistently, so this is not counted as a finding.)

20. **`work.rate.2025`**: "In April to June 2025, 75.3% … higher than in 51 of the other 54 years shown" (life/index, work).
    LF24 2025 Q2 = 75.3. Recount from the page's own series: only 2018 (75.4), 2019 (76.1) and 2020 (75.4) are higher, so 51 of 54 is right. The 1971 values (pre-1992) come from ONS's modelled back-series, and the page notes that the survey was not quarterly before 1992. No issue.

21. **`earn.real.ft.2021`**: "April 2021 £761 (in April 2025 prices)" (index, life/index, earnings).
    £609.8 × CPIH Apr 2025 (137.7) ÷ CPIH Apr 2021 (110.4) = £760.6. The CPIH values were checked against ONS L522. The comparison starts in 2021 because of the SOC 2020 recoding, which is right. See F1.

22. **`earn.real.ft.2025`**: "April 2025 £767 … about the same (+0.8%) … the highest of the 5 years measured the same way" (index, life/index, earnings).
    The ONS ASHE 2026 bulletin confirms £766.60 for April 2025. 767 ÷ 761 = +0.8%. Within 2021 to 2025 it is the highest (2021 is £761). The rank claim is correct. **F1**: the page calls 2025 "provisional", but ASHE 2026 was published on about 22 October 2026, so it no longer is, and April 2026 (£811.20) now exists.

23. **`house.owners.2024`**: "65% of households in England owned their home, 2024-25 … higher than in 10 of the other 16 years measured the same way" (index, life/index, housing).
    The EHS 2024-25 Headline Report says "Owner occupation … (65% of households)". Recount from the page's EHS series 2008-09 to 2024-25 (outright plus mortgage): the years below 64.83% are 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022 and 2023, which is 10. Right. The place (England, not UK) is stated. No issue.

24. **`house.rent.private.2024`**: "The average private rent was £250 a week" (life/index, housing).
    EHS headline report: "The average (mean) weekly private rent (£250)". The social rent of £129 and mean mortgage payment of £242 also match the report, and they are labelled cash, England, mean. No issue.

25. **`hol.world.holiday.2025`**: "58.4 million holiday visits abroad by Great Britain residents in 2025" (index, life/index, holidays).
    Record: Travel trends 2025 tables, sheet 2 C48, GB residents, holiday. ONS Travel trends 2025 (16 Oct 2026) confirms the GB breakdown and new method. Spain, France and Italy as the top countries for all visits (19.1m, 9.1m, 5.7m) match the ONS text. The comparison with 2019 (UK residents, old method) is explicitly marked as not compared. See F2 and F3.

26. **`hol.abroad.per100.2025`**: "about 86 for every 100 residents" (life/index, holidays).
    58.396m ÷ GB population mid-2025 (67.5555m) × 100 = 86.4. The numerator and denominator are both GB, which is right. No issue.

27. **`hol.gb.holiday.2025`**: "Great Britain residents also took 32.1 million overnight holiday trips within Great Britain" (life/index, holidays).
    GBTS "Domestic tourism: Q4 2025 and 2025" (VisitBritain PDF, 11 June 2026), Britain table, Holidays, 2025 visits = 32.1 (2024: 32.5). The record's "read from" note mentions the 'Holidays Q4 2024' line, but the value is the 2025 annual column and is correct. VisitBritain notes a comparability adjustment applied to Q4 2025, which is not mentioned on the page; that is immaterial. No issue.

28. **`school.primary.2026`**: "26.1 pupils in the average state primary school class in England, January 2026" (index, schools).
    DfE Schools, pupils and their characteristics 2025/26: "The average primary class size has decreased slightly by 0.3 to 26.1". Secondary 22.6 and infant pupils in classes over 30 (2.7%) also match. The 2025 figure of 26.4 on life/index ("higher than in 4 of the other 19 years, level with 1") recounts correctly: 2006 to 2009 lower, 2010 level. No issue.

29. **`borrow.yield.GBR.2025`**: "the market rate for new 10-year UK government borrowing averaged 4.58% a year [in 2025], the highest of the G7" (borrowing).
    Record: OECD long-term interest rates, 4.5822. Against the page's other G7 values (USA 4.29, ITA 3.59, FRA 3.37, CAN 3.23, DEU 2.61, JPN 1.55) the UK is highest. September 2026 (5.24% vs USA 4.99%) is also highest. This was not independently re-downloaded. No issue found.

30. **`borrow.imf.GBR.2024`**: "In 2024, UK government debt was 101.3% of GDP, the second lowest of the seven G7 countries" (borrowing).
    Record: IMF WEO GG_DEBT_GDP 101.29. On the page's values only Germany (63.9) is lower, so "second lowest" is right. The OECD measure (92.5%) gives the same ranking, and the two measures are explained. No issue.

---

## Findings

### Material
None found.

### Minor

- **F1: Earnings "provisional" label out of date; latest year missing** (index.html "The 2025 figure is provisional."; life/earnings.html "(provisional)"; life/index.html).
  ONS published "Employee earnings in the UK: 2026" (ASHE 2026) on about 22 October 2026. It gives April 2025 as £766.60 (now revised, unchanged) and April 2026 as £811.20 (+5.8% cash). So 2025 is no longer provisional, and a newer year exists that the pay-after-inflation headline does not use, even though the work and class-size tiles already show 2026. The 2021 to 2025 comparison itself is still correct. Evidence: ONS bulletin annualsurveyofhoursandearnings/2026: "Median weekly earnings for full-time employees were £811.20 in April 2026, compared with £766.60 in April 2025."

- **F2: "Series ends in 2023" / "From 2024 visits abroad are counted for Great Britain residents"** (index.html holidays tile: "1980 to 2023, when that series ends"; life/holidays.html notes).
  ONS still publishes UK-resident totals under the new method (Travel trends 2025: "UK residents made an estimated 99.9 million visits abroad in 2025 … of [which] 95.5 million were by residents of GB"; 94.6 million in 2024). What ended is the International Passenger Survey method, not UK-resident counting. Stopping the comparable series at 2023 is a fair choice, but the wording suggests that no UK figure exists after 2023.

- **F3: Source record says the wrong population** (site/figures/ott-2025.html header: "Where: United Kingdom residents").
  The figures used from it (hol.world.holiday.2025, hol.cty.*.holiday.2025, hol.europeshare.2025) are Great Britain residents, as their own notes and the page text say. This is a metadata inconsistency only.

- **F4: Definition of direct taxes incomplete** (who-pays.html section 2: "Direct taxes: Income Tax, employee National Insurance and Council Tax (after reductions)").
  The ONS FYE2024 bulletin defines direct taxes as including "Income Tax, National Insurance contributions, student loan repayments and Council Tax (less Council Tax benefits or rebates)". Student loan repayments are left out of the site's description. The numbers are ONS's own, so only the explanation is affected.

- **F5: Chart headline smooths over real falls** (life/holidays.html: "Visits abroad per 100 residents rose until 2019, fell until 2021 …").
  The page's own table shows falls before 2019: 2008 112 to 2009 102, and 2011 107 to 2012 105 (also 1984 39 to 1985 38). "Rose until 2019" overstates how steady the rise was. A similar but milder smoothing is in life/schools.html: "Primary class sizes … held level until 2019, then fell", although 2022 to 2023 rose (26.6 to 26.7). DfE describes 2020/21 to 2023/24 as "a period of stability".

## Checked and not counted
- PESA total spending (£1,360.1bn, spending page) and OBR total spending (£1,365.6bn, taxes page) differ. Both are labelled with their basis.
- The HMRC commentary contradicts itself on the top 1% income share (12.4% vs "decreases by 0.3 points to 12.8%"). This is the publisher's error, not the site's.
- I could not verify one quote on spending.html word for word ("The interest payable on debt increased to £106.6 billion, £34.0 billion (46.9%) more…", ONS PSF March 2023) with the tools available. The bulletin does mention the £34.0 billion increase. The auditor may want to check the exact wording.
