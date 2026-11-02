"""Check the built site against its sources.

Usage: python -m builder.check [--axe]

1. Every source file still matches its recorded SHA-256 hash.
2. Every published figure is re-read from its file, sheet and cell (or line or
   row) and compared with the recorded value.
3. Every calculated figure whose formula is plain arithmetic is recalculated.
4. Every number shown on every page matches its recorded value, formatted.
5. Every change shown on a comparison page is recalculated.
6. Every internal link and #anchor resolves.
7. Basic accessibility, wording and labelling rules hold on every page.
   Quoted text inside <blockquote> is the publisher's own wording, so it is
   checked word for word against the source (step 9) instead of for loaded words.
8. With --axe, axe-core accessibility checks run on key pages at phone width.
9. Every quoted explanation appears word for word in its source file and is
   shown on at least one page.
"""
import csv
import hashlib
import io
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

# Words that judge rather than describe. Matched as whole words in visible text.
LOADED = ["shocking", "staggering", "soared", "soaring", "plummeted", "plunged", "massive", "huge", "crisis", "waste", "wasted",
          "burden", "fair share", "unfair", "sadly", "unfortunately", "good news", "bad news", "only just", "skyrocket", "skyrocketed",
          "slashed", "splurge", "handout", "handouts", "scrounger", "typical family", "average family"]

# Loaded terms the site may name, only in curly quotation marks, in order to explain them.
NAMED_TERMS = ["“tax burden”"]

problems = []
QUOTED_PAGES = []


def fail(msg):
    problems.append(msg)


# ---------------------------------------------------------------- source cells

_wb = {}


def workbook(path):
    if path not in _wb:
        import openpyxl
        _wb[path] = openpyxl.load_workbook(ROOT / path, data_only=True, read_only=False)
    return _wb[path]


def cell_value(src_file, locator):
    """Return the raw value at a locator, read independently of the builder."""
    if src_file.endswith(".xlsx"):
        sheet, ref = locator.rsplit("!", 1)
        return workbook(src_file)[sheet][ref].value
    if src_file.endswith(".xls"):
        import xlrd  # legacy Excel: read with xlrd, not the builder's code path
        sheet, ref = locator.rsplit("!", 1)
        m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
        col = 0
        for ch in m.group(1):
            col = col * 26 + ord(ch) - 64
        return xlrd.open_workbook(str(ROOT / src_file)).sheet_by_name(sheet).cell_value(int(m.group(2)) - 1, col - 1)
    if src_file.endswith(".ods"):
        from .readers import ods  # ODS has no second reader available; the builder's reader expands repeats in full
        sheet, ref = locator.rsplit("!", 1)
        m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
        col = 0
        for ch in m.group(1):
            col = col * 26 + ord(ch) - 64
        rows = ods(src_file)[sheet]
        r = rows[int(m.group(2)) - 1]
        return r[col - 1] if col - 1 < len(r) else None
    if src_file.endswith(".csv"):
        text = (ROOT / src_file).read_text(encoding="utf-8-sig")
        m = re.search(r" line (\d+)$", locator)
        if m:
            lines = list(csv.reader(io.StringIO(text)))
            head = lines[0]
            return lines[int(m.group(1)) - 1][head.index("OBS_VALUE" if "OBS_VALUE" in head else "Data values")]
        m = re.fullmatch(r"CDID (\w+) row '(.+)'", locator)
        if m:  # a time-series file with one column per series, found by its CDID row
            rows = list(csv.reader(io.StringIO(text)))
            col = next(r for r in rows if r and r[0] == "CDID").index(m.group(1))
            return next((r[col] for r in rows if r and r[0] == m.group(2)), None)
        m = re.fullmatch(r"\w+ row '(.+)'", locator)
        if m:
            for row in csv.reader(io.StringIO(text)):
                if row and row[0] == m.group(1):
                    return row[1]
            return None
    if src_file.endswith(".json"):
        data = json.loads((ROOT / src_file).read_text())
        m = re.fullmatch(r"value\[(\d+)\]", locator)
        if m:  # JSON-stat (Eurostat): flat value list keyed by position
            return data["value"].get(m.group(1))
        m = re.fullmatch(r"results\[(\d+)\] values\.(\w+)", locator)
        return data["results"][int(m.group(1))]["values"][m.group(2)]
    if src_file.endswith(".pdf"):
        # Read the page text afresh and find the anchor, the line and the nth number on it
        from pypdf import PdfReader
        m = re.fullmatch(r"p(\d+) after '(.+)' line '(.+)' number (\d+)", locator)
        text = PdfReader(ROOT / src_file).pages[int(m.group(1)) - 1].extract_text()
        after = text[text.index(m.group(2)) + len(m.group(2)):]
        line = after[after.index(m.group(3)) + len(m.group(3)):].split("\n", 1)[0]
        return re.findall(r"-?[\d,]+(?:\.\d+)?", line)[int(m.group(4)) - 1].replace(",", "")
    raise ValueError(f"cannot read {src_file} at {locator}")


def as_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").lstrip("±").strip()
    try:
        return float(s)
    except ValueError:
        return None


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def check_facts(data):
    sources = data["sources"]
    facts = {f["id"]: f for f in data["facts"]}
    for s in sources.values():
        digest = hashlib.sha256((ROOT / s["file"]).read_bytes()).hexdigest()
        if digest != s["sha256"]:
            fail(f"hash changed: {s['file']}")
    checked = recalculated = 0
    for f in facts.values():
        if f["status"] in ("calculated",):
            ids = f["inputs"]
            for i in ids:
                if i not in facts:
                    fail(f"{f['id']}: input {i} missing")
            expr = f["formula"]
            if not ids or not expr:
                continue
            for i in sorted(ids, key=len, reverse=True):
                expr = expr.replace(i, f"V[{ids.index(i)}]")
            expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
            if re.fullmatch(r"[\sV\[\]\d\.\+\-\*/\(\)]+", expr):
                vals = [facts[i]["value"] for i in ids]
                if None in vals:
                    if f["value"] is not None:
                        fail(f"{f['id']}: value given although an input is missing")
                    continue
                got = eval(expr, {"__builtins__": {}}, {"V": vals})  # arithmetic only, checked by the pattern above
                if not close(got, f["value"], 1e-9):
                    fail(f"{f['id']}: recalculated {got} != recorded {f['value']}")
                recalculated += 1
            continue
        if f["status"] == "missing" or f["locator"] in ("", "not published"):
            continue
        src = sources[f["source"]]
        raw = cell_value(src["file"], f["locator"])
        rawn = as_number(raw)
        want = None if rawn is None else rawn * f.get("scale", 1)
        if f["source"] == "dfe_api" and want is not None:
            want = round(want, 1)
        if not close(want, f["value"], 1e-9):
            fail(f"{f['id']}: source {src['file']} {f['locator']} = {raw!r}, recorded {f['value']!r}")
        checked += 1
    return facts, checked, recalculated


# ---------------------------------------------------------------- pages

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.datas, self.links, self.ids, self.text = [], [], set(), []
        self.stack, self.h1, self.headings, self.svgs, self.tables, self.captions = [], 0, [], [], 0, 0
        self.lang = None
        self._data = None
        self._script = False
        self._quote = 0
        self.quoted = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag in ("a", "link") and a.get("href"):
            self.links.append(a["href"])
        if tag == "data":
            self._data = [a, ""]
        if tag == "script":
            self._script = True
        if tag == "blockquote":
            self._quote += 1
        if tag == "h1":
            self.h1 += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "svg":
            self.svgs.append(a)
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1

    def handle_endtag(self, tag):
        if tag == "data" and self._data:
            self.datas.append(tuple(self._data))
            self._data = None
        if tag == "script":
            self._script = False
        if tag == "blockquote":
            self._quote -= 1

    def handle_data(self, d):
        if self._data is not None:
            self._data[1] += d
        if self._quote:
            self.quoted.append(d)
        elif not self._script:
            self.text.append(d)


def check_pages(facts):
    sys.path.insert(0, str(ROOT))
    from builder.html import fmt
    pages = sorted(SITE.rglob("*.html"))
    shown = 0
    ids_cache = {}
    for p in pages:
        rel = p.relative_to(SITE).as_posix()
        pp = PageParser()
        pp.feed(p.read_text(encoding="utf-8"))
        if pp.lang != "en-GB":
            fail(f"{rel}: missing lang")
        if pp.h1 != 1:
            fail(f"{rel}: {pp.h1} h1 headings")
        for a, b in zip(pp.headings, pp.headings[1:]):
            if b > a + 1:
                fail(f"{rel}: heading level jumps from h{a} to h{b}")
        for s in pp.svgs:
            if s.get("role") != "img" or not s.get("aria-label"):
                fail(f"{rel}: chart without a text label")
        if pp.tables != pp.captions:
            fail(f"{rel}: table without caption")
        for attrs, text in pp.datas:
            if "data-fact" in attrs:
                fid, kind = attrs["data-fact"], attrs["data-kind"]
                if fid not in facts:
                    fail(f"{rel}: unknown figure {fid}")
                    continue
                want = fmt(facts[fid]["value"], kind)
                if text != want:
                    fail(f"{rel}: {fid} shows {text!r}, expected {want!r}")
                shown += 1
            elif "data-change" in attrs:
                a, b = facts[attrs["data-from"]]["value"], facts[attrs["data-to"]]["value"]
                style = attrs["data-change"]
                v = (b - a) if style in ("pp", "abs") else 100 * (b / a - 1)
                if not close(v, float(attrs["value"]), 1e-9):
                    fail(f"{rel}: change {attrs['data-from']}→{attrs['data-to']} is {attrs['value']}, recalculated {v}")
                shown += 1
            elif "data-margin" in attrs:
                # Combined margin of error for a change: √(a² + b²), each margin in the figure's own units
                va, vb = facts[attrs["data-from"]]["value"], facts[attrs["data-to"]]["value"]
                ma, mb = facts[attrs["data-ma"]]["value"], facts[attrs["data-mb"]]["value"]
                ma = va * ma / 100 if attrs["data-ka"] == "pm_pct" else ma
                mb = vb * mb / 100 if attrs["data-kb"] == "pm_pct" else mb
                v = (ma ** 2 + mb ** 2) ** 0.5
                v = 100 * v / va if attrs["data-margin"] == "pct" else v
                if not close(v, float(attrs["value"]), 1e-9):
                    fail(f"{rel}: combined margin {attrs['data-from']}→{attrs['data-to']} is {attrs['value']}, recalculated {v}")
                shown += 1
        for href in pp.links:
            if re.match(r"^(https?:|mailto:)", href):
                continue
            path, _, frag = href.partition("#")
            target = (p.parent / path).resolve() if path else p
            if path and not target.exists():
                fail(f"{rel}: broken link {href}")
                continue
            if frag and target.suffix == ".html":
                if target not in ids_cache:
                    tp = PageParser()
                    tp.feed(target.read_text(encoding="utf-8"))
                    ids_cache[target] = tp.ids
                if frag not in ids_cache[target]:
                    fail(f"{rel}: missing anchor {href}")
        QUOTED_PAGES.append((rel, "".join(pp.quoted)))
        text = " ".join(pp.text).lower()
        # Naming a term other people use, in quotation marks, to explain it is not adopting it.
        for term in NAMED_TERMS:
            text = text.replace(term, "")
        for w in LOADED:
            if re.search(r"\b" + re.escape(w) + r"\b", text):
                fail(f"{rel}: loaded wording '{w}'")
        if "worked example" in text and "illustration, not a statistic" not in text:
            fail(f"{rel}: worked example without the illustration label")
        if "not available" not in text and "life/" in rel and rel.endswith("2008.html"):
            fail(f"{rel}: expected 2008 gaps to be shown")
    return len(pages), shown


DL_RE = re.compile(r'<p class="dl"><a href="([^"]+\.csv)" download>')


def check_downloads():
    """Every table and chart on a reading page has a CSV download beside it, and each file holds its rows."""
    import csv as _csv
    files = 0
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel.startswith("figures/"):
            continue
        html = p.read_text(encoding="utf-8")
        main = html[html.find("<main"):html.find("</main>")]
        links = DL_RE.findall(main)
        charts = len(re.findall(r"<figure\b", main)) + len(re.findall(r'(?<!aria-hidden="true">)<ul class="(?:bars|bars change)">', main))
        tables = main.count("<table")
        # The rest of a long comparison list folded away ("cont") is covered by the download under its first part.
        lists = len(re.findall(r'<ul class="cmp-list">', main))
        if len(links) != charts + tables + lists:
            fail(f"{rel}: {charts} charts, {lists} lists and {tables} tables but {len(links)} CSV downloads")
        for href in links:
            f = (p.parent / href).resolve()
            if not f.exists():
                continue  # reported as a broken link
            rows = list(_csv.reader(f.read_text(encoding="utf-8-sig").splitlines()))
            if len(rows) < 2 or any(len(r) != len(rows[0]) for r in rows):
                fail(f"{rel}: {href} is not a complete table")
            files += 1
    return files


def check_structure():
    want = ["index.html", "spending.html", "spending-history.html", "taxes.html", "who-pays.html", "household-tax.html", "methods.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html", "life/holidays.html", "life/schools.html", "life/compare/index.html"]
    for w in want:
        if not (SITE / w).exists():
            fail(f"missing page {w}")
    pages = sorted(int(p.stem) for p in (SITE / "life").glob("[0-9]*.html"))
    # Every pair of explorer years (2008 on) has a comparison page; earlier years have a year page only.
    compare = list((SITE / "life/compare").glob("*-*.html"))
    years = sorted({int(x) for p in compare for x in p.stem.split("-")})
    pairs = len(compare)
    if pairs != len(years) * (len(years) - 1) // 2:
        fail(f"{pairs} comparison pages for {len(years)} years")
    # Every pair of three-year spans that do not overlap has a comparison page.
    spans = [p.stem for p in (SITE / "life/compare/spans").glob("*-and-*.html")]
    n = len(years) - 2
    if len(spans) != (n - 3) * (n - 2) // 2:
        fail(f"{len(spans)} span comparison pages for {n} spans")
    for y in years:
        if y not in pages:
            fail(f"missing year page life/{y}.html")
    if pages != list(range(pages[0], pages[-1] + 1)):
        fail("year pages are not one per year")
    return len(pages), pairs


# Pages whose first chart must start high enough on a 360 x 640 phone that at
# least CHART_SHOWN pixels of it are visible within the first two screens.
CHART_EARLY = ["spending.html", "taxes.html", "who-pays.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html",
               "life/holidays.html", "life/schools.html", "life/1985.html", "life/2008.html", "life/2015.html", "life/2021.html"]
PHONE_SCREEN, CHART_SHOWN = 640, 200
FIRST_CHART_JS = """() => {
  const els = [...document.querySelectorAll('main figure, main ul.bars, main ul.cmp-list, main svg[role=img]')]
    .filter(e => e.offsetParent !== null && e.getBoundingClientRect().height > 30);
  return els.length ? Math.min(...els.map(e => e.getBoundingClientRect().top + window.scrollY)) : null;
}"""


def run_axe(paths):
    try:
        from playwright.sync_api import sync_playwright
        from axe_playwright_python.sync_playwright import Axe
    except ImportError:
        fail("--axe needs playwright and axe-playwright-python (make setup)")
        return
    import os
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else pw.chromium.launch()
        for width in (360, 1100):
            page = browser.new_page(viewport={"width": width, "height": 800})
            for path in paths:
                page.goto((SITE / path).as_uri())
                if width == 360 and path in CHART_EARLY:
                    top = page.evaluate(FIRST_CHART_JS)
                    if top is None or top > 2 * PHONE_SCREEN - CHART_SHOWN:
                        fail(f"{path}: first chart starts at {top}px, not within the first two phone screens")
                # Open every folded section, so tables and source lists are checked too
                page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
                if page.evaluate("document.documentElement.scrollWidth") > width + 1:
                    fail(f"{path}: scrolls sideways at {width}px")
                res = Axe().run(page)
                for v in res.response["violations"]:
                    wcag = any(tag.startswith("wcag") for tag in v.get("tags", []))
                    if wcag or v["impact"] in ("serious", "critical"):
                        fail(f"{path} at {width}px: axe {v['id']} ({v['impact']}): {v['help']}")
            page.close()
        browser.close()


def check_explanations():
    sys.path.insert(0, str(ROOT))
    from builder.explain import EXPLANATIONS, missing_quotes, norm
    from builder.sources import all_sources
    for p in missing_quotes(all_sources()):
        fail(p)
    shown = " ".join(norm(t) for _, t in QUOTED_PAGES)
    for key, e in EXPLANATIONS.items():
        if not all(norm(q) in shown for q in e["quote"]):
            fail(f"explanation {key} is not shown on any page")
    return len(EXPLANATIONS)


def main():
    data = json.loads((SITE / "data/facts.json").read_text(encoding="utf-8"))
    facts, checked, recalculated = check_facts(data)
    years, pairs = check_structure()
    n_pages, shown = check_pages(facts)
    n_quotes = check_explanations()
    n_csv = check_downloads()
    if "--axe" in sys.argv:
        run_axe(["index.html", "spending.html", "spending-history.html", "taxes.html", "who-pays.html", "household-tax.html", "methods.html",
                 "glossary.html", "corrections.html", "uncertainty.html", "figures/pesa4.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html", "life/holidays.html", "life/schools.html", "life/jobs-by-industry.html", "life/house-prices.html", "life/1985.html", "life/2008.html", "life/2015.html", "life/2021.html", "life/compare/2010-2025.html",
                 "life/compare/2019-2024.html", "life/compare/index.html", "life/compare/spans/index.html",
                 "life/compare/spans/2009-2011-and-2017-2019.html", "life/compare/spans/2011-2013-and-2022-2024.html", "figures/etb.html"])
    print(f"Re-read {checked:,} figures from source files; recalculated {recalculated:,} derived figures.")
    print(f"Checked {shown:,} numbers on {n_pages} pages ({years} year pages, {pairs} comparison pages).")
    print(f"Checked {n_csv:,} CSV downloads beside the charts and tables.")
    print(f"Matched {n_quotes} quoted explanations word for word against their sources.")
    if problems:
        print(f"\n{len(problems)} problems:")
        for p in problems[:200]:
            print(" -", p)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
