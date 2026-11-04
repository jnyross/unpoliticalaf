"""Topic-page sections for the three longer-run life measures in data_life_extra:
pay spread (earnings), house prices against earnings (housing) and jobs by
industry (work). Each returns a list of parts starting with an <h3>, which
topic_page() turns into its own section.
"""
from .html import NOFOLD, details_table, esc, line_chart, table
from . import findings as F


def _v(facts, fid):
    f = facts.get(fid)
    return None if f is None else f.value


def _chart(facts, num, title, years, items, unit, kind, breaks=(), ymin=None, point_label=str, finding=None, split_breaks=False):
    """A line chart over a measure's own years. items: (name, fid(year), style)."""
    series = [(name, [_v(facts, fid(y)) for y in years], style) for name, fid, style in items]
    ids = [[fid(y) if _v(facts, fid(y)) is not None else None for y in years] for _, fid, _ in items]
    br = [(years.index(y), text) for y, text in breaks if y in years and y != years[0]]
    return line_chart(title, [str(y) for y in years], series, unit, breaks=br, ymin=ymin, kind=kind, ids=ids, num=num,
                      point_labels=[point_label(y) for y in years], finding=finding, split_breaks=split_breaks)


# ---------------------------------------------------------------- earnings: how far apart is pay?

def spread_ref_year(sp, first):
    """Year to compare the latest with: the first year of the latest stretch measured
    the same way (passed in as first), so the headline comparison crosses no break."""
    return max(first, 2006, sp["years"][0])


def spread_block(facts, num, d, first):
    sp = d["life_extra"]["spread"]
    years, last, base = sp["years"], sp["years"][-1], sp["base_year"]
    ref = spread_ref_year(sp, first)
    lo_ch = 100 * (_v(facts, f"spread.real.p10.{last}") / _v(facts, f"spread.real.p10.{ref}") - 1)
    hi_ch = 100 * (_v(facts, f"spread.real.p90.{last}") / _v(facts, f"spread.real.p90.{ref}") - 1)

    def rise(ch):
        return "about the same as" if abs(ch) < 2 else (f"{abs(ch):.0f}% more than" if ch > 0 else f"{abs(ch):.0f}% less than")

    out = ["<h3 id='earnings-spread'>How far apart is pay?</h3>"]
    out.append(f'<div class="answer"><p>Line up every full-time employee by weekly pay. In April {last}, the lowest-paid tenth earned less than {num(f"spread.p10.{last}", "pounds")} a week before tax, '
               f'the middle employee {num(f"spread.p50.{last}", "pounds")} and the best-paid tenth more than {num(f"spread.p90.{last}", "pounds")}. '
               f'The pay at the top-tenth line was {num(f"spread.ratio.{last}", "times")} the pay at the bottom-tenth line, compared with {num(f"spread.ratio.{ref}", "times")} in April {ref}.</p>'
               f'<p>After allowing for rising prices, pay at the bottom-tenth line was {rise(lo_ch)} in {ref}, and pay at the top-tenth line was {rise(hi_ch)} in {ref}. '
               f'These figures show what changed, not why.</p></div>')
    cyears = [y for y in years if y >= 2006]
    out.append(_chart(facts, num, "Weekly pay at three points of the pay ladder, after inflation", cyears,
                      [("Top-tenth line", lambda y: f"spread.real.p90.{y}", "a"), ("Median", lambda y: f"spread.real.p50.{y}", "b"),
                       ("Bottom-tenth line", lambda y: f"spread.real.p10.{y}", "c")],
                      f"£ a week before tax, full-time employees, United Kingdom, April each year, in April {base} prices (adjusted with CPIH, the official consumer prices index that includes housing costs). From 2006, after the survey’s last method change; the table also gives 2002 to 2005. The lines break in 2011 and 2021, when the survey changed the codes it uses to sort jobs into types (“jobs recoded”)", "pounds",
                      breaks=sorted(sp["breaks"].items()), ymin=0, split_breaks=True,
                      finding=F.narrowing("After inflation, the gap between the top-tenth and bottom-tenth lines", lambda d: f"£{d:,.0f} a week", si=0, sj=2, which="last")))
    out.append(details_table("Show pay spread for every year", f"Gross weekly pay of full-time employees, United Kingdom, April each year",
                             ["Year", "Bottom tenth earn less than (cash)", "Median (cash)", "Top tenth earn more than (cash)", "Top line ÷ bottom line (times)",
                              f"Bottom line ({base} prices)", f"Top line ({base} prices)"],
                             [[str(y), num(f"spread.p10.{y}", "pounds"), num(f"spread.p50.{y}", "pounds"), num(f"spread.p90.{y}", "pounds"), num(f"spread.ratio.{y}", "dp1"),
                               num(f"spread.real.p10.{y}", "pounds"), num(f"spread.real.p90.{y}", "pounds")] for y in years]))
    out.append(f'<p class="small">The 10th and 90th percentiles are the pay of the employee one tenth of the way up the ladder and nine tenths of the way up. '
               f'They are lines on the ladder, not averages of the groups. Only full-time employees are counted: part-time workers and the self-employed are not, and pay is for one job before tax, '
               f'not household income. The ratio does not depend on inflation, because both lines are in the same year’s prices. '
               f'ONS notes breaks in the survey in 2004 and 2006 (method changes) and in 2011 and 2021 (new job coding). The chart starts in 2006 and breaks at 2011 and 2021, and changes are worked out only between years on the same side of every break, because a move across a break may come from the change rather than from pay.</p>')
    return out


# ---------------------------------------------------------------- housing: house prices against earnings

AFFORD_PAGE = "life/house-prices.html"


def _the(n):
    return ("the " if n.split()[0] in ("North", "South", "East", "West") else "") + n


def comparable_from(years):
    """ONS: 1997 and 1998 earnings are weekly pay scaled up to a year, not directly
    comparable with later years, so changes are worked out from 1999."""
    return next(y for y in years if y >= 1999)


def _afford_answer(facts, num, d):
    af = d["life_extra"]["afford"]
    years = af["years"]
    last = years[-1]
    first = comparable_from(years)
    names = dict(af["places"])
    regions = [k for k, _ in af["places"] if k not in ("ew", "england", "wales")]
    peak = max(years, key=lambda y: (_v(facts, f"afford.ratio.ew.{y}"), y))
    hi = max(regions, key=lambda k: _v(facts, f"afford.ratio.{k}.{last}"))
    lo = min(regions, key=lambda k: _v(facts, f"afford.ratio.{k}.{last}"))
    peak_txt = (f' The highest ratio was {num(f"afford.ratio.ew.{peak}", "times2")} in {peak}.' if peak != last else " That was the highest since the series began.")
    return (f'<div class="answer"><p>In the year to September {last}, the middle-priced home sold in England and Wales cost {num(f"afford.price.ew.{last}", "pounds")}, '
            f'and the middle full-time employee earned {num(f"afford.earn.ew.{last}", "pounds")} a year before tax. '
            f'So the home cost {num(f"afford.ratio.ew.{last}", "times2")} a year’s earnings, compared with {num(f"afford.ratio.ew.{first}", "times2")} in {first}, the first year measured the same way.{peak_txt} '
            f'It differs a lot by place: {num(f"afford.ratio.{hi}.{last}", "times2")} in {esc(_the(names[hi]))} and {num(f"afford.ratio.{lo}.{last}", "times2")} in {esc(_the(names[lo]))}.</p></div>')


def afford_block(facts, num, d):
    """The short version on the housing page: the answer and a link to the full page."""
    first = d["life_extra"]["afford"]["years"][0]
    return ["<h3 id='housing-afford'>House prices compared with earnings</h3>", NOFOLD, _afford_answer(facts, num, d),
            f'<p class="more-link"><a href="house-prices.html">House prices and earnings since {first}</a>, with each region.</p>']


def afford_page(facts, d, num, sources):
    """A page of its own, so the housing page stays within its size limit."""
    from .html import page, source_line, FOLD
    from .pages_life import topic_nav, CAUSE
    af = d["life_extra"]["afford"]
    years = af["years"]
    first, last = years[0], years[-1]
    body = ['<p class="small"><a href="index.html">Everyday life, year by year</a> › <a href="housing.html">Housing</a></p>',
            f"<h1>How do house prices compare with earnings, and how has that changed since {first}?</h1>", _afford_answer(facts, num, d), topic_nav("housing"), CAUSE]
    body.append("<h2 id='trend'>The ratio over time</h2>")
    body.append(_chart(facts, num, "Median house price as a multiple of median full-time earnings", years,
                       [("England", lambda y: f"afford.ratio.england.{y}", "a"), ("Wales", lambda y: f"afford.ratio.wales.{y}", "b")],
                       "Times a year’s earnings. House prices for the year ending September; earnings of full-time employees working in the area, April", "times2", ymin=0,
                       breaks=[(comparable_from(years), "Earnings counted as yearly pay from 1999")], split_breaks=True,
                       finding=F.pair("In England, house prices as a multiple of earnings", "in Wales they", which="last",
                                      together="House prices as a multiple of earnings {phrase} in both England and Wales")))
    body.append(FOLD)
    body.append(details_table("Show house prices and earnings for every year", "England and Wales: median house price, median full-time annual earnings and the ratio",
                              ["Year", "Median house price", "Median full-time earnings (a year)", "Ratio (times a year’s earnings)"],
                              [[str(y), num(f"afford.price.ew.{y}", "pounds"), num(f"afford.earn.ew.{y}", "pounds"), num(f"afford.ratio.ew.{y}", "dp2")] for y in years]))
    mid = 2008 if 2008 in years else years[len(years) // 2]
    base = comparable_from(years)
    body.append("<h2 id='regions'>Each nation and region</h2>")
    body.append(table(f"Median house price ÷ median full-time earnings (times a year’s earnings), {base}, {mid} and {last}",
                      ["Place", str(base), str(mid), str(last)],
                      [[esc(n), num(f"afford.ratio.{k}.{base}", "dp2"), num(f"afford.ratio.{k}.{mid}", "dp2"), num(f"afford.ratio.{k}.{last}", "dp2")]
                       for k, n in af["places"]]))
    body.append("<h2 id='about'>About these figures</h2>")
    body.append(f'<div class="limit"><p>England and Wales only: Scotland and Northern Ireland publish their own house price figures, which are measured differently, so they are not shown here. '
                f'House prices are the middle price of all homes sold in the year ending September, including homes bought without a mortgage; they are not the price of the same homes each year. '
                f'Earnings are for one full-time employee working in the area, not household income, and {first} and {first + 1} use weekly pay scaled up to a year, which ONS says is not directly comparable with later years. '
                f'The ratio does not include mortgage interest rates, deposits or rents, so it is not a measure of monthly housing costs: see <a href="housing.html#housing-costs">what housing costs</a>. '
                f'ONS publishes the ratio rounded to two decimal places and revises these figures each year.</p></div>')
    body.append(source_line(sources, ["ons-affordability"], up="../"))
    return page(AFFORD_PAGE, f"House prices and earnings since {first}", "\n".join(body),
                f"Median house prices compared with median full-time earnings in England and Wales and each English region, every year since {first}, from ONS.")


# ---------------------------------------------------------------- work: jobs by industry

SHOWN_INDUSTRIES = ["C", "G", "Q", "M", "P", "F"]
INDUSTRY_PAGE = "life/jobs-by-industry.html"


def _industry_answer(facts, num, d):
    jb = d["life_extra"]["jobs"]
    years, names, prov = jb["years"], jb["names"], jb["provisional"]
    first, last = years[0], years[-1]
    lab = (lambda y: f"June {y} (provisional)" if y == prov else f"June {y}")
    shares = {s: _v(facts, f"jobs.share.{s}.{last}") for s in jb["sections"]}
    top = sorted(shares, key=shares.get, reverse=True)[:3]
    return (f'<div class="answer"><p>There were {num(f"jobs.total.{last}", "millions")} jobs in the UK in {lab(last)}. The industries with the most were '
            f'{esc(names[top[0]].lower())} ({num(f"jobs.share.{top[0]}.{last}", "pct")} of all jobs), {esc(names[top[1]].lower())} ({num(f"jobs.share.{top[1]}.{last}", "pct")}) '
            f'and {esc(names[top[2]].lower())} ({num(f"jobs.share.{top[2]}.{last}", "pct")}).</p>'
            f'<p>In June {first}, manufacturing had {num(f"jobs.share.C.{first}", "pct")} of all jobs ({num(f"jobs.ind.C.{first}", "millions")}); in {lab(last)} it had {num(f"jobs.share.C.{last}", "pct")} ({num(f"jobs.ind.C.{last}", "millions")}). '
            f'Health and social work went from {num(f"jobs.share.Q.{first}", "pct")} to {num(f"jobs.share.Q.{last}", "pct")}.</p></div>')


def jobs_people_block(facts, num, d):
    """Why there can be more jobs than people in work: the answer first, then a short table."""
    jb = d["life_extra"]["jobs"]
    years, prov = jb["years"], jb["provisional"]
    first, last = years[0], years[-1]
    lab = (lambda y: f"June {y} (provisional)" if y == prov else f"June {y}")
    gaps = {y: _v(facts, f"jobs.gap.{y}") for y in years}
    gaps = {y: g for y, g in gaps.items() if g is not None}
    lo, hi = min(gaps, key=gaps.get), max(gaps, key=gaps.get)
    return ["<h3 id='jobs-and-people'>Why can there be more jobs than people in work?</h3>",
            f'<div class="answer"><p>Some people have more than one job, and jobs are counted one by one, so someone with two jobs is counted twice. '
            f'In {lab(last)} there were {num(f"jobs.total.{last}", "millions")} jobs and {num(f"jobs.people.{last}", "millions_people")} people in employment, a difference of {num(f"jobs.gap.{last}", "millions")}.</p></div>',
            f'<p>The counts also come from different sources: jobs from employer surveys, self-employment, the armed forces and trainees; people from the Labour Force Survey. '
            f'Jobs were higher in every June from {first} to {last}, by between {num(f"jobs.gap.{lo}", "millions")} ({lo}) and {num(f"jobs.gap.{hi}", "millions")} ({hi}). '
            f'The figures do not show how much of the gap each reason explains.</p>',
            f'<p class="more-link"><a href="jobs-by-industry.html#jobs-people">Jobs and people in employment, June figures</a>: the two counts side by side, and the difference, for selected years.</p>']


def jobs_people_table(facts, num, d):
    """The June jobs and people counts side by side, for selected years (on the jobs by industry page)."""
    jb = d["life_extra"]["jobs"]
    years, prov = jb["years"], jb["provisional"]
    first, last = years[0], years[-1]
    lab = (lambda y: f"June {y} (provisional)" if y == prov else f"June {y}")
    shown = [y for y in dict.fromkeys([first, 2000, 2010, 2020, last]) if _v(facts, f"jobs.gap.{y}") is not None]
    rows = [[lab(y), num(f"jobs.total.{y}", "int"), num(f"jobs.people.{y}", "int"), num(f"jobs.gap.{y}", "int")] for y in shown]
    return ["<h2 id='jobs-people'>Jobs and people in employment</h2>",
            table("Jobs and people in employment, United Kingdom, June, selected years (thousands)",
                  ["Year", "Jobs", "People in employment", "Jobs minus people"], rows),
            '<p class="small">Jobs are workforce jobs (ONS JOBS02); people in employment are from the Labour Force Survey (ONS MGRZ). Both are seasonally adjusted. '
            'The difference is our calculation. The gap is not a count of people with two jobs, because the two counts also differ in source and coverage.</p>']


def industry_block(facts, num, d):
    """The short version on the work page: the answer and a link to the full page."""
    first = d["life_extra"]["jobs"]["years"][0]
    return ["<h3 id='work-industry'>Jobs by industry</h3>", NOFOLD, _industry_answer(facts, num, d),
            f'<p class="more-link"><a href="jobs-by-industry.html">Jobs by industry, every year since {first}</a>: a chart of six large industries and tables for all twenty.</p>']


def industry_page(facts, d, num, sources):
    """A page of its own: about 50 years of figures would push the work page past its size limit."""
    from .html import page, source_line, FOLD
    from .pages_life import groups_chart, topic_nav, CAUSE
    jb = d["life_extra"]["jobs"]
    years, names, prov = jb["years"], jb["names"], jb["provisional"]
    first, last = years[0], years[-1]
    lab = (lambda y: f"June {y} (provisional)" if y == prov else f"June {y}")
    body = ['<p class="small"><a href="index.html">Everyday life, year by year</a> › <a href="work.html">Work</a></p>',
            f"<h1>Which industries do people work in, and how has that changed since {first}?</h1>", _industry_answer(facts, num, d), topic_nav("work"), CAUSE]
    body.append("<h2 id='trend'>Six large industries over time</h2>")
    body.append(groups_chart(facts, "Share of all jobs in six large industries",
                             [(names[s], (lambda s: lambda y: f"jobs.share.{s}.{y}")(s)) for s in SHOWN_INDUSTRIES],
                             "Per cent of all workforce jobs, United Kingdom, June each year, seasonally adjusted", years=years, ymin=0, kind="pct", num=num,
                             finding=F.moves({n: f"the share of jobs in {n[:1].lower() + n[1:]}" for n in names.values()}, which="all"),
                             point_label=lab))
    body.append(FOLD)
    body.append(details_table("Show jobs in the six large industries for every year", "Share of all workforce jobs, United Kingdom, June each year, %",
                              ["Year"] + [esc(names[s]) for s in SHOWN_INDUSTRIES] + ["All jobs (thousands)"],
                              [[lab(y)] + [num(f"jobs.share.{s}.{y}", "pct") for s in SHOWN_INDUSTRIES] + [num(f"jobs.total.{y}", "int")] for y in years]))
    cols = [first, 2000, last] if 2000 in years else [first, last]
    body.append("<h2 id='all-industries'>All twenty industries</h2>")
    body.append(table(f"Workforce jobs by industry, United Kingdom, June {', June '.join(str(c) for c in cols)}",
                      ["Industry"] + [f"Share {c}" for c in cols] + [f"Jobs {c} (thousands)" for c in cols],
                      [[esc(names[s])] + [num(f"jobs.share.{s}.{c}", "pct") for c in cols] + [num(f"jobs.ind.{s}.{c}", "int") for c in cols] for s in jb["sections"]]
                      + [["All industries"] + [""] * len(cols) + [num(f"jobs.total.{c}", "int") for c in cols]]))
    body.extend(jobs_people_table(facts, num, d))
    body.append("<h2 id='about'>About these figures</h2>")
    body.append(f'<div class="limit"><p>These count jobs, not people: someone with two jobs counts twice. They include employee jobs (from surveys of employers), '
                f'self-employment (from the Labour Force Survey), the armed forces and government-supported trainees, and are seasonally adjusted. Industries follow the 2007 Standard Industrial Classification '
                f'for the whole series. ONS notes that before September 2001 the private households figure excludes employee jobs, and that from March 2019 the self-employment part '
                f'has a step change because the Labour Force Survey was reweighted. Shares are our calculation: jobs in the industry ÷ all jobs. '
                f'{lab(prov) + " figures are provisional." if prov else ""}</p></div>')
    body.append(source_line(sources, ["ons-jobs02"], up="../"))
    return page(INDUSTRY_PAGE, f"Jobs by industry since {first}", "\n".join(body),
                f"How many jobs there are in each industry in the UK, every June since {first}, from ONS workforce jobs statistics.")


# ---------------------------------------------------------------- holidays: who could afford a week away?

def holiday_afford_block(facts, num, d):
    """The nearest official yearly measure to 'how many people take a holiday', with its limits."""
    ha = d["life_extra"]["holafford"]
    years = ha["years"]
    out = ["<h3 id='holidays-afford'>How many people take a holiday?</h3>"]
    if not years:
        out.append('<p>No official statistic, published each year, gives the share of people who took a holiday. The travel surveys count trips, not travellers.</p>')
        return out
    first, last = years[0], years[-1]
    cuts = [y for y in ha["breaks"] if y in years and y != first]
    runs, start = [], first
    for c in cuts + [last + 1]:
        run = [y for y in years if start <= y < c]
        if run:
            runs.append(run)
        start = c
    moves = []
    for run in runs:
        if len(run) < 3:
            continue
        a, b = run[0], run[-1]
        va, vb = _v(facts, f"holafford.all.{a}"), _v(facts, f"holafford.all.{b}")
        word = "rose" if vb > va else ("fell" if vb < va else "was unchanged")
        moves.append(f"from {a} to {b} it {word} from {num(f'holafford.all.{a}', 'pct')} to {num(f'holafford.all.{b}', 'pct')}")
    run_text = ", ".join(f"{r[0]} to {r[-1]}" if len(r) > 1 else str(r[0]) for r in runs)
    out.append(f'<div class="answer"><p>No yearly official statistic gives the share of people who took a holiday. '
               f'The nearest asks a different question: could the household afford a week’s holiday away from home? '
               f'In the {last} survey, {num(f"holafford.all.{last}", "pct")} of people in the UK lived in a household that could not: '
               f'{num(f"holafford.low.{last}", "pct")} of people in low-income households and {num(f"holafford.notlow.{last}", "pct")} of people in other households.</p>'
               + (f'<p>The survey changed in {" and ".join(str(c) for c in cuts)}, so only years in the same run are compared: {"; ".join(moves)}.</p>' if moves else "")
               + '</div>')
    # The answer gives each group's figures; the chart and its limits wait in the fold on a phone.
    out.append("<!--keepfold-->")
    out.append(_chart(facts, num, "People whose household could not afford a week’s holiday away from home", years,
                      [("Low-income households", lambda y: f"holafford.low.{y}", "b"), ("Everyone", lambda y: f"holafford.all.{y}", "a"),
                       ("Other households", lambda y: f"holafford.notlow.{y}", "c")],
                      "% of people, United Kingdom, EU-SILC survey year", "pct", breaks=[(y, "Series break") for y in ha["breaks"]], ymin=0,
                      finding=F.gap("The share for people in low-income households", "for people in other households", si=0, sj=2)))
    out.append(details_table("Show who could not afford a week’s holiday, every year",
                             "People whose household could not afford a week’s holiday away from home, % of people, United Kingdom",
                             ["Survey year"] + [esc(label) for _, _, _, label in ha["groups"]],
                             [[str(y) + (" (series break)" if y in ha["breaks"] else "")] + [num(f"holafford.{gk}.{y}", "pct") for gk, _, _, _ in ha["groups"]] for y in years]))
    out.append(f'<div class="limit"><p>This is not the share of people who went on holiday. It counts people whose household said it could not afford a week away; '
               f'people who chose not to go, or who took shorter breaks, are not counted, and one answer covers everyone in the household, children included. '
               f'Low income means below 60% of the middle (median) household income, after adjusting for household size. '
               f'Eurostat marks breaks in the series in {" and ".join(str(y) for y in ha["breaks"])}, so changes across those years are not like-for-like. '
               f'The figures come from the EU statistics on income and living conditions survey, which the Office for National Statistics ran in the UK; Eurostat’s table has UK figures for the {first} to {last} surveys only, because the UK stopped supplying them after leaving the EU. '
               f'The Department for Work and Pensions’ Family Resources Survey asks a similar question every year, but publishes it only as one item inside combined measures of deprivation for children and pensioners, whose questions have changed several times, so it is not shown here.</p></div>')
    return out


# ---------------------------------------------------------------- schools: large classes, infant and key stage 2

def _school_year(y):
    return f"{y - 1}/{str(y)[2:]}"


def _word(a, b, up="rose", down="fell", same="was unchanged"):
    return up if b > a else (down if b < a else same)


def class_detail_blocks(facts, num, d):
    """Two sections for the class sizes page: how many pupils are in classes of more than
    30, and the averages for infant and key stage 2 classes (England, January census)."""
    cd = d["life_extra"]["classes"]
    large = cd["large"]
    py = sorted(large["primary"])
    iy = sorted(cd["infant"])
    a, b = py[0], py[-1]
    out = ["<h3 id='schools-large'>How many pupils are in classes of more than 30?</h3>"]
    p_word = _word(_v(facts, f"school.large.primary.{a}"), _v(facts, f"school.large.primary.{b}"))
    s_word = _word(_v(facts, f"school.large.secondary.{a}"), _v(facts, f"school.large.secondary.{b}"))
    lo = min(py, key=lambda y: (_v(facts, f"school.large.secondary.{y}"), y))
    out.append(f'<div class="answer"><p>In January {b}, {num(f"school.large.primary.{b}", "pct")} of primary pupils and {num(f"school.large.secondary.{b}", "pct")} of secondary pupils '
               f'in English state schools were in classes of more than 30, against {num(f"school.large.primary.{a}", "pct")} and {num(f"school.large.secondary.{a}", "pct")} in January {a}: '
               f'the primary share {p_word} and the secondary share {s_word} (lowest in January {lo}, at {num(f"school.large.secondary.{lo}", "pct")}).</p>'
               f'<p>In infant classes (reception to year 2), where the law sets a limit of 30 with some exceptions, it was {num(f"school.large.infant.{iy[-1]}", "pct")} '
               f'({num(f"school.pupils.infant.over30.{iy[-1]}", "int")} children) in January {iy[-1]}; in key stage 2 classes (years 3 to 6), which have no limit, {num(f"school.large.ks2.{iy[-1]}", "pct")}.</p></div>')
    out.append(_chart(facts, num, "Pupils in classes of more than 30, England", py,
                      [("Primary", lambda y: f"school.large.primary.{y}", "a"), ("Secondary", lambda y: f"school.large.secondary.{y}", "b")],
                      "% of pupils in classes of more than 30, January school census, state-funded schools", "pct", ymin=0, point_label=lambda y: f"January {y}",
                      finding=F.pair("The share of primary pupils in classes of more than 30", "the share of secondary pupils")))
    rows = [[str(y), _school_year(y), num(f"school.large.primary.{y}", "pct"), num(f"school.large.secondary.{y}", "pct"),
             num(f"school.large.infant.{y}", "pct") if y in large["infant"] else '<span class="missing">not in these tables</span>',
             num(f"school.large.ks2.{y}", "pct") if y in large["ks2"] else '<span class="missing">not in these tables</span>'] for y in py]
    out.append(details_table("Show classes of more than 30 for every year", "Pupils in classes of more than 30, % of pupils, England, January census",
                             ["January census", "School year", "Primary", "Secondary", "Infant classes", "Key stage 2 classes"], rows))
    out.append(f'<p class="small">Up to January 2015 the DfE published these shares for primary and secondary schools only, as percentages rounded to 1 decimal place; '
               f'the figures here add its “31 to 35 pupils” and “36 or more pupils” groups. From January 2016 they are worked out from the DfE’s pupil counts. '
               f'Both count classes taught by one teacher.</p>')
    a2, b2 = iy[0], iy[-1]
    out.append("<h3 id='schools-phases'>Infant and key stage 2 classes</h3>")
    i_word = _word(_v(facts, f"school.infant.{a2}"), _v(facts, f"school.infant.{b2}"), up="got bigger", down="got smaller", same="were the same size")
    k_word = _word(_v(facts, f"school.ks2.{a2}"), _v(facts, f"school.ks2.{b2}"), up="got bigger", down="got smaller", same="were the same size")
    out.append(f'<div class="answer"><p>In January {b2}, the average infant class (reception to year 2) in English state schools had {num(f"school.infant.{b2}", "dp1")} pupils '
               f'and the average key stage 2 class (years 3 to 6) {num(f"school.ks2.{b2}", "dp1")}, against {num(f"school.infant.{a2}", "dp1")} and {num(f"school.ks2.{a2}", "dp1")} '
               f'in January {a2}, the first year in the DfE’s current data: infant classes {i_word} and key stage 2 classes {k_word}.</p></div>')
    out.append(_chart(facts, num, "Average infant and key stage 2 class size, England", iy,
                      [("Infant (reception to year 2)", lambda y: f"school.infant.{y}", "a"), ("Key stage 2 (years 3 to 6)", lambda y: f"school.ks2.{y}", "b")],
                      "Pupils per class, January school census, state-funded schools", "dp1", ymin=20, point_label=lambda y: f"January {y}",
                      finding=F.pair("Average infant class sizes", "key stage 2 class sizes")))
    # The answer gives both averages; on a phone the chart waits in the fold.
    out.append("<!--keepfold-->")
    out.append(details_table("Show infant and key stage 2 classes for every year", "Infant and key stage 2 classes, England, January census",
                             ["January census", "School year", "Infant: average class", "Infant: pupils in classes of more than 30", "Key stage 2: average class",
                              "Key stage 2: pupils in classes of more than 30"],
                             [[str(y), _school_year(y), num(f"school.infant.{y}", "dp1"), num(f"school.pupils.infant.over30.{y}", "int"),
                               num(f"school.ks2.{y}", "dp1"), num(f"school.pupils.ks2.over30.{y}", "int")] for y in iy]))
    out.append('<p class="small">Infant and key stage 2 figures start in January 2016 in the DfE data used here. A class over 30 in reception to year 2 can be lawful, '
               'for example when some pupils were admitted under the exceptions the rules allow, so these counts are not counts of unlawful classes.</p>')
    return out


# ---------------------------------------------------------------- holidays: spending and nights abroad

def holiday_spend_block(facts, num, d):
    """Spending on and length of holiday visits abroad (ONS Travel trends)."""
    hs = d["life_extra"]["holspend"]
    have = hs["years"]
    if not have:
        return []
    base = hs["base"]
    years = list(range(have[0], have[-1] + 1))
    last = have[-1]
    old = [y for y in have if y <= 2019]
    a, b = old[0], old[-1]
    out = ["<h3 id='holidays-spend'>How much is spent on holidays abroad, and for how long?</h3>"]
    stay_word = _word(_v(facts, f"hol.stay.{a}"), _v(facts, f"hol.stay.{b}"), up="got longer", down="got shorter", same="stayed the same length")
    spend_word = _word(_v(facts, f"hol.spendper.real.{a}"), _v(facts, f"hol.spendper.real.{b}"))
    out.append(f'<div class="answer"><p>In {last}, Great Britain residents spent {num(f"hol.spendbn.holiday.{last}", "bn1")} on holiday visits abroad, '
               f'which is {num(f"hol.spendper.{last}", "pounds")} per visit, and stayed an average of {num(f"hol.stay.{last}", "dp1")} nights per visit.</p>'
               f'<p>From {a} to {b} (UK residents, before the pandemic and the new method), the average holiday abroad {stay_word}, '
               f'from {num(f"hol.stay.{a}", "dp1")} to {num(f"hol.stay.{b}", "dp1")} nights, and spending per visit after inflation {spend_word}, '
               f'from {num(f"hol.spendper.real.{a}", "pounds")} to {num(f"hol.spendper.real.{b}", "pounds")} in {base} prices.</p></div>')
    br = [(years.index(y), t) for y, t in ((2024, "New method"), (2025, "Fully new method")) if y in years]
    ev = [(years.index(2020), "Covid-19")] if 2020 in years else []
    for title, fid, kind, unit, ymin, finding in (
            ("Spending per holiday visit abroad, after inflation", lambda y: f"hol.spendper.real.{y}", "pounds",
             f"£ per visit in {base} prices (CPIH). Up to 2023 UK residents; from 2024 Great Britain residents (new method)", 0,
             f"Before the pandemic, spending per holiday visit abroad after inflation {spend_word} between {a} and {b}"),
            ("Nights per holiday visit abroad", lambda y: f"hol.stay.{y}", "dp1",
             "Average nights per visit. Up to 2023 UK residents; from 2024 Great Britain residents (new method)", 0,
             f"Before the pandemic, the average holiday abroad {stay_word} between {a} and {b}")):
        vals = [_v(facts, fid(y)) if y in have else None for y in years]
        out.append(line_chart(title, [str(y) for y in years], [(title, vals, "a")], unit, breaks=br, split_breaks=True, ymin=ymin, kind=kind, num=num, events=ev,
                              ids=[[fid(y) if v is not None else None for y, v in zip(years, vals)]], point_labels=[str(y) for y in years], finding=finding))
    rows = []
    for y in years:
        if y not in have:
            rows.append([str(y), '<span class="missing">not available</span>', "", "", "", "", ""])
            continue
        rows.append([str(y), "UK" if y <= 2023 else ("GB, mixed methods" if y == 2024 else "GB"), num(f"hol.spendbn.holiday.{y}", "bn1"),
                     num(f"hol.spendper.{y}", "pounds"), num(f"hol.spendper.real.{y}", "pounds"), num(f"hol.nights.holiday.{y}", "millions"), num(f"hol.stay.{y}", "dp1")])
    out.append(details_table("Show holiday spending and nights for every year", "Holiday visits abroad: spending and nights",
                             ["Year", "Residents of", "Spending (cash)", "Per visit (cash)", f"Per visit ({base} prices)", "Nights", "Nights per visit"], rows))
    # The answer gives the figures; the two charts wait in the fold on a phone.
    out.append("<!--keepfold-->")
    out.append(f'<div class="limit"><p>Spending per visit and nights per visit are averages over every holiday visit, short city breaks and long trips alike, so they do not describe a typical holiday. '
               f'Spending is adjusted for inflation with UK consumer prices (CPIH); this does not allow for exchange rates or for prices in the countries visited. '
               f'2020 has no full-year figures because the survey was suspended, and 2021 holidays were few and unusual because of travel restrictions. '
               f'From 2024 a new method counts Great Britain residents (2024 mixes both), so 2024 and 2025 are not compared with earlier years: a gap may be the method.</p></div>')
    return out
