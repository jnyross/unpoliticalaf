# Unpolitical

An independent, phone-first website that explains UK public money and everyday
life using only official statistics. It answers four questions, with the answer
first and the method close by:

> **Taking over this project?** Read [docs/HANDOFF.md](docs/HANDOFF.md) first. It
> has the project goal, the success test, the current status and the constraints.

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

## Commands

Python 3.10 or later.

```
make setup     # create .venv and install openpyxl
make build     # write the site to site/
make check     # re-read every figure from its source file and check every page
make test      # fast unit tests
make verify    # build + check + test
make benchmark # time a fresh build, save JSON and enforce the 90-second budget
make setup-dev && make a11y   # axe accessibility checks at 360px and 1100px
```

Vercel: install `make setup`, build `make build`, output directory `site`, all set
in `vercel.json`. Only `main` deploys; other branches make no Vercel deployment,
so they don't use up the free plan's 100 deployments a day. Pull requests are
checked by GitHub Actions instead.

### Build performance

Every pull request and push to `main` times `make build` separately from setup,
source checks and tests. `make benchmark` writes `.cache/build-performance.json`
with wall-clock seconds, the result, Python/platform and CI commit/run identity.
CI adds the result to the run summary and retains the JSON as a
`build-performance-<run>-<attempt>` artifact for 30 days, even on build failure.
Compare artifacts from the same runner/Python version to track changes over time.

The initial 90-second budget is roughly twice the 44-second build observed in
[CI run 41928181052](https://github.com/jnyross/unpoliticalaf/actions/runs/41928181052)
on 4 November 2026. A slower build fails the check, as does any failed build.
For a different local machine, run
`.venv/bin/python scripts/build_performance.py --max-seconds 120`.
Investigate regressions with
`.venv/bin/python -m cProfile -o .cache/build.prof -m builder.build` and
`.venv/bin/python -m pstats .cache/build.prof` before changing the CI budget;
record the measurement and reason in the pull request.

Both CI jobs cache pip downloads keyed by their requirement files. They still
install the pinned dependencies and rebuild from retained sources on every run.
Glossary linking also reuses regex matches for repeated prose in a bounded
4,096-entry, in-process cache. It retains only immutable text spans, not each
page's link limits, already-linked terms or relative paths.
An initial before/after run on the same 2-vCPU Boat sandbox (Python 3.12, warm
filesystem, fresh Python processes) reduced build time from 36.58s to 24.69s
(32.5%). All 7,509 hashed output files were identical. This is a single-run
comparison, not a guarantee for other runners.
Generated pages and parsed source data are deliberately not cached, so stale
financial figures cannot bypass source validation. The measured CI build is
followed by the same independent checks and tests as `make verify`, without a
second build. Timings stay outside `site/` to preserve deterministic output.

Each build writes `site/build.json` (the commit and a SHA-256 for every file) and
shows the short commit as "Site version" in every page footer. `make live` builds
locally and checks that https://unpoliticalaf.vercel.app/ serves exactly that
build. The `Live site matches main` workflow runs this after every push to `main`
and daily, and fails if the live site is behind or differs.

The `Auto-merge green PRs` workflow squash-merges any open, non-draft PR from a
`claude/` branch once every check on its latest commit has passed. It runs when
`Build and check` finishes and every 5 minutes. A draft, a `hold` label or a
title starting with WIP keeps a PR open.

## How it is built

| Path | What it does |
| --- | --- |
| `builder/sources.py` | Registry of every source: publisher, title, link, file, SHA-256, dates, coverage |
| `builder/data.py` | Reads each figure from its file and cell into a `Fact` |
| `builder/pages_*.py` | Writes the pages; every displayed figure is a `<data data-fact="…">` element |
| `builder/check.py` | Independent checks: hashes, source cells, recalculations, page numbers, links, wording, accessibility |
| `sources/manifest.json`, `scripts/fetch_sources.py` | List and download newer sources into `data/fetched/` |
| `.github/workflows/fetch-sources.yml` | Runs the downloader on GitHub and commits the files with a receipt (`data/fetched/receipts.json`) |

Official data files live in `data/raw/`, `data/payers/raw/`, `data/life/sources/`
and `data/fetched/`. If any file changes without its recorded hash being updated,
the build stops.

## Updating the data

1. Add or change the download in `sources/manifest.json` and push. The fetch
   workflow downloads it and commits it with its hash and retrieval time.
2. Update the reader in `builder/data.py` if the layout changed.
3. Run `make verify` and review the changed pages.

Contains public sector information licensed under the Open Government Licence v3.0.
