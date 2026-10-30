# UnpoliticalAF

A plain-English guide to UK public spending, with cash, inflation-adjusted and
GDP-share views, spending by area, quick answers, long-run comparisons, source
notes and methods. Core text and tables work without JavaScript; JavaScript
adds view buttons and source pop-ups. Taxes and party proposals remain later
product tickets in [the specification](docs/product-spec.md).

## Build and check

Use Python 3.10+ in the controller's credential-free Linux check environment.
The three required libraries are version-pinned in requirements.txt. The smoke
gate also needs an installed Chrome or Chromium executable; it fails if the
browser or bundled axe-core is unavailable. No browser is downloaded by a check.

```sh
make setup
make build
make verify
make smoke
```

The npm scripts delegate to the same Make targets. There are no npm packages.
Builds and checks use retained files, without fetching data. Setup installs the
pinned Python libraries through the check environment's package mechanism.

- `make build` validates seed hashes, reads workbooks, reconciles totals and
  renders every output. It finishes source validation and rendering before
  changing public files.
- `make verify` independently reopens source cells, checks displayed figures,
  JSON values, sums, neutral wording, palette and reading grade. It compares
  two complete regenerated payloads with the existing output, then runs
  product and publication-boundary tests. Stale output fails.
- `make smoke` serves only the generated site on loopback, checks bytes, MIME
  types and private-path 404s, then audits every page at 360px and 1100px with
  bundled axe-core, including expanded tables and contrast. It also exercises the view controls\n  and core content with JavaScript disabled.
- `make a11y` runs the browser accessibility gate separately.

These commands must pass on the exact candidate through the factory controller.
This port's file edits are not evidence of a passing run, independent review or
live deployment. Manual keyboard and screen-reader checks and human studies
remain pending until actually observed.

## Public and generated files

The only public outputs are:

```text
site/index.html
site/methods.html
site/icon.svg
site/data/spending.json
```

`data/spending.json` is the generated working dataset; the public JSON must be
byte-identical. Both are rebuilt from the seed. `site/` remains generated under
the existing repository contract. The controller generates these artifacts;
do not type in fiscal values or copy a historical site's output. The old
baseline's `styles.css` is removed on a successful rebuild. Unknown files or
symlinks in an output directory stop the build without deleting them.

The builder supports `python3 scripts/build.py --output /tmp/public-preview`.
Inside this repository only `site/` is a valid output directory. It does not
publish the checkout, source workbooks, operational files or private state.
The old `static/` placeholder is not a build input.

`data/raw/` and `data/sources.json` are immutable seeded inputs. A missing or
changed source hash fails closed. Null and dash-marked missing values are not
invented as zero; a missing operand needed for reconciliation stops the build.
The controller must investigate such a failure against retained source notes.
`data/corrections.json` is an append-only editorial log, initially empty for
this site. New entries use date, page, what was wrong and what changed.

## Sources, reuse and limitations

Product code and the icon derive from
[jnyross/un-political at 8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713](https://github.com/jnyross/un-political/tree/8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713).
[Port notes](docs/spending-port.md) record file hashes, adaptations and remaining
verification. The selected source snapshot and its manifest are read-only.
No old factory, CI, agent policies, credentials or deployment bindings are ported.

Fiscal data comes from HM Treasury PESA and OBR publications named in the
retained source catalogue and on the methods page. Contains public sector
information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
Each sourced figure carries the sheet and cell reference; calculated shares and
changes retain both operands. The download retains publication dates and hashes.

PESA outturns, forecasts and OBR historical vintages must be read separately.
The March 2026 forecast note applies to the PESA aggregate forecast, not the
October 2026 OBR databank. The port does not assert a checked actual/estimate
classification for every OBR historical cell. Definition breaks and missing
values stay visible. No next release date is recorded by this port.

The repository remains private. Historical scores from the original product
are not scores or new verification results for this site. Public reporting,
funding evidence, human acceptance and later product requirements have their
own tickets. Do not invent their results.

The factory controller owns Git, independent review, exact-candidate checks and
publication to https://unpoliticalaf.vercel.app . Workers return file edits only.

`make setup` creates the local `.venv` and installs dependencies there. Build and check commands use that environment, leaving system Python unchanged.
