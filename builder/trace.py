"""Trace any figure back to its source.

Three pieces:

- Figure records: one page per source (figures/<source>.html) with an entry
  for every figure the site shows from it, plus the inputs of any
  calculation. Each entry gives the value, period, status and the exact sheet
  and cell, or the calculation with links to its inputs.
- Tap to trace: a small script on every page. Tapping a number opens a panel
  with its source, period and cell or calculation, and a link to its record.
  Without JavaScript, every source line links to the same records.
- Corrections: a public log of errors found and fixed (corrections.html).
"""
import json
import re

from .html import esc, page

FIG_DIR = "figures"

# Errors found on the live site and fixed. Newest first. Add an entry whenever
# a published figure, label or explanation is corrected.
CORRECTIONS = [
    {
        "date": "2 November 2026",
        "pages": [("life/holidays.html", "Holidays since 2008"), ("life/work.html", "Work since 2008")],
        "was": "The holidays section said “The pandemic cut holidays abroad to 4.4 million in 2020”, which states a cause in our own words. The chart titled “Employment rate by age” showed only three of the five age groups.",
        "now": "“In 2020, the first year of the Covid-19 pandemic, holidays abroad fell to 4.4 million.” The chart is titled with the three age groups it shows, and says the other two are in the table.",
        "pr": 86,
    },
    {
        "date": "2 November 2026",
        "pages": [("index.html", "Home"), ("who-pays.html", "Who pays?")],
        "was": "The top 1% share of Income Tax was given without their share of income, which a reader needs to judge it.",
        "now": "Both figures are given together: in 2023-24 the top 1% of Income Tax payers paid 27.2% of Income Tax and had 12.4% of Income Tax payers’ income.",
        "pr": 86,
    },
    {
        "date": "2 November 2026",
        "pages": [("index.html", "Every page (footer)")],
        "was": "The footer said every figure links to its source, but figures could only be traced through the source line under each section, which leads to the whole table rather than the figure.",
        "now": "Tapping any figure shows its source, period and the exact cell or calculation, and each source line leads to a record of every figure taken from that source.",
        "pr": 84,
    },
    {
        "date": "2 November 2026",
        "pages": [("who-pays.html", "Who pays?"), ("household-tax.html", "How much household income goes on tax?")],
        "was": "The ONS income fifths were described as equal-sized groups of households.",
        "now": "They are described as fifths of people, ranked by their household’s income, which is how ONS builds them. The amounts are still per household, as ONS publishes them.",
        "pr": 71,
    },
]

REPO = "https://github.com/jnyross/unpoliticalaf"

STATUS = {
    "outturn": "Published outturn (what happened)",
    "published": "Published figure",
    "forecast": "Forecast by the publisher",
    "projection": "Projection by the publisher",
    "calculated": "Calculated by Unpolitical from published figures",
    "provisional": "Provisional: the publisher may revise it",
    "missing": "Not published for this period",
}


def anchor(fid):
    """A safe, unique HTML id for a figure id (some contain spaces)."""
    return "f-" + re.sub(r"[^A-Za-z0-9_.-]", "_", fid)


def record_href(facts, fid, up=""):
    return f"{up}{FIG_DIR}/{facts[fid].source}.html#{anchor(fid)}"


def where(f):
    """Where in the source file the figure was read, in plain words."""
    loc = f.locator or ""
    m = re.fullmatch(r"(.+)!\$?([A-Z]+)\$?(\d+)", loc)
    if m:
        return f"Sheet “{m.group(1).strip(chr(39))}”, cell {m.group(2)}{m.group(3)}"
    return loc


def value_text(f):
    if f.value is None:
        return "not available"
    v = f.value
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.4f}".rstrip("0").rstrip(".")
    return f"{s} ({f.unit})" if f.unit else s


def _closure(facts, ids):
    seen, todo = set(), list(ids)
    while todo:
        fid = todo.pop()
        if fid in seen or fid not in facts:
            continue
        seen.add(fid)
        todo.extend(facts[fid].inputs)
    return seen


def figure_pages(facts, sources, used):
    """One record page per source, covering the figures shown and their inputs."""
    ids = _closure(facts, used)
    anchors = {}
    for fid in ids:
        a = anchor(fid)
        if anchors.setdefault(a, fid) != fid:
            raise ValueError(f"figure ids {fid!r} and {anchors[a]!r} share the anchor {a}")
    by_src = {sid: [] for sid in sources}
    for fid in ids:
        by_src.setdefault(facts[fid].source, []).append(fid)
    pages = {}
    for sid, fids in by_src.items():
        s = sources[sid]
        up = "../"
        rows = []
        for fid in sorted(fids):
            f = facts[fid]
            dl = [("Value", esc(value_text(f))), ("Period", esc(f.period)), ("Status", esc(STATUS.get(f.status, f.status)))]
            if f.formula:
                dl.append(("Calculation", esc(f.formula)))
                links = ", ".join(f'<a href="{"" if facts[i].source == sid else facts[i].source + ".html"}#{anchor(i)}"><code>{esc(i)}</code></a>'
                                  for i in f.inputs if i in facts)
                if links:
                    dl.append(("Inputs", links))
            if f.locator and not f.formula:
                dl.append(("Read from", esc(where(f))))
            if f.scale != 1:
                dl.append(("Scaling", f"Source value × {f.scale:g}"))
            if f.note:
                dl.append(("Note", esc(f.note)))
            body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in dl)
            rows.append(f'<section class="fig" id="{anchor(fid)}"><h3><code>{esc(fid)}</code></h3><dl>{body}</dl></section>')
        intro = f'''<h1>{esc(s["title"])}: every figure used</h1>
<p>Each figure on Unpolitical that comes from this source is listed below with the exact place it was read from, or the calculation that produced it. Figures are listed by their id, which is also used in the <a href="{up}data/facts.json">downloadable data</a>.</p>
<dl class="srcmeta">
<dt>Publisher</dt><dd>{esc(s["publisher"])}</dd>
<dt>Where</dt><dd>{esc(s["geography"])}</dd>
<dt>Who or what</dt><dd>{esc(s["population"])}</dd>
<dt>Published</dt><dd>{esc(s["published"])}</dd>
<dt>Original</dt><dd><a href="{esc(s["page"])}">{esc(s["page"])}</a></dd>
<dt>File kept</dt><dd><code>{esc(s["file"])}</code> (<a href="{REPO}/blob/main/{esc(s["file"])}">in the public repository</a>)</dd>
<dt>Licence</dt><dd>{esc(s["licence"])}</dd>
</dl>
<p><a href="{up}methods.html#src-{esc(sid)}">Back to sources and methods</a></p>
<h2 id="figures">{len(fids):,} figures</h2>''' + ("" if fids else "<p>No figure from this source is shown directly. It is used for rates or explanations quoted in the text.</p>")
        pages[f"{FIG_DIR}/{sid}.html"] = page(f"{FIG_DIR}/{sid}.html", f"Figures from {s['title']}", intro + "\n".join(rows),
                                             f"Every figure Unpolitical uses from {s['publisher']}: {s['title']}, with its cell or calculation.", contents=False)
    return pages


def corrections_page():
    items = []
    for c in CORRECTIONS:
        where_ = ", ".join(f'<a href="{href}">{esc(t)}</a>' for href, t in c["pages"])
        items.append(f'''<section class="correction"><h2>{esc(c["date"])}</h2>
<dl><dt>Page</dt><dd>{where_}</dd>
<dt>What was wrong</dt><dd>{esc(c["was"])}</dd>
<dt>What it says now</dt><dd>{esc(c["now"])}</dd>
<dt>Change</dt><dd><a href="{REPO}/pull/{c["pr"]}">Change {c["pr"]} in the public repository</a></dd></dl></section>''')
    body = f'''<h1>Corrections</h1>
<p>When we find a mistake in a figure, a label or an explanation, we fix it and record it here: what it said, what it says now, and the change that fixed it. Every change to the site is also public in the <a href="{REPO}/commits/main">code repository</a>.</p>
<p>If you think something is wrong, <a href="{REPO}/issues/new">tell us on GitHub</a>.</p>
{"".join(items)}'''
    return page("corrections.html", "Corrections", body, "Mistakes found on Unpolitical and how they were fixed.", contents=False)


FULL_BUDGET = 330_000  # bytes; above this a page carries only each figure's source

FACT_RE = re.compile(r'data-fact="([^"]+)"')
CHANGE_RE = re.compile(r'data-from="([^"]+)"[^>]*?data-to="([^"]+)"')

TRACE_JS = """<script>
(function(){
var el=document.getElementById('trace-data');if(!el)return;
var D=JSON.parse(el.textContent),up=el.getAttribute('data-up'),S=D.s,F=D.f;
document.documentElement.classList.add('tr');
var box=document.createElement('div');box.id='trace';box.className='trace';box.setAttribute('role','dialog');box.setAttribute('aria-labelledby','trace-h');box.hidden=true;
document.body.appendChild(box);var back=null;
function t(tag,txt,cls){var e=document.createElement(tag);if(txt)e.textContent=txt;if(cls)e.className=cls;return e}
function row(dl,k,v){dl.appendChild(t('dt',k));var dd=t('dd');if(typeof v==='string')dd.textContent=v;else dd.appendChild(v);dl.appendChild(dd)}
function src(id){var r=F[id];return S[typeof r==='number'?r:r[0]]}
function link(id,txt){var a=t('a',txt);a.href=up+'figures/'+src(id)[0]+'.html#f-'+id.replace(/[^A-Za-z0-9_.-]/g,'_');return a}
function close(){box.hidden=true;if(back){back.focus();back=null}}
function open(target,ids,title){
box.innerHTML='';var h=t('p','Where this number comes from','trace-h');h.id='trace-h';box.appendChild(h);
if(title)box.appendChild(t('p',title,'trace-v'));
ids.forEach(function(id){var r=F[id];if(r===undefined)return;var dl=t('dl'),full=typeof r!=='number';
row(dl,'Source',src(id)[1]);if(full){row(dl,'Period',D.p[r[1]]);if(D.t[r[2]])row(dl,'Status',D.t[r[2]]);row(dl,r[4]?'Calculated':'Read from',r[3])}
box.appendChild(dl);var p=t('p');p.appendChild(link(id,full?'See the full record':'See its period and exact cell'));box.appendChild(p)});
var b=t('button','Close','trace-x');b.type='button';b.onclick=close;box.appendChild(b);
back=target;target.setAttribute('tabindex','-1');box.hidden=false;b.focus()}
document.addEventListener('click',function(e){
var d=e.target.closest&&e.target.closest('data[data-fact],data[data-from]');
if(d&&!d.closest('a,#trace')){var ids=d.hasAttribute('data-fact')?[d.getAttribute('data-fact')]:[d.getAttribute('data-from'),d.getAttribute('data-to')];
open(d,ids,d.hasAttribute('data-from')?'A change worked out from these two figures:':'');e.preventDefault();return}
if(!box.hidden&&!e.target.closest('#trace'))close()});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!box.hidden)close()});
})();
</script>"""


def add_trace(html, path, facts, sources):
    """Embed the trace records for the figures on this page and the tap script."""
    ids = set(FACT_RE.findall(html))
    for a, b in CHANGE_RE.findall(html):
        ids.update((a, b))
    ids = {i for i in ids if i in facts}
    if not ids:
        return html
    srcs = sorted({facts[i].source for i in ids})
    si = {sid: n for n, sid in enumerate(srcs)}
    # Pages with very many figures (the explorer) carry only each figure's
    # source, to stay small on phones; the record is one more tap away.
    def blob(full):
        # Periods and statuses repeat across many figures, so each is listed once and referred to by number.
        periods = sorted({facts[i].period for i in ids})
        statuses = sorted({STATUS.get(facts[i].status, facts[i].status) for i in ids})
        pi, ti = {v: n for n, v in enumerate(periods)}, {v: n for n, v in enumerate(statuses)}
        data = {
            "s": [[sid, f'{sources[sid]["publisher"]}: {sources[sid]["title"]}'] for sid in srcs],
            "f": {i: ([si[facts[i].source], pi[facts[i].period], ti[STATUS.get(facts[i].status, facts[i].status)],
                       facts[i].formula or where(facts[i]), 1 if facts[i].formula else 0] if full else si[facts[i].source])
                  for i in sorted(ids)},
        }
        if full:
            data["p"], data["t"] = periods, statuses
        return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    text = blob(True)
    if len(html.encode()) + len(text.encode()) > FULL_BUDGET:
        text = blob(False)
    up = "../" * path.count("/")
    tag = f'<script type="application/json" id="trace-data" data-up="{up}">{text}</script>\n{TRACE_JS}'
    return html.replace("</body>", tag + "\n</body>", 1)
