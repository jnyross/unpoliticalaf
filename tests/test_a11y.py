"""The expanded axe population must be complete, reproducible and fail closed."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from builder import a11y


@pytest.fixture
def site(tmp_path):
    files = {}
    for name in ("index.html", "life/2026.html", "figures/example.html"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html><body>Example</body></html>")
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "build.json").write_text(json.dumps({"commit": "candidate", "files": files}))
    return tmp_path


def clean_scan(path, width):
    return {
        "violations": [],
        "incomplete": [],
        "axe_version": "test-engine",
        "target_size_outcome": "passes",
    }


def finding_scan(key, finding):
    response = clean_scan(None, None)
    response[key] = [finding]
    return response


def reports(site, count=2, scan=clean_scan):
    return [a11y.scan_partition(site, index, count, scan) for index in range(count)]


def test_partitions_cover_every_manifest_html_at_both_widths(site):
    evidence = reports(site, count=4)
    cases = [(case["path"], case["width"]) for part in evidence for case in part["results"]]
    assert len(cases) == len(set(cases)) == 6
    assert {width for _, width in cases} == {360, 1100}
    assert {path for path, _ in cases} == {"index.html", "life/2026.html", "figures/example.html"}
    assert a11y.verify_reports(site, evidence) == []


@pytest.mark.parametrize("mutation", ["missing", "extra", "changed"])
def test_manifest_and_disk_must_reconcile(site, mutation):
    if mutation == "missing":
        (site / "life/2026.html").unlink()
    elif mutation == "extra":
        (site / "unrecorded.html").write_text("extra")
    else:
        (site / "index.html").write_text("changed")
    with pytest.raises(ValueError):
        a11y.scan_partition(site, 0, 1, clean_scan)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "wrong_width", "wrong_manifest"])
def test_union_rejects_incomplete_duplicate_or_foreign_evidence(site, mutation):
    evidence = reports(site)
    if mutation == "missing":
        evidence[0]["results"].pop()
    elif mutation == "duplicate":
        evidence[0]["results"].append(evidence[0]["results"][0])
    elif mutation == "wrong_width":
        evidence[0]["results"][0]["width"] = 375
    else:
        evidence[0]["manifest_sha256"] = "another candidate"
    assert a11y.verify_reports(site, evidence)


def test_timeout_is_recorded_and_not_a_pass(site):
    def timeout(path, width):
        raise TimeoutError("bounded axe scan timed out")

    evidence = reports(site, scan=timeout)
    assert all(case["error"] for part in evidence for case in part["results"])
    assert a11y.verify_reports(site, evidence)


def test_incomplete_requires_exact_candidate_rendered_disposition(site):
    finding = {"id": "color-contrast", "tags": ["wcag2aa"], "nodes": [{"target": ["td"]}]}
    evidence = reports(site, scan=lambda path, width: finding_scan("incomplete", finding))
    assert a11y.verify_reports(site, evidence)
    disposition = {
        "manifest_sha256": evidence[0]["manifest_sha256"],
        "findings": [
            {
                "finding_sha256": a11y.finding_digest(finding),
                "cases": [
                    {"path": case["path"], "width": case["width"]}
                    for part in evidence
                    for case in part["results"]
                ],
                "reason": "Rendered inspection confirms this exact shared template cause.",
                "evidence": "rendered/contrast-inspection.json",
            }
        ],
    }
    assert a11y.verify_reports(site, evidence, disposition) == []
    disposition["manifest_sha256"] = "stale"
    assert a11y.verify_reports(site, evidence, disposition)


def test_wcag22_violation_cannot_be_dispositioned_as_incomplete(site):
    finding = {"id": "target-size", "tags": ["wcag22aa"], "nodes": []}
    evidence = reports(site, scan=lambda path, width: finding_scan("violations", finding))
    disposition = {
        "manifest_sha256": evidence[0]["manifest_sha256"],
        "findings": [
            {
                "finding_sha256": a11y.finding_digest(finding),
                "cases": [
                    {"path": case["path"], "width": case["width"]}
                    for part in evidence
                    for case in part["results"]
                ],
                "reason": "This must not waive a violation.",
                "evidence": "rendered/example.json",
            }
        ],
    }
    assert a11y.verify_reports(site, evidence, disposition)


@pytest.mark.parametrize("field", ["reason", "evidence"])
@pytest.mark.parametrize("value", [None, 42, True, [], {}, "   "])
def test_disposition_requires_nonempty_string_fields(site, field, value):
    evidence = reports(site)
    item = {
        "reason": "Rendered inspection",
        "evidence": "rendered/inspection.json",
        "finding_sha256": "example",
        "cases": [],
    }
    item[field] = value
    disposition = {
        "manifest_sha256": evidence[0]["manifest_sha256"],
        "findings": [item],
    }
    assert a11y.verify_reports(site, evidence, disposition)


@pytest.mark.parametrize("value", ["", "reviewed", 42, False, []])
def test_disposition_root_must_be_an_object(site, value):
    assert a11y.verify_reports(site, reports(site), value)


@pytest.mark.parametrize("value", [None, "reviewed", 42, []])
def test_disposition_entry_must_be_an_object(site, value):
    evidence = reports(site)
    disposition = {
        "manifest_sha256": evidence[0]["manifest_sha256"],
        "findings": [value],
    }
    assert a11y.verify_reports(site, evidence, disposition)


def test_bad_partition_is_rejected(site):
    for index, count in ((-1, 2), (2, 2), (0, 0)):
        with pytest.raises(ValueError):
            a11y.scan_partition(site, index, count, clean_scan)


def test_missing_axe_results_fail_closed(site):
    evidence = reports(site, scan=lambda path, width: {"violations": []})
    assert a11y.verify_reports(site, evidence)


def test_partition_cli_does_not_pass_incomplete(site, monkeypatch, tmp_path):
    finding = {"id": "color-contrast", "tags": ["wcag2aa"]}

    class IncompleteScanner:
        def __init__(self, *args):
            pass

        def __call__(self, path, width):
            return finding_scan("incomplete", finding)

        def close(self):
            pass

    monkeypatch.setattr(a11y, "BrowserScanner", IncompleteScanner)
    monkeypatch.setattr(a11y, "check_expected_routes", lambda site: None)
    assert (
        a11y.main(
            [
                "--site",
                str(site),
                "--partition-count",
                "2",
                "--output",
                str(tmp_path / "partition.json"),
            ]
        )
        == 1
    )


@pytest.mark.skipif(
    os.environ.get("RUN_A11Y_BROWSER_TESTS") != "1",
    reason="Explicit opt-in: installed Chromium is not a unit-test dependency",
)
def test_real_axe_sees_nested_disclosure_content(tmp_path):
    (tmp_path / "nested.html").write_text(
        '<!doctype html><html lang="en"><title>Nested disclosure regression</title>'
        "<body><main><h1>Example</h1><details><summary>Outer</summary>"
        "<details><summary>Inner</summary>"
        '<p id="faint" style="color:#aaa;background:#fff">Nested faint text</p>'
        "</details></details></main></body></html>"
    )
    scanner = a11y.BrowserScanner(tmp_path, 60)
    try:
        for width in a11y.WIDTHS:
            response = scanner("nested.html", width)
            contrast = [item for item in response["violations"] if item["id"] == "color-contrast"]
            assert any("#faint" in node["target"] for item in contrast for node in item["nodes"])
    finally:
        scanner.close()


@pytest.mark.skipif(
    os.environ.get("RUN_A11Y_BROWSER_TESTS") != "1",
    reason="Explicit opt-in: installed Chromium is not a unit-test dependency",
)
def test_hung_browser_is_bounded_and_next_case_can_run(tmp_path):
    (tmp_path / "hung.html").write_text("<script>while (true) {}</script>")
    (tmp_path / "healthy.html").write_text(
        '<!doctype html><html lang="en"><title>Healthy</title>'
        "<body><main><h1>Healthy</h1></main></body></html>"
    )
    scanner = a11y.BrowserScanner(tmp_path, 3)
    try:
        with pytest.raises(TimeoutError):
            scanner("hung.html", 360)
        assert scanner.process is None
        scanner.timeout = 60
        response = scanner("healthy.html", 1100)
        assert response["violations"] == []
    finally:
        scanner.close()


def test_target_size_rule_must_execute_not_merely_exist():
    response = {kind: [] for kind in a11y.RESULT_TYPES}
    with pytest.raises(ValueError, match="did not execute"):
        a11y.target_size_outcome(response)
    response["inapplicable"] = [{"id": "target-size"}]
    assert a11y.target_size_outcome(response) == "inapplicable"


def test_cli_independent_population_failure_cannot_scan(site, monkeypatch):
    def rejected(site):
        raise ValueError("independently expected route missing from both manifest and disk")

    monkeypatch.setattr(a11y, "check_expected_routes", rejected)
    assert a11y.main(["--site", str(site)]) == 1


def test_route_checker_runs_independently_and_propagates_failure(site, monkeypatch):
    calls = []

    def run(command, **kwargs):
        from subprocess import CompletedProcess

        calls.append(command)
        return CompletedProcess(command, 1, stdout="missing figure page", stderr="")

    monkeypatch.setattr(a11y.subprocess, "run", run)
    with pytest.raises(ValueError, match="missing figure"):
        a11y.check_expected_routes(site)
    assert calls[0][-1] == str(site.resolve())
    assert "sys.exit(check.main())" in calls[0][2]


def test_ci_preserves_default_gate_and_runs_real_browser_regressions():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/check.yml").read_text()
    job = workflow.split("\n  accessibility:", 1)[1].split("\n  quality:", 1)[0]
    assert "make a11y-default" in job
    assert "RUN_A11Y_BROWSER_TESTS=1" in job
    assert "--junitxml=test-results/a11y-regressions.xml" in job
    assert "actions/upload-artifact@v4" in job
    assert "if: always()" in job
    assert "continue-on-error" not in job
    guidance = (Path(__file__).resolve().parents[1] / "docs/accessibility-checks.md").read_text()
    assert "full expanded qualification is mandatory" in guidance
    assert "No green default CI job replaces this gate" in guidance


@pytest.mark.skipif(
    os.environ.get("RUN_A11Y_BROWSER_TESTS") != "1",
    reason="Explicit opt-in: installed Chromium is not a unit-test dependency",
)
def test_meta_refresh_scans_original_document_not_destination(tmp_path):
    (tmp_path / "life.html").write_text(
        '<!doctype html><html lang="en"><head><title>Redirect entry</title>'
        '<meta http-equiv="refresh" content="0;url=destination.html"></head>'
        "<body><main><h1>Original redirect entry</h1>"
        '<img id="original-image" src="missing.png">'
        "</main></body></html>"
    )
    (tmp_path / "destination.html").write_text(
        '<!doctype html><html lang="en"><title>Destination</title>'
        "<body><main><h1>Clean destination</h1></main></body></html>"
    )
    scanner = a11y.BrowserScanner(tmp_path, 60)
    try:
        for width in a11y.WIDTHS:
            response = scanner("life.html", width)
            assert response["axe_version"]
            assert response["target_size_outcome"] in a11y.RESULT_TYPES
            assert any(item["id"] == "image-alt" for item in response["violations"])
    finally:
        scanner.close()


@pytest.mark.skipif(
    os.environ.get("RUN_A11Y_BROWSER_TESTS") != "1",
    reason="Explicit opt-in: installed Chromium is not a unit-test dependency",
)
def test_real_target_size_rule_is_enabled_and_reports_failure(tmp_path):
    (tmp_path / "tiny.html").write_text(
        '<!doctype html><html lang="en"><title>Tiny adjacent targets</title>'
        "<style>button{width:8px;height:8px;padding:0;border:0;margin:0;font-size:6px}</style>"
        "<body><main><h1>Targets</h1><button>A</button><button>B</button></main></body></html>"
    )
    scanner = a11y.BrowserScanner(tmp_path, 60)
    try:
        response = scanner("tiny.html", 360)
        assert response["target_size_outcome"] == "violations"
        assert any(item["id"] == "target-size" for item in response["violations"])
    finally:
        scanner.close()
