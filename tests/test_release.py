"""Release artifacts contain exactly the verified build and are reproducible."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("package_release", ROOT / "scripts/package_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
COMMIT = "a" * 40


class ReleasePackage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.site, self.output = root / "site", root / "release"
        (self.site / "life").mkdir(parents=True)
        self.pages = {"index.html": b"<h1>Home</h1>\n", "life/2020.html": b"<p>2020</p>\n"}
        for name, body in self.pages.items():
            (self.site / name).write_bytes(body)
        self.record = {"commit": COMMIT, "files": {
            name: hashlib.sha256(body).hexdigest() for name, body in self.pages.items()}}
        self.write_record()

    def write_record(self):
        (self.site / "build.json").write_text(json.dumps(self.record), encoding="utf-8")

    def package(self):
        return release.package(self.site, self.output, COMMIT)

    def test_archive_and_checksums_cover_exactly_the_built_site(self):
        archive = self.package()
        with tarfile.open(archive) as tar:
            self.assertEqual(set(tar.getnames()), set(self.pages) | {"build.json"})
            for name, body in self.pages.items():
                self.assertEqual(tar.extractfile(name).read(), body)
            self.assertEqual(tar.extractfile("build.json").read(), (self.site / "build.json").read_bytes())
            for member in tar.getmembers():
                self.assertTrue(member.isfile())
                self.assertEqual((member.mtime, member.uid, member.gid, member.mode), (0, 0, 0, 0o644))
        self.assertEqual((self.output / "build.json").read_bytes(), (self.site / "build.json").read_bytes())
        sums = (self.output / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(sums), 2)
        for line in sums:
            digest, name = line.split("  ")
            self.assertEqual(digest, hashlib.sha256((self.output / name).read_bytes()).hexdigest())

    def test_archive_is_identical_despite_mtime_permissions_and_output_path(self):
        first = self.package().read_bytes()
        for name in self.pages:
            os.utime(self.site / name, (123456, 123456))
            (self.site / name).chmod(0o600)
        other = self.output.parent / "another-release"
        second = release.package(self.site, other, COMMIT).read_bytes()
        self.assertEqual(first, second)
        self.assertEqual((self.output / "SHA256SUMS").read_bytes(), (other / "SHA256SUMS").read_bytes())

    def test_different_commit_is_rejected(self):
        self.record["commit"] = "b" * 40
        self.write_record()
        with self.assertRaisesRegex(ValueError, "commit does not match"):
            self.package()
        self.assertFalse(self.output.exists())

    def test_unknown_or_short_commit_is_rejected(self):
        for commit in ("unknown", COMMIT[:7], "../release"):
            with self.subTest(commit=commit), self.assertRaisesRegex(ValueError, "full Git SHA"):
                release.package(self.site, self.output, commit)

    def test_changed_file_is_rejected_before_writing_artifacts(self):
        (self.site / "index.html").write_bytes(b"Changed after verification")
        with self.assertRaisesRegex(ValueError, "does not match its build hash"):
            self.package()
        self.assertFalse(self.output.exists())

    def test_extra_or_missing_files_are_rejected(self):
        extra = self.site / ".env"
        extra.write_text("not part of the build")
        with self.assertRaisesRegex(ValueError, "files differ"):
            self.package()
        extra.unlink()
        (self.site / "index.html").unlink()
        with self.assertRaisesRegex(ValueError, "files differ"):
            self.package()

    def test_symlink_is_rejected_even_when_its_content_matches(self):
        source = self.site / "index.html"
        target = self.site.parent / "outside.html"
        source.rename(target)
        source.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            self.package()

    def test_record_cannot_name_paths_outside_the_site(self):
        for name in ("../outside", "/etc/passwd", "life/../index.html"):
            with self.subTest(name=name):
                self.record["files"][name] = "0" * 64
                self.write_record()
                with self.assertRaisesRegex(ValueError, "files differ"):
                    self.package()
                del self.record["files"][name]

    def test_empty_or_self_referencing_record_is_rejected(self):
        for files in ({}, {"build.json": "0" * 64}):
            self.record["files"] = files
            self.write_record()
            with self.assertRaisesRegex(ValueError, "must list the site files"):
                self.package()

    def test_output_inside_site_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the site"):
            release.package(self.site, self.site / "release", COMMIT)


# Exercise the actual publisher without credentials or GitHub writes.
FAKE_GH = '''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["GH_CALLS"], "a") as log:
    log.write(json.dumps(args) + "\\n")
state = os.environ["RELEASE_STATE"]
command = args[1]
if command == "view":
    if "url" in args:
        print("https://example.invalid/release")
    elif state in ("missing", "create-fails"):
        sys.exit(1)
    else:
        print("false" if state == "published" else "true")
elif command == "create" and state == "create-fails":
    sys.exit(1)
elif command == "upload":
    for name in args[3:]:
        if name != "--clobber" and not Path(name).is_file():
            sys.exit(2)
    if state == "upload-fails":
        sys.exit(1)
'''


class ReleasePublisher(unittest.TestCase):
    def run_publisher(self, state):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake = root / "gh"
            fake.write_text(f"#!{sys.executable}\n" + FAKE_GH, encoding="utf-8")
            fake.chmod(0o755)
            (root / "release").mkdir()
            for name in ("site.tar.gz", "build.json", "SHA256SUMS"):
                (root / "release" / name).write_text("artifact")
            calls = root / "calls.jsonl"
            summary = root / "summary.md"
            env = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}", "COMMIT": COMMIT,
                   "LIVE_RUN": "https://example.invalid/live-run", "RUNNER_TEMP": folder,
                   "GITHUB_STEP_SUMMARY": str(summary), "GH_CALLS": str(calls), "RELEASE_STATE": state}
            # The test must never fall back to a real authenticated gh.
            env.pop("GH_TOKEN", None)
            env.pop("GITHUB_TOKEN", None)
            result = subprocess.run(["bash", str(ROOT / "scripts/publish_release.sh")],
                                    env=env, capture_output=True, text=True)
            return result, [json.loads(line) for line in calls.read_text().splitlines()], (
                summary.read_text() if summary.exists() else "")

    def test_new_release_is_drafted_then_uploaded_then_published(self):
        result, calls, summary = self.run_publisher("missing")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[1] for call in calls], ["view", "create", "upload", "edit", "view"])
        self.assertTrue(all(call[2] == f"site-{COMMIT}" for call in calls))
        self.assertIn("--draft", calls[1])
        self.assertEqual(calls[1][calls[1].index("--target") + 1], COMMIT)
        self.assertIn("--draft=false", calls[3])
        self.assertIn("--latest=false", calls[3])
        self.assertIn("https://example.invalid/release", summary)

    def test_published_release_is_not_modified(self):
        result, calls, _ = self.run_publisher("published")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[1] for call in calls], ["view"])

    def test_interrupted_draft_resumes_upload_before_publication(self):
        result, calls, _ = self.run_publisher("draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[1] for call in calls], ["view", "upload", "edit", "view"])
        self.assertIn("--clobber", calls[1])

    def test_upload_failure_never_publishes_partial_release(self):
        result, calls, summary = self.run_publisher("upload-fails")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[1] for call in calls], ["view", "upload"])
        self.assertEqual(summary, "")

    def test_create_failure_stops_without_uploading_or_publishing(self):
        result, calls, _ = self.run_publisher("create-fails")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[1] for call in calls], ["view", "create"])


if __name__ == "__main__":
    unittest.main()
