"""Everyday life, year by year: an overview, one page per year and a page for
every pair of years.

Years are calendar labels, but each topic is measured over its own period
(for example April to June, the April survey date, a survey year running into
the next calendar year, or a January school census). Every value is shown with
its own period. Missing years stay missing, and comparisons across a change of
definition are not calculated.
"""
from .data import YEARS, NATIONS, REGIONS, AGE_SERIES
from . import explain
from .html import page, table, details_table, line_chart, source_line, fmt, esc
from . import uncertainty as U

FIRST, LAST = YEARS[0], YEARS[-1]


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
    return "UK" if y <= 2023 else "GB"


def gb_survey(y):
    return "earlier survey" if y <= 2019 else "current survey"


# Each measure: key, topic, label, fact-id function, display kind, change style ('pp', 'pct' or None),
# period function, comparability-group function (None = one consistent series)
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
    for key, label, _ in AGE_SERIES:
        m.append((f"work.age.{key}", "work", f"Employment rate, ages {label}", (lambda k: lambda y: f"work.age.{k}.{y}")(key), "pct", "pp", lambda y: f"Apr–Jun {y}", None))
    for key, name in NATIONS[1:]:
        m.append((f"work.place.{key}", "work", f"Employment rate 16 to 64: {name}", (lambda k: lambda y: f"work.place.{k}.{y}")(key), "pct", "pp", lambda y: f"Jan–Dec {y}", None))
    for k in ("prof", "managers", "admin", "skilled", "caring", "elem"):
        code = occ_codes[k]
        m.append((f"work.occ.{k}", "work", f"Share of workers in: {occ_names[k]}", (lambda c: lambda y: f"work.occshare.{occ_scheme(y)}.{c}.{y}")(code), "pct", "pp",
                  lambda y: f"Jan–Dec {y}", occ_scheme))
    m += [
        ("earn.ft", "earnings", "Median weekly pay, full-time employees (April 2025 prices)", lambda y: f"earn.real.ft.{y}", "pounds", "pct", lambda y: f"April {y}", None),
        ("earn.ftcash", "earnings", "Median weekly pay, full-time employees (cash, at the time)", lambda y: f"earn.ft.{y}", "pounds", "pct", lambda y: f"April {y}", None),
        ("earn.men", "earnings", "Full-time men (April 2025 prices)", lambda y: f"earn.real.ft_men.{y}", "pounds", "pct", lambda y: f"April {y}", None),
        ("earn.women", "earnings", "Full-time women (April 2025 prices)", lambda y: f"earn.real.ft_women.{y}", "pounds", "pct", lambda y: f"April {y}", None),
        ("earn.pt", "earnings", "Part-time employees (April 2025 prices)", lambda y: f"earn.real.pt.{y}", "pounds", "pct", lambda y: f"April {y}", None),
    ]
    for key, name in NATIONS[1:]:
        m.append((f"earn.place.{key}", "earnings", f"Full-time, living in {name} (April 2025 prices)", (lambda k: lambda y: f"earn.place.real.{k}.{y}")(key), "pounds", "pct", lambda y: f"April {y}", None))
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
    ]
    return m


TOPICS = [
    ("work", "Work", "United Kingdom. Employment rates for the UK, by sex and by age, and the part-time share: Labour Force Survey, April to June. Employment rates for each nation and English region, and job types: Annual Population Survey, January to December."),
    ("earnings", "Earnings", "United Kingdom, and each nation by where employees live. Median (middle) gross weekly pay before tax, from the Annual Survey of Hours and Earnings in April each year. Adjusted to April 2025 prices with the UK-wide CPIH inflation index."),
    ("housing", "Housing", "England only. English Housing Survey. A survey year runs from April to March, so “2015” means the 2015-16 survey. Rents are averages for households paying rent, before any housing support (such as Housing Benefit). Mortgage payments are averages for households buying with a mortgage. “After inflation” figures use the CPIH price index averaged over each survey year. Overcrowding uses the bedroom standard and is an average of three survey years."),
    ("holidays", "Holidays", "Trips abroad, by year of travel: up to 2023 UK residents (International Passenger Survey); from 2024 Great Britain residents, measured with a new method. Holidays at home: overnight trips within Great Britain by Great Britain residents whose main purpose was a holiday (Great Britain Tourism Survey); Northern Ireland is not covered. Every traveller, adult or child, counts as one trip. “Per 100 residents” divides trips by the mid-year population."),
    ("schools", "Class sizes", "Primary and secondary figures: England only. State-funded schools, classes taught by one teacher, at the January school census. Wales: infant and junior classes in maintained schools at the January school census, from 2023. “2015” means January 2015, in the 2014/15 school year."),
]

TOPIC_SOURCES = {
    "work": ["ons-lf24", "ons-mgsv", "ons-lf25", "ons-mgrz", "ons-ycbe", "ons-ycbh", "ons-ybud", "ons-ybug", "ons-ybuj", "ons-lf2u", "ons-lfk6", "nomis-aps-emp-places", "aps2010", "aps2020"],
    "earnings": ["nomis-ashe-resident", "nomis-ashe-places", "ons-l522"],
    "housing": ["ehs-ft1101", "ehs-ft1241", "ehs-fa3201", "ehs-fa2501", "ehs-fa2555", "ons-l522", "ehs-ft1421", "ehs-fa1422", "ehs-fa1401", "dluhc-lt109"],
    "holidays": ["ott-2009to2019", "ott-2019to2023", "ott-2024", "ott-2025", "gbts-2019-gb-summary", "gbts-2022to2023-tables", "gbts-2024-q4-annual-tables", "gbts-2025-toplines", "ons-ukpop", "ons-gbpop"],
    "schools": ["dfe-spc-2015-tables", "dfe_api", "wg-schools-census-2025"],
}

TOPIC_LIMITS = {
    "work": "Job types use the Standard Occupational Classification. It changed from SOC2010 to SOC2020 in 2021, so shares before and after 2021 are not compared here; 2021 is shown on both bases. Job-type figures start in 2011 in these tables. Labour Force Survey response rates fell sharply from 2020, which makes recent estimates less certain. Figures for each nation and region come from the Annual Population Survey, a larger survey over a whole calendar year, so they do not exactly match the UK figures for April to June. Wales and Northern Ireland have smaller samples, so year-to-year moves of a point or two there may be sampling noise. Ages 65 and over are not included in the 16 to 64 rates.",
    "earnings": "Half of full-time employees earn more than the median and half earn less. Figures exclude the self-employed. ASHE has small breaks in 2011 and 2021, when the coding of jobs changed, and 2020 and 2021 were affected by furlough. 2025 figures are provisional. Figures for each nation are for employees who live there, wherever they work. The same UK-wide price index is used for every nation, because official inflation figures are not published for each nation; prices and living costs differ between places, so a higher wage in one place does not mean people there are better off.",
    "housing": "Housing is run separately in each nation, and Wales, Scotland and Northern Ireland measure it with their own surveys, which use different questions and years, so this section covers England. The survey covers households in self-contained homes in England, not people in care homes or student halls. Figures for 2025-26 are not yet published. Families with children: our calculation adds three published groups (couples, single lone parents and previously married lone parents). Rents and mortgage payments are averages (means), so a few very high payments pull them up; they are not what a particular household pays, and mortgage payments depend on when the home was bought. A household is overcrowded under the bedroom standard if it has fewer bedrooms than the standard says its members need (one for each couple, one for each other person aged 21 or over, one for each pair of young people aged 10 to 20 of the same sex, and one for each pair of children under 10). Overcrowding figures are three-year averages, so neighbouring years share data; the latest published average ends in 2022-23. Rooms: the way rooms are counted changed in 2011-12 (utility rooms stopped being counted), so room figures are not compared across that change. Because of the pandemic, the 2020-21 survey interviewed people by phone instead of face to face, and its sample had more older people and owners and fewer renters and families with children. The publisher says these effects cannot be fully separated from real change, so figures that include 2020-21 are less certain.",
    "holidays": "Figures for 2008 are not in the tables used here. In 2020 and 2021 travel was restricted by the pandemic and the survey was paused from March 2020, so 2020 figures are partial and have no breakdown by destination. From 2024 the figures cover Great Britain residents with a new method, so they are not compared with earlier years. Holidays within Great Britain come from a survey that changed method after 2019 and has no full-year figures for 2020 and 2021, so only 2022 onwards are compared with each other; 2019 is shown on its own. Trips per 100 residents is an average across everyone, including children and people who took no holiday: it does not say how many people went away, because these surveys count trips, not travellers. Countries are ranked by all visits (holidays, family visits and business together) because holiday-only figures by country start in 2024.",
    "schools": "Education is run separately in each nation, and each counts classes in its own way, so figures for different nations are shown side by side but not compared. Wales reports infant classes (reception to year 2) and junior classes (years 3 to 6) rather than one primary figure, and the tables used here start in January 2023. Scotland (which counts classes at a September census) and Northern Ireland are not shown yet, because their figures are not in the tables used here. Average class size is not the same as the number of pupils per teacher. January 2008 to 2015 come from the DfE's 2015 national tables and January 2016 onwards from the DfE's current data; both use the same definition (classes taught by one teacher in state-funded schools).",
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
    out = []
    for y in YEARS:
        if y == current:
            out.append(f'<li><span aria-current="page">{y}</span></li>')
        else:
            out.append(f'<li><a href="{up}{href(y)}">{y}</a></li>')
    return f'<ul class="yearnav{" yearstrip" if strip else ""}">{"".join(out)}</ul>'


def compare_form(up, a=None, b=None):
    def opts(sel):
        return "".join(f'<option value="{y}"{" selected" if y == sel else ""}>{y}</option>' for y in YEARS)
    return f'''<form class="pick" action="{up}compare/index.html" method="get" data-compare>
<label>First year <select name="from">{opts(a or 2010)}</select></label>
<label>Second year <select name="to">{opts(b or LAST)}</select></label>
<button type="submit">Compare</button></form>'''


COMPARE_JS = """<script>
document.querySelectorAll('form[data-compare]').forEach(function(f){f.addEventListener('submit',function(e){
var a=+f.elements.from.value,b=+f.elements.to.value;e.preventDefault();var base=f.getAttribute('action').replace(/index\\.html$/,'');
if(a===b){location.href=base+'../'+a+'.html';return;}
var lo=Math.min(a,b),hi=Math.max(a,b);location.href=base+lo+'-'+hi+'.html';});});
(function(){var p=new URLSearchParams(location.search),a=+p.get('from'),b=+p.get('to');
if(a&&b&&document.body.hasAttribute('data-compare-index')){if(a===b){location.replace('../'+a+'.html');}else{location.replace(Math.min(a,b)+'-'+Math.max(a,b)+'.html');}}})();
</script>"""

CAUSE = '<p class="note"><strong>Change is not cause.</strong> These figures show what changed between years. They do not show why. Many things happen at once, including changes in the economy, prices, population and government policy, and these statistics cannot separate them.</p>'


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
            s.append(f"The largest group of jobs was {esc(OCC_NAMES[sc][top].lower())}: {num(f'work.occshare.{sc}.{top}.{y}', 'pct')} of workers.")
        else:
            s.append(f"Job-type figures for {y} are not in the tables used here (they start in 2011).")
        return " ".join(s)
    if topic == "earnings":
        if not has(f"earn.real.ft.{y}"):
            return f"No earnings figure for {y}."
        return (f"In April {y}, the middle full-time employee earned {num(f'earn.ft.{y}', 'pounds')} a week before tax. "
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
        return s
    return ""


def year_page(facts, d, num, sources, y):
    up = "../"
    body = [f"<h1>Everyday life in {y}</h1>"]
    prev_l = f'<a href="{y - 1}.html">← {y - 1}</a>' if y > FIRST else "<span></span>"
    next_l = f'<a href="{y + 1}.html">{y + 1} →</a>' if y < LAST else "<span></span>"
    body.append(f'<nav class="pager" aria-label="Previous and next year">{prev_l}{next_l}</nav>')
    body.append(f'<nav aria-label="Choose a year">{year_links(y, "", strip=True)}</nav>')
    body.append(f'<p>Each topic is measured over its own period, shown beside every figure. To see how {y} differs from another year, <a href="#compare">compare two years</a>.</p>')
    for key, title, scope in TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        body.append(f'<div class="answer"><p>{headline(facts, num, key, y)}</p></div>')
        body.append(topic_block_for_year(facts, num, sources, key, y, up))
        if any(U.has(m[3](y)) for m in MEAS if m[1] == key):
            body.append(f'<p class="small">± is the 95% margin of error, shown where the publisher gives one. {U.how_sure_link("../")}</p>')
        if key == "work" and 2011 <= y:
            body.append(occupation_table(facts, num, d, y))
        if key == "holidays":
            body.append(holiday_regions(facts, num, y))
            body.append(country_table(facts, num, d, y, 10))
        body.append(explain.for_year(key, y, sources, up=up))
        body.append(f'<p class="small">{esc(scope)}</p>')
        body.append(source_line(sources, [s for s in TOPIC_SOURCES[key] if s in sources], up=up))
    body.append(f'<h2 id="compare">Compare {y} with another year</h2>')
    links = []
    for o in YEARS:
        if o != y:
            a, b = min(o, y), max(o, y)
            links.append(f'<li><a href="compare/{a}-{b}.html">{o}</a></li>')
    body.append(f'<ul class="yearnav">{"".join(links)}</ul>')
    body.append(CAUSE)
    return page(f"life/{y}.html", f"Everyday life in {y}", "\n".join(body), f"Work, earnings, housing, holidays and class sizes in the UK in {y}, from official statistics.")


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
    rooms_basis: "Rooms were counted differently from 2011-12, when utility rooms stopped being counted.",
    hol_basis: "Up to 2023 the survey counted UK residents; from 2024 it counts Great Britain residents with a new method.",
    gb_survey: "The Great Britain Tourism Survey changed its method after 2019, so 2019 is not compared with later years.",
}


def missing_reason(mkey, y):
    """Why a measure has no figure for year y, in plain words."""
    if mkey.startswith("work.occ.") and y < 2011:
        return "job-type figures in these tables start in 2011"
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
    if mkey == "hol.europe" and y == 2020:
        return "the survey was paused for most of 2020, so there is no breakdown by destination"
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
                + _pair_bars(facts, num, m, a, b) + U.check_sentence(facts, num, fa, fb, m[5], (str(a), str(b))))
    near = _nearest_pair(facts, m, a, b)
    link = f' The nearest pair of years with comparable figures is <a href="{near[0]}-{near[1]}.html">{near[0]} and {near[1]}</a>.' if near else ""
    if st == "break":
        return (f"<p>{esc(subject)}: {num(fa, m[4])} in {esc(m[6](a))} and {num(fb, m[4])} in {esc(m[6](b))}, "
                f"but these are <strong>not compared</strong>. {esc(BREAK_REASONS[m[7]])}{link}</p>")
    missing = [y for y in (a, b) if _val(facts, m[3](y)) is None]
    y = missing[0]
    return f"<p>{esc(subject)}: <strong>not compared</strong>, because {esc(missing_reason(mkey, y))}.{link}</p>"


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
    body.append(compare_form("../", a, b))
    # Summary: the same lead measure for every topic, then the biggest changes by a fixed rule.
    body.append('<h2 id="summary">In brief</h2>')
    body.append('<p class="small">The same lead figure is shown for each topic on every comparison page, whichever way it moved. Each figure covers its own period, shown in brackets.</p>')
    for key, title, _ in TOPICS:
        body.append(f'<div class="cmp-key"><h3>{esc(title)}</h3>{key_sentence(facts, num, key, a, b)}</div>')
    top = largest_changes(facts, num, a, b)
    if top:
        body.append(f'<h2 id="largest">Largest changes between {a} and {b}</h2>')
        body.append('<p class="small">Every figure on this page that can be compared, ranked by the size of its change. Shares and amounts are ranked separately, because percentage points and per cent are different measures. Cash figures are left out, because the after-inflation figures are the like-for-like ones.</p>')
        body.append(top)
    body.append(CAUSE)
    for key, title, scope in TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        body.append(f'<p class="small">{esc(scope)}</p>')
        ms = [m for m in MEAS if m[1] == key]
        ok = [m for m in ms if _status(facts, m, a, b) == "ok" and not m[0].endswith("cash")]
        breaks = [m for m in ms if _status(facts, m, a, b) == "break"]
        missing = [m for m in ms if _status(facts, m, a, b) == "missing"]
        if ok:
            body.append(f'<ul class="cmp-list">{"".join(_row_card(facts, num, m, a, b) for m in ok)}</ul>')
        if any(m[0].endswith("cash") and _status(facts, m, a, b) == "ok" for m in ms):
            body.append('<p class="small">Amounts above are after inflation. Cash amounts, as paid at the time, are in the full table below.</p>')
        if breaks:
            reasons = {}
            for m in breaks:
                reasons.setdefault(BREAK_REASONS[m[7]], []).append(m)
            items = []
            for reason, group in reasons.items():
                vals = "".join(f"<li>{esc(m[2])}: {num(m[3](a), m[4])} in {a}, {num(m[3](b), m[4])} in {b}</li>" for m in group)
                items.append(f"<li><p>{esc(reason)}</p><p class=\"small\">Shown side by side, not compared:</p><ul class=\"small cmp-vals\">{vals}</ul></li>")
            body.append(f'<h3>Not compared: the definition changed</h3><ul class="cmp-notes">{"".join(items)}</ul>')
        if missing:
            reasons = {}
            for m in missing:
                for y in (a, b):
                    if _val(facts, m[3](y)) is None:
                        reasons.setdefault((y, missing_reason(m[0], y)), []).append(m)
                        break
            items = []
            for (y, reason), group in reasons.items():
                near = _nearest_pair(facts, group[0], a, b)
                link = f' Nearest comparable pair: <a href="{near[0]}-{near[1]}.html">{near[0]} and {near[1]}</a>.' if near else ""
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
                    body.append(f'<p class="small">{a} counts UK residents and {b} Great Britain residents measured with a new method, so the numbers are listed side by side but not compared.</p>')
        body.append(f'<details class="limit"><summary>Limits of the {esc(title.lower())} figures</summary><p>{esc(TOPIC_LIMITS[key])}</p></details>')
        body.append(source_line(sources, [s for s in TOPIC_SOURCES[key] if s in sources], up="../../"))
    body.append('<p class="small">Changes in percentages are shown in percentage points: a rise from 20% to 25% is +5 percentage points. Changes in money and counts are shown as a percentage of the earlier year. Class sizes change in pupils.</p>')
    return page(f"life/compare/{a}-{b}.html", f"{a} compared with {b}", "\n".join(body), f"How work, pay, housing, holidays and class sizes differed between {a} and {b}.", scripts=COMPARE_JS)


def compare_index(sources):
    body = ["<h1>Compare two years</h1>", "<p>Pick two years to see work, pay, housing, holidays and class sizes side by side.</p>", compare_form("../")]
    body.append("<h2>All comparisons</h2><p>Every pair of years has its own page.</p>")
    for a in YEARS[:-1]:
        links = "".join(f'<li><a href="{a}-{b}.html">{b}</a></li>' for b in YEARS if b > a)
        body.append(f'<h3>{a} with…</h3><ul class="yearnav">{links}</ul>')
    html = page("life/compare/index.html", "Compare two years", "\n".join(body), "Compare everyday life in the UK between two years.", scripts=COMPARE_JS)
    return html.replace("<body>", "<body data-compare-index>", 1)


def series_chart(facts, title, items, unit, breaks=(), ymin=None, scale=1, split_breaks=False, kind=None, num=None, point_label=str):
    labels = [str(y) for y in YEARS]
    series = [(name, [_val(facts, fid(y)) for y in YEARS], style) for name, fid, style in items]
    ids = [[fid(y) if _val(facts, fid(y)) is not None else None for y in YEARS] for _, fid, _ in items]
    return line_chart(title, labels, series, unit, breaks=breaks, ymin=ymin, scale=scale, split_breaks=split_breaks,
                      kind=kind, ids=ids, num=num, point_labels=[point_label(y) for y in YEARS])


def life_index(facts, d, num, sources):
    body = ["<h1>Everyday life, year by year</h1>"]
    body.append(f'''<div class="answer"><p class="lede">How have work, pay, housing, holidays and school class sizes changed since {FIRST}?</p>
<p>Pick a year to see it on its own, or compare two years. Every figure is an official statistic, shown with the period and place it covers.</p></div>''')
    body.append(f"<h2 id='years'>Choose a year</h2>{year_links(None, '')}")
    body.append("<h2 id='compare'>Compare two years</h2>" + compare_form(""))
    body.append('<p class="small">Without JavaScript the button opens a list of every pair of years.</p>')
    body.append(CAUSE)
    y = LAST
    # Work
    body.append("<h2 id='work'>Work</h2>")
    body.append(f'<div class="answer"><p>{headline(facts, num, "work", y)}</p></div>')
    body.append(U.topic_line(num, "work", LAST))
    body.append(series_chart(facts, "Employment rate, ages 16 to 64", [("Men", lambda y: f"work.men.{y}", "a"), ("Women", lambda y: f"work.women.{y}", "b")], "Per cent of people aged 16 to 64 in work, April to June each year", kind="pct", num=num))
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
    body.append(details_table("Show job types for every year", "Share of people in work by job type (major group), January to December", head, rows))
    body.extend(work_ages_block(facts, num))
    body.extend(places_block(facts, num, "work"))
    body.append(explain.for_topic("work", sources, up="../"))
    body.append(f'<div class="limit"><p>{esc(TOPIC_LIMITS["work"])}</p></div>')
    body.append(source_line(sources, [s for s in TOPIC_SOURCES["work"] if s in sources], up="../"))
    # Earnings
    body.append("<h2 id='earnings'>Earnings</h2>")
    ch = 100 * (_val(facts, f"earn.real.ft.{LAST}") / _val(facts, f"earn.real.ft.{FIRST}") - 1)
    how = "about the same as" if abs(ch) < 2 else (f"{abs(ch):.0f}% more than" if ch > 0 else f"{abs(ch):.0f}% less than")
    body.append(f'<div class="answer"><p>In April {LAST}, the middle full-time employee earned {num(f"earn.ft.{LAST}", "pounds")} a week before tax. After allowing for rising prices, that was {how} in April {FIRST}, which was {num(f"earn.real.ft.{FIRST}", "pounds")} in April {LAST} prices.</p></div>')
    body.append(U.topic_line(num, "earnings", LAST))
    body.append(series_chart(facts, "Median weekly pay of full-time employees, after inflation", [("Men", lambda y: f"earn.real.ft_men.{y}", "a"), ("Women", lambda y: f"earn.real.ft_women.{y}", "b")],
                             "£ a week before tax, April each year, in April 2025 prices (CPIH)", breaks=[(YEARS.index(2011), "Coding change"), (YEARS.index(2021), "Coding change")], kind="pounds", num=num))
    body.append(details_table("Show earnings for every year", "Median gross weekly pay, United Kingdom, April each year",
                              ["Year", "Full-time (cash)", "Full-time (2025 prices)", "Full-time men", "Full-time women", "Part-time"],
                              [[str(y), num(f"earn.ft.{y}", "pounds"), num(f"earn.real.ft.{y}", "pounds"), num(f"earn.real.ft_men.{y}", "pounds"), num(f"earn.real.ft_women.{y}", "pounds"), num(f"earn.real.pt.{y}", "pounds")] for y in YEARS]))
    body.append('<p class="small">All columns except “Full-time (cash)” are in April 2025 prices.</p>')
    body.extend(places_block(facts, num, "earnings"))
    body.append(explain.for_topic("earnings", sources, up="../"))
    body.append(f'<div class="limit"><p>{esc(TOPIC_LIMITS["earnings"])}</p></div>')
    body.append(source_line(sources, [s for s in TOPIC_SOURCES["earnings"] if s in sources], up="../"))
    # Housing
    body.append("<h2 id='housing'>Housing</h2>")
    hy = max(yy for yy in YEARS if _val(facts, f"house.private.{yy}") is not None)
    body.append(f'<div class="answer"><p>{headline(facts, num, "housing", hy)} In {FIRST}-{str(FIRST + 1)[2:]}, {num(f"house.private.{FIRST}", "pct0")} rented privately.</p></div>')
    body.append(U.topic_line(num, "housing", LAST))
    body.append(series_chart(facts, "How households in England live", [("Rent privately", lambda y: f"house.private.{y}", "a"), ("Rent from council or housing association", lambda y: f"house.social.{y}", "b")],
                             "Per cent of households in England, survey year starting in the year shown", ymin=0, kind="pct", num=num, point_label=sy))
    body.append(details_table("Show housing for every year", "Housing tenure, England, % of households",
                              ["Survey year", "Own outright", "Mortgage", "Social rent", "Private rent", "Families with children renting privately"],
                              [[f"{y}-{str(y + 1)[2:]}", num(f"house.outright.{y}", "pct"), num(f"house.mortgage.{y}", "pct"), num(f"house.social.{y}", "pct"), num(f"house.private.{y}", "pct"),
                                num(f"house.kids.private.{y}", "pct") if f"house.kids.private.{y}" in facts else "<span class='missing'>not available</span>"] for y in YEARS if f"house.private.{y}" in facts]
                              + [[f"{y}-{str(y + 1)[2:]}", "<span class='missing'>not yet published</span>", "", "", "", ""] for y in YEARS if f"house.private.{y}" not in facts]))
    body.extend(housing_costs_block(facts, num, d))
    body.extend(housing_space_block(facts, num))
    body.extend(housing_regions_block(facts, num))
    body.append(explain.for_topic("housing", sources, up="../"))
    body.append(f'<div class="limit"><p>{esc(TOPIC_LIMITS["housing"])}</p></div>')
    body.append(source_line(sources, [s for s in TOPIC_SOURCES["housing"] if s in sources], up="../"))
    # Holidays
    body.append("<h2 id='holidays'>Holidays</h2>")
    names = d["countries"]["names"]
    tl = top_countries(facts, d, LAST, 3)
    spain_first = all(top_countries(facts, d, y, 1) == ["spain"] for y in d["countries"]["all"])
    body.append(f'''<div class="answer"><p>{headline(facts, num, "holidays", 2019, gb=False)} The pandemic cut holidays abroad to {num("hol.world.holiday.2020", "millions")} in 2020. {headline(facts, num, "holidays", LAST)}</p>
<p>{"Spain has been the most visited country in every year with figures by country. " if spain_first else ""}In {LAST} {esc(names[tl[0]])} had {num(f"hol.cty.{tl[0]}.all.{LAST}", "millions")} visits, followed by {esc(names[tl[1]])} ({num(f"hol.cty.{tl[1]}.all.{LAST}", "millions")}) and {esc(names[tl[2]])} ({num(f"hol.cty.{tl[2]}.all.{LAST}", "millions")}).</p>
<p>Holiday trips within Great Britain are measured by a separate survey, which changed method after 2019; see the table below.</p>
<p>These are counts of trips, not of people. Some people take several holidays a year and many take none, so “per 100 residents” is an average, not a typical experience.</p></div>''')
    body.append(U.topic_line(num, "holidays", LAST))
    body.append(series_chart(facts, "Holiday visits abroad", [("Holiday visits abroad", lambda y: f"hol.world.holiday.{y}", "a")],
                             "Millions of visits. Up to 2023 UK residents; from 2024 Great Britain residents (new method)", breaks=[(YEARS.index(2024), "New method")], ymin=0, scale=1000, split_breaks=True, kind="millions", num=num))
    body.append(details_table("Show holidays for every year", "Visits abroad, millions",
                              ["Year", "Residents of", "Holiday visits", "Per 100 residents", "Of which to Europe", "To North America", "Share of visits that were holidays"],
                              [[str(y), hol_basis(y), num(f"hol.world.holiday.{y}", "millions"), num(f"hol.abroad.per100.{y}", "int"), num(f"hol.europe.holiday.{y}", "millions"), num(f"hol.namerica.holiday.{y}", "millions"),
                                num(f"hol.holshare.{y}", "pct") if f"hol.holshare.{y}" in facts else "<span class='missing'>not available</span>"] for y in YEARS]))
    gb_years = [y for y in YEARS if f"hol.gb.holiday.{y}" in facts]
    body.append(details_table("Show holidays within Great Britain for every year", "Overnight holiday trips within Great Britain by Great Britain residents",
                              ["Year", "Survey", "Holiday trips", "Per 100 residents"],
                              [[str(y), gb_survey(y), num(f"hol.gb.holiday.{y}", "millions"), num(f"hol.gb.per100.{y}", "int")] if y in gb_years
                               else [str(y), "", '<span class="missing">not available</span>', ""] for y in YEARS if y >= 2019]))
    body.append('<p class="small">2020 and 2021 have no full-year figures because of the pandemic. The survey changed method after 2019, so 2019 is not compared with later years. Earlier years used yet other methods and are not shown.</p>')
    body.append(country_table(facts, num, d, LAST, 10))
    cyears = [2009, 2019, LAST]
    top = top_countries(facts, d, LAST, 10)
    body.append(details_table("Show the same countries in 2009 and 2019", "Visits abroad by main country visited (all purposes), millions",
                              ["Country"] + [str(y) for y in cyears],
                              [[esc(names[s])] + [num(f"hol.cty.{s}.all.{y}", "millions") for y in cyears] for s in top]))
    body.append('<p class="small">2009 and 2019 are UK residents; 2025 is Great Britain residents measured with a new method, so the columns are shown side by side but not compared.</p>' if LAST >= 2024 else "")
    body.append(explain.for_topic("holidays", sources, up="../"))
    body.append(f'<div class="limit"><p>{esc(TOPIC_LIMITS["holidays"])}</p></div>')
    body.append(source_line(sources, [s for s in TOPIC_SOURCES["holidays"] if s in sources], up="../"))
    # Schools
    body.append("<h2 id='schools'>Class sizes</h2>")
    body.append(f'<div class="answer"><p>{headline(facts, num, "schools", LAST)} In January {FIRST} the figures were {num(f"school.primary.{FIRST}", "dp1")} and {num(f"school.secondary.{FIRST}", "dp1")}.</p></div>')
    body.append(U.topic_line(num, "schools", LAST))
    body.append(series_chart(facts, "Average class size in England", [("Primary", lambda y: f"school.primary.{y}", "a"), ("Secondary", lambda y: f"school.secondary.{y}", "b")],
                             "Pupils per class, January school census, state-funded schools in England", ymin=15, kind="dp1", num=num))
    body.append(details_table("Show class sizes for every year", "Average class size, England, January census",
                              ["January census", "School year", "Primary", "Secondary"],
                              [[str(y), f"{y - 1}/{str(y)[2:]}", num(f"school.primary.{y}", "dp1"), num(f"school.secondary.{y}", "dp1")] for y in YEARS]))
    wy = [y for y in YEARS if _val(facts, f"school.wales.infant.{y}") is not None]
    body.append("<h3 id='schools-wales'>Wales</h3>")
    body.append(table("Average class size, Wales, January census", ["January census", "School year", "Infant classes (reception to year 2)", "Junior classes (years 3 to 6)"],
                      [[str(y), f"{y - 1}/{str(y)[2:]}", num(f"school.wales.infant.{y}", "dp1"), num(f"school.wales.junior.{y}", "dp1")] for y in wy]))
    body.append('<p class="small">Welsh infant and junior figures are not the same groups as England’s primary figure, so they are not compared with it.</p>')
    body.append(explain.for_topic("schools", sources, up="../"))
    body.append(f'<div class="limit"><p>{esc(TOPIC_LIMITS["schools"])}</p></div>')
    body.append(source_line(sources, [s for s in TOPIC_SOURCES["schools"] if s in sources], up="../"))
    return page("life/index.html", "Everyday life, year by year", "\n".join(body), "How work, earnings, housing, holidays and class sizes have changed in the UK since 2008.", scripts=COMPARE_JS)


def work_ages_block(facts, num):
    out = ["<h3 id='work-age'>By age</h3>"]
    young, old = f"work.age.18_24.{LAST}", f"work.age.50_64.{LAST}"
    out.append(f'<div class="answer"><p>In April to June {LAST}, {num(f"work.age.25_34.{LAST}", "pct")} of people aged 25 to 34 and {num(f"work.age.35_49.{LAST}", "pct")} of those aged 35 to 49 were in work. '
               f'The rate was lower for 18 to 24 year olds ({num(young, "pct")}), many of whom are studying, and for 50 to 64 year olds ({num(old, "pct")}). '
               f'{num(f"work.age.65.{LAST}", "pct")} of people aged 65 and over were in work, compared with {num(f"work.age.65.{FIRST}", "pct")} in {FIRST}.</p></div>')
    out.append(series_chart(facts, "Employment rate by age", [("50 to 64", lambda y: f"work.age.50_64.{y}", "a"), ("18 to 24", lambda y: f"work.age.18_24.{y}", "b"),
                                                            ("65 and over", lambda y: f"work.age.65.{y}", "c")],
                            "Per cent of each age group in work, April to June each year, United Kingdom", ymin=0, kind="pct", num=num))
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
    ys = [y for y in YEARS if _val(facts, fid("uk", y)) is not None]
    a, b = ys[0], ys[-1]
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
        rows.append([esc(n), num(fid(k, a), kind), num(fid(k, b), kind), moe, change_cell(facts, num, fid(k, a), fid(k, b), style, kind)])
    out.append(table(f"{what}: {a} and {b}", ["Place", str(a), str(b), f"Margin of error, {b}", "Change"], rows))
    out.append(f'<p class="small">The margin of error is the 95% range published by ONS for the {b} figure. Smaller places have smaller samples and wider margins, so a difference between two places that is smaller than their margins could be sampling noise. {U.how_sure_link("../")}</p>')
    out.append(details_table(f"Show every year by nation and region", what, ["Year"] + [esc(n) for _, n in places],
                             [[str(y)] + [num(fid(k, y), kind) for k, _ in places] for y in ys]))
    out.append('<p class="small">The nine English regions together make up England.</p>')
    return out


def housing_regions_block(facts, num):
    ys = [y for y in YEARS if _val(facts, f"house.reg.owner.england.{y}") is not None]
    a, b = ys[0], ys[-1]
    places = [("england", "England")] + [(k, n) for k, n, _ in REGIONS]
    out = ["<h3 id='housing-regions'>Homes by tenure in each region</h3>"]
    pr = {k: _val(facts, f"house.reg.private.{k}.{b}") for k, _, _ in REGIONS}
    top = max(pr, key=pr.get)
    names = {k: n for k, n, _ in REGIONS}
    out.append(f'<div class="answer"><p>These figures count homes (dwellings), not households, so they differ a little from the survey figures above. '
               f'At 31 March {b}, {num(f"house.reg.private.england.{b}", "pct0")} of homes in England were rented privately, up from {num(f"house.reg.private.england.{a}", "pct0")} in {a}. '
               f'The share was highest in {names[top]} ({num(f"house.reg.private.{top}.{b}", "pct0")}), where {num(f"house.reg.owner.{top}.{b}", "pct0")} of homes were owner occupied.</p></div>')
    rows = []
    for k, n in places:
        rows.append([esc(n)] + [num(f"house.reg.{t}.{k}.{y}", "pct") for t in ("owner", "private", "social") for y in (a, b)])
    out.append(table(f"Homes by tenure, England and its regions, 31 March {a} and {b}, % of homes",
                     ["Place", f"Owner occupied {a}", f"Owner occupied {b}", f"Private rent {a}", f"Private rent {b}", f"Social rent {a}", f"Social rent {b}"], rows))
    out.append(details_table("Show private renting by region for every year", "Homes rented privately, % of homes, 31 March each year",
                             ["Year"] + [esc(n) for _, n in places], [[str(y)] + [num(f"house.reg.private.{k}.{y}", "pct") for k, _ in places] for y in ys]))
    out.append(f'<p class="small">Social rent adds homes rented from councils and from housing associations (our calculation). Owner occupied includes shared ownership. '
               f'Private renting is estimated from the Labour Force Survey and smoothed; figures from 2024 are provisional. Wales, Scotland and Northern Ireland measure housing with their own surveys and are not shown here.</p>')
    return out


def housing_costs_block(facts, num, d):
    base = d["housing_costs"]["base"]
    b = sy(base)
    ys = [y for y in YEARS if f"house.rent.private.{y}" in facts]
    out = ["<h3 id='housing-costs'>What housing costs</h3>"]
    out.append(f'<div class="answer"><p>In {b}, households renting privately in England paid {num(f"house.rent.private.{base}", "pounds")} a week on average, '
               f'social renters {num(f"house.rent.social.{base}", "pounds")} and households with a mortgage {num(f"house.mortpay.{base}", "pounds")}. '
               f'After allowing for rising prices, the average private rent in {sy(FIRST)} was {num(f"house.real.rent.private.{FIRST}", "pounds")} in {b} prices, '
               f'social rent {num(f"house.real.rent.social.{FIRST}", "pounds")} and the average mortgage payment {num(f"house.real.mortpay.{FIRST}", "pounds")}.</p></div>')
    out.append(series_chart(facts, "Average weekly housing costs in England, after inflation",
                            [("Private rent", lambda y: f"house.real.rent.private.{y}", "a"), ("Mortgage payment", lambda y: f"house.real.mortpay.{y}", "b"),
                             ("Social rent", lambda y: f"house.real.rent.social.{y}", "c")],
                            f"£ a week (mean), survey year starting in the year shown, in {b} prices (CPIH)", ymin=0, kind="pounds", num=num, point_label=sy))
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
               f'{num(f"house.crowd.owners.{last}", "pct")} of owner occupiers. For {sy(FIRST - 2)} to {sy(FIRST)} the figures were '
               f'{num(f"house.crowd.social.{FIRST}", "pct")}, {num(f"house.crowd.private.{FIRST}", "pct")} and {num(f"house.crowd.owners.{FIRST}", "pct")}.</p></div>')
    out.append(series_chart(facts, "Overcrowded households in England, by tenure",
                            [("Social renters", lambda y: f"house.crowd.social.{y}", "a"), ("Private renters", lambda y: f"house.crowd.private.{y}", "b"),
                             ("Owner occupiers", lambda y: f"house.crowd.owners.{y}", "c")],
                            "Per cent of households below the bedroom standard, three-year average ending in the survey year shown", ymin=0, kind="pct", num=num, point_label=sy))
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
    return out


MEAS = []
OCC_NAMES = {}


def init(d):
    OCC_NAMES.clear()
    OCC_NAMES.update(d["work"]["occ_groups"])
    MEAS.clear()
    MEAS.extend(measures(d))
