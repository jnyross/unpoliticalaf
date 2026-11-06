"""Spending by purpose over 100 years, from the OBR's historical public finances database."""
from .html import FOLD, page, details_table, small_multiples, source_line, esc
from .pages_money import views, VIEW_NOTES
from . import findings as F
from . import data_spendhist as H


def spending_history_page(facts, d, num, sources):
    h = d["spend_history"]
    years, ryears = h["years"], h["real_years"]
    last, start = years[-1], ryears[0]
    purposes = h["purposes"]
    keys = [k for k, _ in purposes]

    def g(k, y, kind="pct"):
        return num(f"hist.gdp.{k}.{y}", kind)

    body = ["<h1>Spending by purpose over 100 years</h1>"]
    # Each source is described on its own, so no two years either side of a source change
    # are set side by side (audit 11 judge).
    pesa = H.SOURCE_CHANGES[-1][0]
    ifs_last = years[years.index(pesa) - 1]
    four = {"defence": "defence", "health": "health", "education": "education", "social": "social security"}
    def largest(y):
        return four[max(four, key=lambda k: facts[f"hist.gdp.{k}.{y}"].value)]
    body.append(f'''<div class="answer"><p class="lede">The share of GDP spent on each purpose has shifted over the last century: of defence, health, education and social security, {largest(start)} was the largest in {start}, and {largest(ifs_last)} in {ifs_last}.</p>
<p>In {start}, the first year of the Institute for Fiscal Studies figures, defence cost {g("defence", start)} of GDP, more than health ({g("health", start)}), education ({g("education", start)}) or social security ({g("social", start)}).
By {ifs_last}, the last year of those figures, social security was {g("social", ifs_last)} of GDP, health {g("health", ifs_last)}, education {g("education", ifs_last)} and defence {g("defence", ifs_last)}.
HM Treasury's figures, a different source, give {last} as social security {g("social", last)}, health {g("health", last)}, education {g("education", last)} and defence {g("defence", last)}. Debt interest was {g("debt", last)} on this page's measure; HM Treasury's figure for interest paid out, on the <a href="spending.html">main spending page</a>, is larger ({num(f"spend.gdp.debt_interest.{last}", "pct")} of GDP in {last}).</p>
<p>These figures come from a different source from the <a href="spending.html">main spending page</a> and use different groups, so the two are shown separately and not joined.</p></div>''')

    marks_all = [(H.GEOGRAPHY_CHANGE[0], "Ireland leaves the UK")] + H.SOURCE_CHANGES
    unit = {"gdp": "Per cent of GDP", "real": "£ billion, 2025-26 prices", "cash": "£ billion, cash"}
    kind = {"gdp": "pct", "real": "bn", "cash": "bn"}

    full_from = "1949-50"  # the OBR marks this as its first year of full data

    def chart(v, ys=None):
        ys = ys or [y for y in (years if v == "gdp" else ryears) if y >= full_from]
        breaks = [(ys.index(y), t) for y, t in marks_all if y in ys and y != ys[0]]
        ids = [[f"hist.{v}.{k}.{y}" if facts[f"hist.{v}.{k}.{y}"].value is not None else None for y in ys] for k, _ in purposes]
        return small_multiples(f"Public spending on five purposes, {ys[0]} to {last}", [y[:4] for y in ys],
                               [(n, [facts[i].value if i else None for i in row]) for (k, n), row in zip(purposes, ids)],
                               unit[v] + ". Axis years are financial years starting in April of the year shown.", kind[v],
                               ids=ids, num=num, breaks=breaks, ymin=0, point_labels=ys,
                               finding=F.leader("{name} was the largest of the five {span}", which="last"))

    body.append("<h2 id='purposes'>Five purposes since the Second World War</h2>")
    body.append(f"<p>Health, education, defence, social security and interest on government debt, from {full_from}, the OBR's first year with figures for every purpose except social security, which starts in {h['first']['social']}. "
                f"Amounts after inflation start in {start}, the first year of the price index used. The chart back to {years[0]}, through both world wars, is further down.</p>")
    body.append(views(chart, order=("gdp", "real"), default="gdp", notes={
        "real": VIEW_NOTES["real"] + f" Starts in {start}."}))
    body.append('<p class="small">Amber dashed lines mark where the underlying source changes (to IFS figures in 1955-56 and to HM Treasury PESA in 2020-21). Gaps are years with no published figure. Cash amounts are not charted: over this many years prices rose so much that they cannot be compared, but every cash figure is in the record behind each after-inflation figure.</p>')
    body.append(FOLD)
    body.append(f"<h3>Back to {years[0]}, as a share of GDP</h3><p>Defence spending in the two world wars was far larger than anything since, so this chart is shown separately. Before 1922-23, GDP covers Great Britain and all of Ireland.</p>")
    body.append(chart("gdp", years))
    head = ["Year"] + [esc(n.split(" (")[0]) for _, n in purposes] + ["All public spending"]
    rows = [[y] + [g(k, y) for k in keys + ["total"]] for y in years]
    body.append(details_table("Show every year as a share of GDP", f"Public spending by purpose, % of GDP, {years[0]} to {last}", head, rows))
    rows = [[y] + [num(f"hist.real.{k}.{y}", "bn1") for k in keys + ["total"]] for y in ryears]
    body.append(details_table("Show every year after inflation", f"Public spending by purpose, £ billion in 2025-26 prices, {start} to {last}", head, rows))
    body.append('<p class="small">After-inflation amounts = cash amount × 100 ÷ GDP deflator (2025-26 = 100). Tap any figure to see the cash amount and deflator it was calculated from.</p>')
    body.append(f'''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>The OBR built these long series by joining several sources: the Bank of England's historical dataset before 1955-56, the Institute for Fiscal Studies from 1955-56 to 2019-20, and HM Treasury's PESA for 2020-21 and 2021-22. The OBR says these are not National Statistics and that it made judgements to keep the figures consistent across years.</li>
<li>The groups are not the international COFOG areas used on the <a href="spending.html">main spending page</a>. “Social security” means benefits and the State Pension; “social protection” on the main page is wider and also includes, for example, social care.</li>
<li>There are no figures for health and education before 1920-21 or from 1939-40 to 1947-48, and none for social security before 1955-56.</li>
<li>The series stop at {last}. For 2022-23 the OBR estimated health, education, defence and social security by growing the previous year's figures, so that year is not shown.</li>
<li>The database was last updated in July 2023, so later revisions are not included. Figures for 2020-21 and 2021-22 can differ from the current PESA figures on the main spending page.</li>
<li>Debt interest is the OBR database's own “debt interest” series. It is a different and smaller measure than the interest paid out that HM Treasury reports on the main spending page ({num(f"spend.cash.debt_interest.{last}", "bn")}, {num(f"spend.gdp.debt_interest.{last}", "pct")} of GDP, in {last}, against {num(f"hist.cash.debt.{last}", "bn")} here). Compare debt interest within one page, not across the two.</li>
<li>Amounts after inflation use the GDP deflator from the OBR's October 2026 databank (2025-26 = 100), which is a later release than the cash figures.</li>
</ul></div>''')
    body.append(source_line(sources, ["obrhist", "obrhist-amounts", "obr-prices"], "Sheets “Spending (per cent of GDP)” and “Spending (£m)”, and the GDP deflator from sheet “Aggregates (£bn)” of the databank."))
    return page("spending-history.html", "Spending by purpose over 100 years", "\n".join(body),
                "UK public spending on health, education, defence, social security and debt interest since 1900, as a share of GDP, after inflation and in cash.")
