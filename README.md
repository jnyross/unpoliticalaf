# Unpolitical

An independent, phone-first website that explains UK public money and everyday
life using only official statistics. It answers four questions, with the answer
first and the method close by:

> **Taking over this project?** Read the current section of
> [docs/HANDOFF.md](docs/HANDOFF.md#current-handoff--5-november-2026-decisions)
> first. The older handoff is preserved history, not the current acceptance test.

## Current goal and delivery

John's decisions on **5 November 2026** select [docs/goal-rubric.md](docs/goal-rubric.md):
**>=49/55, every dimension >=4, D11=5, all recorded John's-question probes
passing and no unresolved material finding on the same live candidate**.
Testing and acceptance are agent-run. No human recruitment, consent, real-phone,
outside-human review or actual screen-reader gate is required. A pass is labelled
**"met (simulated)"**, with the rubric's simulation limits, not proof of real
newcomer comprehension. Old 31/32 and frozen-v2 96/100 targets are historical.

The source is public with John's approval. Deliver through PRs with independent
agent review, credential-free Boat checks and CI on the exact candidate, then
agent-managed merge and Vercel/live-byte verification. No self-approval or
direct-main/controller publication. The old controller, claims, bindings and
disabled schedules stay paused and preserved; provider, billing and credentials
stay unchanged. Do not silently enable dormant source or merge writers.

**Completion is not yet established.** [docs/goal-scorecard.md](docs/goal-scorecard.md)
contains dated historical assessments, not a fresh final same-candidate pass.
This guidance change claims no new reader, accessibility or live acceptance.
Commit the sealed-question hash and accurate README before final source freeze;
post-freeze formal audits belong under `docs/standins/audits/` on a non-deploying
evidence branch naming the audited source SHA. Preserve pinned sources/hashes,
dated evidence and unperformed human/freshness history.

- **Where does public money go?** (`spending.html`)
- **Which taxes raise the money?** Taxes, other receipts and borrowing, kept apart (`taxes.html`)
- **Who pays?** Income Tax by taxpayer group, and all taxes by household income (`who-pays.html`)
- **How much household income goes on tax?** Without mixing up household
  averages, personal tax rates and shares of total revenue (`household-tax.html`)

It also has **Everyday life, year by year** (`life/`): work and job types, pay
after inflation, housing, holidays (abroad and within Great Britain, with the most visited countries) and school class sizes from 2008 to
2025, with the longer official series reaching back to 1971. Every year from 1971 has its own page, and every pair of years has a comparison page
(pairs with a year before 2008 compare only the figures measured the same way in both years),
so the core answers and comparisons work without JavaScript.

## Rules the site follows

- Every number comes from an official file kept in this repository, and is shown
  with its period, place, population and units. `site/data/facts.json` lists every
  figure with its exact sheet and cell, or the calculation and its inputs.
- Missing years stay missing. Where a definition changes (job classification in
  2021, the holiday survey method in 2024, and others listed on the pages), the
  series is broken and no change is calculated across the break.
- No invented household is presented as fact. The single worked example is
  labelled “Illustration, not a statistic” and kept apart from the statistics.
- Figures show what changed, not why.
- Plain English, white and grey styling, and a full table next to every chart.

## Environment variables and local setup

**No environment variables, API keys or secrets are required** to build, check,
test or serve the site locally. There is no `.env` file to create or copy, and
the build does not load `.env` files. The site is static: it needs no database,
backend service or Vercel account for local development.

Install Python 3.10 or later (including `venv`) and Make, then run `make setup-test`
and `make verify` from the repository root. Setup installs the pinned packages
in `requirements-test.txt` into `.venv`; subsequent build, check and test commands use
that interpreter without needing to activate it.

For autonomous work, run project installation, builds and tests only in
credential-free Boat (`--no-env`) from a reviewed tracked/index export, never
with host credentials or `.git`. Use Python 3.12 normally and the existing
Python 3.10 compatibility checks where applicable, Node 22 for project tooling
and Node 24 for agent-browser. The commands below describe the project interface,
not permission for agents to execute the project on the host. Sandbox previews
bind loopback port 3181; stop owned processes and verify sandbox deletion.

The optional settings are:

| Setting | Default when unset | When to use it |
| --- | --- | --- |
| `PYTHON` | `python3` | Select the interpreter used to create `.venv`, for example `make setup PYTHON=python3.12`. Later commands still use `.venv/bin/python`. |
| `VERCEL_GIT_COMMIT_SHA` | `git rev-parse HEAD`, or `unknown` if Git metadata is unavailable | Vercel supplies this for the build's version label and `site/build.json`. Leave it unset locally so the current checkout supplies the commit. It is not a credential. |
| `GITHUB_STEP_SUMMARY` | No summary file is written | GitHub Actions supplies a file path for `scripts/check_live.py` to append its report. Leave it unset locally; the live check still prints its result. |

Setup needs network access to install packages. Once installed, `make verify`
uses the official source files already retained in the repository and needs no
external services. `make fetch` and `make live` are separate, network-dependent
commands for refreshing sources and checking the deployed site. Accessibility
checks also need the development packages (`make setup-dev`) and a Chromium
installation (`.venv/bin/python -m playwright install --with-deps chromium`).

After `make build`, preview inside Boat at `http://127.0.0.1:3181`:

```sh
.venv/bin/python -m http.server 3181 --bind 127.0.0.1 --directory site
```

Deployment and automation credentials belong in their hosting or CI settings,
not in this checkout. Do not commit secrets or local `.env` files.

## Commands

Python 3.10 or later.

```
make setup     # create .venv and install production build dependencies
make setup-test # add pytest and build dependencies, without browser tools
make build     # write the site to site/
make check     # re-read every figure from its source file and check every page
make test      # fast unit tests
make test-stability # same pytest suite in fresh processes with seeds 1, 2 and 3
make verify    # build + check + test
make verify-coverage # same population under the combined 80% coverage gate
make benchmark # time a fresh build, save JSON and enforce the 90-second budget
make setup-dev && make quality # lint, format, types, dependencies, stability, guidance, dashboard
make lint      # Ruff syntax/Pyflakes across all first-party Python
make format    # Black writes maintained Python in builder/, scripts/, tests/, quality/
make format-check # check formatting without rewriting files (also in quality/CI)
make typecheck # forced compilation then strict core mypy checks
make check-deps # runtime, browser and developer dependency classification
make setup-quality && make complexity # new-function ceiling 20 and legacy ratchet
make setup-dev && make a11y   # axe accessibility checks at 360px and 1100px
```

Black 25.9.0 owns formatting (Python 3.10 target, 100-character lines in
`pyproject.toml`); Ruff 0.14.3 owns linting, not a second formatting policy.
Both select maintained Python recursively, including nested new modules, without
touching retained official data, pinned references or generated output.
See [CONTRIBUTING.md](CONTRIBUTING.md#lint-and-formatting) for the policy.

### Complexity gate

`make complexity`, also part of `make quality` and its CI job, uses Radon 6.0.1
from the dashboard's canonical `quality/requirements.txt`. It recursively selects
every Python file in `builder/`, `scripts/` and `tests/`, including nested tests,
methods, async functions and closures. This preserves PR #248's population;
`quality/` reporting code remains outside that gate. The dashboard's informative
complexity/maintainability measurements are preserved, not substituted for the gate.

New functions must score **20 or lower**. `complexity-baseline.json` started with
PR #248's 52 existing over-limit functions (base `b8e6ab5`, PR head `b8b9629`).
Each exception belongs only to its exact path and lexical function name; it is
not a shared allowance. Existing exceptions are measured, not excluded, and
cannot increase. Improvements require lowering the ceiling to the measured
score; remove an entry when it reaches 20 or disappears. Renames get the default
ceiling, not the old exception.

Do not raise ceilings or add entries to hide a failing implementation. Split
logic into focused helpers instead. There is no baseline-regeneration command;
downward-only changes need source review. Missing/malformed baselines, empty
source directories and analyzer failures fail closed. Production dependencies
and `make verify` are unchanged.

### Coverage gate and dashboard

`make coverage` (also `make verify-coverage`) measures a fresh build, independent
source/page checks and the canonical timed pytest population, including nested
reporter tests. The minimum is **80% combined statement-and-branch coverage**:
covered statements plus covered branches, divided by all statements plus all
branches. Every Python file recursively under `builder/` and `scripts/` counts,
including unexecuted modules. There are no producer exclusions. This is combined
verification coverage, not unit-only coverage.

The dashboard in `make quality` and `make -f quality/Makefile metrics` uses this
same measurement and gate. Each invocation retains separate ignored reports in
`quality-reports/invocation-*/`, including phase logs, test timings, coverage
HTML/XML/JSON, `metrics.json`, `summary.md` and `index.html`. A failed phase or
report fails the command; an earlier success cannot fill in for it. The reporter
rejects missing, malformed, source-mismatched or incomplete measurement data.
Complexity and maintainability are informative, not new thresholds.
See [quality/README.md](quality/README.md) for report interpretation.

### Build performance

`make benchmark` times the real `make build` in a fresh process. The fixed CI
budget is **90 seconds**: exactly 90 passes, longer fails, and a failed build
always fails even if fast. Setup, independent `make check` and tests are outside
the timing; the build's source hash and quote checks remain inside it.
The budget retains #237's baseline of about 44 seconds in
[CI run 41928181052](https://github.com/jnyross/unpoliticalaf/actions/runs/41928181052)
on 4 November 2026. No new speedup is required.

Measurements stay outside deterministic output in `.cache/build-performance.json`.
The report records wall-clock duration, original build exit, Python executable/
version, platform, named CI commit/run identity and cache context. It observes
whether `site/` and builder bytecode existed before the run; pip cache-hit is
unknown outside configured CI. OS filesystem caches are not flushed or assumed
cold. The glossary cache starts empty in every new build process.
CI appends a summary and retains the JSON for 30 days, including failures.
Compare like runner/Python/cache contexts rather than treating unlike runs as
a measured optimization.

CI caches only pip downloads keyed by all applicable requirement files. It still
installs dependencies and rebuilds from retained sources. Glossary linking caches
only immutable regex match spans for at most 4,096 prose strings in one process.
Page paths, link limits and already-linked terms remain page-specific. No new
source/fact, page or on-disk build cache is introduced, and no generated output is
restored. Existing source readers still run inside each fresh build process.
Independent checks and the complete test/stability populations remain enabled.

Investigate a regression before proposing a budget change:
`.venv/bin/python -m cProfile -o .cache/build.prof -m builder.build`, then
`.venv/bin/python -m pstats .cache/build.prof` (create `.cache/` first).
For a different local machine only, the runner accepts `--max-seconds 120`;
neither Make nor CI overrides the approved 90-second default.

### Local unit tests

From a fresh checkout, run `make setup-test && make build && make test`.
Build first because some tests read the generated pages and data in `site/`.
Setup needs network access to install the pinned dependencies into `.venv`;
it does not change your system Python. Pytest runs both unittest cases and
pytest tests, including nested `tests/` and `quality/tests/`. Collect them with:

```sh
.venv/bin/python -m pytest --collect-only
```

Use `.venv/bin/python`, not an unconfigured system `python3`, for pytest commands.
Alternatively, activate the environment with `. .venv/bin/activate` before
running `python -m pytest --collect-only tests/test_household_shares.py`.
`make setup-test` also includes the existing dashboard's test dependencies.
`make setup-dev` includes the test dependencies as well as the optional browser
tools. Production deployments still use `make setup`, without either set of tools.
CI checks the lightweight test setup, bounded pytest collection and `make verify`.

### Test timing and stability

`make test` runs the canonical pytest population once through the same worker as
`make test-stability`. Pytest's `pyproject.toml` selection includes all nested
`tests/` (including tooling and architecture) and `quality/tests/`, not a second
unittest-only discovery path. `make verify` keeps build + independent check +
timed tests; `make quality` also requires the three-run stability check.
`make test-stability` builds first so the same command works on a clean checkout.
Canonical Make targets clear `PYTEST_ADDOPTS` to prevent hidden deselection;
diagnostic CLI selections and deselected counts are recorded in the reports.

Stability runs use fresh Python processes with `PYTHONHASHSEED=1`, `2` and `3`.
Every original exit, collected ID, outcome and traceback remains in the report.
Any failure, error, collection problem, unexpected success, missing test, crash,
timeout, empty suite or report error fails the aggregate. Later passing runs
are diagnostic evidence, never forgiveness. Stable skips and expected failures
are recorded but not counted as passes. Three passes sample stability, not proof
that a test can never flake.

Each invocation gets a fresh ignored directory under `test-results/performance/`
or `test-results/stability/`. Its `report.json` records per-test outcomes/pass
rates, changing outcomes, all attempt exits/seeds/durations and commit metadata.
`summary.md` summarizes that evidence; `run-*.log` retains complete pytest
output. Every completed worker also writes `run-*/timings.json` (all tests,
sorted slowest first, phase durations and environment metadata) and `summary.md`
(ten slowest tests). Crashed workers have no fabricated complete timing report.
An earlier invocation's files cannot be mistaken for a later run.

Timing uses monotonic clocks. Per-test duration sums pytest setup/call/teardown,
including cleanups; shared class/module fixtures are charged to the tests that
execute them. Suite duration excludes collection; wall duration includes it.
Compare matching IDs only on comparable Python/runners. There is no timing gate.

CI publishes summaries and retains the complete `test-results-<run>-<attempt>`
artifact for 30 days, on success or failure. If setup/build/check prevents tests
from starting, it does not invent a completed run. Reproduce a failure with
`PYTHONHASHSEED=<seed> .venv/bin/python -m pytest '<node ID>'`; record the ID,
seed, original failure and run URL in the issue, fix the cause and rerun.
For a longer probe, use
`.venv/bin/python -m scripts.test_stability --runs 10 --timeout 900`.
Focused diagnostic selections follow `--`, for example
`.venv/bin/python -m scripts.test_stability -- tests/tooling/`.
The default watchdog is 900 seconds per process, increased from the original
300-second proposal because the preserved merged population already takes about
11 minutes in Boat. CI bounds check/quality jobs at 60 minutes. These are
operational timeouts, not new speed gates or permission to omit slow tests.

This replaces the unittest runners proposed in PRs
[#234](https://github.com/jnyross/unpoliticalaf/pull/234) (pinned
`88eef9cd7e2d574b419bbe612cf82e40c82c8fe7`) and
[#238](https://github.com/jnyross/unpoliticalaf/pull/238) (pinned
`0f5b7acfafdbb90a6411fd07fefbe7369a37239f`), retaining their timing,
outcome and evidence safeguards while preserving merged pytest collection.

See [CONTRIBUTING.md](CONTRIBUTING.md) for naming and complete check interfaces.
Ruff is pinned to 0.14.3; strict core typing uses mypy 1.18.2 and
types-openpyxl 3.1.5.20261017. `mypy.ini` declares the initial strict boundary.
Python 3.10 and 3.12 both force-compile first-party code before typing, avoiding
warm-cache false passes. Dependency checks use deptry 0.25.1; browser packages
live in `requirements-a11y.txt` and CLI/stub/dashboard tools are development-only.
The existing dashboard remains descriptive, with no lowered thresholds.

Vercel: install `make setup`, build `make build`, output directory `site`, all set
in `vercel.json`. Only `main` deploys; other branches make no Vercel deployment,
so they don't use up the free plan's 100 deployments a day. Pull requests are
checked by GitHub Actions instead.

### Agent guidance validation

Run `python3 scripts/check_agents.py` without installing dependencies. The
`AGENTS.md freshness` workflow runs it on every pull request and push to `main`,
including code-only changes that could remove or rename a documented path.
It checks root `AGENTS.md` literal repository paths in backticks, inline Markdown
links and link definitions, reports broken references with line numbers, and
rejects paths that escape the checkout. External URLs and absolute operator
paths are not fetched or checked. Link fragments, prose and command execution
are outside this check's scope.

This reference check does not certify acceptance-policy alignment.
`tests/test_goal_guidance.py` protects key current-goal and delivery regressions;
independent review checks the full active-versus-historical meaning. John's
approved current target is in `docs/product-spec.md` and `docs/goal-rubric.md`.

Each build writes `site/build.json` (the commit and a SHA-256 for every file) and
shows the short commit as "Site version" in every page footer. `make live` builds
locally and checks that https://unpoliticalaf.vercel.app/ serves exactly that
build. The `Live site matches main` workflow runs this after every push to `main`
and daily, and fails if the live site is behind or differs.

The legacy `Auto-merge green PRs` workflow is disabled. Agents manage merges
only after independent review and required checks pass on the exact candidate.
Do not re-enable the old five-minute writer or bypass review with green CI alone.

## Code quality metrics

The [quality dashboard](quality/README.md) reports Python line and branch
coverage, function complexity and per-file maintainability on every pull
request and push to `main`. The **Code quality metrics** Actions run has a
summary table and a downloadable offline dashboard with detailed coverage.
Run it locally with `make -f quality/Makefile setup metrics`.

## Release notes

Pushing a version tag such as `v1.0.0` automatically publishes a GitHub release
with generated notes, contributor credits and a full comparison link. Pull
requests are grouped by optional labels; unlabelled contributions are included.
See [docs/releases.md](docs/releases.md) for tagging, prereleases and retries.
This is separate from the site's deployments from `main`.

## Contributing

Follow the [working agreement and source naming conventions](AGENTS.md#source-naming-conventions)
for Python, tests and embedded web code, including the rules for stable data IDs
and official source filenames.

## How it is built

See [Service architecture and dependencies](docs/architecture.md) for the
architecture diagram, build-to-browser data flow, external services and failure
boundaries.

| Path | What it does |
| --- | --- |
| `builder/sources.py` | Registry of every source: publisher, title, link, file, SHA-256, dates, coverage |
| `builder/data.py` | Reads each figure from its file and cell into a `Fact` |
| `builder/pages_*.py` | Writes the pages; every displayed figure is a `<data data-fact="…">` element |
| `builder/check.py` | Independent checks: hashes, source cells, recalculations, page numbers, links, wording, accessibility |
| `sources/manifest.json`, `scripts/fetch_sources.py` | List and download newer sources into `data/fetched/` |
| `.github/workflows/fetch-sources.yml` | Disabled legacy source writer; intentional activation needs reviewed implementation, not an automatic push |

Official data files live in `data/raw/`, `data/payers/raw/`, `data/life/sources/`
and `data/fetched/`. If any file changes without its recorded hash being updated,
the build stops.

## Updating the data

1. Add or change the download in `sources/manifest.json` on a branch. Source-fetch
   and accuracy-result writers are disabled. Use a reviewed explicit acquisition
   run in credential-free Boat (or an intentionally reviewed workflow run),
   retain source bytes and retrieval/hash receipts, and preserve last-good inputs
   on failure. Do not enable dormant schedules or assume a push fetched anything.
2. Update the reader in `builder/data.py` if the layout changed.
3. Run `make verify`, independently reopen official source cells/calculations,
   review the changed pages and deliver the source update through a reviewed PR.

Contains public sector information licensed under the Open Government Licence v3.0.
