"""Exercise the actual embedded health gates without SSH or disk access."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GrafanaStorageHealthTests(unittest.TestCase):
    def check_health(self, data, accepted):
        script = (ROOT/'scripts/prepare-grafana-storage.ps1').read_text()
        gates = re.findall(r'nvme smart-log[^\n]+python3 -c \'([^\n]+)\'', script)
        self.assertEqual(len(gates), 2)
        for number, code in enumerate(gates):
            with self.subTest(gate=number):
                result = subprocess.run([sys.executable,'-c',code],
                                        input=json.dumps(data), text=True, capture_output=True)
                self.assertEqual(result.returncode == 0, accepted, result.stderr)

    def test_standard_nvme_json_spare_field(self):
        self.check_health({'critical_warning':0,'media_errors':215,'avail_spare':99}, True)

    def test_verbose_critical_warning_object(self):
        self.check_health({'critical_warning':{'value':0,'available_spare':0},'media_errors':215,'avail_spare':99}, True)

    def test_rejects_missing_spare_field(self):
        self.check_health({'critical_warning':0,'media_errors':215}, False)

    def test_rejects_low_spare(self):
        self.check_health({'critical_warning':0,'media_errors':215,'avail_spare':98}, False)

    def test_rejects_new_media_errors(self):
        self.check_health({'critical_warning':0,'media_errors':216,'avail_spare':99}, False)

    def test_rejects_critical_warning(self):
        self.check_health({'critical_warning':1,'media_errors':215,'avail_spare':99}, False)


if __name__ == '__main__':
    unittest.main()
