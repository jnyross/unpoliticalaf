"""John's questions: questions the site must answer, and the probes that test them.

The questions and probes live in docs/johns-questions/questions.json.

    python scripts/johns_questions.py check   # every answered probe is still answered on the built site
    python scripts/johns_questions.py gaps    # one line per probe the site cannot answer yet
    python scripts/johns_questions.py pack    # answered probes as a reader question set (JSON)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_test import page_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "johns-questions" / "questions.json"
SITE = ROOT / "site"
PROBE_ID = re.compile(r"^J\d+\.\d+$")


def load(path=QUESTIONS):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def probes(data):
    for q in data["questions"]:
        for p in q["probes"]:
            yield q, p


def is_open(p):
    return not p.get("evidence")


def validate(data):
    """Problems with the file itself, whatever the site says."""
    problems = []
    seen = set()
    for q in data["questions"]:
        for key in ("id", "asked", "added", "source", "probes"):
            if not q.get(key):
                problems.append(f"{q.get('id', '?')}: missing {key}")
        if not q.get("probes"):
            continue
        for p in q["probes"]:
            pid = p.get("id", "?")
            if not PROBE_ID.match(pid) or not pid.startswith(q["id"] + "."):
                problems.append(f"{pid}: probe ids look like {q['id']}.1")
            if pid in seen:
                problems.append(f"{pid}: duplicate probe id")
            seen.add(pid)
            if not p.get("question"):
                problems.append(f"{pid}: missing question")
            if is_open(p):
                if not p.get("gap"):
                    problems.append(f"{pid}: has no evidence, so it needs a one-sentence gap")
                continue
            opts = p.get("options") or {}
            if len(opts) < 2:
                problems.append(f"{pid}: an answered probe needs at least two options")
            if p.get("answer") not in opts:
                problems.append(f"{pid}: answer {p.get('answer')} is not one of the options")
            if not p.get("why"):
                problems.append(f"{pid}: missing why")
    return problems


def check(site=SITE, data=None):
    """Return problems: a broken file, or answered probes the built site no longer supports."""
    data = data or load()
    problems = validate(data)
    cache = {}
    for _, p in probes(data):
        for ev in p.get("evidence") or []:
            path = Path(site) / ev["page"]
            if not path.exists():
                problems.append(f"{p['id']}: page {ev['page']} is missing from the built site")
                continue
            if path not in cache:
                cache[path] = page_text(path)
            if ev["text"] not in cache[path]:
                problems.append(f"{p['id']}: {ev['page']} no longer says: {ev['text']}")
    return problems


def gaps(data=None):
    data = data or load()
    return [f"{p['id']} ({q['asked']}): {p['gap']}" for q, p in probes(data) if is_open(p)]


def pack(data=None):
    """Answered probes in the shape of docs/user-test/questions.json, for the simulated readers."""
    data = data or load()
    out = []
    for q, p in probes(data):
        if is_open(p):
            continue
        out.append({
            "id": p["id"],
            "topic": f"John's question {q['id']}: {q['asked']}",
            "question": p["question"],
            "options": p["options"],
            "answer": p["answer"],
            "critical": False,
            "why": p["why"],
            "evidence": p["evidence"],
        })
    return {"title": "John's questions", "not_sure": data["not_sure"], "questions": out,
            "open": [{"id": p["id"], "question": p["question"], "gap": p["gap"]}
                     for _, p in probes(data) if is_open(p)]}


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "check":
        problems = check()
        for line in problems:
            print(line)
        data = load()
        answered = sum(1 for _, p in probes(data) if not is_open(p))
        total = sum(1 for _ in probes(data))
        print(f"John's questions: {answered} of {total} probes answered on the site; {len(problems)} problems")
        return 1 if problems else 0
    if cmd == "gaps":
        for line in gaps():
            print(line)
        return 0
    if cmd == "pack":
        print(json.dumps(pack(), indent=2, ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
