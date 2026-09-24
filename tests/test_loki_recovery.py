"""Safety checks for the offline Loki recovery candidate."""

import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "loki-recovery.py"
SPEC = importlib.util.spec_from_file_location("loki_recovery", SOURCE)
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


class LokiArchiveSafetyTests(unittest.TestCase):
    def archive(self, entries):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "candidate.tar.gz"
        with tarfile.open(path, "w:gz") as output:
            for name, kind in entries:
                info = tarfile.TarInfo(name)
                if kind == "file":
                    payload = b"fixture"
                    info.size = len(payload)
                    output.addfile(info, io.BytesIO(payload))
                elif kind == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = "/mnt/signalforge-loki/data"
                    output.addfile(info)
        return path

    def test_complete_wal_archive_is_accepted(self):
        path = self.archive([("./wal/checkpoint", "file"), ("./chunks/example", "file")])
        self.assertEqual(RECOVERY.validate_archive(path), 2)

    def test_missing_wal_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "WAL"):
            RECOVERY.validate_archive(self.archive([("./chunks/example", "file")]))

    def test_path_escape_and_symlink_are_rejected(self):
        for dangerous in (("../data/secret", "file"), ("/etc/passwd", "file"),
                          ("./wal/link", "symlink")):
            with self.subTest(entry=dangerous):
                with self.assertRaisesRegex(RuntimeError, "Unsafe"):
                    RECOVERY.validate_archive(self.archive([("./wal/good", "file"), dangerous]))


class LokiSshTargetTests(unittest.TestCase):
    def test_reviewed_user_is_required_before_ssh(self):
        with patch.object(RECOVERY, "command") as run:
            with self.assertRaisesRegex(RuntimeError, "Unexpected SSH target"):
                RECOVERY.verify_head_mount("wmsti@192.168.243.110")
            run.assert_not_called()

    def test_reviewed_user_and_host_are_passed_to_ssh(self):
        with patch.object(RECOVERY, "command", return_value="93a19402-4a5b-4689-aed7-f1841c2cb53b ext4 /dev/nvme0n1p3") as run:
            RECOVERY.verify_head_mount(RECOVERY.SSH_HOST)
            self.assertEqual(run.call_args.args[:2], ("ssh", "wmstipes@192.168.243.110"))


if __name__ == "__main__":
    unittest.main()
