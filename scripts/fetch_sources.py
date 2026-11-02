#!/usr/bin/env python3
"""Download the official sources listed in sources/manifest.json, byte for byte.

Each file is saved under data/fetched/ and recorded in data/fetched/receipts.json
with its URL, retrieval time, size and SHA-256 hash. Run where the network can
reach ons.gov.uk, gov.uk and nomisweb.co.uk (the GitHub workflow does this).
"""
import hashlib, json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "fetched"
UA = {"User-Agent": "Mozilla/5.0 (Unpolitical source fetcher; +https://github.com/jnyross/unpoliticalaf)"}


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as e:  # retry transient failures
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main(only=None):
    manifest = json.loads((ROOT / "sources/manifest.json").read_text())
    receipts_path = OUT / "receipts.json"
    receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() else {}
    failures = []
    for s in manifest["sources"]:
        if only and s["id"] not in only:
            continue
        try:
            url = s.get("url")
            if "find" in s:
                page, _ = get(s["page"])
                m = re.search(s["find"], page.decode("utf-8", "replace"))
                if not m:
                    raise ValueError("no link matching " + s["find"])
                url = urllib.parse.urljoin(s["page"], m.group(0).replace("&amp;", "&"))
            body, ctype = get(url)
            name = s["file"]
            if "find" in s:
                name += Path(urllib.parse.urlparse(url).path).suffix or ".bin"
            path = OUT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            receipts[s["id"]] = {"url": url, "file": name, "bytes": len(body), "content_type": ctype,
                                 "sha256": hashlib.sha256(body).hexdigest(),
                                 "retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            print("ok  ", s["id"], len(body), url)
        except Exception as e:
            failures.append(s["id"])
            print("FAIL", s["id"], e)
    OUT.mkdir(parents=True, exist_ok=True)
    receipts_path.write_text(json.dumps(dict(sorted(receipts.items())), indent=1) + "\n")
    print("failures:", failures)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
