import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load('alert_validator', 'validate-alert-rules.py')
exporter = load('alert_exporter', 'export-alert-rule-tests.py')
runner = load('alert_runner', 'test-alert-rules.py')


class AlertScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('monitoring/alerts', 'k8s/prometheus', 'k8s/grafana/config'):
            shutil.copytree(ROOT/name, self.root/name)

    def mutate(self, change):
        path = self.root/'monitoring/alerts/restaurant-scrape.rules.yaml'
        doc = yaml.safe_load(path.read_text())
        change(doc['groups'][0]['rules'])
        path.write_text(yaml.safe_dump(doc))

    def test_accepted_scope(self):
        validator.validate(self.root)

    def test_rejects_changed_expression(self):
        self.mutate(lambda r: r[0].update(expr=r[0]['expr'].replace('> 0', '> bool 0')))
        with self.assertRaisesRegex(ValueError, 'Expression'):
            validator.validate(self.root)

    def test_rejects_unscoped_expression(self):
        self.mutate(lambda r: r[0].update(expr=r[0]['expr'].replace(',namespace="forge-restaurant"', '')))
        with self.assertRaisesRegex(ValueError, 'Expression'):
            validator.validate(self.root)

    def test_rejects_changed_delay(self):
        self.mutate(lambda r: r[0].update({'for': '1m'}))
        with self.assertRaisesRegex(ValueError, 'delay'):
            validator.validate(self.root)

    def test_rejects_dynamic_identity(self):
        self.mutate(lambda r: r[0]['labels'].update(healthy='{{ $value }}'))
        with self.assertRaisesRegex(ValueError, 'static service labels'):
            validator.validate(self.root)

    def test_rejects_overlapping_keep_firing(self):
        self.mutate(lambda r: r[0].update(keep_firing_for='5m'))
        with self.assertRaisesRegex(ValueError, 'Unexpected rule settings'):
            validator.validate(self.root)

    def test_rejects_extra_rule(self):
        self.mutate(lambda r: r.append(dict(r[0])))
        with self.assertRaisesRegex(ValueError, 'two accepted'):
            validator.validate(self.root)

    def test_rejects_misleading_critical_value(self):
        self.mutate(lambda r: r[1]['annotations'].update(description='{{ $value }} healthy'))
        with self.assertRaisesRegex(ValueError, 'not a healthy-target count'):
            validator.validate(self.root)

    def test_rejects_active_wiring_and_receivers(self):
        path = self.root/'k8s/prometheus/prometheus-config.yaml'
        original = yaml.safe_load(path.read_text())
        for field in ('rule_files', 'alerting'):
            with self.subTest(field=field):
                config = yaml.safe_load(original['data']['prometheus.yml'])
                config[field] = []
                doc = dict(original)
                doc['data'] = {'prometheus.yml': yaml.safe_dump(config)}
                path.write_text(yaml.safe_dump(doc))
                with self.assertRaisesRegex(ValueError, 'Offline phase'):
                    validator.validate(self.root)

    def test_fixture_structure(self):
        suite = exporter.build_suite()
        self.assertEqual(suite['evaluation_interval'], '30s')
        self.assertEqual(len(suite['tests']), 19)
        self.assertEqual(len({t['name'] for t in suite['tests']}), 19)
        for test in suite['tests']:
            self.assertEqual(len(test['alert_rule_test']), 2*len(test['promql_expr_test']))
            for check in test['promql_expr_test']:
                self.assertLessEqual(len(check['exp_samples']), 1, test['name'])
                self.assertEqual(check['expr'], 'ALERTS')
        self.assertEqual(yaml.safe_load(yaml.safe_dump(suite)), suite)

    def test_missing_promtool_is_failure(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/test-alert-rules.py'),
                                 '--promtool', str(self.root/'does-not-exist')],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('did not complete', result.stderr)

    def test_wrong_version_stops_before_tests(self):
        with patch.object(sys, 'argv', ['test-alert-rules.py']), \
             patch.object(runner.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, 'promtool, version 3.0.0', '')
            self.assertEqual(runner.main(), 1)
            self.assertEqual(run.call_count, 1)

    def test_promtool_failure_is_not_success(self):
        with patch.object(sys, 'argv', ['test-alert-rules.py']), \
             patch.object(runner.subprocess, 'run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 0, 'promtool, version 3.13.2', ''),
                               subprocess.CalledProcessError(1, 'scope-validator')]
            self.assertEqual(runner.main(), 1)


if __name__ == '__main__':
    unittest.main()
