"""Everyday life, year by year: a short overview, one page per topic, one page
per year and a page for every pair of years.

Years are calendar labels, but each topic is measured over its own period
(for example April to June, the April survey date, a survey year running into
the next calendar year, or a January school census). Every value is shown with
its own period. Missing years stay missing, and comparisons across a change of
definition are not calculated.
"""
import re

from .data import YEARS, EARLY_YEARS, NATIONS, REGIONS, AGE_SERIES
from . import explain
from .html import FOLD, NOFOLD, before_toc, jump, page, table, details_table, line_chart, small_multiples, source_line, spark, fmt, esc
from . import uncertainty as U
from . import findings as F
from .pages_nations import housing_nations_block, schools_nations_block
from .pages_life_extra import spread_block, afford_block, industry_block, industry_page, afford_page

FIRST, LAST = YEARS[0], YEARS[-1]
RECENT = 2022  # the first year after the pandemic years (2020 and 2021), for a recent comparison beside the default pair
# The first year each topic's longest series reaches (see pages_history.LONG).
FIRST_YEAR = {"work": 1971, "earnings": 2002, "housing": 1981, "holidays": 1980, "schools": 2006}


def occ_scheme(y):
    return "SOC2010" if y <= 2020 else "SOC2020"


def sy(y):
    """Survey-year label: 2015 -> '2015-16'."""
    return f"{y}-{str(y + 1)[2:]}"


def rooms_basis(y):
    return "utility rooms counted" if y <= 2010 else "utility rooms not counted"


def crowd_period(y):
    return f"average of {sy(y - 2)} to {sy(y)}"


def hol_basis(y):
    # ONS: annual 2024 combines the old survey (January to June) and the new one (July to December),
    # so 2024 is compared with neither earlier years nor 2025.
    return "UK" if y <= 2023 else ("GB, mixed methods" if y == 2024 else "GB")


def scot_survey(y):
    return "pandemic-affected survey" if y in (2020, 2021) else "usual survey"


def gb_survey(y):
    return "earlier survey" if y <= 2019 else "current survey"


# Each measure: key, topic, label, fact-id function, display kind, change style ('pp', 'pct' or None),
# period function, comparability-group function (None = one consistent series)
def afford_basis(y):
    """ONS: earnings for 1997 and 1998 in the house-price ratio are weekly pay scaled
    up to a year, not directly comparable with later years."""
    return "weekly pay scaled up" if y <= 1998 else "annual pay"


def earn_basis(y):
    """ASHE periods measured the same way. ONS changed the survey's method in 2004 and
    2006, and the coding of jobs in 2011 (SOC2010) and 2021 (SOC2020), so pay is only
    compared within one of these periods."""
    if y < 2004:
        return "before 2004 method"
    if y < 2006:
        return "2004 and 2005 method"
    if y < 2011:
        return "2006 to 2010, SOC2000 job coding"
    if y < 2021:
        return "2011 to 2020, SOC2010 job coding"
    return "2021 onwards, SOC2020 job coding"


def measures(d):
    base = d["housing_costs"]["base"]
    occ_codes = {"prof": "2000000", "elem": "9000000", "caring": "6000000", "admin": "4000000", "skilled": "5000000", "managers": "1000001"}
    occ_names = {"prof": "Professional occupations", "managers": "Managers, directors and senior officials", "admin": "Administrative and secretarial",
                 "skilled": "Skilled trades", "caring": "Caring, leisure and other services", "elem": "Elementary occupations (e.g. cleaners, labourers)"}
    m = [
        ("work.rate", "work", "Employment rate, ages 16 to 64", lambda y: f"work.rate.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None),
        ("work.men", "work", "Employment rate, men 16 to 64", lambda y: f"work.men.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None),
        ("work.women", "work", "Employment rate, women 16 to 64", lambda y: f"work.women.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None),
        ("work.level", "work", "People in work, aged 16 and over", lambda y: f"work.level.{y}", "millions_people", "pct", lambda y: f"Apr–Jun {y}", None),
        ("work.pt", "work", "Workers who work part-time", lambda y: f"work.ptshare.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None),
    ]
    m += [
        ("work.ind.manuf", "work", "Share of jobs in manufacturing", lambda y: f"jobs.share.C.{y}", "pct", "pp", lambda y: f"June {y}", None),
        ("work.ind.health", "work", "Share of jobs in health and social work", lambda y: f"jobs.share.Q.{y}", "pct", "pp", lambda y: f"June {y}", None),
    ]
    for key, label, _ in AGE_SERIES:
        m.append((f"work.age.{key}", "work", f"Employment rate, ages {label}", (lambda k: lambda y: f"work.age.{k}.{y}")(key), "pct", "pp", lambda y: f"Apr–Jun {y}", None))
    for key, name in NATIONS[1:]:
        m.append((f"work.place.{key}", "work", f"Employment rate 16 to 64: {name}", (lambda k: lambda y: f"work.place.{k}.{y}")(key), "pct", "pp", lambda y: f"Jan–Dec {y}", None))
    for k in ("prof", "managers", "admin", "skilled", "caring", "elem"):
        code = occ_codes[k]
        m.append((f"work.occ.{k}", "work", f"Share of workers in: {occ_names[k]}", (lambda c: lambda y: f"work.occshare.{occ_scheme(y)}.{c}.{y}")(code), "pct", "pp",
                  lambda y: f"Jan–Dec {y}", occ_scheme))
    m += [
        ("earn.ft", "earnings", "Median weekly pay, full-time employees (April 2025 prices)", lambda y: f"earn.real.ft.{y}", "pounds", "pct", lambda y: f"April {y}", earn_basis),
        ("earn.ftcash", "earnings", "Median weekly pay, full-time employees (cash, at the time)", lambda y: f"earn.ft.{y}", "pounds", "pct", lambda y: f"April {y}", earn_basis),
        ("earn.men", "earnings", "Full-time men (April 2025 prices)", lambda y: f"earn.real.ft_men.{y}", "pounds", "pct", lambda y: f"April {y}", earn_basis),
        ("earn.women", "earnings", "Full-time women (April 2025 prices)", lambda y: f"earn.real.ft_women.{y}", "pounds", "pct", lambda y: f"April {y}", earn_basis),
        ("earn.pt", "earnings", "Part-time employees (April 2025 prices)", lambda y: f"earn.real.pt.{y}", "pounds", "pct", lambda y: f"April {y}", earn_basis),
    ]
    m.append(("earn.spread", "earnings", "Full-time pay: top-tenth line ÷ bottom-tenth line", lambda y: f"spread.ratio.{y}", "times", "pct", lambda y: f"April {y}", earn_basis))
    for key, name in NATIONS[1:]:
        m.append((f"earn.place.{key}", "earnings", f"Full-time, living in {name} (April 2025 prices)", (lambda k: lambda y: f"earn.place.real.{k}.{y}")(key), "pounds", "pct", lambda y: f"April {y}", earn_basis))
    m += [
        ("house.outright", "housing", "Households that own outright", lambda y: f"house.outright.{y}", "pct", "pp", lambda y: f"{y}-{str(y + 1)[2:]}", None),
        ("house.mortgage", "housing", "Households buying with a mortgage", lambda y: f"house.mortgage.{y}", "pct", "pp", lambda y: f"{y}-{str(y + 1)[2:]}", None),
        ("house.social", "housing", "Households renting from a council or housing association", lambda y: f"house.social.{y}", "pct", "pp", lambda y: f"{y}-{str(y + 1)[2:]}", None),
        ("house.private", "housing", "Households renting privately", lambda y: f"house.private.{y}", "pct", "pp", lambda y: f"{y}-{str(y + 1)[2:]}", None),
        ("house.kids", "housing", "Families with dependent children renting privately", lambda y: f"house.kids.private.{y}", "pct", "pp", lambda y: f"{y}-{str(y + 1)[2:]}", None),
        ("house.rent.private", "housing", f"Average private rent a week ({sy(base)} prices)", lambda y: f"house.real.rent.private.{y}", "pounds", "pct", sy, None),
        ("house.rent.social", "housing", f"Average social rent a week ({sy(base)} prices)", lambda y: f"house.real.rent.social.{y}", "pounds", "pct", sy, None),
        ("house.mortpay", "housing", f"Average mortgage payment a week ({sy(base)} prices)", lambda y: f"house.real.mortpay.{y}", "pounds", "pct", sy, None),
        ("house.rent.privatecash", "housing", "Average private rent a week (cash, at the time)", lambda y: f"house.rent.private.{y}", "pounds", "pct", sy, None),
        ("house.rent.socialcash", "housing", "Average social rent a week (cash, at the time)", lambda y: f"house.rent.social.{y}", "pounds", "pct", sy, None),
        ("house.mortpaycash", "housing", "Average mortgage payment a week (cash, at the time)", lambda y: f"house.mortpay.{y}", "pounds", "pct", sy, None),
        ("house.afford", "housing", "Median house price ÷ median full-time earnings, England and Wales", lambda y: f"afford.ratio.ew.{y}", "times2", "pct", lambda y: str(y), afford_basis),
        ("house.crowd.all", "housing", "Overcrowded households, all tenures", lambda y: f"house.crowd.all.{y}", "pct", "pp", crowd_period, None),
        ("house.crowd.owners", "housing", "Overcrowded: owner occupiers", lambda y: f"house.crowd.owners.{y}", "pct", "pp", crowd_period, None),
        ("house.crowd.social", "housing", "Overcrowded: social renters", lambda y: f"house.crowd.social.{y}", "pct", "pp", crowd_period, None),
        ("house.crowd.private", "housing", "Overcrowded: private renters", lambda y: f"house.crowd.private.{y}", "pct", "pp", crowd_period, None),
        ("house.rooms5", "housing", "Households with five or more rooms", lambda y: f"house.rooms5.{y}", "pct", "pp", sy, rooms_basis),
        ("hol.visits", "holidays", "Holiday visits abroad", lambda y: f"hol.world.holiday.{y}", "millions", "pct", lambda y: f"Jan–Dec {y}", hol_basis),
        ("hol.per100", "holidays", "Holiday visits abroad per 100 residents", lambda y: f"hol.abroad.per100.{y}", "int", "pct", lambda y: f"Jan–Dec {y}", hol_basis),
        ("hol.gb", "holidays", "Holiday trips within Great Britain (overnight)", lambda y: f"hol.gb.holiday.{y}", "millions", "pct", lambda y: f"Jan–Dec {y}", gb_survey),
        ("hol.gbper100", "holidays", "Holiday trips within Great Britain per 100 residents", lambda y: f"hol.gb.per100.{y}", "int", "pct", lambda y: f"Jan–Dec {y}", gb_survey),
        ("hol.share", "holidays", "Visits abroad that were holidays", lambda y: f"hol.holshare.{y}", "pct", "pp", lambda y: f"Jan–Dec {y}", hol_basis),
        ("hol.europe", "holidays", "Holiday visits that were to Europe", lambda y: f"hol.europeshare.{y}", "pct", "pp", lambda y: f"Jan–Dec {y}", hol_basis),
        ("school.primary", "schools", "Average class size, primary schools", lambda y: f"school.primary.{y}", "dp1", "abs", lambda y: f"January {y}", None),
        ("school.secondary", "schools", "Average class size, secondary schools", lambda y: f"school.secondary.{y}", "dp1", "abs", lambda y: f"January {y}", None),
        ("school.wales.infant", "schools", "Wales: average infant class (reception to year 2)", lambda y: f"school.wales.infant.{y}", "dp1", "abs", lambda y: f"January {y}", None),
        ("school.wales.junior", "schools", "Wales: average junior class (years 3 to 6)", lambda y: f"school.wales.junior.{y}", "dp1", "abs", lambda y: f"January {y}", None),
        ("school.scotland", "schools", "Scotland: average primary class (all stages)", lambda y: f"school.scotland.primary.{y}", "dp1", "abs", lambda y: f"September {y}", None),
        ("nat.house.private.wales", "housing", "Wales: homes rented privately", lambda y: f"house.nat.private.wales.{y}", "pct", "pp", lambda y: f"31 March {y}", None),
        ("nat.house.private.scotland", "housing", "Scotland: homes rented privately", lambda y: f"house.nat.private.scotland.{y}", "pct", "pp", lambda y: f"31 March {y}", scot_survey),
        ("nat.house.private.ni", "housing", "Northern Ireland: households renting privately", lambda y: f"house.nat.private.ni.{y}", "pct0", "pp", sy, None),
    ]
    return m


TOPICS = [
    ("work", "Work", "United Kingdom. Employment rates for the UK, by sex and by age, and the part-time share: Labour Force Survey, April to June. Employment rates for each nation and English region, and job types: Annual Population Survey, January to December."),
    ("earnings", "Earnings", "United Kingdom, and each nation by where employees live. Median (middle) gross weekly pay before tax, from the Annual Survey of Hours and Earnings in April each year. Adjusted to April 2025 prices with the UK-wide CPIH inflation index."),
    ("housing", "Housing", "Mainly England: English Housing Survey, plus homes by tenure in each English region. Wales and Scotland: homes by tenure at 31 March, from each government's dwelling stock estimates. Northern Ireland: households by tenure, Family Resources Survey. In the English Housing Survey a survey year runs from April to March, so “2015” means the 2015-16 survey. Rents are averages for households paying rent, before any housing support (such as Housing Benefit). Mortgage payments are averages for households buying with a mortgage. “After inflation” figures use the CPIH price index averaged over each survey year. Overcrowding uses the bedroom standard and is an average of three survey years."),
    ("holidays", "Holidays", "Trips abroad, by year of travel: up to 2023 UK residents (International Passenger Survey); from 2024 Great Britain residents, measured with a new method. Holidays at home: overnight trips within Great Britain by Great Britain residents whose main purpose was a holiday (Great Britain Tourism Survey); Northern Ireland is not covered. Every traveller, adult or child, counts as one trip. “Per 100 residents” divides trips by the mid-year population."),
    ("schools", "Class sizes", "Primary and secondary figures: England only. State-funded schools, classes taught by one teacher, at the January school census. Wales: infant and junior classes in maintained schools at the January school census, from 2023. Scotland: primary classes (all stages) in publicly funded schools at the September pupil census; no secondary figure. Northern Ireland: no published average class size. “2015” means January 2015, in the 2014/15 school year."),
]

TOPIC_SOURCES = {
    "work": ["ons-lf24", "ons-mgsv", "ons-lf25", "ons-mgrz", "ons-ycbe", "ons-ycbh", "ons-ybud", "ons-ybug", "ons-ybuj", "ons-lf2u", "ons-lfk6", "nomis-aps-emp-places", "aps2010", "aps2020", "ons-jobs02"],
    "earnings": ["nomis-ashe-resident", "nomis-ashe-places", "nomis-ashe-percentiles", "ons-l522"],
    "housing": ["ehs-ft1101", "ehs-ft1241", "ehs-fa3201", "ehs-fa2501", "ehs-fa2555", "ons-l522", "ons-affordability", "ehs-ft1421", "ehs-fa1422", "ehs-fa1401", "dluhc-lt109", "wales-dwelling-stock", "scot-stock-by-tenure", "ni-housing-2025-26"],
    "holidays": ["ott-2009to2019", "ott-2019to2023", "ott-2024", "ott-2025", "gbts-2019-gb-summary", "gbts-2022to2023-tables", "gbts-2024-q4-annual-tables", "gbts-2025-toplines", "ons-ukpop", "ons-gbpop", "eurostat-ilc-mdes02-uk", "ons-l522"],
    "schools": ["dfe-spc-2015-tables", "dfe_api", "wg-schools-census-2025", "scot-pupil-census-2025", "ni-de-enrolments-2025-26"],
}

TOPIC_LIMITS = {
    "work": "Job types use the Standard Occupational Classification. It changed from SOC2010 to SOC2020 in 2021, so shares before and after 2021 are not compared here; 2021 is shown on both bases. Job-type figures start in 2011 in these tables. Labour Force Survey response rates fell sharply from 2020, which makes recent estimates less certain. Figures for each nation and region come from the Annual Population Survey, a larger survey over a whole calendar year, so they do not exactly match the UK figures for April to June. Wales and Northern Ireland have smaller samples, so year-to-year moves of a point or two there may be sampling noise. Ages 65 and over are not included in the 16 to 64 rates.",
    "earnings": "Half of full-time employees earn more than the median and half earn less. Figures exclude the self-employed. ASHE has breaks in 2011 and 2021, when the coding of jobs changed, so pay is not compared across them; 2020 and 2021 were affected by furlough. From 2023 the ONS checks the returns of high earners more strictly and has not applied this to earlier years, so it advises caution when comparing 2022 with 2023, especially for higher pay. 2025 figures are provisional. Figures for each nation are for employees who live there, wherever they work. The same UK-wide price index is used for every nation, because official inflation figures are not published for each nation; prices and living costs differ between places, so a higher wage in one place does not mean people there are better off.",
    "housing": "Housing is run separately in each nation, and Wales, Scotland and Northern Ireland measure it with their own surveys and records, which use different questions, dates and definitions. Housing costs, overcrowding and rooms are for England only: the other nations' surveys measure these differently, so they are not shown side by side here. Homes by tenure in each region and nation, with what each one counts, are on their own page. The English Housing Survey covers households in self-contained homes in England, not people in care homes or student halls. Figures for 2025-26 are not yet published. Families with children: our calculation adds three published groups (couples, single lone parents and previously married lone parents). Rents and mortgage payments are averages (means), so a few very high payments pull them up; they are not what a particular household pays, and mortgage payments depend on when the home was bought. A household is overcrowded under the bedroom standard if it has fewer bedrooms than the standard says its members need (one for each couple, one for each other person aged 21 or over, one for each pair of young people aged 10 to 20 of the same sex, and one for each pair of children under 10). Overcrowding figures are three-year averages, so neighbouring years share data; the latest published average ends in 2022-23. Rooms: the way rooms are counted changed in 2011-12 (utility rooms stopped being counted), so room figures are not compared across that change. Because of the pandemic, the 2020-21 survey interviewed people by phone instead of face to face, and its sample had more older people and owners and fewer renters and families with children. The publisher says these effects cannot be fully separated from real change, so figures that include 2020-21 are less certain.",
    "holidays": "Figures for 2008 are not in the tables used here. In 2020 and 2021 travel was restricted by the pandemic and the survey was paused from March 2020, so there are no full-year holiday figures for 2020: ONS’s 2020 figures by purpose cover only January to mid-March, and there is no breakdown by destination. From 2024 the figures cover Great Britain residents with a new method, so they are not compared with earlier years; ONS says annual 2024 mixes the old method (January to June) and the new one (July to December), so 2024 is not compared with 2025 either. Holidays within Great Britain come from a survey that changed method after 2019 and has no full-year figures for 2020 and 2021, so only 2022 onwards are compared with each other; 2019 is shown on its own. Trips per 100 residents is an average across everyone, including children and people who took no holiday: it does not say how many people went away, because these surveys count trips, not travellers. No official statistic, published each year, gives the share of people who took a holiday. The nearest, the share of people whose household could not afford a week’s holiday away, is shown for the 2005 to 2018 surveys, the only years with UK figures. Countries are ranked by all visits (holidays, family visits and business together) because holiday-only figures by country start in 2024.",
    "schools": "Education is run separately in each nation, and each counts classes in its own way, so figures for different nations are shown side by side but not compared. Wales reports infant classes (reception to year 2) and junior classes (years 3 to 6) rather than one primary figure, and the tables used here start in January 2023. Scotland counts classes at a September census and publishes an average for primary classes only. Northern Ireland's school statistics do not include an average class size. Average class size is not the same as the number of pupils per teacher. Averages for infant and key stage 2 classes, and counts of pupils in classes of more than 30 for each, start in January 2016 in the DfE data used here; shares of pupils in classes of more than 30 for primary and secondary schools start in January 2006. January 2008 to 2015 come from the DfE's 2015 national tables and January 2016 onwards from the DfE's current data; both use the same definition (classes taught by one teacher in state-funded schools).",
}


def _val(facts, fid):
    f = facts.get(fid)
    return None if f is None else f.value


def change_cell(facts, num, a_id, b_id, style, kind):
    a, b = _val(facts, a_id), _val(facts, b_id)
    if a is None or b is None:
        return '<span class="missing">no figure for one of the years</span>'
    num.used.update([a_id, b_id])
    if style == "pp":
        v = b - a
        text = f"{v:+.1f} percentage points"
    elif style == "abs":
        v = b - a
        text = f"{v:+.1f} pupils"
    else:
        v = 100 * (b / a - 1)
        text = f"{v:+.1f}%" if abs(v) < 10 else f"{v:+.0f}%"
    cls = "change-up" if v > 0.049 else ("change-down" if v < -0.049 else "")
    if abs(v) < 0.05:
        text = "no change"
    return f'<data class="{cls}" value="{v!r}" data-change="{style}" data-from="{esc(a_id)}" data-to="{esc(b_id)}">{esc(text)}</data>'


def year_links(current, up, href=lambda y: f"{y}.html", strip=False):
    """Every year from 2008, then the earlier years (fewer figures) folded beneath."""
    def items(years):
        out = []
        for y in years:
            if y == current:
                out.append(f'<li><span aria-current="page">{y}</span></li>')
            else:
                out.append(f'<li><a href="{up}{href(y)}">{y}</a></li>')
        return "".join(out)
    early = (f'<details class="early"{" open" if current in EARLY_YEARS else ""}><summary>Earlier years, {EARLY_YEARS[0]} to {EARLY_YEARS[-1]} (fewer figures)</summary>'
             f'<ul class="yearnav{" yearstrip" if strip else ""}">{items(EARLY_YEARS)}</ul></details>')
    return f'<ul class="yearnav{" yearstrip" if strip else ""}">{items(YEARS)}</ul>{early}'


def year_jump(up):
    """Pick one year and go straight to its page. With JavaScript the button
    opens that year's page; without it, the form lands on the list of years."""
    opts = "".join(f'<option value="{y}"{" selected" if y == YEARS[-1] else ""}>{y}</option>' for y in EARLY_YEARS + YEARS)
    return (f'<form class="jumpyear" action="{up}index.html#years" method="get" data-year>'
            f'<label for="jump-year">Go to a year</label><select id="jump-year" name="year">{opts}</select>'
            '<button type="submit">Go</button><p class="pick-status" role="status" aria-live="polite"></p></form>')


YEAR_JS = """<script>
document.querySelectorAll('form[data-year]').forEach(function(f){var s=f.querySelector('[role=status]');f.elements.year.addEventListener('change',function(){if(s)s.textContent=f.elements.year.value+' chosen. Press Go to open it.';});f.addEventListener('submit',function(e){
e.preventDefault();location.href=f.getAttribute('action').replace(/index\\.html(#.*)?$/,'')+f.elements.year.value+'.html';});});
(function(){var y=+new URLSearchParams(location.search).get('year');if(y&&/^\\d{4}$/.test(y)){location.replace(y+'.html');}})();
</script>"""


# The default and suggested pairs of years. build.py sets these from
# pages_ranges.default_years / suggested_years once the facts are loaded.
DEFAULT_PAIR = [2010, LAST]
SUGGESTED = []


def year_grid(cells):
    """Years as a fixed five-column grid. Each row starts at a year ending in 0 or 5,
    so a year is always in the same column and nothing reflows when a cell is tapped.
    cells: (year, html of the cell's content)."""
    if not cells:
        return ""
    first = cells[0][0] % 5 + 1
    lis = [f'<li class="c{first}">{cells[0][1]}</li>' if first > 1 else f"<li>{cells[0][1]}</li>"]
    lis += [f"<li>{c}</li>" for _, c in cells[1:]]
    return f'<ul class="yearnav yeargrid">{"".join(lis)}</ul>'


PICK_STATUS = '<p class="pick-status" role="status" aria-live="polite"></p>'


def compare_form(up, a=None, b=None, anchor=None):
    """Two years to compare. anchor opens the comparison at one topic's section."""
    a, b = a or DEFAULT_PAIR[0], b or DEFAULT_PAIR[1]
    def opts(sel):
        return "".join(f'<option value="{y}"{" selected" if y == sel else ""}>{y}</option>' for y in EARLY_YEARS + YEARS)
    data = f' data-anchor="{anchor}"' if anchor else ""
    at = f'<input type="hidden" name="at" value="{anchor}">' if anchor else ""
    return f'''<form class="pick" action="{up}compare/index.html#all" method="get" data-compare{data}>{at}
<label>First year <select name="from">{opts(a)}</select></label>
<label>Second year <select name="to">{opts(b)}</select></label>
<button type="submit">Compare {min(a, b)} and {max(a, b)}</button>{PICK_STATUS}</form>'''


def compare_with(y, up=""):
    """A short form to compare year y with any other year, plus a few direct links that work without JavaScript."""
    others = [o for o in EARLY_YEARS + YEARS if o != y]
    sel = LAST if y != LAST else LAST - 10
    opts = "".join(f'<option value="{o}"{" selected" if o == sel else ""}>{o}</option>' for o in others)
    quick = [o for o in dict.fromkeys((y - 1, y - 10, LAST)) if o in others]
    links = " · ".join(f'<a href="{up}compare/{min(o, y)}-{max(o, y)}.html">{min(o, y)} and {max(o, y)}</a>' for o in quick)
    return (f'<form class="pick" action="{up}compare/index.html#all" method="get" data-compare id="compare-top">'
            f'<input type="hidden" name="from" value="{y}"><label>Compare {y} with <select name="to">{opts}</select></label>'
            f'<button type="submit">Compare {min(y, sel)} and {max(y, sel)}</button>{PICK_STATUS}</form><p class="small">Or go straight to {links}.</p>')


COMPARE_JS = """<script>
document.querySelectorAll('form[data-compare]').forEach(function(f){var s=f.querySelector('[role=status]'),btn=f.querySelector('button');
function said(){var a=+f.elements.from.value,b=+f.elements.to.value,lo=Math.min(a,b),hi=Math.max(a,b);
if(a===b){btn.textContent='Open '+a;return 'Both years are '+a+'. Press Open '+a+' to see that year, or choose a different year.';}
btn.textContent='Compare '+lo+' and '+hi;return 'Chosen: '+lo+' and '+hi+'. Press Compare '+lo+' and '+hi+' to open the comparison.';}
f.querySelectorAll('select').forEach(function(sel){sel.addEventListener('change',function(){var t=said();if(s)s.textContent=t;});});
f.addEventListener('submit',function(e){
var a=+f.elements.from.value,b=+f.elements.to.value;e.preventDefault();var base=f.getAttribute('action').replace(/index\\.html(#.*)?$/,'');
if(a===b){location.href=base+'../'+a+'.html';return;}
var lo=Math.min(a,b),hi=Math.max(a,b),h=f.getAttribute('data-anchor');location.href=base+lo+'-'+hi+'.html'+(h?'#'+h:'');});});
(function(){var p=new URLSearchParams(location.search),a=+p.get('from'),b=+p.get('to');
if(a&&b&&document.body.hasAttribute('data-compare-index')){var h=/^[a-z]+$/.test(p.get('at')||'')?'#'+p.get('at'):'';if(a===b){location.replace('../'+a+'.html');}else{location.replace(Math.min(a,b)+'-'+Math.max(a,b)+'.html'+h);}}})();
</script>"""

# Years that official sources describe as unusual. A comparison that starts or
# ends in one of them can show a bigger or smaller change than the long-run
# trend, so comparison pages say so where the reader sees the change. Wording
# follows the linked ONS publications; it describes timing, not cause.
TIMING = [
    (range(2008, 2010), "the 2008 recession, when the UK economy shrank by more than 6%", "explain-ons-2008-recession"),
    (range(2020, 2022), "the coronavirus pandemic, when travel was restricted, many employees were furloughed and several of the surveys used here were disrupted", "explain-ons-ashe-2022"),
]


def _years_text(ys):
    ys = list(ys)
    return str(ys[0]) if len(ys) == 1 else f"{ys[0]} to {ys[-1]}" if len(ys) > 2 else f"{ys[0]} and {ys[1]}"


def timing_note(sources, up, *periods):
    """One plain note when a compared year (or any year in a compared range) was unusual."""
    lines, used = [], []
    for label, years in periods:
        years = list(years)
        for yrs, text, src in TIMING:
            hit = [y for y in years if y in yrs]
            if not hit:
                continue
            if len(years) == 1:
                lines.append(f"{label} was in {text}.")
            else:
                lines.append(f"{label} includes {_years_text(hit)}, in {text}.")
            if src in sources and src not in used:
                used.append(src)
    if not lines:
        return ""
    links = "; ".join(f'<a href="{up}figures/{esc(s)}.html">{esc(sources[s]["publisher"])}: {esc(sources[s]["title"])}</a>' for s in used)
    return ('<div class="limit" id="timing"><p><strong>Timing matters.</strong> ' + " ".join(esc(x) for x in lines)
            + " A comparison that starts or ends in an unusual year can show a bigger or smaller change than the years around it."
            + " The longer run beside each lead figure shows whether a change is part of a longer pattern.</p>"
            + (f'<p class="small">Source: {links}.</p>' if links else "") + "</div>")


CAUSE = '<p class="note"><strong>Change is not cause.</strong> These figures show what changed between years. They do not show why. Many things happen at once, including changes in the economy, prices, population and government policy, and these statistics cannot separate them.</p>'
# The same point, placed beside the employment rates for women and men, where a reader
# looking for why a rate changed will see it.
WORK_CAUSE = '<p class="note"><strong>Change is not cause.</strong> These rates show what share of women and men were in work, not why that share changed. Many things happen at once, such as the economy and government policy, and these statistics cannot separate them.</p>'


def topic_block_for_year(facts, num, sources, topic, y, up):
    """Every measure for one topic in one year, as a label, value and period list.

    A list reads better than a three-column table on a phone, and each value
    keeps its own period beside it.
    """
    ms = [m for m in MEAS if m[1] == topic]
    rows = []
    for key, _, label, fid, kind, _, period, group in ms:
        fact_id = fid(y)
        if fact_id not in facts or facts[fact_id].value is None:
            value = '<span class="missing">not available</span>'
            per = esc(period(y))
        else:
            value = num(fact_id, kind) + U.pm(num, fact_id)
            per = esc(period(y)) + (f" ({group(y)})" if group else "")
        rows.append(f'<div><dt>{esc(label)}</dt><dd>{value}</dd><dd class="per">{per}</dd></div>')
    if all(fid(y) not in facts or facts[fid(y)].value is None for _, _, _, fid, *_ in ms):
        # One clear line instead of a long list of identical gaps.
        return f'<p class="missing">Not available: none of the {len(ms)} measures in this section has a figure for this year.</p>'
    return f'<dl class="stats">{"".join(rows)}</dl>'


def headline(facts, num, topic, y, gb=True):
    """One or two plain sentences answering 'what was it like in year y?'."""
    def has(fid):
        return fid in facts and facts[fid].value is not None
    if topic == "work":
        s = []
        if has(f"work.rate.{y}"):
            s.append(f"In April to June {y}, {num(f'work.rate.{y}', 'pct')} of people aged 16 to 64 were in work ({num(f'work.men.{y}', 'pct')} of men and {num(f'work.women.{y}', 'pct')} of women).")
        sc = occ_scheme(y)
        if has(f"work.occshare.{sc}.2000000.{y}"):
            shares = {c: facts[f"work.occshare.{sc}.{c}.{y}"].value for c in OCC_NAMES[sc] if c != "0" and has(f"work.occshare.{sc}.{c}.{y}")}
            top = max(shares, key=shares.get)
            s.append(f"Over all of {y}, the largest group of jobs was {esc(OCC_NAMES[sc][top].lower())}: {num(f'work.occshare.{sc}.{top}.{y}', 'pct')} of workers.")
        else:
            s.append(f"Job-type figures for {y} are not in the tables used here (they start in 2011).")
        return " ".join(s)
    if topic == "earnings":
        if not has(f"earn.real.ft.{y}"):
            return f"No earnings figure for {y}."
        return (f"In April {y}{' (provisional)' if y == LAST else ''}, the middle full-time employee earned {num(f'earn.ft.{y}', 'pounds')} a week before tax. "
                f"In April 2025 prices that is {num(f'earn.real.ft.{y}', 'pounds')}.")
    if topic == "housing":
        if not has(f"house.private.{y}"):
            return f"The English Housing Survey for {y}-{str(y + 1)[2:]} is not yet published."
        own = f"house.owners.{y}"
        s = f"In {sy(y)}, {num(own, 'pct0')} of households in England owned their home and {num(f'house.private.{y}', 'pct0')} rented privately."
        if has(f"house.rent.private.{y}"):
            s += (f" The average private rent was {num(f'house.rent.private.{y}', 'pounds')} a week, social rent {num(f'house.rent.social.{y}', 'pounds')}"
                  f" and the average mortgage payment {num(f'house.mortpay.{y}', 'pounds')} (cash, at the time).")
        if has(f"house.crowd.all.{y}"):
            s += f" Over the three survey years to {sy(y)}, {num(f'house.crowd.all.{y}', 'pct')} of households were overcrowded."
        return s
    if topic == "holidays":
        if not has(f"hol.world.holiday.{y}"):
            return f"No figure for holidays abroad in {y} in the tables used here."
        who = "UK residents" if hol_basis(y) == "UK" else "Great Britain residents"
        extra = ""
        if has(f"hol.europeshare.{y}"):
            extra = f" {num(f'hol.europeshare.{y}', 'pct0')} of these holidays were in Europe."
        s = f"In {y}, {who} made {num(f'hol.world.holiday.{y}', 'millions')} holiday visits abroad"
        if has(f"hol.abroad.per100.{y}"):
            s += f", about {num(f'hol.abroad.per100.{y}', 'int')} for every 100 residents"
        s += f".{extra}"
        if gb and has(f"hol.gb.holiday.{y}"):
            s += f" Great Britain residents also took {num(f'hol.gb.holiday.{y}', 'millions')} overnight holiday trips within Great Britain."
        return s
    if topic == "schools":
        if not has(f"school.primary.{y}"):
            return f"No class-size figure for January {y}."
        s = (f"In January {y}, the average class in an English state primary school had {num(f'school.primary.{y}', 'dp1')} pupils; "
             f"in secondary schools it was {num(f'school.secondary.{y}', 'dp1')}.")
        if has(f"school.wales.infant.{y}"):
            s += (f" In Wales, infant classes averaged {num(f'school.wales.infant.{y}', 'dp1')} pupils and junior classes {num(f'school.wales.junior.{y}', 'dp1')}.")
        if has(f"school.scotland.primary.{y}"):
            s += f" In Scotland, primary classes averaged {num(f'school.scotland.primary.{y}', 'dp1')} pupils at the September {y} census."
        return s
    return ""


def year_spark(facts, num, topic, y, caption=True, mkey=None, measure=None, years=None, point_label=None):
    """Where year y sits in the topic's key measure, as a small dot chart for every year.

    mkey picks another measure from MEAS; measure gives (label, fact-id function,
    kind, group function) for one that is not in MEAS. years replaces the explorer's
    years (for a figure newer than its range, or a longer series). point_label
    names each year; housing defaults to survey years.
    """
    years = years or YEARS
    if measure:
        label, fid, kind, group = measure
    else:
        mkey = mkey or KEY_MEASURES[topic][0]
        _, _, label, fid, kind, _, _, group = next(m for m in MEAS if m[0] == mkey)
    pts = [(yr, facts[fid(yr)].value if fid(yr) in facts else None) for yr in years]
    have = [(yr, v) for yr, v in pts if v is not None]
    if len(have) < 2:
        return ""
    if y is None:
        y = have[-1][0]  # the latest year with a figure
    # The axis ends at the last figure, so a series that stops early is not drawn or labelled as running on
    # to a later year. A year after it still gets its "no figure" sentence in the caption.
    last_fig = have[-1][0]
    years = [yr for yr in years if yr <= last_fig]
    pts = [(yr, v) for yr, v in pts if yr <= last_fig]
    breaks = bool(group) and len({group(yr) for yr in years}) > 1
    yl = point_label or (sy if topic == "housing" else str)  # housing figures are for survey years, April to March
    aria = f"Dot chart of {label.lower()} for each year from {yl(years[0])} to {yl(years[-1])}, with {yl(y)} shown as a larger dark dot. The caption gives the values."
    svg = spark(pts, aria, highlight=y, group=group, axis=(yl(years[0]), yl(years[-1])), kind=kind, point_label=yl)
    if not caption:
        return svg
    lo = min(have, key=lambda t: t[1])
    hi = max(have, key=lambda t: t[1])
    this = (f"The dark dot is {yl(y)}: {num(fid(y), kind)}{F.place(have, y, group if breaks else None)}." if fid(y) in facts and facts[fid(y)].value is not None
            else f"There is no figure for {yl(y)}.")
    cap = (f"<strong>{esc(label)}</strong>, {yl(years[0])} to {yl(years[-1])}. {this} "
           f"The scale runs from {num(fid(lo[0]), kind)} ({yl(lo[0])}) to {num(fid(hi[0]), kind)} ({yl(hi[0])}) and does not start at zero.")
    if len(have) < len(pts):
        cap += " Years with no figure have no dot."
    if breaks:
        cap += " The dashed line marks a change of definition, so dots either side are not joined."
    return f'<figure class="yearspark">{svg}<figcaption>{cap}</figcaption></figure>'


INFANT_LIMIT = "In England the law limits infant classes (reception to year 2) to 30 pupils, with some exceptions."


def most_visited(facts, d, num, y):
    """The most visited country in year y: holidays only where ONS publishes them by
    country (from 2024), otherwise visits for any purpose, which the sentence says."""
    names = d["countries"]["names"]
    hol = top_countries(facts, d, y, 1, kind="holiday") if d["countries"].get("holiday", {}).get(y) else []
    if hol:
        return f"The most visited country for holidays was {esc(names[hol[0]])} ({num(f'hol.cty.{hol[0]}.holiday.{y}', 'millions')} visits)."
    top = top_countries(facts, d, y, 1)
    if not top:
        return ""
    return (f"Counting visits for any purpose (holidays, family visits and business), the most visited country was "
            f"{esc(names[top[0]])} ({num(f'hol.cty.{top[0]}.all.{y}', 'millions')} visits).")


def year_extra(facts, d, num, topic, y):
    """What readers ask about each topic on a year page, inside its answer box (audit 12 gap 2):
    the most visited country, the infant class limit, and that change is not cause."""
    if topic == "holidays":
        line = most_visited(facts, d, num, y)
        return f'<p>{line} <a href="#holidays-countries-{y}">Top ten</a></p>' if line else ""
    if topic == "schools" and _val(facts, f"school.primary.{y}") is not None:
        large = f"school.large.infant.{y}"
        extra = f" In January {y}, {num(large, 'pct')} of infant pupils were in classes of more than 30." if _val(facts, large) is not None else ""
        return f"<p>{INFANT_LIMIT}{extra}</p>"
    return ""


def year_page(facts, d, num, sources, y):
    up = "../"
    body = [f"<h1>Everyday life in {y}</h1>"]
    prev_l = f'<a href="{y - 1}.html">← {y - 1}</a>' if y > FIRST or y - 1 in EARLY_YEARS else "<span></span>"
    next_l = f'<a href="{y + 1}.html">{y + 1} →</a>' if y < LAST else "<span></span>"
    body.append(f'<nav class="pager" aria-label="Previous and next year">{prev_l}{next_l}</nav>')
    body.append(f'<nav aria-label="Choose a year">{year_links(y, "", strip=True)}</nav>')
    body.append('<p>Each topic is measured over its own period, shown beside every figure.</p>')
    body.append(compare_with(y))
    for key, title, scope in TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        body.append(f'<div class="answer"><p>{headline(facts, num, key, y)}</p>{year_extra(facts, d, num, key, y)}</div>')
        body.append(year_spark(facts, num, key, y))
        body.append(topic_block_for_year(facts, num, sources, key, y, up))
        if key == "work":
            body.append(WORK_CAUSE)
        if any(U.has(m[3](y)) for m in MEAS if m[1] == key):
            body.append(f'<p class="small">± is the 95% margin of error, shown where the publisher gives one. {U.how_sure_link("../")}</p>')
        if key == "work" and 2011 <= y:
            body.append(occupation_table(facts, num, d, y))
        if key == "holidays":
            body.append(holiday_regions(facts, num, y))
            body.append(f'<div id="holidays-countries-{y}">{country_table(facts, num, d, y, 10)}</div>')
        body.append(explain.for_year(key, y, sources, up=up))
        body.append(f'<p class="small">{esc(scope)}</p>')
        body.append(f'<p class="small"><a href="{key}.html">{esc(title)} in every year since {FIRST_YEAR[key]}</a></p>')
        body.append(source_line(sources, [s for s in TOPIC_SOURCES[key] if s in sources], up=up))
    body.append(f'<h2 id="compare">Compare {y} with another year</h2>')
    cells = [(o, f'<span aria-current="page">{o}</span>' if o == y else f'<a href="compare/{min(o, y)}-{max(o, y)}.html">{o}</a>') for o in YEARS]
    body.append(f'<p class="small">Choose the other year. {y} is this page, shown filled in.</p>' + year_grid(cells))
    body.append(CAUSE)
    return page(f"life/{y}.html", f"Everyday life in {y}", "\n".join(body), f"Work, earnings, housing, holidays and class sizes in the UK in {y}, from official statistics.", scripts=COMPARE_JS, toc_after_first=True)


def occupation_table(facts, num, d, y):
    groups = d["work"]["occ_groups"]
    rows = []
    schemes = ["SOC2010", "SOC2020"] if y == 2021 else [occ_scheme(y)]
    head = ["Job type (major group)"] + [f"{s}" for s in schemes]
    for code, name in groups["SOC2020"].items():
        if code == "0":
            continue
        rows.append([esc(name)] + [num(f"work.occshare.{s}.{code}.{y}", "pct") if f"work.occshare.{s}.{code}.{y}" in facts else "–" for s in schemes])
    cap = f"Share of people in work by job type, January to December {y}"
    note = ' <p class="small">2021 is shown on both classifications. The difference between the two columns comes from the change of classification, not from a change in jobs.</p>' if y == 2021 else ""
    return details_table("Show all job types", cap, head, rows) + note


def holiday_regions(facts, num, y):
    rows = []
    for rk, label in (("europe", "Europe"), ("namerica", "North America"), ("other", "Rest of the world"), ("world", "All destinations")):
        rows.append([label] + [num(f"hol.{rk}.{pk}.{y}", "millions") for pk in ("holiday", "vfr", "business", "all")])
    return details_table("Show visits by destination and purpose", f"Visits abroad by destination and purpose, {y} (millions)",
                         ["Destination", "Holiday", "Visiting friends or family", "Business", "All visits"], rows)


def top_countries(facts, d, y, n, kind="all"):
    ids = d["countries"][kind].get(y, [])
    return sorted(ids, key=lambda s: -facts[f"hol.cty.{s}.{kind}.{y}"].value)[:n]


def country_table(facts, num, d, y, n):
    names = d["countries"]["names"]
    top = top_countries(facts, d, y, n)
    if not top:
        return f'<p class="small">No figures by country for {y}: the survey was paused for most of the year.</p>'
    hol = y >= 2024
    head = ["Country, most visited first", "All visits"] + (["Of which holidays"] if hol else [])
    rows = [[esc(names[s]), num(f"hol.cty.{s}.all.{y}", "millions") + U.pm(num, f"hol.cty.{s}.all.{y}")] + ([num(f"hol.cty.{s}.holiday.{y}", "millions")] if hol else [])
            for i, s in enumerate(top)]
    cap = f"Most visited countries, {y}: visits abroad by main country visited (all purposes), millions"
    note = "All visits include holidays, visiting friends or family and business. " if not hol else ""
    note += "± is the 95% margin of error published by ONS; where two countries’ ranges overlap, their order could be sampling noise."
    return table(cap, head, rows) + f'<p class="small">{note}</p>'


# One fixed measure per topic leads each comparison page. They are the same for
# every pair of years, so the summary never depends on which way the numbers moved.
KEY_MEASURES = {
    "work": ("work.rate", "The share of people aged 16 to 64 in work"),
    "earnings": ("earn.ft", "Median full-time weekly pay, after inflation,"),
    "housing": ("house.private", "The share of households in England renting privately"),
    "holidays": ("hol.per100", "Holiday visits abroad for every 100 residents"),
    "schools": ("school.primary", "The average class in English state primary schools"),
}

# Plain-English reasons for each definition change that stops a comparison.
BREAK_REASONS = {
    occ_scheme: "Job types were regrouped in 2021, when the classification changed from SOC2010 to SOC2020, so the groups before and after are not the same.",
    earn_basis: "The pay survey changed its method in 2004 and 2006, and changed how it codes jobs in 2011 and 2021, so pay is only compared between years inside one of those periods.",
    rooms_basis: "Rooms were counted differently from 2011-12, when utility rooms stopped being counted.",
    hol_basis: "Up to 2023 the survey counted UK residents; from 2024 it counts Great Britain residents with a new method. ONS says 2024 mixes the two methods (old for January to June, new for July to December), so 2024 is not compared with 2025 either.",
    gb_survey: "The Great Britain Tourism Survey changed its method after 2019, so 2019 is not compared with later years.",
    afford_basis: "ONS says the earnings behind the 1997 and 1998 ratios are weekly pay scaled up to a year, which is not directly comparable with later years.",
    scot_survey: "Scotland’s statisticians advise against comparing its 2020 and 2021 private-renting figures with other years, because the pandemic disrupted the survey behind them.",
}


def _and(items):
    items = [str(x) for x in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def short_break(group, a, b):
    """One short sentence on why years a and b are not compared, naming the change between them."""
    if group is earn_basis:
        method = [y for y in (2004, 2006) if a < y <= b]
        coding = [y for y in (2011, 2021) if a < y <= b]
        parts = ([f"its method in {_and(method)}"] if method else []) + ([f"how it codes jobs in {_and(coding)}"] if coding else [])
        return f"The pay survey changed {' and '.join(parts)}, so pay in {a} and {b} was measured differently."
    if group is occ_scheme:
        return f"Job types were regrouped in 2021 (SOC2010 to SOC2020), so {a} and {b} use different groups."
    if group is rooms_basis:
        return f"Rooms were counted differently from 2011-12, so {a} and {b} do not count the same rooms."
    if group is hol_basis:
        if 2024 in (a, b):
            return "2024 mixes the survey’s old and new methods, so it is not compared with any other year."
        return f"The survey changed its method in 2024, so {a} and {b} were measured differently."
    if group is gb_survey:
        return f"The Great Britain Tourism Survey changed its method after 2019, so {a} and {b} were measured differently."
    if group is afford_basis:
        return f"The earnings behind the ratio for 1997 and 1998 are weekly pay scaled up to a year, so {a} and {b} were measured differently."
    if group is scot_survey:
        return "Scotland’s statisticians advise against comparing 2020 and 2021 with other years, because the pandemic disrupted the survey."
    return "The definition changed between these years."


# What a reader would otherwise read a difference as, for each topic.
REAL_CHANGE = {
    "work": "who was in work",
    "earnings": "pay",
    "housing": "how people live",
    "holidays": "how often people went abroad",
    "schools": "class sizes",
}


def not_compared_means(topic, kind):
    """What "not compared" means, in plain words, after the reason (audit 12 gap 3).

    kind is "break" (measured differently) or "missing" (no figure for one year)."""
    if kind == "break":
        return (" The site shows both figures but deliberately works out no change between them: "
                f"some or all of the gap could come from the new way of measuring, not from a real change in {REAL_CHANGE[topic]}.")
    return " No change can be worked out without a figure for both."


def near_sentence(facts, num, m, near, topic, lead="Nearest years measured the same way", show_change=True):
    """A link to the nearest comparable pair of years, with that pair's change for measure m."""
    if not near:
        return ""
    x, z = near
    ch = change_cell(facts, num, m[3](x), m[3](z), m[5], m[4]) if m[5] and show_change else ""
    return f' {lead}: <a href="{x}-{z}.html#{topic}">{x} and {z}</a>' + (f" (change: {ch})." if ch else ".")


def missing_reason(mkey, y):
    """Why a measure has no figure for year y, in plain words."""
    if mkey.startswith("work.occ.") and y < 2011:
        return "job-type figures in these tables start in 2011"
    if mkey.startswith("school.wales.") and y < 2023:
        return "the Welsh class-size tables used here start in January 2023"
    if mkey == "nat.house.private.ni":
        return "the Northern Ireland table used here starts in 2012-13" if y < 2012 else f"Northern Ireland’s figures for {sy(y)} are not yet published"
    if mkey.startswith("house.crowd.") and y > 2022:
        return "the latest published overcrowding average ends in 2022-23"
    if mkey.startswith("house.") and y > 2024:
        return f"the English Housing Survey for {sy(y)} is not yet published"
    if mkey.startswith("hol.gb"):
        if y in (2020, 2021):
            return "the Great Britain Tourism Survey has no full-year figures for 2020 and 2021"
        if y < 2019:
            return "earlier Great Britain Tourism Survey years used other methods and are not shown"
    if mkey.startswith("hol.") and y == 2008:
        return "2008 is not in the tables used here"
    if mkey.startswith("hol.") and y == 2020:
        return "the survey stopped on 16 March 2020, so there is no full-year figure for holidays or where people went"
    return "there is no figure in the tables used here"


def _status(facts, m, a, b):
    """'ok', 'missing' or 'break' for one measure and a pair of years."""
    mkey, topic, label, fid, kind, style, period, group = m
    if _val(facts, fid(a)) is None or _val(facts, fid(b)) is None:
        return "missing"
    if group and group(a) != group(b):
        return "break"
    return "ok"


def _change(facts, num, m, a, b):
    """Signed change between the two years, plus its checked <data> element."""
    fa, fb = m[3](a), m[3](b)
    va, vb = _val(facts, fa), _val(facts, fb)
    v = (vb - va) if m[5] in ("pp", "abs") else 100 * (vb / va - 1)
    return v, change_cell(facts, num, fa, fb, m[5], m[4])


def _pair_bars(facts, num, m, a, b):
    """Two bars from zero, one per year, scaled to the larger of the two values."""
    fa, fb = m[3](a), m[3](b)
    top = max(_val(facts, fa), _val(facts, fb)) or 1
    out = []
    for y, f, cls in ((a, fa, "cmp-a"), (b, fb, "cmp-b")):
        w = max(0.0, 100 * _val(facts, f) / top)
        out.append(f'<div class="cmp-bar"><span class="cmp-y">{y}</span><span class="cmp-track" aria-hidden="true"><span class="cmp-fill {cls}" style="width:{w:.1f}%"></span></span>'
                   f'<span class="cmp-v">{num(f, m[4])}</span></div>')
    return "".join(out)


def _row_card(facts, num, m, a, b):
    mkey, topic, label, fid, kind, style, period, group = m
    v, ch = _change(facts, num, m, a, b)
    return (f'<li><p class="cmp-label">{esc(label)}</p>{_pair_bars(facts, num, m, a, b)}'
            f'<p class="cmp-change">Change: {ch} <span class="small">({esc(period(a))} to {esc(period(b))})</span></p>'
            f'{U.check_sentence(facts, num, fid(a), fid(b), style, (str(a), str(b)))}</li>')


def _nearest_pair(facts, m, a, b):
    """The closest other pair of years that has a comparable figure, if any."""
    best = None
    for y in YEARS:
        for (x, z) in ((a, y), (y, b)):
            if x >= z or (x, z) == (a, b):
                continue
            if _status(facts, m, x, z) == "ok":
                dist = abs(x - a) + abs(z - b)
                if best is None or dist < best[0]:
                    best = (dist, x, z)
    return None if best is None else best[1:]


def _join_labels(labels):
    """'Share of workers in: A', 'Share of workers in: B' -> 'Share of workers in: A; B'."""
    heads = {l.split(": ", 1)[0] for l in labels if ": " in l}
    if len(labels) > 1 and len(heads) == 1 and all(": " in l for l in labels):
        head = heads.pop()
        return esc(head) + ": " + "; ".join(esc(l.split(": ", 1)[1]) for l in labels)
    return "; ".join(esc(l) for l in labels)


def key_sentence(facts, num, topic, a, b):
    """One plain sentence for the topic's fixed lead measure, or why it is not compared."""
    mkey, subject = KEY_MEASURES[topic]
    m = next(x for x in MEAS if x[0] == mkey)
    st = _status(facts, m, a, b)
    fa, fb = m[3](a), m[3](b)
    if st == "ok":
        v, ch = _change(facts, num, m, a, b)
        verb = "went up from" if v > 0.049 else ("went down from" if v < -0.049 else "was about the same:")
        return (f"<p>{esc(subject)} {verb} {num(fa, m[4])} ({esc(m[6](a))}) {'and' if abs(v) < 0.05 else 'to'} {num(fb, m[4])} ({esc(m[6](b))}).{(' Change: ' + ch + '.') if abs(v) >= 0.05 else ''}</p>"
                + _pair_bars(facts, num, m, a, b) + U.check_sentence(facts, num, fa, fb, m[5], (str(a), str(b)))
                + long_run(facts, num, m, b, f"../{topic}.html"))
    link = near_sentence(facts, num, m, _nearest_pair(facts, m, a, b), topic)
    if st == "break":
        return (f"<p>{esc(subject.rstrip(','))}: {num(fa, m[4])} in {esc(m[6](a))} and {num(fb, m[4])} in {esc(m[6](b))}, "
                f"<strong>not compared</strong>. {esc(short_break(m[7], a, b))}{esc(not_compared_means(topic, 'break'))}{link}</p>")
    missing = [y for y in (a, b) if _val(facts, m[3](y)) is None]
    y = missing[0]
    return (f"<p>{esc(subject.rstrip(','))}: <strong>not compared</strong>, because there is no figure for {y}: {esc(missing_reason(mkey, y))}."
            f"{esc(not_compared_means(topic, 'missing'))}{link}</p>")


def _same_way(m):
    """Every comparability rule that applies to a measure, as one function of the year.

    The year explorer and the longer series can each record a change of method
    (pay, for example, breaks in 2004 and 2006 only in the longer series), so a
    year counts as measured the same way only if it matches on all of them."""
    from .pages_history import LONG
    rules = [g for g in [m[7]] + [x[7] for x in MEAS + LONG if x[0] == m[0] and x[3](2010) == m[3](2010)] if g]
    return lambda y: tuple(g(y) for g in rules)


def long_run(facts, num, m, b, href):
    """Longer-run context beside a headline change, by a fixed rule.

    Over every year measured the same way as year b: the change from the first
    year to the last, and the lowest and highest yearly figures. Years without a
    figure are counted and said, never filled in."""
    fid, kind, style, period = m[3], m[4], m[5], m[6]
    same = _same_way(m)
    years = [y for y in EARLY_YEARS + YEARS if _val(facts, fid(y)) is not None and same(y) == same(b)]
    if len(years) < 3:
        return ""
    first, last = years[0], years[-1]
    vals = {y: _val(facts, fid(y)) for y in years}
    unit = " pupils" if style == "abs" else ""

    def at(v):
        ys = [y for y in years if vals[y] == v]
        when = [esc(period(y)) for y in ys]
        if len(ys) > 2 and ys == list(range(ys[0], ys[-1] + 1)):
            # A run of tied years reads as one span, not a list.
            when = f"each year, {when[0]} to {when[-1]}"
        else:
            when = ", ".join(when[:-1]) + " and " + when[-1] if len(when) > 1 else when[0]
        return f"{num(fid(ys[0]), kind)}{unit} ({when})"

    gaps = (last - first + 1) - len(years)
    gap_text = f" {gaps} of these years have no figure." if gaps else ""
    how = "same method"
    if m[1] == "work" and first < 1992:
        # ONS joins these years into one series, but the survey itself changed (see LIMITS in pages_history).
        how = "one ONS series (the Labour Force Survey began in 1973 and has run every quarter since 1992, so read the early years as the long-run pattern)"
    return (f'<p class="small cmp-long">Longer run, {esc(period(first))} to {esc(period(last))}, {how}: '
            f'{change_cell(facts, num, fid(first), fid(last), style, kind)}. Lowest {at(min(vals.values()))}, '
            f'highest {at(max(vals.values()))}.{gap_text} <a href="{href}">Chart of every year</a></p>')


def largest_changes(facts, num, a, b, n=3):
    """The biggest comparable changes, ranked by size by a fixed rule (cash figures left out)."""
    ok = [m for m in MEAS if not m[0].endswith("cash") and _status(facts, m, a, b) == "ok"]
    out = []
    for style, title in (("pp", "Shares, in percentage points"), ("pct", "Money and numbers, in per cent")):
        ranked = sorted((m for m in ok if m[5] == style), key=lambda m: -abs(_change(facts, num, m, a, b)[0]))[:n]
        if not ranked:
            continue
        items = []
        for m in ranked:
            topic_title = dict((t[0], t[1]) for t in TOPICS)[m[1]]
            _, ch = _change(facts, num, m, a, b)
            items.append(f'<li><a href="#{m[1]}">{esc(topic_title)}</a>: {esc(m[2])}, {num(m[3](a), m[4])} → {num(m[3](b), m[4])} ({ch})</li>')
        out.append(f'<h3>{title}</h3><ol class="cmp-top">{"".join(items)}</ol>')
    return "".join(out)


def compare_page(facts, d, num, sources, a, b):
    titles = dict((t[0], t[1]) for t in TOPICS)
    body = [f"<h1>{a} compared with {b}</h1>"]
    body.append(f'<p><a href="../{a}.html">Everyday life in {a}</a> · <a href="../{b}.html">Everyday life in {b}</a> · <a href="index.html">Choose two other years</a></p>')
    # Summary first: the same lead measure for every topic, then the biggest changes by a fixed rule.
    # "In brief" has no id, so the contents list goes after it and the answers come first.
    body.append('<h2 class="brief">In brief</h2>')
    body.append('<p class="small">The same lead figure for each topic on every comparison page, whichever way it moved, each for its own period (in brackets). '
                'Shares change in percentage points: 20% to 25% is +5 percentage points. Money and counts change in per cent, class sizes in pupils.</p>')
    for key, title, _ in TOPICS:
        body.append(f'<div class="cmp-key"><h3>{esc(title)}</h3>{key_sentence(facts, num, key, a, b)}</div>')
    top = largest_changes(facts, num, a, b)
    if top:
        body.append(f'<h2 id="largest">Largest changes between {a} and {b}</h2>')
        body.append('<p class="small">Every comparable figure on this page, ranked by the size of its change: shares and amounts separately, after-inflation figures rather than cash.</p>')
        body.append(top)
    body.append(timing_note(sources, "../../", (str(a), [int(a)]), (str(b), [int(b)])))
    body.append(CAUSE)
    for key, title, scope in TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        # On a phone the section shows where the figures cover; "In brief" already gives
        # the lead figure, so every other figure waits in the fold.
        where, _, more_scope = scope.partition(". ")
        body.append(f'<p class="small">{esc(where + "." if more_scope else where)}</p>')
        ms = [m for m in MEAS if m[1] == key]
        ok = [m for m in ms if _status(facts, m, a, b) == "ok" and not m[0].endswith("cash")]
        breaks = [m for m in ms if _status(facts, m, a, b) == "break"]
        missing = [m for m in ms if _status(facts, m, a, b) == "missing"]
        body.append(FOLD + "<!--keepfold-->")
        if more_scope:
            body.append(f'<p class="small">{esc(more_scope)}</p>')
        if ok:
            body.append(f'<ul class="cmp-list">{"".join(_row_card(facts, num, m, a, b) for m in ok)}</ul>')
        if any(m[0].endswith("cash") and _status(facts, m, a, b) == "ok" for m in ms):
            body.append('<p class="small">Amounts above are after inflation. Cash amounts, as paid at the time, are in the full table below.</p>')
        if breaks:
            reasons = {}
            for m in breaks:
                reasons.setdefault(short_break(m[7], a, b), []).append(m)
            items = []
            for reason, group in reasons.items():
                link = near_sentence(facts, num, group[0], _nearest_pair(facts, group[0], a, b), key, "Nearest comparable years", show_change=False)
                vals = "".join(f"<li>{esc(m[2])}: {num(m[3](a), m[4])} in {a}, {num(m[3](b), m[4])} in {b}</li>" for m in group)
                items.append(f"<li><p>{esc(reason)}{link}</p><p class=\"small\">Shown side by side, not compared:</p><ul class=\"small cmp-vals\">{vals}</ul></li>")
            body.append(f'<h3>Not compared: measured differently in {a} and {b}</h3><p class="small">{esc(not_compared_means(key, "break").strip())}</p><ul class="cmp-notes">{"".join(items)}</ul>')
        if missing:
            reasons = {}
            for m in missing:
                for y in (a, b):
                    if _val(facts, m[3](y)) is None:
                        reasons.setdefault((y, missing_reason(m[0], y)), []).append(m)
                        break
            items = []
            for (y, reason), group in reasons.items():
                link = near_sentence(facts, num, group[0], _nearest_pair(facts, group[0], a, b), key, "Nearest comparable years", show_change=False)
                names = _join_labels([m[2] for m in group])
                items.append(f"<li><p>No figure for {y}: {esc(reason)}.{link}</p><p class=\"small\">Not shown: {names}.</p></li>")
            body.append(f'<h3>Not compared: no figure for one of the years</h3><ul class="cmp-notes">{"".join(items)}</ul>')
        rows = []
        for m in ms:
            fa, fb = m[3](a), m[3](b)
            st = _status(facts, m, a, b)
            if st == "break":
                ch = f'<span class="missing">not comparable: definition changed ({esc(m[7](a))} → {esc(m[7](b))})</span>'
            else:
                ch = change_cell(facts, num, fa, fb, m[5], m[4])
            na = '<span class="missing">not available</span>'
            rows.append([esc(m[2]), num(fa, m[4]) if fa in facts else na, num(fb, m[4]) if fb in facts else na, ch])
        body.append(details_table(f"Show the full {esc(title.lower())} table", f"{title}: {a} and {b}", ["Measure", str(a), str(b), "Change"], rows))
        if key == "holidays":
            names = d["countries"]["names"]
            ta, tb = top_countries(facts, d, a, 5), top_countries(facts, d, b, 5)
            if ta or tb:
                crow = []
                for i in range(5):
                    cell = lambda t, y: (f"{esc(names[t[i]])} ({num(f'hol.cty.{t[i]}.all.{y}', 'millions')})" if i < len(t) else '<span class="missing">not available</span>')
                    crow.append([str(i + 1), cell(ta, a), cell(tb, b)])
                body.append(table(f"Five most visited countries, {a} and {b}: all visits abroad, millions", ["Rank", str(a), str(b)], crow))
                if hol_basis(a) != hol_basis(b):
                    desc = {"UK": "UK residents", "GB, mixed methods": "Great Britain residents, half with the old method and half with the new", "GB": "Great Britain residents measured with the new method"}
                    body.append(f'<p class="small">{a} counts {desc[hol_basis(a)]} and {b} {desc[hol_basis(b)]}, so the numbers are listed side by side but not compared.</p>')
        body.append(f'<details class="limit"><summary>Limits of the {esc(title.lower())} figures</summary><p>{esc(TOPIC_LIMITS[key])}</p></details>')
        body.append(source_line(sources, [s for s in TOPIC_SOURCES[key] if s in sources], up="../../"))
    body.append(f'<h2 id="other">Compare other years</h2>')
    body.append(compare_form("../", a, b))
    return page(f"life/compare/{a}-{b}.html", f"{a} compared with {b}", "\n".join(body), f"How work, pay, housing, holidays and class sizes differed between {a} and {b}.", scripts=COMPARE_JS)


def compare_index(sources):
    from .pages_ranges import DEFAULT_RULE, pair_context
    body = ["<h1>Compare two years</h1>", "<p>Pick two years to see work, pay, housing, holidays and class sizes side by side.</p>", compare_form("../")]
    if SUGGESTED:
        a, b = SUGGESTED[0]
        links = "".join(f'<li><a href="{x}-{y}.html">{x} compared with {y}</a></li>' for x, y in SUGGESTED)
        body.append(f'<div class="answer"><p><strong>Suggested comparisons, with all five topics filled:</strong></p><ul>{links}</ul>'
                    f'<p class="small">{esc(DEFAULT_RULE)}{esc(pair_context(a, b))} The others are the latest of these years compared with 10 and 5 years before it, where every topic can be compared. '
                    f'For the years since the pandemic, see <a href="{RECENT}-{LAST}.html">{RECENT} compared with {LAST}</a>, where some topics cannot be compared. '
                    'Years from 2024 cannot be compared for holidays abroad, because the survey changed then (and 2024 mixes the old and new methods), and housing figures for 2025 are not yet published.</p></div>')
    body.append('<p>Or <a href="spans/index.html">compare two sets of years</a>, for example the average of three years with the average of three later years.</p>')
    body.append("<h2 id='all'>All comparisons</h2><p>Every pair of years has its own page.</p>")
    for a in YEARS[:-1]:
        body.append(f'<h3>{a} with…</h3>' + year_grid([(b, f'<a href="{a}-{b}.html">{b}</a>') for b in YEARS if b > a]))
    # Earlier years have fewer figures, so their pairs fold away beneath.
    early = []
    for a in EARLY_YEARS:
        early.append(f'<h3>{a} with…</h3>' + year_grid([(b, f'<a href="{a}-{b}.html">{b}</a>') for b in EARLY_YEARS + YEARS if b > a]))
    body.append(f'<h2 id="earlier">Comparisons with earlier years, {EARLY_YEARS[0]} to {EARLY_YEARS[-1]}</h2>'
                '<p>Fewer official figures reach back before 2008: the employment rate from 1971, visits abroad from 1980, owning and renting in England '
                'from 1981, pay from 2002 and class sizes from 2006. These pages compare only those figures, and only where both years were measured the same way.</p>'
                f'<details><summary>Show every pair with a year from {EARLY_YEARS[0]} to {EARLY_YEARS[-1]}</summary>{"".join(early)}</details>')
    html = page("life/compare/index.html", "Compare two years", "\n".join(body), "Compare everyday life in the UK between two years.", scripts=COMPARE_JS)
    return html.replace("<body>", "<body data-compare-index>", 1)


# Words for the housing tenure groups in chart titles.
TENURE_WORDS = {"Own outright": "the share owning outright", "Own with a mortgage": "the share buying with a mortgage",
                "Rent from council or housing association": "the share renting from a council or housing association",
                "Rent privately": "the share renting privately"}
CLASS_FINDING = F.pair("Primary class sizes", "secondary class sizes")


def series_chart(facts, title, items, unit, breaks=(), ymin=None, scale=1, split_breaks=False, kind=None, num=None, point_label=str, finding=None):
    labels = [str(y) for y in YEARS]
    series = [(name, [_val(facts, fid(y)) for y in YEARS], style) for name, fid, style in items]
    ids = [[fid(y) if _val(facts, fid(y)) is not None else None for y in YEARS] for _, fid, _ in items]
    return line_chart(title, labels, series, unit, breaks=breaks, ymin=ymin, scale=scale, split_breaks=split_breaks,
                      kind=kind, ids=ids, num=num, point_labels=[point_label(y) for y in YEARS], finding=finding)


def groups_chart(facts, title, items, unit, years=None, breaks=(), split_breaks=False, ymin=None, kind=None, num=None, point_label=str, summary_note="", finding=None):
    """Small multiples: one panel per group, all on one scale. items: (name, fid(year))."""
    years = list(years or YEARS)
    series = [(name, [_val(facts, fid(y)) for y in years]) for name, fid in items]
    ids = [[fid(y) if _val(facts, fid(y)) is not None else None for y in years] for _, fid in items]
    return small_multiples(title, [str(y) for y in years], series, unit, kind, ids=ids, num=num, breaks=breaks,
                           split_breaks=split_breaks, ymin=ymin, point_labels=[point_label(y) for y in years], summary_note=summary_note,
                           finding=finding)


def _work(facts, d, num, sources):
    """(answer box, detail parts) for the work topic."""
    body = []
    y = LAST
    # The survey can be a year newer than the explorer's range, as the home page shows (audit 11 judge)
    nw = LAST + 1
    newer = ""
    if _val(facts, f"work.rate.{nw}") is not None:
        mw = (f' ({num(f"work.men.{nw}", "pct")} of men and {num(f"work.women.{nw}", "pct")} of women)'
              if all(_val(facts, f"work.{k}.{nw}") is not None for k in ("men", "women")) else "")
        newer = (f' The April to June {nw} survey found {num(f"work.rate.{nw}", "pct")} in work{mw}. '
                 f'It is not on the year pages, which stop at {LAST}, the latest year that most topics have.')
    jb = d["life_extra"]["jobs"]
    jf, jl = jb["years"][0], jb["years"][-1]
    # Manufacturing's long fall is asked about often, so it sits in the answer box,
    # not only in the jobs by industry section lower down (audit 11 gap 6).
    # Women's and men's rates sit in the answer box too, so a reader who stops at the first
    # screen sees them (audit 14 gap 1: a phone reader could not find them).
    wf = FIRST_YEAR["work"]
    sex = (f'<p>Since {wf}, women\'s rate went from {num(f"work.women.{wf}", "pct")} to {num(f"work.women.{y}", "pct")}; '
           f'men\'s from {num(f"work.men.{wf}", "pct")} to {num(f"work.men.{y}", "pct")}.</p>')
    answer = (f'<div class="answer"><p>{headline(facts, num, "work", y)}{newer}</p>{sex}'
              f'<p>Manufacturing went from {num(f"jobs.share.C.{jf}", "pct")} of all jobs in June {jf} to {num(f"jobs.share.C.{jl}", "pct")} in June {jl}'
              f'{" (provisional)" if jl == jb["provisional"] else ""}. <a href="#work-industry">Jobs by industry</a></p></div>')
    body.append(U.topic_line(num, "work", LAST))
    body.append(series_chart(facts, "Employment rate, ages 16 to 64", [("Men", lambda y: f"work.men.{y}", "a"), ("Women", lambda y: f"work.women.{y}", "b")], "Per cent of people aged 16 to 64 in work, April to June each year", kind="pct", num=num,
                             finding=F.narrowing("The gap between men's and women's employment rates", lambda d: f"{d:.1f} points")))
    body.append(details_table("Show work figures for every year", "Work, United Kingdom", ["Year", "Employment rate 16-64", "Men", "Women", "People in work", "Part-time share"],
                              [[str(y), num(f"work.rate.{y}", "pct"), num(f"work.men.{y}", "pct"), num(f"work.women.{y}", "pct"), num(f"work.level.{y}", "millions_people"), num(f"work.ptshare.{y}", "pct")] for y in YEARS]))
    groups = d["work"]["occ_groups"]
    rows = []
    for yy in YEARS:
        for s in (["SOC2010", "SOC2020"] if yy == 2021 else [occ_scheme(yy)]):
            if f"work.occshare.{s}.2000000.{yy}" not in facts:
                rows.append([f"{yy}", "<span class='missing'>not in these tables</span>"] + [""] * 8)
                break
            rows.append([f"{yy} ({s})"] + [num(f"work.occshare.{s}.{c}.{yy}", "pct") for c in groups["SOC2020"] if c != "0"])
    head = ["Year"] + [esc(n.split(" occupations")[0].split(",")[0]) for c, n in groups["SOC2020"].items() if c != "0"]
    oyears = [yy for yy in YEARS if f"work.occshare.{occ_scheme(yy)}.2000000.{yy}" in facts]
    body.append(groups_chart(facts, "Share of people in work by job type",
                             [(n.split(" occupations")[0], (lambda c: lambda yy: f"work.occshare.{occ_scheme(yy)}.{c}.{yy}")(c)) for c, n in groups["SOC2020"].items() if c != "0"],
                             "Per cent of people in work, January to December, United Kingdom. Up to 2020 SOC2010 job types; from 2021 SOC2020, so the lines break there",
                             years=oyears, breaks=[(oyears.index(2021), "New job classification")] if 2021 in oyears else (), split_breaks=True, ymin=0, kind="pct", num=num,
                             finding=F.leader("{name} jobs were the largest group {span}", which="last")))
    body.append(details_table("Show job types for every year", "Share of people in work by job type (major group), January to December", head, rows))
    body.extend(work_ages_block(facts, num))
    body.extend(industry_block(facts, num, d))
    body.extend(places_block(facts, num, "work"))
    return answer, body


def same_basis_runs(facts, fid, years, group):
    """Each stretch of years measured the same way, as (first, last) years that have a figure.

    Changes are worked out only inside one stretch, never across a break."""
    runs = {}
    for y in years:
        if _val(facts, fid(y)) is not None:
            runs.setdefault(group(y), []).append(y)
    return [(ys[0], ys[-1]) for ys in runs.values() if len(ys) > 1]


def _how(ch):
    return "about the same as" if abs(ch) < 2 else (f"{abs(ch):.0f}% more than" if ch > 0 else f"{abs(ch):.0f}% less than")


EARN_BREAKS = (2011, 2021)


def _how_short(ch):
    return "About the same" if abs(ch) < 2 else (f"{abs(ch):.0f}% more" if ch > 0 else f"{abs(ch):.0f}% less")


def earn_stretches(facts):
    """Each stretch of years the pay survey measured the same way, newest first,
    as (first, last, % change after inflation). Never crosses a break."""
    years = list(range(FIRST_YEAR["earnings"], LAST + 1))
    runs = same_basis_runs(facts, lambda y: f"earn.real.ft.{y}", years, earn_basis)
    return [(a, b, 100 * (_val(facts, f"earn.real.ft.{b}") / _val(facts, f"earn.real.ft.{a}") - 1)) for a, b in reversed(runs)]


def earn_before_after(num, a, b, ch, cls="ba"):
    """Before and after pay, after inflation, as two big numbers (audit 10 gap 6)."""
    return (f'<div class="{cls}"><p><span class="ba-y">April {a}</span><span class="ba-v">{num(f"earn.real.ft.{a}", "pounds")}</span></p>'
            f'<span class="ba-to" aria-hidden="true">→</span>'
            f'<p><span class="ba-y">April {b}</span><span class="ba-v">{num(f"earn.real.ft.{b}", "pounds")}</span></p></div>')


def _change_words(facts, num, a, b):
    """Plain words and the tagged change for real pay between two years inside one stretch."""
    ch = 100 * (_val(facts, f"earn.real.ft.{b}") / _val(facts, f"earn.real.ft.{a}") - 1)
    word = "was about the same" if abs(ch) < 2 else ("rose" if ch > 0 else "fell")
    return f"{word} ({change_cell(facts, num, f'earn.real.ft.{a}', f'earn.real.ft.{b}', 'pct', 'pounds')})"


def _earnings(facts, d, num, sources):
    """(answer box, detail parts) for the earnings topic."""
    body = []
    stretches = earn_stretches(facts)
    a, b, ch = stretches[0]
    earlier = "".join(f'<li>{num(f"earn.real.ft.{x}", "pounds")} in April {x} to {num(f"earn.real.ft.{z}", "pounds")} in April {z}: '
                      f'{change_cell(facts, num, f"earn.real.ft.{x}", f"earn.real.ft.{z}", "pct", "pounds")}</li>' for x, z, _ in stretches[1:3])
    answer = (f'<div class="answer"><h2 class="ba-h">Pay after inflation: before and after</h2>'
              f'<p class="small">Middle full-time employee, £ a week before tax, UK, both years in April {LAST} prices</p>'
              + earn_before_after(num, a, b, ch) +
              f'<p>After allowing for rising prices, pay in April {b} was {_how(ch)} in April {a} ({change_cell(facts, num, f"earn.real.ft.{a}", f"earn.real.ft.{b}", "pct", "pounds")}). '
              f'In cash, at the time, pay went from {num(f"earn.ft.{a}", "pounds")} to {num(f"earn.ft.{b}", "pounds")} a week.</p>'
              f'<p>The survey changed how it codes jobs in 2011 and 2021, so pay is compared only within each stretch. Earlier stretches:</p>'
              f'<ul class="ba-list">{earlier}</ul></div>')
    body.append(U.topic_line(num, "earnings", LAST))
    body.append(series_chart(facts, "Median weekly pay of full-time employees, after inflation", [("Men", lambda y: f"earn.real.ft_men.{y}", "a"), ("Women", lambda y: f"earn.real.ft_women.{y}", "b")],
                             "£ a week before tax, April each year, in April 2025 prices (adjusted with CPIH, the official consumer prices index that includes housing costs). The lines break in 2011 and 2021, when the survey changed the codes it uses to sort jobs into types (“jobs recoded”), so pay is not compared across them",
                             breaks=[(YEARS.index(y), "Jobs recoded") for y in EARN_BREAKS], split_breaks=True, kind="pounds", num=num,
                             finding=F.narrowing("After inflation, the gap between men's and women's median full-time pay", lambda d: f"£{d:,.0f} a week", which="last")))
    body.append(f'<p>The chart breaks in 2011, so the years either side are not joined into one change. '
                f'From April 2008 to April 2010 real pay {_change_words(facts, num, 2008, 2010)}. '
                f'From April 2011 to April 2014 it {_change_words(facts, num, 2011, 2014)}. '
                f'This page therefore gives no single change from 2008 to 2014.</p>')
    body.append(details_table("Show earnings for every year", "Median gross weekly pay, United Kingdom, April each year",
                              ["Year", "Full-time (cash)", "Full-time (2025 prices)", "Full-time men", "Full-time women", "Part-time"],
                              [[str(y), num(f"earn.ft.{y}", "pounds"), num(f"earn.real.ft.{y}", "pounds"), num(f"earn.real.ft_men.{y}", "pounds"), num(f"earn.real.ft_women.{y}", "pounds"), num(f"earn.real.pt.{y}", "pounds")] for y in YEARS]))
    body.append('<p class="small">All columns except “Full-time (cash)” are in April 2025 prices.</p>')
    body.extend(spread_block(facts, num, d, a))
    body.extend(places_block(facts, num, "earnings"))
    return answer, body

def _housing(facts, d, num, sources):
    """(answer box, detail parts) for the housing topic."""
    body = []
    y = LAST
    hy = max(yy for yy in YEARS if _val(facts, f"house.private.{yy}") is not None)
    answer = (f'<div class="answer"><p>{headline(facts, num, "housing", hy)} In {FIRST}-{str(FIRST + 1)[2:]}, {num(f"house.private.{FIRST}", "pct0")} rented privately.</p></div>')
    body.append(U.topic_line(num, "housing", LAST))
    hyears = [y for y in YEARS if y <= hy]
    body.append(groups_chart(facts, "How households in England live", [("Own outright", lambda y: f"house.outright.{y}"), ("Own with a mortgage", lambda y: f"house.mortgage.{y}"),
                                                                       ("Rent from council or housing association", lambda y: f"house.social.{y}"), ("Rent privately", lambda y: f"house.private.{y}")],
                             "Per cent of households in England, survey year starting in the year shown", years=hyears, ymin=0, kind="pct", num=num, point_label=sy,
                             finding=F.moves(TENURE_WORDS)))
    body.append(details_table("Show housing for every year", "Housing tenure, England, % of households",
                              ["Survey year", "Own outright", "Mortgage", "Social rent", "Private rent", "Families with children renting privately"],
                              [[f"{y}-{str(y + 1)[2:]}", num(f"house.outright.{y}", "pct"), num(f"house.mortgage.{y}", "pct"), num(f"house.social.{y}", "pct"), num(f"house.private.{y}", "pct"),
                                num(f"house.kids.private.{y}", "pct") if f"house.kids.private.{y}" in facts else "<span class='missing'>not available</span>"] for y in YEARS if f"house.private.{y}" in facts]
                              + [[f"{y}-{str(y + 1)[2:]}", "<span class='missing'>not yet published</span>", "", "", "", ""] for y in YEARS if f"house.private.{y}" not in facts]))
    body.extend(housing_costs_block(facts, num, d))
    body.extend(afford_block(facts, num, d))
    body.extend(housing_space_block(facts, num))
    body.extend(housing_places_block(facts, num, d))
    return answer, body

def _hol_cell(facts, num, y):
    """Holiday visits abroad for one year; a part-year figure says which weeks it covers."""
    if f"hol.world.holiday.{y}.part" in facts:
        return f'{num(f"hol.world.holiday.{y}.part", "millions")} <span class="small">({esc(facts[f"hol.world.holiday.{y}.part"].period)} only; no full-year figure)</span>'
    return num(f"hol.world.holiday.{y}", "millions")


def _top_holiday_countries(facts, d, num):
    """The most visited countries in the latest year. Holiday-only figures by country
    start in 2024; before that only visits for any purpose exist, and the text says so."""
    names = d["countries"]["names"]
    hl = top_countries(facts, d, LAST, 3, kind="holiday") if d["countries"].get("holiday", {}).get(LAST) else []
    if len(hl) == 3:
        return (f'In {LAST} the most visited countries for holidays were {esc(names[hl[0]])} ({num(f"hol.cty.{hl[0]}.holiday.{LAST}", "millions")} visits), '
                f'{esc(names[hl[1]])} ({num(f"hol.cty.{hl[1]}.holiday.{LAST}", "millions")}) and {esc(names[hl[2]])} ({num(f"hol.cty.{hl[2]}.holiday.{LAST}", "millions")}).')
    tl = top_countries(facts, d, LAST, 3)
    return (f'In {LAST} the most visited countries were {esc(names[tl[0]])} ({num(f"hol.cty.{tl[0]}.all.{LAST}", "millions")} visits for any purpose), {esc(names[tl[1]])} '
            f'({num(f"hol.cty.{tl[1]}.all.{LAST}", "millions")}) and {esc(names[tl[2]])} ({num(f"hol.cty.{tl[2]}.all.{LAST}", "millions")}); there are no holiday-only figures by country for that year.')


def _holidays(facts, d, num, sources):
    """(answer box, detail parts) for the holidays topic."""
    body = []
    y = LAST
    names = d["countries"]["names"]
    spain_first = all(top_countries(facts, d, y, 1) == ["spain"] for y in d["countries"]["all"])
    # The most visited countries get their own short paragraph near the top, with a link
    # to their section, as readers missed them inside a longer one (audit 11 gap 6).
    answer = (f'''<div class="answer"><p>{headline(facts, num, "holidays", LAST)}</p>
<p>{_top_holiday_countries(facts, d, num)} <a href="#holidays-countries">Top ten</a></p>
<p>In 2019, before the pandemic, UK residents made {num("hol.world.holiday.2019", "millions")} holiday visits abroad (not compared with {LAST}: different residents and survey method). There is no figure for all of 2020, as the survey stopped on 16 March ({num("hol.world.holiday.2020.part", "millions")} by then); in 2021 they made {num("hol.world.holiday.2021", "millions")}.</p>
</div>''')

    body.append(U.topic_line(num, "holidays", LAST))
    body.append('<p>These count trips, not people, so “per 100 residents” is an average, not a typical experience.</p>')
    body.append(series_chart(facts, "Holiday visits abroad", [("Holiday visits abroad", lambda y: f"hol.world.holiday.{y}", "a")],
                             "Millions of visits. Up to 2023 UK residents; from 2024 Great Britain residents, new method. No 2020 figure: the survey stopped on 16 March", breaks=[(YEARS.index(2024), "New method"), (YEARS.index(2025), "Fully new method")], ymin=0, scale=1000, split_breaks=True, kind="millions", num=num,
                             finding=F.trend("Holiday visits abroad by UK residents", which="first",
                                             after="; 2024 and 2025 use a new method and are not compared")))
    body.append(details_table("Show holidays for every year", "Visits abroad, millions",
                              ["Year", "Residents of", "Holiday visits", "Per 100 residents", "Of which to Europe", "To North America", "Share of visits that were holidays"],
                              [[str(y), hol_basis(y), _hol_cell(facts, num, y), num(f"hol.abroad.per100.{y}", "int"), num(f"hol.europe.holiday.{y}", "millions"), num(f"hol.namerica.holiday.{y}", "millions"),
                                num(f"hol.holshare.{y}", "pct") if f"hol.holshare.{y}" in facts else "<span class='missing'>not available</span>"] for y in YEARS]))
    gb_years = [y for y in YEARS if f"hol.gb.holiday.{y}" in facts]
    body.append(details_table("Show holidays within Great Britain for every year", "Overnight holiday trips within Great Britain by Great Britain residents",
                              ["Year", "Survey", "Holiday trips", "Per 100 residents"],
                              [[str(y), gb_survey(y), num(f"hol.gb.holiday.{y}", "millions"), num(f"hol.gb.per100.{y}", "int")] if y in gb_years
                               else [str(y), "", '<span class="missing">not available</span>', ""] for y in YEARS if y >= 2019]))
    body.append('<p class="small">2020 and 2021 have no full-year figures (pandemic). The survey changed method after 2019, so 2019 is not compared with later years. Earlier years used other methods and are not shown.</p>')
    from .pages_life_extra import holiday_afford_block, holiday_spend_block
    body.extend(holiday_spend_block(facts, num, d))
    body.extend(holiday_afford_block(facts, num, d))
    body.append("<h3 id='holidays-countries'>Most visited countries</h3>" + FOLD)
    if spain_first:
        body.append("<p>Counting visits for any purpose (holidays, family visits and business), Spain has been the most visited country in every year with figures by country.</p>")
    body.append(country_table(facts, num, d, LAST, 10))
    cyears = [2009, 2019, LAST]
    top = top_countries(facts, d, LAST, 10)
    body.append(details_table("Show the same countries in 2009 and 2019", "Visits abroad by main country visited (all purposes), millions",
                              ["Country"] + [f"{y} (new method)" if y == LAST and LAST >= 2024 else str(y) for y in cyears],
                              [[esc(names[s])] + [num(f"hol.cty.{s}.all.{y}", "millions") for y in cyears] for s in top]))
    return answer, body

def _infant_limit(facts, num, d):
    """The legal limit on infant classes, near the top of the class sizes page (audit 11 gap 6)."""
    iy = sorted(d["life_extra"]["classes"]["large"]["infant"])[-1]
    return (f'<p>{INFANT_LIMIT} '
            f'In January {iy}, {num(f"school.large.infant.{iy}", "pct")} of infant pupils were in classes of more than 30. '
            f'<a href="#schools-large">Classes of more than 30</a></p>')


def _schools(facts, d, num, sources):
    """(answer box, detail parts) for the schools topic."""
    body = []
    y = LAST
    # England's January census can be a year newer than the explorer's range: show it here
    newer = [y for y in (LAST + 1,) if _val(facts, f"school.primary.{y}") is not None and _val(facts, f"school.secondary.{y}") is not None]
    sy = YEARS + newer
    latest = (f' The January {newer[-1]} census ({newer[-1] - 1}/{str(newer[-1])[2:]} school year) found {num(f"school.primary.{newer[-1]}", "dp1")} and '
              f'{num(f"school.secondary.{newer[-1]}", "dp1")}. It is not on the year pages, which stop at {LAST}, the latest year that most topics have.') if newer else ""
    answer = (f'<div class="answer"><p>{headline(facts, num, "schools", LAST)} In January {FIRST_YEAR["schools"]} the figures were {num(f"school.primary.{FIRST_YEAR['schools']}", "dp1")} and {num(f"school.secondary.{FIRST_YEAR['schools']}", "dp1")}.{latest}</p>'
              f'{_infant_limit(facts, num, d)}</div>')
    body.append(U.topic_line(num, "schools", LAST))
    body.append(line_chart("Average class size in England", [str(y) for y in sy],
                             [(n, [_val(facts, f(y)) for y in sy], st) for n, f, st in (("Primary", lambda y: f"school.primary.{y}", "a"), ("Secondary", lambda y: f"school.secondary.{y}", "b"))],
                             "Pupils per class, January school census, state-funded schools in England", ymin=15, kind="dp1", num=num,
                             ids=[[f(y) for y in sy] for f in (lambda y: f"school.primary.{y}", lambda y: f"school.secondary.{y}")], finding=CLASS_FINDING)
                  if newer else series_chart(facts, "Average class size in England", [("Primary", lambda y: f"school.primary.{y}", "a"), ("Secondary", lambda y: f"school.secondary.{y}", "b")],
                             "Pupils per class, January school census, state-funded schools in England", ymin=15, kind="dp1", num=num, finding=CLASS_FINDING))
    body.append(details_table("Show class sizes for every year", "Average class size, England, January census",
                              ["January census", "School year", "Primary", "Secondary"],
                              [[str(y), f"{y - 1}/{str(y)[2:]}", num(f"school.primary.{y}", "dp1"), num(f"school.secondary.{y}", "dp1")] for y in sy]))
    from .pages_life_extra import class_detail_blocks
    body.extend(class_detail_blocks(facts, num, d))
    wy = [y for y in YEARS if _val(facts, f"school.wales.infant.{y}") is not None]
    wales = table("Average class size, Wales, January census", ["January census", "School year", "Infant classes (reception to year 2)", "Junior classes (years 3 to 6)"],
                  [[str(y), f"{y - 1}/{str(y)[2:]}", num(f"school.wales.infant.{y}", "dp1"), num(f"school.wales.junior.{y}", "dp1")] for y in wy])
    body.extend(schools_nations_block(facts, num, d, wy[-1], wales))
    return answer, body


# key -> (page question, what the topic page covers, one-line hub link text)
TOPIC_PAGES = {
    "work": ("How has work changed?", "employment by sex and age, the kinds of jobs people do, and each nation and region"),
    "earnings": ("How has pay changed after inflation?", "pay for men, women and part-time employees, and each nation and region"),
    "housing": ("How has housing changed?", "who owns and rents, what housing costs, space and overcrowding, regions and nations"),
    "holidays": ("How have holidays changed?", "holidays abroad and at home, what is spent and for how many nights, the countries people visit, and who could afford a week away"),
    "schools": ("How have class sizes changed?", "primary, secondary, infant and key stage 2 classes in England, how many pupils are in classes of more than 30, and figures for Wales and Scotland"),
}
TOPIC_BUILDERS = {"work": _work, "earnings": _earnings, "housing": _housing, "holidays": _holidays, "schools": _schools}
TREND_HEADINGS = {"work": "Employment", "earnings": "Pay after inflation", "housing": "Who owns and who rents",
                  "holidays": "Visits abroad", "schools": "Class sizes in England"}
_SUB_H3 = re.compile(r"<h3 id='([^']+)'>(.*?)</h3>")


def topic_nav(current):
    items = []
    for key, title, _ in TOPICS:
        items.append(f'<li><span aria-current="page">{esc(title)}</span></li>' if key == current else f'<li><a href="{key}.html">{esc(title)}</a></li>')
    return f'<nav aria-label="Topics"><ul class="yearnav">{"".join(items)}</ul></nav>'


def has_year_figure(facts, num, key, y):
    """True when a year has a figure for this topic in the tables a year page uses."""
    from . import pages_history as H
    if y in YEARS:
        return any(_val(facts, m[3](y)) is not None for m in MEAS if m[1] == key)
    return bool(H._topic_rows(facts, num, key, y))


def year_finder(facts, num, key):
    """Find one year's figure from a topic page, without JavaScript (audit 13 gap 3).
    Each year links to that year's page at this topic's section, where the figure is shown
    with its source. A year with no figure for the topic is shown greyed, not linked, so a
    gap is never filled in silently (see has_year_figure). Panels with the figures on this
    page were tried first; they added about 180 KB to the work page, over the reading limit."""
    title = dict((k, t) for k, t, _ in TOPICS)[key]

    def item(y):
        if has_year_figure(facts, num, key, y):
            return f'<li><a href="{y}.html#{key}">{y}</a></li>'
        return f'<li><span class="missing" aria-label="{y}: no figure">{y}</span></li>'
    recent = "".join(item(y) for y in YEARS)
    early = "".join(item(y) for y in EARLY_YEARS)
    return (f'<details class="findyear"><summary>Find one year\'s figure</summary>'
            f'<p class="small">Choose a year to open its page at {esc(title.lower())}, with the figure and its source. '
            f'Years in grey have no figure for {esc(title.lower())} in the tables used here.</p>'
            f'<ul class="yearnav">{recent}</ul>'
            f'<details class="early"><summary>Earlier years, {EARLY_YEARS[0]} to {EARLY_YEARS[-1]} (fewer figures)</summary>'
            f'<ul class="yearnav">{early}</ul></details></details>')


def topic_page(facts, d, num, sources, key):
    """One topic over every year: the answer, its charts and tables, then how it is measured."""
    title = dict((k, t) for k, t, _ in TOPICS)[key]
    question = TOPIC_PAGES[key][0].format(first=FIRST)
    answer, detail = TOPIC_BUILDERS[key](facts, d, num, sources)
    # Sub-sections become sections of their own, so each keeps its answer in view on a phone.
    detail = [_SUB_H3.sub(r"<h2 id='\1'>\2</h2>", part) for part in detail]
    first_chart = next(i for i, part in enumerate(detail) if "data-chart=" in part)
    first = FIRST_YEAR[key]
    # The longest series leads the page, so a reader looking for change since the
    # 1970s or 1980s sees it first (audit 11 gap 3). Its table, limits and sources fold away.
    from . import pages_history
    long_shown, long_folded = pages_history.block(facts, num, sources, key)
    # On work, the "change is not cause" note sits under the answer box, beside the women's
    # and men's rates, instead of with the topic links (audit 11 gap 2, audit 14 gap 1).
    # Then the years since 2008, with more measures. Work, pay, housing and class sizes
    # repeat the long chart's measure over fewer years, so on a phone that chart waits in
    # the fold; holidays shows holiday visits, which the longer series does not have.
    since = FIRST + 1 if key == "holidays" else FIRST  # holiday-only figures start in 2009
    if key == "holidays":
        recent = [FOLD, detail[first_chart]]
    else:
        recent = [f"<p>From {since} the official tables cover more each year: {esc(TOPIC_PAGES[key][1])}.</p>", FOLD,
                  detail[first_chart], "<!--keepfold-->"]
    recent += detail[:first_chart] + detail[first_chart + 1:first_chart + 2]
    rest = detail[first_chart + 2:]
    # On work the note sits straight under the answer, before the long chart, so a phone
    # reader sees it on the first screen (audit 14 gap 1).
    body = [f'<p class="small"><a href="index.html">Everyday life, year by year</a></p>', f'<h1 id="key-answer">{esc(question)}</h1>', answer,
            WORK_CAUSE if key == "work" else "",
            f"<h2 id='trend'>{esc(TREND_HEADINGS[key])} since {first}</h2>", before_toc(topic_nav(key) + f'<p class="more-link"><a href="#years">Pick a year, or compare two years of {esc(title.lower())}</a></p>' + ("" if key == "work" else CAUSE))]
    body.extend(long_shown + [FOLD] + long_folded)
    body.append(f"<h2 id='recent'>Since {since}, in more detail</h2>")
    body.extend(recent + rest)
    body.append("<h2 id='about'>About these figures</h2>")
    # The first sentence of the limits stays in view; the rest folds away with the sources.
    lead, _, more = TOPIC_LIMITS[key].partition(". ")
    body.append(f'<div class="limit"><p>{esc(lead + "." if more else lead)}</p></div>')
    body.append(FOLD)
    if more:
        body.append(f'<div class="limit"><p>{esc(more)}</p></div>')
    body.append(f'<p class="small">{esc(dict((k, sc) for k, _, sc in TOPICS)[key])}</p>')
    body.append(explain.for_topic(key, sources, up="../"))
    body.append(source_line(sources, [s for s in TOPIC_SOURCES[key] if s in sources], up="../"))
    body.append(f"<h2 id='years'>Find or compare years</h2>")
    # The comparison opens at this topic's section. It comes before the year finder, so when the
    # finder's links appear, the numbers a screen-reader or voice-control reader already knows
    # (audit 14 gap 8) stay the same: only the links that follow move on.
    body.append(NOFOLD + compare_form("", anchor=key))
    # One year's figure for this topic, found without JavaScript (audit 13 gap 3).
    body.append(year_finder(facts, num, key))
    return page(f"life/{key}.html", f"{title} since {first}", "\n".join(body),
                f"{title} in the UK every year since {first}, from official statistics: {TOPIC_PAGES[key][1]}.", toc_after_first=True, scripts=COMPARE_JS)


def _hub_holidays(facts, d, num):
    """The holidays answer, shortened for the hub: the latest year only."""
    return f'<div class="answer"><p>{headline(facts, num, "holidays", LAST)}</p></div>'


def _hub_schools(facts, d, num):
    """The class sizes answer, shortened for the hub: the newer January census stays on the topic page."""
    y0 = FIRST_YEAR["schools"]  # the first year of the series, not the explorer's first year (audit 12)
    return (f'<div class="answer"><p>{headline(facts, num, "schools", LAST)} In January {y0}, the first year of this series, the figures were '
            f'{num(f"school.primary.{y0}", "dp1")} and {num(f"school.secondary.{y0}", "dp1")}.</p></div>')


def _hub_earnings(facts, d, num):
    """Before and after pay, without the earlier stretches (those are on the earnings page)."""
    a, b, ch = earn_stretches(facts)[0]
    return (f'<div class="answer">{earn_before_after(num, a, b, ch)}'
            f'<p>Pay of the middle full-time employee, £ a week before tax, UK, in April {LAST} prices (provisional): {_how_short(ch).lower()} '
            f'({change_cell(facts, num, f"earn.real.ft.{a}", f"earn.real.ft.{b}", "pct", "pounds")}). '
            f'The survey changed how it codes jobs in 2011 and 2021, so pay is compared only within each stretch.</p></div>')


# Shorter answers for the hub, where every topic shares one page.
def _hub_work(facts, d, num):
    """The work answer, shortened for the hub: manufacturing's share stays on the topic page."""
    # Kept to two short sentences, so the first chart stays within two phone screens
    # under the questions at the top of the hub.
    y = LAST
    sc = occ_scheme(y)
    shares = {c: facts[f"work.occshare.{sc}.{c}.{y}"].value for c in OCC_NAMES[sc]
              if c != "0" and _val(facts, f"work.occshare.{sc}.{c}.{y}") is not None}
    top = max(shares, key=shares.get)
    return (f'<div class="answer"><p>In April to June {y}, {num(f"work.rate.{y}", "pct")} of people aged 16 to 64 were in work '
            f'(men {num(f"work.men.{y}", "pct")}, women {num(f"work.women.{y}", "pct")}). '
            f'The largest group of jobs in {y} was {esc(OCC_NAMES[sc][top].lower())} ({num(f"work.occshare.{sc}.{top}.{y}", "pct")}).</p></div>')


HUB_ANSWERS = {"holidays": _hub_holidays, "schools": _hub_schools, "earnings": _hub_earnings, "work": _hub_work}


def hub_quick(facts, d, num):
    """Short answers to what readers bring to the hub, at the top (audit 12 gap 2): readers
    missed the infant class limit, the most visited country and the change-is-not-cause
    note when each sat inside its own topic further down a long page."""
    names = d["countries"]["names"]
    firsts = {top_countries(facts, d, y, 1)[0] for y in d["countries"]["all"] if top_countries(facts, d, y, 1)}
    items = ['<strong>Change is not cause:</strong> these figures show what changed, not why.',
             f'<strong>Infant classes in England</strong> are limited by law to 30 pupils, with some exceptions. <a href="schools.html#schools-large">More</a>']
    if len(firsts) == 1:
        c = esc(names[firsts.pop()])
        items.append(f'<strong>Most visited country abroad:</strong> {c}, counting visits for any purpose, in every year with figures by country. <a href="holidays.html#holidays-countries">Top ten</a>')
    lis = "".join(f"<li>{x}</li>" for x in items)
    return f'<div class="answer"><ul class="quick" aria-label="Often asked">{lis}</ul></div>'


def life_index(facts, d, num, sources):
    """A light hub: each topic's answer, a link to its own page, and the year and comparison choosers."""
    body = ["<h1>Everyday life, year by year</h1>"]
    body.append(hub_quick(facts, d, num))
    body.append(jump("Jump to", [(f"#{k}", t) for k, t, _ in TOPICS] + [("#compare", "Compare years")], year_jump("")))
    # Each topic's answer and chart come first, so a chart shows within the
    # first two phone screens; the year and comparison choosers follow.
    for key, title, _ in TOPICS:
        answer, _detail = TOPIC_BUILDERS[key](facts, d, num, sources)
        answer = HUB_ANSWERS[key](facts, d, num) if key in HUB_ANSWERS else answer
        body.append(f"<h2 id='{key}'>{esc(title)}</h2>{NOFOLD}")
        body.append(answer)
        from .pages_history import long_spark
        body.append(long_spark(facts, num, key))
        body.append(f'<p class="more-link"><a href="{key}.html">{esc(title)} in every year since {FIRST_YEAR[key]}</a></p>')
    body.append("<h2 id='compare'>Compare two years</h2>" + compare_form(""))
    body.append('<p class="small">Without JavaScript the button opens a list of every pair of years.</p>')
    a, b = DEFAULT_PAIR
    from .pages_ranges import pair_context
    body.append(f'<p>Start with <a href="compare/{a}-{b}.html">{a} compared with {b}</a>, the earliest and latest years in which all five topics can be compared, '
                f'or <a href="compare/spans/index.html">compare two sets of years</a>.{esc(pair_context(a, b, brief=True))} '
                f'For the years since the pandemic, see <a href="compare/{RECENT}-{LAST}.html">{RECENT} compared with {LAST}</a>, where some topics cannot be compared because surveys changed.</p>')
    body.append(f'<p class="small">All topics but holidays can be compared from {FIRST}. Earlier years, back to 1971, use only the figures measured then: '
                'the employment rate from 1971, visits abroad from 1980, owning and renting in England from 1981, pay from 2002 and class sizes from 2006.</p>')
    body.append(f"<h2 id='years'>Choose a year</h2>{year_links(None, '')}")
    return page("life/index.html", "Everyday life, year by year", "\n".join(body), f"How work, earnings, housing, holidays and class sizes have changed in the UK, year by year from {EARLY_YEARS[0]} to {LAST}.", scripts=COMPARE_JS + YEAR_JS, contents=False)


def work_ages_block(facts, num):
    out = ["<h3 id='work-age'>By age</h3>"]
    young, old = f"work.age.18_24.{LAST}", f"work.age.50_64.{LAST}"
    out.append(f'<div class="answer"><p>In April to June {LAST}, {num(f"work.age.25_34.{LAST}", "pct")} of people aged 25 to 34 and {num(f"work.age.35_49.{LAST}", "pct")} of those aged 35 to 49 were in work. '
               f'The rate was lower for 18 to 24 year olds ({num(young, "pct")}), many of whom are studying, and for 50 to 64 year olds ({num(old, "pct")}). '
               f'{num(f"work.age.65.{LAST}", "pct")} of people aged 65 and over were in work, compared with {num(f"work.age.65.{FIRST}", "pct")} in {FIRST}.</p></div>')
    out.append(groups_chart(facts, "Employment rate by age group", [(lab, (lambda k: lambda y: f"work.age.{k}.{y}")(k)) for k, lab, _ in AGE_SERIES],
                            "Per cent of each age group in work, April to June each year, United Kingdom", ymin=0, kind="pct", num=num,
                            finding=F.count("The employment rate", "age groups")))
    out.append(details_table("Show employment by age for every year", "Employment rate by age group, United Kingdom, April to June, %",
                             ["Year"] + [lab for _, lab, _ in AGE_SERIES],
                             [[str(y)] + [num(f"work.age.{k}.{y}", "pct") for k, _, _ in AGE_SERIES] for y in YEARS]))
    out.append('<p class="small">The rate for each age group is the share of everyone in that group who did any paid work in the survey week, including students with part-time jobs.</p>')
    return out


def places_block(facts, num, topic):
    """A nation-and-region table: first year, latest year and change, plus every year on request."""
    if topic == "work":
        fid, kind, style = (lambda k, y: f"work.place.{k}.{y}"), "pct", "pp"
        title, what = "By nation and region", "Employment rate, ages 16 to 64, January to December, %"
    else:
        fid, kind, style = (lambda k, y: f"earn.place.real.{k}.{y}"), "pounds", "pct"
        title, what = "By nation and region", "Median weekly pay of full-time employees, by where they live, April each year, in April 2025 prices"
    places = [(k, n) for k, n in NATIONS] + [(k, n) for k, n, _ in REGIONS]
    subject = "The employment rate" if topic == "work" else "After inflation, median full-time pay"
    ys = [y for y in YEARS if _val(facts, fid("uk", y)) is not None]
    a, b = ys[0], ys[-1]
    brk, prev = {}, None
    if topic == "earnings":
        # Pay is compared only within one job-coding period (see earn_basis).
        runs = same_basis_runs(facts, lambda y: fid("uk", y), ys, earn_basis)
        (a, b), prev = runs[-1], runs[-2]
        brk = dict(breaks=[(ys.index(y), "Jobs recoded") for y in EARN_BREAKS if y in ys[1:]], split_breaks=True)
    out = [f"<h3 id='{topic}-places'>{title}</h3>"]
    vals = {k: _val(facts, fid(k, b)) for k, _ in NATIONS[1:]}
    hi, lo = max(vals, key=vals.get), min(vals, key=vals.get)
    names = dict(NATIONS)
    rnames = {k: n for k, n, _ in REGIONS}
    rv = {k: _val(facts, fid(k, b)) for k in rnames}
    rtop, rlo = max(rv, key=rv.get), min(rv, key=rv.get)
    if topic == "work":
        out.append(f'<div class="answer"><p>In {b}, the employment rate was highest in {names[hi]} ({num(fid(hi, b), kind)}) and lowest in {names[lo]} ({num(fid(lo, b), kind)}). '
                   f'Every nation had a higher rate than in {a}.</p></div>' if all(_val(facts, fid(k, b)) > _val(facts, fid(k, a)) for k in vals) else
                   f'<div class="answer"><p>In {b}, the employment rate was highest in {names[hi]} ({num(fid(hi, b), kind)}) and lowest in {names[lo]} ({num(fid(lo, b), kind)}).</p></div>')
    else:
        out.append(f'<div class="answer"><p>In April {b}, full-time employees living in {names[hi]} had the highest median pay of the four nations ({num(fid(hi, b), kind)} a week) '
                   f'and those in {names[lo]} the lowest ({num(fid(lo, b), kind)}). Within England, pay was highest for people living in {rnames[rtop]} ({num(fid(rtop, b), kind)}) and lowest in {rnames[rlo]} ({num(fid(rlo, b), kind)}). '
                   f'Pay does not show what money buys: prices, especially housing costs, differ between places.</p></div>')
    rows = []
    for k, n in places:
        mk = "pm_pp" if kind == "pct" else "pm_pounds"
        moe = num(U.MARGINS[fid(k, b)][0], mk) if U.has(fid(k, b)) else '<span class="missing">not published</span>'
        row = [esc(n), num(fid(k, a), kind), num(fid(k, b), kind), moe, change_cell(facts, num, fid(k, a), fid(k, b), style, kind)]
        if prev:
            row.append(change_cell(facts, num, fid(k, prev[0]), fid(k, prev[1]), style, kind))
        rows.append(row)
    out.append(groups_chart(facts, f"{what.split(',')[0]}: the four nations", [(n, (lambda k: lambda y: fid(k, y))(k)) for k, n in NATIONS[1:]],
                            what, years=ys, kind=kind, num=num, summary_note=f"One panel for each place, on the same scale. The table below gives every place's figures for {a} and {b}, with margins of error, and the full table gives every year.",
                            finding=F.count(subject, "nations"), **brk))
    out.append(groups_chart(facts, f"{what.split(',')[0]}: regions of England", [(n, (lambda k: lambda y: fid(k, y))(k)) for k, n, _ in REGIONS],
                            what, years=ys, kind=kind, num=num, summary_note=f"One panel for each place, on the same scale. The table below gives every place's figures for {a} and {b}, with margins of error, and the full table gives every year.",
                            finding=F.count(subject, "regions"), **brk))
    head = ["Place", str(a), str(b), f"Margin of error, {b}", f"Change, {a} to {b}" if prev else "Change"]
    if prev:
        head.append(f"Change, {prev[0]} to {prev[1]}")
    out.append(table(f"{what}: {a} and {b}", head, rows))
    if prev:
        out.append(f'<p class="small">Pay is compared only between years when the survey coded jobs the same way: {a} to {b}, and separately {prev[0]} to {prev[1]}. It is not compared across the coding changes in 2011 and 2021.</p>')
    out.append(f'<p class="small">The margin of error is the 95% range published by ONS for the {b} figure. Smaller places have smaller samples and wider margins, so a difference between two places that is smaller than their margins could be sampling noise. {U.how_sure_link("../")}</p>')
    out.append(details_table(f"Show every year by nation and region", what, ["Year"] + [esc(n) for _, n in places],
                             [[str(y)] + [num(fid(k, y), kind) for k, _ in places] for y in ys]))
    out.append('<p class="small">The nine English regions together make up England.</p>')
    # The answer names the highest and lowest places; the panels wait in the fold on a phone.
    out.append("<!--keepfold-->")
    return out


PLACES_PAGE = "life/housing-places.html"


def _places_answer(facts, num, d):
    ys = [y for y in YEARS if _val(facts, f"house.reg.private.england.{y}") is not None]
    b = ys[-1]
    pr = {k: _val(facts, f"house.reg.private.{k}.{b}") for k, _, _ in REGIONS}
    top, low = max(pr, key=pr.get), min(pr, key=pr.get)
    names = {k: n for k, n, _ in REGIONS}
    n = d["nations"]
    nb = min(ys[-1], n["wales"][-1], n["scotland"][-1])
    return (f'<div class="answer"><p>At 31 March {b}, {num(f"house.reg.private.england.{b}", "pct0")} of homes in England were rented privately: '
            f'from {num(f"house.reg.private.{low}.{b}", "pct0")} ({names[low]}) to {num(f"house.reg.private.{top}.{b}", "pct0")} ({names[top]}). '
            f'In {nb} it was {num(f"house.nat.private.wales.{nb}", "pct0")} in Wales and {num(f"house.nat.private.scotland.{nb}", "pct0")} in Scotland, where homes that come with a job or business are counted with private renting. '
            f'Each nation measures housing its own way, so small gaps between nations should not be read as real differences.</p></div>')


def housing_places_block(facts, num, d):
    """The short version on the housing page: the answer and a link to the regions and nations page."""
    return ["<h3 id='housing-places'>Each region and nation</h3>", NOFOLD, _places_answer(facts, num, d),
            '<p class="more-link"><a href="housing-places.html">Homes by tenure in each region and nation</a>, with a chart of every English region.</p>']


def places_page(facts, d, num, sources):
    """A page of its own, so the housing page stays short on a phone."""
    body = ['<p class="small"><a href="index.html">Everyday life, year by year</a> › <a href="housing.html">Housing</a></p>',
            "<h1>Who owns and who rents in each region and nation?</h1>", _places_answer(facts, num, d), topic_nav("housing"), CAUSE]
    parts = housing_regions_block(facts, num) + housing_nations_block(facts, num, d)
    body.extend(_SUB_H3.sub(r"<h2 id='\1'>\2</h2>", part) for part in parts)
    body.append("<h2 id='about'>About these figures</h2>")
    body.append('<div class="limit"><p>Housing is run separately in each nation, and each counts homes in its own way, so figures for different nations are shown side by side '
                'but never added into a UK total. These are counts of homes (dwellings), except Northern Ireland, which publishes a survey of households.</p></div>')
    body.append(FOLD)
    body.append(source_line(sources, [s for s in ("dluhc-lt109", "wales-dwelling-stock", "scot-stock-by-tenure", "ni-housing-2025-26") if s in sources], up="../"))
    return page(PLACES_PAGE, "Housing in each region and nation", "\n".join(body),
                "Homes owned and rented in each region of England and in Wales, Scotland and Northern Ireland, from official housing statistics.")


def housing_regions_block(facts, num):
    ys = [y for y in YEARS if _val(facts, f"house.reg.owner.england.{y}") is not None]
    a, b = ys[0], ys[-1]
    places = [("england", "England")] + [(k, n) for k, n, _ in REGIONS]
    out = ["<h3 id='housing-regions'>Homes by tenure in each region</h3>"]
    pr = {k: _val(facts, f"house.reg.private.{k}.{b}") for k, _, _ in REGIONS}
    top = max(pr, key=pr.get)
    names = {k: n for k, n, _ in REGIONS}
    out.append(f'<div class="answer"><p>These figures count homes (dwellings), not households, so they differ a little from the survey figures on the <a href="housing.html">housing page</a>. '
               f'At 31 March {b}, {num(f"house.reg.private.england.{b}", "pct0")} of homes in England were rented privately, up from {num(f"house.reg.private.england.{a}", "pct0")} in {a}. '
               f'The share was highest in {names[top]} ({num(f"house.reg.private.{top}.{b}", "pct0")}), where {num(f"house.reg.owner.{top}.{b}", "pct0")} of homes were owner occupied.</p></div>')
    rows = []
    for k, n in places:
        rows.append([esc(n)] + [num(f"house.reg.{t}.{k}.{y}", "pct") for t in ("owner", "private", "social") for y in (a, b)])
    out.append(table(f"Homes by tenure, England and its regions, 31 March {a} and {b}, % of homes",
                     ["Place", f"Owner occupied {a}", f"Owner occupied {b}", f"Private rent {a}", f"Private rent {b}", f"Social rent {a}", f"Social rent {b}"], rows))
    out.append(groups_chart(facts, "Homes rented privately in each region of England", [("All of England" if k == "england" else n, (lambda k: lambda y: f"house.reg.private.{k}.{y}")(k)) for k, n in places],
                            "Per cent of homes rented privately, 31 March each year", years=ys, ymin=0, kind="pct", num=num,
                            finding=F.count("The share of homes rented privately", "areas shown"),
                            summary_note=f"One panel for each place, on the same scale. The table above gives every region's figures for {a} and {b}, and the table below gives every year."))
    out.append(details_table("Show private renting by region for every year", "Homes rented privately, % of homes, 31 March each year",
                             ["Year"] + [esc(n) for _, n in places], [[str(y)] + [num(f"house.reg.private.{k}.{y}", "pct") for k, _ in places] for y in ys]))
    out.append(f'<p class="small">Social rent adds homes rented from councils and from housing associations (our calculation). Owner occupied includes shared ownership. '
               f'Private renting is estimated from the Labour Force Survey and smoothed; figures from 2024 are provisional. Wales, Scotland and Northern Ireland are shown below.</p>')
    return out


def housing_costs_block(facts, num, d):
    base = d["housing_costs"]["base"]
    b = sy(base)
    ys = [y for y in YEARS if f"house.rent.private.{y}" in facts]
    out = ["<h3 id='housing-costs'>What housing costs</h3>"]
    out.append(f'<div class="answer"><p>In {b}, households renting privately in England paid {num(f"house.rent.private.{base}", "pounds")} a week on average, '
               f'social renters {num(f"house.rent.social.{base}", "pounds")} and households with a mortgage {num(f"house.mortpay.{base}", "pounds")} '
               f'After inflation, in {b} prices, the {sy(FIRST)} figures were {num(f"house.real.rent.private.{FIRST}", "pounds")}, '
               f'{num(f"house.real.rent.social.{FIRST}", "pounds")} and {num(f"house.real.mortpay.{FIRST}", "pounds")}.</p></div>')
    out.append(series_chart(facts, "Average weekly housing costs in England, after inflation",
                            [("Private rent", lambda y: f"house.real.rent.private.{y}", "a"), ("Mortgage payment", lambda y: f"house.real.mortpay.{y}", "b"),
                             ("Social rent", lambda y: f"house.real.rent.social.{y}", "c")],
                            f"£ a week (mean), survey year starting in the year shown, in {b} prices (CPIH)", ymin=0, kind="pounds", num=num, point_label=sy,
                            finding=F.pair("After inflation, average private rent", "the average mortgage payment")))
    out.append(details_table("Show housing costs for every year", f"Average (mean) weekly rent before housing support and mortgage payment, England",
                             ["Survey year", "Private rent (cash)", f"Private rent ({b} prices)", "Social rent (cash)", f"Social rent ({b} prices)",
                              "Mortgage (cash)", f"Mortgage ({b} prices)"],
                             [[sy(y), num(f"house.rent.private.{y}", "pounds"), num(f"house.real.rent.private.{y}", "pounds"), num(f"house.rent.social.{y}", "pounds"),
                               num(f"house.real.rent.social.{y}", "pounds"), num(f"house.mortpay.{y}", "pounds"), num(f"house.real.mortpay.{y}", "pounds")] for y in ys]
                             + [[sy(y), "<span class='missing'>not yet published</span>", "", "", "", "", ""] for y in YEARS if y not in ys]))
    return out


def housing_space_block(facts, num):
    cy = [y for y in YEARS if f"house.crowd.all.{y}" in facts]
    last = cy[-1]
    out = ["<h3 id='housing-space'>Space and overcrowding</h3>"]
    out.append(f'<div class="answer"><p>Over the three survey years {sy(last - 2)} to {sy(last)}, {num(f"house.crowd.all.{last}", "pct")} of households in England were overcrowded: '
               f'{num(f"house.crowd.social.{last}", "pct")} of social renters, {num(f"house.crowd.private.{last}", "pct")} of private renters and '
               f'{num(f"house.crowd.owners.{last}", "pct")} of owner occupiers, against {num(f"house.crowd.social.{FIRST}", "pct")}, {num(f"house.crowd.private.{FIRST}", "pct")} '
               f'and {num(f"house.crowd.owners.{FIRST}", "pct")} for {sy(FIRST - 2)} to {sy(FIRST)}.</p></div>')
    out.append(series_chart(facts, "Overcrowded households in England, by tenure",
                            [("Social renters", lambda y: f"house.crowd.social.{y}", "a"), ("Private renters", lambda y: f"house.crowd.private.{y}", "b"),
                             ("Owner occupiers", lambda y: f"house.crowd.owners.{y}", "c")],
                            "Per cent of households below the bedroom standard, three-year average ending in the survey year shown", ymin=0, kind="pct", num=num, point_label=sy,
                            finding=F.leader("{name} were the most likely to be overcrowded {span}")))
    out.append(details_table("Show overcrowding for every year", "Overcrowded households, England, % (three-year averages, bedroom standard)",
                             ["Three survey years", "All households", "Owner occupiers", "Social renters", "Private renters"],
                             [[f"{sy(y - 2)} to {sy(y)}", num(f"house.crowd.all.{y}", "pct"), num(f"house.crowd.owners.{y}", "pct"), num(f"house.crowd.social.{y}", "pct"),
                               num(f"house.crowd.private.{y}", "pct")] for y in cy]
                             + [[f"{sy(y - 2)} to {sy(y)}", "<span class='missing'>not yet published</span>", "", "", ""] for y in YEARS if y not in cy]))
    ry = [y for y in YEARS if f"house.rooms5.{y}" in facts]
    rows = []
    for y in ry:
        rows.append([f"{sy(y)} ({rooms_basis(y)})"] + [num(f"house.rooms.{k}.{y}", "pct") for k in ("r12", "r3", "r4", "r5", "r6", "r7", "r8")] + [num(f"house.rooms5.{y}", "pct")])
    out.append(details_table("Show number of rooms for every year", "Households by number of rooms, England, % of all households",
                             ["Survey year", "1 or 2", "3", "4", "5", "6", "7", "8 or more", "5 or more"], rows))
    out.append('<p class="small">Room counts before and after 2011-12 are not comparable: from 2011-12 utility rooms were no longer counted.</p>')
    # The answer gives each group's figures; the chart waits in the fold on a phone.
    out.append("<!--keepfold-->")
    return out


MEAS = []
OCC_NAMES = {}


def init(d):
    OCC_NAMES.clear()
    OCC_NAMES.update(d["work"]["occ_groups"])
    MEAS.clear()
    MEAS.extend(measures(d))
