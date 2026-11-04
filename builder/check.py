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
from html import unescape as html_unescape
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
            series = re.match(r"(\w+) line ", locator)  # e.g. "CFMZ6JM line 2": the column is named by its series code
            key = series.group(1) if series and series.group(1) in head else ("OBS_VALUE" if "OBS_VALUE" in head else "Data values")
            return lines[int(m.group(1)) - 1][head.index(key)]
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
        m = re.fullmatch(r"values\.(\w+)\.(\w+)\.(\d{4})", locator)
        if m:  # IMF DataMapper: values -> indicator -> country -> year
            return data["values"][m.group(1)][m.group(2)].get(m.group(3))
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
    if src_file.endswith(".html"):
        # ONS bulletin text: the first number after a sentence that appears once in the page
        import html as _html
        m = re.fullmatch(r"after '(.+)' number (\d+)", locator)
        raw = (ROOT / src_file).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S))))
        assert text.count(m.group(1)) == 1, m.group(1)
        tail = text[text.index(m.group(1)) + len(m.group(1)):]
        return re.findall(r"\d[\d,]*", tail)[int(m.group(2)) - 1].replace(",", "")
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
        if "not available" not in text and rel == "life/2008.html":
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
    want = ["index.html", "spending.html", "spending-history.html", "taxes.html", "tax-history.html", "who-pays.html", "household-tax.html", "methods.html", "sources.html", "spending-areas.html", "who-pays-households.html", "international.html", "productivity.html", "borrowing.html", "defence.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html", "life/holidays.html", "life/schools.html", "life/compare/index.html"]
    for w in want:
        if not (SITE / w).exists():
            fail(f"missing page {w}")
    pages = sorted(int(p.stem) for p in (SITE / "life").glob("[0-9]*.html"))
    # Every pair of years has a comparison page, including the years before 2008.
    compare = list((SITE / "life/compare").glob("*-*.html"))
    years = sorted({int(x) for p in compare for x in p.stem.split("-")})
    pairs = len(compare)
    if pairs != len(years) * (len(years) - 1) // 2:
        fail(f"{pairs} comparison pages for {len(years)} years")
    # Every pair of three-year spans that do not overlap has a comparison page.
    spans = [p.stem for p in (SITE / "life/compare/spans").glob("*-and-*.html")]
    n = len([y for y in years if y >= 2008]) - 2
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
CHART_EARLY = ["spending.html", "taxes.html", "tax-history.html", "international.html", "productivity.html", "borrowing.html", "defence.html", "who-pays.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html",
               "life/holidays.html", "life/schools.html", "life/1985.html", "life/2008.html", "life/2015.html", "life/2021.html"]
PHONE_SCREEN, CHART_SHOWN = 640, 200
# Pages that must stay short on a 360px phone with every "More on ..." section closed,
# in phone screens of 640px (goal audits 6 and 7: about 8 screens, Sources split).
# DEFAULT_COMPARE stands for the comparison the life hub starts with, which moves with the data.
DEFAULT_COMPARE = "default comparison"
# The life hub gets 8.8 like the topic pages: its "Jump to" bar (audit 9 gap 7) costs about a quarter of a screen.
MAX_SCREENS = {"spending.html": 8.5, "who-pays.html": 8.5, "household-tax.html": 8.5, "life/index.html": 8.8,
               "taxes.html": 8.8, "life/work.html": 8.8, "life/earnings.html": 8.8, "life/housing.html": 8.8,
               "life/holidays.html": 8.8, "life/schools.html": 8.8, DEFAULT_COMPARE: 8.8,
               "methods.html": 9.5, "sources.html": 4}


def default_compare():
    """The comparison page the life hub links first ("Start with ...")."""
    m = re.search(r'Start with <a href="(compare/\d+-\d+\.html)"', (SITE / "life/index.html").read_text(encoding="utf-8"))
    return "life/" + m.group(1) if m else None
FIRST_CHART_JS = """() => {
  const els = [...document.querySelectorAll('main figure, main ul.bars, main ul.cmp-list, main svg[role=img]')]
    .filter(e => e.offsetParent !== null && e.getBoundingClientRect().height > 30);
  return els.length ? Math.min(...els.map(e => e.getBoundingClientRect().top + window.scrollY)) : null;
}"""


# Every tappable thing on the page, with its size (shared with scripts/a11y_benchmark.py).
TARGETS_JS = """() => {
  // Content of a closed <details> still has a size in Chromium, but cannot be seen or tapped.
  const hiddenIn = e => { const d = e.closest('details:not([open])'); return !!d && !(e.closest('summary') && e.closest('summary').parentElement === d); };
  const sel = 'a[href], button, summary, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"])';
  const out = [];
  for (const e of document.querySelectorAll(sel)) {
    let t = e;
    // Hidden radio and checkbox inputs are tapped through their label.
    if (e.matches('input[type=radio], input[type=checkbox]') && e.labels && e.labels.length) t = e.labels[0];
    const r = t.getBoundingClientRect(), s = getComputedStyle(t);
    if (r.width === 0 || r.height === 0 || s.visibility === 'hidden' || r.right < 0 || hiddenIn(t)) continue;
    if (e.classList.contains('skip') || e.closest('.govuk-skip-link, .skiplink, [class*=skip]')) continue;
    // A link inside running text is exempt from 2.5.8.
    const p = e.closest('p, li, dd, td, th, figcaption, blockquote');
    let inline = false;
    if (e.tagName === 'A' && p && s.display === 'inline') {
      const txt = (p.innerText || '').trim(), own = (e.innerText || '').trim();
      inline = txt.length > own.length + 10;
    }
    // Or has a 24px circle of space around its centre that no other target overlaps.
    out.push({tag: e.tagName.toLowerCase(), text: (e.getAttribute('aria-label') || e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 50),
              w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, inline,
              cx: r.left + r.width / 2, cy: r.top + scrollY + r.height / 2});
  }
  // Spacing exception: a small target passes if a 24px circle on its centre touches no other target's circle.
  for (const t of out) {
    t.spaced = !out.some(o => o !== t && Math.hypot(o.cx - t.cx, o.cy - t.cy) < 24);
  }
  return out;
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
                limit = MAX_SCREENS.get(DEFAULT_COMPARE if path == default_compare() else path)
                if width == 360 and limit:
                    screens = page.evaluate("document.documentElement.scrollHeight") / PHONE_SCREEN
                    if screens > limit:
                        fail(f"{path}: {screens:.1f} phone screens long, over the {limit} limit")
                if width == 360:
                    # WCAG 2.2 2.5.8: targets at least 24 x 24 px, unless inside a sentence or well spaced
                    for t in page.evaluate(TARGETS_JS):
                        if (t["w"] < 24 or t["h"] < 24) and not t["inline"] and not t["spaced"]:
                            fail(f"{path}: tap target '{t['text'][:40]}' is {t['w']}x{t['h']}px, under 24x24 (WCAG 2.5.8)")
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


# Words a chart heading may not use: they judge or suggest a cause rather than state what changed.
LOADED_TITLE = re.compile(r"\b(soar|surge|plunge|plummet|slump|skyrocket|crisis|boom|collapse|thanks to|because|due to|caused|record)\w*", re.I)


def check_findings():
    """Every chart heading states its finding: a heading, then what the chart measures
    beneath it, in neutral words."""
    n = 0
    for path in SITE.rglob("*.html"):
        if path.parts[len(SITE.parts)] == "figures":
            continue
        html = path.read_text(encoding="utf-8")
        for m in re.finditer(r'<p class="ctitle"[^>]*>(.*?)</p>(<p class="csub")?', html):
            n += 1
            rel = path.relative_to(SITE)
            if not m.group(2):
                fail(f"{rel}: chart “{m.group(1)}” has no finding as its heading")
            elif LOADED_TITLE.search(m.group(1)):
                fail(f"{rel}: chart heading “{m.group(1)}” uses loaded or causal wording")
    return n


# A rise or fall of at least this share of a line's range must be named in a trend heading.
BIG_MOVE = 0.3
# A smaller turn back at the very end of a line still has to be named (see turn_back_at_end).
TAIL_MOVE = 0.15
_NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def _value(cell):
    m = _NUMBER.search(cell.replace("\u2212", "-")) if cell and cell != "no figure" else None
    return float(m.group().replace(",", "")) if m else None


def big_turns(vals):
    """Points where a line turns after a big move: a peak or low that stands out from
    the line on both sides by at least BIG_MOVE of the line's range (its prominence).
    Worked out from the figures the chart shows, without the builder's own rule.
    Returns a list of (indices, 'peak' or 'low'); a run of equal values is one turn."""
    pts = [i for i, v in enumerate(vals) if v is not None]
    if len(pts) < 3:
        return []
    span = max(vals[i] for i in pts) - min(vals[i] for i in pts)
    if span <= 0 or span < 0.02 * max(abs(vals[i]) for i in pts):
        return []  # every year within 2% of the others: "changed little" is a fair reading
    out = []
    k = 1
    while k < len(pts) - 1:
        j = k
        while j + 1 < len(pts) - 1 and vals[pts[j + 1]] == vals[pts[k]]:
            j += 1  # a flat top or bottom counts once
        run = pts[k:j + 1]
        v = vals[run[0]]
        for sign, kind in ((1, "peak"), (-1, "low")):
            def base(side):
                seq = pts[:k][::-1] if side < 0 else pts[j + 1:]
                b = v
                for i in seq:
                    if (vals[i] - v) * sign > 0:
                        break
                    b = min(b, vals[i]) if sign > 0 else max(b, vals[i])
                return b
            left, right = base(-1), base(1)
            if not pts[:k] or not pts[j + 1:]:
                continue
            prom = (v - max(left, right)) if sign > 0 else (min(left, right) - v)
            if prom >= BIG_MOVE * span - 1e-9:
                out.append((run, kind))
        k = j + 1
    return out


def turn_back_at_end(vals):
    """A line that ends at least TAIL_MOVE of its range back from a peak or low after
    its last big turn, however small that move is next to the line's big moves.
    Returns (indices of the latest such peak or low, 'peak' or 'low') or None. A title that ends
    "then rose" about a line whose latest figures fell would mislead, so the heading
    must name that peak or low and the move after it."""
    pts = [i for i, v in enumerate(vals) if v is not None]
    if len(pts) < 3:
        return None
    span = max(vals[i] for i in pts) - min(vals[i] for i in pts)
    if span <= 0 or span < 0.02 * max(abs(vals[i]) for i in pts):
        return None
    turns = big_turns(vals)
    start = turns[-1][0][-1] if turns else pts[0]
    tail = [i for i in pts if i >= start]
    last = tail[-1]
    way = 1 if vals[last] >= vals[start] else -1
    # the latest point the line ends that far back from, with no later point past it
    back = [k for k in tail[1:-1] if (vals[k] - vals[last]) * way >= TAIL_MOVE * span - 1e-9
            and all((vals[k] - vals[j]) * way >= 0 for j in tail if j > k)]
    if not back:
        return None
    n = tail.index(back[-1])
    while n > 1 and (vals[tail[n - 1]] - vals[tail[n]]) * way >= 0:
        n -= 1  # back up to the top (or bottom) of that peak (or low)
    run = [i for i in tail[n:] if vals[i] == vals[tail[n]] and all(vals[j] == vals[i] for j in tail[n:] if j <= i)]
    return run, "peak" if way > 0 else "low"


def crosses_break(title, lines, rows, breaks):
    """Problems with a trend heading that reads across a marked definition break: it
    describes years on both sides of one, or compares a figure with "the 2019 level"
    when the line goes on past a break after 2019, so the reader is led to set figures
    either side of the break against each other."""
    out = []
    labels = [str(r[0]).replace(" (calendar year)", "") for r in rows]
    for part in lines.split():
        si, a, b = (int(x) for x in part.split(":"))
        vals = [_value(r[si + 1]) for r in rows]
        for k in breaks:
            if a < k < b and any(v is not None for v in vals[a:k]) and any(v is not None for v in vals[k:b]):
                out.append(f"describes years either side of the break at {labels[k]}, so it compares figures that are not comparable")
        last = max((i for i, v in enumerate(vals) if v is not None), default=-1)
        for m in re.finditer(r"the (\S+) level", title):
            if m.group(1) not in labels:
                continue
            ref = labels.index(m.group(1))
            for k in breaks:
                if ref < k <= last:
                    out.append(f"compares with the {m.group(1)} level, but the line goes on past the break at {labels[k]}, "
                               "so readers will set later figures against it; name the year the comparable run ends instead")
    return sorted(set(out))


def check_trend_titles():
    """A heading that says how a line moved names every big rise and fall: each peak or
    low that the line moves at least BIG_MOVE of its range into and back out of."""
    n = 0
    for path in SITE.rglob("*.html"):
        if path.parts[len(SITE.parts)] == "figures":
            continue
        html = path.read_text(encoding="utf-8")
        for fig in re.finditer(r"<figure>(.*?)</figure>", html, re.S):
            t = re.search(r'<p class="ctitle"[^>]*data-lines="([^"]*)"[^>]*>(.*?)</p>', fig.group(1))
            if not t:
                continue
            n += 1
            rel = path.relative_to(SITE)
            title = html_unescape(t.group(2))
            d = re.search(r"data-chart='([^']*)'", fig.group(1))
            if not d:
                fail(f"{rel}: trend heading “{title}” has no chart figures to check it against")
                continue
            rows = json.loads(html_unescape(d.group(1)))["rows"]
            br = re.search(r'data-breaks="([^"]*)"', t.group(0))
            breaks = [int(x) for x in br.group(1).split()] if br else []
            for msg in crosses_break(title, t.group(1), rows, breaks):
                fail(f"{rel}: heading “{title}” {msg}")
            for part in t.group(1).split():
                si, a, b = (int(x) for x in part.split(":"))
                vals = [_value(r[si + 1]) for r in rows[a:b]]
                labels = [str(r[0]).replace(" (calendar year)", "") for r in rows[a:b]]
                for run, kind in big_turns(vals):
                    named = any(re.search(r"(?<![\w/-])" + re.escape(labels[i]) + r"(?![\w/-])", title) for i in run)
                    if not named or "rose" not in title or "fell" not in title:
                        fail(f"{rel}: heading “{title}” leaves out the {kind} in {labels[run[-1]]}, a move of at least {BIG_MOVE:.0%} of the line's range")
                end = turn_back_at_end(vals)
                if end:
                    run, kind = end
                    verb = "fell" if kind == "peak" else "rose"
                    at = [m.end() for i in run for m in re.finditer(r"(?<![\w/-])" + re.escape(labels[i]) + r"(?![\w/-])", title)]
                    if not at or not any(re.search(r"\b" + verb + r"\b", title[k:].split(";")[0].split(", while ")[0]) for k in at):
                        fail(f"{rel}: heading “{title}” does not say the line {verb} after its {kind} in {labels[run[0]]}: "
                             f"its latest figure is at least {TAIL_MOVE:.0%} of the line's range back from it")
    return n


def check_axis_notes():
    """Every line chart whose scale starts above zero says so under the chart."""
    sys.path.insert(0, str(ROOT))
    from builder.html import ZERO_NOTE
    n = 0
    for path in SITE.rglob("*.html"):
        if path.parts[len(SITE.parts)] == "figures":
            continue
        html = path.read_text(encoding="utf-8")
        for fig in re.finditer(r"<figure>(.*?)</figure>", html, re.S):
            body = fig.group(1)
            # the lowest y-axis tick is the first right-aligned label drawn in the chart
            t = re.search(r'<text x="[\d.]+" y="[\d.]+" text-anchor="end">(-?[\d,.]+)</text>', body)
            if not t:
                continue
            lo = float(t.group(1).replace(",", ""))
            if lo <= 0:
                continue
            n += 1
            cap = re.search(r"<figcaption>(.*?)</figcaption>", body, re.S)
            want = ZERO_NOTE.format(t.group(1))
            if not cap or want not in html_unescape(cap.group(1)):
                title = re.search(r'<p class="ctitle"[^>]*>(.*?)</p>', body)
                fail(f"{path.relative_to(SITE)}: chart “{html_unescape(title.group(1)) if title else '?'}” starts its scale at {t.group(1)} but its caption does not say “{want}”")
    return n


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
    n_findings = check_findings()
    n_trends = check_trend_titles()
    n_axes = check_axis_notes()
    if "--axe" in sys.argv:
        dc = default_compare()
        if dc is None:
            fail("life/index.html: no 'Start with' comparison link")
        run_axe(([dc] if dc else []) + ["index.html", "spending.html", "spending-history.html", "taxes.html", "tax-history.html", "who-pays.html", "household-tax.html", "methods.html", "sources.html", "spending-areas.html", "who-pays-households.html", "international.html", "productivity.html", "borrowing.html", "defence.html",
                 "glossary.html", "corrections.html", "uncertainty.html", "figures/pesa4.html", "life/index.html", "life/work.html", "life/earnings.html", "life/housing.html", "life/holidays.html", "life/schools.html", "life/jobs-by-industry.html", "life/house-prices.html", "life/generations.html", "life/1985.html", "life/2008.html", "life/2015.html", "life/2021.html", "life/compare/2010-2025.html",
                 "life/compare/2019-2024.html", "life/compare/1985-2025.html", "life/compare/2002-2025.html", "life/compare/index.html", "life/compare/spans/index.html",
                 "life/compare/spans/2009-2011-and-2017-2019.html", "life/compare/spans/2011-2013-and-2022-2024.html", "figures/etb.html"])
    print(f"Re-read {checked:,} figures from source files; recalculated {recalculated:,} derived figures.")
    print(f"Checked {shown:,} numbers on {n_pages} pages ({years} year pages, {pairs} comparison pages).")
    print(f"Checked {n_csv:,} CSV downloads beside the charts and tables.")
    print(f"Checked that {n_findings} chart headings state their finding in neutral words.")
    print(f"Checked that {n_trends} trend headings name every big rise and fall of their line.")
    print(f"Checked that {n_axes} line charts whose scale starts above zero say so.")
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
