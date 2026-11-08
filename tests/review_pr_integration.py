"""Explicit real-tool integration, never GitHub access.

The inherited non-test_ filename intentionally excludes optional analyzer tooling
from ordinary unit-test discovery. The review gate invokes this file explicitly.
"""

from pathlib import Path
from html.parser import HTMLParser
import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import review_pr as review


class RealAnalyzerTests(unittest.TestCase):
    def test_real_container_cannot_observe_parent_token_process_or_host_files(self):
        if not os.environ.get("REVIEW_ANALYZER_IMAGE"):
            self.skipTest("Container integration requires the built trusted analyzer image")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            command = review.analyzer_command("ruff", [], directory)
            probe = (
                "import json,os,pathlib,socket; "
                "assert os.getpid()==1; "
                "assert not pathlib.Path('/var/run/docker.sock').exists(); "
                "assert not pathlib.Path('/home/user/project').exists(); "
                "assert not os.environ.get('GITHUB_TOKEN'); "
                "assert not os.environ.get('GH_TOKEN'); "
                "assert [n for _,n in socket.if_nameindex()]==['lo']; "
                "assert 'CapEff:\\t0000000000000000' in pathlib.Path('/proc/self/status').read_text(); "
                "print(json.dumps({'pid_namespace':True,'network_disabled':True,'no_token':True,'no_host_files':True}))"
            )
            command[-4:] = ["python", "-I", "-c", probe]
            with patch.dict(
                os.environ,
                {"GITHUB_TOKEN": "synthetic-parent-only", "GH_TOKEN": "synthetic-parent-only"},
            ):
                process = subprocess.run(
                    command, capture_output=True, encoding="utf-8", check=True, timeout=30
                )
            self.assertTrue(all(json.loads(process.stdout).values()))
            # Host-owned input directory is readable but cannot be modified.
            command[-1] = "from pathlib import Path; Path('/scan/forbidden').write_text('x')"
            denied = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=30)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("Read-only file system", denied.stderr)
            self.assertFalse((directory / "forbidden").exists())

    def test_real_tools_ignore_parent_pythonpath_and_pr_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "data"
            directory.mkdir()
            sentinel = root / "must-not-exist"
            (root / "sitecustomize.py").write_text(
                f"open({str(sentinel)!r}, 'w').write('executed')"
            )
            (root / "ruff.toml").write_text('lint.ignore = ["F821"]\n')
            (root / "pyproject.toml").write_text('[tool.bandit]\nskips = ["B301"]\n')
            (directory / "0.py").write_text(
                "import pickle\nresult = 未定义\nvalue = pickle.loads(b'x')\n"
            )
            with patch.dict(
                os.environ, {"PYTHONPATH": str(root), "GITHUB_TOKEN": "synthetic-do-not-inherit"}
            ):
                findings = review.analyze(
                    directory, {"0.py": ("[literal](https://evil.test).py", {2, 3})}
                )
            self.assertTrue(
                any("F821" in finding[2] and "未定义" in finding[3] for finding in findings)
            )
            self.assertTrue(any("B301" in finding[2] for finding in findings))
            self.assertFalse(sentinel.exists())

    def test_rendered_adversarial_payload_has_only_literal_inline_content(self):
        corpus = [
            "docs/[click](https://evil.test)/x.py",
            "![image](https://evil.test)",
            "`code` **bold** _italic_ @someone #123",
            "https://evil.test www.evil.test someone@evil.test",
            "</code><img src=x> &lt;tag&gt;",
            "line\n# forged heading",
            "😀 & < > `",
        ]
        findings = [(value, index + 1, value, value) for index, value in enumerate(corpus)]
        payload = review.review_payload("a" * 40, "marker", findings, len(corpus), len(corpus))
        # markdown-it-py is already Bandit's Rich dependency, not a production import.
        process = subprocess.run(
            [
                os.environ["REVIEW_ANALYZER_PYTHON"],
                "-I",
                "-c",
                "import json,sys; from markdown_it import MarkdownIt; "
                "print(json.dumps([MarkdownIt('commonmark').render(s) for s in json.load(sys.stdin)]))",
            ],
            input=json.dumps(
                [payload["body"], *(comment["body"] for comment in payload["comments"])]
            ),
            capture_output=True,
            encoding="utf-8",
            check=True,
            env={},
            timeout=30,
        )
        rendered = json.loads(process.stdout)

        class Inspector(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.tags = []
                self.values = []
                self.in_code = False

            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)
                self.in_code = tag == "code"

            def handle_endtag(self, tag):
                if tag == "code":
                    self.in_code = False

            def handle_data(self, data):
                if self.in_code:
                    self.values.append(data)

        for index, body in enumerate(rendered):
            parser = Inspector()
            parser.feed(body)
            self.assertNotIn("a", parser.tags)
            self.assertNotIn("img", parser.tags)
            if index:
                expected = corpus[index - 1].replace("\n", "\\u000a")
                self.assertEqual(parser.values, [expected, expected])
        artifact = os.environ.get("REVIEW_RENDER_ARTIFACT")
        if artifact:
            Path(artifact).write_text(
                "<!doctype html><meta charset=utf-8><title>Literal review fixture</title>"
                + "\n<hr>\n".join(rendered)
            )

    def test_real_tools_find_correctness_and_security_without_executing_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sentinel = directory / "must-not-exist"
            source = (
                "import pickle\nfrom pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('executed')\n"
                "result = undefined_review_name  # noqa\n"
                "value = pickle.loads(b'not-a-pickle')  # nosec\n"
            )
            (directory / "0.py").write_text(source)
            findings = review.analyze(directory, {"0.py": ("builder/fixture.py", {3, 4, 5})})
            self.assertTrue(any("F821" in f[2] and f[1] == 4 for f in findings))
            self.assertTrue(any("B301" in f[2] and f[1] == 5 for f in findings))
            self.assertFalse(sentinel.exists(), "PR code must never execute")
            old_only = review.analyze(directory, {"0.py": ("builder/fixture.py", {2})})
            self.assertEqual(old_only, [])

    def test_real_tools_accept_clean_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "0.py").write_text("def double(value):\n    return value * 2\n")
            self.assertEqual(review.analyze(directory, {"0.py": ("clean.py", {1, 2})}), [])

    def test_real_tools_do_not_claim_syntax_errors_are_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "0.py").write_text("def broken(:\n")
            with self.assertRaises(review.ReviewError):
                review.analyze(directory, {"0.py": ("broken.py", {1})})


if __name__ == "__main__":
    unittest.main()
