# Offline Restaurant API alert rules

Milestone 030, offline phase only. Nothing in this directory is mounted into or referenced by the live Prometheus configuration. These files are not Kubernetes manifests. Do not run a deployment helper or add `rule_files` to activate them during this phase.

The accepted [Milestone 029 specification](../../docs/observability/limited-alerting-specification.md) defines two service-level scrape-coverage conditions: warning for one or two healthy targets over five minutes, and critical for no healthy targets over two minutes. The expected three-target baseline and both delays remain provisional operator choices, not measured SLOs.

## Files and checks

- `restaurant-scrape.rules.yaml`: the two candidate rules, stable static labels, diagnostic annotations, and existing runbook link.
- `scripts/validate-alert-rules.py`: static design and inactive-configuration guardrails; not a PromQL parser.
- `scripts/export-alert-rule-tests.py`: deterministic generator for 19 synthetic promtool scenarios, with expected states independent of the rule file.
- `scripts/test-alert-rules.py`: local runner requiring an existing promtool 3.13.2 binary; fails if missing, wrong-version, or any validation step fails.
- `tests/test_alert_rules.py`: source-level and negative regression tests, not execution of the PromQL expressions.
- `.github/workflows/alert-rule-validation.yml`: PR/main CI using the same Prometheus 3.13.2 image version as existing repository validation. Containers run with no network and read-only repository mounts; pulling the image and installing PyYAML require network before offline evaluation.

## Local validation

Use the repository Python environment with its existing validation dependency, PyYAML 6.0.2. From the repository root:

```powershell
python .\scripts\validate-alert-rules.py
python -m unittest discover -s tests -p 'test_alert_rules.py'
```

If promtool 3.13.2 is already installed, run the complete offline checks:

```powershell
python .\scripts\test-alert-rules.py --promtool "C:\path\to\promtool.exe"
```

Replace the placeholder with the actual executable path. The runner does not install software, contact the cluster, load a Prometheus server configuration, or change live resources. Temporary fixture files are removed on exit. Alternatively, let the new GitHub Actions job execute the pinned evaluator; do not substitute static-check success for that job's result.

The generated YAML has an absolute rule-file path for the current checkout. CI mounts the checkout at that same absolute path inside the container. Regenerate fixtures after moving a checkout; do not commit environment-specific generated YAML.

## Fixture coverage and interpretation

Every checkpoint asserts both rule firing results and the complete `ALERTS` vector, including pending states, static labels, and absence of overlapping alerts. Firing checks assert expanded annotations. Fixtures cover:

- healthy/idle traffic, one/two healthy targets, all-down and absent startup;
- explicit staleness versus missing samples aging through the default lookback;
- all-down to absent continuity, brief deficits, changing target counts, and Pod replacement;
- escalation, partial recovery with independent delays, full recovery, and extra rollout targets;
- unrelated jobs/namespaces that must not mask scoped absence or partial coverage.

The critical expression's numeric value differs between all-down and absent branches; its annotation intentionally does not call `$value` a target count. Query errors and a stopped evaluator are not simulated as successful empty vectors. No promtool fixture here demonstrates monitoring self-health, delivered notifications, or real discovery timing.

## Current evidence and activation gate

Local static validation, 13 regression tests, existing manifest validation, and 17 Grafana regression tests passed during preparation. Promtool and Docker were unavailable in the preparation workspace; an attempted official binary download timed out. They were not executed locally. Subsequently, [GitHub Actions run 34542077003](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/34542077003) passed on 2026-09-10 for commit `29a6e31`: real promtool 3.13.2 validated both rules and passed all 19 scenarios, and all 13 source-level tests passed. No rule or fixture changes were needed. This is offline synthetic evidence, not live-cluster validation; PR #5 remains in draft.

With pinned-evaluator evidence recorded, the remaining activation prerequisites include review of ordinary rollout/replacement timing, confirm the manual replica baseline, and review a minimal rule-loading change plus rollback. Separately approve any cluster mutation. An eventual activation review must define how rule state is inspected without implying notification delivery, handle planned maintenance, and confirm the monitoring-system failure blind spot. No receiver, Alertmanager, self-scrape, dashboard change, or new exporter is included here.

Rollback for this offline phase is to revert the repository change; there is no live configuration to roll back. Live rollback procedures belong to the later activation review, not to this unactivated package.

Reference: [Prometheus rule unit testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/) and [alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/).
