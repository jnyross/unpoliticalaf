"""Enforce a Radon complexity ceiling and ratchet down existing complexity debt."""

import ast
import json
from pathlib import Path
from pathlib import PurePosixPath
import sys
import tokenize

# This developer-only CLI reuses the dashboard's Radon pin, not production setup.
from radon.complexity import cc_visit_ast  # deptry: ignore[DEP004]

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIRS = ("builder", "scripts", "tests")
MAX_COMPLEXITY = 20


class FunctionScores(ast.NodeVisitor):
    """Name functions by lexical scope, including methods and nested functions."""

    def __init__(self):
        self.scope = []
        self.scores = {}

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        name = ".".join([*self.scope, node.name])
        block = cc_visit_ast(ast.Module(body=[node], type_ignores=[]))[0]
        # Repeated definitions (for example property accessors) share a ceiling.
        self.scores[name] = max(block.complexity, self.scores.get(name, 0))
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef


def measure(root):
    scores = {}
    for directory in SOURCE_DIRS:
        paths = sorted((root / directory).rglob("*.py"))
        if not paths:
            raise ValueError(f"No Python files found in {directory}/")
        for path in paths:
            with tokenize.open(path) as source:
                tree = ast.parse(source.read(), filename=str(path))
            visitor = FunctionScores()
            visitor.visit(tree)
            relative = path.relative_to(root).as_posix()
            scores.update({f"{relative}:{name}": score for name, score in visitor.scores.items()})
    return scores


def _unique_entries(pairs):
    baseline = {}
    for name, ceiling in pairs:
        if name in baseline:
            raise ValueError(f"Duplicate baseline identifier: {name!r}")
        baseline[name] = ceiling
    return baseline


def _valid_identifier(name):
    if not isinstance(name, str) or name.count(":") != 1:
        return False
    filename, function = name.split(":")
    path = PurePosixPath(filename)
    return (
        len(path.parts) >= 2
        and path.parts[0] in SOURCE_DIRS
        and path.suffix == ".py"
        and path.as_posix() == filename
        and "\\" not in filename
        and ".." not in path.parts
        and all(part.isidentifier() for part in function.split("."))
    )


def load_baseline(path):
    baseline = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_entries)
    if not isinstance(baseline, dict):
        raise ValueError("Complexity baseline must be an object")
    for name, ceiling in baseline.items():
        if not _valid_identifier(name):
            raise ValueError(f"Invalid function identifier: {name!r}")
        if type(ceiling) is not int or ceiling <= MAX_COMPLEXITY:
            raise ValueError(f"{name}: baseline ceilings must be integers above {MAX_COMPLEXITY}")
    return baseline


def violations(scores, baseline):
    problems = []
    for name, score in sorted(scores.items()):
        ceiling = baseline.get(name, MAX_COMPLEXITY)
        if score > ceiling:
            problems.append(f"{name}: complexity {score} exceeds ceiling {ceiling}")
    for name, ceiling in sorted(baseline.items()):
        score = scores.get(name)
        if score is None:
            problems.append(f"{name}: remove obsolete baseline entry")
        elif score < ceiling:
            action = "remove entry" if score <= MAX_COMPLEXITY else f"lower ceiling to {score}"
            problems.append(f"{name}: complexity fell from {ceiling} to {score}; {action}")
    return problems


def main(root=ROOT):
    try:
        baseline = load_baseline(root / "complexity-baseline.json")
        scores = measure(root)
    except Exception as error:
        # Any analyzer/input failure is an error, never an empty healthy report.
        print(f"Complexity analysis failed: {error}", file=sys.stderr)
        return 2
    problems = violations(scores, baseline)
    debt = {name: score for name, score in scores.items() if score > MAX_COMPLEXITY}
    print(
        f"Analyzed {len(scores)} functions; default ceiling {MAX_COMPLEXITY}; "
        f"{len(debt)} existing over-limit functions."
    )
    for name, score in sorted(debt.items()):
        print(f"  {name}: {score} (ceiling {baseline.get(name, MAX_COMPLEXITY)})")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Complexity gate passed; no new or increased complexity debt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
