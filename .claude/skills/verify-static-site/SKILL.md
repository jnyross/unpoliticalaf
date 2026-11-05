---
name: verify-static-site
description: Build and verify UnpoliticalAF's static site against its retained official sources. Use when changing data readers, calculations, page templates or assets, investigating a failed build or CI check, or preparing verification evidence for a pull request.
---

# Verify the UnpoliticalAF static site

Use this workflow to check a candidate, not to deploy it or declare the product
accepted. Run commands from the assigned repository root. Read `AGENTS.md`,
`docs/HANDOFF.md` and, for product changes, `docs/product-spec.md` first.
The commands below mirror `Makefile` and `.github/workflows/check.yml`; inspect
those files if the workflow has changed.

## 1. Identify the candidate and scope

```sh
git status --short --branch
git rev-parse HEAD
git diff --stat
```

Record the commit and whether there are uncommitted edits. Preserve other
writers' work. Do not switch branches, reset files or clean the checkout to
make a check pass. Use an assigned isolated checkout if another writer is active.

Locate the source of the change rather than editing generated HTML:

| Change | Relevant files |
| --- | --- |
| Official source file or provenance | `builder/sources.py`, `sources/manifest.json`, retained files under `data/` |
| Source cells, facts or calculations | `builder/data.py`, `builder/data_*.py`, `builder/readers.py` |
| Pages, chart markup or styling | `builder/pages_*.py`, `builder/html.py`, `assets/` |
| Independent validation or regression | `builder/check.py`, `tests/` |

`site/` is ignored generated output. `make build` replaces it, so do not store
handwritten work there. `.venv/` is also local and ignored. Do not commit either.

## 2. Prepare and run the core checks

Use Python 3.10 or newer; CI uses Python 3.12. On a fresh checkout:

```sh
make setup
```

This creates `.venv/` and installs the pinned production requirements, including
the spreadsheet and PDF readers. It needs package-network access. Use the
repository virtual environment, not global package installs. If setup fails,
report the failed command and cause; do not call the remaining checks passed.

```sh
make verify
```

Run this serially, not with `make -j`: the checker needs the completed build.
The stages are:

1. `make build`: checks source hashes and quoted explanations, then generates
   HTML, CSV downloads, `site/data/facts.json` and `site/build.json`.
2. `make check`: independently re-reads source figures, recalculates derived
   facts and checks rendered numbers, links, tables, chart wording and limits.
3. `make test`: runs the `unittest` regression suite in `tests/`.

For diagnosis, run the failing stage separately. `make check` requires a current
successful build; `make test` alone is not a substitute for `make verify`.
After fixing a failure, rerun the affected stage and then `make verify`.

## 3. Check source and presentation integrity

For a data change, reopen the retained official file and confirm the exact
sheet/cell or PDF locator, units, period, geography and population. Check the
calculation inputs, not just the displayed rounded result. Follow the emitted
fact in `site/data/facts.json` back to its registered source.

Keep missing values missing, forecasts labelled and incompatible definitions
separate. Never change a source hash merely to silence a mismatch, substitute
zero, silently interpolate, weaken reconciliation checks or relax page limits.
Investigate the changed bytes and provenance first. New source downloads follow
`sources/manifest.json` and the fetch workflow described in `README.md`; local
verification does not authorize fetching, committing or publishing new data.
Record corrections to published mistakes in `CORRECTIONS` in `builder/trace.py`.

For a page, chart or shared style change, also inspect the affected generated
pages: answer-first wording, neutral treatment, visible methods/source links,
complete adjacent tables, mobile layout and core content without JavaScript.
Automated checks do not replace this inspection or independent review.

Run the browser accessibility gate for presentation changes:

```sh
make setup-dev
.venv/bin/python -m playwright install chromium
make build
make a11y
```

This uses axe at 360px and 1100px and the strict accessibility benchmark. If
Chromium cannot launch because system libraries are missing, use the supported
CI/sandbox environment. CI uses Ubuntu 24.04 and Playwright's `--with-deps`
installation; do not install system packages on the host without authorization.
Report an unavailable browser check as blocked, not passed.

## 4. Return evidence, not acceptance claims

Run `git diff --check` and inspect `git status --short` after verification.
Report the candidate commit, any uncommitted edits, commands with their actual
outcomes, inspected pages and remaining failures or skipped checks with reasons.
Keep source-integrity failures distinct from environment/setup failures.

Do not run `make live` to validate an unpublished branch: it compares a build
with production, which may serve another commit. Local checks do not prove a
deployment matches, satisfy independent review or replace the real five-person
phone study. This skill authorizes no push, merge, deployment, scheduler change,
credential access or acceptance-score update.
