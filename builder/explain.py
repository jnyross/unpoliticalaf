"""Explanations quoted word for word from official publications.

The site's own text describes figures and does not say why they changed. Where
an official body (ONS, HMRC, a government department) has published its own
explanation, we quote it here, clearly attributed and linked, next to the
figures it explains.

Each quote must appear word for word in the publication's page, kept under
data/fetched/ (downloaded byte for byte by scripts/fetch_sources.py). The build
and builder.check both confirm this, so a quote cannot drift from its source.
"""
import html as _html
import re

from .html import esc
from .readers import ROOT

# id: question shown above the quote, source id (see sources.FETCHED), the
# publication's title and date, the passages quoted (each must appear in the
# source, and they are shown in this order), where it is shown, and for life
# topics the years it applies to on the year pages.
EXPLANATIONS = {
    # ------------------------------------------------------------ spending
    "covid-spending": dict(
        question="Why did spending jump in 2020-21?",
        source="explain-ons-psf-2021-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2021", date="23 April 2021",
        quote=["Central government tax and National Insurance receipts (combined) in the financial year ending (FYE) March 2021 (April 2020 to March 2021) fell by £34.9 billion (or 5.0%) compared with the same period a year earlier, while government support for individuals and businesses during the pandemic contributed to an increase of £203.2 billion (or 27.5%) in central government day-to-day (or current) spending.",
               "This substantial increase largely reflects the impact of the coronavirus pandemic on the public finances, with the furlough schemes alone adding £78.2 billion to borrowing in the FYE March 2021."]),
    "energy-2022": dict(
        question="Why did spending rise again in 2022-23?",
        source="explain-ons-psf-2023-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2023", date="25 April 2023",
        quote=["Central government current expenditure was £967.0 billion in the FYE 2023, an increase of £74.0 billion (8.3%) compared with FYE 2022, reflecting the impact of rising inflation and energy costs.",
               "the steady rise in receipts not enough to offset the £34.0 billion increase in interest payable on the government’s debt and the initally estimated £41.2 billion cost of the combined energy support schemes and other one-off costs."],
        gloss="“FYE 2023” means the financial year ending March 2023, which this site calls 2022-23. The second passage explains the gap between day-to-day spending and receipts that year."),
    "debt-interest-2022": dict(
        question="Why did interest on government debt rise in 2022-23?",
        source="explain-ons-psf-2023-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2023", date="25 April 2023",
        quote=["The interest payable on debt increased to £106.6 billion, £34.0 billion (46.9%) more compared with FYE 2022, as the rises in the Retail Prices Index have increased the interest payable on index-linked gilts."],
        gloss="Index-linked gilts are government bonds whose payments rise with the Retail Prices Index, a measure of inflation. ONS figures for debt interest are measured differently from the HM Treasury figures above, so the amounts differ."),
    # ------------------------------------------------------------ borrowing costs
    "gilt-prices": dict(
        question="What moves the price of UK government bonds?",
        source="explain-dmo-about-gilts", publisher="UK Debt Management Office",
        title="About gilts", date="page undated, downloaded 3 November 2026",
        quote=["Gilt prices change because market pricing changes as views about interest rate prospects and other factors relevant to the capital markets change.",
               "That assessment will be affected by many factors, including the market’s collective view of what will happen to interest rates over future years; of both the level of and uncertainty about inflation in the future; and of other issues, such as the levels of outright supply and the strength and nature of demand from investors."],
        gloss="The Debt Management Office sells gilts for the government. When a gilt's price falls, its yield rises: a buyer pays less for the same fixed payments. “Outright supply” means how many gilts the government sells."),
    "debt-interest-drivers": dict(
        question="How do interest rates and inflation feed into the UK's interest bill?",
        source="explain-obr-debt-interest", publisher="Office for Budget Responsibility",
        title="Debt interest (central government, net of APF)", date="last updated 26 March 2025",
        quote=["a 1 percentage point increase in gilt rates in 2024-25 (which persists in each subsequent year of the forecast) increases debt interest payments by rising amounts over the forecast period, reaching £12.0 billion by the end of the forecast. This increases steadily over time as the rate increase only affects new gilt issuance;",
               "a 1 percentage point increase in RPI inflation in 2024-25 increases debt interest payments by £5.9 billion in the same year and by rising amounts over the forecast period;"],
        gloss="The OBR is the UK's official forecaster of the public finances. The first passage means a rise in yields raises the interest bill slowly, as old gilts are repaid and new ones sold. The second shows how inflation raises it at once, through index-linked gilts, whose payments rise with the Retail Prices Index (RPI)."),
    # ------------------------------------------------------------ fiscal rules
    "defence-fiscal-rule-2025": dict(
        question="What fiscal rule was the government working to in 2025?",
        source="explain-obr-frs-2025", publisher="Office for Budget Responsibility",
        title="Fiscal risks and sustainability – July 2025", date="8 July 2025",
        quote=["In October 2024, the newly elected Government adopted a new fiscal rule targeting public sector net financial liabilities (PSNFL).",
               "the fiscal rule is for PSNFL to be falling as a share of GDP in a particular year of the forecast (currently 2029-30)"],
        gloss="PSNFL is the balance-sheet measure the rule uses. The Budget and Spring Forecast since then may have changed the rule, which this site has not yet checked."),
    "borrowing-costs-2025": dict(
        question="Have borrowing costs risen only in the UK?",
        source="explain-obr-frs-2025", publisher="Office for Budget Responsibility",
        title="Fiscal risks and sustainability – July 2025", date="8 July 2025",
        quote=["There are signs that the scale of public borrowing in the UK and other large, advanced economies is putting global sovereign debt markets under pressure.",
               "Government borrowing costs have risen across the world and long-term gilt yields are now higher in the UK than at any point since the start of the century."],
        gloss="“Sovereign debt” means money borrowed by governments. The OECD figures above show yields in the other G7 countries too."),
    # ------------------------------------------------------------ taxes
    "borrowing-records": dict(
        question="How did borrowing in 2020-21 compare with 2009-10, after the 2008 recession?",
        source="explain-ons-psf-2021-03", publisher="Office for National Statistics",
        title="Public sector finances, UK: March 2021", date="23 April 2021",
        quote=["Borrowing had generally been falling since its peak of £157.7 billion during the financial crisis in the FYE March 2010. However, largely as a result of the impact of the coronavirus pandemic, borrowing in the latest full financial year (April 2020 to March 2021) was nearly double this previous record.",
               "Expressed as a ratio of gross domestic product (GDP), public sector net borrowing (excluding public sector banks, PSNB ex) in the FYE March 2021 was 14.5%, the highest such ratio since the end of World War Two, when in FYE March 1946 it was 15.2%."]),
    "frozen-thresholds": dict(
        question="Why are more people paying Income Tax?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["The total number of Income Tax payers is projected to rise to 40.8 million in 2026 to 2027, mainly due to population and income growth combined with frozen Income Tax thresholds. The Personal Allowance is set at £12,570 in 2021 to 2022 through to 2030 to 2031, due to the extension of the freeze at Autumn Budget 2025."]),
    # ------------------------------------------------------------ who pays
    "top1-share": dict(
        question="Why does the top 1% share go up and down?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["The introduction of the additional rate in 2010 on taxable income over £150,000 led to a behavioural response by individuals bringing forward, or ‘forestalling’, income in 2009 to 2010.",
               "In April 2013, the additional rate was reduced from 50% to 45% which led to the deferral of income from the 2012 to 2013 tax year to the 2013 to 2014 tax year.",
               "The peak in shares of Income Tax liabilities at the top end of the distribution in 2021 to 2022, and subsequent fall in 2022 to 2023 onwards, is also due to the freeze in the higher rate threshold and Personal Allowance. This means there were more Income Tax payers overall in these years, changing the distribution among percentile groups.",
               "In 2023 to 2024, the additional rate threshold was lowered from £150,000 to £125,140. This is estimated to have led to a small amount of forestalled income into 2022 to 2023.",
               "The share of income for higher rate taxpayers with earnings around the new threshold was:",
               "artificially high in 2022 to 2023",
               "artificially low in 2023 to 2024"]),
    "retired-net": dict(
        question="Do retired households get back more than they pay in tax?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["For retired households, 90.1% were net recipients, largely reflecting the 10.1% uprating to state pensions and pension credits (classified as cash benefits)."],
        gloss="“Net recipients” are people in households that receive more in benefits, including services such as the NHS and education, than they pay in taxes."),
    "taxpayers-age": dict(
        question="Why are there more Income Tax payers aged 75 and over?",
        source="explain-hmrc-spi-2324-commentary", publisher="HM Revenue and Customs",
        title="Personal Incomes Statistics 2023 to 2024: commentary", date="29 April 2026",
        quote=["The proportion of taxpayers in the 75 and over range continues to increase, reflecting the UK’s ageing population. 11.6% of taxpayers were in the 75 and over age range in the tax year 2023 to 2024, compared to 10.5% of taxpayers in the tax year 2022 to 2023.",
               "For the 2023 to 2024 tax year, there has also been a revision in the sampling methodology for recipients of the state pension in the SPI. This methodological change has added up to an estimated 196,000 taxpaying state pensioners across the total distribution, with the majority being basic rate taxpayers."],
        gloss="The SPI is HMRC's Survey of Personal Incomes, the source of the figures in this section. The second passage means part of the rise in older taxpayers comes from a change in how the survey counts people receiving the State Pension, not only from changes in people's lives."),
    # ------------------------------------------------------------ household tax
    "average-rates": dict(
        question="How much Income Tax do people at different incomes pay, as a share of their income?",
        source="explain-hmrc-itl-commentary", publisher="HM Revenue and Customs",
        title="Income Tax liabilities statistics: commentary", date="15 July 2026",
        quote=["In 2023 to 2024, the average Income Tax rate was 4.8% for those with incomes from £15,000 to below £20,000, increasing to 9.0% for incomes from £20,000 to below £30,000 and 12.3% for incomes from £30,000 to below £50,000. For incomes within the higher rate tax band, the average Income Tax rate rose to 18.9% for individuals earning between £50,000 and £100,000 and then rose to 29.2% for individuals earning between £100,000 and £150,000."],
        gloss="These are averages for Income Tax payers in each income range, and cover Income Tax only, not National Insurance or taxes on spending."),
    "fiscal-drag": dict(
        question="Why did direct taxes rise in cash in 2023/24?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["Income tax thresholds in FYE 2024 remained at 2022 levels, creating fiscal drag and so increasing households tax liabilities."],
        gloss="“In cash” means the pounds paid rose. As a share of gross income, direct taxes did not rise: the table above (Table 8 of the same survey) shows 22.9% in 2023/24, down from 23.2% in 2022/23. After inflation, the same ONS bulletin says direct taxes fell for the average household."),
    "indirect-spending": dict(
        question="Why can indirect taxes be a large share of income for lower-income households?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["indirect taxes are then paid via expenditure; disposable income minus indirect taxes is referred to as \"post-tax income\", where indirect taxes refer to those on goods and services such as Value Added Tax (VAT), duty on tobacco, alcohol and fuel, and Stamp Duty"],
        gloss="ONS's latest bulletin defines the steps in this order: gross income, then direct taxes, then indirect taxes paid on spending. The table below measures the lowest-income fifth's indirect taxes against gross income, disposable income and spending, so you can see how much the answer depends on the total used."),
    "redistribution": dict(
        question="What do taxes and benefits do to the gap between richer and poorer households?",
        source="explain-ons-etb-latest", publisher="Office for National Statistics",
        title="Effects of taxes and benefits on UK household income: financial year ending 2024", date="25 September 2025",
        quote=["The richest fifth of people's mean equivalised household income before taxes and benefits (£116,600) was 12.2 times larger than the poorest fifth (£9,600); however, this gap reduced to 3.3 times larger (£85,100 and £25,700, respectively) after all taxes and benefits."],
        gloss="“Equivalised” means adjusted for the size of the household. “After all taxes and benefits” includes the value of services such as the NHS and schools."),
    # ------------------------------------------------------------ life: work
    "recession-jobs": dict(
        topic="work", years=range(2008, 2014),
        question="What happened to jobs after the 2008 recession?",
        source="explain-ons-2008-recession", publisher="Office for National Statistics",
        title="The 2008 recession 10 years on", date="30 April 2018",
        quote=["As the economy got smaller, lots of people lost their jobs and employers stopped hiring. By the end of 2011, almost 2.7 million people were looking for work. The quarterly unemployment rate reached 8.4%, the highest rate since 1995."]),
    "lfs-quality": dict(
        topic="work", years=range(2023, 2026),
        question="How reliable are the latest employment figures?",
        source="explain-ons-lmo-latest", publisher="Office for National Statistics",
        title="Labour market overview, UK: October 2026", date="20 October 2026",
        quote=["As part of work to address quality concerns with the LFS, response levels and rates have shown clear improvement, with responses now close to their pre-coronavirus pandemic level.",
               "Estimates from January to March 2025 include the full effect of the improvements in LFS data collection and sampling methods introduced from January 2024 onwards."],
        gloss="The LFS is the Labour Force Survey, the source of the employment rates on this site."),
    # ------------------------------------------------------------ life: earnings
    "recession-pay": dict(
        # Only on the years the pay freeze and cap it names applied to (audit 11 judge, L5).
        topic="earnings", years=range(2011, 2018),
        question="What did the ONS say about pay in the decade after the 2008 recession?",
        source="explain-ons-2008-recession", publisher="Office for National Statistics",
        title="The 2008 recession 10 years on", date="30 April 2018",
        quote=["Earnings have lagged behind prices for most of the decade since the start of the recession. In the public sector, a pay freeze (from 2011) and pay cap (from 2013) kept wage rises below inflation, while in the private sector wage growth was also slow."]),
    "pandemic-pay": dict(
        topic="earnings", years=range(2020, 2023),
        question="Can pay in 2020 and 2021 be compared with other years?",
        source="explain-ons-ashe-2022", publisher="Office for National Statistics",
        title="Employee earnings in the UK: 2022", date="26 October 2022",
        quote=["Over the coronavirus pandemic period, earnings estimates were affected by changes in composition of the workforce and the impact of the Coronavirus Job Retention Scheme (furlough) making interpretation difficult; also data collection disruption and lower response rates mean that, for 2020 and 2021, data were subject to more uncertainty and should be treated with caution; we would encourage users to focus on long-term trends rather than year-on-year changes."]),
    "pay-2022": dict(
        topic="earnings", years=(2022,),
        question="What happened to pay after inflation in 2022?",
        source="explain-ons-ashe-2022", publisher="Office for National Statistics",
        title="Employee earnings in the UK: 2022", date="26 October 2022",
        quote=["Median weekly pay for full-time employees was £640 in April 2022, which is a 5.0% increase over the £610 in 2021. In real terms (that is, adjusted for inflation) in April 2022, median weekly pay for full-time employees fell by 2.6% on the year."]),
    # ------------------------------------------------------------ life: housing
    "tenure-trend": dict(
        topic="housing", years=(),
        question="How have owning and renting changed over the longer run?",
        source="explain-ehs-2024-25-ch1", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 1: profile of households and dwellings", date="9 July 2026",
        quote=["Ownership rates were highest in 2003 at 71% of households but steadily declined post financial crisis in the early 2010’s to a low point in 2013-14 (63%).",
               "Throughout the 1980s and 1990s, the proportion of private rented households was relatively steady at between 9% to 11%. While the sector has doubled in size since the early 2000s, the rate has remained around 19% or 20% since 2013-14."]),
    "outright-owners": dict(
        topic="housing", years=(2024,),
        question="Why do more people now own their home outright?",
        source="explain-ehs-2024-25-ch1", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 1: profile of households and dwellings", date="9 July 2026",
        quote=["The increase in the number and proportion of outright owners is at least partly explained by population ageing, with large numbers of people reaching retirement age, paying off their mortgages and becoming outright owners"]),
    "long-mortgages": dict(
        topic="housing", years=(2024,),
        question="How are first-time buyers paying for their homes?",
        source="explain-ehs-2024-25-ch2", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2024 to 2025 headline findings, chapter 2: housing costs and affordability", date="9 July 2026",
        quote=["Compared to five years ago in 2019-20, the proportion of first time buyers with a mortgage of 30 years or more has increased significantly (from 47% in 2019-20 to 62% in 2024-25)"],
        gloss="First-time buyers here are households that bought their first home in the three years before the survey."),
    "rent-affordability": dict(
        topic="housing", years=(2023,),
        question="How much of their income do lower-income renters spend on rent?",
        source="explain-ehs-2023-24-rented-report", publisher="Ministry of Housing, Communities and Local Government",
        title="English Housing Survey 2023 to 2024: rented sectors", date="17 July 2025",
        quote=["On average, 71% of private renters in the lowest two income quintiles spent more than 30% of their gross household income on rent, compared to 33% of mortgagors and 42% of social renters."],
        gloss="“The lowest two income quintiles” means the 40% of households with the lowest incomes. Mortgagors are people buying their home with a mortgage."),
    # ------------------------------------------------------------ life: holidays
    "pandemic-travel": dict(
        topic="holidays", years=(2020, 2021),
        question="What happened to travel abroad in 2020 and 2021?",
        source="explain-ons-travel-2021", publisher="Office for National Statistics",
        title="Travel trends: 2021", date="15 June 2022",
        quote=["Travel and tourism statistics are usually based on the results of the International Passenger Survey (IPS), but the survey was suspended on 16 March 2020 because of the coronavirus (COVID-19) pandemic. No IPS data were collected from this date until the survey restarted on 18 January 2021.",
               "UK residents made 19.1 million visits abroad in 2021, which was 20% less than the previous year and was because of the continued travel restrictions."]),
    "travel-2022": dict(
        topic="holidays", years=(2022,),
        question="Did holidays go back to normal in 2022?",
        source="explain-ons-travel-2022", publisher="Office for National Statistics",
        title="Travel trends: 2022", date="26 May 2023",
        quote=["The most frequent reason for visits was for holidays, both for UK residents visiting abroad and overseas residents visiting the UK; this has reverted to a more traditional reason after the coronavirus pandemic, when the most common reason for travel was to see friends and relatives."]),
    "travel-method-2024": dict(
        topic="holidays", years=(2024, 2025),
        question="Why can't 2024 be compared directly with earlier years?",
        source="explain-ons-travel-2024", publisher="Office for National Statistics",
        title="Travel trends: 2024", date="26 August 2025",
        quote=["Annual 2024 estimates consist of Quarter 1 (Jan to Mar) and Quarter 2 (Apr to June) 2024 data collected and produced under our previous International Passenger Survey (IPS) design, and Quarter 3 (July to Sept) and Quarter 4 (Oct to Dec) 2024 data collected and produced under our new design; there may be differences between these two halves and this affects how the estimates can be used."]),
    # ------------------------------------------------------------ life: schools
    "infant-limit": dict(
        topic="schools", years=range(2008, 2026),
        question="Is there a legal limit on class sizes?",
        source="dfe-spc-page", publisher="Department for Education",
        title="Schools, pupils and their characteristics: academic year 2025/26", date="4 June 2026",
        quote=["Large Classes - An infant class is described as ‘large’ when it exceeds the statutory limit of 30 pupils. There are no formal policy restrictions on any other class sizes.",
               "This means that a class of, for example, 32 pupils is lawful if two or more of those pupils have been admitted under lawful exceptions."],
        gloss="This is the rule in England. Infant classes are reception, year 1 and year 2. The primary and secondary averages say nothing about the limit on their own; the infant figures on the class sizes page show how many pupils are in classes of more than 30, some of which are lawful exceptions."),
    # ------------------------------------------------------------ leaving the UK
    "leave-total-2025": dict(
        question="How many people left the UK in the latest year?",
        source="explain-ons-ltim-yearending-dec-2025", publisher="Office for National Statistics",
        title="Long-term international migration, provisional: year ending December 2025", date="21 May 2026",
        quote=["The provisional estimate for total long-term emigration in the most recent period is 642,000.",
               "Emigration has been increasing since 2022 but was down by 38,000 from the updated YE December 2024 estimate of 680,000; which was mainly because of a slower increase in non-EU+ emigration and larger decrease in EU+ emigration in the last 12 months."],
        gloss="“Long-term” means a person who leaves the UK to live elsewhere for 12 months or more. The ONS figures are provisional and it revises them as more data arrives."),
    "leave-definition": dict(
        question="What counts as leaving the UK?",
        source="explain-ons-ltim-yearending-dec-2025", publisher="Office for National Statistics",
        title="Long-term international migration, provisional: year ending December 2025", date="21 May 2026",
        quote=["When we refer to emigration, we are referring to long-term emigration from the UK. This is when a person has left the UK to live in another country for a period of at least 12 months."],
        gloss="Short trips, including holidays, do not count, even though they are many millions a year."),
    "leave-by-nationality": dict(
        question="Who left the UK in the year ending December 2025?",
        source="explain-ons-ltim-yearending-dec-2025", publisher="Office for National Statistics",
        title="Long-term international migration, provisional: year ending December 2025", date="21 May 2026",
        quote=["In YE December 2025, 278,000 non-EU+ nationals left the UK; just over half of these originally arrived with study-related visas.",
               "Emigration of EU+ nationals declined in YE December 2025 to 118,000, down by 24% from the updated YE December 2024 estimates of 155,000.",
               "In YE December 2025, 246,000 British nationals left the UK, a slight decline of 4% from the updated YE December 2024 estimates of 257,000."],
        gloss="As ONS defines them, EU+ is all current EU countries plus Norway, Iceland, Liechtenstein and Switzerland. Non-EU+ is every other country. British nationals are counted separately."),
    "leave-reasons": dict(
        question="Does the official data record why people left?",
        source="explain-ons-ltim-yearending-dec-2025", publisher="Office for National Statistics",
        title="Long-term international migration, provisional: year ending December 2025", date="21 May 2026",
        quote=["Reasons for emigration are based on the initial reason why an individual arrived in the UK."],
        gloss="So the “reason” recorded is the visa or route a person first came to the UK on, such as a study visa. It is not a reason given for leaving."),
    "leave-method": dict(
        question="Has the British figure risen, or has the way it is measured changed?",
        source="explain-ons-uk-emigration-explained", publisher="Office for National Statistics",
        title="UK emigration explained: what we know about Brits moving abroad", date="21 May 2026",
        quote=["For instance, using IPS data we had previously estimated that 77,000 British nationals emigrated out of the UK in the year ending December 2024. With our new method, we have been able to revise that to 257,000, a difference of 180,000.",
               "This does not mean 180,000 more Brits suddenly left the UK. We just now have a clearer idea of the true number that do emigrate each year. The significant change in our methods means we cannot compare our improved estimates with those from before June 2021.",
               "But it is not correct to say that our migration statistics show a recent rise in emigration of British nationals."],
        gloss="IPS means the International Passenger Survey, which ONS used before its new method. It asked travellers at ports and airports about their plans."),
    "leave-british-net": dict(
        question="How do British nationals who leave compare with those who arrive?",
        source="explain-ons-uk-emigration-explained", publisher="Office for National Statistics",
        title="UK emigration explained: what we know about Brits moving abroad", date="21 May 2026",
        quote=["We have also seen a drop in the number of Brits immigrating to the UK (arriving to live long-term), from 140,000 in 2024 to 110,000 in 2025. This has widened the gap between those leaving and arriving. When more people leave than arrive, it is known as negative net migration. Around 136,000 more Brits left than arrived in 2025.",
               "Our estimates for 2025 are provisional however, and may be revised up or down as more complete information becomes available."],
        gloss="Net migration is the number arriving minus the number leaving. A negative figure means more people left than arrived."),
    "leave-difficult": dict(
        question="Why is it hard to count British people who leave?",
        source="explain-ons-uk-emigration-explained", publisher="Office for National Statistics",
        title="UK emigration explained: what we know about Brits moving abroad", date="21 May 2026",
        quote=["Estimating British emigration is difficult – British nationals do not require a visa to leave or enter the UK, and millions regularly travel internationally for holidays and other short-term trips which do not count as emigration."]),
    "leave-surveys": dict(
        question="What do the statistics not cover?",
        source="explain-ons-uk-emigration-explained", publisher="Office for National Statistics",
        title="UK emigration explained: what we know about Brits moving abroad", date="21 May 2026",
        quote=["We do not produce estimates on how many British nationals are living abroad or where they are.",
               "We cannot carry out high-quality surveys overseas, or access the administrative data foreign governments hold about their populations."]),
    "nondom-regime": dict(
        question="What changed for non-domiciled taxpayers in April 2025?",
        source="explain-hmrc-nondom-2025", publisher="HM Revenue and Customs",
        title="Statistical commentary on non-domiciled taxpayers in the UK: tax year 2024 to 2025", date="published July 2026",
        quote=["From 6 April 2025 the remittance basis of taxation, which is based on domicile status, was replaced with a new tax regime based on residence",
               "this release is for tax year ending 2025 which occurred prior to these policy changes being implemented."],
        gloss="“Domicile” is a legal idea about a person's permanent home. The new regime is based on how long a person lives in the UK instead."),
    "nondom-flows": dict(
        question="Did fewer non-domiciled taxpayers leave in 2024 to 2025?",
        source="explain-hmrc-nondom-2025", publisher="HM Revenue and Customs",
        title="Statistical commentary on non-domiciled taxpayers in the UK: tax year 2024 to 2025", date="published July 2026",
        quote=["Fewer taxpayers flowed out of the non-domiciled taxpayer population than in the previous year (around 9,000 compared with 11,200), while the number of newly arrived non-domiciled taxpayers also fell (around 8,600 compared with 10,000)."],
        gloss="HMRC counts people who stop claiming non-domiciled status as “flowing out” of that group. The commentary does not say how many of them left the UK."),
    "nondom-residence": dict(
        question="Do most non-domiciled taxpayers live in the UK?",
        source="explain-hmrc-nondom-2025", publisher="HM Revenue and Customs",
        title="Statistical commentary on non-domiciled taxpayers in the UK: tax year 2024 to 2025", date="published July 2026",
        quote=["As in previous years, the majority of non-domiciled taxpayers in the tax year ending 2025 indicated UK residence."]),
    "nondom-income-tax": dict(
        question="How much Income Tax did non-domiciled taxpayers pay?",
        source="explain-hmrc-nondom-2025", publisher="HM Revenue and Customs",
        title="Statistical commentary on non-domiciled taxpayers in the UK: tax year 2024 to 2025", date="published July 2026",
        quote=["At around £9.7 billion, the Income Tax revenue from non-domiciled and deemed domiciled taxpayers is £556 million (or 6%) higher than in tax year ending 2024 and is at its highest level since tax year ending 2017."],
        gloss="Deemed domiciled taxpayers are former non-domiciled taxpayers who are now treated as UK domiciled for Income Tax and Capital Gains Tax."),
    "nondom-provisional": dict(
        question="How firm are the latest non-dom numbers?",
        source="explain-hmrc-nondom-2025", publisher="HM Revenue and Customs",
        title="Statistical commentary on non-domiciled taxpayers in the UK: tax year 2024 to 2025", date="published July 2026",
        quote=["Figures for tax years ending 2023, 2024 and 2025 are provisional (subject to future updates)."]),
    # ------------------------------------------------------------ immigration
    "imm-net-migration": dict(
        question="How many people moved to the UK, net, in the latest year?",
        source="explain-ons-ltim-dec2025", publisher="Office for National Statistics",
        title="Long-term international migration, provisional: year ending December 2025", date="released 21 May 2026",
        quote=["Long-term immigration is where an individual moves to the UK for 12 months or more, long-term emigration is where an individual leaves the UK for 12 months or more.",
               "Long-term net migration is immigration minus emigration.",
               "At 171,000, long-term international net migration for year ending (YE) December 2025 has nearly halved from YE December 2024 (updated to 331,000)",
               "Provisional net migration was 350,000 for non-EU+ nationals in YE December 2025, down from 511,000 a year earlier.",
               "The provisional net migration of British nationals remained broadly stable, estimated at negative 136,000."],
        note="These are provisional figures. The ONS revises earlier years, as the figure for YE December 2024 shows."),
    "imm-mac-partner": dict(
        question="Does one visa route pay for itself over a lifetime?",
        source="explain-mac-annual-2025", publisher="Migration Advisory Committee",
        title="Migration Advisory Committee annual report 2025, chapter 1: fiscal analysis of the Family visa", date="annual report 2025, accessible version",
        quote=["the partners of British citizens and settled residents, will incur a net lifetime fiscal deficit of -£5.6bn in present value terms",
               "Partner applicants and SW adult dependants can contribute considerably less through taxation than UK residents and still be more fiscally positive.",
               "During their first two decades in the UK, the cohort make an annual positive net fiscal contribution.",
               "This, combined with a decline in their employment rate and higher public spending as they age, causes the cohort to incur an annual net fiscal deficit as they remain in the UK."],
        gloss="The MAC models the 2022/23 cohort of Partner route applicants. The Partner route is one part of the Family visa, so this does not describe every migrant. “SW” means the Skilled Worker route. “Present value” means future sums are discounted to today’s value."),
    "imm-obr-time": dict(
        question="Does the answer change over time?",
        source="explain-obr-migration-fiscal", publisher="Office for Budget Responsibility",
        title="The impact of migration on the fiscal forecast", date="box first published March 2024",
        quote=["The fiscal impacts of migration are likely to become less beneficial over time, reflecting that after a minimum of 5-years, migrants can apply for indefinite leave to remain and therefore become eligible for welfare benefits.",
               "The overall long-term impact of migration on the public finances is more uncertain."],
        gloss="Indefinite leave to remain is the UK’s permanent settled status. This box uses data from March 2024, and its forecast covers five years."),
    "imm-obr-services": dict(
        question="How do migrants’ use of public services show up in the public finances?",
        source="explain-obr-migration-fiscal", publisher="Office for Budget Responsibility",
        title="The impact of migration on the fiscal forecast", date="box first published March 2024",
        quote=["While migrants will consume public services such as education, healthcare, and transport, there is no direct link between the size of the population and the money allocated for departmental spending on public services.",
               "reduce DEL spending per person by £40 in 2028-29 and increase the pressure on those services"],
        gloss="DEL means departmental expenditure limits: the amounts government sets for each department’s spending. The £40 figure comes from the OBR’s central forecast with about 350,000 more net migration by 2028-29."),
    "imm-obr-scenarios": dict(
        question="How much could the answer change if migration were higher or lower?",
        source="explain-obr-migration-fiscal", publisher="Office for Budget Responsibility",
        title="The impact of migration on the fiscal forecast", date="box first published March 2024",
        quote=["in which net migration is 200,000 a year higher or lower than in our central forecast.",
               "In the higher migration scenario, receipts are £18.0 billion higher by the forecast horizon with contributions from both migration specific fees (£0.5 billion) and general taxation (£17.5 billion).",
               "so that while migration still improves the public finances it does so by less than in the unadjusted DEL scenario, with borrowing £13.1 billion lower and debt 2.5 per cent of GDP lower by 2028-29.",
               "These scenarios are a simplification and are highly uncertain."],
        gloss="The two versions differ in whether the government spends more on public services for the extra people. The OBR says the scenarios are simplified, so they show the size of the uncertainty, not a forecast."),
    "imm-obr-gdp": dict(
        question="How does migration affect GDP per person, not only total GDP?",
        source="explain-obr-migration-gdp", publisher="Office for Budget Responsibility",
        title="Net migration and GDP per person (box, Economic and fiscal outlook, March 2026)", date="March 2026",
        quote=["Net inward migration has been a significant driver of GDP growth, but its impact on GDP per person is much more uncertain.",
               "higher net inward migration raised the aggregate level of real GDP by around 1 to 2 per cent after five years.",
               "However, the impact on real GDP per person was either slightly positive or slightly negative, depending on the assumptions made about the labour supply and average productivity of new migrants and the effect on economy-wide productivity and participation."],
        gloss="GDP is the total output of the economy. GDP per person divides it by the population, which is one common measure of living standards."),
}

_text_cache = {}

QUOTE_MARKS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " ", "–": "-", "—": "-"})


def norm(s):
    """Collapse whitespace and typographic quotes and dashes so a quote can be matched in page text."""
    return re.sub(r"\s+", " ", s.translate(QUOTE_MARKS)).strip()


def page_text(path):
    """Visible text of a fetched HTML page, normalised."""
    if path not in _text_cache:
        raw = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?i)</?(abbr|acronym)\b[^>]*>", "", raw)  # inline: "the <abbr>UK</abbr>’s" reads "the UK’s"
        raw = re.sub(r"<[^>]+>", " ", raw)
        _text_cache[path] = norm(_html.unescape(raw))
    return _text_cache[path]


def missing_quotes(sources):
    """List every quoted passage that cannot be found in its source file."""
    problems = []
    for key, e in EXPLANATIONS.items():
        s = sources.get(e["source"])
        if not s:
            problems.append(f"explanation {key}: source {e['source']} is not in the source registry")
            continue
        text = page_text(s["file"])
        for q in e["quote"]:
            if norm(q) not in text:
                problems.append(f"explanation {key}: quote not found in {s['file']}: {q[:80]!r}")
    return problems


def box(key, sources, up="", heading=None):
    """An attributed quote with its source. heading: an <h3>/<h4> level, or None for a bold question line."""
    e = EXPLANATIONS[key]
    s = sources[e["source"]]
    q = " … ".join(esc(p) for p in e["quote"])
    title = esc(e["question"])
    head = f'<{heading} class="q">{title}</{heading}>' if heading else f'<p class="q"><strong>{title}</strong></p>'
    return f'''<aside class="explain" aria-label="{esc(e['publisher'])} explanation">
{head}
<p class="who">In the words of the {esc(e['publisher'])}:</p>
<blockquote cite="{esc(s['page'])}"><p>“{q}”</p></blockquote>
{f'<p class="small">{esc(e["gloss"])}</p>' if e.get("gloss") else ""}
<p class="src">Quoted word for word from <a href="{esc(s['page'])}">{esc(e['title'])}</a> ({esc(e['date'])}). {esc(e.get('note', 'Figures inside the quote are as the publisher gave them at the time and may since have been revised.'))} <a href="{up}sources.html#src-{esc(e['source'])}">Source record</a>.</p>
</aside>'''


def for_year(topic, year, sources, up=""):
    """Quotes that apply to one topic in one year, for the year pages."""
    return "".join(box(k, sources, up) for k, e in EXPLANATIONS.items() if e.get("topic") == topic and year in e.get("years", ()))


def for_topic(topic, sources, up=""):
    """Every quote for a topic, folded away so the topic stays short on a phone."""
    keys = [k for k, e in EXPLANATIONS.items() if e.get("topic") == topic]
    if not keys:
        return ""
    return (f'<details class="explain-all"><summary>What official bodies say about these figures ({len(keys)})</summary>'
            + "".join(box(k, sources, up) for k in keys) + "</details>")
