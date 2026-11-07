#!/usr/bin/env python3
"""Join coverage.py and Radon measurements into an offline quality dashboard."""
import argparse
import html
import json
from pathlib import Path

from radon.complexity import add_inner_blocks, cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit
from radon.raw import analyze


def collect(root, coverage):
    """Include every owned Python file, even one never imported by verification."""
    rows = []
    for folder in ("builder", "scripts"):
        for path in sorted((root / folder).rglob("*.py")):
            name = path.relative_to(root).as_posix()
            # Missing data is an error, not a healthy-looking zero or omitted row.
            summary = coverage["files"][name]["summary"]
            source = path.read_text(encoding="utf-8")
            blocks = add_inner_blocks(cc_visit(source))
            functions = [
                {
                    "name": block.fullname,
                    "line": block.lineno,
                    "complexity": block.complexity,
                    "rank": cc_rank(block.complexity),
                }
                for block in blocks
                if not hasattr(block, "methods")
            ]
            score = mi_visit(source, multi=True)
            rows.append(
                {
                    "path": name,
                    "statements": summary["num_statements"],
                    "covered_lines": summary["covered_lines"],
                    "branches": summary["num_branches"],
                    "covered_branches": summary["covered_branches"],
                    "sloc": analyze(source).sloc,
                    "maintainability_index": round(score, 2),
                    "maintainability_rank": mi_rank(score),
                    "functions": functions,
                    "max_complexity": max((f["complexity"] for f in functions), default=0),
                }
            )
    if not rows:
        raise ValueError("No Python sources found")
    return {"schema_version": 1, "totals": coverage["totals"], "files": rows}


def percentage(covered, total):
    return f"{100 * covered / total:.1f}%" if total else "n/a"


def markdown(report):
    totals = report["totals"]
    lines = [
        "# Code quality metrics",
        "",
        "Scope: all Python in `builder/` and `scripts/`. Coverage measures "
        "build, independent checks and unit tests together, not unit tests alone.",
        "",
        "| Metric | Measured value |",
        "| --- | --- |",
        f"| Line coverage | {percentage(totals['covered_lines'], totals['num_statements'])} |",
        f"| Branch coverage | {percentage(totals['covered_branches'], totals['num_branches'])} |",
        f"| Python files | {len(report['files'])} |",
        f"| Maximum function complexity | {max(r['max_complexity'] for r in report['files'])} |",
        f"| Files with maintainability rank C | {sum(r['maintainability_rank'] == 'C' for r in report['files'])} |",
        "",
        "Download this run's **code-quality-metrics** artifact and open `index.html` "
        "for the dashboard, `coverage/index.html` for uncovered lines, or "
        "`metrics.json` / `coverage.xml` for machine-readable measurements.",
        "",
        "## Files (lowest maintainability index first)",
        "",
        "| File | Lines | Branches | Max complexity | Maintainability index (rank) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in sorted(report["files"], key=lambda r: (r["maintainability_index"], r["path"])):
        lines.append(
            f"| `{row['path']}` | {percentage(row['covered_lines'], row['statements'])} "
            f"| {percentage(row['covered_branches'], row['branches'])} "
            f"| {row['max_complexity']} "
            f"| {row['maintainability_index']:.2f} ({row['maintainability_rank']}) |"
        )
    return "\n".join(lines) + "\n"


def dashboard(report):
    rows = []
    for row in sorted(report["files"], key=lambda r: (r["maintainability_index"], r["path"])):
        rows.append(
            f"<tr><th scope=\"row\">{html.escape(row['path'])}</th>"
            f"<td>{percentage(row['covered_lines'], row['statements'])}</td>"
            f"<td>{percentage(row['covered_branches'], row['branches'])}</td>"
            f"<td>{row['max_complexity']}</td>"
            f"<td>{row['maintainability_index']:.2f} ({row['maintainability_rank']})</td></tr>"
        )
    functions = [
        (row["path"], function) for row in report["files"] for function in row["functions"]
    ]
    hotspots = [
        f"<tr><th scope=\"row\">{html.escape(path)}:{f['line']} "
        f"{html.escape(f['name'])}</th><td>{f['complexity']} ({f['rank']})</td></tr>"
        for path, f in sorted(
            functions, key=lambda item: (-item[1]["complexity"], item[0], item[1]["line"])
        )[:20]
    ]
    totals = report["totals"]
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Code quality metrics</title>"
        "<style>body{font:1rem system-ui;margin:2rem;max-width:100rem}"
        "table{border-collapse:collapse}th,td{border:1px solid #aaa;padding:.5rem;"
        "text-align:left}th{overflow-wrap:anywhere}a{color:#0645ad}</style>"
        "<main><h1>Code quality metrics</h1>"
        "<p>All Python in builder/ and scripts/. Coverage combines the build, "
        "independent checks and unit tests. Tests, retained reference code, "
        "generated output, JavaScript and this reporting tool are outside this scope.</p>"
        f"<p>Line coverage: <strong>{percentage(totals['covered_lines'], totals['num_statements'])}"
        "</strong>. Branch coverage: "
        f"<strong>{percentage(totals['covered_branches'], totals['num_branches'])}</strong>.</p>"
        '<p><a href="coverage/index.html">Explore uncovered lines and branches</a> · '
        '<a href="metrics.json">Download all metrics (JSON)</a> · '
        '<a href="coverage.xml">Coverage XML</a></p>'
        "<p>Complexity counts independent paths per function (lower is simpler). "
        "Radon maintainability index is 0–100 (higher is easier to maintain); "
        "ranks: A &gt; 19, B &gt; 9–19, C 0–9. These are monitoring signals, "
        "not proof of correctness or replacement quality gates.</p>"
        "<table><caption>Files, lowest maintainability index first</caption>"
        '<thead><tr><th scope="col">File</th><th scope="col">Lines covered</th>'
        '<th scope="col">Branches covered</th><th scope="col">Max complexity</th>'
        '<th scope="col">Maintainability index (rank)</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
        "<h2>20 most complex functions</h2><table><thead><tr>"
        '<th scope="col">Function and source line</th>'
        '<th scope="col">Complexity (rank)</th></tr></thead><tbody>'
        + "".join(hotspots)
        + "</tbody></table></main></html>\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("quality-reports"))
    args = parser.parse_args(argv)
    coverage = json.loads((args.output / "coverage.json").read_text(encoding="utf-8"))
    report = collect(args.root, coverage)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "summary.md").write_text(markdown(report), encoding="utf-8")
    (args.output / "index.html").write_text(dashboard(report), encoding="utf-8")
    print(markdown(report))


if __name__ == "__main__":
    main()
