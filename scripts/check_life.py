"""Independent life audit, reopening retained DfE originals before every check.

No life/school producer readers, arithmetic, maps or renderers are used as an
oracle. The older independent school audit owns its complete foundation schema.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from html.parser import HTMLParser
from pathlib import Path
import json

import check_schools as school

ROOT = Path(__file__).resolve().parents[1]
PHASE_ORDER = ("5kyxd", "tfHTE", "TaWMP", "cDwC3")
MISSING = "No retained school observation for one or both anchors."
FORMULA = "right pupils / right classes - left pupils / left classes"


def rounded(value, signed=False):
    return format(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
                  "+.1f" if signed else ".1f")


def _expected(data, originals, evidence):
    school.check(data["schools"], originals, evidence)
    query = school.decode(originals[school.INPUTS[0]])
    grid = {(int(r["timePeriod"]["period"].split("/")[1]),
             r["filters"]["5cGdi"], r["filters"]["cAd31"]): (i, r)
            for i, r in enumerate(query["results"])}
    periods = {int(p["period"].split("/")[1]): p["period"]
               for p in school.decode(originals[school.INPUTS[1]])["timePeriods"]}

    def operand(anchor, phase, code):
        i, row = grid[(anchor, phase, "XdTUf")]
        return {"raw": row["values"][code], "indicator": code,
                "anchor": anchor, "phase": phase,
                "source": {"path": evidence[school.INPUTS[0]]["path"],
                           "sha256": evidence[school.INPUTS[0]]["sha256"],
                           "locator": "/results/" + str(i) + "/values/" + code}}

    def mean(year, phase):
        _, row = grid[(year, phase, "XdTUf")]
        return school.number(row["values"]["QtxWw"], True) / school.number(row["values"]["EAicq"], True)

    anchors = []
    for year in range(2008, 2027):
        available = year in periods
        anchors.append({
            "year": year, "available": available, "period": periods.get(year),
            "census": (f"January {year}; third Thursday (methodology rule, not an individually reported date)"
                       if available else None),
            "previous": year - 1 if year > 2008 else None,
            "next": year + 1 if year < 2026 else None,
            "nearest": None if available else min(periods, key=lambda y: (abs(y - year), y))})
    comparisons = []
    for left in range(2008, 2027):
        for right in range(2008, 2027):
            for phase in PHASE_ORDER:
                available = left in periods and right in periods
                a = mean(left, phase) if left in periods else None
                b = mean(right, phase) if right in periods else None
                comparisons.append({
                    "id": f"{left}:{right}:{phase}", "from": left, "to": right,
                    "phase": phase, "available": available, "reason": None if available else MISSING,
                    "from_period": periods.get(left), "to_period": periods.get(right),
                    "left": rounded(a) if available else None,
                    "right": rounded(b) if available else None,
                    "display": rounded(b - a, signed=True) if available else None,
                    "unit": "pupils per class", "formula": FORMULA,
                    "operands": ([operand(right, phase, "QtxWw"), operand(right, phase, "EAicq"),
                                  operand(left, phase, "QtxWw"), operand(left, phase, "EAicq")]
                                 if available else [])})
    return {
        "schema_version": 1, "domain": "life", "private": False, "default_anchor": 2026,
        "topics": {"schools": "available", "work": "not yet built", "earnings": "not yet built",
                   "housing": "not yet built", "holidays": "not yet built"},
        "schools": data["schools"], "anchors": anchors, "comparisons": comparisons}


def _validate_data(data, originals, evidence):
    expected = _expected(data, originals, evidence)
    school.same(data, expected, "complete life projection")
    return expected


class Node:
    def __init__(self, tag="", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
        self.parent = None

    @property
    def text(self):
        return " ".join("".join(c.text if isinstance(c, Node) else c for c in self.children).split())

    def find(self, tag=None, **attrs):
        matches = []
        for child in self.children:
            if isinstance(child, Node):
                if (tag is None or child.tag == tag) and all(
                        key in child.attrs and (value is None or child.attrs[key] == value)
                        for key, value in attrs.items()):
                    matches.append(child)
                matches.extend(child.find(tag, **attrs))
        return matches


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        school.require(len(dict(attrs)) == len(attrs), "Life duplicate HTML attribute")
        node = Node(tag, attrs)
        node.parent = self.stack[-1]
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        school.require(len(self.stack) > 1 and self.stack[-1].tag == tag,
                       "Life malformed HTML nesting: " + tag)
        self.stack.pop()

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def one(node, tag=None, **attrs):
    matches = node.find(tag, **attrs)
    school.require(len(matches) == 1, "Life missing/duplicate DOM field: " + repr((tag, attrs)))
    return matches[0]


def text_is(node, expected, label):
    school.same(node.text, " ".join(expected.split()), "life DOM " + label)


def _validate_page(data, html, originals, evidence):
    document = Document(html)
    dom = document.root
    school.require(len(html.encode("utf-8")) < 500000, "Life HTML exceeds strict byte cap")
    school.require(len(document.stack) == 1, "Life unclosed HTML element")
    ids = [n.attrs["id"] for n in dom.find(id=None)]
    school.require(len(ids) == len(set(ids)), "Life duplicate DOM id")
    # The complete text and provenance checks below are deliberately based on
    # independently audited rows, never on hidden numeric data attributes alone.
    _check_structure(dom)
    rows = data["schools"]["rows"]
    row_index = {(r["anchor"], r["filters"]["5cGdi"], r["filters"]["cAd31"]): r for r in rows}
    seen = set()
    annual = dom.find("tr", **{"data-school-row": None})
    school.require(len(annual) == 176, "Life annual DOM row count")
    for node in annual:
        key = (int(node.attrs["data-anchor"]), node.attrs["data-phase"], node.attrs["data-band"])
        school.require(key in row_index and key not in seen, "Life annual DOM grid identity")
        seen.add(key)
        row = row_index[key]
        cells = [c for c in node.children if isinstance(c, Node) and c.tag in ("td", "th")]
        school.require(len(cells) == 7, "Life annual DOM cell count")
        text_is(cells[0], row["phase"], "phase")
        text_is(cells[1], row["band"], "band")
        measures = [
            ("classes", row["published"]["EAicq"]["display"]),
            ("pupils", row["published"]["QtxWw"]["display"]),
            ("mean", row["derived"]["mean"]["display"]),
            ("class_share", row["derived"]["class_share"]["display"]),
            ("pupil_share", row["derived"]["pupil_share"]["display"])]
        for cell, (measure, value) in zip(cells[2:], measures):
            span = one(cell, "span", **{"data-measure": measure})
            text_is(cell, value, measure + " complete cell")
            text_is(span, value, measure)
            school.same(span.attrs.get("data-value"), value, "life DOM numeric attribute")
            if measure in ("classes", "pupils"):
                indicator = "EAicq" if measure == "classes" else "QtxWw"
                refs = row["published"][indicator]["source"]["locator"]
            else:
                refs = " ".join(o["source"]["locator"] for o in row["derived"][measure]["operands"])
            school.same(span.attrs.get("data-ref"), refs, "life annual operand references")
    school.require(seen == set(row_index), "Life annual DOM grid incomplete")
    pairs = {p["id"]: p for p in data["comparisons"]}
    pair_rows = dom.find("tr", **{"data-school-pair": None})
    expected_keys = {p["id"] for p in data["comparisons"] if p["available"] and p["from"] < p["to"]}
    seen_pairs = set()
    for node in pair_rows:
        key = ":".join((node.attrs["data-from"], node.attrs["data-to"], node.attrs["data-phase"]))
        school.require(key in expected_keys and key not in seen_pairs, "Life pair DOM identity")
        seen_pairs.add(key)
        pair = pairs[key]
        cells = [c for c in node.children if isinstance(c, Node) and c.tag in ("td", "th")]
        school.require(len(cells) == 5, "Life pair DOM cell count")
        text_is(cells[0], str(pair["from"]) + " (" + short(pair["from_period"]) + ")", "pair from")
        text_is(cells[1], str(pair["to"]) + " (" + short(pair["to_period"]) + ")", "pair to")
        for cell, measure, field in zip(cells[2:], ("left", "right", "change"), ("left", "right", "display")):
            span = one(cell, "span", **{"data-measure": measure})
            text_is(cell, pair[field], "pair complete cell")
            text_is(span, pair[field], "pair " + measure)
            school.same(span.attrs.get("data-value"), pair[field], "life pair numeric attribute")
            school.same(span.attrs.get("data-comparison-id"), key, "life pair comparison mapping")
            operands = pair["operands"][2:] if measure == "left" else pair["operands"][:2] if measure == "right" else pair["operands"]
            school.same(span.attrs.get("data-ref"), " ".join(o["source"]["locator"] for o in operands),
                        "life pair operand references")
    school.same(sorted(seen_pairs), sorted(expected_keys), "life complete native pair tables")
    _check_labels(dom, data)
    _check_script(dom, data)
    return dom


def short(period):
    left, right = period.split("/")
    return left + "/" + right[-2:]


def children(node, *tags):
    return [c for c in node.children if isinstance(c, Node) and c.tag in tags]


def _check_structure(dom):
    """Reject concealment attributes and classes outside this static contract."""
    allowed = {
        "html": {"lang"}, "head": set(), "body": {"class"}, "title": set(),
        "meta": {"charset", "name", "content"}, "link": {"rel", "href"},
        "style": set(), "script": set(), "header": set(), "footer": set(),
        "main": {"id"}, "h1": set(), "h2": set(), "h3": set(), "strong": set(),
        "nav": {"id", "class", "aria-label", "data-pid"},
        "a": {"href", "class", "aria-current", "download", "data-year-step", "data-nearest-year", "data-school-source"},
        "p": {"id", "class", "role", "data-pid", "data-anchor", "data-school-period",
              "data-school-summary", "data-school-gap", "data-available"},
        "span": {"class", "data-measure", "data-value", "data-ref", "data-comparison-id", "data-school-date"},
        "section": {"id", "tabindex", "data-life-year", "data-anchor"},
        "div": {"id", "class", "role", "aria-label", "tabindex", "hidden"},
        "label": {"for"}, "select": {"id"}, "option": {"value", "selected"},
        "details": {"class", "open"}, "summary": set(), "table": {"id"},
        "caption": set(), "thead": set(), "tbody": set(), "td": set(), "th": {"scope"},
        "tr": {"data-school-row", "data-anchor", "data-phase", "data-band", "data-school-pair", "data-from", "data-to"},
        "ul": {"class"}, "li": {"data-school-residual", "data-period", "data-phase", "data-indicator"},
        "blockquote": {"data-school-note"}, "code": {"data-source-hash"}, "br": set(),
    }
    classes = {"body": {"nojs"}, "a": {"skip"}, "nav": {"site-nav", "page-links"},
               "p": {"small", "name"}, "span": {"brand"}, "div": {"life-controls", "table-scroll"},
               "details": {"tbl"}, "ul": {"name"}}
    for node in dom.find():
        school.require(node.tag in allowed and set(node.attrs) <= allowed[node.tag],
                       "Life hidden or unexpected DOM attributes/elements")
        if "class" in node.attrs:
            school.require(node.attrs["class"] in classes.get(node.tag, set()),
                           "Life unexpected DOM class")
        if "hidden" in node.attrs:
            school.require(node.tag == "div" and node.attrs.get("id") in
                           ("life-year-controls", "compare-controls") and
                           node.attrs.get("class") == "life-controls",
                           "Life hidden core content")
        if "aria-current" in node.attrs:
            school.require(node.tag == "a" and node.attrs["aria-current"] == "page" and
                           node.attrs.get("href") == "life.html", "Life unexpected current-page state")
    html = one(dom, "html")
    school.require(html.parent is dom and len(children(dom, "html")) == 1, "Life invalid root wrapper")
    body, head = one(html, "body"), one(html, "head")
    school.require(body.parent is html and head.parent is html, "Life invalid head/body wrappers")
    main = one(dom, "main", id="main")
    school.require(main.parent is body, "Life invalid main wrapper")
    for section in dom.find("section"):
        expected_parent = one(dom, "section", id="compare") if section.attrs.get("id", "").startswith("pairs-") else main
        school.require(section.parent is expected_parent, "Life misplaced core section")


def _check_headers(table, expected):
    header = one(table, "thead")
    cells = children(one(header, "tr"), "th")
    school.same([n.text for n in cells], expected, "life table column labels")
    school.require(all(n.attrs.get("scope") == "col" for n in cells), "Life column header scope")
    for row in one(table, "tbody").find("tr"):
        first = children(row, "th", "td")[0]
        school.require(first.tag == "th" and first.attrs.get("scope") == "row", "Life row header scope")


def _check_labels(dom, data):
    foundation = data["schools"]
    header = one(dom, "header")
    text_is(one(header, "h1"), "Life, year by year", "page title")
    header_paragraphs = children(header, "p")
    text_is(header_paragraphs[1], "This first view covers school class sizes in England. "
            "Other topics are not yet built. Work, earnings, housing and holidays are still to come.", "honest topic coverage")
    main = one(dom, "main", id="main")
    school.same([h.text for h in children(main, "h2")], ["School class sizes"], "life main topic heading")
    text_is(children(main, "p")[0], "Choose any year from 2008 to 2026. School data here run from January 2016 to January 2026. "
            "Earlier anchors show a gap.", "annual range and source coverage")
    compare = one(dom, "section", id="compare")
    text_is(one(compare, "h2"), "Compare school years", "comparison heading")
    text_is(children(compare, "p")[0], "Choose two anchors and one phase. Each mean uses that phase’s own pupil and class counts. "
            "A positive change means a larger mean class; a negative change means a smaller mean class.", "signed comparison meaning")
    for field, label in (("life-year-select", "Jump to an annual anchor"), ("compare-from", "From anchor"),
                         ("compare-to", "To anchor"), ("compare-phase", "School phase")):
        text_is(one(dom, "label", **{"for": field}), label, "control label")
    text_is(one(dom, "p", id="life-year-status"), "All annual sections are below.", "initial annual status")
    for controls in ("life-year-controls", "compare-controls"):
        school.require("hidden" in one(dom, "div", id=controls).attrs, "Life enhancement controls must initially be hidden")
    phases = {o["id"]: o["label"] for f in foundation["definitions"]["filters"]
              if f["id"] == "5cGdi" for o in f["options"]}
    indexed = {(r["anchor"], r["filters"]["5cGdi"], r["filters"]["cAd31"]): r for r in foundation["rows"]}
    text_is(one(dom, "p", **{"data-pid": "technical-preview"}),
            "TECHNICAL PREVIEW — reader acceptance pending", "preview stage")
    text_is(one(dom, "p", **{"data-pid": "aggregate-disclaimer"}),
            "These are totals for groups, not a tracked person, an observed family or a typical child. "
            "A change does not show what caused it.", "aggregate and causality limits")
    text_is(one(dom, "p", **{"data-pid": "pair-mapping"}),
            "The tables below give every forward pair for all four phases. "
            "For a reverse pair, swap the two means and reverse the sign of the shown change. "
            "For the same observed year, both means are that year’s mean and the change is +0.0. "
            "If either anchor is 2008–2015, the result is unavailable, even for the same year. "
            "The nearest observation for those gaps is January 2016 (2015/16). "
            "Missing values are never zero. All ordered choices are also in the data download.", "native ordered pair mapping")
    text_is(one(dom, "p", **{"data-pid": "pair-method"}),
            "Changes use to-year pupils / classes minus from-year pupils / classes, before rounding. "
            "Each result is in pupils per class, shown to one decimal. Source and method.", "comparison formula")
    scope = ("England, by school location, not pupil residence. State-funded primary and secondary schools; classes taught by one teacher. "
             "These are observed January census counts, not forecasts. Class size is not pupil-teacher ratio or one child’s class. "
             "Primary overlaps Infant and KS2: do not add phases. DfE sources and notes.")
    scopes = dom.find("p", **{"data-pid": "school-scope"})
    school.require(len(scopes) == 21, "Life adjacent scope count")
    for node in scopes:
        text_is(node, scope, "population/geography/status/overlap")
        school.same(one(node, "a").attrs.get("href"), "#school-sources", "life adjacent source link")

    navigation = one(dom, "nav", id="life-years")
    school.same([(a.text, a.attrs.get("href")) for a in navigation.find("a")],
                [(str(y), "#year-" + str(y)) for y in range(2008, 2027)], "life native nineteen anchors")
    sections = dom.find("section", **{"data-life-year": None})
    school.require(len(sections) == 19, "Life annual section count")
    annual_heads = ["Phase", "Size band", "Classes", "Pupils", "Pupils per class", "Class share (%)", "Pupil share (%)"]
    for anchor in data["anchors"]:
        year = anchor["year"]
        section = one(dom, "section", id="year-" + str(year))
        school.same(section.attrs.get("data-life-year"), str(year), "life annual section identity")
        school.same(section.attrs.get("data-anchor"), str(year), "life annual anchor identity")
        school.same(section.attrs.get("tabindex"), "-1", "life annual focus target")
        text_is(one(section, "h2"), "Year " + str(year), "year heading")
        nav = one(section, "nav", **{"aria-label": "Years beside " + str(year)})
        expected_steps = []
        for key, label in (("previous", "Previous year"), ("next", "Next year")):
            target = anchor[key]
            if target is None:
                expected_steps.append((label + ": none", None))
            else:
                expected_steps.append((label + ": " + str(target), "#year-" + str(target)))
                school.same(one(nav, "a", **{"data-year-step": key}).attrs.get("href"),
                            "#year-" + str(target), "life adjacent year mapping")
        school.same([(n.text, n.attrs.get("href")) for n in children(nav, "a", "span")],
                    expected_steps, "life chronological previous/next labels")
        one(section, "p", **{"data-pid": "school-scope"})
        if not anchor["available"]:
            text_is(one(section, "p", **{"data-school-gap": "true"}),
                     "Not in the selected DfE dataset. No retained school observation for this anchor. This gap is not zero. "
                    "We do not fill it with a later value.", "gap versus zero")
            nearest = one(section, "a", **{"data-nearest-year": str(anchor["nearest"])})
            school.same(nearest.attrs.get("href"), "#year-" + str(anchor["nearest"]), "life nearest mapping")
            nearest_anchor = next(a for a in data["anchors"] if a["year"] == anchor["nearest"])
            text_is(nearest, "January " + str(anchor["nearest"]) + ", academic year " + short(nearest_anchor["period"]),
                    "nearest actual period")
            text_is(nearest.parent, "Nearest school observation: January " + str(anchor["nearest"])
                    + ", academic year " + short(nearest_anchor["period"])
                    + ". This is not an observation for the selected year.", "gap nearest scope")
            school.require(not section.find("tr") and not section.find("p", **{"data-school-summary": None}),
                           "Life unavailable anchor contains observations")
            continue
        text_is(one(section, "p", **{"data-school-period": str(year)}),
                "Academic year " + short(anchor["period"]) + "; January " + str(year) + " census.", "actual census/academic period")
        school.require(not section.find("p", **{"data-school-gap": None}) and
                       not section.find("a", **{"data-nearest-year": None}), "Life observed anchor labelled as gap")
        for phase in PHASE_ORDER[:2]:
            summary = one(section, "p", **{"data-school-summary": phase})
            row = indexed[(year, phase, "XdTUf")]
            measure = row["derived"]["mean"]
            text_is(summary, phases[phase] + ": " + measure["display"] + " pupils per class.", "annual summary")
            span = one(summary, "span", **{"data-measure": "mean"})
            school.same(span.attrs.get("data-value"), measure["display"], "life summary numeric attribute")
            school.same(span.attrs.get("data-ref"), " ".join(o["source"]["locator"] for o in measure["operands"]),
                        "life summary raw source references")
            school.same(summary.attrs.get("data-anchor"), str(year), "life summary anchor")
        table = one(section, "table", id="school-table-" + str(year))
        _check_headers(table, annual_heads)
        details = one(section, "details")
        text_is(one(details, "summary"), "Show all school phases and size bands", "annual table disclosure")
        text_is(children(details, "p")[0], "Shares use the published total for this phase and year. "
                "Class shares count classes; pupil shares count pupils. They are different wholes. "
                "Means use each row’s own pupils divided by its classes. Values are shown to one decimal.", "share denominator and mean definitions")
        text_is(one(table, "caption"), "England one-teacher classes, " + short(anchor["period"]) + "; January " + str(year),
                "annual table period/population caption")
        school.require(len(table.find("tr", **{"data-school-row": None})) == 16, "Life phase/band rows outside actual year table")
    phase_navigation = one(dom, "nav", **{"aria-label": "School phase pair tables"})
    school.same([(a.text, a.attrs.get("href")) for a in phase_navigation.find("a")],
                [(phases[code] + " pairs", "#pairs-" + code) for code in PHASE_ORDER], "life native phase pair links")
    for phase in PHASE_ORDER:
        pair_section = one(dom, "section", id="pairs-" + phase)
        school.same(pair_section.attrs.get("tabindex"), "-1", "life pair section focus target")
        text_is(one(pair_section, "h3"), phases[phase] + " year pairs", "native pair phase heading")
        table = one(pair_section, "table", id="pair-table-" + phase)
        _check_headers(table, ["From anchor", "To anchor", "From mean", "To mean", "Signed change"])
        text_is(one(pair_section, "summary"), phases[phase] + ": all forward year pairs", "native pair disclosure")
        text_is(one(table, "caption"), phases[phase] + ", pupils per class; observed January census", "pair phase/unit/status caption")
        school.require(len(table.find("tr", **{"data-school-pair": None})) == 55, "Life incomplete phase pair table")
        school.require(all(n.attrs["data-phase"] == phase for n in table.find("tr", **{"data-school-pair": None})),
                       "Life pair row in wrong phase table")
    for field in ("life-year-select", "compare-from", "compare-to"):
        select = one(dom, "select", id=field)
        school.same([(o.attrs.get("value"), o.text) for o in select.find("option")],
                    [(str(y), str(y)) for y in range(2008, 2027)], "life control anchor labels")
    select = one(dom, "select", id="compare-phase")
    school.same([(o.attrs.get("value"), o.text) for o in select.find("option")],
                [(code, phases[code]) for code in PHASE_ORDER], "life control phase labels")
    for field, selected in (("life-year-select", "2026"), ("compare-from", "2016"), ("compare-to", "2026")):
        options = one(dom, "select", id=field).find("option")
        school.same([o.attrs.get("value") for o in options if "selected" in o.attrs], [selected],
                    "life default control selection")
    result = one(dom, "p", id="compare-result")
    pair = next(p for p in data["comparisons"] if p["id"] == "2016:2026:5kyxd")
    school.same(result.attrs.get("role"), "status", "life comparison accessible result")
    school.same(result.attrs.get("data-available"), "true", "life initial comparison availability")
    text_is(result, phases[pair["phase"]] + ": January " + str(pair["from"]) + " (academic " + short(pair["from_period"]) + "): "
            + pair["left"] + " pupils per class. January " + str(pair["to"]) + " (academic " + short(pair["to_period"]) + "): "
            + pair["right"] + " pupils per class. Signed change (to minus from): " + pair["display"] + " pupils per class.",
            "initial comparison visible actual period and signed answer")
    for measure, field in (("left", "left"), ("right", "right"), ("change", "display")):
        span = one(result, "span", **{"data-measure": measure})
        school.same(span.attrs.get("data-value"), pair[field], "life initial pair numeric attribute")
        school.same(span.attrs.get("data-comparison-id"), pair["id"], "life initial pair mapping")
        operands = pair["operands"][2:] if measure == "left" else pair["operands"][:2] if measure == "right" else pair["operands"]
        school.same(span.attrs.get("data-ref"), " ".join(o["source"]["locator"] for o in operands),
                    "life initial comparison raw operands")
    ordering = one(dom, "p", **{"data-pid": "school-phase-order"})
    latest = max(r["anchor"] for r in foundation["rows"])
    school.same(ordering.attrs.get("data-anchor"), str(latest), "life latest phase ordering anchor")
    primary, secondary = indexed[(latest, "5kyxd", "XdTUf")], indexed[(latest, "tfHTE", "XdTUf")]
    def own_mean(row):
        return school.number(row["published"]["QtxWw"]["raw"], True) / school.number(row["published"]["EAicq"]["raw"], True)
    difference = next(p for p in foundation["comparisons"] if p["id"] == "primary_minus_secondary_" + str(latest))
    relation = "lower than" if own_mean(secondary) < own_mean(primary) else "higher than" if own_mean(secondary) > own_mean(primary) else "the same as"
    text_is(ordering, f"In January {latest}, Secondary had a mean {relation} Primary. Secondary: "
            + secondary["derived"]["mean"]["display"] + " pupils per class. Primary: "
            + primary["derived"]["mean"]["display"] + " pupils per class. Primary minus Secondary: "
            + difference["display"] + " pupils per class. DfE source and method.", "latest phase ordering and signed difference")
    for measure, value in (("secondary_mean", secondary["derived"]["mean"]),
                           ("primary_mean", primary["derived"]["mean"]),
                           ("primary_minus_secondary", difference)):
        span = one(ordering, "span", **{"data-measure": measure})
        school.same(span.attrs.get("data-value"), value["display"], "life latest ordering numeric attribute")
        school.same(span.attrs.get("data-ref"), " ".join(o["source"]["locator"] for o in value["operands"]),
                    "life latest ordering raw operands")
    school.same(one(ordering, "a").attrs.get("href"), "#school-sources", "life ordering adjacent source")
    school.require(len(dom.find("span", **{"data-measure": None})) == 1568 + sum(Decimal(r["residual_total_minus_bands"]) != 0 for r in foundation["reconciliations"]), "Life unchecked extra or missing numeric span")
    _check_sources(dom, foundation)


def _check_sources(dom, foundation):
    section = one(dom, "section", id="school-sources")
    text_is(one(section, "h2"), "School sources and limits", "source heading")
    publication = foundation["publication"]
    paragraphs = children(section, "p")
    text_is(paragraphs[0], "Department for Education (DfE): " + publication["title"]
            + ". API version " + publication["version"] + ".", "dataset title/version")
    dates = [
        ("api_published", "API version published", publication["api_published"]),
        ("published", "Release published", publication["release"]["published"]),
        ("lastUpdated", "Release last updated", publication["release"]["lastUpdated"]),
        ("methodology", "Method page published", publication["methodology"]["published"])]
    school.require(len(section.find("span", **{"data-school-date": None})) == 4, "Life date metadata count")
    for key, label, value in dates:
        span = one(section, "span", **{"data-school-date": key})
        text_is(span, value, "source date")
        text_is(span.parent, label + ": " + value + ".", "source date meaning")
    release = publication["nextReleaseDate"]
    expected_next = (f"Next release announced: {release['year']}-{release['month']:02d} (month only; no day is stated)."
                     if release else "No next release date is announced in these sources.")
    text_is(paragraphs[1], expected_next, "next release announcement")
    text_is(paragraphs[2],
            "Each annual anchor names the academic year ending in that year. The census is in January. "
            "The third-Thursday rule comes from the method page; it is not a separately reported date for each row. "
            "All eleven years use this current release. January 2021 is present. No older release is joined to it.", "source series and census scope")
    text_is(paragraphs[3],
            "The one-decimal means are pupils divided by each row’s own classes. "
            "Changes subtract those unrounded means, then round once. "
            "We use decimal arithmetic with 50-digit precision and round halves up. "
            "Do not subtract rounded means to check a change.", "source arithmetic and rounding")
    text_is(paragraphs[4],
            "Some published totals differ from their three size bands. These are total minus band sum. "
            "We keep each published total as the share’s whole. "
            "We do not force band shares to sum to 100 or assign a cause.", "published residual meaning")
    expected_residuals = {(r["timePeriod"]["period"], r["phase"], r["indicator"]): r
                          for r in foundation["reconciliations"] if Decimal(r["residual_total_minus_bands"]) != 0}
    residual_nodes = section.find("li", **{"data-school-residual": "true"})
    school.require(len(residual_nodes) == len(expected_residuals), "Life residual DOM count")
    seen = set()
    for node in residual_nodes:
        key = (node.attrs["data-period"], node.attrs["data-phase"], node.attrs["data-indicator"])
        school.require(key in expected_residuals and key not in seen, "Life residual DOM identity")
        seen.add(key)
        record = expected_residuals[key]
        text_is(node, record["phase"] + ", " + short(record["timePeriod"]["period"]) + ": "
                + record["residual_total_minus_bands"] + " " + record["unit"] + ".", "source-derived residual")
        span = one(node, "span", **{"data-measure": "residual"})
        school.same(span.attrs.get("data-value"), record["residual_total_minus_bands"], "life residual numeric attribute")
        school.same(span.attrs.get("data-ref"), " ".join(o["source"]["locator"] for o in record["operands"]),
                    "life residual precise raw operands")
    text_is(paragraphs[5],
            "All " + str(len(foundation["rows"])) + " national rows, source locators, full hashes, notes, formulas and operands are in "
            "Download life data (JSON). The local-authority catalogue preview is separate: its z means not applicable. "
            "A blank or z is never a national zero.", "preview quality/source scope")
    download = one(paragraphs[5], "a")
    school.same(download.attrs.get("href"), "data/life.json", "life downloadable evidence path")
    school.same(download.attrs.get("download"), "life.json", "life downloadable evidence filename")
    school.require(len(section.find("a", **{"data-school-source": None})) == 5, "Life source link count")
    school.require(len(section.find("code", **{"data-source-hash": None})) == 5, "Life original hash count")
    for name, source in foundation["sources"].items():
        link = one(section, "a", **{"data-school-source": name})
        text_is(link, name, "source filename")
        school.same(link.attrs.get("href"), source["url"], "life official source exact URL")
        code = one(section, "code", **{"data-source-hash": name})
        text_is(code, source["sha256"], "original SHA256")
        school.require(code.parent is link.parent, "Life original hash detached from source")
    school.require(len(section.find("blockquote", **{"data-school-note": None})) == len(foundation["notes"]), "Life exact source notes count")
    for key, note in foundation["notes"].items():
        quote = one(section, "blockquote", **{"data-school-note": key})
        text_is(quote, note["text"], "original source note " + key)
        siblings = children(quote.parent, "blockquote", "p", "ul", "pre", "summary")
        following = siblings[siblings.index(quote) + 1]
        text_is(following, "Source locator: " + note["source"]["locator"] + ". Original SHA-256: " + note["source"]["sha256"] + ".",
                "source note precise locator/hash")
    detail = one(section, "details")
    detail_paragraphs = children(detail, "p")
    text_is(detail_paragraphs[len(foundation["notes"])], publication["footnote_caution"], "catalogue generic footnote caution")
    school.same([n.text for n in detail_paragraphs[len(foundation["notes"]) + 1:]],
                [" ".join(json.dumps(n, ensure_ascii=False, sort_keys=True).split())
                 for n in publication["catalogue_footnotes"]], "life retained catalogue footnotes")
    footer = one(dom, "footer")
    source = foundation["sources"][school.INPUTS[4]]
    text_is(children(footer, "p")[0],
            "School data: Department for Education, Schools, pupils and their characteristics. "
            "Contains public sector information licensed under the Open Government Licence v3.0.", "DfE attribution")
    school.same([(a.text, a.attrs.get("href")) for a in children(footer, "p")[0].find("a")],
                [("Schools, pupils and their characteristics", source["url"]),
                 ("Open Government Licence v3.0", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/")],
                "life DfE attribution and licence links")


def _check_script(dom, data):
    # Check every enhancement mapping as data without evaluating JavaScript.
    import re
    script = one(dom, "script").text
    match = re.match(r"var DEFAULT_YEAR=([0-9]+);var PHASE_LABELS=(.*?);var PAIRS=(.*?);\s*\(function", script)
    school.require(match is not None, "Life enhancement mapping missing")
    school.same(int(match[1]), data["default_anchor"], "life enhancement default anchor")
    phases = {o["id"]: o["label"] for f in data["schools"]["definitions"]["filters"]
              if f["id"] == "5cGdi" for o in f["options"]}
    school.same(school.decode(match[2]), phases, "life enhancement phase labels")
    pairs = {p["id"]: [p["left"], p["right"], p["display"], p["from_period"], p["to_period"]]
             if p["available"] else None for p in data["comparisons"]}
    school.same(school.decode(match[3]), pairs, "life all 1444 enhancement mappings")


def validate_data(root, data):
    with localcontext() as context:
        context.prec = 50
        originals, evidence = school.reopen(root)
        _validate_data(data, originals, evidence)
    return 176


def validate_candidate(root, data, html):
    with localcontext() as context:
        context.prec = 50
        originals, evidence = school.reopen(root)
        expected = _validate_data(data, originals, evidence)
        _validate_page(expected, html, originals, evidence)
    return 176


def validate_page(root, data, html):
    return validate_candidate(root, data, html)


def validate(root=ROOT, site=None):
    root = Path(root)
    site = root / "site" if site is None else Path(site)
    private = school.decode(school.read(root, "data/life.json"))
    public = school.decode(school.read(site, "data/life.json"))
    school.same(public, private, "private/public life semantic parity")
    count = validate_candidate(root, private, school.read(site, "life.html").decode("utf-8"))
    print("Life: five originals, 176 annual rows and complete ordered comparisons independently verified; reader acceptance pending")
    return count


if __name__ == "__main__":
    validate()
