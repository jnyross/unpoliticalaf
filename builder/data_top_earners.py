"""High earners and Income Tax (John's question J6: how many would have to leave before receipts were meaningfully damaged).

HMRC Survey of Personal Incomes 2023-24, Table 3.3: taxpayers, total income before tax and
Income Tax by band of total income, for all taxpayers. The bands' total Income Tax (£274bn)
matches HMRC's Table 2.4 total, which data.py already reads.

Everything here is arithmetic on published figures. The what-if is mechanical: each leaver is
assumed to take the average Income Tax of their band, and nothing else changes. The page says so.
"""
from .data import Fact, num
from .readers import ods, ref

PATH = "data/fetched/hmrc/spi-2023-24-tables-3-1-to-3-11.ods"
SHEET = "Table_3_3_before_tax"
SRC = "hmrc-spi-2324-tables"
Y = "2023 to 2024"
RECEIPTS = "rec.total.2023-24"  # public sector current receipts, ONS/OBR, £bn
INCOME_TAX_TOTAL = "hmrc.total.2023 to 2024"  # Income Tax liabilities, HMRC Table 2.4, £bn

# Lower limits of the SPI bands (£ of total income before tax).
BANDS = [12570, 15000, 20000, 30000, 40000, 50000, 70000, 100000, 150000, 200000, 300000, 500000, 1000000]
# Groups are every band from a lower limit upwards.
GROUPS = {"ge150k": 150000, "ge500k": 500000, "ge1m": 1000000}
GROUP_LABELS = {"ge150k": "£150,000 and over", "ge500k": "£500,000 and over", "ge1m": "£1 million and over"}
# Leavers in each what-if row: a stated number, or "all" = every taxpayer in the group.
SCENARIOS = {
    "ge1m": [("s1000", 1000), ("s10000", 10000), ("all", None)],
    "ge150k": [("s1000", 1000), ("s10000", 10000), ("s100000", 100000), ("all", None)],
}


def build(facts):
    rows = ods(PATH)[SHEET]
    band_rows = {}
    total_row = None
    for i, r in enumerate(rows):
        if len(r) < 6 or str(r[1]).strip() != "All":
            continue
        if str(r[0]).strip() == "All ranges":
            total_row = i
            continue
        try:
            lo = int(float(r[0]))
        except (TypeError, ValueError):
            continue
        if lo in BANDS:
            band_rows[lo] = i
    assert total_row is not None and set(band_rows) == set(BANDS), "SPI Table 3.3 layout changed"

    # Raw figures, as published (taxpayers in thousands; income and tax in £ million).
    for lo in BANDS + ["all"]:
        i = total_row if lo == "all" else band_rows[lo]
        tag = "all" if lo == "all" else str(lo)
        for col, key, unit in ((2, "n", "thousand taxpayers"), (3, "inc", "£ million"), (4, "tax", "£ million")):
            facts.add(Fact(f"spi.band.{tag}.{key}", num(rows[i][col]), unit, Y, SRC, f"{SHEET}!{ref(i, col)}", "outturn",
                           note=("All taxpayers, UK. " if lo == "all" else "") + "Total income before tax, the band's lower limit."))

    def sum_of(members, key):
        return [f"spi.band.{m}.{key}" for m in members]

    # Groups: sums of the bands from each lower limit upwards.
    for g, lo in GROUPS.items():
        members = [b for b in BANDS if b >= lo]
        for key, unit in (("n", "thousand taxpayers"), ("inc", "£ million"), ("tax", "£ million")):
            ids = sum_of(members, key)
            facts.add(Fact(f"spi.{g}.{key}", sum(facts[i].value for i in ids), unit, Y, SRC, facts[ids[0]].locator, "calculated",
                           formula=" + ".join(ids), inputs=ids, note=f"Sum of the bands from £{lo:,} up."))
        n, tax, inc = facts[f"spi.{g}.n"], facts[f"spi.{g}.tax"], facts[f"spi.{g}.inc"]
        facts.add(Fact(f"spi.{g}.avgtax", tax.value * 1000 / n.value, "£ a year", Y, SRC, tax.locator, "calculated",
                       formula=f"{tax.id} × 1,000 ÷ {n.id}", inputs=[tax.id, n.id],
                       note="Average Income Tax per taxpayer in the group: £ million × 1,000 ÷ thousand taxpayers."))
        facts.add(Fact(f"spi.{g}.taxbn", tax.value / 1000, "£bn", Y, SRC, tax.locator, "calculated", formula=f"{tax.id} ÷ 1,000",
                       inputs=[tax.id], note="Income Tax in £ billion, for the text."))
        for key, base, label in (("n", "spi.band.all.n", "% of all taxpayers"), ("tax", "spi.band.all.tax", "% of all Income Tax"),
                                 ("inc", "spi.band.all.inc", "% of all taxpayers' income")):
            facts.add(Fact(f"spi.{g}.sh_{key}", 100 * facts[f"spi.{g}.{key}"].value / facts[base].value, label, Y, SRC,
                           facts[f"spi.{g}.{key}"].locator, "calculated", formula=f"100 × {g} {key} ÷ {base}", inputs=[f"spi.{g}.{key}", base]))

    # Each band's average Income Tax, for the table on the page.
    for lo in BANDS:
        n, tax = facts[f"spi.band.{lo}.n"], facts[f"spi.band.{lo}.tax"]
        facts.add(Fact(f"spi.band.{lo}.avgtax", tax.value * 1000 / n.value, "£ a year", Y, SRC, tax.locator, "calculated",
                       formula=f"spi.band.{lo}.tax × 1,000 ÷ spi.band.{lo}.n", inputs=[tax.id, n.id]))
        facts.add(Fact(f"spi.band.{lo}.sh_tax", 100 * tax.value / facts["spi.band.all.tax"].value, "% of all Income Tax", Y, SRC,
                       tax.locator, "calculated", formula=f"100 × spi.band.{lo}.tax ÷ spi.band.all.tax", inputs=[tax.id, "spi.band.all.tax"]))

    # What-if: leavers × average Income Tax of their group. Mechanical, before any other response.
    receipts = facts[RECEIPTS]
    income_tax = facts[INCOME_TAX_TOTAL]
    yard = facts.add(Fact("wif.yard.bn", 0.01 * receipts.value, "£bn", receipts.period, receipts.source, receipts.locator, "calculated",
                          formula=f"1% × {RECEIPTS}", inputs=[RECEIPTS], note="One per cent of public sector current receipts, 2023-24."))
    for g, scenarios in SCENARIOS.items():
        avg = facts[f"spi.{g}.avgtax"]
        n_group = facts[f"spi.{g}.n"]
        for key, n_people in scenarios:
            if n_people is None:
                pf = facts.add(Fact(f"wif.{g}.{key}.n", n_group.value * 1000, "people", Y, SRC, n_group.locator, "calculated",
                                    formula=f"{n_group.id} × 1,000", inputs=[n_group.id]))
            else:
                pf = facts.add(Fact(f"wif.{g}.{key}.n", float(n_people), "people", Y, SRC, avg.locator, "calculated",
                                    note="A stated number of leavers, for the what-if."))
            bn = facts.add(Fact(f"wif.{g}.{key}.bn", pf.value * avg.value / 1e9, "£bn", Y, SRC, avg.locator, "calculated",
                                formula=f"{pf.id} × {avg.id} ÷ 1,000,000,000", inputs=[pf.id, avg.id],
                                note="Mechanical: the leavers' average Income Tax, before any change by anyone else."))
            facts.add(Fact(f"wif.{g}.{key}.pct_tax", 100 * bn.value / income_tax.value, "% of all Income Tax", Y, SRC, bn.locator, "calculated",
                           formula=f"100 × {bn.id} ÷ {income_tax.id}", inputs=[bn.id, income_tax.id]))
            facts.add(Fact(f"wif.{g}.{key}.pct_rec", 100 * bn.value / receipts.value, "% of all receipts", Y, SRC, bn.locator, "calculated",
                           formula=f"100 × {bn.id} ÷ {RECEIPTS}", inputs=[bn.id, RECEIPTS]))
        # Leavers from each group that would equal one per cent of receipts.
        people = yard.value * 1e9 / avg.value
        pf = facts.add(Fact(f"wif.yard.{g}.n", round(people, -3), "people", Y, SRC, avg.locator, "calculated",
                            formula=f"{yard.id} × 1,000,000,000 ÷ {avg.id}, rounded to the nearest 1,000", inputs=[yard.id, avg.id]))
        facts.add(Fact(f"wif.yard.{g}.share", 100 * people / (n_group.value * 1000), "% of the group", Y, SRC, pf.locator, "calculated",
                       formula=f"100 × {pf.id} ÷ ({n_group.id} × 1,000)", inputs=[pf.id, n_group.id]))
    return {"groups": GROUP_LABELS, "bands": BANDS}
