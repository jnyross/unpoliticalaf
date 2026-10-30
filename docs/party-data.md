# Commons party evidence: partial candidate, not accepted public output

This repair retains a real Commons roster and two historical proposal examples.
It does **not** close #8. Thirteen of the fifteen parties have no proposal record
in this seed; no independent fiscal/editorial review has been performed.
`candidate`, an acquired publication, an attributed assessment, and a passed
structural check are distinct from accepted content. No party content is emitted
by the four-file fiscal public allowlist.

## Requirements and source of the contract

The pinned `reference/un-political/SOURCE.json` identifies source revision
`8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713`. Its `docs/rubric.md` has SHA-256
`97dce23dec4003babc2865f80e7a65cda23fe86bcf94d01dc506605b45249a70`.
Impartiality level 3 requires the same template, fields, order and length limits,
and permits linked attributed judgements only from IFS, OBR, Resolution Foundation,
Full Fact and NAO. Coverage level 4 requires every Commons party and independent
assessments of costed plans. `docs/product-spec.md` requirement 5 adds neutral
alphabetical ordering, no party colours or ratings, explicit unavailable costs
and assessments, scope, baseline, year and status. Neither source supplies a
literal JSON field order or numeric length limit: the common field order below
and common validator limits are implementation choices for later rendering.
The named-body domain mapping in `party_data.py` resolves publisher identities;
it does not assert that those bodies endorse the site or reviewed this seed.

## Retained evidence and classification

`data/party-evidence/20261030-repair2/` contains five complete successful original
HTTP responses and their complete deterministic readable-text extractions, plus
`acquisition.json`. No source assets used by this seed are omitted or excluded
from the review diff. The separate `data/party-sources.json` binds exact official
URL, actual observed UTC retrieval timestamp, publication date and exact raw
publication-date locator, or the roster snapshot date, plus both file hashes.
HTML extraction omits script, style and SVG contents, normalizes whitespace in
text nodes and joins them with newlines. It retains all other text, including
navigation and footers; it is not a manually selected quotation archive.
The validator reopens raw responses, verifies their hashes and regenerates text
before checking character offsets and verbatim quotations.

The official endpoint is
`https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2026-10-30`.
Its self link records Commons at **00:00:00 on 30 October 2026**, not the end of
that day or the time it was fetched. The response contains 17 groups: 15 parties,
11 MPs in Independent and one Speaker, totalling 650. It reports `totalResults: 0`
despite nonempty `items`; this is an unpaginated party-state endpoint, not the
member-search API. Completeness is exact equality of all source group identities
and counts, with subgroup reconciliation, duplicate rejection and house/date
self-link checks. Counts are imported, not a hard-coded assumption of 650.

Independents are a separately classified Parliament group, not one party or one
manifesto. The Speaker is a separate office. `non_party_members` is retained as
the schema key for these **groups**, with `parliament_id`, `name`, `classification`
and `mp_count`; it does not claim to identify individual MPs. The official dated
state already groups Labour/Co-op with Labour. No separate Co-op group is added.
Sinn Féin is included as Commons representation without inferring attendance.

## Common record order and limits

Parties use `id`, `name`, `official_domain`, `mp_count`, `publication_sources`,
`coverage`, `unavailable_reason`, `proposals`. Party order is case-insensitive
alphabetical name, then Parliament ID. A retained party publication can be listed
without claiming a costed plan exists: Your Party's landing page is such a case.
Its linked printable draft has not been acquired or assessed by this seed.

Every proposal uses the same fields in this order:
`id`, `title`, `proposal_date`, `fiscal_year`, `fiscal_year_reason`, `baseline`,
`scope`, `geography`, `status`, `evidence`, `costs_claimed`, `funding_claimed`,
`assessments`, `overlap_key`, `overlaps_with`. Titles and party names are limited
to 160 characters, IDs to 100, explanatory fields to 400, and verbatim quotations
to 4,000. The same rules apply to every party. Proposals are alphabetical by title
then ID. JSON object order is a documented presentation contract, not a claim
that JSON itself assigns semantic significance to object order.

Amounts are exact decimal strings with explicit currency units and annual,
cumulative, one-off or unspecified time basis. A missing amount has
`availability: unavailable`, a reason and no items; it cannot become zero.
A missing fiscal year is null with a reason. `status: proposed` here describes
what the publication proposed **at its publication date**, not current enactment,
withdrawal or whether a 2024 offer is still the party's policy in 2026. That current
status has not been established. No manifesto or speech figure is an outturn.

The Labour example imports the Public Services table's 2028-29 additional
spending total (including Barnett consequentials) and its revenue total. The
source says not all revenue is allocated to spending. The Green Prosperity Plan
and reallocations are excluded. The SNP speech's extra NHS allocation has no
specified fiscal year or time basis in the retained passage; both remain missing.
There is no sum of different parties' claims or overlapping proposals.
Exact duplicate excerpts are refused. Intersecting excerpts from the same source
hash for one party must declare the same complete, symmetric overlap group,
even if their start/end offsets differ. Separate passages discussing the same
policy can still need editorial overlap classification.

Independent assessments use `publisher`, `assessed_on`, `scope`, `evidence`.
They contain only an attributed source quotation, not a site-authored rating.
The retained Resolution Foundation passage concerns the overall Conservative
and Labour spending plans, not verification of the individual Labour table or
a 2026 plan. The SNP assessment is explicitly unavailable. Structural validation
does not prove fiscal interpretation, numeric scope or comprehensive coverage.

## Execution and acceptance

All product execution, dependency installs and official HTTP acquisition run in
credential-free Boat. The factory owns integration, independent review, exact
candidate checks, publication and live qualification. The following commands
are for that environment, not the credential-bearing fleet host:

```sh
make setup
python3 scripts/acquire_party_evidence.py --output data/party-evidence/NEW_ID --roster-date YYYY-MM-DD
python3 scripts/import_party_evidence.py --evidence-dir data/party-evidence/20261030-repair2
python3 scripts/party_data.py --as-of 2026-10-30
make build
make verify
make smoke
```

Acquisition is deliberately bounded to the five sources this repair supports.
It creates a new directory exclusively, records failures, refuses unexpected
origins, types, dates and excessive size, and never overwrites a previous record.
It is not a comprehensive party-plan refresh command. The importer reopens and
validates all evidence before replacing candidate files. No protected fiscal raw
file, catalogue, reference, harness or dependency is modified.

`make verify` discovers the party tests, including actual retained evidence and
corruption cases. The fiscal builder is unchanged: a wall-clock party freshness
failure cannot block rebuilding unrelated fiscal public bytes. Offline regression
tests use the observed acquisition date; explicit current acceptance checks use
the current UTC date by default. The roster fails after 30 days and publication
retrievals after 90 days. A historical publication date is never rewritten into a
current plan date; recent retrieval alone does not establish current relevance.

The controller must separately require complete party proposal coverage and
real external factory fiscal/editorial verdicts on its exact Git candidate:

```sh
python3 scripts/party_data.py --require-coverage --require-reviews \
  --fiscal-verdict /PRIVATE/fiscal/verdict.json \
  --editorial-verdict /PRIVATE/editorial/verdict.json \
  --base-sha BASE --candidate-sha CANDIDATE --tree TREE
```

These files use the existing factory `base_sha`, `candidate_sha`, `tree`,
`findings` verdict format. Every binding must match and blocking findings refuse
acceptance. The trusted controller authenticates receipt provenance, independent
reviewer roles and that these expected Git IDs identify the files being checked.
The parser cannot establish those facts by itself. It must never be used as a
standalone certificate of review. `reviews.fiscal` and `reviews.editorial` remain
null in the data; invented embedded approvals are refused. The report always
keeps `public_accepted: false`; actual publication is a later controller decision.
Both strict commands currently fail as intended. A passing structural pipeline
is not a passing #8 acceptance gate.

## Outstanding original acceptance

All original #8 criteria remain on the factory successor. Full proposal acquisition
and current-plan classification for every party remain incomplete. The 13 parties
without proposal records are Alliance, Conservative, Democratic Unionist Party,
Green Party, Liberal Democrat, Plaid Cymru, Reform UK, Restore Britain, Sinn Féin,
Social Democratic & Labour Party, Traditional Unionist Voice, Ulster Unionist Party
and Your Party. The two populated examples are not a complete survey of their
parties' offers. Missing costs, funding, years and assessments require evidence,
not inference. The roster is complete for the stated source snapshot only.

The private handoff retains separate source-acquisition probes for all remaining
parties. Some official routes return 403; several accessible full PDFs individually
exceed the unchanged 1,000,000-byte factory review budget. These probe downloads
are not used as claims or accepted evidence in this seed. The factory may reuse
unchanged, hash-verified sources already on main in a later bounded increment;
this seed does not change their protection or hide assets to fit a gate.

Independent fiscal/editorial checking of every populated claim, broader official
source and assessment coverage, current freshness qualification, public party
methods alongside a future renderer, exact-candidate official gates, deployment
and live verification remain pending. No #9 rendering, rubric rescore, human
review, scheduled freshness history or original-session replay is claimed here.
