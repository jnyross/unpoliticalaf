# Readable source-cell evidence

These CSV files are researcher extracts from the retained original HMRC Table2.4
ODS and ONS workbook. They let read-only reviewers inspect exact labels, notes
and selected published values. They are not independent truth or an accepted
product dataset. The implementation must reopen the original source files,
verify original/stored hashes and compare every retained audit row with its
source. Do not use a rehashed or edited CSV as proof that a source agrees.

`published_text_json` in the HMRC extract is an ASCII JSON string. Parse the CSV,
then JSON-decode that field to recover the exact ODS displayed text, including
commas, percentages, explicit spaces, trailing spaces, tabs, line breaks and
paragraph separators. Compare the decoded string exactly; do not strip or
normalize whitespace. This encoding preserves upstream text without literal
trailing whitespace in the repository. ONS `published_value` is the source
cached scalar converted to text, not a replacement raw workbook. Preserve
missing/suppressed values.

`scripts/check_payer_sources.py` checks all 296 HMRC and 497 ONS cells against
the originals. Rehashing a changed CSV in `index.json` does not bypass source
comparison. A successful run is still required through the controller.

Only the two register-listed numeric workbooks appear here. The research-only
collated HMRC taxpayer-count workbook is deliberately excluded. These audit files
stay private and do not belong in `site/` or public data downloads.
