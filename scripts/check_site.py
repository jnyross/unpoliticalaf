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

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section" and a.get("id"):
            self.section_ids.add(a["id"])
        if tag in ("script", "style", "svg"):
            self._skip += 1
        classes = (a.get("class") or "").split()
        if tag not in ("br", "img", "input", "meta", "link"):
            self._names.append(tag == "cite" or "name" in classes or "official" in classes)
        if tag == "data":
            self._fig = {"value": a.get("value"), "ref": a.get("data-ref"), "calc": a.get("data-calc"), "text": ""}
        if tag in ("p", "dd", "li") and not self._skip:
            self._para = []

    def handle_endtag(self, tag):
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
        if self._skip:
            return
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


def validate(site=SITE):
    read = cells()
    errors, report = [], []
    if not (site / "index.html").is_file():
        raise ValueError("index.html: missing spending page")
    independent_data_checks(site, read)
    if not (site / "methods.html").is_file():
        errors.append("methods.html: missing methods page")
    for path in sorted(site.glob("*.html")):
        raw = path.read_text()
        name = path.name
        p = Page()
        p.feed(raw)
        if name == "methods.html":
            for section_id in ("about", "corrections"):
                if section_id not in p.section_ids:
                    errors.append(f"{name}: missing section id={section_id!r}")

        size = path.stat().st_size
        if size > MAX_BYTES:
            errors.append(f"{name}: {size} bytes is over the {MAX_BYTES} limit")

        if name == "index.html":
            for section_id in ("answers", "hundred", "items", "total", "decades", "areas"):
                if section_id not in p.section_ids:
                    errors.append(f"{name}: missing product section {section_id}")
            if not p.figures:
                errors.append(f"{name}: no sourced figures")

        for f in p.figures:
            if not f["ref"]:
                errors.append(f"{name}: figure {f['text']!r} has no source reference")
                continue
            shown = float(f["value"])
            if not math.isfinite(shown):
                errors.append(f"{name}: non-finite displayed value")
                continue
            refs = re.findall(r"(.+?![A-Z]+[0-9]+)(?: |$)", f["ref"])
            values = [read(ref) for ref in refs]
            if not values or any(value is None for value in values):
                errors.append(f"{name}: missing source operand for {f['text']!r}")
                continue
            if f["calc"] not in (None, "share", "change"):
                errors.append(f"{name}: unknown formula {f['calc']!r}")
                continue
            if f["calc"] == "share":
                expect, tol = read(refs[0]) / read(refs[1]) * 100, 1e-3
            elif f["calc"] == "change":
                expect, tol = (read(refs[1]) - read(refs[0])) / read(refs[0]) * 100, 1e-3
            else:
                expect, tol = read(refs[0]), 0.051
            if abs(shown - expect) > tol:
                errors.append(f"{name}: {f['text']!r} is {shown} but {f['ref']} gives {expect}")
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


def independent_data_checks(site, read):
    """Reopen raw cells without using the extraction or rendering parsers."""
    data = json.loads((site / "data/spending.json").read_text())
    if data["sources"] != json.loads((ROOT / "data/sources.json").read_text()):
        raise ValueError("Published source catalogue differs from retained catalogue")

    def near(actual, expected, tolerance, label):
        if actual is None or expected is None or abs(actual - expected) > tolerance + 1e-9:
            raise ValueError(f"Independent reconciliation failed: {label}: {actual} vs {expected}")

    def walk(value):
        if isinstance(value, dict):
            if "v" in value and "ref" in value:
                raw = read(value["ref"])
                if value["v"] is None:
                    if raw is not None:
                        raise ValueError(f"Lost source value: {value['ref']}")
                else:
                    if not math.isfinite(value["v"]):
                        raise ValueError("Non-finite generated value")
                    # The most coarsely rounded data entries use one decimal.
                    near(value["v"], raw, 0.050000001, value["ref"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)

    aggregates = {row["year"]: row for row in data["aggregates"]}
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
        sheet = workbook["4_2"]
        # Locate the adjustment row independently, rather than accepting the extractor's total.
        adjustment_row = next(cell.row for row in sheet.iter_rows() for cell in row
                              if str(cell.value).strip().startswith("Accounting adjustments"))
        for year in data["years"]:
            service_ref = data["services_total"][year]["ref"]
            service = read(service_ref)
            functions = [read(area["series"][year]["nominal"]["ref"]) for area in data["functions"]]
            if any(value is None for value in functions):
                raise ValueError(f"Cannot reconcile missing functional spending in {year}")
            near(sum(functions), service, 0.05 * len(functions), f"areas -> services, {year}")
            column = re.search(r"!([A-Z]+)", service_ref).group(1)
            adjustment_ref = f"4_2!{column}{adjustment_row}"
            tme = read(aggregates[year]["tme"]["nominal"]["ref"])
            near(service + read(adjustment_ref), tme, 0.1, f"services + adjustments -> TME, {year}")
        latest = data["latest_year"]
        parts = [read(part["ref"]) for part in data["debt_parts"]]
        if any(value is None for value in parts):
            raise ValueError("Cannot reconcile missing debt-interest components")
        near(sum(parts), read(data["debt_interest"][latest]["ref"]), 0.3, "debt components")
        base = data["base_year"]
        for area in data["functions"]:
            row = area["series"][base]
            near(read(row["nominal"]["ref"]), read(row["real"]["ref"]), 0.05, f"base year {area['id']}")
    finally:
        workbook.close()
    print("Independent JSON source-cell and reconciliation checks passed")


def main():
    validate()


if __name__ == "__main__":
    main()
