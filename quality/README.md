# Code quality dashboard

The **Code quality metrics** GitHub Actions workflow runs on every pull request
and push to `main`, and can also be run manually. It needs no service token or
external quality platform. Source and reports stay in this repository's
Actions runs.

Open the workflow's run summary for line/branch coverage, maximum function
complexity and a per-file maintainability table. Download its
`code-quality-metrics` artifact, extract it and open `index.html` for the offline
dashboard inside its `invocation-*` directory, including the 20 most complex functions with source line numbers.
`coverage/index.html` shows uncovered lines and branches. Artifacts are retained
for 30 days, allowing comparisons between runs; this is not a hosted time-series
service.

## Run locally

From the repository root, with Python 3.10+:

```sh
make -f quality/Makefile setup metrics
```

This uses the existing test setup (including pytest), installs pinned development-only
coverage.py and Radon tools, tests the reporter, then runs the unchanged build,
independent source/page checks and canonical timed pytest population under branch
coverage. It enforces the same 80% gate as `make verify-coverage` and fails if any
measured phase or report fails. Each run writes a fresh ignored
`quality-reports/invocation-*/` directory and prints its location:

- `index.html`: combined dashboard.
- `summary.md`: the same per-file measurements shown in Actions.
- `coverage/`, `coverage.xml`, `coverage.json`: detailed coverage in HTML,
  Cobertura XML and JSON.
- `metrics.json`: coverage counts, logical source lines, Radon maintainability
  index/rank, and complexity/rank/source line for every function and method.
- `measurement.json`: source/test/config hashes, phase commands and original
  exits, and the coverage JSON hash; phase logs and `test-timings/` are retained.

Old invocations remain separate, never appended into a new measurement. Report
generation rejects missing or malformed data, unsuccessful measured phases or
exports, changed source bytes, mismatched JSON, and coverage older than the
measurement start. Re-running `python -m quality.report --output PATH` requires
that invocation's matching source tree, not arbitrary historical coverage.

## Interpretation and scope

Coverage measures all three verification phases together, **not unit-test
coverage alone**. Both coverage and Radon include every Python file under
`builder/` and `scripts/`, including files never imported during verification.
Missing coverage for a source file fails report generation rather than silently
hiding it. Tests, pinned `reference/` code, generated `site/`, JavaScript and this
reporting tool are outside that scope.

The approved **80%** minimum uses coverage.py's combined statement-and-branch
denominator: `(covered_lines + covered_branches) / (num_statements + num_branches)`.
It is not an 80% line-only or per-file requirement. Separate line and branch
percentages in the dashboard are diagnostics. The configuration is
`quality/coverage.ini`, with no source omissions. Test discovery comes from the
root `pyproject.toml`, including `quality/tests`, and runs through the same
`scripts.test_performance` worker as stability checks, with timings retained.

Cyclomatic complexity counts independent paths per function: lower is simpler.
Radon's maintainability index combines Halstead volume, complexity, source lines
and comments into a 0–100 score: higher is easier to maintain. Its ranks are
A (>19), B (>9 to 19), C (0 to 9). The dashboard sorts files by lowest index and
shows complexity hotspots to make existing maintenance debt visible, rather
than hiding it behind an average.

These measurements monitor the codebase; they do not assert a historical trend
before runs exist, impose their own complexity/maintainability thresholds, or replace the existing
correctness and accessibility checks. Production dependencies, deterministic
site output and deployment commands are unchanged.

The separate `make complexity` gate, included in `make quality`, enforces the
new-function ceiling of 20 and the reviewed legacy baseline for all Python under
`builder/`, `scripts/` and `tests/`. Its scope is deliberately different from this
dashboard's `builder/` and `scripts/` measurements. See the root README's
complexity policy.
