# Expanded accessibility checks

Run project commands only in the approved credential-free Boat environment.
Build the actual committed candidate with `VERCEL_GIT_COMMIT_SHA` set to its SHA
and `make production-build`. Keep that build unchanged during inspection.

`make a11y` retains the existing default-state, phone-length and 24px target
checks, then scans **every manifest HTML path**, including redirect entries and
figure pages, at 360px and 1100px with all nested disclosures open. It adds no
global 44px or 16px requirement; the recorded T128 trade-off remains unchanged.
Subsequent main-frame navigation is blocked so an entry cannot silently scan
its redirect destination. Each result records the axe version and actual
`target-size` execution outcome; full pass-node lists are not retained.

## Bounded partitions

Each direct partition and union command first runs the existing independent
source/page checker. Its stated annual/pair/span population and internal links
catch required routes absent from both manifest and disk, including linked
figure pages. The axe checker additionally reconciles all manifest HTML routes
and hashes with disk. A deleted route cannot disappear into a smaller green
scan merely by removing its manifest entry.

For eight bounded runs, use distinct output names and indexes 0 through 7:

```sh
make a11y-default
make a11y-partition A11Y_ARGS="--partition-index 0 --partition-count 8 --output /home/user/runtime/partition-0.json"
# Repeat for indexes 1 through 7, preserving each result even when exit is 1.
make a11y-union A11Y_ARGS="--verify /home/user/runtime/partition-*.json"
```

The per-case wall-clock deadline defaults to 60 seconds (`--timeout` changes
that bound). Evidence is saved after every completed case. The union requires
all assigned cases exactly once, at the required widths/state, on the identical
build manifest. Missing reports, duplicate cases, altered bytes, timed-out
cases, violations and unresolved relevant incomplete findings fail.

PR CI runs eight fail-fast-disabled partitions with 60-minute job bounds and
always uploads available reports. Its final `accessibility` job independently
rebuilds the same production candidate and verifies their exact union. CI
requires no unresolved relevant incompletes; failed/missing matrix work cannot
be replaced by a successful aggregate.

## Rendered incomplete dispositions outside the deployed source

Incomplete findings are **not passes**. Inspect their actual rendered nodes,
backgrounds, states and widths using agent-browser. Equivalent findings may
share a justified template/cause assessment, but enumerate the complete
affected population and retain the rendered evidence. Do not label agent
inspection as real-device or human screen-reader evidence.

For an unchanged candidate, keep dispositions and inspection artifacts in the
private runtime evidence directory or the approved non-deploying evidence
branch. Do not commit a new build-manifest digest into the deploying source:
that would create a new candidate and a digest loop.

Supply a JSON file shaped like:

```json
{
  "manifest_sha256": "<SHA-256 of the exact site/build.json bytes>",
  "findings": [
    {
      "finding_sha256": "<builder.a11y.finding_digest of the full incomplete rule object>",
      "cases": [{"path": "life/compare/2011-2019.html", "width": 360}],
      "reason": "<actual rendered assessment and shared-cause justification>",
      "evidence": "<retained rendered inspection artifact reference>"
    }
  ]
}
```

Different full finding objects need separate entries; entries may reference the
same justified inspection. Then run:

```sh
make a11y-union A11Y_ARGS="--verify /home/user/runtime/partition-*.json --dispositions /home/user/runtime/rendered-reviews.json"
```

A disposition only resolves its exact incomplete finding/cases on that manifest.
It cannot waive violations, scan errors or population gaps. Any source/render
change requires a new build, scan population and applicable rendered assessment.
