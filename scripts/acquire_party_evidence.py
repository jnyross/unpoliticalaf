"""Bounded public HTTP acquisition. Run only in the controller's credential-free Boat.

Never updates the accepted dataset. A new directory contains complete response bytes,
deterministic readable text and observed acquisition outcomes, including failures.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from party_source_storage import encode_response


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(" ".join(data.split()))


def readable(raw, kind):
    if kind == "roster":
        return raw.decode("utf-8")
    parser = ReadableHTML()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    return "\n".join(parser.parts) + "\n"


def entries(roster_date):
    return [
        ("commons", "roster", "UK Parliament", None,
         f"https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/{roster_date}",
         None, None),
        ("labour-fiscal-2024", "party", "Labour", "15",
         "https://labour.org.uk/change/labours-fiscal-plan/", "2024-06-13", '"datePublished":"2024-06-13'),
        ("snp-speech-2024", "party", "Scottish National Party", "29",
         "https://www.snp.org/snp-leader-john-swinneys-2024-manifesto-speech/", "2024-06-19", "19 June, 2024"),
        ("yourparty-statement", "party", "Your Party", "1115",
         "https://www.yourparty.uk/political-statement/", "2025-11-25", '"datePublished":"2025-11-25'),
        ("resolution-comparison-2024", "assessment", "Resolution Foundation", None,
         "https://www.resolutionfoundation.org/publications/the-economic-battle-lines-of-the-general-election/",
         "2024-06-14", "14 June 2024"),
    ]


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if (new.scheme != "https" or new.hostname != old.hostname or new.username
                or new.password or new.port not in (None, 443)):
            raise ValueError("redirect leaves the requested official HTTPS origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    request = Request(url, headers={"User-Agent": "UnpoliticalAF-source-check/1.0"})
    with build_opener(OfficialRedirects()).open(request, timeout=40) as response:
        raw = response.read(750_001)
        if len(raw) > 750_000:
            raise ValueError("response exceeds bounded acquisition size; no partial snapshot retained")
        return raw, response.status, response.url, response.headers.get_content_type()


def acquire(output, roster_date, fetcher=fetch):
    """No overwrite or silent fallback; failed refresh leaves the previous directory intact."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", roster_date):
        raise ValueError("invalid roster date")
    from datetime import date
    if date.fromisoformat(roster_date) > datetime.now(timezone.utc).date():
        raise ValueError("future roster date")
    output = Path(output).absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("output contains symlink")
    output.mkdir(parents=True, exist_ok=False)
    sources, outcomes, retained = [], [], 0
    for key, kind, publisher, party_id, url, published, locator in entries(roster_date):
        outcome = {"id": key, "url": url, "attempted_at": timestamp()}
        try:
            raw, status, final, content_type = fetcher(url)
            outcome.update(http_status=status, final_url=final, retrieved_at=timestamp(),
                           response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest())
            if status != 200 or final != url:
                raise ValueError("unexpected HTTP status or final URL")
            if content_type != ("application/json" if kind == "roster" else "text/html"):
                raise ValueError("unexpected official response content type")
            if locator is not None and locator not in raw.decode("utf-8"):
                raise ValueError("publication date locator absent from response")
            text = readable(raw, kind).encode("utf-8")
            stored = encode_response(raw)
            if retained + max(len(raw), len(stored)) + len(text) > 750_000:
                raise ValueError("complete raw/text evidence exceeds acquisition budget; source not retained")
            raw_path, path = output / (key + "-response.json"), output / (key + ".txt")
            raw_path.write_bytes(stored)
            path.write_bytes(text)
            retained += max(len(raw), len(stored)) + len(text)
            sources.append({"id": key, "kind": kind, "publisher": publisher, "party_id": party_id,
                            "url": url, "published_on": published, "publication_locator": locator,
                            "retrieved_at": outcome["retrieved_at"],
                            "snapshot_as_of": roster_date if kind == "roster" else None,
                            "path": path.name, "sha256": hashlib.sha256(text).hexdigest(),
                            "raw_path": raw_path.name, "raw_sha256": outcome["response_sha256"]})
            outcome["retained"] = True
        except (OSError, ValueError, UnicodeError) as error:
            outcome.update(retained=False, error=str(error), completed_at=timestamp())
            if isinstance(error, HTTPError):
                outcome["http_status"] = error.code
        outcomes.append(outcome)
    (output / "acquisition.json").write_text(json.dumps({"sources": sources, "outcomes": outcomes},
                                                       ensure_ascii=False, indent=2) + "\n")
    return all(row["retained"] for row in outcomes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roster-date", default=datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args()
    try:
        complete = acquire(args.output, args.roster_date)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Acquisition refused: {error}\n")
    if not complete:
        parser.exit(1, "Acquisition incomplete; see acquisition.json; previous evidence unchanged\n")
    print("Bounded acquisition retained; this is not complete party-plan coverage or review")


if __name__ == "__main__":
    main()
