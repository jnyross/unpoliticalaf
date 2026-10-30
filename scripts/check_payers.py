"""Independent payer verifier. Does not import the producer or its mappings.

validate_data(root, data) and validate_page(root, data, html) raise ValueError.
Raw ODS and XLSX are reopened with ZIP/XML; cached values, labels, formulas,
notes, original response hashes and envelope hashes are checked independently.
"""
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

# Reviewed immutable source identities. The editable register cannot repin them.
PINS = (
    ("hmrc-latest-release.html.json", 76341, "bb6ec060b31ea763be441ac6e1b14954b853c06d917f1e823d9f7354d592ef1e", 81497, "80b26b666e449cf6f8c4161808dbb4cc7d31f3d8ece4c25d40203cad8c3d8836"),
    ("hmrc-table24-july2026.ods", 18791, "8eb6281c40d716367cd063c5cfd124ba49fb7ab223c8ebacfb6680db1113c6b7", None, None),
    ("ons-bulletin-2024.html.json", 96972, "3ea7d0ca5d0461f9f8f1759ec96b0203358fdebd10a59afc60c3b4eb3582bfcc", 102228, "438d846bff86d243b4b0d9aca02a60a730e8356eeba2ea99dd92322497c77566"),
    ("ons-dataset-page.html.json", 79070, "13069b94e2a005f77ad75e97d076bf61c76ceeba9dcc7f045d8aa91517b2befb", 82089, "72d9a514afb25653ee15b41360bd4fe10227e64984038cef34620605823d4f42"),
    ("ons-etb-fye2024.xlsx", 247472, "2e38c1694d922427509879b9553a4c3473b8ba1174898c2dd414668ecbb2bf73", None, None),
    ("ons-qmi.html.json", 122882, "84bd2949ad4d453155a9b27714e6bf41f6634075317b5bbbc5a0a7668f972e7f", 129005, "e4d4c73363d52bf11141c0df79a736b6012dadae15782bbf768b9acc45b07de4"),
    ("ons-technical-2019.html.json", 176769, "2822bc0a9f9f1c214f9fdf37d5aa1c2a4c31122fd09919af7324c3c95f1b2f15", 183056, "333f37418a495e5f46b724f6366001330f1d5b42462e2954bd2749ab1907f8f1"),
)
URLS = (
    "https://www.gov.uk/government/statistics/income-tax-liabilities-statistics-tax-year-2023-to-2024-to-tax-year-2026-to-2027",
    "https://assets.publishing.service.gov.uk/media/6a54e2b72467584757371e1a/Table_2.4_Shares_of_total_Income_Tax_liability.ods",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/theeffectsoftaxesandbenefitsonhouseholdincomefinancialyearending2014",
    "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/theeffectsoftaxesandbenefitsonhouseholdincomefinancialyearending2014/financialyearending2024/etbreferencetablesfye202324final.xlsx",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/methodologies/theeffectsoftaxesandbenefitsonukhouseholdincome",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/articles/theeffectsoftaxesandbenefitsonhouseholdincome/financialyearending2019",
)
DATES = ("2026-07-15", "2026-07-15", "2025-09-25", "2025-09-25", "2025-09-25", "2018-06-15", "2020-06-25")
IDS = ("hmrc_release", "hmrc", "ons_bulletin", "ons_dataset", "ons", "ons_qmi", "ons_method")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def input_path(root, relative):
    given = Path(root).absolute()
    require(not any(p.is_symlink() for p in (given, *given.parents)), "Symlink in payer input root")
    base = given.resolve(strict=True)
    relative = Path(relative)
    require(not relative.is_absolute() and ".." not in relative.parts, "Unsafe payer path")
    current = base
    for component in relative.parts:
        current /= component
        require(not current.is_symlink(), "Symlink in payer input")
    require(current.is_file() and current.resolve().is_relative_to(base), "Missing or escaped payer input")
    return current


def check_sources(root, public):
    register_bytes = input_path(root, "data/payers/sources.json").read_bytes()
    require(hashlib.sha256(register_bytes).hexdigest() ==
            "25fac4399c7f622848e86a208fa8546d9c0c09f5368f13a952447a098d116dcf", "Pinned source register changed")
    register = json.loads(register_bytes)
    require(register.get("schema_version") == 1, "Register schema changed")
    entries = register["sources"]
    require(len(entries) == 7 and {e["file"] for e in entries} ==
            {"data/payers/raw/" + p[0] for p in PINS}, "Register source set changed")
    require(set(public) == set(IDS), "Public source set changed")
    for index, (filename, size, digest, stored_size, stored_digest) in enumerate(PINS):
        entry = next(e for e in entries if e["file"] == "data/payers/raw/" + filename)
        require((entry["bytes"], entry["sha256"], entry["url"], entry["publication_or_update_date"]) ==
                (size, digest, URLS[index], DATES[index]), "Source register identity changed")
        blob = input_path(root, entry["file"]).read_bytes()
        if stored_digest:
            require((entry.get("stored_bytes"), entry.get("stored_sha256")) == (stored_size, stored_digest),
                    "Envelope register identity changed")
            require(len(blob) == stored_size and hashlib.sha256(blob).hexdigest() == stored_digest,
                    "Envelope bytes changed")
            envelope = json.loads(blob)
            require(set(envelope) == {"encoding", "original_response"} and
                    envelope.get("encoding") == "utf-8" and isinstance(envelope.get("original_response"), str),
                    "Invalid response envelope")
            blob = envelope["original_response"].encode("utf-8")
        require(len(blob) == size and hashlib.sha256(blob).hexdigest() == digest, "Original source bytes changed")
        sid = IDS[index]
        expected = {"url": URLS[index], "sha256": digest, "bytes": size, "published": DATES[index],
                    "publisher": "HM Revenue & Customs" if index < 2 else "Office for National Statistics",
                    "publication": {"hmrc_release": "Income Tax liabilities, July 2026 release",
                                    "hmrc": "Income Tax liabilities, Table 2.4",
                                    "ons_bulletin": "Effects of taxes and benefits, FYE 2024 bulletin",
                                    "ons_dataset": "Effects of taxes and benefits dataset",
                                    "ons": "Effects of taxes and benefits, FYE 2024 reference tables",
                                    "ons_method": "Effects of taxes and benefits, FYE 2019 technical report",
                                    "ons_qmi": "Effects of taxes and benefits QMI"}.get(sid, sid.replace("_", " "))}
        if stored_digest:
            expected.update(stored_sha256=stored_digest, stored_bytes=stored_size)
        require(public[sid] == expected, "Public source metadata changed")


def raw_cells(root):
    """A separate reader: XLSX uses raw shared strings and cached XML scalars."""
    table_ns = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    office_ns = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    text_ns = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    with ZipFile(input_path(root, "data/payers/raw/hmrc-table24-july2026.ods")) as z:
        ods = ET.fromstring(z.read("content.xml"))
    sheets = {t.get("{" + table_ns + "}name"): t for t in ods.iter("{" + table_ns + "}table")}
    x = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with ZipFile(input_path(root, "data/payers/raw/ons-etb-fye2024.xlsx")) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = ["".join(n.itertext()) for n in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        targets = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        xlsx = {}
        for sh in workbook.find(x + "sheets"):
            target = targets[sh.get(rel)]
            name = target.lstrip("/") if target.startswith("/") else "xl/" + target
            xlsx[sh.get("name")] = {c.get("r"): c for c in ET.fromstring(z.read(name)).iter(x + "c")}

    def paragraph(element):
        pieces = [element.text or ""]
        for child in element:
            local = child.tag.removeprefix("{" + text_ns + "}")
            if local == "s":
                count = child.get("{" + text_ns + "}c", "1")
                require(bool(re.fullmatch(r"[1-9][0-9]{0,4}", count)), "Invalid ODF space count")
                content = " " * int(count)
            elif local == "tab":
                content = "\t"
            elif local == "line-break":
                content = "\n"
            else:
                content = paragraph(child)
            pieces.extend((content, child.tail or ""))
        return "".join(pieces)

    def read(sid, sheet, address):
        if sid == "hmrc":
            match = re.fullmatch(r"([A-Z]+)([0-9]+)", address)
            target_column = 0
            for letter in match[1]:
                target_column = target_column * 26 + ord(letter) - 64
            target_row = int(match[2])
            row_number = 1
            found = None
            for row in sheets[sheet].iter("{" + table_ns + "}table-row"):
                repeat = int(row.get("{" + table_ns + "}number-rows-repeated", "1"))
                if row_number <= target_row < row_number + repeat:
                    column = 1
                    for cell in row:
                        if cell.tag not in {"{" + table_ns + "}table-cell", "{" + table_ns + "}covered-table-cell"}:
                            continue
                        count = int(cell.get("{" + table_ns + "}number-columns-repeated", "1"))
                        if column <= target_column < column + count:
                            found = cell
                            break
                        column += count
                    break
                row_number += repeat
            require(found is not None, "Required ODS source cell absent")
            text = "\n".join(paragraph(p) for p in found.findall("{" + text_ns + "}p"))
            stored = found.get("{" + office_ns + "}value")
            value = float(stored) if stored is not None else text or None
            formula = found.get("{" + table_ns + "}formula")
        else:
            cell = xlsx[sheet].get(address)
            value, formula = None, None
            if cell is not None:
                v, f = cell.find(x + "v"), cell.find(x + "f")
                formula = "=" + f.text if f is not None and f.text else None
                if cell.get("t") == "inlineStr":
                    value = "".join(cell.find(x + "is").itertext())
                elif v is not None and v.text is not None:
                    kind = cell.get("t")
                    value = shared[int(v.text)] if kind == "s" else (v.text if kind in {"str", "e"} else (bool(int(v.text)) if kind == "b" else float(v.text)))
            text = None
        return {"source_id": sid, "sheet": sheet, "cell": address, "value": value, "text": text, "formula": formula}
    return read


def expected_values():
    """Independent display identity map, deliberately separate from producer."""
    specs = []
    sheet = "2_4_Taxpayer_share_tax"
    for gid, column, group in (("bottom50", "F", "Bottom 50%"), ("top10", "I", "Top 10%"), ("top1", "K", "Top 1%")):
        specs.append(("hmrc-" + gid, "hmrc", sheet, column + "27", group, "Share of Income Tax due",
                      "Total Income Tax liabilities", [(sheet, "A1"), (sheet, "A27"), (sheet, column + "2"), ("Contents", "A5")]))
    measures = (("direct", 5, "Direct taxes", "Gross household income"),
                ("indirect", 9, "Indirect taxes", "Gross household income"),
                ("combined", 15, "Direct and indirect taxes counted in this ONS analysis", "Gross household income"),
                ("expenditure", 22, "Indirect taxes", "Household expenditure"))
    for index, column in enumerate("DEFGH", 1):
        group = ("Bottom fifth", "Second fifth", "Middle fifth", "Fourth fifth", "Top fifth")[index - 1]
        for key, row, measure, denominator in measures:
            specs.append((f"ons-{index}-{key}", "ons", "Table 8", f"{column}{row}", group, measure, denominator,
                          [("Table 8", "A1"), ("Table 8", column + "4"), ("Table 8", f"B{row}"),
                           ("Table 8", "A22" if row == 22 else "A5")]))
    return specs


def validate_data(root, data):
    require(set(data) == {"schema_version", "scope", "sources", "values", "source_cells", "groups_overlap", "ons_group_basis"},
            "Unexpected public payer fields")
    require(data["schema_version"] == 1 and data["groups_overlap"] is True, "Invalid schema or overlap claim")
    require(data["scope"] == "Two separate official views; not complete all-tax incidence", "Scope changed")
    require(data["ons_group_basis"] == "Five approximately equal-person groups, not equal-household groups", "Group basis changed")
    check_sources(root, data["sources"])
    read = raw_cells(root)
    expected_cells = {}

    def retain(sid, sheet, address):
        ref = f"{sid}:{sheet}!{address}"
        expected_cells[ref] = read(sid, sheet, address)
        return ref

    expected = []
    for vid, sid, sheet, address, group, measure, denominator, labels in expected_values():
        reference = retain(sid, sheet, address)
        value = expected_cells[reference]["value"]
        if isinstance(value, str) and re.fullmatch(r"\s*[0-9]+(?:\.[0-9]+)?\s*", value):
            value = float(value)
        require(type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 100, "Missing/suppressed source percentage")
        expected.append({"id": vid, "value": float(value), "group": group, "measure": measure,
                         "source_id": sid, "sheet": sheet, "cell": address,
                         "source_sha256": PINS[1 if sid == "hmrc" else 4][2],
                         "published": DATES[1 if sid == "hmrc" else 4], "period": "2023/24",
                         "year_basis": "Tax year" if sid == "hmrc" else "Financial year ending 2024",
                         "status": "Estimated outturn" if sid == "hmrc" else "Completed-year survey/model estimates, not a forecast",
                         "unit": "%", "denominator": denominator, "geography": "UK",
                         "population": "UK individuals with positive Income Tax liability" if sid == "hmrc" else "UK people in private households",
                         "ranking": "Income assessable for tax before deductions and allowances" if sid == "hmrc" else "Equivalised household disposable income",
                         "formula": None, "operands": [], "source_cell": reference,
                         "label_cells": [retain(sid, sh, a) for sh, a in labels]})
    for address in ("A3", "A4", "A5", "A6"):
        retain("hmrc", "Contents", address)
    for sheet, addresses in {
        "Cover sheet": ("A1", "A5", "A6", "A9", "A20", "A23"), "Table 8": ("A2",),
        "Notes": ("B4", "B6", "B8", "B9", "B16", "B31"),
        "Table 2b": ("A43", "B44", "B45", "A65", "B66", "C45"),
    }.items():
        for address in addresses:
            retain("ons", sheet, address)
    # Bind the public aliases to the actual source labels, not only to numbers.
    # Strip edge whitespace here only; source_cells retains the exact source text.
    label_aliases = (
        ("hmrc", "2_4_Taxpayer_share_tax", "F2", "Bottom 50% percentile group", "group", "Bottom 50%", ["hmrc-bottom50"]),
        ("hmrc", "2_4_Taxpayer_share_tax", "I2", "Top 10% percentile group", "group", "Top 10%", ["hmrc-top10"]),
        ("hmrc", "2_4_Taxpayer_share_tax", "K2", "Top 1% percentile group", "group", "Top 1%", ["hmrc-top1"]),
    )
    label_aliases += tuple(("ons", "Table 8", column + "4", raw, "group", alias,
                           [f"ons-{i}-{measure}" for measure in ("direct", "indirect", "combined", "expenditure")])
                          for i, column, raw, alias in (
                              (1, "D", "Bottom", "Bottom fifth"), (2, "E", "2nd", "Second fifth"),
                              (3, "F", "3rd", "Middle fifth"), (4, "G", "4th", "Fourth fifth"),
                              (5, "H", "Top", "Top fifth")))
    label_aliases += tuple(("ons", "Table 8", address, raw, "measure", alias,
                           [f"ons-{i}-{measure}" for i in range(1, 6)])
                          for address, raw, measure, alias in (
                              ("B5", "Direct taxes", "direct", "Direct taxes"),
                              ("B9", "Indirect taxes", "indirect", "Indirect taxes"),
                              ("B15", "All taxes", "combined", "Direct and indirect taxes counted in this ONS analysis"),
                              ("B22", "Indirect taxes", "expenditure", "Indirect taxes")))
    label_aliases += (
        ("ons", "Table 8", "A5", "Percentages of gross income", "denominator", "Gross household income",
         [f"ons-{i}-{m}" for i in range(1, 6) for m in ("direct", "indirect", "combined")]),
        ("ons", "Table 8", "A22", "Percentages of expenditure", "denominator", "Household expenditure",
         [f"ons-{i}-expenditure" for i in range(1, 6)]),
    )
    public_values = {v["id"]: v for v in data["values"]}
    for sid, sheet, address, source_label, field, alias, value_ids in label_aliases:
        actual = read(sid, sheet, address)["value"]
        require(isinstance(actual, str) and actual.strip() == source_label,
                "Source label does not support the public alias: " + sheet + "!" + address)
        require(all(public_values.get(vid, {}).get(field) == alias for vid in value_ids),
                "Public group/measure/denominator alias differs from its source label")
    require(data["values"] == expected, "Public values or semantic provenance differ from original cells")
    require(data["source_cells"] == expected_cells, "Public source labels, notes, scalars or formulas differ")
    require("2023 to 2024" in expected_cells["hmrc:Contents!A5"]["value"] and
            "outturn" in expected_cells["hmrc:Contents!A5"]["value"], "Outturn source note absent")
    require("[note13]" in expected_cells["ons:Table 8!A2"]["value"], "Expenditure note identity absent")
    require(expected_cells["ons:Table 2b!C45"]["value"] == "..", "Suppression must remain suppression")
    public = json.dumps(data, ensure_ascii=False)
    require(not any(token in public for token in ("/home/", "data/payers/raw/", "original_response", "<!DOCTYPE", "36.7 million")),
            "Private/raw data leaked into public payer data")
    return True


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.nodes, self.stack = [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "text": [], "parents": list(self.stack)}
        self.nodes.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        for node in self.stack:
            node["text"].append(value)


def validate_page(root, data, text):
    validate_data(root, data)
    require(len(text.encode("utf-8")) < 500000, "Payer HTML is too large")
    document = Page(text)
    main = [n for n in document.nodes if n["tag"] == "main" and n["attrs"].get("id") == "main"]
    require(len(main) == 1, "Missing unique payer main")
    main = main[0]
    nodes = [n for n in document.nodes if main in n["parents"]]
    figures = [n for n in nodes if n["tag"] == "data"]
    require(len(figures) == 23, "Missing, duplicated or untracked payer figures")
    by_id = {v["id"]: v for v in data["values"]}
    require({n["attrs"].get("data-payer-id") for n in figures} == set(by_id), "Wrong figure identities")
    for node in figures:
        attrs = node["attrs"]
        value = by_id[attrs["data-payer-id"]]
        expected_attrs = {"value": str(value["value"]), "data-payer-id": value["id"],
                          "data-ref": value["sheet"] + "!" + value["cell"],
                          "data-source-sha256": value["source_sha256"], "data-period": "2023/24",
                          "data-status": value["status"], "data-denominator": value["denominator"],
                          "data-unit": "%", "data-population": value["population"], "data-ranking": value["ranking"],
                          "data-group": value["group"], "data-measure": value["measure"],
                          "data-formula": "published source cell"}
        require(attrs == expected_attrs, "Rendered figure provenance changed")
        require("".join(node["text"]) == f'{value["value"]:.1f}%', "Rendered percentage text changed")
        require(any(p["tag"] == "table" for p in node["parents"]), "No semantic table for payer value")
        require(not any(p["tag"] == "details" or "hidden" in p["attrs"] or
                        p["attrs"].get("aria-hidden") == "true" or
                        re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", p["attrs"].get("style", ""))
                        for p in [node] + node["parents"]), "Core payer value hidden")
        row = next(p for p in reversed(node["parents"]) if p["tag"] == "tr")
        require(value["group"] in "".join(row["text"]), "Table group label changed")
    tables = [n for n in nodes if n["tag"] == "table"]
    require(len(tables) == 3, "Expected three always-available tables")
    contracts = (
        ("HMRC: shares of total Income Tax liabilities, 2023/24 estimated outturn",
         ["Income group", "Share of Income Tax due"],
         ["hmrc-bottom50", "hmrc-top10", "hmrc-top1"]),
        ("ONS: percentages of gross household income, 2023/24 completed-year estimates",
         ["Income group", "Direct / gross income", "Indirect / gross income", "Combined / gross income"],
         [f"ons-{i}-{m}" for i in range(1, 6) for m in ("direct", "indirect", "combined")]),
        ("ONS: indirect taxes as a percentage of household expenditure, 2023/24 completed-year estimates",
         ["Income group", "Indirect / expenditure"],
         [f"ons-{i}-expenditure" for i in range(1, 6)]),
    )
    for table, (caption, heads, value_ids) in zip(tables, contracts):
        descendants = [n for n in nodes if table in n["parents"]]
        captions = ["".join(n["text"]) for n in descendants if n["tag"] == "caption"]
        headers = ["".join(n["text"]) for n in descendants if n["tag"] == "th" and n["attrs"].get("scope") == "col"]
        actual_ids = [n["attrs"].get("data-payer-id") for n in descendants if n["tag"] == "data"]
        require(captions == [caption] and headers == heads and actual_ids == value_ids,
                "Table year, status, denominator, group order or measure changed")
    headings = ["".join(n["text"]) for n in nodes if n["tag"] == "h2"]
    require(headings == ["Who owed Income Tax in 2023/24?", "How do taxes compare with household income?",
                         "Who sends the tax, and who bears its cost?", "Where can I check the numbers?"],
            "Payer heading scope/year changed")
    for table in tables:
        regions = [p for p in table["parents"] if p["attrs"].get("role") == "region"]
        captions = [n for n in nodes if n["tag"] == "caption" and table in n["parents"]]
        require(len(captions) == 1 and regions and
                regions[-1]["attrs"].get("aria-labelledby") == captions[0]["attrs"].get("id") and
                bool(captions[0]["attrs"].get("id")),
                "Table scroll region must name its own caption")
    source_sections = [n for n in nodes if n["tag"] == "section" and n["attrs"].get("id") == "payer-sources"]
    require(len(source_sections) == 1, "Missing unique payer source section")
    source_section = source_sections[0]
    require(source_section["parents"][-1] is main and
            all(nodes.index(n) < nodes.index(source_section) for n in nodes
                if n["tag"] == "table" or any(p["tag"] == "table" for p in n["parents"])),
            "Source details must follow all three complete tables")
    require(any(n["tag"] == "section" and n["attrs"].get("id") == "burden" and
                n["parents"][-1] is main and nodes.index(n) < nodes.index(source_section) for n in nodes) and
            all(nodes.index(n) < nodes.index(source_section) for n in nodes
                if any(p["attrs"].get("id") == "burden" for p in n["parents"])),
            "Source details must follow the explanation of tax burden")
    for sid, section_id, table_ids, link_text in (
        ("hmrc", "income-tax", ["hmrc-table"], "HMRC Table 2.4 (ODS)"),
        ("ons", "household-taxes", ["ons-income-table", "ons-expenditure-table"], "ONS reference tables (XLSX), Table 8"),
    ):
        panels = [n for n in nodes if n["tag"] == "section" and n["attrs"].get("id") == section_id]
        require(len(panels) == 1, "Missing unique source panel")
        panel = panels[0]
        notes = [n for n in nodes if n["tag"] == "p" and n["attrs"].get("id") == sid + "-source-note"]
        require(len(notes) == 1 and notes[0]["parents"][-1] is panel,
                "Workbook source note moved outside its panel")
        note = notes[0]
        anchors = [n for n in nodes if n["tag"] == "a" and note in n["parents"]]
        require(len(anchors) == 1 and anchors[0]["attrs"] ==
                {"data-payer-source": sid, "href": URLS[1 if sid == "hmrc" else 4]} and
                "".join(anchors[0]["text"]) == link_text,
                "Adjacent workbook link identity changed")
        require(not any("hidden" in p["attrs"] or p["attrs"].get("aria-hidden") == "true" or
                        p["tag"] == "details" or
                        re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", p["attrs"].get("style", ""))
                        for p in [note, anchors[0]] + note["parents"]), "Adjacent source link hidden")
        captions = [n for n in nodes if n["tag"] == "caption" and n["attrs"].get("id") in table_ids]
        require(len(captions) == len(table_ids) and all(panel in n["parents"] and nodes.index(n) < nodes.index(note)
                                                     for n in captions), "Source note must follow its panel tables")
        details = [n for n in nodes if n["tag"] == "details" and n["attrs"].get("id") == sid + "-sources"]
        require(len(details) == 1 and details[0]["parents"][-1] is source_section, "Source details moved outside final source section")
        downloads = [n for n in nodes if n["tag"] == "a" and details[0] in n["parents"]]
        require(len(downloads) == 1 and downloads[0]["attrs"] ==
                {"data-payer-source": sid, "href": URLS[1 if sid == "hmrc" else 4]} and
                "".join(downloads[0]["text"]) == "Download the original workbook",
                "Source-details workbook link changed")
        detail_intro = [" ".join("".join(n["text"]).split()) for n in nodes
                        if n["tag"] == "p" and n["parents"][-1] is details[0]]
        source = data["sources"][sid]
        require(f'{source["publication"]}; published {source["published"]}. Unit: %. Geography: UK. '
                'Values use the published cells, not sums of rounded parts.' in detail_intro and
                'Source SHA-256: ' + source["sha256"] in detail_intro,
                "Source-details publication, date, unit, geography or hash changed")
        rendered_cells = [" ".join("".join(n["text"]).split()) for n in nodes
                          if n["tag"] == "li" and details[0] in n["parents"]]
        expected_cells = [f'{v["group"]}: {v["measure"]} — {v["sheet"]}!{v["cell"]}. '
                          f'Denominator: {v["denominator"]}.' for v in data["values"] if v["source_id"] == sid]
        require(rendered_cells == expected_cells, "Source-details cell list changed")
        rendered_notes = [" ".join("".join(n["text"]).split()) for n in nodes
                          if details[0] in n["parents"] and n["tag"] == "p" and
                          "payer-source-cell" in n["attrs"].get("class", "").split()]
        expected_notes = []
        for cell in data["source_cells"].values():
            if cell["source_id"] == sid and (cell["sheet"] in {"Notes", "Cover sheet"} or
                    (cell["sheet"] == "Contents" and cell["cell"] in {"A4", "A5"}) or
                    (cell["sheet"] == "Table 8" and cell["cell"] == "A2")):
                raw = cell["text"] if cell["text"] is not None else cell["value"]
                expected_notes.append(" ".join(f'{cell["sheet"]}!{cell["cell"]}: {raw}'.split()))
        require(rendered_notes == expected_notes, "Rendered source notes changed")
    links = {n["attrs"].get("href") for n in document.nodes if n["tag"] == "a"}
    require(set(URLS) <= links and {"data/payers.json", "index.html", "taxes.html", "who-pays.html", "methods.html"} <= links,
            "Source/download/navigation links missing")
    require(not any(n["tag"] == "nav" for n in nodes), "Page callback owns the main navigation")
    bars = [n for n in nodes if "data-payer-bar" in n["attrs"]]
    bar_ids = {"hmrc-bottom50", "hmrc-top10", "hmrc-top1"} | {f"ons-{i}-combined" for i in range(1, 6)}
    require(len(bars) == 8 and {b["attrs"]["data-payer-bar"] for b in bars} == bar_ids, "Chart identities changed")
    bar_labels = [n for n in nodes if "data-payer-bar-label" in n["attrs"]]
    require(len(bar_labels) == 8 and {n["attrs"]["data-payer-bar-label"] for n in bar_labels} == bar_ids,
            "Bar value label identities changed")
    for bar in bars:
        entry = by_id[bar["attrs"]["data-payer-bar"]]
        require(bar["attrs"].get("style") == f'width:{entry["value"]}%', "Bar width differs from source")
        chart = next((p for p in reversed(bar["parents"]) if "data-chart-denominator" in p["attrs"]), None)
        require(chart and chart["attrs"]["data-chart-denominator"] == entry["denominator"], "Bar denominator changed")
        label = next(n for n in bar_labels if n["attrs"]["data-payer-bar-label"] == entry["id"])
        require(label["tag"] == "span" and label["attrs"].get("class") == "payer-bar-value" and
                "".join(label["text"]) == f'{entry["value"]:.1f}%', "Bar value label differs from source")
        require(chart in label["parents"] and len(label["parents"]) >= 2 and
                label["parents"][-2] is bar["parents"][-2], "Bar value label moved away from its bar")
        heading = label["parents"][-1]
        require(heading["attrs"].get("class") == "payer-bar-heading" and
                entry["group"] in "".join(heading["text"]), "Bar value label lacks its group label")
        require(not any("hidden" in p["attrs"] or p["tag"] == "details" or
                        re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", p["attrs"].get("style", "")) or
                        (p["attrs"].get("aria-hidden") == "true" and p is not chart)
                        for p in [label] + label["parents"]), "Bar value label hidden")
    # Required limits must remain outside collapsed source details.
    def concealed(node):
        return any(p["tag"] == "details" or "hidden" in p["attrs"] or
                   p["attrs"].get("aria-hidden") == "true" or
                   re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", p["attrs"].get("style", ""))
                   for p in [node] + node["parents"])

    visible = " ".join(" ".join(n["text"]) for n in nodes if n["tag"] == "p" and not concealed(n))
    visible = " ".join(visible.split())
    for phrase in (
        "The top 1% is part of the top 10%", "The top 10% is part of the top 50%",
        "The bottom 50% and top 10% do not overlap",
        "taxpayers with a positive Income Tax bill, not all adults", "Do not add their shares",
        "Tax due is not cash collected", "tax year 2023 to 2024",
        "equivalised household disposable income", "household size and needs",
        "People with no Income Tax bill are excluded", "before deductions and allowances",
        "not households", "not the HMRC taxpayer groups", "private households", "not a forecast",
        "Gross income includes cash benefits", "Disposable income is gross income after direct taxes",
        "high gross income but low disposable income", "Deferred lump-sum tax payments",
        "savings or borrowing", "Temporary low income, sampling and measurement issues",
        "not a tax rate on purchases or a lifetime tax burden", "household expenditure, not income",
        "include student-loan repayments", "Corporation Tax is not allocated",
        "final and intermediate indirect taxes fully to consumers", "employer National Insurance",
        "Employee and self-employed National Insurance are direct taxes", "producers, workers, buyers and others",
        "FYE 2019", "25 June 2020", "Sections 7 and 10", "15 June 2018",
        "Current workbook notes take priority", "not a measure of all UK taxes",
        "not be mapped wholly to either ONS group", "Do not combine them",
    ):
        require(phrase in visible, "Missing visible fiscal limit: " + phrase)
    bottom = next((n for n in nodes if n["attrs"].get("id") == "bottom-group"), None)
    require(bottom is not None and not concealed(bottom), "Bottom-group warning hidden")
    ons_scope = next((n for n in nodes if n["tag"] == "h3" and "".join(n["text"]) ==
                      "Direct and indirect taxes counted in this ONS analysis"), None)
    require(ons_scope is not None and bottom["parents"][-1] is ons_scope["parents"][-1] and
            nodes.index(ons_scope) < nodes.index(bottom) < min(nodes.index(b) for b in bars
                                                            if b["attrs"]["data-payer-bar"].startswith("ons-")),
            "Bottom-group warning must follow ONS scope and precede the bars")
    scope_index = nodes.index(ons_scope)
    scope_siblings = [n for n in nodes[scope_index + 1:] if n["parents"] and
                      n["parents"][-1] is ons_scope["parents"][-1]]
    require(scope_siblings and scope_siblings[0] is bottom,
            "Bottom-group warning must directly follow ONS scope")
    overlap = next((n for n in nodes if n["attrs"].get("id") == "overlap"), None)
    require(overlap is not None and not concealed(overlap) and " ".join("".join(overlap["text"]).split()) ==
            "The top 1% is part of the top 10%. The top 10% is part of the top 50%. "
            "The bottom 50% and top 10% do not overlap. "
            "These groups refer to taxpayers with a positive Income Tax bill, not all adults. "
            "Do not add their shares. Tax due is not cash collected. This is Income Tax only, not all UK taxes.",
            "Shown HMRC group relationship changed")
    require(any(n["tag"] == "h3" and "".join(n["text"]) ==
                "Direct and indirect taxes counted in this ONS analysis" and not concealed(n) for n in nodes),
            "ONS tax scope heading changed or hidden")
    require(all(not concealed(n) for n in nodes if n["tag"] == "h2"), "Payer heading hidden")
    # Permit the checked nesting explanation, but no extra top-50 claims or figures.
    claims = visible.replace("The top 10% is part of the top 50%.", "", 1)
    require(not re.search(r"(?:top 50%|groups are disjoint|groups do not overlap|non-overlapping groups|share of all UK taxes|all-tax rate)", claims, re.I),
            "Unsupported overlap or all-tax claim")
    require(not any(token in text for token in ("36.7 million", "36,700,000", "data/payers/raw/", "original_response", "/home/")),
            "Unapproved count or raw/private source leak")
    return True
