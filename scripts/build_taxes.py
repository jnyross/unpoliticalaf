"""Static, no-JavaScript current tax and fiscal-balance page."""
import html
import json

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
    "corporation_tax": "Includes Bank Surcharge, Electricity Generator Levy, residential property developers tax and Pillar 2 taxes. Energy profits levy, petroleum revenue tax and bank levy stay in other taxes.",
    "other_taxes": "A calculated remainder after the named groups. It draws partly on a mixed source line that is not itemised. Arithmetic closure does not prove the classification of each tax or refund.",
    "non_tax": "A calculated difference: all receipts AG minus National Accounts taxes AH. It is not the mixed AF row relabelled as non-tax. Do not add AD, AE or AF again.",
}


def esc(value):
    return html.escape(str(value), quote=True)


def shown(node):
    value = node["v"]
    if value is None:
        return "not given"
    if node["unit"] == "percent GDP":
        return f"{value:,.1f}%"
    if node["unit"] == "GBP per 100 GBP receipts":
        return f"£{value:,.2f}"
    return f"£{value:,.3f}bn"


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


def bars(data, identities, labels):
    # A centred zero line preserves negative values. The table beside the chart
    # carries the same signed values and is the accessible alternative.
    extent = max((abs(data["nodes"][i]["v"]) for i in identities if data["nodes"][i]["v"] is not None), default=0)
    out = ['<div class="tax-bars" aria-hidden="true">']
    for identity, label in zip(identities, labels):
        node = data["nodes"][identity]
        value = node["v"]
        width = 0 if value is None or extent == 0 else abs(value) / extent * 50
        left = 50 - width if value is not None and value < 0 else 50
        out.append(f'<div class="tax-bar"><span>{esc(label)}</span>'
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
            bars(data, identities, [data["nodes"][i]["label"] for i in identities]) +
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
    group_ids = [f"group/{name}/{year}" for name in LABELS]
    rows = [[esc(label), f(f"group/{name}/{year}"), f(f"share/{name}/{year}")]
            for name, label in LABELS.items()]
    source = data["source"]
    outturn = [y for y in data["years"] if data["nodes"][f"cash/C/{y}"]["status"] != "forecast"]
    forecasts = [y for y in data["years"] if data["nodes"][f"cash/C/{y}"]["status"] == "forecast"]
    if not outturn or not forecasts:
        raise ValueError("Current tax presentation requires outturn and separately labelled forecast years")
    forecast_refs = {"Receipts (£bn)!C41", "Aggregates (£bn)!C95", "Aggregates (per cent of GDP)!C92"}
    notes = "".join(f'<dt><code>{esc(ref)}</code></dt><dd class="name"' +
                    (f' data-tax-forecast="source-note" data-tax-note-ref="{esc(ref)}"' if ref in forecast_refs else "") +
                    f'>{esc(text)}</dd>' for ref, text in data["notes"].items())
    body = f"""<header data-pid="tax-header">
<h1>Taxes, receipts and borrowing</h1>
<p class="lead">In {esc(year)}, the UK public sector received {f(f"component/AG/{year}")}.
This is the latest outturn in these tables. “bn” means billion.
The public finance financial year runs from April to March.</p>
<p>Receipts are not all tax. National Accounts taxes were {f(f"component/AH/{year}")}.
Receipts outside those taxes were {f(f"group/non_tax/{year}")}.</p>
<p>On the same OBR basis, spending was {f(f"cash/D/{year}")}, borrowing was {f(f"cash/O/{year}")},
and debt at end March was {f(f"cash/X/{year}")}.</p>
<p class="small">Source: <cite>{esc(source["publisher"])}, {esc(source["publication"])}</cite>.
File date: {esc(source["published"])}; retrieved {esc(source["downloaded"])}.
The file date is its HTTP header date, not a verified release date.
Outturn can be revised. These data are consistent with the 22 September 2026 public finances bulletin.
No next release date is announced in the retained evidence.</p>
</header><main id="main">
<nav class="page-links" aria-label="On this page"><a href="#receipt-groups">Main taxes</a>
<a href="#balance">Borrowing and debt</a><a href="#tax-history">History and forecasts</a>
<a href="#tax-sources">Check the sources</a></nav>
<section id="receipt-groups" data-pid="receipt-groups"><h2>Where each £100 of receipts came from</h2>
<p>The whole is all current public receipts (source total AG).
The shares mean “of each £100 of all current public receipts”. They are not shares of tax.
These six groups form one partition. Do not add totals to their own parts.</p>
{bars(data, group_ids, list(LABELS.values()))}
{table(f"Six receipt groups, {year}: of each £100 of all current public receipts (AG)",
       ["Group", "Cash", "Of each £100 of receipts"], rows)}
<dl data-pid="receipt-group-limits">{"".join(f"<dt><strong>{esc(label)}</strong></dt><dd>{esc(CAVEATS[name])}</dd>" for name, label in LABELS.items())}</dl>
<p>The source rows below keep each part's sign. The formula multiplier shows whether to add or subtract it.</p>
{"".join(component_detail(data, name) for name in LABELS)}
</section>
<section id="balance" data-pid="fiscal-balance"><h2>How receipts, spending and borrowing fit</h2>
<p>Using matching OBR <cite>Aggregates (£bn)</cite> rows:
spending {f(f"cash/D/{year}")} minus receipts {f(f"cash/C/{year}")}
equals {f(f"balance/{year}")}. The source's borrowing row is {f(f"cash/O/{year}")}.
Borrowing is not tax or receipts. It is the annual gap on this accrual basis.</p>
<p class="note">The <a href="index.html">spending page</a> uses PESA.
That is a different vintage and presentation. Its spending total is not the OBR total used in this balance.
Do not subtract receipts here from PESA spending.</p>
<p>Debt is a stock at end March. Borrowing is a flow over a year.
Changes in debt need not equal borrowing.
Published debt is {f(f"cash/X/{year}")}, or {f(f"gdp/X/{year}")} of GDP.
Debt uses March-centred GDP, not annual GDP. We retain the published share;
we do not replace it with a ratio worked out from the stock.</p></section>
<section id="tax-history" data-pid="tax-history"><h2>Annual history from {esc(data["years"][0])}</h2>
<p>These are the current OBR series. Cash is in £bn; GDP columns are published shares of the economy.
No inflation-adjusted tax view has been verified. A GDP share is not real spending.
It can rise if GDP falls. Missing values say “not given”; they are not zero.</p>
<p>Receipts: aggregate C, public sector current receipts. Spending: D, total managed expenditure.
Borrowing: O, public sector net borrowing. Debt: X, public sector net debt.
Each cash and GDP series uses its own year row and source cell.
Receipts, spending and borrowing use annual accruals and financial-year GDP.
Debt is an end-March cash stock with March-centred GDP.</p>
{history(data, outturn, "Current OBR annual outturn: cash (£bn) and published GDP shares (%)")}
<details data-pid="tax-forecasts"><summary>Forecasts: {esc(forecasts[0])} to {esc(forecasts[-1])}</summary>
<p data-tax-forecast="outlook">These years are forecasts, not observed facts. They use the October 2026 OBR outlook.
Outturn and forecasts are separate. Source notes for each table are below.</p>
{history(data, forecasts, "October 2026 OBR forecasts: cash (£bn) and published GDP shares (%)", forecast=True)}</details>
</section>
<section id="who-pays" data-pid="tax-incidence"><h2>Does this show who pays?</h2>
<p>These tables show collections by tax type. They do not show payer groups or who bears the cost.
Employers can send PAYE to HMRC. Businesses remit VAT.
The body that sends the money is not always the person who carries the economic cost.
These sources give no incidence percentages. Who-pays evidence will come separately.</p></section>
<section id="tax-sources" data-pid="tax-sources"><h2>Check a tax figure</h2>
<p><a href="data/taxes.json">Download the selected tax and fiscal data (JSON)</a>.
Each value names its year, exact cells, ordered formula, unit, status and source version.
The download holds current tables from this workbook, with history from {esc(data["years"][0])}.
It does not splice in the older historical workbook.</p>
<p><a href="{esc(source["page"])}">OBR source page</a> ·
<a href="{esc(source["url"])}">Download the official OBR workbook</a> ·
<a href="methods.html#tax-methods">Tax methods and limits</a></p>
<p class="small">Source SHA-256: <code>{esc(source["sha256"])}</code>.
The source metadata and formula are also on each figure as data attributes.
Open the source rows above or use this download with the workbook. Values themselves are not keyboard controls.</p>
<details><summary>Read the original current-table source notes</summary><dl>{notes}</dl></details>
</section></main>"""
    return page("Taxes, receipts and borrowing | UnpoliticalAF", body)
