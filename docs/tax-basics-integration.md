# Tax basics integration and review repair

## Outcome and publication boundary

This candidate integrates the 7 retained qualitative guidance responses with the
tax and payer product. It adds no current rates, personal tax calculator, fiscal
figure, public page or public JSON dataset. The public manifest remains exactly
8 files. Source registers, raw envelopes, audits, scripts and evidence stay private.

The homepage adds 4 newcomer questions and routes before the existing spending
answers. It retains the sourced spending headline, all 8 spending answers, charts
and tables. All pages retain Spending / Taxes / Who pays / Methods navigation.
The tax definitions precede receipt groups. The collection explanation is an
aside directly after the payer burden heading, after all 3 core tables, before
the ONS allocation explanation. Both marked basics disclosures use native details.
All fiscal denominators, populations, statuses and source limits remain required.

## Actual accumulated candidate changes

The candidate contains more than the original guidance import and insertion:

- `build_payers.py` also uses shorter payer prose for readability. The rewrite
  retains the causes and limits of deferred payments, temporary low income,
  savings/borrowing, sampling, measurement and model assumptions. It adds exact
  `data-payer-limit` contracts and a separately bound suppression warning.
- `check_payers.py` independently binds those visible warnings and their placement.
  It checks all 23 source percentages, table labels, bar widths and values,
  adjacent source links and source-note disclosures. The document-wide unsupported
  claim guard permits the top-group nesting sentence only in its unique checked
  note. It does not exempt arbitrary header/footer claims.
- `payer_projection.py` and `check_payers.py` bind the period and year basis to
  HMRC year labels and ONS Table 8/Cover labels. Selected provenance includes
  HMRC A2 and ONS Cover A5. Note-label cells A8, A9 and A16 are retained alongside
  B8, B9 and B16. Independent checks bind notes 5, 6 and 13 to their exact text
  and Table 8 bracket references. These changes preserve 23 percentages.
- `build_site.configure()` accepts optional validated payer and guidance data.
  Legacy spending-only callers obtain real validated payer data and guidance;
  neither methods section is omitted. Failed validation must not be cached.
- The shared callback preserves the tax controller's complete 4-sentence payer
  limitation and adds an onward link in a separate paragraph. It retains one
  shared OGL footer and the exact 8-file publication boundary.

These are accumulated preparation changes, not a claim that one worker authored
all of them. The obsolete seed-only description is not a current evidence claim.

## Review repair at d5baa129

The native exact review of `d5baa129eb7bc8ef924e2fe631a00b9473a3093d`
was blocked. The basics root-container branch did not apply the descendant
attribute guard. Thus one hidden attribute could conceal the complete explanation.
It also recorded unguarded methods records, positional source/locator pairing,
weak source-heading anchors, an unnecessary Scottish anchor for Welsh copy, and
inaccurate evidence records.

The bounded shared repair adds independent container and ancestor visibility
checks in the tax and payer validators. They reject hidden, aria-hidden, inline
hiding styles and known responsive/view hiding classes. Root basics containers
must not acquire classes. The fragment checker applies an exact 7-attribute
allowlist to roots and descendants before the root branch returns: `data-basics`,
`aria-labelledby`, `id`, `data-basics-claim`, `data-basics-scope`, `href` and `open`.
Every other attribute is rejected, including `popover`, `inert`, `role`,
`tabindex`, classes, styles and event handlers. Native open details remain valid.
Source-heading checks and the Welsh anchor correction remain unchanged.

Guidance methods now use an explicit source-ID-to-locator map, not zip position.
The renderer requires exactly the 7 source IDs and renders a fixed order. Each
row carries its guidance source ID. Register reordering cannot attach a locator
to the wrong source.

`check_site.check_guidance_methods()` independently validates the retained source
bytes, then checks the real `methods.html#tax-guidance` record. It checks the
heading, visibility, retrieval date, no-established-publication-date wording,
scope, one native disclosure, all 7 ordered source IDs, exact official URLs,
heading locators, original-response hashes and retained-envelope hashes. It does
not import the producer or its locator mapping. The public-byte basics gate now
requires the methods page as well as both content pages; check_site and verify
therefore inspect published methods bytes before deterministic regeneration.

## Tests and unchanged gates

Added shared tests mutate root sections/asides and ancestors with hidden,
aria-hidden, display/visibility styles and view/responsive classes. Tax/payer
validators must reject those independently of the fragment validator.
Methods tests mutate URLs, original and retained hashes, heading locators, source
IDs, order, retrieval/status wording and visibility in actual rendered content.
Renderer tests reverse source order and reject missing, extra or duplicate IDs.
Published-byte coverage includes the methods page.

Existing tests retain real source/hash checks, explicit-root isolation, no
foreign-source fallback, last-good publication safety, exact fiscal counts and
private-path 404s. Forecast-date guards, neutral palette, grade 7 limit, page-size
limit, all tables, 44px controls and the strict 8-file allowlist remain unchanged.
No raw sources, registers, audit CSVs, dependencies or factory files are changed
by this repair.

## Delivered successor and round-3 reader repair

The controller handoff reports that successor #37 delivered revision
`2af5faf9edb54ab9163bea45edee5bfa9c06a307`. This is the pinned base for #38 and
supersedes this document's earlier preparation-only live-state description. It does not
alter the original #33 attempt, claim or needs-john receipt.

The parent reports whole-product council round 2 as Opus 9.3, Grok 9.3 and Muse
9.6. Muse was satisfied; the round was not satisfied overall. These are attributed
reports, not new worker-observed scores or approval of this candidate.

The bounded round-3 reader repair changes no financial values or retained sources:

- The decade spending headline is immediately followed by a comparison note,
  before the first money chart. Both OBR October 2026 and HM Treasury PESA 2026
  GDP shares use existing source-backed `<data>` values. The note says that the
  vintages and GDP bases differ, the figures are not directly comparable, and
  their gap is not a spending change. Independent checks bind position, both
  identities, visible copy and the headline; mutations cannot move the note
  elsewhere and leave the guard satisfied. Exact attribute contracts cover the
  known shell ancestors, both paragraphs, citations and data elements. Unknown
  classes and attributes, native concealment attributes and unknown wrappers
  are rejected, rather than relying on a concealment blacklist. Added mutations
  cover these routes. The parent owns browser paint checks for the new note.
- The decade comparison uses neutral language, keeps the warning that a GDP
  share can rise when GDP falls, and calls the money received receipts in its
  heading, legend, prose and table. The Methods source description does too.
- The Corporation Tax scope now identifies this site's receipts group. It stays
  separate from the GOV.UK profits definition and retains the U4/C42 locator.
- Both basics modules say “Our summary of official guidance” before their claims.
  Methods explicitly calls them summaries, not quotations. Independent copy
  contracts and mutations cover these labels.
- The retained Welsh “How you pay” text describes PAYE, pension deductions, the
  HMRC tax-code prefix and Self Assessment. It does not explicitly state the
  broader collection claim. The Welsh summary therefore omits “HMRC collects
  the tax”; the Scottish statement and all retained-source pins stay unchanged.

The parent supplied the approved 5-sentence payer definition. The Methods
`fiscal-glossary` now repeats that exact direct, indirect, final and intermediate
tax copy, including household scope and the explicit ONS model assumption.
It uses the same official bulletin glossary and technical-report section 7 URLs,
fragments and locators. Independent Methods checks bind the copy, exact attribute
contracts, source envelope/body hashes, heading quotations and Table 8 example
labels from the retained workbook. Mutations cover meaning, links, locators,
visibility, missing/duplicate definitions, retained bytes and example labels.
The public-byte basics gate checks this glossary as well as guidance Methods.
Another worker retains ownership of the payer definitions and source bindings.

This worker used source-file tools only. No build, tests, browser checks, Git,
network, review approval or publication were performed for this repair. The
parent must regenerate output, run targeted and full checks, retain all 24
original bindings and the exact 8-file public boundary, and obtain exact-candidate
review before making a new pass claim. The grade limit remains 7.0. Existing
attribute allowlists, ancestor guards and browser checks are not relaxed.

## Ticket #38 source-only handoff

The ticket reports that preparation revision
`c7a2fb3413a2c0499fce4d2e2325788a37c73298` passed the full credential-free Boat
pipeline with 242 tests and browser checks, and that sandbox `bx_tn8dct9p`
was deleted with exit 0. This is attributed preparation evidence from the
controller handoff, not an observed pass for the current draft.

Inspection of this workspace found the prepared reader templates and semantic
mutations already present, while all four checked-in HTML pages still had the
earlier copy. The file-only repair aligns those pages with the templates:
the adjacent source-backed vintage note, receipts labels, ONS definitions and
identical Methods glossary, summary labels, explicit Corporation Tax group name
and the bounded Welsh correction. The fiscal values and their source attributes
are reused unchanged. No public JSON, retained source or source register is edited.

Independent source inspection found that the browser guard checked the new payer
and vintage paragraphs but omitted their inline source links, citations and
figures. It also omitted the Methods glossary label. The repair includes those
descendants and the fiscal glossary in the existing paint checks, and adds
real-layout negative fixtures for the source span, both ONS anchors, both vintage
citations and figures, and glossary label, copy and link. The existing default,
expanded and no-JavaScript fixture loops remain in place. No attribute allowlist,
visibility guard, adjacency exemption, reading-grade limit or public-output
boundary is relaxed.

This draft is unverified. Only confined file reads and writes were performed.
The controller still needs to regenerate and compare all eight canonical public
files, run the full declared Boat pipeline and all shards, obtain independent
exact-candidate fiscal and implementation review, and verify deployment SHA and
live bytes. The preparation receipt does not cover these later source changes.
Whole-product council acceptance must use that same delivered revision. The
reported 9.3/9.3/9.6 round does not meet all-three 9.5 and explicit satisfaction.
Human studies, formal inherited 31/32 evidence and freshness history remain
pending until observed.

## Historical handoff and evidence limits

The parent reports that candidate `9dc` passed the full Boat check run with
231 tests. Its sandbox `bx_skdybngs` was deleted. That result belongs only to
that candidate; it does not cover the later attribute-allowlist repair.

The later repair replaces the incomplete attribute blacklist after review finding
B1 identified native `popover` concealment and `inert` access removal. Added
mutations cover both roots, claims, details and summaries, including unknown
attributes. A positive test retains native open details. This bounded repair
uses source-file read/edit tools only, with no execution or Git actions. Its
resulting exact candidate and check outcome are not yet established. No new
build, test pass, review approval or deployment is claimed.

The parent must combine the 2 non-overlapping repairs and run the full declared
pipeline on the resulting exact candidate. This includes source checks, build,
verification, unit/smoke tests, default/expanded axe at 360px and desktop, keyboard,
no-JavaScript content, no overflow and unchanged reading-grade limits. A new
independent review must resolve the blocking finding and advisories with evidence.
Human and same-live-product council evidence remain separate requirements.

At that historical handoff, the live product was revision
`168a7ad9cfe0305c12a3e891f1961bd8439536ac`. The preparation was not ticket #33
publication. The parent subsequently reported #37 delivery as noted above.
Preserve the original claim, attempt and needs-john receipt. No factory state
or issue body is edited here.

## Successor browser visibility completion

Source inspection of the successor found a remaining browser-check gap: positive
layout boxes did not prove that an overflow-clipping ancestor painted the text.
The guard also omitted the separate Corporation Tax scope paragraph, definition
labels and unmarked disclosure paragraphs. Static attribute checks did not cover
concealment introduced through a stylesheet.

The browser guard now checks those text elements and the methods guidance source
rows, source links and hashes in default, expanded and no-JavaScript runs. It rejects legacy CSS clipping,
content outside horizontal page bounds and text clipped by its own box or an
ancestor's scroll area. Vertical page scrolling remains valid. The existing smoke
entry point also exercises real-layout mutations for ancestor opacity, inert,
popover, overflow clipping, legacy clip, clip-path, off-page transforms and
concealed scope, labels, disclosure text, methods source rows, links and hashes. Closed native
disclosure content is checked after expansion rather than rejected by default.

This bounded worker used workspace file tools only. No repository programs,
tests or browser checks were executed here. The controller must run the full
pipeline and exact-candidate independent review before making any pass or
deployment claim; the added regression cases are source changes, not observed
test results.
