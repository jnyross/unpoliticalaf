"""UX heuristic checks for the five principles in docs/goal-rubric.md (T128).

Usage:
  python scripts/ux_heuristics.py                 # sample of built pages (site/)
  python scripts/ux_heuristics.py --all           # every page except figures/ and csv/
  python scripts/ux_heuristics.py --json out.json # also write the raw results

Checks are named by principle: C (clarity and simplicity), K (consistency),
F (feedback and responsiveness), A (accessibility and inclusivity) and U (user
control and error prevention). The rubric says what each one means.

Run `make build` first: this reads the built site in site/. It does not
replace `make a11y` (axe-core, tap targets, Tab order) or `make check` (figures,
links, page size). Pages are measured at 360 x 640 (phone) and 1100 x 800
(desktop), and with JavaScript off for the core answer.
"""

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

PHONE = {"width": 360, "height": 640}
DESKTOP = {"width": 1100, "height": 800}

# Thresholds. A failure is a gap to fix, not a score.
ANSWER_WITHIN_PX = 1280  # the first answer starts within two phone screens
PROSE_MIN_PX = 16  # paragraphs and list items (the 17px body text, as GOV.UK does at 16px)
OTHER_MIN_PX = 13  # table cells, labels, captions and source lines
CHART_MIN_PX = 12  # chart labels as drawn on a phone, after the SVG scale
GENERIC_LINKS = ["here", "click here", "more", "read more", "link", "this", "view", "go", "details"]
GENERIC_SUMMARIES = [
    "more",
    "show",
    "details",
    "expand",
    "open",
    "read more",
    "more info",
    "more information",
]

# Measures one page at the current viewport. `k` holds the thresholds above.
PAGE_JS = """(k) => {
  const main = document.querySelector('main') || document.body;
  const visible = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
                        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const text = e => (e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ');
  const px = e => parseFloat(getComputedStyle(e).fontSize);
  const out = {};

  // C1: one h1, near the top.
  const h1s = [...main.querySelectorAll('h1')];
  out.h1_count = h1s.length;
  out.h1_top = h1s.length ? Math.round(h1s[0].getBoundingClientRect().top + scrollY) : null;

  // C2: heading levels never skip.
  const heads = [...main.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible);
  out.heading_skips = [];
  for (let i = 1; i < heads.length; i++) {
    const a = +heads[i-1].tagName[1], b = +heads[i].tagName[1];
    if (b > a + 1) out.heading_skips.push('"' + text(heads[i]).slice(0, 50) + '" after h' + a);
  }

  // C3: the answer starts near the top.
  const answer = main.querySelector('.answer, .lede');
  out.answer_top = answer ? Math.round(answer.getBoundingClientRect().top + scrollY) : null;

  // C4: link text says where the link goes.
  out.generic_links = [...main.querySelectorAll('a[href]')].filter(visible)
                        .filter(a => k.generic_links.includes(text(a).toLowerCase())).map(text).slice(0, 5);

  // F1: each disclosure says what it reveals and shows a marker.
  const sums = [...main.querySelectorAll('details > summary')].filter(visible);
  out.summaries = sums.length;
  out.generic_summaries = sums.filter(s => k.generic_summaries.includes(text(s).toLowerCase()) || text(s).length < 4)
                            .map(text).slice(0, 5);
  out.summary_no_marker = sums.filter(s => {
    const b = getComputedStyle(s, '::before'), a = getComputedStyle(s, '::after'), m = getComputedStyle(s, '::marker');
    const drawn = v => v && !['none', 'normal', '""', ''].includes(v);
    const bordered = parseFloat(b.borderRightWidth) > 0 || parseFloat(b.borderBottomWidth) > 0;
    return !(bordered || drawn(a.content) || drawn(m.content));
  }).map(s => text(s).slice(0, 40)).slice(0, 5);

  // K1/K2: navigation, footer and home link, compared across pages by the caller.
  const nav = document.querySelector('nav.main');
  // Links are compared without their relative path, so ../spending.html and spending.html match.
  out.nav = nav ? [...nav.querySelectorAll('a')].map(a => text(a) + ' -> ' + (a.getAttribute('href') || '').replace(/^(\\.\\.\\/)+/, '')).join(' | ') : null;
  out.footer = !!document.querySelector('footer');
  out.home_link = [...document.querySelectorAll('header a.brand')].some(a => /(^|\\/)index\\.html$/.test(a.getAttribute('href') || ''));

  // U1: a way back to the top on long pages.
  out.long_page = document.documentElement.scrollHeight > 2 * innerHeight;
  out.backtop = !!document.querySelector('.backtop, a[href="#top"], a[href="#main"]');

  // U2: forms submit with a button and label their controls, so they work without JavaScript.
  out.forms = [...main.querySelectorAll('form')].map(f => ({
    submit: !!f.querySelector('button[type=submit], input[type=submit], button:not([type])'),
    labelled: [...f.querySelectorAll('select, input:not([type=hidden]):not([type=submit])')]
                .every(c => (c.labels && c.labels.length > 0) || c.getAttribute('aria-label')),
    method: (f.getAttribute('method') || 'get').toLowerCase()
  }));

  // A1: every field has a label anywhere on the page.
  out.unlabelled_fields = [...document.querySelectorAll('select, input:not([type=hidden]):not([type=submit]), textarea')]
    .filter(c => !(c.labels && c.labels.length) && !c.getAttribute('aria-label') && !c.getAttribute('aria-labelledby')).length;

  // A2: no sideways scrolling.
  out.overflow_x = document.documentElement.scrollWidth - innerWidth > 1;

  // A3: text sizes as drawn. Prose is paragraphs and list items outside source lines and small print.
  const secondary = e => e.closest('.src, .small, .dl, .more-link, .readout, .pick-status, .version, summary, figcaption, caption');
  const prose = [...main.querySelectorAll('p, li')].filter(e => visible(e) && text(e).length > 0 && !secondary(e));
  out.prose_min_px = prose.length ? Math.min(...prose.map(px)) : null;
  out.prose_small = prose.filter(e => px(e) < k.prose_min).slice(0, 3).map(e => text(e).slice(0, 40) + ' ' + px(e) + 'px');
  const other = [...main.querySelectorAll('td, th, label, figcaption, caption, summary, p.small, p.dl, .src')]
    .filter(e => visible(e) && text(e).length > 0);
  out.other_small = other.filter(e => px(e) < k.other_min).slice(0, 3).map(e => text(e).slice(0, 40) + ' ' + px(e) + 'px');

  // A4: chart labels as drawn at this width (SVG font size times the screen scale).
  const labels = [...main.querySelectorAll('svg text')].filter(t => t.getBoundingClientRect().width > 0 && text(t).length > 0);
  const drawn = labels.map(t => { const m = t.getScreenCTM(); return m ? px(t) * Math.hypot(m.a, m.b) : px(t); });
  out.chart_text_min_px = drawn.length ? Math.round(Math.min(...drawn) * 10) / 10 : null;
  out.chart_text_small = drawn.filter(v => v < k.chart_min).length;
  out.charts = main.querySelectorAll('svg[data-chart], [data-chart] svg').length;
  return out;
}"""

# Tap the first visible chart with a readout (feedback after an action) and read the readout back.
TAP_JS = """() => {
  const picked = [...document.querySelectorAll('[data-chart]')].find(el => {
    const svg = el.tagName.toLowerCase() === 'svg' ? el : el.querySelector('svg');
    // Charts inside a closed <details> have a box but are not drawn, so skip them.
    return svg && svg.getBoundingClientRect().width > 0 && !el.closest('details:not([open])')
        && el.parentNode.querySelector(':scope > p.readout');
  });
  if (!picked) return false;
  picked.setAttribute('data-ux-tap', '1');
  const svg = picked.tagName.toLowerCase() === 'svg' ? picked : picked.querySelector('svg');
  svg.scrollIntoView({block: 'center', behavior: 'instant'});
  return true;
}"""

SPOT_JS = """() => {
  const el = document.querySelector('[data-ux-tap]');
  const svg = el.tagName.toLowerCase() === 'svg' ? el : el.querySelector('svg');
  const r = svg.getBoundingClientRect();
  return {x: r.left + r.width / 2, y: r.top + r.height / 2};
}"""

READOUT_JS = """() => {
  const el = document.querySelector('[data-ux-tap]');
  const p = el && el.parentNode.querySelector(':scope > p.readout');
  return p ? p.textContent : null;
}"""


def pages_to_check(all_pages):
    pages = [
        p
        for p in sorted(SITE.rglob("*.html"))
        if not set(p.relative_to(SITE).parts) & {"figures", "csv"}
    ]
    if all_pages:
        return pages
    rng = random.Random(2026)  # fixed, so a repeat run checks the same pages
    compare = [p for p in pages if "compare" in p.parts and "spans" not in p.parts]
    spans = [p for p in pages if "spans" in p.parts]
    rest = [p for p in pages if p not in compare and p not in spans]
    return (
        rest + rng.sample(compare, min(20, len(compare))) + rng.sample(spans, min(10, len(spans)))
    )


def measure(paths):
    from playwright.sync_api import sync_playwright

    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    consts = {
        "generic_links": GENERIC_LINKS,
        "generic_summaries": GENERIC_SUMMARIES,
        "prose_min": PROSE_MIN_PX,
        "other_min": OTHER_MIN_PX,
        "chart_min": CHART_MIN_PX,
    }
    results = []
    with sync_playwright() as pw:
        browser = (
            pw.chromium.launch(executable_path=exe, args=["--no-sandbox"])
            if exe
            else pw.chromium.launch()
        )
        for path in paths:
            row = {"page": path.relative_to(SITE).as_posix()}
            if 'http-equiv="refresh"' in path.read_text(encoding="utf-8", errors="ignore")[:4000]:
                row["redirect"] = (
                    True  # a page that only forwards to another; the target is checked itself
                )
                results.append(row)
                continue
            try:
                for name, vp in (("phone", PHONE), ("desktop", DESKTOP)):
                    ctx = browser.new_context(viewport=vp, device_scale_factor=1)
                    page = ctx.new_page()
                    page.goto(path.as_uri(), wait_until="load", timeout=60000)
                    row[name] = page.evaluate(PAGE_JS, consts)
                    if name == "phone" and page.evaluate(TAP_JS):
                        page.wait_for_timeout(
                            400
                        )  # let any smooth scroll finish before reading the position
                        spot = page.evaluate(SPOT_JS)
                        before = page.evaluate(READOUT_JS) or ""
                        page.mouse.click(spot["x"], spot["y"])
                        page.wait_for_timeout(300)
                        after = page.evaluate(READOUT_JS) or ""
                        row["tap"] = {
                            "before": before,
                            "after": after,
                            "changed": after != before and any(ch.isdigit() for ch in after),
                        }
                    ctx.close()
                # U3: the h1 and the answer show with JavaScript off.
                ctx = browser.new_context(viewport=PHONE, java_script_enabled=False)
                page = ctx.new_page()
                page.goto(path.as_uri(), wait_until="load", timeout=60000)
                h1 = page.locator("main h1").first
                ans = page.locator(".answer").first
                row["nojs"] = {
                    "h1": h1.count() > 0 and bool((h1.text_content() or "").strip()),
                    "answer": ans.count() == 0 or bool((ans.text_content() or "").strip()),
                }
                ctx.close()
            except Exception as e:  # noqa: BLE001
                row["error"] = f"{e.__class__.__name__}: {str(e)[:200]}"
            results.append(row)
            print(f"measured {row['page']}", file=sys.stderr)
        browser.close()
    return results


def evaluate(results):
    """One line per check: how many pages fail it, and up to six examples."""
    checks = {}
    rows = [r for r in results if "error" not in r and not r.get("redirect")]
    n = len(rows)
    ref_nav = rows[0]["phone"]["nav"] if rows else None

    def add(name, standard, failing, total):
        checks[name] = {
            "standard": standard,
            "failing": len(failing),
            "checked": total,
            "examples": [f"{r['page']}: {why}" for r, why in failing[:6]],
        }

    add(
        "E0 pages load and measure",
        "every page loads",
        [(r, r["error"]) for r in results if "error" in r],
        len(results),
    )
    ph = lambda r: r["phone"]
    add(
        "C1 one h1, near the top",
        "one h1, within 200px of the top at 360px",
        [
            (r, f"{ph(r)['h1_count']} h1s, top {ph(r)['h1_top']}px")
            for r in rows
            if ph(r)["h1_count"] != 1 or (ph(r)["h1_top"] or 0) > 200
        ],
        n,
    )
    add(
        "C2 heading levels never skip",
        "no heading skips a level",
        [(r, "; ".join(ph(r)["heading_skips"][:2])) for r in rows if ph(r)["heading_skips"]],
        n,
    )
    # Reference pages (methods, sources, corrections, comparison spans) have no answer block and are not checked here.
    answered = [r for r in rows if ph(r)["answer_top"] is not None]
    add(
        "C3 answer near the top",
        f"on pages with an answer block, the answer starts within {ANSWER_WITHIN_PX}px at 360px",
        [
            (r, f"answer starts at {ph(r)['answer_top']}px")
            for r in answered
            if ph(r)["answer_top"] > ANSWER_WITHIN_PX
        ],
        len(answered),
    )
    add(
        "C4 link text says where it goes",
        "no link reads only 'here', 'more' or similar",
        [(r, ", ".join(ph(r)["generic_links"])) for r in rows if ph(r)["generic_links"]],
        n,
    )
    add(
        "K1 same main navigation",
        "every page has the same main navigation",
        [(r, "different navigation") for r in rows if ph(r)["nav"] != ref_nav],
        n,
    )
    add(
        "K2 footer and home link",
        "every page has a footer and a link home",
        [
            (r, "no footer" if not ph(r)["footer"] else "no home link")
            for r in rows
            if not ph(r)["footer"] or not ph(r)["home_link"]
        ],
        n,
    )
    add(
        "F1 disclosures say what they open and show a marker",
        "every closed section has a specific label and a visible marker",
        [
            (r, "; ".join(ph(r)["generic_summaries"] + ph(r)["summary_no_marker"]))
            for r in rows
            if ph(r)["generic_summaries"] or ph(r)["summary_no_marker"]
        ],
        n,
    )
    tapped = [r for r in rows if r.get("tap")]
    add(
        "F2 a tap on a chart updates its readout",
        "a tap on the first chart shows its values",
        [
            (r, f"readout stayed '{r['tap']['after'][:60]}'")
            for r in tapped
            if not r["tap"]["changed"]
        ],
        len(tapped),
    )
    add(
        "A1 every field has a label",
        "every select and input has a label",
        [
            (r, f"{ph(r)['unlabelled_fields']} unlabelled fields")
            for r in rows
            if ph(r)["unlabelled_fields"]
        ],
        n,
    )
    add(
        "A2 no sideways scrolling at 360px",
        "no horizontal page scroll at 360px",
        [(r, "page is wider than the screen") for r in rows if ph(r)["overflow_x"]],
        n,
    )
    add(
        "A3 prose at least 16px",
        f"paragraphs and list items are at least {PROSE_MIN_PX}px at 360px",
        [(r, "; ".join(ph(r)["prose_small"][:2])) for r in rows if ph(r)["prose_small"]],
        n,
    )
    add(
        "A3b table, label and caption text at least 13px",
        f"table cells, labels and captions are at least {OTHER_MIN_PX}px",
        [(r, "; ".join(ph(r)["other_small"][:2])) for r in rows if ph(r)["other_small"]],
        n,
    )
    add(
        "A4 chart labels at least 12px as drawn",
        f"chart text is at least {CHART_MIN_PX}px as drawn at 360px",
        [
            (
                r,
                f"smallest {ph(r)['chart_text_min_px']}px, {ph(r)['chart_text_small']} labels under",
            )
            for r in rows
            if ph(r)["chart_text_small"]
        ],
        n,
    )
    add(
        "U1 long pages have a way back to the top",
        "pages taller than two screens have a back-to-top link",
        [(r, "no back-to-top link") for r in rows if ph(r)["long_page"] and not ph(r)["backtop"]],
        n,
    )
    add(
        "U2 forms work without JavaScript",
        "every form has a labelled control, a submit button and uses GET",
        [
            (r, "a form lacks a button, a label, or uses POST")
            for r in rows
            if any(
                not f["submit"] or not f["labelled"] or f["method"] != "get" for f in ph(r)["forms"]
            )
        ],
        n,
    )
    add(
        "U3 the answer works without JavaScript",
        "the h1 and the answer show with scripts off",
        [
            (r, f"h1 {r['nojs']['h1']}, answer {r['nojs']['answer']}")
            for r in rows
            if not (r["nojs"]["h1"] and r["nojs"]["answer"])
        ],
        n,
    )
    return checks


def report(checks):
    lines = ["| Check | Standard | Pages failing | Pages checked |", "|---|---|---|---|"]
    lines += [
        f"| {name} | {c['standard']} | {c['failing']} | {c['checked']} |"
        for name, c in checks.items()
    ]
    lines.append("")
    for name, c in checks.items():
        if c["examples"]:
            lines.append(f"### {name}")
            lines += [f"- {e}" for e in c["examples"]]
            lines.append("")
    return "\n".join(lines)


def main():
    paths = pages_to_check("--all" in sys.argv)
    results = measure(paths)
    checks = evaluate(results)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(
            json.dumps({"checks": checks, "results": results}, indent=1)
        )
    print(f"Checked {len(paths)} pages at 360 x 640 and 1100 x 800.\n")
    print(report(checks))
    return 1 if any(c["failing"] for c in checks.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
