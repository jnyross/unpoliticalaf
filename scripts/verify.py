"""Check source cells, reconciliations and exact deterministic public output."""
from build import PUBLIC_FILES, ROOT, payloads, validate_output
from build_data import build_data
from check_site import validate
from check_audit import validate as validate_audit
from check_receipt_audit import validate as validate_receipt_audit


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


def main():
    validate_audit()
    validate_receipt_audit()
    site = validate_output(ROOT / "site")
    observed = snapshot(site)
    if set(observed) != PUBLIC_FILES:
        raise AssertionError("Build missing or public-file manifest changed; run make build")
    retained = (ROOT / "data/spending.json").read_bytes()
    if retained != observed["data/spending.json"]:
        raise AssertionError("Published and generated spending data differ")
    first = payloads(build_data())
    second = payloads(build_data())
    if first != second:
        raise AssertionError("Rebuilding twice produced different output")
    if observed != first:
        raise AssertionError("Generated output is stale or changed; run make build")
    validate(site)
    print("Exact public manifest, source hashes, source cells, reconciliation and reproducibility passed")


if __name__ == "__main__":
    main()
