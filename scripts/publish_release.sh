#!/usr/bin/env bash
# Called only by the gated release job, after make verify and packaging.
set -euo pipefail

: "${COMMIT:?}" "${LIVE_RUN:?}" "${RUNNER_TEMP:?}" "${GITHUB_STEP_SUMMARY:?}"
tag="site-$COMMIT"
if draft=$(gh release view "$tag" --json isDraft --jq '.isDraft'); then
  if [ "$draft" = false ]; then
    echo "Release $tag is already published; leaving it unchanged."
    exit 0
  fi
else
  printf 'Site built from commit `%s`.\n\nLive files verified byte for byte: %s\n\nDownload `site.tar.gz` and `SHA256SUMS`, then run `sha256sum -c SHA256SUMS` with `build.json` alongside them.\n' \
    "$COMMIT" "$LIVE_RUN" > "$RUNNER_TEMP/release-notes.md"
  gh release create "$tag" --draft --target "$COMMIT" \
    --title "Site ${COMMIT:0:7}" --notes-file "$RUNNER_TEMP/release-notes.md"
fi
gh release upload "$tag" "$RUNNER_TEMP/release/site.tar.gz" \
  "$RUNNER_TEMP/release/build.json" "$RUNNER_TEMP/release/SHA256SUMS" --clobber
# Commit-addressed releases are an archive, not a rolling "latest" tag.
# An older successful live run must not replace a newer latest release.
gh release edit "$tag" --draft=false --latest=false
gh release view "$tag" --json url --jq '.url' >> "$GITHUB_STEP_SUMMARY"
