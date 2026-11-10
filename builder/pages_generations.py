"""Did parents have it easier than this generation? (John's question J12)

The page compares what the site can measure at the same age, in two years, and
says plainly what it cannot yet measure. It gives no overall verdict: "easier"
depends on which things are counted, and the measures move in different directions.

Every figure comes from a fact already in the build. Where two figures come from
different surveys or definitions they are not joined: home ownership for all households
is shown only for the English Housing Survey years, home ownership by age sets the 1991
Labour Force Survey beside the English Housing Survey with the difference stated, and
house prices against earnings start in 1999, the first year measured the same way.
"""

from .html import page, source_line, table, FOLD
from . import findings as F
from .pages_life import CAUSE, groups_chart
from .pages_life_extra import _chart
from .pages_age_pay import WORK_FIRST, pay_answer, pay_section, security_section
from .pages_life_expectancy import life_section

PAGE = "life/generations.html"
AFFORD_FIRST = (
    1999  # 1997 and 1998 earnings are weekly pay scaled up; not compared with later years
)
OWN_FIRST, OWN_LAST = 2008, 2024  # English Housing Survey: 2008-09 to 2024-25 (survey years)
OWN_AGE_THEN = 1991  # Labour Force Survey, by age of the head of household
OWN_AGE_GROUPS = [("25-34", "25 to 34"), ("35-44", "35 to 44")]
SCHOOL_FIRST = 2006  # first January class-size census in the explorer
AGES = [("18_24", "18 to 24"), ("25_34", "25 to 34"), ("35_49", "35 to 49")]
# The later year of each pair is fixed rather than the explorer's newest year: John's recorded
# J12 probes ask about 2025, and newer survey years are on the topic and year pages.
LAST = 2025


def _afford_last(facts):
    """The newest year with a house price to earnings ratio: house prices can lag the explorer's last year."""
    return max(
        y
        for y in range(AFFORD_FIRST, LAST + 1)
        if f"afford.ratio.ew.{y}" in facts and facts[f"afford.ratio.ew.{y}"].value is not None
    )


def _answer(facts, num):
    w_first, w_last = WORK_FIRST, LAST
    af = _afford_last(facts)
    return (
        f'<div class="answer"><p>No single answer: “easier” depends on what is measured. '
        f'Aged 25 to 34, a larger share were in work in {w_last} ({num(f"work.age.25_34.{w_last}", "pct")}) than in {w_first} ({num(f"work.age.25_34.{w_first}", "pct")}); '
        f'aged 18 to 24, {num(f"work.age.18_24.{w_last}", "pct")} against {num(f"work.age.18_24.{w_first}", "pct")}. '
        f'The middle-priced home in England and Wales has gone from {num(f"afford.ratio.ew.{AFFORD_FIRST}", "times2")} a year’s earnings to {num(f"afford.ratio.ew.{af}", "times2")} in {af}. '
        f'Owning in England: {num(f"house.owners.{OWN_FIRST}", "pct")} of households in {OWN_FIRST}-{str(OWN_FIRST + 1)[2:]}, {num(f"house.owners.{OWN_LAST}", "pct")} in {OWN_LAST}-{str(OWN_LAST + 1)[2:]}; '
        f'where the household’s main person was aged 25 to 34, {num(f"own.hrp.25-34.{OWN_AGE_THEN}", "pct0")} owned in {OWN_AGE_THEN} and {num(f"own.hrp.25-34.{OWN_LAST}", "pct0")} in {OWN_LAST}-{str(OWN_LAST + 1)[2:]}, from two different surveys. '
        f"University fees: up to £1,000 in 1998, paid up front; £9,535 for England in 2025-26. "
        f"State Pension age: 66 for people born in 1960, 68 for those born from 6 April 1978. "
        f'{pay_answer(num)}<a href="#same-age">Life expectancy at 30 is under Same age below</a>. '
        '<a href="tax-comparison.html">Tax at the same real pay: one hypothetical employee paid a smaller share in 2025-26 than in 1992-93</a>.</p></div>'
    )


def _same_age_rows(facts, num):
    rows = []
    for key, label in AGES:
        rows.append(
            [
                f"Aged {label}",
                num(f"work.age.{key}.{WORK_FIRST}", "pct"),
                num(f"work.age.{key}.{LAST}", "pct"),
            ]
        )
    return rows


def _owner_rows(facts, num):
    return [
        [
            "Households in England who own their home, all ages",
            num(f"house.owners.{OWN_FIRST}", "pct"),
            num(f"house.owners.{OWN_LAST}", "pct"),
        ]
    ]


def page_body(facts, d, num, sources):
    body = [
        '<p class="small"><a href="index.html">Everyday life, year by year</a></p>',
        '<h1 id="key-answer">Did parents have it easier than this generation?</h1>',
        _answer(facts, num),
        '<p class="note"><strong>Different people, not the same people.</strong> Each figure is for one age group in one year. '
        "It does not follow one person through their life.</p>",
        "<h2 id='what-easier-means'>What “easier” could mean</h2>",
        "<p>People mean different things by “easier”. This page separates them, so each can be read on its own:</p>",
        FOLD,
        "<ul><li>Getting work, and the kind of work available at a given age.</li>"
        "<li>Pay after inflation, at a given age.</li>"
        "<li>Buying a home, and the cost of a home compared with earnings.</li>"
        "<li>The cost of studying at university.</li>"
        "<li>Pensions, and what income people can expect when they stop work.</li>"
        "<li>The public services children use, such as school classes.</li>"
        "<li>How long people live.</li></ul>",
        "<h2 id='same-age'>Same age: work, pay, job security and life expectancy</h2>",
        _same_age_chart(facts, num),
        FOLD,
        table(
            f"Share of each age group in work, April to June, UK, {WORK_FIRST} and {LAST}",
            ["Age group", str(WORK_FIRST), str(LAST)],
            _same_age_rows(facts, num),
        ),
        "<p>Employment is the share of each age group who did any paid work in the survey week, including students with part-time jobs. "
        "The rate for 18 to 24 year olds is lower partly because many of them are studying. "
        'The survey has changed over the years, so read small differences with care; <a href="work.html#work-age">the work page</a> lists the changes. '
        '<a href="work.html#work-age">Employment by age, every year</a>.</p>',
        security_section(num, sources),
        pay_section(num, sources),
        life_section(num, sources),
        "<h2 id='housing-cost'>Buying a home, compared with earnings</h2>",
        "<p>The house price and earnings figures are for everyone, not for people of one age, so they show the position of the whole market. Home ownership around the age of 30 is further down this section.</p>",
        _afford_chart(facts, num),
        FOLD,
        table(
            f"Median house price ÷ median full-time earnings, England and Wales, {AFFORD_FIRST} and {_afford_last(facts)}",
            ["Measure", str(AFFORD_FIRST), str(_afford_last(facts))],
            [
                [
                    "Times a year’s earnings",
                    num(f"afford.ratio.ew.{AFFORD_FIRST}", "times2"),
                    num(f"afford.ratio.ew.{_afford_last(facts)}", "times2"),
                ]
            ],
        ),
        "<p>House prices are for the year to September. Earnings are for one full-time employee working in the area, before tax. "
        '<a href="house-prices.html">House prices and earnings, every year, with each region</a>.</p>',
        table(
            f"Share of households in England who own their home, {OWN_FIRST}-09 and {OWN_LAST}-25, English Housing Survey",
            [
                "Measure",
                f"{OWN_FIRST}-{str(OWN_FIRST + 1)[2:]}",
                f"{OWN_LAST}-{str(OWN_LAST + 1)[2:]}",
            ],
            _owner_rows(facts, num),
        ),
        f"<p>This is the share of all households, not of people at a given age. The English Housing Survey began in {OWN_FIRST}, so this row is not compared with earlier years. "
        f'<a href="housing.html">Owning and renting, every year</a>.</p>',
        "<h3 id='owning-at-30'>Owning a home around the age of 30</h3>",
        f'<p>The nearest measure is the age group 25 to 34. In {OWN_AGE_THEN}, {num(f"own.hrp.25-34.{OWN_AGE_THEN}", "pct0")} of households whose head was aged 25 to 34 owned their home. '
        f'In {OWN_LAST}-{str(OWN_LAST + 1)[2:]}, {num(f"own.hrp.25-34.{OWN_LAST}", "pct0")} of households whose reference person was aged 25 to 34 did. '
        f"On this measure, owning was less common in this age group in {OWN_LAST}-{str(OWN_LAST + 1)[2:]} than in {OWN_AGE_THEN}.</p>",
        '<div class="limit"><p><strong>Not people aged exactly 30.</strong> These are households, grouped by the age of one person in each, in a ten-year age group. '
        "They are not the share of all 30-year-olds who own a home, which no official table here gives. "
        f"The {OWN_AGE_THEN} figure is from the Labour Force Survey, which grouped households by the head of household (in a couple, the man); "
        "the later figure is from the English Housing Survey, which uses the household reference person (the person in whose name the home is owned or rented; where two people share that, the one with the higher income). "
        "ONS says the two pick a different person in around 10% of households, and that reference people tend to be slightly younger. England only.</p></div>",
        table(
            f"Households owning their home, by age of the household’s main person, England, {OWN_AGE_THEN} and {OWN_LAST}-{str(OWN_LAST + 1)[2:]}",
            [
                "Age group",
                f"{OWN_AGE_THEN} (Labour Force Survey, head of household)",
                f"{OWN_LAST}-{str(OWN_LAST + 1)[2:]} (English Housing Survey, household reference person)",
            ],
            [
                [
                    label,
                    num(f"own.hrp.{g}.{OWN_AGE_THEN}", "pct"),
                    num(f"own.hrp.{g}.{OWN_LAST}", "pct"),
                ]
                for g, label in OWN_AGE_GROUPS
            ],
        ),
        '<p><a href="house-prices.html#owners-by-age">Home ownership by age, every age group</a>.</p>',
        "<h2 id='schools'>Public services: school classes</h2>",
        table(
            f"Average primary class size, England, January {SCHOOL_FIRST} and {LAST}",
            ["Measure", str(SCHOOL_FIRST), str(LAST)],
            [
                [
                    "Pupils per class",
                    num(f"school.primary.{SCHOOL_FIRST}", "dp1"),
                    num(f"school.primary.{LAST}", "dp1"),
                ]
            ],
        ),
        "<p>These figures describe the classes in each year, not the classes the parents attended. The site holds no class size figures from before 2006. "
        '<a href="schools.html">Class sizes, every year</a>.</p>',
        "<h2 id='university'>University tuition fees</h2>",
        "<p>In 1998 the fee was up to £1,000 across the UK, paid up front rather than through a loan. The 2025-26 figure is the cap for England: £9,535.</p>",
        FOLD,
        table(
            "Tuition fee for a full-time undergraduate, 1998-99 and 2025-26",
            ["Measure", "1998-99", "2025-26"],
            [
                ["Fee, cash", num("fee.ft.1998", "pounds"), num("fee.ft.2025", "pounds")],
                [
                    "1998 fee in April 2025 prices (calculated)",
                    num("fee.ft.1998.2025", "pounds"),
                    num("fee.ft.2025", "pounds"),
                ],
            ],
        ),
        "<p>From 2006 students could borrow a tuition fee loan, repaid after graduation. "
        "The 1998 figure in 2025 prices uses the CPIH index, which the site uses elsewhere for real pay.</p>",
        source_line(sources, ["parl-cbp-tuition-fees", "parl-hansard-1998-tuition-fees"], up="../"),
        "<h2 id='pension-age'>State Pension age</h2>",
        "<p>People born in 1960 reach State Pension age at 66 years and 0 to 9 months, depending on the month of birth. "
        "For people born from 6 April 1978 it is 68 under current law.</p>",
        FOLD,
        table(
            "State Pension age under current law, by year of birth",
            ["Born in", "1960", "1990"],
            [
                [
                    "State Pension age",
                    f"66, plus {spa_range(facts)} months (depending on birth month)",
                    f"{int(facts['spa.months.1990'].value // 12)} years",
                ]
            ],
        ),
        "<p>The Pensions Act 2007 sets the rise from 67 to 68 for 2044 to 2046. "
        "The government has launched a third review of State Pension age, and a review could change the timetable for 68.</p>",
        source_line(sources, ["dwp-spa-timetable"], up="../"),
        "<h2 id='cannot-yet'>What this page cannot show yet</h2>",
        "<p>These comparisons need figures that the site does not yet hold. Each is listed so it can be added, from the source named, when it is available:</p>",
        "<ul>"
        "<li><strong>Student loans for living costs</strong>: maintenance loans and the total a student borrows, in each year since the 1990s.</li>"
        "<li><strong>Pension coverage</strong>: the share of people with a workplace or private pension, by year.</li>"
        "<li><strong>Tax at the same income</strong>: income tax and National Insurance for one income level, in each year.</li>"
        "</ul>",
        CAUSE,
        "<h2 id='about'>About these figures</h2>",
        FOLD,
        '<div class="limit"><p>Employment rates are for the UK, from the quarterly Labour Force Survey, April to June, seasonally adjusted. '
        "House prices and earnings are for England and Wales. Class sizes are for state-funded primary schools in England. "
        "Home ownership is from the English Housing Survey, which covers England only; the 1991 figures by age are from the Labour Force Survey, as published in the English Housing Survey 2008-09 report. "
        "Each measure is compared only with its own earlier figures, and changes are not calculated across any break in the survey or the definition.</p></div>",
        source_line(
            sources,
            [
                "ons-ybud",
                "ons-ybug",
                "ons-ybuj",
                "ons-affordability",
                "ehs-ft1101",
                "ehs-0809-annex-ch1",
                "ehs-annex-ch1",
                "ons-lfs-guide-household",
                "dfe-spc-2015-tables",
                "dfe_api",
            ],
            up="../",
        ),
    ]
    return "\n".join(body)


def spa_range(facts):
    """Months after 66 for people born in 1960, from the timetable's stated ages."""
    return f"0 to {int(facts['spa.months.1960.max'].value - facts['spa.months.1960.min'].value)}"


def _same_age_chart(facts, num):
    items = [(f"Aged {label}", (lambda k: lambda y: f"work.age.{k}.{y}")(k)) for k, label in AGES]
    return groups_chart(
        facts,
        "Share of each age group in work",
        items,
        "Per cent of each age group in work, April to June each year, United Kingdom",
        years=list(range(WORK_FIRST, LAST + 1)),
        ymin=0,
        kind="pct",
        num=num,
        finding=F.count("The employment rate", "age groups"),
    )


def _afford_chart(facts, num):
    years = list(range(AFFORD_FIRST, _afford_last(facts) + 1))
    return _chart(
        facts,
        num,
        "House prices as a multiple of earnings, England and Wales",
        years,
        [("England and Wales", lambda y: f"afford.ratio.ew.{y}", "a")],
        "Times a year’s earnings. House prices for the year to September; earnings of full-time employees, April",
        "times2",
        ymin=0,
        finding=F.trend("House prices as a multiple of earnings, England and Wales"),
    )


def generations_page(facts, d, num, sources):
    return page(
        PAGE,
        "Did parents have it easier than this generation?",
        page_body(facts, d, num, sources),
        "Compares people of the same age in different years on work, housing, schools and what the site cannot yet show.",
    )
