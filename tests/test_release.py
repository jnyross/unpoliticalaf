"""Release artifacts contain exactly the verified build and are reproducible."""

import gzip
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from builder import feature_flags

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "package_release", ROOT / "scripts/package_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
COMMIT = "a" * 40


class ReleaseGhBoundary(unittest.TestCase):
    def test_malicious_host_and_debug_environment_cannot_redirect_gh(self):
        hostile = {
            "GH_HOST": "attacker.invalid",
            "GH_DEBUG": "api",
            "GH_REPO": "attacker.invalid/other/repo",
            "GH_ENTERPRISE_TOKEN": "test-enterprise",
            "GITHUB_ENTERPRISE_TOKEN": "test-enterprise",
            "GH_CONFIG_DIR": "/intended/config",
            "GH_TOKEN": "test-token",
        }
        with (
            patch.dict(os.environ, hostile),
            patch.object(
                release.subprocess, "run", return_value=SimpleNamespace(stdout=b"[]")
            ) as run,
        ):
            self.assertEqual(release._gh("api", "repos/jnyross/unpoliticalaf/releases"), b"[]")
        args, kwargs = run.call_args
        self.assertEqual(args[0][-2:], ["--hostname", "github.com"])
        self.assertEqual(kwargs["timeout"], 60)
        for name in (
            "GH_HOST",
            "GH_DEBUG",
            "GH_REPO",
            "GH_ENTERPRISE_TOKEN",
            "GITHUB_ENTERPRISE_TOKEN",
        ):
            self.assertNotIn(name, kwargs["env"])
        self.assertEqual(kwargs["env"]["GH_CONFIG_DIR"], "/intended/config")
        self.assertEqual(kwargs["env"]["GH_TOKEN"], "test-token")

    def test_cli_errors_expose_only_exception_type_not_untrusted_details(self):
        errors = [
            ValueError("private build detail"),
            subprocess.CalledProcessError(1, ["secret-command"], output=b"secret-output"),
            subprocess.TimeoutExpired(["secret-command"], 60, output=b"secret-output"),
            tarfile.ReadError("private archive detail"),
        ]
        for error in errors:
            stderr = io.StringIO()
            with (
                self.subTest(error=type(error).__name__),
                patch.object(release, "publish", side_effect=error),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                release.main(["--publish"])
            self.assertEqual(stderr.getvalue(), f"Release failed: {type(error).__name__}\n")


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
        self.record = {
            "commit": COMMIT,
            "feature_flags": dict(feature_flags.production({})),
            "files": {name: hashlib.sha256(body).hexdigest() for name, body in self.pages.items()},
        }
        self.write_record()

    def write_record(self):
        (self.site / "build.json").write_text(json.dumps(self.record), encoding="utf-8")

    def package(self):
        return release.package(self.site, self.output, COMMIT)

    def test_archive_and_checksums_cover_exactly_the_built_site(self):
        archive = self.package()
        self.assertEqual(archive.read_bytes()[4:8], b"\0" * 4)
        with tarfile.open(archive) as tar:
            self.assertEqual(set(tar.getnames()), set(self.pages) | {"build.json"})
            self.assertEqual(tar.getnames(), sorted(tar.getnames()))
            for name, body in self.pages.items():
                self.assertEqual(tar.extractfile(name).read(), body)
            self.assertEqual(
                tar.extractfile("build.json").read(), (self.site / "build.json").read_bytes()
            )
            for member in tar.getmembers():
                self.assertTrue(member.isfile())
                self.assertEqual(
                    (member.mtime, member.uid, member.gid, member.mode), (0, 0, 0, 0o644)
                )
                self.assertEqual((member.uname, member.gname), ("", ""))
        self.assertEqual(
            (self.output / "build.json").read_bytes(), (self.site / "build.json").read_bytes()
        )
        sums = (self.output / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(sums), 2)
        self.assertEqual([line.split("  ")[1] for line in sums], ["build.json", "site.tar.gz"])
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
        self.assertEqual(
            (self.output / "SHA256SUMS").read_bytes(), (other / "SHA256SUMS").read_bytes()
        )

    def test_different_commit_is_rejected(self):
        self.record["commit"] = "b" * 40
        self.write_record()
        with self.assertRaisesRegex(ValueError, "commit does not match"):
            self.package()
        self.assertFalse(self.output.exists())

    def test_unknown_or_short_commit_is_rejected(self):
        for commit in ("unknown", COMMIT[:7], "../release", "A" * 40, "g" * 40, COMMIT + "\n"):
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
                with self.assertRaisesRegex(ValueError, "Unsafe manifest path"):
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

    def test_nonproduction_flags_are_rejected_without_artifacts(self):
        for flags in (
            None,
            {},
            {"chart_interactions": 1, "sticky_navigation": True},
            {"chart_interactions": False, "sticky_navigation": True},
        ):
            self.record["feature_flags"] = flags
            self.write_record()
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.package()
            self.assertFalse(self.output.exists())

    def test_malformed_manifest_and_hashes_are_rejected(self):
        for files in (None, [], {"index.html": 12}, {"index.html": "x" * 64}):
            self.record["files"] = files
            self.write_record()
            with self.subTest(files=files), self.assertRaises(ValueError):
                self.package()
        self.assertFalse(self.output.exists())

    def test_duplicate_manifest_keys_are_not_silently_overwritten(self):
        record = json.dumps(self.record)
        (self.site / "build.json").write_text(
            record.replace('"commit":', f'"commit": "{COMMIT}", "commit":', 1)
        )
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.package()

    def test_directory_and_build_record_symlinks_are_rejected(self):
        target = self.site.parent / "outside"
        target.mkdir()
        (self.site / "linked").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            self.package()
        (self.site / "linked").unlink()
        record = self.site / "build.json"
        record.rename(target / "build.json")
        record.symlink_to(target / "build.json")
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            self.package()

    def test_unsafe_manifest_spellings_are_rejected(self):
        for name in ("./index.html", "life//2020.html", "life\\2020.html", "", "a\nb"):
            self.record["files"] = {name: "0" * 64}
            self.write_record()
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "Unsafe manifest path"),
            ):
                self.package()

    def test_site_root_symlink_and_special_files_are_rejected(self):
        alias = self.site.parent / "alias"
        alias.symlink_to(self.site, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            release.package(alias, self.output, COMMIT)
        os.mkfifo(self.site / "fifo")
        with self.assertRaisesRegex(ValueError, "Special files"):
            self.package()
        self.assertFalse(self.output.exists())

    def test_output_symlinks_cannot_overwrite_unrelated_files(self):
        self.output.mkdir()
        target = self.site.parent / "unrelated"
        target.write_bytes(b"unchanged")
        (self.output / "site.tar.gz").symlink_to(target)
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            self.package()
        self.assertEqual(target.read_bytes(), b"unchanged")


# All publishing tests intercept the subprocess boundary: no real gh or tokens.
class ReleasePublisher(unittest.TestCase):
    def setUp(self):
        fixture = ReleasePackage()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.output = fixture.output
        fixture.package()
        self.calls = []
        self.remote = None
        self.assets = {}
        self.tag_object = {"type": "commit", "sha": COMMIT}
        self.tag_present = True
        self.failure = None
        self.environ = {
            "COMMIT": COMMIT,
            "LIVE_RUN": "https://github.com/jnyross/unpoliticalaf/actions/runs/123",
            "GITHUB_REPOSITORY": "jnyross/unpoliticalaf",
            "RUNNER_TEMP": str(self.output.parent),
            "GITHUB_STEP_SUMMARY": str(self.output.parent / "summary"),
        }
        # package fixture's output is named release, matching the CLI contract.
        gh_patch = patch.object(release, "_gh", side_effect=self.fake_gh)
        self.addCleanup(gh_patch.stop)
        gh_patch.start()

    def seed_release(self, draft=True):
        self.remote = {
            "id": 42,
            "tag_name": f"site-{COMMIT}",
            "draft": draft,
            "target_commitish": COMMIT,
            "html_url": "https://github.com/jnyross/unpoliticalaf/releases/42",
        }

    def fake_gh(self, *args):
        self.calls.append(args)
        if self.failure and self.failure in args:
            raise RuntimeError("injected failure")
        if args[0] == "api":
            endpoint = args[1]
            if "/git/matching-refs/" in endpoint:
                refs = [{"ref": f"refs/tags/site-{COMMIT}", "object": self.tag_object}]
                return json.dumps(refs if self.tag_present else []).encode()
            if "/git/tags/" in endpoint:
                return json.dumps({"object": {"type": "commit", "sha": COMMIT}}).encode()
            if "/releases/assets/" in endpoint:
                return self.assets[endpoint.rsplit("/", 1)[1]]
            if endpoint.endswith("/releases"):
                return json.dumps([[self.remote] if self.remote else []]).encode()
            if endpoint.endswith("/assets"):
                return json.dumps([[{"id": name, "name": name} for name in self.assets]]).encode()
            return json.dumps(self.remote).encode()
        command = args[1]
        if command == "create":
            self.seed_release()
        elif command == "upload":
            path = Path(args[3])
            self.assets[path.name] = path.read_bytes()
        elif command == "edit":
            self.remote["draft"] = False
            self.tag_present = True
        return b""

    def run_publisher(self):
        return release.publish(self.environ)

    def writes(self):
        return [call for call in self.calls if call[0] == "release"]

    def test_new_release_is_drafted_verified_then_published(self):
        self.run_publisher()
        writes = self.writes()
        self.assertEqual(
            [call[1] for call in writes], ["create", "upload", "upload", "upload", "edit"]
        )
        self.assertIn("--draft", writes[0])
        self.assertIn("--latest=false", writes[0])
        self.assertEqual(writes[0][writes[0].index("--target") + 1], COMMIT)
        self.assertIn("--draft=false", writes[-1])
        self.assertIn("--latest=false", writes[-1])
        self.assertFalse(any("--clobber" in call for call in writes))

    def test_published_release_is_verified_but_never_modified(self):
        self.run_publisher()
        self.calls.clear()
        self.run_publisher()
        self.assertEqual(self.writes(), [])

    def test_draft_recovery_uploads_only_missing_assets(self):
        self.seed_release()
        self.assets["build.json"] = (self.output / "build.json").read_bytes()
        self.run_publisher()
        uploads = [Path(call[3]).name for call in self.writes() if call[1] == "upload"]
        self.assertEqual(set(uploads), {"site.tar.gz", "SHA256SUMS"})

    def test_wrong_target_and_tag_are_rejected_without_writes(self):
        self.seed_release()
        self.remote["target_commitish"] = "main"
        with self.assertRaisesRegex(ValueError, "target"):
            self.run_publisher()
        self.assertEqual(self.writes(), [])
        self.remote["target_commitish"] = COMMIT
        self.remote["draft"] = False
        self.tag_object["sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "tag"):
            self.run_publisher()
        self.assertEqual(self.writes(), [])

    def test_annotated_tag_is_peeled_before_verification(self):
        self.seed_release()
        self.tag_object = {"type": "tag", "sha": "c" * 40}
        self.run_publisher()
        self.assertTrue(any("/git/tags/" in call[1] for call in self.calls))

    def test_asset_corruption_or_unknown_asset_prevents_any_writes(self):
        for draft in (True, False):
            self.seed_release(draft)
            complete = {name: (self.output / name).read_bytes() for name in release.ASSET_NAMES}
            for assets in ({**complete, "build.json": b"corrupt"}, {"unexpected": b"unknown"}):
                self.assets = assets
                self.calls.clear()
                with self.assertRaises(ValueError):
                    self.run_publisher()
                self.assertEqual(self.writes(), [])

    def test_incomplete_published_release_is_not_repaired(self):
        self.seed_release(False)
        with self.assertRaisesRegex(ValueError, "missing"):
            self.run_publisher()
        self.assertEqual(self.writes(), [])

    def test_missing_tag_is_allowed_for_a_draft_but_not_a_published_release(self):
        self.seed_release(False)
        self.tag_present = False
        with self.assertRaisesRegex(ValueError, "tag is missing"):
            self.run_publisher()
        self.assertEqual(self.writes(), [])
        self.seed_release(True)
        self.run_publisher()
        self.assertTrue(self.tag_present)

    def test_api_create_and_upload_failures_do_not_publish(self):
        for failure in ("api", "create", "upload"):
            self.failure = failure
            self.remote = None
            self.calls.clear()
            with self.assertRaisesRegex(RuntimeError, "injected"):
                self.run_publisher()
            self.assertFalse(any(call[1] == "edit" for call in self.writes()))

    def test_invalid_commit_proof_url_and_local_corruption_fail_before_api(self):
        for key, value in (
            ("COMMIT", "abc"),
            ("LIVE_RUN", ""),
            ("LIVE_RUN", "https://example.com/fake"),
        ):
            environ = {**self.environ, key: value}
            with self.assertRaises(ValueError):
                release.publish(environ)
            self.assertEqual(self.calls, [])
        (self.output / "site.tar.gz").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.run_publisher()
        self.assertEqual(self.calls, [])

    def test_unapproved_repository_is_rejected_even_with_matching_run_url(self):
        environ = {
            **self.environ,
            "GITHUB_REPOSITORY": "other/repo",
            "LIVE_RUN": "https://github.com/other/repo/actions/runs/123",
        }
        with self.assertRaisesRegex(ValueError, "approved repository"):
            release.publish(environ)
        self.assertEqual(self.calls, [])

    def rewrite_archive(self, transform):
        archive = self.output / "site.tar.gz"
        with tarfile.open(archive) as tar:
            entries = [(member, tar.extractfile(member).read()) for member in tar.getmembers()]
        transform(entries)
        raw = io.BytesIO()
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for member, body in entries:
                    if not member.isfile():
                        body = b""
                    member.size = len(body)
                    tar.addfile(member, io.BytesIO(body))
        archive.write_bytes(raw.getvalue())
        artifacts = {name: (self.output / name).read_bytes() for name in release.ARTIFACT_NAMES}
        (self.output / "SHA256SUMS").write_bytes(release._checksums(artifacts))

    def test_regenerated_checksums_cannot_hide_archive_content_mutations(self):
        original = (self.output / "site.tar.gz").read_bytes()
        transforms = (
            lambda entries: entries.pop(),
            lambda entries: entries.append(entries[-1]),
            lambda entries: entries.reverse(),
            lambda entries: entries.__setitem__(0, (entries[0][0], b"changed build record")),
            lambda entries: entries.__setitem__(-1, (entries[-1][0], b"changed page")),
            lambda entries: setattr(entries[-1][0], "name", "../unsafe"),
            lambda entries: setattr(entries[-1][0], "name", "extra"),
        )
        for transform in transforms:
            (self.output / "site.tar.gz").write_bytes(original)
            self.rewrite_archive(transform)
            with self.subTest(transform=transform), self.assertRaises(ValueError):
                self.run_publisher()
            self.assertEqual(self.calls, [])

    def test_archive_metadata_and_links_are_rejected_before_api(self):
        original = (self.output / "site.tar.gz").read_bytes()
        for attribute, value in (
            ("mtime", 1),
            ("uid", 1),
            ("gid", 1),
            ("mode", 0o755),
            ("uname", "someone"),
            ("gname", "group"),
            ("type", tarfile.SYMTYPE),
            ("type", tarfile.LNKTYPE),
            ("pax_headers", {"comment": "extra metadata"}),
        ):
            (self.output / "site.tar.gz").write_bytes(original)
            self.rewrite_archive(lambda entries: setattr(entries[-1][0], attribute, value))
            with self.subTest(attribute=attribute, value=value), self.assertRaises(ValueError):
                self.run_publisher()
            self.assertEqual(self.calls, [])

    def test_invalid_archive_with_regenerated_checksums_is_rejected(self):
        (self.output / "site.tar.gz").write_bytes(b"not an archive")
        artifacts = {name: (self.output / name).read_bytes() for name in release.ARTIFACT_NAMES}
        (self.output / "SHA256SUMS").write_bytes(release._checksums(artifacts))
        with self.assertRaises((ValueError, tarfile.TarError, OSError)):
            self.run_publisher()
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
