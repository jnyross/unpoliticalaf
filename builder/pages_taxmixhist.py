"""Taxes by type since 1948-49, from the OBR's historical public finances database."""

from .html import FOLD, page, details_table, small_multiples, switch, change_bars, source_line, esc
from .pages_money import derive
from . import findings as F


# A few words on what a group covers, for the summary.
ABOUT = {
    "duties": ", on goods such as alcohol, tobacco and fuel",
    "nics": ", paid on earnings by workers and employers",
}


def short(kv):
    return kv[1].split(" (")[0]


def tax_history_page(facts, d, num, sources):
    h = d["tax_mix_history"]
    years, groups = h["years"], h["groups"]
    first, last = years[0], years[-1]
    keys = [k for k, _ in groups]

    # Every group crosses the 1999-00 change to accruals, and several cross a tax being
    # replaced, so changes are worked out only from the last break on.
    since = h["breaks"][-1][0]
    for k, _ in groups:
        derive(
            facts,
            f"thist.sharechange.{k}.{since}.{last}",
            facts[f"thist.share.{k}.{last}"].value - facts[f"thist.share.{k}.{since}"].value,
            "percentage points",
            f"{since} to {last}",
            "obrhist-receipts-shares",
            [f"thist.share.{k}.{last}", f"thist.share.{k}.{since}"],
            f"thist.share.{k}.{last} − thist.share.{k}.{since}",
        )
    named = [kv for kv in groups if kv[0] != "other"]
    moves = sorted(named, key=lambda kv: facts[f"thist.sharechange.{kv[0]}.{since}.{last}"].value)
    fell, rose = moves[0], moves[-1]

    recent = [y for y in years if y >= since]
    it = sorted(recent, key=lambda y: facts[f"thist.share.income_tax.{y}"].value)
    lo, hi = it[0], it[-1]
    top3 = sorted(named, key=lambda kv: -facts[f"thist.share.{kv[0]}.{last}"].value)[:3]

    def s(k, y):
        return num(f"thist.share.{k}.{y}", "pct0")

    body = ["<h1>Which taxes raised the money since 1948?</h1>"]
    body.append(
        f"""<div class="answer"><p class="lede">In {last}, {esc(short(top3[0]))}, {esc(short(top3[1]))} and {esc(short(top3[2]))} raised the largest shares of all public sector receipts: {s(top3[0][0], last)}, {s(top3[1][0], last)} and {s(top3[2][0], last)}.</p>
<p>Since {since}, when the current way of counting receipts began, Income Tax has raised between {s("income_tax", lo)} and {s("income_tax", hi)} of all receipts each year. Earlier years were counted differently and several taxes were replaced, so they are shown on their own and not compared with later years.</p></div>"""
    )
    marks = [(y, label) for y, label, _ in h["breaks"]]

    def chart(v):
        pre = {"share": "thist.share", "gdp": "thist.gdp"}[v]
        unit = {
            "share": "Per cent of all public sector receipts in each year",
            "gdp": "Per cent of GDP",
        }[v]
        breaks = [(years.index(y), t) for y, t in marks]
        ids = [[f"{pre}.{k}.{y}" for y in years] for k in keys]
        return small_multiples(
            f"Public receipts by type, {first} to {last}",
            [y[:4] for y in years],
            [(n, [facts[i].value for i in row]) for (k, n), row in zip(groups, ids)],
            unit
            + ". Axis years are financial years starting in April of the year shown. Source: OBR historical public finances database.",
            "pct",
            ids=ids,
            num=num,
            breaks=breaks,
            split_breaks=True,
            ymin=0,
            point_labels=years,
            # The share view reads every group's trend; the GDP view sums it up, to keep the page within its size limit
            summary_note=(
                ""
                if v == "share"
                else "The second table below gives every group's share of GDP in every year."
            ),
            finding=F.within(
                "Income Tax raised between {lo} and {hi} of "
                + {"share": "all receipts", "gdp": "GDP"}[v]
                + " in every year from {first} to {last}",
                # one decimal for GDP, where whole numbers would hide years below 9%
                (lambda x: f"{x:.0f}%") if v == "share" else (lambda x: f"{x:.1f}%"),
                si=keys.index("income_tax"),
                which="last",
            ),
        )

    body.append(
        switch(
            "Show each group as",
            [
                (
                    "Share of all receipts",
                    "Each group's share of everything the public sector received that year. A smaller share does not have to mean less money: other receipts may have grown faster.",
                    chart("share"),
                ),
                (
                    "Share of GDP",
                    "Each group as a share of GDP, the value of everything produced in the UK that year, as published by the OBR.",
                    chart("gdp"),
                ),
            ],
        )
    )
    body.append(
        "<p class='small'>Seven groups, one panel each, on the same scale. Amber dashed lines mark where a tax was replaced or the way receipts are counted changed, and the lines break there, so values either side are not compared:</p>"
    )
    body.append(
        "<ul class='small'>"
        + "".join(f"<li><strong>{y}:</strong> {esc(text)}</li>" for y, _, text in h["breaks"])
        + "</ul>"
    )
    body.append(f"<h2 id='mix'>What changed between {since} and {last}</h2>")
    # "Everything else" mixes taxes and other receipts, so it is not ranked with the named
    # taxes, but say so when it moved more than the largest named rise or fall.
    other = facts[f"thist.sharechange.other.{since}.{last}"].value
    other_note = ""
    if (
        other > facts[f"thist.sharechange.{rose[0]}.{since}.{last}"].value
        or other < facts[f"thist.sharechange.{fell[0]}.{since}.{last}"].value
    ):
        other_note = (
            f" These rankings cover the six named taxes. “Everything else”, which mixes smaller taxes with receipts that are not taxes, "
            f"{'rose' if other > 0 else 'fell'} more: {s('other', since)} to {s('other', last)}."
        )
    body.append(
        f"""<p>Income Tax raised {s("income_tax", since)} of all receipts in {since} and {s("income_tax", last)} in {last}. Over those years its share was lowest in {lo} ({s("income_tax", lo)}) and highest in {hi} ({s("income_tax", hi)}).
The largest fall was in <strong>{esc(short(fell))}</strong>{ABOUT.get(fell[0], "")}: {s(fell[0], since)} of all receipts in {since}, {s(fell[0], last)} in {last}.
The largest rise was in <strong>{esc(short(rose))}</strong>{ABOUT.get(rose[0], "")}: {s(rose[0], since)} to {s(rose[0], last)}.{other_note}
All public sector receipts were {num(f"thist.gdp.total.{since}", "pct")} of GDP in {since} and {num(f"thist.gdp.total.{last}", "pct")} in {last}.</p>"""
    )
    body.append(
        f"""<p>Changes are not worked out back to {first}. Every group crosses the change in how receipts were counted in {since}, and some cross a tax being replaced, so a change over the whole period would partly come from those changes, not from what each tax raised. The chart and the tables give every year, and each stretch between breaks can be read on its own.</p>"""
    )
    body.append(
        '<p>These figures come from the OBR\'s historical database, which is older than the figures on the <a href="taxes.html">main taxes page</a> (from 1999-00) and groups some taxes differently, so the two are shown separately and not joined.</p>'
    )
    body.append(FOLD)
    items = [
        (
            esc(n),
            f"thist.sharechange.{k}.{since}.{last}",
            f"{s(k, since)} of all receipts in {since}, {s(k, last)} in {last}",
        )
        for k, n in moves[::-1]
    ]
    body.append(
        change_bars(
            items,
            "pts",
            num,
            caption=f"Change in each group's share of all public sector receipts, {since} to {last}, in percentage points. "
            "A percentage point is the simple difference between two percentages: from 6% to 2% is a fall of 4 points.",
        )
    )
    body.append(
        '<p class="small">“Everything else” is all receipts minus the six named groups: business rates, oil and gas taxes, stamp duties, Capital Gains Tax, Inheritance Tax, the TV licence fee, smaller taxes, and receipts that are not taxes, such as interest, dividends and the surpluses of public bodies.</p>'
    )
    head = ["Year"] + [esc(n.split(" (")[0]) for _, n in groups]
    rows = [[y] + [num(f"thist.share.{k}.{y}", "pct") for k in keys] for y in years]
    body.append(
        details_table(
            "Show every year as a share of all receipts",
            f"Public receipts by type, % of all public sector receipts, {first} to {last}",
            head,
            rows,
        )
    )
    rows = [[y] + [num(f"thist.gdp.{k}.{y}", "pct") for k in keys + ["total"]] for y in years]
    body.append(
        details_table(
            "Show every year as a share of GDP",
            f"Public receipts by type, % of GDP, {first} to {last}",
            head + ["All receipts"],
            rows,
        )
    )
    body.append(
        '<p class="small">Shares of all receipts = each group\'s cash receipts ÷ all public sector current receipts in the same year × 100. Tap any figure to see the £ million amounts it was calculated from.</p>'
    )
    body.append(
        f"""<div class="limit"><p><strong>Limits.</strong></p><ul>
<li>The OBR built these series by joining Bank of England and ONS figures. It says they are not National Statistics and that it made judgements to keep them consistent across years.</li>
<li>Up to 1998-99 receipts are counted on a cash basis, and from 1999-00 on an accruals basis, so jumps around that year can come from the change in method. That is why changes are worked out only from 1999-00.</li>
<li>Some taxes were replaced by others (listed under the chart). The OBR's groups keep one name across those years, so each line breaks there rather than join two different taxes.</li>
<li>“Everything else” mixes taxes and other receipts, because the OBR's long series does not separate them for every year.</li>
<li>The database was last updated in July 2023, so {last} is an early estimate and later revisions are not included. The <a href="taxes.html">main taxes page</a> has newer figures from 1999-00, grouped differently.</li>
<li>Shares show what the tax system raised, not why it changed: tax rates, prices, wages, spending patterns and North Sea oil all move them.</li>
</ul></div>"""
    )
    body.append(
        source_line(
            sources,
            ["obrhist-receipts", "obrhist-receipts-shares", "obrhist-receipts-amounts"],
            "Sheets “Receipts (per cent of GDP)” and “Receipts (£m)”. Shares of all receipts calculated here.",
        )
    )
    return page(
        "tax-history.html",
        "Which taxes raised the money since 1948?",
        "\n".join(body),
        "UK public receipts by type of tax since 1948-49: Income Tax, National Insurance, VAT, duties, Corporation Tax and Council Tax, as shares of all receipts and of GDP.",
    )
