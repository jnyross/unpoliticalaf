# Exact ODF text repair

Original source candidate17d5f6f failed an independent credential-free Boat check
at HMRC `Contents!A3`. The official ODS was intact. The readable CSV used a text
extraction that omitted explicit ODF spaces, tabs and paragraph separators.

The correction regenerates HMRC displayed text with all `text:s` counts,
`text:tab`, `text:line-break` and paragraph boundaries preserved. It changes
206 selected text cells, including footnote prose and spaces before percent
signs. It does not change a numeric source, source file, source hash, ONS CSV,
semantic classification, population, period or status. The independent checker remains strict. It must compare every selected
audit cell to the raw source. The CSV field `published_text_json` stores each
complete string as ASCII JSON. This preserves trailing spaces and paragraph
boundaries without literal trailing whitespace in the repository. The checker
only adds JSON decoding before its unchanged exact text equality comparison. A rehashed CSV with stripped spaces must fail.

The predecessor failure, source snapshots, claim, session and receipts stay
preserved. No renderer or fiscal interpretation is approved by this repair.
The exact combined successor still needs independent review and full Boat and
live-byte checks. No test result is claimed by this document.
