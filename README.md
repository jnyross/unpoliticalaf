# UnpoliticalAF

A plain-English guide to UK public spending, taxes, receipts, borrowing and debt.
Spending has cash, inflation-adjusted and GDP-share views, area histories and
quick answers. Taxes has current OBR receipt groups, cash and published GDP-share
history, and separate forecasts. Core text, source details and tables work
without JavaScript. Who pays keeps HMRC Income Tax liability shares separate from
ONS household tax estimates, with income and expenditure denominators explained.
Party proposals remain a separate ticket in [the specification](docs/product-spec.md).

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
  bundled axe-core, including expanded tables and contrast. It also exercises the view controls
  and core content with JavaScript disabled.
- `make a11y` runs the browser accessibility gate separately.

These commands must pass on the exact candidate through the factory controller.
This port's file edits are not evidence of a passing run, independent review or
live deployment. Manual keyboard and screen-reader checks and human studies
remain pending until actually observed.

The recorded Vercel contract is repository root, preset **Other**, install
`make setup`, build `make build`, output `site`. This is the contract documented
in this repository's README at `3296b28ba01d89a5f1f9403b71f63e8c44a472e1`;
this recovery seed does not change bindings or independently recheck Vercel's
settings/build image. The controller owns that deployment check.

Readable source evidence for the spending recovery is in [data/audit](data/audit/README.md).
`make verify` reopens all selected raw cells with a reader separate from the
exporter, including labels, units, blanks, literal dashes and number formats.
The [original audit seed](docs/issue-4-recovery-seed.md) is historical preparation,
with its then-outstanding work preserved. The [fiscal schema](docs/fiscal-schema.md) describes the
recovery implementation, per-value records, source-specific rounding models,
explicit OBR status uncertainty, residuals, and #22's full-row/date repair.
The #21 worker edited source only; the controller generated the committed
artifacts in deployed `8e60e9e03707ec38cb274468306e95085bb0bee3` on
30 October 2026 (private receipts: `receipts/21/1793368898495164182/`).
Passing seed software checks does not complete #4/#20/#22: independent fiscal
and product review, official candidate gates and canonical live verification
remain the existing controller's responsibility.

## Public and generated files

The only public outputs are:

```text
site/index.html
site/methods.html
site/taxes.html
site/who-pays.html
site/icon.svg
site/data/spending.json
site/data/taxes.json
site/data/payers.json
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
invented as zero; a missing required PESA operand stops the build. Historical
identities with genuine source gaps are recorded as not testable with named
missing operands.
The controller must investigate such a failure against retained source notes.
The payer build also reads the seven retained official sources listed in
`data/payers/sources.json`. It publishes only 23 selected percentages and their
provenance, never the workbooks or full HTML responses. The independent payer
checker reopens those sources with a separate reader and pins their hashes.
See [payer methods](docs/payer-methods.md) for populations, scope and limitations.
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
The forecast date in PESA Table 4.1 notes B51/B52 applies to the PESA aggregate
forecast, not the separately vintaged OBR databank. The port does not assert a
checked actual/estimate classification for every OBR historical cell. Definition breaks and missing
values stay visible. No next release date is recorded by this port.

The repository remains private. Historical scores from the original product
are not scores or new verification results for this site. Public reporting,
funding evidence, human acceptance and later product requirements have their
own tickets. Do not invent their results.

The factory controller owns Git, independent review, exact-candidate checks and
publication to https://unpoliticalaf.vercel.app . Workers return file edits only.

`make setup` creates the local `.venv` and installs dependencies there. Build and check commands use that environment, leaving system Python unchanged.

Receipt evidence is separately scoped in
[data/audit/receipts](data/audit/receipts/README.md). The controller build now
creates the private `data/receipts.json` working dataset, with seven source
receipt/debt tables, original missingness and explicit reconciliation limits.
`make verify` independently reopens its raw workbooks and checks deterministic
regeneration, in addition to both audit scopes. See
[receipt methods](docs/receipts-methods.md) for the tax/non-tax residual formulas,
historical licence-fee overlap and debt/GDP limits. Only the selected CURRENT
tables enter `site/data/taxes.json`; the private receipt dataset is never published.
The explicit public allowlist has eight files. Tax output is checked by
`scripts/check_taxes.py`, which separately reopens the pinned current workbook
and binds every public node, signed rendered value and chart encoding to exact
cells, ordered formulas, units, years and status. This adds no historical receipt
splice or debt repair. Source edits are not a passing check, fiscal approval,
live deployment or completed issue #5/#26/#29 acceptance.

The private work-methods foundation reopens the six complete official HTML pages
registered in `data/life/work-methods-sources.json`. `make verify` checks stored
and recovered original bytes, then audits an in-memory definitions projection
with separate HTML locators. No derived file or public work story is produced.
The QMI, quality update and revision notices retain population, response, weight
and coding cautions; the LFS coding article is not proof of APS affected periods.
Confidence `20701` remains uninterpreted. Work counts and their catalogue history
need their own verified foundation before use. See
[the work-methods contract](docs/life-work-methods-source-contract.md).
This source foundation earns no v2 product score or human acceptance evidence.
