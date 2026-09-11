# Limited alerting activation review

Status: Activated and verified on 2026-09-11 after explicit operator approval. No notification delivery is claimed.

## Exact change

The existing `prometheus-config` ConfigMap gains one embedded file, `restaurant-scrape.rules.yaml`, byte-equivalent in YAML meaning to the canonical offline-tested rules. `prometheus.yml` gains one `rule_files` entry for `/etc/prometheus/restaurant-scrape.rules.yaml`. The existing Deployment already mounts the entire ConfigMap read-only at `/etc/prometheus`.

No Deployment template, image, Service, RBAC, storage, Grafana setting, Alertmanager, receiver, credential, notification channel, exporter or application resource changes. The evaluator remains the single existing Prometheus instance, so its own outage is still invisible to these rules.

## Read-only review gate

From a clean checkout of the activation-review branch, run:

```powershell
python .\scripts\validate-alert-rules.py
python .\scripts\validate-k8s-manifests.py
python -m unittest discover -s tests -p 'test_alert_rules.py'
python -m unittest discover -s tests -p 'test_prometheus_alert_activation.py'
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 metrics-alerts-plan
```

The last command checks the exact known ConfigMap hash, expected Kubernetes context, Prometheus 3.13.2 image, one ready evaluator, and three healthy scoped targets. It inspects existing SignalForge rule state, summarizes 24 hours of target-count samples, asks the API server to validate the candidate, prints `kubectl diff`, and exits with `PLAN ONLY`. Port-forwarding is local process state, not a cluster object.

On Windows, `kubectl diff` still expects a `diff.exe`; PowerShell's built-in `diff` alias does not satisfy that requirement. If the executable is not already on `PATH`, the helper locates the copy bundled with Git for Windows and adds only its directory to the helper process environment. Failure to locate it stops the plan without changing the cluster.

While the live ConfigMap remains at the pre-activation baseline, the broad `metrics-deploy` helper refuses to apply a repository manifest containing this rule wiring. This prevents a routine redeployment from bypassing the dedicated review, recovery and verification path. Once the candidate is already live, ordinary redeployment remains available.

Review the reported history for normal rollouts or maintenance that would make the provisional five-minute warning or two-minute critical delays noisy. Missing history is not success. The plan does not generate traffic or inject failure, and its history query cannot establish user-facing availability.

## Approved activation procedure

After the plan output and diff were accepted, the operator ran the explicit direct command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\manage-prometheus-alerts.ps1 -Activate
```

Activation is allowed only from the exact Milestone 030 baseline ConfigMap. Before applying anything, the helper saves and re-reads a recovery ConfigMap under `%USERPROFILE%\SignalForge-Backups\prometheus`. It then applies only `prometheus-config`, restarts only `deployment/prometheus`, waits for rollout, confirms three healthy Restaurant API targets, and requires exactly two accepted alert rules with `health=ok` and `state=inactive`.

This creates evaluator-visible rules only. With no Alertmanager or receiver, firing state is visible through Prometheus but no message is delivered. A successful inactive check does not prove warning/critical live timing; record subsequent naturally occurring evidence without causing an outage.

## Activation evidence

- Approval: Mike explicitly approved Milestone 030 alert activation after PR #6 merged at `f54b961` and clean `main` was confirmed.
- Preflight: exact baseline ConfigMap, three healthy targets, no candidate rules loaded, and 2,881 of 2,881 30-second samples at three targets over the preceding 24 hours.
- Change: only `configmap/prometheus-config` was configured; only `deployment/prometheus` was restarted.
- Rollout: completed successfully.
- Immediate validation: three healthy targets; both accepted rules loaded with `health=ok` and `state=inactive`.
- Independent follow-up: live ConfigMap classified as `candidate`, the repository diff was empty, and both rules remained healthy and inactive.
- Recovery file: `C:\Users\wmsti\SignalForge-Backups\prometheus\alert-activation-20260911-154646Z.json`, 1,587 bytes, written at 2026-09-11 15:46:46 UTC.
- Recovery SHA-256: `BE7D39DD99715B70A99E5151D7E268EBA197F8F7C1F7E61D6C338468558403FA`.
- Rollback: not invoked because all post-change validation passed.

No failure was injected. This evidence establishes rule loading and healthy inactive evaluation, not delivered notifications, real-incident timing, application availability, or independent evaluator monitoring.

## Failure and rollback

If any post-mutation step fails, the helper attempts to reapply the saved baseline ConfigMap, restart Prometheus, and verify three healthy targets with the candidate rules absent. It retains the recovery file in all cases. If automatic rollback also fails, stop and use the exact path printed by the helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\manage-prometheus-alerts.ps1 `
  -Rollback `
  -RecoveryFile "C:\Users\<operator>\SignalForge-Backups\prometheus\alert-activation-<timestamp>Z.json"
```

Rollback accepts only a file whose name, namespace and normalized baseline configuration hash match the known pre-activation state. It does not delete the ConfigMap, PV, PVC, TSDB data or rule source. A Prometheus restart creates a short collection/evaluation gap but preserves retained TSDB history.

## Maintenance and interpretation

- Planned application scale-down or maintenance can legitimately satisfy these service-level coverage expressions; record or review the condition rather than treating every firing state as an incident.
- More than three healthy targets does not fire a coverage alert. A failed extra rollout target can therefore remain diagnostic rather than alerting.
- The alerts measure scrape coverage, not end-user availability, latency, error rate, notification delivery or Prometheus self-health.
- Changing the manual three-replica baseline, either delay, receiver architecture or failure-testing scope requires a new review rather than an ad hoc live edit.
