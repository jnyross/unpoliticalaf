"""Check the built site against the raw spreadsheets and the rubric's automated rules.

Exits non-zero if any figure on a page does not match the cell it names, if banned
evaluative words appear, if colours outside the neutral palette are used, if a page
is over the size limit, or if the reading level is above the target.
"""

import json
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
    sources = json.loads((ROOT / "data/sources.json").read_text())
    owner = {sheet: src for src in sources.values() for sheet in src["sheets"]}
    books = {}

    def read(ref):
        sheet, cell = ref.rsplit("!", 1)
        src = owner[sheet]
        if src["file"] not in books:
            books[src["file"]] = load_workbook(ROOT / src["file"], read_only=False, data_only=True)
        v = books[src["file"]][sheet][cell].value
        v = 0.0 if v in ("-", None) else float(v)
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
    return 0.39 * words / sents + 11.8 * syl / words - 15.59


def main():
    read = cells()
    errors, report = [], []
    if not (SITE / "methods.html").is_file():
        errors.append("methods.html: missing methods page")
    for path in sorted(SITE.glob("*.html")):
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

        for f in p.figures:
            if not f["ref"]:
                errors.append(f"{name}: figure {f['text']!r} has no source reference")
                continue
            shown = float(f["value"])
            refs = re.findall(r"(.+?![A-Z]+[0-9]+)(?: |$)", f["ref"])
            if f["calc"] == "share":
                expect, tol = read(refs[0]) / read(refs[1]) * 100, 1e-3
            elif f["calc"] == "change":
                expect, tol = (read(refs[1]) - read(refs[0])) / read(refs[0]) * 100, 1e-3
            else:
                expect, tol = read(refs[0]), 0.051
            if abs(shown - expect) > tol:
                errors.append(f"{name}: {f['text']!r} is {shown} but {f['ref']} gives {expect}")
            nums = re.findall(r"-?[\d,]+\.?\d*", f["text"])
            if nums and f["calc"] is None:
                text_v = float(nums[0].replace(",", ""))
                if abs(abs(text_v) - abs(shown)) > max(0.51, abs(shown) * 0.005):
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


if __name__ == "__main__":
    main()
