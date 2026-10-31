"""Check every built HTML page with bundled axe-core and local headless Chromium.

No browser or JavaScript is downloaded here. Install the pinned Python dependencies
with make setup and provide Chrome/Chromium in the check environment.
"""

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
from pathlib import Path
import json
import shutil
import sys
from threading import Thread
from time import monotonic, sleep
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
WIDTHS = (360, 1100)
TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")


def find_chrome():
    for name in ("chromium", "chromium-browser", "google-chrome",
                 "google-chrome-stable", "chrome"):
        binary = shutil.which(name)
        if binary:
            return binary
    for binary in ("/opt/google/chrome/chrome", "/opt/chromium/chrome"):
        if Path(binary).is_file():
            return binary
    raise RuntimeError("Chrome/Chromium not found. Install it in the check environment; "
                       "the accessibility check cannot be skipped.")


def bundled_axe():
    # This pinned pip package ships axe-core as package data. Read that local
    # copy directly so we can select all required WCAG tags, including 2.2 AA.
    spec = find_spec("axe_playwright_python")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Bundled axe-core is missing; run make setup.")
    package = Path(next(iter(spec.submodule_search_locations)))
    for name in ("axe.min.js", "axe.js"):
        candidates = sorted(package.rglob(name))
        if candidates:
            return candidates[0].read_text(encoding="utf-8")
    raise RuntimeError("The installed axe-playwright-python package has no bundled axe-core.")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextmanager
def serve_site():
    handler = partial(QuietHandler, directory=str(SITE))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def check_payer_browser(page, data):
    """Bind the browser's core content and links to the checked public projection."""
    if page.locator("h1").all_text_contents() != ["Who pays tax?"]:
        raise RuntimeError("Payer browser heading changed")
    headings = page.locator("main h2")
    if headings.all_text_contents() != [
            "Who owed Income Tax in 2023/24?",
            "How do taxes compare with household income?",
            "Who sends the tax, and who bears its cost?",
            "Where can I check the numbers?"]:
        raise RuntimeError("Payer browser section headings changed")
    if not all(headings.nth(i).is_visible() for i in range(headings.count())):
        raise RuntimeError("Payer browser section heading hidden")
    figures = page.locator("data[data-payer-id]")
    if figures.count() != len(data["values"]):
        raise RuntimeError("Payer browser figure set changed")
    for entry in data["values"]:
        figure = page.locator(f'data[data-payer-id="{entry["id"]}"]')
        if (figure.count() != 1 or not figure.is_visible() or
                figure.inner_text() != f'{entry["value"]:.1f}%'):
            raise RuntimeError("Payer browser value missing or changed: " + entry["id"])
        for attribute, field in (("value", "value"), ("data-denominator", "denominator"),
                                 ("data-status", "status"), ("data-population", "population")):
            if figure.get_attribute(attribute) != str(entry[field]):
                raise RuntimeError("Payer browser value metadata changed: " + entry["id"])
    for sid in ("hmrc", "ons"):
        for selector in (f'#{sid}-source-note a', f'#{sid}-sources a'):
            link = page.locator(selector)
            if link.count() != 1 or link.get_attribute("href") != data["sources"][sid]["url"]:
                raise RuntimeError("Payer browser workbook route changed: " + selector)
        if not page.locator(f'#{sid}-source-note a').is_visible():
            raise RuntimeError("Payer browser adjacent source link hidden")
    interpretations = page.locator('[data-payer-interpretation]')
    if interpretations.count() != 2:
        raise RuntimeError("Payer browser interpretation set changed")
    for sid, panel, caption, denominator, copy in (
        ("hmrc", "income-tax", "hmrc-table", "Total Income Tax liabilities",
         "These are shares of total Income Tax due. They are not the Income Tax rate of any person."),
        ("ons", "household-taxes", "ons-income-table", "Gross household income",
         "This is the group's combined taxes as a share of its gross household income. "
         "It is not one person's Income Tax rate."),
    ):
        paragraph = page.locator(f'[data-payer-interpretation="{sid}"]')
        if (paragraph.count() != 1 or not paragraph.is_visible() or
                " ".join(paragraph.inner_text().split()) != copy or
                not paragraph.evaluate("""(node, expected) => {
                    const chart = node.nextElementSibling;
                    const table = chart?.nextElementSibling;
                    return node.tagName === 'P' && node.parentElement.id === expected.panel &&
                        chart?.getAttribute('data-chart-denominator') === expected.denominator &&
                        table?.getAttribute('aria-labelledby') === expected.caption &&
                        !!table.querySelector('table caption#' + expected.caption);
                }""", {"panel": panel, "caption": caption, "denominator": denominator})):
            raise RuntimeError("Payer browser interpretation copy, panel or adjacency changed: " + sid)
    download = page.locator('#payer-sources a[href="data/payers.json"]')
    if download.count() != 1 or not download.is_visible():
        raise RuntimeError("Payer browser selected-data download missing")


def check_basics_browser(page, *, expanded=False):
    """Check required guidance text, including clipping and ancestor concealment."""
    modules = page.locator('[data-basics], #tax-guidance, [data-payer-definition], [data-payer-interpretation], #spending-vintage-note, #fiscal-glossary')
    for index in range(modules.count()):
        module = modules.nth(index)
        if not module.is_visible():
            raise RuntimeError("Basics container is not visible")
        interpretation = module.get_attribute('data-payer-interpretation')
        if interpretation is not None:
            # Inspect the paragraph itself, not just any descendant elements.
            targets = module
        elif module.get_attribute('data-payer-definition') == 'tax-types':
            targets = page.locator('[data-payer-definition], [data-payer-definition] span, [data-payer-definition] a')
        elif module.get_attribute('id') == 'spending-vintage-note':
            targets = page.locator('#spending-vintage-note, #spending-vintage-note cite, #spending-vintage-note data')
        else:
            targets = module.locator('p, dt, h2, h3, summary, a, code, [data-guidance-source]')
        for target_index in range(targets.count()):
            target = targets.nth(target_index)
            closed = target.evaluate("""node => {
                for (let p = node.parentElement; p; p = p.parentElement) {
                    if (p.tagName === 'DETAILS' &&
                        node.hasAttribute('data-payer-interpretation')) return true;
                    if (p.tagName === 'DETAILS' && !p.open &&
                        !p.querySelector(':scope > summary')?.contains(node)) return true;
                }
                return false;
            }""")
            if closed and interpretation is not None:
                raise RuntimeError("Payer interpretation must stay outside disclosures")
            if closed and not expanded:
                continue
            if not target.is_visible():
                raise RuntimeError("Basics claim/heading is not visible")
            visible = target.evaluate("""node => {
                const box = node.getBoundingClientRect();
                const tolerance = 1;
                if (box.width <= 0 || box.height <= 0 ||
                    box.left < -tolerance ||
                    box.right > document.documentElement.clientWidth + tolerance ||
                    box.top + window.scrollY < -tolerance) return false;
                for (let p = node; p; p = p.parentElement) {
                    const css = getComputedStyle(p);
                    if (p.inert || p.hasAttribute('hidden') || p.hasAttribute('popover') ||
                        p.getAttribute('aria-hidden') === 'true' || Number(css.opacity) <= 0 ||
                        css.display === 'none' || css.visibility !== 'visible' ||
                        css.clip !== 'auto' || css.clipPath !== 'none' ||
                        css.contentVisibility === 'hidden') return false;
                    const clips = value => /^(hidden|clip|auto|scroll)$/.test(value);
                    if (p === node &&
                        ((clips(css.overflowX) && p.scrollWidth > p.clientWidth + tolerance) ||
                         (clips(css.overflowY) && p.scrollHeight > p.clientHeight + tolerance))) return false;
                    if (p !== node) {
                        // Positive layout boxes can still be outside an
                        // ancestor's painted scroll/clip area. Do not compare
                        // vertical bounds to the viewport: readers may scroll.
                        const bounds = p.getBoundingClientRect();
                        const left = bounds.left + p.clientLeft;
                        const top = bounds.top + p.clientTop;
                        if ((clips(css.overflowX) &&
                             (box.left < left - tolerance ||
                              box.right > left + p.clientWidth + tolerance)) ||
                            (clips(css.overflowY) &&
                             (box.top < top - tolerance ||
                              box.bottom > top + p.clientHeight + tolerance))) return false;
                    }
                }
                return true;
            }""")
            if not visible:
                raise RuntimeError("Basics claim/heading is concealed by an ancestor")


def check_basics_browser_guards(browser):
    """Real-layout regressions; mocks cannot establish CSS clipping behaviour."""
    fixture = """<!doctype html><html lang="en-GB"><body><main>
<section data-basics="taxes"><h2>Tax definitions</h2>
<dl><dt>Income Tax</dt><dd><p data-basics-claim="income">Tax on income.
<a href="#income-source">Guidance: Overview</a></p></dd></dl>
<p data-basics-scope="ct">The OBR group also includes related charges.</p>
<details><summary>More rules</summary><p>Required disclosure explanation.</p></details>
</section>
<section id="interpretation-hmrc"><p data-payer-interpretation="hmrc">These are shares of total Income Tax due. They are not the Income Tax rate of any person.</p></section>
<section id="interpretation-ons"><p data-payer-interpretation="ons">This is the group's combined taxes as a share of its gross household income. It is not one person's Income Tax rate.</p></section>
<p data-payer-definition="tax-types">Direct taxes come out of income. Indirect taxes are paid through spending.
<span>Sources: <a data-definition-source="ons_bulletin" href="#glossary">ONS glossary</a>;
<a data-definition-source="ons_method" href="#post-tax-income">ONS technical report</a></span></p>
<p id="spending-vintage-note"><cite>OBR vintage</cite> shows <data>one GDP share</data>.
<cite>PESA vintage</cite> shows <data>another GDP share</data>. The source vintages and GDP bases differ.</p>
<dl id="fiscal-glossary"><dt>ONS definitions</dt><dd id="ons-tax-definitions">
<p>The same direct and indirect tax definitions.</p>
<p>Sources: <a href="#glossary">ONS glossary</a>; <a href="#post-tax-income">ONS technical report</a></p>
</dd></dl>
<section id="tax-guidance"><h2>Guidance sources</h2>
<details><summary>Source records</summary>
<ul><li data-guidance-source="income-tax"><a href="#source">Retained source locator</a>
Original response SHA-256: <code>0123456789abcdef</code>.</li></ul>
</details></section>
</main></body></html>"""
    mutations = (
        ("main", "node.style.opacity = '0'"),
        ("main", "node.inert = true"),
        ("main", "node.setAttribute('popover', 'auto')"),
        ("main", "node.style.cssText = 'height:1px;overflow:hidden'"),
        ("main", "node.style.cssText = 'max-height:1px;overflow:clip'"),
        ("main", "node.style.cssText = 'position:absolute;clip:rect(0px,1px,1px,0px)'"),
        ("main", "node.style.clipPath = 'inset(100%)'"),
        ("main", "node.style.transform = 'translateX(-200vw)'"),
        ("main", "node.style.transform = 'translateX(200vw)'"),
        ("#fiscal-glossary > dt", "node.style.opacity = '0'"),
        ("#ons-tax-definitions p:first-child", "node.style.clipPath = 'inset(100%)'"),
        ("#ons-tax-definitions a:first-child", "node.style.opacity = '0'"),
        ("#ons-tax-definitions", "node.style.opacity = '0'"),
        ("#spending-vintage-note", "node.style.opacity = '0'"),
        ("#spending-vintage-note", "node.style.cssText = 'height:1px;overflow:hidden'"),
        ("#spending-vintage-note cite:first-of-type", "node.style.opacity = '0'"),
        ("#spending-vintage-note cite:last-of-type", "node.style.visibility = 'hidden'"),
        ("#spending-vintage-note data:first-of-type", "node.style.opacity = '0'"),
        ("#spending-vintage-note data:last-of-type", "node.style.clipPath = 'inset(100%)'"),
        ("[data-payer-definition] span", "node.style.opacity = '0'"),
        ('[data-definition-source="ons_bulletin"]', "node.style.opacity = '0'"),
        ('[data-definition-source="ons_method"]', "node.style.clipPath = 'inset(100%)'"),
        ("[data-payer-definition]", "node.style.opacity = '0'"),
        ("[data-payer-definition]", "node.style.cssText = 'height:1px;overflow:hidden'"),
        ("[data-basics-scope]", "node.style.opacity = '0'"),
        ("[data-basics-scope]", "node.style.cssText = 'height:1px;overflow:hidden'"),
        ("[data-basics] dt", "node.style.cssText = 'max-height:1px;overflow:clip'"),
        ("[data-basics] dt", "node.style.opacity = '0'"),
        ("[data-basics] details p", "node.style.opacity = '0'"),
        ("#tax-guidance li", "node.style.opacity = '0'"),
        ("[data-basics] a", "node.style.opacity = '0'"),
        ("#tax-guidance code", "node.style.visibility = 'hidden'"),
    )
    # Each required paragraph and its own panel ancestor must survive the same
    # real layout checks, including both closed and open disclosure concealment.
    interpretation_mutations = tuple(
        (selector, mutation)
        for sid in ("hmrc", "ons")
        for selector in (f'[data-payer-interpretation="{sid}"]', f'#interpretation-{sid}')
        for mutation in (
            "node.style.opacity = '0'",
            "node.style.clipPath = 'inset(100%)'",
            "node.style.cssText = 'height:1px;overflow:hidden'",
            "node.style.cssText = 'max-height:1px;overflow:clip'",
            "node.inert = true",
            "node.setAttribute('aria-hidden', 'true')",
            "node.style.transform = 'translateX(200vw)'",
            "const detail = document.createElement('details'); "
            "detail.innerHTML = '<summary>Source</summary>'; "
            "node.replaceWith(detail); detail.append(node)",
            "const detail = document.createElement('details'); detail.open = true; "
            "detail.innerHTML = '<summary>Source</summary>'; "
            "node.replaceWith(detail); detail.append(node)",
        )
    )
    mutations += interpretation_mutations
    for scripts_enabled in (True, False):
        context = browser.new_context(java_script_enabled=scripts_enabled,
                                      viewport={"width": 360, "height": 900})
        try:
            page = context.new_page()
            page.set_content(fixture)
            check_basics_browser(page)
            # Closed native disclosure text is optional until it is opened.
            page.locator('[data-basics] details p').evaluate(
                "node => { node.style.opacity = '0'; }")
            check_basics_browser(page)
            for selector, mutation in mutations:
                for expanded in (False, True):
                    page.set_content(fixture)
                    if expanded:
                        page.locator("details").evaluate_all(
                            "nodes => nodes.forEach(node => { node.open = true; })")
                    check_basics_browser(page, expanded=expanded)
                    target = page.locator(selector)
                    if target.count() != 1:
                        raise RuntimeError("Basics browser mutation target is not unique: " + selector)
                    target.evaluate("node => { " + mutation + "; }")
                    closed_content = selector in (
                        "[data-basics] details p", "#tax-guidance li", "#tax-guidance code")
                    if closed_content and not expanded:
                        check_basics_browser(page)
                        continue
                    try:
                        check_basics_browser(page, expanded=expanded)
                    except RuntimeError:
                        pass
                    else:
                        raise RuntimeError("Basics browser accepted concealment: " + selector + ": " + mutation)
        finally:
            context.close()



def settle_life_hash(page, fragment):
    """Wait for native hash handling and stable scroll, also with JS disabled."""
    deadline = monotonic() + 5
    previous, stable = None, 0
    while monotonic() < deadline:
        state = page.evaluate("({hash: location.hash, x: scrollX, y: scrollY})")
        position = (state["x"], state["y"])
        stable = stable + 1 if position == previous and state["hash"] == fragment else 0
        if stable >= 4:
            return
        previous = position
        sleep(0.02)
    raise RuntimeError("Life anchor hash/scroll did not settle: " + fragment)


def life_selected_year(page):
    value = page.locator("#life-year-select").input_value()
    selected = page.locator('[data-life-year][aria-current="true"]')
    if selected.count() != 1 or selected.get_attribute("data-life-year") != value:
        raise RuntimeError("Life selected year and annual section disagree")
    return value


def check_life_target(page, fragment, activator=None):
    target = page.locator('[id="' + fragment[1:] + '"]')
    if target.count() != 1 or not target.is_visible():
        raise RuntimeError("Life fragment target missing or hidden: " + fragment)
    if not target.evaluate("""node => {
        const box = node.getBoundingClientRect();
        return box.width > 0 && box.height > 0 &&
            box.top >= -2 && box.top < innerHeight && box.left >= -1 &&
            box.left < document.documentElement.clientWidth;
    }"""):
        raise RuntimeError("Life fragment did not scroll to its target: " + fragment)
    # Native anchors need not focus a nonfocusable heading/section. Chromium may
    # retain the activating link or use body. A focusable target should receive
    # native focus; do not let a year listener move focus to unrelated content.
    if activator is not None:
        focus_ok = target.evaluate("""(node, source) => {
            const active = document.activeElement;
            const focusable = node.matches(
                '[tabindex], a[href], button, input, select, textarea, [contenteditable="true"]');
            if (node === source && active === source) return true;
            if (focusable) return node === active || node.contains(active);
            return active === document.body || active === source ||
                active === node || node.contains(active);
        }""", activator.element_handle())
        if not focus_ok:
            raise RuntimeError("Life fragment focus moved to unrelated content: " + fragment)


def activate_life_anchor(page, link, fragment, *, keyboard=False, selected=None,
                         scripts_enabled=True):
    if link.count() != 1:
        raise RuntimeError("Life anchor is missing or ambiguous: " + fragment)
    changed = page.evaluate("location.hash") != fragment
    # Focus first also exposes the keyboard-only skip link for a normal click.
    link.focus()
    if changed and scripts_enabled:
        page.evaluate("""() => {
            window.__lifeAnchorHashChanged = false;
            addEventListener("hashchange", () => { window.__lifeAnchorHashChanged = true; },
                             {once: true});
        }""")
    if keyboard:
        link.press("Enter")
    else:
        link.click()
    if changed and scripts_enabled:
        page.wait_for_function("window.__lifeAnchorHashChanged === true")
    settle_life_hash(page, fragment)
    check_life_target(page, fragment, link)
    if selected is not None and life_selected_year(page) != str(selected):
        raise RuntimeError("Life anchor hijacked the selected year: " + fragment)


def check_life_visibility(page, *, expanded=False):
    """Required text cannot disappear through opacity, clipping or ancestors."""
    targets = page.locator(
        'header h1, header p, header strong, header a, main > h2, main > p, '
        'main > nav a, footer p, footer a, [data-value], '
        '#life-years a, [data-life-year] h2, [data-life-year] h3, '
        '[data-life-year] p, #compare > h2, #school-sources > h2, '
        '#compare h3, #compare summary, [data-life-year] summary, '
        '#compare table caption, [data-school-row] [data-value], '
        '[data-school-pair] [data-value], #compare-result, '
        '[data-pid="school-phase-order"], [data-pid="pair-method"], '
        '[data-pid="pair-mapping"], #school-sources p, #school-sources li, '
        '#school-sources blockquote, #school-sources a, #school-sources code')
    if not targets.count():
        raise RuntimeError("Life readable content is missing")
    failures = targets.evaluate_all("""(nodes, expanded) => {
        const visible = node => {
            const closed = node.closest("details:not([open])");
            if (!expanded && closed && !closed.querySelector(":scope > summary")?.contains(node))
                return true;
            const box = node.getBoundingClientRect();
            if (box.width <= 0 || box.height <= 0 ||
                box.top + scrollY < -1) return false;
            for (let p = node; p; p = p.parentElement) {
                const css = getComputedStyle(p);
                if (p.inert || p.hidden || p.hasAttribute('popover') ||
                    p.getAttribute('aria-hidden') === 'true' ||
                    Number(css.opacity) <= 0 || css.display === 'none' ||
                    css.visibility !== 'visible' || css.clip !== 'auto' ||
                    css.clipPath !== 'none' || css.contentVisibility === 'hidden')
                    return false;
                const clip = value => /^(hidden|clip|auto|scroll)$/.test(value);
                const bounds = p.getBoundingClientRect();
                // Horizontal overflow inside the labelled table region is
                // accessible by native scrolling; vertical clipping is not.
                const tableScroll = p.matches('[role="region"][tabindex="0"]') &&
                    !!p.querySelector('table') && css.overflowX === 'auto';
                if (clip(css.overflowY) &&
                    (box.top < bounds.top + p.clientTop - 1 ||
                     box.bottom > bounds.top + p.clientTop + p.clientHeight + 1))
                    return false;
                if (!tableScroll && clip(css.overflowX) &&
                    (box.left < bounds.left + p.clientLeft - 1 ||
                     box.right > bounds.left + p.clientLeft + p.clientWidth + 1))
                    return false;
            }
            const region = node.closest('[role="region"][tabindex="0"]');
            return !!region || (box.left >= -1 &&
                box.right <= document.documentElement.clientWidth + 1);
        };
        return nodes.filter(node => !visible(node)).map(node => node.innerText.slice(0, 100));
    }""", expanded)
    if failures:
        raise RuntimeError("Life required text is hidden or clipped: " + "; ".join(failures[:5]))


def check_life_number(locator, expected, label):
    expected = str(expected)
    if (locator.count() != 1 or not locator.is_visible() or
            locator.get_attribute("data-value") != expected or
            locator.inner_text().replace(",", "").strip().removesuffix("%") != expected):
        raise RuntimeError("Life browser numeric answer changed: " + label)


def check_life_browser(page, data, *, expanded=False):
    """Bind visible annual answers to the independently checked public data."""
    if page.locator("[data-life-year]").count() != 19:
        raise RuntimeError("Life browser must retain all 19 annual sections")
    years = [str(year) for year in range(2008, 2027)]
    if page.locator("[data-life-year]").evaluate_all(
            "nodes => nodes.map(node => node.getAttribute('data-life-year'))") != years:
        raise RuntimeError("Life annual anchor order changed")
    for year in years:
        section = page.locator("#year-" + year)
        link = page.locator('#life-years a[href="#year-' + year + '"]')
        if not section.is_visible() or link.count() != 1 or not link.is_visible():
            raise RuntimeError("Life annual section/link hidden: " + year)
    expected = []
    for row in data["schools"]["rows"]:
        phase = row["filters"]["5cGdi"]
        band = row["filters"]["cAd31"]
        selector = (f'[data-school-row][data-anchor="{row["anchor"]}"]'
                    f'[data-phase="{phase}"][data-band="{band}"]')
        measures = {
            "classes": row["published"]["EAicq"]["display"],
            "pupils": row["published"]["QtxWw"]["display"],
            "mean": row["derived"]["mean"]["display"],
            "class_share": row["derived"]["class_share"]["display"],
            "pupil_share": row["derived"]["pupil_share"]["display"],
        }
        expected.extend({"selector": selector + f' [data-measure="{measure}"]', "value": value}
                        for measure, value in measures.items())
        if phase in ("5kyxd", "tfHTE") and band == "XdTUf":
            expected.append({
                "selector": (f'[data-school-summary="{phase}"][data-anchor="{row["anchor"]}"]'
                             ' [data-measure="mean"]'),
                "value": row["derived"]["mean"]["display"]})
    for pair in data["comparisons"]:
        if not pair["available"] or pair["from"] >= pair["to"]:
            continue
        selector = (f'[data-school-pair][data-from="{pair["from"]}"]'
                    f'[data-to="{pair["to"]}"][data-phase="{pair["phase"]}"]')
        expected.extend({
            "selector": selector + f' [data-measure="{measure}"]', "value": pair[field]}
            for measure, field in (("left", "left"), ("right", "right"), ("change", "display")))
    for record in data["schools"]["reconciliations"]:
        if record["residual_total_minus_bands"] == "0":
            continue
        expected.append({
            "selector": (f'[data-school-residual][data-period="{record["timePeriod"]["period"]}"]'
                         f'[data-phase="{record["phase"]}"][data-indicator="{record["indicator"]}"]'
                         ' [data-measure="residual"]'),
            "value": record["residual_total_minus_bands"]})
    default_pair = next(pair for pair in data["comparisons"]
                        if pair["id"] == "2016:2026:5kyxd")
    expected.extend({
        "selector": '#compare-result ' + f'[data-measure="{measure}"]',
        "value": default_pair[field]}
        for measure, field in (("left", "left"), ("right", "right"), ("change", "display")))
    for phase, measure in (("5kyxd", "primary_mean"), ("tfHTE", "secondary_mean")):
        row = next(row for row in data["schools"]["rows"]
                   if row["anchor"] == 2026 and row["filters"]["5cGdi"] == phase and
                   row["filters"]["cAd31"] == "XdTUf")
        expected.append({
            "selector": f'[data-pid="school-phase-order"] [data-measure="{measure}"]',
            "value": row["derived"]["mean"]["display"]})
    difference = next(item for item in data["schools"]["comparisons"]
                      if item["id"] == "primary_minus_secondary_2026")
    expected.append({
        "selector": '[data-pid="school-phase-order"] [data-measure="primary_minus_secondary"]',
        "value": difference["display"]})
    failures = page.evaluate("""({expected, expanded}) => expected.flatMap(entry => {
        const nodes = document.querySelectorAll(entry.selector), node = nodes[0];
        if (nodes.length === 1 && !expanded && node.closest("details:not([open])")) return [];
        return nodes.length !== 1 || !node.getBoundingClientRect().width ||
            !node.getBoundingClientRect().height ||
            node.getAttribute('data-value') !== entry.value ||
            node.innerText.replaceAll(',', '').trim().replace(/%$/, '') !== entry.value
            ? [entry.selector] : [];
    })""", {"expected": expected, "expanded": expanded})
    if failures:
        raise RuntimeError("Life browser numeric answer changed: " + "; ".join(failures[:5]))
    for phase in ("5kyxd", "tfHTE", "TaWMP", "cDwC3"):
        pair_table = page.locator("#pairs-" + phase)
        if not pair_table.is_visible() or pair_table.locator("[data-school-pair]").count() != 55:
            raise RuntimeError("Life no-JavaScript pair table missing: " + phase)
        table = pair_table.locator("table")
        if not table.is_visible():
            summary = pair_table.locator("details > summary")
            if expanded or summary.count() != 1 or not summary.is_visible():
                raise RuntimeError("Life pair table is concealed or cannot be expanded: " + phase)
    check_life_visibility(page, expanded=expanded)


def check_life_navigation(page, origin):
    """Exercise real native click/Enter and progressive year controls."""
    url = origin + "/life.html"
    page.goto(url, wait_until="load")
    page.wait_for_function("!document.querySelector('#life-year-controls').hidden")
    default = life_selected_year(page)
    if (default != "2026" or page.evaluate("location.hash") != "" or
            page.evaluate("scrollY > 1 || document.activeElement !== document.body")):
        raise RuntimeError("Life initial visit rewrote the URL or selected the wrong year")
    for keyboard in (False, True):
        for fragment in ("#main", "#life-years", "#compare", "#school-sources",
                         "#pairs-5kyxd", "#pairs-tfHTE", "#pairs-TaWMP", "#pairs-cDwC3"):
            page.goto(url + "#year-2020", wait_until="load")
            settle_life_hash(page, "#year-2020")
            check_life_target(page, "#year-2020", page.locator("#year-2020"))
            if life_selected_year(page) != "2020":
                raise RuntimeError("Life initial year fragment did not synchronize")
            link = page.locator('a[href="' + fragment + '"]').first
            activate_life_anchor(page, link, fragment, keyboard=keyboard, selected=2020)
        # Exercise actual inline DfE citations as well as the Sources navigation.
        for selector in (
                '#year-2008 a[href="#school-sources"]',
                '#year-2026 a[href="#school-sources"]',
                '#compare > [data-pid="school-scope"] a[href="#school-sources"]',
                '[data-pid="pair-method"] a[href="#school-sources"]',
                '[data-pid="school-phase-order"] a[href="#school-sources"]'):
            page.goto(url + "#year-2020", wait_until="load")
            activate_life_anchor(page, page.locator(selector), "#school-sources",
                                 keyboard=keyboard, selected=2020)
        # Every supported annual link must change year, fragment and scroll.
        for year in range(2008, 2027):
            fragment = "#year-" + str(year)
            page.goto(url + ("#year-2026" if year != 2026 else "#year-2008"),
                      wait_until="load")
            activate_life_anchor(page, page.locator('#life-years a[href="' + fragment + '"]'),
                                 fragment, keyboard=keyboard, selected=year)
    page.goto(url + "#year-2008", wait_until="load")
    for year in range(2008, 2026):
        activate_life_anchor(
            page, page.locator(f'#year-{year} a[data-year-step="next"]'),
            f"#year-{year + 1}", selected=year + 1)
    for year in range(2026, 2008, -1):
        activate_life_anchor(
            page, page.locator(f'#year-{year} a[data-year-step="previous"]'),
            f"#year-{year - 1}", keyboard=True, selected=year - 1)
    if (page.locator('#year-2008 a[data-year-step="previous"]').count() or
            page.locator('#year-2026 a[data-year-step="next"]').count()):
        raise RuntimeError("Life boundary steps link outside supported annual anchors")
    year_select = page.locator("#life-year-select")
    for year in range(2008, 2027):
        year_select.select_option(str(year))
        settle_life_hash(page, "#year-" + str(year))
        check_life_target(page, "#year-" + str(year))
        if life_selected_year(page) != str(year):
            raise RuntimeError("Life year select failed: " + str(year))
    year_select.select_option("2025")
    settle_life_hash(page, "#year-2025")
    year_select.focus()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    settle_life_hash(page, "#year-2026")
    check_life_target(page, "#year-2026", year_select)
    if life_selected_year(page) != "2026":
        raise RuntimeError("Life year select failed native keyboard change")
    for fragment in ("#compare", "#school-sources", "#pairs-5kyxd"):
        page.goto(url + fragment, wait_until="load")
        settle_life_hash(page, fragment)
        check_life_target(page, fragment, page.locator("body"))
        if life_selected_year(page) != default:
            raise RuntimeError("Life nonyear reload changed selected year: " + fragment)
    for fragment in ("#year-2007", "#year-2027", "#year-nope", "#year-2020-extra",
                     "#year-%E0%A4%A", "#%"):
        page.goto(url + "#year-2020", wait_until="load")
        focused = page.evaluate("document.activeElement.id")
        page.evaluate("(hash) => { location.hash = hash; }", fragment)
        settle_life_hash(page, fragment)
        if (life_selected_year(page) != "2020" or
                page.evaluate("document.activeElement.id") != focused):
            raise RuntimeError("Life unsupported hash hijacked selected year/focus: " + fragment)
        page.reload(wait_until="load")
        settle_life_hash(page, fragment)
        if (life_selected_year(page) != default or
                page.evaluate("document.activeElement !== document.body")):
            raise RuntimeError("Life malformed/unsupported reload changed focus/year: " + fragment)
    page.goto(url, wait_until="load")



def check_life_comparison_controls(page, data):
    """Every ordered choice must render the checked answer through real handlers."""
    initial_year = life_selected_year(page)
    initial_hash = page.evaluate("location.hash")
    failures = page.evaluate("""pairs => {
        const from = document.querySelector('#compare-from');
        const to = document.querySelector('#compare-to');
        const phase = document.querySelector('#compare-phase');
        const result = document.querySelector('#compare-result');
        if (![from, to, phase, result].every(Boolean)) return ['Missing comparison controls'];
        const visible = node => {
            if (!node || !node.getBoundingClientRect().width ||
                !node.getBoundingClientRect().height) return false;
            for (let p = node; p; p = p.parentElement) {
                const css = getComputedStyle(p);
                if (p.hidden || p.inert || p.getAttribute('aria-hidden') === 'true' ||
                    Number(css.opacity) <= 0 || css.display === 'none' ||
                    css.visibility !== 'visible' || css.clip !== 'auto' ||
                    css.clipPath !== 'none' || css.contentVisibility === 'hidden') return false;
            }
            return true;
        };
        const failures = [];
        for (const pair of pairs) {
            for (const [control, value] of [[from, pair.from], [to, pair.to], [phase, pair.phase]]) {
                control.value = String(value);
                if (control.value !== String(value)) {
                    failures.push('Option absent: ' + pair.id); break;
                }
                control.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if (!visible(result) || result.getAttribute('role') !== 'status' ||
                result.getAttribute('data-available') !== String(pair.available)) {
                failures.push('Unavailable/hidden result: ' + pair.id); continue;
            }
            if (pair.available) {
                for (const [measure, field] of [['left', 'left'], ['right', 'right'], ['change', 'display']]) {
                    const spans = result.querySelectorAll('[data-measure="' + measure + '"]');
                    const span = spans[0];
                    if (spans.length !== 1 || !visible(span) ||
                        span.getAttribute('data-value') !== pair[field] ||
                        span.textContent.replaceAll(',', '').trim() !== pair[field]) {
                        failures.push('Wrong visible ' + measure + ': ' + pair.id);
                    }
                }
            } else if (!result.innerText.includes(pair.reason) ||
                       result.querySelector('[data-measure][data-value]') ||
                       !result.querySelector('a[href="#year-2016"]')) {
                failures.push('Missing comparison converted to value or lost nearest link: ' + pair.id);
            }
        }
        return failures;
    }""", data["comparisons"])
    if failures:
        raise RuntimeError("Life comparison handlers failed: " + "; ".join(failures[:10]))
    if life_selected_year(page) != initial_year or page.evaluate("location.hash") != initial_hash:
        raise RuntimeError("Life comparison controls hijacked annual selection or fragment")
    # Actual keyboard changes independently exercise native select interaction.
    pairs = {(str(p["from"]), str(p["to"]), p["phase"]): p for p in data["comparisons"]}
    for selector, baseline in (("#compare-from", "2016"), ("#compare-to", "2025"),
                               ("#compare-phase", "5kyxd")):
        page.locator("#compare-from").select_option("2016")
        page.locator("#compare-to").select_option("2026")
        page.locator("#compare-phase").select_option("5kyxd")
        control = page.locator(selector)
        control.select_option(baseline)
        before = control.input_value()
        control.focus()
        control.press("ArrowDown")
        control.press("Enter")
        if control.input_value() == before:
            raise RuntimeError("Life comparison select failed keyboard change: " + selector)
        key = (page.locator("#compare-from").input_value(),
               page.locator("#compare-to").input_value(),
               page.locator("#compare-phase").input_value())
        pair = pairs[key]
        for measure, field in (("left", "left"), ("right", "right"), ("change", "display")):
            check_life_number(page.locator(f'#compare-result [data-measure="{measure}"]'),
                              pair[field], "keyboard comparison/" + measure)
    for selector, value in (("#compare-from", "2016"), ("#compare-to", "2026"),
                            ("#compare-phase", "5kyxd")):
        page.locator(selector).select_option(value)
    if life_selected_year(page) != initial_year or page.evaluate("location.hash") != initial_hash:
        raise RuntimeError("Life keyboard comparison controls hijacked annual selection")


def check_life_plain(page, data):
    for selector in ("#life-year-select", "#compare-from", "#compare-to", "#compare-phase"):
        control = page.locator(selector)
        if control.count() != 1 or (control.is_visible() and not control.is_disabled()):
            raise RuntimeError("No-JavaScript life enhancement control is active: " + selector)
    check_life_browser(page, data)
    for keyboard in (False, True):
        for year in range(2008, 2027):
            fragment = "#year-" + str(year)
            activate_life_anchor(page, page.locator('#life-years a[href="' + fragment + '"]'),
                                 fragment, keyboard=keyboard, scripts_enabled=False)
        for year in range(2008, 2026):
            activate_life_anchor(
                page, page.locator(f'#year-{year} a[data-year-step="next"]'),
                f"#year-{year + 1}", keyboard=keyboard, scripts_enabled=False)
        for year in range(2026, 2008, -1):
            activate_life_anchor(
                page, page.locator(f'#year-{year} a[data-year-step="previous"]'),
                f"#year-{year - 1}", keyboard=keyboard, scripts_enabled=False)


def check():
    pages = sorted(SITE.glob("*.html"))
    if {path.name for path in pages} != {"index.html", "taxes.html", "who-pays.html", "life.html", "methods.html"}:
        raise RuntimeError("Expected exactly spending, taxes, who-pays, life and methods HTML pages; build the site first.")
    chrome = find_chrome()
    axe_source = bundled_axe()
    payer_bytes = (SITE / "data/payers.json").read_bytes()
    payer_data = json.loads(payer_bytes)
    life_bytes = (SITE / "data/life.json").read_bytes()
    life_data = json.loads(life_bytes)
    from playwright.sync_api import sync_playwright

    violations = 0
    with serve_site() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=chrome, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-background-networking"],
        )
        try:
            check_basics_browser_guards(browser)
            context = browser.new_context()
            # The audit is entirely local, even if a later page adds an external
            # asset. Never fetch axe-core, fonts or other assets from the network.
            def local_assets_only(route):
                if route.request.url.startswith(origin + "/"):
                    route.continue_()
                else:
                    route.abort()

            context.route("**/*", local_assets_only)
            # Follow the actual local download route and compare its bytes.
            download = context.request.get(origin + "/data/payers.json")
            if (download.status != 200 or download.body() != payer_bytes or
                    "application/json" not in download.headers.get("content-type", "")):
                raise RuntimeError("Payer browser JSON download route failed")
            life_download = context.request.get(origin + "/data/life.json")
            if (life_download.status != 200 or life_download.body() != life_bytes or
                    "application/json" not in life_download.headers.get("content-type", "")):
                raise RuntimeError("Life browser JSON download route failed")
            for private in (
                    "data/life/schools.json", "data/schools.json",
                    "data/life/school-sources.json", "data/life/work-data-sources.json",
                    "data/life/work-methods-sources.json", "data/life/holiday-methods-sources.json",
                    "data/life/sources/schools/dfe-national-class-sizes-1.0.json",
                    "data/life/sources/schools/dfe-class-sizes-meta-1.0.json"):
                if context.request.get(origin + "/" + private).status != 404:
                    raise RuntimeError("Private life foundation is publicly served: " + private)
            page = context.new_page()
            page.set_default_timeout(30_000)
            script_errors = []
            page.on("pageerror", lambda error: script_errors.append(str(error)))
            for path in pages:
                for width in WIDTHS:
                    script_errors.clear()
                    page.set_viewport_size({"width": width, "height": 900})
                    response = page.goto(f"{origin}/{quote(path.name)}", wait_until="load")
                    if response is None or response.status != 200:
                        raise RuntimeError(f"Could not load {path.name} at {width}px.")
                    if script_errors:
                        raise RuntimeError(f"Page script error: {path.name}: {script_errors}")
                    nav = page.locator('nav.site-nav[aria-label="Primary"]')
                    if nav.count() != 1:
                        raise RuntimeError(f"Expected one shared primary navigation: {path.name}")
                    for target in ("index.html", "taxes.html", "who-pays.html", "life.html", "methods.html"):
                        link = nav.locator(f'a[href="{target}"]')
                        if link.count() != 1 or not link.is_visible():
                            raise RuntimeError(f"Missing visible top navigation to {target}: {path.name}")
                    if path.name == "life.html":
                        check_life_navigation(page, origin)
                        check_life_comparison_controls(page, life_data)
                    # Exercise the progressive view controls before the audit.
                    buttons = page.locator(".views button")
                    for index in range(buttons.count()):
                        button = buttons.nth(index)
                        button.click()
                        if button.get_attribute("aria-pressed") != "true":
                            raise RuntimeError("View control did not update its pressed state")
                        view = button.get_attribute("data-view")
                        if not page.locator(f".v-{view}").first.is_visible():
                            raise RuntimeError(f"View control did not reveal {view}")
                    if buttons.count():
                        buttons.first.click()
                    page.add_script_tag(content=axe_source)
                    # Fail closed if the bundled version cannot actually check
                    # every requested tag or omits colour contrast.
                    page.evaluate("""tags => {
                        const rules = axe.getRules();
                        const missing = tags.filter(tag =>
                            !rules.some(rule => rule.tags.includes(tag)));
                        if (missing.length) {
                            throw new Error('Bundled axe-core lacks tags: ' + missing.join(', '));
                        }
                        if (!rules.some(rule => rule.ruleId === 'color-contrast' &&
                            rule.tags.some(tag => tags.includes(tag)))) {
                            throw new Error('Colour contrast rule is missing');
                        }
                    }""", list(TAGS))
                    states = ["default"]
                    if page.locator("details").count():
                        states.append("expanded")
                    for state in states:
                        if state == "expanded":
                            page.locator("details").evaluate_all(
                                "details => details.forEach(detail => { detail.open = true; })"
                            )
                        if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                            raise RuntimeError(f"Page overflow: {path.name}, {width}px, {state}")
                        check_basics_browser(page, expanded=state == "expanded")
                        if path.name == "who-pays.html":
                            check_payer_browser(page, payer_data)
                        if path.name == "life.html":
                            check_life_browser(page, life_data, expanded=state == "expanded")
                        table_failures = page.locator("table").evaluate_all("""tables =>
                            tables.flatMap(table => {
                                const region = table.closest('[role="region"]');
                                return !region || region.tabIndex !== 0 ||
                                    !(region.getAttribute('aria-label') || region.getAttribute('aria-labelledby')) ||
                                    getComputedStyle(region).overflowX !== 'auto'
                                    ? ['Table lacks labelled keyboard scroll region'] : [];
                            })""")
                        if table_failures:
                            raise RuntimeError("; ".join(table_failures))
                        small_targets = page.locator("nav a, summary, button, select, [data-year-step]").evaluate_all("""nodes =>
                            nodes.filter(node => {
                                const box = node.getBoundingClientRect();
                                return box.width > 0 && box.height > 0 &&
                                    (box.width < 44 || box.height < 44);
                            }).map(node => node.textContent.trim())""")
                        if small_targets:
                            raise RuntimeError(f"Controls below 44px on {path.name}: {small_targets}")
                        if path.name in ("taxes.html", "who-pays.html") and page.locator("data[tabindex='0']").count():
                            raise RuntimeError("Tax/payer figures must not each be a keyboard tab stop")
                        for index in range(page.locator("summary").count()):
                            summary = page.locator("summary").nth(index)
                            if not summary.is_visible():
                                continue
                            detail = summary.locator("..")
                            was_open = detail.get_attribute("open") is not None
                            summary.focus()
                            page.keyboard.press("Enter")
                            if (detail.get_attribute("open") is not None) == was_open:
                                raise RuntimeError(f"Disclosure failed keyboard activation: {path.name}")
                            page.keyboard.press("Enter")
                        if script_errors:
                            raise RuntimeError(f"Page script error: {path.name}: {script_errors}")
                        result = page.evaluate("""async tags => await axe.run(document, {
                            runOnly: {type: 'tag', values: tags},
                            rules: {'color-contrast': {enabled: true}}
                        })""", list(TAGS))
                        for violation in result["violations"]:
                            violations += 1
                            for node in violation["nodes"]:
                                selector = node["target"]
                                print(f"FAIL {violation['id']} | {path.name} | "
                                      f"{width}px | {state} | selector={selector} | "
                                      f"{node.get('failureSummary', violation['help'])}")
                        print(f"{path.name}: {width}px, {state}: "
                              f"{len(result['violations'])} axe violations")
            context.close()
            # Open the same core product with enhancement scripts disabled.
            plain = browser.new_context(java_script_enabled=False,
                                        viewport={"width": 360, "height": 900})
            plain.route("**/*", local_assets_only)
            reader = plain.new_page()
            for path in pages:
                for width in WIDTHS:
                    reader.set_viewport_size({"width": width, "height": 900})
                    response = reader.goto(f"{origin}/{quote(path.name)}", wait_until="load")
                    if response is None or response.status != 200 or not reader.locator("main").is_visible():
                        raise RuntimeError(f"No-JavaScript content unavailable: {path.name}")
                    if reader.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                        raise RuntimeError(f"No-JavaScript default overflow: {path.name}, {width}px")
                    check_basics_browser(reader)
                    if path.name == "life.html":
                        check_life_plain(reader, life_data)
                    if path.name in ("taxes.html", "who-pays.html") and not reader.locator("details").count():
                        raise RuntimeError(f"Source detail is missing without JavaScript: {path.name}")
                    for index in range(reader.locator("details").count()):
                        detail = reader.locator("details").nth(index)
                        summary = detail.locator(":scope > summary")
                        if detail.get_attribute("open") is None:
                            # Native disclosure must work with the keyboard.
                            summary.focus()
                            reader.keyboard.press("Enter")
                        if detail.get_attribute("open") is None:
                            raise RuntimeError(f"No-JavaScript keyboard disclosure failed: {path.name}")
                    for region in reader.locator("table").evaluate_all("""tables =>
                        tables.map(table => {
                            const region = table.closest('[role="region"]');
                            return !!region && region.tabIndex === 0 &&
                                !!(region.getAttribute('aria-label') || region.getAttribute('aria-labelledby')) &&
                                getComputedStyle(region).overflowX === 'auto';
                        })"""):
                        if not region:
                            raise RuntimeError(f"No-JavaScript table lacks keyboard scroll access: {path.name}")
                    if not reader.locator("table").count():
                        raise RuntimeError(f"No-JavaScript table alternative missing: {path.name}")
                    if reader.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                        raise RuntimeError(f"No-JavaScript expanded overflow: {path.name}, {width}px")
                    check_basics_browser(reader, expanded=True)
                    if path.name == "who-pays.html":
                        check_payer_browser(reader, payer_data)
                    if path.name == "life.html":
                        check_life_browser(reader, life_data, expanded=True)
            plain.close()
        finally:
            browser.close()
    if violations:
        print(f"FAIL accessibility: {violations} rule violations")
        return 1
    print("Accessibility: 0 axe violations, including colour contrast, "
          "for WCAG 2.2 AA at 360px and 1100px.")
    return 0


def main():
    try:
        return check()
    except Exception as error:
        print(f"FAIL accessibility check could not complete: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
