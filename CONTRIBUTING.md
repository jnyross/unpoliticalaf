# Contributing

Follow [AGENTS.md](AGENTS.md), including its naming rules and stable public IDs.
Agent installs and project execution belong in credential-free Boat, not on the
host. No secret, `.env`, database or hosting account is needed.

## Test naming and discovery

Name tests `test_<subject>.py` and methods `test_<behaviour>`. Keep helpers out
of that filename pattern. `make test` uses pytest to collect both `tests/`
(including nested directories) and `quality/tests/`, including unittest cases.
`testexample.py` and `example_test.py` are deliberately not collected.

## Setup and checks

- `make setup` installs only production dependencies for `make build` and
  `make check`. It does not install pytest.
- `make setup-test && make verify` installs pytest and dashboard-test dependencies,
  builds the site, checks source data/pages and runs all tests. Build first when
  running `make test` separately, because some tests read `site/`.
- `make setup-dev` adds browser, lint, typing and dashboard dependencies.
- With Node 22, `npm ci --ignore-scripts` installs the locked developer tools.
  Run `npm run test:duplicates` for the Node regression suite, separately from pytest.
- `make quality` runs Ruff, Black's non-mutating check, forced Python compilation,
  strict core typing, dependency checks, complexity, duplication, seeded stability,
  guidance references and the existing quality dashboard. It requires the locked
  Node tools as well as `make setup-dev`.
  `make lint`, `make typecheck` and `make check-deps` also run separately.
- `make setup-typing && make typecheck` installs just production and typing
  packages. The strict boundary is listed in `mypy.ini`; extend it without
  weakening strictness. Compilation covers all first-party Python, even outside
  that initial migration boundary, and must run on Python 3.10 and 3.12.
- `make a11y` additionally needs Chromium, installed with
  `.venv/bin/python -m playwright install --with-deps chromium`, and a built site.

## Lint and formatting

Ruff 0.14.3 checks syntax/Pyflakes; Black 25.9.0 owns formatting. Do not use
`ruff format` as a second policy. Run `make format` to write formatting changes,
then `make format-check` to check without rewriting files. Black targets Python
3.10 with 100-character lines in `pyproject.toml`; Ruff uses `ruff.toml`.
Both commands explicitly select all Python files recursively in `builder/`,
`scripts/`, `tests/` and `quality/`, including newly added nested modules. Nested
tool configurations do not override those root policies. Retained official
data, `reference/` and generated `site/` are outside the selection. Formatting
must preserve stable fact/source IDs, public URLs/fragments and upstream names.
The existing CI quality job runs both checks, not a competing formatting job.

## Duplicate code

`make duplication` and `npm run check:duplicates` enforce the same jscpd 4.0.5
gate. The original Python selection is `builder/`, `scripts/`, `tests/`, recursively,
not generated output, retained publisher data or the separate dashboard.
Keep `.jscpd.json`'s five-line/50-token weak-mode rules and 0.5% line budget.
The wrapper rejects incomplete scans/tool errors and checks the raw line ratio;
console matches and `reports/duplication/jscpd-report.json` identify the population.
Do not add suppressions, enlarge the denominator with data, raise the budget or
merge deliberately independent fiscal readers/checkers to get a pass.
See [README.md](README.md#duplicate-code) for the exact denominator and file rules.

Use `.venv/bin/python` for direct commands. CI runs these same interfaces.
Submit through independently reviewed PRs with exact-candidate Boat/CI checks;
green tooling is not independent fiscal or accessibility approval.
