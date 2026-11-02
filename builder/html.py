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
:root{--ink:#16191d;--ink2:#3a4148;--muted:#5a6168;--line:#dcdfe3;--line2:#eceef0;--soft:#f4f5f7;--soft2:#fafbfb;--bar:#3a4552;--bar2:#a3abb3;--link:#1d4f7a;--focus:#1a5fb4;--warn:#fbf6e8;--warnline:#a07800;--bg:#fff;--r:10px}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:12px}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--link);text-underline-offset:2px}
a.term{color:inherit;text-decoration:underline dotted var(--muted);text-decoration-thickness:1.5px;text-underline-offset:3px}a.term:hover{text-decoration-style:solid}
dl.glossary{margin:0 0 24px}dl.glossary dt{font-weight:650;margin-top:18px;scroll-margin-top:12px}dl.glossary dt:target{background:var(--warn)}dl.glossary dd{margin:2px 0 0}
a:focus-visible,summary:focus-visible,select:focus-visible,button:focus-visible,.tablewrap:focus-visible,nav.main ul:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
header.site{border-bottom:1px solid var(--line);background:#fff}
header.site .wrap{display:flex;flex-direction:column;padding-top:0;padding-bottom:0}
.brand{display:inline-flex;align-items:center;gap:8px;min-height:48px;font-weight:750;letter-spacing:-.01em;color:var(--ink);text-decoration:none;font-size:1.1rem}
.mark{display:inline-flex;align-items:flex-end;gap:2px;height:18px}.mark i{display:block;width:5px;background:var(--ink);border-radius:1px}.mark i:nth-child(1){height:10px}.mark i:nth-child(2){height:18px}.mark i:nth-child(3){height:14px;background:var(--bar2)}
nav.main{margin:0 -16px;position:relative}
nav.main::after{content:"";position:absolute;right:0;top:0;bottom:3px;width:28px;background:linear-gradient(90deg,rgba(255,255,255,0),#fff);pointer-events:none}
nav.main ul{list-style:none;margin:0;padding:0 16px;display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
nav.main ul::-webkit-scrollbar{display:none}
nav.main li{flex:none}
nav.main a{display:flex;align-items:center;min-height:44px;padding:0 10px;color:var(--ink2);text-decoration:none;font-size:.94rem;white-space:nowrap;border-bottom:3px solid transparent}
nav.main a:hover{color:var(--ink);border-bottom-color:var(--line)}
nav.main a[aria-current=page]{color:var(--ink);font-weight:650;border-bottom-color:var(--ink)}
nav.main li:first-child a{padding-left:0}
.wrap{max-width:44rem;margin:0 auto;padding-left:16px;padding-right:16px}
main{padding-bottom:56px}
h1{font-size:1.85rem;line-height:1.15;letter-spacing:-.02em;margin:28px 0 14px}
h2{font-size:1.38rem;line-height:1.25;letter-spacing:-.01em;margin:48px 0 12px;padding-top:20px;border-top:1px solid var(--line)}
h3{font-size:1.1rem;line-height:1.3;margin:28px 0 8px}
p{margin:0 0 12px}
ul,ol{padding-left:1.3em}
li{margin-bottom:4px}
.lede{font-size:1.14rem;line-height:1.5;font-weight:500}
.eyebrow{display:block;font-size:.8rem;font-weight:650;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:24px 0 -8px}
.answer{background:var(--soft);border-radius:var(--r);padding:16px 16px 4px;margin:14px 0 18px}
.answer p{margin-bottom:12px}
.small,.src{font-size:.87rem;color:var(--muted);line-height:1.5}
.src{margin:8px 0 0}
details.src{border:0;border-top:1px solid var(--line2);border-radius:0;padding:0;margin:10px 0 0}details.src summary{font-weight:500;font-size:.87rem;min-height:44px;color:var(--link)}details.src ul{margin:0 0 8px;padding-left:1.1em}details.src li{margin-bottom:6px}
.note{border-left:3px solid var(--bar2);padding:2px 0 2px 12px;margin:16px 0;color:var(--ink2);font-size:.95rem}
.limit{background:var(--warn);border-radius:var(--r);border-left:4px solid var(--warnline);padding:12px 14px 2px;margin:16px 0 8px;font-size:.93rem;line-height:1.5}
.scale{border-left:4px solid var(--line);padding:2px 0 2px 12px;margin:0 0 18px;font-size:.96rem}
.illustration{border:2px dashed var(--bar2);border-radius:var(--r);padding:14px 16px;margin:24px 0;background:#fff}
.illustration .tag{display:inline-block;font-size:.78rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;background:var(--ink);color:#fff;padding:3px 8px;border-radius:4px;margin-bottom:6px}
.keyfigs{list-style:none;margin:16px 0 20px;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.keyfigs li{margin:0;border:1px solid var(--line);border-radius:var(--r);padding:12px 12px 10px;background:#fff}
.keyfigs .big{display:block;font-size:1.6rem;line-height:1.1;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums;margin-bottom:4px}
.keyfigs .what{display:block;font-size:.86rem;line-height:1.35;color:var(--ink2)}
.keyfigs li.wide{grid-column:1/-1}
.toc{border:1px solid var(--line);border-radius:var(--r);padding:10px 14px 6px;margin:20px 0 8px;font-size:.95rem}
.toc h2{font-size:.8rem;font-weight:650;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 2px;padding:0;border:0}
.toc ol{margin:0;padding:0;list-style:none}
.toc li{margin:0;border-top:1px solid var(--line2)}
.toc li:first-child{border-top:0}
.toc a{display:flex;align-items:center;min-height:40px;text-decoration:none;line-height:1.3;padding:4px 0}
.toc a::before{content:"↓";color:var(--muted);margin-right:10px;font-size:.85em}
.bars{margin:14px 0 6px;padding:0;list-style:none}
.bars li{margin:0 0 10px}
.bars .lab{display:flex;justify-content:space-between;align-items:baseline;gap:12px;font-size:.95rem;line-height:1.35}
.bars .lab span:last-child{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:700}
.bars .track{height:14px;background:var(--soft);margin-top:4px;border-radius:3px;overflow:hidden}
.bars .fill{height:14px;background:var(--bar);border-radius:3px}
.bars .fill.alt{background:var(--bar2)}
.bars .track.ctr{position:relative;background:linear-gradient(var(--ink2),var(--ink2)) center/1.5px 100% no-repeat,var(--soft)}.bars .track.ctr .fill{position:absolute;top:0;border-radius:0}.bars .fill.neg{background:var(--bar2)}.bars .sub{font-size:.82rem;color:var(--muted);font-variant-numeric:tabular-nums}.bars .dir{font-weight:400;color:var(--muted);font-size:.85em}
.bars .fill.fc{background:repeating-linear-gradient(45deg,var(--bar2) 0 4px,#fff 4px 7px)}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:8px 0 12px;font-variant-numeric:tabular-nums;line-height:1.4}
caption{text-align:left;font-weight:650;padding:4px 0 8px;font-size:.92rem}
th,td{border-bottom:1px solid var(--line);padding:8px 6px;text-align:right;vertical-align:top}
th:first-child,td:first-child{text-align:left;padding-left:0}
thead th{border-bottom:2px solid var(--ink);vertical-align:bottom;font-weight:650}
tbody th{font-weight:500}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:0}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tablewrap table{min-width:100%}
details{margin:10px 0 16px;border:1px solid var(--line);border-radius:var(--r);padding:0 14px}
details[open]{padding-bottom:8px}
summary{cursor:pointer;min-height:48px;display:flex;align-items:center;gap:10px;color:var(--link);font-weight:600;font-size:.95rem;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"";flex:none;width:8px;height:8px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(-45deg);margin:0 2px;transition:transform .15s}
details[open]>summary::before{transform:rotate(45deg)}
figure{margin:16px 0 8px}
figure .ctitle{font-weight:650;font-size:.98rem;margin:0 0 4px}
figcaption{font-size:.86rem;color:var(--muted);line-height:1.45;margin-top:4px}
svg{display:block;overflow:visible}
svg text{font:15px -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;fill:#4a5158}
svg text.lbl{font-weight:650;fill:#1f252b;paint-order:stroke;stroke:#fff;stroke-width:4px;stroke-linejoin:round}
svg text.lbl.b{fill:#5d666e}
.key{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.87rem;color:var(--ink2);margin:4px 0 6px}
.key i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px;background:var(--bar)}
.key i.b{background:var(--bar2)}.key i.c{width:18px;height:8px;background:linear-gradient(var(--bar),var(--bar)) center/18px 1.5px no-repeat,linear-gradient(var(--bar),var(--bar)) center/8px 8px no-repeat}.key i.d{background:repeating-linear-gradient(90deg,var(--bar) 0 4px,transparent 4px 7px)}
.cards{list-style:none;padding:0;margin:16px 0;display:grid;gap:12px}
.cards li{border:1px solid var(--line);border-radius:var(--r);padding:14px}
.cards h2,.cards h3{margin:0 0 6px;border:0;padding:0;font-size:1.1rem}
.cards p{margin:0 0 8px}
.stats{margin:12px 0 8px;padding:0;border-top:1px solid var(--line)}
.stats>div{display:grid;grid-template-columns:1fr auto;gap:2px 16px;padding:10px 0;border-bottom:1px solid var(--line2)}
.stats dt{font-size:.95rem;line-height:1.35}
.stats dd{margin:0;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap}
.stats .per{grid-column:1/-1;font-size:.82rem;color:var(--muted);font-weight:400;text-align:left;white-space:normal}
.stats .missing{font-weight:400}
.yearnav{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px;padding:0;list-style:none}
.yearnav li{margin:0}
.yearnav a,.yearnav span{display:inline-flex;align-items:center;justify-content:center;min-width:56px;min-height:44px;padding:0 8px;border:1px solid var(--line);border-radius:8px;text-decoration:none;font-variant-numeric:tabular-nums}
.yearnav a:hover{border-color:var(--ink2)}
.yearnav span[aria-current]{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:650}
.yearstrip{flex-wrap:nowrap;overflow-x:auto;margin:8px -16px 12px;padding:2px 16px 6px;scrollbar-width:thin}
.yearstrip li{flex:none}
.pager{display:flex;justify-content:space-between;gap:12px;margin:12px 0}
.pager a{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border:1px solid var(--line);border-radius:8px;text-decoration:none;font-weight:600}
form.pick{display:flex;flex-wrap:wrap;gap:10px 12px;align-items:flex-end;background:var(--soft);border-radius:var(--r);padding:14px;margin:12px 0}
form.pick label{display:flex;flex-direction:column;font-size:.9rem;font-weight:600;gap:4px}
select,button{font:inherit;min-height:44px;padding:6px 10px;border:1px solid #767676;border-radius:8px;background:#fff;color:var(--ink)}
button{background:var(--ink);color:#fff;border-color:var(--ink);padding:6px 18px;font-weight:600;cursor:pointer}
.missing{color:var(--muted);font-style:italic}
a.card{display:block;border:1px solid var(--line);border-radius:var(--r);padding:16px;color:var(--ink);text-decoration:none;background:#fff}
a.card:hover{border-color:var(--ink2)}
a.card:hover h2,a.card:hover h3,a.card:focus h2,a.card:focus h3{text-decoration:underline}
a.card h2,a.card h3{color:var(--link);margin:0 0 8px;padding:0;border:0;font-size:1.12rem;line-height:1.3}
a.card .big{display:block;font-size:2rem;line-height:1.05;font-weight:750;letter-spacing:-.02em;font-variant-numeric:tabular-nums;margin:2px 0 6px}
a.card p{margin:0 0 6px;font-size:.95rem;color:var(--ink2)}
a.card .more{display:block;margin-top:8px;font-size:.9rem;font-weight:600;color:var(--link)}
a.card .mini{margin:10px 0 2px}
a.card .mini .track{height:10px;background:var(--soft);border-radius:3px;overflow:hidden}
a.card .mini .fill{height:10px;background:var(--bar)}
a.button{display:inline-flex;align-items:center;min-height:48px;padding:6px 20px;background:var(--ink);color:#fff;text-decoration:none;border-radius:8px;font-weight:600}
.hero{padding:8px 0 4px}
.hero h1{font-size:2.05rem;margin-bottom:12px}
.principles{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px}
.principles li{margin:0;padding:12px 14px;background:var(--soft);border-radius:var(--r);font-size:.95rem;line-height:1.45}
.principles strong{display:block;margin-bottom:2px}
.source{border-top:1px solid var(--line);padding-top:8px}
.source dl{display:grid;grid-template-columns:8rem 1fr;gap:4px 12px;font-size:.92rem}
.source dt{color:var(--muted)}.source dd{margin:0;overflow-wrap:anywhere}
.hash{font-size:.8rem}
.change-up::before{content:"▲ ";font-size:.75em}.change-down::before{content:"▼ ";font-size:.75em}
.cmp-key{border-left:4px solid var(--bar);background:var(--soft);padding:10px 12px;margin:10px 0}
.cmp-key h3{margin:0 0 4px;font-size:1rem}
.cmp-key p{margin:0 0 6px}
.cmp-list,.cmp-notes{list-style:none;margin:8px 0 12px;padding:0}
.cmp-list li{border-bottom:1px solid var(--line);padding:8px 0}
.cmp-label{font-weight:600;margin:0 0 4px}
.cmp-bar{display:grid;grid-template-columns:3.2em 1fr auto;gap:8px;align-items:center;font-size:.92rem;margin:2px 0}
.cmp-y{color:var(--muted)}
.cmp-v{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.cmp-track{height:12px;background:#fff;border:1px solid var(--line)}
.cmp-key .cmp-track{background:#fff}
.cmp-list .cmp-track{background:var(--soft);border:0}
.cmp-fill{display:block;height:100%}
.cmp-a{background:var(--bar2)}.cmp-b{background:var(--bar)}
.cmp-change{margin:4px 0 0;font-size:.95rem}
.cmp-notes li{border-left:4px solid var(--warnline);background:var(--warn);padding:8px 12px;margin:8px 0}
.cmp-notes p{margin:0 0 4px}
.cmp-notes .cmp-vals{list-style:disc;padding-left:1.2em;margin:0}.cmp-notes .cmp-vals li{border:0;background:none;padding:0;margin:0 0 2px}
.cmp-top{padding-left:1.4em;margin:6px 0 12px}
.cmp-top li{margin:0 0 6px}
details.limit summary{color:var(--ink)}
footer{border-top:1px solid var(--line);background:var(--soft2);padding:20px 0 36px;font-size:.88rem;color:var(--muted)}
footer ul{list-style:none;padding:0;margin:0 0 14px;display:flex;flex-wrap:wrap;gap:0 18px}
footer ul a{display:inline-flex;align-items:center;min-height:44px;color:var(--ink2)}
@media (min-width:640px){.cards{grid-template-columns:1fr 1fr}h1{font-size:2.2rem}.hero h1{font-size:2.5rem}.keyfigs{grid-template-columns:repeat(3,1fr)}.keyfigs li.wide{grid-column:auto}.principles{grid-template-columns:1fr 1fr}
header.site .wrap{flex-direction:row;align-items:center;gap:16px}.brand{margin-right:auto}nav.main{margin:0}nav.main::after{display:none}nav.main ul{padding:0}nav.main a{min-height:56px}.yearstrip{flex-wrap:wrap;overflow:visible;margin:8px 0 16px;padding:0}}
@media print{nav.main,.skip,form.pick,.toc{display:none}details{display:block;border:0;padding:0}}
"""

NAV = [
    ("index.html", "Home"),
    ("spending.html", "Spending"),
    ("taxes.html", "Taxes"),
    ("who-pays.html", "Who pays"),
    ("household-tax.html", "Tax and income"),
    ("life/index.html", "Year by year"),
    ("glossary.html", "Glossary"),
    ("methods.html", "Sources"),
]


def esc(s):
    return escape(str(s), quote=True)


def toc(body):
    """'On this page' jump links, built from the h2 headings that have ids.

    Long phone pages need a way to skip ahead. Only added when a page has at
    least three such sections. Placed before the first h2, so the answer
    still comes first.
    """
    found = re.findall(r'<h2 id=["\']([^"\']+)["\']>(.*?)</h2>', body, flags=re.S)
    if len(found) < 3:
        return body
    items = "".join(f'<li><a href="#{esc(i)}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in found)
    nav = f'<nav class="toc" aria-labelledby="toc-h"><h2 id="toc-h">On this page</h2><ol>{items}</ol></nav>'
    k = re.search(r'<h2[ >]', body)
    return body[:k.start()] + nav + "\n" + body[k.start():]


def page(path, title, body, description="", scripts="", contents=True):
    depth = path.count("/")
    up = "../" * depth
    nav = "".join(
        f'<li><a href="{up}{href}"{" aria-current=page" if href == path or (href == "life/index.html" and path.startswith("life/")) else ""}>{esc(label)}</a></li>'
        for href, label in NAV)
    foot = "".join(f'<li><a href="{up}{href}">{esc(label)}</a></li>' for href, label in NAV)
    full_title = SITE if path == "index.html" else f"{title} – {SITE}"
    if contents:
        body = toc(body)
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description or title)}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="{up}icon.svg" type="image/svg+xml">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="{up}index.html"><span class="mark" aria-hidden="true"><i></i><i></i><i></i></span>{SITE}</a>
<nav class="main" aria-label="Main"><ul>{nav}</ul></nav></div></header>
<main id="main" class="wrap">
{body}
</main>
<footer><div class="wrap">
<nav aria-label="Footer"><ul>{foot}</ul></nav>
<p>{SITE} is an independent guide built only from official UK statistics. It does not support or oppose any party or policy. Every figure links to its source on the <a href="{up}methods.html">sources and methods</a> page.</p>
<p>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
</div></footer>
{scripts}
</body>
</html>
"""


def keyfigs(items):
    """Key figures as large tiles. items: (number html, what it is, wide?)."""
    lis = "".join(f'<li{" class=wide" if wide else ""}><span class="big">{n}</span><span class="what">{w}</span></li>' for n, w, wide in items)
    return f'<ul class="keyfigs">{lis}</ul>'


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
    if len(parts) <= 2:
        return f'<p class="src">Source: {"; ".join(parts)}.{(" " + extra) if extra else ""}</p>'
    # A long run of links buries the page on a phone: name the publishers, list the tables one tap away.
    pubs = []
    for sid in ids:
        p = sources[sid]["publisher"].split(" (")[0]
        if p not in pubs:
            pubs.append(p)
    items = "".join(f"<li>{a}</li>" for a in parts)
    return (f'<details class="src"><summary>Sources: {esc(", ".join(pubs))} ({len(parts)} tables)</summary>'
            f'<ul>{items}</ul>{("<p>" + extra + "</p>") if extra else ""}</details>')


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


def change_bars(items, kind, num, caption=""):
    """Bars that grow left for a fall and right for a rise, from a shared zero line.

    items: (label html, fact id, optional note html). The note should give the
    amounts, so a big percentage on a small base is not mistaken for a big sum.
    """
    items = [it if len(it) == 3 else (*it, "") for it in items]
    vals = [num.facts[f].value for _, f, _ in items if num.facts[f].value is not None]
    top = max(abs(v) for v in vals) or 1
    lis = []
    for label, fid, sub in items:
        v = num.facts[fid].value
        w = 0 if v is None else 50 * abs(v) / top
        side = "left:50%" if (v or 0) >= 0 else f"right:50%"
        word = "" if v is None else ("rise" if v > 0 else ("fall" if v < 0 else "no change"))
        lis.append(f'<li><div class="lab"><span>{label}</span><span>{num(fid, kind)} <span class="dir">{word}</span></span></div>'
                   + (f'<div class="sub">{sub}</div>' if sub else "")
                   + f'<div class="track ctr" aria-hidden="true"><div class="fill{" neg" if (v or 0) < 0 else ""}" style="{side};width:{w:.1f}%"></div></div></li>')
    cap = f'<p class="small">{caption}</p>' if caption else ""
    return f'{cap}<ul class="bars change">{"".join(lis)}</ul>'


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
    W, H = 400, round(height * 400 / 480) + 20
    direct = len(series) <= 3 and all(len(nm) <= 26 for nm, _, _ in series) and len(series) > 1
    L, R, T, B = 44, 8, 14, 30
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
    # x labels: first, last and as many between as fit without touching
    def extent(i):
        w = 8.2 * len(_short(labels[i]))
        if i == 0:
            return x(i), x(i) + w
        if i == n - 1:
            return x(i) - w, x(i)
        return x(i) - w / 2, x(i) + w / 2
    step = max(1, math.ceil(n / 5))
    idx = []
    for i in list(range(0, n - 1, step)):
        lo_, hi_ = extent(i)
        if idx and lo_ < extent(idx[-1])[1] + 10:
            continue
        if n > 1 and hi_ > extent(n - 1)[0] - 10:
            continue
        idx.append(i)
    idx.append(n - 1)
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
        # a: dark thick line; b: grey line; c: dark thin line with a square at every point
        colour = "#8d969e" if style == "b" else "#3d4852"
        width = {"a": 2.5, "b": 2, "c": 1.5}.get(style, 2)
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
                if style == "c":
                    parts.append(f'<rect x="{x(i) - 3.5:.1f}" y="{y(v) - 3.5:.1f}" width="7" height="7" fill="{colour}"/>')
                elif len(seg) == 1:
                    parts.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{colour}"/>')
    if direct:
        parts.extend(_end_labels(series, x, y, T, H - B))
    label = f"{title}. {desc}" if desc else title
    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(label)} The table below gives every value.">'
           + "".join(parts) + "</svg>")
    key = ""
    if (len(series) > 1 and not direct) or forecast_from is not None:
        items = [] if direct else [f'<span><i class="{"" if s == "a" else s}"></i>{esc(nm)}</span>' for nm, _, s in series]
        if forecast_from is not None:
            items.append('<span><i class="d"></i>Forecast (dashed)</span>')
        key = f'<div class="key">{"".join(items)}</div>'
    return f'<figure><p class="ctitle" aria-hidden="true">{esc(title)}</p>{key}{svg}<figcaption>{esc(unit_label)}</figcaption></figure>'


def _end_labels(series, x, y, top, bottom):
    """Name each line beside its last point, so readers don't need a key.

    Labels sit above the end of a line that rises into it and below one that
    falls into it, then are nudged apart so they never overlap.
    """
    labs = []
    for name, vals, style in series:
        pts = [(i, v) for i, v in enumerate(vals) if v is not None]
        if not pts:
            continue
        i, v = pts[-1]
        prev = pts[-2][1] if len(pts) > 1 else v
        ly = y(v) + (18 if prev > v else -9)
        labs.append([ly, x(i), name, style])
    labs.sort()
    for k in range(1, len(labs)):
        if labs[k][0] - labs[k - 1][0] < 17:
            labs[k][0] = labs[k - 1][0] + 17
    for lab in labs:
        lab[0] = min(max(lab[0], top + 12), bottom - 4)
    for k in range(len(labs) - 2, -1, -1):
        if labs[k + 1][0] - labs[k][0] < 17:
            labs[k][0] = labs[k + 1][0] - 17
    return [f'<text class="lbl{" b" if st == "b" else ""}" x="{lx - 2:.1f}" y="{ly:.1f}" text-anchor="end">{esc(nm)}</text>' for ly, lx, nm, st in labs]


def _nice_step(raw):
    if raw <= 0:
        return 1
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _tick(v, step=1):
    if step >= 1 and float(step).is_integer():
        return f"{v:,.0f}"
    if step >= 1:
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    return f"{v:.1f}"


def _short(label):
    s = str(label)
    if len(s) == 7 and s[4] == "-":  # 2025-26 -> 2025-26
        return s
    return s
