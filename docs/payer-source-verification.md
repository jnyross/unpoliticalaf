# Payer source verification

This change prepares private source evidence only. It adds no public page,
figure, renderer, downloadable dataset or public file allowance. The existing
source register and seven official responses retain their exact bytes. The
successor repairs HMRC audit text and its JSON string representation, as
recorded in `payer-source-spacing-repair.md`; ONS audit values are unchanged.
The methods, corrections and audit README distinguish retained evidence from
absent research-only material. The tax renderer's separate publication hold remains.

## Verification contract

`scripts/check_payer_sources.py` pins the exact retained `sources.json` hash.
It checks the length and SHA-256 of all seven original responses. For each
HTML response it separately checks the stored ASCII JSON envelope and the
complete UTF-8 body recovered from `original_response`, without trimming.
Release/retrieval dates and source status remain those in the retained register;
the checker adds no inferred guidance date.

The checker independently reopens the ODS and XLSX, without importing an
extractor or fiscal transformation. A fixed selection requires all 296 HMRC
and 497 ONS audit rows, including headings, labels, years and notes. ODS values
are displayed text: paragraphs use newline separators, explicit ODF spaces,
tabs and line breaks are preserved, and repeated row/column spans are visited
without expanding them into a whole grid. ONS values are cached scalars
converted to text, without evaluating formulas. Blanks remain empty text;
suppression markers remain literal text. No missing value becomes zero.

The audit index records CSV hashes for accidental corruption. It is not source
truth: changing a CSV and rehashing the index still requires every value and
cell identity to agree with the unchanged official workbook. This also protects
note 13's expenditure definition and the separate published Table 8 totals.
The broader interpretation limits and corrected citations remain in
`payer-source-seed.md`, `payer-source-methods.md` and
`payer-source-corrections.md`.

## Controller checks still required

The declared `make verify` calls the source checker and discovers
`tests/test_payer_sources.py`. The tests include altered workbook bytes,
changed HTML body/envelope, recovered-body corruption despite an updated
envelope hash, rehashed numeric/note errors, wrong or missing cell identity,
ODS repeats/whitespace, and blanks/suppression. Existing public manifest and
deterministic byte checks are unchanged; tests also require private source,
audit and documentation paths to be rejected by the public output validator.

These checks were authored and independently reviewed statically in the bounded
file-editing role. No program or test was executed here. The text-only tool
cannot decode binary workbooks, so exact ODS whitespace compatibility and all
793 source comparisons remain pending controller execution. The corruption
suite includes a rehashed HMRC CSV with stripped ODF spaces; that must fail
at `Contents!A3`. The predecessor failed there before this whitespace repair;
its failure and session remain preserved. A comparison
failure must be investigated against the original; do not normalize away a
mismatch or silently accept a second text representation.

The controller must perform its unchanged setup/build/verify/smoke, independent
exact-candidate review, unchanged-public-byte comparison, and canonical live
artifact checks for exactly `index.html`, `methods.html`, `icon.svg` and
`data/spending.json`. Source-check success would establish evidence fidelity only.
It does not accept fiscal interpretation, a future renderer, human studies,
the formal source rubric, the overall 9.5/10 goal or publication.
