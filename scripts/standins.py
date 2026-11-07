#!/usr/bin/env python3
"""Tools for the rubric v3 stand-ins (docs/goal-rubric.md, docs/standins/).

The stand-ins are fresh Claude sessions that play newcomers, a screen-reader
user, a fact-checker and impartiality critics. This script is what they use to
see the site, plus the scoring that turns their answers into a result. It
serves the built site/ folder (the audited commit, which the "Live site matches
main" check shows is byte-identical to the live site) on a local port.

Simulated phone reader (sees only screenshots, can only tap and scroll):

    python scripts/standins.py phone start  --state R1-phone.json [--budget 40] [--shots DIR]
    python scripts/standins.py phone scroll --state R1-phone.json down|up
    python scripts/standins.py phone tap    --state R1-phone.json N
    python scripts/standins.py phone choose --state R1-phone.json N "option text"
    python scripts/standins.py phone back   --state R1-phone.json

Screen-reader reader (sees only what a screen reader announces):

    python scripts/standins.py sr start --state SR-state.json [--budget 40]
    python scripts/standins.py sr tap|choose|back --state SR-state.json ...

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
from standin_score import (  # noqa: E402, F401 (public scoring API)
    BUDGET,
    score,
    score_johns,
    validate_pack,
)

STEP = HEIGHT - 80  # one scroll keeps a little of the last screen in view

MAIN_PAGES = [
    "index.html",
    "spending.html",
    "taxes.html",
    "who-pays.html",
    "household-tax.html",
    "life/index.html",
    "glossary.html",
    "methods.html",
    "sources.html",
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
        if "y" in op:  # some controls (the floating menu) only show once the page is scrolled
            page.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", op["y"])
            page.wait_for_timeout(50)
        loc = page.locator(op["sel"]).first
        with contextlib.suppress(Exception):  # a replay that fails must not lock the session
            if op["op"] == "choose":
                loc.select_option(label=op["value"], timeout=3000)
            else:
                loc.click(timeout=3000)
    page.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", st["scroll"])
    page.wait_for_timeout(50)


def _rel(url, base):
    return url[len(base) :] if url.startswith(base) else url


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
        lines.append(
            "Numbered things you can tap on this screen (the yellow numbers in the screenshot):"
        )
    else:
        lines.append("What a screen reader announces on this page, in reading order:")
        lines.append(page.locator("body").aria_snapshot())
        lines.append("Numbered links and controls on this page:")
    for i, it in enumerate(items, 1):
        extra = ""
        if it["kind"] == "select":
            opts = it["options"]
            shown = (
                ", ".join(opts)
                if len(opts) <= 12
                else f"{opts[0]} to {opts[-1]}, {len(opts)} choices"
            )
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
    manifest = SITE / "build.json"
    try:
        site_commit = json.loads(manifest.read_text())["commit"]
        build_digest = _digest(manifest)
        if not site_commit or site_commit == "unknown":
            raise ValueError("unidentified build")
    except (OSError, ValueError, KeyError):
        print("Build with an identified source commit before starting reader sessions.")
        return 1
    if action == "start":
        if Path(path).exists():
            print("Refusing to overwrite an existing reader state; use a fresh session path.")
            return 1
        st = {
            "reader": Path(path).stem,
            "mode": mode,
            "budget": int(opt("--budget", BUDGET)),
            "actions": 0,
            "url": "index.html",
            "ops": [],
            "scroll": 0,
            "history": [],
            "log": [],
            "shots": opt("--shots", str(Path(tempfile.gettempdir()) / "standin-shots")),
            "items": [],
            "site_commit": site_commit,
            "build_digest": build_digest,
        }
        if st["budget"] != BUDGET:
            print("Reader sessions require the approved 40-action budget.")
            return 1
    else:
        st = load_state(path)
        if (st.get("site_commit"), st.get("build_digest"), st.get("mode")) != (
            site_commit,
            build_digest,
            mode,
        ):
            print("The built candidate or reader mode changed; start a fresh session.")
            return 1
        if st["actions"] >= st["budget"]:
            print(
                f"Time is up: you have used all {st['budget']} actions. Write down your answers now."
            )
            return 1
    with serve() as base, browser() as b:
        ctx = b.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=1,
        )
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
            page.evaluate(
                "d => window.scrollTo({top: window.scrollY + d, behavior: 'instant'})",
                STEP if down else -STEP,
            )
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
                    st["log"].append(f"failed choose [{n}]: not a select")
                    save_state(path, st)
                    print(f"[{n}] is not a list you can choose from. Nothing happened.")
                    return 1
                try:
                    loc.select_option(label=value)
                except Exception:
                    st["log"].append(f"failed choose [{n}]: unavailable option")
                    save_state(path, st)
                    print(f"[{n}] has no choice called {value!r}. Nothing happened.")
                    return 1
                st["ops"].append(
                    {
                        "op": "choose",
                        "sel": it["sel"],
                        "value": value,
                        "y": page.evaluate("window.scrollY"),
                    }
                )
                st["log"].append(f"choose [{n}] {it['label']} = {value}")
            else:
                st["log"].append(f"tap [{n}] {it['kind']}: {it['label']}")
                y_before = page.evaluate("window.scrollY")
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
                        st["ops"].append({"op": "tap", "sel": it["sel"], "y": y_before})
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
            total = page.evaluate(
                "document.querySelectorAll('a[href], button, summary, select, input, [tabindex]').length"
            )
            seen, last, stuck = [], None, 0
            for _ in range(min(max_tabs, total + 5)):
                page.keyboard.press("Tab")
                key = page.evaluate(
                    """() => { const e = document.activeElement;
                  if (!e || e === document.body || e === document.documentElement) return null;
                  let p = [], n = e; while (n && n.parentElement) { p.unshift([...n.parentElement.children].indexOf(n)); n = n.parentElement; }
                  return p.join('.'); }"""
                )
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
                    problems.append(
                        f"{rel}: focus loops back after {len(seen)} elements, before the end of the page"
                    )
                    break
                seen.append(key)
                last, stuck = key, 0
            print(f"{rel}: Tab reached {len(seen)} elements, then left the page")
    return problems


def summaries(site=SITE):
    """Every chart on a reading page has a text summary that gives numbers, not just a title."""
    problems, n = [], 0
    chart = re.compile(
        r'<svg\b[^>]*role="img"[^>]*>|<ul class="(?:bars|bars change|cmp-list)"[^>]*>'
    )
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
    print(
        f"Sealed {len(pack['questions'])} questions: commit {out} now, and keep the questions out of the repo until every reader has answered."
    )
    return 0


def unseal(questions, audit_dir):
    try:
        want = (Path(audit_dir) / "new-questions.sha256").read_text(encoding="utf-8").split()[0]
        matches = _digest(questions) == want
    except (OSError, IndexError):
        matches = False
    if not matches:
        print(
            "The question file does not match the seal: it changed after the readers were briefed."
        )
        return 1
    print("The question file matches the seal.")
    return 0


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
        Path(argv[2], "reader-scores.json").write_text(
            json.dumps(res, indent=1) + "\n", encoding="utf-8"
        )
        return 0 if res["all_reader_standins"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
