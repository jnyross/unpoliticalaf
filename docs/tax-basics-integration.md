# Tax basics integration

## Scope and result

This change connects the retained qualitative guidance modules to the current tax
and payer pages. It does not add a page, a JSON projection, rates, personal tax
examples or fiscal values. The exact public allowlist remains 8 files.

The homepage asks 4 newcomer questions before the existing spending quick answers.
The onward routes are Spending, How spending changed, Taxes and Who pays. The
existing sourced spending headline, 8 spending questions, charts and tables remain.
All pages retain the shared 4-link primary navigation.

`build_taxes.render()` inserts `build_basics.tax_basics()` immediately before the
receipt groups. Its page link now targets the definition heading. The existing
`Our explanation` label and all 6 technical group explanations stay unchanged.
All 6 component source disclosures remain in the final Check the sources section.

`build_payers.render()` inserts `build_basics.payer_basics()` after all 3 tables
and before the existing burden methodology. The exact existing burden heading,
43 required visible fiscal limits, source links and 23 fiscal identities remain.
The ONS assumptions still distinguish collection from ultimate economic costs.

## API and validation

- `build.payloads()` validates `data/tax-basics` against the explicit build root.
  It renders both complete public pages, then calls `validate_fragments()` on
  their actual HTML before any private or public output write.
- `check_site.independent_basics_checks(site, root=None)` validates the retained
  guidance, regular public HTML files and marked fragments independently of the
  producer. An explicit root never falls back to the module checkout.
- Both `check_site.validate()` and `verify.main()` call this independent gate.
  The latter checks published bytes before deterministic regeneration.
- `build_site.configure()` adds an optional fourth argument, `basics_sources`.
  The normal build supplies the root-validated register. Legacy callers that omit
  it get real guidance validation in `section_basics_methods()`, not an empty
  section or an unchecked default. No payer lifecycle change is made here.
- Methods names the official guidance URLs, precise source headings, original
  response hashes and retained-envelope hashes under a native disclosure. It
  states retrieval on 30 October 2026, no established publication date and no
  known next update. Private source registers and responses are not downloads.

The independent basics module checks only marked fragments. Existing raw fiscal,
forecast-date, reading-grade, neutrality, source-note and reconciliation gates
remain active on the rest of each page. No threshold or expected identity count
is reduced.

The payer checker permits exactly the marked aside heading and its single native
source-limits disclosure. It does not ignore arbitrary aside headings or all
`details`. Every other payer disclosure must remain a named workbook disclosure
in the final source section, after all tables and the full burden section.
The tax checker permits exactly one marked devolved-rules disclosure before the
receipt groups, and the existing marked forecast disclosure in history. Other
source depth remains in the final source section.

## Added acceptance tests

`tests/test_product.py` adds checks for:

- The real published fragments, 4 newcomer routes, source-age methods text and
  unchanged tax/payer fiscal identity counts.
- Changed qualitative meaning and source hrefs through both public-byte entry
  points, `check_site.validate()` and `verify.main()`.
- Rejection of unmarked early disclosures, while preserving marked disclosures.
- Explicit root binding, no foreign-source fallback, and retention of last-good
  private/public files after source or fragment failure.
- HTTP 404s for all 7 guidance responses, their private register and directory,
  module/test paths and evidence/integration notes.

## Handoff and remaining evidence

Only source-file read/write/edit tools were used for this integration. No commands,
Git actions, network requests, builds or tests were run. The reported 11 module
passes on seed `de1188d` are prior evidence supplied by the parent, not checks of
this integrated candidate.

The controller must run the full declared build, verify, unit, smoke and browser
pipeline on the combined candidate. Check reading grade at or below 7, page sizes,
exact 8-file publication, default/expanded axe states at 360px and desktop, native
keyboard disclosure and no-JavaScript content. The existing accessibility checker
already enumerates every disclosure dynamically; no count, size or 44px rule was
changed. A fresh independent fiscal/copy review and the ticket's same-live-product
council review remain required. Human study and formal rubric evidence stay pending.

Sequential merges remain the parent's responsibility:

1. The independent payer UI change owns table sizing, captions and numeric bar
   labels. Here, `build_payers.py` changes only the basics import and insertion.
   `check_payers.py` changes only the heading/disclosure and placement contracts.
2. The payer lifecycle repair owns validated `PAYERS` loading for legacy callers.
   Here, `build_site.py` changes the configure signature/globals for guidance,
   newcomer markup and the new guidance methods section. `tests/test_product.py`
   has additive basics tests. Merge those shared-file changes sequentially.

No generated files, raw sources, source registers, audits, dependencies, factory
configuration, fiscal projections, dedicated tax/payer tests or other worktrees
were changed by this worker.
