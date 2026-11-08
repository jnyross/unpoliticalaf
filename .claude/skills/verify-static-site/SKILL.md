---
name: verify-static-site
description: Verify UnpoliticalAF data, calculations, static pages and tooling in credential-free Boat. Use for focused worker checks, full candidate verification, source-integrity diagnosis, UI accessibility checks and honest pull-request evidence.
---

# Verify the UnpoliticalAF static site

This checks a candidate, not product acceptance or deployment. Adapted from
PR #255, source commit `40bd2053a69c4cf7052c086766e7b4359128c789`.
Read the current sections of [AGENTS.md](../../../AGENTS.md),
[handoff](../../../docs/HANDOFF.md) and [contributor guide](../../../CONTRIBUTING.md).
For product changes also read the [specification](../../../docs/product-spec.md)
and current [goal rubric](../../../docs/goal-rubric.md). Inspect the canonical
[Makefile](../../../Makefile) and [CI](../../../.github/workflows/check.yml);
do not invent a command or replace an existing gate.
Paths in commands and inline code below are relative to the repository root;
Markdown links are relative to this skill file.

## 1. Freeze the scope and export safely

On the host, inspect Git metadata and edit only the assigned checkout:

```sh
git status --short --branch
git rev-parse HEAD
git diff --stat
git diff --cached --stat
git diff --check
```

Preserve other writers' work. Never reset, stash or clean their files to pass a
check. Record HEAD, the exported tree and any staged/uncommitted differences.
An index export is **staged development evidence**, not clean-commit/live proof.
Use a reviewed immutable tracked/index export, excluding Git metadata, credentials,
environment files, private runtime bindings, installed packages and generated output.

All project installs, builds, tests and containers run only in credential-free
Boat with `--no-env`, explicit sandbox IDs, bounded lifetime and verified cleanup.
Use the current assigned orchestration outside this repository; this public skill
does not embed machine paths, credentials or controller configuration. Never use
an implicit current sandbox or copy creator logins. If safe Boat execution is
unavailable, report blocked, not passed; do not fall back to host execution.

Use Python 3.12 normally, Python 3.10 for applicable compatibility checks, Node 22
for project tools and Node 24 for agent-browser. In the Git-free export set
`VERCEL_GIT_COMMIT_SHA` to the actual recorded source HEAD before building.
For final checks, export the **clean committed candidate**, rerun after committing,
and retain that exact SHA plus the reviewed production flags/build configuration.
Do not use `unknown`, invent a SHA, or call staged results final-candidate proof.

## 2. Choose focused or full checks

Run these commands serially **inside Boat**, from its exported repository root.
Do not use parallel make: checks/tests need the completed build. Production-only
`make setup` does not install pytest. The browser-free worker setup is:

```sh
make setup-test
make build
.venv/bin/python -m pytest tests/test_verification_skill.py tests/test_check_agents.py tests/test_goal_guidance.py
```

That is a runnable guidance-only example, not a universal test selection. Select
the affected regression files and meaningful negative cases for the actual change.
Pytest collects both `tests/` and `quality/tests/`, including nested unittest
cases; do not replace it with root-only unittest discovery.

The full build/source/page/test gate is:

```sh
make verify
```

This runs build, independent check and the canonical timed pytest population.
Run full verification for data, calculation, rendering and cross-module changes;
a focused pass or `make test` alone is not a substitute.

The full current quality gate additionally needs developer and locked Node tools:

```sh
make setup-dev
npm ci --ignore-scripts
make quality
npm run test:duplicates
```

`make quality` composes Ruff, non-mutating Black, compilation/strict core typing,
dependency checks, complexity, duplication, architecture, seeded stability,
guidance references and the measured coverage/dashboard gate. It does not replace
`make verify` or browser checks. `make lint`, `make format-check`,
`make typecheck`, `make check-deps` and `make architecture` can diagnose failures.
Keep every original seeded failure; a successful retry cannot erase it.

In Git-free exports setup skips hook installation. Install/exercise hooks only
in disposable Boat Git metadata, never the host checkout. The dev container uses
`make setup-dev-tools` and an external `VENV`; there use `"$VENV/bin/python"`
for direct Python commands instead of the `.venv/bin/python` examples above.
Preserve the canonical pins, selections and thresholds.

## 3. Check source and calculation integrity

Change producers, not generated HTML. Source identities are registered in
[builder/sources.py](../../../builder/sources.py) and the
[source manifest](../../../sources/manifest.json); retained originals are under
[data/](../../../data/). Extraction lives in [builder/](../../../builder/),
with [readers](../../../builder/readers.py), independent
[checking](../../../builder/check.py) and [trace records](../../../builder/trace.py).
`site/` and `.venv/` are ignored disposable output, not places for handwritten work.

For changed figures, independently reopen the official original. Record publisher,
retained bytes/hash, publication/vintage, exact sheet/cell or PDF locator, units,
actual period, geography/population and observed/provisional/estimate/forecast
status. Trace the emitted fact in `site/data/facts.json` to that source, then
independently recompute derived formulas and all transitive operands at source
precision. Producer self-consistency or matching rounded output is not independent
source verification. Check reconciliation, adjacent tables and offered CSVs.

Keep missing values missing and incompatible definitions separate. Never replace
missing with zero, silently interpolate, relabel a forecast or change a hash to
silence a mismatch. Investigate changed bytes/provenance before accepting them.
Use the existing selective fetch procedure in [README.md](../../../README.md),
not an unsolicited whole-source refresh or dormant scheduled writer. Review
file/receipt/hash diffs and retain last-good pairs on failed acquisition.
Record published factual corrections in `CORRECTIONS` in `builder/trace.py`,
including the eventual merged PR number. Preserve pinned originals and history.

For a failing build/check, retain both the human stdout report and stderr
diagnostics, actual exit status and affected source/fact/path. Separate invalid
source/calculation evidence from setup/network failures. Fix the cause, rerun the
affected stage and the applicable full gates, keeping the failed run identifiable.

## 4. UI, accessibility and no-JavaScript checks

For templates, navigation, charts, assets or shared styles, also run:

```sh
make setup-dev
.venv/bin/python -m playwright install --with-deps chromium
make build
make a11y
```

Use agent-browser with an explicit owned session for actual navigation at 360px
and 1100px. Serve only inside Boat on loopback port 3181. Check the changed default
states, keyboard/focus, answer-first layout, neutral treatment, source disclosures,
chart/table alternatives, downloads and real no-JavaScript core routes/comparisons.
Use the existing Playwright/no-JS tools alongside agent-browser.
The current rubric's axe population is all generated HTML at both widths with
disclosures expanded. Inspect incomplete findings, never count them as passes;
do not treat a sampled automation run as exhaustive or weaken existing thresholds.
Record the actual population/pages/actions and any gap.
Close only owned browser sessions, stop only owned processes and verify sandbox
deletion after exporting evidence, even on failure. TTL alone is not cleanup proof.
For documentation-only changes, explicitly explain why UI checks were not run.

## 5. Report evidence and deliver through reviewed PRs

Report source SHA/tree, clean versus staged label, production flags/configuration,
built manifest identity when applicable, sandbox/run identity, each command's
actual exit status, test/check population, logs and original failures. List
blocked, skipped and unrun checks with reasons, not as passes. Report inspected
pages/source locators, findings and cleanup receipts without publishing secrets,
private runtime evidence or raw environment metadata.

Before publication, an author must obtain independent agent review of that exact
candidate, fix material findings, and pass applicable Boat/CI gates. No
self-approval. Use the authorised PR process and agent-managed merge, not direct
main pushes; leave the old controller, claims and disabled schedules paused.
This workflow does not itself publish, activate schedules or change credentials.

Do not run `make live` against an unpublished branch as if it were a deployment
test. For authorised post-merge qualification, verify the actual deployed revision
and every served manifest byte against a trusted rebuild of the **same commit**
with its production flags. Local green checks are not live-byte or acceptance proof.
Acceptance is agent-run under the current rubric, labelled **"met (simulated)"**
with simulation limits, never real-person comprehension or measured human time.
Historical unperformed human evidence remains history, not a required human gate.
