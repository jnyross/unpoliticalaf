# Automated PR reviews

`Automated code and security review` posts a GitHub **pull request review**, not
just a CI status. It runs when a non-draft PR opens, receives commits, reopens or
becomes ready. The review is attached to the exact head commit and includes inline
comments and a summary of the findings and coverage. Rerunning the same head/base
pair does not post duplicate reviews.

## What it reviews

- Ruff checks Python syntax, undefined names, invalid control flow and suspicious
  comparisons (`E9,F63,F7,F82`). Formatting and unused imports are not review noise.
- Bandit assesses medium/high-severity Python security issues with medium/high
  confidence, such as shell injection and unsafe deserialization.
- Tools inspect the full changed Python files, but only findings on added lines
  (including replacement lines) become comments. Deleted files are not scanned.
- A review with no findings states the exact coverage, not blanket approval.
  Non-Python-only changes explicitly receive no code/security assessment.

This supplements, and does not replace, `make verify`, accessibility checks or
independent human/model review. It cannot validate fiscal facts, provenance,
impartiality, business logic or non-Python code.

## Security and failure handling

The workflow uses `pull_request_target` so it can comment on fork PRs without
service credentials. **Never check out the PR head in this workflow.** Checkout
is pinned to the trusted base SHA with persisted credentials disabled. The base
supplies the script and pinned tool versions in `requirements-review.txt`.

PR Python blobs are fetched by immutable SHA through the authorized base
repository (not a private fork's API) and saved under numeric names in a
temporary directory. They are parsed as data, never imported or executed. No
project dependencies, PR configuration, hooks or tests run in this privileged job.
The analyzer subprocesses do not receive the GitHub token. `noqa` and `nosec`
comments cannot suppress this independent review. Only `contents: read` and
`pull-requests: write` permissions are granted; reviews use `COMMENT`, never
`APPROVE` or `REQUEST_CHANGES`.

Missing/truncated diffs, parse errors, tool/API failures and size limits fail the job
without posting a clean review. Limits are 100 changed Python files, 1 MB per
file and 5 MB total. Reviews show at most 50 findings, state any truncation, and
review again after another push. A newer head/base cancels or discards stale work.

## Testing and rollout

```sh
python -m pip install -r requirements-review.txt
python -m unittest discover -s tests -p 'test_review_pr.py' -v
python -m unittest discover -s tests -p 'review_pr_integration.py' -v
```

Unit tests mock GitHub writes. The explicit integration suite exercises actual
analyzers using safe fixtures and verifies PR code never executes. The existing
`make test` discovers the unit tests without installing review-only dependencies.
No GitHub credentials or paid review service are needed.

The workflow becomes active **after this change is merged**. As a trusted-base
workflow, it cannot review its own installation PR before then. On the next PR,
check the Reviews tab for a `github-actions[bot]` review attached to the head SHA,
including actual findings if present, rather than treating a green check as proof.
If no review appears, inspect this workflow's failed run. Repository Actions must
allow `GITHUB_TOKEN` to create PR reviews. Fork runs may also need a maintainer's
approval under the repository's Actions policy.
