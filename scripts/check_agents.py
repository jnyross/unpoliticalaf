"""Check root AGENTS.md repository references without network access or execution.

Checks literal paths in inline code, inline Markdown links and link definitions.
Absolute operator paths and external URLs are outside this checkout's scope.
This is a reference-integrity check, not an assessment of policy or product prose.
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
CODE = re.compile(r"`([^`\n]+)`")
LINK = re.compile(
    r"\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)" r"""(?:\s+(?:"[^"\n]*"|'[^'\n]*'|\([^)\n]*\)))?\s*\)"""
)
DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)")


def local_reference(value):
    """Return the decoded relative path, or None for an external reference."""
    value = value.strip("<>")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith(("/", "~")):
        return None
    return unquote(parsed.path) or None


def references(text):
    """Yield (line number, relative path) for the supported literal syntax."""
    for number, line in enumerate(text.splitlines(), 1):
        targets = set()
        for match in CODE.finditer(line):
            value = match[1]
            # Prose, scores and shell commands are not literal path references.
            if (
                not any(c.isspace() for c in value)
                and not re.fullmatch(r"\d+(?:[./]\d+)*", value)
                and ("/" in value or "." in value or value == "Makefile")
            ):
                targets.add(value)
        targets.update(match[1] for match in LINK.finditer(line))
        definition = DEFINITION.match(line)
        if definition:
            targets.add(definition[1])
        for value in sorted(targets):
            path = local_reference(value)
            if path:
                yield number, path


def check(root):
    """Return (reference count, diagnostics); never modify the instruction file."""
    root = Path(root).resolve()
    agents = root / "AGENTS.md"
    try:
        text = agents.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return 0, [f"AGENTS.md: cannot read instructions: {error}"]
    if not text.strip():
        return 0, ["AGENTS.md: instructions are empty"]

    problems = []
    count = 0
    for number, path in references(text):
        count += 1
        target = root / path
        label = f"AGENTS.md:{number}: {path}"
        if not target.resolve().is_relative_to(root):
            problems.append(f"{label}: reference leaves the repository")
        elif not target.exists():
            problems.append(f"{label}: referenced path does not exist")
        elif path.endswith("/") and not target.is_dir():
            problems.append(f"{label}: expected a directory")
    if not count:
        problems.append("AGENTS.md: no repository references found to validate")
    return count, problems


def main(root=ROOT):
    count, problems = check(root)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"AGENTS.md: checked {count} repository references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
