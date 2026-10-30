"""Offline Commons party-plan contract. Acquisition and promotion belong to the controller."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from acquire_party_evidence import readable

ROOT = Path(__file__).resolve().parent.parent
# Named bodies: pinned reference/un-political/docs/rubric.md §2 level 3,
# SHA256 97dce23dec4003babc2865f80e7a65cda23fe86bcf94d01dc506605b45249a70.
# Full publisher names/domains resolve the rubric's abbreviations; they are
# provenance checks, never a claim that a body reviewed any candidate.
ASSESSORS = {
    "Institute for Fiscal Studies": "ifs.org.uk",
    "Office for Budget Responsibility": "obr.uk",
    "Resolution Foundation": "resolutionfoundation.org",
    "Full Fact": "fullfact.org",
    "National Audit Office": "nao.org.uk",
}
ROOT_FIELDS = "schema_version status as_of reason roster_sources parties non_party_members reviews"
SOURCE_FIELDS = ("id kind publisher party_id url published_on publication_locator retrieved_at "
                 "snapshot_as_of path sha256 raw_path raw_sha256")
PARTY_FIELDS = "id name official_domain mp_count publication_sources coverage unavailable_reason proposals"
PROPOSAL_FIELDS = ("id title proposal_date fiscal_year fiscal_year_reason baseline scope geography status evidence "
                   "costs_claimed funding_claimed assessments overlap_key overlaps_with")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names, label):
    require(isinstance(value, dict) and set(value) == set(names.split()),
            f"{label}: missing or extra fields")


def text(value, label, limit=400):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            f"{label}: expected nonempty text, at most {limit} characters")
    return value


def day(value, label):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value),
            f"{label}: expected ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{label}: invalid date") from error


def integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, f"{label}: expected integer")
    return value


def sequence(value, label):
    require(isinstance(value, list), f"{label}: expected array")
    return value


def unique(values, label):
    require(len(values) == len(set(values)), f"{label}: duplicate")
    return values


def host(url):
    parts = urlsplit(text(url, "source URL", 2000))
    require(parts.scheme == "https" and parts.hostname and not parts.username
            and not parts.password and parts.port in (None, 443) and not parts.fragment,
            "source URL must be HTTPS without credentials or fragment")
    return parts.hostname.lower()


def domain_match(actual, official):
    return actual == official or actual.endswith("." + official)


def load_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def retained_bytes(path):
    """Read the new party evidence family without changing protected fiscal inputs."""
    require(re.fullmatch(r"data/party-evidence/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.(json|txt|html)", path) is not None,
            "snapshot must be in data/party-evidence with a simple filename")
    target = ROOT / path
    require(not any(p.is_symlink() for p in (target, *target.parents)),
            "snapshot path contains symlink")
    return target.read_bytes()


def candidate_digest(data, manifest):
    """Review binding excludes review receipts, includes every evidence hash and record."""
    candidate = {key: value for key, value in data.items() if key != "reviews"}
    encoded = json.dumps({"data": candidate, "manifest": manifest}, sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def sources(manifest, today, read):
    fields(manifest, "schema_version sources", "party source manifest")
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
            "unsupported source schema")
    result, snapshots = {}, {}
    for source in sequence(manifest["sources"], "sources"):
        fields(source, SOURCE_FIELDS, "source")
        key = text(source["id"], "source id", 100)
        require(key not in result, "duplicate source id")
        require(source["kind"] in ("roster", "party", "assessment"), "unknown source kind")
        text(source["publisher"], "publisher", 160)
        actual_host = host(source["url"])
        stamp = text(source["retrieved_at"], "retrieval timestamp", 60)
        try:
            observed = datetime.fromisoformat(stamp)
        except ValueError as error:
            raise ValueError("invalid retrieval timestamp") from error
        require(observed.tzinfo is not None and observed.utcoffset().total_seconds() == 0,
                "retrieval timestamp must be UTC")
        retrieved = observed.date()
        require(retrieved <= today, "future retrieval date")
        published = source["published_on"]
        if published is not None:
            require(day(published, "publication date") <= retrieved, "publication after retrieval")
        for field in ("sha256", "raw_sha256"):
            require(isinstance(source[field], str)
                    and re.fullmatch(r"[0-9a-f]{64}", source[field]), "invalid snapshot hash")
        path = text(source["path"], "snapshot path", 200)
        require(re.fullmatch(r"data/party-evidence/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.txt", path),
                "invalid protected snapshot path")
        if source["kind"] == "roster":
            require(actual_host == "members-api.parliament.uk", "roster must use Parliament API")
            require(source["party_id"] is None, "roster cannot belong to one party")
            require(published is None and source["publication_locator"] is None,
                    "dated API snapshot is not a publication")
            require(day(source["snapshot_as_of"], "roster snapshot date") <= retrieved,
                    "roster snapshot cannot follow retrieval")
            require((today - retrieved).days <= 30, "stale roster evidence")
        else:
            require(source["snapshot_as_of"] is None and published is not None,
                    "publication metadata missing")
            require((today - retrieved).days <= 90, "stale publication evidence")
            if source["kind"] == "party":
                text(source["party_id"], "party source owner", 100)
            else:
                require(source["party_id"] is None, "assessment source cannot be a party claim")
                require(source["publisher"] in ASSESSORS
                        and domain_match(actual_host, ASSESSORS[source["publisher"]]),
                        "assessment publisher/domain not permitted")
        raw = read(path)
        require(isinstance(raw, bytes), "snapshot reader must return bytes")
        require(hashlib.sha256(raw).hexdigest() == source["sha256"], "changed snapshot hash")
        raw_path = source["raw_path"]
        require(isinstance(raw_path, str) and re.fullmatch(
            r"data/party-evidence/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.(json|html)", raw_path),
            "invalid original response path")
        original = read(raw_path)
        require(hashlib.sha256(original).hexdigest() == source["raw_sha256"],
                "changed original response hash")
        require(readable(original, source["kind"]).encode("utf-8") == raw,
                "readable snapshot differs from complete response extraction")
        if source["kind"] != "roster":
            locator = text(source["publication_locator"], "publication locator", 200)
            require(locator in original.decode("utf-8"), "publication date locator absent")
            match = re.search(r"\d{4}-\d{2}-\d{2}", locator)
            if match:
                located_date = match.group()
            else:
                located_date = None
                for fmt in ("%d %B %Y", "%d %B, %Y"):
                    try:
                        located_date = datetime.strptime(locator, fmt).date().isoformat()
                        break
                    except ValueError:
                        pass
            require(located_date == published, "publication date differs from retained locator")
        snapshots[key] = raw.decode("utf-8")
        result[key] = source
    return result, snapshots


def parliament_parties(ids, catalogue, snapshots, as_of):
    """Reopen the complete official dated StateOfTheParties response.

    This endpoint returns totalResults=0 even when items is populated. It is
    not a paginated Search response. Never treat that metadata as zero MPs.
    """
    require(len(ids) == 1, "exactly one complete dated roster source required")
    key = ids[0]
    require(isinstance(key, str) and key in catalogue, "missing roster source")
    source = catalogue[key]
    require(source["kind"] == "roster" and source["snapshot_as_of"] == as_of,
            "roster source/date mismatch")
    parts = urlsplit(source["url"])
    require(parts.path == f"/api/Parties/StateOfTheParties/1/{as_of}" and not parts.query,
            "roster must request the unfiltered dated Commons state")
    page = load_json(snapshots[key])
    require(isinstance(page, dict), "invalid Parliament page")
    require(page.get("skip") == 0 and page.get("take") == 0,
            "dated roster must not be paginated")
    # Bind the response's self link, not only the requested URL, to house/date.
    stamp = day(as_of, "roster date")
    expected = f"StateOfTheParties/Commons/{stamp.day}/{stamp.month}/{stamp.year} 00:00:00"
    require(any(link.get("rel") == "self" and link.get("href") == expected
                for link in sequence(page.get("links"), "Parliament links")),
            "roster response self link differs from requested house/date")
    represented, non_party = {}, {}
    for row in sequence(page.get("items"), "Parliament items"):
        require(isinstance(row, dict) and isinstance(row.get("value"), dict), "missing roster value")
        value = row["value"]
        party = value.get("party")
        require(isinstance(party, dict) and type(party.get("isIndependentParty")) is bool,
                "missing official party classification")
        key = str(integer(party.get("id"), "Parliament party id", 1))
        name = text(party.get("name"), "Parliament party name", 160)
        count = integer(value.get("total"), "MP count", 1)
        require(sum(integer(value.get(k), "MP subgroup") for k in ("male", "female", "nonBinary")) == count,
                "roster count does not reconcile with subgroups")
        require(key not in represented and key not in non_party, "duplicate Parliament party")
        classification = ("speaker" if (key, name) == ("47", "Speaker") else
                          "independent" if party["isIndependentParty"] else None)
        record = {"name": name, "count": count}
        if classification:
            record["classification"] = classification
            non_party[key] = record
        else:
            represented[key] = record
    require(represented, "empty Commons roster")
    return represented, non_party


def evidence(ref, kind, catalogue, snapshots, used, *, party_id=None, publisher=None):
    fields(ref, "source_id start end quote", "evidence reference")
    key = text(ref["source_id"], "evidence source id", 100)
    require(key in catalogue, "missing evidence source")
    source = catalogue[key]
    require(source["kind"] == kind, "wrong evidence kind")
    if party_id is not None:
        require(source["party_id"] == party_id, "claim belongs to another party")
    if publisher is not None:
        require(source["publisher"] == publisher, "assessment attribution mismatch")
    quote = text(ref["quote"], "verbatim quotation", 4000)
    start = integer(ref["start"], "quotation start")
    end = integer(ref["end"], "quotation end", 1)
    require(start < end <= len(snapshots[key]) and snapshots[key][start:end] == quote,
            "quotation/locator differs from retained snapshot")
    used.add(key)
    return source


def availability(record, label):
    fields(record, "availability reason items", label)
    require(record["availability"] in ("available", "unavailable"), f"{label}: invalid availability")
    items = sequence(record["items"], label + " items")
    if record["availability"] == "unavailable":
        text(record["reason"], label + " reason")
        require(not items, f"{label}: missing is not zero or an invented item")
    else:
        require(record["reason"] is None and bool(items), f"{label}: available requires items")
    return items


def amounts(record, label, party_id, catalogue, snapshots, used, proposal_date):
    items = availability(record, label)
    unique([json.dumps(item, sort_keys=True, allow_nan=False) for item in items], label + " items")
    for item in items:
        fields(item, "amount unit basis evidence", label + " item")
        value = item["amount"]
        require(isinstance(value, str) and re.fullmatch(r"-?(0|[1-9]\d*)(\.\d+)?", value),
                "claimed amount must be an exact decimal string")
        try:
            require(Decimal(value).is_finite(), "non-finite claimed amount")
        except InvalidOperation as error:
            raise ValueError("invalid claimed amount") from error
        require(item["unit"] in ("GBP", "GBP million", "GBP billion"), "unknown claimed unit")
        require(item["basis"] in ("annual", "cumulative", "one_off", "unspecified"),
                "unknown claimed time basis")
        source = evidence(item["evidence"], "party", catalogue, snapshots, used, party_id=party_id)
        require(source["published_on"] == proposal_date, "amount/proposal source-date mismatch")
        tokens = re.findall(r"(?<![\d.])-?\d[\d,]*(?:\.\d+)?(?![\d.])", item["evidence"]["quote"])
        require(any(Decimal(token.replace(",", "")) == Decimal(value) for token in tokens),
                "claimed amount absent from exact source quotation")


def validate(data, manifest, *, as_of=None, read=retained_bytes, require_reviews=False,
             require_coverage=False, factory_reviews=None, binding=None):
    """Validate only: never fetch, mutate, refresh, publish or certify editorial truth."""
    today = as_of or datetime.now(timezone.utc).date()
    require(type(today) is date, "validation as_of must be a date")
    fields(data, ROOT_FIELDS, "party dataset")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1,
            "unsupported party schema")
    require(data["status"] in ("unavailable", "candidate"), "invalid party dataset status")
    catalogue, snapshots = sources(manifest, today, read)
    fields(data["reviews"], "fiscal editorial", "reviews")
    require(all(value is None for value in data["reviews"].values()),
            "in-data approvals prohibited; use external factory verdicts")
    for key in ("roster_sources", "parties", "non_party_members"):
        sequence(data[key], key)
    if data["status"] == "unavailable":
        text(data["reason"], "unavailable dataset reason")
        require(data["as_of"] is None and not catalogue and not data["roster_sources"]
                and not data["parties"] and not data["non_party_members"]
                and all(v is None for v in data["reviews"].values()),
                "unavailable seed cannot claim evidence, records or review")
        require(not (require_reviews or require_coverage), "party publication blocked: roster evidence unavailable")
        return {"status": "unavailable", "review_bindings_complete": False, "reason": data["reason"]}

    require(data["reason"] is None and day(data["as_of"], "roster date") <= today,
            "invalid candidate date/reason")
    require((today - day(data["as_of"], "roster date")).days <= 30, "stale roster snapshot")
    represented, non_party = parliament_parties(data["roster_sources"], catalogue, snapshots, data["as_of"])

    used, party_ids, ordering, proposal_ids, identities = set(data["roster_sources"]), [], [], set(), set()
    for party in data["parties"]:
        fields(party, PARTY_FIELDS, "party")
        key = text(party["id"], "party id", 100)
        party_ids.append(key)
        name = text(party["name"], "party name", 160)
        ordering.append((name.casefold(), key))
        require(key in represented and name == represented[key]["name"], "unrepresented party/name")
        require(integer(party["mp_count"], "party MP count", 1) == represented[key]["count"],
                "party MP coverage differs from Parliament")
        domain = party["official_domain"]
        if domain is not None:
            require(isinstance(domain, str) and re.fullmatch(r"[a-z0-9]+([.-][a-z0-9]+)*\.[a-z]{2,}", domain),
                    "invalid official party domain")
        publication_sources = sequence(party["publication_sources"], "party publications")
        unique(publication_sources, "party publications")
        for source_id in publication_sources:
            require(source_id in catalogue and catalogue[source_id]["kind"] == "party"
                    and catalogue[source_id]["party_id"] == key, "party publication owner mismatch")
            used.add(source_id)
        require(party["coverage"] in ("recorded", "unavailable"), "invalid party coverage")
        proposals = sequence(party["proposals"], "proposals")
        if party["coverage"] == "unavailable":
            text(party["unavailable_reason"], "party evidence unavailable reason")
            require(not proposals, "unavailable proposals cannot contain claims")
        else:
            require(domain is not None and party["unavailable_reason"] is None and proposals,
                    "recorded coverage requires official domain and proposals")
        groups = {}
        order = []
        for proposal in proposals:
            fields(proposal, PROPOSAL_FIELDS, "proposal")
            proposal_id = text(proposal["id"], "proposal id", 100)
            require(proposal_id not in proposal_ids, "duplicate proposal id")
            proposal_ids.add(proposal_id)
            title = text(proposal["title"], "proposal title", 160)
            order.append((title.casefold(), proposal_id))
            proposed = day(proposal["proposal_date"], "proposal date")
            require(proposed <= today, "future proposal publication date")
            year = proposal["fiscal_year"]
            if year is None:
                text(proposal["fiscal_year_reason"], "unavailable fiscal year reason")
            else:
                require(isinstance(year, str) and re.fullmatch(r"\d{4}-\d{2}", year)
                        and (int(year[:4]) + 1) % 100 == int(year[-2:]), "invalid fiscal year")
                require(proposal["fiscal_year_reason"] is None, "known fiscal year cannot have missing reason")
            for field in ("baseline", "scope", "geography"):
                text(proposal[field], field)
            require(proposal["status"] in ("proposed", "adopted", "withdrawn", "superseded"),
                    "invalid proposal status")
            src = evidence(proposal["evidence"], "party", catalogue, snapshots, used, party_id=key)
            require(src["id"] in publication_sources, "proposal source absent from party publications")
            require(src["published_on"] == proposal["proposal_date"], "proposal/source date mismatch")
            identity = (key, src["sha256"],
                        proposal["evidence"]["start"], proposal["evidence"]["end"])
            require(identity not in identities, "duplicate proposal excerpt; merge duplicate record")
            identities.add(identity)
            for field in ("costs_claimed", "funding_claimed"):
                amounts(proposal[field], field, key, catalogue, snapshots, used, proposal["proposal_date"])
            for item in availability(proposal["assessments"], "assessments"):
                fields(item, "publisher assessed_on scope evidence", "assessment")
                text(item["scope"], "assessment scope")
                require(item["publisher"] in ASSESSORS, "unapproved independent assessor")
                src = evidence(item["evidence"], "assessment", catalogue, snapshots, used,
                               publisher=item["publisher"])
                require(src["published_on"] == item["assessed_on"]
                        and proposed <= day(item["assessed_on"], "assessment date") <= today,
                        "assessment date mismatch")
            group = text(proposal["overlap_key"], "overlap key", 100)
            related = sequence(proposal["overlaps_with"], "overlaps_with")
            for other in related:
                text(other, "overlapping proposal id", 100)
            unique(related, "overlaps_with")
            groups.setdefault(group, []).append(proposal)
        # Offset intersections cannot be concealed by declaring different overlap keys.
        for index, left in enumerate(proposals):
            for right in proposals[index + 1:]:
                a, b = left["evidence"], right["evidence"]
                if (catalogue[a["source_id"]]["sha256"] == catalogue[b["source_id"]]["sha256"]
                        and max(a["start"], b["start"]) < min(a["end"], b["end"])):
                    require(left["overlap_key"] == right["overlap_key"]
                            and right["id"] in left["overlaps_with"]
                            and left["id"] in right["overlaps_with"],
                            "overlapping proposal excerpts require explicit symmetric overlap group")
        require(order == sorted(order), "proposals must be alphabetical")
        for group in groups.values():
            for proposal in group:
                require(sorted(proposal["overlaps_with"]) ==
                        sorted(p["id"] for p in group if p["id"] != proposal["id"]),
                        "overlap group must be explicit, complete and symmetric")
        # Every retained party source must belong to the declared party and official domain.
        for src in catalogue.values():
            if src["kind"] == "party" and src["party_id"] == key:
                require(domain is not None and domain_match(host(src["url"]), domain)
                        and src["publisher"] == name, "party source owner/domain mismatch")
    unique(party_ids, "parties")
    require(set(party_ids) == set(represented), "Commons party coverage incomplete")
    require(ordering == sorted(ordering), "parties must be alphabetical")

    recorded_non_party = {}
    for member in data["non_party_members"]:
        fields(member, "parliament_id name classification mp_count", "non-party group")
        member_id = text(member["parliament_id"], "non-party Parliament id", 100)
        require(member_id not in recorded_non_party, "duplicate non-party group")
        recorded_non_party[member_id] = {"name": member["name"], "classification": member["classification"],
                                         "count": integer(member["mp_count"], "non-party count", 1)}
    require(recorded_non_party == non_party, "independent/Speaker coverage differs from Parliament")
    require([m["parliament_id"] for m in data["non_party_members"]] == sorted(non_party),
            "non-party members must be ordered by Parliament id")
    require(used == set(catalogue), "unused or unreferenced source evidence")

    ready = external_reviews(factory_reviews, binding) if factory_reviews else False
    covered = all(p["coverage"] == "recorded" for p in data["parties"])
    require(not require_coverage or covered, "party acceptance blocked: proposal coverage incomplete")
    require(not require_reviews or ready, "party publication blocked: independent reviews pending")
    return {"status": "candidate", "public_accepted": False, "proposal_coverage_complete": covered,
            "review_bindings_complete": ready, "candidate_sha256": candidate_digest(data, manifest),
            "party_count": len(party_ids), "mp_count": sum(p["count"] for p in
                                                               [*represented.values(), *non_party.values()])}


def external_reviews(receipts, binding):
    """Consume real factory verdict JSON, supplied by the trusted controller.

    The controller establishes reviewer independence, receipt authenticity and the
    exact Git base/candidate/tree. This parser cannot certify those facts itself.
    No receipt names, consent, reviewer identities or approvals are put in data.
    """
    require(binding is not None, "external verdicts need exact Git binding")
    fields(binding, "base_sha candidate_sha tree", "factory binding")
    require(all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{40}", v) for v in binding.values()),
            "invalid factory Git binding")
    fields(receipts, "fiscal editorial", "external factory reviews")
    for receipt in receipts.values():
        fields(receipt, "base_sha candidate_sha tree findings", "factory verdict")
        require(all(receipt[k] == v for k, v in binding.items()), "factory verdict exact candidate mismatch")
        for finding in sequence(receipt["findings"], "factory findings"):
            fields(finding, "severity file line issue", "factory finding")
            require(finding["severity"] in ("blocking", "advisory"), "invalid factory severity")
            text(finding["file"], "finding file")
            integer(finding["line"], "finding line", 1)
            text(finding["issue"], "finding issue", 20000)
            require(finding["severity"] != "blocking", "factory verdict has blocking findings")
    return True


def validate_files(candidate=None, manifest=None, *, as_of=None, require_reviews=False,
                   require_coverage=False, factory_reviews=None, binding=None):
    def document(path):
        target = Path(path)
        require(not any(p.is_symlink() for p in (target.absolute(), *target.absolute().parents)),
                "party input contains symlink")
        return load_json(target.read_bytes())
    return validate(document(candidate or ROOT / "data/parties.json"),
                    document(manifest or ROOT / "data/party-sources.json"),
                    as_of=as_of, require_reviews=require_reviews, require_coverage=require_coverage,
                    factory_reviews=factory_reviews, binding=binding)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--as-of", help="UTC check date, YYYY-MM-DD; default today")
    parser.add_argument("--require-reviews", action="store_true")
    parser.add_argument("--require-coverage", action="store_true")
    parser.add_argument("--fiscal-verdict", type=Path)
    parser.add_argument("--editorial-verdict", type=Path)
    for name in ("base-sha", "candidate-sha", "tree"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    try:
        receipts = None
        if args.fiscal_verdict or args.editorial_verdict:
            require(args.fiscal_verdict and args.editorial_verdict, "both external verdicts required")
            require(args.fiscal_verdict.resolve() != args.editorial_verdict.resolve(),
                    "separate external reviews required")
            receipts = {"fiscal": load_json(args.fiscal_verdict.read_bytes()),
                        "editorial": load_json(args.editorial_verdict.read_bytes())}
        report = validate_files(args.candidate, args.manifest,
                                as_of=day(args.as_of, "check date") if args.as_of else None,
                                require_reviews=args.require_reviews, require_coverage=args.require_coverage,
                                factory_reviews=receipts,
                                binding={"base_sha": args.base_sha, "candidate_sha": args.candidate_sha,
                                         "tree": args.tree} if receipts else None)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        parser.exit(1, f"Party data refused: {error}\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
