"""Independent raw-byte work-data audit; no producer parser or constants as oracle."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/life/sources/work-data"
REGISTER = "data/life/work-data-sources.json"
REGISTER_SHA256 = "7012808e1caecc0ad20bc8ff5cdd012e648db355582dc74a5da22989ccb46baa"
OCCUPATIONS = [0, 1000001, 2000000, 3000000, 4000000, 5000000,
               6000000, 7000000, 8000000, 9000000]
KINDS = ("jtype", "ftpt", "etype", "c_sex", "measure", "measures", "occupation", "time")


def require(condition, message):
    if not condition:
        raise ValueError("Work data: " + message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), "mismatch: " + label)


def decode(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Work data: nonfinite JSON number " + value)

    def floating(value):
        number = float(value)
        require(math.isfinite(number), "nonfinite JSON number")
        return number

    return json.loads(body, object_pairs_hook=unique, parse_constant=nonfinite,
                      parse_float=floating)


def read(root, relative):
    require(type(relative) is str, "invalid path")
    part = Path(relative)
    require(bool(part.parts) and not part.is_absolute() and ".." not in part.parts
            and str(part) == relative, "unsafe path")
    root = Path(root).absolute()
    path = root / part
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlinks forbidden")
    metadata = path.stat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
            and path.resolve().is_relative_to(root.resolve()), "unsafe regular file")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def layout(number):
    prefix = "aps" + str(number) + "-"
    occupation = "c_occpuk11h_0" if number == 210 else "soc2020_full"
    return {
        "definition": (prefix + "definition.json.json", "def"),
        "jtype": (prefix + "jtype.json.json", "jtype.def"),
        "ftpt": (prefix + "ftpt.json.json", "ftpt.def"),
        "etype": (prefix + "etype.json.json", "etype.def"),
        "c_sex": (prefix + ("sex" if number == 210 else "c_sex") + ".json.json", "c_sex.def"),
        "measure": (prefix + "measure.json.json", "measure.def"),
        "measures": (prefix + "measures.json.json", "measures.def"),
        "occupation": (prefix + "occupation.json.json", occupation + ".def"),
        "time": (prefix + "time.json.json", "time.def"),
        "csv": (prefix + "uk-calendar-annual.csv", occupation)}


def csv_url(number):
    occupation = "c_occpuk11h_0" if number == 210 else "soc2020_full"
    years = range(2011, 2022) if number == 210 else range(2021, 2026)
    return (
        "https://www.nomisweb.co.uk/api/v01/dataset/NM_" + str(number) +
        "_1.data.csv?geography=2092957697&jtype=0&ftpt=0&etype=0&c_sex=0,1,2&" +
        occupation + "=0,1000001,2000000,3000000,4000000,5000000,6000000,7000000,8000000,9000000" +
        "&measure=1&measures=20100,20701&date=" + ",".join(str(y) + "-12" for y in years) +
        "&select=date,date_name,geography_code,geography_name,jtype_name,ftpt_name,etype_name,c_sex_name," +
        occupation + "," + occupation +
        "_name,measure_name,measures_name,obs_value,obs_status,obs_status_name,obs_conf,obs_conf_name,record_count")


def reopen(root=ROOT):
    raw = read(root, REGISTER)
    require(digest(raw) == REGISTER_SHA256, "pinned register changed")
    manifest = decode(raw)
    same(manifest["schema_version"], 1, "register schema")
    same(manifest["domain"], "work-data", "register domain")
    expected_urls = {}
    for number in (210, 218):
        for kind, (name, endpoint) in layout(number).items():
            expected_urls[name] = (csv_url(number) if kind == "csv" else
                "https://www.nomisweb.co.uk/api/v01/dataset/NM_" +
                str(number) + "_1/" + endpoint + ".sdmx.json")
    entries = manifest["sources"]
    require(type(entries) is list and len(entries) == 20, "closed 20-source register")
    require({entry["path"] for entry in entries} ==
            {DIRECTORY + "/" + name for name in expected_urls}, "closed source paths")
    directory = Path(root).absolute() / DIRECTORY
    require(not any(p.is_symlink() for p in (directory, *directory.parents)),
            "source directory symlink")
    require(stat.S_ISDIR(directory.stat().st_mode) and
            {p.name for p in directory.iterdir()} == set(expected_urls), "closed source directory")
    originals, evidence = {}, {}
    for name, url in expected_urls.items():
        entry = next(e for e in entries if e["path"] == DIRECTORY + "/" + name)
        same(entry["url"], url, "exact official URL")
        stored = read(root, entry["path"])
        if name.endswith(".csv"):
            body = stored
            require("stored_bytes" not in entry and "stored_sha256" not in entry,
                    "CSV custody format")
        else:
            require(len(stored) == entry["stored_bytes"] and
                    digest(stored) == entry["stored_sha256"], "stored envelope hash/length")
            envelope = decode(stored)
            require(type(envelope) is dict and
                    set(envelope) == {"encoding", "original_response"} and
                    envelope["encoding"] == "utf-8" and
                    type(envelope["original_response"]) is str, "exact UTF8 envelope")
            body = envelope["original_response"].encode("utf-8")
            decode(body)
        require(len(body) == entry["bytes"] and digest(body) == entry["sha256"],
                "original hash/length")
        originals[name] = body
        evidence[name] = dict(entry)
    require(sum(len(body) for body in originals.values()) == 690629, "original byte total")
    require(sum(e.get("stored_bytes", e["bytes"]) for e in evidence.values()) == 749071,
            "stored byte total")
    return originals, evidence


def reference(evidence, name):
    return {key: evidence[name][key] for key in ("path", "url", "sha256")}


def annotations(record):
    entries = record.get("annotations", {}).get("annotation", [])
    require(type(entries) is list, "annotation list")
    result = {}
    for entry in entries:
        require(entry["annotationtitle"] not in result, "duplicate annotation title")
        result[entry["annotationtitle"]] = entry["annotationtext"]
    return result


def check(projection, originals, evidence):
    expected_names = {name for number in (210, 218) for name, _ in layout(number).values()}
    same(sorted(originals), sorted(expected_names), "original source closure")
    same(sorted(evidence), sorted(expected_names), "evidence source closure")
    datasets = []
    for number, classification, first, last, count, occupation, time_count, occupation_count in (
            (210, "SOC2010", 2011, 2021, 660, "C_OCCPUK11H_0", 64, 494),
            (218, "SOC2020", 2021, 2025, 300, "SOC2020_FULL", 19, 552)):
        files = layout(number)
        identity = "NM_" + str(number) + "_1"
        codeprefix = "CL_" + str(number) + "_1_"
        periods = [str(y) + "-12" for y in range(first, last + 1)]
        definition_doc = decode(originals[files["definition"][0]])["structure"]
        same(definition_doc["header"]["id"], identity, "definition dataset")
        require(len(definition_doc["keyfamilies"]["keyfamily"]) == 1, "one keyfamily")
        definition = definition_doc["keyfamilies"]["keyfamily"][0]
        same(definition["id"], identity, "keyfamily dataset")
        same(annotations(definition)["Units"], "Persons", "unit persons")
        same(annotations(definition)["LastUpdated"],
             "2022-04-12 07:00:00" if number == 210 else "2026-10-20 07:00:00",
             "dataset last update")
        dimensions = {d["conceptref"]: d["codelist"] for d in definition["components"]["dimension"]}
        selected, maps = {}, {}
        requested = {
            "jtype": [0], "ftpt": [0], "etype": [0], "c_sex": [0, 1, 2],
            "measure": [1], "measures": [20100, 20701],
            "occupation": OCCUPATIONS, "time": periods}
        for kind in KINDS:
            name = files[kind][0]
            structure = decode(originals[name])["structure"]
            same(structure["header"]["id"], identity, "catalogue dataset")
            require(len(structure["codelists"]["codelist"]) == 1, "one codelist")
            catalogue = structure["codelists"]["codelist"][0]
            concept = occupation if kind == "occupation" else kind.upper()
            same(catalogue["id"], codeprefix + concept, "dataset-specific codelist")
            if kind == "time":
                same(definition["components"]["timedimension"]["codelist"],
                     catalogue["id"], "time dimension binding")
            else:
                same(dimensions[concept], catalogue["id"], "dimension binding")
            codes = catalogue["code"]
            require(type(codes) is list, "complete code list")
            mapping = {}
            for code in codes:
                key = code["value"]
                require(type(key) is (str if kind == "time" else int) and key not in mapping,
                        "unique typed source codes")
                require(type(code["description"]["value"]) is str, "literal code label")
                annotations(code)
                mapping[key] = code
            if kind in ("time", "occupation"):
                same(len(codes), time_count if kind == "time" else occupation_count,
                     "complete original catalogue")
            chosen = [mapping[code] for code in requested[kind]]
            selected[kind] = {"source": reference(evidence, name), "id": catalogue["id"],
                              "selected": chosen}
            maps[kind] = mapping
        for kind in ("jtype", "ftpt", "etype"):
            same(maps[kind][0]["description"]["value"], "Total", "total label")
        same([maps["c_sex"][c]["description"]["value"] for c in (0, 1, 2)],
             ["All persons", "Males", "Females"], "sex binding")
        same(maps["measure"][1]["description"]["value"], "Count", "count measure")
        for code, literal in ((20100, "Value"), (20701, "Confidence")):
            same(maps["measures"][code]["description"]["value"], literal.lower(),
                 "lowercase measures description")
            same(annotations(maps["measures"][code])["Description"], literal,
                 "capitalised measures annotation")
        for period in periods:
            year = period[:4]
            same(maps["time"][period]["description"]["value"],
                 "Jan " + year + "-Dec " + year, "actual calendar label")
        # Deliberately retain known contradictions, without repairing source metadata.
        if number == 210:
            same(annotations(maps["time"]["2011-12"]), {}, "unknown earliest weighting annotation")
            same(annotations(maps["time"]["2019-12"])["end period"], "2010-12-01",
                 "retained conflicting end annotation")
        else:
            same(annotations(maps["time"]["2025-12"])["start period"], "2025-09-01",
                 "retained conflicting start annotation")
        name = files["csv"][0]
        reader = csv.DictReader(io.StringIO(originals[name].decode("utf-8"), newline=""),
                                strict=True)
        header = ["DATE", "DATE_NAME", "GEOGRAPHY_CODE", "GEOGRAPHY_NAME", "JTYPE_NAME",
                  "FTPT_NAME", "ETYPE_NAME", "C_SEX_NAME", occupation, occupation + "_NAME",
                  "MEASURE_NAME", "MEASURES_NAME", "OBS_VALUE", "OBS_STATUS", "OBS_STATUS_NAME",
                  "OBS_CONF", "OBS_CONF_NAME", "RECORD_COUNT"]
        same(reader.fieldnames, header, "exact CSV header")
        sex_lookup = {maps["c_sex"][c]["description"]["value"]: c for c in (0, 1, 2)}
        measure_lookup = {annotations(maps["measures"][c])["Description"]: c for c in (20100, 20701)}
        grid, rows = {}, []
        for row in reader:
            require(set(row) == set(header) and all(type(v) is str for v in row.values()),
                    "complete CSV fields")
            require(reader.line_num == len(rows) + 2, "single physical CSV record")
            for column, value in (
                    ("GEOGRAPHY_CODE", "K02000001"), ("GEOGRAPHY_NAME", "United Kingdom"),
                    ("JTYPE_NAME", maps["jtype"][0]["description"]["value"]),
                    ("FTPT_NAME", maps["ftpt"][0]["description"]["value"]),
                    ("ETYPE_NAME", maps["etype"][0]["description"]["value"]),
                    ("MEASURE_NAME", maps["measure"][1]["description"]["value"]),
                    ("OBS_STATUS", "A"), ("OBS_STATUS_NAME", "Normal Value"),
                    ("OBS_CONF", "F"), ("OBS_CONF_NAME", "Free (free for publication)"),
                    ("RECORD_COUNT", str(count))):
                same(row[column], value, "source context " + column)
            require(row["DATE"] in periods, "only requested calendar periods")
            same(row["DATE_NAME"], maps["time"][row["DATE"]]["description"]["value"],
                 "DATE_NAME binding, not start/end annotations")
            require(re.fullmatch(r"0|[1-9][0-9]*", row[occupation]) is not None,
                    "integer occupation code")
            occupation_code = int(row[occupation])
            require(occupation_code in OCCUPATIONS, "selected occupation")
            same(row[occupation + "_NAME"], maps["occupation"][occupation_code]["description"]["value"],
                 "exact occupation code-label binding")
            sex = sex_lookup[row["C_SEX_NAME"]]
            measure = measure_lookup[row["MEASURES_NAME"]]
            require(re.fullmatch(r"0|[1-9][0-9]*", row["OBS_VALUE"]) is not None,
                    "published nonnegative integer; missing is not zero")
            value = int(row["OBS_VALUE"])
            key = (row["DATE"], occupation_code, sex, measure)
            require(key not in grid, "duplicate observation")
            grid[key] = value
            rows.append({"line": reader.line_num, "fields": row,
                         "codes": {"JTYPE": 0, "FTPT": 0, "ETYPE": 0, "C_SEX": sex,
                                   "MEASURE": 1, "MEASURES": measure}, "value": value})
        expected_grid = {(p, o, s, m) for p in periods for o in OCCUPATIONS
                         for s in (0, 1, 2) for m in (20100, 20701)}
        require(set(grid) == expected_grid and len(rows) == count, "complete unique observation grid")
        require(any(grid[(p, 0, s, 20100)] !=
                    sum(grid[(p, o, s, 20100)] for o in OCCUPATIONS[1:])
                    for p in periods for s in (0, 1, 2)),
                "published totals must not become an exhaustive occupation partition")
        datasets.append({"id": identity, "classification": classification, "definition": definition,
                         "catalogues": selected, "source": reference(evidence, name), "rows": rows})
    scope = decode(r'''{
  "geography": {
    "code": "K02000001",
    "name": "United Kingdom",
    "query_code": "2092957697"
  },
  "unit": "people",
  "source_unit": "Persons",
  "population_contract": "UK resident persons aged 16+ in work, including employees, self-employed people, unpaid family workers and temporary absence; communal-establishment and Armed Forces exceptions require the separate methods foundation. APS people and ASHE employee jobs on adult rates must not form a ratio.",
  "period_binding": "DATE and DATE_NAME bind calendar years; conflicting raw start/end annotations are preserved, never repaired.",
  "quality_cross_check": "Separate methods foundation required before public claims: survey estimates, declining response, official statistics in development and outdated population weights. No methods HTML is a local input to this projection.",
  "confidence_20701": null,
  "suppression_definition": null,
  "indicative_definition": null,
  "denominator": null,
  "formulas": [],
  "revision_limits": [
    "Catalogue comments and version 0 do not prove a complete revision history or an unrevised vintage; absent annotations do not prove a correction or weighting vintage.",
    "APS210 last updated 12 April 2022 predates the later 2022 and 2023 notices; neither 2021 catalogue entry proves receipt of those revisions. Do not attribute overlap differences to SOC alone.",
    "RTI reweighting starts October 2020–September 2021 onwards; the separate Northern Ireland response adjustment has no stated start period in the retained notice. These are methods cross-references, not claims independently established by this closed source set."
  ],
  "required_later_ui_notes": [
    "Nomis later reported an occupation coding error affecting periods from April 2020–March 2021; this SOC2010 dataset records no revision for 2021.",
    "Nomis reported a Wales weighting error affecting this period; UK figures largely unaffected; no revision recorded in this dataset.",
    "Neither note proves whether a correction occurred. APS210 2011-12 has no annotation; its precise weighting vintage remains unknown."
  ],
  "comparisons": "No delta, occupation-share partition, SOC join, interpolation, significance, error bars or causal decomposition."
}''')
    expected = {
        "schema_version": 1, "domain": "work-data", "private": True,
        "status": "Source foundation; v2 unassessed; human evidence pending.",
        "scope": scope, "sources": evidence, "datasets": datasets}
    # Canonical strict JSON distinguishes booleans, integers and floats, rejects
    # nonfinite values, and closes every field against independently reopened bytes.
    same(projection, expected, "complete private projection")
    return sum(len(dataset["rows"]) for dataset in datasets)


def validate(root=ROOT, projection=None):
    try:
        originals, evidence = reopen(root)
        if projection is None:
            from work_data_projection import project
            projection = project(root)
            same(projection, project(root), "deterministic in-memory projection")
        return check(projection, originals, evidence)
    except (KeyError, TypeError, IndexError, OSError, UnicodeError, csv.Error) as error:
        raise ValueError("Malformed work data projection/source") from error


if __name__ == "__main__":
    print(f"Verified {validate()} private work source rows; v2 remains unassessed")
