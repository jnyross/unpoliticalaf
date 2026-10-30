"""Minimal CURRENT OBR projection. Historical receipt data never enters this payload."""
import json
from copy import deepcopy

SOURCE_KEYS = ("publication", "publisher", "published", "page", "url", "downloaded",
               "sha256", "licence", "published_note")
COMPONENTS = ("Q", "R", "S", "AB", "C", "D", "U", "V", "AH", "AG")
GROUPS = ("income_tax", "nic", "vat", "corporation_tax", "other_taxes", "non_tax")


def project(receipts):
    tables = receipts["tables"]
    rt = tables["current_receipts"]
    cash = tables["current_aggregates_cash"]
    gdp = tables["current_aggregates_gdp"]
    years = list(rt["series"]["AG"]["values"])
    latest = max(y for y in years if rt["series"]["AG"]["values"][y]["status"] == "outturn")
    result = {
        "schema_version": 1,
        "source": {k: receipts["sources"]["obr_databank"][k] for k in SOURCE_KEYS},
        "latest_year": latest, "years": years, "notes": {},
        "source_labels": {rt["series"][c]["label_ref"]: rt["series"][c]["label"]
                          for c in ("U", "V", "W", "X", "Y")}, "nodes": {},
    }
    for table in (rt, cash, gdp):
        result["notes"].update({ref: cell["raw"] for ref, cell in table["notes"].items()})
    nodes = result["nodes"]

    def direct(table, column, year, identity):
        series = table["series"][column]
        value = series["values"][year]
        node = {k: deepcopy(value[k]) for k in
                ("v", "ref", "year_ref", "status", "basis", "geography", "scope")}
        node.update({k: series[k] for k in ("label", "label_ref", "code", "code_ref", "role", "unit")})
        node.update(year=year, formula="source_cell",
                    operands=[{"ref": value["ref"], "coefficient": 1}],
                    missing_operands=[value["ref"]] if value["v"] is None else [])
        nodes[identity] = node

    for family, table in (("cash", cash), ("gdp", gdp)):
        for column in ("C", "D", "O", "X"):
            for year in years:
                direct(table, column, year, f"{family}/{column}/{year}")
    for column in COMPONENTS:
        direct(rt, column, latest, f"component/{column}/{latest}")
    for name in GROUPS:
        identity = f"group/{name}/{latest}"
        nodes[identity] = {k: deepcopy(rt["derived"][name][latest][k]) for k in
                           ("v", "formula", "operands", "unit", "status", "basis",
                            "geography", "scope", "missing_operands")}
        nodes[identity]["year"] = latest
        group = nodes[identity]
        denominator = nodes[f"component/AG/{latest}"]
        missing = ([identity] if group["v"] is None else []) + (
            [f"component/AG/{latest}"] if denominator["v"] is None or denominator["v"] == 0 else [])
        nodes[f"share/{name}/{latest}"] = {
            "v": None if missing or denominator["v"] == 0 else group["v"] / denominator["v"] * 100,
            "year": latest, "unit": "GBP per 100 GBP receipts",
            **{k: group[k] for k in ("status", "basis", "geography", "scope")},
            "formula": "share_of_receipts",
            "operands": [{"id": identity, "coefficient": 1},
                         {"id": f"component/AG/{latest}", "coefficient": 1}],
            "missing_operands": missing,
        }
    spending, income = nodes[f"cash/D/{latest}"], nodes[f"cash/C/{latest}"]
    missing = spending["missing_operands"] + income["missing_operands"]
    nodes[f"balance/{latest}"] = {
        "v": None if missing else spending["v"] - income["v"], "year": latest,
        "unit": "GBP billion",
        **{k: spending[k] for k in ("status", "basis", "geography", "scope")},
        "formula": "linear_combination",
        "operands": [{"ref": spending["ref"], "coefficient": 1},
                     {"ref": income["ref"], "coefficient": -1}],
        "missing_operands": missing,
    }
    return result


def encode(data):
    return (json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
