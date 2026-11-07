"""Independent interpretation of recorded arithmetic, never producer formulas.

The small grammar accepts fact IDs, finite numbers (including grouped thousands),
parentheses, + - × ÷ and round(expression, integer places). Literal-only formulas
represent explicitly stated what-if assumptions, not published source values.
Missing source operands propagate as missing only after syntax is checked;
unresolved dependencies and invalid arithmetic are errors, not missing evidence.
"""

import ast
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

NUMBER = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?")
TOKEN = re.compile(r"round\b|[()+\-*/,]")


@dataclass
class CalculationCounts:
    candidates: int = 0
    evaluated: int = 0
    missing: int = 0
    literals: int = 0
    failed: int = 0


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"non-numeric value {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite value {value!r}")
    return result


def _expression(formula: str, inputs: list[str]) -> ast.Expression:
    """Tokenize complete declared IDs atomically, including overlapping IDs."""
    aliases = {fid: f"operand_{index}" for index, fid in enumerate(dict.fromkeys(inputs))}
    pattern = "|".join(re.escape(fid) for fid in sorted(aliases, key=len, reverse=True))
    operand = re.compile(r"(?<![\w.])(?:" + pattern + r")(?![\w.])") if pattern else None
    formula = formula.replace("×", "*").replace("÷", "/").replace("−", "-")
    tokens, used = [], set()
    offset = 0
    while offset < len(formula):
        if formula[offset].isspace():
            offset += 1
            continue
        match = operand.match(formula, offset) if operand else None
        if match:
            used.add(match.group())
            tokens.append(aliases[match.group()])
        else:
            match = NUMBER.match(formula, offset) or TOKEN.match(formula, offset)
            if not match:
                raise ValueError(f"unsupported formula syntax at {formula[offset:]!r}")
            tokens.append(match.group().replace(",", "") if match.re is NUMBER else match.group())
        offset = match.end()
    if used != set(inputs):
        raise ValueError(f"formula does not use declared inputs: {sorted(set(inputs) - used)}")
    try:
        return ast.parse(" ".join(tokens), mode="eval")
    except SyntaxError as error:
        raise ValueError(f"invalid formula syntax: {formula!r}") from error


def _round_places(node: ast.expr) -> int:
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        sign, node = -1, node.operand
    if not isinstance(node, ast.Constant) or type(node.value) is not int:
        raise ValueError("round places must be an integer literal")
    places = sign * node.value
    if abs(places) > 12:
        raise ValueError("round places outside supported range -12 to 12")
    return places


def _binary(operation: ast.operator, left: float | None, right: float | None) -> float | None:
    if isinstance(operation, ast.Div) and right == 0:
        raise ValueError("invalid arithmetic: division by zero")
    if left is None or right is None:
        return None
    if isinstance(operation, ast.Add):
        result = left + right
    elif isinstance(operation, ast.Sub):
        result = left - right
    elif isinstance(operation, ast.Mult):
        result = left * right
    elif isinstance(operation, ast.Div):
        result = left / right
    else:
        raise ValueError("unsupported binary arithmetic")
    return _number(result)


def _arithmetic(node: ast.expr, values: Mapping[str, float | None]) -> float | None:
    if isinstance(node, ast.Constant):
        return _number(node.value)
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _arithmetic(node.operand, values)
        return None if value is None else (-value if isinstance(node.op, ast.USub) else value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _arithmetic(node.left, values)
        right = _arithmetic(node.right, values)
        return _binary(node.op, left, right)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "round" and len(node.args) == 2 and not node.keywords):
        places = _round_places(node.args[1])
        value = _arithmetic(node.args[0], values)
        return None if value is None else _number(round(value, places))
    raise ValueError(f"unsupported formula operation: {ast.dump(node)}")


def _check_result(result: float | None, recorded: object) -> None:
    if result is None:
        if recorded is not None:
            raise ValueError("value given although an input is missing")
    elif recorded is None:
        raise ValueError(f"unexplained missing result; recalculated {result}")
    elif not math.isclose(result, _number(recorded), rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"recalculated {result} != recorded {recorded}")


def check_calculations(
    facts: Mapping[str, Mapping[str, Any]], fail: Callable[[str], None],
) -> CalculationCounts:
    """Account for every candidate, following independently recomputed dependencies."""
    counts = CalculationCounts()
    resolved: dict[str, float | None] = {}
    errors: dict[str, str] = {}
    visiting: set[str] = set()

    def resolve(fid: str) -> float | None:
        if fid in errors:
            raise ValueError(f"invalid dependency {fid}: {errors[fid]}")
        if fid in visiting:
            raise ValueError(f"cyclic calculation dependency {fid}")
        if fid in resolved:
            return resolved[fid]
        if fid not in facts:
            raise ValueError(f"input {fid} missing")
        fact = facts[fid]
        if fact["status"] != "calculated":
            if fact["status"] == "missing" and fact["value"] is not None:
                raise ValueError(f"input {fid} marked missing but has a value")
            return None if fact["value"] is None else _number(fact["value"])
        visiting.add(fid)
        try:
            formula, inputs = fact.get("formula"), fact.get("inputs")
            if not isinstance(formula, str) or not formula.strip():
                raise ValueError("empty or missing formula")
            if not isinstance(inputs, list) or any(not isinstance(i, str) or not i for i in inputs):
                raise ValueError("inputs must be a list of nonempty fact IDs")
            expression = _expression(formula, inputs)
            if not inputs and not isinstance(expression.body, ast.Constant):
                raise ValueError("empty operands require an explicit numeric literal assumption")
            values = {f"operand_{index}": resolve(i) for index, i in enumerate(dict.fromkeys(inputs))}
            result = _arithmetic(expression.body, values)
            _check_result(result, fact["value"])
            resolved[fid] = result
            return result
        except (ValueError, OverflowError, RecursionError) as error:
            errors[fid] = str(error)
            raise ValueError(str(error)) from error
        finally:
            visiting.remove(fid)

    for fid, fact in facts.items():
        if fact["status"] != "calculated":
            continue
        counts.candidates += 1
        try:
            result = resolve(fid)
        except (ValueError, OverflowError, RecursionError) as error:
            fail(f"{fid}: calculation/formula: {error}")
            counts.failed += 1
        else:
            if result is None:
                counts.missing += 1
            elif not fact["inputs"]:
                counts.literals += 1
            else:
                counts.evaluated += 1
    return counts
