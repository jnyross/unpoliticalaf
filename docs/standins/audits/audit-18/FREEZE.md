# Audit-18 frozen candidate

## Audited source and publication

- Frozen source C: `190fd460b8a8cd6ee8cf1c07db8f6e3924934ba8`.
- Frozen source tree: `ca9b264e2bf20f2b1baa31ecd1aec3c639476335`.
- PR: [#264](https://github.com/jnyross/unpoliticalaf/pull/264).
- Reviewed PR head and seal commit S:
  `eb34adec30b23aec739b90e61237cd2d51adc108`.
- Reviewed head tree: `ca9b264e2bf20f2b1baa31ecd1aec3c639476335`.
  `git diff --exit-code S C` is empty; merged and reviewed trees are equal.
- Merge: agent-managed `gh pr merge --merge --match-head-commit
  eb34adec30b23aec739b90e61237cd2d51adc108`,
  recorded at `2026-11-11T15:02:55Z`.
- Checker candidate: `f4b21597b549fcceb831363775bf0b0d1e6a2cf9`,
  tree `3556520cf9e4d6acda51cb02b03e84f9d17a558f`.

## Seal and production configuration

- Seal SHA-256:
  `6b564b59e64eb1d7a6534f30b577a3a1e868835381bbb002dc885666f9c0f9bc`.
- Committed hash file:
  `docs/standins/audits/audit-18/new-questions.sha256`.
- Writer prompt SHA-256:
  `2ee0472dd00c582542fd7d1ebdf869da8357eeb929d18e9d962fb4b81d985482`.
- Production `feature_flags`:
  `{"chart_interactions": true, "sticky_navigation": true}`.

Question pack is in private custody outside the repository; exact path is recorded only in mission handoffs.

## Build identity

Receipt paths below are relative to the private mission root.

- Pinned-stamp receipt:
  `runtime/publish-pinned-identity.OmqagBQI/receipt.json`.
- Both retained build manifests:
  `runtime/publish-pinned-identity.OmqagBQI/base-build.json` and
  `runtime/publish-pinned-identity.OmqagBQI/head-build.json`.
- Comparison:
  `runtime/publish-pinned-identity.OmqagBQI/comparison.json`.
  Production rebuilds of the checker source and S used the same
  `VERCEL_GIT_COMMIT_SHA=f4b21597b549fcceb831363775bf0b0d1e6a2cf9`.
  Their `files` maps and `feature_flags` are equal, with all 7920 manifest
  entries reconciled against each build's served files.
- Both pinned manifests also have equal `files` and `feature_flags` to the
  recorded checker delivery manifest:
  `evidence/publish-audit18/checker-candidate-build.json`;
  checker delivery receipt:
  `runtime/delivery-package.Q2xP0sbL/receipt.json`.
  The only checker-source-to-S source addition is the committed seal hash;
  site inputs are unchanged. The S-to-C relation is tree equality.
- Live identity uses the separate, same-C production rebuild:
  `runtime/live.HgBAjDSL/receipt.json` and
  `runtime/live.HgBAjDSL/command.log`.
  It verifies live commit C, production flags, manifest identity and every
  one of the 7920 listed served-file byte hashes. `build.json` itself is
  compared by commit, flags and files map, not by a raw byte hash.
  This exact completed publish receipt is reused, not a new reader build.
- Commit stamps affect generated page footers and `build.json`.
  No raw `build.json` byte/SHA equality or unpinned `files`-map equality is
  claimed across different commit stamps. The checker relation is the
  same-pinned-stamp files-and-flags result above; the live relation is the
  separate same-C production-byte verification.

## Gate, review, CI, deployment and cleanup receipts

- Publication record: `evidence/publish-audit18/publish-receipt.json`.
- Verify/quality: `runtime/final-gate.2jC07zww/receipt.json`.
- Analyzer, Node, workflow and container gates:
  `runtime/lockdown-final.lbuh8UTD/receipt.json`.
- Browser regressions:
  `runtime/publish-browser-regressions.3iBQTUtt/receipt.json`.
- Successful accessibility union:
  `runtime/final-union.Gg8TjlYM/receipt.json`, 3822 cases,
  zero unresolved gate problems; 40 moderate non-gating landmark warnings remain.
- Preserved failed canonical attempt:
  `runtime/final-canonical.VYLoNANw/receipt.json`, exit 2, not a pass.
  Partition exits before dispositions remain recorded in the publication record.
- Publish approval: `evidence/publish-audit18/review-approval.md`;
  pre-merge public readback:
  `evidence/publish-audit18/pr-premerge-body-readback.json`.
- CI: `evidence/publish-audit18/pr-ci-green.json`, 18/18 successful checks.
- Deployment: `evidence/publish-audit18/deployment-run-success.json`,
  `evidence/publish-audit18/deployment-success.log`, and
  [workflow 43044412747](https://github.com/jnyross/unpoliticalaf/actions/runs/43044412747).
- Live readback: `evidence/publish-audit18/live-observation-success.json`.
- Sandbox cleanup: `evidence/publish-audit18/cleanup-summary.json` and
  `evidence/publish-audit18/final-sandbox-inventory.json`;
  all 14 publication sandboxes deleted and absent.
- Independent freeze approval:
  `evidence/freeze-audit18/freeze-review.md`.

## Session exclusions and independent reviewers

- Writer: `dbcad005-fe56-4a4e-9945-fbb280b26a78`.
- Checkers: `a837b505-6b89-41ee-ab49-f3bf1a0c13a1` and
  `58286ae0-23e8-4a03-a60f-f66b2a0d51fe`.
- Driver: `1b387d77-cb5d-45cc-9c32-df6fd033a3e7`.
- Probe: `9f19c860-eaf6-46dd-8e8f-baab2ab486bf`.
- Additional conservative lineage exclusion: session prefix `41442637`.
- All the above are excluded from every later reader, screen-reader,
  informal-reader, fact-checker, critic, judge, assessor, review and fix role.
- Publish reviewer: `991195c5-5f7e-46fe-a2f0-5bb31d65150c`.
- Fresh independent freeze reviewer:
  `2cb3759f-d98e-4d75-b2d6-275eb0f91f65`.

## Formal post-freeze evidence

Formal post-freeze reports belong under `docs/standins/audits/audit-18/`
on the non-deploying `evidence/audit-18` branch. Every report must state the
audited source SHA C explicitly, separately from its evidence-branch commit.
Subsequent observation and assessment use frozen C without rebuilding, merging
or moving main; stop if C or the seal changes.
