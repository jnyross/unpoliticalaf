#!/usr/bin/env python3
"""Copy only the explicit public inputs; never publish the project directory."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = ("index.html", "styles.css")


def build(output: Path) -> None:
    output = output.absolute()
    # Reject symlinks before resolving so a link cannot redirect publication.
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("output path must not contain symlinks")
    output = output.resolve()
    source = ROOT / "static"
    if output == ROOT or output in ROOT.parents or output == source or source in output.parents:
        raise ValueError("output must not overlap project or static sources")
    # Inside the repository, site/ is the sole generated-output location.
    if ROOT in output.parents and output != ROOT / "site":
        raise ValueError("inside the project, output must be site/")
    if output.exists():
        if not output.is_dir():
            raise ValueError("output must be a directory")
        if any(p.name not in PUBLIC_FILES or not p.is_file() or p.is_symlink() for p in output.iterdir()):
            raise ValueError("output contains unexpected files; refusing to overwrite")
    payloads = {}
    for name in PUBLIC_FILES:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"public source must be a regular file: {name}")
        payloads[name] = path.read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        (output / name).write_bytes(content)
    print(f"Built {len(payloads)} public files in {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    try:
        build(args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Build refused: {error}\n")


if __name__ == "__main__":
    main()
