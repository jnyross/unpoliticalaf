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
build. The `Live site matches main` workflow runs this after every push to `main`
and daily, and fails if the live site is behind or differs.

The `Auto-merge green PRs` workflow squash-merges any open, non-draft PR from a
`claude/` branch once every check on its latest commit has passed. It runs when
`Build and check` finishes and every 5 minutes. A draft, a `hold` label or a
title starting with WIP keeps a PR open.

## Release notes

Pushing a version tag such as `v1.0.0` automatically publishes a GitHub release
with generated notes, contributor credits and a full comparison link. Pull
requests are grouped by optional labels; unlabelled contributions are included.
See [docs/releases.md](docs/releases.md) for tagging, prereleases and retries.
This is separate from the site's deployments from `main`.

## Automated deployment archives

After `Verify and record production deployment` (or the legacy
`Live site matches main` entry point) succeeds for this repository's `main`,
`Release verified site` checks out that exact commit, runs `make verify`, and
publishes a GitHub Release tagged `site-<full commit SHA>`. Each release contains:

- `site.tar.gz`: the complete static site, including its build record.
- `build.json`: the commit and every served file's SHA-256, also available separately.
- `SHA256SUMS`: checksums for the archive and build record.

The packager refuses changed, missing, extra or symlinked site files. Archive
metadata is fixed, so packaging the same build produces identical bytes. After
downloading all three files, run `sha256sum -c SHA256SUMS`, then extract with
`tar -xzf site.tar.gz -C <empty directory>`.

Vercel remains the only deployment path. No Vercel token or extra deployment is
needed. The release workflow uses only GitHub's built-in token, with write access
limited to its release job. Failed or cancelled live checks and non-main runs
cannot publish a release. This also covers auto-merge's explicit live-check
dispatch, not just ordinary pushes. Both entry points serialize releases by SHA,
so a legacy dispatch and a routine deployment cannot publish duplicate releases.

Assets upload to a draft before publication. Rerunning a failed release job
resumes its draft; an already published release stays unchanged. The daily live
check also retries a missing release. Releases are commit-addressed archives,
not a rolling “latest” release, and do not redeploy or roll back production.
Version tags (`v...`) remain owned by `Publish release notes`. Site archives never
claim latest or become the comparison boundary for version notes. See
[docs/releases.md](docs/releases.md) for the two release families.
To reproduce packaging locally after `make verify`:

```sh
.venv/bin/python scripts/package_release.py --commit "$(git rev-parse HEAD)" --output /tmp/unpoliticalaf-release
```

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
