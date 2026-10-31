"""Independent work-methods audit; reopens complete retained HTML originals.

No producer parser, locator, constants or expected output are used as an oracle.
This source foundation validates definitions and warnings, never numeric cells.
"""
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/life/sources/work-methods"
REGISTER = "data/life/work-methods-sources.json"
REGISTER_SHA256 = "f2cd4520c1c1bc345957967e8c3ef1d5eba312111d50699419b1332f400f9fc7"
INPUTS = [
    "current-qmi-crawl-2.html.json",
    "current-qmi-crawl-3.html.json",
    "aps-final-crawl-0.html.json",
    "aps-final-crawl-2.html.json",
    "quality-glossary-crawl-1.html.json",
    "pandemic-soc-crawl-1.html.json"
]
URLS = [
    "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/annualpopulationsurveyapsqmi",
    "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/annualpopulationsurveyqualityupdateseptember2026",
    "https://www.nomisweb.co.uk/articles/1304.aspx",
    "https://www.nomisweb.co.uk/articles/1350.aspx",
    "https://www.nomisweb.co.uk/datasets/aps218",
    "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/revisionofmiscodedoccupationaldataintheonslabourforcesurveyuk/january2021toseptember2022"
]
ASSERTIONS = json.loads(r'''[
  {
    "id": "qmi-revised",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "output-information",
    "heading": "1. Output information",
    "tag": "p",
    "quote": "Last revised: 6 February 2026",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-household-uk",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "quote": "The Annual Population Survey (APS) is a continuous household survey covering the UK, with the aim of providing estimates of main social and labour market variables between censuses, down to a local-area level.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-annual-periods",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "quote": "We publish quarterly APS datasets that include 12 months of survey data for overlapping annual periods (January to December, April to March, July to June, and October to September); the current achieved sample size is approximately 80,000 UK households and 175,000 individuals per year, as of our October 2024 to September 2025 dataset.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-development",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "important-points",
    "heading": "3. Important points",
    "tag": "p",
    "quote": "The ongoing challenges with response rates, levels, and weighting approach mean that both LFS- and APS-based labour market statistics will be considered official statistics in development until further review; estimates of change should be treated with additional caution because of the increased volatility of LFS and APS estimates (for more information, see our Labour market in the regions of the UK statistical bulletins).",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-communal-exceptions",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "quote": "APS coverage does not include communal establishments, except for NHS housing (though the relevant sample frame has not been updated since its inception), and students in boarding schools and halls of residence.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-armed-forces",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "quote": "Members of the armed forces are only included if they live in private accommodation.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-under16",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-summary",
    "heading": "Limitations",
    "tag": "p",
    "quote": "Workers aged under 16 years are not included.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-estimates",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Accuracy and reliability",
    "tag": "p",
    "quote": "As the APS is a sample survey, it provides estimates of population characteristics rather than exact measures. In principle, many random samples could be drawn and each would give different results. This is because each sample would include different people who would give different answers to the questions asked. The spread of these results is the sampling variability.",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-employment",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "quote": "Employment includes those people who are aged 16 years or over who:",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-employment-paid",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "quote": "did some paid work in the reference week (whether as an employee or self-employed)",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-employment-temporary",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "quote": "had a job that they were temporarily away from (for example, on holiday)",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-employment-training",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "quote": "are on government-supported training and employment programmes",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "qmi-employment-unpaid",
    "source_file": "current-qmi-crawl-2.html.json",
    "anchor": "quality-characteristics-of-the-data",
    "heading": "Employment",
    "tag": "p",
    "quote": "are doing unpaid family work (that is, working in a family business)",
    "applies_to": "aps-methods-qmi-2026"
  },
  {
    "id": "quality-vintage",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "cite-this-page",
    "heading": "10. Cite this page",
    "tag": "p",
    "quote": "Office for National Statistics (ONS), released 15 September 2026, ONS website, supporting methodology article, Annual Population Survey quality update: September 2026",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-response",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "longer-term-quality-of-the-aps",
    "heading": "5. Longer-term quality of the APS",
    "tag": "p",
    "quote": "The number of interviews achieved for the Annual Population Survey (APS), and therefore the size of the dataset available for analysis, was slowly decreasing over time as shown in Figure 1. The longer-term reduction, between 2006 and 2020 in particular, reflects the challenge of falling response rates for household surveys. This trend has been experienced by other comparable countries. This was one of the main reasons for the Office for National Statistics (ONS) developing the Transformed Labour Force Survey (TLFS) as the sustainable strategic solution to declining participation rates and quality issues affecting traditional social surveys.",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-caution",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "longer-term-quality-of-the-aps",
    "heading": "5. Longer-term quality of the APS",
    "tag": "p",
    "quote": "We continue to advise users of APS data to use caution when analysing results and ensure they calculate measures of accuracy to determine whether results are sufficiently reliable for their analytical purposes.",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-small-detail",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "what-this-means-for-users",
    "heading": "6. What this means for users",
    "tag": "p",
    "quote": "Estimates for larger populations and broader geographical areas will generally be based on more responses and therefore be less affected by the reduced sample. Users should take greater care when interpreting estimates for small areas, small population groups and detailed breakdowns, where estimates may be more uncertain and more likely to vary between periods, or where results may need to be suppressed to maintain confidentiality.",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-no-small-difference-inference",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "what-this-means-for-users",
    "heading": "6. What this means for users",
    "tag": "p",
    "quote": "avoid assuming that small differences between places, groups or time periods represent meaningful change unless explicit measures of change have been calculated",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-outdated-weights",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "detailed-collection-changes-that-could-cause-discontinuity",
    "heading": "2022-based weighting",
    "tag": "p",
    "quote": "Important LFS datasets have undergone more recent changes to their weighting, most recently incorporating adjusted population statistics labelled 2024-based weights, as explained in our Impact of reweighting on Labour Force Survey key indicators: February 2024 article and in our Impact of reweighting on Labour Force Survey key indicators: December 2024 article. However, APS datasets have not been updated since their 2022-based weights. This means that APS results are not fully consistent with LFS results and are not fully consistent with current population statistics.",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "quality-pandemic",
    "source_file": "current-qmi-crawl-3.html.json",
    "anchor": "detailed-collection-changes-that-could-cause-discontinuity",
    "heading": "The coronavirus (COVID-19) pandemic",
    "tag": "p",
    "quote": "Levels and quality of response to all waves and samples of the LFS from 2020 were affected by the coronavirus (COVID-19) pandemic. We undertook a variety of measures to mitigate the effects, including increasing the size of the issued sample and changing data collection from face-to-face-first to telephone-first, utilising services to find telephone numbers to contact respondents. Methodological adjustments have been made, and analysis conducted, on LFS and APS results following these changes to ensure results are as accurate and consistent as possible. However, there were effects on the levels and type of response during this time that may have affected the quality of LFS and APS results.",
    "applies_to": "aps-quality-update-2026"
  },
  {
    "id": "notice2022-date",
    "source_file": "aps-final-crawl-0.html.json",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "quote": "The Annual Population Survey datasets were updated on 16 August 2022 with new figures for the Apr 2021 - Mar 2022 survey period.",
    "applies_to": "aps-2022-notice"
  },
  {
    "id": "notice2022-rti-ni",
    "source_file": "aps-final-crawl-0.html.json",
    "anchor": "page-wrap",
    "heading": "Reweighting",
    "tag": "p",
    "quote": "Annual Population Survey (APS) responses have been reweighted for periods from October 2020 to September 2021 onwards using updated HM Revenue and Customs (HMRC) Real Time Information (RTI) data. The non-response bias adjustment, previously implemented for England, Wales and Scotland data, has now also been applied to Northern Ireland data.",
    "applies_to": "aps-2022-notice"
  },
  {
    "id": "notice2022-wales",
    "source_file": "aps-final-crawl-0.html.json",
    "anchor": "page-wrap",
    "heading": "Reweighting",
    "tag": "p",
    "quote": "The ONS has identified an error in the calculation of population weights in the Annual Population Survey (APS) in some recent periods, affecting the age breakdown of the population in Wales to a small extent. The most recent datasets (Oct 2020-Sep 2021 and onwards) are not affected, and breakdowns for the UK as a whole would be largely unaffected. The affected annual datasets are for Apr 2019-Mar 2020 to Jul 2020-Jun 2021 inclusive, and these datasets will need to be revised. The ONS anticipates this will be done in the labour market statistics release due on 13 September 2022.",
    "applies_to": "aps-2022-notice"
  },
  {
    "id": "notice2023-date",
    "source_file": "aps-final-crawl-2.html.json",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "quote": "The Annual Population Survey (APS) datasets were updated on 15 August 2023 with new figures for the Apr 2022 - Mar 2023 survey period. At the same time, occupational estimates have been revised and new Related Vocational Qualification (RFQ) estimates added.",
    "applies_to": "aps-2023-notice"
  },
  {
    "id": "notice2023-aps-range",
    "source_file": "aps-final-crawl-2.html.json",
    "anchor": "page-wrap",
    "heading": null,
    "tag": "p",
    "quote": "Occupation revisions: occupational estimates have been revised back to the Apr 2020 - Mar 2021 period to correct the coding error identified in the SOC estimates. For more detail on the new methodology used and its impact, see Revision of miscoded occupational data in the ONS Labour Force Survey.",
    "applies_to": "aps-2023-notice"
  },
  {
    "id": "coding-lfs-title-range",
    "source_file": "pandemic-soc-crawl-1.html.json",
    "anchor": "cite-this-article",
    "heading": "7. Cite this article",
    "tag": "p",
    "quote": "Office for National Statistics (ONS), released 11 July 2023, ONS website, article, Revision of miscoded occupational data in the ONS Labour Force Survey, UK: January 2021 to September 2022",
    "applies_to": "lfs-coding-paper-2023"
  },
  {
    "id": "coding-lfs-comparison",
    "source_file": "pandemic-soc-crawl-1.html.json",
    "anchor": "anticipated-changes-in-the-revised-occupational-data",
    "heading": "4. Anticipated changes in the revised occupational data",
    "tag": "p",
    "quote": "The analysis presented in this update is based on comparisons of the averages of weighted counts for main job taken from the Labour Force Survey (LFS) data from 2019 to 2020 (SOC2010 mapped to SOC2020), the original data for main jobs for LFS from January to March 2021, and the revised data for main jobs for LFS from January to March 2021.",
    "applies_to": "lfs-coding-paper-2023"
  },
  {
    "id": "coding-new-data",
    "source_file": "pandemic-soc-crawl-1.html.json",
    "anchor": "future-developments",
    "heading": "5. Future developments",
    "tag": "p",
    "quote": "The issue in the coding frame resulting in this coding error has been resolved and new occupational data collected from October 2022 is therefore not affected by the coding error anymore.",
    "applies_to": "lfs-coding-paper-2023"
  },
  {
    "id": "coding-reprocessing",
    "source_file": "pandemic-soc-crawl-1.html.json",
    "anchor": "future-developments",
    "heading": "5. Future developments",
    "tag": "p",
    "quote": "With all Standard Occupational Classification (SOC) codes that were identified as highly impacted by the coding error having been recoded, the focus then turned to re-processing the Labour Force Survey (LFS) and Annual Population Survey (APS) microdata. This involved revising relevant derived variables and re-running the income weight, which uses SOC codes in population calibrations. All relevant aggregate tables for the LFS and APS have subsequently been updated.",
    "applies_to": "lfs-coding-paper-2023"
  },
  {
    "id": "aps218-coverage",
    "source_file": "quality-glossary-crawl-1.html.json",
    "anchor": "page-wrap",
    "heading": "Coverage",
    "tag": "p",
    "quote": "United Kingdom",
    "applies_to": "aps218-dataset-metadata"
  },
  {
    "id": "aps218-units",
    "source_file": "quality-glossary-crawl-1.html.json",
    "anchor": "page-wrap",
    "heading": "Units",
    "tag": "p",
    "quote": "Persons",
    "applies_to": "aps218-dataset-metadata"
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


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), "Work methods mismatch: " + label)


def decode(body):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate work methods JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite work methods JSON number: " + value)

    def floating(value):
        parsed = float(value)
        require(math.isfinite(parsed), "Nonfinite work methods JSON number")
        return parsed

    return json.loads(body, object_pairs_hook=unique, parse_constant=nonfinite,
                      parse_float=floating)


def read(root, relative):
    require(type(relative) is str, "Invalid work methods path")
    part = Path(relative)
    require(bool(part.parts) and not part.is_absolute() and ".." not in part.parts
            and str(part) == relative, "Unsafe work methods path")
    root = Path(root).absolute()
    path = root / part
    require(not any(p.is_symlink() for p in (path, *path.parents)),
            "Work methods symlinks forbidden")
    metadata = path.stat()
    require(stat.S_ISREG(metadata.st_mode) and path.resolve().is_relative_to(root.resolve()),
            "Work methods evidence must be a regular file within root")
    require(metadata.st_nlink == 1, "Work methods hard links forbidden")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def reopen(root):
    raw = read(root, REGISTER)
    require(digest(raw) == REGISTER_SHA256, "Pinned work methods register changed")
    register = decode(raw)
    same(register["schema_version"], 1, "register schema")
    same(register["domain"], "work-methods", "register domain")
    entries = register["sources"]
    require(type(entries) is list and len(entries) == 6 and
            {e["path"] for e in entries} == {DIRECTORY + "/" + n for n in INPUTS},
            "Work methods closed exactly-six source set changed")
    directory = Path(root).absolute() / DIRECTORY
    require(not any(p.is_symlink() for p in (directory, *directory.parents)),
            "Work methods symlinks forbidden")
    require(stat.S_ISDIR(directory.stat().st_mode) and
            {p.name for p in directory.iterdir()} == set(INPUTS),
            "Work methods source directory set changed")
    originals, evidence = {}, {}
    for name, url in zip(INPUTS, URLS):
        entry = next(e for e in entries if e["path"] == DIRECTORY + "/" + name)
        same(entry["url"], url, "exact official URL")
        stored = read(root, entry["path"])
        require(len(stored) == entry["stored_bytes"] and digest(stored) == entry["stored_sha256"],
                "Work methods stored hash/length mismatch")
        envelope = decode(stored)
        require(type(envelope) is dict and set(envelope) == {"encoding", "original_response"}
                and envelope["encoding"] == "utf-8" and type(envelope["original_response"]) is str,
                "Work methods envelope encoding/keys changed")
        body = envelope["original_response"].encode("utf-8")
        require(len(body) == entry["bytes"] and digest(body) == entry["sha256"],
                "Work methods recovered original hash/length mismatch")
        originals[name], evidence[name] = body, dict(entry)
    require(sum(map(len, originals.values())) == 413349,
            "Work methods original byte total changed")
    require(sum(e["stored_bytes"] for e in evidence.values()) == 445383,
            "Work methods stored byte total changed")
    return originals, evidence


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
    require(len(sections) == 1, "Work methods original anchor missing/ambiguous")
    nodes = list(sections[0].walk())
    if spec["heading"] is None:
        start = 0
        stop = next((i for i, n in enumerate(nodes) if re.fullmatch("h[1-6]", n.tag)),
                    len(nodes))
    else:
        heads = [n for n in nodes if re.fullmatch("h[1-6]", n.tag)
                 and normalized(n) == spec["heading"]]
        require(len(heads) == 1, "Work methods original heading missing/ambiguous")
        start = nodes.index(heads[0])
        stop = next((i for i in range(start + 1, len(nodes))
                     if re.fullmatch("h[1-6]", nodes[i].tag)
                     and int(nodes[i].tag[1]) <= int(heads[0].tag[1])), len(nodes))
    found = [n for n in nodes[start + 1:stop]
             if n.tag == spec["tag"] and normalized(n) == spec["quote"]]
    require(len(found) == 1, "Work methods original quote missing/ambiguous: " + spec["id"])
    return found[0]


def employment_list(paragraph, tree):
    # Preserve the age-qualified intro and all four inclusion groups as one list.
    siblings = [n for n in paragraph.parent.children if isinstance(n, Node)]
    index = siblings.index(paragraph)
    require(index + 1 < len(siblings) and siblings[index + 1].tag == "ul",
            "Work methods employment inclusion list detached")
    listing = siblings[index + 1]
    items = [n for n in listing.children if isinstance(n, Node)]
    require(len(items) == 4 and all(n.tag == "li" for n in items),
            "Work methods employment inclusion list changed")
    expected = [s["quote"] for s in ASSERTIONS if s["id"].startswith("qmi-employment-")]
    same([normalized(n) for n in items], expected, "complete employment inclusion list")


def check(projection, originals, evidence):
    same(sorted(originals), sorted(INPUTS), "reopened original set")
    same(sorted(evidence), sorted(INPUTS), "reopened evidence set")
    trees = {name: Tree(body) for name, body in originals.items()}
    records = []
    for spec in ASSERTIONS:
        name = spec["source_file"]
        entry = evidence[name]
        paragraph = locate(trees[name], spec)
        if spec["id"] == "qmi-employment":
            employment_list(paragraph, trees[name])
        records.append({
            "id": spec["id"], "quote": normalized(paragraph), "applies_to": spec["applies_to"],
            "source": {"path": entry["path"], "url": entry["url"], "sha256": entry["sha256"],
                       "anchor": spec["anchor"], "heading": spec["heading"], "tag": spec["tag"]}})
    # Exact closure rejects added observations, inferred confidence definitions,
    # removed cautions, fabricated periods, causal decompositions and numeric ratios.
    expected = {
        "schema_version": 1, "domain": "work-methods", "private": True,
        "status": "Source foundation; v2 unassessed; human evidence pending.",
        "scope": SCOPE, "sources": evidence, "records": records, "observations": []}
    same(projection, expected, "complete private methods projection")
    return len(records)


def validate(root=ROOT, projection=None):
    try:
        originals, evidence = reopen(root)
        if projection is None:
            from work_methods_projection import project
            projection = project(root)
            same(projection, project(root), "deterministic in-memory projection")
        return check(projection, originals, evidence)
    except (KeyError, TypeError, IndexError, OSError, UnicodeError) as error:
        raise ValueError("Malformed work methods projection/source") from error


if __name__ == "__main__":
    print(f"Verified {validate()} private work method definitions; no numeric observations")
