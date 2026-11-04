"""Is immigration a good or a bad thing? What official evidence says, and where it cannot decide.

John's question (docs/johns-questions/questions.json, J2). The page does not give a verdict.
It shows the measurable parts, each as words quoted from an official publication with its
date, population and units, and it says plainly which parts depend on values.
"""
from .html import page, esc
from .explain import box


def _link(sources, key):
    s = sources[key]
    return f'<a href="{esc(s["page"])}">{esc(s["title"])}</a> ({esc(s["publisher"])})'


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
        "<p>Official estimates of public-service use by migrants are not on this page yet. The Office for Budget "
        "Responsibility (OBR) explains how its forecast treats them.</p>",
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

        "<h2>What the site does not yet show</h2>",
        "<ul>"
        "<li>How many NHS and adult social care staff are non-UK nationals. The official figures are in spreadsheets "
        "published with the NHS workforce statistics, and the site has not yet taken them.</li>"
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
        "</ul>",
    ]
    return page(
        "immigration.html",
        "Is immigration a good or a bad thing?",
        "\n".join(body),
        description="What official evidence says about immigration’s effect on public money, public services and the economy, and where the evidence cannot decide.",
    )
