"""Why UK government debt is high: debt and borrowing over 125 years, and what official bodies say moved them."""
from .html import FOLD, page, details_table, line_chart, source_line, switch
from .explain import box as explain
from . import findings as F

def why_debt_page(facts, d, num, sources):
    h = d["debt_history"]
    years = h["years"]
    last = h["last"]
    first_y = years[0]

    def v(key, y):
        return facts[f"debt.{key}.{y}"].value

    debt_peak = max(years, key=lambda y: v("psnd", y))
    war_years = [y for y in years if "1939-40" <= y <= "1946-47"]
    war_max_year = max(war_years, key=lambda y: v("psnb", y))
    war_min_year = min(war_years, key=lambda y: v("psnb", y))
    v2020 = "2020-21"
    v2008 = "2007-08"

    body = ["<h1>Why is UK government debt high?</h1>"]
    body.append(f'''<div class="answer"><p class="lede">UK public sector net debt was {num(f"debt.psnd.{last}", "pct")} of GDP in {last}, against {num(f"debt.psnd.{v2008}", "pct")} in {v2008}.
Debt is what the public sector owes at the end of each year, less the financial assets it holds. Borrowing is the amount it borrowed during the year, which adds to debt. Each year's borrowing adds to debt. Borrowing means spending more than the government receives from taxes and other income.</p>
<p>The biggest recent rises in borrowing came in the 2008 recession and in the Covid pandemic. In 2022-23, borrowing stayed high while support for energy costs and interest on debt rose. The sections below set out each period with the official figures and what the official bodies say.</p></div>''')

    # ---------------------------------------------------------------- the long run
    body.append('<h2 id="history">How debt has changed since 1900</h2>')
    body.append(f"<p>Both lines are shares of GDP, the value of everything the UK produces in a year, so they stay comparable as the economy grew. The switch above the charts shows debt or each year's borrowing. Both are financial years, which run from April to March: {last} means April 2022 to March 2023.</p>")
    debt_vals = [v("psnd", y) for y in years]
    borrow_vals = [v("psnb", y) for y in years]
    labels = years
    debt_chart = line_chart(
        f"Public sector net debt, % of GDP, {first_y} to {last}", labels,
        [("Public sector net debt", debt_vals, "a")],
        "Per cent of GDP. Financial years, April to March. Source: OBR.",
        ymin=0, kind="pct", num=num,
        ids=[[f"debt.psnd.{y}" for y in years]],
        point_labels=years,
        finding=F.trend("Public sector net debt", which="all"))
    borrow_chart = line_chart(
        f"Public sector net borrowing, % of GDP, {first_y} to {last}", labels,
        [("Public sector net borrowing", borrow_vals, "a")],
        "Per cent of GDP. Financial years, April to March. Source: OBR.",
        kind="pct", num=num,
        ids=[[f"debt.psnb.{y}" for y in years]],
        point_labels=years,
        finding=F.trend("Public sector net borrowing", which="all"))
    body.append(switch("Measure", [
        ("Debt", f"Net debt at the end of each year, {first_y} to {last}.", debt_chart),
        ("Borrowing", f"Borrowing in each year, {first_y} to {last}. Below zero means the government had a surplus in that year.", borrow_chart),
    ]))
    body.append(f"<p>Debt was highest in {debt_peak}, at {num(f'debt.psnd.{debt_peak}', 'pct')} of GDP. It was {num(f'debt.psnd.{v2008}', 'pct')} in {v2008}, before the 2008 recession.</p>")
    body.append(FOLD)
    body.append(details_table("Show every year", f"Public sector net debt and net borrowing, % of GDP, {first_y} to {last} (OBR)",
                              ["Financial year", "Net debt, % of GDP", "Net borrowing, % of GDP"],
                              [[y, num(f"debt.psnd.{y}", "pct"), num(f"debt.psnb.{y}", "pct")] for y in years]))

    # ---------------------------------------------------------------- periods
    body.append('<h2 id="periods">Four periods when debt rose</h2>')
    body.append(f'''<h3>The Second World War and after</h3>
<p>From {war_years[0]} to {war_years[-1]}, borrowing was largest in {war_max_year}, at {num(f"debt.psnb.{war_max_year}", "pct")} of GDP, and smallest in {war_min_year}, at {num(f"debt.psnb.{war_min_year}", "pct")}. Debt was highest in {debt_peak}, at {num(f"debt.psnd.{debt_peak}", "pct")} of GDP. It then fell, and was {num("debt.psnd.1990-91", "pct")} of GDP in 1990-91.</p>''')
    body.append(f'''<h3 id="recession-2008">The 2008 recession</h3>
<p>Borrowing was {num(f"debt.psnb.{v2008}", "pct")} of GDP in {v2008} and {num("debt.psnb.2008-09", "pct")} in 2008-09, then {num("debt.psnb.2009-10", "pct")} in 2009-10. Debt rose from {num(f"debt.psnd.{v2008}", "pct")} of GDP to {num("debt.psnd.2009-10", "pct")} over the same period.</p>''')
    body.append(explain("debt-2008", sources, heading="h4"))
    body.append(f'''<h3 id="covid">The Covid pandemic</h3>
<p>Borrowing reached {num(f"debt.psnb.{v2020}", "pct")} of GDP in {v2020}, and debt was {num("debt.psnd.2021-22", "pct")} of GDP at the end of March 2022.</p>''')
    body.append(explain("covid-borrowing-2021", sources, heading="h4"))
    body.append(explain("covid-spending", sources, heading="h4"))
    body.append(f'''<h3 id="energy">Energy support and interest, 2022-23</h3>
<p>Borrowing was {num("debt.psnb.2022-23", "pct")} of GDP in 2022-23, and debt {num("debt.psnd.2022-23", "pct")} of GDP at the end of March 2023.</p>''')
    body.append(explain("energy-2022", sources, heading="h4"))
    body.append(explain("debt-interest-2022", sources, heading="h4"))

    # ---------------------------------------------------------------- what the OBR says
    body.append('<h2 id="obr">What the Office for Budget Responsibility says</h2>')
    body.append("<p>The Office for Budget Responsibility is the UK's official forecaster of the public finances. Its July 2025 report gives several explanations of the rise in debt. Three are quoted here in full.</p>")
    body.append(explain("debt-pandemic-2025", sources, heading="h3"))
    body.append(explain("debt-rules-2025", sources, heading="h3"))
    body.append(explain("debt-ageing-2025", sources, heading="h3"))

    # ---------------------------------------------------------------- interest and other countries
    body.append('<h2 id="interest">Interest and other countries</h2>')
    body.append(f'''<p>Interest on debt is part of government spending. The <a href="borrowing.html">borrowing page</a> shows how much the UK pays to borrow, how much of its spending goes on interest, and how UK debt compares with the other G7 countries. On the IMF's measure, UK general government debt was {num("borrow.imf.GBR.2024", "pct")} of GDP in 2024.</p>''')

    body.append('''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>This page uses public sector net debt, which takes away the financial assets the public sector holds. Gross debt, as the IMF measures it for other countries, is higher, so the two figures are not directly comparable.</li>
<li>The figures before 1955-56 come from a long-run compilation, and the OBR says judgements were made to keep years consistent.</li>
<li>A share of GDP changes when GDP changes as well as when debt does. The share can fall in a year of borrowing if the economy grows faster than debt.</li>
<li>These figures show when borrowing rose and what official bodies say lay behind it. They do not show whether the borrowing was the right choice, or what would have happened without it.</li>
<li>People disagree about how far debt should come down, and whether through spending, taxes or growth. These figures do not settle that question.</li>
</ul></div>''')
    body.append(source_line(sources, ["obrhist-aggregates", "imf-weo-debt"],
                            "Net debt and net borrowing are from the OBR historical database, sheet “Aggregates (per cent of GDP)”, 1900-01 to 2022-23. Quotations are from the OBR and ONS publications named above."))
    return page("why-debt.html", "Why is UK government debt high?", "\n".join(body),
                "Public sector net debt and borrowing since 1900, the periods that raised them, and what the Office for Budget Responsibility and the ONS say.")

