"""How UK tax and government spending compare with other OECD countries, as a share of GDP."""
from .html import FOLD, page, table, details_table, bars, line_chart, switch, source_line, esc, fmt
from .pages_money import derive
from . import findings as F

UK, AVG = "GBR", "OECD_REP"


def _ranked(facts, num, it, prefix, year, kind_word):
    """Every OECD member with a figure, highest first, with the UK and the average marked.

    Each country carries its rank (1 = highest). Returns the full list, a short list
    (the three highest, the UK with the two countries either side, the average and
    the three lowest, with a line saying how many are left out between), the count
    of countries and how many are above the UK.
    """
    areas = [a for a in it["members"] + [AVG] if facts.get(f"{prefix}.{a}.{year}") and facts[f"{prefix}.{a}.{year}"].value is not None]
    areas.sort(key=lambda a: -facts[f"{prefix}.{a}.{year}"].value)
    countries = [a for a in areas if a != AVG]
    items = []
    for a in areas:
        name = esc(it["names"][a])
        if a == UK:
            name = f"<strong>{countries.index(a) + 1}. {name}</strong>"
        elif a == AVG:
            name = f"<strong>{name}</strong> (not a country)"
        else:
            name = f"{countries.index(a) + 1}. {name}"
        items.append((name, f"{prefix}.{a}.{year}", "" if a in (UK, AVG) else "alt"))
    higher = sum(1 for a in countries if facts[f"{prefix}.{a}.{year}"].value > facts[f"{prefix}.{UK}.{year}"].value)
    return items, _short(areas, countries, items), len(countries), higher


def _short(areas, countries, items):
    """The ranking cut to the rows a reader needs, with each gap counted, not hidden."""
    n, u = len(countries), countries.index(UK)
    keep = set(range(3)) | set(range(n - 3, n)) | set(range(u - 2, u + 3))
    keep = {k for k in keep if 0 <= k < n}
    out, skipped = [], 0
    for item, a in zip(items, areas):
        if a == AVG or countries.index(a) in keep:
            if skipped:
                out.append((f"{skipped} {'country' if skipped == 1 else 'countries'} not shown here", None, "gap"))
                skipped = 0
            out.append(item)
        else:
            skipped += 1
    if skipped:
        out.append((f"{skipped} {'country' if skipped == 1 else 'countries'} not shown here", None, "gap"))
    return out


def _missing(it, codes, year, why):
    if not codes:
        return ""
    names = ", ".join(esc(it["names"][a]) for a in codes)
    return f"<p class='small'>Not shown: {names}, because the OECD had not published a {year} figure for {'it' if len(codes) == 1 else 'them'} {why}.</p>"


def _beside(facts, a, b):
    """Plain words for how one share compares with another: within 1 point counts as close."""
    gap = facts[a].value - facts[b].value
    return "close to" if abs(gap) < 1 else ("above" if gap > 0 else "below")


G7 = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"]
WORDS = ["", "", "second ", "third ", "fourth "]


def place_word(p, n):
    """'highest', 'third highest', 'second lowest' ... for place p (1 = highest) out of n."""
    if p * 2 <= n + 1:
        return WORDS[p] + "highest"
    return WORDS[n - p + 1] + "lowest"


def nth(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _g7(facts, num, it, ty, sy):
    """The UK's place among the G7, the group of seven large economies, on tax and on spending."""
    def order(prefix, year):
        have = [a for a in G7 if facts.get(f"{prefix}.{a}.{year}") and facts[f"{prefix}.{a}.{year}"].value is not None]
        return sorted(have, key=lambda a: -facts[f"{prefix}.{a}.{year}"].value)
    t, s = order("intl.tax", ty), order("intl.spend", sy)
    tp, sp = t.index(UK) + 1, s.index(UK) + 1
    missing = [it["names"][a] for a in G7 if a not in t or a not in s]
    rows = []
    for a in sorted(G7, key=lambda a: t.index(a) if a in t else 99):
        name = esc(it["names"][a])
        name = f"<strong>{name}</strong>" if a == UK else name
        rows.append([name, num(f"intl.tax.{a}.{ty}", "pct"), f"{t.index(a) + 1}" if a in t else "",
                     num(f"intl.spend.{a}.{sy}", "pct"), f"{s.index(a) + 1}" if a in s else ""])
    def among(n):
        return "" if n == 7 else f" (of the {n} with a figure for that year)"
    def g7_bars(order_, prefix, year, what):
        items = [(f"<strong>{esc(it['names'][a])}</strong>" if a == UK else esc(it["names"][a]), f"{prefix}.{a}.{year}", "" if a == UK else "alt")
                 for a in order_]
        return bars(items, "pct", num, maxval=60, caption=f"{what} as a % of GDP, {year}, G7 countries. The UK has the darker bar.")
    out = [f'<h2 id="g7">The UK beside the other G7 countries</h2>',
           f"<p>The G7 is a group of seven large economies. Among them, the UK had the {place_word(tp, len(t))} tax as a share of GDP in {ty}{among(len(t))}, and the {place_word(sp, len(s))} government spending as a share of GDP in {sy}{among(len(s))}.</p>",
           switch("Show the G7", [
               ("Taxes", f"The UK ranked {nth(tp)} of {len(t)} on tax in {ty}, where 1st is the highest.", g7_bars(t, "intl.tax", ty, "All taxes, including social security contributions,")),
               ("Spending", f"The UK ranked {nth(sp)} of {len(s)} on government spending in {sy}, where 1st is the highest.", g7_bars(s, "intl.spend", sy, "General government spending")),
           ]),
           details_table("Show the G7 as a table", f"Taxes and government spending, % of GDP, G7 countries{', ' + str(ty) if ty == sy else ''}. Rank 1 is the highest.",
                         ["Country", f"Taxes, {ty}", "Rank", f"Spending, {sy}", "Rank"], rows)]
    if missing:
        out.append(f"<p class='small'>Not ranked: {esc(', '.join(missing))}, because the OECD had not published a figure.</p>")
    out.append("<p class='small'>For government debt and borrowing costs in the G7, see <a href='borrowing.html'>how UK debt and borrowing costs compare</a>.</p>")
    return "\n".join(out)


def international_page(facts, d, num, sources):
    it = d["intl"]
    ty, sy, ky, fy = it["tax_year"], it["spend_year"], it["kind_year"], it["fn_year"]
    tax_items, tax_short, tax_n, tax_higher = _ranked(facts, num, it, "intl.tax", ty, "tax")
    sp_items, sp_short, sp_n, sp_higher = _ranked(facts, num, it, "intl.spend", sy, "spending")
    t_uk, t_avg = f"intl.tax.{UK}.{ty}", f"intl.tax.{AVG}.{ty}"
    s_uk, s_avg = f"intl.spend.{UK}.{sy}", f"intl.spend.{AVG}.{sy}"

    body = ["<h1>How do UK taxes and spending compare with other countries?</h1>"]
    body.append(f'''<div class="answer"><p class="lede">In {ty}, UK taxes were {num(t_uk, "pct")} of GDP, {_beside(facts, t_uk, t_avg)} the OECD average of {num(t_avg, "pct")}. Government spending{"" if sy == ty else " in " + str(sy)} was {num(s_uk, "pct")} of GDP, {_beside(facts, s_uk, s_avg)} the average of {num(s_avg, "pct")}.</p></div>''')
    year_word = str(ty) if ty == sy else f"{ty} and {sy}"
    body.append(_g7(facts, num, it, ty, sy))
    body.append(f'<h2 id="countries">The UK beside each OECD country, {year_word}</h2>')
    short_note = "Shown: the three highest, the UK with the two countries either side of it, the OECD average and the three lowest. Rank 1 is the highest."
    def ranking(short, full, n, caption):
        return (bars(short, "pct", num, maxval=60, caption=f"{caption} {short_note}")
                + f"<details><summary>Show all {n} countries</summary>{bars(full, 'pct', num, maxval=60)}</details>")
    tax_bars = ranking(tax_short, tax_items, tax_n,
                       f"All taxes, including social security contributions such as National Insurance, as a % of GDP, {ty}. The UK and the OECD average have darker bars.")
    sp_bars = ranking(sp_short, sp_items, sp_n,
                      f"Spending by general government (central, regional and local government and social security funds) as a % of GDP, {sy}. The UK and the OECD average have darker bars.")
    body.append(switch("Show", [
        ("Taxes", f"Of the {tax_n} countries with a figure for {ty}, {tax_higher} collected a larger share of GDP in tax than the UK.", tax_bars + _missing(it, it["tax_missing"], ty, "when this data was downloaded")),
        ("Spending", f"Of the {sp_n} countries with a figure for {sy}, {sp_higher} spent a larger share of GDP than the UK.", sp_bars + _missing(it, it["spend_missing"], sy, "when this data was downloaded")),
    ]))
    body.append("<p>The OECD is a group of 38 mostly high-income countries. GDP is the value of everything produced in a country in a year; dividing by it lets countries of very different sizes be compared. It does not show how much tax any one person pays.</p>")
    body.append(FOLD)
    body.append(source_line(sources, ["oecd-rs-tax", "oecd-gov-pf"], "Total tax revenue and general government expenditure, as % of GDP. The “OECD average” is the OECD's simple average of its member countries, each counted equally."))

    # Over time: the UK beside the average, each on its own measure.
    tyears = [y for y in it["tax_years"] if y <= ty]
    syears = it["spend_years"]
    tax_ids = [[f"intl.tax.{UK}.{y}" for y in tyears], [f"intl.tax.{AVG}.{y}" if f"intl.tax.{AVG}.{y}" in facts else None for y in tyears]]
    sp_ids = [[f"intl.spend.{UK}.{y}" for y in syears], [f"intl.spend.{AVG}.{y}" if f"intl.spend.{AVG}.{y}" in facts else None for y in syears]]

    def vals(ids):
        return [[facts[i].value if i else None for i in row] for row in ids]

    covid = [(syears.index("2020"), "Covid")] if "2020" in syears else []
    tv, sv = vals(tax_ids), vals(sp_ids)
    t_above = sum(1 for u, a in zip(*tv) if u is not None and a is not None and u > a)
    t_both = sum(1 for u, a in zip(*tv) if u is not None and a is not None)
    s_above = [y for y, u, a in zip(syears, *sv) if u is not None and a is not None and u > a]
    s_both = sum(1 for u, a in zip(*sv) if u is not None and a is not None)
    body.append(f'<h2 id="time">How has this changed over time?</h2>')
    body.append(f'''<div class="answer"><p>Taxes in the UK were {num(f"intl.tax.{UK}.{tyears[0]}", "pct")} of GDP in {tyears[0]}, when the OECD average was {num(f"intl.tax.{AVG}.{tyears[0]}", "pct")}, and {num(t_uk, "pct")} in {ty}, against {num(t_avg, "pct")}. The UK share was above the average in {t_above} of the {t_both} years.
Government spending was above the average in {len(s_above)} of the {s_both} years from {syears[0]} to {sy}.</p></div>''')
    body.append(switch("Show", [
        ("Taxes", f"All taxes as a % of GDP, {tyears[0]} to {ty}.",
         line_chart(f"Taxes as a share of GDP, UK and OECD average, {tyears[0]} to {ty}", tyears,
                    [("United Kingdom", tv[0], "a"), ("OECD average", tv[1], "b")], "Per cent of GDP. Calendar years. Source: OECD Revenue Statistics.",
                    ymin=0, kind="pct", num=num, ids=tax_ids, finding=F.gap("The UK's tax share of GDP", "the OECD average"))),
        ("Spending", f"General government spending as a % of GDP, {syears[0]} to {sy}. The OECD's yearly series starts in {syears[0]}.",
         line_chart(f"Government spending as a share of GDP, UK and OECD average, {syears[0]} to {sy}", syears,
                    [("United Kingdom", sv[0], "a"), ("OECD average", sv[1], "b")], "Per cent of GDP. Calendar years. Source: OECD Government at a Glance.",
                    ymin=0, kind="pct", num=num, ids=sp_ids, events=covid, finding=F.gap("The UK's spending share of GDP", "the OECD average"))),
    ]))
    body.append("<p class='small'>The OECD average covers the countries that are members today, using the figures each had in each year. Some countries' figures start later than others, so the early average is based on fewer countries.</p>")
    body.append(FOLD)
    rows = [[y, num(f"intl.tax.{UK}.{y}", "pct"), num(f"intl.tax.{AVG}.{y}", "pct")] for y in tyears]
    body.append(details_table("Show taxes every year", f"Taxes as % of GDP, UK and OECD average, {tyears[0]} to {ty}", ["Year", "UK", "OECD average"], rows))
    rows = [[y, num(f"intl.spend.{UK}.{y}", "pct"), num(f"intl.spend.{AVG}.{y}", "pct")] for y in syears]
    body.append(details_table("Show spending every year", f"Government spending as % of GDP, UK and OECD average, {syears[0]} to {sy}", ["Year", "UK", "OECD average"], rows))

    # Kinds of tax.
    body.append(f'<h2 id="kinds">Which kinds of tax differ, {ky}?</h2>')
    rows = []
    for k, name, uk_names in it["tax_kinds"]:
        a, b = f"intl.taxkind.{k}.{UK}.{ky}", f"intl.taxkind.{k}.{AVG}.{ky}"
        diff = derive(facts, f"intl.taxkind.diff.{k}.{ky}", facts[a].value - facts[b].value, "percentage points", ky, "oecd-rs-tax", [a, b], f"{a} − {b}")
        rows.append([f"{esc(name)}<br><span class='small'>UK: {esc(uk_names)}</span>", num(a, "pct"), num(b, "pct"), num(diff, "pts")])
    kinds = sorted(it["tax_kinds"], key=lambda t: facts[f"intl.taxkind.diff.{t[0]}.{ky}"].value)
    lo, hi = kinds[0], kinds[-1]
    body.append(f'''<p>Compared with the average, the UK raised more from <strong>{esc(hi[1].lower())}</strong> ({num(f"intl.taxkind.{hi[0]}.{UK}.{ky}", "pct")} of GDP against {num(f"intl.taxkind.{hi[0]}.{AVG}.{ky}", "pct")}) and less from <strong>{esc(lo[1].lower())}</strong> ({num(f"intl.taxkind.{lo[0]}.{UK}.{ky}", "pct")} against {num(f"intl.taxkind.{lo[0]}.{AVG}.{ky}", "pct")}).</p>''')
    body.append(details_table("Show all five kinds of tax", f"Main kinds of tax, % of GDP, UK and OECD average, {ky}", ["Kind of tax", "UK", "OECD average", "UK minus average"], rows))
    body.append("<p class='small'>Differences are calculated from the unrounded figures, so they can differ by 0.1 from the rounded figures shown.</p>")
    body.append("<p class='small'>The OECD groups taxes the same way for every country. Smaller kinds, such as payroll taxes, are not shown, so the five do not add up to the total.</p>")

    # Spending by purpose.
    body.append(f'<h2 id="purpose">Which areas of spending differ, {fy}?</h2>')
    rows = []
    for g, name in it["functions"]:
        a, b = f"intl.fn.{g}.{UK}.{fy}", f"intl.fn.{g}.{AVG}.{fy}"
        diff = derive(facts, f"intl.fn.diff.{g}.{fy}", facts[a].value - facts[b].value, "percentage points", fy, "oecd-gov-cofog", [a, b], f"{a} − {b}")
        rows.append([esc(name), num(a, "pct"), num(b, "pct"), num(diff, "pts")])
    fns = sorted(it["functions"], key=lambda t: facts[f"intl.fn.diff.{t[0]}.{fy}"].value)
    flo, fhi = fns[0], fns[-1]
    body.append(f'''<p>The largest differences from the average in {fy}: the UK spent more on <strong>{esc(fhi[1].lower())}</strong> ({num(f"intl.fn.{fhi[0]}.{UK}.{fy}", "pct")} of GDP against {num(f"intl.fn.{fhi[0]}.{AVG}.{fy}", "pct")}) and less on <strong>{esc(flo[1].lower())}</strong> ({num(f"intl.fn.{flo[0]}.{UK}.{fy}", "pct")} against {num(f"intl.fn.{flo[0]}.{AVG}.{fy}", "pct")}).</p>''')
    body.append(details_table("Show all ten areas", f"Government spending by purpose (COFOG), % of GDP, UK and OECD average, {fy}", ["Area", "UK", "OECD average", "UK minus average"], rows))
    body.append(f"<p class='small'>Areas follow COFOG, the international classification also used on the <a href='spending.html'>spending page</a>. {fy} is the latest year with figures for the UK and the average.</p>")
    body.append(FOLD)

    body.append(f'''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>These figures show how large taxes and spending are compared with each economy. They do not show which level is better, or what people get in return.</li>
<li>Countries pay for the same things in different ways. Where health insurance or pensions are compulsory but paid to private firms, as health insurance is in Switzerland, the money may not count as tax or government spending at all. Some countries pay benefits that are then taxed, which raises both tax and spending.</li>
<li>GDP is not a perfect measure of an economy's size. In Ireland it is raised by the profits of large multinational companies, which makes Ireland's shares look lower; Ireland's own statistics office publishes another measure for this reason.</li>
<li>The “OECD average” counts each country equally, so Iceland counts as much as the United States. It is not the share for the OECD as a whole.</li>
<li>The OECD revises these figures as countries send newer data. Figures here are as downloaded on the date shown on each source page.</li>
</ul></div>''')
    body.append(f'''<div class="limit"><p><strong>Why the UK figures differ from other pages.</strong> The <a href="taxes.html">taxes</a> and <a href="spending.html">spending</a> pages use UK figures for financial years (April to March) and the whole public sector, including public corporations, from the OBR and HM Treasury.
The OECD uses calendar years and general government only, and counts some items differently, so its UK figures do not match those pages exactly. They are shown here, not joined to the UK series, because they are measured the same way for every country.</p></div>''')
    body.append(source_line(sources, ["oecd-rs-tax", "oecd-gov-pf", "oecd-gov-cofog"],
                            "OECD data is published under the Creative Commons Attribution 4.0 licence. Differences from the average calculated here."))
    return page("international.html", "How do UK taxes and spending compare with other countries?", "\n".join(body),
                "UK taxes and government spending as a share of GDP beside the 37 other OECD countries and the OECD average, from OECD Revenue Statistics and Government at a Glance.")
