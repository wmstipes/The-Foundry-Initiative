import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('grafana_validator', ROOT/'scripts/validate-grafana.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class GrafanaBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)/'grafana'
        shutil.copytree(ROOT/'k8s/grafana', self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def mutate_yaml(self, name, mutation):
        path = self.base/name
        data = yaml.safe_load(path.read_text())
        mutation(data)
        path.write_text(yaml.safe_dump(data))

    def test_valid_configuration(self):
        validator.validate(self.base)

    def test_rejects_prometheus_storage_reuse(self):
        self.mutate_yaml('grafana-local-pv.yaml', lambda d: d['spec']['local'].update(path='/mnt/signalforge-prometheus/data'))
        with self.assertRaisesRegex(ValueError, 'isolated storage'):
            validator.validate(self.base)

    def test_rejects_public_service(self):
        self.mutate_yaml('grafana-service.yaml', lambda d: d['spec'].update(type='NodePort'))
        with self.assertRaisesRegex(ValueError, 'exposure'):
            validator.validate(self.base)

    def test_rejects_inline_credentials(self):
        def change(d):
            env = d['spec']['template']['spec']['containers'][0]['env']
            env[3] = {'name':'GF_SECURITY_ADMIN_PASSWORD','value':'fixture-not-a-real-secret'}
        self.mutate_yaml('grafana-deployment.yaml', change)
        with self.assertRaisesRegex(ValueError, 'Secret references'):
            validator.validate(self.base)

    def test_rejects_unpinned_image(self):
        self.mutate_yaml('grafana-deployment.yaml', lambda d: d['spec']['template']['spec']['containers'][0].update(image='grafana/grafana:latest'))
        with self.assertRaisesRegex(ValueError, 'Unverified'):
            validator.validate(self.base)

    def test_rejects_api_token(self):
        self.mutate_yaml('grafana-deployment.yaml', lambda d: d['spec']['template']['spec'].update(automountServiceAccountToken=True))
        with self.assertRaisesRegex(ValueError, 'API token'):
            validator.validate(self.base)

    def test_rejects_missing_data_zero_fallback(self):
        path = self.base/'dashboards/signalforge-restaurant-overview.json'
        dashboard = json.loads(path.read_text())
        dashboard['panels'][0]['targets'][0]['expr'] += ' or vector(0)'
        path.write_text(json.dumps(dashboard))
        with self.assertRaisesRegex(ValueError, 'Missing data'):
            validator.validate(self.base)

    @unittest.skipUnless(shutil.which('bash'), 'Bash is required for the SSH stdin regression')
    def test_preflight_accepts_windows_native_pipeline_line_endings(self):
        helper = (ROOT/'scripts/get-grafana-preflight.ps1').read_text()
        command = re.search(r'\$HostChecks.*?\$SshTarget "([^"]+)"', helper, re.S).group(1)
        result = subprocess.run([shutil.which('bash'),'-c',command],
                                input=b'printf "verified\\n"\r\nexit\r\n',capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,b'verified\n')

    @unittest.skipUnless(shutil.which('bash'), 'Bash is required for shell syntax validation')
    def test_storage_host_script_syntax_without_execution(self):
        helper = (ROOT/'scripts/prepare-grafana-storage.ps1').read_text()
        body = re.search(r"\$HostScript = @'\n(.*?)\n'@",helper,re.S).group(1)
        result = subprocess.run(
            [shutil.which('bash'),'-n'],
            input=body.encode('utf-8'),
            capture_output=True,
        )
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
