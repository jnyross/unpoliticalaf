"""Build the static site in site/ from data/spending.json.

Every figure on the page is a <data> element. Its value attribute holds the number and
data-ref names the source cell (or, for shares, the cells it was calculated from), so
scripts/check_site.py can check each one against the raw spreadsheets.
"""

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWS = [("real", "Adjusted for inflation"), ("nominal", "Cash, as spent at the time"),
         ("gdp", "Share of the whole economy (GDP)")]
INK, SOFT, GRID = "#1f2937", "#4b5563", "#e5e7eb"


def esc(s):
    return html.escape(str(s), quote=True)


def where(ref):
    sheet, cell = ref.rsplit("!", 1)
    src = SHEET_SOURCE[sheet]
    table = f"Table {sheet.replace('_', '.')}" if sheet[0].isdigit() else f"sheet '{sheet}'"
    return f"{src['publisher']}, {src['publication']}, {table}, cell {cell}"


def money(v, unit="bn"):
    if unit == "bn":
        return f"£{v:,.1f}bn" if abs(v) < 100 else f"£{v:,.0f}bn"
    return f"{v:.1f}%"


def fig(entry, text=None, kind="bn"):
    """A value whose full fiscal contract is in the downloadable registry."""
    v = entry["v"]
    if v is None:
        return '<span class="small">not given</span>'
    meta = D["provenance"][entry["value_id"]]
    status = D["status_definitions"][meta["status"]]["label"]
    note = f'{where(entry["ref"])}. {meta["period"]}; {meta["unit"]}; {status}.'
    shown = text if text is not None else money(v, kind)
    return (f'<data value="{v}" data-value-id="{esc(entry["value_id"])}" '
            f'data-ref="{esc(entry["ref"])}" title="Source: {esc(note)}">{esc(shown)}</data>')


def calculation(kind, a, b, text_fn):
    key = kind + ":" + a["value_id"] + ":" + b["value_id"]
    node = D["derived"][key]
    if node["v"] is None:
        if node.get("comparability") == "definition_break":
            refs = "; ".join(where(ref) for ref in node["comparison_refs"])
            return (f'<span class="small" title="{esc(refs)}">'
                    'not comparable: the definition changed</span>')
        return '<span class="small">not given: no comparable calculation</span>'
    refs = f'{a["ref"]} {b["ref"]}'
    title = (f'{D["formulae"][kind]}. Operands: {where(a["ref"])} and {where(b["ref"])}. '
             'Units, scope, periods and status are in the data file.')
    return (f'<data value="{node["v"]:.4f}" data-calc="{kind}" data-derived-id="{esc(key)}" '
            f'data-ref="{esc(refs)}" title="{esc(title)}">{esc(text_fn(node["v"]))}</data>')


def change(old, new):
    return calculation("change", old, new, lambda c: f'{abs(c):.0f}% {"more" if c > 0 else "less"}')


def share(part, whole, text_fn=lambda s: f"£{s:.0f}"):
    return calculation("share", part, whole, text_fn)


# ---------------------------------------------------------------- charts

def hbar(rows):
    """Horizontal bar chart in HTML, so labels stay readable on small screens.
    rows: (label, value, display_text). Screen readers use the table below instead."""
    top = max(r[1] for r in rows)
    out = ['<div class="bars" aria-hidden="true">']
    for label, v, txt in rows:
        out.append(f'<div class="bar"><span class="bl">{esc(label)}</span>'
                   f'<span class="bt"><span class="bf" style="width:{max(0, v / top * 100):.1f}%"></span>'
                   f'<span class="bv">{esc(txt)}</span></span></div>')
    out.append("</div>")
    return "".join(out)


def nice_max(v):
    """Smallest round axis top (4 to 6 gridlines of a round step) that fits v."""
    best = None
    for mag in (0.1, 1, 10, 100, 1000):
        for step in (1, 2, 2.5, 5):
            for n in (4, 5, 6):
                top = step * mag * n
                if top >= v and (best is None or top < best[0]):
                    best = (top, step * mag)
    return best


def line(years, series, forecast_from=None, breaks=(), width=680, height=260, small=False, unit="bn"):
    """One SVG <g> with a line chart. series: list of values (None allowed)."""
    l, r, t, b = (44, 10, 12, 26) if small else (60, 16, 16, 30)
    vals = [v for v in series if v is not None]
    if not vals:
        return '<text x="20" y="40">No data given</text>'
    hi, step = nice_max(max(vals))
    lo = min(0, min(vals))
    pw, ph = width - l - r, height - t - b
    x = lambda i: l + i * pw / (len(years) - 1)
    y = lambda v: t + ph - (v - lo) / (hi - lo) * ph
    g = []
    k = 0
    while k <= hi + 1e-9:
        g.append(f'<line x1="{l}" x2="{width - r}" y1="{y(k):.1f}" y2="{y(k):.1f}" stroke="{GRID}"/>')
        lab = f"{k:g}%" if unit == "gdp" else f"£{k:,.0f}bn"
        g.append(f'<text x="{l - 6}" y="{y(k) + 4:.1f}" text-anchor="end" class="axis">{lab}</text>')
        k += step
    every = max(1, round(len(years) / (5 if small else 8)))
    for i, yr in enumerate(years):
        last = i == len(years) - 1
        if (i % every == 0 and len(years) - 1 - i >= every * 0.6) or last:
            anchor = "end" if last else "start" if i == 0 else "middle"
            g.append(f'<text x="{x(i) + (4 if last else 0):.1f}" y="{height - 8}" text-anchor="{anchor}" class="axis">{yr}</text>')
    if forecast_from is not None:
        fx = x(forecast_from - 0.5)
        g.append(f'<rect x="{fx:.1f}" y="{t}" width="{width - r - fx:.1f}" height="{ph}" fill="#f3f4f6"/>')
        g.append(f'<text x="{fx + 4:.1f}" y="{t + 12}" class="axis">Forecast</text>')
    for i, note in breaks:
        bx = x(i - 0.5)
        g.append(f'<line x1="{bx:.1f}" x2="{bx:.1f}" y1="{t}" y2="{t + ph}" stroke="{SOFT}" stroke-dasharray="2 3"/>')
        g.append(f'<text x="{bx + 3:.1f}" y="{t + ph - 4}" class="axis">{esc(note)}</text>')
    # Split at missing cells and definition breaks, preserving the year positions.
    boundaries = {i for i, _ in breaks}
    for forecast in (False, True):
        segment = []
        def flush():
            if segment:
                dash = ' stroke-dasharray="6 5"' if forecast else ""
                points = " ".join(f"{px:.1f},{py:.1f}" for px, py in segment)
                g.append(f'<polyline fill="none" stroke="{INK}" stroke-width="2.5"{dash} points="{points}"/>')
                segment.clear()
        for i, value in enumerate(series):
            if i in boundaries:
                flush()
            visible = (forecast_from is not None and i >= forecast_from - 1) if forecast else (forecast_from is None or i < forecast_from)
            if value is None or not visible:
                flush()
            else:
                segment.append((x(i), y(value)))
        flush()
    return "".join(g)


def columns(labels, series, width=680, height=240, small=False):
    """Vertical column chart for values in per cent. series: list of (values, fill).
    A missing value is drawn as 'n/a' so a gap in the data is never shown as zero."""
    l, r, t, b = (44, 6, 12, 26) if small else (44, 10, 14, 30)
    vals = [v for vs, _ in series for v in vs if v is not None]
    hi, step = nice_max(max(vals))
    lo = min(0, min(vals))
    pw, ph = width - l - r, height - t - b
    y = lambda v: t + ph - (v - lo) / (hi - lo) * ph
    slot = pw / len(labels)
    bw = slot * 0.7 / len(series)
    g = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-hidden="true" class="chart{" small" if small else ""}">']
    k = 0
    while k <= hi + 1e-9:
        g.append(f'<line x1="{l}" x2="{width - r}" y1="{y(k):.1f}" y2="{y(k):.1f}" stroke="{GRID}"/>')
        g.append(f'<text x="{l - 5}" y="{y(k) + 4:.1f}" text-anchor="end" class="axis">{k:g}%</text>')
        k += step
    for i, lab in enumerate(labels):
        x0 = l + i * slot + slot * 0.15
        for j, (vs, fill) in enumerate(series):
            v, x = vs[i], x0 + j * bw
            if v is None:
                g.append(f'<text x="{x + bw / 2:.1f}" y="{y(0) - 4:.1f}" text-anchor="middle" class="axis">n/a</text>')
                continue
            top, base = (y(v), y(0)) if v >= 0 else (y(0), y(v))
            g.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{base - top:.1f}" fill="{fill}"/>')
        short = lab if not small else "\u2019" + lab[2:4]
        g.append(f'<text x="{l + i * slot + slot / 2:.1f}" y="{height - 9}" text-anchor="middle" class="axis">{short}</text>')
    g.append("</svg>")
    return "".join(g)


def view_chart(make, width=680, height=260):
    """Three versions of a chart (one per view); CSS shows the selected one."""
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-hidden="true" class="chart">']
    for key, _ in VIEWS:
        parts.append(f'<g class="v v-{key}">{make(key)}</g>')
    parts.append("</svg>")
    return "".join(parts)


def table(caption, head, rows):
    out = [f'<details class="tbl"><summary>Show the numbers in a table</summary>'
           f'<div class="table-scroll" role="region" aria-label="{esc(caption)}" tabindex="0">'
           f'<table><caption>{esc(caption)}</caption><thead><tr>']
    out += [f'<th scope="col">{esc(h)}</th>' for h in head]
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f'<th scope="row">{c}</th>' if i == 0 else f"<td>{c}</td>" for i, c in enumerate(row)) + "</tr>")
    out.append("</tbody></table></div></details>")
    return "".join(out)


# ---------------------------------------------------------------- page sections

def configure(data, corrections=None, payers=None, basics_sources=None):
    """Bind a validated in-memory dataset; importing this module reads no files."""
    global D, SRC, LATEST, BASE, SHEET_SOURCE, VIEWS, CORRECTIONS, PAYERS, BASICS_SOURCES
    global agg, funcs, total, services, interest, latest, ranked, years, agg_years, TEN, TWENTY, H, first_forecast
    D = data
    PAYERS = payers
    BASICS_SOURCES = basics_sources
    CORRECTIONS = [] if corrections is None else corrections
    SRC = D["sources"]
    LATEST, BASE = D["latest_year"], D["base_year"]
    SHEET_SOURCE = {sheet: src for src in SRC.values() for sheet in src["sheets"]}
    VIEWS = [("real", f"Adjusted for inflation ({BASE} prices)"),
             ("nominal", "Cash, as spent at the time"), ("gdp", "Share of the whole economy (GDP)")]
    agg = {e["year"]: e for e in D["aggregates"]}
    funcs = {f["id"]: f for f in D["functions"]}
    total = agg[LATEST]["tme"]
    services = D["services_total"][LATEST]
    interest = D["debt_interest"][LATEST]
    latest = {f["id"]: f["series"][LATEST]["nominal"] for f in D["functions"]}
    ranked = sorted((f for f in D["functions"] if f["id"] != "eu"), key=lambda f: -latest[f["id"]]["v"])
    years = D["years"]
    agg_years = [e["year"] for e in D["aggregates"]]
    # Comparisons step back from the latest year in tens of years, so no year is picked by hand.
    TEN = years[years.index(LATEST) - 10]
    TWENTY = years[years.index(LATEST) - 20]
    H = D["history"]
    first_forecast = next((i for i, e in enumerate(D["aggregates"]) if e["forecast"]), None)


def section_hundred():
    rows = [(f["plain"], latest[f["id"]]["v"] / services["v"] * 100,
             f"£{latest[f['id']]['v'] / services['v'] * 100:.0f}") for f in ranked]
    trows = [[esc(f["plain"]) + f'<br><small>{esc(f["official"])}</small>', fig(latest[f["id"]]),
              share(latest[f["id"]], services, lambda s: f"£{s:.2f}")] for f in ranked]
    eu = latest["eu"]
    trows.append(["Payments to and from the EU<br><small>EU transactions</small>", fig(eu), share(eu, services, lambda s: f"£{s:.2f}")])
    trows.append(["<strong>Total spending on services</strong>", fig(services), share(services, services, lambda s: f"£{s:.2f}")])
    return f"""
<section id="hundred">
<h2>Out of every £100</h2>
<p>Here is how each £100 spent on public services was split in {LATEST}.
The top area was <strong>{esc(ranked[0]["plain"].lower())}</strong>.
It took {share(latest[ranked[0]["id"]], services)} of every £100.
Health came next, with {share(latest["health"], services)}.</p>
{hbar(rows)}
<p class="small">We round each amount to the nearest pound, so they may not add up to £100.
The £100 is split from {fig(services)}, not the full {fig(total["nominal"])}.
The gap is made up of book-keeping items that do not belong to one area.</p>
{table(f"Spending by area, {LATEST}", ["Area", "Spent", "Out of every £100"], trows)}
</section>"""


def section_items():
    rows = [(d["plain"], d["v"], money(d["v"])) for d in D["details"]]
    trows = [[esc(d["plain"]) + f'<br><small>{esc(d["official"])}</small>', fig(d)] for d in D["details"]]
    parts = "".join(f'<li><span class="name">{esc(p["official"][0].upper() + p["official"][1:])}</span>: {fig(p)}</li>' for p in D["debt_parts"])
    return f"""
<section id="items">
<h2>Ten spending items</h2>
<p>These are ten selected items within the spending areas in {LATEST}. These items sit inside the area totals, so do not add the two lists.</p>
<p class="small">The source counts some primary academy spending under secondary schools.
Health uses a Treasury grouping where the needed detail is not available in England and Wales.
The defence figure uses the UN definition; it is not a NATO total.
See <cite>PESA Table 5.2, notes 4, 6 and 7</cite>. Each item's data record keeps the source notes.</p>
{hbar(rows)}
{table(f"Selected items, {LATEST}", ["Item", "Spent"], trows)}
<h3 id="debt">Interest on government debt</h3>
<p>The Treasury's line for debt interest in {LATEST} is {fig(interest)}.
That is {share(interest, services)} of every £100.
Not all of it is interest on loans. Here is what it is made of:</p>
<ul>{parts}</ul>
<p class="small">The Bank of England item covers its bond-buying scheme (quantitative easing) and a related lending scheme.
Source: <cite>{esc(where(D["debt_parts"][0]["ref"]).split(", cell")[0])}</cite>, notes 2 and 3.</p>
</section>"""


def section_total():
    def make(view):
        vals = [e["tme"][view]["v"] for e in D["aggregates"]]
        return line(agg_years, vals, forecast_from=first_forecast, unit=view)
    then = agg[TEN]["tme"]
    trows = [[e["year"] + (" (forecast)" if e["forecast"] else ""), fig(e["tme"]["nominal"]), fig(e["tme"]["real"]),
              fig(e["tme"]["gdp"], kind="gdp")] for e in D["aggregates"]]
    return f"""
<section id="total">
<h2>Total spending since {agg_years[0][:4]}</h2>
<p>In {LATEST} the public sector spent {fig(total["nominal"])} in all.
That was {fig(total["gdp"], kind="gdp")} of the value of all the goods and services made in the UK that year (GDP).
Ten years earlier, in {TEN}, it was {fig(then["gdp"], kind="gdp")}.
<a href="#decades">See every ten years back to 1945</a>.</p>
{view_chart(make)}
<p class="small">Years after {LATEST} are a forecast. They have a dashed line and a grey background.
The GDP and price forecasts are from the <cite>Office for Budget Responsibility</cite>, dated <span data-pesa-forecast-date="1">{esc(D["pesa_context"]["forecast_date"])}</span>.
The dates and price basis are in <cite>PESA {esc(D["pesa_context"]["forecast_ref"])} and {esc(D["pesa_context"]["deflator_ref"])}</cite>.
From 2020-21, the figures include help given during Covid and when prices rose fast.
(<cite>PESA Table 4.2, note 2</cite>)</p>
{table(f"Total Managed Expenditure, {agg_years[0]} to {agg_years[-1]}", ["Year", "Cash", f"Adjusted for inflation ({BASE} prices)", "Share of GDP"], trows)}
</section>"""


def pct(entry):
    return fig(entry, kind="gdp") if entry["v"] is not None else '<span class="small">not given</span>'


def section_decades():
    dec = H["decades"]
    t = {x["id"]: x for x in H["totals"]}
    sp, rc = t["spending"]["values"], t["receipts"]["values"]
    legend = (f'<p class="legend"><span class="key" style="background:{INK}"></span> Spending '
              f'<span class="key" style="background:{SOFT}"></span> Income</p>')
    def both(series, height):
        # A wide chart for big screens and a compact one for phones; CSS shows one.
        return (f'<div class="wide">{columns(dec, series, height=height)}</div>'
                f'<div class="narrow">{columns(dec, series, width=340, height=height * 0.8, small=True)}</div>')
    money_chart = both([([sp[y]["v"] for y in dec], INK), ([rc[y]["v"] for y in dec], SOFT)], 240)
    debt_chart = both([([t["debt"]["values"][y]["v"] for y in dec], INK)], 200)
    trows = [[y] + [pct(t[k]["values"][y]) for k in ("spending", "receipts", "borrowing", "debt")] for y in dec]
    hist_src = SRC["obr_hist"]
    cards = []
    for a in H["areas"]:
        ys = list(a["values"])
        cards.append(f"""
<article class="card" id="decade-{a["id"]}">
<h3>{esc(a["plain"])}</h3>
<p class="official">Official name: <span class="name">{esc(a["official"])}</span></p>
{columns(ys, [([a["values"][y]["v"] for y in ys], INK)], width=340, height=170, small=True)}
{table(f'{a["official"]}, share of GDP', ["Year", "Share of GDP"], [[y, pct(a["values"][y])] for y in ys])}
</article>""")
    first, last = dec[0], dec[-1]
    return f"""
<section id="decades">
<h2>Every ten years since 1945</h2>
<p>These charts step back ten years at a time from {last}, to {first}, the first year after the Second World War.
They always show each amount as a share of GDP. That is the fairest way to compare years so far apart.</p>
<h3>Spending and income</h3>
<p>In {first}, spending was {pct(sp[first])} of GDP. In {last} it was {pct(sp[last])}.
When spending is more than income, the government borrows the gap.</p>
{legend}
{money_chart}
<h3>Total debt</h3>
<p>This measure of debt takes off the liquid assets counted by the source. In {first} it was {pct(t["debt"]["values"][first])} of GDP.
In {last} it was {pct(t["debt"]["values"][last])}.</p>
{debt_chart}
{table(f"Spending, income, borrowing and debt, share of GDP, {first} to {last}",
       ["Year", "Spending", "Income", "Borrowing", "Debt"], trows)}
<p class="small">Source: <cite>{esc(SRC["obr_databank"]["publisher"])}, {esc(SRC["obr_databank"]["publication"])}</cite>.
This file is newer than the Treasury tables used above, so it can differ a little.
Each value has an uncertain actual/estimate status in the data file. The notes do not give a clear final status.
The <span data-pesa-forecast-date="1">{esc(D["pesa_context"]["forecast_date"])}</span> forecast note above applies to the Treasury totals, not this OBR file.
The OBR sheet's own notes name both March and October forecasts. The registry keeps these conflicts and each series' update notes
(<cite>Public finances since 1900, B2 and B139 to B148</cite>).
For {last} it gives spending of {pct(sp[last])} of GDP; the Treasury gives {fig(total["gdp"], kind="gdp")}.
Missing figures are shown as “not given”, not zero.</p>
<h3>Spending on five areas</h3>
<p>Here is the spend on five big areas, every ten years.
The newest year here is {max(y for a in H["areas"] for y in a["values"])}, because this data set stops in {H["areas_last_year"]}.
These areas are counted in a different way from the ones higher up this page, so the numbers do not match them.</p>
<div class="cards">{"".join(cards)}</div>
<p class="small">Source: <cite>{esc(hist_src["publisher"])}, {esc(hist_src["publication"])}</cite>.
The OBR says these are not National Statistics. It made its own choices to join up older and newer sources.
There are no health or education figures for 1945-46. "Interest on government debt" here is central government
interest only, after taking off the Bank of England's bond-buying scheme.
The source's 2022-23 values for several areas are grown from past years. These are estimates, not observed data.
The fixed decade view stops at 2015-16 (<cite>Contents, D51 to D56</cite>).</p>
</section>"""


BREAKS = {
    "education": [("2011-12", "Student loans removed")],
    "economic": [("2011-12", "TfL added"), ("2015-16", "Rail added")],
    "eu": [("2010-11", "VAT basis changed")],
}


def section_areas():
    cards = []
    for f in ranked:
        boundaries = BREAKS.get(f["id"], [])
        breaks = [(years.index(year), note) for year, note in boundaries if year in years]

        def make(view, f=f, breaks=breaks):
            return line(years, [f["series"][y][view]["v"] for y in years], breaks=breaks, width=340,
                        height=190, small=True, unit=view)
        steps = []
        for then in (TEN, TWENTY):
            mark = " *" if any(then < year <= LATEST for year, _ in boundaries) else ""
            steps.append(f"<li>{then}: {change(f['series'][then]['real'], f['series'][LATEST]['real'])}{mark}</li>")
        crossed = [year for year, _ in boundaries if TWENTY < year <= LATEST]
        caveat = (f'<p class="small">* The way this is counted changed in {" and ".join(crossed)}. '
                  'No percentage change is given across those breaks.</p>' if crossed else "")
        note = f'<p class="note">{esc(f["note"])}</p>' if f["note"] else ""
        trows = [[y, fig(f["series"][y]["nominal"]), fig(f["series"][y]["real"]), fig(f["series"][y]["gdp"], kind="gdp")] for y in years]
        cards.append(f"""
<article class="card" id="area-{f["id"]}">
<h3>{esc(f["plain"])}</h3>
<p class="official">Official name: <span class="name">{esc(f["official"])}</span></p>
<p>{fig(latest[f["id"]])} in {LATEST}. Once rising prices are taken into account, how that compares with:</p>
<ul class="steps">{"".join(steps)}</ul>{caveat}
{view_chart(make, 340, 190)}
{note}
{table(f'{f["official"]}, {years[0]} to {LATEST}', ["Year", "Cash", "Inflation-adjusted", "Share of GDP"], trows)}
</article>""")
    return f"""
<section id="areas">
<h2>Each area over time</h2>
<p>Here is the spend on each area from {years[0]} to {LATEST}.
Each chart has its own scale, and each one starts at zero.
So compare the shapes, not the heights.</p>
<div class="cards">{"".join(cards)}</div>
</section>"""


def section_answers():
    h = funcs["health"]["series"]
    s, e = h[TEN]["real"], h[LATEST]["real"]
    comparable = s["v"] not in (None, 0) and e["v"] is not None
    up = comparable and e["v"] > s["v"]
    health_answer = (
        f'{"Yes" if up else "No"}. It was {fig(s)} in {TEN} (in {LATEST} prices) and {fig(e)} in {LATEST}: '
        f'{change(s, e)}. <a href="#area-health">See the chart</a>.'
        if comparable else 'Not enough data for this comparison. <a href="#area-health">See the table</a>.'
    )
    pensions = next(d for d in D["details"] if d["id"] == "pensions")
    qa = [
        ("What does the government spend the most on?",
         f'{esc(ranked[0]["plain"])}: {fig(latest[ranked[0]["id"]])} in {LATEST}. <a href="#hundred">See the split</a>.'),
        ("Out of every £100 spent on services, how much goes on health?",
         f'{share(latest["health"], services)}. <a href="#hundred">See every area</a>.'),
        ("How much goes on interest on government debt?",
         f'{fig(interest)} in {LATEST} (PESA outturn, subject to revision), of which {fig(D["debt_parts"][0])} is interest on loans to the government. <a href="#debt">See what is in it</a>.'),
        ("Has health spending gone up in the last ten years, once rising prices are taken into account?",
         health_answer),
        ("Is total spending a bigger share of the economy than ten years ago?",
         f'{"Yes" if total["gdp"]["v"] > agg[TEN]["tme"]["gdp"]["v"] else "No"}. {fig(total["gdp"], kind="gdp")} of GDP in {LATEST}, compared with {fig(agg[TEN]["tme"]["gdp"], kind="gdp")} in {TEN}. <a href="#decades">See every ten years since 1945</a>.'),
        ("How much goes on pensions, compared with defence?",
         f'Pensions paid in old age: {fig(pensions)}. Defence: {fig(latest["defence"])}. <a href="#items">See the selected items</a>.'),
        ("Which numbers are forecasts?",
         f'The Treasury totals after {LATEST} are forecasts. They have a dashed line and the word "Forecast". Earlier Treasury years are outturn and can be revised. The OBR series uses its own vintage; see the source notes.'),
        ("Where can I check a number myself?",
         'Tap or point at any number. You will see the table and cell it comes from. <a href="methods.html">How this site works</a> links to each file we use.'),
    ]
    items = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in qa)
    return f'<section id="answers"><h2>Quick answers</h2>{items}</section>'


CSS = """
:root{--ink:#1f2937;--soft:#4b5563;--line:#e5e7eb}
*{box-sizing:border-box}
:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
[id]{scroll-margin-top:12rem}
.skip{position:absolute;left:18px;top:8px;z-index:2;background:#fff;padding:8px;transform:translateY(-200%)}
.skip:focus{transform:none}
body{margin:0;font:17px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:#fff}
header,main,footer{max-width:760px;margin:0 auto;padding:0 18px;overflow-wrap:anywhere}
main,section,.card{min-width:0}
header{padding-top:28px}
h1{font-size:2rem;line-height:1.2;margin:.2em 0}
h2{font-size:1.45rem;margin:2.2em 0 .4em;border-top:2px solid var(--ink);padding-top:.6em}
h3{font-size:1.1rem;margin:1.2em 0 .2em}
.lead{font-size:1.2rem}
.small,.note,.official{font-size:.88rem;color:var(--soft)}
.note{border-left:3px solid var(--line);padding-left:10px}
data{border-bottom:1px dotted var(--soft);cursor:help;font-weight:600}
.chart{width:100%;height:auto;display:block;margin:.6em 0}
.chart text{font-size:13px;fill:var(--ink)}
.chart .axis{font-size:11px;fill:var(--soft)}
.bars{margin:.8em 0}
.bar{display:grid;grid-template-columns:minmax(0,38%) 1fr;gap:10px;align-items:center;margin:5px 0;font-size:.9rem}
.bl{text-align:right}
.bt{display:flex;align-items:center;gap:6px}
.bf{display:block;height:20px;background:var(--ink);min-width:2px}
.bv{white-space:nowrap;font-weight:600}
@media (max-width:560px){.bar{grid-template-columns:1fr;gap:2px;margin:9px 0}.bl{text-align:left}}
.legend{font-size:.9rem}.key{display:inline-block;width:12px;height:12px;margin:0 4px 0 10px;vertical-align:-1px}
.chart.small .axis{font-size:12px}
.steps{margin:.2em 0}
.narrow{display:none}
@media (max-width:560px){.wide{display:none}.narrow{display:block}}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px}
.card{border-top:1px solid var(--line)}
.card .chart .axis{font-size:12px}
.v{display:none}
body.view-real .v-real,body.view-nominal .v-nominal,body.view-gdp .v-gdp{display:inline}
.views{position:sticky;top:0;background:#fff;padding:8px max(18px,calc((100% - 724px)/2));border-bottom:1px solid var(--line);z-index:1}
.views button{font:inherit;font-size:.9rem;padding:4px 10px;margin:2px 4px 2px 0;border:1px solid var(--ink);background:#fff;color:var(--ink);border-radius:4px;cursor:pointer}
.views button[aria-pressed=true]{background:var(--ink);color:#fff}
.nojs .views button,.nojs .views br{display:none}
.tip{position:fixed;left:12px;right:12px;bottom:12px;max-width:600px;margin:0 auto;background:var(--ink);color:#fff;padding:10px 14px;border-radius:6px;font-size:.9rem;cursor:pointer}
.tbl{max-width:100%}
.table-scroll{overflow-x:auto;max-width:100%}
code{overflow-wrap:anywhere}
nav.page-links{display:flex;flex-wrap:wrap;gap:8px 16px}
.site-nav{max-width:760px;margin:0 auto;padding:8px 18px;display:flex;flex-wrap:wrap;gap:4px 16px;border-bottom:1px solid var(--line)}
.site-nav .brand{flex-basis:100%;font-weight:700;font-size:1.15rem;text-decoration:none}
.site-nav a,.page-links a,summary,.views button{min-height:44px;min-width:44px}
.site-nav a,.page-links a{display:inline-flex;align-items:center;padding:6px 4px}
summary{padding:10px 0}
.tax-scroll{overflow-x:auto;max-width:100%;margin:.8em 0}
.tax-scroll table{width:100%}
.tax-scroll th,.tax-scroll td{min-width:7rem}
.tax-scroll th:first-child{min-width:12rem}
.tax-scroll code{white-space:normal}
.tax-bars{margin:1em 0}
.tax-bar{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) auto;gap:8px;align-items:center;font-size:.88rem;margin:10px 0}
.tax-track{position:relative;height:22px;background:#fff;border-left:1px solid #6b7280}
.tax-bars[data-tax-scale=signed] .tax-track{border-left:0;background:linear-gradient(to right,#fff 49.6%,#6b7280 49.6%,#6b7280 50.4%,#fff 50.4%)}
.tax-fill{position:absolute;top:2px;height:18px;background:var(--ink)}
.tax-bar data{font-size:.85rem;white-space:nowrap}
#tax-sources code{overflow-wrap:anywhere}
@media(max-width:560px){.tax-bar{grid-template-columns:minmax(0,1fr) auto}.tax-bar>span:first-child{grid-column:1 / -1}}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.5em 0}
th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:right;vertical-align:top}
th[scope=row],caption{text-align:left}
caption{font-weight:600;padding:4px 0}
details{margin:.4em 0}
summary{cursor:pointer;color:var(--ink);font-weight:600}
.tbl summary{font-weight:400;font-size:.9rem;color:var(--soft)}
#answers details{border-bottom:1px solid var(--line);padding:6px 0}
a{color:var(--ink)}
footer{margin-top:3em;padding:1.5em 18px 3em;font-size:.85rem;color:var(--soft);border-top:1px solid var(--line)}
@media (max-width:480px){body{font-size:16px}h1{font-size:1.6rem}}
"""

JS = """
document.body.classList.remove('nojs');
var bs=document.querySelectorAll('.views button');
bs.forEach(function(b){b.addEventListener('click',function(){
  document.body.className='view-'+b.dataset.view;
  bs.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false')});
  document.getElementById('view-label').textContent=b.textContent;
})});
var tip=document.getElementById('tip');
document.querySelectorAll('data[title]:not([data-tax-id])').forEach(function(d){
  d.tabIndex=0;d.setAttribute('role','button');d.setAttribute('aria-controls','tip');
  function showSource(){if(!tip)return;tip.textContent=d.title;tip.hidden=false;}
  d.addEventListener('click',showSource);
  d.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){e.preventDefault();showSource();}
  });
});
if(tip)tip.addEventListener('click',function(){tip.hidden=true});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&tip){tip.hidden=true;}});
"""


def footer():
    pubs = {(s["publisher"], s["publication"], s["page"], s["published"]) for s in SRC.values()}
    if PAYERS is not None:
        pubs.update((s["publisher"], s["publication"], s["url"], s["published"])
                    for s in PAYERS["sources"].values())
    data = "; ".join(f'{esc(a)}, <a href="{esc(c)}">{esc(b)}</a> ({esc(d)})' for a, b, c, d in sorted(pubs))
    return f"""<footer>
<p class="name">Data: {data}.
Contains public sector information licensed under the
<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
<p><a href="index.html">Spending</a> · <a href="taxes.html">Taxes</a> · <a href="who-pays.html">Who pays</a> · <a href="methods.html">Methods</a> ·
<a href="methods.html#about">About</a> · <a href="methods.html#corrections">Corrections</a> ·
<a href="data/spending.json">Download spending data (JSON)</a></p>
</footer>"""


def page(title, body, views=False):
    if title == "Who pays tax? | UnpoliticalAF":
        # The shared footer owns the single licence notice on integrated pages.
        licence = ('<p>Contains public sector information licensed under the\n'
                   '<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">'
                   'Open Government Licence v3.0</a>.</p>')
        if body.count(licence) != 1:
            raise ValueError("Payer licence notice changed; check shared footer attribution")
        body = body.replace(licence, "")
    # Keep the tax renderer/checker contract intact. Add a distinct onward route
    # after its exact scope paragraph, without inventing remitter examples.
    if title == "Taxes, receipts and borrowing | UnpoliticalAF":
        marker = ('<p data-pid="who-pays-limit">This page does not show who pays.\n'
                  'These tables show receipts by tax type. They do not show how payments are split between people,\n'
                  'or who ultimately bears the cost. They give no percentages for who bears that cost.</p>')
        if body.count(marker) != 1:
            raise ValueError("Tax who-pays route anchor changed")
        body = body.replace(marker, marker + '<p><a href="who-pays.html">Who pays tax?</a> '
                            'shows separate Income Tax and household views. '
                            'Receipts and household tax costs are different measures.</p>')
    current = ("index.html" if views else "taxes.html" if title.startswith("Taxes,")
               else "who-pays.html" if title.startswith("Who pays tax?") else "methods.html")
    navigation = "".join(
        f'<a href="{target}"' + (' aria-current="page"' if target == current else '') + f'>{label}</a>'
        for target, label in (("index.html", "Spending"), ("taxes.html", "Taxes"),
                              ("who-pays.html", "Who pays"), ("methods.html", "Methods")))
    switch = ""
    if views:
        buttons = "".join(f'<button type="button" data-view="{k}" aria-pressed="{"true" if k == "real" else "false"}">{esc(t)}</button>'
                          for k, t in VIEWS)
        switch = (f'<nav class="views" aria-label="How to show money over time">Charts show: '
                  f'<span id="view-label" class="small">{esc(VIEWS[0][1])}</span><br>{buttons}</nav>')
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="icon" href="icon.svg">
<style>{CSS}</style>
</head>
<body class="view-real nojs">
<a class="skip" href="#main">Skip to content</a>
<nav class="site-nav" aria-label="Primary" data-pid="primary-nav">
<span class="brand">UnpoliticalAF</span>
{navigation}
</nav>
{switch}
{body}
{footer()}
<p id="tip" class="tip" role="status" hidden></p>
<script>{JS}</script>
</body>
</html>
"""


def index():
    s = SRC["pesa_ch4"]
    body = f"""<header>
<h1>Where the UK's public money goes</h1>
<p data-pid="newcomer-route">Start with a question. Follow a link for the figures and their limits.</p>
<p class="lead">In {LATEST} the UK public sector spent {fig(total["nominal"])}.
This page shows what it went on, and how that has changed.
It uses the government's own figures.</p>
<p class="small">The figures are from <cite>HM Treasury, {esc(s["publication"])}</cite>, out on {esc(s["published"])}.
PESA treats {LATEST} as outturn; it can be revised.
Tap a number, or use Tab then Enter, to see its source. "bn" means billion.</p>
</header>
<main id="main">
<section id="start" data-pid="newcomer-questions"><h2>What would you like to know?</h2>
<dl>
<dt>Where does the money go?</dt><dd><a href="#hundred">Spending: see the main areas</a>.</dd>
<dt>How has it changed?</dt><dd><a href="#total">How spending changed: cash, prices and GDP</a>.</dd>
<dt>How is the money raised?</dt><dd><a href="taxes.html">Taxes: receipts, borrowing and debt</a>.</dd>
<dt>Who pays?</dt><dd><a href="who-pays.html">Who pays: people and households</a>, with each view's limits.</dd>
</dl></section>
<nav class="page-links" aria-label="On this page">
<a href="#answers">Quick answers</a><a href="#hundred">Spending by area</a>
<a href="#total">Total spending</a><a href="#decades">Since 1945</a>
<a href="#areas">Area histories</a><a href="methods.html#check">How to check a figure</a>
</nav>
{section_answers()}
{section_hundred()}
{section_items()}
{section_total()}
{section_decades()}
{section_areas()}
</main>"""
    return page("Where the UK's public money goes | UnpoliticalAF", body, views=True)


def section_corrections():
    corrections = CORRECTIONS
    if corrections:
        items = "".join(
            f'<li><strong>Date:</strong> {esc(c["date"])}<br>'
            f'<strong>Page:</strong> {esc(c["page"])}<br>'
            f'<strong>What was wrong:</strong> {esc(c["what was wrong"])}<br>'
            f'<strong>What changed:</strong> {esc(c["what changed"])}</li>'
            for c in corrections)
        body = f"<ul>{items}</ul>"
    else:
        body = "<p>No corrections yet.</p>"
    return f'<section id="corrections"><h2>Corrections</h2>{body}</section>'


def reconciliation_table():
    selected = [r for r in D["reconciliations"]
                if r["period"] == LATEST or r["id"] in
                ("history-current/2015-16", "history-functions/2015-16", "OBR-borrowing/1975-76")]
    rows = []
    def amount(report, field):
        value = report[field]
        if value is None:
            return "No bound set" if field == "quantisation_budget" else "Not testable"
        refs = " ".join(o["ref"] for o in report["operands"])
        return (f'<data value="{value}" data-report-id="{esc(report["id"])}" '
                f'data-report-field="{field}" data-calc="reconciliation" data-ref="{esc(refs)}">'
                f'{value:.6f}</data>')
    for report in selected:
        refs = "; ".join(o["ref"] for o in report["operands"])
        excluded = "; ".join(report["excluded_refs"]) or "None"
        missing = "; ".join(report["missing_operands"]) or "None"
        rows.append([f'{esc(report["id"])}<br><small>{esc(report["basis"])}</small>',
                     amount(report, "residual"), amount(report, "quantisation_budget"),
                     f'{esc(report["unit"])}<br>{esc(report["outcome"])}',
                     f'<small>Operands: {esc(refs)}<br>Excluded subsets: {esc(excluded)}<br>Missing: {esc(missing)}</small>'])
    return table("Source reconciliation ledger: latest year and selected historical checks",
                 ["Check and scope", "Signed residual", "Rounding budget", "Unit and result", "Source cells"], rows)


def section_payer_methods():
    global PAYERS
    if PAYERS is None:
        # Compatibility callers bind spending with configure(data). Resolve the
        # missing family from this root, and cache it only after validation.
        from payer_projection import project
        from check_payers import validate_data
        payers = project(ROOT)
        validate_data(ROOT, payers)
        PAYERS = payers
    sources = PAYERS["sources"]
    by_source = {sid: next(v for v in PAYERS["values"] if v["source_id"] == sid)
                 for sid in ("hmrc", "ons")}
    links = "".join(
        f'<li><a href="{esc(s["url"])}"><cite>{esc(s["publication"])}</cite></a>. '
        f'Published or updated: {esc(s["published"])}.</li>' for s in sources.values())
    return f'''<section id="payer-methods" data-pid="payer-methods">
<h2>Who pays: two different views</h2>
<p>The <a href="who-pays.html">Who pays page</a> keeps the two views apart.
<a href="data/payers.json">Download the selected payer data</a> for source cells, hashes, notes and labels.
No next release date is recorded in this source set.</p>
<p>HMRC Table 2.4 uses {esc(by_source['hmrc']['period'])}, {esc(by_source['hmrc']['status'].lower())}.
It covers UK people with a positive Income Tax bill, not people with no bill.
It ranks their income assessable for tax before deductions and allowances. This is not a rank of wealth.
Shares are of Income Tax due, not cash received or all UK taxes.
The top group sits inside a wider top group. The bottom half and top groups are separate.
Do not add the shares.</p>
<p>ONS uses {esc(by_source['ons']['period'])}, {esc(by_source['ons']['status'].lower())}.
It covers people in UK private households. It ranks them by household income after direct taxes,
adjusted for household size and needs. The fifths hold about equal numbers of people, not households.
They are not the HMRC groups.</p>
<p>Gross income includes cash benefits. Direct taxes are taken off to give disposable income.
The income table uses gross income as the whole. Its combined shares are published values,
not sums of rounded parts. The other table uses household spending as the whole for indirect taxes.
Neither is a tax rate on each purchase.</p>
<p>Deferred lump-sum direct-tax payments can put people with high gross income in a low disposable-income group.
Spending can exceed current income through savings or borrowing. Low income can be short-lived.
Sampling and measurement also affect the results. The spending view helps show why an income ratio needs care.
Neither view gives a lifetime tax burden.</p>
<p>Sending tax to HMRC is not the same as bearing its cost. ONS assigns final and intermediate indirect taxes
fully to consumers in this model. That includes employer National Insurance.
Employee and self-employed National Insurance are direct taxes. The OBR receipts total for National Insurance
cannot be put wholly in either group. Actual costs can fall on firms, workers, buyers and others.</p>
<p>The technical report covers FYE 2019; sections 7 and 10 explain the model's limits.
Its publication date is {esc(sources['ons_method']['published'])}. The QMI date is {esc(sources['ons_qmi']['published'])}.
These older methods do not prove that each detail is current. Current workbook notes take priority.
Direct taxes here include student-loan repayments. Corporation Tax is not assigned to households.
This is not all UK taxes. Suppressed cells stay suppressed, not zero.</p>
<p>Do not join these views into a top-group all-tax burden, one average, or a match to receipts.
Each source link below gives its own version and full official URL.</p>
<ul class="name">{links}</ul>
</section>'''


def section_basics_methods():
    sources = BASICS_SOURCES
    if sources is None:
        # Legacy configure(data)/methods() callers also need real, checked guidance.
        # The explicit build path supplies its own root-validated register instead.
        import json
        from check_basics import validate_sources
        validate_sources(ROOT)
        sources = json.loads((ROOT / "data/tax-basics/sources.json").read_text(encoding="utf-8"))
    # These headings identify the retained text used for the qualitative copy.
    locators = (
        "Income Tax: Overview; Income Tax allowances and reliefs",
        "National Insurance: Overview; Who pays National Insurance; National Insurance classes",
        "PAYE for employers: Introduction to PAYE; Deductions from their pay; Reporting pay and deductions; Paying HMRC",
        "Scottish Government: Income Tax",
        "How VAT works: Overview; Your responsibilities as a VAT-registered business; What VAT is charged on; How much VAT you must charge",
        "Welsh Income Tax: Income Tax in Wales; Who pays the Welsh rates; How you pay",
        "Corporation Tax: Overview; Profits you pay Corporation Tax on",
    )
    rows = "".join(
        f'<li><a href="{esc(s["url"])}">{esc(locator)}</a>'
        f'<p class="small">Original response SHA-256: <code>{esc(s["sha256"])}</code>. '
        f'Retained copy SHA-256: <code>{esc(s["stored_sha256"])}</code>.</p></li>'
        for s, locator in zip(sources["sources"], locators))
    return f'''<section id="tax-guidance" data-pid="tax-guidance-methods">
<h2>Where the tax definitions come from</h2>
<p>Official guidance explains the tax rules. It is not the source of the household percentages or receipt totals.
We checked these guidance pages on 30 October 2026. They are living guidance; no publication date is established.
The next update is unknown. We use no current rates or personal tax examples.</p>
<p>The short definitions link to the official page and name the relevant heading.
The OBR group limits and ONS model limits remain beside their own figures.
These definitions do not describe who bears every tax cost.</p>
<details><summary>Guidance headings and retained file hashes</summary>
<p>Each link opens the official guidance. The headings below locate the text we used.
The hashes identify the original response and its lossless retained copy.
A later download can change because these are living pages. Private source registers and raw responses are not public downloads.</p>
<ul class="name">{rows}</ul></details></section>'''


def methods():
    src_rows = "".join(
        f'<tr><th scope="row"><a href="{esc(s["url"])}">{esc(Path(s["file"]).name)}</a></th><td>{esc(s["published"])}</td>'
        f'<td>{esc(s["downloaded"])}</td><td><code>{esc(s["sha256"][:16])}…</code></td></tr>' for s in SRC.values())
    checks = "".join(f"<li>{esc(c)}</li>" for c in D["checks"])
    ledger = reconciliation_table()
    body = f"""<header><h1>How this site works</h1></header>
<main id="main">
<section id="about">
<h2>About</h2>
<p>John Ross runs this site.</p>
</section>
<h2>What this site is for</h2>
<p>This site shows where UK public money goes, in plain words.
It uses official figures and nothing else.
It does not say if any spend is right or wrong.
It does not back any party.</p>
<section id="check"><h2>How to check a figure</h2>
<ul>
<li>Find the official source publication, table and version in the source note.</li>
<li>Check the fiscal year, unit, scale and definitions for that cell.</li>
<li>Read the source notes: an actual, estimate and forecast are not the same. A forecast is not observed spending.</li>
<li>Check reconciliation with the published total. Allow for rounding, exclusions and scope differences. Rounded parts may not add up exactly.</li>
</ul>
<p>When figures are published, they can later be revised. The dates below show which files we use.
No next release date has been recorded in this port.</p>
</section>
<h2>Where the numbers come from</h2>
<p>Most numbers come from one report by the Treasury:
<a href="{esc(SRC["pesa_ch4"]["page"])}"><cite>{esc(SRC["pesa_ch4"]["publication"])}</cite></a> (PESA).
These are <cite>Accredited Official Statistics</cite>.
They cover all public bodies across the whole UK.
That means central government, local councils and firms the state owns.</p>
<p>The figures every ten years since 1945 come from the <cite>Office for Budget Responsibility</cite> (OBR).
The OBR is the official body that checks the government's figures.
Its <cite>{esc(SRC["obr_databank"]["publication"])}</cite> gives spending, income, borrowing and debt.
Its <cite>{esc(SRC["obr_hist"]["publication"])}</cite> gives spending on five areas.
The OBR says the second one is not National Statistics.
It joins up old sources, and it made its own choices to do that.</p>
<p>The Treasury counts years through {LATEST} as outturn. Later total-spending years are forecasts.
The price base and forecast date come from the notes in <cite>PESA {esc(D["pesa_context"]["status_ref"])},
{esc(D["pesa_context"]["deflator_ref"])} and {esc(D["pesa_context"]["forecast_ref"])}</cite>.
The newer OBR sheet has mixed dates in its notes. It names both March and October forecasts.
We keep the conflict, rather than call all values observed data.
Each series cites its own numerator and GDP update notes.
See <cite>Public finances since 1900, B2 and B139 to B148</cite>.</p>
<p>The older OBR area series joins sources. Its status is uncertain.
Its 2022-23 extrapolations are estimates; our decade tables end in 2015-16
(<cite>Contents, D51 to D56</cite>).</p>
<div class="table-scroll" role="region" aria-label="Source files" tabindex="0"><table><caption>Source files</caption><thead><tr><th scope="col">File</th><th scope="col">Published</th><th scope="col">Downloaded</th><th scope="col">SHA-256 (start)</th></tr></thead>
<tbody>{src_rows}</tbody></table></div>
<p>Each file has a unique code, called a hash. The full codes are in <a href="data/spending.json">the data file</a>.
You can download the files and check the codes match.
If they match, the files have not been changed.</p>
<section id="provenance">
<h2>The record behind each value</h2>
<p>The data file has a <code>provenance</code> record for each value.
Its <code>source_id</code> links to the source file, full hash, publication and dates in <code>sources</code>.
The record names the exact cell, year, unit, scale, price basis, UK coverage and accounting scope.
It also names the label, year and unit cells used to check its meaning.</p>
<p>The <code>source_cells</code> records keep raw values, formulas and formats.
A blank, a literal dash and a numeric zero stay distinct.
The source notes do not define every dash in the PESA tables. We keep those as missing.
A number format that shows zero as a dash does not turn that zero into a missing value.</p>
<p>The <code>formulae</code> and <code>derived</code> records give each formula and its ordered operands.
Money in Table 5.2 is in millions; we divide by a thousand to show billions.
Changes that cross a known definition break are not given as percentages.
The data record names the source note for each break.
Shares use spending on services as the whole. Changes use the same series in two years.
Neither calculation fills a missing value.</p>
<p>The OBR publication dates in the catalogue were read from file headers.
They have not been verified as release dates. Their retrieval dates are recorded too.</p>
</section>
<h2>How the numbers are checked</h2>
<p>A script reads the Treasury files. No number is typed in by hand.
The build checks the following sums before it writes the pages:</p>
<ul class="name">{checks}</ul>
<p>Then a second script reads every number on the page.
It checks each one against the cell it names in the source file.
The source files and sums can be checked again with the build commands in the README.</p>
<h3>Residuals and limits</h3>
<p>A residual is the signed sum of the source operands. We do not change a value to make a sum fit.
For PESA, the budget is half the stored rounding step for each operand, added together.
The checker first checks that each value lies on that source grid.
This is a rounding budget, not a bound on how well the source measures spending.</p>
<p>OBR ratios keep more digits than we show. Their identities use those stored digits and a small allowance for computer arithmetic.
The one-decimal format is not a source error bound.
Checks with missing operands stay untested. The source's “other” series is already a residual, so its sum is not an independent measure of accuracy.</p>
<p>The OBR and PESA comparison has different vintages and GDP bases.
We show its difference with no pass/fail bound. There is no established half-point error budget.</p>
{ledger}
<p>The full <code>reconciliations</code> ledger in <a href="data/spending.json">the data file</a>
has all years, signed operands, budgets, residuals and exclusions.
Selected items sit inside function totals. They are never added to those totals.
The historical pensioner subsets are excluded from the function sum to avoid counting them twice.</p>
<section id="tax-methods" data-pid="tax-methods">
<h2>Taxes, receipts and debt</h2>
<p>The <a href="taxes.html">Taxes page</a> uses the OBR's current receipts and aggregate tables.
The source version is <cite>{esc(SRC["obr_databank"]["publication"])}</cite>.
<a href="data/taxes.json">Download the selected tax data</a> for full hashes, exact cells, years, units, status and formulas.
The official <a href="{esc(SRC["obr_databank"]["url"])}">OBR workbook download</a> is the source.
The <a href="taxes.html#tax-sources">source notes</a> keep each table's own status and GDP notes.</p>
<p>The six receipt groups use ordered source rows:
income tax Q+R+S; National Insurance AB; VAT C+D; corporation tax U+V;
other taxes AH minus those named groups; and receipts outside taxes AG−AH.
Their shares use all current public receipts AG as the whole, not tax AH.
No total is added to its own parts. Negative source values keep their signs.</p>
<p>VAT includes refunds and is a source-based grouping, not household VAT burden.
The notes do not explicitly settle refund classification within National Accounts taxes.
Corporation tax includes related charges.
Other taxes is a remainder, partly from a mixed line that is not itemised.
Non-tax is a difference, not the mixed AF line relabelled.
A sum that closes does not prove these classifications.</p>
<p>The balance uses spending D minus receipts C and checks borrowing O in the same OBR aggregate table.
PESA is a different vintage and presentation. We do not subtract OBR receipts from PESA spending.
Debt X is a stock at end March; borrowing is an annual accrual flow.
Debt changes need not equal borrowing.
Published debt shares use March-centred GDP. We keep them as published, even when a cash ratio differs.</p>
<p>The history shows total receipts, spending, borrowing and debt, not history by tax type.
It starts in 1999-00, the first year of the current receipt table.
It does not splice in the older historical receipt data.
Outturn can be revised. Later forecasts are shown apart from outturn, with their own source notes.
No inflation-adjusted tax view has been verified.
A GDP share is not a real-terms measure, and can rise when GDP falls.</p>
<p>These tables show receipts by tax type. They do not show how payments are split between people,
or who ultimately bears the cost.</p>
<p><a href="who-pays.html">Who pays tax?</a> gives two separate official views.</p>
</section>
{section_payer_methods()}
{section_basics_methods()}
<h2>Words used on this site</h2>
<dl>
<dt><strong>Total spending</strong></dt><dd>The Treasury calls this <cite>Total Managed Expenditure</cite>.
It is all the public sector spends, including building work and interest.</dd>
<dt><strong>Spending on services</strong></dt><dd>Total spending split into areas such as health and defence.
It leaves out some book-keeping items that do not belong to one area.</dd>
<dt><strong>Adjusted for inflation</strong></dt><dd>Prices rise over time, so £1 bought more in the past.
We show older amounts in {BASE} prices so you can compare years fairly.
This uses the same price measure as the Treasury tables.</dd>
<dt><strong>Share of GDP</strong></dt><dd>GDP is the value of all the goods and services made in the UK in a year.
This shows spending as a part of that.</dd>
<dt><strong>Comparing years</strong></dt><dd>We compare in steps of ten years, counting back from {LATEST}.
So we use {TEN}, {TWENTY} and so on, back to {H["decades"][0]}. We do not pick years by hand.</dd>
<dt><strong>Areas</strong></dt><dd>The areas are the ones the United Nations uses, called <cite>COFOG</cite>.
We give each one a plain name next to its official name.</dd>
</dl>
<h2>What this site does not cover yet</h2>
<ul>
<li>A complete account of who bears all UK tax costs.</li>
<li>What each party plans to do.</li>
<li>Spending per person or per home.</li>
</ul>
{section_corrections()}
<h2>Report an error</h2>
<p>A way to report errors is coming soon.</p>
</main>"""
    return page("How this site works | UnpoliticalAF", body)
