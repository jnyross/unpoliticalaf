# Code quality dashboard

The **Code quality metrics** GitHub Actions workflow runs on every pull request
and push to `main`, and can also be run manually. It needs no service token or
external quality platform. Source and reports stay in this repository's
Actions runs.

Open the workflow's run summary for line/branch coverage, maximum function
complexity and a per-file maintainability table. Download its
`code-quality-metrics` artifact, extract it and open `index.html` for the offline
dashboard, including the 20 most complex functions with source line numbers.
`coverage/index.html` shows uncovered lines and branches. Artifacts are retained
for 30 days, allowing comparisons between runs; this is not a hosted time-series
service.

## Run locally

From the repository root, with Python 3.10+:

```sh
make -f quality/Makefile setup metrics
```

This uses the existing production setup, installs pinned development-only
coverage.py and Radon tools, tests the reporter, then runs the unchanged build,
independent source/page checks and unit tests under branch coverage. It fails if
any of those checks fail. It writes ignored output to `quality-reports/`:

- `index.html`: combined dashboard.
- `summary.md`: the same per-file measurements shown in Actions.
- `coverage/`, `coverage.xml`, `coverage.json`: detailed coverage in HTML,
  Cobertura XML and JSON.
- `metrics.json`: coverage counts, logical source lines, Radon maintainability
  index/rank, and complexity/rank/source line for every function and method.

## Interpretation and scope

Coverage measures all three verification phases together, **not unit-test
coverage alone**. Both coverage and Radon include every Python file under
`builder/` and `scripts/`, including files never imported during verification.
Missing coverage for a source file fails report generation rather than silently
hiding it. Tests, pinned `reference/` code, generated `site/`, JavaScript and this
reporting tool are outside that scope.

Cyclomatic complexity counts independent paths per function: lower is simpler.
Radon's maintainability index combines Halstead volume, complexity, source lines
and comments into a 0–100 score: higher is easier to maintain. Its ranks are
A (>19), B (>9 to 19), C (0 to 9). The dashboard sorts files by lowest index and
shows complexity hotspots to make existing maintenance debt visible, rather
than hiding it behind an average.

These measurements monitor the codebase; they do not assert a historical trend
before runs exist, impose arbitrary new thresholds, or replace the existing
correctness and accessibility checks. Production dependencies, deterministic
site output and deployment commands are unchanged.
