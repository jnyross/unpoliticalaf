"""Check source cells, reconciliations and exact deterministic public output."""
from build import PUBLIC_FILES, ROOT, payloads, validate_output
from build_data import build_data
from build_receipts import build_receipts, encode as encode_receipts
from check_receipts import validate as validate_receipts
from check_site import validate, independent_payer_checks, independent_basics_checks
from check_audit import validate as validate_audit
from check_receipt_audit import validate as validate_receipt_audit
from check_payer_sources import validate as validate_payer_sources
from check_schools import validate as validate_schools
from check_holiday_methods import validate as validate_holiday_methods
from check_work_methods import validate as validate_work_methods
from check_work_data import validate as validate_work_data
from life_projection import project as project_life, encode as encode_life
from check_life import validate as validate_life


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


def verify_life_generated(root=ROOT):
    """Compare real retained/generated life bytes with two fresh projections."""
    first = encode_life(project_life(root))
    if first != encode_life(project_life(root)):
        raise AssertionError("Life regeneration is not deterministic")
    for relative in ("data/life.json", "site/data/life.json"):
        path = root / relative
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
            raise ValueError("Life publication must contain regular files")
    if (root / "data/life.json").read_bytes() != first:
        raise AssertionError("Generated life data is stale or changed; run make build")
    if (root / "site/data/life.json").read_bytes() != first:
        raise AssertionError("Published life data is stale or changed; run make build")


def main():
    validate_audit()
    validate_receipt_audit()
    validate_payer_sources()
    validate_schools()
    validate_holiday_methods()
    validate_work_methods()
    validate_work_data()
    verify_life_generated(ROOT)
    validate_life(ROOT)
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
