# Feature flags and safe rollouts

This static site uses a custom build-time feature-flag system, registered in
`builder/feature_flags.py`. It controls optional enhancements, never source
verification, factual content, accessibility checks or core no-JavaScript access.

| Flag | Default | What disabling it does |
| --- | --- | --- |
| `chart_interactions` | `true` | Omits tap, hover and keyboard readout JavaScript. Static charts, summaries, tables and CSV links remain. |
| `sticky_navigation` | `true` | Omits sticky-header activation. The normal header and “Top and menu” link remain. |

These two features already shipped, so their defaults preserve existing behaviour.
New `FeatureFlag` entries default to `false`; enable new work deliberately after
review. Use `feature_flags.enabled("registered_name")` at its rendering boundary,
and test both paths. Unknown names raise an error, rather than silently enabling
or hiding mistyped features.

## Configure and verify

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
Unset the variable or use `{}` to select defaults. Configuration is not read from
`.env` files. The normal setup/build/check/test commands are unchanged.

## Roll out and roll back

1. Add a new flag with its default off and tests for enabled and disabled output.
2. Build and check the enabled version locally with the override. GitHub Actions
   runs `make verify` with defaults and with both existing enhancements disabled;
   extend that matrix when adding a new flag.
3. Keep production off while the enabled candidate is reviewed and checked.
   If a deployment operator sets overrides, scope them separately to each
   environment. Branch deployments remain disabled by `vercel.json`; a flag
   does not create a preview deployment or bypass the existing release controller.
4. Enable production only through the normal reviewed release process. To roll
   back an enhancement, set its override to `false`, rebuild, check and deploy
   through that same process. Setting a variable alone does not change served files.

Flags affect every visitor to a given built artifact. This is environment-scoped
rollout, not percentage targeting or a runtime kill switch. Do not use flags as
authorization: all generated output is public site content. No secrets belong in
flag names or values.

`site/build.json` records effective `feature_flags` alongside the source commit
and file hashes, without timestamps. Identical source and settings produce the
same output. `make live` must use the same overrides as the deployed build; it
checks both the flag snapshot and the generated file hashes.

Remove a temporary flag and its override from every environment once the rollout
is complete and the fallback is no longer needed.
