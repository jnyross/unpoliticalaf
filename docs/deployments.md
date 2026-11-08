# Verified production deployment receipts

`scripts/record_deployment.py` retains GitHub deployment evidence for an
**already successful Vercel deployment**. It does not deploy to Vercel. This
integrates the receipt and history intent of PR #240, pinned at
`b06d95990fc8987f8666f7f4d6f39a05d627553c`; its tests are retained and extended in
`tests/test_deployments.py`. Adding this tool does not activate any workflow,
schedule, auto-merge or source writer. No historical cadence is asserted here.

## Preconditions and checks

After reviewed intentional workflow activation, a serialized receipt-writing
job must:

1. Check out the exact committed candidate, reachable from `main` in
   `jnyross/unpoliticalaf`. Supply its SHA as `GITHUB_SHA` and use the normal
   GitHub run/ref/repository/event variables.
2. Set up the repository's pinned Python environment and run
   `make production-build`, not the ordinary build. Git-free rebuilds must set
   `VERCEL_GIT_COMMIT_SHA` to the same candidate. The build and production
   feature-flag configuration must come from that candidate.
3. Invoke `.venv/bin/python scripts/record_deployment.py --wait 1500`.
   Recording has GitHub API side effects; do not run this command as a local
   test or inside credential-free Boat checks.

The CLI checks GitHub's run evidence (requested run ID, both repository and
head-repository full names, exact SHA, main branch, trigger and workflow path)
rather than trusting a main-ref environment label alone. Only
`.github/workflows/deploy.yml` and `.github/workflows/live.yml` are accepted. A
`workflow_run` trigger also requires `action: completed`, successful completed
upstream run evidence in the event file, and a separate API confirmation of
that upstream run, including its requested ID and allowed workflow path.
The current recording job itself need not be complete.
The checked-out/build SHA must match the run evidence; stale or mismatched
candidates fail closed rather than silently substituting a different SHA.
Push, manual dispatch and reusable-workflow triggers on main are supported;
schedules and other triggers are refused. Workflow YAML guards are not a
substitute for these CLI checks.

The latest `Vercel` commit status is selected from paginated status history for
the exact SHA. Pending, failed or missing latest evidence cannot inherit an
older success. A successful status must be authored by `vercel[bot]`
(ID `35613825`, type `Bot`), with a timezone-aware provider timestamp and an
HTTPS URL under
`vercel.com/johns-projects-d6b53aae/unpoliticalaf/<deployment-id>`.
An identically named context from another creator or another project is refused.

The CLI invokes the existing `check_live` verifier with the fixed production
URL `https://unpoliticalaf.vercel.app/` and the local `site` directory. That
verifier requires the reviewed current production feature flags and checks
the manifest and every served file. The recorder additionally checks the
**raw live `build.json` bytes** against the unchanged local file and rechecks
the provider status before writing. No arbitrary URL or branch CLI argument
is accepted.

## Receipt identity and recovery

The deployment uses `environment: verified-site-receipts`, `task: deploy`, the
exact SHA, `production_environment: false`, `transient_environment: false`,
`auto_merge: false` and no requested status-context override. Each success
status sets `auto_inactive: false`. GitHub environment names are
case-insensitive and Vercel's GitHub integration may record `Production` or
`Preview` deployments, so receipts use their own environment and never mark any
other deployment inactive. The receipt jobs declare no workflow `environment:`,
so Actions adds no deployment record of its own. Records in any other
environment are never receipts. The first receipt makes GitHub create the
`verified-site-receipts` environment with no protection rules; that is
expected, and adding rules there would be a separate reviewed activation
decision. Its payload is:

| Field | Evidence |
| --- | --- |
| `source` | `verified-vercel-deployment` |
| `provider_url` | Original successful Vercel status target URL |
| `deployed_at` | Original provider status `created_at`, not recording time |
| `recording_run` | Original GitHub Actions run URL |
| `build_sha256` | SHA-256 of verified raw `site/build.json` bytes |

Release tooling can match `build_sha256` against the production archive's
`build.json`. A matching commit alone does not prove identical release bytes.

Reruns find receipts by **SHA + provider URL + provider timestamp + build
digest**. An earlier valid success still counts after becoming inactive, and
does not produce another receipt. If a run stopped between receipt creation
and its success status, a fresh successful verification can finish that same
receipt. Recovery preserves the original immutable payload, including its
provider timestamp/URL and original `recording_run`. The new success status's
`log_url` identifies the recovery verification run. A different provider event
or different build gets a separate receipt; old evidence is never relabelled.

Each freshly verified recording run needs its own trusted success status whose
`log_url` is that exact run URL, so release evidence can bind to the upstream
run ID. Reusing an already successful receipt appends one such status when
missing, without duplicating the receipt or changing its original payload.
Repeating the same run does not append another identical proof status.
The `record()` return boolean means **receipt created**, not status appended:
both recovery and fresh proof on a reused receipt return `False`.

The caller must serialize receipt writes, for example through one shared
workflow concurrency group with cancellation disabled. GitHub's deployment API
does not offer an atomic create-if-absent operation. If a write response is
lost, rerun verification and look up the receipt; do not invent a successful
status. Recovery is idempotent under this serialization requirement, not a
claim of transactional cross-job writes.

## Trust, bounds and reporting

The client pins `gh api --hostname github.com` and the approved repository,
allowlists API paths, removes foreign-host/debug environment overrides, uses a
60-second subprocess timeout, and never prints raw command output or tokens
on failure. Use only the existing workflow token and its intentionally
reviewed permissions: contents/statuses/actions read and deployments write.
The writing job installs only the hash-checked wheel closure in
`requirements-release.txt` (`make setup-release`), and its actions are pinned
to reviewed commit SHAs. `live.yml` calls `deploy.yml` with deployments write
for that job, so the read-only `live` job narrows its own token to contents
read before its ordinary unhashed `make setup`.
No Vercel API write, new credential, provider or endpoint configuration is
needed. A local read-only report may use the existing authenticated `gh` CLI.

Provider URLs reject credentials, ports, fragments, queries and malformed
paths. Recording and status log URLs must name an Actions run in this
repository. Pagination is 100 items per page, at most 100 pages per traversal;
reaching the limit fails closed instead of presenting a partial report as a
complete history. The provider wait argument is bounded to 0–1800 seconds.

The payload marker is **not an authentication or security boundary**. Anyone
with the same repository/token write authority can forge evidence. Receipt
schema and success provenance are validated before reuse/counting. Both the
receipt creator and each counted success status creator must be
`github-actions[bot]` (ID `41898282`, type `Bot`); malformed
records are skipped and marked invalid receipts are reported. Legacy records
without a build digest cannot establish current byte-verified evidence.

For a read-only report:

```sh
.venv/bin/python scripts/record_deployment.py --report
```

The report counts distinct successful committed SHAs in each of four rolling
seven-day windows using provider timestamps. It does not count daily checks,
reruns, incomplete receipts, future timestamps or absent history as shipping.
The target of at least two commits per week is a target, not a demonstrated
cadence. Old missing observations remain missing. A report API failure fails
the read-only command; a failure after a successful receipt write instead
preserves that success and explicitly reports frequency as unavailable,
without fabricated zero counts.

## Validation

Unit coverage includes provider failures, exact-SHA/ref/build checks,
idempotence, recovery, timestamp windows, pagination, malformed history,
endpoint/token-routing restrictions, creator/project spoofing, current-run
proof status deduplication, completed-run ID/repository/path CLI guards, raw
manifest bytes and report failure after a successful receipt.

Run the regression suite in credential-free Boat, not on the agent host.
Synthetic fixtures are not production receipts. Exact-candidate CI and actual
provider/API observation belong to reviewed qualification. No successful
production receipt or deployment frequency is claimed by this document.

The canonical writer in `deploy.yml` and downstream site archive workflow are
gated by `vars.REVIEWED_PRODUCTION_DELIVERY == 'true'`. This integration does not
set that variable or authorize its activation. The legacy `live.yml` dispatch
delegates to the same verifier; no daily schedule is introduced or restored.
