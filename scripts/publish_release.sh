#!/usr/bin/env bash
# Only a reviewed, serialized caller with exact-candidate/live evidence may run.
set -euo pipefail
: "${COMMIT:?}" "${LIVE_RUN:?}" "${RUNNER_TEMP:?}" "${GITHUB_STEP_SUMMARY:?}" "${GITHUB_REPOSITORY:?}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python3}" "$script_dir/package_release.py" --publish
