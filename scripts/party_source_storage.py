"""Lossless, uncompressed HTTP response bytes in reviewable ASCII JSON.

Latin-1 maps each byte to the same-valued Unicode code point. JSON escapes all
control/non-ASCII characters, including original CR/LF and trailing whitespace.
Joining lines and encoding Latin-1 reconstructs every response byte exactly.
"""
import argparse
import hashlib
import json
from pathlib import Path

FORMAT = "http-response-latin1-lines-v1"


def encode_response(raw):
    if not isinstance(raw, bytes):
        raise ValueError("original response must be bytes")
    document = {"format": FORMAT, "byte_length": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "lines": raw.decode("latin-1").splitlines(keepends=True)}
    return (json.dumps(document, ensure_ascii=True, indent=2) + "\n").encode("ascii")


def decode_response(stored):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate response container field")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("non-finite response container value")

    try:
        document = json.loads(stored, object_pairs_hook=pairs, parse_constant=constant)
        if (not isinstance(document, dict)
                or set(document) != {"format", "byte_length", "sha256", "lines"}
                or document["format"] != FORMAT
                or type(document["byte_length"]) is not int or document["byte_length"] < 0
                or not isinstance(document["lines"], list)
                or not all(isinstance(line, str) for line in document["lines"])):
            raise ValueError("invalid response container schema")
        raw = "".join(document["lines"]).encode("latin-1")
        if (len(raw) != document["byte_length"]
                or hashlib.sha256(raw).hexdigest() != document["sha256"]):
            raise ValueError("changed original response hash or byte length")
        if encode_response(raw) != stored:
            raise ValueError("noncanonical response container")
        return raw
    except (TypeError, UnicodeError) as error:
        raise ValueError("invalid response container encoding") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("container", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sha256", required=True, help="Original response hash from the source manifest")
    args = parser.parse_args()
    try:
        raw = decode_response(args.container.read_bytes())
        if hashlib.sha256(raw).hexdigest() != args.sha256:
            raise ValueError("response differs from manifest hash")
        # Exclusive creation: independent inspection must not overwrite evidence.
        with args.output.open("xb") as output:
            output.write(raw)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Response decoding refused: {error}\n")


if __name__ == "__main__":
    main()
