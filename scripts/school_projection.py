"""Private, in-memory school source projection; no output files or import writes.

Each row supplies period, geography, population, phase, band, status, notes and
raw provenance for every nested measure. Operands retain original numeric
strings and source locators. This is a source foundation, not a public product.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
from html import unescape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/life/sources/schools"
REGISTER = "data/life/school-sources.json"
REGISTER_SHA256 = "a0132d8fabc0ea45e71ecade606c102560072a1f58c9a618921519c6ea6a5412"
FILES = (
    "dfe-national-class-sizes-1.0.json", "dfe-class-sizes-meta-1.0.json",
    "catalogs-methods-crawl-2.html.json", "catalogs-methods-crawl-3.html.json",
    "official-pages-crawl-3.html.json",
)
DATASET = "019e7401-70d1-73ca-9855-bd7258e5a1ca"
API = "https://api.education.gov.uk/statistics/v1/data-sets/" + DATASET
URLS = (
    API + "/query?dataSetVersion=1.0&geographicLevels.eq=NAT&pageSize=1000",
    API + "/meta?dataSetVersion=1.0",
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/2d8a11dd-1079-4819-85e4-91c764b6e3fc",
    "https://explore-education-statistics.service.gov.uk/methodology/schools-pupils-and-their-characteristics",
    "https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics",
)
POPULATION = "Classes taught by one teacher in state-funded primary and secondary schools"
STATUS = "Observed January school census counts; current release, not a forecast"


def safe_path(root, relative):
    root = Path(root).absolute()
    parts = Path(relative).parts
    if Path(relative).is_absolute() or ".." in parts or not parts:
        raise ValueError("Unsafe school path")
    target = root / relative
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("School inputs must not contain symlinks")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("School input outside root")
    return target


def strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate school JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite school JSON number: " + value)

    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)


def sources(root):
    register_bytes = safe_path(root, REGISTER).read_bytes()
    if hashlib.sha256(register_bytes).hexdigest() != REGISTER_SHA256:
        raise ValueError("Pinned school register changed")
    register = strict_json(register_bytes)
    entries = register["sources"]
    expected = {DIRECTORY + "/" + f for f in FILES}
    if (register["schema_version"] != 1 or register["domain"] != "schools" or
            len(entries) != 5 or {e["path"] for e in entries} != expected):
        raise ValueError("School source set changed")
    directory = safe_path(root, DIRECTORY)
    if {p.name for p in directory.iterdir()} != set(FILES):
        raise ValueError("Unexpected school source directory entry")
    originals, evidence = {}, {}
    for name, url in zip(FILES, URLS):
        entry = next(e for e in entries if e["path"] == DIRECTORY + "/" + name)
        if entry["url"] != url:
            raise ValueError("School source URL/version changed")
        stored = safe_path(root, entry["path"]).read_bytes()
        body = stored
        if name.endswith(".html.json"):
            if (len(stored) != entry["stored_bytes"] or
                    hashlib.sha256(stored).hexdigest() != entry["stored_sha256"]):
                raise ValueError("School stored envelope hash/length mismatch")
            envelope = strict_json(stored)
            if (set(envelope) != {"encoding", "original_response"} or
                    envelope["encoding"] != "utf-8" or
                    not isinstance(envelope["original_response"], str)):
                raise ValueError("Invalid school UTF8 envelope")
            body = envelope["original_response"].encode("utf-8")
        if len(body) != entry["bytes"] or hashlib.sha256(body).hexdigest() != entry["sha256"]:
            raise ValueError("School original hash/length mismatch")
        originals[name] = body
        evidence[name] = dict(entry)
    return originals, evidence


def next_props(body):
    matches = re.findall(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>',
                         body.decode("utf-8"))
    if len(matches) != 1:
        raise ValueError("School page data missing or duplicated")
    return strict_json(matches[0])["props"]["pageProps"]


def paragraph(html, contains):
    matches = [unescape(re.sub(r"<[^>]*>", "", p))
               for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", html)]
    selected = [p for p in matches if contains in p]
    if len(selected) != 1:
        raise ValueError("School source paragraph missing or ambiguous")
    return selected[0]


def numeric(raw, count=False):
    if (not isinstance(raw, str) or
            not re.fullmatch(r"[0-9]+" if count else r"[0-9]+(?:\.[0-9]+)?", raw)):
        raise ValueError("Missing, nonfinite or invalid school number")
    value = Decimal(raw)
    if not value.is_finite():
        raise ValueError("Nonfinite school value")
    return value


def rounded(value, places=1, signed=False):
    with localcontext() as context:
        context.prec = 50
        result = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return format(result, ("+" if signed else "") + "." + str(places) + "f")


def metadata(meta):
    # These codes are a closed contract; labels and precision come from metadata.
    phases = {"TaWMP": "Infant (Reception plus KS1)", "cDwC3": "KS2",
              "5kyxd": "Primary", "tfHTE": "Secondary"}
    bands = {"zeoRF": "1 to 30", "kxKDh": "31 to 35",
             "u2cKo": "36 plus", "XdTUf": "Total"}
    filters = {f["id"]: f for f in meta["filters"]}
    if len(meta["filters"]) != 2 or set(filters) != {"5cGdi", "cAd31"}:
        raise ValueError("School filters changed")
    for code, column, label, options in (
            ("5cGdi", "class_type", "Type of class", phases),
            ("cAd31", "class_size", "Size of class", bands)):
        f = filters[code]
        if (f["column"] != column or f["label"] != label or
                len(f["options"]) != 4 or {x["id"]: x["label"] for x in f["options"]} != options):
            raise ValueError("School code-label map changed")
    indicators = [
        {"id": "Wc9V2", "column": "class_size_average", "label": "Average class size", "decimalPlaces": 1},
        {"id": "EAicq", "column": "class_count", "label": "Number of classes", "decimalPlaces": 0},
        {"id": "QtxWw", "column": "pupil_count", "label": "Number of pupils", "decimalPlaces": 0},
    ]
    periods = [{"code": "AY", "period": f"{y}/{y+1}", "label": f"{y}/{str(y+1)[-2:]}"}
               for y in range(2015, 2026)]
    if meta["geographicLevels"] != [
            {"code": "LA", "label": "Local authority"}, {"code": "NAT", "label": "National"},
            {"code": "PCON", "label": "Parliamentary constituency"}, {"code": "REG", "label": "Regional"}]:
        raise ValueError("School geographic level labels changed")
    national = [x for x in meta["locations"] if x["level"]["code"] == "NAT"]
    if (meta["indicators"] != indicators or meta["timePeriods"] != periods or
            national != [{"level": {"code": "NAT", "label": "National"},
                          "options": [{"id": "dP0Zw", "label": "England", "code": "E92000001"}]}]):
        raise ValueError("School indicators, precision, years or geography changed")
    return {"filters": meta["filters"], "indicators": meta["indicators"],
            "timePeriods": meta["timePeriods"], "geographicLevels": meta["geographicLevels"], "national": national[0],
            "unit_basis": "API indicator labels/columns: pupils, classes and pupils per class; no separate unit field"}


def project(root=ROOT):
    with localcontext() as context:
        context.prec = 50
        try:
            return _project(root)
        except (KeyError, TypeError, IndexError) as error:
            raise ValueError("Malformed school source structure") from error


def _project(root):
    bodies, evidence = sources(root)
    query = strict_json(bodies[FILES[0]])
    meta = strict_json(bodies[FILES[1]])
    definitions = metadata(meta)
    catalogue = next_props(bodies[FILES[2]])
    method = next_props(bodies[FILES[3]])["data"]
    release = next_props(bodies[FILES[4]])
    dataset, version = catalogue["apiDataSet"], catalogue["apiDataSetVersion"]
    if (dataset["id"] != DATASET or version["version"] != "1.0" or
            catalogue["dataSetFile"]["api"] != {"id": DATASET, "version": "1.0"} or
            dataset["title"] != "Class sizes - state-funded primary and secondary schools" or
            dataset["latestVersion"]["version"] != "1.0" or version["status"] != "Published"):
        raise ValueError("School dataset title/version changed")
    if (query["warnings"] != [] or
            query["paging"] != {"page": 1, "pageSize": 1000, "totalResults": 176, "totalPages": 1}):
        raise ValueError("School national query incomplete")

    def source(name, locator):
        return {"path": evidence[name]["path"], "sha256": evidence[name]["sha256"], "locator": locator}

    blocks = {b["id"]: b["body"] for s in method["content"] for b in s["content"]
              if b["type"] == "HtmlBlock"}
    release_blocks = {b["id"]: b["body"] for s in release["homeContent"]["content"]
                      for b in s["content"] if b["type"] == "HtmlBlock"}
    note_specs = (
        ("geography", FILES[3], "8fb23e54-1071-481b-aaf8-3eb79c5a93b4", "The main figures presented"),
        ("method", FILES[3], "e61523ad-ce39-49b1-85b2-193730b8d02e", "From 2019,"),
        ("census", FILES[3], "1bc01fcc-7728-45f4-9cd7-ebae456e7a24", "third Thursday in January"),
        ("one_teacher", FILES[4], "02240e24-faaf-4288-923d-54446b7b42d0", "The figures below represent"),
        ("phases", FILES[4], "10db2eb9-034d-4d5b-9097-ad802d5e8109", "Primary schools typically"),
        ("infant", FILES[4], "02240e24-faaf-4288-923d-54446b7b42d0", "Infant classes cover reception"),
        ("ks2", FILES[4], "52d24b62-426b-4d93-81f8-8ae4399d1c04", "pupils in years 3 to 6"),
    )
    notes = {}
    for key, name, block, fragment in note_specs:
        text = paragraph((blocks if name == FILES[3] else release_blocks)[block], fragment)
        notes[key] = {"text": text, "source": source(name, "__NEXT_DATA__/HtmlBlock/" + block + "/p contains " + fragment)}
    if ("for all years" not in notes["method"]["text"] or
            "rather than where pupils live" not in notes["geography"]["text"] or
            "one teacher only" not in notes["one_teacher"]["text"]):
        raise ValueError("School scope/method changed")
    rows, raw_index = [], {}
    phases = {o["id"]: o["label"] for f in meta["filters"] if f["id"] == "5cGdi" for o in f["options"]}
    bands = {o["id"]: o["label"] for f in meta["filters"] if f["id"] == "cAd31" for o in f["options"]}
    expected = {(p["period"], t, b) for p in meta["timePeriods"] for t in phases for b in bands}
    for index, raw in enumerate(query["results"]):
        if (set(raw) != {"timePeriod", "geographicLevel", "locations", "filters", "values"} or
                raw["timePeriod"].get("code") != "AY" or set(raw["timePeriod"]) != {"code", "period"} or
                raw["geographicLevel"] != "NAT" or raw["locations"] != {"NAT": "dP0Zw"} or
                set(raw["filters"]) != {"5cGdi", "cAd31"} or
                set(raw["values"]) != {"Wc9V2", "EAicq", "QtxWw"}):
            raise ValueError("School row identity changed")
        key = (raw["timePeriod"]["period"], raw["filters"]["5cGdi"], raw["filters"]["cAd31"])
        if key not in expected or key in raw_index:
            raise ValueError("School grid duplicate or extra row")
        raw_index[key] = (index, raw)
    if set(raw_index) != expected or len(query["results"]) != 176:
        raise ValueError("School grid missing rows")

    def operand(index, raw, indicator):
        return {"raw": raw["values"][indicator], "indicator": indicator,
                "timePeriod": raw["timePeriod"], "filters": raw["filters"],
                "geographicLevel": raw["geographicLevel"], "locations": raw["locations"],
                "source": source(FILES[0], f"/results/{index}/values/{indicator}")}

    for key in sorted(raw_index):
        index, raw = raw_index[key]
        period, phase, band = key
        total_index, total = raw_index[(period, phase, "XdTUf")]
        classes = numeric(raw["values"]["EAicq"], True)
        pupils = numeric(raw["values"]["QtxWw"], True)
        published_mean = numeric(raw["values"]["Wc9V2"])
        total_classes = numeric(total["values"]["EAicq"], True)
        total_pupils = numeric(total["values"]["QtxWw"], True)
        if min(classes, total_classes, total_pupils) <= 0:
            raise ValueError("School zero denominator")
        mean = pupils / classes
        if rounded(mean) != rounded(published_mean):
            raise ValueError("School published mean does not match weighted counts")
        published = {}
        for indicator, unit, precision in (("Wc9V2", "pupils per class", 1),
                                            ("EAicq", "classes", 0), ("QtxWw", "pupils", 0)):
            published[indicator] = {"raw": raw["values"][indicator],
                                    "display": rounded(numeric(raw["values"][indicator]), precision),
                                    "unit": unit, "decimalPlaces": precision, "quality": None,
                                    "source": source(FILES[0], f"/results/{index}/values/{indicator}")}
        derived = {}
        for name, value, unit, formula, operands in (
                ("mean", mean, "pupils per class", "pupils / classes",
                 [operand(index, raw, "QtxWw"), operand(index, raw, "EAicq")]),
                ("class_share", classes / total_classes * 100, "% of classes in this phase",
                 "100 * band classes / published total classes",
                 [operand(index, raw, "EAicq"), operand(total_index, total, "EAicq")]),
                ("pupil_share", pupils / total_pupils * 100, "% of pupils in this phase",
                 "100 * band pupils / published total pupils",
                 [operand(index, raw, "QtxWw"), operand(total_index, total, "QtxWw")])):
            derived[name] = {"display": rounded(value), "unit": unit, "decimalPlaces": 1,
                             "rounding": "ROUND_HALF_UP", "formula": formula, "operands": operands}
        anchor = int(period.split("/")[1])
        row_notes = ["geography", "method", "census", "one_teacher",
                     {"TaWMP": "infant", "cDwC3": "ks2"}.get(phase, "phases")]
        rows.append({"timePeriod": dict(raw["timePeriod"]), "anchor": anchor,
                     "census": f"January {anchor}; third Thursday (methodology rule, not an individually reported date)",
                     "geographicLevel": "NAT", "locations": {"NAT": "dP0Zw"},
                     "geography": "England by school location, not pupil residence",
                     "population": POPULATION, "status": STATUS, "filters": dict(raw["filters"]),
                     "phase": phases[phase], "band": bands[band], "notes": row_notes,
                     "source": source(FILES[0], f"/results/{index}"),
                     "published": published, "derived": derived})
    reconciliations = []
    for period in sorted({k[0] for k in raw_index}):
        for phase in sorted(phases):
            components = [raw_index[(period, phase, band)] for band in ("zeoRF", "kxKDh", "u2cKo")]
            ti, total = raw_index[(period, phase, "XdTUf")]
            for indicator in ("EAicq", "QtxWw"):
                band_sum = sum(numeric(r["values"][indicator], True) for _, r in components)
                residual = numeric(total["values"][indicator], True) - band_sum
                reconciliations.append({
                    "timePeriod": total["timePeriod"], "phase": phases[phase], "indicator": indicator,
                    "unit": "classes" if indicator == "EAicq" else "pupils",
                    "population": POPULATION, "geography": "England by school location, not pupil residence",
                    "status": STATUS, "notes": ["geography", "method", "census", "one_teacher"],
                    "band_sum": str(band_sum), "published_total": total["values"][indicator],
                    "residual_total_minus_bands": str(residual),
                    "formula": "published total - sum(three size bands within the same phase)",
                    "operands": [operand(ti, total, indicator)] + [operand(i, r, indicator) for i, r in components],
                    "note": "Retain published totals as denominators; do not force shares to sum to 100 or add overlapping phases."})
    comparisons = []
    for name, left, right in (
            ("primary_2016_to_2026", ("2015/2016", "5kyxd", "XdTUf"), ("2025/2026", "5kyxd", "XdTUf")),
            ("primary_minus_secondary_2026", ("2025/2026", "tfHTE", "XdTUf"), ("2025/2026", "5kyxd", "XdTUf"))):
        li, lr = raw_index[left]
        ri, rr = raw_index[right]
        delta = (numeric(rr["values"]["QtxWw"], True) / numeric(rr["values"]["EAicq"], True) -
                 numeric(lr["values"]["QtxWw"], True) / numeric(lr["values"]["EAicq"], True))
        comparisons.append({"id": name, "display": rounded(delta, signed=True), "unit": "pupils per class",
                            "decimalPlaces": 1, "rounding": "ROUND_HALF_UP",
                            "formula": "right pupils / right classes - left pupils / left classes",
                            "operands": [operand(ri, rr, "QtxWw"), operand(ri, rr, "EAicq"),
                                         operand(li, lr, "QtxWw"), operand(li, lr, "EAicq")],
                            "population": POPULATION, "geography": "England by school location, not pupil residence",
                            "status": STATUS, "notes": ["geography", "method", "census", "one_teacher", "phases"]})
    return {
        "schema_version": 1, "domain": "schools", "private": True,
        "scope": {"population": POPULATION, "status": STATUS,
                  "overlap": "Primary overlaps Infant and KS2; these views must never be added.",
                  "meaning": "Class size is not pupil-teacher ratio or an individual child's actual class.",
                  "series": "Current release for all eleven years; no old-release splice or January 2021 gap.",
                  "context": "Row context applies to every nested published and derived measure.",
                  "rounding": "Decimal original strings, precision 50; ROUND_HALF_UP at metadata precision"},
        "sources": evidence, "definitions": definitions, "notes": notes,
        "publication": {
            "dataset_id": dataset["id"], "title": dataset["title"], "summary": dataset["summary"],
            "version": version["version"], "api_published": version["published"],
            "version_notes": version["notes"], "status": version["status"],
            "catalogue_release": catalogue["dataSetFile"]["release"],
            "release": {k: release["releaseVersionSummary"][k] for k in
                        ("title", "slug", "published", "lastUpdated", "type", "publication")},
            "methodology": {k: method[k] for k in ("title", "slug", "published")},
            "nextReleaseDate": catalogue["publicationSummary"]["nextReleaseDate"],
            "catalogue_footnotes": catalogue["dataSetFile"]["footnotes"],
            "footnote_caution": "Catalogue footnotes are retained verbatim, not substituted for the class-size population.",
            "provenance": [source(FILES[2], "__NEXT_DATA__/props/pageProps"),
                           source(FILES[3], "__NEXT_DATA__/props/pageProps/data"),
                           source(FILES[4], "__NEXT_DATA__/props/pageProps/releaseVersionSummary")]},
        "quality_codes": {"z": "Not applicable; never zero or a national observation"},
        "catalogue_preview": {
            "data": catalogue["dataSetFile"]["file"]["dataCsvPreview"],
            "source": source(FILES[2], "__NEXT_DATA__/props/pageProps/dataSetFile/file/dataCsvPreview"),
            "caution": "Local-authority preview, not extra national rows; retain raw z and every blank."},
        "rows": rows, "reconciliations": reconciliations, "comparisons": comparisons,
    }
