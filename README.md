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
make setup-dev && make a11y   # axe accessibility checks at 360px and 1100px
```

Vercel: install `make setup`, build `make build`, output directory `site`, all set
in `vercel.json`. Only `main` deploys; other branches make no Vercel deployment,
so they don't use up the free plan's 100 deployments a day. Pull requests are
checked by GitHub Actions instead.

Each build writes `site/build.json` (the commit and a SHA-256 for every file) and
shows the short commit as "Site version" in every page footer. `make live` builds
locally and checks that https://unpoliticalaf.vercel.app/ serves exactly that
build. The `Verify and record production deployment` workflow runs this after every push to `main`
and daily, and fails if the live site is behind or differs.

That workflow lives in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).
It also requires a successful Vercel commit status before recording a `production`
deployment in GitHub, with the exact SHA, Vercel deployment link and verification
run. Vercel's existing Git integration remains the deployer; this does not add a
second deployer, require a Vercel token or redeploy on a schedule. Failed checks
create no successful deployment record. Daily checks and reruns reuse the record
for a commit, even after a newer deployment has made it inactive.
The successful deployment status's `log_url` is the authoritative verification
run; the payload's `recording_run` identifies the run that first created the
record, which may have been interrupted before the success status was written.

`live.yml` remains a manual-dispatch compatibility entry point for older
auto-merge runs and calls `deploy.yml`. Its earlier history remains available
with `gh run list --workflow=live.yml`. Commits superseded before live verification
are not counted.

To inspect actual shipping frequency (not the number of live checks):

```sh
gh run list --workflow=deploy.yml --limit 30
python3 scripts/record_deployment.py --report  # uses the authenticated gh CLI
```

The read-only report counts distinct, successfully verified production commits in
each of the last four seven-day windows, using Vercel's deployment timestamps.
The target is at least two per week. Records start when this workflow is merged;
no historical releases or deployment frequency are invented. Low counts call for
shipping useful, checked changes, not scheduled no-op deployments.

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
