"""Are people leaving the UK, and do the official figures show why?

Answers John's question 5 (docs/johns-questions/questions.json). The numbers are
quoted word for word from ONS and HMRC publications (builder/explain.py), so each
one can be checked against its source. The page says what the figures can and
cannot show about why people leave.
"""
from .html import page, table, esc
from .explain import box as explain

PAGE = "leaving-uk.html"
TITLE = "Are people leaving the UK?"

SOURCES_LINE = (
    '<p class="src">Sources: <a href="https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/internationalmigration/bulletins/longterminternationalmigrationprovisional/yearendingdecember2025">'
    'ONS, Long-term international migration, provisional: year ending December 2025</a>; '
    '<a href="https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/internationalmigration/articles/ukemigrationexplainedwhatweknowaboutbritsmovingabroad/2026-05-21">'
    'ONS, UK emigration explained (21 May 2026)</a>; '
    '<a href="https://www.gov.uk/government/statistics/statistics-on-non-domiciled-taxpayers-in-the-uk/statistical-commentary-on-non-domiciled-taxpayers-in-the-uk">'
    'HMRC, Statistical commentary on non-domiciled taxpayers in the UK, tax year 2024 to 2025</a>. '
    'Figures are provisional where the publisher says so.</p>'
)


def leaving_page(facts, d, num, sources):
    b = [f'<h1>{esc(TITLE)}</h1>']
    b.append('<div class="answer"><p class="lead"><strong>Yes, a large number of people leave the UK each year, and the official estimate has risen since 2022.</strong> '
             'About 642,000 people left the UK to live abroad for at least 12 months in the year ending December 2025, according to provisional ONS estimates. '
             'That was 38,000 fewer than the year before.</p></div>')
    b.append('<p>The official figures record when people leave. None of them records why anyone left, so they cannot show whether taxes or living standards were a reason.</p>')

    b.append('<h2 id="short">The short answer</h2>')
    b.append('<ul>'
             '<li>In the year ending December 2025, 642,000 people left the UK for 12 months or more. That is 38,000 fewer than the year before, after an increase since 2022.</li>'
             '<li>Of these, 246,000 were British nationals, down from 257,000. ONS changed how it measures British nationals in 2025, so this cannot be compared with figures from before June 2021.</li>'
             '<li>More British nationals left than arrived, by around 136,000 in 2025.</li>'
             '<li>HMRC figures for non-domiciled taxpayers show fewer people leaving that group in the 2024 to 2025 tax year than the year before. Income Tax paid by that group rose.</li>'
             '<li>No official figure here shows why people leave, so none can show whether taxes or living standards are the cause.</li>'
             '</ul>')

    b.append('<h2 id="how-many">How many people leave the UK?</h2>')
    b.append(table("Long-term emigration from the UK, year ending December 2025 (provisional, rounded)",
                   ["Group", "Left the UK"],
                   [["All nationalities", "642,000"],
                    ["Non-EU+ nationals", "278,000"],
                    ["EU+ nationals", "118,000"],
                    ["British nationals", "246,000"]]))
    b.append('<p>The total is the sum of the three nationality groups. In the year ending December 2025, the total is provisional.</p>')
    b.append(explain("leave-total-2025", sources, heading="h3"))
    b.append(explain("leave-by-nationality", sources, heading="h3"))
    b.append(explain("leave-definition", sources, heading="h3"))

    b.append('<h2 id="british">British nationals: has the figure risen?</h2>')
    b.append('<p>Not on the official figures. ONS changed its method in November 2025 and revised its series back to June 2021, so older figures for British nationals are much lower and are not comparable. '
             'The change in method makes the British figures look higher than before, so comparisons across the change are misleading.</p>')
    b.append(explain("leave-method", sources, heading="h3"))
    b.append(explain("leave-british-net", sources, heading="h3"))

    b.append('<h2 id="who">Who leaves, and where do they go?</h2>')
    b.append('<p>Among non-EU+ nationals, just over half of those who left had first come to the UK on a study visa. ONS gives no reason for leaving, only the route by which people first arrived.</p>')
    b.append(explain("leave-difficult", sources, heading="h3"))
    b.append(explain("leave-surveys", sources, heading="h3"))

    b.append('<h2 id="why">Why do people leave? What the figures can and cannot show</h2>')
    b.append('<p><strong>None of the official figures on this page records why anyone left.</strong> '
             'The ONS reason is the visa a person first arrived on, which says little about why they left years later.</p>')
    b.append(explain("leave-reasons", sources, heading="h3"))
    b.append('<p>The figures on this page cannot show whether taxes or living standards were a reason for leaving. '
             'They do not record what a leaver paid in tax, how their pay changed, or what they said about their plans. '
             'A survey of people who left could say more, but the ONS says it cannot carry out high-quality surveys overseas.</p>')

    b.append('<h2 id="high-earners">High earners and non-domiciled taxpayers</h2>')
    b.append('<p>Non-domiciled taxpayers are people whose permanent home is outside the UK and who claim that status for tax. '
             'HMRC counts them each tax year. Its figures end with the 2024 to 2025 tax year, before a new residence-based regime began on 6 April 2025.</p>')
    b.append(explain("nondom-regime", sources, heading="h3"))
    b.append(explain("nondom-flows", sources, heading="h3"))
    b.append('<p>HMRC counts people who stop claiming non-domiciled status. That is not the same as leaving the country, and the commentary does not say how many of them left the UK.</p>')
    b.append(explain("nondom-residence", sources, heading="h3"))
    b.append(explain("nondom-income-tax", sources, heading="h3"))
    b.append(explain("nondom-provisional", sources, heading="h3"))

    b.append('<h2 id="living">Living standards</h2>')
    b.append('<p>The official sources on this page do not measure living standards. '
             'For how pay has changed after inflation, see <a href="life/earnings.html">Earnings after inflation</a>. '
             'For what taxes take from household income, see <a href="household-tax.html">Tax and income</a>. '
             'Neither shows whether living standards are a reason people leave.</p>')
    b.append('<p>This site does not compare living standards between countries. The <a href="international.html">international page</a> compares tax and spending as a share of GDP.</p>')

    b.append('<h2 id="limits">What to keep in mind</h2>')
    b.append('<ul>'
             '<li>Figures for the latest years are provisional and may be revised.</li>'
             '<li>“Leaving” here means living abroad for 12 months or more. Holidays and short trips do not count.</li>'
             '<li>British nationals are counted with a new method from June 2021, so earlier years cannot be compared with it.</li>'
             '<li>The HMRC figures count changes in tax status, not departures from the UK.</li>'
             '<li>No source here asks people why they left.</li>'
             '</ul>')
    b.append(SOURCES_LINE)
    return page(PAGE, TITLE, "\n".join(b),
                "Official figures on how many people leave the UK, British and non-British nationals, non-domiciled taxpayers, and what they cannot show about why people leave.")
