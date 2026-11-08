# Feature flags and safe rollouts

This static site uses a custom build-time feature-flag system, registered in
`builder/feature_flags.py`. It controls optional enhancements, never source
verification, factual content, accessibility checks or core no-JavaScript access.

| Flag | Default | What disabling it does |
| --- | --- | --- |
| `chart_interactions` | `true` | Omits tap, hover and keyboard readout JavaScript. Static charts, summaries, tables and CSV links remain. |
| `sticky_navigation` | `true` | Omits sticky-header activation. The normal header and “Top and menu” link remain. |

These two features already shipped, so their defaults preserve existing behaviour.
New `FeatureFlag` entries default to `false` for local builds; production must
explicitly name every flag. `builder.build` resolves one immutable snapshot.
It passes that snapshot to the pure `builder.html.apply_feature_flags` helper,
which reads no environment or files, and to the manifest writer. The narrow
HTML-to-flag-validation import is allowed by the architecture contracts; flag
configuration itself has no builder dependencies. Test both enabled and disabled output.

## One reviewed production configuration

`config/feature-flags.production.json` is the sole production source of truth.
It is checked into Git, must contain every registered flag as a JSON boolean,
and initially preserves both already-shipped enhancements. Change this file in
a reviewed PR to roll out or roll back a feature.

All production entry points read that same local file:

- Vercel's `buildCommand` runs `make production-build`.
- `.github/workflows/live.yml` rebuilds with `make production-build`.
- `make live` also depends on `production-build` before comparing served files.

Deployment verification, metrics collection and release packaging must reuse
`production-build`, never rebuild from remote flags or ordinary local defaults.
Those integrations are delivered separately; this change does not activate them.
Run the live verifier with `.venv/bin/python` so later metrics imports use the
same installed production dependencies.

`production-build` runs `python -m builder.build --production`. It rejects
`UNPOLITICAL_FEATURE_FLAGS` if present, even if empty or `{}`. Do not configure
that variable in Vercel; remove any prior Vercel-only override before activating
this build command. Missing, incomplete or invalid production files fail before
existing output is replaced. There is no silent fallback to defaults.

```sh
make production-build   # build the reviewed production settings
make production-verify  # same build, then source/page checks and unit tests
make live               # same build, then compare against the live site
```

The live verifier gets expected flags and hashes from the independently rebuilt
local artifact. It never adopts settings or expected hashes from the remote
manifest. A remote deployment with different flags fails, even at the same
commit; lying about its flags cannot make different served bytes pass.
The verifier also rejects a local artifact whose complete boolean flag snapshot
does not match the checked-in production configuration, before any HTTP request.

## Local experiments

`UNPOLITICAL_FEATURE_FLAGS` is a JSON object of **boolean** overrides. Unspecified
flags keep their registered defaults. For example:

```sh
make setup
UNPOLITICAL_FEATURE_FLAGS='{"chart_interactions":false}' make verify
UNPOLITICAL_FEATURE_FLAGS='{"chart_interactions":false,"sticky_navigation":false}' make verify
make verify  # defaults, if the variable is not exported in your shell
```

Invalid JSON, unknown flags, duplicate keys, strings such as `"false"`, numbers
and an explicitly empty value stop the build before existing output is replaced.
Unset the variable or use `{}` to select local defaults. Configuration is not
read from `.env` files. `make build` and `make verify` remain local experiments;
they are not substitutes for the explicit production build.

## Roll out and roll back

1. Add a new flag with its default off and tests for enabled and disabled output.
2. Add its explicit production setting as `false` in the production file. Build
   and check the enabled version locally with an environment override.
3. GitHub Actions verifies all four boolean combinations, and the
   reviewed production configuration. The stable `check` job requires all flag
   configurations and its own default checks to pass. Extend the cases for new
   features; preserve the separate architecture job supplied by #253.
4. Enable production in the checked-in file only through the normal reviewed
   release process. To roll back, set its production value to `false`, rebuild,
   check and deploy through that same process. Branch deployments remain disabled
   by `vercel.json`; flags do not create previews or bypass reviewed PR delivery.

Flags affect every visitor to a given built artifact. This is environment-scoped
rollout, not percentage targeting or a runtime kill switch. Do not use flags as
authorization: all generated output is public site content. No secrets belong in
flag names or values.

`site/build.json` records effective `feature_flags` alongside the source commit
and file hashes, without timestamps. Identical source and settings produce the
same output. One immutable flag snapshot drives rendering and the manifest;
neither stage re-reads a potentially changed configuration. `make live` checks
both that snapshot and the generated file hashes.

Remove a temporary flag from the registry and production file, plus any local
overrides, once the rollout is complete and the fallback is no longer needed.
