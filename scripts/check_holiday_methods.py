"""Independent holiday method audit: reopens complete originals before producer.

No producer parsers, locators, constants or expected projection are used.
The HTML tree binds a quote to its section, heading and (where relevant) the
immediately preceding prohibition list. This validates definitions, not cells.
"""
import hashlib
from html.parser import HTMLParser
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
INPUTS = ("travel-methods-crawl-0.html.json", "travel-methods-crawl-1.html.json",
          "travel-methods-crawl-2.html.json", "travel-qmi-crawl-0.html.json")
URLS = [
    "https://www.ons.gov.uk/peoplepopulationandcommunity/leisureandtourism/articles/improvingourtravelandtourismstatistics/october2026update",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/leisureandtourism/articles/improvingourtravelandtourismstatistics/september2026update",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/leisureandtourism/articles/traveltrends/2019",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/leisureandtourism/methodologies/internationalpassengersurveyqmi"
]
ASSERTIONS = [
    {
        "id": "qmi-revision",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "output-information",
        "heading": "1. Output information",
        "quote": "Last revised: 10 May 2023"
    },
    {
        "id": "qmi-visits",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-characteristics-of-the-international-passenger-survey-data",
        "heading": "Concepts and definitions",
        "quote": "As mentioned, IPS estimates are based on the number of visits. This means those entering or leaving the UK more than once in the same period are counted on each visit. The count of visits relates to UK residents returning to this country and to overseas residents leaving it. Other main definitions and concepts are available in our Travel trends articles."
    },
    {
        "id": "qmi-coverage",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-summary",
        "heading": "Limitations",
        "quote": "Additionally, about 90% of passengers entering and leaving the UK have a chance of being sampled in the survey. The remainder are either passengers travelling at night, when interviewing is suspended, or on those routes too small in volume, or too expensive, to be covered."
    },
    {
        "id": "qmi-additions",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "methods-used-to-produce-the-international-passenger-survey-data",
        "heading": "Additional sources of data",
        "quote": "The weighting referred to is conducted based on the routes sampled in the IPS. Unfortunately, as the IPS does not cover all passenger routes, additional figures are obtained from other sources and added to the totals derived from the IPS when producing estimates of overseas travel and tourism. These additions are:"
    },
    {
        "id": "qmi-revised-series",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "important-points",
        "heading": "3. Important points",
        "quote": "Methodological improvements relating to the survey's weighting were introduced for the 2019 estimates, and a revised series was published in May 2019 for the years 2009 to 2018."
    },
    {
        "id": "qmi-suspension",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "important-points",
        "heading": "3. Important points",
        "quote": "The IPS was suspended because of the Coronavirus (COVID-19) pandemic between 16 March 2020 and 18 January 2021. Therefore, high-level estimates of travel and tourism have been produced for April to December 2020 using alternative sources."
    },
    {
        "id": "qmi-tablets",
        "source_file": "travel-qmi-crawl-0.html",
        "anchor": "quality-summary",
        "heading": "Recent improvements",
        "quote": "In April 2018, the IPS moved to data collection using tablet computers, rather than paper-based questionnaires. More information is available about the rollout of data collection changes. The changes have improved efficiency and translations to different languages. They have allowed for greater flexibility when updating the survey, and there is evidence that survey respondents relate better to the \"one-question-per-screen\" layout. Time series analysis has been conducted and no discontinuities have been identified as a result of this change."
    },
    {
        "id": "trend-revised-series",
        "source_file": "travel-methods-crawl-2.html",
        "anchor": "impacts-of-the-new-ips-methodology",
        "heading": "6. Impacts of the new IPS methodology",
        "quote": "The figures presented in this article have been produced using an improved methodology, relating to adjusting the weights applied during the survey’s processing. The improved method has been used to produce the final travel and tourism estimates for 2019 and revised estimates for 2009 to 2018."
    },
    {
        "id": "trend-visits",
        "source_file": "travel-methods-crawl-2.html",
        "anchor": "glossary",
        "heading": "Visits",
        "quote": "The figures relate to the number of completed visits, not the number of visitors. Anyone entering or leaving more than once in the same period is counted on each visit."
    },
    {
        "id": "current-visits",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "glossary",
        "heading": "Visits",
        "quote": "The figures for visits relate to the number of completed visits, not the number of visitors. Anyone entering or leaving more than once in the same period would be counted on each visit."
    },
    {
        "id": "current-residents",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "glossary",
        "heading": "Visits outside the UK by residents of Great Britain or the UK",
        "quote": "Visits for a period of less than 12 months by people permanently residing in Great Britain or the UK, who may be of foreign nationality."
    },
    {
        "id": "current-no-adjustment",
        "source_file": "travel-methods-crawl-0.html",
        "anchor": "understanding-the-comparability-of-estimates-over-time",
        "heading": "How these figures can be used",
        "quote": "Therefore, users should not apply the estimated level shifts to create their own adjusted historical time series. Although the modelling approach provides a suitable framework for investigating discontinuities, a longer time series under the new methodology is needed before adjustments can be made robustly."
    }
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), "Holiday mismatch: " + label)


def decode(body):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate holiday JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite holiday JSON number: " + value)

    def floating(value):
        parsed = float(value)
        require(math.isfinite(parsed), "Nonfinite holiday JSON number")
        return parsed

    return json.loads(body, object_pairs_hook=unique, parse_constant=nonfinite, parse_float=floating)


def read(root, relative):
    require(isinstance(relative, str), "Invalid holiday path")
    part = Path(relative)
    require(bool(part.parts) and not part.is_absolute() and ".." not in part.parts, "Unsafe holiday path")
    root = Path(root).absolute()
    path = root / part
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Holiday symlinks forbidden")
    metadata = path.stat()
    require(stat.S_ISREG(metadata.st_mode) and path.resolve().is_relative_to(root.resolve()),
            "Holiday evidence must be a regular file within root")
    require(metadata.st_nlink == 1, "Holiday hard links forbidden")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def reopen(root):
    raw = read(root, REGISTER)
    require(digest(raw) == REGISTER_SHA256, "Pinned holiday register changed")
    register = decode(raw)
    same(register["schema_version"], 1, "register schema")
    same(register["domain"], "holiday-methods", "register domain")
    entries = register["sources"]
    require(len(entries) == 4 and {e["path"] for e in entries} ==
            {DIRECTORY + "/" + n for n in INPUTS}, "Holiday closed source path set changed")
    directory = Path(root) / DIRECTORY
    require(not any(p.is_symlink() for p in (directory, *directory.parents)), "Holiday symlinks forbidden")
    require({p.name for p in directory.iterdir()} == set(INPUTS), "Holiday source directory set changed")
    originals, evidence = {}, {}
    for name, url in zip(INPUTS, URLS):
        entry = next(e for e in entries if e["path"] == DIRECTORY + "/" + name)
        same(entry["url"], url, "exact official URL")
        stored = read(root, entry["path"])
        require(len(stored) == entry["stored_bytes"] and digest(stored) == entry["stored_sha256"],
                "Holiday stored hash/length mismatch")
        envelope = decode(stored)
        require(set(envelope) == {"encoding", "original_response"} and
                envelope["encoding"] == "utf-8" and type(envelope["original_response"]) is str,
                "Holiday envelope encoding/keys changed")
        body = envelope["original_response"].encode("utf-8")
        require(len(body) == entry["bytes"] and digest(body) == entry["sha256"],
                "Holiday recovered original hash/length mismatch")
        originals[name], evidence[name] = body, dict(entry)
    require(sum(len(b) for b in originals.values()) == 589144, "Holiday original byte total changed")
    require(sum(e["stored_bytes"] for e in evidence.values()) == 619860, "Holiday stored byte total changed")
    raw_quotes = read(root, QUOTES)
    require(digest(raw_quotes) == QUOTES_SHA256, "Pinned holiday quote register changed")
    quotes = decode(raw_quotes)
    same(quotes["schema_version"], 1, "quote schema")
    require(len(quotes["quotes"]) == 8, "Holiday mandatory quote set changed")
    return originals, evidence, quotes["quotes"]


class Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def text(self):
        return "".join(c.text() if isinstance(c, Node) else c for c in self.children)


class Tree(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node("root")
        self.feed(body.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def normalized(node):
    return " ".join(node.text().split())


def locate(tree, spec):
    sections = [n for n in tree.root.walk() if n.attrs.get("id") == spec["anchor"]]
    require(len(sections) == 1, "Holiday original anchor missing/ambiguous")
    nodes = list(sections[0].walk())
    heads = [n for n in nodes if re.fullmatch("h[2-6]", n.tag) and normalized(n) == spec["heading"]]
    require(len(heads) == 1, "Holiday original heading missing/ambiguous")
    start = nodes.index(heads[0])
    stop = next((i for i in range(start+1, len(nodes))
                 if re.fullmatch("h[2-6]", nodes[i].tag) and nodes[i].tag <= heads[0].tag), len(nodes))
    found = [n for n in nodes[start+1:stop] if n.tag == "p" and normalized(n) == spec["quote"]]
    require(len(found) == 1, "Holiday original quote missing/ambiguous")
    return found[0]


def prohibition(paragraph):
    item = paragraph.parent
    require(item is not None and item.tag == "li" and item.parent.tag == "ul",
            "Holiday comparison must be a list prohibition")
    listing = item.parent
    siblings = [n for n in listing.parent.children if isinstance(n, Node)]
    index = siblings.index(listing)
    require(index > 0 and siblings[index-1].tag == "p" and
            normalized(siblings[index-1]) == "Users should not:",
            "Holiday comparison prohibition polarity lost")


def check(projection, originals, evidence, quotes):
    trees = {name: Tree(body) for name, body in originals.items()}
    records = []
    specs = [dict(q, id="current-" + str(i+1)) for i, q in enumerate(quotes)] + ASSERTIONS
    for index, spec in enumerate(specs):
        name = spec["source_file"] + ".json"
        entry = evidence[name]
        if index < 8:
            same(spec["original_sha256"], entry["sha256"], "quote original hash")
        paragraph = locate(trees[name], spec)
        context = None
        if index == 6:
            prohibition(paragraph)
            context = "Users should not:"
        records.append({
            "id": spec["id"], "quote": normalized(paragraph), "context": context,
            "applies_to": "current-GB-methods-2024-2025" if name in INPUTS[:2] else "older-UK-methods",
            "source": {"path": entry["path"], "url": entry["url"], "sha256": entry["sha256"],
                       "anchor": spec["anchor"], "heading": spec["heading"]}})
    # Exact closed comparison also rejects fabricated observations, formulas,
    # denominators, provisional labels, removed caveats and cross-vintage claims.
    expected = {
        "schema_version": 1, "domain": "holiday-methods", "private": True,
        "status": "Source foundation; v2 unassessed; human evidence pending.",
        "scope": {
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
        },
        "sources": evidence, "records": records, "observations": []}
    same(projection, expected, "complete methods projection")
    return len(records)


def validate(root=ROOT, projection=None):
    originals, evidence, quotes = reopen(root)
    if projection is None:
        from holiday_methods_projection import project
        projection = project(root)
        same(projection, project(root), "deterministic in-memory projection")
    try:
        return check(projection, originals, evidence, quotes)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Malformed holiday methods projection/source") from error


if __name__ == "__main__":
    print(f"Verified {validate()} private holiday method definitions; no numeric observations")
