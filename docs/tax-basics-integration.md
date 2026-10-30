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

## Handoff and evidence limits

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

The existing live product is revision `168a7ad9cfe0305c12a3e891f1961bd8439536ac`.
This preparation is not ticket #33 publication. Preserve the original claim,
attempt and needs-john receipt. Only a new controller-owned successor can proceed
after preparation passes. No factory state or issue body is edited here.
