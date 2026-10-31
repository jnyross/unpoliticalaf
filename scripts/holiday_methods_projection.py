"""Private holiday methods projection. Returns memory only; never writes output.

Regex locators are deliberately separate from the audit's HTML tree reader.
The four complete official pages remain immutable source inputs.
"""
from copy import deepcopy
import hashlib
from html import unescape
import json
import math
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/life/sources/holiday-methods"
REGISTER = "data/life/holiday-methods-sources.json"
REGISTER_SHA256 = "3ad959baf1ec72ece23ef7efbc1692e19374168a1930a4027d55b288a9542b3f"
QUOTES = "data/life/holiday-method-quotes.json"
QUOTES_SHA256 = "2d397804b3a3af1c8bbcbdebbe8f2962934880b816ebf73773063b0ac1eec7f1"
FILES = ("travel-methods-crawl-0.html.json", "travel-methods-crawl-1.html.json",
         "travel-methods-crawl-2.html.json", "travel-qmi-crawl-0.html.json")
LEGACY = [
    {
        "id": "qmi-revision",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "output-information",
        "heading": "1. Output information",
        "fragment": "Last revised: 10 May 2023"
    },
    {
        "id": "qmi-visits",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-characteristics-of-the-international-passenger-survey-data",
        "heading": "Concepts and definitions",
        "fragment": "As mentioned, IPS estimates"
    },
    {
        "id": "qmi-coverage",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-summary",
        "heading": "Limitations",
        "fragment": "Additionally, about 90%"
    },
    {
        "id": "qmi-additions",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "methods-used-to-produce-the-international-passenger-survey-data",
        "heading": "Additional sources of data",
        "fragment": "The weighting referred to"
    },
    {
        "id": "qmi-revised-series",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "important-points",
        "heading": "3. Important points",
        "fragment": "Methodological improvements relating"
    },
    {
        "id": "qmi-suspension",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "important-points",
        "heading": "3. Important points",
        "fragment": "The IPS was suspended"
    },
    {
        "id": "qmi-tablets",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-summary",
        "heading": "Recent improvements",
        "fragment": "In April 2018,"
    },
    {
        "id": "trend-revised-series",
        "source_file": "travel-methods-crawl-2.html",
        "anchor": "impacts-of-the-new-ips-methodology",
        "heading": "6. Impacts of the new IPS methodology",
        "fragment": "The figures presented in this article"
    },
    {
        "id": "trend-visits",
        "source_file": "travel-methods-crawl-2.html",
        "anchor": "glossary",
        "heading": "Visits",
        "fragment": "The figures relate to the number"
    },
    {
        "id": "current-visits",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "glossary",
        "heading": "Visits",
        "fragment": "The figures for visits relate"
    },
    {
        "id": "current-residents",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "glossary",
        "heading": "Visits outside the UK by residents of Great Britain or the UK",
        "fragment": "Visits for a period"
    },
    {
        "id": "current-no-adjustment",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "understanding-the-comparability-of-estimates-over-time",
        "heading": "How these figures can be used",
        "fragment": "Therefore, users should not apply"
    }
]
SCOPE = {
    "measure": "Overseas holiday-purpose visits, not people.",
    "excluded": [
        "Domestic holidays",
        "Household participation",
        "A family's holiday frequency",
        "Affordability"
    ],
    "historical_basis": "Older UK only; QMI revised 10 May 2023 does not govern 2024/2025 GB.",
    "current_basis": "2024/2025 GB breakdowns; UK headline totals only. Workbook notes still required.",
    "series_boundaries": [
        "2009–2019 revised published trend; not an unchanged survey or proof every cell was reweighted.",
        "2020 gap; incomplete alternative-source estimates are not a proven Q1 observation.",
        "2021–2023 distinct block: Irish land border excluded in 2021 and some tunnel figures modelled; workbook evidence pending.",
        "2024 composite old Q1/Q2, new Q3/Q4; not comparable with 2023 or 2025.",
        "2025 separate development basis; no provisional label inferred from discontinuity research."
    ],
    "unverified": [
        "Numeric source cells, units, holiday definitions, rounding, confidence and suppression codes require separately retained workbooks.",
        "2021 border/tunnel limitations are frozen-contract cautions, not independently evidenced by these four pages."
    ]
}


def strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate holiday JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite holiday JSON number: " + value)

    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            return invalid(value)
        return parsed

    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)


def read(root, relative):
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts or not part.parts:
        raise ValueError("Unsafe holiday path")
    root = Path(root).absolute()
    path = root / part
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Holiday evidence must not contain symlinks")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Holiday evidence must be a regular file within root")
    if metadata.st_nlink != 1:
        raise ValueError("Holiday hard links forbidden")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def sources(root):
    raw = read(root, REGISTER)
    if digest(raw) != REGISTER_SHA256:
        raise ValueError("Pinned holiday register changed")
    register = strict_json(raw)
    entries = register["sources"]
    if (register["schema_version"] != 1 or register["domain"] != "holiday-methods" or
            len(entries) != 4 or {e["path"] for e in entries} !=
            {DIRECTORY + "/" + name for name in FILES}):
        raise ValueError("Holiday closed source set changed")
    directory = Path(root) / DIRECTORY
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("Holiday source directory contains symlinks")
    if {p.name for p in directory.iterdir()} != set(FILES):
        raise ValueError("Holiday source directory set changed")
    originals, evidence = {}, {}
    for entry in entries:
        stored = read(root, entry["path"])
        if len(stored) != entry["stored_bytes"] or digest(stored) != entry["stored_sha256"]:
            raise ValueError("Holiday stored hash/length mismatch")
        envelope = strict_json(stored)
        if (set(envelope) != {"encoding", "original_response"} or
                envelope["encoding"] != "utf-8" or type(envelope["original_response"]) is not str):
            raise ValueError("Holiday envelope encoding/keys changed")
        body = envelope["original_response"].encode("utf-8")
        if len(body) != entry["bytes"] or digest(body) != entry["sha256"]:
            raise ValueError("Holiday recovered original hash/length mismatch")
        name = Path(entry["path"]).name
        originals[name], evidence[name] = body, dict(entry)
    return originals, evidence


def text(html):
    return " ".join(unescape(re.sub(r"<[^>]*>", "", html)).split())


def locate(body, anchor, heading, fragment, exact=False):
    html = body.decode("utf-8")
    sections = list(re.finditer(r'<div\b[^>]*\bid="([^"]+)"[^>]*class="section__content--markdown"[^>]*>', html))
    matches = [(m, sections[i+1].start() if i+1 < len(sections) else len(html))
               for i, m in enumerate(sections) if m[1] == anchor]
    if len(matches) != 1:
        raise ValueError("Holiday anchor missing/ambiguous")
    match, end = matches[0]
    section = html[match.end():end]
    headings = list(re.finditer(r"<h([2-6])\b[^>]*>([\s\S]*?)</h\1>", section))
    selected = [i for i, h in enumerate(headings) if text(h[2]) == heading]
    if len(selected) != 1:
        raise ValueError("Holiday heading missing/ambiguous")
    index = selected[0]
    start = headings[index]
    stop = next((h.start() for h in headings[index+1:] if int(h[1]) <= int(start[1])), len(section))
    block = section[start.end():stop]
    paragraphs = [text(m[1]) for m in re.finditer(r"<p\b[^>]*>([\s\S]*?)</p>", block)]
    found = [p for p in paragraphs if (p == fragment if exact else p.startswith(fragment))]
    if len(found) != 1:
        raise ValueError("Holiday quote missing/ambiguous")
    return found[0], block


def record(spec, quote, evidence, context=None):
    name = spec["source_file"] + ".json"
    entry = evidence[name]
    return {"id": spec["id"], "quote": quote, "context": context,
            "applies_to": "current-GB-methods-2024-2025" if name in FILES[:2] else "older-UK-methods",
            "source": {"path": entry["path"], "url": entry["url"], "sha256": entry["sha256"],
                       "anchor": spec["anchor"], "heading": spec["heading"]}}


def project(root=ROOT):
    originals, evidence = sources(root)
    raw = read(root, QUOTES)
    if digest(raw) != QUOTES_SHA256:
        raise ValueError("Pinned holiday quote register changed")
    quotes = strict_json(raw)
    if quotes["schema_version"] != 1 or len(quotes["quotes"]) != 8:
        raise ValueError("Holiday mandatory quote set changed")
    records = []
    for index, quote in enumerate(quotes["quotes"]):
        name = quote["source_file"] + ".json"
        if quote["original_sha256"] != evidence[name]["sha256"]:
            raise ValueError("Holiday quote original hash binding changed")
        selected, block = locate(originals[name], quote["anchor"], quote["heading"], quote["quote"], exact=True)
        context = None
        if index == 6:
            # Preserve the actual preceding prohibition and its list, not merely
            # the existence of a negative phrase somewhere on the page.
            lists = re.findall(r"<p\b[^>]*>([\s\S]*?)</p>\s*<ul\b[^>]*>([\s\S]*?)</ul>", block)
            if not any(text(p) == "Users should not:" and selected in text(items) for p, items in lists):
                raise ValueError("Holiday comparison prohibition polarity lost")
            context = "Users should not:"
        spec = dict(quote, id=f"current-{index+1}")
        records.append(record(spec, selected, evidence, context))
    for spec in LEGACY:
        selected, _ = locate(originals[spec["source_file"] + ".json"],
                             spec["anchor"], spec["heading"], spec["fragment"])
        records.append(record(spec, selected, evidence))
    return {"schema_version": 1, "domain": "holiday-methods", "private": True,
            "status": "Source foundation; v2 unassessed; human evidence pending.",
            "scope": deepcopy(SCOPE), "sources": evidence, "records": records,
            "observations": []}
