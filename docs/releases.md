# Release notes

The **Publish release notes** workflow creates a GitHub release whenever a tag
matching `v[0-9]*` is pushed. GitHub generates the notes from merged pull requests,
including contributor credits and a full comparison link. It explicitly selects
the newest published version release in the tag's ancestry, never a site archive
or draft. Stable checkpoints also exclude prereleases. If no eligible version
exists, notes list all merged main PRs whose merge commits belong to the tagged
history, including contributor credits and a full-history link. This initial list
is ungrouped; subsequent notes use the label categories below.
No Conventional Commit format, npm publication or extra service token is needed.

## Publish a release

After this workflow is merged into `main`:

1. Choose a checked commit on `main`. Confirm **Build and check** has passed for
   that exact commit before tagging it.
2. Use an unused version tag, such as `v1.0.0` for a stable release or
   `v1.1.0-rc.1` for a prerelease. For example, from a clean checkout:

   ```sh
   git fetch origin main --tags
   git tag -a v1.0.0 origin/main -m "Unpolitical v1.0.0"
   git push origin v1.0.0
   ```

3. Check **Actions → Publish release notes**, then the repository's **Releases**
   page. Tags containing `-` produce prereleases and are not marked latest.
   Stable releases explicitly become latest.

The tag must include the workflow (tag an updated `main`, not an older commit
from before it was added). Push it using your normal Git credentials: tags
pushed by another workflow's `GITHUB_TOKEN` do not trigger this workflow.
The notes publisher rejects tags outside `main` ancestry before any release
write, including retries of existing versions.
The workflow loads the notes helper from trusted `main`, not tag-provided code.

## Deployment archives are a separate namespace

| Tag | Meaning | Latest |
| --- | --- | --- |
| `site-<full 40-character SHA>` | Exact production-byte archive | Never |
| `v[0-9]*` | Deliberate version checkpoint and PR notes | Stable only |

Site archives never create version tags, shorten version notes or redeploy.
`scripts/package_release.py --site site --output /outside/site/release --commit <SHA>`
validates the complete `build.json` file inventory and production feature flags,
rejects missing, extra, changed, unsafe or symlink files, then emits deterministic
`site.tar.gz`, `build.json` and sorted `SHA256SUMS`. Tar ownership, mode and time
are normalized; gzip has no filename and a zero timestamp. Output must be outside
the site. The build record is packaged unchanged, not rewritten to claim checks.
With all three downloads alongside each other, use `sha256sum -c SHA256SUMS`.

The publisher interface is `bash scripts/publish_release.sh`, with `COMMIT`,
`GITHUB_REPOSITORY`, `LIVE_RUN` (the actual same-repository Actions run URL),
`RUNNER_TEMP` and `GITHUB_STEP_SUMMARY` supplied by its caller. Assets must be in
`$RUNNER_TEMP/release`; `PYTHON` may select the checked environment's interpreter.
`GITHUB_REPOSITORY` must be exactly `jnyross/unpoliticalaf`. GitHub API calls
explicitly target `github.com`; inherited host/repository routing, enterprise
tokens and HTTP debugging are removed. Each `gh` subprocess has a 60-second
timeout; CLI failures report only the exception type, never raw API output.
Intended local GitHub configuration and ordinary GitHub credentials are retained.
Only a reviewed gate may call it after independent exact-candidate/production
checks and a real live-byte comparison, serialized per SHA. Neither a manifest
nor a run-shaped URL independently proves those checks happened. The `contents: write`
release job pins every action to a reviewed commit SHA, checks out without
persisted credentials and installs Python packages only with
`make setup-release`: hash-checked wheels from `requirements-release.txt`,
which must cover exactly the `requirements-test.txt` pins. The release
automation remains disabled until explicitly reviewed activation; packaging and
this documentation do not authorize a release, schedule, tag or API write.

Publishing creates a draft first. Retries check the exact target commit and
existing tag (peeling annotated tags), download/hash every existing asset, and
upload only missing draft assets. Nothing is clobbered. Unexpected, duplicate,
corrupt or missing published assets fail closed; published releases are never
repaired or replaced. A conflicting draft target, moved tag or corrupt asset
requires investigation and intentional recovery, not blind retry. The final
draft must have all three matching assets before publication, with latest false.
The caller owns independent evidence/receipt binding and per-SHA concurrency;
release metadata alone is not deployment proof.
Before any publication API call, the publisher also opens the archive without
extracting files, verifies its exact complete manifest inventory, file hashes
and byte-identical `build.json`, and requires sorted, normalized tar/gzip bytes.
Links, duplicate/extra/missing members and changed metadata are rejected even
when someone regenerates the outer checksums.

## What goes into the notes

`.github/release.yml` groups pull requests by optional labels:

| Labels | Section |
| --- | --- |
| `enhancement`, `feature` | Features and improvements |
| `bug`, `fix` | Fixes |
| `documentation` | Documentation |
| `maintenance`, `dependencies`, `chore` | Maintenance and dependencies |
| Any other labels, or no label | Other changes |

No authors or labels are excluded. Use clear pull request titles because GitHub
uses those titles in the generated notes. Direct commits are not listed as pull
request entries, but remain visible through the full comparison link.

## Retry or edit

If a run fails, fix the reported cause and rerun it from Actions. Runs for the
same tag are serialized. If the release already exists, the workflow leaves
its notes and publication status unchanged, so a retry cannot overwrite manual
edits. API errors other than a missing release fail the run rather than being
treated as a missing release.

Maintainers can edit the release notes in GitHub after publication. Do not move
an existing release tag to a different commit; use a new version instead.

Release notes do not build the site, publish packages or change the existing
Vercel deployment process. A release tag is a documented checkpoint, not proof
that its commit is currently deployed.
