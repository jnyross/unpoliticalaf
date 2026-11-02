"""Topic-page sections for the three longer-run life measures in data_life_extra:
pay spread (earnings), house prices against earnings (housing) and jobs by
industry (work). Each returns a list of parts starting with an <h3>, which
topic_page() turns into its own section.
"""
from .html import details_table, esc, line_chart, table


def _v(facts, fid):
    f = facts.get(fid)
    return None if f is None else f.value


def _chart(facts, num, title, years, items, unit, kind, breaks=(), ymin=None, point_label=str):
    """A line chart over a measure's own years. items: (name, fid(year), style)."""
    series = [(name, [_v(facts, fid(y)) for y in years], style) for name, fid, style in items]
    ids = [[fid(y) if _v(facts, fid(y)) is not None else None for y in years] for _, fid, _ in items]
    br = [(years.index(y), text) for y, text in breaks if y in years and y != years[0]]
    return line_chart(title, [str(y) for y in years], series, unit, breaks=br, ymin=ymin, kind=kind, ids=ids, num=num,
                      point_labels=[point_label(y) for y in years])


# ---------------------------------------------------------------- earnings: how far apart is pay?

def spread_ref_year(sp, first):
    """Year to compare the latest with: the explorer's first year, but never before
    ONS's 2006 method change, so the headline comparison does not cross it."""
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
                      f"£ a week before tax, full-time employees, United Kingdom, April each year, in April {base} prices (CPIH). From 2006, after the survey’s last method change; the table also gives 2002 to 2005", "pounds",
                      breaks=sorted(sp["breaks"].items()), ymin=0))
    out.append(details_table("Show pay spread for every year", f"Gross weekly pay of full-time employees, United Kingdom, April each year",
                             ["Year", "Bottom tenth earn less than (cash)", "Median (cash)", "Top tenth earn more than (cash)", "Top line ÷ bottom line (times)",
                              f"Bottom line ({base} prices)", f"Top line ({base} prices)"],
                             [[str(y), num(f"spread.p10.{y}", "pounds"), num(f"spread.p50.{y}", "pounds"), num(f"spread.p90.{y}", "pounds"), num(f"spread.ratio.{y}", "dp1"),
                               num(f"spread.real.p10.{y}", "pounds"), num(f"spread.real.p90.{y}", "pounds")] for y in years]))
    out.append(f'<p class="small">The 10th and 90th percentiles are the pay of the employee one tenth of the way up the ladder and nine tenths of the way up. '
               f'They are lines on the ladder, not averages of the groups. Only full-time employees are counted: part-time workers and the self-employed are not, and pay is for one job before tax, '
               f'not household income. The ratio does not depend on inflation, because both lines are in the same year’s prices. '
               f'ONS notes breaks in the survey in 2004 and 2006 (method changes) and in 2011 and 2021 (new job coding). The chart starts in 2006 and marks 2011 and 2021. Small moves across these breaks may come from the change rather than from pay. {last} figures are provisional.</p>')
    return out


# ---------------------------------------------------------------- housing: house prices against earnings

AFFORD_PAGE = "life/house-prices.html"


def _the(n):
    return ("the " if n.split()[0] in ("North", "South", "East", "West") else "") + n


def _afford_answer(facts, num, d):
    af = d["life_extra"]["afford"]
    years = af["years"]
    first, last = years[0], years[-1]
    names = dict(af["places"])
    regions = [k for k, _ in af["places"] if k not in ("ew", "england", "wales")]
    peak = max(years, key=lambda y: (_v(facts, f"afford.ratio.ew.{y}"), y))
    hi = max(regions, key=lambda k: _v(facts, f"afford.ratio.{k}.{last}"))
    lo = min(regions, key=lambda k: _v(facts, f"afford.ratio.{k}.{last}"))
    peak_txt = (f' The highest ratio was {num(f"afford.ratio.ew.{peak}", "times2")} in {peak}.' if peak != last else " That was the highest since the series began.")
    return (f'<div class="answer"><p>In {last}, the middle-priced home sold in England and Wales cost {num(f"afford.price.ew.{last}", "pounds")}, '
            f'and the middle full-time employee working there earned {num(f"afford.earn.ew.{last}", "pounds")} a year before tax. '
            f'So the home cost {num(f"afford.ratio.ew.{last}", "times2")} a year’s earnings, compared with {num(f"afford.ratio.ew.{first}", "times2")} in {first}.{peak_txt}</p>'
            f'<p>The ratio differs a lot by place: in {last} it was {num(f"afford.ratio.{hi}.{last}", "times2")} in {esc(_the(names[hi]))} and {num(f"afford.ratio.{lo}.{last}", "times2")} in {esc(_the(names[lo]))}.</p></div>')


def afford_block(facts, num, d):
    """The short version on the housing page: the answer and a link to the full page."""
    first = d["life_extra"]["afford"]["years"][0]
    return ["<h3 id='housing-afford'>House prices compared with earnings</h3>", _afford_answer(facts, num, d),
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
                       "Times a year’s earnings. House prices for the year ending September; earnings of full-time employees working in the area, April", "times2", ymin=0))
    body.append(FOLD)
    body.append(details_table("Show house prices and earnings for every year", "England and Wales: median house price, median full-time annual earnings and the ratio",
                              ["Year", "Median house price", "Median full-time earnings (a year)", "Ratio (times a year’s earnings)"],
                              [[str(y), num(f"afford.price.ew.{y}", "pounds"), num(f"afford.earn.ew.{y}", "pounds"), num(f"afford.ratio.ew.{y}", "dp2")] for y in years]))
    mid = 2008 if 2008 in years else years[len(years) // 2]
    body.append("<h2 id='regions'>Each nation and region</h2>")
    body.append(table(f"Median house price ÷ median full-time earnings (times a year’s earnings), {first}, {mid} and {last}",
                      ["Place", str(first), str(mid), str(last)],
                      [[esc(n), num(f"afford.ratio.{k}.{first}", "dp2"), num(f"afford.ratio.{k}.{mid}", "dp2"), num(f"afford.ratio.{k}.{last}", "dp2")]
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


def industry_block(facts, num, d):
    """The short version on the work page: the answer and a link to the full page."""
    first = d["life_extra"]["jobs"]["years"][0]
    return ["<h3 id='work-industry'>Jobs by industry</h3>", _industry_answer(facts, num, d),
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
    out.append(f'<div class="answer"><p>No official statistic, published each year, gives the share of people who took a holiday: the travel surveys above count trips, not travellers. '
               f'The nearest yearly official figure answers a different question: could the household afford a week’s holiday away from home? '
               f'In the {last} survey, {num(f"holafford.all.{last}", "pct")} of people in the UK lived in a household that could not. '
               f'In {last}, {num(f"holafford.low.{last}", "pct")} of people in low-income households could not afford a week away, compared with {num(f"holafford.notlow.{last}", "pct")} of people in other households.</p>'
               + (f'<p>The survey changed in {" and ".join(str(c) for c in cuts)}, so only years within the same run ({run_text}) are compared: {"; ".join(moves)}.</p>' if moves else "")
               + '</div>')
    out.append(_chart(facts, num, "People whose household could not afford a week’s holiday away from home", years,
                      [("Low-income households", lambda y: f"holafford.low.{y}", "b"), ("Everyone", lambda y: f"holafford.all.{y}", "a"),
                       ("Other households", lambda y: f"holafford.notlow.{y}", "c")],
                      "% of people, United Kingdom, EU-SILC survey year", "pct", breaks=[(y, "Series break") for y in ha["breaks"]], ymin=0))
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
