"""Reproduce the bounded, explicitly partial party seed from retained evidence only.

No HTTP, publication, fiscal certification or guesses about current policy status.
The two 2024 examples exercise real provenance; they are not a complete survey.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re

from party_data import ROOT, load_json, retained_bytes, validate


def unavailable(reason):
    return {"availability": "unavailable", "reason": reason, "items": []}


def populated(items):
    return {"availability": "available", "reason": None, "items": items}


def seed(directory):
    directory = Path(directory)
    prefix = directory.relative_to(ROOT).as_posix()
    if not re.fullmatch(r"data/party-evidence/[a-zA-Z0-9_-]+", prefix):
        raise ValueError("input must be a new party-evidence directory")
    acquisition = load_json(retained_bytes(prefix + "/acquisition.json"))
    sources = acquisition["sources"]
    for source in sources:
        for field in ("path", "raw_path"):
            pattern = r"[a-zA-Z0-9_-]+\.txt" if field == "path" else r"[a-zA-Z0-9_-]+-response\.json"
            if not re.fullmatch(pattern, source[field]):
                raise ValueError("unsafe acquisition source path")
            source[field] = prefix + "/" + source[field]
    manifest = {"schema_version": 1, "sources": sources}
    by_id = {s["id"]: s for s in sources}
    text = {key: retained_bytes(s["path"]).decode("utf-8") for key, s in by_id.items()}

    def ref(key, quote):
        start = text[key].index(quote)
        return {"source_id": key, "start": start, "end": start + len(quote), "quote": quote}

    def section(key, start, end):
        source = text[key]
        return source[source.index(start):source.index(end, source.index(start))].strip()

    roster = by_id["commons"]["snapshot_as_of"]
    parties, non_party = [], []
    for row in load_json(text["commons"])["items"]:
        value, party = row["value"], row["value"]["party"]
        key, name = str(party["id"]), party["name"]
        if key == "47" and name == "Speaker" or party["isIndependentParty"]:
            non_party.append({"parliament_id": key, "name": name,
                              "classification": "speaker" if key == "47" else "independent",
                              "mp_count": value["total"]})
            continue
        pubs = [s["id"] for s in sources if s["kind"] == "party" and s["party_id"] == key]
        domains = {"15": "labour.org.uk", "29": "snp.org", "1115": "yourparty.uk"}
        parties.append({"id": key, "name": name, "official_domain": domains.get(key),
                        "mp_count": value["total"], "publication_sources": pubs,
                        "coverage": "unavailable", "unavailable_reason":
                        "No proposal dataset acquired for this party in this bounded seed; coverage remains pending.",
                        "proposals": []})
    by_party = {p["id"]: p for p in parties}

    labour_key = "labour-fiscal-2024"
    table = section(labour_key, "Public Services\n", "Green Prosperity Plan\n")
    cost_quote = re.search(r"Total including Barnett consequentials\n([\d,]+)", table).group()
    funding_quote = re.search(r"Total\n([\d,]+)", table).group()
    assessment_key = "resolution-comparison-2024"
    assessment = section(assessment_key, "Neither of the manifestos have much to say", "On top of this,")
    labour = {
        "id": "labour-public-services-2024", "title": "Additional public services spending (2024 manifesto)",
        "proposal_date": by_id[labour_key]["published_on"], "fiscal_year": "2028-29", "fiscal_year_reason": None,
        "baseline": "Source uses the last year of the most recent OBR forecast (2028-29); additional spending, not total departmental budgets.",
        "scope": "Public Services table including Barnett consequentials. Excludes Green Prosperity Plan and reallocations. Not all revenue is allocated to spending.",
        "geography": "Mixed service remits; source footnotes distinguish England and Wales, UK-wide costs and Barnett allocations to Scotland, Wales and Northern Ireland.",
        "status": "proposed", "evidence": ref(labour_key, table),
        "costs_claimed": populated([{"amount": cost_quote.split("\n")[-1].replace(",", ""),
                                    "unit": "GBP million", "basis": "annual", "evidence": ref(labour_key, cost_quote)}]),
        "funding_claimed": populated([{"amount": funding_quote.split("\n")[-1].replace(",", ""),
                                      "unit": "GBP million", "basis": "annual", "evidence": ref(labour_key, funding_quote)}]),
        "assessments": populated([{"publisher": "Resolution Foundation", "assessed_on": "2024-06-14",
                                   "scope": "Overall Conservative and Labour spending plans; not verification of this individual table or of a 2026 plan.",
                                   "evidence": ref(assessment_key, assessment)}]),
        "overlap_key": "labour-public-services-2024", "overlaps_with": [],
    }
    snp_key = "snp-speech-2024"
    snp_quote = "That would see an extra £1.6 billion for the NHS in Scotland."
    snp_context = section(snp_key, "The SNP manifesto argues for new, sensible fiscal rules", "We will demand an end")
    snp = {
        "id": "snp-nhs-scotland-2024", "title": "NHS funding in Scotland (2024 launch speech)",
        "proposal_date": by_id[snp_key]["published_on"], "fiscal_year": None,
        "fiscal_year_reason": "The retained speech does not state a fiscal year for the extra NHS allocation.",
        "baseline": "Additional funding in the 2024 launch speech; a quantified comparison baseline is unavailable in this passage.",
        "scope": "Additional NHS allocation in Scotland described in a Westminster manifesto launch speech; not a full plan costing.",
        "geography": "Scotland", "status": "proposed", "evidence": ref(snp_key, snp_context),
        "costs_claimed": populated([{"amount": re.search(r"£([\d.]+) billion", snp_quote).group(1),
                                    "unit": "GBP billion", "basis": "unspecified", "evidence": ref(snp_key, snp_quote)}]),
        "funding_claimed": unavailable("No specific revenue amount tied to this allocation established in the retained speech."),
        "assessments": unavailable("No assessment of this allocation from a rubric-named body retained in this seed."),
        "overlap_key": "snp-nhs-scotland-2024", "overlaps_with": [],
    }
    for key, proposal in (("15", labour), ("29", snp)):
        by_party[key].update(coverage="recorded", unavailable_reason=None, proposals=[proposal])
    by_party["1115"]["unavailable_reason"] = (
        "Retained Political Statement landing describes principles and links to a printable draft. "
        "It supplies no costed fiscal plan here; linked documents and current plan coverage remain unverified.")
    data = {"schema_version": 1, "status": "candidate", "as_of": roster, "reason": None,
            "roster_sources": ["commons"],
            "parties": sorted(parties, key=lambda p: (p["name"].casefold(), p["id"])),
            "non_party_members": sorted(non_party, key=lambda p: p["parliament_id"]),
            "reviews": {"fiscal": None, "editorial": None}}
    # Validate *all* hashes, complete response extraction, roster and claims before writing.
    validate(data, manifest, as_of=date.fromisoformat(max(s["retrieved_at"][:10] for s in sources)))
    return data, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        data, manifest = seed(args.evidence_dir.resolve())
        for name, value in (("parties.json", data), ("party-sources.json", manifest)):
            path = ROOT / "data" / name
            if any(p.is_symlink() for p in (path, *path.parents)):
                raise ValueError("party output contains symlink")
        for name, value in (("parties.json", data), ("party-sources.json", manifest)):
            (ROOT / "data" / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, OSError, KeyError, AttributeError) as error:
        parser.exit(1, f"Party import refused before publication: {error}\n")
    print("Partial candidate written; coverage and independent factory review remain pending")


if __name__ == "__main__":
    main()
