"""Taxes by type since 1948-49, from the OBR's historical public finances database."""
from .html import FOLD, page, details_table, small_multiples, switch, change_bars, source_line, esc
from .pages_money import derive


# A few words on what a group covers, for the summary.
ABOUT = {"duties": ", on goods such as alcohol, tobacco and fuel", "nics": ", paid on earnings by workers and employers"}


def short(kv):
    return kv[1].split(" (")[0]


def tax_history_page(facts, d, num, sources):
    h = d["tax_mix_history"]
    years, groups = h["years"], h["groups"]
    first, last = years[0], years[-1]
    keys = [k for k, _ in groups]

    for k, _ in groups:
        derive(facts, f"thist.sharechange.{k}.{first}.{last}", facts[f"thist.share.{k}.{last}"].value - facts[f"thist.share.{k}.{first}"].value,
               "percentage points", f"{first} to {last}", "obrhist-receipts-shares",
               [f"thist.share.{k}.{last}", f"thist.share.{k}.{first}"], f"thist.share.{k}.{last} − thist.share.{k}.{first}")
    named = [kv for kv in groups if kv[0] != "other"]
    moves = sorted(named, key=lambda kv: facts[f"thist.sharechange.{kv[0]}.{first}.{last}"].value)
    fell, rose = moves[0], moves[-1]

    it = sorted(years, key=lambda y: facts[f"thist.share.income_tax.{y}"].value)
    lo, hi = it[0], it[-1]

    def s(k, y):
        return num(f"thist.share.{k}.{y}", "pct0")

    body = ["<h1>Which taxes raised the money since 1948?</h1>"]
    body.append(f'''<div class="answer"><p class="lede">Income Tax has raised roughly a quarter of all public sector receipts since {first}. National Insurance and VAT now raise a larger share, and duties on goods a smaller one.</p></div>''')
    marks = [(y, label) for y, label, _ in h["breaks"]]

    def chart(v):
        pre = {"share": "thist.share", "gdp": "thist.gdp"}[v]
        unit = {"share": "Per cent of all public sector receipts in each year", "gdp": "Per cent of GDP"}[v]
        breaks = [(years.index(y), t) for y, t in marks]
        ids = [[f"{pre}.{k}.{y}" for y in years] for k in keys]
        return small_multiples(f"Public receipts by type, {first} to {last}", [y[:4] for y in years],
                               [(n, [facts[i].value for i in row]) for (k, n), row in zip(groups, ids)],
                               unit + ". Axis years are financial years starting in April of the year shown. Source: OBR historical public finances database.",
                               "pct", ids=ids, num=num, breaks=breaks, ymin=0, point_labels=years)

    body.append(switch("Show each group as", [
        ("Share of all receipts", "Each group's share of everything the public sector received that year. A smaller share does not have to mean less money: other receipts may have grown faster.", chart("share")),
        ("Share of GDP", "Each group as a share of GDP, the value of everything produced in the UK that year, as published by the OBR.", chart("gdp")),
    ]))
    body.append("<p class='small'>Seven groups, one panel each, on the same scale. Amber dashed lines mark where a tax was replaced or the way receipts are counted changed:</p>")
    body.append("<ul class='small'>" + "".join(f"<li><strong>{y}:</strong> {esc(text)}</li>" for y, _, text in h["breaks"]) + "</ul>")
    body.append(f"<h2 id='mix'>What changed between {first} and {last}</h2>")
    body.append(f'''<p>Income Tax raised {s("income_tax", first)} of all receipts in {first} and {s("income_tax", last)} in {last}. Its share was lowest in {lo} ({s("income_tax", lo)}) and highest in {hi} ({s("income_tax", hi)}).
The largest fall was in <strong>{esc(short(fell))}</strong>{ABOUT.get(fell[0], "")}: {s(fell[0], first)} of all receipts in {first}, {s(fell[0], last)} in {last}.
The largest rise was in <strong>{esc(short(rose))}</strong>{ABOUT.get(rose[0], "")}: {s(rose[0], first)} to {s(rose[0], last)}.
VAT, and purchase tax before it, went from {s("vat", first)} to {s("vat", last)}.
All public sector receipts were {num(f"thist.gdp.total.{first}", "pct")} of GDP in {first} and {num(f"thist.gdp.total.{last}", "pct")} in {last}.</p>''')
    body.append('<p>These figures come from the OBR\'s historical database, which is older than the figures on the <a href="taxes.html">main taxes page</a> (from 1999-00) and groups some taxes differently, so the two are shown separately and not joined.</p>')
    body.append(FOLD)
    items = [(esc(n), f"thist.sharechange.{k}.{first}.{last}",
              f"{s(k, first)} of all receipts in {first}, {s(k, last)} in {last}") for k, n in moves[::-1]]
    body.append(change_bars(items, "pts", num, caption=f"Change in each group's share of all public sector receipts, {first} to {last}, in percentage points. "
                            "A percentage point is the simple difference between two percentages: from 6% to 2% is a fall of 4 points."))
    body.append('<p class="small">“Everything else” is all receipts minus the six named groups: business rates, oil and gas taxes, stamp duties, Capital Gains Tax, Inheritance Tax, the TV licence fee, smaller taxes, and receipts that are not taxes, such as interest, dividends and the surpluses of public bodies.</p>')
    head = ["Year"] + [esc(n.split(" (")[0]) for _, n in groups]
    rows = [[y] + [num(f"thist.share.{k}.{y}", "pct") for k in keys] for y in years]
    body.append(details_table("Show every year as a share of all receipts", f"Public receipts by type, % of all public sector receipts, {first} to {last}", head, rows))
    rows = [[y] + [num(f"thist.gdp.{k}.{y}", "pct") for k in keys + ["total"]] for y in years]
    body.append(details_table("Show every year as a share of GDP", f"Public receipts by type, % of GDP, {first} to {last}", head + ["All receipts"], rows))
    body.append('<p class="small">Shares of all receipts = each group\'s cash receipts ÷ all public sector current receipts in the same year × 100. Tap any figure to see the £ million amounts it was calculated from.</p>')
    body.append(f'''<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>The OBR built these series by joining Bank of England and ONS figures. It says they are not National Statistics and that it made judgements to keep them consistent across years.</li>
<li>Up to 1998-99 receipts are counted on a cash basis, and from 1999-00 on an accruals basis, so small jumps around that year can come from the change in method.</li>
<li>Some taxes were replaced by others (listed under the chart). Each line keeps the OBR's grouping, so a line that crosses one of those years joins two different taxes.</li>
<li>“Everything else” mixes taxes and other receipts, because the OBR's long series does not separate them for every year.</li>
<li>The database was last updated in July 2023, so {last} is an early estimate and later revisions are not included. The <a href="taxes.html">main taxes page</a> has newer figures from 1999-00, grouped differently.</li>
<li>Shares show what the tax system raised, not why it changed: tax rates, prices, wages, spending patterns and North Sea oil all move them.</li>
</ul></div>''')
    body.append(source_line(sources, ["obrhist-receipts", "obrhist-receipts-shares", "obrhist-receipts-amounts"], "Sheets “Receipts (per cent of GDP)” and “Receipts (£m)”. Shares of all receipts calculated here."))
    return page("tax-history.html", "Which taxes raised the money since 1948?", "\n".join(body),
                "UK public receipts by type of tax since 1948-49: Income Tax, National Insurance, VAT, duties, Corporation Tax and Council Tax, as shares of all receipts and of GDP.")
