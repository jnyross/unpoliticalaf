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
        "date": "4 November 2026",
        "pages": [("methods.html", "Methods"), ("spending.html", "Where does public money go?"), ("spending-areas.html", "Spending on each area, every year"),
                  ("international.html", "How do UK taxes and spending compare with other countries?")],
        "was": "The methods page said poverty and hardship “are not measured here”, though official low-income and inequality series exist. The spending page gave total spending growth without a per-person figure, so it overstated growth as the population rose. The spending-by-area summary named the largest rise by pounds, which always favours the biggest area. The first G7 chart showed four of the seven countries, with no stated rule for choosing them.",
        "now": "The methods page says those series exist and that the site does not show them yet. The spending page gives per-person spending after inflation beside the total, and its year-by-year table has a per-person column. The spending-by-area summary ranks rises in per cent. The first G7 chart shows every G7 country that has a figure for the year.",
        "pr": 176,
    },
    {
        "date": "4 November 2026",
        "pages": [("index.html", "Home"), ("life/earnings.html", "Earnings after inflation"), ("life/holidays.html", "Holidays since 1980"),
                  ("who-pays.html", "Who pays?")],
        "was": "The earnings pages called April 2025 pay provisional, although ONS's 2026 release kept it unchanged and published April 2026 pay, which the site did not mention. The home tile and the holidays chart said the visits series ends in 2023 with no reason given, and the holiday chart title said visits rose until 2019 without naming the dips before it. The 2025 holiday source record said United Kingdom residents, although the figures used from it are for Great Britain residents. The direct-taxes note left out student loan repayments.",
        "now": "The 2025 earnings figure is no longer labelled provisional. The earnings pages say ONS published April 2026 pay in October 2026 and that this series does not yet include it. The holiday tile and chart say the comparable series ends in 2023 because ONS changed method from 2024. The holiday and class-size chart titles name the smaller moves. The source record names Great Britain residents. The direct-taxes note lists student loan repayments.",
        "pr": 177,
    },
    {
        "date": "4 November 2026",
        "pages": [("spending.html", "Where does public money go?"), ("index.html", "Home"), ("life/house-prices.html", "House prices"),
                  ("life/2025.html", "Everyday life in 2025")],
        "was": "Exact halves were rounded to the even digit, so £132.5bn showed as £132bn and 31,150 thousand visits as 31.1 million. The words under the share-of-GDP chart skipped the 2021-22 low of 43.4%. The home page called ONS’s 33.6% an average across households, though it covers all people. The house-price lead said “In 2025” for the year to September 2025. A small chart of private renting on year pages ran to 2025-26, though its last figure is 2024-25.",
        "now": "Exact halves are rounded up: £133bn and 31.2 million. The words name the 2021-22 low before the 2025-26 figure. The home page says the 33.6% is an average across all people. The house-price lead says the price is for the year to September 2025 and the earnings for April 2025. The chart’s axis and caption end at its last figure.",
        "pr": 168,
    },
    {
        "date": "4 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980")],
        "was": "The chart title said holiday visits abroad “rose until 2019, fell in 2021, then rose until 2023; later years use a new method and are not compared”, although the chart also shows 2024 and 2025, including the 58.4 million in the headline. The title read as if the chart stopped in 2023.",
        "now": "The title names the two years after the method change: “…then rose until 2023; 2024 and 2025 use a new method and are not compared”.",
        "pr": 166,
    },
    {
        "date": "3 November 2026",
        "pages": [("household-tax.html", "How much of household income goes on tax?")],
        "was": "A heading asked “Why did direct taxes rise in 2023/24?”, and the explanation under it said fiscal drag made people pay a greater proportion of their income in tax. The page's own figures showed direct taxes fell as a share of gross income, from 23.2% in 2022/23 to 22.9% in 2023/24.",
        "now": "The heading asks why direct taxes rose in cash. A note beside it says their share of gross income fell, and that after inflation they fell for the average household.",
        "pr": 156,
    },
    {
        "date": "3 November 2026",
        "pages": [("life/index.html", "Everyday life, year by year"), ("life/work.html", "Work"), ("life/earnings.html", "Earnings"),
                  ("who-pays.html", "Who pays?"), ("who-pays-households.html", "Retired people and kinds of household"),
                  ("taxes.html", "Which taxes raise the money?"), ("life/housing-places.html", "Housing in each region and nation")],
        "was": "The life page's home-ownership chart was labelled to 2025-26, though the latest figure is 2024-25, and its class sizes compared January 2025 with 2008 although the series starts in 2006. "
               "Men's employment was said to fall “to a low of 75.4% in 2010”, though 1993 was lower (75.1%). Who pays described the ONS's retired households as “the households that retired people live in”. "
               "The taxes page said Corporation Tax includes North Sea profits without saying the other North Sea taxes are in “all other taxes”, and called debt “93.3% of a year's GDP”. "
               "Scotland's private renting was not marked as including homes that come with a job or business.",
        "now": "The chart ends at 2024-25 and class sizes are compared with January 2006. The 2010 figure is no longer called the low. Retired households are defined as those where more than half the income comes from retired people. "
               "The taxes page names the Energy Profits Levy and Petroleum Revenue Tax and gives debt as a share of GDP on the OBR's measure. Scotland's figure says it includes homes tied to a job.",
        "pr": 154,
    },
    {
        "date": "3 November 2026",
        "pages": [("index.html", "Home"), ("who-pays.html", "Who pays?"), ("who-pays-households.html", "Retired people and kinds of household"),
                  ("borrowing.html", "Debt and borrowing costs"), ("life/schools.html", "Class sizes")],
        "was": "The home page and the who-pays headline said 27.2% of Income Tax “was paid by” the top 1%; HMRC's figure is Income Tax owed for the year. The borrowing page said the government “paid an average of 4.58% a year to borrow for 10 years”, which is the market yield on 10-year gilts, not the rate paid on its debt. Retired people's tax figures were described as “retired households”, though they are averages over people. The class size title said primary classes “rose until 2016, then fell”, though they were 27.1 in every year from 2016 to 2019.",
        "now": "The top 1% “owed” 27.2% of Income Tax, and the who-pays chart shows each group's share of income beside its share of tax. The borrowing page calls 4.58% the market interest rate on 10-year bonds and says it is not the average rate on existing debt. Retired people's figures are for the households they live in. Chart titles and summaries now say when a peak or low was held: primary class sizes “rose until 2016, held level until 2019, then fell”.",
        "pr": 148,
    },
    {
        "date": "3 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980"), ("life/house-prices.html", "House prices and earnings")],
        "was": "Both holiday chart titles said visits “rose back to about the 2019 level”. On the first chart, readers could set the 2025 figure (Great Britain residents, new method) against 2019 (UK residents, old method), across the method change the page says is not compared; on the second, 126 visits per 100 residents in 2023 was called about the same as 140 in 2019. The holidays summary gave visits for any purpose to Spain (19.1 million), France (9.1 million) and Italy (5.7 million) as if they were holidays. The house prices and earnings title described 1997 and 1998 together with later years, across the 1999 change in how earnings are counted.",
        "now": "The first holiday title stops at 2023 and says later years use a new method and are not compared; the second says visits rose back part of the way and that the series ends in 2023. The summary gives holiday visits by country (Spain 15.6 million, France 5.9 million and Greece 4.3 million in 2025; Italy, third for all visits, had 3.6 million) and labels the all-purpose ranking as such. The house prices title starts at 1999. A build check now fails any chart title that describes years either side of a marked break, or compares with an earlier level when the line goes on past a break.",
        "pr": 142,
    },
    {
        "date": "3 November 2026",
        "pages": [("spending.html", "Where does public money go?"), ("tax-history.html", "Which taxes raised the money since 1948?"),
                  ("life/house-prices.html", "House prices and earnings"), ("borrowing.html", "Debt and borrowing costs"),
                  ("life/earnings.html", "Earnings"), ("spending-history.html", "Spending by purpose over 100 years")],
        "was": "The spending page said “£11 of every £100 went on debt interest” without saying the £100 was spending on services. Tax history said Income Tax was “between 9% and 10% of GDP” every year from 1999-00 (it was 8.6% to 8.8% from 2012-13 to 2019-20), called 17.1% in 2009-10 National Insurance’s high when it later reached 18.2%, and ranked the largest rise without saying “Everything else” rose more. House prices were compared with 1997, whose earnings ONS says are not directly comparable with later years. Some summaries named one “largest” change when two were equal, or called £716 to £716 a fall. The borrowing page led with a single month’s bond yield and listed causes of yields in its own words.",
        "now": "The £11 is “of every £100 spent on services” (£9.6 of every £100 of all spending). Income Tax is given as 8.6% to 10.0% of GDP; a turn is called “a high” only when no later year is higher; and the ranking says “Everything else” rose more. House prices are compared from 1999. Equal changes are named together and a change that rounds to nothing is not called a rise or fall. The borrowing page leads with the latest full year and attributes what moves yields to the Debt Management Office and the OBR.",
        "pr": 139,
    },
    {
        "date": "3 November 2026",
        "pages": [("life/schools.html", "Class sizes since 2006"), ("life/house-prices.html", "House prices and earnings"),
                  ("household-tax.html", "How much household income goes on tax?"), ("index.html", "Home")],
        "was": "The chart title for primary pupils in classes of more than 30 ended “then rose”, and its summary called January 2020 the high. The share was highest in January 2025 (13.3%) and fell to 12.6% in January 2026. Titles on house prices and on household taxes since 2018/19 also left out a fall in their latest years. The home page called January 2025 and April to June 2025 the latest figures for class sizes and work, when January 2026 and April to June 2026 were already published.",
        "now": "The titles and summaries name the latest peak or low and the move after it, such as “rose until January 2025, then fell in January 2026”, and a build check fails if a title hides a turn like this. The home page shows the January 2026 class size and the April to June 2026 employment rate.",
        "pr": 135,
    },
    {
        "date": "3 November 2026",
        "pages": [("spending.html", "Where does public money go?"), ("index.html", "Home")],
        "was": "The spending page said “State pensions alone cost £155bn”. That figure is HM Treasury’s “old age: of which pensions” line, which covers more than the State Pension. The home page also said every everyday-life topic had figures from 2008, but holidays start in 2009.",
        "now": "The £155bn is described as HM Treasury’s old age pensions line, which covers more than the State Pension alone. The home page, the life hub and the early-year pages say holidays start in 2009.",
        "pr": 131,
    },
    {
        "date": "3 November 2026",
        "pages": [("household-tax.html", "How much household income goes on tax?"), ("index.html", "Home")],
        "was": "The household tax page explained the lowest-income fifth’s indirect taxes in its own words (“because their households spend more of their income, some of it from savings or borrowing”), and a chart title said taxes took “the largest share of income” for the lowest-income fifth in 2023/24, when it was 36.7% against 36.2% for the highest-income fifth. The home page card showed the shares by fifth with no word on what they were made of.",
        "now": "The explanation is now a quote from the ONS, with its source and date. The chart title says the two fifths had a similar share, less than one percentage point apart. The home page card says the lowest-income fifth’s share is mostly indirect tax such as VAT and the highest-income fifth’s mostly direct tax such as Income Tax.",
        "pr": 129,
    },
    {
        "date": "3 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980"), ("life/index.html", "Everyday life")],
        "was": "Holiday visits abroad in 2020 were given as 4.4 million, about 7 for every 100 residents, and drawn on the charts as the year’s low. ONS’s 2020 figures by purpose of visit come only from the passenger survey, which stopped on 16 March 2020, so they cover only January to mid-March, not the whole year.",
        "now": "2020 has no holiday figure on the charts, in comparisons or per 100 residents. The holidays page says the survey stopped on 16 March and gives the 4.4 million as January to mid-March only. Line charts whose scale starts above zero now say so under the chart, and a build check fails if one does not.",
        "pr": 126,
    },
    {
        "date": "2 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980"), ("spending.html", "Where does public money go?")],
        "was": "Two chart titles named only one turn in a line that turned more than once: “Holiday visits abroad by UK residents fell until 2020, then rose above the 2009 level” (they rose from 41.2 million in 2009 to 58.7 million in 2019 first), and “As a share of GDP, total public spending rose until 2020-21, then fell back part of the way” (it fell from 46.0% in 2009-10 to 39.1% in 2018-19 first).",
        "now": "Chart titles and their summaries in words name every large rise and fall in order, for example “Holiday visits abroad by UK residents rose until 2019, fell in 2020, then rose back to about the 2019 level”. A build check now fails if a title leaves one out.",
        "pr": 118,
    },
    {
        "date": "2 November 2026",
        "pages": [("sources.html", "Sources"), ("life/work.html", "Work since 1971")],
        "was": "The link to the original data for the two occupation sources (Annual Population Survey by occupation, SOC2010 and SOC2020) went to the whole Nomis dataset, which gives different figures, so a reader could not reproduce the numbers.",
        "now": "The link is the exact Nomis query that gives the data used. A random check of 50 figures against the publishers’ files found every figure matched.",
        "pr": 110,
    },
    {
        "date": "2 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980"), ("life/compare/2024-2025.html", "2024 compared with 2025")],
        "was": "Holidays abroad in 2024 were compared with 2025 as if measured the same way, for example holiday visits abroad rising from 56.0 million to 58.4 million.",
        "now": "ONS says annual 2024 figures mix the old survey (January to June) and the new one (July to December), so 2024 is now compared with neither earlier years nor 2025.",
        "pr": 105,
    },
    {
        "date": "2 November 2026",
        "pages": [("life/holidays.html", "Holidays since 1980"), ("life/work.html", "Work since 1971")],
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
<dt>Retrieved</dt><dd>{esc(s["retrieved"])}</dd>
<dt>SHA-256</dt><dd><code class="hash">{esc(s["sha256"])}</code></dd>
</dl>
<p><a href="{up}sources.html#src-{esc(sid)}">Back to the list of sources</a></p>
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
# Reading pages have a tighter size limit (build.MAX_READING_PAGE_BYTES); a reading
# page that would pass it with full records falls back to source-only records instead.
READING_BUDGET = 245_000

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
    budget = FULL_BUDGET if path.startswith(FIG_DIR + "/") else min(FULL_BUDGET, READING_BUDGET)
    if len(html.encode()) + len(text.encode()) > budget:
        text = blob(False)
    up = "../" * path.count("/")
    tag = f'<script type="application/json" id="trace-data" data-up="{up}">{text}</script>\n{TRACE_JS}'
    return html.replace("</body>", tag + "\n</body>", 1)
