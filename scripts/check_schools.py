"""Independent school audit: reopen all five originals, then check memory only.

No producer reader, rounding helper, constants or expected output are imported.
The optional producer call happens only after independent source reopening.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/life/sources/schools"
REGISTER = "data/life/school-sources.json"
REGISTER_SHA256 = "a0132d8fabc0ea45e71ecade606c102560072a1f58c9a618921519c6ea6a5412"
INPUTS = (
    "dfe-national-class-sizes-1.0.json", "dfe-class-sizes-meta-1.0.json",
    "catalogs-methods-crawl-2.html.json", "catalogs-methods-crawl-3.html.json",
    "official-pages-crawl-3.html.json",
)
IDENTITY = "019e7401-70d1-73ca-9855-bd7258e5a1ca"
ENDPOINT = "https://api.education.gov.uk/statistics/v1/data-sets/" + IDENTITY
URLS = (
    ENDPOINT + "/query?dataSetVersion=1.0&geographicLevels.eq=NAT&pageSize=1000",
    ENDPOINT + "/meta?dataSetVersion=1.0",
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/2d8a11dd-1079-4819-85e4-91c764b6e3fc",
    "https://explore-education-statistics.service.gov.uk/methodology/schools-pupils-and-their-characteristics",
    "https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics",
)
PHASES = {"TaWMP": "Infant (Reception plus KS1)", "cDwC3": "KS2", "5kyxd": "Primary", "tfHTE": "Secondary"}
BANDS = {"zeoRF": "1 to 30", "kxKDh": "31 to 35", "u2cKo": "36 plus", "XdTUf": "Total"}
POPULATION = "Classes taught by one teacher in state-funded primary and secondary schools"
STATUS = "Observed January school census counts; current release, not a forecast"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, label):
    # Exact types as well as values; JSON booleans must not masquerade as counts.
    try:
        left = json.dumps(actual, sort_keys=True, ensure_ascii=True, allow_nan=False)
        right = json.dumps(expected, sort_keys=True, ensure_ascii=True, allow_nan=False)
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid JSON school projection: " + label) from error
    require(left == right, "School mismatch: " + label)


def decode(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate school JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite school JSON constant: " + value)

    return json.loads(body, object_pairs_hook=unique, parse_constant=nonfinite)


def read(root, relative):
    require(isinstance(relative, str), "Invalid school path")
    part = Path(relative)
    require(not part.is_absolute() and ".." not in part.parts, "Unsafe school path")
    root = Path(root).absolute()
    path = root / part
    require(not any(p.is_symlink() for p in (path, *path.parents)),
            "School evidence must be without symlinks")
    require(path.is_file() and path.resolve().is_relative_to(root.resolve()),
            "School evidence must be a regular file within root")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def reopen(root):
    raw_register = read(root, REGISTER)
    require(digest(raw_register) == REGISTER_SHA256, "Pinned school register hash changed")
    register = decode(raw_register)
    require(register["schema_version"] == 1 and register["domain"] == "schools",
            "School register identity changed")
    entries = register["sources"]
    closed = {DIRECTORY + "/" + name for name in INPUTS}
    require(len(entries) == 5 and {e["path"] for e in entries} == closed,
            "School closed source path set changed")
    directory = Path(root) / DIRECTORY
    require(not any(p.is_symlink() for p in (directory, *directory.parents)),
            "School source directory must be without symlinks")
    require({p.name for p in directory.iterdir()} == set(INPUTS),
            "School source directory set changed")
    originals, evidence = {}, {}
    for name, url in zip(INPUTS, URLS):
        e = next(x for x in entries if x["path"] == DIRECTORY + "/" + name)
        require(e["url"] == url, "School exact URL/dataset/version changed")
        stored = read(root, e["path"])
        body = stored
        if name.endswith(".html.json"):
            require(len(stored) == e["stored_bytes"] and digest(stored) == e["stored_sha256"],
                    "School stored envelope hash/length mismatch")
            envelope = decode(stored)
            require(set(envelope) == {"encoding", "original_response"} and
                    envelope["encoding"] == "utf-8" and isinstance(envelope["original_response"], str),
                    "School envelope encoding/keys changed")
            body = envelope["original_response"].encode("utf-8")
        require(len(body) == e["bytes"] and digest(body) == e["sha256"],
                "School recovered original hash/length mismatch")
        originals[name], evidence[name] = body, dict(e)
    require(sum(len(b) for b in originals.values()) == 393595, "School original byte floor changed")
    require(sum(e.get("stored_bytes", e["bytes"]) for e in entries) == 409925,
            "School full stored source bytes changed")
    release = evidence[INPUTS[4]]
    require(release["reported_request_status"] == 308 and
            release["reported_redirect_location"] == "/find-statistics/school-pupils-and-their-characteristics/2025-26" and
            release["reported_response_headers"]["content-length"] == "64" and
            "no final200headerclaim" in release["custody_caution"],
            "School redirect/header-body custody changed")
    return originals, evidence


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts, self.paragraphs = [], []
        self.in_script = False
        self.in_paragraph = False
        self.current = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "__NEXT_DATA__":
            require(not self.in_script, "Nested school page data")
            self.in_script, self.current = True, []
        elif tag == "p":
            self.in_paragraph, self.current = True, []

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            self.scripts.append("".join(self.current))
            self.in_script, self.current = False, []
        elif tag == "p" and self.in_paragraph:
            self.paragraphs.append("".join(self.current))
            self.in_paragraph, self.current = False, []

    def handle_data(self, data):
        if self.in_script or self.in_paragraph:
            self.current.append(data)


def page(body):
    parser = PageParser()
    parser.feed(body.decode("utf-8"))
    require(len(parser.scripts) == 1, "School original page data missing/duplicated")
    return decode(parser.scripts[0])["props"]["pageProps"]


def text_paragraph(body, fragment):
    parser = PageParser()
    parser.feed(body)
    selected = [p for p in parser.paragraphs if fragment in p]
    require(len(selected) == 1, "School source note missing/ambiguous")
    return selected[0]


def number(raw, integer=False):
    require(isinstance(raw, str) and
            re.fullmatch(r"[0-9]+" if integer else r"[0-9]+(?:\.[0-9]+)?", raw) is not None,
            "School missing/nonfinite/invalid raw numeric string")
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError("Invalid school decimal") from error
    require(value.is_finite() and value >= 0, "Invalid school numeric range")
    return value


def display(value, places=1, signed=False):
    quantum = Decimal("1") if places == 0 else Decimal("0.1")
    result = value.quantize(quantum, rounding=ROUND_HALF_UP)
    return format(result, ("+" if signed else "") + "." + str(places) + "f")


def check(projection, originals, evidence):
    query = decode(originals[INPUTS[0]])
    meta = decode(originals[INPUTS[1]])
    cat, method_page, release = [page(originals[n]) for n in INPUTS[2:]]
    method = method_page["data"]
    periods = [{"code": "AY", "period": str(y) + "/" + str(y+1), "label": str(y) + "/" + str(y+1)[2:]}
               for y in range(2015, 2026)]
    expected_filters = [
        {"id": "cAd31", "column": "class_size", "label": "Size of class",
         "hint": "Class size (1 to 30, 31 to 35, 36 plus)",
         "options": [{"id": k, "label": v} for k, v in BANDS.items()]},
        {"id": "5cGdi", "column": "class_type", "label": "Type of class",
         "hint": "Type of class (Infant (Reception plus KS1), KS2, Primary or Secondary)",
         "options": [{"id": k, "label": v} for k, v in PHASES.items()]},
    ]
    indicators = [
        {"id": "Wc9V2", "column": "class_size_average", "label": "Average class size", "decimalPlaces": 1},
        {"id": "EAicq", "column": "class_count", "label": "Number of classes", "decimalPlaces": 0},
        {"id": "QtxWw", "column": "pupil_count", "label": "Number of pupils", "decimalPlaces": 0},
    ]
    same(meta["filters"], expected_filters, "original metadata code-label/hint map")
    same(meta["indicators"], indicators, "original metadata indicators/unit/precision")
    same(meta["timePeriods"], periods, "original eleven academic years")
    same(meta["geographicLevels"], [
        {"code": "LA", "label": "Local authority"}, {"code": "NAT", "label": "National"},
        {"code": "PCON", "label": "Parliamentary constituency"}, {"code": "REG", "label": "Regional"}],
        "original geographic level labels")
    nat = [g for g in meta["locations"] if g["level"]["code"] == "NAT"]
    same(nat, [{"level": {"code": "NAT", "label": "National"},
                "options": [{"id": "dP0Zw", "label": "England", "code": "E92000001"}]}],
         "original national geography")
    same(query["warnings"], [], "original query warnings")
    same(query["paging"], {"page": 1, "pageSize": 1000, "totalResults": 176, "totalPages": 1},
         "original national paging")
    require(cat["apiDataSet"]["id"] == IDENTITY and
            cat["dataSetFile"]["api"] == {"id": IDENTITY, "version": "1.0"} and
            cat["apiDataSet"]["latestVersion"]["version"] == "1.0" and
            cat["apiDataSetVersion"]["version"] == "1.0" and
            cat["apiDataSet"]["title"] == "Class sizes - state-funded primary and secondary schools" and
            cat["apiDataSetVersion"]["published"] == "2026-06-04T08:30:26.258127+00:00" and
            cat["apiDataSetVersion"]["status"] == "Published",
            "School original catalogue dataset/title/version/publication changed")
    require(release["releaseVersionSummary"]["slug"] == "2025-26" and
            release["releaseVersionSummary"]["published"] == "2026-06-04T08:30:09.6670964+00:00" and
            release["releaseVersionSummary"]["lastUpdated"] == "2026-10-16T15:20:02.6106164+00:00" and
            method["published"] == "2026-10-16T15:18:35.5258037",
            "School original release/method dates changed")

    def ref(name, locator):
        return {"path": evidence[name]["path"], "sha256": evidence[name]["sha256"], "locator": locator}

    method_blocks = {b["id"]: b["body"] for s in method["content"] for b in s["content"] if b["type"] == "HtmlBlock"}
    rel_blocks = {b["id"]: b["body"] for s in release["homeContent"]["content"] for b in s["content"] if b["type"] == "HtmlBlock"}
    notes = {}
    for key, name, bid, fragment in [
        ("geography", INPUTS[3], "8fb23e54-1071-481b-aaf8-3eb79c5a93b4", "The main figures presented"),
        ("method", INPUTS[3], "e61523ad-ce39-49b1-85b2-193730b8d02e", "From 2019,"),
        ("census", INPUTS[3], "1bc01fcc-7728-45f4-9cd7-ebae456e7a24", "third Thursday in January"),
        ("one_teacher", INPUTS[4], "02240e24-faaf-4288-923d-54446b7b42d0", "The figures below represent"),
        ("phases", INPUTS[4], "10db2eb9-034d-4d5b-9097-ad802d5e8109", "Primary schools typically"),
        ("infant", INPUTS[4], "02240e24-faaf-4288-923d-54446b7b42d0", "Infant classes cover reception"),
        ("ks2", INPUTS[4], "52d24b62-426b-4d93-81f8-8ae4399d1c04", "pupils in years 3 to 6"),
    ]:
        note = text_paragraph((method_blocks if name == INPUTS[3] else rel_blocks)[bid], fragment)
        notes[key] = {"text": note, "source": ref(name, "__NEXT_DATA__/HtmlBlock/" + bid + "/p contains " + fragment)}
    require("for all years" in notes["method"]["text"] and
            "prior to 2018/19" in notes["method"]["text"] and
            "rather than where pupils live" in notes["geography"]["text"] and
            "one teacher only" in notes["one_teacher"]["text"],
            "School original population/current-vintage notes changed")
    expected_keys = {"schema_version", "domain", "private", "scope", "sources", "definitions", "notes",
                     "publication", "quality_codes", "catalogue_preview", "rows", "reconciliations", "comparisons"}
    same(sorted(projection), sorted(expected_keys), "closed projection keys")
    same(projection["schema_version"], 1, "schema")
    same(projection["domain"], "schools", "domain")
    same(projection["private"], True, "private foundation")
    same(projection["sources"], evidence, "full custody evidence")
    same(projection["scope"], {
        "population": POPULATION, "status": STATUS,
        "overlap": "Primary overlaps Infant and KS2; these views must never be added.",
        "meaning": "Class size is not pupil-teacher ratio or an individual child's actual class.",
        "series": "Current release for all eleven years; no old-release splice or January 2021 gap.",
        "context": "Row context applies to every nested published and derived measure.",
        "rounding": "Decimal original strings, precision 50; ROUND_HALF_UP at metadata precision"}, "scope")
    same(projection["definitions"], {
        "filters": meta["filters"], "indicators": meta["indicators"], "timePeriods": meta["timePeriods"],
        "geographicLevels": meta["geographicLevels"], "national": nat[0],
        "unit_basis": "API indicator labels/columns: pupils, classes and pupils per class; no separate unit field"},
        "source-bound definitions")
    same(projection["notes"], notes, "verbatim notes and provenance")
    same(projection["publication"], {
        "dataset_id": cat["apiDataSet"]["id"], "title": cat["apiDataSet"]["title"], "summary": cat["apiDataSet"]["summary"],
        "version": cat["apiDataSetVersion"]["version"], "api_published": cat["apiDataSetVersion"]["published"],
        "version_notes": cat["apiDataSetVersion"]["notes"], "status": cat["apiDataSetVersion"]["status"],
        "catalogue_release": cat["dataSetFile"]["release"],
        "release": {k: release["releaseVersionSummary"][k] for k in
                    ("title", "slug", "published", "lastUpdated", "type", "publication")},
        "methodology": {k: method[k] for k in ("title", "slug", "published")},
        "nextReleaseDate": cat["publicationSummary"]["nextReleaseDate"],
        "catalogue_footnotes": cat["dataSetFile"]["footnotes"],
        "footnote_caution": "Catalogue footnotes are retained verbatim, not substituted for the class-size population.",
        "provenance": [ref(INPUTS[2], "__NEXT_DATA__/props/pageProps"),
                       ref(INPUTS[3], "__NEXT_DATA__/props/pageProps/data"),
                       ref(INPUTS[4], "__NEXT_DATA__/props/pageProps/releaseVersionSummary")]}, "publication")
    same(projection["quality_codes"], {"z": "Not applicable; never zero or a national observation"}, "z meaning")
    preview = cat["dataSetFile"]["file"]["dataCsvPreview"]
    require(preview["rows"][2][-1] == "z" and preview["rows"][2][2] == "Local authority",
            "School original preview z/scope changed")
    same(projection["catalogue_preview"], {
        "data": preview, "source": ref(INPUTS[2], "__NEXT_DATA__/props/pageProps/dataSetFile/file/dataCsvPreview"),
        "caution": "Local-authority preview, not extra national rows; retain raw z and every blank."}, "raw preview/z")

    grid = {}
    expected_grid = {(p["period"], t, b) for p in periods for t in PHASES for b in BANDS}
    for index, r in enumerate(query["results"]):
        same(sorted(r), sorted(("timePeriod", "geographicLevel", "locations", "filters", "values")), "original row keys")
        same(sorted(r["timePeriod"]), ["code", "period"], "original period keys")
        same(r["timePeriod"]["code"], "AY", "original timePeriod code")
        same(r["geographicLevel"], "NAT", "original geographic level")
        same(r["locations"], {"NAT": "dP0Zw"}, "original location")
        same(sorted(r["filters"]), sorted(("5cGdi", "cAd31")), "original filters")
        same(sorted(r["values"]), sorted(("QtxWw", "Wc9V2", "EAicq")), "original value IDs")
        key = (r["timePeriod"]["period"], r["filters"]["5cGdi"], r["filters"]["cAd31"])
        require(key in expected_grid and key not in grid, "School original duplicate/extra grid row")
        for code in ("QtxWw", "EAicq", "Wc9V2"):
            number(r["values"][code], code != "Wc9V2")
        require(number(r["values"]["EAicq"], True) > 0, "School original zero denominator")
        grid[key] = (index, r)
    require(set(grid) == expected_grid and len(query["results"]) == 176, "School original missing grid rows")

    def operand(index, row, code):
        return {"raw": row["values"][code], "indicator": code,
                "timePeriod": row["timePeriod"], "filters": row["filters"],
                "geographicLevel": row["geographicLevel"], "locations": row["locations"],
                "source": ref(INPUTS[0], "/results/" + str(index) + "/values/" + code)}

    seen = set()
    require(isinstance(projection["rows"], list) and len(projection["rows"]) == 176, "School projected row count changed")
    for row in projection["rows"]:
        key = (row["timePeriod"]["period"], row["filters"]["5cGdi"], row["filters"]["cAd31"])
        require(key in grid and key not in seen, "School projected missing/duplicate/extra identity")
        seen.add(key)
        i, raw = grid[key]
        ti, total = grid[(key[0], key[1], "XdTUf")]
        pupils, classes = number(raw["values"]["QtxWw"], True), number(raw["values"]["EAicq"], True)
        tp, tc = number(total["values"]["QtxWw"], True), number(total["values"]["EAicq"], True)
        require(tp > 0 and tc > 0, "School original zero total denominator")
        mean = pupils / classes
        require(display(mean) == display(number(raw["values"]["Wc9V2"])),
                "School original mean differs from weighted counts")
        published = {}
        for code, unit, precision in [("Wc9V2", "pupils per class", 1), ("EAicq", "classes", 0), ("QtxWw", "pupils", 0)]:
            published[code] = {"raw": raw["values"][code], "display": display(number(raw["values"][code]), precision),
                               "unit": unit, "decimalPlaces": precision, "quality": None,
                               "source": ref(INPUTS[0], "/results/" + str(i) + "/values/" + code)}
        derived = {}
        for name, value, unit, formula, ops in [
            ("mean", mean, "pupils per class", "pupils / classes", [operand(i, raw, "QtxWw"), operand(i, raw, "EAicq")]),
            ("class_share", 100 * classes / tc, "% of classes in this phase",
             "100 * band classes / published total classes", [operand(i, raw, "EAicq"), operand(ti, total, "EAicq")]),
            ("pupil_share", 100 * pupils / tp, "% of pupils in this phase",
             "100 * band pupils / published total pupils", [operand(i, raw, "QtxWw"), operand(ti, total, "QtxWw")]),
        ]:
            derived[name] = {"display": display(value), "unit": unit, "decimalPlaces": 1,
                             "rounding": "ROUND_HALF_UP", "formula": formula, "operands": ops}
        year = int(key[0].split("/")[1])
        same(row, {
            "timePeriod": raw["timePeriod"], "anchor": year,
            "census": str("January " + str(year) + "; third Thursday (methodology rule, not an individually reported date)"),
            "geographicLevel": "NAT", "locations": {"NAT": "dP0Zw"},
            "geography": "England by school location, not pupil residence", "population": POPULATION, "status": STATUS,
            "filters": raw["filters"], "phase": PHASES[key[1]], "band": BANDS[key[2]],
            "notes": ["geography", "method", "census", "one_teacher",
                      {"TaWMP": "infant", "cDwC3": "ks2"}.get(key[1], "phases")],
            "source": ref(INPUTS[0], "/results/" + str(i)), "published": published, "derived": derived}, "row " + repr(key))
    require(seen == expected_grid, "School projected grid incomplete")
    residuals = []
    for period in sorted(p["period"] for p in periods):
        for phase in sorted(PHASES):
            ti, total = grid[(period, phase, "XdTUf")]
            parts = [grid[(period, phase, b)] for b in ("zeoRF", "kxKDh", "u2cKo")]
            for code in ("EAicq", "QtxWw"):
                subtotal = sum(number(r["values"][code], True) for _, r in parts)
                residuals.append({
                    "timePeriod": total["timePeriod"], "phase": PHASES[phase], "indicator": code,
                    "unit": "classes" if code == "EAicq" else "pupils",
                    "population": POPULATION, "geography": "England by school location, not pupil residence",
                    "status": STATUS, "notes": ["geography", "method", "census", "one_teacher"],
                    "band_sum": str(subtotal), "published_total": total["values"][code],
                    "residual_total_minus_bands": str(number(total["values"][code], True) - subtotal),
                    "formula": "published total - sum(three size bands within the same phase)",
                    "operands": [operand(ti, total, code)] + [operand(i, r, code) for i, r in parts],
                    "note": "Retain published totals as denominators; do not force shares to sum to 100 or add overlapping phases."})
    same(projection["reconciliations"], residuals, "published band residuals")
    expected_pairs = []
    for name, left, right in [
        ("primary_2016_to_2026", ("2015/2016", "5kyxd", "XdTUf"), ("2025/2026", "5kyxd", "XdTUf")),
        ("primary_minus_secondary_2026", ("2025/2026", "tfHTE", "XdTUf"), ("2025/2026", "5kyxd", "XdTUf")),
    ]:
        li, a = grid[left]
        ri, b = grid[right]
        difference = (number(b["values"]["QtxWw"], True) / number(b["values"]["EAicq"], True) -
                      number(a["values"]["QtxWw"], True) / number(a["values"]["EAicq"], True))
        expected_pairs.append({
            "id": name, "display": display(difference, signed=True), "unit": "pupils per class", "decimalPlaces": 1,
            "rounding": "ROUND_HALF_UP", "formula": "right pupils / right classes - left pupils / left classes",
            "operands": [operand(ri, b, "QtxWw"), operand(ri, b, "EAicq"), operand(li, a, "QtxWw"), operand(li, a, "EAicq")],
            "population": POPULATION, "geography": "England by school location, not pupil residence",
            "status": STATUS, "notes": ["geography", "method", "census", "one_teacher", "phases"]})
    same(projection["comparisons"], expected_pairs, "signed unrounded mean comparisons")
    return len(seen)


def validate(root=ROOT, projection=None):
    with localcontext() as context:
        context.prec = 50
        try:
            originals, evidence = reopen(root)
            if projection is None:
                from school_projection import project
                projection = project(root)
            count = check(projection, originals, evidence)
        except (KeyError, TypeError, IndexError) as error:
            raise ValueError("Malformed school evidence/projection") from error
    print(f"School foundation: 5 original responses and {count} national rows independently verified; no product acceptance")
    return count


if __name__ == "__main__":
    validate()
