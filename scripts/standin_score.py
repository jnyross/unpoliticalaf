"""Action-based scoring for agent stand-ins, not elapsed-time human evidence."""

import hashlib
import json
import re
from pathlib import Path

import johns_questions as jq

BUDGET = 40
NEW_PASS = 0.80
JOHNS_PASS = 0.80
UPLIFT_MIN = 20
SR_MIN_CORRECT = 9
READERS = {f"R{i}" for i in range(1, 6)}


def read_record(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def correct(answers, questions):
    if not isinstance(answers, dict):
        return 0
    return sum(str(answers.get(str(q["id"]), "")).strip().upper() == q["answer"] for q in questions)


def complete(answers, questions):
    return (
        isinstance(answers, dict)
        and set(answers) == {str(q["id"]) for q in questions}
        and all(
            isinstance(value, str) and value.strip().upper() in set(q.get("options", {})) | {"E"}
            for q in questions
            for value in [answers[str(q["id"])]]
        )
    )


def reader_set(readers):
    return (
        len(readers) == 5
        and {r.get("reader") for r in readers} == READERS
        and len({r.get("site_commit") for r in readers}) == 1
        and all(
            isinstance(r.get("site_commit"), str)
            and r["site_commit"].strip() not in {"", "unknown"}
            for r in readers
        )
    )


def session_valid(audit, reader, suffix, count, mode, identity):
    """Require the tool state, not merely a claimed action count in the answers."""
    name = f"{reader.get('reader')}-{suffix}"
    state = read_record(Path(audit) / "readers" / f"{name}.json")
    actions = state.get("actions")
    return (
        bool(identity)
        and state.get("reader") == name
        and state.get("mode") == mode
        and state.get("site_commit") == reader.get("site_commit") == identity[0]
        and state.get("build_digest") == identity[1]
        and type(state.get("budget")) is int
        and state["budget"] == BUDGET
        and type(reader.get("budget")) is int
        and reader["budget"] == BUDGET
        and type(actions) is int
        and 0 <= actions <= BUDGET
        and type(count) is int
        and count == actions
        and isinstance(state.get("log"), list)
        and len(state["log"]) == actions
        and all(isinstance(entry, str) and entry for entry in state["log"])
    )


def build_identity(audit, readers):
    if not reader_set(readers):
        return None
    first = read_record(Path(audit) / "readers" / "R1-phone.json")
    digest = first.get("build_digest", "")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return None
    return readers[0]["site_commit"], digest


def validate_pack(pack):
    questions = pack.get("questions", [])
    bad = []
    if len(questions) != 24:
        bad.append("needs exactly 24 new questions")
    ids = [str(q.get("id", "")) for q in questions]
    if len(set(ids)) != len(ids) or "" in ids:
        bad.append("question ids must be present and unique")
    for question in questions:
        if question.get("answer") not in question.get("options", {}):
            bad.append(f"Q{question.get('id')}: answer is not one of the options")
    return bad


def sealed_pack(audit, supplied=None):
    path = audit / "new-questions.json"
    pack = read_record(path)
    try:
        seal = (audit / "new-questions.sha256").read_text().split()
        matches = bool(seal) and hashlib.sha256(path.read_bytes()).hexdigest() == seal[0]
    except OSError:
        matches = False
    if not matches or validate_pack(pack) or (supplied is not None and supplied != pack):
        return None
    return pack


def _johns_population(data, pk):
    """Return the independent groups and whether they cover the answered probes."""
    groups = {
        group: [p for q, p in jq.probes(data) if q["id"] in ids and not jq.is_open(p)]
        for group, ids in jq.TOPIC_GROUPS.items()
    }
    all_ids = [p["id"] for _, p in jq.probes(data)]
    grouped_ids = [p["id"] for group in groups.values() for p in group]
    answered_ids = [q["id"] for q in pk["questions"]]
    valid = not (
        len(set(all_ids)) != len(all_ids)
        or sorted(grouped_ids) != sorted(answered_ids)
        or not all_ids
    )
    return groups, valid


def _johns_reader_gaps(reader, groups, questions, audit_dir, identity):
    counts = reader.get("johns_actions_used", {})
    if not isinstance(counts, dict) or set(counts) != set(groups):
        return [f"{reader['reader']}: missing seven grouped action counts"]
    gaps = []
    if not all(
        complete(reader.get(field), questions)
        for field in ("johns_with_site", "johns_without_site")
    ):
        gaps.append(f"{reader['reader']}: incomplete John's answers")
    for group in groups:
        if not session_valid(audit_dir, reader, f"johns-{group}", counts[group], "phone", identity):
            gaps.append(f"{reader['reader']}/{group}: missing, mixed or invalid action state")
    return gaps


def score_johns(readers, data=None, audit_dir=None, identity=None):
    """Every retained probe and every independent grouped session must pass."""
    data = data if data is not None else jq.load()
    pk = jq.pack(data)
    lines, gaps = ["John's questions:"], []
    valid = reader_set(readers) and audit_dir is not None
    groups, population_valid = _johns_population(data, pk)
    if not population_valid:
        valid = False
        gaps.append("invalid or incomplete probe/group population")
    if valid:
        identity = identity or build_identity(audit_dir, readers)
        for reader in readers:
            reader_gaps = _johns_reader_gaps(reader, groups, pk["questions"], audit_dir, identity)
            if reader_gaps:
                valid = False
                gaps += reader_gaps
    else:
        gaps.append("requires five complete same-candidate readers and grouped states")
    gaps += [f"{q['id']}: {q['gap']}" for q in pk["open"]]
    for question in pk["questions"]:
        right = sum(correct(r.get("johns_with_site", {}), [question]) for r in readers)
        before = sum(correct(r.get("johns_without_site", {}), [question]) for r in readers)
        passed = valid and right >= 5 * JOHNS_PASS
        lines.append(
            f"  {question['id']}: {right}/5 right with the site, {before} without: "
            + ("PASS" if passed else "FAIL")
        )
        if not passed:
            gaps.append(f"{question['id']}: fewer than four valid readers answered correctly")
    lines += ["  gap: " + gap for gap in gaps]
    lines.append("  PASS: every probe passed" if not gaps else f"  FAIL: {len(gaps)} gaps")
    return {"johns_questions": not gaps, "johns_gaps": gaps}, lines


def _fixed_reader_passes(reader, questions, rules):
    return correct(reader.get("with_site", {}), questions) >= rules["min_correct_each"] and all(
        correct(reader.get("with_site", {}), [q]) for q in questions if q["critical"]
    )


def _score_fixed(audit, readers, questions, rules, valid, identity):
    """Score the fixed phone questions and their prior-knowledge uplift."""
    fixed_complete = valid and all(complete(r.get("with_site"), questions) for r in readers)
    fixed_states = valid and all(
        session_valid(audit, r, "phone", r.get("actions_used"), "phone", identity) for r in readers
    )
    total = sum(correct(r.get("with_site", {}), questions) for r in readers)
    each = all(_fixed_reader_passes(r, questions, rules) for r in readers)
    res = {
        "phone_test": bool(
            fixed_complete and fixed_states and each and total >= rules["min_correct_total"]
        )
    }
    lines = [
        f"Simulated phone test: {total}/60 (needs 48 total, each 9/12, all critical, "
        "complete states within 40 actions): " + ("PASS" if res["phone_test"] else "FAIL")
    ]
    prior_complete = valid and all(complete(r.get("without_site"), questions) for r in readers)
    before = sum(correct(r.get("without_site", {}), questions) for r in readers)
    res["prior_knowledge"] = bool(
        fixed_complete and fixed_states and prior_complete and total - before >= UPLIFT_MIN
    )
    lines.append(
        f"Prior knowledge: uplift {total - before}/60 (needs 20): "
        + ("PASS" if res["prior_knowledge"] else "FAIL")
    )
    return res, lines


def _score_new(audit, readers, new_pack, valid, identity):
    new = sealed_pack(audit, new_pack)
    new_ok, got = False, 0
    if new is not None:
        new_questions = new["questions"]
        got = sum(correct(r.get("new_with_site", {}), new_questions) for r in readers)
        new_ok = (
            valid
            and all(
                complete(r.get(field), new_questions)
                for r in readers
                for field in ("new_with_site", "new_without_site")
            )
            and all(
                session_valid(audit, r, "new", r.get("new_actions_used"), "phone", identity)
                for r in readers
            )
            and got / (24 * 5) >= NEW_PASS
        )
    return bool(new_ok), got


def _score_screen_reader(audit, questions, identity):
    sr = read_record(audit / "readers/SR.json")
    sr_answers = sr.get("with_site", {})
    return bool(
        sr.get("reader") == "SR"
        and complete(sr_answers, questions)
        and session_valid(audit, sr, "state", sr.get("actions_used"), "sr", identity)
        and correct(sr_answers, questions) >= SR_MIN_CORRECT
        and all(correct(sr_answers, [q]) for q in questions if q["critical"])
        and not sr.get("blockers")
    )


def score(audit_dir, pack=None, new_pack=None):
    audit = Path(audit_dir)
    pack = pack or read_record(
        Path(__file__).resolve().parent.parent / "docs/user-test/questions.json"
    )
    questions, rules = pack["questions"], pack["pass_rules"]
    paths = sorted(p for p in (audit / "readers").glob("R*.json") if re.fullmatch(r"R\d+", p.stem))
    readers = [read_record(path) for path in paths]
    valid = reader_set(readers) and all(
        path.stem == r.get("reader") for path, r in zip(paths, readers)
    )
    identity = build_identity(audit, readers) if valid else None
    res, lines = _score_fixed(audit, readers, questions, rules, valid, identity)
    new_ok, got = _score_new(audit, readers, new_pack, valid, identity)
    res["new_questions"] = new_ok
    lines.append(
        f"New questions: {got}/120 (needs 80%, valid seal and separate 40-action states): "
        + ("PASS" if new_ok else "FAIL")
    )
    res["screen_reader"] = _score_screen_reader(audit, questions, identity)
    lines.append(
        "Agent accessibility-tree stand-in: " + ("PASS" if res["screen_reader"] else "FAIL")
    )
    jres, jlines = score_johns(readers, audit_dir=audit if valid else None, identity=identity)
    res.update(jres)
    lines += jlines
    res["d11_ready_for_5"] = all(
        res[key] for key in ("phone_test", "prior_knowledge", "new_questions")
    )
    res["all_reader_standins"] = (
        res["d11_ready_for_5"] and res["screen_reader"] and res["johns_questions"]
    )
    lines.append(
        "Reader stand-ins for D11 level 5: " + ("PASS" if res["d11_ready_for_5"] else "FAIL")
    )
    lines.append(
        "Overall reader stand-ins: "
        + (
            "MET, recorded as met (simulated); not real-person comprehension evidence"
            if res["all_reader_standins"]
            else "NOT MET"
        )
    )
    return res, lines
