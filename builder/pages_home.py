"""Home page and the sources and methods page."""
from .html import page, esc, table


def home_page(facts, d, num, sources):
    sp = d["spending"]["latest"]
    y = "2025-26"
    L = 2025
    body = [f'''<div class="hero"><h1>Public money and everyday life in the UK, in plain numbers</h1>
<p class="lede">Where public money goes, who pays for it, and how work, pay, housing, holidays and schools have changed. Every figure is an official statistic, and shows where it comes from and what it can't tell you.</p></div>
<h2 id="money">Public money: four questions</h2>
<div class="cards">
<a class="card" href="spending.html"><h3>Where does public money go?</h3>
<span class="big">{num(f"spend.cash.tme.{sp}", "bn")}</span>
<p>spent by the public sector in {esc(sp)}. The largest area was social protection, including pensions: {num(d["spending"]["per100"]["social"], "per100")} of every £100 spent on services.</p>
<span class="more">Spending by area and over time</span></a>
<a class="card" href="taxes.html"><h3>Which taxes raise the money?</h3>
<span class="big">{num(f"rec.taxes.{y}", "bn")}</span>
<p>raised in taxes in {y}. Income Tax, National Insurance and VAT raised {num(f"rec.big3share.{y}", "pct0")} of it. Borrowing covered another {num(f"agg.psnb.{y}", "bn")}.</p>
<span class="more">Taxes, other receipts and borrowing</span></a>
<a class="card" href="who-pays.html"><h3>Who pays?</h3>
<span class="big">{num("hmrc.share.top1.2023 to 2024", "pct")}</span>
<p>of all Income Tax was paid by the top 1% of Income Tax payers in 2023 to 2024. Every household also pays taxes on spending, such as VAT.</p>
<span class="more">Income Tax and all taxes, by group</span></a>
<a class="card" href="household-tax.html"><h3>How much household income goes on tax?</h3>
<span class="big">{num("etb.t8.gross.all.all", "pct")}</span>
<p>of gross household income, on average across everyone, in 2023/24. That is an average across households, not anyone's tax rate.</p>
<span class="more">Direct, indirect and combined taxes</span></a>
</div>
<h2 id="life">Everyday life, year by year</h2>
<p>Pick any year from 2008 to {L}, or compare two. Each topic shows the latest figure and what it covers.</p>
<div class="cards">
<a class="card" href="life/index.html#work"><h3>Work</h3><span class="big">{num(f"work.rate.{L}", "pct")}</span><p>of people aged 16 to 64 were in work, April to June {L}, UK.</p></a>
<a class="card" href="life/index.html#earnings"><h3>Earnings</h3><span class="big">{num(f"earn.ft.{L}", "pounds")}</span><p>a week before tax for the middle full-time employee, April {L}, UK.</p></a>
<a class="card" href="life/index.html#housing"><h3>Housing</h3><span class="big">{num("house.owners.2024", "pct0")}</span><p>of households in England owned their home, 2024-25.</p></a>
<a class="card" href="life/index.html#holidays"><h3>Holidays</h3><span class="big">{num(f"hol.world.holiday.{L}", "millions")}</span><p>holiday visits abroad by Great Britain residents in {L}.</p></a>
<a class="card" href="life/index.html#schools"><h3>Class sizes</h3><span class="big">{num(f"school.primary.{L}", "dp1")}</span><p>pupils in the average state primary school class in England, January {L}.</p></a>
<a class="card" href="life/compare/index.html"><h3>Compare two years</h3><p>See any two years from 2008 to {L} side by side, with what changed and where definitions changed.</p><span class="more">Choose two years</span></a>
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
    body = ['<h1>Sources and methods</h1>',
            '<p>Every number on this site is copied or calculated from the official files listed below. The files are kept in the site’s public code repository, and the build stops if any file changes without its record being updated.</p>',
            '<h2 id="principles">Principles</h2><ul>'
            '<li><strong>Official sources only.</strong> Figures come from UK government departments, the Office for National Statistics and the Office for Budget Responsibility.</li>'
            '<li><strong>No invented continuity.</strong> Missing years are shown as missing. Where a definition changes, the series is broken and no change is calculated across the break.</li>'
            '<li><strong>No invented households presented as fact.</strong> Where a made-up person helps explain a rule, it is labelled “Illustration, not a statistic” and kept apart from the official figures.</li>'
            '<li><strong>Change is not cause.</strong> The site shows what changed. It does not say why in its own words. Where an official body such as the Office for National Statistics or HM Revenue and Customs has published its own explanation, we quote it word for word, name who said it, and link to it. The check confirms that every quote still matches the publication.</li>'
            '<li><strong>Neutral language.</strong> We describe figures; we don’t judge them.</li></ul>',
            '<h2 id="calculations">Calculations</h2><ul>'
            '<li><strong>Per £100 of spending</strong>: spending on a function ÷ total spending on services × 100 (HM Treasury PESA Table 4.2). Interest on debt is shown as a share of total managed expenditure.</li>'
            '<li><strong>Real terms (spending)</strong>: HM Treasury’s own 2025-26 prices (PESA Table 4.3).</li>'
            '<li><strong>Pay after inflation</strong>: cash pay × (CPIH in April 2025 ÷ CPIH in April of that year), using ONS series L522.</li>'
            '<li><strong>Changes in percentages</strong> are shown in percentage points; changes in money and counts as a percentage of the earlier figure.</li>'
            '<li><strong>Non-tax receipts</strong>: total current receipts minus taxes (OBR).</li>'
            '<li><strong>Families with children renting privately</strong>: private-renting families ÷ all families, adding couples, single lone parents and previously married lone parents (EHS FT1241).</li>'
            '<li><strong>Housing costs after inflation</strong>: cash rent or mortgage payment × (average CPIH over the latest survey year ÷ average CPIH over that survey year). A survey year runs from April to the following March, so each average uses the twelve monthly CPIH values (ONS series L522) for those months.</li>'
            '<li><strong>Households with five or more rooms</strong>: the published percentages with five, six, seven, and eight or more rooms, added together (EHS FA1401).</li>'
            '<li><strong>Holiday share of visits</strong> and <strong>Europe share</strong>: holiday visits ÷ all visits, and holiday visits to Europe ÷ all holiday visits.</li>'
            '<li><strong>Holidays per 100 residents</strong>: holiday trips × 100 ÷ mid-year population (ONS UKPOP up to 2023 for trips abroad, GBPOP from 2024 and for trips within Great Britain). This is an average over everyone, including children and people who took no holiday.</li>'
            '<li><strong>Most visited countries</strong>: single countries ranked by visits in that year; groups such as “Rest of Europe” are left out.</li></ul>',
            '<h2 id="data">Every figure, machine-readable</h2>',
            f'<p><a href="data/facts.json">Download all {len(facts):,} figures as JSON</a>. Each has an id, value, unit, period, source id, the exact sheet and cell (or a description of the calculation and its inputs), and whether it is published outturn, a forecast, a projection or our calculation. Figures on each page are tagged with the same id.</p>',
            '<h2 id="reproduce">How to reproduce the site</h2><p>With Python 3.10 or later: <code>make setup</code>, then <code>make build</code> and <code>make check</code>. The check re-opens every source file, re-reads each figure, and confirms that every number on every page matches its record.</p>',
            '<h2 id="sources">Sources</h2>']
    for sid, s in sorted(sources.items(), key=lambda kv: (kv[1]["publisher"], kv[1]["title"])):
        n = used_counts.get(sid, 0)
        body.append(f'''<section class="source" id="src-{esc(sid)}"><h3>{esc(s["title"])}</h3>
<dl>
<dt>Publisher</dt><dd>{esc(s["publisher"])}</dd>
<dt>Where</dt><dd>{esc(s["geography"])}</dd>
<dt>Who or what</dt><dd>{esc(s["population"])}</dd>
<dt>Published</dt><dd>{esc(s["published"])}</dd>
<dt>Retrieved</dt><dd>{esc(s["retrieved"])}</dd>
<dt>Link</dt><dd><a href="{esc(s["page"])}">{esc(s["page"])}</a></dd>
<dt>File kept</dt><dd><code>{esc(s["file"])}</code></dd>
<dt>SHA-256</dt><dd><code class="hash">{esc(s["sha256"])}</code></dd>
<dt>Figures used</dt><dd>{n:,}</dd>
<dt>Licence</dt><dd>{esc(s["licence"])}</dd>
</dl></section>''')
    return page("methods.html", "Sources and methods", "\n".join(body), "Where every figure on Unpolitical comes from and how it is calculated.")
