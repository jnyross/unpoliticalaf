# Release notes

The **Publish release notes** workflow creates a GitHub release whenever a tag
matching `v[0-9]*` is pushed. GitHub generates the notes from merged pull requests,
including contributor credits and a full comparison link. It explicitly selects
the most recently created published version release in the tag's ancestry as the
starting point, ignoring `site-<sha>` archives and drafts. Stable versions also
ignore prereleases. The first version lists merged `main` PRs across the tag's
full history, with contributor credits and a history link, even if site archives
already exist. This initial list is ungrouped; subsequent version notes use the
categories below.
No Conventional Commit format, npm publication or extra service token is needed.

## Deployment archives and version checkpoints

There are two disjoint release families:

| Tag | Trigger and owner | Meaning |
| --- | --- | --- |
| `site-<full SHA>` | Successful main verification, `Release verified site` | Byte-verified deployed snapshot with static archive and checksums; never marked latest |
| `v[0-9]*` | Explicit version-tag push, `Publish release notes` | Deliberate version checkpoint with release notes |

The site workflow accepts both `Verify and record production deployment`
(`deploy.yml`, the routine entry point after the deployment-recording change) and
`Live site matches main` (`live.yml`, retained for legacy dispatches).
Only successful, same-repository `main` push/schedule/manual runs may publish.
Both names share a per-SHA concurrency key and the same `site-<sha>` tag:
rechecks or compatibility dispatches reuse a draft or leave a published archive
unchanged. They do not create version tags, publish version notes or redeploy.
Version publishing never modifies site archives, and explicitly choosing its
version-only history boundary prevents frequent snapshots from truncating notes.

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
   Stable releases use GitHub's version-based latest-release selection.

The tag must include the workflow (tag an updated `main`, not an older commit
from before it was added). Push it using your normal Git credentials: tags
pushed by another workflow's `GITHUB_TOKEN` do not trigger this workflow.

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
