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
make setup-quality && make complexity  # enforce Python cyclomatic complexity
make setup-dev && make a11y   # axe accessibility checks at 360px and 1100px
```

Vercel: install `make setup`, build `make build`, output directory `site`, all set
in `vercel.json`. Only `main` deploys; other branches make no Vercel deployment,
so they don't use up the free plan's 100 deployments a day. Pull requests are
checked by GitHub Actions instead.

### Complexity gate

The `complexity` CI job uses pinned Radon to analyze every Python file in
`builder/`, `scripts/` and `tests/`, including methods, async functions and nested
functions. New functions must have cyclomatic complexity **20 or lower**
(Radon A–C). Production setup and `make verify` do not require quality tools;
run `make setup-quality && make complexity` locally, or use `make setup-dev`.

`complexity-baseline.json` records the 52 existing functions above 20 at adoption
(base commit `b8e6ab5`).
These are measured on every run, not excluded: an increase fails CI, as does
any new over-limit function. The gate prints the remaining debt. If a function
gets simpler, lower its recorded ceiling to the measured value, or remove its
entry once it reaches 20. Deleted or renamed entries also fail until removed.
Do not raise ceilings or add entries to accommodate new complexity; split the
logic into focused helpers instead. There is intentionally no baseline-update
command. Changes to the baseline need the same review as source changes.

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
