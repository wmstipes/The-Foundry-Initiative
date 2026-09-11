import hashlib
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/manage-prometheus-alerts.ps1'


def normalized_hash(text):
    normalized = text.replace('\r\n', '\n').rstrip('\r\n') + '\n'
    return hashlib.sha256(normalized.encode()).hexdigest()


class AlertActivationGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding='utf-8-sig')

    def test_activation_and_rollback_are_explicit(self):
        self.assertIn('[switch]$Activate', self.source)
        self.assertIn('[switch]$Rollback', self.source)
        self.assertIn('if ($Activate -and $Rollback)', self.source)
        self.assertIn('if (-not $Activate)', self.source)
        self.assertIn('PLAN ONLY: no cluster objects were changed.', self.source)

    def test_mutation_follows_baseline_and_recovery_guards(self):
        baseline = self.source.index('if ($State -ne "baseline")')
        recovery = self.source.index('$SavedRecovery = Save-RecoveryConfigMap')
        apply_candidate = self.source.index('Invoke-Kubectl @("apply", "-f", $ManifestPath)')
        self.assertLess(baseline, recovery)
        self.assertLess(recovery, apply_candidate)
        self.assertIn('if ($Changed)', self.source)
        self.assertIn('Invoke-Rollback $SavedRecovery', self.source)

    def test_candidate_hashes_match_manifest(self):
        manifest = yaml.safe_load(
            (ROOT/'k8s/prometheus/prometheus-config.yaml').read_text(encoding='utf-8-sig')
        )
        expected_config = re.search(r'\$CandidateConfigHash = "([0-9a-f]{64})"', self.source).group(1)
        expected_rules = re.search(r'\$CandidateRuleHash = "([0-9a-f]{64})"', self.source).group(1)
        self.assertEqual(normalized_hash(manifest['data']['prometheus.yml']), expected_config)
        self.assertEqual(normalized_hash(manifest['data']['restaurant-scrape.rules.yaml']), expected_rules)

    def test_scope_and_no_receiver_are_preserved(self):
        self.assertIn('job=\"restaurant-api\",namespace=\"forge-restaurant\"', self.source)
        config = yaml.safe_load(
            yaml.safe_load((ROOT/'k8s/prometheus/prometheus-config.yaml').read_text())['data']['prometheus.yml']
        )
        self.assertNotIn('alerting', config)

    def test_broad_deploy_refuses_first_activation(self):
        deploy = (ROOT/'scripts/deploy-prometheus.ps1').read_text(encoding='utf-8-sig')
        guard = deploy.index('if ($CandidateIncludesRules)')
        first_apply = deploy.index('kubectl apply -f')
        self.assertLess(guard, first_apply)
        self.assertIn('Refusing first alert activation through metrics-deploy', deploy)

    def test_windows_diff_fallback_precedes_kubectl_diff(self):
        fallback = self.source.index('function Enable-KubectlDiff')
        invocation = self.source.index('    Enable-KubectlDiff\n')
        kubectl_diff = self.source.index('    & kubectl diff -f $ManifestPath')
        self.assertLess(fallback, invocation)
        self.assertLess(invocation, kubectl_diff)
        self.assertIn('Git\\usr\\bin\\diff.exe', self.source)
        self.assertIn('Get-Command diff.exe -CommandType Application', self.source)
        self.assertNotIn('Get-Command diff -ErrorAction', self.source)


if __name__ == '__main__':
    unittest.main()
