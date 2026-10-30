"""Check source cells, reconciliations and exact deterministic public output."""
from build import PUBLIC_FILES, ROOT, payloads, validate_output
from build_data import build_data
from build_receipts import build_receipts, encode as encode_receipts
from check_receipts import validate as validate_receipts
from check_site import validate, independent_payer_checks, independent_basics_checks
from check_audit import validate as validate_audit
from check_receipt_audit import validate as validate_receipt_audit
from check_payer_sources import validate as validate_payer_sources


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


def main():
    validate_audit()
    validate_receipt_audit()
    validate_payer_sources()
    validate_receipts()
    receipt_bytes = (ROOT / "data/receipts.json").read_bytes()
    first_receipts = encode_receipts(build_receipts())
    if first_receipts != encode_receipts(build_receipts()):
        raise AssertionError("Receipt regeneration is not deterministic")
    if receipt_bytes != first_receipts:
        raise AssertionError("Generated receipt data is stale or changed; run make build")
    site = validate_output(ROOT / "site")
    observed = snapshot(site)
    if set(observed) != PUBLIC_FILES:
        raise AssertionError("Build missing or public-file manifest changed; run make build")
    independent_basics_checks(site, root=ROOT)
    independent_payer_checks(site)
    retained = (ROOT / "data/spending.json").read_bytes()
    if retained != observed["data/spending.json"]:
        raise AssertionError("Published and generated spending data differ")
    first = payloads(build_data(), build_receipts())
    second = payloads(build_data(), build_receipts())
    if first != second:
        raise AssertionError("Rebuilding twice produced different output")
    if observed != first:
        raise AssertionError("Generated output is stale or changed; run make build")
    validate(site)
    print("Exact public manifest, source hashes, source cells, reconciliation and reproducibility passed")


if __name__ == "__main__":
    main()
