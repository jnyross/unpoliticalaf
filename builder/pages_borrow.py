"""How UK government debt and borrowing costs compare with the other G7 countries."""
from .html import FOLD, page, details_table, bars, line_chart, small_multiples, switch, source_line, esc
from .explain import box as explain
from . import findings as F
from .pages_intl import place_word

UK, AVG = "GBR", "OECD_REP"


def _ordinal(n):
    return place_word(n, 7)


def _rank(facts, prefix, areas, period):
    """Areas sorted highest first, and the UK's place among them (1 = highest)."""
    order = sorted(areas, key=lambda a: -facts[f"{prefix}.{a}.{period}"].value)
    return order, order.index(UK) + 1


def _bar_items(facts, prefix, order, period, names, extra=()):
    items = []
    for a in list(order) + list(extra):
        name = esc(names[a])
        if a == UK:
            name = f"<strong>{name}</strong>"
        elif a == AVG:
            name = f"<strong>{name}</strong> (not a country)"
        items.append((name, f"{prefix}.{a}.{period}", "" if a in (UK, AVG) else "alt"))
    return items


def _higher_lower(order, names):
    """'higher than Germany, lower than Canada, France, …' for the UK's place in a ranked list."""
    i = order.index(UK)
    above = [_the(names[a]) for a in order[:i]]
    below = [_the(names[a]) for a in order[i + 1:]]
    parts = []
    if above:
        parts.append("lower than " + _join(above))
    if below:
        parts.append("higher than " + _join(below))
    return " and ".join(parts)


def _the(name):
    return "the " + name if name.startswith("United") else name


def _join(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def borrowing_page(facts, d, num, sources):
    b = d["borrow"]
    g7, names = b["g7"], b["names"]
    iy, dy, yy, ym = b["imf_year"], b["debt_year"], b["yield_year"], b["yield_month"]
    ny = b["int_year"]

    debt_order, debt_place = _rank(facts, "borrow.imf", g7, iy)
    oecd_order, oecd_place = _rank(facts, "borrow.debt", g7, dy)
    ym_order, ym_place = _rank(facts, "borrow.yieldm", g7, ym)
    yy_order, yy_place = _rank(facts, "borrow.yield", g7, yy)
    int_order, int_place = _rank(facts, "borrow.int", g7, ny)
    ir_order, ir_place = _rank(facts, "borrow.intrev", g7, ny)

    body = ["<h1>How do UK debt and borrowing costs compare with other major countries?</h1>"]
    body.append(f'''<div class="answer"><p class="lede">In {iy}, UK government debt was {num(f"borrow.imf.{UK}.{iy}", "pct")} of GDP, the {_ordinal(debt_place)} of the seven G7 countries: {_higher_lower(debt_order, names)}.</p>
<p>In {yy}, the latest full year, the UK government paid an average of {num(f"borrow.yield.{UK}.{yy}", "pct2")} a year to borrow for 10 years, the {_ordinal(yy_place)} of the G7. The latest month, {b["yield_month_name"]}, was {num(f"borrow.yieldm.{UK}.{ym}", "pct2")}, the {_ordinal(ym_place)} of the G7.</p>
</div>''')

    # ---------------------------------------------------------------- debt
    body.append(f'<h2 id="debt">How much does each government owe?</h2>')
    imf_bars = bars(_bar_items(facts, "borrow.imf", debt_order, iy, names), "pct", num, maxval=260,
                    caption=f"General government gross debt, % of GDP, {iy}. IMF figures. The UK has a darker bar.")
    oecd_bars = bars(_bar_items(facts, "borrow.debt", oecd_order, dy, names, extra=[AVG]), "pct", num, maxval=260,
                     caption=f"General government gross debt, % of GDP, {dy}, with government bonds counted at their market price. OECD figures. The UK and the OECD average have darker bars.")
    body.append(switch("Measure", [
        ("IMF", f"IMF figures, {iy}.", imf_bars),
        ("OECD", f"On the OECD's measure the UK was also the {_ordinal(oecd_place)} of the G7, at {num(f'borrow.debt.{UK}.{dy}', 'pct')} of GDP in {dy}. The OECD average was {num(f'borrow.debt.{AVG}.{dy}', 'pct')}.", oecd_bars),
    ]))
    body.append("<p>The G7 is the group of seven large, high-income economies: Canada, France, Germany, Italy, Japan, the United Kingdom and the United States. Debt and interest are compared as a share of GDP, the value of everything a country produces in a year, so that countries of different sizes can be compared.</p>")
    body.append(f'''<p class="small">The two organisations measure debt differently. The OECD follows the international system of national accounts, which counts government bonds at their market price. When interest rates rise, the market price of existing bonds falls, and so does debt measured this way. This is one reason the OECD's figure for the UK fell from {num(f"borrow.debt.{UK}.2021", "pct")} of GDP in 2021 to {num(f"borrow.debt.{UK}.2022", "pct")} in 2022, while the IMF's fell from {num(f"borrow.imf.{UK}.2021", "pct")} to {num(f"borrow.imf.{UK}.2022", "pct")}.</p>''')
    body.append(FOLD)
    years = b["imf_years"]
    series = [(names[a], [facts[f"borrow.imf.{a}.{y}"].value if f"borrow.imf.{a}.{y}" in facts else None for y in years]) for a in g7]
    ids = [[f"borrow.imf.{a}.{y}" if f"borrow.imf.{a}.{y}" in facts else None for y in years] for a in g7]
    body.append(small_multiples(f"Government debt as a share of GDP, G7, {years[0]} to {iy}", years, series,
                                "Per cent of GDP. Calendar years. Source: IMF.", "pct", ids=ids, num=num, ymin=0,
                                summary_note="The table below gives every country's figure for every year.",
                                finding=F.leader("{name} had the highest debt compared with the size of its economy {span}")))
    rows = [[y] + [num(i, "pct") if i else "not available" for i in col] for y, col in zip(years, zip(*ids))]
    body.append(details_table("Show debt every year", f"General government gross debt, % of GDP, G7, {years[0]} to {iy} (IMF)", ["Year"] + [esc(names[a]) for a in g7], rows))
    body.append(source_line(sources, ["imf-weo-debt", "oecd-gov-pf-g7"], "General government means central, regional and local government together. Gross debt does not subtract what the government owns."))

    # ---------------------------------------------------------------- yields
    body.append(f'<h2 id="yields">How much does each government pay to borrow?</h2>')
    body.append("<p>The UK Debt Management Office and the Office for Budget Responsibility explain what moves borrowing costs: <a href='#why'>their words are quoted further down</a>.</p>")
    body.append(f'''<div class="answer"><p>Governments borrow by selling bonds: promises to repay on a set date, with interest every year until then. UK government bonds are called gilts. The <strong>yield</strong> on a 10-year bond is the yearly interest, as a percentage of what is paid for the bond, that a buyer would earn by keeping it for 10 years. When yields are higher, new borrowing costs the government more.</p>
<p>Over the whole of {yy}, the latest full year, the UK's 10-year yield averaged {num(f"borrow.yield.{UK}.{yy}", "pct2")}, the {_ordinal(yy_place)} of the G7: {_higher_lower(yy_order, names)}. In the latest month, {b["yield_month_name"]}, it was {num(f"borrow.yieldm.{UK}.{ym}", "pct2")}, the {_ordinal(ym_place)} of the G7.</p></div>''')
    body.append(switch("Period", [
        (f"{yy} average", f"Yearly average for {yy}.", bars(_bar_items(facts, "borrow.yield", yy_order, yy, names), "pct2", num, maxval=6,
                                                             caption=f"Yield on 10-year government bonds, average for {yy}, per cent a year. The UK has a darker bar.")),
        (b["yield_month_name"], f"Average for {b['yield_month_name']}, the latest month.", bars(_bar_items(facts, "borrow.yieldm", ym_order, ym, names), "pct2", num, maxval=6,
                                                             caption=f"Yield on 10-year government bonds, average for {b['yield_month_name']}, per cent a year. The UK has a darker bar.")),
    ]))
    body.append("<p>The yield is the price the government pays for new 10-year borrowing. It changes every day as bonds are bought and sold.</p>")
    body.append(FOLD)
    years = b["yield_years"]
    series = [(names[a], [facts[f"borrow.yield.{a}.{y}"].value if f"borrow.yield.{a}.{y}" in facts else None for y in years]) for a in g7]
    ids = [[f"borrow.yield.{a}.{y}" if f"borrow.yield.{a}.{y}" in facts else None for y in years] for a in g7]
    body.append(small_multiples(f"10-year government bond yields, G7, {years[0]} to {yy}", years, series,
                                "Per cent a year, yearly averages. Source: OECD.", "pct2", ids=ids, num=num,
                                summary_note="The table below gives every country's figure for every year.",
                                finding=F.leader("{name} paid the most to borrow for 10 years {span}")))
    rows = [[y] + [num(i, "pct2") if i else "not available" for i in col] for y, col in zip(years, zip(*ids))]
    body.append(details_table("Show yields every year", f"10-year government bond yields, yearly average, per cent, G7, {years[0]} to {yy}", ["Year"] + [esc(names[a]) for a in g7], rows))
    body.append("<p class='small'>Yields below zero, as in Germany and Japan in some years, mean buyers accepted getting back slightly less than they paid. Italy's figures start in 1992. The yield on a bond is not the same as the average interest rate a government pays on all its debt, which includes bonds sold years earlier at other rates.</p>")
    body.append(source_line(sources, ["oecd-finmark-irlt"], "The OECD's long-term interest rates are the yields on government bonds with about 10 years to repay."))

    # ---------------------------------------------------------------- interest
    body.append(f'<h2 id="interest">How much interest does each government pay?</h2>')
    body.append(f'''<div class="answer"><p>In {ny}, the UK government's interest payments, after subtracting interest it received, were {num(f"borrow.int.{UK}.{ny}", "pct")} of GDP, the {_ordinal(int_place)} of the G7: {_higher_lower(int_order, names)}. That was {num(f"borrow.intrev.{UK}.{ny}", "pct")} of everything the government received in taxes and other income, also the {_ordinal(ir_place)} of the G7.</p></div>''')
    body.append(switch("Show", [
        ("% of GDP", f"Net interest paid, % of GDP, {ny}.",
         bars(_bar_items(facts, "borrow.int", int_order, ny, names, extra=[AVG]), "pct", num, maxval=5,
              caption=f"Net interest paid by general government, % of GDP, {ny}. The UK and the OECD average have darker bars.")),
        ("% of revenue", f"Net interest paid, as a share of government revenue, {ny}. Calculated here: interest ÷ revenue.",
         bars(_bar_items(facts, "borrow.intrev", ir_order, ny, names, extra=[AVG]), "pct", num, maxval=15,
              caption=f"Net interest paid by general government as a % of its revenue, {ny}. The UK and the OECD average have darker bars.")),
    ]))
    body.append("<p class='small'>Net interest is interest paid minus interest received. A figure below zero, as for Japan, means the government received slightly more interest than it paid.</p>")
    body.append(FOLD)
    years = b["int_years"]
    t_ids = [[f"borrow.int.{UK}.{y}" for y in years], [f"borrow.int.{AVG}.{y}" if f"borrow.int.{AVG}.{y}" in facts else None for y in years]]
    vals = [[facts[i].value if i else None for i in row] for row in t_ids]
    body.append(line_chart(f"Net interest paid as a share of GDP, UK and OECD average, {years[0]} to {ny}", years,
                           [("United Kingdom", vals[0], "a"), ("OECD average", vals[1], "b")], "Per cent of GDP. Calendar years. Source: OECD Government at a Glance.",
                           ymin=0, kind="pct", num=num, ids=t_ids, finding=F.gap("The UK's net interest bill", "the OECD average")))
    g_ids = [[f"borrow.int.{a}.{y}" if f"borrow.int.{a}.{y}" in facts else None for a in g7 + [AVG]] for y in years]
    rows = [[y] + [num(i, "pct") if i else "not available" for i in row] for y, row in zip(years, g_ids)]
    body.append(details_table("Show interest every year", f"Net interest paid by general government, % of GDP, G7 and OECD average, {years[0]} to {ny}", ["Year"] + [esc(names[a]) for a in g7 + [AVG]], rows))
    body.append("<p>The UK's interest bill rose sharply in 2022. Some UK government bonds are index-linked gilts, whose payments rise with the Retail Prices Index, a measure of inflation. The Office for National Statistics' explanation of the 2022-23 rise is quoted on the <a href='spending.html'>spending page</a>, and the Office for Budget Responsibility's in the next section.</p>")
    body.append(source_line(sources, ["oecd-gov-pf-g7"], "Interest as a share of revenue calculated here from the OECD's interest and revenue figures, both as % of GDP."))

    # ---------------------------------------------------------------- what moves yields
    body.append('<h2 id="why">What affects what a government pays to borrow?</h2>')
    body.append('''<div class="answer"><p>The UK Debt Management Office, which sells gilts for the government, names several things that move gilt prices, and so yields (quoted in full below):</p><ul>
<li>what investors expect interest rates to be over future years;</li>
<li>the level of inflation they expect, and how uncertain it is;</li>
<li>how many gilts the government sells, and how strong investors' demand for them is.</li></ul>
<p>The Office for Budget Responsibility, also quoted below, adds that borrowing costs have risen across the world, and points to public borrowing in the UK and other large, advanced economies.</p></div>''')
    body.append(explain("gilt-prices", sources, heading="h3"))
    body.append(explain("debt-interest-drivers", sources, heading="h3"))
    body.append(explain("borrowing-costs-2025", sources, heading="h3"))

    body.append(f'''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>These figures compare governments; they do not show which level of debt or interest is right, or what the borrowing paid for.</li>
<li>Different yields can reflect different central bank rates and inflation, not only how investors judge each government. Countries that share the euro (France, Germany and Italy) have the same central bank, so differences between their yields say more about how investors see each government than differences between, say, the UK and Japan.</li>
<li>GDP-based shares change when GDP changes, as well as when debt or interest changes.</li>
<li>The OECD and IMF revise these figures as countries send newer data. Figures here are as downloaded on the date on each source page.</li>
</ul></div>''')
    body.append(f'''<div class="limit"><p><strong>Why the UK figures differ from other pages.</strong> The <a href="spending.html">spending</a> and <a href="spending-history.html">spending history</a> pages use UK figures for financial years and the whole public sector from the OBR and HM Treasury. The figures here are for calendar years and general government, measured the same way for every country, so they do not match those pages exactly and are not joined to them.</p></div>''')
    body.append(f'<p>See also: <a href="international.html">how UK taxes and spending compare with other countries</a>.</p>')
    body.append(source_line(sources, ["imf-weo-debt", "oecd-gov-pf-g7", "oecd-finmark-irlt"],
                            "OECD data is published under the Creative Commons Attribution 4.0 licence. IMF data is reproduced with attribution."))
    return page("borrowing.html", "How do UK debt and borrowing costs compare with other major countries?", "\n".join(body),
                "UK government debt, 10-year borrowing costs and debt interest beside the other G7 countries, from the IMF and OECD, with what moves borrowing costs.")
