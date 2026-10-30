"""Check every built HTML page with bundled axe-core and local headless Chromium.

No browser or JavaScript is downloaded here. Install the pinned Python dependencies
with make setup and provide Chrome/Chromium in the check environment.
"""

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
from pathlib import Path
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


def check():
    pages = sorted(SITE.glob("*.html"))
    if {path.name for path in pages} != {"index.html", "taxes.html", "methods.html"}:
        raise RuntimeError("Expected exactly spending, taxes and methods HTML pages; build the site first.")
    chrome = find_chrome()
    axe_source = bundled_axe()
    from playwright.sync_api import sync_playwright

    violations = 0
    with serve_site() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=chrome, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-background-networking"],
        )
        try:
            context = browser.new_context()
            # The audit is entirely local, even if a later page adds an external
            # asset. Never fetch axe-core, fonts or other assets from the network.
            def local_assets_only(route):
                if route.request.url.startswith(origin + "/"):
                    route.continue_()
                else:
                    route.abort()

            context.route("**/*", local_assets_only)
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
                    nav = page.locator("nav")
                    for target in ("index.html", "taxes.html", "methods.html"):
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
                        if path.name == "taxes.html":
                            table_failures = page.locator("table").evaluate_all("""tables =>
                                tables.flatMap(table => {
                                    const region = table.closest('[role="region"]');
                                    return !region || region.tabIndex !== 0 ||
                                        !(region.getAttribute('aria-label') || region.getAttribute('aria-labelledby')) ||
                                        getComputedStyle(region).overflowX !== 'auto'
                                        ? ['Tax table lacks labelled keyboard scroll region'] : [];
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
                                raise RuntimeError(f"Tax controls below 44px: {small_targets}")
                            if page.locator("data[tabindex='0']").count():
                                raise RuntimeError("Tax figures must not each be a keyboard tab stop")
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
                response = reader.goto(f"{origin}/{quote(path.name)}", wait_until="load")
                if response is None or response.status != 200 or not reader.locator("main").is_visible():
                    raise RuntimeError(f"No-JavaScript content unavailable: {path.name}")
                for index in range(reader.locator("details").count()):
                    detail = reader.locator("details").nth(index)
                    if detail.get_attribute("open") is None:
                        detail.locator(":scope > summary").click()
                    if detail.get_attribute("open") is None:
                        raise RuntimeError(f"No-JavaScript disclosure failed: {path.name}")
                if path.name == "taxes.html":
                    summary = reader.locator("details summary").first
                    if not summary.count():
                        raise RuntimeError("Tax source detail is missing without JavaScript")
                    # Native disclosure must respond to keyboard, not a click handler.
                    detail = summary.locator("..")
                    was_open = detail.get_attribute("open") is not None
                    summary.focus()
                    reader.keyboard.press("Enter")
                    if (detail.get_attribute("open") is not None) == was_open:
                        raise RuntimeError("Tax source detail failed keyboard activation")
                    for region in reader.locator("table").evaluate_all("""tables =>
                        tables.map(table => {
                            const region = table.closest('[role="region"]');
                            return !!region && region.tabIndex === 0 &&
                                !!(region.getAttribute('aria-label') || region.getAttribute('aria-labelledby'));
                        })"""):
                        if not region:
                            raise RuntimeError("No-JavaScript tax table lacks keyboard scroll access")
                if not reader.locator("table").count():
                    raise RuntimeError(f"No-JavaScript table alternative missing: {path.name}")
                if reader.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                    raise RuntimeError(f"No-JavaScript mobile overflow: {path.name}")
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
