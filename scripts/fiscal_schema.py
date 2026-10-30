"""Fiscal schema construction from hash-bound, readable audit cells.

No workbook interpretation is inferred from a numeric match. The declarative
contract binds each product series to labels, periods, units and accounting scope.
check_fiscal uses a separately reopened workbook reader to verify this boundary.
"""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from audit_scope import SHEETS
from fiscal_contract import (BASE, YEARS, FUNCTION_ROWS, DETAIL_ROWS, selections)

ROOT = Path(__file__).resolve().parent.parent
STATUS = {
    "pesa_outturn": {"kind": "actual", "label": "PESA outturn; subject to revision"},
    "pesa_forecast": {"kind": "forecast", "label": "PESA forecast; OBR 3 March 2026"},
    "obr_databank_historical": {"kind": "uncertain", "candidates": ["actual", "estimate"],
        "label": "Historical OBR value; outturn/estimate status uncertain; notes conflict"},
    "obr_databank_forecast": {"kind": "forecast", "label": "OBR forecast; March/October vintage conflict unresolved"},
    "obr_joined_historical": {"kind": "uncertain", "candidates": ["actual", "estimate"],
        "label": "Joined historical series; source status uncertain; not National Statistics"},
    "obr_extrapolated": {"kind": "estimate", "label": "OBR extrapolation, not observed outturn"},
}
FORMULAE = {
    "source": "round(raw_source_value * scale, decimal_places); no rounding if decimal_places is null",
    "signed_sum": "sum(coefficient * scaled_raw_operand)",
    "quantisation_budget": "sum(abs(coefficient) * stored_source_quantum / 2)",
    "share": "part / whole * 100",
    "change": "(new - old) / old * 100",
}
DASH = {
    "4_1": "Literal dash: meaning unspecified in retained table; never interpreted as zero.",
    "4_2": "Literal dash: meaning unspecified in retained table; never interpreted as zero.",
    "4_3": "Literal dash: meaning unspecified in retained table; never interpreted as zero.",
    "4_4": "Literal dash: meaning unspecified in retained table; never interpreted as zero.",
    "5_2": "Literal dash: no explicit definition in retained notes; never interpreted as zero.",
    "Public finances since 1900": "Blank/dash: source value unavailable; never filled by the spending-minus-receipts identity.",
    "Spending (per cent of GDP)": "Literal dash: unavailable/gap; Contents D50, D52, D53 and D56 describe gaps or coverage. Never zero.",
}


def audit_reader(root=ROOT):
    index = json.loads((root / "data/audit/index.json").read_text())
    sources = json.loads((root / "data/sources.json").read_text())
    result = {}
    for entry in index["sheets"]:
        src = sources[entry["source_id"]]
        if any(entry[k] != src[s] for k, s in (
                ("source_file", "file"), ("source_sha256", "sha256"),
                ("published", "published"), ("retrieved", "downloaded"))):
            raise ValueError("Audit source identity changed")
        path = root / "data/audit" / entry["file"]
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Audit extract hash changed")
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                ref = entry["sheet"] + "!" + row["cell"]
                if ref in result:
                    raise ValueError("Duplicate audit cell")
                result[ref] = {"kind": row["kind"], "value": json.loads(row["raw_value_json"]),
                    "number_format": entry["formats"][int(row["format_id"])],
                    "formula": json.loads(row["formula_json"])}
        result[entry["sheet"] + "!@sheet"] = {"kind": "text", "value": entry["sheet"],
                                             "number_format": None, "formula": None}
    return result.__getitem__


def normal(text):
    text = re.sub(r"\s*\(\d+\)(,\s*\(\d+\))*", "", str(text).replace("\u00a0", " "))
    return " ".join(text.split())


def numeric(cell):
    if cell["kind"] == "blank" or (cell["kind"] == "text" and str(cell["value"]).strip() in ("", "-")):
        return None
    if cell["kind"] != "number" or isinstance(cell["value"], bool):
        raise ValueError("Fiscal source operand is not numeric")
    value = float(cell["value"])
    if not math.isfinite(value):
        raise ValueError("Non-finite fiscal operand")
    return value


def missingness(cell):
    if cell["kind"] == "blank":
        return "blank"
    if cell["kind"] == "text" and str(cell["value"]).strip() == "-":
        return "literal_dash"
    if cell["kind"] == "text" and str(cell["value"]).strip() == "":
        return "empty_text"
    return "present"


def metadata(p, read):
    for role, (ref, expected) in p["identity"].items():
        if normal(read(ref)["value"]) != normal(expected):
            raise ValueError(f"Fiscal semantic {role} mismatch: {p['series']} {ref}")
    sheet = p["ref"].rsplit("!", 1)[0]
    refs = []
    if p["source_id"].startswith("pesa"):
        if sheet == "4_1":
            status = "pesa_forecast" if p["period"] > BASE else "pesa_outturn"
            refs = ["4_1!B3", "4_1!B51", "4_1!B52", "4_1!B53"]
        elif sheet == "5_2":
            status, refs = "pesa_outturn", ["5_2!G6", "5_2!B137", "5_2!B138", "5_2!B147"]
        else:
            status, refs = "pesa_outturn", [sheet + "!B4", sheet + "!A1"]
            if sheet in ("4_3", "4_4"):
                refs.append(sheet + "!A28")
    elif p["source_id"] == "obr_databank":
        status = "obr_databank_historical"
        debt = p["series"].endswith(".debt")
        numerator = "B142" if p["period"] <= ("1973-74" if debt else "1945-46") else "B143"
        denominator = "B146" if p["period"] <= "1947-48" else "B147"
        refs = ["Public finances since 1900!" + c for c in
                ("B2", "B139", numerator, denominator, "B144", "B148")]
    else:
        status = "obr_extrapolated" if p["period"] == "2022-23" and p["note"] != "D57" else "obr_joined_historical"
        refs = ["Contents!" + c for c in ("D4", "D31", "D46", p["note"], "D64")]
    for ref in refs:
        if read(ref)["kind"] != "text":
            raise ValueError(f"Missing fiscal status/scope evidence: {ref}")
    cell = read(p["ref"])
    return {k: p[k] for k in ("ref", "source_id", "period", "series", "unit", "scale",
            "geography", "scope", "basis", "precision", "identity")} | {
        "status": status, "status_refs": refs, "missingness": missingness(cell),
        "formula": "source", "operands": [p["ref"]]}


def value_id(p):
    return p["series"] + "/" + p["period"]


def source_value(p, read):
    v = numeric(read(p["ref"]))
    if v is None:
        return None
    v *= p["scale"]
    # Table 5.2 is first normalised from million to billion at three decimals,
    # matching its retained integer-million values before the site's 1dp display.
    if p["source_id"] == "pesa_ch5":
        v = round(v, 3)
    return v if p["precision"] is None else round(v, p["precision"])


def reconciliation_specs():
    """Signed operands, quantisation steps and exclusions; never balancing plugs.

    Steps describe the stored source quantisation in the stated units. They are
    NOT measurement/statistical error bounds. The reader validates that every
    operand lies on that grid. Exact ratio identities use numerical epsilon only.
    """
    for y in YEARS:
        c = chr(ord("B") + int(y[:4]) - 2003)
        ar = int(y[:4]) - 1985 + 6
        parts = [(f"4_2!{c}{r}", 1, 0.1) for r, _ in FUNCTION_ROWS.values()]
        yield (f"functions/{y}", y, "GBP billion", parts + [(f"4_2!{c}25", -1, 0.1)],
               [], "TES functions; excludes all of-which subcategories and accounting adjustments")
        yield (f"services-to-TME/{y}", y, "GBP billion",
            [(f"4_2!{c}25", 1, 0.1), (f"4_2!{c}26", 1, 0.1), (f"4_2!{c}27", -1, 0.1)],
            [], "TES plus separately retained accounting adjustments; excludes temporary bank-classification effects (4_2 A35)")
        yield (f"TME-tables/{y}", y, "GBP billion",
            [(f"4_2!{c}27", 1, 0.1), (f"4_1!M{ar}", -1, 0.1)], [], "Same PESA TME basis, Tables 4.1 and 4.2")
    for key, (r, _) in FUNCTION_ROWS.items():
        yield (f"base-price/{key}", BASE, "GBP billion",
               [(f"4_2!X{r}", 1, 0.1), (f"4_3!X{r}", -1, 0.1)], [],
               "Same nominal and real price base; 4_3 A28")
    for key, n, r in (("current", "C", "D"), ("investment", "I", "J"), ("tme", "M", "N")):
        yield (f"aggregate-base/{key}", BASE, "GBP billion",
               [(f"4_1!{n}46", 1, 0.1), (f"4_1!{r}46", -1, 0.1)], [], "Same price base; 4_1 B51")
    for key, ch5 in zip(FUNCTION_ROWS, (20, 27, 37, 56, 64, 74, 79, 87, 99, 121, 130)):
        ch4 = FUNCTION_ROWS[key][0]
        for start in range(2021, 2026):
            y = f"{start}-{(start + 1) % 100:02d}"
            c4, c5 = chr(ord("B") + start - 2003), chr(ord("C") + start - 2021)
            yield (f"detail-total/{key}/{y}", y, "GBP billion",
                [(f"5_2!{c5}{ch5}", 1, 0.001), (f"4_2!{c4}{ch4}", -1, 0.1)],
                [], "PESA same-function totals, integer £million versus 0.1 £billion")
    yield ("debt-components", BASE, "GBP billion",
           [(f"5_2!G{r}", 1, 0.001) for r in range(15, 20)] + [("5_2!G14", -1, 0.001)],
           [], "Public debt transactions, including Bank of England and pension items; 5_2 B137:B138")
    yield ("debt-tables", BASE, "GBP billion",
           [("5_2!G14", 1, 0.001), ("4_2!X9", -1, 0.1)], [], "Public debt transactions versus PESA debt-interest line")
    for start in range(1900, 2032):
        y, r = f"{start}-{(start + 1) % 100:02d}", start - 1900 + 7
        s = "Public finances since 1900"
        yield (f"OBR-borrowing/{y}", y, "percentage points",
            [(f"{s}!D{r}", 1, 0), (f"{s}!C{r}", -1, 0), (f"{s}!E{r}", -1, 0)],
            [], "Stored unrounded ratios; no filling of missing borrowing")
    for start in range(1700, 2023):
        y, r = f"{start}-{(start + 1) % 100:02d}", start - 1700 + 7
        s = "Spending (per cent of GDP)"
        yield (f"history-current/{y}", y, "percentage points",
            [(f"{s}!E{r}", 1, 0), (f"{s}!F{r}", 1, 0), (f"{s}!D{r}", -1, 0)],
            [], "Stored identity E=D-F; E6 and Contents D49; missing investment is not zero")
        yield (f"history-functions/{y}", y, "percentage points",
            [(f"{s}!{c}{r}", 1, 0) for c in ("G", "H", "I", "L", "M", "N")] + [(f"{s}!D{r}", -1, 0)],
            [f"{s}!J{r}", f"{s}!K{r}"],
            "Other is a SOURCE residual (N6, Contents D58), not an independent total check; pensioner subsets J/K excluded")


def report_context(name, period):
    if name == "OBR-PESA-vintages":
        return {"formula": "signed_sum", "geography": "UK",
                "statuses": ["obr_databank_historical", "pesa_outturn"],
                "status_refs": ["Public finances since 1900!B2", "Public finances since 1900!B139",
                    "Public finances since 1900!B143", "Public finances since 1900!B147",
                    "Public finances since 1900!B144", "Public finances since 1900!B148", "4_1!B3"]}
    if name.startswith("history-"):
        geography = ("Great Britain" if period < "1800-01" else "historical boundary uncertain" if period == "1800-01"
                     else "Great Britain and Ireland" if period < "1922-23" else "UK")
        refs = ["Contents!" + c for c in ("D31", "D48", "D49", "D50", "D51", "D52", "D53", "D56", "D57", "D58", "D64")]
        return {"formula": "signed_sum", "geography": geography,
                "statuses": ["obr_joined_historical"], "status_refs": refs}
    if name.startswith("OBR-"):
        return {"formula": "signed_sum", "geography": "UK" if period >= "1922-23" else "historical UK incl. Ireland",
                "statuses": ["obr_databank_forecast" if period > BASE else "obr_databank_historical"],
                "status_refs": ["Public finances since 1900!" + c for c in
                    ("B2", "B139", "B142", "B143", "B144", "B146", "B147", "B148")]}
    return {"formula": "signed_sum", "geography": "UK", "statuses": ["pesa_outturn"],
            "status_refs": ["4_1!B3", "4_1!B51", "4_1!B52", "5_2!G6"]}


def partition(refs):
    if len(refs) != len(set(refs)):
        raise ValueError("Duplicate or overlapping reconciliation operands")
    # Prevent adding PESA parent functions and their selected subcategories.
    for key, (row, _, parent) in DETAIL_ROWS.items():
        parent_row = FUNCTION_ROWS[parent][0]
        if f"5_2!G{row}" in refs and f"4_2!X{parent_row}" in refs:
            raise ValueError("Overlapping parent and selected-item totals")


def reconciliations(read):
    reports = []
    for name, period, unit, terms, exclusions, reason in reconciliation_specs():
        refs = [ref for ref, _, _ in terms]
        partition(refs)
        operands, missing = [], []
        for ref, coefficient, quantum in terms:
            v = numeric(read(ref))
            if v is None:
                missing.append(ref)
            elif ref.startswith("5_2!"):
                v *= 0.001
            if v is not None and quantum and abs(v / quantum - round(v / quantum)) > 1e-6:
                raise ValueError(f"Source quantisation changed: {ref}")
            operands.append({"ref": ref, "coefficient": coefficient, "value": v, "quantum": quantum})
        if missing and not name.startswith(("OBR-", "history-")):
            raise ValueError(f"Missing required reconciliation operands: {name}: {missing}")
        residual = None if missing else math.fsum(o["coefficient"] * o["value"] for o in operands)
        budget = math.fsum(abs(o["coefficient"]) * o["quantum"] / 2 for o in operands)
        # Floating-point computation allowance, in the reported unit, not a
        # fiscal data tolerance. No format-derived error is assigned to ratios.
        epsilon = 1e-9
        if residual is not None and abs(residual) > budget + epsilon:
            raise ValueError(f"Fiscal reconciliation failed: {name}: residual {residual}, budget {budget}")
        reports.append({"id": name, "period": period, "unit": unit, "operands": operands,
            "residual": residual, "quantisation_budget": budget, "numeric_epsilon": epsilon,
            "outcome": "not_testable_missing" if missing else "within_quantisation",
            "missing_operands": missing, "excluded_refs": exclusions, "basis": reason,
            **report_context(name, period)})
    # Different publication vintages do not have an established error bound.
    refs = ["Public finances since 1900!D132", "4_1!O46"]
    vals = [numeric(read(ref)) for ref in refs]
    if any(v is None for v in vals):
        raise ValueError("Missing cross-vintage comparison operand")
    reports.append({"id": "OBR-PESA-vintages", "period": BASE, "unit": "percentage points",
        "operands": [{"ref": ref, "value": v} for ref, v in zip(refs, vals)],
        "residual": vals[0] - vals[1], "quantisation_budget": None,
        "numeric_epsilon": None, "outcome": "not_comparable",
        "missing_operands": [], "excluded_refs": [],
        "basis": "Different OBR/PESA vintages and GDP bases; no established source error bound. Difference shown, no pass/fail proximity claim."})
    reports[-1].update(report_context("OBR-PESA-vintages", BASE))
    return reports


def derived(data):
    """Enumerate every rendered share/change; results use the published operands."""
    result = {}
    def add(kind, a, b):
        aid, bid = a["value_id"], b["value_id"]
        key = kind + ":" + aid + ":" + bid
        av, bv = a["v"], b["v"]
        ok = av is not None and bv is not None and (bv != 0 if kind == "share" else av != 0)
        v = (av / bv * 100 if kind == "share" else (bv - av) / av * 100) if ok else None
        pa, pb = data["provenance"][aid], data["provenance"][bid]
        if pa["unit"] != pb["unit"] or pa["basis"] != pb["basis"] or pa["geography"] != pb["geography"]:
            raise ValueError("Incompatible derived fiscal operands")
        if kind == "share" and (pa["period"] != pb["period"] or pb["scope"] != "TES"):
            raise ValueError("Share must use same-period TES denominator")
        if kind == "change" and pa["series"] != pb["series"]:
            raise ValueError("Change must compare the same fiscal series")
        result[key] = {"v": v, "formula": kind, "operands": [aid, bid],
            "periods": [pa["period"], pb["period"]], "unit": "per 100 of TES" if kind == "share" else "percent change",
            "scale": 1, "geography": pa["geography"], "scope": [pa["scope"], pb["scope"]],
            "statuses": [pa["status"], pb["status"]],
            "basis": pa["basis"], "missingness": "present" if ok else "missing_or_zero_denominator"}
    whole = data["services_total"][BASE]
    for area in data["functions"]:
        add("share", area["series"][BASE]["nominal"], whole)
        for start in ("2015-16", "2005-06"):
            add("change", area["series"][start]["real"], area["series"][BASE]["real"])
    add("share", data["debt_interest"][BASE], whole)
    add("share", whole, whole)
    return result


def enrich(data, root=ROOT):
    read = audit_reader(root)
    provenance, evidence = {}, {}
    for node, p in selections(data):
        key = value_id(p)
        meta = metadata(p, read)
        expected = source_value(p, read)
        if expected is None and p["source_id"].startswith("pesa"):
            raise ValueError(f"Missing required fiscal value: {key}")
        if node["ref"] != p["ref"] or node["v"] != expected:
            raise ValueError(f"Fiscal semantic/value mismatch: {key}")
        node["value_id"] = key
        provenance[key] = meta
        for ref in [p["ref"]] + [v[0] for v in p["identity"].values()] + meta["status_refs"]:
            evidence[ref] = read(ref)
    reports = reconciliations(read)
    for report in reports:
        for ref in [o["ref"] for o in report["operands"]] + report["excluded_refs"] + report["status_refs"]:
            evidence[ref] = read(ref)
    data.update({"fiscal_schema_version": 2, "provenance": provenance, "source_cells": evidence,
                 "status_definitions": STATUS, "formulae": FORMULAE, "dash_semantics": DASH,
                 "sheet_sources": {sheet: sid for sid, sheets in SHEETS.items() for sheet in sheets},
                 "reconciliations": reports})
    data["derived"] = derived(data)
    return data
