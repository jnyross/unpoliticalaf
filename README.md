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

## Environment variables and local setup

**No environment variables, API keys or secrets are required** to build, check,
test or serve the site locally. There is no `.env` file to create or copy, and
the build does not load `.env` files. The site is static: it needs no database,
backend service or Vercel account for local development.

Install Python 3.10 or later (including `venv`) and Make, then run `make setup`
and `make verify` from the repository root. Setup installs the pinned packages
in `requirements.txt` into `.venv`; subsequent build, check and test commands use
that interpreter without needing to activate it.

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

After `make build`, preview the generated files at `http://127.0.0.1:8000`:

```sh
.venv/bin/python -m http.server 8000 --bind 127.0.0.1 --directory site
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
make verify    # build + check + test
make setup-dev && make a11y   # axe accessibility checks at 360px and 1100px
```

### Dev container

With Docker and VS Code's Dev Containers extension installed, open this repository
and choose **Dev Containers: Reopen in Container**. The container uses Python 3.12
(matching CI), runs as the non-root `vscode` user, and selects `.venv/bin/python`
for editing and unittest discovery. On creation it runs `make setup-dev` and
installs Playwright's Chromium browser and Linux dependencies, so the first setup
needs network access. No API keys or deployment credentials are needed.

The container's `.venv` uses a dedicated Docker volume for each dev container,
not the host virtualenv. Existing host virtualenv files (including macOS Python
symlinks) are neither copied into the volume nor modified. Rebuilds reuse the
container volume and rerun setup. Docker may create an empty `.venv` mount-point
directory on a fresh host checkout.

Once setup finishes, run `make verify` and `make a11y` in the container terminal.
To preview the generated site, run
`.venv/bin/python -m http.server 8000 --bind 0.0.0.0 --directory site`
and open the forwarded port 8000. Stop the preview with Ctrl+C. After changing the
container configuration or dependency files, rebuild the container to rerun setup.

### Local unit tests

From a fresh checkout, run `make setup-test && make build && make test`.
Build first because some tests read the generated pages and data in `site/`.
Setup needs network access to install the pinned dependencies into `.venv`;
it does not change your system Python. The tests use `unittest`, and pytest
can collect the same tests without running them:

```sh
.venv/bin/python -m pytest --collect-only tests/test_household_shares.py
```

Use `.venv/bin/python`, not an unconfigured system `python3`, for pytest commands.
Alternatively, activate the environment with `. .venv/bin/activate` before
running `python -m pytest --collect-only tests/test_household_shares.py`.
`make setup-dev` includes the test dependencies as well as the optional browser
tools. Production deployments still use `make setup`, without either set of tools.
CI checks the lightweight test setup, bounded pytest collection and `make verify`.

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

This check does not modify protected instructions or certify acceptance-policy
alignment. The v1 target paragraph still awaits the supported operator route in
[issue #56](https://github.com/jnyross/unpoliticalaf/issues/56); the current
product target is defined in `docs/product-spec.md`.

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
