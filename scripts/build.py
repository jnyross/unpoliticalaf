#!/usr/bin/env python3
"""Build the spending product from retained data, publishing an explicit allowlist."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from build_data import build_data
import build_site

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = frozenset({"index.html", "methods.html", "icon.svg", "data/spending.json"})
# A previous baseline can be replaced, but no other files may be deleted.
LEGACY_FILES = frozenset({"styles.css"})


def validate_output(output):
    output = Path(output).absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("output path must not contain symlinks")
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError("output must not overlap project sources")
    if ROOT in output.parents and output != ROOT / "site":
        raise ValueError("inside the project, output must be site/")
    if output.exists():
        if not output.is_dir():
            raise ValueError("output must be a directory")
        for path in output.rglob("*"):
            name = path.relative_to(output).as_posix()
            if path.is_symlink():
                raise ValueError("output must not contain symlinks")
            if path.is_dir() and name == "data":
                continue
            if not path.is_file() or name not in PUBLIC_FILES | LEGACY_FILES:
                raise ValueError(f"output contains unexpected file: {name}")
    return output


def regular_input(path):
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError(f"input must be a regular file: {path}")
    return path.read_bytes()


def payloads(data):
    corrections = json.loads(regular_input(ROOT / "data/corrections.json"))
    build_site.configure(data, corrections)
    encoded = (json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return {
        "index.html": build_site.index().encode("utf-8"),
        "methods.html": build_site.methods().encode("utf-8"),
        "icon.svg": regular_input(ROOT / "assets/icon.svg"),
        "data/spending.json": encoded,
    }


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def build(output, *, write_data=True):
    output = validate_output(output)
    data_path = ROOT / "data/spending.json"
    if write_data and (data_path.is_symlink() or (data_path.exists() and not data_path.is_file())):
        raise ValueError("data/spending.json must be a regular file")
    if (ROOT / "data").is_symlink():
        raise ValueError("data directory must not be a symlink")
    # All source validation and rendering finishes before any public file changes.
    data = build_data()
    public = payloads(data)
    if set(public) != PUBLIC_FILES:
        raise ValueError("unexpected public payload")
    for name in ("index.html", "methods.html"):
        if len(public[name]) >= 500_000:
            raise ValueError(f"{name}: over the HTML size limit")
    validate_output(output)
    if write_data:
        atomic_write(data_path, public["data/spending.json"])
    for name, content in public.items():
        atomic_write(output / name, content)
    for name in LEGACY_FILES:
        (output / name).unlink(missing_ok=True)
    print(f"Built {len(public)} public files in {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    try:
        build(args.output)
    except (ValueError, OSError, AssertionError, KeyError, TypeError) as error:
        parser.exit(1, f"Build refused: {error}\n")


if __name__ == "__main__":
    main()
