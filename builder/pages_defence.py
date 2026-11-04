"""Why UK defence spending is limited: what it costs, how it compares and how it could be paid for.

Every figure comes from the same retained sources as the rest of the site:
- PESA 2026 (HM Treasury, public expenditure): defence spending in cash, after inflation
  and as a share of GDP, 2003-04 to 2025-26 (the COFOG "defence" function).
- OECD Government at a Glance: defence as a share of GDP for the G7, calendar years.
- OBR public finances databank (October 2026): nominal GDP and tax receipts.

The page calculates what 1% of GDP is worth, so the cost of any extra spending can be
read off it. It never says whether the UK can afford more: that is a judgement about
priorities, and the page sets out the choices instead.
"""
from .html import FOLD, page, details_table, bars, line_chart, switch, source_line, esc
from .pages_money import derive
from .explain import box as explain
from . import findings as F

UK, AVG = "GBR", "OECD_REP"
G7 = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"]
CASH_PAIR = 2015  # the start of the ten-year window used for the "compared with 2015-16" sentence (impartiality rule: ten years for spending by area)


def _ordinal_word(n):
    return {1: "highest", 2: "second highest", 3: "third highest", 4: "fourth highest", 5: "fifth highest",
            6: "sixth highest", 7: "seventh highest"}.get(n, f"{n}th highest")


def _ranked_g7(facts, it, year):
    """G7 countries that have a defence figure for the year, highest first, with the UK's place."""
    have = [a for a in G7 if f"intl.fn.GF02.{a}.{year}" in facts]
    have.sort(key=lambda a: -facts[f"intl.fn.GF02.{a}.{year}"].value)
    return have, have.index(UK) + 1


def _the(name):
    return "the " + name if name.startswith("United") else name


def _years(facts, sp):
    return [y for y in sp["years"] if f"spend.cash.defence.{y}" in facts and f"spend.gdp.defence.{y}" in facts]


def defence_page(facts, d, num, sources):
    sp, it, borrow = d["spending"], d["intl"], d["borrow"]
    latest = sp["latest"]  # 2025-26, outturn
    years = _years(facts, sp)
    first = years[0]
    names = it["names"]

    # ------------------------------------------------------------- calculated figures
    cash, real, gdp = f"spend.cash.defence.{latest}", f"spend.real.defence.{latest}", f"spend.gdp.defence.{latest}"
    real_base = f"spend.real.defence.{CASH_PAIR}-{str(CASH_PAIR + 1)[-2:]}"
    share_base = f"spend.gdp.defence.{CASH_PAIR}-{str(CASH_PAIR + 1)[-2:]}"
    real_change = derive(facts, f"defence.realchange.{CASH_PAIR}", (facts[real].value / facts[real_base].value - 1) * 100,
                         "%", latest, "pesa4", [real, real_base],
                         f"({real} ÷ {real_base} − 1) × 100", note="Change in spending after inflation, 2025-26 prices.")

    gdp_now = f"agg.gdpcash.{latest}"
    tax_now = f"rec.taxes.{latest}"
    edu_now = f"spend.cash.education.{latest}"
    one = derive(facts, f"defence.1pct.{latest}", facts[gdp_now].value * 0.01, "£bn", latest, "obr-prices", [gdp_now],
                 f"{gdp_now} × 0.01", note="One per cent of nominal GDP, the cost of 1% of GDP in that year.")
    half = derive(facts, f"defence.half.{latest}", facts[gdp_now].value * 0.005, "£bn", latest, "obr-prices", [gdp_now],
                  f"{gdp_now} × 0.005", note="Half of one per cent of nominal GDP.")
    tax_share = derive(facts, f"defence.1pct.taxshare.{latest}", facts[one].value / facts[tax_now].value * 100, "%", latest,
                       "obr-prices", [one, tax_now], f"{one} ÷ {tax_now} × 100",
                       note="1% of GDP as a share of all tax receipts in the same year.")
    edu_share = derive(facts, f"defence.1pct.edushare.{latest}", facts[one].value / facts[edu_now].value * 100, "%", latest,
                       "pesa4", [one, edu_now], f"{one} ÷ {edu_now} × 100",
                       note="1% of GDP as a share of cash spending on education in the same year.")
    pop = f"pop.uk.{latest[:4]}"
    per_head = derive(facts, f"defence.1pct.perperson.{latest}", facts[one].value * 1e9 / facts[pop].value, "£ per person", latest,
                      "obr-prices", [one, pop], f"{one} × 1000000000 ÷ {pop}",
                      note="An average across everyone in the UK, children included; not anyone's bill.")

    # ------------------------------------------------------------- the answer
    body = ["<h1>What limits UK defence spending, and what would more cost?</h1>"]
    body.append(f'''<div class="answer"><p class="lede">In {latest} the UK spent {num(cash, "bn")} on defence, {num(gdp, "pct")} of GDP. Extra spending has to be paid for by borrowing, by taxes or by spending less elsewhere, and each has costs. Whether the UK can afford more depends on which costs people accept, and this page does not decide that for you.</p>
<p>Each extra 1% of GDP in defence spending would cost about {num(one, "bn")} a year at {latest} levels. That is about {num(tax_share, "pct")} of all tax receipts.</p></div>''')

    body.append('<h2 id="spending">How much does the UK spend on defence?</h2>')
    body.append(switch("Measure", [
        ("Cash", f"Spending in the money of each year, £ billion, {first} to {latest}. PESA outturn.",
         line_chart(f"UK defence spending in cash, {first} to {latest}", years,
                    [("Defence", [facts[f"spend.cash.defence.{y}"].value for y in years], "a")],
                    "£ billion, cash. Financial years. Source: HM Treasury PESA 2026.",
                    ymin=0, kind="bn", num=num, ids=[[f"spend.cash.defence.{y}" for y in years]],
                    finding=F.trend("Defence spending in cash", which="all", dips=0.1))),
        ("After inflation", f"£ billion at 2025-26 prices, so years can be compared. {first} to {latest}.",
         line_chart(f"UK defence spending after inflation, {first} to {latest}", years,
                    [("Defence", [facts[f"spend.real.defence.{y}"].value for y in years], "a")],
                    "£ billion, 2025-26 prices. Financial years. Source: HM Treasury PESA 2026.",
                    ymin=0, kind="bn", num=num, ids=[[f"spend.real.defence.{y}" for y in years]],
                    finding=F.trend("Defence spending after inflation", which="all", dips=0.1))),
        ("% of GDP", f"Spending as a share of GDP, {first} to {latest}.",
         line_chart(f"UK defence spending as a share of GDP, {first} to {latest}", years,
                    [("Defence", [facts[f"spend.gdp.defence.{y}"].value for y in years], "a")],
                    "Per cent of GDP. Financial years. Source: HM Treasury PESA 2026.",
                    ymin=0, kind="pct", num=num, ids=[[f"spend.gdp.defence.{y}" for y in years]],
                    finding=F.trend("Defence as a share of GDP", which="all", dips=0.1))),
    ]))
    gdp_v, gdp_base_v = facts[gdp].value, facts[share_base].value
    share_cmp = "lower" if gdp_v < gdp_base_v else ("higher" if gdp_v > gdp_base_v else "the same")
    body.append(f"<p>Defence spending was {num(cash, 'bn')} in {latest}, up from {num(f'spend.cash.defence.{CASH_PAIR}-{str(CASH_PAIR + 1)[-2:]}', 'bn')} in {CASH_PAIR}-{str(CASH_PAIR + 1)[-2:]}. "
                f"After inflation the rise was {num(real_change, 'pct')}, from {num(real_base, 'bn')} to {num(real, 'bn')} at 2025-26 prices. "
                f"Its share of GDP was {share_cmp} in {latest} than in {CASH_PAIR}-{str(CASH_PAIR + 1)[-2:]}: {num(gdp, 'pct')} against {num(share_base, 'pct')}.</p>")
    body.append(FOLD)
    rows = [[y, num(f"spend.cash.defence.{y}", "bn"), num(f"spend.real.defence.{y}", "bn"), num(f"spend.gdp.defence.{y}", "pct")] for y in years]
    body.append(details_table("Show defence spending every year", f"UK defence spending, {first} to {latest}: cash, after inflation and % of GDP",
                              ["Financial year", "Cash, £ billion", "After inflation, £ billion (2025-26 prices)", "% of GDP"], rows))
    body.append("<p class='small'>Defence here is the government's official “defence” spending, the COFOG function in PESA. It excludes military pensions, which count as social protection, so it is lower than the figure NATO uses. The 2025-26 figures are outturn.</p>")
    body.append(source_line(sources, ["pesa4"], "Financial years, April to March."))

    # ------------------------------------------------------------- peers
    fy = it["fn_year"]
    have, place = _ranked_g7(facts, it, fy)
    top = have[0]
    items = []
    for a in have:
        name = esc(names[a])
        if a == UK:
            name = f"<strong>{name}</strong>"
        items.append((name, f"intl.fn.GF02.{a}.{fy}", "" if a == UK else "alt"))
    items.append((f"<strong>{esc(names[AVG])}</strong> (not a country)", f"intl.fn.GF02.{AVG}.{fy}", ""))
    maxval = facts[f"intl.fn.GF02.{top}.{fy}"].value * 1.1
    body.append(f'<h2 id="peers">How does UK defence spending compare with other G7 countries?</h2>')
    body.append(f'''<div class="answer"><p>In {fy}, UK defence spending was {num(f"intl.fn.GF02.{UK}.{fy}", "pct")} of GDP on the OECD's measure, the {_ordinal_word(place)} of the {len(have)} G7 countries with a figure.{"" if top == UK else f" The highest was {_the(names[top])}, at {num(f'intl.fn.GF02.{top}.{fy}', 'pct')}."}</p></div>''')
    body.append(bars(items, "pct", num, maxval=maxval,
                     caption=f"Government spending on defence, % of GDP, {fy}. OECD figures, calendar years. The UK has a darker bar."))
    missing = [names[a] for a in G7 if a not in have]
    if missing:
        body.append(f"<p>{esc(', '.join(missing))}: the OECD table has no defence figure for {'this country' if len(missing) == 1 else 'these countries'}, so {'it is' if len(missing) == 1 else 'they are'} not shown. A missing figure is not the same as zero.</p>")
    body.append(f"<p>France's and Germany's figures are provisional. The OECD measure is the COFOG defence function, so it is close to the PESA figure above but not the same year or the same source. NATO publishes its own defence figures on a wider definition, and the site does not show them yet.</p>")
    body.append(FOLD)
    body.append(source_line(sources, ["oecd-gov-cofog"], "The OECD average is an unweighted average of its member countries, not a country."))

    # ------------------------------------------------------------- competes with
    pairs = [(k, f"spend.per100.{k}.{latest}") for k in ("social", "health", "general", "education", "economic", "order", "housing", "recreation", "environment", "defence")]
    labels = {"social": "Social protection (pensions, benefits)", "health": "Health", "general": "General public services (incl. debt interest)",
              "education": "Education", "economic": "Economic affairs", "order": "Public order and safety", "housing": "Housing and community",
              "recreation": "Recreation, culture and religion", "environment": "Environment", "eu": "EU transactions", "defence": "Defence"}
    pairs.sort(key=lambda p: -facts[p[1]].value)
    items = [(f"<strong>{esc(labels[k])}</strong>" if k == "defence" else esc(labels[k]), fid, "" if k == "defence" else "alt") for k, fid in pairs]
    body.append('<h2 id="competes">What does defence compete with?</h2>')
    body.append(f"<p>Defence is one of many purposes that share the same money. In {latest}, of every £100 the government spent on services, defence took {num(f'spend.per100.defence.{latest}', 'per100dp1')}. "
                f"Social protection took {num(f'spend.per100.social.{latest}', 'per100dp1')} and health {num(f'spend.per100.health.{latest}', 'per100dp1')}. "
                f"Interest on government debt is counted inside general public services, and is shown in <a href=\"borrowing.html#interest\">debt interest beside other countries</a>.</p>")
    body.append(bars(items, "per100dp1", num, maxval=facts[f"spend.per100.social.{latest}"].value * 1.05,
                     caption=f"Spending by purpose, £ per £100 of spending on services, {latest}. Defence has a darker bar."))
    body.append(f'<p class="small">Shares are of total spending on services. The full breakdown is on <a href="spending-areas.html">spending areas</a>, and the totals are on the <a href="spending.html">main spending page</a>.</p>')

    # ------------------------------------------------------------- cost
    body.append('<h2 id="cost">What would extra defence spending cost?</h2>')
    body.append(f'''<div class="answer"><p>Costs can be compared in a simple way: one per cent of GDP. In {latest}, GDP was {num(gdp_now, "bn")} in cash terms, so 1% of it is {num(one, "bn")} a year, and 0.5% is {num(half, "bn")}.</p>
<p>For scale, {num(one, "bn")} is about {num(tax_share, "pct")} of all tax receipts in {latest} ({num(tax_now, "bn")}), and about {num(edu_share, "pct")} of what the government spent on education in cash terms. Spread across everyone in the UK it is about {num(per_head, "pounds")} a person a year: an average, not anyone's bill.</p></div>''')
    body.append("<p>These are simple arithmetic on the year's GDP, not forecasts. They show what the cost would be if spending rose by that much, with no other change. They do not show how the spending would be used, what it would buy, or how the economy would respond.</p>")

    # ------------------------------------------------------------- funding
    body.append('<h2 id="funding">How could extra spending be paid for?</h2>')
    body.append(f'''<p>There are three broad ways, and most plans combine them. The site does not say which is right.</p>
<ul>
<li><strong>Borrowing.</strong> Extra spending that is not matched by taxes adds to debt. UK government debt was {num(f"borrow.imf.{UK}.{borrow['imf_year']}", "pct")} of GDP in {borrow['imf_year']} on the IMF's measure, and interest is paid on it every year. The yield on new 10-year borrowing is set out, year by year, on <a href="borrowing.html#yields">UK borrowing costs beside the G7</a>.</li>
<li><strong>Tax.</strong> Higher taxes raise the money directly. {num(one, "bn")} is about {num(tax_share, "pct")} of all tax receipts in {latest}. See <a href="taxes.html">taxes</a> for where that money comes from now.</li>
<li><strong>Less spending elsewhere.</strong> Money can be moved from other purposes. {num(one, "bn")} is about {num(edu_share, "pct")} of cash spending on education in {latest}, for example. See <a href="spending.html">spending</a> for the sizes of the other purposes.</li>
</ul>''')
    body.append("<p>Each way has costs. Borrowing spreads the cost over time but adds interest. Tax changes fall on different people in different ways, which is covered on <a href=\"who-pays.html\">who pays</a>. Cuts to other purposes mean less of what they provide.</p>")

    # ------------------------------------------------------------- open questions
    body.append('<h2 id="rules">What are the government\'s fiscal rules?</h2>')
    body.append("<p>A fiscal rule is a target that the government sets for its public finances. The Office for Budget Responsibility (OBR) describes the rule that applied in 2025 like this:</p>")
    body.append(explain("defence-fiscal-rule-2025", sources))
    body.append('<h2 id="limits">What the figures do not show</h2>')
    body.append("<ul><li>How much room the fiscal rule leaves for extra spending (its headroom) is not on the site yet, so it cannot say how much there is.</li>"
                "<li>NATO's own defence figures, which use a wider definition than the OECD and PESA, are not on this site yet.</li>"
                "<li>Canada has no defence figure in the OECD table used above.</li></ul>")
    body.append('<p>Whether the UK can afford more is a judgement about priorities. People who say it cannot afford more often point to high debt and the interest bill. Others say defence should come first in spending decisions, or that faster growth would make more room over time. The figures on this page are the same whichever view you hold.</p>')

    body.append(source_line(sources, ["pesa4", "obr-prices", "oecd-gov-cofog"], "Calculations are shown with each figure, so they can be checked from the sources."))
    return page("defence.html", "What limits UK defence spending, and what would more cost?", "\n".join(body),
                description="The UK's defence spending in cash, after inflation and as a share of GDP, compared with the G7, and what extra spending would cost and how it could be paid for.")
