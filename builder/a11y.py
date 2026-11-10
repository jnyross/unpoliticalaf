"""Manifest-wide expanded axe scans and exact partition-union verification.

Run ``python -m builder.a11y --help``. Existing default-state/page-length/24px
checks remain in ``builder.check --axe``; this adds every generated HTML page.
JSON evidence is candidate-bound and incomplete findings require rendered review,
not an automatic pass. A disposition records an agent's inspection, not proof
that an automated checker can establish conformance.
"""

import argparse
import hashlib
import json
import multiprocessing
import mimetypes
import os
import signal
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

WIDTHS = (360, 1100)
STATE = "all-details-expanded"
SCHEMA = 2
DEFAULT_SITE = Path(__file__).resolve().parents[1] / "site"
RESULT_TYPES = ("passes", "inapplicable", "violations", "incomplete")


def check_expected_routes(site):
    """Run the independent checker as orchestration, not a producer import.

    Its independently stated year/pair/span population and internal-link checks
    catch routes (including linked figure pages) missing from BOTH manifest and
    disk. Preserve the existing import contracts and fiscal checker boundary.
    """
    program = (
        "import sys; from pathlib import Path; from builder import check; "
        "check.SITE = Path(sys.argv[1]); sys.exit(check.main())"
    )
    result = subprocess.run(
        [sys.executable, "-c", program, str(site.resolve())],
        cwd=DEFAULT_SITE.parent,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise ValueError(
            "independent expected-route/page check failed:\n" + result.stdout + result.stderr
        )


def target_size_outcome(response):
    for outcome in RESULT_TYPES:
        if any(finding["id"] == "target-size" for finding in response[outcome]):
            return outcome
    raise ValueError("axe did not execute the required WCAG 2.2 AA target-size rule")


def finding_digest(finding):
    return hashlib.sha256(json.dumps(finding, sort_keys=True).encode()).hexdigest()


def population(site):
    """Reconcile manifest HTML routes and bytes with the complete disk population."""
    raw = (site / "build.json").read_bytes()
    manifest = json.loads(raw)
    files = manifest["files"]
    paths = sorted(name for name in files if name.endswith(".html"))
    if not paths:
        raise ValueError("manifest has no HTML routes")
    for name in paths:
        route = PurePosixPath(name)
        if route.is_absolute() or ".." in route.parts or route.as_posix() != name:
            raise ValueError(f"unsafe manifest route: {name}")
    actual = {path.relative_to(site).as_posix() for path in site.rglob("*.html")}
    if set(paths) != actual:
        raise ValueError(
            f"manifest/disk HTML mismatch: missing={sorted(set(paths) - actual)}, "
            f"unexpected={sorted(actual - set(paths))}"
        )
    for name in paths:
        path = site / name
        if path.is_symlink() or not path.resolve().is_relative_to(site.resolve()):
            raise ValueError(f"unsafe HTML file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != files[name]:
            raise ValueError(f"HTML differs from manifest: {name}")
    return hashlib.sha256(raw).hexdigest(), paths


def partition_cases(paths, index, count):
    if count < 1 or not 0 <= index < count:
        raise ValueError("partition index must be in [0, partition count)")
    cases = [(path, width) for path in paths for width in WIDTHS]
    return cases[index::count]


def scan_partition(site, index, count, scan, save=None):
    digest, paths = population(site)
    report = {
        "schema": SCHEMA,
        "manifest_sha256": digest,
        "state": STATE,
        "widths": list(WIDTHS),
        "partition_index": index,
        "partition_count": count,
        "results": [],
    }
    cases = partition_cases(paths, index, count)
    if save:
        save(report)
    for path, width in cases:
        result = {"path": path, "width": width, "state": STATE}
        try:
            response = scan(path, width)
            for key in ("violations", "incomplete"):
                if not isinstance(response[key], list):
                    raise ValueError(f"axe {key} is not a list")
                result[key] = response[key]
            result["axe_version"] = response["axe_version"]
            result["target_size_outcome"] = response["target_size_outcome"]
            if not result["axe_version"] or result["target_size_outcome"] not in RESULT_TYPES:
                raise ValueError("missing axe version or target-size execution evidence")
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"
        report["results"].append(result)
        if save:
            save(report)
    # A changed build during scanning invalidates even an otherwise clean run.
    if population(site)[0] != digest:
        raise ValueError("manifest changed during scanning")
    return report


def relevant(finding):
    return any(tag.startswith("wcag") for tag in finding.get("tags", [])) or finding.get(
        "impact"
    ) in ("serious", "critical")


def disposition_cases(dispositions, digest):
    if dispositions is None:
        return set()
    if not isinstance(dispositions, dict):
        raise ValueError("rendered dispositions must be an object")
    if dispositions.get("manifest_sha256") != digest:
        raise ValueError("rendered dispositions belong to a different manifest")
    accepted = set()
    for item in dispositions["findings"]:
        if not isinstance(item, dict):
            raise ValueError("each rendered disposition must be an object")
        for field in ("reason", "evidence"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("disposition needs rendered evidence and a reason as strings")
        for case in item["cases"]:
            accepted.add((case["path"], case["width"], item["finding_sha256"]))
    return accepted


def _result_problems(result, accepted):
    """Validate one completed/error case independently of partition coverage."""
    case = (result["path"], result["width"])
    label = f"{case[0]} at {case[1]}px"
    if result.get("error"):
        return [f"{label}: {result['error']}"]
    problems = []
    if not result["axe_version"] or result["target_size_outcome"] not in RESULT_TYPES:
        problems.append(f"{label}: missing axe version/target-size execution")
    for key in ("violations", "incomplete"):
        if not isinstance(result[key], list):
            raise ValueError(f"{label}: missing axe result list")
        for finding in result[key]:
            if not relevant(finding):
                continue
            identity = (*case, finding_digest(finding))
            if key == "violations" or identity not in accepted:
                problems.append(f"{label}: {key} {finding['id']}")
    return problems


def verify_reports(site, reports, dispositions=None):
    """Reject gaps, duplicates, foreign candidates, errors and unresolved findings."""
    digest, paths = population(site)
    problems = []
    seen = set()
    partitions = set()
    expected = set(partition_cases(paths, 0, 1))
    count = reports[0]["partition_count"] if reports else 0
    try:
        accepted = disposition_cases(dispositions, digest)
        for report in reports:
            index = report["partition_index"]
            if (
                report["schema"] != SCHEMA
                or report["manifest_sha256"] != digest
                or report["state"] != STATE
                or report["widths"] != list(WIDTHS)
                or report["partition_count"] != count
                or index in partitions
            ):
                problems.append("incompatible or duplicate partition evidence")
            partitions.add(index)
            assigned = set(partition_cases(paths, index, count))
            local = set()
            for result in report["results"]:
                case = (result["path"], result["width"])
                label = f"{case[0]} at {case[1]}px"
                if case in seen or case not in assigned or result["state"] != STATE:
                    problems.append(f"{label}: duplicate, unassigned or wrong-state case")
                seen.add(case)
                local.add(case)
                problems.extend(_result_problems(result, accepted))
            if local != assigned:
                problems.append(f"partition {index}: missing assigned cases")
        if partitions != set(range(count)) or seen != expected:
            problems.append("partition union does not equal every manifest HTML path x 360/1100")
    except (KeyError, TypeError, ValueError) as error:
        problems.append(f"invalid evidence: {error}")
    return problems


def _browser_worker(connection, site):
    """One browser per partition. The parent enforces a real wall-clock deadline."""
    os.setsid()
    from axe_playwright_python.sync_playwright import Axe
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        executable = Path("/opt/pw-browsers/chromium")
        options = (
            {"executable_path": str(executable), "args": ["--no-sandbox"]}
            if executable.exists()
            else {}
        )
        browser = playwright.chromium.launch(**options)
        page = browser.new_page()
        # Aborting a refresh request alone can already destroy its old context.
        # Cancel the pending refresh without changing the original meta element.
        page.add_init_script(
            """document.addEventListener('DOMContentLoaded', () => {
              if ([...document.querySelectorAll('meta[http-equiv]')].some(meta =>
                meta.httpEquiv.toLowerCase() === 'refresh')) {
                window.stop();
              }
            }, {once: true})"""
        )
        page.set_default_timeout(20000)
        axe = Axe()
        original_url = None
        initial_navigation = False

        def guard_navigation(route):
            request = route.request
            if request.is_navigation_request() and request.frame == page.main_frame:
                if not (initial_navigation and request.url == original_url):
                    route.abort()
                    return
            url = urlsplit(request.url)
            resource = (site / unquote(url.path).lstrip("/")).resolve()
            if url.netloc != "a11y.invalid" or not resource.is_relative_to(site.resolve()):
                route.abort()
            elif resource.is_file():
                route.fulfill(
                    body=resource.read_bytes(),
                    content_type=mimetypes.guess_type(resource.name)[0]
                    or "application/octet-stream",
                )
            else:
                route.fulfill(status=404, body="Not found", content_type="text/plain")

        page.route("**/*", guard_navigation)
        try:
            while True:
                case = connection.recv()
                if case is None:
                    return
                path, width = case
                try:
                    page.set_viewport_size({"width": width, "height": 800})
                    # Chromium does not reliably route file:// navigations.
                    # Fulfil a synthetic same-origin HTTP URL from unchanged
                    # local bytes, with no server or external network request.
                    original_url = "http://a11y.invalid/" + quote(path, safe="/")
                    initial_navigation = True
                    try:
                        # Commit only: block subsequent navigation before load
                        # handlers/meta refresh can replace the original document.
                        page.goto(original_url, wait_until="commit", timeout=20000)
                    finally:
                        initial_navigation = False
                    page.wait_for_load_state("domcontentloaded")
                    if page.url != original_url:
                        raise ValueError("page URL changed before axe")
                    page.evaluate(
                        """async () => {
                          document.querySelectorAll('details').forEach(detail => {
                            detail.open = true;
                          });
                          await document.fonts.ready;
                          await new Promise(resolve => requestAnimationFrame(() =>
                            requestAnimationFrame(resolve)));
                          if (document.querySelector('details:not([open])')) {
                            throw new Error('A nested disclosure remains closed');
                          }
                        }"""
                    )
                    # The wrapper default only retains full violation nodes.
                    # Keep every incomplete node for actual rendered review.
                    response = axe.run(
                        page,
                        options={
                            "resultTypes": ["violations", "incomplete"],
                            "rules": {"target-size": {"enabled": True}},
                        },
                    ).response
                    outcome = target_size_outcome(response)
                    if page.url != original_url or page.evaluate("location.href") != original_url:
                        raise ValueError("page URL changed during axe")
                    if page.evaluate("document.documentElement.scrollWidth") > width + 1:
                        raise ValueError("expanded document scrolls sideways")
                    connection.send(
                        {
                            "violations": response["violations"],
                            "incomplete": response["incomplete"],
                            "axe_version": response["testEngine"]["version"],
                            "target_size_outcome": outcome,
                        }
                    )
                except Exception as error:
                    connection.send({"error": f"{type(error).__name__}: {error}"})
        finally:
            browser.close()


class BrowserScanner:
    """Kill and recreate an unresponsive browser; never silently skip its case."""

    def __init__(self, site, timeout):
        self.site = site
        self.timeout = timeout
        self.process = None
        self.connection = None

    def close(self):
        if self.process is not None:
            try:
                self.connection.send(None)
            except (BrokenPipeError, EOFError, OSError):
                pass
            self.process.join(timeout=5)
            if self.process.is_alive():
                # Own session only: also reap the Playwright driver and browser,
                # not just Python, when a case times out.
                try:
                    os.killpg(self.process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                self.process.join(timeout=5)
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.join()
            self.process = None
            self.connection.close()

    def __call__(self, path, width):
        if self.process is None:
            context = multiprocessing.get_context("spawn")
            self.connection, child = context.Pipe()
            self.process = context.Process(target=_browser_worker, args=(child, self.site))
            self.process.start()
            child.close()
        try:
            self.connection.send((path, width))
            if not self.connection.poll(self.timeout):
                raise TimeoutError(f"axe exceeded {self.timeout}s")
            response = self.connection.recv()
            if "error" in response:
                raise ValueError(response["error"])
            return response
        except Exception:
            self.close()
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--partition-index", type=int, default=0)
    parser.add_argument("--partition-count", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=60, help="wall-clock seconds per case")
    parser.add_argument("--output", type=Path, default=Path("test-results/a11y/expanded.json"))
    parser.add_argument(
        "--verify", nargs="+", type=Path, help="verify the exact union of JSON reports"
    )
    parser.add_argument(
        "--dispositions", type=Path, help="candidate-bound rendered incomplete reviews"
    )
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    try:
        check_expected_routes(args.site)
        dispositions = json.loads(args.dispositions.read_text()) if args.dispositions else None
        if args.verify:
            reports = [json.loads(path.read_text()) for path in args.verify]
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)

            def save(report):
                temporary = args.output.with_suffix(".tmp")
                temporary.write_text(json.dumps(report, indent=1) + "\n")
                temporary.replace(args.output)

            scanner = BrowserScanner(args.site.resolve(), args.timeout)
            try:
                report = scan_partition(
                    args.site, args.partition_index, args.partition_count, scanner, save
                )
            finally:
                scanner.close()
            reports = [report]
            if args.partition_count > 1:
                # A partition alone cannot claim complete-population success.
                print(f"Partition evidence: {args.output}; run --verify on ALL partitions.")
                accepted = disposition_cases(dispositions, report["manifest_sha256"])
                unresolved = any(
                    case.get("error")
                    or any(
                        relevant(finding)
                        and (
                            key == "violations"
                            or (case["path"], case["width"], finding_digest(finding))
                            not in accepted
                        )
                        for key in ("violations", "incomplete")
                        for finding in case.get(key, [])
                    )
                    for case in report["results"]
                )
                return 1 if unresolved else 0
        problems = verify_reports(args.site, reports, dispositions)
        for problem in problems:
            print(problem)
        print(
            f"Expanded axe: {sum(len(report['results']) for report in reports)} cases; "
            f"{len(problems)} unresolved problems."
        )
        return 1 if problems else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"Expanded axe failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
