# Automated PR reviews

The implementation is **held, not active**. Its manual-only workflow has a hard
`false` job guard. Merging this change does not activate a privileged job or a
schedule. Designated qualification must independently review the exact candidate
and intentionally remove that guard before any bounded validation dispatch.

When intentionally enabled, `Automated code and security review` posts a GitHub
**pull request review**, not just a CI status. Dispatch specifies `pr_number`
and `expected_head_sha`. Only the main workflow ref is eligible. A result is
attached to that exact current head, with inline findings and an explicit scope.

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
independent agent review. It cannot validate fiscal facts, provenance,
impartiality, business logic or non-Python code.

## Security and failure handling

**Never check out the PR head in this workflow.** The manual workflow checks out
its immutable trusted-main `github.sha`, with persisted credentials disabled.
That trusted snapshot supplies the script and direct analyzer pins in
`requirements-review.txt` (Ruff 0.14.3, Bandit 1.8.6). No PR dependencies install.
Analyzers install as binary packages in a trusted Docker image before the
token-bearing step. The minimal build context contains only trusted requirements.
Publication pins the resulting immutable image ID. Transitive
packages use their upstream dependency constraints, not a fully hash-locked
supply-chain attestation. The Python base tag is mutable at image-build time;
the completed image is immutable for the scan. The credentialed parent runs with `python -I -S`,
loading only stdlib, never analyzer site packages or startup hooks. Analyzer
containers have their own PID namespace, no network, no capabilities, no privilege
escalation, a read-only root/input mount and no host credential/Docker socket
mounts. They run as the runner UID with bounded memory/processes and temporary
scratch space. Scrubbing an environment alone would not isolate the parent's
token from `/proc`; the container boundary is required by the credentialed CLI.
Container/host-kernel compromise is not covered by these static checks.

PR Python blobs are fetched by immutable SHA through the authorized base
repository (not a private fork's API) and saved under numeric names in a
temporary directory. They are parsed as data, never imported or executed. No
project dependencies, PR configuration, hooks or tests run in this privileged job.
The analyzer subprocesses run with `-I`, explicit UTF-8 decoding and an allowlisted
environment without GitHub tokens, Python paths or inherited credentials. `noqa` and `nosec`
comments cannot suppress this independent review. Only `contents: read` and
`pull-requests: write` permissions are granted; reviews use `COMMENT`, never
`APPROVE` or `REQUEST_CHANGES`.

Missing/truncated diffs, parse errors, tool/API failures and size limits fail the job
without posting a clean review. Limits are 100 changed Python files, 1 MB per
file and 5 MB total. Each analyzer has a 120-second timeout. Reviews show at most
50 findings and state truncation. Timed-out containers receive a bounded forced
removal attempt by their unique generated name; runner/Boat teardown is the final
cleanup boundary if Docker itself fails. Untrusted fields are literal `<code>` content:
punctuation becomes whole numeric entities; control, bidi and invisible separators
become visible Unicode escapes. Each field has a 350-byte encoded budget including
wrapper/ellipsis; whole Unicode code points/entities/escapes are never sliced.
Summary and inline bodies are checked against a conservative 65,000-byte bound.
API paths/added-line anchors remain the original values, not display escapes.

All dispatches serialize by repository/PR with `cancel-in-progress: false`.
After scanning and building the payload, the publisher re-lists reviews for the
exact bot marker, then fetches current open/non-draft/head/base state immediately
before POST. Closed, draft or changed pairs are discarded. Serialized same-pair
reruns see the published marker and skip. Never introduce another publisher or
cancel/retry an ambiguous in-flight POST: GitHub has no atomic compare-and-post
review API, and state can still change between the last GET and POST. A POST
failure (including 422) fails, never masquerades as dedup success. Do not blindly
retry it; inspect actual reviews first. This is not a transactional state lock.

## Testing and rollout

```sh
make setup-test
python3 -m venv /tmp/review-analyzers
/tmp/review-analyzers/bin/python -m pip install --only-binary=:all: -r requirements-review.txt
.venv/bin/python -m pytest tests/test_review_pr.py
REVIEW_ANALYZER_PYTHON=/tmp/review-analyzers/bin/python .venv/bin/python -m pytest tests/review_pr_integration.py
```

Unit tests mock GitHub writes. The explicit integration suite exercises actual
analyzers using safe fixtures and verifies PR code never executes. The existing
`make test` discovers the unit tests without installing review-only dependencies.
Run these inside credential-free Boat, never on the agent host. The direct-tool
integration above skips the container-specific probe. To include it and test the
production analyzer route, build the trusted image from a temporary context with
only `requirements-review.txt`, using `config/review-analyzers.Dockerfile` and
`docker build --iidfile`; pass that image ID as `REVIEW_ANALYZER_IMAGE` alongside
the interpreter variable (used only for the local Markdown renderer). No GitHub
credentials or paid review service are needed. The explicit integration includes
real tools, nonexecution sentinels, configuration isolation and CommonMark
rendering/DOM inspection. Local rendering is not actual GitHub display evidence.

The repair alone claims no live bot integration. After independent review and
intentional activation, qualification dispatches one harmless validation PR at
its observed head, inspects the real `github-actions[bot]` COMMENT, path/line and
literal rendering, then reruns the same pair and confirms the count is unchanged.
Keep the main-only guard, serialization and trusted snapshot checkout intact.
Event triggers require a separate reviewed change with equivalent serialization
and immutable trusted-base checkout, not merely adding `pull_request_target` to
this dispatch-specific schema. No schedule is authorized. Repository Actions must
allow `GITHUB_TOKEN` to create PR reviews. Green/skipped checks alone prove no
publication, and COMMENT never supplies independent approval.
