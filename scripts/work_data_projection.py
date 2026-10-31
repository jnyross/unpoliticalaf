"""Private, memory-only projection of the complete retained APS source foundation.

Published cells remain literal integers with their CSV rows and source locators.
No comparisons, uncertainty interpretation, derived file or public output.
"""
from copy import deepcopy
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
KINDS = ("definition", "jtype", "ftpt", "etype", "c_sex", "measure",
         "measures", "occupation", "time")
OCCUPATIONS = (0, 1000001, 2000000, 3000000, 4000000, 5000000,
               6000000, 7000000, 8000000, 9000000)
SCOPE = json.loads(r'''{
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


def filename(dataset, kind):
    suffix = "sex" if dataset == 210 and kind == "c_sex" else kind
    return f"aps{dataset}-{suffix}.json.json"


FILES = tuple(name for dataset in (210, 218) for name in
              (f"aps{dataset}-uk-calendar-annual.csv",
               *(filename(dataset, kind) for kind in KINDS)))


def strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate work data JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite work data JSON: " + value)

    def finite(value):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else invalid(value)

    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid,
                      parse_float=finite)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def read(root, relative):
    if type(relative) is not str:
        raise ValueError("Invalid work data path")
    part = Path(relative)
    if (not part.parts or part.is_absolute() or ".." in part.parts
            or str(part) != relative):
        raise ValueError("Unsafe work data path")
    root = Path(root).absolute()
    path = root / part
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Work data symlinks forbidden")
    try:
        metadata = path.stat()
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1
                or not path.resolve().is_relative_to(root.resolve())):
            raise ValueError("Work data must be an unlinked regular file inside root")
        return path.read_bytes()
    except OSError as exc:
        raise ValueError("Work data file unavailable: " + relative) from exc


def sources(root):
    raw = read(root, REGISTER)
    if digest(raw) != REGISTER_SHA256:
        raise ValueError("Pinned work data register changed")
    register = strict_json(raw)
    entries = register["sources"]
    paths = {DIRECTORY + "/" + name for name in FILES}
    if (type(register["schema_version"]) is not int
            or register["schema_version"] != 1 or register["domain"] != "work-data"
            or len(entries) != 20 or {e["path"] for e in entries} != paths):
        raise ValueError("Work data closed source register changed")
    directory = Path(root).absolute() / DIRECTORY
    if (any(p.is_symlink() for p in (directory, *directory.parents))
            or not directory.is_dir()
            or {p.name for p in directory.iterdir()} != set(FILES)):
        raise ValueError("Work data closed source directory changed")
    originals, evidence = {}, {}
    for entry in entries:
        stored = read(root, entry["path"])
        if "stored_sha256" in entry:
            if (len(stored) != entry["stored_bytes"]
                    or digest(stored) != entry["stored_sha256"]):
                raise ValueError("Work data stored hash/length mismatch")
            envelope = strict_json(stored)
            if (type(envelope) is not dict
                    or set(envelope) != {"encoding", "original_response"}
                    or envelope["encoding"] != "utf-8"
                    or type(envelope["original_response"]) is not str):
                raise ValueError("Work data envelope changed")
            body = envelope["original_response"].encode("utf-8")
            strict_json(body)
        else:
            body = stored
        if len(body) != entry["bytes"] or digest(body) != entry["sha256"]:
            raise ValueError("Work data original hash/length mismatch")
        name = Path(entry["path"]).name
        originals[name], evidence[name] = body, dict(entry)
    return originals, evidence


def locator(entry):
    return {key: entry[key] for key in ("path", "url", "sha256")}


def code_list(originals, dataset, kind):
    structure = strict_json(originals[filename(dataset, kind)])["structure"]
    field = ("C_OCCPUK11H_0" if dataset == 210 else "SOC2020_FULL") if kind == "occupation" else kind.upper()
    lists = structure["codelists"]["codelist"]
    if (structure["header"]["id"] != f"NM_{dataset}_1" or len(lists) != 1
            or lists[0]["id"] != f"CL_{dataset}_1_{field}"):
        raise ValueError("Work data codelist belongs to wrong dataset/dimension")
    codes = lists[0]["code"]
    if len({str(code["value"]) for code in codes}) != len(codes):
        raise ValueError("Duplicate work data catalogue code")
    return lists[0]


def project(root=ROOT):
    originals, evidence = sources(root)
    datasets = []
    for dataset, first, last, classification in (
            (210, 2011, 2021, "SOC2010"), (218, 2021, 2025, "SOC2020")):
        occupation = "C_OCCPUK11H_0" if dataset == 210 else "SOC2020_FULL"
        structure = strict_json(originals[filename(dataset, "definition")])["structure"]
        families = structure["keyfamilies"]["keyfamily"]
        if len(families) != 1 or families[0]["id"] != f"NM_{dataset}_1":
            raise ValueError("Wrong work data definition")
        selected = {"jtype": (0,), "ftpt": (0,), "etype": (0,),
                    "c_sex": (0, 1, 2), "measure": (1,), "measures": (20100, 20701),
                    "occupation": OCCUPATIONS,
                    "time": tuple(f"{year}-12" for year in range(first, last + 1))}
        catalogues = {}
        for kind, wanted in selected.items():
            catalogue = code_list(originals, dataset, kind)
            by_code = {str(code["value"]): code for code in catalogue["code"]}
            try:
                codes = [by_code[str(code)] for code in wanted]
            except KeyError as exc:
                raise ValueError("Missing requested work data code") from exc
            catalogues[kind] = {"source": locator(evidence[filename(dataset, kind)]),
                                "id": catalogue["id"], "selected": codes}
        # Query fixes these codes; CSV labels alone must never pick another code.
        labels = {}
        for kind in ("jtype", "ftpt", "etype", "c_sex", "measure", "measures"):
            labels[kind] = {}
            for code in catalogues[kind]["selected"]:
                if kind == "measures":
                    descriptions = [a["annotationtext"] for a in code["annotations"]["annotation"]
                                    if a["annotationtitle"] == "Description"]
                    if len(descriptions) != 1:
                        raise ValueError("Missing measure Description binding")
                    label = descriptions[0]
                else:
                    label = code["description"]["value"]
                if label in labels[kind]:
                    raise ValueError("Ambiguous work data label")
                labels[kind][label] = code["value"]
        csv_name = f"aps{dataset}-uk-calendar-annual.csv"
        reader = csv.DictReader(io.StringIO(originals[csv_name].decode("utf-8")), strict=True)
        expected_header = ["DATE", "DATE_NAME", "GEOGRAPHY_CODE", "GEOGRAPHY_NAME",
                           "JTYPE_NAME", "FTPT_NAME", "ETYPE_NAME", "C_SEX_NAME",
                           occupation, occupation + "_NAME", "MEASURE_NAME", "MEASURES_NAME",
                           "OBS_VALUE", "OBS_STATUS", "OBS_STATUS_NAME", "OBS_CONF",
                           "OBS_CONF_NAME", "RECORD_COUNT"]
        if reader.fieldnames != expected_header:
            raise ValueError("Work data CSV header changed")
        rows = []
        for fields in reader:
            if None in fields or any(value is None for value in fields.values()):
                raise ValueError("Ragged work data CSV")
            if re.fullmatch(r"0|[1-9][0-9]*", fields["OBS_VALUE"]) is None:
                raise ValueError("Missing or noninteger work data value")
            try:
                codes = {kind.upper(): labels[kind][fields[kind.upper() + "_NAME"]]
                         for kind in labels}
            except KeyError as exc:
                raise ValueError("Work data CSV/codelist label mismatch") from exc
            rows.append({"line": reader.line_num, "fields": fields,
                         "codes": codes, "value": int(fields["OBS_VALUE"])})
        datasets.append({"id": f"NM_{dataset}_1", "classification": classification,
                         "definition": families[0], "catalogues": catalogues,
                         "source": locator(evidence[csv_name]), "rows": rows})
    return {"schema_version": 1, "domain": "work-data", "private": True,
            "status": "Source foundation; v2 unassessed; human evidence pending.",
            "scope": deepcopy(SCOPE), "sources": evidence, "datasets": datasets}
