"""Offline reader for unchanged pinned party assets; inventory is NOT fiscal approval.

Run in credential-free Boat. No fetching, mutation, PDF execution or publication.
The immutable snapshot anchor is intentionally independent of editable inventory
hashes. A refreshed snapshot requires a separately reviewed source increment.
"""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from acquire_party_evidence import readable
from party_data import (ROOT, fields, host, load_json, parliament_parties, require,
                        sequence, text, unique)
from party_source_storage import decode_response

PINNED_REVISION = "7e4fb4b6f476e21f6579ea55b7540dd8aa9fce0c"
PREFIX = "reference/party-sources/2026-10-30/"
SNAPSHOT_SHA256 = "c0f0ef8359610c616fc9b8b0829758303cf85fb279005c2b58faab72e1e81840"
DEFAULT_INVENTORY = ROOT / "data/party-evidence/20261030-inventory/inventory.json"
OBSERVATION_PREFIX = "data/party-evidence/20261030-inventory/"
OBSERVATION_SHA256 = "c6bb497f91ab91ae6ea8c41105aaf4d26b314888666572cc8085f361e20dac01"
CLASSES = {"historical_2024", "devolved_2026", "principles", "rolling_index",
           "dated_2026_publication", "assessment_2024", "assessment_index", "remit"}
DOCUMENT_FIELDS = ("source_id party_id url retrieved_at raw_path raw_sha256 raw_bytes "
                   "text_sha256 text_method extraction_tool classification scope "
                   "published_on publication_locator evidence limitations")
PARTY_FIELDS = "id name current_status documents missing"
# All remain unresolved in this bounded inventory, including for parties with
# historical examples. Source presence is never comprehensive current coverage.
MISSING = ["complete_current_westminster_inventory", "current_status_verification",
           "complete_proposal_extraction", "cost_funding_year_baseline_verification",
           "independent_fiscal_review", "independent_editorial_review"]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def local_read(path):
    prefix = next((p for p in (PREFIX, OBSERVATION_PREFIX) if path.startswith(p)), None)
    require(prefix is not None and re.fullmatch(r"[A-Za-z0-9_.-]+", path[len(prefix):]),
            "asset outside reviewed party evidence families")
    target = ROOT / path
    require(not any(p.is_symlink() for p in (target, *target.parents)), "asset contains symlink")
    return target.read_bytes()


class PinnedReader:
    def __init__(self, read=local_read):
        self.read = read
        raw = read(PREFIX + "SNAPSHOT.json")
        require(digest(raw) == SNAPSHOT_SHA256, "pinned snapshot anchor changed")
        snapshot = load_json(raw)
        self.entries = {}
        for entry in sequence(snapshot["files"], "pinned files"):
            fields(entry, "path bytes sha256", "pinned file")
            name = entry["path"]
            require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", name),
                    "unsafe pinned filename")
            require(name not in self.entries, "duplicate pinned filename")
            require(type(entry["bytes"]) is int and entry["bytes"] >= 0,
                    "invalid pinned byte count")
            require(isinstance(entry["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]),
                    "invalid pinned hash")
            self.entries[name] = entry
        self.retrievals = load_json(self.asset("retrievals.json"))
        self.extraction = load_json(self.asset("EXTRACTION.json"))
        self.extractions = {row["input"]: row for row in self.extraction["records"]}
        require(len(self.extractions) == len(self.extraction["records"]), "duplicate PDF extraction")
        seeds = load_json(self.asset("source-seeds.json")) + load_json(self.asset("additional-sources.json"))
        self.seeds = {row["id"]: row for row in seeds}
        observed = read(OBSERVATION_PREFIX + "observation.json")
        require(digest(observed) == OBSERVATION_SHA256, "observation anchor changed")
        self.observation = load_json(observed)

    def asset(self, name):
        require(name in self.entries, "asset absent from pinned snapshot")
        raw = self.read(PREFIX + name)
        entry = self.entries[name]
        require(type(raw) is bytes and len(raw) == entry["bytes"] and digest(raw) == entry["sha256"],
                "pinned asset bytes/hash changed: " + name)
        return raw

    def verify_all(self):
        for name in self.entries:
            self.asset(name)
        return len(self.entries)

    def source(self, key):
        if key == "yourparty-explainer-observed":
            return self.observed_source()
        rows = [row for row in self.retrievals if row.get("id") == key and row.get("status") == 200]
        require(rows, "no complete retained HTTP response for source: " + str(key))
        identities = {(r.get("path"), r.get("sha256"), r.get("url")) for r in rows}
        require(len(identities) == 1, "ambiguous source retrieval")
        row = rows[-1]
        raw = self.asset(row["path"])
        require(digest(raw) == row["sha256"], "retrieval/pinned hash mismatch")
        require(row.get("bytes", len(raw)) == len(raw), "retrieval byte count mismatch")
        host(row["url"])
        require(row.get("final_url", row["url"]) == row["url"], "unresolved redirected source origin")
        stamp = datetime.fromisoformat(row["retrieved_at"])
        require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0,
                "source retrieval must be UTC")
        tool = None
        if row["path"].endswith(".pdf"):
            require(raw.startswith(b"%PDF-"), "source is not a PDF")
            require(row["path"] in self.extractions, "PDF has no retained extraction")
            extraction = self.extractions[row["path"]]
            require(extraction["exit_code"] == 0 and extraction["source_sha256"] == digest(raw),
                    "PDF extraction input mismatch")
            content = self.asset(extraction["output"])
            require(digest(content) == extraction["output_sha256"] and len(content) == extraction["bytes"],
                    "PDF extraction output mismatch")
            method, tool = "retained_pdftotext_layout", self.extraction["tool"]
        elif row["path"].endswith(".html"):
            content, method = readable(raw, "party").encode("utf-8"), "complete_html_readable_v1"
        elif row["path"].endswith(".txt"):
            # Honour a real BOM; do not mistake a lone 0xff for a BOM. Some
            # retained official text has no verifiable encoding. Latin-1 below
            # is a reversible byte view, explicitly NOT a text-encoding claim.
            if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                content, method = raw.decode("utf-16").encode("utf-8"), "official_plain_text_utf16_bom"
            else:
                try:
                    raw.decode("utf-8")
                    content, method = raw, "official_plain_text_utf8"
                except UnicodeDecodeError:
                    content = raw.decode("latin-1").encode("utf-8")
                    method = "latin1_byte_view_encoding_unverified"
        else:
            raise ValueError("source reader requires PDF, HTML or official text")
        party = row.get("party_id", self.seeds.get(key, {}).get("party_id"))
        info = {"source_id": key, "party_id": str(party) if party is not None else None,
                "url": row["url"], "retrieved_at": row["retrieved_at"],
                "raw_path": PREFIX + row["path"], "raw_sha256": digest(raw), "raw_bytes": len(raw),
                "text_sha256": digest(content), "text_method": method, "extraction_tool": tool}
        return info, content.decode("utf-8"), raw

    def observed_source(self):
        rows = self.observation["sources"]
        require(len(rows) == 1, "unexpected observed sources")
        row = rows[0]
        require(row["raw_path"] == "yourparty-explainer-observed-response.json"
                and row["source_id"] == "yourparty-explainer-observed" and row["party_id"] == "1115"
                and row["status"] == 200 and row["retained"] is True
                and row["content_type"] == "text/html"
                and row["url"] == row["final_url"] == "https://www.yourparty.uk/political-statement-explainer/",
                "observed source identity mismatch")
        raw = decode_response(self.read(OBSERVATION_PREFIX + row["raw_path"]))
        require(digest(raw) == row["sha256"] and len(raw) == row["bytes"], "observed original response changed")
        content = readable(raw, "party").encode("utf-8")
        return {"source_id": row["source_id"], "party_id": row["party_id"], "url": row["url"],
                "retrieved_at": row["retrieved_at"], "raw_path": OBSERVATION_PREFIX + row["raw_path"],
                "raw_sha256": digest(raw), "raw_bytes": len(raw), "text_sha256": digest(content),
                "text_method": "complete_html_readable_v1", "extraction_tool": None}, content.decode("utf-8"), raw


def locator(content, start, end):
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(content),
            "invalid source offsets")
    return {"start": start, "end": end, "pdf_page": content[:start].count("\f") + 1 if "\f" in content else None,
            "quote": content[start:end]}


def validate_inventory(inventory, reader=None, *, as_of=None, require_current=False):
    reader = reader or PinnedReader()
    today = as_of or datetime.now(timezone.utc).date()
    fields(inventory, "schema_version pinned_revision pinned_snapshot_sha256 as_of roster_source_id documents parties limitations",
           "source inventory")
    require(type(inventory["schema_version"]) is int and inventory["schema_version"] == 1,
            "unknown inventory schema")
    require(inventory["pinned_revision"] == PINNED_REVISION and
            inventory["pinned_snapshot_sha256"] == SNAPSHOT_SHA256, "inventory pin mismatch")
    require(inventory["as_of"] == "2026-10-30" and inventory["roster_source_id"] == "commons-state-2026-10-30",
            "inventory must match pinned dated roster")
    snapshot_date = date.fromisoformat(inventory["as_of"])
    require(snapshot_date <= today and (today - snapshot_date).days <= 30, "stale/future inventory roster")
    roster = load_json(reader.asset("commons-state-2026-10-30.json"))
    # Reuse the real roster's house/date, duplicate and subgroup reconciliation.
    represented, _ = parliament_parties(["roster"], {"roster": {
        "kind": "roster", "snapshot_as_of": inventory["as_of"],
        "url": "https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2026-10-30"}},
        {"roster": json.dumps(roster)}, inventory["as_of"])
    documents = {}
    for document in sequence(inventory["documents"], "inventory documents"):
        fields(document, DOCUMENT_FIELDS, "inventory document")
        require(list(document) == DOCUMENT_FIELDS.split(), "inventory document field order differs")
        key = text(document["source_id"], "inventory source id", 100)
        require(key not in documents, "duplicate inventory source")
        info, content, raw = reader.source(key)
        require(all(document[k] == v for k, v in info.items()), "inventory/source provenance mismatch")
        retrieved = datetime.fromisoformat(info["retrieved_at"]).date()
        require(retrieved <= today and (today - retrieved).days <= 90, "stale/future inventory source")
        require(document["classification"] in CLASSES, "invalid inventory classification")
        for name in ("scope", "limitations"):
            text(document[name], name, 400)
        published, date_locator = document["published_on"], document["publication_locator"]
        if published is None:
            require(date_locator is None, "missing publication date must stay explicit")
        else:
            require(isinstance(published, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", published)
                    and date.fromisoformat(published) <= retrieved, "invalid inventory publication date")
            text(date_locator, "publication locator", 200)
            require(date_locator in raw.decode("utf-8"), "publication locator absent from original")
            match = re.search(r"\d{4}-\d{2}-\d{2}", date_locator)
            located = match.group() if match else datetime.strptime(date_locator, "%B %d, %Y").date().isoformat()
            require(located == published, "publication date/locator mismatch")
        ref = document["evidence"]
        fields(ref, "start end pdf_page quote", "inventory locator")
        text(ref["quote"], "inventory quote", 1000)
        require((ref["pdf_page"] is None or type(ref["pdf_page"]) is int) and
                ref == locator(content, ref["start"], ref["end"]), "source quotation/page locator mismatch")
        documents[key] = document
    require(list(documents) == sorted(documents), "inventory sources must be alphabetical")
    parties, used = [], set()
    for party in sequence(inventory["parties"], "inventory parties"):
        fields(party, PARTY_FIELDS, "inventory party")
        require(list(party) == PARTY_FIELDS.split(), "inventory party field order differs")
        key = party["id"]
        require(key in represented and party["name"] == represented[key]["name"], "unrepresented inventory party")
        parties.append(key)
        require(party["current_status"] == "not_verified", "this inventory cannot assert current coverage")
        require(party["missing"] == MISSING, "unverified acceptance fields cannot be cleared")
        ids = sequence(party["documents"], "party document ids")
        unique(ids, "party documents")
        require(ids == sorted(ids) and ids, "each party needs ordered retained source candidates")
        for source_id in ids:
            require(source_id in documents and documents[source_id]["party_id"] == key,
                    "inventory document belongs to another party")
            used.add(source_id)
    unique(parties, "inventory parties")
    require(set(parties) == set(represented), "inventory Commons party coverage incomplete")
    require(parties == sorted(parties, key=lambda k: (represented[k]["name"].casefold(), k)),
            "inventory parties must be alphabetical")
    require(all(d["party_id"] is None or k in used for k, d in documents.items()),
            "unreferenced inventory party source")
    for value in sequence(inventory["limitations"], "inventory limitations"):
        text(value, "inventory limitation", 400)
    require(inventory["limitations"], "inventory limitations required")
    require(not require_current, "current-plan acceptance blocked: all 15 current inventories remain incomplete")
    return {"party_count": len(parties), "source_count": len(documents),
            "current_coverage_complete": False, "public_accepted": False,
            "missing_current_parties": [represented[k]["name"] for k in parties],
            "pinned_snapshot_sha256": SNAPSHOT_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--as-of", type=date.fromisoformat)
    parser.add_argument("--require-current-coverage", action="store_true")
    parser.add_argument("--source", help="Retained source id; prints provenance then full text")
    parser.add_argument("--page", type=int, help="Physical PDF page, starting at 1; not printed page label")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    try:
        reader = PinnedReader()
        reader.verify_all()
        inventory = load_json(args.inventory.read_bytes())
        report = validate_inventory(inventory, reader, as_of=args.as_of,
                                    require_current=args.require_current_coverage)
        if args.source:
            require(args.source in {d["source_id"] for d in inventory["documents"]}, "source absent from inventory")
            info, content, _ = reader.source(args.source)
            if args.page is not None:
                require(info["text_method"] == "retained_pdftotext_layout", "page selection requires PDF")
                pages = content.split("\f")
                if pages[-1] == "":
                    pages.pop()
                require(1 <= args.page <= len(pages), "PDF page outside source")
                start = sum(len(page) + 1 for page in pages[:args.page - 1])
                selected = locator(content, start, start + len(pages[args.page - 1]))
            elif args.start is not None or args.end is not None:
                selected = locator(content, args.start, args.end)
            else:
                selected = {"start": 0, "end": len(content), "quote": content}
            print(json.dumps({"provenance": info, "locator": selected}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        parser.exit(1, f"Party source audit refused: {error}\n")


if __name__ == "__main__":
    main()
