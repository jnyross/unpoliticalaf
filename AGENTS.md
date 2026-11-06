# UnpoliticalAF working agreement

## Scope and authority

John authorised the full original Un-political product specification, ticketed
implementation and autonomous deployment on 30 October 2026. Read
`docs/product-spec.md` before product work. It supersedes the old placeholder-only
restrictions. Reuse the pinned product source and data in `reference/un-political/`
and `data/`; the original `/home/john/projects/un-political` is read-only.

John's decisions on 5 November 2026 supersede the old acceptance and delivery
rules. Work only in the assigned UnpoliticalAF checkout. The source is public
with John's approval. Deliver through pull requests, not direct-main pushes:
independent agent review, credential-free Boat checks and CI must pass on the
exact candidate before an agent manages its merge. No author may approve their
own work. Verify deployment to `https://unpoliticalaf.vercel.app` against a
rebuild of that same commit with its production flags.

Keep the old software-factory controller, claims, bindings and disabled
schedules paused and preserved. Do not operate or repair them. Do not enable
auto-merge, source-fetch or accuracy-result writers without reviewed intentional
activation; no dormant schedule is authorised. No credential, provider, endpoint,
subscription, speed or billing changes are authorised.

## Delivery rules

- Follow the current ticket and its dependencies. One writer owns each path.
- Preserve the setup/build/verify commands and deterministic static output.
- Every fiscal number comes from retained official source data with exact
  provenance. Independently verify source cells, calculations and reconciliation.
  Never turn missing values into zero or forecasts into observed facts.
- Preserve impartial wording, equivalent party treatment, accessible mobile and
  no-JavaScript content, and adjacent table alternatives to charts.
- Keep independent review and exact-candidate checks. A model must not approve
  its own implementation or fiscal interpretation. Fix findings and rerun checks.
- Acceptance testing and review are agent-run. No human study, recruitment,
  consent, actual-phone, outside-human review or actual screen-reader gate is
  required. Record agent-tested results as "met (simulated)", with simulation
  limits, never as real-person comprehension or elapsed human time. Preserve
  unperformed human evidence and freshness history honestly as historical gaps.
- The current goal is `docs/goal-rubric.md`: at least 49/55, every dimension at
  least 4, D11 = 5, all recorded John's probes passing and no unresolved material
  finding on the same live candidate. The old 31/32 and frozen-v2 96/100 targets
  are historical. Independently score each deployed wave and turn deficits into
  follow-up tickets until the target is achieved. Preserve evidence and scores;
  never redefine success or treat the first ticket list as the end of the work.
- All Claude calls use the existing CLIProxy subscription route. Use the existing
  configured model roles and standard speed. Do not add direct
  paid API keys, new paid services or change provider/billing defaults.
- Keep secrets, private factory state, agent notes and runtime bindings out of Git.
  Public source approval does not authorise exposing private runtime evidence.

## Source naming conventions

These rules apply to new and changed first-party source in `builder/`, `scripts/`
and `tests/`, including the HTML, CSS and JavaScript embedded in Python strings.
Reviewers must request corrections for naming that departs from these rules,
unless an exception below applies. Do not rename unrelated existing code merely
to apply this agreement.

### Python

| Kind | Convention | Repository example |
| --- | --- | --- |
| Modules and scripts | Lowercase `snake_case` with a .py extension | `builder/data_top_earners.py`, `scripts/check_live.py` |
| Functions, methods, parameters and variables | Lowercase `snake_case` | `find_row`, `get_value`, `used_counts` |
| Classes, including dataclasses and test classes | `CapWords` | `Fact`, `Facts`, `Formatting` |
| Module-level constants and fixed lookup tables | `UPPER_SNAKE_CASE` | `EARLY_YEARS`, `MAX_PAGE_BYTES` |
| Internal helpers | One leading underscore plus `snake_case` | `_cell_col` |
| Unit test files and methods | `test_<subject>` with a .py extension; `test_<behaviour>` methods | `tests/test_builder.py`, `test_missing_figure_is_not_zero` |

- Use `self` for instance methods and `cls` for class methods. Keep required
  Python special methods such as `__init__` unchanged.
- Write acronyms in lowercase inside functions and modules (`gdp`, `data_nato`),
  rather than introducing mixed forms such as `readGDP`.
- Use descriptive domain names. Short loop indices and established local names
  such as `wb` and `ws` are fine in a small scope; avoid opaque names in new APIs.
  Distinguish amounts, shares and units in names where confusion is possible
  (for example, `tax_bn` versus `tax_share_pct`).

### Embedded web code

- Use `camelCase` for JavaScript functions and local variables, and
  `UPPER_SNAKE_CASE` for fixed shared constants. Preserve browser API spellings
  such as `getElementById` and `scrollIntoView`.
- Use lowercase, hyphen-separated words for new multiword CSS classes, HTML IDs,
  `data-*` attributes and public page slugs, as in the class `pick-status`,
  attribute `data-fact` and page stem `who-pays`. Keep their Python string
  producers, CSS selectors, JavaScript consumers and tests in sync.

### Stable names and review checks

- Preserve publisher filenames, worksheet labels, official series codes and
  upstream schemas exactly. Do not rename retained data or anything in
  `reference/un-political/` to match source-code style.
- Treat existing fact IDs, source IDs, JSON keys, download names, URLs and
  fragment IDs as compatibility contracts, not ordinary Python identifiers.
  Follow the adjacent registry's pattern for new entries. Any necessary rename
  must update all producers, consumers, provenance references and tests together,
  and preserve existing public links.
- Explain any new externally required naming exception in a nearby comment or
  docstring. Independent review must check both identifier spelling and all
  references affected by a rename. Run `make test` for source changes and
  `make verify` when names affect generated pages or data. These checks catch
  broken references; naming style itself is enforced through review, not a
  naming linter.

## Sources and completion

`docs/product-spec.md` owns requirements; GitHub owns the live backlog. Reference
material is pinned and hashed in `reference/un-political/SOURCE.json`. Preserve
pinned originals, hashes and dated assessments. The installed factory and its
operational guide are historical, not the current delivery procedure; private
configuration stays outside the repository.

Complete a ticket only when its specified checks and independent review pass on
the exact candidate, it merges through a reviewed PR, and its live deployment is
verified where required.
Report a concrete failed check or missing decision rather than inventing evidence
or requesting permissions already granted above. Paid services, unapproved
integrations, provider/billing/credential/schedule changes and material
product-scope changes still need John.
