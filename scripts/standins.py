#!/usr/bin/env python3
"""Tools for the rubric v3 stand-ins (docs/goal-rubric.md, docs/standins/).

The stand-ins are fresh Claude sessions that play newcomers, a screen-reader
user, a fact-checker and impartiality critics. This script is what they use to
see the site, plus the scoring that turns their answers into a result. It
serves the built site/ folder (the audited commit, which the "Live site matches
main" check shows is byte-identical to the live site) on a local port.

Simulated phone reader (sees only screenshots, can only tap and scroll):

    python scripts/standins.py phone start  --state R1.json [--budget 40] [--shots DIR]
    python scripts/standins.py phone scroll --state R1.json down|up
    python scripts/standins.py phone tap    --state R1.json N
    python scripts/standins.py phone choose --state R1.json N "option text"
    python scripts/standins.py phone back   --state R1.json

Screen-reader reader (sees only what a screen reader announces):

    python scripts/standins.py sr start --state SR.json [--budget 40]
    python scripts/standins.py sr tap|choose|back --state SR.json ...

Automated accessibility checks on every main page (no reader involved):

    python scripts/standins.py keyboard [PAGE ...]   # no keyboard traps
    python scripts/standins.py summaries             # every chart has a text summary

Sealing the new question set before the readers run, and checking it after:

    python scripts/standins.py seal   QUESTIONS.json AUDIT_DIR
    python scripts/standins.py unseal QUESTIONS.json AUDIT_DIR

Scoring the readers' answers against the v3 pass bars:

    python scripts/standins.py score AUDIT_DIR
"""
import contextlib
import functools
import hashlib
import http.server
import json
import re
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PACK = ROOT / "docs" / "user-test" / "questions.json"
WIDTH, HEIGHT = 360, 640
BUDGET = 40  # actions, about 8 minutes of phone use (12 seconds each)
SECONDS_PER_ACTION = 12
STEP = HEIGHT - 80  # one scroll keeps a little of the last screen in view

NEW_PASS = 0.80          # new-question test: share right with the site
JOHNS_PASS = 0.80        # John's questions: share of readers right on each probe
UPLIFT_MIN = 20          # prior-knowledge check: extra right answers out of 60
SR_MIN_CORRECT = 9       # screen-reader reader: same bar as one phone tester

MAIN_PAGES = [
    "index.html", "spending.html", "taxes.html", "who-pays.html", "household-tax.html",
    "life/index.html", "glossary.html", "methods.html", "sources.html",
]

# Elements a phone user can tap, in page order.
TAPPABLE_JS = """
(onlyVisible) => {
  const sel = 'a[href], button, summary, select, input[type=submit], input[type=radio], input[type=checkbox], [role=button], [role=tab]';
  const out = [];
  const path = (el) => {
    const parts = [];
    while (el && el.nodeType === 1 && el !== document.body) {
      let i = 1, s = el;
      while ((s = s.previousElementSibling)) if (s.tagName === el.tagName) i++;
      parts.unshift(el.tagName.toLowerCase() + ':nth-of-type(' + i + ')');
      el = el.parentElement;
    }
    return 'body > ' + parts.join(' > ');
  };
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width === 0 || r.height === 0 || st.visibility === 'hidden' || st.display === 'none') continue;
    if (el.checkVisibility && !el.checkVisibility()) continue;  // inside a closed <details>
    if (onlyVisible && (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth)) continue;
    if (r.right <= 0 || r.bottom <= -50) continue;  // moved off screen until focused, like a skip link
    let own = '';
    if (el.labels && el.labels[0]) { const c = el.labels[0].cloneNode(true); c.querySelectorAll('select, input').forEach(x => x.remove()); own = c.textContent; }
    const named = el.getAttribute('aria-label') || own.trim();
    let label = (named || (el.tagName === 'SELECT' ? el.name : el.innerText) || el.value || '').replace(/\\s+/g, ' ').trim();
    if (!label && el.id) { const l = document.querySelector('label[for="' + el.id + '"]'); if (l) label = l.innerText.trim(); }
    let kind = el.tagName.toLowerCase();
    if (kind === 'a') kind = 'link';
    if (kind === 'summary') kind = 'expand';
    const item = {sel: path(el), kind, label: label.slice(0, 80), x: r.left + r.width / 2, y: r.top + r.height / 2,
                  left: r.left, top: r.top};
    if (kind === 'select') {
      item.options = [...el.options].map(o => o.text.trim());
      item.value = el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : '';
    }
    out.push(item);
  }
  return out;
}
"""

BADGES_JS = """
(items) => {
  const box = document.createElement('div');
  box.id = '__standin_badges';
  box.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  items.forEach((it, i) => {
    const b = document.createElement('span');
    b.textContent = String(i + 1);
    b.style.cssText = 'position:absolute;font:bold 10px/12px sans-serif;background:#ffe600;color:#000;' +
      'border:1px solid #000;padding:0 2px;left:' + Math.max(0, it.left - 4) + 'px;top:' + Math.max(0, it.top - 6) + 'px';
    box.appendChild(b);
  });
  document.body.appendChild(box);
}
"""


# ----------------------------------------------------------------- serving

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@contextlib.contextmanager
def serve(site=SITE):
    if not (site / "index.html").exists():
        sys.exit("No built site: run `make build` first.")
    handler = functools.partial(_Quiet, directory=str(site))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()


@contextlib.contextmanager
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        try:
            yield b
        finally:
            b.close()


# ----------------------------------------------------------- reader sessions

def load_state(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _same_page(a, b):
    return a.split("#")[0] == b.split("#")[0]


def _open(page, base, st):
    """Load the current page, replay this page's taps and choices, restore the scroll."""
    page.goto(base + st["url"], wait_until="load")
    for op in st["ops"]:
        loc = page.locator(op["sel"]).first
        if op["op"] == "choose":
            loc.select_option(label=op["value"])
        else:
            loc.click()
    page.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", st["scroll"])
    page.wait_for_timeout(50)


def _rel(url, base):
    return url[len(base):] if url.startswith(base) else url


def _view(page, mode, st, shots):
    """What the reader gets back after each action."""
    items = page.evaluate(TAPPABLE_JS, mode == "phone")
    st["items"] = [{k: it[k] for k in ("sel", "kind", "label")} for it in items]
    lines = [f"Page: {st['url']}", f"Actions used: {st['actions']} of {st['budget']}"]
    if mode == "phone":
        total = page.evaluate("document.documentElement.scrollHeight")
        y = page.evaluate("window.scrollY")
        st["scroll"] = y
        lines.append(f"Screen {int(y / HEIGHT + 0.5) + 1} of {max(1, -(-total // HEIGHT))}")
        page.evaluate(BADGES_JS, items)
        shots = Path(shots)
        shots.mkdir(parents=True, exist_ok=True)
        shot = shots / f"{st['reader']}-{st['actions']:02d}.png"
        page.screenshot(path=str(shot))
        page.evaluate("document.getElementById('__standin_badges').remove()")
        lines.append(f"Screenshot (open it to see the screen): {shot}")
        lines.append("Numbered things you can tap on this screen (the yellow numbers in the screenshot):")
    else:
        lines.append("What a screen reader announces on this page, in reading order:")
        lines.append(page.locator("body").aria_snapshot())
        lines.append("Numbered links and controls on this page:")
    for i, it in enumerate(items, 1):
        extra = ""
        if it["kind"] == "select":
            opts = it["options"]
            shown = ", ".join(opts) if len(opts) <= 12 else f"{opts[0]} to {opts[-1]}, {len(opts)} choices"
            extra = f" (now: {it['value']}; choices: {shown})"
        lines.append(f"  [{i}] {it['kind']}: {it['label']}{extra}")
    return "\n".join(lines)


def session(mode, args):
    if not args or "--state" not in args:
        print(__doc__)
        return 2
    action, opts, rest, i = args[0], {}, [], 1
    while i < len(args):
        if args[i].startswith("--"):
            opts[args[i]] = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    path = opts["--state"]
    opt = lambda name, default: opts.get(name, default)
    if action == "start":
        st = {"reader": Path(path).stem, "mode": mode, "budget": int(opt("--budget", BUDGET)), "actions": 0,
              "url": "index.html", "ops": [], "scroll": 0, "history": [], "log": [],
              "shots": opt("--shots", str(Path(tempfile.gettempdir()) / "standin-shots")), "items": []}
    else:
        st = load_state(path)
        if st["actions"] >= st["budget"]:
            print(f"Time is up: you have used all {st['budget']} actions. Write down your answers now.")
            return 1
    with serve() as base, browser() as b:
        ctx = b.new_context(viewport={"width": WIDTH, "height": HEIGHT}, is_mobile=True, has_touch=True,
                            device_scale_factor=1)
        page = ctx.new_page()
        if action != "start":
            _open(page, base, st)
        else:
            page.goto(base + st["url"], wait_until="load")
        note = ""
        if action == "start":
            pass
        elif action == "scroll" and mode == "phone":
            down = (rest[0] if rest else "down") == "down"
            page.evaluate("d => window.scrollTo({top: window.scrollY + d, behavior: 'instant'})", STEP if down else -STEP)
            st["actions"] += 1
            st["log"].append(f"scroll {'down' if down else 'up'}")
        elif action in ("tap", "choose"):
            n = int(rest[0])
            if not 1 <= n <= len(st["items"]):
                print(f"There is no [{n}] in the last view. Nothing happened.")
                return 1
            it = st["items"][n - 1]
            st["actions"] += 1
            before = st["url"]
            loc = page.locator(it["sel"]).first
            if action == "choose":
                value = rest[1] if len(rest) > 1 else ""
                if it["kind"] != "select":
                    print(f"[{n}] is not a list you can choose from. Nothing happened.")
                    return 1
                try:
                    loc.select_option(label=value)
                except Exception:
                    print(f"[{n}] has no choice called {value!r}. Nothing happened.")
                    return 1
                st["ops"].append({"op": "choose", "sel": it["sel"], "value": value})
                st["log"].append(f"choose [{n}] {it['label']} = {value}")
            else:
                st["log"].append(f"tap [{n}] {it['kind']}: {it['label']}")
                try:
                    loc.click(timeout=3000)
                    clicked = True
                except Exception:
                    clicked = False  # not replayed later, so the session cannot get stuck on it
                with contextlib.suppress(Exception):
                    page.wait_for_load_state("load", timeout=1500)
                page.wait_for_load_state("load")
                now = _rel(page.url, base)
                if _same_page(now, before):
                    if now == before and clicked:
                        st["ops"].append({"op": "tap", "sel": it["sel"]})
                    st["url"] = now
                else:
                    st["history"].append({"url": before, "ops": st["ops"], "scroll": st["scroll"]})
                    st["url"], st["ops"] = now, []
                    note = "(new page)"
        elif action == "back":
            st["actions"] += 1
            st["log"].append("back")
            if st["history"]:
                prev = st["history"].pop()
                st.update(url=prev["url"], ops=prev["ops"], scroll=prev["scroll"])
                _open(page, base, st)
            else:
                note = "(nothing to go back to)"
        else:
            print(__doc__)
            return 2
        out = _view(page, mode, st, st["shots"])
        ctx.close()
    save_state(path, st)
    print((note + "\n" if note else "") + out)
    if st["actions"] >= st["budget"]:
        print("That was your last action. Write down your answers now.")
    return 0


# ------------------------------------------------- automated accessibility

def keyboard(pages=None, max_tabs=400):
    """Tab through each page from the top. A trap is focus that stops moving, or
    that comes back to an earlier element before it leaves the page."""
    problems = []
    with serve() as base, browser() as b:
        page = b.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        for rel in pages or MAIN_PAGES:
            page.goto(base + rel, wait_until="load")
            total = page.evaluate("document.querySelectorAll('a[href], button, summary, select, input, [tabindex]').length")
            seen, last, stuck = [], None, 0
            for _ in range(min(max_tabs, total + 5)):
                page.keyboard.press("Tab")
                key = page.evaluate("""() => { const e = document.activeElement;
                  if (!e || e === document.body || e === document.documentElement) return null;
                  let p = [], n = e; while (n && n.parentElement) { p.unshift([...n.parentElement.children].indexOf(n)); n = n.parentElement; }
                  return p.join('.'); }""")
                if key is None:
                    break  # focus left the page: reached the end
                if key == last:
                    stuck += 1
                    if stuck >= 3:
                        problems.append(f"{rel}: focus stuck on one element after {len(seen)} tabs")
                        break
                    continue
                if seen and key == seen[0]:
                    break  # wrapped round to the first element: reached the end
                if key in seen:  # back to an earlier element without leaving the page
                    problems.append(f"{rel}: focus loops back after {len(seen)} elements, before the end of the page")
                    break
                seen.append(key)
                last, stuck = key, 0
            print(f"{rel}: Tab reached {len(seen)} elements, then left the page")
    return problems


def summaries(site=SITE):
    """Every chart on a reading page has a text summary that gives numbers, not just a title."""
    problems, n = [], 0
    chart = re.compile(r'<svg\b[^>]*role="img"[^>]*>|<ul class="(?:bars|bars change|cmp-list)"[^>]*>')
    for path in sorted(site.rglob("*.html")):
        rel = path.relative_to(site).as_posix()
        if rel.startswith("figures/"):
            continue
        for m in chart.finditer(path.read_text(encoding="utf-8")):
            tag = m.group(0)
            if 'aria-hidden="true"' in tag:
                continue
            n += 1
            label = re.search(r'aria-label="([^"]*)"', tag)
            if tag.startswith("<svg") and (not label or not re.search(r"\d", label.group(1))):
                problems.append(f"{rel}: chart has no text summary with figures")
    print(f"{n} charts checked")
    return problems


# ------------------------------------------------------------- sealing

def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seal(questions, audit_dir):
    pack = json.loads(Path(questions).read_text(encoding="utf-8"))
    bad = validate_pack(pack)
    if bad:
        print("\n".join(bad))
        return 1
    out = Path(audit_dir) / "new-questions.sha256"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"{_digest(questions)}  new-questions.json\n", encoding="utf-8")
    print(f"Sealed {len(pack['questions'])} questions: commit {out} now, and keep the questions out of the repo until every reader has answered.")
    return 0


def unseal(questions, audit_dir):
    want = (Path(audit_dir) / "new-questions.sha256").read_text(encoding="utf-8").split()[0]
    if _digest(questions) != want:
        print("The question file does not match the seal: it changed after the readers were briefed.")
        return 1
    print("The question file matches the seal.")
    return 0


def validate_pack(pack):
    bad = []
    for q in pack.get("questions", []):
        if q.get("answer") not in q.get("options", {}):
            bad.append(f"Q{q.get('id')}: answer is not one of the options")
    if not pack.get("questions"):
        bad.append("no questions")
    return bad


# ------------------------------------------------------------- scoring

def _correct(answers, questions):
    return sum(1 for q in questions if str(answers.get(str(q["id"]), "")).strip().upper() == q["answer"])


def score(audit_dir, pack=None, new_pack=None):
    """Apply the v3 pass bars to the readers' answer files. Returns (results, lines)."""
    from user_test import score as human_score  # same pass rules as the real test
    audit = Path(audit_dir)
    pack = pack or json.loads(PACK.read_text(encoding="utf-8"))
    qs = pack["questions"]
    readers = sorted(p for p in (audit / "readers").glob("R*.json") if re.fullmatch(r"R\d+", p.stem))
    readers = [json.loads(p.read_text(encoding="utf-8")) for p in readers]
    lines, res = [], {}

    # 1. Simulated five-person phone test, on the goal's own bar.
    rows = []
    for r in readers:
        row = {"participant": r["reader"], "consent": "yes", "eligible": "yes",
               "site_commit": r.get("site_commit", ""), "phone": "simulated 360x640",
               "seconds_taken": str(r.get("actions_used", 10**6) * SECONDS_PER_ACTION)}
        if r.get("actions_used", 10**6) > r.get("budget", BUDGET):
            row["seconds_taken"] = str(10**6)
        row.update({f"q{k}": v for k, v in r.get("with_site", {}).items()})
        rows.append(row)
    ok, sub = human_score(rows, pack)
    res["phone_test"] = ok
    lines += ["Simulated phone test (goal's bar):"] + ["  " + s for s in sub]

    # 2. Prior-knowledge check: the site must add at least 20 right answers out of 60.
    with_site = sum(_correct(r.get("with_site", {}), qs) for r in readers)
    without = sum(_correct(r.get("without_site", {}), qs) for r in readers)
    uplift = with_site - without
    res["prior_knowledge"] = len(readers) == pack["pass_rules"]["participants"] and uplift >= UPLIFT_MIN
    lines.append(f"Prior-knowledge check: {without}/{len(qs) * len(readers)} right without the site, "
                 f"{with_site} with it, so the site added {uplift} (needs {UPLIFT_MIN}): "
                 + ("PASS" if res["prior_knowledge"] else "FAIL"))

    # 3. Same test, new questions (sealed before the run).
    new_file = audit / "new-questions.json"
    if new_pack is None and new_file.exists():
        if unseal(new_file, audit) != 0:
            new_pack = None
            res["new_questions"] = False
            lines.append("New questions: FAIL (the file does not match its seal)")
        else:
            new_pack = json.loads(new_file.read_text(encoding="utf-8"))
    if new_pack is not None:
        nq = new_pack["questions"]
        got = sum(_correct(r.get("new_with_site", {}), nq) for r in readers)
        base = sum(_correct(r.get("new_without_site", {}), nq) for r in readers)
        possible = len(nq) * len(readers)
        share = got / possible if possible else 0
        res["new_questions"] = bool(readers) and share >= NEW_PASS
        lines.append(f"New questions: {got}/{possible} right with the site ({share:.0%}, needs {NEW_PASS:.0%}); "
                     f"{base} without it: " + ("PASS" if res["new_questions"] else "FAIL"))
    elif "new_questions" not in res:
        res["new_questions"] = False
        lines.append("New questions: FAIL (no new-questions.json in the audit folder)")

    # 4. Screen-reader reader.
    sr_file = audit / "readers" / "SR.json"
    if sr_file.exists():
        sr = json.loads(sr_file.read_text(encoding="utf-8"))
        got = _correct(sr.get("with_site", {}), qs)
        missed = [q["id"] for q in qs if q["critical"] and str(sr.get("with_site", {}).get(str(q["id"]), "")).upper() != q["answer"]]
        res["screen_reader"] = got >= SR_MIN_CORRECT and not missed and sr.get("actions_used", 10**6) <= sr.get("budget", BUDGET)
        lines.append(f"Screen-reader reader: {got}/{len(qs)}" + (f", missed critical {missed}" if missed else "")
                     + ": " + ("PASS" if res["screen_reader"] else "FAIL"))
    else:
        res["screen_reader"] = False
        lines.append("Screen-reader reader: FAIL (no readers/SR.json)")

    # 5. John's questions (docs/johns-questions/): every probe must be answered on the site,
    # and on each one at least 80% of the readers must be right with the site.
    jres, jlines = score_johns(readers)
    res.update(jres)
    lines += jlines

    d11 = 5 if res["phone_test"] and res["prior_knowledge"] and res["new_questions"] else None
    res["d11_ready_for_5"] = d11 == 5
    lines.append("Reader stand-ins for D11 level 5: " + ("all PASS, recorded as met (simulated)" if d11 else "not all passed"))
    return res, lines


def score_johns(readers, data=None):
    """Score readers on John's questions. Returns (results, lines); every failure is a gap."""
    import johns_questions as jq
    data = data or jq.load()
    pk = jq.pack(data)
    lines, gaps = ["John's questions:"], []
    for o in pk["open"]:
        gaps.append(f"{o['id']}: {o['gap']}")
    for q in pk["questions"]:
        right = sum(1 for r in readers
                    if str(r.get("johns_with_site", {}).get(q["id"], "")).strip().upper() == q["answer"])
        before = sum(1 for r in readers
                     if str(r.get("johns_without_site", {}).get(q["id"], "")).strip().upper() == q["answer"])
        ok = bool(readers) and right / len(readers) >= JOHNS_PASS
        lines.append(f"  {q['id']}: {right}/{len(readers)} right with the site, {before} without: "
                     + ("PASS" if ok else "FAIL"))
        if not ok:
            gaps.append(f"{q['id']}: readers could not answer \"{q['question']}\" from the site "
                        f"({right} of {len(readers)} right); see their confusion notes.")
    lines += [f"  open, not on the site yet: {o['id']}" for o in pk["open"]]
    passed = not gaps
    lines.append("  " + ("PASS: the site answers every one of John's questions" if passed
                         else f"FAIL: {len(gaps)} gaps"))
    lines += ["  gap: " + g for g in gaps]
    return {"johns_questions": passed, "johns_gaps": gaps}, lines


# ------------------------------------------------------------------ main

def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd in ("phone", "sr"):
        return session(cmd, argv[2:])
    if cmd == "keyboard":
        problems = keyboard(argv[2:] or None)
        print("\n".join(problems) or "No keyboard traps.")
        return 1 if problems else 0
    if cmd == "summaries":
        problems = summaries()
        print("\n".join(problems) or "Every chart has a text summary with figures.")
        return 1 if problems else 0
    if cmd == "seal" and len(argv) == 4:
        return seal(argv[2], argv[3])
    if cmd == "unseal" and len(argv) == 4:
        return unseal(argv[2], argv[3])
    if cmd == "score" and len(argv) == 3:
        res, lines = score(argv[2])
        print("\n".join(lines))
        Path(argv[2], "reader-scores.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        return 0 if res["d11_ready_for_5"] and res["screen_reader"] and res["johns_questions"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
