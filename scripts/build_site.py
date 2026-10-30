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
    """A sourced figure from the data."""
    v = entry["v"]
    if v is None:
        return '<span class="small">not given</span>'
    shown = text if text is not None else money(v, kind)
    return (f'<data value="{v}" data-ref="{entry["ref"]}" title="Source: {esc(where(entry["ref"]))}">'
            f"{esc(shown)}</data>")


def change(old, new):
    """Percentage change from old to new, with both source cells named."""
    if old["v"] in (None, 0) or new["v"] is None:
        return '<span class="small">not given: no comparable change</span>'
    c = (new["v"] - old["v"]) / old["v"] * 100
    return (f'<data value="{c:.4f}" data-calc="change" data-ref="{old["ref"]} {new["ref"]}" '
            f'title="Calculated from {esc(where(old["ref"]))} and {esc(where(new["ref"]))}">'
            f'{abs(c):.0f}% {"more" if c > 0 else "less"}</data>')


def share(part, whole, text_fn=lambda s: f"£{s:.0f}"):
    """A figure calculated as part / whole x 100, with both source cells named."""
    if part["v"] is None or whole["v"] in (None, 0):
        return '<span class="small">not given: no comparable share</span>'
    s = part["v"] / whole["v"] * 100
    refs = f'{part["ref"]} {whole["ref"]}'
    return (f'<data value="{s:.4f}" data-calc="share" data-ref="{refs}" '
            f'title="Calculated from {esc(where(part["ref"]))} and {esc(where(whole["ref"]))}">'
            f"{esc(text_fn(s))}</data>")


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
    out = [f'<details class="tbl"><summary>Show the numbers in a table</summary><table><caption>{esc(caption)}</caption><thead><tr>']
    out += [f'<th scope="col">{esc(h)}</th>' for h in head]
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f'<th scope="row">{c}</th>' if i == 0 else f"<td>{c}</td>" for i, c in enumerate(row)) + "</tr>")
    out.append("</tbody></table></details>")
    return "".join(out)


# ---------------------------------------------------------------- page sections

def configure(data, corrections=None):
    """Bind a validated in-memory dataset; importing this module reads no files."""
    global D, SRC, LATEST, BASE, SHEET_SOURCE, VIEWS, CORRECTIONS
    global agg, funcs, total, services, interest, latest, ranked, years, agg_years, TEN, TWENTY, H, first_forecast
    D = data
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
    trows.append(["<strong>Total spending on services</strong>", fig(services), "£100.00"])
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
{hbar(rows)}
{table(f"Largest items, {LATEST}", ["Item", "Spent"], trows)}
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
<h2>Total spending since 1985</h2>
<p>In {LATEST} the public sector spent {fig(total["nominal"])} in all.
That was {fig(total["gdp"], kind="gdp")} of the value of all the goods and services made in the UK that year (GDP).
Ten years earlier, in {TEN}, it was {fig(then["gdp"], kind="gdp")}.
<a href="#decades">See every ten years back to 1945</a>.</p>
{view_chart(make)}
<p class="small">Years after {LATEST} are a forecast. They have a dashed line and a grey background.
The forecast is from the <cite>Office for Budget Responsibility</cite>, made on 3 March 2026.
From 2020-21, the figures include help given during Covid and when prices rose fast.
(<cite>PESA Table 4.2, note 2</cite>)</p>
{table("Total Managed Expenditure, 1985-86 to 2028-29", ["Year", "Cash", f"Adjusted for inflation ({BASE} prices)", "Share of GDP"], trows)}
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
The latest year may be an estimate; this port has not checked each cell's status. Read the source file notes.
The March 2026 forecast note above applies to the Treasury totals, not this OBR file.
For {last} it gives spending of {pct(sp[last])} of GDP; the Treasury gives {fig(total["gdp"], kind="gdp")}.
Missing figures are shown as “not given”, not zero.</p>
<h3>Spending on five areas</h3>
<p>Here is the spend on five big areas, every ten years.
The newest year here is {dec[-2]}, because this data set stops in {H["areas_last_year"]}.
These areas are counted in a different way from the ones higher up this page, so the numbers do not match them.</p>
<div class="cards">{"".join(cards)}</div>
<p class="small">Source: <cite>{esc(hist_src["publisher"])}, {esc(hist_src["publication"])}</cite>.
The OBR says these are not National Statistics. It made its own choices to join up older and newer sources.
There are no health or education figures for 1945-46. "Interest on government debt" here is central government
interest only, after taking off the Bank of England's bond-buying scheme.</p>
</section>"""


BREAKS = {"education": ("2011-12", "Student loans removed"), "economic": ("2015-16", "Network Rail added")}


def section_areas():
    cards = []
    for f in ranked:
        brk = BREAKS.get(f["id"])
        breaks = [(years.index(brk[0]), brk[1])] if brk else []

        def make(view, f=f, breaks=breaks):
            return line(years, [f["series"][y][view]["v"] for y in years], breaks=breaks, width=340,
                        height=190, small=True, unit=view)
        steps = []
        for then in (TEN, TWENTY):
            mark = " *" if brk and then < brk[0] else ""
            steps.append(f"<li>{then}: {change(f['series'][then]['real'], f['series'][LATEST]['real'])}{mark}</li>")
        caveat = (f'<p class="small">* The way this is counted changed in {brk[0]}, so this comparison is not exact.</p>'
                  if brk and TWENTY < brk[0] else "")
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
{table(f'{f["official"]}, 2003-04 to {LATEST}', ["Year", "Cash", "Inflation-adjusted", "Share of GDP"], trows)}
</article>""")
    return f"""
<section id="areas">
<h2>Each area over time</h2>
<p>Here is the spend on each area from 2003-04 to {LATEST}.
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
header,main,footer{max-width:760px;margin:0 auto;padding:0 18px}
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
.tbl{overflow-x:auto;max-width:100%}
code{overflow-wrap:anywhere}
nav.page-links{display:flex;flex-wrap:wrap;gap:8px 16px}
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
document.querySelectorAll('data[title]').forEach(function(d){
  d.tabIndex=0;d.setAttribute('role','button');d.setAttribute('aria-controls','tip');
  function showSource(){tip.textContent=d.title;tip.hidden=false;}
  d.addEventListener('click',showSource);
  d.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){e.preventDefault();showSource();}
  });
});
tip.addEventListener('click',function(){tip.hidden=true});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){tip.hidden=true;}});
"""


def footer():
    pubs = {(s["publisher"], s["publication"], s["page"], s["published"]) for s in SRC.values()}
    data = "; ".join(f'{esc(a)}, <a href="{esc(c)}">{esc(b)}</a> ({esc(d)})' for a, b, c, d in sorted(pubs))
    return f"""<footer>
<p class="name">Data: {data}.
Contains public sector information licensed under the
<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
<p><a href="index.html">Where the money goes</a> · <a href="methods.html">How this site works</a> ·
<a href="methods.html#about">About</a> · <a href="methods.html#corrections">Corrections</a> ·
<a href="data/spending.json">Download all the data (JSON)</a></p>
</footer>"""


def page(title, body, views=False):
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
<p class="lead">In {LATEST} the UK public sector spent {fig(total["nominal"])}.
This page shows what it went on, and how that has changed.
It uses the government's own figures.</p>
<p class="small">The figures are from <cite>HM Treasury, {esc(s["publication"])}</cite>, out on {esc(s["published"])}.
PESA treats {LATEST} as outturn; it can be revised.
Tap a number, or use Tab then Enter, to see its source. "bn" means billion.</p>
</header>
<main id="main">
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


def methods():
    src_rows = "".join(
        f'<tr><th scope="row"><a href="{esc(s["url"])}">{esc(Path(s["file"]).name)}</a></th><td>{esc(s["published"])}</td>'
        f'<td>{esc(s["downloaded"])}</td><td><code>{esc(s["sha256"][:16])}…</code></td></tr>' for s in SRC.values())
    checks = "".join(f"<li>{esc(c)}</li>" for c in D["checks"])
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
<div class="tbl"><table><caption>Source files</caption><thead><tr><th scope="col">File</th><th scope="col">Published</th><th scope="col">Downloaded</th><th scope="col">SHA-256 (start)</th></tr></thead>
<tbody>{src_rows}</tbody></table></div>
<p>Each file has a unique code, called a hash. The full codes are in <a href="data/spending.json">the data file</a>.
You can download the files and check the codes match.
If they match, the files have not been changed.</p>
<h2>How the numbers are checked</h2>
<p>A script reads the Treasury files. No number is typed in by hand.
The build checks the following sums before it writes the pages:</p>
<ul class="name">{checks}</ul>
<p>Then a second script reads every number on the page.
It checks each one against the cell it names in the source file.
The source files and sums can be checked again with the build commands in the README.</p>
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
<li>Which taxes the money comes from.</li>
<li>What each party plans to do.</li>
<li>Spending per person or per home.</li>
</ul>
{section_corrections()}
<h2>Report an error</h2>
<p>A way to report errors is coming soon.</p>
</main>"""
    return page("How this site works | UnpoliticalAF", body)

