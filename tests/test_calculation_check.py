"""Independent calculation checking must never silently skip a candidate."""
import ast
import json
import math
import subprocess
from pathlib import Path

import pytest

from builder import check
from builder.check_calculations import check_calculations

ROOT = Path(__file__).resolve().parents[1]


def source(fid="a", value=2):
    return {"id": fid, "value": value, "status": "published", "locator": ""}


def calculated(fid="derived", value=2, formula="a", inputs=None):
    return {"id": fid, "value": value, "status": "calculated",
            "formula": formula, "inputs": ["a"] if inputs is None else inputs}


def validate(*records):
    errors = []
    counts = check_calculations({fact["id"]: fact for fact in records}, errors.append)
    assert counts.candidates == counts.evaluated + counts.missing + counts.literals + counts.failed
    return counts, errors


def test_unknown_formula_cannot_silently_pass():
    data = {"sources": {}, "facts": [
        {"id": "a", "value": 2, "status": "published", "locator": ""},
        {"id": "derived", "value": 2, "status": "calculated",
         "formula": "unsupported(a)", "inputs": ["a"]},
    ]}
    check.problems.clear()
    try:
        check.check_facts(data)
        assert any("derived" in problem and "formula" in problem
                   for problem in check.problems), check.problems
    finally:
        check.problems.clear()


@pytest.mark.parametrize(("formula", "values", "expected"), [
    ("100 × a.1 ÷ a.10", {"a.1": 5, "a.10": 20}, 25),
    ("a + b + c", {"a": 1, "b": 2, "c": 3}, 6),
    ("total − (a + b)", {"total": 20, "a": 1, "b": 2}, 17),
    ("(a + b) ÷ 2", {"a": 4, "b": 8}, 6),
    ("a × 1,000,000,000 ÷ b", {"a": 2, "b": 4}, 500000000),
    ("100 × b.1999 to 2000 ÷ b.2025-26", {"b.1999 to 2000": 2, "b.2025-26": 4}, 50),
    ("-a + +b", {"a": 4, "b": 8}, 4),
    ("round(a ÷ b, -3)", {"a": 25000, "b": 10}, 2000),
    ("round(a ÷ b, -3)", {"a": 35000, "b": 10}, 4000),
    ("round(a, 2)", {"a": 2.126}, 2.13),
    ("0.01 × a", {"a": 500}, 5),
    ("a × 1e3", {"a": 2}, 2000),
    ("1000", {}, 1000),  # an explicit, independently checked what-if assumption
])
def test_supported_expression_forms(formula, values, expected):
    counts, errors = validate(*(source(fid, value) for fid, value in values.items()),
                             calculated(value=expected, formula=formula, inputs=list(values)))
    assert errors == []
    assert counts.evaluated + counts.literals == counts.candidates == 1


@pytest.mark.parametrize(("record", "diagnostic"), [
    (calculated(formula="unsupported(a)"), "unsupported formula"),
    (calculated(formula=""), "empty or missing formula"),
    (calculated(formula=None), "empty or missing formula"),
    (calculated(formula="a + unknown"), "unsupported formula"),
    (calculated(formula="a", inputs=[]), "unsupported formula"),
    (calculated(formula="a", inputs=["a", "absent"]), "does not use declared inputs"),
    (calculated(formula="absent", inputs=["absent"]), "input absent missing"),
    (calculated(formula="a", inputs="a"), "inputs must be a list"),
    (calculated(formula="a", inputs=[""]), "inputs must be a list"),
    (calculated(formula="a ** 2"), "formula syntax"),
    (calculated(formula="a // 2"), "formula syntax"),
    (calculated(formula="a / 0"), "division by zero"),
    (calculated(formula="a * 1e309"), "non-finite"),
    (calculated(formula="round(a, a)"), "round places"),
    (calculated(formula="round(a, 100)"), "round places"),
    (calculated(formula="operand_0 + a"), "unsupported formula"),
    (calculated(formula="a.10"), "unsupported formula"),
    (calculated(value=999), "recalculated"),
    (calculated(value=None), "unexplained missing"),
    (calculated(value=math.inf), "non-finite"),
    (calculated(value=True), "non-numeric"),
    (calculated(value=5, formula="2 + 3", inputs=[]), "empty operands"),
])
def test_bad_calculations_have_meaningful_failures(record, diagnostic):
    counts, errors = validate(source(), record)
    assert counts.failed == 1
    assert any("derived:" in error and diagnostic in error for error in errors), errors


def test_missing_operands_propagate_through_independent_dependencies():
    counts, errors = validate(
        source(value=None), source("b", 3),
        calculated("next", None, "derived + b", ["derived", "b"]),
        calculated(value=None, formula="100 × a ÷ b", inputs=["a", "b"]),
    )
    assert errors == []
    assert counts.missing == counts.candidates == 2


@pytest.mark.parametrize(("formula", "diagnostic"), [
    ("a / 0", "division by zero"),
    ("a ** 2", "formula syntax"),
    ("unknown(a)", "unsupported formula"),
])
def test_missing_value_does_not_hide_bad_syntax_or_arithmetic(formula, diagnostic):
    counts, errors = validate(source(value=None), calculated(value=None, formula=formula))
    assert counts.failed == 1
    assert diagnostic in errors[0]


def test_missing_operand_cannot_be_reported_as_zero():
    counts, errors = validate(source(value=None), calculated(value=0))
    assert counts.failed == 1
    assert "value given although an input is missing" in errors[0]


def test_missing_status_operand_cannot_supply_a_number():
    counts, errors = validate({**source(), "status": "missing"}, calculated())
    assert counts.failed == 1
    assert "marked missing but has a value" in errors[0]


def test_invalid_dependency_cannot_supply_its_recorded_value():
    counts, errors = validate(source(), calculated(value=3),
                             calculated("next", 6, "derived × 2", ["derived"]))
    assert counts.failed == 2
    assert any("next:" in error and "invalid dependency derived" in error for error in errors)


def test_cyclic_dependencies_fail_without_recursing_forever():
    counts, errors = validate(calculated(formula="next", inputs=["next"]),
                             calculated("next", 2, "derived", ["derived"]))
    assert counts.failed == 2
    assert any("cyclic calculation dependency" in error for error in errors)


def test_repeated_operand_and_repeated_declared_input_are_supported():
    counts, errors = validate(source(), calculated(value=1, formula="a ÷ a", inputs=["a", "a"]))
    assert errors == []
    assert counts.evaluated == 1


def test_checker_has_no_producer_imports_or_python_eval():
    tree = ast.parse((ROOT / "builder/check_calculations.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert not (node.module or "").startswith(("builder", "scripts"))
        elif isinstance(node, ast.Import):
            assert not any(alias.name.startswith(("builder", "scripts")) for alias in node.names)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "eval"


def test_direct_make_check_rejects_mutated_builds_and_clean_rerun_passes():
    """Run the real command against disposable Boat output, retaining each exit."""
    facts_path = ROOT / "site/data/facts.json"
    if not facts_path.exists():
        subprocess.run(["make", "build"], cwd=ROOT, check=True, capture_output=True, text=True)
    original = facts_path.read_bytes()
    data = json.loads(original)
    target = next(fact for fact in data["facts"] if fact["id"] == "wif.yard.ge1m.n")
    mutations = [
        ({"value": target["value"] + 1000}, "recalculated"),
        ({"formula": "unknown(" + target["inputs"][0] + ")"}, "unsupported formula"),
        ({"formula": ""}, "empty or missing formula"),
        ({"inputs": []}, "unsupported formula"),
        ({"formula": "absent", "inputs": ["absent"]}, "input absent missing"),
        ({"formula": target["inputs"][0] + " ÷ 0", "inputs": target["inputs"][:1]}, "division by zero"),
        ({"value": None}, "unexplained missing"),
    ]
    try:
        # One changed existing record and one batch of extra candidate records
        # exercise two real mutated builds without reopening every source seven
        # times. The unit cases above retain individual negative verdicts.
        for batch in (mutations[:1], mutations[1:]):
            mutated = json.loads(original)
            for index, (mutation, _diagnostic) in enumerate(batch):
                if len(batch) == 1:
                    fact = next(item for item in mutated["facts"] if item["id"] == target["id"])
                else:
                    fact = {**target, "id": f"regression.calculation.{index}"}
                    mutated["facts"].append(fact)
                fact.update(mutation)
            facts_path.write_text(json.dumps(mutated))
            result = subprocess.run(["make", "check"], cwd=ROOT, capture_output=True, text=True)
            print(f"Direct mutated make check {batch!r}: exit {result.returncode}\n{result.stdout}")
            assert result.returncode != 0, result.stdout + result.stderr
            for index, (_mutation, diagnostic) in enumerate(batch):
                fid = target["id"] if len(batch) == 1 else f"regression.calculation.{index}"
                assert any(f"{fid}: calculation/formula:" in line and diagnostic in line
                           for line in result.stdout.splitlines()), result.stdout + result.stderr
    finally:
        facts_path.write_bytes(original)
    clean = subprocess.run(["make", "check"], cwd=ROOT, capture_output=True, text=True)
    print(f"Direct clean make check: exit {clean.returncode}\n{clean.stdout}")
    assert clean.returncode == 0, clean.stdout + clean.stderr


def test_candidate_calculated_population_is_fully_accounted_for():
    path = ROOT / "site/data/facts.json"
    if not path.exists():
        subprocess.run(["make", "build"], cwd=ROOT, check=True, capture_output=True, text=True)
    data = json.loads(path.read_text())
    facts = {fact["id"]: fact for fact in data["facts"]}
    errors = []
    counts = check_calculations(facts, errors.append)
    assert errors == []
    assert counts.candidates == sum(fact["status"] == "calculated" for fact in data["facts"])
    assert counts.candidates == counts.evaluated + counts.missing + counts.literals
    assert counts.candidates > 1000
    # The retained candidate currently has complete calculation operands.
    # Null propagation is exercised explicitly above, not invented in its data.
    assert counts.literals == 5  # Matches the stated SCENARIOS in data_top_earners.py.
    print(f"Candidate calculations: {counts}")
