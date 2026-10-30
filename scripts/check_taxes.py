"""Independently bind the public current-tax projection and HTML to OBR cells.

No producer, projection or renderer mapping is imported here. The current source
hash, selections and ordered formulas are transcribed separately. This verifies
the accepted display rules, not the fiscal merit of their classification.
"""
import hashlib
import html
import json
import math
import re
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_HASH = "5e7ebb343bee091960052b1727bf7bff6997216e8a5bf7805d18770aa7d5914a"
SOURCE_HASH = "16a4bf46d8692e18790e87add342c6c44aa909cebb19f68ae857126a36d36459"
SOURCE_FILE = "data/raw/OBR_Public_finances_databank_October_2026.xlsx"
SOURCE_FIELDS = ("publication", "publisher", "published", "page", "url",
                 "downloaded", "sha256", "licence", "published_note")
RECEIPTS = "Receipts (£bn)"
CASH = "Aggregates (£bn)"
GDP = "Aggregates (per cent of GDP)"
GROUPS = {
    "income_tax": [("Q", 1), ("R", 1), ("S", 1)],
    "nic": [("AB", 1)],
    "vat": [("C", 1), ("D", 1)],
    "corporation_tax": [("U", 1), ("V", 1)],
    "other_taxes": [("AH", 1), ("Q", -1), ("R", -1), ("S", -1),
                    ("AB", -1), ("C", -1), ("D", -1), ("U", -1), ("V", -1)],
    "non_tax": [("AG", 1), ("AH", -1)],
}
GROUP_LABELS = {
    "income_tax": "Income tax",
    "nic": "National Insurance contributions",
    "vat": "VAT including refunds (net VAT plus refunds)",
    "corporation_tax": "Corporation tax and related charges",
    "other_taxes": "Other National Accounts taxes",
    "non_tax": "Receipts outside National Accounts taxes",
}
CT_EXPLANATION = (
    "Adds the source's onshore and offshore corporation tax rows. "
    "The onshore label includes Bank Surcharge and the Electricity Generator Levy (EGL). "
    "OBR note 3 also includes residential property developers tax and Pillar 2 taxes. "
    "Petroleum revenue tax, energy profits levy and bank levy stay in other taxes.")
NON_TAX_EXPLANATION = (
    "A calculated difference: all receipts minus National Accounts taxes. "
    "It is not the mixed source row relabelled as non-tax. "
    "Do not add the source's interest, dividend or operating surplus rows again.")
OUTTURN_EXPLANATION = (
    "Outturn can be revised. The outturn figures are consistent with the public "
    "finances bulletin released on 22 September 2026.")
PAYER_LIMIT = (
    "This page does not show who pays. "
    "These tables show receipts by tax type. They do not show how payments are split between people, "
    "or who ultimately bears the cost. They give no percentages for who bears that cost.")
NOTES = {
    RECEIPTS: ("C1", "C40", "C41", "C42", "C43"),
    CASH: ("C1", "D7", "O7", "C94", "C95"),
    GDP: ("C1", "C89", "C90", "C91", "C92"),
    "Glossary": ("C5", "C6", "C11", "C14", "C15"),
}


def require(condition, message):
    if not condition:
        raise ValueError("Tax source check: " + message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValueError("Tax source check: non-finite JSON: " + value)
    regular(path)
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=unique_object, parse_constant=invalid)


def regular(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)),
            "symlink in input path")
    require(path.is_file(), "missing regular file: " + str(path))


def digest(path):
    regular(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def year_name(start):
    return f"{start}-{(start + 1) % 100:02d}"


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


class Raw:
    """Read only the accepted current workbook; no historical receipt splice."""
    def __init__(self, root):
        path = root / SOURCE_FILE
        require(digest(path) == SOURCE_HASH, "pinned current workbook hash changed")
        self.values = load_workbook(path, read_only=True, data_only=True)
        try:
            self.formulas = load_workbook(path, read_only=True, data_only=False)
        except BaseException:
            self.values.close()
            raise
        self.cache = {}

    def close(self):
        self.values.close()
        self.formulas.close()

    def cell(self, ref):
        sheet, coordinate = ref.rsplit("!", 1)
        if sheet not in self.cache:
            bounds = {"max_row": 24, "max_col": 5} if sheet == "Glossary" else {"max_row": 106, "max_col": 34}
            values = {cell.coordinate: cell for row in self.values[sheet].iter_rows(**bounds)
                      for cell in row if hasattr(cell, "coordinate")}
            formulas = {cell.coordinate: cell for row in self.formulas[sheet].iter_rows(**bounds)
                        for cell in row if hasattr(cell, "coordinate")}
            self.cache[sheet] = values, formulas
        values, formulas = self.cache[sheet]
        cell, formula = values.get(coordinate), formulas.get(coordinate)
        require(not cell or cell.data_type != "e", "Excel error: " + ref)
        require(not formula or formula.data_type != "f", "unreviewed Excel formula: " + ref)
        return cell.value if cell else None

    def numeric(self, ref):
        value = self.cell(ref)
        if value is None or isinstance(value, str) and value.strip() in ("", "-"):
            return None
        require(number(value), "non-numeric fiscal cell: " + ref)
        return float(value)


def expected_data(root=ROOT):
    """Build checker expectations directly from pinned raw cells, never product JSON."""
    root = Path(root)
    require(digest(root / "data/sources.json") == CATALOGUE_HASH, "catalogue hash changed")
    source = read_json(root / "data/sources.json")["obr_databank"]
    require(source["file"] == SOURCE_FILE and source["sha256"] == SOURCE_HASH,
            "current source identity changed")
    raw = Raw(root)
    try:
        notes = {sheet + "!" + cell: raw.cell(sheet + "!" + cell)
                 for sheet, cells in NOTES.items() for cell in cells}
        for ref, text in notes.items():
            require(isinstance(text, str) and text, "source note is missing: " + ref)
        # Independently establish the names behind the tax and non-tax scope prose.
        source_labels = {RECEIPTS + "!" + c + "4": raw.cell(RECEIPTS + "!" + c + "4")
                         for c in ("U", "V", "W", "X", "Y", "AD", "AE", "AF")}
        compare(source_labels, {
            RECEIPTS + "!U4": "Onshore corporation tax (includes Bank Surcharge and EGL)3",
            RECEIPTS + "!V4": "Offshore corporation tax",
            RECEIPTS + "!W4": "Petroleum revenue tax",
            RECEIPTS + "!X4": "Energy profits levy",
            RECEIPTS + "!Y4": "Bank levy",
            RECEIPTS + "!AD4": "Public sector interest and dividend receipts",
            RECEIPTS + "!AE4": "Public sector gross operating surplus (GOS)",
            RECEIPTS + "!AF4": "Other public sector taxes and receipts",
        }, "tax and non-tax scope labels")
        require(notes[RECEIPTS + "!C42"] ==
                "1 Includes road lorry user charge. 2 Also includes capacity markets, green gas levy and warm home discount. 3 Also includes, residential property developers tax and Pillar 2 taxes",
                "corporation-tax inclusion note changed")
        # The explicit note pairs independently establish the outturn boundary.
        outturn = "22 September 2026"
        forecast = "2026-27"
        for sheet, actual_cell, forecast_cell in (
                (RECEIPTS, "C40", "C41"), (CASH, "C94", "C95"), (GDP, "C91", "C92")):
            require(outturn in notes[sheet + "!" + actual_cell],
                    "outturn bulletin note changed")
            text = notes[sheet + "!" + forecast_cell]
            require(forecast in text and "October 2026" in text,
                    "forecast boundary/vintage note changed")
        require("Debt at end March" in notes[GDP + "!C90"] and
                "GDP centred on end-March" in notes[GDP + "!C90"],
                "published debt GDP denominator convention changed")
        require(raw.cell(CASH + "!C1") == "£ billion", "cash units changed")
        require(raw.cell(GDP + "!C1") == "Per cent of GDP1", "GDP units changed")

        years = [year_name(start) for start in range(1999, 2032)]
        latest = year_name(2025)
        nodes = {}

        def direct(family, sheet, column, year):
            start = int(year[:4])
            row = start - {"component": 1999, "cash": 1946, "gdp": 1948}[family] + {
                "component": 7, "cash": 8, "gdp": 5}[family]
            ref, year_ref = f"{sheet}!{column}{row}", f"{sheet}!B{row}"
            require(raw.cell(year_ref) == year, "wrong source fiscal year: " + year_ref)
            label_ref = f"{sheet}!{column}4"
            label = raw.cell(label_ref)
            require(isinstance(label, str) and label, "series label is missing: " + label_ref)
            code_ref = None if family == "gdp" else f"{sheet}!{column}5"
            role = ({"D": "refund_component", "AG": "receipts_total", "AH": "tax_total"}.get(
                column, "tax_component") if family == "component" else
                {"C": "receipts_total", "D": "spending_total",
                 "O": "borrowing_flow", "X": "debt_stock"}[column])
            value = raw.numeric(ref)
            return {
                "v": value, "ref": ref, "year": year, "year_ref": year_ref,
                "label": label, "label_ref": label_ref,
                "code": raw.cell(code_ref) if code_ref else None, "code_ref": code_ref,
                "role": role, "unit": "percent GDP" if family == "gdp" else "GBP billion",
                "status": "forecast" if start >= 2026 else "outturn",
                "basis": "cash_stock" if role == "debt_stock" else "annual_accrual",
                "geography": "UK", "scope": "public_sector", "formula": "source_cell",
                "operands": [{"ref": ref, "coefficient": 1}],
                "missing_operands": [ref] if value is None else [],
            }

        for family, sheet in (("cash", CASH), ("gdp", GDP)):
            for column in ("C", "D", "O", "X"):
                for year in years:
                    nodes[f"{family}/{column}/{year}"] = direct(family, sheet, column, year)
        for column in ("Q", "R", "S", "AB", "C", "D", "U", "V", "AH", "AG"):
            nodes[f"component/{column}/{latest}"] = direct("component", RECEIPTS, column, latest)

        def calculated(terms, sheet, row, year):
            operands = [{"ref": f"{sheet}!{column}{row}", "coefficient": coefficient}
                        for column, coefficient in terms]
            missing = [op["ref"] for op in operands if raw.numeric(op["ref"]) is None]
            value = None if missing else math.fsum(
                raw.numeric(op["ref"]) * op["coefficient"] for op in operands)
            return {
                "v": value, "year": year, "unit": "GBP billion", "status": "outturn",
                "basis": "annual_accrual", "geography": "UK", "scope": "public_sector",
                "formula": "linear_combination", "operands": operands,
                "missing_operands": missing,
            }

        for name, terms in GROUPS.items():
            group_id = f"group/{name}/{latest}"
            node = calculated(terms, RECEIPTS, 33, latest)
            nodes[group_id] = node
            denominator_id = f"component/AG/{latest}"
            denominator = nodes[denominator_id]["v"]
            missing = ([group_id] if node["v"] is None else []) + (
                [denominator_id] if denominator is None or denominator == 0 else [])
            nodes[f"share/{name}/{latest}"] = {
                "v": None if missing else node["v"] / denominator * 100,
                "year": latest, "unit": "GBP per 100 GBP receipts", "status": "outturn",
                "basis": "annual_accrual", "geography": "UK", "scope": "public_sector",
                "formula": "share_of_receipts",
                "operands": [{"id": group_id, "coefficient": 1},
                             {"id": denominator_id, "coefficient": 1}],
                "missing_operands": missing,
            }
        nodes[f"balance/{latest}"] = calculated([("D", 1), ("C", -1)], CASH, 87, latest)

        # Recheck the accepted same-table balance with a storage-arithmetic
        # budget. This bound is derived from raw operands and never public input.
        for year in years:
            spending, receipts, borrowing = (nodes[f"cash/{c}/{year}"]["v"] for c in ("D", "C", "O"))
            if all(value is not None for value in (spending, receipts, borrowing)):
                residual = math.fsum((spending, -receipts, -borrowing))
                budget = 4 * sum(math.ulp(value) for value in (spending, receipts, borrowing))
                require(abs(residual) <= budget, "same-vintage borrowing identity changed: " + year)
        return {"schema_version": 1, "source": {key: source[key] for key in SOURCE_FIELDS},
                "latest_year": latest, "years": years, "notes": notes,
                "source_labels": source_labels, "nodes": nodes}
    finally:
        raw.close()


def compare(actual, expected, location="taxes"):
    """Strict keys/order/types and exact numbers: equal values cannot hide wrong cells."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected),
                location + ": missing or unexpected fields/nodes")
        for key, value in expected.items():
            compare(actual[key], value, location + "/" + key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected),
                location + ": missing/extra ordered operands or years")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, location + "/" + str(index))
    elif number(expected):
        require(number(actual) and actual == expected, location + ": numeric value changed")
    else:
        require(type(actual) is type(expected) and actual == expected,
                location + ": source identity, context, formula or missingness changed")


def validate_data(data, root=ROOT):
    require(type(data.get("schema_version")) is int, "schema version must be an integer")
    expected = expected_data(root)
    compare(data, expected)
    return expected


def display(node):
    if node["v"] is None:
        return "not given"
    if node["unit"] == "percent GDP":
        return ("−" if node["v"] < 0 else "") + format(abs(node["v"]), ",.1f") + "%"
    magnitude = abs(node["v"])
    prefix = "−£" if node["v"] < 0 else "£"
    if node["unit"] == "GBP per 100 GBP receipts":
        return prefix + format(magnitude, ",.2f")
    cash = Decimal(str(node["v"])).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return prefix + format(abs(cash), ",.1f") + "bn"


def source_refs(node, nodes):
    if node["formula"] == "share_of_receipts":
        return source_refs(nodes[node["operands"][0]["id"]], nodes) + " " + source_refs(
            nodes[node["operands"][1]["id"]], nodes)
    return " ".join(op["ref"] for op in node["operands"])


class TaxPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.figures = []
        self.current = None
        self.stack = []
        self.bar_groups = []
        self.bar_group = None
        self.bar_row = None
        self.tables = []
        self.table = None
        self.table_row = None
        self.table_cell = None
        self.bar_label = False
        self.bound = {}
        self.binding = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag not in ("area", "base", "br", "col", "embed", "hr", "img",
                       "input", "link", "meta", "param", "source", "track", "wbr"):
            self.stack.append((tag, classes))
        if tag == "div" and "tax-bars" in classes:
            require(self.bar_group is None, "nested tax chart groups")
            self.bar_group = {"scale": attributes.get("data-tax-scale"), "rows": []}
        if tag == "div" and "tax-bar" in classes:
            require(self.bar_group is not None and self.bar_row is None, "unbound tax chart row")
            self.bar_row = {}
        if tag == "span" and self.bar_row is not None and "label" not in self.bar_row:
            self.bar_row["label"] = ""
            self.bar_label = True
        bindings = [(key, attributes[key]) for key in
                    ("data-tax-explanation", "data-tax-note-ref", "data-tax-label-ref") if key in attributes]
        if bindings:
            require(len(bindings) == 1 and self.binding is None, "nested/ambiguous source prose")
            key = bindings[0]
            require(tag == "dd" and key not in self.bound, "duplicate/misplaced source prose")
            self.bound[key] = ""
            self.binding = key
        if tag == "span" and "tax-fill" in classes:
            require(self.bar_row is not None and "style" not in self.bar_row, "duplicate/unbound chart fill")
            self.bar_row["style"] = attributes.get("style")
        if tag == "table":
            require(self.table is None, "nested tax tables")
            self.table = []
        if tag == "tr":
            require(self.table is not None and self.table_row is None, "unbound table row")
            self.table_row = []
        if tag in ("th", "td"):
            require(self.table_row is not None and self.table_cell is None, "unbound table cell")
            self.table_cell = {"text": "", "ids": []}
        if tag != "data":
            return
        require(self.current is None, "nested data elements")
        require(len({name for name, _ in attrs}) == len(attrs), "duplicate data attributes")
        self.current = {"attrs": attributes, "text": ""}
        if self.table_cell is not None:
            self.table_cell["ids"].append(attributes.get("data-tax-id"))
        if self.bar_row is not None:
            require("identity" not in self.bar_row, "duplicate chart row value")
            self.bar_row["identity"] = attributes.get("data-tax-id")

    def handle_endtag(self, tag):
        if tag == "span":
            self.bar_label = False
        if tag == "dd":
            self.binding = None
        if tag == "data":
            require(self.current is not None, "unmatched data element")
            self.figures.append(self.current)
            self.current = None
        if tag in ("th", "td"):
            require(self.table_cell is not None and self.table_row is not None, "unclosed table cell")
            self.table_cell["text"] = " ".join(self.table_cell["text"].split())
            self.table_row.append(self.table_cell)
            self.table_cell = None
        if tag == "tr":
            require(self.table is not None and self.table_row is not None, "unclosed table row")
            self.table.append(self.table_row)
            self.table_row = None
        if tag == "table":
            require(self.table is not None, "unclosed table")
            self.tables.append(self.table)
            self.table = None
        if not self.stack:
            return
        opened, classes = self.stack.pop()
        require(opened == tag, "unbalanced tax HTML elements")
        if tag == "div" and "tax-bar" in classes:
            require(self.bar_group is not None and self.bar_row is not None, "unclosed chart row")
            self.bar_group["rows"].append(self.bar_row)
            self.bar_row = None
        if tag == "div" and "tax-bars" in classes:
            require(self.bar_group is not None, "unclosed chart group")
            self.bar_groups.append(self.bar_group)
            self.bar_group = None

    def handle_data(self, text):
        if self.bar_label:
            self.bar_row["label"] += text
        if self.binding is not None:
            self.bound[self.binding] += text
        if self.current is not None:
            self.current["text"] += text
        if self.table_cell is not None:
            self.table_cell["text"] += text


def validate_bars(groups, data):
    year = data["latest_year"]
    # Shares use a fixed £100 denominator, not the largest cash group.
    selections = [[f"share/{name}/{year}" for name in GROUPS]]
    selections += [[f"component/{column}/{year}" for column in columns] for columns in
                   (("Q", "R", "S"), ("AB",), ("C", "D"), ("U", "V"))]
    require(len(groups) == len(selections), "missing/extra tax chart groups")
    for index, (group, identities) in enumerate(zip(groups, selections)):
        rows = group["rows"]
        require([row.get("identity") for row in rows] == identities,
                "chart identities do not match source partition/components")
        values = [data["nodes"][identity]["v"] for identity in identities]
        negative = any(value is not None and value < 0 for value in values)
        require(index != 0 or not negative, "main partition must be nonnegative")
        scale = "receipts-100" if index == 0 else "signed" if negative else "positive"
        require(group["scale"] == scale, "wrong chart denominator/baseline")
        extent = 100 if index == 0 else max((abs(v) for v in values if v is not None), default=0)
        labels = list(GROUP_LABELS.values()) if index == 0 else [
            re.sub(r"(?<=\D)[123]$", "", data["nodes"][identity]["label"]) for identity in identities]
        for row, identity, label in zip(rows, identities, labels):
            value = data["nodes"][identity]["v"]
            width = 0 if value is None or extent == 0 else abs(value) / extent * (50 if negative else 100)
            origin = 50 if negative else 0
            left = origin - width if value is not None and value < 0 else origin
            require(row.get("label") == label, identity + ": incorrect plain chart label")
            require(row.get("style") == f"left:{left:.4f}%;width:{width:.4f}%",
                    identity + ": chart magnitude/sign position differs from raw value")


def validate_tables(tables, data):
    """Bind visible column labels, years/statuses and group names to their nodes."""
    year = data["latest_year"]
    labels = GROUP_LABELS
    def text(value):
        return {"text": " ".join(value.split()), "ids": []}
    def figure(identity):
        return {"text": display(data["nodes"][identity]), "ids": [identity]}
    expected = [[
        [text(value) for value in ("Group", "Cash", "Of each £100 of receipts")],
        *[[text(label), figure(f"group/{name}/{year}"), figure(f"share/{name}/{year}")]
          for name, label in labels.items()],
    ]]
    components = (("Q", "R", "S"), ("AB",), ("C", "D"), ("U", "V"),
                  ("AH", "Q", "R", "S", "AB", "C", "D", "U", "V"), ("AG", "AH"))
    for name, columns in zip(GROUPS, components):
        rows = [[text(value) for value in ("Source series", "Cash (source sign)", "Formula multiplier", "Source cell", "Status")]]
        for column in columns:
            identity = f"component/{column}/{year}"
            node = data["nodes"][identity]
            coefficient = next(coefficient for col, coefficient in GROUPS[name] if col == column)
            rows.append([text(node["label"]), figure(identity), text(f"{coefficient:+g}"),
                         text(node["ref"]), text(node["status"])])
        expected.append(rows)
    header = ("April–March year", "Receipts cash", "Receipts GDP", "Spending cash", "Spending GDP",
              "Borrowing cash", "Borrowing GDP", "End-March debt cash", "Debt GDP", "Status")
    for forecast in (False, True):
        rows = [[text(value) for value in header]]
        for fiscal_year in data["years"]:
            status = data["nodes"][f"cash/C/{fiscal_year}"]["status"]
            if (status == "forecast") != forecast:
                continue
            row = [text(fiscal_year)]
            for column in ("C", "D", "O", "X"):
                row.extend([figure(f"cash/{column}/{fiscal_year}"), figure(f"gdp/{column}/{fiscal_year}")])
            row.append(text(status))
            rows.append(row)
        expected.append(rows)
    # The basic story and its history precede all 6 source-detail tables.
    expected = expected[:1] + expected[-2:] + expected[1:-2]
    compare(tables, expected, "rendered tax table labels/years/statuses/columns")


def validate_story(raw, bound, data):
    """Bind source wording and keep technical depth after the basic story."""
    normalize = lambda text: " ".join(text.split())

    class Story(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack, self.nodes = [], []

        def handle_starttag(self, tag, attrs):
            node = {"tag": tag, "attrs": dict(attrs), "parents": list(self.stack)}
            self.nodes.append(node)
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                           "meta", "param", "source", "track", "wbr"}:
                self.stack.append(node)

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1]["tag"] == tag:
                self.stack.pop()

    story = Story()
    story.feed(raw)
    basics = [n for n in story.nodes if n["attrs"].get("data-basics") == "taxes"]
    require(len(basics) == 1 and basics[0]["tag"] == "section" and
            basics[0]["parents"][-1]["tag"] == "main", "missing unique tax basics section")
    basics = basics[0]
    def concealed(node):
        return any(p["tag"] == "details" or "hidden" in p["attrs"] or
                   p["attrs"].get("aria-hidden", "").lower() == "true" or
                   set(p["attrs"].get("class", "").split()) & {"v", "narrow", "wide"} or
                   re.search(r"display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)",
                             p["attrs"].get("style", ""), re.I)
                   for p in [node] + node["parents"])
    require(not concealed(basics) and "class" not in basics["attrs"], "tax basics container hidden")
    groups = next((n for n in story.nodes if n["attrs"].get("id") == "receipt-groups"), None)
    require(groups is not None and story.nodes.index(basics) < story.nodes.index(groups) and
            all(story.nodes.index(n) < story.nodes.index(groups) for n in story.nodes
                if basics in n["parents"]), "tax basics must precede first receipt groups")
    basic_details = [n for n in story.nodes if n["tag"] == "details" and basics in n["parents"]]
    require(len(basic_details) == 1 and basic_details[0]["parents"][-1] is basics,
            "tax basics must have one native devolved-rules disclosure")
    for detail in (n for n in story.nodes if n["tag"] == "details"):
        if detail is basic_details[0]:
            continue
        require(any(p["attrs"].get("id") == "tax-sources" for p in detail["parents"]) or
                (detail["attrs"].get("data-pid") == "tax-forecasts" and
                 any(p["attrs"].get("id") == "tax-history" for p in detail["parents"])),
                "unmarked source depth interrupts tax story")
    for ref, note in data["notes"].items():
        require(bound.get(("data-tax-note-ref", ref)) == note,
                "missing/changed original OBR note: " + ref)
    for ref, label in data["source_labels"].items():
        require(bound.get(("data-tax-label-ref", ref)) == label,
                "missing/changed scope source label: " + ref)
    require(bound.get(("data-tax-explanation", "corporation_tax")) == CT_EXPLANATION,
            "corporation-tax explanation differs from checked scope")
    require(bound.get(("data-tax-explanation", "non_tax")) == NON_TAX_EXPLANATION,
            "non-tax explanation differs from checked scope")
    require({key[1] for key in bound if key[0] == "data-tax-explanation"} == set(GROUPS),
            "all 6 group explanations must remain available")
    sources = re.search(r'<section id="tax-sources"[^>]*>(.*?)</section>', raw, re.S)
    require(sources is not None, "missing source section")
    headers = re.findall(r'<header data-pid="tax-header">(.*?)</header>', raw, re.S)
    require(len(headers) == 1, "missing/duplicate tax header")
    outturn_notes = re.findall(
        r'<p class="small" data-pid="tax-outturn-note">(.*?)</p>', raw, re.S)
    require(len(outturn_notes) == 1 and
            normalize(html.unescape(outturn_notes[0])) == OUTTURN_EXPLANATION and
            outturn_notes[0] in headers[0],
            "header outturn bulletin date/explanation changed")
    file_note = (
        f'File date: {data["source"]["published"]}; retrieved {data["source"]["downloaded"]}. '
        "The file date is its HTTP header date, not a verified release date.")
    file_notes = re.findall(r'<p class="small">(File date:.*?)</p>', raw, re.S)
    require(len(file_notes) == 1 and
            normalize(html.unescape(file_notes[0])) == file_note and
            file_notes[0] in sources[1] and "File date:" not in headers[0],
            "HTTP file date must remain distinct under Check the sources")
    payer_notes = re.findall(r'<p data-pid="who-pays-limit">(.*?)</p>', raw, re.S)
    require(len(payer_notes) == 1 and
            normalize(html.unescape(payer_notes[0])) == PAYER_LIMIT,
            "missing/changed payer and incidence limitation")
    positions = []
    for name in GROUPS:
        marker = f'<details data-pid="tax-source-{name}">'
        require(raw.count(marker) == 1 and sources[1].count(marker) == 1,
                "source detail must follow story inside Check the sources: " + name)
        positions.append(raw.index(marker))
    require(raw.index('id="who-pays"') < min(positions), "source depth interrupts basic story")
    require('<h3>Our explanation</h3>' in raw and
            raw.count('OBR note (original wording):') == len(data["notes"]),
            "source notes and our explanation must have distinct labels")
    for text in (
            "<h1>Taxes and other receipts</h1>",
            "Not all receipts are tax.",
            "The whole is all current public receipts: taxes plus other receipts.",
            "They are not shares of tax.",
            "Total receipts, spending, borrowing and debt since 1999-00",
            "Tax-type history is not shown.",
            "Negative borrowing means receipts were greater than spending.",
            "This page does not show who pays.",
            "That bulletin date is not the later forecast vintage."):
        require(text in normalize(raw), "missing plain-language scope: " + text)
    require(not re.search(r"Employers can send PAYE|Businesses remit VAT|Basics guidance will follow", raw),
            "unsupported remitter claim")
    require('data-tax-scale="receipts-100"' in raw, "missing £100 chart denominator")
    # Exact-note bindings do not allow a second, unverified source claim.
    require(len(bound) == len(data["notes"]) + len(data["source_labels"]) + len(GROUPS),
            "unexpected source prose binding")


def validate_html(raw, data, require_all=True):
    parser = TaxPage()
    parser.feed(raw)
    require(parser.current is None and not parser.stack, "unclosed data or HTML element")
    seen = set()
    nodes = data["nodes"]
    for figure in parser.figures:
        attrs = figure["attrs"]
        identity = attrs.get("data-tax-id")
        require(identity in nodes, "rendered figure lacks a valid tax identity")
        node = nodes[identity]
        require(not any(key in attrs for key in ("data-value-id", "data-derived-id", "data-report-id")),
                "tax figure mixes legacy fiscal identities")
        expected_attrs = {
            "data-ref": source_refs(node, nodes), "data-formula": node["formula"],
            "data-unit": node["unit"], "data-year": node["year"], "data-status": node["status"],
            "data-source-version": data["source"]["sha256"],
        }
        for key, value in expected_attrs.items():
            require(attrs.get(key) == value, identity + ": wrong rendered " + key)
        require("data-operands" in attrs, identity + ": missing rendered formula operands")
        compare(json.loads(attrs["data-operands"], object_pairs_hook=unique_object),
                node["operands"], identity + "/rendered operands")
        value = attrs.get("value")
        if node["v"] is None:
            require(value == "", identity + ": missing rendered value replaced")
        else:
            try:
                parsed = float(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("Tax source check: invalid rendered value: " + identity) from exc
            require(number(parsed) and parsed == node["v"], identity + ": rendered numeric value changed")
        require(figure["text"] == display(node), identity + ": rendered signed text changed")
        require(attrs.get("tabindex") is None and attrs.get("role") != "button",
                identity + ": figures must not add stops to the main keyboard path")
        seen.add(identity)
    if require_all:
        require(seen == set(nodes), "missing rendered public tax nodes")
        validate_bars(parser.bar_groups, data)
        validate_tables(parser.tables, data)
        validate_story(raw, parser.bound, data)
    return seen



def checked_forecast_prose(raw, data):
    """Mask dates in exact, independently bound current-OBR text snippets.

    The legacy PESA date guard still sees every other word and every other date.
    In particular, mentioning OBR does not exempt an unmarked forecast claim.
    Call after validate_data/validate has bound this data to the raw workbook.
    """
    forecast_refs = {RECEIPTS + "!C41", CASH + "!C95", GDP + "!C92"}
    seen = set()
    vintage_match = re.search(r"published ([A-Za-z]+ \d{4})", data["notes"][RECEIPTS + "!C41"])
    require(vintage_match is not None, "current forecast vintage note is missing")
    vintage = vintage_match.group(1)
    expected_outlook = (
        f"These years are forecasts, not observed facts. They use the {vintage} OBR outlook. "
        "Outturn and forecasts are separate. Source notes for each table are below.")
    expected_caption = f"{vintage} OBR forecasts: cash (£bn) and published GDP shares (%)"

    class Attributes(HTMLParser):
        def handle_starttag(self, tag, attrs):
            require(len({key for key, _ in attrs}) == len(attrs), "duplicate forecast marker attributes")
            self.attrs = dict(attrs)

    def checked(match):
        attribute_parser = Attributes()
        attribute_parser.feed("<" + match["tag"] + match["attrs"] + ">")
        attrs = attribute_parser.attrs
        marker = attrs.get("data-tax-forecast")
        if marker is None:
            return match.group(0)
        require("<" not in match["body"], "forecast marker must contain plain source text")
        text = " ".join(html.unescape(match["body"]).split())
        if marker == "source-note":
            identity = attrs.get("data-tax-note-ref")
            require(match["tag"] == "dd" and identity in forecast_refs,
                    "unknown current forecast source-note marker")
            expected = " ".join(data["notes"][identity].split())
        elif marker == "outlook":
            identity = "outlook"
            require(match["tag"] == "p", "forecast outlook marker must be a paragraph")
            expected = expected_outlook
        elif marker == "caption":
            identity = "caption"
            require(match["tag"] == "caption", "forecast caption marker must be a caption")
            expected = expected_caption
        else:
            raise ValueError("Tax source check: unknown forecast prose marker")
        require(identity not in seen, "duplicate forecast prose marker")
        require(text == expected, "forecast prose differs from current source/approved display: " + identity)
        seen.add(identity)
        # Retain every other word. This prevents arbitrary marked blocks from
        # sheltering extra dates, source claims or stale PESA wording.
        body = match["body"].replace(vintage, "current OBR vintage")
        return "<" + match["tag"] + match["attrs"].replace("data-tax-forecast", "data-checked-tax-forecast") + ">" + body + "</" + match["tag"] + ">"

    result = re.sub(r"<(?P<tag>p|dd|caption)\b(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>",
                    checked, raw, flags=re.S)
    require(seen == forecast_refs | {"outlook", "caption"}, "missing current forecast prose markers")
    require("data-tax-forecast" not in result, "unsupported forecast marker placement")
    return result


def validate(site=ROOT / "site", root=ROOT):
    site, root = Path(site), Path(root)
    path = site / "data/taxes.json"
    regular(path)
    require(path.stat().st_size < 500_000, "public tax data exceeds 500KB")
    data = read_json(path)
    expected = validate_data(data, root)
    html_path = site / "taxes.html"
    regular(html_path)
    require(html_path.stat().st_size < 500_000, "tax HTML exceeds 500KB")
    validate_html(html_path.read_text(encoding="utf-8"), expected)
    print(f"Independent current OBR tax check: {len(expected['nodes'])} public nodes, exact formulas, units, years, statuses and signed HTML checked")
    return expected


if __name__ == "__main__":
    validate()
