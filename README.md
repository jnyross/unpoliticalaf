# UnpoliticalAF

A plain-English, impartial guide to UK public spending, taxes, borrowing, debt and
party proposals. The [product specification](docs/product-spec.md) is drawn from
the pinned original Un-political repository. This repository currently contains
the starter site; the [product epic](https://github.com/jnyross/unpoliticalaf/issues/2) tracks the full build and continuing 9.5/10 acceptance loop.

## Work and verification

```sh
make setup
make build
make verify
make smoke
```

The factory owns the dependency-ordered GitHub tickets, independent review,
credential-free checks and publication. Its model workers edit an isolated
checkout and return their work to the controller. Claude uses the existing
CLIProxy subscription route.

The live destination is https://unpoliticalaf.vercel.app . Vercel uses the
repository root, preset Other, install `make setup`, build `make build` and output
`site`. A live placeholder does not mean the fiscal product is finished.

## Pinned source material

The original repository at commit `8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713`
is read-only. `reference/un-political/` contains the selected reusable scripts,
asset, requirements and human-check protocols. `data/raw/` and `data/sources.json`
contain its licensed source-data seed. `reference/un-political/SOURCE.json` records
the original paths and SHA-256 hashes. The first product ticket ports and verifies
these materials while preserving this project's factory contract.

Do not copy old factory code, credentials, deployment state or agent policies.
The source site's historical scores do not establish this site's score. Human
acceptance, public-source publication and funding/reporting decisions have separate
tickets; their results must never be invented. The repository remains private.
