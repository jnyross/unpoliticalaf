"""Everyday life before 2008: the longer series, and one page for each earlier year.

Every topic in the year-by-year explorer has figures from 2008, except holidays,
which start in 2009. Some official series reach
further back: the employment rate from 1971, tenure in England from 1981, visits
abroad from 1980, pay from 2002 and class sizes from 2006. Each is shown with its
own survey, and changes are only calculated within a stretch measured the same way.
Years with no published figure stay empty.
"""
from .data import YEARS, EARLY_YEARS, AGE_SERIES
from .html import page, table, details_table, line_chart, source_line, spark, esc, _join
from . import pages_life as L
from . import findings as F

LAST = YEARS[-1]
ALL = EARLY_YEARS + YEARS

# The first year each topic's longer series reaches.
FIRST_YEAR = L.FIRST_YEAR


# ONS: methods changed in 2004 and 2006, and job coding in 2011 and 2021 (see pages_life.earn_basis).
earn_method = L.earn_basis


# Each long-run measure: key, topic, label, fact-id function, display kind, change style,
# period function, comparability group (None = one series), last year of the series (None = latest).
LONG = [
    ("work.rate", "work", "Employment rate, ages 16 to 64", lambda y: f"work.rate.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None, None),
    ("work.men", "work", "Employment rate, men 16 to 64", lambda y: f"work.men.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None, None),
    ("work.women", "work", "Employment rate, women 16 to 64", lambda y: f"work.women.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None, None),
    ("work.level", "work", "People in work, aged 16 and over", lambda y: f"work.level.{y}", "millions_people", "pct", lambda y: f"Apr–Jun {y}", None, None),
    ("work.pt", "work", "Workers who work part-time", lambda y: f"work.ptshare.{y}", "pct", "pp", lambda y: f"Apr–Jun {y}", None, None),
] + [
    (f"work.age.{k}", "work", f"Employment rate, ages {label}", (lambda k: lambda y: f"work.age.{k}.{y}")(k), "pct", "pp", lambda y: f"Apr–Jun {y}", None, None)
    for k, label, _ in AGE_SERIES
 ] + [
    ("work.ind.manuf", "work", "Share of jobs in manufacturing", lambda y: f"jobs.share.C.{y}", "pct", "pp", lambda y: f"June {y}", None, None),
    ("work.ind.health", "work", "Share of jobs in health and social work", lambda y: f"jobs.share.Q.{y}", "pct", "pp", lambda y: f"June {y}", None, None),
] + [
    ("earn.ft", "earnings", "Median weekly pay, full-time employees (April 2025 prices)", lambda y: f"earn.real.ft.{y}", "pounds", "pct", lambda y: f"April {y}", earn_method, None),
    ("earn.ftcash", "earnings", "Median weekly pay, full-time employees (cash, at the time)", lambda y: f"earn.ft.{y}", "pounds", "pct", lambda y: f"April {y}", earn_method, None),
    ("earn.men", "earnings", "Full-time men (April 2025 prices)", lambda y: f"earn.real.ft_men.{y}", "pounds", "pct", lambda y: f"April {y}", earn_method, None),
    ("earn.women", "earnings", "Full-time women (April 2025 prices)", lambda y: f"earn.real.ft_women.{y}", "pounds", "pct", lambda y: f"April {y}", earn_method, None),
    ("earn.pt", "earnings", "Part-time employees (April 2025 prices)", lambda y: f"earn.real.pt.{y}", "pounds", "pct", lambda y: f"April {y}", earn_method, None),
    ("earn.spread", "earnings", "Full-time pay: top-tenth line ÷ bottom-tenth line", lambda y: f"spread.ratio.{y}", "times", "pct", lambda y: f"April {y}", earn_method, None),
    ("house.afford", "housing", "Median house price ÷ median full-time earnings, England and Wales", lambda y: f"afford.ratio.ew.{y}", "times2", "pct", lambda y: str(y), None, None),
    ("house.lfs.outright", "housing", "Households that own outright", lambda y: f"house.lfs.outright.{y}", "pct", "pp", lambda y: f"{y}, Labour Force Survey", None, 2008),
    ("house.lfs.mortgage", "housing", "Households buying with a mortgage", lambda y: f"house.lfs.mortgage.{y}", "pct", "pp", lambda y: f"{y}, Labour Force Survey", None, 2008),
    ("house.lfs.social", "housing", "Households renting from a council or housing association", lambda y: f"house.lfs.social.{y}", "pct", "pp", lambda y: f"{y}, Labour Force Survey", None, 2008),
    ("house.lfs.private", "housing", "Households renting privately", lambda y: f"house.lfs.private.{y}", "pct", "pp", lambda y: f"{y}, Labour Force Survey", None, 2008),
    ("hol.ips.all", "holidays", "Visits abroad by UK residents, all purposes", lambda y: f"hol.ips.all.{y}", "millions", "pct", lambda y: f"Jan–Dec {y}", None, 2023),
    ("hol.ips.per100", "holidays", "Visits abroad per 100 UK residents, all purposes", lambda y: f"hol.ips.per100.{y}", "int", "pct", lambda y: f"Jan–Dec {y}", None, 2023),
    ("school.primary", "schools", "Average class size, primary schools", lambda y: f"school.primary.{y}", "dp1", "abs", lambda y: f"January {y}", None, None),
    ("school.secondary", "schools", "Average class size, secondary schools", lambda y: f"school.secondary.{y}", "dp1", "abs", lambda y: f"January {y}", None, None),
]

SOURCES = {
    "work": ["ons-lf24", "ons-mgsv", "ons-lf25", "ons-mgrz", "ons-ycbe", "ons-ycbh", "ons-ybud", "ons-ybug", "ons-ybuj", "ons-lf2u", "ons-lfk6", "explain-ons-lfs-qmi", "ons-jobs02"],
    "earnings": ["nomis-ashe-resident", "nomis-ashe-percentiles", "ons-l522", "ons-ashe-qmi"],
    "housing": ["ehs-ft1101", "ons-affordability"],
    "holidays": ["ons-ott-timeseries", "ons-ukpop"],
    "schools": ["dfe-spc-2015-tables"],
}

# What changes before 2008, in plain words. Each is drawn from the source's own notes.
LIMITS = {
    "work": ("The Labour Force Survey began in 1973. It ran every two years until 1983 and once a year from 1984 to 1991, and it has run every quarter "
             "since spring 1992 (ONS, Labour Force Survey quality and methodology information). So the April to June figures before 1992 are not all "
             "from a survey carried out in that quarter, and 1971 and 1972 come before the survey began. ONS publishes them as one series from 1971; "
             "read the early years as the long-run pattern, not exact year-to-year moves. Part-time and age-group figures start in 1992. "
             "Jobs by industry come from a different source, ONS workforce jobs, which counts jobs rather than people, every June from 1978."),
    "earnings": ("Pay comes from the Annual Survey of Hours and Earnings, which replaced the New Earnings Survey in 2004. ONS says changes to its methods "
                 "caused breaks in the series in 2004, 2006 and 2011, and job coding changed again in 2021. Changes are only worked out between years "
                 "measured the same way: 2002 and 2003, 2004 and 2005, 2006 to 2010, 2011 to 2020, and 2021 onwards. The earlier "
                 "New Earnings Survey is not used here. Prices are adjusted with CPIH, the same index used for later years."),
    "housing": ("Before the English Housing Survey began in 2008-09, tenure in England was measured by the Labour Force Survey: the Department of the "
                "Environment's housing questions for 1981, 1984, 1988 and 1991, then the ONS Labour Force Survey every year from 1992 to 2008. Those are "
                "calendar years, and the English Housing Survey uses survey years (April to March) and a different sample, so the two are shown side by side "
                "but changes are not calculated between them. In 2008 both measured tenure, so the table shows how close they were. Figures for 1997 to 2008 "
                "use reweighted Labour Force Survey data from August 2008 (note in table FT1101). The table splits council and housing association renting "
                "only from 2008-09. There are no figures for the years between 1981, 1984, 1988 and 1991. House prices compared with earnings cover "
                "England and Wales from 1997; ONS says the 1997 and 1998 earnings are weekly pay scaled up to a year, so they are not directly comparable with later years."),
    "holidays": ("Before 2009 the holiday-only figures on this page are not in the tables used here. The longer series counts every visit abroad by UK "
                 "residents, whatever the purpose: holidays, visiting friends or family, business and other trips. It comes from the International "
                 "Passenger Survey, the same survey behind the holiday figures up to 2023. From 2024 visits abroad are counted for Great Britain residents "
                 "with a new method, so the series stops at 2023. 2020 and 2021 were cut short by pandemic travel restrictions. These are counts of visits, "
                 "not of people: one person can make several visits a year."),
    "schools": ("Class sizes for January 2006 and 2007 come from the same Department for Education table as 2008 to 2015, on the same definition "
                "(classes taught by one teacher in state-funded schools in England). Earlier years are not in the tables used here."),
}

ANCHOR = "history"


def _has(facts, fid):
    return fid in facts and facts[fid].value is not None


def latest_comparable(facts, m, y):
    """The latest year measured the same way as y, or None."""
    group, end = m[7], m[8]
    ys = [o for o in ALL if o > y and (end is None or o <= end) and _has(facts, m[3](o)) and (group is None or group(o) == group(y))]
    return ys[-1] if ys else None


def school_years(facts, first):
    """Class-size years from first, plus a January census newer than the explorer's range."""
    return [y for y in ALL if y >= first] + [y for y in (LAST + 1,) if _has(facts, f"school.primary.{y}") and _has(facts, f"school.secondary.{y}")]


def chart(facts, num, topic):
    """The longer chart for one topic, from its first year to its last."""
    first = FIRST_YEAR[topic]
    if topic == "work":
        years = [y for y in ALL if y >= first]
        items = [("Men", lambda y: f"work.men.{y}", "a"), ("Women", lambda y: f"work.women.{y}", "b")]
        return _line(facts, num, "Employment rate since 1971, men and women", years, items,
                     "Per cent of people aged 16 to 64 in work, April to June each year, United Kingdom. Before 1992 the survey was not quarterly",
                     "pct", events=[(years.index(1992), "Quarterly survey from 1992")],
                     finding=F.narrowing("The gap between men's and women's employment rates", lambda d: f"{d:.0f} points"))
    if topic == "earnings":
        years = [y for y in ALL if y >= first]
        items = [("Men", lambda y: f"earn.real.ft_men.{y}", "a"), ("Women", lambda y: f"earn.real.ft_women.{y}", "b")]
        breaks = [(years.index(y), t) for y, t in ((2004, "Method change"), (2006, "Method change"), (2011, "Jobs recoded"), (2021, "Jobs recoded"))]
        return _line(facts, num, "Median full-time weekly pay since 2002, after inflation", years, items,
                     "£ a week before tax, April each year, in April 2025 prices (adjusted with CPIH, the official consumer prices index that includes housing costs), United Kingdom. The lines break at each change to the survey's method (2004 and 2006) and each time it changed the codes it uses to sort jobs into types (2011 and 2021)", "pounds", breaks=breaks,
                     split=True, finding=F.narrowing("After inflation, the gap between men's and women's median full-time pay", lambda d: f"£{d:,.0f} a week", which="last"))
    if topic == "housing":
        years = list(range(first, 2025))
        def pick(key):
            return lambda y: f"house.lfs.{key}.{y}" if y < 2008 else f"house.{key}.{y}"
        items = [("Own outright", pick("outright")), ("Own with a mortgage", pick("mortgage")),
                 ("Rent from council or housing association", pick("social")), ("Rent privately", pick("private"))]
        return L.groups_chart(facts, "Owning and renting in England since 1981", items,
                              "Per cent of households in England. Up to 2007 Labour Force Survey, calendar years; from 2008-09 English Housing Survey, survey years, so the lines break there",
                              years=years, breaks=[(years.index(2008), "New survey")], split_breaks=True, ymin=0, kind="pct", num=num,
                              point_label=lambda y: str(y) if y < 2008 else L.sy(y), finding=F.moves(L.TENURE_WORDS, which="first"))
    if topic == "holidays":
        years = list(range(first, 2024))
        items = [("Visits abroad per 100 residents", lambda y: f"hol.ips.per100.{y}", "a")]
        return _line(facts, num, "Visits abroad by UK residents since 1980, per 100 residents", years, items,
                     "Visits abroad for any purpose, per 100 UK residents, January to December, International Passenger Survey", "int", ymin=0,
                     events=[(years.index(2020), "Covid")], finding=F.trend("Visits abroad per 100 residents", which="all"))
    if topic == "schools":
        years = school_years(facts, first)
        items = [("Primary", lambda y: f"school.primary.{y}", "a"), ("Secondary", lambda y: f"school.secondary.{y}", "b")]
        return _line(facts, num, "Average class size in England since 2006", years, items,
                     "Pupils per class, January school census, state-funded schools in England", "dp1", ymin=15, finding=L.CLASS_FINDING)
    return ""


def _line(facts, num, title, years, items, unit, kind, breaks=(), split=False, ymin=None, events=(), point_label=str, finding=None):
    series = [(name, [L._val(facts, fid(y)) for y in years], style) for name, fid, style in items]
    ids = [[fid(y) if L._val(facts, fid(y)) is not None else None for y in years] for _, fid, _ in items]
    scale = 1000 if kind == "millions" else 1
    return line_chart(title, [str(y) for y in years], series, unit, breaks=breaks, split_breaks=split, ymin=ymin, scale=scale,
                      kind=kind, ids=ids, num=num, events=events, point_labels=[point_label(y) for y in years], finding=finding)


def table_for(facts, num, topic):
    """Every year's figures for the topic's longer series, in one table."""
    first = FIRST_YEAR[topic]
    miss = "<span class='missing'>no figure</span>"

    def cell(fid, kind):
        return num(fid, kind) if _has(facts, fid) else miss
    if topic == "work":
        rows = [[str(y), cell(f"work.rate.{y}", "pct"), cell(f"work.men.{y}", "pct"), cell(f"work.women.{y}", "pct"), cell(f"work.level.{y}", "millions_people"),
                 cell(f"work.ptshare.{y}", "pct")] for y in ALL if y >= first]
        return details_table("Show work figures for every year since 1971", "Work, United Kingdom, April to June each year",
                             ["Year", "Employment rate 16-64", "Men", "Women", "People in work", "Part-time share"], rows)
    if topic == "earnings":
        rows = [[str(y), earn_method(y), cell(f"earn.ft.{y}", "pounds"), cell(f"earn.real.ft.{y}", "pounds"), cell(f"earn.real.ft_men.{y}", "pounds"),
                 cell(f"earn.real.ft_women.{y}", "pounds"), cell(f"earn.real.pt.{y}", "pounds")] for y in ALL if y >= first]
        return details_table("Show pay for every year since 2002", "Median gross weekly pay, United Kingdom, April each year",
                             ["Year", "Survey method", "Full-time (cash)", "Full-time (2025 prices)", "Full-time men", "Full-time women", "Part-time"], rows)
    if topic == "housing":
        rows = [[f"{y} (Labour Force Survey)", cell(f"house.lfs.outright.{y}", "pct"), cell(f"house.lfs.mortgage.{y}", "pct"),
                 cell(f"house.lfs.social.{y}", "pct"), cell(f"house.lfs.private.{y}", "pct")] for y in sorted(facts_years(facts, "house.lfs.private"))]
        rows += [[f"{L.sy(y)} (English Housing Survey)", cell(f"house.outright.{y}", "pct"), cell(f"house.mortgage.{y}", "pct"),
                  cell(f"house.social.{y}", "pct"), cell(f"house.private.{y}", "pct")] for y in YEARS if _has(facts, f"house.private.{y}")]
        return details_table("Show tenure for every year since 1981", "Housing tenure, England, % of households",
                             ["Year and survey", "Own outright", "Mortgage", "Social rent", "Private rent"], rows)
    if topic == "holidays":
        rows = [[str(y), cell(f"hol.ips.all.{y}", "millions"), cell(f"hol.ips.per100.{y}", "int")] for y in range(first, 2024)]
        return details_table("Show visits abroad for every year since 1980", "Visits abroad by UK residents, all purposes",
                             ["Year", "Visits abroad", "Per 100 residents"], rows)
    if topic == "schools":
        rows = [[str(y), f"{y - 1}/{str(y)[2:]}", cell(f"school.primary.{y}", "dp1"), cell(f"school.secondary.{y}", "dp1")] for y in school_years(facts, first)]
        return details_table("Show class sizes for every year since 2006", "Average class size, England, January census",
                             ["January census", "School year", "Primary", "Secondary"], rows)
    return ""


def facts_years(facts, prefix):
    return [y for y in ALL if _has(facts, f"{prefix}.{y}")]


def answer(facts, num, topic):
    """One or two sentences on the longer view, built only from shown figures."""
    if topic == "work":
        a = 1971
        return (f"In April to June {a}, {num(f'work.men.{a}', 'pct')} of men and {num(f'work.women.{a}', 'pct')} of women aged 16 to 64 were in work. "
                f"In {LAST} the figures were {num(f'work.men.{LAST}', 'pct')} and {num(f'work.women.{LAST}', 'pct')}. "
                f"The share for everyone aged 16 to 64 changed by {L.change_cell(facts, num, f'work.rate.{a}', f'work.rate.{LAST}', 'pp', 'pct')} over the whole period.")
    if topic == "earnings":
        runs = L.same_basis_runs(facts, lambda y: f"earn.real.ft.{y}", [y for y in ALL if y >= 2006], earn_method)
        parts = [f"from April {a} to April {b} by {L.change_cell(facts, num, f'earn.real.ft.{a}', f'earn.real.ft.{b}', 'pct', 'pounds')}" for a, b in runs]
        return (f"In April 2002 the middle full-time employee earned {num('earn.ft.2002', 'pounds')} a week, which is {num('earn.real.ft.2002', 'pounds')} in April 2025 prices. "
                f"Because the survey's methods changed in 2004 and 2006, that figure is shown for the record but not compared with later years. "
                f"The survey also changed how it codes jobs in 2011 and 2021, so pay is compared only within each stretch. After inflation, full-time pay changed "
                + _join(parts) + ".")
    if topic == "housing":
        return (f"In 1981, {num('house.lfs.owners.1981', 'pct0')} of households in England owned their home and {num('house.lfs.private.1981', 'pct0')} rented privately. "
                f"By 2008, on the same survey, it was {num('house.lfs.owners.2008', 'pct0')} and {num('house.lfs.private.2008', 'pct0')}. "
                f"The English Housing Survey, which starts in 2008-09, found {num('house.owners.2008', 'pct0')} and {num('house.private.2008', 'pct0')} that year.")
    if topic == "holidays":
        return (f"In 1980 UK residents made {num('hol.ips.all.1980', 'millions')} visits abroad for any purpose, about {num('hol.ips.per100.1980', 'int')} for every 100 residents. "
                f"In 2019, before the pandemic, they made {num('hol.ips.all.2019', 'millions')}, about {num('hol.ips.per100.2019', 'int')} for every 100 residents.")
    if topic == "schools":
        return (f"In January 2006 the average class had {num('school.primary.2006', 'dp1')} pupils in English state primary schools and "
                f"{num('school.secondary.2006', 'dp1')} in secondary schools.")
    return ""


def block(facts, num, sources, topic):
    """The 'Before 2008' section of a topic page."""
    first = FIRST_YEAR[topic]
    out = [f"<h3 id='{ANCHOR}'>Before 2008: since {first}</h3>",
           f'<div class="answer"><p>{answer(facts, num, topic)}</p></div>',
           chart(facts, num, topic), table_for(facts, num, topic)]
    out.append(f'<div class="limit"><p>{esc(LIMITS[topic])}</p></div>')
    out.append(f'<p class="small" id="early-{topic}">Pick an earlier year:</p><ul class="yearnav" aria-labelledby="early-{topic}">{early_links("", topic)}</ul>')
    out.append(source_line(sources, [s for s in SOURCES[topic] if s in sources], up="../"))
    return out


def early_links(up, topic=None):
    years = [y for y in EARLY_YEARS if topic is None or y >= FIRST_YEAR[topic]]
    return "".join(f'<li><a href="{up}{y}.html">{y}</a></li>' for y in years)


def _topic_rows(facts, num, topic, y):
    rows = []
    for m in LONG:
        if m[1] != topic or not _has(facts, m[3](y)):
            continue
        key, _, label, fid, kind, style, period, group, end = m
        o = latest_comparable(facts, m, y)
        if o is None:
            later = "<span class='missing'>no later year measured the same way</span>"
            change = ""
        else:
            later = f"{num(fid(o), kind)} ({esc(period(o))})"
            change = L.change_cell(facts, num, fid(y), fid(o), style, kind)
        per = esc(period(y)) + (f" ({esc(group(y))})" if group else "")
        rows.append([esc(label), f"{num(fid(y), kind)}<br><span class='small'>{per}</span>", later, change])
    return rows


def early_spark(facts, num, topic, y):
    """Where year y sits in the topic's longest measure, as a small dot chart of every year."""
    m = next((m for m in LONG if m[1] == topic and _has(facts, m[3](y))), None)
    if not m:
        return ""
    _, _, label, fid, kind, _, _, group, end = m
    years = [o for o in ALL if (end is None or o <= end)]
    pts = [(o, facts[fid(o)].value if _has(facts, fid(o)) else None) for o in years]
    have = [(o, v) for o, v in pts if v is not None]
    first = have[0][0]
    pts = [(o, v) for o, v in pts if o >= first]
    last = pts[-1][0]
    aria = f"Dot chart of {label.lower()} for each year from {first} to {last}, with {y} shown as a larger dark dot. The caption gives the values."
    svg = spark(pts, aria, highlight=y, group=group, axis=(first, last), kind=kind)
    lo = min(have, key=lambda t: t[1])
    hi = max(have, key=lambda t: t[1])
    split = group if group and len({group(o) for o, _ in pts}) > 1 else None
    cap = (f"<strong>{esc(label)}</strong>, {first} to {last}. The dark dot is {y}: {num(fid(y), kind)}{F.place(have, y, split)}. "
           f"The scale runs from {num(fid(lo[0]), kind)} ({lo[0]}) to {num(fid(hi[0]), kind)} ({hi[0]}) and does not start at zero.")
    if len(have) < len(pts):
        cap += " Years with no figure have no dot."
    if group and len({group(o) for o, _ in pts}) > 1:
        cap += " The dashed line marks a change of definition, so dots either side are not joined."
    return f'<figure class="yearspark">{svg}<figcaption>{cap}</figcaption></figure>'


def early_year_page(facts, d, num, sources, y):
    """One earlier year: the figures that reach back this far, each against the latest year measured the same way."""
    up = "../"
    body = [f"<h1>Everyday life in {y}</h1>"]
    prev_l = f'<a href="{y - 1}.html">← {y - 1}</a>' if y > EARLY_YEARS[0] else "<span></span>"
    body.append(f'<nav class="pager" aria-label="Previous and next year">{prev_l}<a href="{y + 1}.html">{y + 1} →</a></nav>')
    body.append(f'<nav aria-label="Choose a year">{L.year_links(y, "", strip=True)}</nav>')
    have = [t for t, _, _ in L.TOPICS if any(m[1] == t and _has(facts, m[3](y)) for m in LONG)]
    names = _join([dict((k, t) for k, t, _ in L.TOPICS)[t].lower() for t in have]) if have else ""
    body.append(f'<div class="answer"><p>Fewer official figures reach back to {y}. '
                + (f"This page shows those that do, for {esc(names)}, each beside the latest year measured the same way. " if have else "")
                + f'Work, earnings, housing and class sizes have figures from 2008, and holidays from 2009: see <a href="2008.html">2008</a> or <a href="2009.html">2009</a>.</p></div>')
    body.append(L.compare_with(y))
    for key, title, _scope in L.TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        rows = _topic_rows(facts, num, key, y)
        if not rows:
            first = FIRST_YEAR[key]
            why = (f"the {title.lower()} figures used here start in {first}" if y < first else f"there is no {title.lower()} figure for {y} in the tables used here")
            body.append(f'<p class="missing">Not available: {esc(why)}.</p>')
            body.append(f'<p class="small"><a href="{key}.html#{ANCHOR}">{esc(title)} before 2008</a></p>')
            continue
        body.append(early_spark(facts, num, key, y))
        body.append(table(f"{title}: {y} and the latest year measured the same way", ["Measure", str(y), "Latest comparable year", "Change"], rows))
        body.append(f'<div class="limit"><p>{esc(LIMITS[key])}</p></div>')
        body.append(f'<p class="small"><a href="{key}.html#{ANCHOR}">{esc(title)} in every year since {FIRST_YEAR[key]}</a></p>')
        body.append(source_line(sources, [s for s in SOURCES[key] if s in sources], up=up))
    body.append(f'<h2 id="compare">Compare {y} with another year</h2>')
    body.append(L.compare_form("", y, LAST))
    body.append(L.CAUSE)
    return page(f"life/{y}.html", f"Everyday life in {y}", "\n".join(body),
                f"The official figures on work, pay, housing, travel abroad and class sizes in the UK that reach back to {y}.", scripts=L.COMPARE_JS, toc_after_first=True)
