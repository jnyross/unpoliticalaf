"""Private work-method definitions. Returns memory only; never writes output.

Reopens the six complete official pages. Regex extraction is independent of the
checker's HTML tree. No work observations can be produced from these pages.
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
DIRECTORY = "data/life/sources/work-methods"
REGISTER = "data/life/work-methods-sources.json"
REGISTER_SHA256 = "f2cd4520c1c1bc345957967e8c3ef1d5eba312111d50699419b1332f400f9fc7"
FILES = ["current-qmi-crawl-2.html.json","current-qmi-crawl-3.html.json","aps-final-crawl-0.html.json","aps-final-crawl-2.html.json","quality-glossary-crawl-1.html.json","pandemic-soc-crawl-1.html.json"]
URLS = ["https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/annualpopulationsurveyapsqmi","https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/annualpopulationsurveyqualityupdateseptember2026","https://www.nomisweb.co.uk/articles/1304.aspx","https://www.nomisweb.co.uk/articles/1350.aspx","https://www.nomisweb.co.uk/datasets/aps218","https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/revisionofmiscodedoccupationaldataintheonslabourforcesurveyuk/january2021toseptember2022"]

def strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate work methods JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite work methods JSON number: " + value)

    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            return invalid(value)
        return parsed

    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)


def read(root, relative):
    if type(relative) is not str:
        raise ValueError("Invalid work methods path")
    part = Path(relative)
    if (part.is_absolute() or ".." in part.parts or not part.parts
            or str(part) != relative):
        raise ValueError("Unsafe work methods path")
    root = Path(root).absolute()
    path = root / part
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Work methods evidence must not contain symlinks")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Work methods evidence must be a regular file within root")
    if metadata.st_nlink != 1:
        raise ValueError("Work methods hard links forbidden")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def sources(root):
    raw = read(root, REGISTER)
    if digest(raw) != REGISTER_SHA256:
        raise ValueError("Pinned work methods register changed")
    register = strict_json(raw)
    entries = register["sources"]
    if (type(register["schema_version"]) is not int or register["schema_version"] != 1 or register["domain"] != "work-methods" or
            len(entries) != 6 or {e["path"] for e in entries} !=
            {DIRECTORY + "/" + name for name in FILES}):
        raise ValueError("Work methods closed source set changed")
    directory = Path(root) / DIRECTORY
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("Work methods source directory contains symlinks")
    if (not stat.S_ISDIR(directory.stat().st_mode) or
            {p.name for p in directory.iterdir()} != set(FILES)):
        raise ValueError("Work methods source directory set changed")
    originals, evidence = {}, {}
    for name, url in zip(FILES, URLS):
        entry = next(e for e in entries if e["path"] == DIRECTORY + "/" + name)
        if entry["url"] != url:
            raise ValueError("Work methods official URL changed")
        stored = read(root, entry["path"])
        if len(stored) != entry["stored_bytes"] or digest(stored) != entry["stored_sha256"]:
            raise ValueError("Work methods stored hash/length mismatch")
        envelope = strict_json(stored)
        if (type(envelope) is not dict or set(envelope) != {"encoding", "original_response"} or
                envelope["encoding"] != "utf-8" or type(envelope["original_response"]) is not str):
            raise ValueError("Work methods envelope encoding/keys changed")
        body = envelope["original_response"].encode("utf-8")
        if len(body) != entry["bytes"] or digest(body) != entry["sha256"]:
            raise ValueError("Work methods recovered original hash/length mismatch")
        name = Path(entry["path"]).name
        originals[name], evidence[name] = body, dict(entry)
    return originals, evidence


# Locators identify full paragraphs; the independent audit freezes exact wording.
SPECS = json.loads(r'''[
  {
    "id": "qmi-revised",
    "anchor": "output-information",
    "heading": "1. Output information",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "Last revised: 6 February 2026"
  },
  {
    "id": "qmi-household-uk",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "The Annual Population Survey (APS) is a continuous household survey"
  },
  {
    "id": "qmi-annual-periods",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "We publish quarterly APS datasets that include 12 months of"
  },
  {
    "id": "qmi-development",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "The ongoing challenges with response rates, levels, and weighting approach"
  },
  {
    "id": "qmi-communal-exceptions",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "APS coverage does not include communal establishments, except for NHS"
  },
  {
    "id": "qmi-armed-forces",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "Members of the armed forces are only included if they"
  },
  {
    "id": "qmi-under16",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "Workers aged under 16 years are not included."
  },
  {
    "id": "qmi-estimates",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Accuracy and reliability",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "As the APS is a sample survey, it provides estimates"
  },
  {
    "id": "qmi-employment",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "Employment includes those people who are aged 16 years or"
  },
  {
    "id": "qmi-employment-paid",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "did some paid work in the reference week (whether as"
  },
  {
    "id": "qmi-employment-temporary",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "had a job that they were temporarily away from (for"
  },
  {
    "id": "qmi-employment-training",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "are on government-supported training and employment programmes"
  },
  {
    "id": "qmi-employment-unpaid",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "applies_to": "aps-methods-qmi-2026",
    "file": "current-qmi-crawl-2.html.json",
    "fragment": "are doing unpaid family work (that is, working in a"
  },
  {
    "id": "quality-vintage",
    "anchor": "cite-this-page",
    "heading": "10. Cite this page",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "Office for National Statistics (ONS), released 15 September 2026, ONS"
  },
  {
    "id": "quality-response",
    "anchor": "longer-term-quality-of-the-aps",
    "heading": "5. Longer-term quality of the APS",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "The number of interviews achieved for the Annual Population Survey"
  },
  {
    "id": "quality-caution",
    "anchor": "longer-term-quality-of-the-aps",
    "heading": "5. Longer-term quality of the APS",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "We continue to advise users of APS data to use"
  },
  {
    "id": "quality-small-detail",
    "anchor": "what-this-means-for-users",
    "heading": "6. What this means for users",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "Estimates for larger populations and broader geographical areas will generally"
  },
  {
    "id": "quality-no-small-difference-inference",
    "anchor": "what-this-means-for-users",
    "heading": "6. What this means for users",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "avoid assuming that small differences between places, groups or time"
  },
  {
    "id": "quality-outdated-weights",
    "anchor": "detailed-collection-changes-that-could-cause-discontinuity",
    "heading": "2022-based weighting",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "Important LFS datasets have undergone more recent changes to their"
  },
  {
    "id": "quality-pandemic",
    "anchor": "detailed-collection-changes-that-could-cause-discontinuity",
    "heading": "The coronavirus (COVID-19) pandemic",
    "tag": "p",
    "applies_to": "aps-quality-update-2026",
    "file": "current-qmi-crawl-3.html.json",
    "fragment": "Levels and quality of response to all waves and samples"
  },
  {
    "id": "notice2022-date",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "applies_to": "aps-2022-notice",
    "file": "aps-final-crawl-0.html.json",
    "fragment": "The Annual Population Survey datasets were updated on 16 August"
  },
  {
    "id": "notice2022-rti-ni",
    "anchor": "page-wrap",
    "heading": "Reweighting",
    "tag": "p",
    "applies_to": "aps-2022-notice",
    "file": "aps-final-crawl-0.html.json",
    "fragment": "Annual Population Survey (APS) responses have been reweighted for periods"
  },
  {
    "id": "notice2022-wales",
    "anchor": "page-wrap",
    "heading": "Reweighting",
    "tag": "p",
    "applies_to": "aps-2022-notice",
    "file": "aps-final-crawl-0.html.json",
    "fragment": "The ONS has identified an error in the calculation of"
  },
  {
    "id": "notice2023-date",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "applies_to": "aps-2023-notice",
    "file": "aps-final-crawl-2.html.json",
    "fragment": "The Annual Population Survey (APS) datasets were updated on 15"
  },
  {
    "id": "notice2023-aps-range",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "applies_to": "aps-2023-notice",
    "file": "aps-final-crawl-2.html.json",
    "fragment": "Occupation revisions: occupational estimates have been revised back to the"
  },
  {
    "id": "coding-lfs-title-range",
    "anchor": "cite-this-article",
    "heading": "7. Cite this article",
    "tag": "p",
    "applies_to": "lfs-coding-paper-2023",
    "file": "pandemic-soc-crawl-1.html.json",
    "fragment": "Office for National Statistics (ONS), released 11 July 2023, ONS"
  },
  {
    "id": "coding-lfs-comparison",
    "anchor": "anticipated-changes-in-the-revised-occupational-data",
    "heading": "4. Anticipated changes in the revised occupational data",
    "tag": "p",
    "applies_to": "lfs-coding-paper-2023",
    "file": "pandemic-soc-crawl-1.html.json",
    "fragment": "The analysis presented in this update is based on comparisons"
  },
  {
    "id": "coding-new-data",
    "anchor": "future-developments",
    "heading": "5. Future developments",
    "tag": "p",
    "applies_to": "lfs-coding-paper-2023",
    "file": "pandemic-soc-crawl-1.html.json",
    "fragment": "The issue in the coding frame resulting in this coding"
  },
  {
    "id": "coding-reprocessing",
    "anchor": "future-developments",
    "heading": "5. Future developments",
    "tag": "p",
    "applies_to": "lfs-coding-paper-2023",
    "file": "pandemic-soc-crawl-1.html.json",
    "fragment": "With all Standard Occupational Classification (SOC) codes that were identified"
  },
  {
    "id": "aps218-coverage",
    "anchor": "page-wrap",
    "heading": "Coverage",
    "tag": "p",
    "applies_to": "aps218-dataset-metadata",
    "file": "quality-glossary-crawl-1.html.json",
    "fragment": "United Kingdom"
  },
  {
    "id": "aps218-units",
    "anchor": "page-wrap",
    "heading": "Units",
    "tag": "p",
    "applies_to": "aps218-dataset-metadata",
    "file": "quality-glossary-crawl-1.html.json",
    "fragment": "Persons"
  }
]''')
SCOPE = json.loads(r'''{
  "population": "UK household survey employment: people aged 16 years or over; communal establishments are excluded except stated NHS housing and student exceptions; Armed Forces only in private accommodation.",
  "measure": "Survey estimates of people, not exact headcounts or employee jobs.",
  "periods": "Calendar years must be selected from separately retained observations; rolling annual periods are not calendar years.",
  "quality": "Official statistics in development; declining response, smaller samples, outdated population weights and possible discontinuities require adjacent cautions.",
  "confidence": "Confidence 20701 remains literal metadata only; no retained definition binds it to a 95% half-width, error bars or significance.",
  "revision_limits": [
    "2022 RTI reweighting and Northern Ireland non-response adjustment begin October 2020–September 2021; the separate Wales error affects April 2019–March 2020 to July 2020–June 2021, with UK figures largely unaffected.",
    "The 2023 Nomis APS notice revises occupational estimates back to April 2020–March 2021; the ONS coding paper's January 2021–September 2022 title is LFS-specific and is not proof of the APS affected range.",
    "Historical weighting and coding revision annotations remain incomplete. These six method pages do not prove that SOC2010 calendar 2021 received later revisions, that affected 2020 counts were corrected, or that overlap differences are caused by SOC alone.",
    "APS218 dataset page is not a complete historical revision audit or a definition of Confidence 20701."
  ],
  "unverified": [
    "Numeric cells, calendar selections, exact code/label bindings, observation statuses and reconciliation require the separate work-data foundation.",
    "APS people and ASHE employee jobs on adult rates have different populations and must not be combined into a ratio; ASHE coverage is a frozen-contract requirement, not independently validated by these pages.",
    "No numerical observations, interpolation, uncertainty calculation, significance claim or causal decomposition is produced.",
    "Frozen-contract cross-reference requirements awaiting the separate count/catalogue foundation: APS210 last update 12 April 2022 predates both notices; APS218's 2021 catalogue entry is incomplete; version 0 does not prove unrevised; APS210 2011–2012 weighting vintage is unknown. Counts and catalogues are absent from this six-page set, so these historical details are not independently verified here."
  ],
  "frozen_contract_pending_notes": [
    "Beside SOC2010 calendar 2021: “Nomis later reported an occupation coding error affecting periods from April 2020–March 2021; this SOC2010 dataset records no revision for 2021.”",
    "Beside affected 2020 counts: “Nomis reported a Wales weighting error affecting this period; UK figures largely unaffected; no revision recorded in this dataset.”",
    "These required later-UI notes await the separate count/catalogue foundation; neither proves whether a correction occurred."
  ],
  "quality_definitions": {
    "confidence_20701": null,
    "suppression": null,
    "indicative": null
  }
}''')


def text(html):
    return " ".join(unescape(re.sub(r"<[^>]*>", "", html)).split())


def locate(body, anchor, heading, tag, fragment):
    """Bind a paragraph to its div and heading; no whole-page phrase search."""
    html = body.decode("utf-8")
    openings = list(re.finditer(r'<div\b[^>]*\bid="' + re.escape(anchor) + r'"[^>]*>', html))
    if len(openings) != 1:
        raise ValueError("Work methods anchor missing/ambiguous")
    opening = openings[0]
    depth, end = 1, None
    for token in re.finditer(r"</?div\b[^>]*>", html[opening.end():], re.I):
        depth += -1 if token[0].startswith("</") else 1
        if depth == 0:
            end = opening.end() + token.start()
            break
    if end is None:
        raise ValueError("Work methods div not closed")
    section = html[opening.end():end]
    headings = list(re.finditer(r"<h([1-6])\b[^>]*>([\s\S]*?)</h\1>", section))
    if heading is None:
        # Nomis notice lead, before any in-body heading.
        block = section[:headings[0].start()] if headings else section
    else:
        matches = [i for i, h in enumerate(headings) if text(h[2]) == heading]
        if len(matches) != 1:
            raise ValueError("Work methods heading missing/ambiguous")
        index = matches[0]
        start = headings[index]
        stop = next((h.start() for h in headings[index+1:]
                     if int(h[1]) <= int(start[1])), len(section))
        block = section[start.end():stop]
    candidates = [text(m[1]) for m in re.finditer(
        r"<" + tag + r"\b[^>]*>([\s\S]*?)</" + tag + ">", block)]
    found = [candidate for candidate in candidates if candidate.startswith(fragment)]
    if len(found) != 1:
        raise ValueError("Work methods quote missing/ambiguous")
    return found[0]


def project(root=ROOT):
    originals, evidence = sources(root)
    records = []
    for spec in SPECS:
        entry = evidence[spec["file"]]
        quote = locate(originals[spec["file"]], spec["anchor"], spec["heading"],
                       spec["tag"], spec["fragment"])
        records.append({
            "id": spec["id"], "quote": quote, "applies_to": spec["applies_to"],
            "source": {"path": entry["path"], "url": entry["url"], "sha256": entry["sha256"],
                       "anchor": spec["anchor"], "heading": spec["heading"], "tag": spec["tag"]}})
    return {"schema_version": 1, "domain": "work-methods", "private": True,
            "status": "Source foundation; v2 unassessed; human evidence pending.",
            "scope": deepcopy(SCOPE), "sources": evidence, "records": records,
            "observations": []}
