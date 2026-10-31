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
    download = page.locator('#payer-sources a[href="data/payers.json"]')
    if download.count() != 1 or not download.is_visible():
        raise RuntimeError("Payer browser selected-data download missing")


def check_basics_browser(page, *, expanded=False):
    """Check required guidance text, including clipping and ancestor concealment."""
    modules = page.locator('[data-basics], #tax-guidance, [data-payer-definition], #spending-vintage-note, #fiscal-glossary')
    for index in range(modules.count()):
        module = modules.nth(index)
        if not module.is_visible():
            raise RuntimeError("Basics container is not visible")
        if module.get_attribute('data-payer-definition') == 'tax-types':
            targets = page.locator('[data-payer-definition], [data-payer-definition] span, [data-payer-definition] a')
        elif module.get_attribute('id') == 'spending-vintage-note':
            targets = page.locator('#spending-vintage-note, #spending-vintage-note cite, #spending-vintage-note data')
        else:
            targets = module.locator('p, dt, h2, h3, summary, a, code, [data-guidance-source]')
        for target_index in range(targets.count()):
            target = targets.nth(target_index)
            closed = target.evaluate("""node => {
                for (let p = node.parentElement; p; p = p.parentElement) {
                    if (p.tagName === 'DETAILS' && !p.open &&
                        !p.querySelector(':scope > summary')?.contains(node)) return true;
                }
                return false;
            }""")
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


def check():
    pages = sorted(SITE.glob("*.html"))
    if {path.name for path in pages} != {"index.html", "taxes.html", "who-pays.html", "methods.html"}:
        raise RuntimeError("Expected exactly spending, taxes, who-pays and methods HTML pages; build the site first.")
    chrome = find_chrome()
    axe_source = bundled_axe()
    payer_bytes = (SITE / "data/payers.json").read_bytes()
    payer_data = json.loads(payer_bytes)
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
                    for target in ("index.html", "taxes.html", "who-pays.html", "methods.html"):
                        link = nav.locator(f'a[href="{target}"]')
                        if link.count() != 1 or not link.is_visible():
                            raise RuntimeError(f"Missing visible top navigation to {target}: {path.name}")
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
                        small_targets = page.locator("nav a, summary, button").evaluate_all("""nodes =>
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
                                !!(region.getAttribute('aria-label') || region.getAttribute('aria-labelledby'));
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
