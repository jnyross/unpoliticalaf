"""How UK productivity compares with other G7 countries: output per hour and per worker.

Figures come from the ONS international comparisons of productivity (data_prod.py).
Levels are in pounds at current prices, converted with purchasing power parities,
so they compare the size of economies per hour worked, not what anyone earns.
Trends are after inflation (volume indexes), rebased to 2008 = 100.
"""
from .html import FOLD, page, table, details_table, bars, line_chart, switch, source_line, esc

UK = "GBR"
G7 = ["GBR", "USA", "DEU", "FRA", "ITA", "CAN", "JPN"]
OTHERS = ["USA", "DEU", "FRA", "ITA", "CAN"]  # the five other G7 countries with a figure in every year from 2008
BASE = 2008


def _name(p, iso):
    return ("the " if iso in ("GBR", "USA") else "") + p["names"][iso]


def _levels_bars(facts, num, p, latest):
    """Output per hour in the latest year, highest first. Japan has no figure, so it is named as a gap."""
    have = [i for i in G7 if f"prod.oph.{i}.{latest}" in facts]
    have.sort(key=lambda i: -facts[f"prod.oph.{i}.{latest}"].value)
    items = []
    for i in have:
        name = esc(p["names"][i])
        label = f"<strong>{name}</strong>" if i == UK else name
        items.append((label, f"prod.oph.{i}.{latest}", "" if i == UK else "alt"))
    for i in G7:
        if i in have:
            continue
        last = max((y for y in range(latest - 1, latest - 6, -1) if f"prod.oph.{i}.{y}" in facts), default=None)
        words = f"{esc(p['names'][i])}: no {latest} figure"
        if last:
            words += f" (latest, {last}: {num(f'prod.oph.{i}.{last}', 'pounds2')})"
        items.append((words, None, "gap"))
    return bars(items, "pounds2", num, maxval=65,
                caption=f"Output per hour worked in {latest}, in pounds at current prices, converted with purchasing power parities. The UK has the darker bar.")


def _rank_words(facts, latest):
    """Which G7 countries (with a figure) the UK is below, and which it is above, in the latest year."""
    uk = facts[f"prod.oph.{UK}.{latest}"].value
    below, above = [], []
    for i in G7:
        fid = f"prod.oph.{i}.{latest}"
        if i == UK or fid not in facts:
            continue
        (below if facts[fid].value > uk else above).append(i)
    return below, above


def _uk_finding(labels, series, stretches):
    """Says where the UK line sits below the average, leaving out the base year, when both start level at 100."""
    x, y = series[0][1], series[1][1]
    years = [i for i in range(len(labels)) if labels[i] != str(BASE) and x[i] is not None and y[i] is not None]
    if years and all(x[i] < y[i] for i in years):
        return f"The UK was below the other five G7 countries on average in every year from {labels[years[0]]} to {labels[years[-1]]}"
    return ""


def productivity_page(facts, d, num, sources):
    p = d["productivity"]
    latest = p["latest"]
    years = [y for y in p["trend_years"]]
    below, above = _rank_words(facts, latest)

    def join(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

    uk_lvl = num(f"prod.oph.{UK}.{latest}", "pounds2")
    def phrase(i):
        return f"{num(f'prod.oph.{i}.{latest}', 'pounds2')} in {_name(p, i)}"
    lower = join([phrase(i) for i in below])
    higher = join([phrase(i) for i in above])
    gap_note = f"Japan has no {latest} figure in this series." if p["missing_latest"] else ""
    rise = num(f"prod.change.{UK}.{latest}", "pct")
    full_rise = num(f"prod.fullchange.{UK}.{latest}", "pct")
    first_uk = p["uk_first"]
    avg_rise = num(f"prod.change.avg5.{latest}", "pct")
    body = ["<h1>How does UK productivity compare with other countries?</h1>"]
    body.append(
        f'<div class="answer"><p class="lede">In {latest}, UK output per hour worked was {uk_lvl}. '
        f'That was lower than {lower}, and higher than {higher}. {gap_note}</p>'
        f'<p>After inflation, UK output per hour rose by {full_rise} between {first_uk}, the first year of the ONS series, and {latest}. '
        f'The comparison with other G7 countries starts in {BASE}, the first year all five of them have a figure. Over {BASE} to {latest}, UK output per hour rose by {rise}, '
        f'and the other five G7 countries on this page rose by {avg_rise} on average.</p></div>')

    body.append(switch("Show", [
        ("Levels", f"Output per hour worked in {latest}, in pounds, for each G7 country.", _levels_bars(facts, num, p, latest)),
        ("Since 2008", f"Output per hour worked after inflation, {BASE} = 100, from {BASE} to {latest}. The line for the other five G7 countries is the simple average of their own indexes.",
         line_chart(f"Output per hour worked after inflation, UK and the other five G7 countries, {BASE} to {latest}",
                    [str(y) for y in years],
                    [("United Kingdom", [facts[f"prod.trend.{UK}.{y}"].value for y in years], "a"),
                     ("Other five G7 countries (average)", [facts[f"prod.trend.avg5.{y}"].value for y in years], "b")],
                    f"Index, {BASE} = 100 (after inflation). Calendar years. Source: ONS, international comparisons of productivity.",
                    ymin=90, ymax=115, kind="dp1", num=num,
                    ids=[[f"prod.trend.{UK}.{y}" for y in years], [f"prod.trend.avg5.{y}" for y in years]],
                    finding=_uk_finding)),
    ]))
    body.append("<p>The G7 is the group of seven large economies: Canada, France, Germany, Italy, Japan, the UK and the United States. "
                "Output per hour worked is the economy's output (GDP) divided by the hours its people work. It shows how much each hour produces, not how much anyone is paid.</p>")

    body.append(FOLD)
    body.append(f'<h2 id="workers">Output per worker, {latest}</h2>')
    body.append(f'<p>Output per worker divides the same output by the number of people in work, whatever their hours. In {latest}, UK output per worker was {num(f"prod.opw.{UK}.{latest}", "pounds")} '
                f'at current prices, against {num(f"prod.opw.USA.{latest}", "pounds")} in the United States and {num(f"prod.opw.DEU.{latest}", "pounds")} in Germany. '
                f'Japan has no {latest} figure.</p>')
    rows = []
    for i in G7:
        rows.append([f"<strong>{esc(p['names'][i])}</strong>" if i == UK else esc(p["names"][i]),
                     num(f"prod.oph.{i}.{latest}", "pounds2") if f"prod.oph.{i}.{latest}" in facts else "not published",
                     num(f"prod.opw.{i}.{latest}", "pounds") if f"prod.opw.{i}.{latest}" in facts else "not published"])
    body.append(table(f"Output per hour worked and per worker, {latest}, G7 countries, in pounds at current prices", ["Country", "Per hour worked", "Per worker"], rows))

    body.append(f'<h2 id="years">Every year since {BASE}</h2>')
    body.append(f"<p>The yearly figures for each country are below, from 2008 (the year the trend starts). Japan's figures stop in 2020. The ONS series itself starts in {p['years'][0]}.</p>")
    cols = ["GBR", "USA", "DEU", "FRA", "ITA", "CAN", "JPN"]
    head = ["Year"] + [esc(p["names"][i]) for i in cols]
    yrows = []
    for y in p["years"]:
        if y < 2008:
            continue
        yrows.append([str(y)] + [num(f"prod.oph.{i}.{y}", "pounds2") if f"prod.oph.{i}.{y}" in facts else "not published" for i in cols])
    body.append(details_table("Show output per hour worked for every year", f"Output per hour worked, in pounds at current prices, 2008 to {latest}", head, yrows))
    trows = []
    for y in years:
        trows.append([str(y), num(f"prod.trend.{UK}.{y}", "dp1"), num(f"prod.trend.avg5.{y}", "dp1")])
    body.append(details_table("Show the trend since 2008 for every year", f"Output per hour worked after inflation, index 2008 = 100, UK and the other five G7 countries (average), 2008 to {latest}",
                              ["Year", "UK", "Other five G7 countries (average)"], trows))

    body.append(f'''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>Levels are converted to pounds with purchasing power parities, which are estimates. They show the size of the difference, not an exact amount.</li>
<li>Hours are counted in different ways. The ONS uses the OECD's measure of UK hours, which comes from the EU Labour Force Survey, and not the UK's own national measure, so UK levels can differ from the figures on other pages.</li>
<li>Output per worker counts people, not hours, so it is lower where many people work part time.</li>
<li>These figures measure how much each hour or worker produces. They do not show what causes a gap, and they do not measure how well people's lives are going.</li>
<li>The series ends in {latest}. The ONS stopped publishing it in 2024. The OECD publishes later figures for the same countries, which this site does not yet use.</li>
<li>Japan has no figure for {latest}, so it is not in the average of the other five countries and is not ranked for that year.</li>
<li>The ONS corrected this dataset in January 2023. The figures here are the corrected version.</li>
</ul></div>''')
    body.append(source_line(sources, ["ons-icp"],
                            "Levels are calculated from the ONS tables in pounds at current prices. Trends are rebased to 2008 = 100 from the ONS volume index (2019 = 100). Each rebased figure is our calculation from the ONS figures."))
    return page("productivity.html", "How does UK productivity compare with other countries?", "\n".join(body),
                f"UK output per hour worked and per worker beside the G7 countries, {p['years'][0]} to {latest}, from ONS international comparisons of productivity.")
