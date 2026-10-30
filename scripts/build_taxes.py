"""Static, no-JavaScript current tax and fiscal-balance page."""
import html
import json
import re
from decimal import Decimal, ROUND_HALF_UP

LABELS = {
    "income_tax": "Income tax",
    "nic": "National Insurance contributions",
    "vat": "VAT including refunds (net VAT plus refunds)",
    "corporation_tax": "Corporation tax and related charges",
    "other_taxes": "Other National Accounts taxes",
    "non_tax": "Receipts outside National Accounts taxes",
}
PARTS = {
    "income_tax": ("Q", "R", "S"), "nic": ("AB",), "vat": ("C", "D"),
    "corporation_tax": ("U", "V"), "other_taxes": ("AH", "Q", "R", "S", "AB", "C", "D", "U", "V"), "non_tax": ("AG", "AH"),
}
CAVEATS = {
    "income_tax": "PAYE, self-assessed and other income tax are added with their source signs. Other income tax can be negative.",
    "nic": "National Insurance is shown as its own source series.",
    "vat": "This gross grouping is a source-based presentation, not household VAT burden. The notes do not explicitly establish how refunds are classified within National Accounts taxes. The net VAT and refund rows are separate below.",
    "corporation_tax": "Adds the source's onshore and offshore corporation tax rows. The onshore label includes Bank Surcharge and the Electricity Generator Levy (EGL). OBR note 3 also includes residential property developers tax and Pillar 2 taxes. Petroleum revenue tax, energy profits levy and bank levy stay in other taxes.",
    "other_taxes": "A calculated remainder after the named groups. It draws partly on a mixed source line that is not itemised. Arithmetic closure does not prove the classification of each tax or refund.",
    "non_tax": "A calculated difference: all receipts minus National Accounts taxes. It is not the mixed source row relabelled as non-tax. Do not add the source's interest, dividend or operating surplus rows again.",
}


def esc(value):
    return html.escape(str(value), quote=True)


def shown(node):
    value = node["v"]
    if value is None:
        return "not given"
    sign = "−" if value < 0 else ""
    if node["unit"] == "percent GDP":
        return f"{sign}{abs(value):,.1f}%"
    if node["unit"] == "GBP per 100 GBP receipts":
        return f"{sign}£{abs(value):,.2f}"
    rounded = Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return f"{sign}£{abs(rounded):,.1f}bn"


def refs(data, node):
    result = []
    for operand in node["operands"]:
        if "ref" in operand:
            result.append(operand["ref"])
        else:
            result.extend(refs(data, data["nodes"][operand["id"]]))
    return result


def figure(data, identity):
    node = data["nodes"][identity]
    attrs = {
        "value": "" if node["v"] is None else repr(node["v"]),
        "data-tax-id": identity, "data-ref": " ".join(refs(data, node)),
        "data-formula": node["formula"], "data-unit": node["unit"],
        "data-year": node["year"], "data-status": node["status"],
        "data-operands": json.dumps(node["operands"], ensure_ascii=False, separators=(",", ":")),
        "data-source-version": data["source"]["sha256"],
    }
    return "<data " + " ".join(f'{key}="{esc(value)}"' for key, value in attrs.items()) + ">" + esc(shown(node)) + "</data>"


def table(caption, headings, rows, forecast=False):
    marker = ' data-tax-forecast="caption"' if forecast else ""
    return (f'<div class="tax-scroll" role="region" aria-label="{esc(caption)}" tabindex="0">'
            f'<table><caption{marker}>{esc(caption)}</caption><thead><tr>' +
            "".join(f'<th scope="col">{esc(h)}</th>' for h in headings) +
            "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(f'<th scope="row">{cell}</th>' if i == 0 else f"<td>{cell}</td>"
                                    for i, cell in enumerate(row)) + "</tr>" for row in rows) +
            "</tbody></table></div>")


def chart_label(label):
    # Footnote markers belong to exact source labels in the table, not the chart.
    return re.sub(r"(?<=\D)[123]$", "", label)


def bars(data, identities, labels, receipts=False):
    values = [data["nodes"][i]["v"] for i in identities]
    signed = any(value is not None and value < 0 for value in values)
    if receipts and signed:
        raise ValueError("Receipt partition chart requires nonnegative shares")
    scale = "receipts-100" if receipts else "signed" if signed else "positive"
    extent = 100 if receipts else max((abs(v) for v in values if v is not None), default=0)
    baseline = 50 if signed else 0
    span = 50 if signed else 100
    out = [f'<div class="tax-bars" data-tax-scale="{scale}" aria-hidden="true">']
    for identity, label in zip(identities, labels):
        value = data["nodes"][identity]["v"]
        width = 0 if value is None or extent == 0 else abs(value) / extent * span
        left = baseline - width if value is not None and value < 0 else baseline
        out.append(f'<div class="tax-bar"><span>{esc(chart_label(label))}</span>'
                   f'<span class="tax-track"><span class="tax-fill" style="left:{left:.4f}%;width:{width:.4f}%"></span></span>'
                   f'<span>{figure(data, identity)}</span></div>')
    return "".join(out) + "</div>"


def component_detail(data, name):
    year = data["latest_year"]
    columns = PARTS[name]
    identities = [f"component/{c}/{year}" for c in columns]
    rows = []
    group = data["nodes"][f"group/{name}/{year}"]
    for identity in identities:
        node = data["nodes"][identity]
        coefficient = next(o["coefficient"] for o in group["operands"] if o["ref"] == node["ref"])
        rows.append([esc(node["label"]), figure(data, identity), f"{coefficient:+g}",
                     f'<code>{esc(node["ref"])}</code>',
                     esc(node["status"])])
    formula = " ".join(f'{o["coefficient"]:+g} × {o["ref"]}' for o in group["operands"])
    return (f'<details data-pid="tax-source-{name}"><summary>Source rows: {esc(LABELS[name])}</summary>'
            f'<p class="small">Ordered formula: <code>{esc(formula)}</code>. '
            'Unit: GBP billion. Annual accruals; UK public sector. Source version and signed operands are also on each value and in the download.</p>' +
            ("" if name in ("other_taxes", "non_tax") else
             bars(data, identities, [data["nodes"][i]["label"] for i in identities])) +
            table(f"Component source rows for {LABELS[name]}, {year}",
                  ["Source series", "Cash (source sign)", "Formula multiplier", "Source cell", "Status"], rows) + "</details>")


def history(data, years, label, forecast=False):
    rows = []
    for year in years:
        values = [esc(year)]
        for column in ("C", "D", "O", "X"):
            values += [figure(data, f"cash/{column}/{year}"), figure(data, f"gdp/{column}/{year}")]
        values.append(esc(data["nodes"][f"cash/C/{year}"]["status"]))
        rows.append(values)
    return table(label, ["April–March year", "Receipts cash", "Receipts GDP", "Spending cash", "Spending GDP",
                         "Borrowing cash", "Borrowing GDP", "End-March debt cash", "Debt GDP", "Status"], rows, forecast=forecast)


def render(data, page):
    year = data["latest_year"]
    f = lambda identity: figure(data, identity)
    share_ids = [f"share/{name}/{year}" for name in LABELS]
    rows = [[esc(label), f(f"group/{name}/{year}"), f(f"share/{name}/{year}")]
            for name, label in LABELS.items()]
    source = data["source"]
    outturn = [y for y in data["years"] if data["nodes"][f"cash/C/{y}"]["status"] != "forecast"]
    forecasts = [y for y in data["years"] if data["nodes"][f"cash/C/{y}"]["status"] == "forecast"]
    if not outturn or not forecasts:
        raise ValueError("Current tax presentation requires outturn and separately labelled forecast years")
    forecast_refs = {"Receipts (£bn)!C41", "Aggregates (£bn)!C95", "Aggregates (per cent of GDP)!C92"}
    notes = "".join(f'<dt>OBR note (original wording): <code>{esc(ref)}</code></dt>'
                    f'<dd class="name" data-tax-note-ref="{esc(ref)}"' +
                    (' data-tax-forecast="source-note"' if ref in forecast_refs else "") +
                    f'>{esc(text)}</dd>' for ref, text in data["notes"].items())
    explanations = "".join(
        f'<dt><strong>{esc(label)}</strong></dt><dd data-tax-explanation="{name}">{esc(CAVEATS[name])}</dd>'
        for name, label in LABELS.items())
    source_labels = "".join(
        f'<dt><code>{esc(ref)}</code></dt><dd class="name" data-tax-label-ref="{esc(ref)}">{esc(label)}</dd>'
        for ref, label in data["source_labels"].items())
    body = f"""<header data-pid="tax-header">
<h1>Taxes and other receipts</h1>
<p class="lead">In {esc(year)}, the UK public sector received {f(f"component/AG/{year}")} in taxes and other receipts.
This is the latest outturn in these tables. “bn” means billion.
The financial year runs from April to March. Cash totals are rounded to one decimal place.</p>
<p>Not all receipts are tax. Taxes on the source's National Accounts basis were {f(f"component/AH/{year}")}.
Other receipts were {f(f"group/non_tax/{year}")}.</p>
<p>On the same OBR basis, spending was {f(f"cash/D/{year}")}, borrowing was {f(f"cash/O/{year}")},
and debt at end March was {f(f"cash/X/{year}")}.</p>
<p class="small">Source: <cite>{esc(source["publisher"])}, {esc(source["publication"])}</cite>.
No next release date is announced in the retained evidence.</p>
<p class="small" data-pid="tax-outturn-note">Outturn can be revised. The outturn figures are consistent with the public finances bulletin released on 22 September 2026.</p>
<p class="small">That bulletin date is not the later forecast vintage. Forecast years are shown separately below.</p>
</header><main id="main">
<nav class="page-links" aria-label="On this page"><a href="#receipt-groups">Main taxes</a>
<a href="#balance">Borrowing and debt</a><a href="#tax-history">History and forecasts</a>
<a href="#tax-sources">Check the sources</a></nav>
<section id="receipt-groups" data-pid="receipt-groups"><h2>Where each £100 of receipts came from</h2>
<p data-pid="receipt-denominator">The whole is all current public receipts: taxes plus other receipts.
The shares mean “of each £100 of all current public receipts”. They are not shares of tax.
The six groups add up to the whole. Do not add totals to their own parts.</p>
{bars(data, share_ids, list(LABELS.values()), receipts=True)}
{table(f"Six receipt groups, {year}: of each £100 of all current public receipts",
       ["Group", "Cash", "Of each £100 of receipts"], rows)}
<h3>Our explanation</h3>
<dl data-pid="receipt-group-limits">{explanations}</dl>
<p><a href="#tax-sources">Check the sources</a> for each group's rows and signed formula.</p>
</section>
<section id="balance" data-pid="fiscal-balance"><h2>How receipts, spending and borrowing fit</h2>
<p>Using matching OBR <cite>Aggregates (£bn)</cite> rows:
spending {f(f"cash/D/{year}")} minus receipts {f(f"cash/C/{year}")}
equals {f(f"balance/{year}")}. The source's borrowing row is {f(f"cash/O/{year}")}.
Borrowing is not tax or receipts. It is the annual gap on this accrual basis.
Negative borrowing means receipts were greater than spending.</p>
<p class="note">The <a href="index.html">spending page</a> uses PESA.
That is a different vintage and presentation. Its spending total is not the OBR total used in this balance.
Do not subtract receipts here from PESA spending.</p>
<p>Debt is a stock at end March. Borrowing is a flow over a year.
Changes in debt need not equal borrowing.
Published debt is {f(f"cash/X/{year}")}, or {f(f"gdp/X/{year}")} of GDP.
Debt uses March-centred GDP, not annual GDP. We retain the published share;
we do not replace it with a ratio worked out from the stock.</p></section>
<section id="tax-history" data-pid="tax-history"><h2>Total receipts, spending, borrowing and debt since {esc(data["years"][0])}</h2>
<p data-pid="tax-history-scope">Tax-type history is not shown. These are histories of total receipts, spending, borrowing and debt.</p>
<p>These are the current OBR series. Cash is in £bn; GDP columns are published shares of the economy.
No inflation-adjusted tax view has been verified. A GDP share is not real spending.
It can rise if GDP falls. Missing values say “not given”; they are not zero.</p>
<p>Receipts, spending and borrowing use annual accruals and financial-year GDP.
Debt is an end-March cash stock with March-centred GDP.</p>
{history(data, outturn, "Current OBR annual outturn: cash (£bn) and published GDP shares (%)")}
<details data-pid="tax-forecasts"><summary>Forecasts: {esc(forecasts[0])} to {esc(forecasts[-1])}</summary>
<p data-tax-forecast="outlook">These years are forecasts, not observed facts. They use the October 2026 OBR outlook.
Outturn and forecasts are separate. Source notes for each table are below.</p>
{history(data, forecasts, "October 2026 OBR forecasts: cash (£bn) and published GDP shares (%)", forecast=True)}</details>
</section>
<section id="who-pays" data-pid="tax-incidence"><h2>Does this show who pays?</h2>
<p data-pid="who-pays-limit">This page does not show who pays.
These tables show receipts by tax type. They do not show how payments are split between people,
or who ultimately bears the cost. They give no percentages for who bears that cost.</p></section>
<section id="tax-sources" data-pid="tax-sources"><h2>Check the sources</h2>
<p>The source rows keep each part's sign. The formula multiplier shows whether to add or subtract it.
The two remainder groups have signed formula tables, not component bars.</p>
{"".join(component_detail(data, name) for name in LABELS)}
<details data-pid="tax-series-codes"><summary>Source totals, codes and scope labels</summary>
<p>The share denominator is receipts total AG, not National Accounts taxes AH.
In the aggregate tables, receipts are C, spending D, borrowing O and debt X.
Each cash and GDP series uses its own year row and source cell.</p>
<dl>{source_labels}</dl></details>
<p><a href="data/taxes.json">Download the selected tax and fiscal data (JSON)</a>.
Each value names its year, exact cells, ordered formula, unit, status and source version.
The download holds current tables from this workbook, with history from {esc(data["years"][0])}.
It does not splice in the older historical workbook.</p>
<p><a href="{esc(source["page"])}">OBR source page</a> ·
<a href="{esc(source["url"])}">Download the official OBR workbook</a> ·
<a href="methods.html#tax-methods">Tax methods and limits</a></p>
<p class="small">File date: {esc(source["published"])}; retrieved {esc(source["downloaded"])}.
The file date is its HTTP header date, not a verified release date.</p>
<p class="small">Source SHA-256: <code>{esc(source["sha256"])}</code>.
The source metadata and formula are also on each figure as data attributes.
Open the source rows in this section or use this download with the workbook. Values themselves are not keyboard controls.</p>
<details><summary>Read the original current-table source notes</summary><dl>{notes}</dl></details>
</section></main>"""
    return page("Taxes, receipts and borrowing | UnpoliticalAF", body)
