"""Concrete archive integrity and extraction boundaries for C7 candidate acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("console_candidate", ROOT / "scripts/verify-forgeops-console-candidate.py")
CANDIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANDIDATE)


class ConsoleCandidateArchiveTests(unittest.TestCase):
    def fixture(self, root, extra=None, tamper=False, omit=None):
        bundle = {"protocol": "forgeops.console/v1alpha1", "sourceDigest": "a" * 64}
        files = {"forgeops-console": b"fixture", "forgeops-console-demo": b"fixture",
                 "web/index.html": b"<html></html>", "web/forgeops-bundle.json": json.dumps(bundle).encode(),
                 "README.md": b"fixture", "LICENSE": b"fixture"}
        if omit:
            files.pop(omit)
        manifest = {"schema": "forgeops.console.candidate/v1alpha1", "status": "unsigned-candidate",
                    "commit": "a" * 40, "os": "linux", "arch": "amd64", "bundle": bundle,
                    "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
        if tamper:
            files["web/index.html"] = b"changed after manifest"
        archive = root / "candidate.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for name, data in files.items():
                output.writestr(name, data)
            output.writestr("manifest.json", json.dumps(manifest))
            if extra:
                output.writestr(*extra)
        return archive, hashlib.sha256(archive.read_bytes()).hexdigest()

    def test_valid_candidate_extracts_only_declared_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, digest = self.fixture(root)
            result = CANDIDATE.unpack(archive, root / "installed", digest)
            self.assertEqual(result["commit"], "a" * 40)
            self.assertEqual((root / "installed/web/index.html").read_bytes(), b"<html></html>")

    def test_wrong_archive_checksum_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, _ = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "archive checksum"):
                CANDIDATE.unpack(archive, root / "installed", "0" * 64)
            self.assertFalse((root / "installed").exists())

    def test_changed_member_rejected_even_when_archive_checksum_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, digest = self.fixture(root, tamper=True)
            with self.assertRaisesRegex(ValueError, "member checksum"):
                CANDIDATE.unpack(archive, root / "installed", digest)
            self.assertFalse((root / "installed").exists())

    def test_unsafe_paths_and_links_rejected_before_extraction(self):
        for name in ("../escape", "/absolute", "C:/escape", "web\\escape", "web/../escape", "web/CON", "web/trailing."):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive, digest = self.fixture(root, extra=(name, b"unexpected"))
                with self.assertRaisesRegex(ValueError, "unsafe archive"):
                    CANDIDATE.unpack(archive, root / "installed", digest)
                self.assertFalse((root / "installed").exists())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive, digest = self.fixture(root, extra=(info, b"../escape"))
            with self.assertRaisesRegex(ValueError, "unsafe archive"):
                CANDIDATE.unpack(archive, root / "installed", digest)

    def test_undeclared_or_case_colliding_member_rejected(self):
        for name in ("extra.txt", "README.MD"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive, digest = self.fixture(root, extra=(name, b"unexpected"))
                with self.assertRaises(ValueError):
                    CANDIDATE.unpack(archive, root / "installed", digest)
                self.assertFalse((root / "installed").exists())

    def test_manifest_cannot_omit_required_runtime_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, digest = self.fixture(root, omit="forgeops-console")
            with self.assertRaisesRegex(ValueError, "runtime files missing"):
                CANDIDATE.unpack(archive, root / "installed", digest)


if __name__ == "__main__":
    unittest.main()
