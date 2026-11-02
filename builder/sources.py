"""Registry of every official source the site uses.

Each entry names the publisher, the publication, the exact file kept in this
repository, where it came from and what period, place and population it covers.
The build checks each file's SHA-256 hash against the value recorded here, so a
changed or replaced file stops the build instead of silently changing figures.
"""
import hashlib
import json

from .readers import ROOT

OGL = "Open Government Licence v3.0"
GBTS_TERMS = "Official statistics published by VisitEngland, VisitScotland and Visit Wales; figures quoted with attribution"


def _fetched(source_id):
    receipts = json.loads((ROOT / "data/fetched/receipts.json").read_text())
    return receipts[source_id]


SOURCES = {
    "pesa4": dict(
        publisher="HM Treasury",
        title="Public Expenditure Statistical Analyses (PESA) 2026, Chapter 4 tables",
        page="https://www.gov.uk/government/statistics/public-expenditure-statistical-analyses-2026",
        url="https://assets.publishing.service.gov.uk/media/6a5772e09e63154454413700/PESA_2026_CP_Chapter_4_tables.xlsx",
        file="data/raw/PESA_2026_CP_Chapter_4_tables.xlsx",
        sha256="50ae80d95c4e542c34a17dfa8bc302858ca6508b6753e27bb31920cec9bb75c4",
        published="16 July 2026", retrieved="29 October 2026",
        geography="United Kingdom", population="Whole public sector",
    ),
    "pesa5": dict(
        publisher="HM Treasury",
        title="Public Expenditure Statistical Analyses (PESA) 2026, Chapter 5 tables",
        page="https://www.gov.uk/government/statistics/public-expenditure-statistical-analyses-2026",
        url="https://assets.publishing.service.gov.uk/media/6a5772f59e63154454413701/PESA_2026_CP_Chapter_5_tables.xlsx",
        file="data/raw/PESA_2026_CP_Chapter_5_tables.xlsx",
        sha256="ccb4539bb837c2b6a7f9509da49bd409eb9e5a910f3332311b494291fbd33107",
        published="16 July 2026", retrieved="29 October 2026",
        geography="United Kingdom", population="Whole public sector",
    ),
    "obr": dict(
        publisher="Office for Budget Responsibility",
        title="Public finances databank, October 2026",
        page="https://obr.uk/data/",
        url="https://obr.uk/download/public-finances-databank-october-2026-efo/",
        file="data/raw/OBR_Public_finances_databank_October_2026.xlsx",
        sha256="16a4bf46d8692e18790e87add342c6c44aa909cebb19f68ae857126a36d36459",
        published="October 2026", retrieved="29 October 2026",
        geography="United Kingdom", population="Whole public sector",
    ),
    "hmrc24": dict(
        publisher="HM Revenue and Customs",
        title="Income Tax statistics, Table 2.4: shares of total income and Income Tax for percentile groups",
        page="https://www.gov.uk/government/statistics/income-tax-liabilities-statistics-tax-year-2023-to-2024-to-tax-year-2026-to-2027",
        url="https://assets.publishing.service.gov.uk/media/6a54e2b72467584757371e1a/Table_2.4_Shares_of_total_Income_Tax_liability.ods",
        file="data/payers/raw/hmrc-table24-july2026.ods",
        sha256="8eb6281c40d716367cd063c5cfd124ba49fb7ab223c8ebacfb6680db1113c6b7",
        published="15 July 2026", retrieved="30 October 2026",
        geography="United Kingdom", population="Individuals with an Income Tax liability (taxpayers only)",
    ),
    "etb": dict(
        publisher="Office for National Statistics",
        title="The effects of taxes and benefits on household income, financial year ending 2024: reference tables",
        page="https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024",
        url="https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/theeffectsoftaxesandbenefitsonhouseholdincomefinancialyearending2014/financialyearending2024/etbreferencetablesfye202324final.xlsx",
        file="data/payers/raw/ons-etb-fye2024.xlsx",
        sha256="2e38c1694d922427509879b9553a4c3473b8ba1174898c2dd414668ecbb2bf73",
        published="25 September 2025", retrieved="30 October 2026",
        geography="United Kingdom", population="All individuals, grouped by their household's income (private households)",
    ),
    "aps2010": dict(
        publisher="Office for National Statistics (via Nomis)",
        title="Annual Population Survey: employment by occupation (SOC2010), January to December",
        page="https://www.nomisweb.co.uk/datasets/aps210",
        url="https://www.nomisweb.co.uk/api/v01/dataset/NM_210_1.data.csv",
        file="data/life/sources/work-data/aps210-uk-calendar-annual.csv",
        sha256="9bd1e5427dab27003f08b2fde0c7b8df85717e0acaf221093ccc941ccacce285",
        published="Nomis dataset NM_210_1", retrieved="31 October 2026",
        geography="United Kingdom", population="People aged 16 and over in employment",
    ),
    "aps2020": dict(
        publisher="Office for National Statistics (via Nomis)",
        title="Annual Population Survey: employment by occupation (SOC2020), January to December",
        page="https://www.nomisweb.co.uk/datasets/aps218",
        url="https://www.nomisweb.co.uk/api/v01/dataset/NM_218_1.data.csv",
        file="data/life/sources/work-data/aps218-uk-calendar-annual.csv",
        sha256="e4388e5746ea8e5db6da36c12066abab615036196bb395f37ead005d26161b25",
        published="Nomis dataset NM_218_1", retrieved="31 October 2026",
        geography="United Kingdom", population="People aged 16 and over in employment",
    ),
    "dfe_api": dict(
        publisher="Department for Education",
        title="Schools, pupils and their characteristics: class sizes, national (API data set, version 1.0)",
        page="https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics",
        url="https://api.education.gov.uk/statistics/v1/data-sets/019e7401-70d1-73ca-9855-bd7258e5a1ca/query?dataSetVersion=1.0&geographicLevels.eq=NAT&pageSize=1000",
        file="data/life/sources/schools/dfe-national-class-sizes-1.0.json",
        sha256="b87e9c64b823ca25134fe6d6fd1ae1cc7b8fbabfe4da5f0a12af0dc8fa56ec04",
        published="2025/26 release", retrieved="31 October 2026",
        geography="England", population="State-funded schools; classes taught by one teacher",
    ),
}

# Sources downloaded by scripts/fetch_sources.py. URL, hash and retrieval time
# come from data/fetched/receipts.json, written at download time.
FETCHED = {
    "ons-mgrz": ("Office for National Statistics", "Labour market statistics: people in employment aged 16 and over (MGRZ)", "United Kingdom", "People aged 16 and over"),
    "ons-lf24": ("Office for National Statistics", "Labour market statistics: employment rate, aged 16 to 64 (LF24)", "United Kingdom", "People aged 16 to 64"),
    "ons-mgsv": ("Office for National Statistics", "Labour market statistics: male employment rate, aged 16 to 64 (MGSV)", "United Kingdom", "Men aged 16 to 64"),
    "ons-lf25": ("Office for National Statistics", "Labour market statistics: female employment rate, aged 16 to 64 (LF25)", "United Kingdom", "Women aged 16 to 64"),
    "ons-ycbe": ("Office for National Statistics", "Labour market statistics: people in full-time employment (YCBE)", "United Kingdom", "People aged 16 and over in employment"),
    "ons-ycbh": ("Office for National Statistics", "Labour market statistics: people in part-time employment (YCBH)", "United Kingdom", "People aged 16 and over in employment"),
    "ons-l522": ("Office for National Statistics", "Consumer prices: CPIH index, all items, 2015=100 (L522)", "United Kingdom", "Household spending basket"),
    "nomis-ashe-resident": ("Office for National Statistics (via Nomis)", "Annual Survey of Hours and Earnings (ASHE), resident analysis: median gross weekly pay", "United Kingdom", "Employees on adult rates whose pay was not affected by absence"),
    "nomis-ashe-places": ("Office for National Statistics (via Nomis)", "Annual Survey of Hours and Earnings (ASHE), resident analysis: median gross weekly pay of full-time employees, by nation and English region", "United Kingdom nations and English regions (where employees live)", "Full-time employees on adult rates whose pay was not affected by absence"),
    "nomis-aps-emp-places": ("Office for National Statistics (via Nomis)", "Annual Population Survey: employment rate, aged 16 to 64, by nation and English region", "United Kingdom nations and English regions", "People aged 16 to 64 living in private households"),
    "nomis-aps-emp-places-ci": ("Office for National Statistics (via Nomis)", "Annual Population Survey: employment rate, aged 16 to 64, by nation and English region, with 95% confidence intervals", "United Kingdom nations and English regions", "People aged 16 to 64 living in private households"),
    "nomis-aps-measure-codes": ("Office for National Statistics (via Nomis)", "Annual Population Survey (NM_17_5): list of measures, including “Confidence”", "United Kingdom", "Not applicable (code list)"),
    "nomis-ashe-resident-cv": ("Office for National Statistics (via Nomis)", "Annual Survey of Hours and Earnings (ASHE), resident analysis: median gross weekly pay with its coefficient of variation", "United Kingdom", "Employees on adult rates whose pay was not affected by absence"),
    "nomis-ashe-measure-codes": ("Office for National Statistics (via Nomis)", "Annual Survey of Hours and Earnings (NM_30_1): list of measures, including “Confidence”", "United Kingdom", "Not applicable (code list)"),
    "nomis-ashe-article": ("Nomis (Office for National Statistics)", "Annual Survey of Hours and Earnings: notes on the data, including coefficients of variation", "United Kingdom", "Not applicable (guidance)"),
    "ons-lfs-a11": ("Office for National Statistics", "A11: Labour Force Survey sampling variability (95% confidence intervals)", "United Kingdom", "People aged 16 to 64 (employment rate)"),
    "ons-uncertainty-guide": ("Office for National Statistics", "Uncertainty and how we measure it for our surveys", "Not applicable", "Not applicable (guidance)"),
    "ons-ybud": ("Office for National Statistics", "Labour market statistics: employment rate, aged 18 to 24 (YBUD)", "United Kingdom", "People aged 18 to 24"),
    "ons-ybug": ("Office for National Statistics", "Labour market statistics: employment rate, aged 25 to 34 (YBUG)", "United Kingdom", "People aged 25 to 34"),
    "ons-ybuj": ("Office for National Statistics", "Labour market statistics: employment rate, aged 35 to 49 (YBUJ)", "United Kingdom", "People aged 35 to 49"),
    "ons-lf2u": ("Office for National Statistics", "Labour market statistics: employment rate, aged 50 to 64 (LF2U)", "United Kingdom", "People aged 50 to 64"),
    "ons-lfk6": ("Office for National Statistics", "Labour market statistics: employment rate, aged 65 and over (LFK6)", "United Kingdom", "People aged 65 and over"),
    "dluhc-lt109": ("Ministry of Housing, Communities and Local Government", "Dwelling stock live table 109: estimated dwelling stock by tenure and region, England", "England and its nine regions", "All dwellings (homes), including empty ones"),
    "wales-dwelling-stock": ("Welsh Government (StatsWales)", "Dwelling stock estimates by tenure and local authority area", "Wales", "All dwellings (homes); owner occupied includes intermediate tenure"),
    "scot-stock-by-tenure": ("Scottish Government", "Housing statistics: estimated stock of dwellings by tenure, 1993 to 2025", "Scotland", "All dwellings (homes); empty private homes and second homes counted separately"),
    "ni-housing-2025-26": ("Department for Communities (Northern Ireland)", "Northern Ireland housing statistics 2025-26, table 1.3: household tenure (Family Resources Survey)", "Northern Ireland", "Households (survey sample)"),
    "scot-pupil-census-2025": ("Scottish Government", "Pupil census supplementary statistics 2025, table 2.10: average class size of primary school pupils", "Scotland", "Pupils in publicly funded primary schools"),
    "ni-de-enrolments-2025-26": ("Department of Education (Northern Ireland)", "School enrolments 2025/26 statistical bulletins (release page)", "Northern Ireland", "Pupils in grant-aided schools"),
    "wg-schools-census-2025": ("Welsh Government", "Schools' census results: January 2025, tables 16 and 17 (infant and junior class sizes)", "Wales", "Infant and junior classes in maintained schools"),
    "ashe-2025-fig1": ("Office for National Statistics", "Employee earnings in the UK: 2025, Figure 1 data", "United Kingdom", "Employee jobs"),
    "ehs-ft1101": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FT1101: trends in tenure", "England", "All households"),
    "ehs-ft1241": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FT1241: trends in tenure, households with dependent children", "England", "Couples and lone parents with dependent children"),
    "ehs-fa3201": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FA3201: rent before housing support", "England", "Social and private renting households paying rent"),
    "ehs-fa2501": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FA2501: mortgage payment per week, 2008-09 to 2021-22", "England", "Households buying with a mortgage, including shared owners"),
    "ehs-fa2555": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FA2555: mortgage payment per week, 2022-23 onwards", "England", "Households buying with a mortgage, including shared owners"),
    "ehs-ft1421": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FT1421: trends in overcrowding by tenure (three-year averages)", "England", "All households"),
    "ehs-fa1422": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FA1422: overcrowding and under-occupation by tenure (three-year averages)", "England", "All households"),
    "ehs-fa1401": ("Ministry of Housing, Communities and Local Government", "English Housing Survey live table FA1401: number of rooms by tenure", "England", "All households"),
    "ott-2019to2023": ("Office for National Statistics", "Travel trends, Section 3: UK residents' visits abroad, 2019 to 2023", "United Kingdom residents", "Visits abroad by UK residents"),
    "ott-2009to2019": ("Office for National Statistics", "Travel trends, Section 3: UK residents' visits abroad, 2009 to 2019", "United Kingdom residents", "Visits abroad by UK residents"),
    "ott-2024": ("Office for National Statistics", "Travel trends: UK residents' visits abroad, 2024 annual tables", "United Kingdom residents", "Visits abroad by UK residents"),
    "ott-2025": ("Office for National Statistics", "Travel trends: UK residents' visits abroad, 2025 annual tables", "United Kingdom residents", "Visits abroad by UK residents"),
    "gbts-2019-gb-summary": ("VisitEngland, VisitScotland and Visit Wales", "Great Britain Tourism Survey: GB all trips by purpose, summary tables 2019 (earlier survey method)", "Great Britain", "Overnight trips in Great Britain by GB residents, adults and accompanying children"),
    "gbts-2022to2023-tables": ("VisitEngland, VisitScotland and Visit Wales", "Great Britain Tourism Survey: domestic overnight trips, 2022 to 2023, tables", "Great Britain", "Overnight trips in Great Britain by GB residents, adults and accompanying children"),
    "gbts-2024-q4-annual-tables": ("VisitEngland, VisitScotland and Visit Wales", "Great Britain Tourism Survey: domestic overnight trips, Q4 and annual 2024, tables", "Great Britain", "Overnight trips in Great Britain by GB residents, adults and accompanying children"),
    "gbts-2025-toplines": ("VisitEngland, VisitScotland and Visit Wales", "Great Britain Tourism Survey: domestic overnight and day trips in Q4 2025 and in 2025, toplines", "Great Britain", "Overnight trips in Great Britain by GB residents, adults and accompanying children"),
    "ons-ukpop": ("Office for National Statistics", "Population estimates: United Kingdom mid-year population (UKPOP)", "United Kingdom", "Usually resident population, all ages"),
    "ons-gbpop": ("Office for National Statistics", "Population estimates: Great Britain mid-year population (GBPOP)", "Great Britain", "Usually resident population, all ages"),
    "dfe-spc-2015-tables": ("Department for Education", "Schools, pupils and their characteristics: January 2015, national tables (SFR16/2015)", "England", "State-funded schools; classes taught by one teacher"),
    "hmrc-spi-2324-tables": ("HM Revenue and Customs", "Personal Incomes Statistics, tax year 2023 to 2024: collated tables 3.1 to 3.11 (Survey of Personal Incomes)", "United Kingdom", "Individuals with some Income Tax liability (taxpayers only)"),
    "gov-income-tax-rates": ("HM Revenue and Customs (GOV.UK)", "Income Tax rates and Personal Allowances", "England, Wales and Northern Ireland", "Individuals"),
    "gov-ni-rates": ("HM Revenue and Customs (GOV.UK)", "National Insurance rates and categories", "United Kingdom", "Employees"),
    # Explanatory publications quoted word for word on the pages (see builder/explain.py).
    "explain-ons-psf-2021-03": ("Office for National Statistics", "Public sector finances, UK: March 2021 (statistical bulletin)", "United Kingdom", "Whole public sector"),
    "explain-ons-psf-2023-03": ("Office for National Statistics", "Public sector finances, UK: March 2023 (statistical bulletin)", "United Kingdom", "Whole public sector"),
    "explain-hmrc-itl-commentary": ("HM Revenue and Customs", "Income Tax liabilities statistics: tax year 2023 to 2024 to tax year 2026 to 2027, bulletin commentary", "United Kingdom", "Individuals with an Income Tax liability"),
    "explain-hmrc-spi-2324-commentary": ("HM Revenue and Customs", "Personal Incomes Statistics 2023 to 2024: commentary", "United Kingdom", "Individuals with some Income Tax liability"),
    "explain-hmrc-spi-quality": ("HM Revenue and Customs", "Background quality report: Personal Income Statistics release", "United Kingdom", "Not applicable (guidance)"),
    "explain-ons-etb-latest": ("Office for National Statistics", "Effects of taxes and benefits on UK household income: financial year ending 2024 (statistical bulletin)", "United Kingdom", "People in private households"),
    "explain-ons-2008-recession": ("Office for National Statistics", "The 2008 recession 10 years on (article)", "United Kingdom", "Whole economy"),
    "explain-ons-lmo-latest": ("Office for National Statistics", "Labour market overview, UK: October 2026 (statistical bulletin)", "United Kingdom", "People aged 16 and over"),
    "explain-ons-ashe-2022": ("Office for National Statistics", "Employee earnings in the UK: 2022 (statistical bulletin)", "United Kingdom", "Employee jobs"),
    "explain-ehs-2023-24-rented-report": ("Ministry of Housing, Communities and Local Government", "English Housing Survey 2023 to 2024: rented sectors (report)", "England", "Households renting privately or socially"),
    "explain-ehs-2024-25-ch1": ("Ministry of Housing, Communities and Local Government", "English Housing Survey 2024 to 2025 headline findings on demographics and household resilience, chapter 1", "England", "All households"),
    "explain-ehs-2024-25-ch2": ("Ministry of Housing, Communities and Local Government", "English Housing Survey 2024 to 2025 headline findings on demographics and household resilience, chapter 2", "England", "All households"),
    "explain-ons-travel-2021": ("Office for National Statistics", "Travel trends: 2021 (article)", "United Kingdom residents and overseas visitors", "Visits abroad and visits to the UK"),
    "explain-ons-travel-2022": ("Office for National Statistics", "Travel trends: 2022 (article)", "United Kingdom residents and overseas visitors", "Visits abroad and visits to the UK"),
    "explain-ons-travel-2024": ("Office for National Statistics", "Travel trends: 2024 (article)", "United Kingdom and Great Britain residents and overseas visitors", "Visits abroad and visits to the UK"),
    "dfe-spc-page": ("Department for Education", "Schools, pupils and their characteristics: academic year 2025/26 (release page)", "England", "Pupils in schools in England"),
}


def all_sources():
    out = {}
    for key, s in SOURCES.items():
        out[key] = dict(s, licence=OGL, id=key)
    for key, (publisher, title, geography, population) in FETCHED.items():
        try:
            r = _fetched(key)
        except KeyError:
            continue
        out[key] = dict(id=key, publisher=publisher, title=title, url=r["url"], page=r["url"],
                        file="data/fetched/" + r["file"], sha256=r["sha256"],
                        published="see publisher page", retrieved=r["retrieved"][:10],
                        geography=geography, population=population,
                        licence=GBTS_TERMS if key.startswith("gbts-") else OGL)
    return out


def verify_hashes(sources):
    """Fail if any retained file differs from the recorded hash."""
    problems = []
    for s in sources.values():
        if not s.get("sha256"):
            continue
        digest = hashlib.sha256((ROOT / s["file"]).read_bytes()).hexdigest()
        if digest != s["sha256"]:
            problems.append(f"{s['id']}: {s['file']} hash {digest} != recorded {s['sha256']}")
    return problems
