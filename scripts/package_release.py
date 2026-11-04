"""Package a checked site without timestamps, local files or changed content.

Run after make verify. The caller supplies the exact commit that passed the
live-site workflow; build.json must name it and account for every site file.
"""
import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def package(site, output, commit):
    site, output = Path(site).resolve(), Path(output).resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Release commit must be a full Git SHA")
    if output == site or site in output.parents:
        raise ValueError("Release output must be outside the site directory")
    record_bytes = (site / "build.json").read_bytes()
    record = json.loads(record_bytes)
    if record.get("commit") != commit:
        raise ValueError("Build commit does not match the verified commit")
    files = record.get("files")
    if not isinstance(files, dict) or not files or "build.json" in files:
        raise ValueError("Build record must list the site files, excluding itself")
    actual = set()
    for path in site.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not release files: {path}")
        if path.is_file():
            actual.add(path.relative_to(site).as_posix())
    if actual != set(files) | {"build.json"}:
        raise ValueError("Site files differ from the build record")
    # Read and validate everything before creating an artifact. Use the same
    # bytes for hashing and packaging so no changed file can slip into the tar.
    bodies = {"build.json": record_bytes}
    for name, expected in sorted(files.items()):
        body = (site / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError(f"Site file does not match its build hash: {name}")
        bodies[name] = body

    output.mkdir(parents=True, exist_ok=True)
    archive = output / "site.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for name, body in sorted(bodies.items()):
                    info = tarfile.TarInfo(name)
                    info.size = len(body)
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(body))
    (output / "build.json").write_bytes(record_bytes)
    sums = []
    for name in ("site.tar.gz", "build.json"):
        digest = hashlib.sha256((output / name).read_bytes()).hexdigest()
        sums.append(f"{digest}  {name}\n")
    (output / "SHA256SUMS").write_text("".join(sums), encoding="utf-8")
    return archive


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args(argv)
    try:
        archive = package(args.site, args.output, args.commit)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Release packaging failed: {error}\n")
    print(f"Packaged {args.commit} into {archive}")


if __name__ == "__main__":
    main()
