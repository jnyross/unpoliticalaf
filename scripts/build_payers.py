"""Framework-free payer page. render(data, page_callback) returns HTML only.

The callback has the existing build_site.page(title, body) signature. The
controller owns file publication, shared navigation, CSS and output allowlists.
"""
from html import escape
from build_basics import payer_basics


def esc(value):
    return escape(str(value), quote=True)


STYLE = """<style>
.payers{overflow-wrap:anywhere}.payers section{margin-block:2rem}
.payers .payer-scroll{max-width:100%;overflow-x:auto}
.payers table{width:100%;min-width:0;table-layout:auto}
.payers .payer-scroll[aria-labelledby="hmrc-table"] table,
.payers .payer-scroll[aria-labelledby="ons-expenditure-table"] table{width:100%;min-width:0;table-layout:auto}
.payers .payer-scroll[aria-labelledby="ons-income-table"] table{min-width:34rem}
.payers caption{white-space:normal;text-align:left;overflow-wrap:anywhere}
.payers th,.payers td{padding:.6rem;vertical-align:top;white-space:normal;overflow-wrap:anywhere}
.payers .payer-note{background:#f3f4f6;padding:1rem;border-radius:8px}
.payers nav{display:flex;flex-wrap:wrap;gap:.4rem 1rem}
.payers a,.payers summary{min-height:44px;padding-block:10px}
.payers nav a,.payers .source-links a{display:inline-block}
.payers summary{cursor:pointer}.payers :focus-visible{outline:3px solid #1f2937;outline-offset:3px}
.payer-chart{display:grid;gap:.6rem}.payer-chart p{margin:0}
.payer-bar-heading{display:flex;justify-content:space-between;gap:.75rem;align-items:baseline}
.payer-bar-value{white-space:nowrap;font-weight:600;flex-shrink:0}
.payer-track{display:block;background:#f3f4f6;height:16px;width:100%}
.payer-fill{display:block;height:100%;background:#4b5563}
.payer-source-cell{margin-block:.5rem}.payer-source-cell code{overflow-wrap:anywhere}
</style>"""


def figure(entry):
    attributes = {"value": str(entry["value"]), "data-payer-id": entry["id"],
                  "data-ref": f'{entry["sheet"]}!{entry["cell"]}',
                  "data-source-sha256": entry["source_sha256"],
                  "data-period": entry["period"], "data-status": entry["status"],
                  "data-denominator": entry["denominator"], "data-unit": entry["unit"],
                  "data-population": entry["population"], "data-ranking": entry["ranking"],
                  "data-group": entry["group"], "data-measure": entry["measure"],
                  "data-formula": "published source cell"}
    attrs = " ".join(f'{key}="{esc(value)}"' for key, value in attributes.items())
    return f'<data {attrs}>{entry["value"]:.1f}%</data>'


def bars(entries, label):
    # Each independent bar starts at zero. HMRC is not an additive chart.
    return (f'<div class="payer-chart" aria-hidden="true" data-chart-denominator="{esc(label)}">'
            '<p>Each bar runs from 0% to 100%.</p>' + "".join(
                f'<div><span class="payer-bar-heading"><span>{esc(v["group"])}</span>'
                f'<span class="payer-bar-value" data-payer-bar-label="{esc(v["id"])}">{v["value"]:.1f}%</span>'
                '</span><span class="payer-track">'
                f'<span class="payer-fill" data-payer-bar="{esc(v["id"])}" style="width:{v["value"]}%"></span>'
                '</span></div>' for v in entries) + '</div>')


def table(caption, heads, rows, table_id):
    return (f'<div class="payer-scroll" role="region" aria-labelledby="{table_id}" tabindex="0">'
            f'<table><caption id="{table_id}">{esc(caption)}</caption><thead><tr>' +
            "".join(f'<th scope="col">{esc(h)}</th>' for h in heads) + '</tr></thead><tbody>' +
            "".join('<tr><th scope="row">' + esc(row[0]) + '</th>' +
                    "".join('<td>' + figure(v) + '</td>' for v in row[1:]) + '</tr>' for row in rows) +
            '</tbody></table></div>')


def source_details(data, sid):
    source = data["sources"][sid]
    records = [v for v in data["values"] if v["source_id"] == sid]
    cells = "".join(f'<li>{esc(v["group"])}: {esc(v["measure"])} — '
                    f'<code>{esc(v["sheet"])}!{esc(v["cell"])}</code>. '
                    f'Denominator: {esc(v["denominator"])}.</li>' for v in records)
    notes = "".join(f'<p class="payer-source-cell"><code>{esc(c["sheet"])}!{esc(c["cell"])}</code>: '
                    f'{esc(c["text"] if c["text"] is not None else c["value"])}</p>'
                    for c in data["source_cells"].values()
                    if c["source_id"] == sid and (c["sheet"] in {"Notes", "Cover sheet"} or
                       (c["sheet"] == "Contents" and c["cell"] in {"A4", "A5"}) or
                       (c["sheet"] == "Table 8" and c["cell"] == "A2")))
    return f'''<details id="{sid}-sources"><summary>Source cells and notes: {esc(source['publisher'])}</summary>
<p>{esc(source['publication'])}; published {esc(source['published'])}.
Unit: %. Geography: UK. Values use the published cells, not sums of rounded parts.</p>
<p><a data-payer-source="{sid}" href="{esc(source['url'])}">Download the original workbook</a></p>
<p>Source SHA-256: <code>{esc(source['sha256'])}</code></p><ul>{cells}</ul>{notes}</details>'''


def render(data, page_callback):
    """Render validated data without I/O. Always expose the semantic tables."""
    entries = {v["id"]: v for v in data["values"]}
    hmrc = [entries["hmrc-" + key] for key in ("bottom50", "top10", "top1")]
    ons_rows = [[entries[f"ons-{index}-direct"]["group"]] +
                [entries[f"ons-{index}-{measure}"] for measure in ("direct", "indirect", "combined")]
                for index in range(1, 6)]
    alt_rows = [[entries[f"ons-{index}-indirect"]["group"], entries[f"ons-{index}-expenditure"]]
                for index in range(1, 6)]
    source_links = "".join(f'<li><a href="{esc(s["url"])}">{esc(s["publication"])}</a> '
                           f'({esc(s["published"])})</li>' for s in data["sources"].values())
    hsrc, osrc = data["sources"]["hmrc"], data["sources"]["ons"]
    body = f'''{STYLE}<header><h1>Who pays tax?</h1>
<p class="lead">Two official views answer different questions. Do not join them into one tax bill.</p></header>
<main id="main" class="payers">
<section id="income-tax"><h2>Who owed Income Tax in 2023/24?</h2>
<p>Share of Income Tax due for tax year 2023 to 2024, estimated outturn. HMRC published these estimates on 15 July 2026.
They cover UK people with a positive Income Tax bill. People with no Income Tax bill are excluded.</p>
<p>HMRC ranks people by income assessable for tax, before deductions and allowances.
This is not a rank of wealth or all income.</p>
<p class="payer-note" id="overlap">The top 1% is part of the top 10%. The bottom 50% and top 10% do not overlap.
These groups refer to taxpayers with a positive Income Tax bill, not all adults.
Do not add their shares. Tax due is not cash collected. This is Income Tax only, not all UK taxes.</p>
{bars(hmrc, 'Total Income Tax liabilities')}
{table('HMRC: shares of total Income Tax liabilities, 2023/24 estimated outturn', ['Income group', 'Share of Income Tax due'], [[v['group'], v] for v in hmrc], 'hmrc-table')}
<p class="source-links" id="hmrc-source-note">Source: <a data-payer-source="hmrc" href="{esc(hsrc['url'])}">HMRC Table 2.4 (ODS)</a>.
The denominator is total Income Tax liabilities.</p></section>
<section id="household-taxes"><h2>How do taxes compare with household income?</h2>
<p>ONS estimates for 2023/24, the financial year ending 2024. Published 25 September 2025.
These are completed-year survey/model estimates, not a forecast. They cover UK people in private households.</p>
<p>ONS ranks people by equivalised household disposable income.
This means household income after direct taxes, adjusted for household size and needs.
It makes five groups with about equal numbers of people, not households.
These are not the HMRC taxpayer groups.</p>
<p>Gross income includes cash benefits. Disposable income is gross income after direct taxes.
The table shows taxes as a percentage of gross household income for each group.</p>
<h3>Direct and indirect taxes counted in this ONS analysis</h3>
<div class="payer-note" id="bottom-group"><h3>Why the bottom group needs care</h3>
<p>Deferred lump-sum tax payments can leave people with high gross income but low disposable income.
They can enter the bottom group. These payments need not reflect a typical year's tax bill.</p>
<p>Spending can exceed current income through savings or borrowing. Temporary low income, sampling and measurement issues also matter.
A high indirect-tax share of income is not a tax rate on purchases or a lifetime tax burden.
Compare the spending measure below too.</p></div>
<p>The bars show the published combined share of gross household income. The table gives both parts as well.</p>
{bars([entries[f'ons-{i}-combined'] for i in range(1, 6)], 'Gross household income')}
{table('ONS: percentages of gross household income, 2023/24 completed-year estimates', ['Income group', 'Direct / gross income', 'Indirect / gross income', 'Combined / gross income'], ons_rows, 'ons-income-table')}
<p>Combined values come from published Table 8 row 15. Rounded parts may not add to that total.</p>
<h3>How do indirect taxes compare with spending?</h3>
<p>The denominator here is household expenditure, not income. It gives another view of the same indirect taxes.</p>
{table('ONS: indirect taxes as a percentage of household expenditure, 2023/24 completed-year estimates', ['Income group', 'Indirect / expenditure'], alt_rows, 'ons-expenditure-table')}
<p>ONS makes expenditure consistent with disposable income (note 13). Neither measure is a rate on each purchase.</p>
<p class="source-links" id="ons-source-note">Source: <a data-payer-source="ons" href="{esc(osrc['url'])}">ONS reference tables (XLSX), Table 8</a>.
Current direct taxes include student-loan repayments. Corporation Tax is not allocated to households in this analysis.
This is not a measure of all UK taxes. Suppressed components stay suppressed; we do not fill them in.</p>
</section>
<section id="burden"><h2>Who sends the tax, and who bears its cost?</h2>
{payer_basics()}
<p>ONS assigns final and intermediate indirect taxes fully to consumers in this model.
This includes employer National Insurance. Employee and self-employed National Insurance are direct taxes.</p>
<p>Actual costs can fall on producers, workers, buyers and others in varying shares.
Full consumer allocation is an assumption, not a settled fact. A combined National Insurance receipts total
must not be mapped wholly to either ONS group.</p>
<p>The linked technical report covers FYE 2019. It was published on 25 June 2020.
Sections 7 and 10 explain these assumptions and limits. The QMI is dated 15 June 2018.
These are the latest linked reports we found in the sources we kept.
They are older reports. Some details may have changed. Current workbook notes take priority.</p>
<p>HMRC and ONS use different populations and tax measures. Do not combine them into a top-1% all-tax burden,
an average across the panels, or a match to tax receipts.</p></section>
<section id="payer-sources"><h2>Where can I check the numbers?</h2>
<p><a href="data/payers.json">Download the selected payer data (JSON)</a>.
It keeps the exact source cells, hashes, labels, units and notes. No next release date is recorded here.</p>
<ul class="source-links">{source_links}</ul>
{source_details(data, 'hmrc')}{source_details(data, 'ons')}
<p>Contains public sector information licensed under the
<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
</section></main>'''
    return page_callback("Who pays tax? | UnpoliticalAF", body)
