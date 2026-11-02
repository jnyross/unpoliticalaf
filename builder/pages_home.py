"""Home page and the sources and methods page."""
from .html import page, esc, table


def home_page(facts, d, num, sources):
    sp = d["spending"]["latest"]
    y = "2025-26"
    body = [f'''<h1>Public money and everyday life in the UK, in plain numbers</h1>
<p class="lede">Clear answers from official statistics. Every figure shows where it comes from, what period it covers and what it can't tell you.</p>
<div class="cards">
<a class="card" href="spending.html"><h2>Where does public money go?</h2>
<p>{num(f"spend.cash.tme.{sp}", "bn")} was spent in {esc(sp)}. Social protection, including pensions, was the largest share: {num(d["spending"]["per100"]["social"], "per100")} of every £100 spent on services.</p></a>
<a class="card" href="taxes.html"><h2>Which taxes raise the money?</h2>
<p>Taxes raised {num(f"rec.taxes.{y}", "bn")} in {y}. Income Tax, National Insurance and VAT raised {num(f"rec.big3share.{y}", "pct0")} of it. Borrowing covered another {num(f"agg.psnb.{y}", "bn")}.</p></a>
<a class="card" href="who-pays.html"><h2>Who pays?</h2>
<p>The top 1% of Income Tax payers paid {num("hmrc.share.top1.2023 to 2024", "pct")} of all Income Tax in 2023 to 2024. Every household pays taxes on spending, such as VAT.</p></a>
<a class="card" href="household-tax.html"><h2>How much household income goes on tax?</h2>
<p>On average, {num("etb.t8.gross.all.all", "pct")} of gross household income in 2023/24. That is an average across households, not anyone's tax rate.</p></a>
</div>
<h2>Everyday life, year by year</h2>
<p>See how work, pay after inflation, housing, holidays at home and abroad, and school class sizes have changed since 2008. Pick a year or compare two.</p>
<p><a class="button" href="life/index.html">Explore everyday life</a></p>
<h2>How to read this site</h2>
<ul>
<li>Every number comes from an official UK source. Select “Source” under a figure to see exactly where.</li>
<li>Gaps stay gaps. When a year is missing or a definition changed, we say so and don't fill it in.</li>
<li>Anything invented to explain a rule, such as a worked example, is marked “Illustration, not a statistic”.</li>
<li>Figures show what changed, not why it changed.</li>
</ul>''']
    return page("index.html", "Unpolitical", "\n".join(body), "Independent, plain-English answers about UK public spending, taxes and everyday life, from official statistics.")


def methods_page(facts, sources, used_counts):
    body = ['<h1>Sources and methods</h1>',
            '<p>Every number on this site is copied or calculated from the official files listed below. The files are kept in the site’s public code repository, and the build stops if any file changes without its record being updated.</p>',
            '<h2 id="principles">Principles</h2><ul>'
            '<li><strong>Official sources only.</strong> Figures come from UK government departments, the Office for National Statistics and the Office for Budget Responsibility.</li>'
            '<li><strong>No invented continuity.</strong> Missing years are shown as missing. Where a definition changes, the series is broken and no change is calculated across the break.</li>'
            '<li><strong>No invented households presented as fact.</strong> Where a made-up person helps explain a rule, it is labelled “Illustration, not a statistic” and kept apart from the official figures.</li>'
            '<li><strong>Change is not cause.</strong> The site shows what changed. It does not say why.</li>'
            '<li><strong>Neutral language.</strong> We describe figures; we don’t judge them.</li></ul>',
            '<h2 id="calculations">Calculations</h2><ul>'
            '<li><strong>Per £100 of spending</strong>: spending on a function ÷ total spending on services × 100 (HM Treasury PESA Table 4.2). Interest on debt is shown as a share of total managed expenditure.</li>'
            '<li><strong>Real terms (spending)</strong>: HM Treasury’s own 2025-26 prices (PESA Table 4.3).</li>'
            '<li><strong>Pay after inflation</strong>: cash pay × (CPIH in April 2025 ÷ CPIH in April of that year), using ONS series L522.</li>'
            '<li><strong>Changes in percentages</strong> are shown in percentage points; changes in money and counts as a percentage of the earlier figure.</li>'
            '<li><strong>Non-tax receipts</strong>: total current receipts minus taxes (OBR).</li>'
            '<li><strong>Families with children renting privately</strong>: private-renting families ÷ all families, adding couples, single lone parents and previously married lone parents (EHS FT1241).</li>'
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
