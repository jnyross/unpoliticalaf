"""Shared HTML pieces: page shell, number formatting, accessible charts and tables.

Every number shown on a page is wrapped in <data value=".." data-fact="id">,
so the checker can confirm the text matches the stored fact and its source.
Charts are plain HTML/CSS or inline SVG drawn at build time, so they work
without JavaScript, and each one sits next to a complete table.
"""
import json
import math
import re
from html import escape
from . import version

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
@media (max-width:47.99rem){nav.main{margin:0}nav.main::after{display:none}nav.main ul{display:grid;grid-template-columns:repeat(4,1fr);gap:0 4px;padding:0 0 4px;overflow:visible}nav.main li{margin:0;min-width:0}nav.main a,nav.main li:first-child a{justify-content:center;text-align:center;white-space:normal;line-height:1.15;font-size:.86rem;padding:4px 2px;min-height:44px}}
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
details.src{border:0;border-top:1px solid var(--line2);border-radius:0;padding:0;margin:10px 0 0}details.src summary{font-weight:500;font-size:.87rem;min-height:44px;color:var(--link)}details.src ul{margin:0 0 8px;padding-left:1.1em}details.src li{margin-bottom:6px}details.src li a{display:inline-block;padding:4px 0}
.note{border-left:3px solid var(--bar2);padding:2px 0 2px 12px;margin:16px 0;color:var(--ink2);font-size:.95rem}
.moe,.moe-in{color:var(--muted);font-size:.88em;white-space:nowrap;font-variant-numeric:tabular-nums}.sure{font-size:.93rem;color:var(--ink2);margin:-6px 0 16px}.sure-check{margin:4px 0 0}
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
.spark{display:block;width:100%;height:auto;max-width:30rem}.spark .ln{fill:none;stroke:var(--bar2);stroke-width:1.5}.spark .pt{fill:var(--bar2)}.spark .hi{fill:var(--ink);stroke:#fff;stroke-width:1.5}.spark .brk{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}.spark .gap{stroke:var(--line);stroke-width:2}
.spark-ax{display:flex;justify-content:space-between;max-width:30rem;font-size:.8rem;color:var(--muted);font-variant-numeric:tabular-nums;margin-top:2px}
figure.yearspark{margin:4px 0 14px}figure.yearspark figcaption{font-size:.87rem;color:var(--muted);line-height:1.5;margin-top:4px}
a.card .mini{margin:6px 0 4px}.cards .mini li{border:0;border-radius:0;padding:0}a.card .mini .bars{margin:8px 0 2px}a.card .mini .bars li{margin:0 0 6px}a.card .mini .bars .lab{font-size:.84rem;color:var(--ink2)}a.card .mini .bars .track,a.card .mini .bars .fill{height:8px}
figure .ctitle{font-weight:650;font-size:.98rem;margin:0 0 4px}
figcaption{font-size:.86rem;color:var(--muted);line-height:1.45;margin-top:4px}
.csum{margin:8px 0 0;padding:8px 12px;background:var(--soft2);border-left:3px solid var(--line);font-size:.92rem}
.csum .csum-h{font-weight:650;margin:0 0 2px;font-size:.92rem}.csum ul{margin:0;padding-left:1.1em}.csum li{margin:0 0 4px}.csum .small{margin:4px 0 0}
.readout{min-height:44px;margin:4px 0 0;font-size:.92rem;color:var(--ink2)}.readout b{font-weight:650}
svg[data-chart],.sm svg{touch-action:pan-y;cursor:crosshair}[data-chart]:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.sm{display:grid;grid-template-columns:1fr 1fr;gap:12px 14px;margin:6px 0 4px}.sm>div{display:flex;flex-direction:column;justify-content:flex-end;min-width:0}
.sm .smt{font-size:.87rem;font-weight:650;line-height:1.25;margin:0 0 2px;color:var(--ink)}.smkey{font-size:.87rem;color:var(--ink2);margin:2px 0 6px}
.sm use.c,.sm use.o{fill:none;stroke-linecap:round;stroke-linejoin:round}.sm use.c{stroke:#d5d9dd;stroke-width:1}.sm use.o{stroke:#3d4852;stroke-width:2.5}
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
.explain{border:1px solid var(--line);border-left:4px solid var(--bar2);padding:10px 14px;margin:16px 0;background:#fff}
.explain .q{margin:0 0 4px;font-size:1rem;border:0;padding:0}
.explain .who{font-size:.9rem;color:var(--muted);margin:0 0 4px}
.explain blockquote{margin:0 0 8px;padding:0}
.explain blockquote p{margin:0}
details.limit summary{color:var(--ink)}
details.more{border-color:var(--line2)}details.more>summary{flex-wrap:wrap;row-gap:0;padding:6px 0}details.more>summary .hint{flex-basis:100%;padding-left:24px;font-weight:400;font-size:.85rem;color:var(--muted)}
footer{border-top:1px solid var(--line);background:var(--soft2);padding:20px 0 36px;font-size:.88rem;color:var(--muted)}
footer ul{list-style:none;padding:0;margin:0 0 14px;display:flex;flex-wrap:wrap;gap:0 18px}
footer ul a{display:inline-flex;align-items:center;min-height:44px;color:var(--ink2)}
@media (min-width:640px){.sm{grid-template-columns:repeat(3,1fr)}.cards{grid-template-columns:1fr 1fr}h1{font-size:2.2rem}.hero h1{font-size:2.5rem}.keyfigs{grid-template-columns:repeat(3,1fr)}.keyfigs li.wide{grid-column:auto}.principles{grid-template-columns:1fr 1fr}
header.site .wrap{flex-direction:row;align-items:center;gap:16px}.brand{margin-right:auto}nav.main{margin:0}nav.main::after{display:none}nav.main ul{padding:0}nav.main a{min-height:56px}.yearstrip{flex-wrap:wrap;overflow:visible;margin:8px 0 16px;padding:0}}
.tr data[data-fact],.tr data[data-from]{cursor:pointer}.tr data[data-fact]:hover,.tr data[data-from]:hover{background:var(--soft)}
.trace{position:fixed;left:8px;right:8px;bottom:8px;max-width:560px;margin:0 auto;max-height:70vh;overflow:auto;background:#fff;border:1px solid var(--ink2);border-radius:var(--r);box-shadow:0 6px 24px rgba(0,0,0,.18);padding:12px 16px;z-index:20;font-size:.95rem}
.trace .trace-h{font-weight:650;margin:0 0 6px}.trace .trace-v{margin:0 0 6px;color:var(--muted)}.trace dl{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;margin:0 0 4px}.trace dt{color:var(--muted)}.trace dd{margin:0;overflow-wrap:anywhere}.trace p{margin:4px 0 8px}
.trace-x{min-height:44px;min-width:88px;font:inherit;color:var(--ink);border:1px solid var(--line);background:var(--soft);border-radius:8px;cursor:pointer}
section.fig,section.correction{border-top:1px solid var(--line);padding:8px 0;scroll-margin-top:12px}section.fig:target{background:var(--warn)}section.fig h3{font-size:1rem;margin:4px 0;overflow-wrap:anywhere}section.fig dl,section.correction dl,dl.srcmeta{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;margin:0}section.fig dt,section.correction dt,dl.srcmeta dt{color:var(--muted)}section.fig dd,section.correction dd,dl.srcmeta dd{margin:0;overflow-wrap:anywhere}
@media print{nav.main,.skip,form.pick,.toc,.trace{display:none}details{display:block;border:0;padding:0}}
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
    least three such sections. Placed before the first h2 with an id, so the
    answer (and any heading without an id, such as "In brief") comes first.
    """
    found = re.findall(r'<h2 id=["\']([^"\']+)["\']>(.*?)</h2>', body, flags=re.S)
    if len(found) < 3:
        return body
    items = "".join(f'<li><a href="#{esc(i)}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in found)
    nav = f'<nav class="toc" aria-labelledby="toc-h"><h2 id="toc-h">On this page</h2><ol>{items}</ol></nav>'
    k = re.search(r'<h2 id=', body)
    return body[:k.start()] + nav + "\n" + body[k.start():]


# Marker a page writer puts in a section to say "fold everything after this".
FOLD = "<!--fold-->"
# Marker that keeps a section fully open, even when it has an answer box.
NOFOLD = "<!--nofold-->"

_H2 = re.compile(r'<h2 id=["\']([^"\']+)["\']>(.*?)</h2>', re.S)


def _top_answer(sec):
    """(start, end) of the first .answer div at the top level of a section, or None."""
    m = re.search(r'<div class="answer">', sec)
    if not m:
        return None
    depth, i = 0, m.start()
    for t in re.finditer(r'<(/?)div\b[^>]*>', sec[m.start():]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return m.start(), m.start() + t.end()
    return None


def _contents_hint(html):
    """What a folded part holds, in a few words, so readers know whether to open it."""
    kinds = []
    if "<figure" in html or 'class="bars' in html or 'class="cmp-list' in html:
        kinds.append("chart")
    if "<table" in html:
        kinds.append("table")
    if 'class="limit' in html or "class=\"note" in html:
        kinds.append("limits")
    if 'class="official' in html or "What official bodies say" in html:
        kinds.append("official words")
    if 'class="src' in html or 'class="source' in html:
        kinds.append("sources")
    if not kinds:
        return ""
    if len(kinds) == 1:
        return kinds[0]
    return ", ".join(kinds[:-1]) + " and " + kinds[-1]


_CHART_OPEN = re.compile(r'<(figure)\b[^>]*>|<(ul) class="(?:bars|cmp-list)[^"]*">')
_CAPTION = re.compile(r'<p class="small">(?:(?!</p>).)*</p>\s*$', re.S)
_NEST = re.compile(r'<(/?)(details|aside|div|figure|ul|blockquote|table)\b[^>]*>')
KEEP_ROWS = 4  # rows of a long comparison list kept in view; the rest fold away


def _first_chart(rest):
    """(start, end) of the first chart that sits at the top level of a folded part, or None.

    Charts inside a disclosure, aside or table are left alone. A short caption
    paragraph straight before the chart travels with it.
    """
    for m in _CHART_OPEN.finditer(rest):
        depth = 0
        for t in _NEST.finditer(rest, 0, m.start()):
            depth += -1 if t.group(1) else 1
        if depth:
            continue
        tag = m.group(1) or m.group(2)
        level = 0
        for t in re.finditer(rf'<(/?){tag}\b[^>]*>', rest[m.start():]):
            level += -1 if t.group(1) else 1
            if level == 0:
                start, end = m.start(), m.start() + t.end()
                cap = _CAPTION.search(rest[:start])
                if cap and not re.search(r"<(?:div|ul|details|table|figure|aside)\b", rest[cap.start():start]):
                    start = cap.start()
                return start, end
        return None
    return None


def _split_long_list(chart):
    """Keep the first few rows of a long comparison list in view; return (shown, folded)."""
    m = re.match(r'(.*?<ul class="cmp-list">)(.*)(</ul>)$', chart, re.S)
    if not m:
        return chart, ""
    rows = re.findall(r'<li>.*?</li>(?=<li>|$)', m.group(2), re.S)
    if len(rows) <= KEEP_ROWS + 1:
        return chart, ""
    return (m.group(1) + "".join(rows[:KEEP_ROWS]) + m.group(3),
            '<ul class="cmp-list">' + "".join(rows[KEEP_ROWS:]) + "</ul>")


def keep_chart(lead, rest):
    """Move a section's main chart out of its fold so it shows under the answer.

    On a phone a folded section otherwise shows only words. The chart keeps its
    caption, summary and labels; tables, limits and sources stay folded.
    """
    if "<!--keepfold-->" in rest:
        return lead, rest.replace("<!--keepfold-->", "")
    if re.search(r'<figure\b|<ul class="(?:bars|cmp-list)', lead):
        return lead, rest
    c = _first_chart(rest)
    if not c:
        return lead, rest
    chart = rest[c[0]:c[1]]
    shown, more = _split_long_list(chart)
    return lead + "\n" + shown, rest[:c[0]] + more + rest[c[1]:]


def fold(body):
    """Fold the detail of each section so a phone reader sees the answers first.

    A section runs from an h2 with an id to the next one. The heading and the
    section's answer stay in view; the rest (charts, tables, limits, sources)
    goes into one "More on ..." disclosure, which works without JavaScript.
    What stays in view is everything up to the end of the section's first
    top-level .answer box, or everything before a FOLD marker, followed by the
    section's main chart (see keep_chart). Sections with neither, or with
    NOFOLD, are left as they are.
    """
    heads = list(_H2.finditer(body))
    if not heads:
        return body
    out = [body[:heads[0].start()]]
    for k, h in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(body)
        head, sec = body[h.start():h.end()], body[h.end():end]
        if NOFOLD in sec:
            out.append(head + sec.replace(NOFOLD, ""))
            continue
        if FOLD in sec:
            lead, rest = sec.split(FOLD, 1)
        else:
            a = _top_answer(sec)
            if not a:
                out.append(head + sec)
                continue
            lead, rest = sec[:a[1]], sec[a[1]:]
        lead, rest = keep_chart(lead, rest)
        if not rest.strip():
            out.append(head + lead)
            continue
        name = re.sub(r"<[^>]+>", "", h.group(2)).strip()
        name = re.sub(r"^\d+\.\s*", "", name)
        hint = _contents_hint(rest)
        hint = f'<span class="hint">{esc(hint)}</span>' if hint else ""
        out.append(f'{head}{lead}\n<details class="more"><summary><span>More on {esc(name)}</span>{hint}</summary>\n{rest}\n</details>\n')
    return "".join(out)


def page(path, title, body, description="", scripts="", contents=True, folded=True):
    depth = path.count("/")
    up = "../" * depth
    nav = "".join(
        f'<li><a href="{up}{href}"{" aria-current=page" if href == path or (href == "life/index.html" and path.startswith("life/")) else ""}>{esc(label)}</a></li>'
        for href, label in NAV)
    foot = "".join(f'<li><a href="{up}{href}">{esc(label)}</a></li>' for href, label in NAV)
    full_title = SITE if path == "index.html" else f"{title} – {SITE}"
    if folded:
        body = fold(body)
    if contents:
        body = toc(body)
    if "data-chart=" in body:
        scripts = scripts + CHART_JS
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
<p>{SITE} is an independent guide built only from official UK statistics. It does not support or oppose any party or policy. Tap any figure to see where it comes from, or see every source on the <a href="{up}methods.html">sources and methods</a> page. Mistakes we fix are listed under <a href="{up}corrections.html">corrections</a>. Survey figures are estimates: see <a href="{up}uncertainty.html">how sure they are</a>.</p>
<p>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
<p class="version">Site version {version.short()}</p>
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
    if kind == "pts":
        return f"{value:+.1f} points"
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
    # Margins of error (95%), shown after the figure they belong to
    if kind == "pm_pp":
        return f"±{value:.1f} points"
    if kind == "pm_pounds":
        return f"±£{value:,.0f}"
    if kind == "pm_pct":
        return f"±{value:.0f}%" if value >= 9.5 else f"±{value:.1f}%"
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
        parts.append(f'<a href="{up}figures/{esc(sid)}.html">{esc(s["publisher"])}: {esc(s["title"])}</a>')
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


def line_chart(title, labels, series, unit_label, breaks=(), forecast_from=None, ymin=None, ymax=None, height=240, desc="", scale=1, split_breaks=False,
               kind=None, ids=None, num=None, events=(), point_labels=None, future="forecast"):
    """Inline SVG line chart.

    labels: list of x labels. series: list of (name, values list (None = gap), style 'a'|'b').
    Missing values break the line; nothing is interpolated.
    breaks: list of (index, text) drawn as dashed vertical lines between index-1 and index.
    forecast_from: index from which values are forecasts (dashed line, shaded area).
    future: the publisher's word for those values, "forecast" (OBR) or "projection" (HMRC).
    events: list of (index, text) for things that happened, such as Covid. Drawn as a grey
    dotted line; unlike breaks they say nothing about definitions.
    kind: number format (see fmt). With kind, the chart gets a written summary under it
    (first, latest, highest and lowest values) and a tap or hover readout added by script.
    ids: one list of fact ids per series, so the summary's numbers are traceable figures
    (needs num). point_labels: longer names for each point used in the summary and readout,
    such as "2008-09" where the axis shows "2008".
    """
    raw = series
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
        parts.append(f'<text x="{W - R - 2}" y="{H - B - 6}" text-anchor="end">{future.capitalize()}</text>')
    taken = []  # x ranges of break labels already drawn
    for i, text in breaks:
        bx = x(i) - (x(1) - x(0)) / 2 if n > 1 else x(i)
        parts.append(f'<line x1="{bx:.1f}" x2="{bx:.1f}" y1="{T}" y2="{H - B}" stroke="#b58900" stroke-dasharray="4 3"/>')
        # Right-align the label when it would run past the chart's right edge
        w = len(text) * 6.6
        right = bx > W * 0.65 or bx + 3 + w > W
        lo_, hi_ = (bx - 3 - w, bx - 3) if right else (bx + 3, bx + 3 + w)
        if any(lo_ < b + 4 and hi_ > a - 4 for a, b in taken):
            continue  # breaks close together share one label; the summary names each
        taken.append((lo_, hi_))
        if right:
            parts.append(f'<text x="{bx - 3:.1f}" y="{T + 12}" text-anchor="end" fill="#7a5c00">{esc(text)}</text>')
        else:
            parts.append(f'<text x="{bx + 3:.1f}" y="{T + 12}" fill="#7a5c00">{esc(text)}</text>')
    for i, text in events:
        ex = x(i)
        parts.append(f'<line x1="{ex:.1f}" x2="{ex:.1f}" y1="{T}" y2="{H - B}" stroke="#8d969e" stroke-dasharray="1 3" stroke-width="1.5"/>')
        # Labelled at the foot of the chart, clear of the line ends and their labels
        if ex > W * 0.65:
            parts.append(f'<text x="{ex - 3:.1f}" y="{H - B - 6}" text-anchor="end">{esc(text)}</text>')
        else:
            parts.append(f'<text x="{ex + 3:.1f}" y="{H - B - 6}">{esc(text)}</text>')
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
    elif len(series) == 1 and kind:
        parts.extend(_end_value(raw[0][1], series[0][1], kind, forecast_from, x, y, T))
    label = f"{title}. {desc}" if desc else title
    attrs = ""
    summary = ""
    if kind:
        names = [nm for nm, _, _ in raw]
        plabels = list(point_labels or labels)
        rows = [[plabels[i]] + [fmt(vals[i], kind) if vals[i] is not None else "no figure" for _, vals, _ in raw] for i in range(n)]
        read = {"x": [round(x(i), 1) for i in range(n)], "t": T, "b": H - B, "names": names, "rows": rows,
                "fc": forecast_from}
        attrs = _chart_attr(read)
        summary = chart_summary(plabels, raw, kind, ids=ids, num=num, breaks=breaks, split_breaks=split_breaks,
                                forecast_from=forecast_from, events=events, future=future)
    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(label)} The table below gives every value."{attrs}>'
           + "".join(parts) + "</svg>")
    key = ""
    if (len(series) > 1 and not direct) or forecast_from is not None:
        items = [] if direct else [f'<span><i class="{"" if s == "a" else s}"></i>{esc(nm)}</span>' for nm, _, s in series]
        if forecast_from is not None:
            items.append(f'<span><i class="d"></i>{future.capitalize()} (dashed)</span>')
        key = f'<div class="key">{"".join(items)}</div>'
    return f'<figure><p class="ctitle" aria-hidden="true">{esc(title)}</p>{key}{svg}<figcaption>{esc(unit_label)}</figcaption>{summary}</figure>'


def _chart_attr(read):
    """The readout data as a single-quoted attribute, so JSON quotes need no escaping."""
    text = json.dumps(read, ensure_ascii=False, separators=(",", ":"))
    return " data-chart='" + text.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;") + "'"


_SM_COUNT = [0]


def spark(points, label, highlight=None, group=None, axis=None):
    """A small dot chart of one measure, year by year, for a quick sense of where a year sits.

    points: (year, value or None). Missing years get no dot and a short grey mark
    on the baseline. Dots are joined only between neighbouring years in the same
    comparability group (group(year)); a dashed line marks each change of definition.
    The scale fits the values and is stated in the caption by whoever uses it.
    """
    W, H, P = 320, 56, 6
    vals = [v for _, v in points if v is not None]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or abs(hi) * 0.05 or 1
    lo, hi = lo - pad, hi + pad
    n = len(points)
    x = lambda i: P + (W - 2 * P) * (i / (n - 1) if n > 1 else 0.5)
    y = lambda v: H - P - (H - 2 * P) * (v - lo) / (hi - lo)
    g = group or (lambda _y: None)
    parts, seg = [], []
    for i, (yr, v) in enumerate(points):
        if i and g(points[i - 1][0]) != g(yr):
            if len(seg) > 1:
                parts.append(f'<polyline class="ln" points="{" ".join(seg)}"/>')
            seg = []
            bx = (x(i - 1) + x(i)) / 2
            parts.append(f'<line class="brk" x1="{bx:.1f}" y1="2" x2="{bx:.1f}" y2="{H - 2}"/>')
        if v is None:
            if len(seg) > 1:
                parts.append(f'<polyline class="ln" points="{" ".join(seg)}"/>')
            seg = []
            parts.append(f'<line class="gap" x1="{x(i) - 3:.1f}" y1="{H - 2}" x2="{x(i) + 3:.1f}" y2="{H - 2}"/>')
            continue
        seg.append(f"{x(i):.1f},{y(v):.1f}")
    if len(seg) > 1:
        parts.append(f'<polyline class="ln" points="{" ".join(seg)}"/>')
    dots = []
    for i, (yr, v) in enumerate(points):
        if v is not None:
            on = yr == highlight
            dots.append((on, f'<circle class="{"hi" if on else "pt"}" cx="{x(i):.1f}" cy="{y(v):.1f}" r="{5 if on else 2.5}"/>'))
    parts += [d for on, d in dots if not on] + [d for on, d in dots if on]
    svg = (f'<svg class="spark" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}" focusable="false">'
           f'{"".join(parts)}</svg>')
    a, b = axis or (points[0][0], points[-1][0])
    return svg + f'<div class="spark-ax" aria-hidden="true"><span>{a}</span><span>{b}</span></div>'


def small_multiples(title, labels, series, unit_label, kind, ids=None, num=None, breaks=(), split_breaks=False,
                    ymin=None, scale=1, point_labels=None, desc="", summary_note=""):
    """One small line chart per group, so no group is hidden behind a key.

    Used instead of line_chart() when more than three groups matter. Every panel
    has the same scale, so heights can be compared across panels, and shows the
    other groups as faint grey lines for context. The group is named above its
    panel and its latest value is written at the line's end.

    series: list of (name, values list (None = gap)). Missing values break the
    line; nothing is interpolated. breaks: (index, text) definition changes,
    drawn as amber dashed lines and read separately in the summary (the text is
    given in the summary, as panels are too small to label). kind, ids, num and
    point_labels work as in line_chart(): one "What the chart shows" summary for
    all groups and one tap/hover/arrow readout that marks the year in every panel.
    summary_note: where a table right beside the chart already gives each group's
    first and latest figures, say so in this sentence instead of repeating them.
    """
    raw = [(nm, vals, "a") for nm, vals in series]
    scaled = [[None if v is None else v / scale for v in vals] for _, vals in series]
    W, H = 180, 120
    L, R, T, B = 34, 6, 18, 22
    n = len(labels)
    allv = [v for vals in scaled for v in vals if v is not None]
    lo = min(allv) if ymin is None else ymin
    hi = max(allv)
    if hi == lo:
        hi = lo + 1
    step_v = _nice_step((hi - lo) / 2)
    lo2 = lo if ymin is not None else step_v * math.floor(lo / step_v)
    hi2 = step_v * math.ceil(hi / step_v)
    if hi2 <= hi:
        hi2 += step_v

    def x(i):
        return L + (W - L - R) * (i / max(1, n - 1))

    def y(v):
        return T + (H - T - B) * (1 - (v - lo2) / (hi2 - lo2))

    split_at = {i for i, _ in breaks} if split_breaks else set()

    def segments(vals):
        segs, cur = [], []
        for i, v in enumerate(vals):
            if (i in split_at and cur) or v is None:
                if cur:
                    segs.append(cur)
                cur = [] if v is None else [(i, v)]
                continue
            cur.append((i, v))
        if cur:
            segs.append(cur)
        return segs

    def path(seg):
        if len(seg) == 1:  # a lone year: a round dot drawn by the line cap
            i, v = seg[0]
            return f"M{x(i):.1f},{y(v):.1f}h0.1"
        return " ".join(f"{'M' if k == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for k, (i, v) in enumerate(seg))

    # The axes and every group's line are drawn once, in the first panel, and
    # reused by the others (<use>), which keeps pages with many panels small.
    _SM_COUNT[0] += 1
    pid = f"sm{_SM_COUNT[0]}"
    frame = []
    v = lo2
    while v <= hi2 + step_v / 1000:
        yy = y(v)
        frame.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#e3e5e8"/>')
        frame.append(f'<text x="{L - 5}" y="{yy + 5:.1f}" text-anchor="end">{_tick(v, step_v)}</text>')
        v += step_v
    frame.append(f'<text x="{x(0):.1f}" y="{H - 4}" text-anchor="start">{esc(_short(labels[0]))}</text>')
    if n > 1:
        frame.append(f'<text x="{x(n - 1):.1f}" y="{H - 4}" text-anchor="end">{esc(_short(labels[-1]))}</text>')
    for i, _ in breaks:
        bx = x(i) - (x(1) - x(0)) / 2 if n > 1 else x(i)
        frame.append(f'<line x1="{bx:.1f}" x2="{bx:.1f}" y1="{T}" y2="{H - B}" stroke="#b58900" stroke-dasharray="4 3"/>')
    drawn = {si: " ".join(path(seg) for seg in segments(vals)) for si, vals in enumerate(scaled)}
    # Each panel draws every line in light grey, then its own group in black on top.
    defs = (f'<defs><g id="{pid}f">{"".join(frame)}</g>'
            + "".join(f'<path id="{pid}s{si}" d="{d}"/>' for si, d in drawn.items() if d)
            + f'<g id="{pid}a">' + "".join(f'<use href="#{pid}s{si}"/>' for si, d in drawn.items() if d) + "</g></defs>")
    panels = []
    for si, (name, vals) in enumerate(series):
        parts = [defs] if si == 0 else []
        parts.append(f'<use href="#{pid}f"/><use href="#{pid}a" class="c"/>')
        if drawn[si]:
            parts.append(f'<use href="#{pid}s{si}" class="o"/>')
            parts.extend(_end_value(vals, scaled[si], kind, None, x, y, T - 2))
        else:
            parts.append(f'<text x="{(L + W - R) / 2:.1f}" y="{(T + H - B) / 2 + 5:.1f}" text-anchor="middle">No figures</text>')
        svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(name)}">'
               + "".join(parts) + "</svg>")
        panels.append(f'<div><p class="smt" aria-hidden="true">{esc(name)}</p>{svg}</div>')
    plabels = list(point_labels or labels)
    names = [nm for nm, _ in series]
    rows = [[plabels[i]] + [fmt(vals[i], kind) if vals[i] is not None else "no figure" for _, vals in series] for i in range(n)]
    read = {"x": [round(x(i), 1) for i in range(n)], "t": T, "b": H - B, "names": names, "rows": rows, "fc": None}
    label = f"{title}. {desc} " if desc else f"{title}. "
    grid = (f'<div class="sm" role="group" aria-label="{esc(label)}One small chart for each of {len(series)} groups, all on the same scale. The summary and table below give every value."'
            f'{_chart_attr(read)}>' + "".join(panels) + "</div>")
    key = '<p class="smkey">Each panel shows one group in black; the other groups are in light grey. All panels use the same scale.</p>'
    if summary_note:
        summary = f'<div class="csum"><p class="csum-h">What the chart shows</p><p>{summary_note}</p></div>'
    else:
        summary = chart_summary(plabels, raw, kind, ids=ids, num=num, breaks=breaks, split_breaks=split_breaks, extremes=False)
    return f'<figure><p class="ctitle" aria-hidden="true">{esc(title)}</p>{key}{grid}<figcaption>{esc(unit_label)}</figcaption>{summary}</figure>'


def _end_value(raw_vals, vals, kind, forecast_from, x, y, top):
    """Write the latest measured value beside the end of a single line."""
    pts = [i for i, v in enumerate(vals) if v is not None and (forecast_from is None or i < forecast_from)]
    if not pts:
        return []
    i = pts[-1]
    ly = max(y(vals[i]) - 9, top + 12)
    return [f'<text class="lbl" x="{x(i) - 2:.1f}" y="{ly:.1f}" text-anchor="end">{esc(fmt(raw_vals[i], kind))}</text>']


def _stretches(n, breaks, forecast_from):
    """Runs of points that can be read together: split at every definition break,
    even where the chart joins the line, and stop before any forecast years."""
    end = n if forecast_from is None else min(n, forecast_from)
    cuts = sorted(i for i, _ in breaks if 0 < i < end)
    edges = [0] + cuts + [end]
    return [(edges[k], edges[k + 1]) for k in range(len(edges) - 1) if edges[k + 1] > edges[k]]


def chart_summary(labels, series, kind, ids=None, num=None, breaks=(), split_breaks=False, forecast_from=None, events=(), future="forecast",
                  extremes=True):
    """A plain-English reading of a line chart: for each line, the first and latest
    values, the highest and lowest, and any missing years. Built from the same values
    as the chart. Nothing is compared across a definition break the chart splits at,
    and forecasts are kept apart from measured years. extremes=False leaves out the
    highest and lowest, for small multiples with many groups, where each panel shows them.
    """
    def show(si, i):
        vals = series[si][1]
        if ids and num and ids[si][i]:
            return num(ids[si][i], kind)
        return esc(fmt(vals[i], kind))

    items = []
    spans = _stretches(len(labels), breaks, forecast_from)
    for si, (name, vals, _) in enumerate(series):
        parts = []
        for a, b in spans:
            pts = [i for i in range(a, b) if vals[i] is not None]
            if not pts:
                continue
            first, last = pts[0], pts[-1]
            lead = f"{esc(labels[first])} to {esc(labels[last])}: " if len(spans) > 1 else ""
            if first == last:
                parts.append(f"{lead}{show(si, first)} in {esc(labels[first])}.")
                continue
            text = f"{lead}{show(si, first)} in {esc(labels[first])} and {show(si, last)} in {esc(labels[last])}."
            if extremes and len(pts) >= 3:
                hi = max(pts, key=lambda i: (vals[i], i))
                lo = min(pts, key=lambda i: (vals[i], -i))
                extra = []
                if hi not in (first, last):
                    extra.append(f"highest {show(si, hi)} ({esc(labels[hi])})")
                if lo not in (first, last):
                    extra.append(f"lowest {show(si, lo)} ({esc(labels[lo])})")
                if extra:
                    text += " In between: " + " and ".join(extra) + "."
            gaps = [labels[i] for i in range(first, last + 1) if vals[i] is None]
            if gaps:
                text += f" No figure for {esc(_join(gaps))}."
            parts.append(text)
        if forecast_from is not None and forecast_from < len(labels):
            fpts = [i for i in range(forecast_from, len(labels)) if vals[i] is not None]
            if fpts:
                parts.append(f"{future.capitalize()} for {esc(labels[fpts[-1]])}: {show(si, fpts[-1])}.")
        if parts:
            who = f"<strong>{esc(name)}</strong>: " if len(series) > 1 else ""
            items.append(f"<li>{who}{' '.join(parts)}</li>")
    notes = []
    for i, text in breaks:
        if split_breaks:
            notes.append(f"The line breaks at {esc(labels[i])} ({esc(text.lower())}), so values either side are not compared.")
        else:
            notes.append(f"The amber dashed line before {esc(labels[i])} marks a change ({esc(text.lower())}), so each side is read separately here.")
    for i, text in events:
        notes.append(f"The grey dotted line marks {esc(labels[i])} ({esc(text)}). It shows when it happened, not what it caused.")
    if forecast_from is not None and forecast_from < len(labels):
        notes.append(f"Years from {esc(labels[forecast_from])} are {future}s, not measurements.")
    if not items:
        return ""
    note = f'<p class="small">{" ".join(notes)}</p>' if notes else ""
    return f'<div class="csum"><p class="csum-h">What the chart shows</p><ul>{"".join(items)}</ul>{note}</div>'


def _join(xs):
    xs = [str(v) for v in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


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


# Added on top of the drawn charts: tap, hover or use the arrow keys to read one
# year's values. Without JavaScript the chart, its summary and its table still work.
CHART_JS = """<script>
document.querySelectorAll('[data-chart]').forEach(function(el){
var d=JSON.parse(el.getAttribute('data-chart')),ns='http://www.w3.org/2000/svg',cur=-1;
var svgs=el.tagName.toLowerCase()==='svg'?[el]:Array.prototype.slice.call(el.querySelectorAll('svg'));
var out=document.createElement('p');out.className='readout';out.setAttribute('aria-live','polite');
out.textContent='Tap or hover on the chart, or select it and use the arrow keys, to read each year.';
var cap=el.parentNode.querySelector('figcaption');el.parentNode.insertBefore(out,cap?cap.nextSibling:el.nextSibling);
var gs=svgs.map(function(svg){var g=document.createElementNS(ns,'line');g.setAttribute('y1',d.t);g.setAttribute('y2',d.b);g.setAttribute('stroke','#1a5fb4');g.setAttribute('stroke-width','1.5');g.style.display='none';svg.appendChild(g);return g;});
el.setAttribute('tabindex','0');
function show(i){if(i<0||i>=d.x.length)return;cur=i;var r=d.rows[i];gs.forEach(function(g){g.setAttribute('x1',d.x[i]);g.setAttribute('x2',d.x[i]);g.style.display='';});
out.textContent='';var b=document.createElement('b');b.textContent=r[0]+(d.fc!==null&&i>=d.fc?' (forecast)':'')+': ';out.appendChild(b);
out.appendChild(document.createTextNode(d.names.length>1?d.names.map(function(n,k){return n+' '+r[k+1];}).join('; '):r[1]));}
svgs.forEach(function(svg){
function near(e){var p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;var q=p.matrixTransform(svg.getScreenCTM().inverse()),best=0;
d.x.forEach(function(v,k){if(Math.abs(v-q.x)<Math.abs(d.x[best]-q.x))best=k;});return best;}
svg.addEventListener('pointermove',function(e){show(near(e));});svg.addEventListener('pointerdown',function(e){show(near(e));});});
el.addEventListener('keydown',function(e){var k=e.key,i=cur<0?d.x.length-1:cur;
if(k==='ArrowLeft'){i=Math.max(0,cur<0?i:i-1);}else if(k==='ArrowRight'){i=Math.min(d.x.length-1,cur<0?i:i+1);}else if(k==='Home'){i=0;}else if(k==='End'){i=d.x.length-1;}else{return;}
e.preventDefault();show(i);});
});
</script>"""
