"""Is immigration a good or a bad thing? What official evidence says, and where it cannot decide.

John's question (docs/johns-questions/questions.json, J2). The page does not give a verdict.
It shows the measurable parts, each as words quoted from an official publication with its
date, population and units, and it says plainly which parts depend on values.
"""

from .html import page, esc, table
from .explain import box


def _link(sources, key):
    s = sources[key]
    return f'<a href="{esc(s["page"])}">{esc(s["title"])}</a> ({esc(s["publisher"])})'


def _staff_nationality(num, sources):
    """J2.5: NHS and adult social care staff by nationality, two producers kept apart."""

    def nhs(key, kind="int"):
        return num(f"nhs.nat.hc.{key}.aug2026", kind), num(f"nhs.nat.fte.{key}.aug2026", kind)

    def care(key, kind):
        return [num(f"asc.nat.{key}.{s}.2025-26", kind) for s in ("all", "la", "ind", "dpr")]

    nhs_rows = [
        ("United Kingdom", *nhs("uk")),
        ("European Union", *nhs("eu")),
        ("Other European Economic Area", *nhs("eea")),
        ("Rest of the world", *nhs("row")),
        ("Not recorded", *nhs("unknown")),
        ("All staff (published total)", *nhs("all")),
        (
            "Share of staff with a recorded nationality who are not UK nationals",
            *nhs("nonuk.share", "pct"),
        ),
    ]
    care_rows = [
        ("Filled posts (estimate)", *care("posts", "int")),
        ("British", *care("british", "pct0")),
        ("EU (not British)", *care("eu", "pct0")),
        ("Outside the EU", *care("noneu", "pct0")),
        ("Not British (EU and outside the EU)", *care("nonbritish", "pct0")),
    ]
    return [
        "<h2>What share of NHS and adult social care staff in England are not UK nationals?</h2>",
        "<p>Two official producers publish these figures. They count different things on different dates, "
        "so the two figures cannot be added together into one share for both sectors.</p>",
        '<div class="answer"><p><strong>NHS, 31 August 2026:</strong> '
        f"{num('nhs.nat.hc.nonuk.share.aug2026', 'pct')} of staff with a recorded nationality were not UK nationals "
        f"({num('nhs.nat.hc.nonuk.aug2026', 'int')} of {num('nhs.nat.hc.known.aug2026', 'int')} people). "
        "<strong>Adult social care, 2025/26:</strong> "
        f"{num('asc.nat.nonbritish.all.2025-26', 'pct0')} of filled posts with a known nationality were held by people "
        "who are not British.</p></div>",
        "<p>Nationality is not the same as country of birth. These figures do not show whether or when anyone moved to the UK.</p>",
        "<h3>NHS hospital and community health services, 31 August 2026</h3>",
        "<p>NHS England counts staff directly employed by NHS trusts and other core organisations in England. "
        "GP practices and other primary care staff are counted in separate NHS workforce statistics, so they are not in these figures. "
        "Headcount counts people. Full time equivalent counts contracted hours, so someone working half time counts as 0.5.</p>",
        f"<p>Counted as full time equivalent, the share was {num('nhs.nat.fte.nonuk.share.aug2026', 'pct')}.</p>",
        "<p>Staff report their own nationality, and some choose not to. "
        f"{num('nhs.nat.hc.unknown.aug2026', 'int')} people ({num('nhs.nat.hc.unknown.share.aug2026', 'pct')} of all staff) "
        "had no recorded nationality. They are left out of the share: they are not counted as UK or non-UK nationals, "
        "and they are not in the total the share is worked out from.</p>",
        table(
            "NHS staff by nationality group, 31 August 2026",
            ["Nationality group", "Headcount (people)", "Full time equivalent"],
            nhs_rows,
        ),
        '<p class="small">The published headcount total is slightly lower than the sum of the groups, because some '
        "staff work in more than one role. The share uses the sum of the four recorded groups.</p>",
        "<h3>Adult social care, 2025/26</h3>",
        "<p>Skills for Care estimates the adult social care workforce from employer records. The figures are "
        "filled posts, not people: one person can hold more than one post. They cover local authorities, independent "
        "employers and people who employ their own care staff with direct payments. Since 2024/25 they have not "
        "included adult social care roles employed by the NHS.</p>",
        "<p>The estimates are rounded, and the shares are published to the whole per cent. Posts with no recorded "
        "nationality are left out of the shares before Skills for Care works them out, and it does not publish how many there are. "
        "The data are for September 2025 (local authorities), March 2026 (independent employers) and February 2026 "
        "(direct payment recipients).</p>",
        table(
            "Adult social care filled posts by nationality, 2025/26",
            [
                "Nationality",
                "All sectors",
                "Local authorities",
                "Independent employers",
                "Direct payment recipients",
            ],
            care_rows,
        ),
        "<h3>Who publishes these figures</h3>",
        "<p>NHS England publishes the NHS figures as part of the Government Statistical Service. "
        "Skills for Care is a charity that became an official statistics producer in 2023. Its report on staff employed by "
        "local authority adult social services departments has been accredited official statistics since February 2025. "
        "The report these nationality estimates come from does not say they are accredited.</p>",
    ]


def immigration_page(facts, d, num, sources):
    body = [
        "<h1>Is immigration a good or a bad thing?</h1>",
        '<div class="answer"><p><strong>The site does not answer that question, because the answer depends on what you value.</strong> '
        "It shows what official evidence says about the parts that can be measured: how many people move to the UK, "
        "their effect on public money, how they relate to public services, and their effect on the economy. "
        "Where official estimates differ, the range is shown.</p></div>",
        "<h2>How many people move to the UK?</h2>",
        "<p>Official figures count people who come to live in the UK for 12 months or more, minus those who leave for "
        "12 months or more. The latest figures are for the year ending December 2025.</p>",
        box("imm-net-migration", sources, heading="h3"),
        "<h2>What do migrants pay and cost in public money?</h2>",
        "<p>Estimates depend on the group of migrants and the visa route. The Migration Advisory Committee (MAC) "
        "models lifetime taxes and public spending for one route, the Partner route of the Family visa. It does not "
        "give a single answer for all migrants.</p>",
        box("imm-mac-partner", sources, heading="h3"),
        box("imm-obr-time", sources, heading="h3"),
        "<h2>How do migrants relate to public services?</h2>",
        "<p>The official sources the site uses do not give a measured figure for how much public services migrants use. "
        "The Office for Budget Responsibility (OBR) explains how its forecast treats them: public-service spending is "
        "set by the government, not by a fixed link to the number of people.</p>",
        box("imm-obr-services", sources, heading="h3"),
        "<h2>What does migration do to the economy?</h2>",
        box("imm-obr-gdp", sources, heading="h3"),
        "<h2>How much could the answer change?</h2>",
        "<p>The OBR has tested what happens if net migration were 200,000 a year higher or lower than its forecast. "
        "The results depend on whether public spending rises to match the extra population.</p>",
        box("imm-obr-scenarios", sources, heading="h3"),
        "<h2>What drove recent population growth?</h2>",
        f"<p>In the year to mid-2025 the UK population grew by {num('mye.change.2025', 'int')} people. "
        f"The main reason was net international migration: {num('mye.netmig.2025', 'int')} people. "
        f"Natural change (births minus deaths) added {num('mye.natural.2025', 'int')}, from {num('mye.births.2025', 'int')} births and {num('mye.deaths.2025', 'int')} deaths.</p>",
        '<p class="small">Source: ONS mid-year population estimates for the UK, year to mid-2025. Estimates are rounded and do not add exactly to the total change.</p>',
        *_staff_nationality(num, sources),
        "<h2>What the site does not yet show</h2>",
        "<ul>"
        "<li>A measured figure for how much public services migrants use, as opposed to what the OBR assumes.</li>"
        "</ul>",
        "<h2>Where values come in</h2>",
        "<p>The figures above cannot settle these questions. They depend on what you value and how you weigh it:</p>"
        "<ul>"
        "<li>How much weight to give public money compared with other effects of migration.</li>"
        "<li>How to judge the effect of migration on particular places, communities and public services.</li>"
        "<li>What level of migration is right for the country.</li>"
        "</ul>",
        "<h2>Sources</h2>",
        "<ul>"
        f"<li>{_link(sources, 'explain-ons-ltim-dec2025')}</li>"
        f"<li>{_link(sources, 'explain-mac-annual-2025')}</li>"
        f"<li>{_link(sources, 'explain-obr-migration-fiscal')}, first published March 2024</li>"
        f"<li>{_link(sources, 'explain-obr-migration-gdp')}, March 2026</li>"
        f"<li>{_link(sources, 'ons-mye-uk-mid2025')}</li>"
        f"<li>{_link(sources, 'nhs-hchs-workforce-aug26')}</li>"
        f"<li>{_link(sources, 'nhs-hchs-dqa-aug26')}</li>"
        f"<li>{_link(sources, 'sfc-asc-appendix-2026')}</li>"
        f"<li>{_link(sources, 'sfc-state-2026')}</li>"
        f"<li>{_link(sources, 'sfc-method-jun26')}</li>"
        "</ul>",
    ]
    return page(
        "immigration.html",
        "Is immigration a good or a bad thing?",
        "\n".join(body),
        description="What official evidence says about immigration’s effect on public money, public services and the economy, and where the evidence cannot decide.",
    )
