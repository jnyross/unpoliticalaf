"""Which commit a build came from, so the live site can be matched to the code."""

import functools
import os
import subprocess

from .readers import ROOT


@functools.lru_cache(maxsize=None)
def commit() -> str:
    """Full commit hash of the source being built, or "unknown".

    Vercel builds without a .git folder but sets VERCEL_GIT_COMMIT_SHA.
    """
    sha = os.environ.get("VERCEL_GIT_COMMIT_SHA", "").strip()
    if not sha:
        try:
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            sha = ""
    return sha or "unknown"


def short() -> str:
    sha = commit()
    return sha if sha == "unknown" else sha[:7]
