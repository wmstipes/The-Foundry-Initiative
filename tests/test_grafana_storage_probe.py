import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('bash'), 'Requires Bash')
class StorageProbeTests(unittest.TestCase):
    def test_signature_gate(self):
        for name in ('prepare-grafana-storage.ps1','finish-grafana-storage.ps1'):
            script=(ROOT/'scripts'/name).read_text()
            gate=script[script.index('set +e\nprobe_output='):script.index('# Never force a format')]
            prefix='set -eu\npart=/dev/fixture\nblkid() { test "$*" = "-p --no-part-details -o export /dev/fixture" || return 4; printf "%s" "$FIXTURE_TEXT"; return "$FIXTURE_RC"; }\n'
            for rc, output, accepted in [(0,'',True),(2,'',True),(0,'TYPE=ext4\n',False),(8,'',False),(4,'probe error',False),(2,'read error',False)]:
                with self.subTest(helper=name,rc=rc,output=output):
                    fixture = (
                        f'FIXTURE_TEXT={shlex.quote(output)}\n'
                        f'FIXTURE_RC={shlex.quote(str(rc))}\n'
                    )
                    result=subprocess.run(
                        [shutil.which('bash'),'-s'],
                        input=(fixture+prefix+gate).encode('utf-8'),
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode==0,accepted,result.stderr)

    def test_resume_has_no_partition_mutation_and_parses(self):
        script=(ROOT/'scripts/finish-grafana-storage.ps1').read_text()
        body=re.search(r"\$HostScript = @'\n(.*?)\n'@",script,re.S).group(1)
        self.assertNotIn('sfdisk --lock',body)
        self.assertNotIn('--append',body)
        self.assertNotIn('partx --add',body)
        self.assertIn('A8E50BC1-1B9C-419B-A13D-3EE72C29FF56',body)
        result=subprocess.run([shutil.which('bash'),'-n'],input=body.encode('utf-8'),capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':
    unittest.main()
