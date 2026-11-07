"""Accessibility side-by-side: measure pages from this site and from GOV.UK and ONS
the same way, so the results can be compared.

Usage:
  python scripts/a11y_benchmark.py                 # this site's built pages (site/)
  python scripts/a11y_benchmark.py --benchmarks    # GOV.UK and ONS pages (needs network)
  python scripts/a11y_benchmark.py --json out.json # also write the raw results
  python scripts/a11y_benchmark.py --strict        # fail on a keyboard or tap-target problem (make a11y)

For each page, at a 360 x 640 phone viewport, it records:

1. Keyboard: presses Tab until focus returns to the top (or 600 presses) and
   records every stop: whether the first stop is a skip link, how many presses
   reach the main content, stops with no visible focus style, stops on
   hidden or off-screen elements, and whether the skip link moves focus into
   the main content.
2. Charts: the accessibility tree (as Chromium exposes it to screen readers)
   for each chart (svg, figure or bar list), its role, name and how many
   separate text pieces a screen reader would read out.
3. Tap targets: the size of every link, button, summary, form control and
   focusable element. Under 24 x 24 CSS pixels fails WCAG 2.2 success
   criterion 2.5.8 (AA) unless it is a link inside a sentence or has enough
   space around it. Under 44 x 44 misses 2.5.5 (AAA), which GOV.UK's design
   system aims for on buttons and form controls.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

OURS = [
    "index.html",
    "spending.html",
    "taxes.html",
    "who-pays.html",
    "household-tax.html",
    "life/index.html",
    "life/earnings.html",
    "life/compare/2010-2025.html",
    "life/2015.html",
    "methods.html",
]

BENCHMARKS = [
    ("GOV.UK", "https://www.gov.uk/income-tax-rates"),
    (
        "GOV.UK",
        "https://www.gov.uk/government/statistics/public-spending-statistics-release-july-2025",
    ),
    (
        "GOV.UK",
        "https://www.gov.uk/government/publications/how-public-spending-was-calculated-in-your-tax-summary",
    ),
    (
        "ONS",
        "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2025",
    ),
    (
        "ONS",
        "https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/theeffectsoftaxesandbenefitsonhouseholdincome/2024",
    ),
    (
        "ONS",
        "https://www.ons.gov.uk/peoplepopulationandcommunity/housing/bulletins/housingaffordabilityinenglandandwales/2025",
    ),
]

# Describes the element that has focus now.
FOCUS_JS = """() => {
  const e = document.activeElement;
  if (!e || e === document.body) return null;
  const r = e.getBoundingClientRect(), s = getComputedStyle(e);
  const main = document.querySelector('main, [role=main], #main, #main-content');
  // A visible focus style: an outline, a box-shadow, or a change of background,
  // colour or border compared with the same element when it is not focused.
  const focused = {o: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0,
                   bs: s.boxShadow, bg: s.backgroundColor, c: s.color, bd: s.borderBottomColor + s.borderBottomWidth,
                   td: s.textDecorationLine + s.textDecorationThickness};
  return {tag: e.tagName.toLowerCase(), role: e.getAttribute('role'), cls: (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) || '',
          text: (e.getAttribute('aria-label') || e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60),
          href: e.getAttribute('href'), w: r.width, h: r.height, top: r.top, left: r.left,
          inMain: !!(main && main.contains(e)), focused,
          visible: r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && r.right > 0 && r.left < innerWidth};
}"""

# Style of the same element with focus moved away, to compare with FOCUS_JS.
BLUR_JS = """() => {
  const e = document.activeElement; if (!e || e === document.body) return null;
  window.__bench = e; e.blur(); const s = getComputedStyle(e);
  const r = {bs: s.boxShadow, bg: s.backgroundColor, c: s.color, bd: s.borderBottomColor + s.borderBottomWidth,
             td: s.textDecorationLine + s.textDecorationThickness};
  e.focus({preventScroll: true});
  return r;
}"""

sys.path.insert(0, str(ROOT))
from builder.check import TARGETS_JS  # noqa: E402  (shared with the CI check)


CHARTS_JS = """() => {
  const els = [...document.querySelectorAll('main svg, main figure, main ul.bars, main ul.cmp-list, main [role=img], main canvas, main .highcharts-container, main iframe')];
  // Keep the outermost element of each chart.
  return els.filter(e => !els.some(o => o !== e && o.contains(e)))
    .filter(e => e.getBoundingClientRect().height > 40)
    .slice(0, 6).map((e, i) => { e.setAttribute('data-bench', String(i)); return i; });
}"""


def walk_keyboard(page, limit=600):
    stops, seen_top = [], None
    page.evaluate("window.scrollTo(0,0); document.activeElement && document.activeElement.blur()")
    page.keyboard.press("Tab")
    for _ in range(limit):
        info = page.evaluate(FOCUS_JS)
        if info is None:
            break
        key = (
            info["tag"],
            info["text"],
            info["href"],
            round(info["top"] + page.evaluate("scrollY")),
        )
        if seen_top is None:
            seen_top = key
        elif key == seen_top:
            break
        info["key"] = key
        f, un = info["focused"], page.evaluate(BLUR_JS) or {}
        info["styled"] = f["o"] or not all(f[k] == un.get(k) for k in ("bs", "bg", "c", "bd", "td"))
        stops.append(info)
        page.keyboard.press("Tab")
    no_style = [s for s in stops if not s["styled"]]
    first_main = next((i + 1 for i, s in enumerate(stops) if s["inMain"]), None)
    skip = (
        stops[0]
        if stops and "skip" in (stops[0]["text"].lower() + str(stops[0]["cls"]).lower())
        else None
    )
    skip_works = None
    if skip:
        page.evaluate(
            "window.scrollTo(0,0); document.activeElement && document.activeElement.blur()"
        )
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        page.keyboard.press("Tab")
        after = page.evaluate(FOCUS_JS)
        skip_works = bool(after and after["inMain"])
    hidden = [s for s in stops if not s["visible"]]
    return {
        "stops": len(stops),
        "skip_first": bool(skip),
        "skip_works": skip_works,
        "presses_to_main": first_main,
        "no_focus_style": len(no_style),
        "sampled": len(stops),
        "no_focus_examples": [f"{s['tag']} '{s['text'][:40]}'" for s in no_style[:5]],
        "hidden_stops": len(hidden),
        "hidden_examples": [f"{s['tag']} '{s['text'][:40]}'" for s in hidden[:5]],
    }


def charts(page):
    out = []
    for i in page.evaluate(CHARTS_JS):
        loc = page.locator(f"[data-bench='{i}']")
        try:
            snap = loc.aria_snapshot(timeout=5000)
        except Exception as e:  # noqa: BLE001
            snap = f"(no snapshot: {e.__class__.__name__})"
        lines = [l for l in snap.splitlines() if l.strip()]
        tag = loc.evaluate(
            "e => e.tagName.toLowerCase() + (e.getAttribute('role') ? '[role=' + e.getAttribute('role') + ']' : '')"
        )
        has_table = loc.evaluate(
            """e => { const f = e.closest('figure, section, div') || e.parentElement;
            let n = f; for (let k = 0; k < 4 && n; k++, n = n.parentElement) { if (n.querySelector('table')) return true; } return false; }"""
        )
        out.append(
            {
                "element": tag,
                "tree_lines": len(lines),
                "tree": "\n".join(lines[:12]),
                "table_nearby": has_table,
            }
        )
    return out


def targets(page):
    ts = page.evaluate(TARGETS_JS)
    small = [t for t in ts if (t["w"] < 24 or t["h"] < 24) and not t["inline"] and not t["spaced"]]
    under44 = [t for t in ts if (t["w"] < 44 or t["h"] < 44) and not t["inline"]]
    return {
        "targets": len(ts),
        "inline_links": sum(t["inline"] for t in ts),
        "fail_2_5_8": len(small),
        "fail_examples": [f"{t['tag']} '{t['text'][:30]}' {t['w']}x{t['h']}" for t in small[:6]],
        "under_44": len(under44),
        "under_44_examples": [
            f"{t['tag']} '{t['text'][:30]}' {t['w']}x{t['h']}" for t in under44[:6]
        ],
    }


def measure(urls):
    from playwright.sync_api import sync_playwright

    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    results = []
    with sync_playwright() as pw:
        browser = (
            pw.chromium.launch(executable_path=exe, args=["--no-sandbox"])
            if exe
            else pw.chromium.launch()
        )
        ctx = browser.new_context(
            viewport={"width": 360, "height": 640},
            device_scale_factor=2,
            has_touch=False,
            user_agent="Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Mobile Safari/537.36",
        )
        for who, url in urls:
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="load", timeout=60000)
                page.wait_for_timeout(1500)
                # Dismiss cookie banners so they do not change the keyboard path.
                for sel in [
                    "button:has-text('Accept additional cookies')",
                    "button:has-text('Reject additional cookies')",
                    "button:has-text('Accept all cookies')",
                    "button:has-text('Reject')",
                    ".ons-js-reject-cookies",
                ]:
                    b = page.locator(sel).first
                    if b.count() and b.is_visible():
                        b.click()
                        page.wait_for_timeout(500)
                        break
                r = {"who": who, "url": url, "title": page.title()}
                r["keyboard"] = walk_keyboard(page)
                page.reload(wait_until="load")
                page.wait_for_timeout(800)
                r["charts"] = charts(page)
                r["tap"] = targets(page)
            except Exception as e:  # noqa: BLE001
                r = {"who": who, "url": url, "error": f"{e.__class__.__name__}: {str(e)[:200]}"}
            results.append(r)
            page.close()
        browser.close()
    return results


def report(results):
    lines = [
        "| Site | Page | Tab stops | Skip link first / works | Presses to main | No focus style | Hidden stops | Targets failing 2.5.8 | Under 44px (not in text) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        name = r["url"].rstrip("/").split("/")[-1] or r["url"]
        if "error" in r:
            lines.append(f"| {r['who']} | {name} | error: {r['error']} |||||||")
            continue
        k, t = r["keyboard"], r["tap"]
        lines.append(
            f"| {r['who']} | {name} | {k['stops']} | {'yes' if k['skip_first'] else 'no'} / {k['skip_works']} | {k['presses_to_main']} | "
            f"{k['no_focus_style']} of {k['sampled']} | {k['hidden_stops']} | {t['fail_2_5_8']} of {t['targets']} | {t['under_44']} |"
        )
    lines.append("")
    for r in results:
        if "error" in r:
            continue
        lines.append(f"### {r['who']}: {r['title']}\n\n{r['url']}\n")
        k, t = r["keyboard"], r["tap"]
        if k["no_focus_examples"]:
            lines.append("- No focus style: " + "; ".join(k["no_focus_examples"]))
        if k["hidden_examples"]:
            lines.append("- Hidden tab stops: " + "; ".join(k["hidden_examples"]))
        if t["fail_examples"]:
            lines.append("- Under 24px: " + "; ".join(t["fail_examples"]))
        if t["under_44_examples"]:
            lines.append("- Under 44px: " + "; ".join(t["under_44_examples"]))
        for i, c in enumerate(r["charts"]):
            lines.append(
                f"- Chart {i + 1}: `{c['element']}`, {c['tree_lines']} lines in the accessibility tree, table nearby: {c['table_nearby']}"
            )
            lines.append("\n```\n" + c["tree"] + "\n```")
        lines.append("")
    return "\n".join(lines)


def main():
    if "--benchmarks" in sys.argv:
        urls = BENCHMARKS
    else:
        urls = [("Unpolitical", (SITE / p).as_uri()) for p in OURS]
    results = measure(urls)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(results, indent=1))
    print(report(results))
    if "--strict" in sys.argv:
        bad = []
        for r in results:
            if "error" in r:
                bad.append(f"{r['url']}: {r['error']}")
                continue
            k, t = r["keyboard"], r["tap"]
            name = r["url"].split("/site/")[-1]
            if not (k["skip_first"] and k["skip_works"]):
                bad.append(f"{name}: the first Tab stop is not a working skip link")
            if k["no_focus_style"]:
                bad.append(
                    f"{name}: {k['no_focus_style']} Tab stops show no focus style: {k['no_focus_examples']}"
                )
            if k["hidden_stops"]:
                bad.append(
                    f"{name}: {k['hidden_stops']} Tab stops are hidden: {k['hidden_examples']}"
                )
            if t["fail_2_5_8"]:
                bad.append(
                    f"{name}: {t['fail_2_5_8']} tap targets under 24px: {t['fail_examples']}"
                )
        for b in bad:
            print("FAIL", b, file=sys.stderr)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
