"""Home page, the methods page and the list of sources."""
import re

from .html import page, esc, table, bars


def home_page(facts, d, num, sources):
    sp = d["spending"]["latest"]
    y = "2025-26"
    L = 2025
    from .pages_life import FIRST, earn_stretches, earn_before_after, _how_short
    ea, eb, ech = earn_stretches(facts)[0]
    from .data import EARLY_YEARS
    E = EARLY_YEARS[0]
    per = d["spending"]["per100"]
    names = {k: v["name"] for k, v in d["spending"]["views"]["cash"]["series"].items()}
    top3 = sorted((k for k in names if k in per and k not in ("services", "adjustments", "tme", "debt_interest", "transport", "eu")),
                  key=lambda k: -facts[per[k]].value)[:3]

    def mini(html):
        # A small picture of the card's figures. The card text says the same in words,
        # so it is hidden from screen readers to keep the link name short.
        return f'<div class="mini" aria-hidden="true">{html}</div>'

    v_spend = mini(bars([(esc(names[k]), per[k], "") for k in top3], "per100", num, maxval=100))
    v_tax = mini(bars([("Income Tax", f"rec.share.income_tax.{y}", ""), ("National Insurance", f"rec.share.nics.{y}", ""),
                       ("VAT", f"rec.share.vat.{y}", "")], "pct0", num, maxval=100))
    v_who = mini(bars([("Their share of taxpayers' income", "hmrc.income.top1.2023 to 2024", "alt"),
                       ("Their share of Income Tax", "hmrc.share.top1.2023 to 2024", "")], "pct", num, maxval=100))
    fifths = ["Lowest-income fifth", "Second fifth", "Middle fifth", "Fourth fifth", "Highest-income fifth"]
    v_hh = mini(bars([(f, f"etb.t8.gross.all.q{i + 1}", "") for i, f in enumerate(fifths)], "pct", num, maxval=100))
    from .pages_history import long_spark, FIRST_YEAR as FY

    def newest(fid):
        """The explorer's last year, or the year after when a newer figure is out (work and class sizes)."""
        return L + 1 if fid(L + 1) in facts and facts[fid(L + 1)].value is not None else L
    Lw, Ls = newest(lambda yr: f"work.rate.{yr}"), newest(lambda yr: f"school.primary.{yr}")
    # Each card's small chart shows the topic's longest series (audit 11 gap 3).
    sparks = {"work": mini(long_spark(facts, num, "work", Lw, caption=False)),
              "earnings": mini(long_spark(facts, num, "earnings", L, caption=False)),
              "housing": mini(long_spark(facts, num, "housing", 2024, caption=False)),
              "holidays": mini(long_spark(facts, num, "holidays", caption=False)),
              "schools": mini(long_spark(facts, num, "schools", Ls, caption=False))}
    body = [f'''<div class="hero"><h1>Public money and everyday life in the UK, in plain numbers</h1>
<p class="lede">Where public money goes, who pays for it, and how work, pay, housing, holidays and schools have changed. Every figure is an official statistic, and shows where it comes from and what it can't tell you.</p></div>
<h2 id="money">Public money: four questions</h2>
<div class="cards">
<a class="card" href="spending.html"><h3>Where does public money go?</h3>
<span class="big">{num(f"spend.cash.tme.{sp}", "bn")}</span>
<p>spent by the public sector in {esc(sp)}. HM Treasury splits {num(f"spend.cash.services.{sp}", "bn")} of this by area, the spending on services; the rest is accounting entries it does not split. Of every £100 spent on services, the largest area was social protection, including pensions: {num(per["social"], "per100")}. General public services ({num(per["general"], "per100")}) includes debt interest ({num(per["debt_interest"], "per100")} of the {num(per["general"], "per100")}), counted as interest paid out; the “net” figure the OBR and IFS often quote, after interest received, is lower.</p>
{v_spend}
<span class="more">Spending by area and over time</span></a>
<a class="card" href="taxes.html"><h3>Which taxes raise the money?</h3>
<span class="big">{num(f"rec.taxes.{y}", "bn")}</span>
<p>raised in taxes in {y}. Income Tax, National Insurance and VAT raised {num(f"rec.big3share.{y}", "pct0")} of it. Borrowing covered another {num(f"agg.psnb.{y}", "bn")}.</p>
{v_tax}
<span class="more">Taxes, other receipts and borrowing</span></a>
<a class="card" href="who-pays.html"><h3>Who pays?</h3>
<span class="big">{num("hmrc.share.top1.2023 to 2024", "pct")}</span>
<p>of all Income Tax for the year was owed by the top 1% of Income Tax payers in 2023 to 2024. They had {num("hmrc.income.top1.2023 to 2024", "pct")} of all Income Tax payers' income. Every household also pays taxes on spending, such as VAT.</p>
{v_who}
<span class="more">Income Tax and all taxes, by group</span></a>
<a class="card" href="household-tax.html"><h3>How much household income goes on tax?</h3>
<span class="big">{num("etb.t8.gross.all.all", "pct")}</span>
<p>of gross household income, on average across everyone, in 2023/24. That is an average across households, not anyone's tax rate. By income fifth:</p>
{v_hh}
<p>For the lowest-income fifth, most of this is indirect tax such as VAT ({num("etb.t8.gross.indirect.q1", "pct")} of income, or {num("etb.t8.spend.indirect.q1", "pct")} of their spending: the share depends on what it is divided by); for the highest-income fifth, most is direct tax such as Income Tax.</p>
<span class="more">Direct, indirect and combined taxes</span></a>
</div>
<p><a href="international.html">How do UK taxes and spending compare with other countries?</a> The UK beside the other OECD countries, as a share of GDP.</p>
<p><a href="borrowing.html">How do UK debt and borrowing costs compare with other major countries?</a> Debt, 10-year borrowing costs and debt interest beside the other G7 countries.</p>
<h2 id="life">Everyday life, year by year</h2>
<p>Pick any year from {E} to {L}, or compare two. Work, earnings, housing and class sizes have figures from {FIRST} and holidays from {FIRST + 1}, and some reach further back. Each topic shows the latest figure and what it covers, with a small chart of its longest official series: the employment rate since {FY["work"]}, home ownership in England since {FY["housing"]}, visits abroad since {FY["holidays"]}, pay since {FY["earnings"]} and class sizes since {FY["schools"]}. In each small chart the dark dot is the latest year, a gap means no figure, and a dashed line means the definition or survey changed. The small charts do not start at zero.</p>
<div class="cards">
<a class="card" href="life/work.html"><h3>Work</h3><span class="big">{num(f"work.rate.{Lw}", "pct")}</span><p>of people aged 16 to 64 were in work, April to June {Lw}, UK. The year pages stop at {L}.</p>{sparks["work"]}</a>
<a class="card" href="life/earnings.html"><h3>Earnings after inflation</h3>{earn_before_after(num, ea, eb, ech)}<p>a week before tax for the middle full-time employee, UK, both in April {L} prices: <strong>{_how_short(ech).lower()}</strong>. In cash, {num(f"earn.ft.{ea}", "pounds")} to {num(f"earn.ft.{eb}", "pounds")}. Compared from {ea}, when the survey last changed how it codes jobs. The {L} figure is provisional. The small chart shows each year since {FY["earnings"]} after inflation.</p>{sparks["earnings"]}</a>
<a class="card" href="life/housing.html"><h3>Housing</h3><span class="big">{num("house.owners.2024", "pct0")}</span><p>of households in England owned their home, 2024-25.</p>{sparks["housing"]}</a>
<a class="card" href="life/holidays.html"><h3>Holidays</h3><span class="big">{num(f"hol.world.holiday.{L}", "millions")}</span><p>holiday visits abroad by Great Britain residents in {L}. The small chart shows visits abroad for any purpose per 100 UK residents, {FY["holidays"]} to 2023, when that series ends.</p>{sparks["holidays"]}</a>
<a class="card" href="life/schools.html"><h3>Class sizes</h3><span class="big">{num(f"school.primary.{Ls}", "dp1")}</span><p>pupils in the average state primary school class in England, January {Ls}. The year pages stop at {L}.</p>{sparks["schools"]}</a>
<a class="card" href="life/compare/index.html"><h3>Compare two years</h3><p>See any two years from {E} to {L} side by side, with what changed and where definitions changed. Before {FIRST} fewer figures exist.</p><span class="more">Choose two years</span></a>
</div>
<h2 id="how">How to read this site</h2>
<ul class="principles">
<li><strong>Every number has a source.</strong> Each section names the official source, and the sources page gives the exact file, table and cell.</li>
<li><strong>Gaps stay gaps.</strong> When a year is missing or a definition changed, we say so and don't fill it in.</li>
<li><strong>Illustrations are labelled.</strong> Anything invented to explain a rule, such as a worked example, is marked “Illustration, not a statistic”.</li>
<li><strong>Change is not cause.</strong> Figures show what changed, not why. Where an official body has explained a change, we quote its own words and say who said it.</li>
</ul>''']
    return page("index.html", "Unpolitical", "\n".join(body), contents=False, description="Independent, plain-English answers about UK public spending, taxes and everyday life, from official statistics.")


def methods_page(facts, sources, used_counts):
    body = ['<h1>Methods</h1>',
            '<p>Every number on this site is copied or calculated from the official files in the <a href="sources.html">list of sources</a>. The files are kept in the site’s public code repository, and the build stops if any file changes without its record being updated.</p>',
            '<h2 id="principles">Principles</h2><ul>'
            '<li><strong>Official sources only.</strong> Figures come from UK government departments, the Office for National Statistics and the Office for Budget Responsibility.</li>'
            '<li><strong>No invented continuity.</strong> Missing years are shown as missing. Where a definition changes, the series is broken and no change is calculated across the break.</li>'
            '<li><strong>No invented households presented as fact.</strong> Where a made-up person helps explain a rule, it is labelled “Illustration, not a statistic” and kept apart from the official figures.</li>'
            '<li><strong>Change is not cause.</strong> The site shows what changed. It does not say why in its own words. Where an official body such as the Office for National Statistics or HM Revenue and Customs has published its own explanation, we quote it word for word, name who said it, and link to it. The check confirms that every quote still matches the publication.</li>'
            '<li><strong>Neutral language.</strong> We describe figures; we don’t judge them.</li>'
            '<li><strong>How we choose what to show.</strong> Headline figures use the publisher’s own main measure for the latest year it has measured. '
            'Comparisons over time use fixed windows (ten years for spending by area, the first and latest year for each series) and the same lead figure on every comparison page, '
            'whichever way it moved, so years are not picked for the result. Bars always start at zero. Line charts show their scale on the axis and may not start at zero, so that change is visible.</li></ul>',
            '<h2 id="calculations">Calculations</h2><ul>'
            '<li><strong>Per £100 of spending</strong>: spending on a function ÷ total spending on services × 100 (HM Treasury PESA Table 4.2). Interest on debt is part of general public services and is shown on the same basis; the spending page also gives it per £100 of total managed expenditure.</li>'
            '<li><strong>Real terms (spending)</strong>: HM Treasury’s own 2025-26 prices (PESA Table 4.3).</li>'
            '<li><strong>Pay after inflation</strong>: cash pay × (CPIH in April 2025 ÷ CPIH in April of that year), using ONS series L522.</li>'
            '<li><strong>Changes in percentages</strong> are shown in percentage points; changes in money and counts as a percentage of the earlier figure.</li>'
            '<li><strong>Non-tax receipts</strong>: total current receipts minus taxes (OBR).</li>'
            '<li><strong>Families with children renting privately</strong>: private-renting families ÷ all families, adding couples, single lone parents and previously married lone parents (EHS FT1241).</li>'
            '<li><strong>Housing costs after inflation</strong>: cash rent or mortgage payment × (average CPIH over the latest survey year ÷ average CPIH over that survey year). A survey year runs from April to the following March, so each average uses the twelve monthly CPIH values (ONS series L522) for those months.</li>'
            '<li><strong>Households with five or more rooms</strong>: the published percentages with five, six, seven, and eight or more rooms, added together (EHS FA1401).</li>'
            '<li><strong>Holiday share of visits</strong> and <strong>Europe share</strong>: holiday visits ÷ all visits, and holiday visits to Europe ÷ all holiday visits.</li>'
            '<li><strong>Holidays per 100 residents</strong>: holiday trips × 100 ÷ mid-year population (ONS UKPOP up to 2023 for trips abroad, GBPOP from 2024 and for trips within Great Britain). This is an average over everyone, including children and people who took no holiday.</li>'
            '<li><strong>Most visited countries</strong>: single countries ranked by visits in that year; groups such as “Rest of Europe” are left out.</li>'
            '<li><strong>Margins of error</strong>: shown only where the publisher gives one (95%). Where ONS gives a coefficient of variation (CV), margin = 1.96 × CV ÷ 100 × figure. Where it gives lower and upper limits, margin = half the gap between them, as a share of its estimate. A change is compared with the two margins combined, √(a² + b²). See <a href="uncertainty.html">how sure are these figures?</a></li></ul>',
            '<h2 id="data">Every figure, machine-readable</h2>',
            f'<p><a href="data/facts.json">Download all {len(facts):,} figures as JSON</a>. Each has an id, value, unit, period, source id, the exact sheet and cell (or a description of the calculation and its inputs), and whether it is published outturn, a forecast, a projection or our calculation. Figures on each page are tagged with the same id.</p>',
            '<p>Every chart and table also has a "Download this data (CSV)" link beside it. The file holds the same figures the page shows, written as they are shown, with their units. Tap a figure on the page to see where it comes from.</p>',
            '<h2 id="trace">Tracing a figure</h2><p>Tap or click any number on the site to see its source, period and the exact cell it was read from, or the calculation that produced it. The source line under each section leads to a record of every figure taken from that source. Without JavaScript, the source line still works. Mistakes we have fixed are listed on the <a href="corrections.html">corrections</a> page.</p>',
            '<h2 id="reproduce">How to reproduce the site</h2><p>With Python 3.10 or later: <code>make setup</code>, then <code>make build</code> and <code>make check</code>. The check re-opens every source file, re-reads each figure, and confirms that every number on every page matches its record.</p>',
            '<h2 id="sample-check">Checking a random sample against the publishers</h2><p>On 2 November 2026 we drew 50 figures at random from the site (40 from every figure shown and 10 from the headline pages), downloaded each source again from the publisher’s own website, and redid every calculation. All 50 matched. The check found one problem, now fixed: the two occupation sources linked to an address on Nomis that did not give the same data. The sample, method and results are <a href="https://github.com/jnyross/unpoliticalaf/tree/main/docs/accuracy-check">in the public repository</a>.</p>',
            '<h2 id="sources">Sources</h2>',
            f'<p>The site uses {len(sources)} official files. The <a href="sources.html">list of sources</a> groups them by publisher; each one links to its full record: '
            'publisher, place and people covered, publication and retrieval dates, the original link, the copy kept, its SHA-256 fingerprint and every figure used from it.</p>',
            # Old links to a source record on this page (methods.html#src-...) go to its new place.
            '<script>if(/^#src-/.test(location.hash))location.replace("sources.html"+location.hash)</script>']
    return page("methods.html", "Methods", "\n".join(body), "How Unpolitical chooses, calculates and checks every figure.")


def publisher_group(publisher):
    """The organisation a source is listed under: the publisher without notes in brackets."""
    name = publisher if publisher.endswith("(Northern Ireland)") else re.sub(r"\s*\(.*\)$", "", publisher).strip()
    return "Office for National Statistics" if name == "Nomis" else name


def group_id(name):
    return "pub-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def sources_page(sources, used_counts):
    """Every official file the site uses, grouped by publisher, each linking to its full record."""
    groups = {}
    for sid, s in sources.items():
        groups.setdefault(publisher_group(s["publisher"]), []).append((sid, s))
    order = sorted(groups, key=lambda g: (-len(groups[g]), g))
    body = ['<h1>Sources</h1>',
            f'<p>Every number on this site is copied or calculated from the {len(sources)} official files below. Each title opens the full record: who published it, '
            'the place and people it covers, when it was published and retrieved, the original link, the copy kept in the public repository, and every figure used from it. '
            'How figures are chosen and calculated is on the <a href="methods.html">methods</a> page.</p>']
    for g in order:
        items = []
        for sid, s in sorted(groups[g], key=lambda kv: kv[1]["title"]):
            n = used_counts.get(sid, 0)
            figs = f"{n:,} figure{'s' if n != 1 else ''} used" if n else "used for rates or quoted explanations"
            items.append(f'<li id="src-{esc(sid)}"><a href="figures/{esc(sid)}.html">{esc(s["title"])}</a> '
                         f'<span class="small">{esc(s["published"])}; {figs}</span></li>')
        # One closed list per publisher keeps the page short on a phone; a link to one source opens its list.
        body.append(f'<details class="srcgroup" id="{group_id(g)}"><summary>{esc(g)} ({len(items)})</summary><ul class="srclist">' + "".join(items) + "</ul></details>")
    body.append(f'<p class="small">{len(sources)} files from {len(order)} publishers. Every figure taken from them is also in the <a href="data/facts.json">downloadable data</a>.</p>')
    return page("sources.html", "Sources", "\n".join(body), "Every official file Unpolitical uses, grouped by publisher, with a full record for each.",
                folded=False, contents=False, scripts=OPEN_TARGET_JS)


# Opens the publisher list that holds a linked source (sources.html#src-...), for browsers
# that do not open a closed <details> on their own when its contents are the link target.
OPEN_TARGET_JS = """<script>
(function(){function go(){var h=location.hash.slice(1);if(!h)return;var e=document.getElementById(h);if(!e)return;
var d=e.closest('details');if(d&&!d.open){d.open=true;e.scrollIntoView()}}go();window.addEventListener('hashchange',go)})();
</script>"""
