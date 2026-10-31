"""Check the built site against the raw spreadsheets and the rubric's automated rules.

Exits non-zero if any figure on a page does not match the cell it names, if banned
evaluative words appear, if colours outside the neutral palette are used, if a page
is over the size limit, or if the reading level is above the target.
"""

import json
import hashlib
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from openpyxl import load_workbook

from check_fiscal import RawReader, pesa_forecast_date, validate_fiscal
from fiscal_contract import selections
from check_taxes import validate as validate_taxes, checked_forecast_prose
from check_payers import validate_data as validate_payer_data, validate_page as validate_payer_page, Page as SemanticPage, raw_cells as payer_raw_cells
from check_basics import validate_sources as validate_basics_sources, validate_fragments as validate_basics_fragments

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MAX_BYTES = 500_000
MAX_GRADE = 7.0

# Evaluative words that frame numbers as good or bad. Matched as whole words.
BANNED = """
massive huge enormous staggering whopping eye-watering soaring skyrocketing ballooning spiralling
slashed savage brutal crippling draconian austerity reckless profligate wasteful bloated lavish
generous meagre paltry pitiful measly shocking scandalous disastrous catastrophic crisis-hit
failing failed broken record-breaking unprecedented alarming worrying sadly unfortunately
thankfully finally only merely just mere
""".split()
# "only" and "just" are fine in instructions ("only total spending after ..."), so they
# are allowed when they are not next to a number.
CONTEXT_ONLY = {"only", "just", "merely", "mere"}

PALETTE = {"#1f2937", "#4b5563", "#e5e7eb", "#f3f4f6", "#6b7280", "#fff", "#ffffff", "none"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.figures, self.text, self.paras = [], [], []
        self.section_ids = set()
        self._skip = 0
        self._names = []  # open tags that hold proper names, left out of the reading score
        self._fig = None
        self._para = None
        self.date_labels = []
        self._date_label = None
        self._date_span_depth = 0
        self.unmarked_text = []

    def text_boundary(self, tag):
        # Keep inline text contiguous (including split words), but preserve the
        # visible separation of blocks and line breaks for prose date checks.
        if not self._skip and tag in (
                "address", "article", "aside", "blockquote", "body", "br",
                "caption", "dd", "details", "dialog", "div", "dl", "dt",
                "fieldset", "figcaption", "figure", "footer", "form", "h1",
                "h2", "h3", "h4", "h5", "h6", "header", "hgroup", "hr",
                "li", "main", "menu", "nav", "ol", "p", "pre", "search",
                "section", "summary", "table", "tbody", "td", "tfoot", "th",
                "thead", "tr", "ul"):
            self.unmarked_text.append(" ")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.text_boundary(tag)
        if tag == "span":
            marked = a.get("data-pesa-forecast-date") == "1"
            if marked and self._date_label is not None:
                raise ValueError("Independent PESA nested forecast date marker")
            if self._date_label is not None:
                self._date_span_depth += 1
            elif marked:
                self._date_label = []
                self._date_span_depth = 1
        if tag == "section" and a.get("id"):
            self.section_ids.add(a["id"])
        if tag in ("script", "style", "svg"):
            self._skip += 1
        classes = (a.get("class") or "").split()
        if tag not in ("br", "img", "input", "meta", "link"):
            self._names.append(tag == "cite" or "name" in classes or "official" in classes)
        if tag == "data":
            self._fig = {"value": a.get("value"), "ref": a.get("data-ref"), "calc": a.get("data-calc"),
                         "tax_id": a.get("data-tax-id"), "payer_id": a.get("data-payer-id"), "value_id": a.get("data-value-id"), "derived_id": a.get("data-derived-id"),
                         "report_id": a.get("data-report-id"), "report_field": a.get("data-report-field"),
                         "title": a.get("title"), "text": ""}
        if tag in ("p", "dd", "li") and not self._skip:
            self._para = []

    def handle_endtag(self, tag):
        self.text_boundary(tag)
        if tag == "span" and self._date_label is not None:
            self._date_span_depth -= 1
            if self._date_span_depth == 0:
                self.date_labels.append("".join(self._date_label))
                self._date_label = None
        if tag not in ("br", "img", "input", "meta", "link") and self._names:
            self._names.pop()
        if tag in ("script", "style", "svg"):
            self._skip -= 1
        if tag == "data" and self._fig is not None:
            self.figures.append(self._fig)
            self._fig = None
        if tag in ("p", "dd", "li") and self._para is not None:
            self.paras.append(" ".join(self._para))
            self._para = None

    def handle_data(self, data):
        if self._date_label is not None:
            self._date_label.append(data)
        if self._skip:
            return
        if self._date_label is None:
            self.unmarked_text.append(data)
        self.text.append(data)
        if self._fig is not None:
            self._fig["text"] += data
        if self._para is not None and not any(self._names):
            self._para.append(data)


def cells():
    manifest = ROOT / "data/sources.json"
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != "5e7ebb343bee091960052b1727bf7bff6997216e8a5bf7805d18770aa7d5914a":
        raise ValueError("Source catalogue differs from the pinned seed")
    sources = json.loads(manifest.read_text())
    for source in sources.values():
        path = ROOT / source["file"]
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Source hash mismatch: {source['file']}")
    owner = {sheet: src for src in sources.values() for sheet in src["sheets"]}
    books = {}

    def read(ref):
        sheet, cell = ref.rsplit("!", 1)
        src = owner[sheet]
        if src["file"] not in books:
            books[src["file"]] = load_workbook(ROOT / src["file"], read_only=False, data_only=True)
        v = books[src["file"]][sheet][cell].value
        if v is None or (isinstance(v, str) and v.strip() in ("-", "")):
            return None
        v = float(v)
        if not math.isfinite(v):
            raise ValueError(f"Non-finite source cell: {ref}")
        return v * src["scale"]
    return read


def syllables(word):
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups) - (1 if word.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def grade(paras):
    words = sents = syl = 0
    for p in paras:
        p = re.sub(r"£?\d[\d,]*(\.\d+)?(-\d+)?(bn|%)?", "N", p)
        ws = re.findall(r"[A-Za-z][A-Za-z'-]*|N", p)
        if len(ws) < 4:
            continue
        words += len(ws)
        sents += max(1, len(re.findall(r"[.!?:](\s|$)", p)))
        syl += sum(1 if w == "N" else syllables(w) for w in ws)
    if not words or not sents:
        raise ValueError("No prose found for the reading-grade check")
    return 0.39 * words / sents + 11.8 * syl / words - 15.59


def check_pesa_dates(raw, data, read, name):
    """Validate prose and every forecast tooltip against separately read notes."""
    date = pesa_forecast_date(read)
    page = Page()
    page.feed(raw)
    if page.date_labels != ([date, date] if name == "index.html" else []):
        raise ValueError(f"Independent PESA rendered date/vintage mismatch: {name}")
    # Date spans and tooltips are not the only places a stale literal can appear.
    # Check visible prose on every page, including pages with no required spans.
    unmarked = "".join(page.unmarked_text)
    # Preserve the original unconditional current-source-date guard, regardless
    # of nearby wording (including publication/archive/projection claims).
    if date in " ".join(unmarked.split()):
        raise ValueError(f"Independent PESA unmarked forecast date/vintage: {name}")
    prose_date = r"\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
    for sentence in re.split(r"(?<=[.!?])\s+", unmarked):
        if not re.search(prose_date, sentence, re.I):
            continue
        # On these spending pages, forecast-note / Economic and fiscal outlook
        # dates are PESA claims and must use the independently checked markers.
        # Other dates alone are not such claims. OBR/history keywords never
        # exempt a dated forecast claim, within or across blocks.
        outlook = re.search(r"\beconomic\s+and\s+fiscal\s+outlook\b", sentence, re.I)
        forecast = re.search(r"\bforecasts?\b", sentence, re.I)
        if outlook or forecast:
            raise ValueError(f"Independent PESA unmarked forecast date/vintage: {name}")
    forecast_ids = {key for key, meta in data["provenance"].items() if meta["status"] == "pesa_forecast"}
    label = "PESA forecast; OBR " + date + "."
    for figure in page.figures:
        if figure["value_id"] in forecast_ids and not (figure["title"] or "").endswith(label):
            raise ValueError(f"Independent PESA tooltip date/vintage mismatch: {name}")


def validate(site=SITE):
    independent_basics_checks(site)
    read = cells()
    errors, report = [], []
    if not (site / "index.html").is_file():
        raise ValueError("index.html: missing spending page")
    independent_data_checks(site, read)
    tax_data = validate_taxes(site)
    payer_data = independent_payer_checks(site)
    payer_ids = {v["id"] for v in payer_data["values"]}
    data = json.loads((site / "data/spending.json").read_text())
    raw_fiscal = RawReader()
    nodes = {node["value_id"]: node for node, _ in selections(data)}
    reports = {r["id"]: r for r in data["reconciliations"]}
    if not (site / "methods.html").is_file():
        errors.append("methods.html: missing methods page")
    for path in sorted(site.glob("*.html")):
        raw = path.read_text()
        name = path.name
        date_raw = checked_forecast_prose(raw, tax_data) if name == "taxes.html" else raw
        check_pesa_dates(date_raw, data, raw_fiscal, name)
        p = Page()
        p.feed(raw)
        if name == "methods.html":
            check_guidance_methods(raw)
            for section_id in ("about", "corrections", "payer-methods", "tax-guidance"):
                if section_id not in p.section_ids:
                    errors.append(f"{name}: missing section id={section_id!r}")

        size = path.stat().st_size
        if size > MAX_BYTES:
            errors.append(f"{name}: {size} bytes is over the {MAX_BYTES} limit")

        if name == "index.html":
            check_spending_comparison(raw, data)
            for section_id in ("answers", "hundred", "items", "total", "decades", "areas"):
                if section_id not in p.section_ids:
                    errors.append(f"{name}: missing product section {section_id}")
            if not p.figures:
                errors.append(f"{name}: no sourced figures")

        for f in p.figures:
            if f["payer_id"]:
                # The independent payer checker binds exact attributes, visible
                # text, table labels and bar widths to reopened original cells.
                if name != "who-pays.html" or f["payer_id"] not in payer_ids or any(
                        f[key] is not None for key in
                        ("tax_id", "value_id", "derived_id", "report_id", "report_field", "calc")):
                    errors.append(f"{name}: payer figure outside its verified page or mixed fiscal identities")
                continue
            if f["tax_id"]:
                # validate_taxes has independently reopened the current workbook
                # and checked every tax figure's exact attributes AND signed text.
                # Tax nodes cannot acquire a legacy identity or move to another page.
                if name != "taxes.html" or f["tax_id"] not in tax_data["nodes"]:
                    errors.append(f"{name}: tax figure outside its verified page")
                continue
            if not f["ref"]:
                errors.append(f"{name}: figure {f['text']!r} has no source reference")
                continue
            shown = float(f["value"])
            if not math.isfinite(shown):
                errors.append(f"{name}: non-finite displayed value")
                continue
            if f["value_id"] in nodes and not f["derived_id"] and not f["report_id"]:
                node = nodes[f["value_id"]]
                expect, refs, calc = node["v"], node["ref"], None
            elif f["derived_id"] in data["derived"] and not f["value_id"] and not f["report_id"]:
                node = data["derived"][f["derived_id"]]
                expect = node["v"]
                refs = " ".join(data["provenance"][key]["ref"] for key in node["operands"])
                calc = node["formula"]
            elif f["report_id"] in reports and not f["value_id"] and not f["derived_id"]:
                node = reports[f["report_id"]]
                if f["report_field"] not in ("residual", "quantisation_budget"):
                    errors.append(f"{name}: unknown reconciliation field")
                    continue
                expect = node[f["report_field"]]
                refs = " ".join(o["ref"] for o in node["operands"])
                calc = "reconciliation"
            else:
                errors.append(f"{name}: figure lacks a valid semantic value/formula identity")
                continue
            if f["ref"] != refs or f["calc"] != calc:
                errors.append(f"{name}: source cells or formula do not match fiscal identity")
                continue
            if expect is None or abs(shown - expect) > 0.000051:
                errors.append(f"{name}: {f['text']!r} does not match verified fiscal value {expect}")
            nums = re.findall(r"-?[\d,]+\.?\d*", f["text"])
            if nums:
                text_v = float(nums[0].replace(",", ""))
                decimals = len(nums[0].split(".")[1]) if "." in nums[0] else 0
                if abs(abs(text_v) - abs(shown)) > 0.5 * 10 ** -decimals + 1e-3:
                    errors.append(f"{name}: text {f['text']!r} does not show value {shown}")

        text = " ".join(p.text)
        for w in BANNED:
            for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.I):
                if w in CONTEXT_ONLY:
                    around = text[max(0, m.start() - 4): m.end() + 6]
                    if not re.search(r"\d|£", around):
                        continue
                errors.append(f"{name}: evaluative word {w!r} in {text[max(0, m.start() - 30): m.end() + 30]!r}")

        for c in set(re.findall(r'(?:fill|stroke|color|background)\s*[:=]\s*"?(#[0-9a-fA-F]{3,6})', raw)):
            if c.lower() not in PALETTE:
                errors.append(f"{name}: colour {c} is outside the neutral palette")

        g = grade(p.paras)
        if g > MAX_GRADE:
            errors.append(f"{name}: reading grade {g:.1f} is above {MAX_GRADE}")
        report.append(f"{name}: {len(p.figures)} figures checked against source cells, "
                      f"reading grade {g:.1f}, {size // 1000} KB")

    print("\n".join(report))
    if errors:
        print("\n".join("FAIL " + e for e in errors))
        sys.exit(1)
    print("all checks passed")


def check_spending_comparison(raw, data):
    """Bind the two source vintages to the headline, before its first chart."""
    def require(ok, message):
        if not ok:
            raise ValueError("Spending comparison: " + message)
    def text(node):
        return " ".join("".join(node["text"]).split())
    document = SemanticPage(raw)
    def unique(identifier):
        found = [n for n in document.nodes if n["attrs"].get("id") == identifier]
        require(len(found) == 1, "missing or duplicate " + identifier)
        return found[0]
    section = unique("decades")
    headline = unique("decade-spending-headline")
    note = unique("spending-vintage-note")
    require(section["tag"] == "section" and section["parents"] and section["parents"][-1]["tag"] == "main",
            "decade section misplaced")
    children = [n for n in document.nodes if n["parents"] and n["parents"][-1] is section]
    require(headline["tag"] == note["tag"] == "p" and headline in children and note in children and
            children.index(note) == children.index(headline) + 1,
            "vintage note must immediately follow the spending headline")
    charts = [n for n in document.nodes if section in n["parents"] and n["tag"] == "svg"]
    require(charts and document.nodes.index(note) < document.nodes.index(charts[0]),
            "vintage note must precede the decade charts")
    descendants = [n for n in document.nodes if note in n["parents"]]
    require(headline["attrs"] == {"id": "decade-spending-headline"} and
            note["attrs"] == {"id": "spending-vintage-note"}, "comparison paragraph attributes changed")
    # Exact contracts reject all undeclared attributes, including unknown classes
    # that a stylesheet could conceal. Browser checks separately inspect paint.
    shell = {"html": ({"lang": "en-GB"},),
             "body": ({"class": "view-real nojs"}, {"class": "view-real"}),
             "main": ({"id": "main"},), "section": ({"id": "decades"},)}
    require([n["tag"] for n in note["parents"]] == ["html", "body", "main", "section"] and
            headline["parents"] == note["parents"], "comparison ancestor structure changed")
    for ancestor in note["parents"]:
        require(ancestor["attrs"] in shell[ancestor["tag"]], "comparison ancestor attributes changed")
    for paragraph in (headline, note):
        for node in (n for n in document.nodes if paragraph in n["parents"]):
            allowed = (node["tag"] == "cite" and paragraph is note and not node["attrs"]) or (
                node["tag"] == "data" and set(node["attrs"]) ==
                {"value", "data-value-id", "data-ref", "title"} and bool(node["attrs"]["title"]))
            require(allowed and node["parents"][-1] is paragraph,
                    "comparison descendant attributes or structure changed")
    year = data["latest_year"]
    spending = next(row for row in data["history"]["totals"] if row["id"] == "spending")["values"][year]
    pesa = next(row for row in data["aggregates"] if row["year"] == year)["tme"]["gdp"]
    first = data["history"]["decades"][0]
    first_spending = next(row for row in data["history"]["totals"] if row["id"] == "spending")["values"][first]
    headline_figures = [n for n in document.nodes if headline in n["parents"] and n["tag"] == "data"]
    require([n["attrs"].get("data-value-id") for n in headline_figures] ==
            [first_spending["value_id"], spending["value_id"]] and
            text(headline) == f'In {first}, spending was {first_spending["v"]:.1f}% of GDP. '
            f'In {year} it was {spending["v"]:.1f}%. '
            'When spending is more than receipts, the government borrows the gap.',
            "spending headline or its source identities changed")
    figures = [n for n in descendants if n["tag"] == "data"]
    require(len(figures) == 2, "both source-backed GDP shares are required")
    for node, source in zip(figures, (spending, pesa)):
        require(node["attrs"].get("data-value-id") == source["value_id"] and
                node["attrs"].get("data-ref") == source["ref"] and
                node["attrs"].get("value") == str(source["v"]) and text(node) == f'{source["v"]:.1f}%',
                "vintage figure source identity changed")
    expected = (f'For {year}, OBR, October 2026 shows {spending["v"]:.1f}% of GDP. '
                f'HM Treasury, PESA 2026 shows {pesa["v"]:.1f}%. '
                'These use different vintages and GDP bases. They are not directly comparable. '
                'The gap is not a change in spending.')
    require(text(note) == expected, "vintage explanation changed")
    prose = text(section)
    require("fairest" not in prose.lower() and "A GDP share can rise when GDP falls." in prose,
            "neutral comparison or GDP caveat changed")
    require(not re.search(r"\bincome\b", prose, re.I), "receipts must not be labelled income")
    require(any(n["tag"] == "h3" and text(n) == "Spending and receipts" for n in children),
            "receipts heading changed")
    # Node text does not insert boundaries between adjacent table cells. Bind
    # the actual headers, not a whole-section word search such as Income.
    captions = [n for n in document.nodes if section in n["parents"] and n["tag"] == "caption" and
                text(n) == f"Spending, receipts, borrowing and debt, share of GDP, {first} to {year}"]
    require(len(captions) == 1 and captions[0]["parents"][-1]["tag"] == "table",
            "decade receipts table missing or changed")
    table = captions[0]["parents"][-1]
    require([text(n) for n in document.nodes if table in n["parents"] and n["tag"] == "th" and
             n["attrs"].get("scope") == "col"] == ["Year", "Spending", "Receipts", "Borrowing", "Debt"],
            "decade receipts table headers changed")
    return True


def independent_basics_checks(site, root=None):
    """Check retained guidance and marked fragments in actual published HTML."""
    root = ROOT if root is None else Path(root)
    site = Path(site)
    validate_basics_sources(root)
    pages = []
    for name in ("taxes.html", "who-pays.html"):
        path = site / name
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
            raise ValueError("Basics publication must contain regular HTML files")
        if path.stat().st_size >= MAX_BYTES:
            raise ValueError("Basics publication exceeds page size limit")
        pages.append(path.read_text(encoding="utf-8"))
    result = validate_basics_fragments(*pages, root=root)
    path = site / "methods.html"
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Guidance methods must be a regular HTML file")
    methods = path.read_text(encoding="utf-8")
    check_guidance_methods(methods, root=root)
    check_ons_glossary(methods, root=root)
    return result


def check_ons_glossary(raw, root=None):
    """Bind the Methods definitions to their own retained ONS evidence."""
    root = ROOT if root is None else Path(root)
    def require(ok, message):
        if not ok:
            raise ValueError("ONS glossary: " + message)
    def text(node):
        return " ".join("".join(node["text"]).split())
    document = SemanticPage(raw)
    definitions = [n for n in document.nodes if n["attrs"].get("id") == "ons-tax-definitions"]
    require(len(definitions) == 1, "missing or duplicate definitions")
    definition = definitions[0]
    require(definition["tag"] == "dd" and definition["attrs"] == {"id": "ons-tax-definitions"} and
            [n["tag"] for n in definition["parents"]] == ["html", "body", "main", "dl"],
            "definition structure changed")
    shell = {"html": ({"lang": "en-GB"},),
             "body": ({"class": "view-real nojs"}, {"class": "view-real"}),
             "main": ({"id": "main"},), "dl": ({"id": "fiscal-glossary"},)}
    require(all(n["attrs"] in shell[n["tag"]] for n in definition["parents"]),
            "ancestor attributes changed")
    nodes = [n for n in document.nodes if definition in n["parents"]]
    paragraphs = [n for n in nodes if n["tag"] == "p"]
    require([n["tag"] for n in nodes] == ["p", "p", "a", "a"] and
            all(n["parents"][-1] is definition and not n["attrs"] for n in paragraphs),
            "definition markup or attributes changed")
    copy = ("ONS takes direct taxes, such as Income Tax and Council Tax after benefits or rebates, from household income. "
            "Indirect taxes are paid through spending, such as VAT and duty on alcohol or fuel. "
            "Final taxes are on goods and services bought for household use. "
            "Intermediate taxes are on goods and services firms use to make other goods and services. "
            "In this model, ONS assumes firms pass the full cost of intermediate taxes to buyers in prices.")
    require(text(paragraphs[0]) == copy and text(paragraphs[1]) ==
            "Sources: ONS FYE 2024 glossary; ONS FYE 2019 technical report, section 7", "definition copy changed")
    siblings = [n for n in document.nodes if n["parents"] and n["parents"][-1] is definition["parents"][-1]]
    position = siblings.index(definition)
    require(position > 0 and siblings[position - 1]["tag"] == "dt" and not siblings[position - 1]["attrs"] and
            text(siblings[position - 1]) == "Direct and indirect taxes in this ONS analysis", "glossary label changed")
    sources = (
        ("ons_bulletin", "ons-bulletin-2024.html.json", "438d846bff86d243b4b0d9aca02a60a730e8356eeba2ea99dd92322497c77566",
         "3ea7d0ca5d0461f9f8f1759ec96b0203358fdebd10a59afc60c3b4eb3582bfcc",
         "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024",
         "glossary", "Glossary: Stages in the redistribution of income", "ONS FYE 2024 glossary", "Stages in the redistribution of income", (
             "direct taxes include deductions such as Income Tax, National Insurance contributions, student loan repayments and Council Tax (less Council Tax benefits or rebates)",
             "indirect taxes are then paid via expenditure",
             "indirect taxes refer to those on goods and services such as Value Added Tax (VAT), duty on tobacco, alcohol and fuel, and Stamp Duty")),
        ("ons_method", "ons-technical-2019.html.json", "333f37418a495e5f46b724f6366001330f1d5b42462e2954bd2749ab1907f8f1",
         "2822bc0a9f9f1c214f9fdf37d5aa1c2a4c31122fd09919af7324c3c95f1b2f15",
         "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/articles/theeffectsoftaxesandbenefitsonhouseholdincome/financialyearending2019",
         "post-tax-income", "7. Post-tax income", "ONS FYE 2019 technical report, section 7", "7. Post-tax income", (
             "Final goods and services are those that are sold to final users (in this case household consumers)",
             "intermediate goods are those that are used in the production of final goods",
             "In this analysis only taxes on goods and services consumed by households are included",
             "We assume that companies pass on the full cost of intermediate taxes to the consumer in the price of the final good")),
    )
    for anchor, (sid, filename, stored_hash, body_hash, url, fragment, locator, label, heading, quotes) in zip(nodes[2:], sources):
        require(anchor["parents"][-1] is paragraphs[1] and anchor["attrs"] ==
                {"data-definition-source": sid, "data-locator": locator, "href": url + "#" + fragment} and
                text(anchor) == label, "source URL or locator changed")
        path = root / "data/payers/raw" / filename
        require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink in retained source")
        blob = path.read_bytes()
        require(hashlib.sha256(blob).hexdigest() == stored_hash, "retained source hash changed")
        original = json.loads(blob)["original_response"]
        require(hashlib.sha256(original.encode("utf-8")).hexdigest() == body_hash, "original source hash changed")
        evidence = SemanticPage(original)
        sections = [n for n in evidence.nodes if n["attrs"].get("id") == fragment]
        require(len(sections) == 1, "source section changed")
        section = sections[0]
        require(any(text(n) == heading for n in evidence.nodes if section in n["parents"] and
                    n["tag"] in {"h2", "h3", "h4"}) and all(q in text(section) for q in quotes),
                "source heading or evidence changed")
    workbook = root / "data/payers/raw/ons-etb-fye2024.xlsx"
    require(not any(p.is_symlink() for p in (workbook, *workbook.parents)) and
            hashlib.sha256(workbook.read_bytes()).hexdigest() ==
            "2e38c1694d922427509879b9553a4c3473b8ba1174898c2dd414668ecbb2bf73", "example workbook hash changed")
    read = payer_raw_cells(root)
    for address, label in (("B5", "Direct taxes"), ("C6", "Income Tax"),
                           ("C8", "Council Tax and Northern Ireland rates"), ("B9", "Indirect taxes"),
                           ("C10", "Value Added Tax (VAT)"), ("C11", "Duty on alcohol"),
                           ("C13", "Duty on hydrocarbon oils and Vehicle Excise Duty")):
        require(read("ons", "Table 8", address)["value"] == label, "example source label changed: " + address)
    return True


def check_guidance_methods(raw, root=None):
    """Bind the published guidance record to independently checked source bytes."""
    root = ROOT if root is None else Path(root)
    validate_basics_sources(root)
    register = json.loads((root / "data/tax-basics/sources.json").read_text(encoding="utf-8"))
    # Independent locator map: do not import the renderer or its source ordering.
    locators = {
        "income-tax": "Income Tax: Overview; Income Tax allowances and reliefs",
        "national-insurance": "National Insurance: Overview; Who pays National Insurance; National Insurance classes",
        "paye-remitter": "PAYE for employers: Introduction to PAYE; Deductions from their pay; Reporting pay and deductions; Paying HMRC",
        "scottish-powers": "Scottish Government: Income Tax",
        "vat": "How VAT works: Overview; Your responsibilities as a VAT-registered business; What VAT is charged on; How much VAT you must charge",
        "welsh-income-tax": "Welsh Income Tax: Income Tax in Wales; Who pays the Welsh rates; How you pay",
        "corporation-tax": "Corporation Tax: Overview; Profits you pay Corporation Tax on",
    }
    def require(ok, message):
        if not ok:
            raise ValueError("Guidance methods: " + message)
    def text(node):
        return " ".join("".join(node["text"]).split())
    def concealed(node):
        return any("hidden" in p["attrs"] or p["attrs"].get("aria-hidden", "").lower() == "true" or
                   set(p["attrs"].get("class", "").split()) & {"v", "narrow", "wide"} or
                   re.search(r"display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)",
                             p["attrs"].get("style", ""), re.I)
                   for p in [node] + node["parents"])
    document = SemanticPage(raw)
    sections = [n for n in document.nodes if n["attrs"].get("id") == "tax-guidance"]
    require(len(sections) == 1, "missing or duplicated section")
    section = sections[0]
    require(section["tag"] == "section" and section["attrs"].get("data-pid") == "tax-guidance-methods" and
            section["parents"] and section["parents"][-1]["tag"] == "main" and
            not concealed(section) and not any(p["tag"] == "details" for p in section["parents"]),
            "section hidden or misplaced")
    shell = {"html": {"lang": {"en-GB"}},
             "body": {"class": {"view-real nojs", "view-real"}}, "main": {"id": {"main"}}}
    for ancestor in section["parents"]:
        allowed = shell.get(ancestor["tag"])
        require(allowed is not None and set(ancestor["attrs"]) <= set(allowed) and
                all(value in allowed[key] for key, value in ancestor["attrs"].items()),
                "ancestor attributes changed")
    require(section["attrs"] == {"id": "tax-guidance", "data-pid": "tax-guidance-methods"},
            "section attributes changed")
    nodes = [n for n in document.nodes if section in n["parents"]]
    # Every methods descendant has a small explicit attribute contract too.
    for node in nodes:
        attrs, tag = node["attrs"], node["tag"]
        if tag == "li":
            allowed = set(attrs) == {"data-guidance-source"} and attrs["data-guidance-source"] in locators
        elif tag == "a":
            allowed = set(attrs) == {"href"}
        elif tag in {"p", "ul"}:
            allowed = not attrs or attrs == {"class": "small" if tag == "p" else "name"}
        else:
            allowed = tag in {"h2", "details", "summary", "code"} and not attrs
        require(allowed, "descendant attributes changed")
    headings = [n for n in nodes if n["tag"] in {"h1", "h2", "h3"}]
    require(len(headings) == 1 and headings[0]["tag"] == "h2" and
            text(headings[0]) == "Where the tax definitions come from" and not concealed(headings[0]),
            "heading changed or hidden")
    intros = [n for n in nodes if n["tag"] == "p" and n["parents"][-1] is section]
    require([text(n) for n in intros] == [
        "Official guidance explains the tax rules. It is not the source of the household percentages or receipt totals. "
        "We checked these guidance pages on 30 October 2026. They are living guidance; no publication date is established. "
        "The next update is unknown. We use no current rates or personal tax examples.",
        "These are our summaries of official guidance, not quotations. "
        "The short definitions link to the official page and name the relevant heading. "
        "The OBR group limits and ONS model limits remain beside their own figures. "
        "These definitions do not describe who bears every tax cost."] and all(not concealed(n) for n in intros),
        "retrieval date, status or scope changed")
    require(register["retrieved_date_utc"] == "2026-10-30", "retrieval register changed")
    details = [n for n in nodes if n["tag"] == "details"]
    require(len(details) == 1 and details[0]["parents"][-1] is section and not concealed(details[0]),
            "missing or hidden source disclosure")
    summaries = [n for n in nodes if n["tag"] == "summary"]
    require(len(summaries) == 1 and summaries[0]["parents"][-1] is details[0] and
            text(summaries[0]) == "Guidance headings and retained file hashes" and not concealed(summaries[0]),
            "source disclosure label changed")
    rows = [n for n in nodes if n["tag"] == "li"]
    require([n["attrs"].get("data-guidance-source") for n in rows] == list(locators), "source IDs/order changed")
    sources = {Path(s["file"]).name.removeprefix("basics-").removesuffix(".html.json"): s
               for s in register["sources"]}
    require(len(register["sources"]) == 7 and set(sources) == set(locators), "source register IDs changed")
    for row, sid in zip(rows, locators):
        descendants = [n for n in nodes if row in n["parents"]]
        links = [n for n in descendants if n["tag"] == "a"]
        codes = [n for n in descendants if n["tag"] == "code"]
        source = sources[sid]
        require(details[0] in row["parents"] and not concealed(row) and len(links) == 1 and
                links[0]["attrs"] == {"href": source["url"]} and text(links[0]) == locators[sid] and
                [text(n) for n in codes] == [source["sha256"], source["stored_sha256"]] and
                text(row) == locators[sid] + "Original response SHA-256: " + source["sha256"] +
                ". Retained copy SHA-256: " + source["stored_sha256"] + "." and
                all(not concealed(n) for n in descendants), "source URL, locator or hash changed: " + sid)
    require(len([n for n in nodes if n["tag"] == "a"]) == 7, "unexpected source links")
    return True


def independent_payer_checks(site):
    """Validate published bytes independently of build-time producer checks."""
    paths = (site / "data/payers.json", site / "who-pays.html")
    for path in paths:
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
            raise ValueError("Payer publication must contain regular files")
        if path.stat().st_size >= MAX_BYTES:
            raise ValueError("Payer publication exceeds size limit")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate public payer JSON key: " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Non-finite public payer JSON: " + value)

    data = json.loads(paths[0].read_text(encoding="utf-8"),
                      object_pairs_hook=unique, parse_constant=invalid)
    validate_payer_data(ROOT, data)
    validate_payer_page(ROOT, data, paths[1].read_text(encoding="utf-8"))
    return data


def independent_data_checks(site, read):
    """Reopen raw cells without using the extraction or rendering parsers."""
    data = json.loads((site / "data/spending.json").read_text())
    if data["sources"] != json.loads((ROOT / "data/sources.json").read_text()):
        raise ValueError("Published source catalogue differs from retained catalogue")

    source = data["sources"]["pesa_ch4"]
    workbook = load_workbook(ROOT / source["file"], data_only=True, read_only=True)
    try:
        # Read pinned note coordinates directly, independently of the builder's
        # note search. Do not accept the generated date/boundary as evidence.
        notes = workbook["4_1"]
        boundary = re.search(r"up to (\d{4}-\d{2})", notes["B3"].value).group(1)
        price = notes["B51"].value
        gdp_note = notes["B52"].value
        base = re.search(r"adjusted to (\d{4}-\d{2}) price levels", price).group(1)
        date = re.search(r"outlook - ([^)]+)\)", gdp_note).group(1)
        if f"outlook - {date})" not in price:
            raise ValueError("PESA forecast notes conflict")
        expected_context = {"last_outturn": boundary, "status_ref": "4_1!B3",
                            "forecast_date": date, "forecast_ref": "4_1!B52",
                            "deflator_ref": "4_1!B51", "base_year": base}
        if data["pesa_context"] != expected_context or data["latest_year"] != boundary or data["base_year"] != base:
            raise ValueError("Independent PESA status/vintage check failed")
        if any(row["forecast"] != (row["year"] > boundary) for row in data["aggregates"]):
            raise ValueError("Independent PESA forecast boundary check failed")
    finally:
        workbook.close()
    validate_fiscal(data)
    print("Independent JSON semantic source-cell, schema and reconciliation checks passed")


def main():
    validate()


if __name__ == "__main__":
    main()
