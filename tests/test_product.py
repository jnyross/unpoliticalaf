"""Product, publication-boundary and local HTTP checks for the public fiscal pages."""
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import re
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit, unquote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build as builder
import build_data
from check_site import independent_data_checks, cells

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.nodes = []
        self._stack = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        node = {"tag": tag, "attrs": dict(attrs), "children": [], "text": []}
        self.nodes.append(node)
        if self._stack:
            self._stack[-1]["children"].append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img",
                       "input", "link", "meta", "param", "source", "track", "wbr"}:
            self._stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index]["tag"] == tag:
                del self._stack[index:]
                break

    def handle_data(self, data):
        self.text.append(data)
        for node in self._stack:
            node["text"].append(data)

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass



def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


class ProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = ROOT / "site"
        cls.files = snapshot(cls.site)
        if set(cls.files) != builder.PUBLIC_FILES:
            raise AssertionError("Run make build before product verification or smoke")
        cls.data = json.loads(cls.files["data/spending.json"])

    def test_complete_public_product(self):
        self.assertEqual(self.files["data/spending.json"], (ROOT / "data/spending.json").read_bytes())
        self.assertGreaterEqual(len(self.data["years"]), 20)
        self.assertEqual(len(self.data["functions"]), 11)
        self.assertEqual(self.data["base_year"], self.data["latest_year"])
        decades = self.data["history"]["decades"]
        self.assertEqual(decades[0], "1945-46")
        self.assertEqual(decades[-1], self.data["latest_year"])
        self.assertTrue(all(int(b[:4]) - int(a[:4]) == 10 for a, b in zip(decades, decades[1:])))
        self.assertEqual(self.data["product_source"]["revision"], "8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713")

    def test_semantics_links_and_no_javascript_content(self):
        docs = {name: Document(self.files[name].decode("utf-8"))
                for name in ("index.html", "taxes.html", "methods.html")}
        ids = {name: [attrs["id"] for _, attrs in doc.tags if "id" in attrs]
               for name, doc in docs.items()}
        for name, doc in docs.items():
            raw = self.files[name].decode("utf-8")
            self.assertLess(len(self.files[name]), 500_000)
            self.assertRegex(raw.lower(), r"<!doctype\s+html\s*>")
            self.assertEqual(len(doc.elements("main")), 1)
            self.assertEqual(len(doc.elements("h1")), 1)
            self.assertEqual(len(doc.elements("title")), 1)
            self.assertTrue(doc.elements("html")[0]["lang"].startswith("en"))
            self.assertIn("width=device-width", next(a["content"] for a in doc.elements("meta")
                                                   if a.get("name") == "viewport"))
            self.assertEqual(len(ids[name]), len(set(ids[name])), "Duplicate IDs")
            self.assertEqual(doc.elements("a")[0]["href"], "#" + doc.elements("main")[0]["id"])
            self.assertIn("Open Government Licence v3.0", raw)
            for tag, attrs in doc.tags:
                # Citations may link out; page resources must remain local.
                if tag in ("script", "img", "link", "iframe"):
                    target = attrs.get("src", attrs.get("href", ""))
                    self.assertFalse(target.startswith(("http:", "https:", "//")))
                if tag == "a":
                    link = urlsplit(attrs.get("href", ""))
                    if link.scheme or link.netloc:
                        continue
                    target = unquote(link.path) or name
                    self.assertIn(target, self.files, f"Broken link: {name} -> {target}")
                    if link.fragment:
                        self.assertIn(unquote(link.fragment), ids[target])
            for table in [node for node in doc.nodes if node["tag"] == "table"]:
                self.assertTrue(any(child["tag"] == "caption" for child in table["children"]))
            self.assertTrue(all(a.get("scope") in ("row", "col") for a in doc.elements("th")))

        index = docs["index.html"]
        answers = next(node for node in index.nodes if node["attrs"].get("id") == "answers")
        self.assertEqual(sum(child["tag"] == "details" for child in answers["children"]), 8)
        for section_id in ("hundred", "items", "total", "decades", "areas"):
            section = next(node for node in index.nodes if node["attrs"].get("id") == section_id)
            self.assertIn("Show the numbers in a table", " ".join(section["text"]))
        self.assertGreater(len(index.elements("data")), 100)
        self.assertTrue(all(a.get("data-ref") and a.get("value") for a in index.elements("data")))
        # Static table text is present before the enhancement script runs.
        self.assertIn("not given", self.files["index.html"].decode("utf-8"))
        self.assertNotIn("All the rest is real spending", self.files["index.html"].decode("utf-8"))

    def test_tax_navigation_and_public_projection_boundary(self):
        expected_links = {"index.html", "taxes.html", "methods.html"}
        for name in ("index.html", "taxes.html", "methods.html"):
            doc = Document(self.files[name].decode("utf-8"))
            navigation = [node for node in doc.nodes if node["tag"] == "nav"]
            self.assertTrue(navigation, f"Missing top navigation: {name}")
            def descendants(node):
                for child in node["children"]:
                    yield child
                    yield from descendants(child)
            links = {child["attrs"].get("href") for nav in navigation
                     for child in descendants(nav) if child["tag"] == "a"}
            self.assertTrue(expected_links <= links, f"Incomplete navigation: {name}")
            self.assertIn("UnpoliticalAF", " ".join(doc.text))
        raw = self.files["taxes.html"].decode("utf-8")
        tax = Document(raw)
        self.assertLess(len(self.files["data/taxes.json"]), 500_000)
        public = json.loads(self.files["data/taxes.json"])
        self.assertIsInstance(public, dict)
        self.assertTrue(public)
        self.assertNotEqual(public, json.loads((ROOT / "data/receipts.json").read_text()))
        self.assertTrue(tax.elements("details"), "Source detail must work without JavaScript")
        self.assertTrue(tax.elements("table"), "Tax figures need semantic table alternatives")
        self.assertTrue(tax.elements("data"), "Tax figures must carry fiscal metadata")
        self.assertTrue(all(node.get("data-tax-id") and "value" in node
                            for node in tax.elements("data")))
        for node in (n for n in tax.nodes if n["tag"] == "data"):
            if node["attrs"].get("value") == "":
                self.assertEqual("".join(node["text"]), "not given")
        self.assertFalse(any(node.get("tabindex") == "0" for node in tax.elements("data")),
                         "Visible figures must not each add a tab stop")
        self.assertIn("data/taxes.json", {node.get("href") for node in tax.elements("a")})
        self.assertNotIn("data/receipts.json", {node.get("href") for node in tax.elements("a")})
        for table in [node for node in tax.nodes if node["tag"] == "table"]:
            regions = [region for region in tax.nodes
                       if region["attrs"].get("role") == "region"
                       and region["attrs"].get("tabindex") == "0"
                       and (region["attrs"].get("aria-label") or region["attrs"].get("aria-labelledby"))]
            def contains(node):
                return table in node["children"] or any(contains(child) for child in node["children"])
            self.assertTrue(any(contains(region) for region in regions),
                            "Tax table needs a labelled, keyboard-focusable scroll region")

    def test_responsive_focus_and_chart_alternatives(self):
        raw = self.files["index.html"].decode("utf-8")
        self.assertRegex(raw, r"@media\s*[^{}]*max-width")
        self.assertRegex(raw, r":focus-visible\{[^}]*outline:")
        self.assertIn("overflow-x:auto", raw)
        self.assertNotRegex(raw, r"outline\s*:\s*(?:none|0)\s*[;}]")
        for attrs in Document(raw).elements("svg"):
            self.assertEqual(attrs.get("aria-hidden"), "true")

    def test_independent_checker_rejects_corrupt_generated_value(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "data").mkdir()
            data = json.loads(self.files["data/spending.json"])
            data["services_total"][data["latest_year"]]["v"] += 1
            (site / "data/spending.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
                independent_data_checks(site, cells())

    def test_built_product_http_bytes_types_and_private_404s(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(self.site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            for name, content in self.files.items():
                with self.subTest(name=name), urlopen(base + "/" + name, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), content)
                    expected = ("text/html" if name.endswith(".html") else
                                "application/json" if name.endswith(".json") else "image/svg+xml")
                    self.assertEqual(response.headers.get_content_type(), expected)
            with urlopen(base + "/", timeout=5) as response:
                self.assertEqual(response.read(), self.files["index.html"])
            for name in ("README.md", "AGENTS.md", ".git/config", ".env", "scripts/build.py",
                         "tests/test_product.py", "data/raw/", "data/sources.json", "data/audit/index.json",
                         "data/receipts.json", "data/audit/", "docs/receipts-methods.md",
                         "factory/project.json", "reference/", "missing.html"):
                with self.subTest(private=name), self.assertRaises(HTTPError) as caught:
                    urlopen(base + "/" + name, timeout=5)
                self.assertEqual(caught.exception.code, 404)
                caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


class PublicationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.project = self.work / "project"
        for name in ("static", "scripts", "tests", ".git", "data", "assets"):
            (self.project / name).mkdir(parents=True)
            (self.project / name / "keep.txt").write_text("private sentinel")
        (self.project / "README.md").write_text("private documentation")

    def test_builder_rejects_unsafe_targets_without_reading_sources(self):
        original = snapshot(self.project)
        with patch.object(builder, "ROOT", self.project), patch.object(builder, "build_data") as read:
            for target in (self.project, self.project.parent, self.project / "static",
                           self.project / "scripts", self.project / "tests", self.project / ".git",
                           self.project / "data", self.project / "README.md",
                           self.project / "static/generated"):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    builder.build(target)
            read.assert_not_called()
        self.assertEqual(snapshot(self.project), original)

    def test_contaminated_and_symlinked_output_preserved(self):
        output = self.work / "public"
        output.mkdir()
        (output / "index.html").write_text("last good")
        (output / "credentials.json").write_text("private")
        before = snapshot(output)
        with self.assertRaises(ValueError):
            builder.build(output)
        self.assertEqual(snapshot(output), before)
        (output / "credentials.json").unlink()
        (output / "data").symlink_to(self.project / "data", target_is_directory=True)
        with self.assertRaises(ValueError):
            builder.build(output)
        self.assertTrue((output / "data").is_symlink())
        link = self.work / "linked"
        link.symlink_to(output, target_is_directory=True)
        for target in (link, link / "child"):
            with self.assertRaises(ValueError):
                builder.build(target)
        self.assertFalse((output / "child").exists())

    def test_failed_source_validation_keeps_last_good_publication(self):
        output = self.work / "public"
        (output / "data").mkdir(parents=True)
        for name in builder.PUBLIC_FILES:
            (output / name).write_text("last good")
        before = snapshot(output)
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value={}), patch.object(
                builder, "validate_receipts"), patch.object(
                builder, "build_data", side_effect=ValueError("source hash mismatch")):
            with self.assertRaisesRegex(ValueError, "source hash mismatch"):
                builder.build(output)
        self.assertEqual(snapshot(output), before)
        self.assertFalse((self.project / "data/spending.json").exists())

    def test_exact_allowlist_and_legacy_cleanup(self):
        output = self.work / "public"
        output.mkdir()
        (output / "styles.css").write_text("old baseline")
        public = {name: f"public {name}".encode() for name in builder.PUBLIC_FILES}
        before = snapshot(self.project)
        receipts = {"private_receipt_sentinel": "only in the private build root"}
        self.assertEqual(builder.PUBLIC_FILES, {
            "index.html", "taxes.html", "methods.html", "icon.svg",
            "data/spending.json", "data/taxes.json"})
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value=receipts) as receipt_read, patch.object(
                builder, "validate_receipts") as receipt_check, patch.object(
                builder, "build_data", return_value={}), patch.object(
                builder, "payloads", return_value=public):
            builder.build(output)
            self.assertEqual(snapshot(output), public)
            for path in (output / name for name in builder.PUBLIC_FILES):
                self.assertEqual(path.stat().st_mode & 0o777, 0o644)
            for name in ("spending", "receipts"):
                self.assertEqual((self.project / f"data/{name}.json").stat().st_mode & 0o777, 0o644)
            self.assertEqual((self.project / "data/spending.json").read_bytes(), public["data/spending.json"])
            self.assertEqual((self.project / "data/receipts.json").read_bytes(), builder.encode_receipts(receipts))
            self.assertTrue(all(b"private_receipt_sentinel" not in content for content in snapshot(output).values()))
            builder.build(output)
            self.assertEqual(snapshot(output), public)
            self.assertEqual(receipt_read.call_count, 2)
            self.assertEqual(receipt_check.call_count, 2)
            for call in receipt_read.call_args_list:
                self.assertEqual(call.args, ())
                self.assertEqual(call.kwargs, {"root": self.project})
            for call in receipt_check.call_args_list:
                self.assertEqual(call.args, (receipts,))
                self.assertEqual(call.kwargs, {"root": self.project})
        self.assertEqual(set(snapshot(self.project)) - set(before), {"data/spending.json", "data/receipts.json"})
        for name, content in before.items():
            self.assertEqual((self.project / name).read_bytes(), content)


    def test_foreign_receipt_sources_cannot_fill_an_empty_build_root(self):
        # Real producer: the module's repository has valid inputs, this root
        # does not. Falling back to module defaults would import private data.
        output = self.work / "public"
        before = snapshot(self.project)
        repository = snapshot(ROOT / "data")
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_data", return_value={}) as spending, patch.object(
                builder, "payloads", return_value={name: b"public" for name in builder.PUBLIC_FILES}):
            with self.assertRaises((FileNotFoundError, ValueError)):
                builder.build(output)
            spending.assert_not_called()
        self.assertFalse(output.exists())
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(snapshot(ROOT / "data"), repository)

    def test_foreign_receipt_validator_cannot_use_repository_catalogue(self):
        # Real validator: a valid receipt object from elsewhere must still be
        # checked against this build root, whose catalogue is deliberately bad.
        (self.project / "data/sources.json").write_text("{}")
        receipts = json.loads((ROOT / "data/receipts.json").read_text())
        output = self.work / "public"
        before = snapshot(self.project)
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value=receipts), patch.object(
                builder, "build_data", return_value={}) as spending, patch.object(
                builder, "payloads", return_value={name: b"public" for name in builder.PUBLIC_FILES}):
            with self.assertRaisesRegex(ValueError, "Source catalogue hash changed"):
                builder.build(output)
            spending.assert_not_called()
        self.assertFalse(output.exists())
        self.assertEqual(snapshot(self.project), before)

    def test_receipt_validation_failure_preserves_private_and_public_files(self):
        output = self.work / "public"
        (output / "data").mkdir(parents=True)
        for name in builder.PUBLIC_FILES | builder.LEGACY_FILES:
            (output / name).write_text("last good")
        for name in ("spending", "receipts"):
            (self.project / f"data/{name}.json").write_text("last good private")
        before, private = snapshot(output), snapshot(self.project)
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value={}), patch.object(
                builder, "validate_receipts", side_effect=ValueError("bad receipt source")) as check, patch.object(
                builder, "build_data") as spending:
            with self.assertRaisesRegex(ValueError, "bad receipt source"):
                builder.build(output)
            check.assert_called_once_with({}, root=self.project)
            spending.assert_not_called()
        self.assertEqual(snapshot(output), before)
        self.assertEqual(snapshot(self.project), private)

    def test_receipt_private_target_rejects_symlink_and_directory(self):
        foreign = self.work / "foreign.json"
        foreign.write_text("foreign private sentinel")
        target = self.project / "data/receipts.json"
        for kind in ("symlink", "directory"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    target.symlink_to(foreign)
                else:
                    target.mkdir()
                before = snapshot(self.project)
                with patch.object(builder, "ROOT", self.project), patch.object(
                        builder, "build_receipts") as read:
                    with self.assertRaisesRegex(ValueError, "receipts.json must be a regular file"):
                        builder.build(self.work / "public")
                    read.assert_not_called()
                self.assertEqual(snapshot(self.project), before)
                self.assertEqual(foreign.read_text(), "foreign private sentinel")
                self.assertFalse((self.work / "public").exists())
                if kind == "symlink":
                    target.unlink()
                else:
                    target.rmdir()

    def test_receipts_do_not_extend_public_payload_contract(self):
        output = self.work / "public"
        public = {name: b"public" for name in builder.PUBLIC_FILES}
        public["data/receipts.json"] = b"private receipt sentinel"
        before = snapshot(self.project)
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value={}), patch.object(
                builder, "validate_receipts"), patch.object(builder, "build_data", return_value={}), patch.object(
                builder, "payloads", return_value=public):
            with self.assertRaisesRegex(ValueError, "unexpected public payload"):
                builder.build(output)
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse(output.exists())

    def test_no_private_writes_still_validates_receipts_in_build_root(self):
        output = self.work / "public"
        public = {name: b"public" for name in builder.PUBLIC_FILES}
        before = snapshot(self.project)
        with patch.object(builder, "ROOT", self.project), patch.object(
                builder, "build_receipts", return_value={}) as read, patch.object(
                builder, "validate_receipts") as check, patch.object(
                builder, "build_data", return_value={}), patch.object(builder, "payloads", return_value=public):
            builder.build(output, write_data=False)
            read.assert_called_once_with(root=self.project)
            check.assert_called_once_with({}, root=self.project)
        self.assertEqual(snapshot(output), public)
        self.assertEqual(snapshot(self.project), before)

    def test_missing_is_not_zero(self):
        for marker in (None, "", "-", " - "):
            self.assertIsNone(build_data.number(marker))
        self.assertEqual(build_data.number(0), 0.0)
        with self.assertRaises(ValueError):
            build_data.number(float("nan"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
