"""Observable static-baseline checks; standard library only, no network services."""
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = {"index.html", "styles.css"}


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="unpoliticalaf-test-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.output = self.work / "public"
        self.build(self.output)

    def build(self, output, root=ROOT, success=True):
        result = subprocess.run(
            [sys.executable, str(root / "scripts/build.py"), "--output", str(output)],
            cwd=root, capture_output=True, text=True, timeout=20,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, "Unsafe output was accepted")
        return result

    def snapshot(self, directory):
        return {str(p.relative_to(directory)): p.read_bytes()
                for p in directory.rglob("*") if p.is_file()}

    def test_exact_allowlist_source_bytes_and_determinism(self):
        first = self.snapshot(self.output)
        self.assertEqual(set(first), PUBLISHED)
        self.assertEqual({p.name for p in self.output.iterdir()}, PUBLISHED)
        for name, data in first.items():
            self.assertEqual(data, (ROOT / "static" / name).read_bytes())
        self.build(self.output)
        self.assertEqual(self.snapshot(self.output), first)
        other = self.work / "second"
        self.build(other)
        self.assertEqual(self.snapshot(other), first)

    def test_contaminated_output_is_rejected_without_data_loss(self):
        (self.output / "credentials.json").write_text('private sentinel')
        (self.output / "nested").mkdir()
        (self.output / "nested" / "README.md").write_text('private sentinel')
        before = self.snapshot(self.output)
        self.build(self.output, success=False)
        self.assertEqual(self.snapshot(self.output), before)
        for path in self.output.rglob("*"):
            self.assertFalse(path.is_symlink(), str(path))

    def test_semantic_document_and_navigation(self):
        text = (self.output / "index.html").read_text(encoding="utf-8")
        doc = Document(text)
        self.assertRegex(text.lower(), r"<!doctype\s+html\s*>")
        self.assertEqual(len(doc.elements("html")), 1)
        self.assertRegex(doc.elements("html")[0].get("lang", ""), r"^en(?:-|$)")
        self.assertEqual(len(doc.elements("title")), 1)
        self.assertRegex(text, r"(?is)<title>\s*[^<\s].*?</title>")
        viewport = [a for a in doc.elements("meta") if a.get("name") == "viewport"]
        self.assertEqual(len(viewport), 1)
        self.assertIn("width=device-width", viewport[0].get("content", ""))
        self.assertEqual(len(doc.elements("main")), 1)
        self.assertEqual(len(doc.elements("h1")), 1)
        ids = [a["id"] for _, a in doc.tags if "id" in a]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate IDs")
        links = doc.elements("a")
        self.assertTrue(links, "Need keyboard-accessible skip link")
        main_id = doc.elements("main")[0].get("id")
        self.assertTrue(main_id)
        self.assertEqual(links[0].get("href"), "#" + main_id)
        self.assertRegex(text, r"(?is)<a\b[^>]*>[^<]*skip[^<]*</a>")
        self.assertTrue(doc.elements("nav"), "Need semantic navigation")
        fragments = [a["href"][1:] for a in links if a.get("href", "").startswith("#")]
        self.assertTrue(fragments)
        for target in fragments:
            self.assertIn(target, ids, "Broken navigation target")
        styles = [a for a in doc.elements("link") if a.get("rel") == "stylesheet"]
        self.assertEqual(len(styles), 1)
        self.assertIn(styles[0].get("href"), ("styles.css", "./styles.css", "/styles.css"))
        self.assertFalse(doc.elements("script"), "Baseline must not need JavaScript")
        for _, attrs in doc.tags:
            for key in ("src", "href"):
                value = attrs.get(key, "")
                self.assertFalse(value.startswith(("http:", "https:", "//")),
                                 "Baseline must not load external resources")

    def test_honest_status_and_product_intentions(self):
        doc = Document((self.output / "index.html").read_text(encoding="utf-8"))
        visible = " ".join(" ".join(doc.text).split()).lower()
        self.assertRegex(visible, r"under construction|in development|not yet (?:ready|available)|being built")
        self.assertRegex(visible, r"spend(?:ing|s)?|expenditure")
        self.assertRegex(visible, r"tax(?:es|ation)?")
        self.assertRegex(visible, r"plan|intend|will|aim|building|future")
        self.assertNotRegex(visible, r"[£$€]|\b\d[\d,.]*\s*(?:billion|million|trillion|percent|%)")
        self.assertNotRegex(visible, r"\b(?:deployed|factory|application) (?:is )?(?:fully operational|complete|live)\b")

    def test_responsive_and_keyboard_focus_css(self):
        css = (self.output / "styles.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertRegex(css, r"@media\s*[^{}]*(?:min-width|max-width)")
        self.assertRegex(css, r":focus(?:-visible)?\b[^{}]*\{[^}]*\b(?:outline|box-shadow|border)\s*:")
        self.assertRegex(css, r"(?:max-width\s*:|width\s*:\s*(?:100%|min\(|clamp\())")
        self.assertNotRegex(css, r"outline\s*:\s*(?:none|0)\s*[;}]", "Do not remove focus outline")

    def fixture_project(self):
        project = self.work / "fixture"
        shutil.copytree(ROOT / "scripts", project / "scripts")
        shutil.copytree(ROOT / "static", project / "static")
        for name in ("tests", ".git", "data"):
            (project / name).mkdir()
            (project / name / "keep.txt").write_text("do not delete")
        (project / "README.md").write_text("private project documentation")
        return project

    def test_builder_rejects_unsafe_targets_without_data_loss(self):
        project = self.fixture_project()
        original = self.snapshot(project)
        for target in (project, project.parent, project / "static", project / "scripts",
                       project / "tests", project / ".git", project / "data",
                       project / "README.md", project / "static" / "generated"):
            with self.subTest(target=str(target)):
                self.build(target, root=project, success=False)
                self.assertEqual(self.snapshot(project), original)
        external = self.work / "outside"
        external.mkdir()
        marker = external / "keep.txt"
        marker.write_text("keep me")
        link = project / "linked-output"
        link.symlink_to(external, target_is_directory=True)
        self.build(link, root=project, success=False)
        self.assertTrue(link.is_symlink())
        self.assertEqual(marker.read_text(), "keep me")
        self.build(link / "child", root=project, success=False)
        self.assertFalse((external / "child").exists())

    def test_built_output_http_bytes_types_and_private_404s(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(self.output)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            for path, name, kind in (("/", "index.html", "text/html"),
                                     ("/index.html", "index.html", "text/html"),
                                     ("/styles.css", "styles.css", "text/css")):
                with self.subTest(path=path), urlopen(base + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get_content_type(), kind)
                    self.assertEqual(response.read(), (self.output / name).read_bytes())
            for path in ("/README.md", "/AGENTS.md", "/.git/config", "/.env",
                         "/.codeaf/", "/scripts/build.py", "/tests/test_baseline.py",
                         "/data/raw/", "/factory/project.json", "/missing.html"):
                with self.subTest(private=path):
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(base + path, timeout=5)
                    self.assertEqual(caught.exception.code, 404)
                    caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main(verbosity=2)
