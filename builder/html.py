"""Shared HTML pieces: page shell, number formatting, accessible charts and tables.

Every number shown on a page is wrapped in <data value=".." data-fact="id">,
so the checker can confirm the text matches the stored fact and its source.
Charts are plain HTML/CSS or inline SVG drawn at build time, so they work
without JavaScript, and each one sits next to a complete table.
"""
import math
import re
from html import escape

SITE = "Unpolitical"

CSS = """
:root{--ink:#1d1d1f;--muted:#555b61;--line:#d5d8db;--soft:#f3f4f5;--bar:#3d4852;--bar2:#9aa3ab;--focus:#1a5fb4;--warn:#fff7e0;--warnline:#b58900;--bg:#fff}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:#1d4f7a;text-underline-offset:2px}
a:focus-visible,summary:focus-visible,select:focus-visible,button:focus-visible,.tablewrap:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
header.site{border-bottom:1px solid var(--line);background:#fafafa}
header.site .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:4px 16px;padding-top:10px;padding-bottom:10px}
.brand{font-weight:700;color:var(--ink);text-decoration:none;font-size:1.05rem;margin-right:auto}
nav.main ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:0 4px}
nav.main a{display:inline-block;padding:10px 8px;min-height:44px;color:var(--ink);text-decoration:none;font-size:.95rem}
nav.main a[aria-current=page]{text-decoration:underline;text-decoration-thickness:2px;font-weight:600}
.wrap{max-width:46rem;margin:0 auto;padding-left:16px;padding-right:16px}
main{padding-bottom:48px}
h1{font-size:1.75rem;line-height:1.2;margin:28px 0 12px}
h2{font-size:1.3rem;line-height:1.25;margin:36px 0 10px;padding-top:12px;border-top:1px solid var(--line)}
h3{font-size:1.08rem;margin:24px 0 8px}
p{margin:0 0 12px}
.lede{font-size:1.1rem}
.answer{background:var(--soft);border-left:4px solid var(--bar);padding:12px 14px;margin:12px 0 16px}
.answer p:last-child{margin-bottom:0}
.small,.src{font-size:.88rem;color:var(--muted)}
.src{margin-top:6px}
.note{border-left:4px solid var(--line);padding:4px 12px;margin:12px 0;color:var(--muted);font-size:.95rem}
.limit{background:var(--warn);border-left:4px solid var(--warnline);padding:10px 12px;margin:12px 0;font-size:.95rem}
.illustration{border:2px dashed var(--bar2);padding:12px 14px;margin:20px 0;background:#fff}
.illustration .tag{display:inline-block;font-size:.8rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:var(--ink);color:#fff;padding:2px 8px;margin-bottom:6px}
.bars{margin:12px 0 4px;padding:0;list-style:none}
.bars li{margin:0 0 8px}
.bars .lab{display:flex;justify-content:space-between;gap:12px;font-size:.95rem}
.bars .lab span:last-child{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
.bars .track{height:12px;background:var(--soft);margin-top:3px}
.bars .fill{height:12px;background:var(--bar)}
.bars .fill.alt{background:var(--bar2)}
.bars .fill.fc{background:repeating-linear-gradient(45deg,var(--bar2) 0 4px,#fff 4px 7px)}
table{border-collapse:collapse;width:100%;font-size:.92rem;margin:8px 0 12px;font-variant-numeric:tabular-nums}
caption{text-align:left;font-weight:600;padding:4px 0 6px}
th,td{border-bottom:1px solid var(--line);padding:6px 6px;text-align:right;vertical-align:top}
th:first-child,td:first-child{text-align:left}
thead th{border-bottom:2px solid var(--ink)}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
details{margin:8px 0 16px}
summary{cursor:pointer;min-height:44px;display:flex;align-items:center;color:#1d4f7a;text-decoration:underline;text-underline-offset:2px}
figure{margin:12px 0}
figcaption{font-size:.9rem;color:var(--muted)}
svg text{font:15px -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;fill:#333}
.key{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.88rem;color:var(--muted);margin:4px 0}
.key i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px;background:var(--bar)}
.key i.b{background:var(--bar2)}.key i.d{background:repeating-linear-gradient(90deg,var(--bar) 0 4px,transparent 4px 7px)}
.cards{list-style:none;padding:0;margin:16px 0;display:grid;gap:12px}
.cards li{border:1px solid var(--line);padding:14px}
.cards h2,.cards h3{margin:0 0 6px;border:0;padding:0;font-size:1.1rem}
.cards p{margin:0 0 8px}
.yearnav{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px;padding:0;list-style:none}
.yearnav a,.yearnav span{display:inline-flex;align-items:center;justify-content:center;min-width:52px;min-height:44px;padding:0 8px;border:1px solid var(--line);text-decoration:none}
.yearnav span[aria-current]{background:var(--ink);color:#fff;border-color:var(--ink)}
.pager{display:flex;justify-content:space-between;gap:12px;margin:12px 0}
.pager a{display:inline-flex;align-items:center;min-height:44px}
form.pick{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:flex-end;background:var(--soft);padding:12px;margin:12px 0}
form.pick label{display:flex;flex-direction:column;font-size:.9rem}
select,button{font:inherit;min-height:44px;padding:6px 8px;border:1px solid #767676;background:#fff;color:var(--ink)}
button{background:var(--ink);color:#fff;border-color:var(--ink);padding:6px 16px}
.missing{color:var(--muted);font-style:italic}
a.card{display:block;border:1px solid var(--line);padding:14px;color:var(--ink);text-decoration:none;background:#fff}
a.card:hover h2,a.card:focus h2{text-decoration:underline}
a.card h2{color:#1d4f7a}
a.button{display:inline-flex;align-items:center;min-height:44px;padding:6px 16px;background:var(--ink);color:#fff;text-decoration:none}
.source{border-top:1px solid var(--line);padding-top:8px}
.source dl{display:grid;grid-template-columns:8rem 1fr;gap:4px 12px;font-size:.92rem}
.source dt{color:var(--muted)}.source dd{margin:0;overflow-wrap:anywhere}
.hash{font-size:.8rem}
.change-up::before{content:"▲ ";font-size:.75em}.change-down::before{content:"▼ ";font-size:.75em}
footer{border-top:1px solid var(--line);padding:16px 0 32px;font-size:.88rem;color:var(--muted)}
@media (min-width:640px){.cards{grid-template-columns:1fr 1fr}h1{font-size:2rem}}
@media print{nav.main,.skip,form.pick{display:none}details{display:block}}
"""

NAV = [
    ("index.html", "Home"),
    ("spending.html", "Spending"),
    ("taxes.html", "Taxes"),
    ("who-pays.html", "Who pays"),
    ("household-tax.html", "Tax and income"),
    ("life/index.html", "Year by year"),
    ("methods.html", "Sources"),
]


def esc(s):
    return escape(str(s), quote=True)


def page(path, title, body, description="", scripts=""):
    depth = path.count("/")
    up = "../" * depth
    nav = "".join(
        f'<li><a href="{up}{href}"{" aria-current=page" if href == path or (href == "life/index.html" and path.startswith("life/")) else ""}>{esc(label)}</a></li>'
        for href, label in NAV)
    full_title = SITE if path == "index.html" else f"{title} – {SITE}"
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description or title)}">
<link rel="icon" href="{up}icon.svg" type="image/svg+xml">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="{up}index.html">{SITE}</a>
<nav class="main" aria-label="Main"><ul>{nav}</ul></nav></div></header>
<main id="main" class="wrap">
{body}
</main>
<footer><div class="wrap">
<p>{SITE} is an independent guide built only from official UK statistics. It does not support or oppose any party or policy. Every figure links to its source on the <a href="{up}methods.html">sources and methods</a> page.</p>
<p>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
</div></footer>
{scripts}
</body>
</html>
"""


# ------------------------------------------------------------------ numbers

def fmt(value, kind):
    """Format a number for display. kind controls rounding and units."""
    if value is None:
        return None
    if kind == "bn":
        return f"£{value:,.1f}bn" if abs(value) < 100 else f"£{value:,.0f}bn"
    if kind == "bn1":
        return f"£{value:,.1f}bn"
    if kind == "pct":
        return f"{value:.1f}%"
    if kind == "pct0":
        return f"{value:.0f}%"
    if kind == "pounds":
        return f"£{value:,.0f}"
    if kind == "pounds2":
        return f"£{value:,.2f}"
    if kind == "per100":
        return f"£{value:.0f}"
    if kind == "dp1":
        return f"{value:.1f}"
    if kind == "millions":
        return f"{value / 1000:.1f} million"
    if kind == "millions_people":
        return f"{value / 1000:.1f} million"
    if kind == "millions_raw":
        return f"{value / 1_000_000:.1f} million"
    if kind == "int":
        return f"{value:,.0f}"
    raise ValueError(kind)


class Num:
    """Formats facts into <data> elements and remembers every fact used on a page."""

    def __init__(self, facts):
        self.facts = facts
        self.used = set()
        self.absent = set()

    def __call__(self, fid, kind):
        if fid not in self.facts:
            self.absent.add(fid)
            return '<span class="missing">not available</span>'
        f = self.facts[fid]
        self.used.add(fid)
        text = fmt(f.value, kind)
        if text is None:
            return f'<span class="missing" data-fact="{esc(fid)}" data-kind="{kind}">not available</span>'
        return f'<data value="{f.value!r}" data-fact="{esc(fid)}" data-kind="{kind}">{esc(text)}</data>'

    def v(self, fid):
        self.used.add(fid)
        return self.facts[fid].value


def source_line(sources, ids, extra="", up=""):
    parts = []
    for sid in ids:
        s = sources[sid]
        parts.append(f'<a href="{up}methods.html#src-{esc(sid)}">{esc(s["publisher"])}: {esc(s["title"])}</a>')
    return f'<p class="src">Source: {"; ".join(parts)}.{(" " + extra) if extra else ""}</p>'


# ------------------------------------------------------------------ charts

def bars(items, kind, num, maxval=None, caption=""):
    """Horizontal bar list. items: (label, fact_id, style) ; style '' | 'alt' | 'fc'."""
    vals = [num.facts[f].value for _, f, _ in items if num.facts[f].value is not None]
    top = maxval or max(vals)
    lis = []
    for label, fid, style in items:
        v = num.facts[fid].value
        w = 0 if v is None else max(0.0, 100 * v / top)
        lis.append(f'<li><div class="lab"><span>{label}</span><span>{num(fid, kind)}</span></div>'
                   f'<div class="track" aria-hidden="true"><div class="fill {style}" style="width:{w:.1f}%"></div></div></li>')
    cap = f'<p class="small">{caption}</p>' if caption else ""
    return f'{cap}<ul class="bars">{"".join(lis)}</ul>'


def table(caption, head, rows, first_col_header=True):
    th = "".join(f'<th scope="col">{h}</th>' for h in head)
    body = []
    for r in rows:
        cells = []
        for k, c in enumerate(r):
            if k == 0 and first_col_header:
                cells.append(f'<th scope="row">{c}</th>')
            else:
                cells.append(f"<td>{c}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    label = re.sub(r"<[^>]+>", "", str(caption))
    return (f'<div class="tablewrap" tabindex="0" role="region" aria-label="{esc(label)}"><table><caption>{caption}</caption><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def details_table(summary, caption, head, rows):
    return f"<details><summary>{summary}</summary>{table(caption, head, rows)}</details>"


def line_chart(title, labels, series, unit_label, breaks=(), forecast_from=None, ymin=None, ymax=None, height=240, desc="", scale=1, split_breaks=False):
    """Inline SVG line chart.

    labels: list of x labels. series: list of (name, values list (None = gap), style 'a'|'b').
    Missing values break the line; nothing is interpolated.
    breaks: list of (index, text) drawn as dashed vertical lines between index-1 and index.
    forecast_from: index from which values are forecasts (dashed line, shaded area).
    """
    W, H = 480, height
    L, R, T, B = 50, 10, 14, 30
    series = [(nm, [None if v is None else v / scale for v in vals], st) for nm, vals, st in series]
    allv = [v for _, vals, _ in series for v in vals if v is not None]
    lo = min(allv) if ymin is None else ymin
    hi = max(allv) if ymax is None else ymax
    if hi == lo:
        hi = lo + 1
    step_v = _nice_step((hi - lo) / 4)
    lo2 = lo if ymin is not None else step_v * math.floor(lo / step_v)
    hi2 = step_v * math.ceil(hi / step_v) if ymax is None else hi
    if hi2 <= hi and ymax is None:
        hi2 += step_v
    n = len(labels)

    def x(i):
        return L + (W - L - R) * (i / max(1, n - 1))

    def y(v):
        return T + (H - T - B) * (1 - (v - lo2) / (hi2 - lo2))
    parts = []
    # grid and y ticks at round numbers
    v = lo2
    while v <= hi2 + step_v / 1000:
        yy = y(v)
        parts.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#e3e5e8"/>')
        parts.append(f'<text x="{L - 6}" y="{yy + 4:.1f}" text-anchor="end">{_tick(v, step_v)}</text>')
        v += step_v
    # x labels: first, last and a few between, never overlapping
    step = max(1, math.ceil(n / 5))
    idx = [i for i in range(0, n, step) if n - 1 - i >= step * 0.8] + [n - 1]
    for i in idx:
        anchor = "start" if i == 0 else ("end" if i == n - 1 else "middle")
        parts.append(f'<text x="{x(i):.1f}" y="{H - 10}" text-anchor="{anchor}">{esc(_short(labels[i]))}</text>')
    if forecast_from is not None and forecast_from < n:
        fx = x(forecast_from) - (x(1) - x(0)) / 2
        parts.append(f'<rect x="{fx:.1f}" y="{T}" width="{W - R - fx:.1f}" height="{H - T - B}" fill="#f1f2f3"/>')
        parts.append(f'<text x="{W - R - 2}" y="{H - B - 6}" text-anchor="end">Forecast</text>')
    for i, text in breaks:
        bx = x(i) - (x(1) - x(0)) / 2 if n > 1 else x(i)
        parts.append(f'<line x1="{bx:.1f}" x2="{bx:.1f}" y1="{T}" y2="{H - B}" stroke="#b58900" stroke-dasharray="4 3"/>')
        if bx > W * 0.65:
            parts.append(f'<text x="{bx - 3:.1f}" y="{T + 12}" text-anchor="end" fill="#7a5c00">{esc(text)}</text>')
        else:
            parts.append(f'<text x="{bx + 3:.1f}" y="{T + 12}" fill="#7a5c00">{esc(text)}</text>')
    for name, vals, style in series:
        colour = "#3d4852" if style == "a" else "#8d969e"
        width = 2.5 if style == "a" else 2
        segs, cur = [], []
        split_at = {i for i, _ in breaks} if split_breaks else set()
        for i, v in enumerate(vals):
            if i in split_at and cur:
                segs.append(cur)
                cur = []
            if v is None:
                if cur:
                    segs.append(cur)
                cur = []
            else:
                cur.append((i, v))
        if cur:
            segs.append(cur)
        for seg in segs:
            solid = [(i, v) for i, v in seg if forecast_from is None or i < forecast_from]
            dashed = [(i, v) for i, v in seg if forecast_from is not None and i >= forecast_from - 1]
            for pts, dash in ((solid, ""), (dashed, ' stroke-dasharray="5 4"')):
                if len(pts) > 1:
                    d = " ".join(f"{'M' if k == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for k, (i, v) in enumerate(pts))
                    parts.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}"{dash}/>')
            for i, v in seg:
                if len(seg) == 1:
                    parts.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{colour}"/>')
    label = f"{title}. {desc}" if desc else title
    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(label)} The table below gives every value.">'
           + "".join(parts) + "</svg>")
    key = ""
    if len(series) > 1 or forecast_from is not None:
        items = [f'<span><i class="{"" if s == "a" else "b"}"></i>{esc(nm)}</span>' for nm, _, s in series]
        if forecast_from is not None:
            items.append('<span><i class="d"></i>Forecast (dashed)</span>')
        key = f'<div class="key">{"".join(items)}</div>'
    return f'<figure>{key}{svg}<figcaption>{esc(unit_label)}</figcaption></figure>'


def _nice_step(raw):
    if raw <= 0:
        return 1
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _tick(v, step=1):
    if step >= 1:
        return f"{v:,.0f}"
    return f"{v:.1f}"


def _short(label):
    s = str(label)
    if len(s) == 7 and s[4] == "-":  # 2025-26 -> 2025-26
        return s
    return s
