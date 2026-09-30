# 2026-09-30 — Headlamp OIDC rejection after Dex recovery rehearsal

- Status: **Resolved for the observed session**, follow-ups open.
- Severity: SEV2 for the Headlamp access failure; administrator CLI/SSH remained available.
- Owner: Mike (operator); Codex assisted with diagnosis and documentation.
- Documentation PR: [#163](https://github.com/wmstipes/The-Foundry-Initiative/pull/163), kept draft/open.
- Times below are September 30, 2026, America/New_York (EDT, UTC−04:00).
- Evidence: operator-supplied terminal output and browser observations. No
  independent remote cluster inspection or exact outage-duration measurement.
- Versions: Kubernetes/kubeadm 1.36.4, Dex 2.44.0, Headlamp 0.45.0,
  containerd 1.7.24; one control-plane node, `forge-head`.

## Summary and impact

A recovered Dex instance supported a fresh Headlamp login during a controlled
issuer-route rehearsal. After routing returned to original Dex, Headlamp sign-in
failed and repeated browser BasicAuth challenges obscured an API-server OIDC
signature rejection. Restarting only the API-server container restored acceptance
of the **same** locally verified token. Fresh browser login then worked; three
BasicAuth prompts occurred during entry, but none recurred during navigation or
refresh. The reason for those initial prompts remains unresolved.

The API restart interrupted management access and coincided with controller
restarts/readiness warnings. All listed Pods were fully Ready/Running afterward,
including the Istio lab. This was not a zero-impact operation.

## Timeline

| Approximate EDT time | Observation or action | Evidence |
| --- | --- | --- |
| 13:15 | Private Dex logical export captured | Config and signing-key UID/resourceVersion unchanged across capture; one signing-key object, nine other CR types empty |
| 13:16 onward | Original and restored Dex rotated independently | Active key IDs differed; four shared verification keys had identical public material |
| 13:48–13:53 | Approved temporary issuer route to recovered Dex; fresh login | Operator could view cluster resources |
| 13:56 | Temporary ingress/policy deleted; issuer served original keys again | Original and recovered Deployments ready, API ready; subsequent login failed |
| 14:54 | Bounded API-server logs inspected | 14 signature/authentication/OIDC matches; exact signature-error phrase identified |
| About 15:00 | Headlamp restarted | Same rejection persisted |
| 15:23 | Direct TokenReview failed | `authenticated=false`; `failed to verify id token signature` |
| 15:24 | Laptop RSA/SHA-256 verification passed | Same token valid against original Dex's HTTPS-published public key |
| 15:26–15:30 | Approved API restart; crictl absent; guarded ctr fallback sent SIGTERM once | Exact API-server container selected; manifest SHA-256 unchanged |
| 15:31–15:32 | API recovered; same-token TokenReview passed | Authenticated and expected user true; no error |
| 15:35 | Fresh Headlamp entry worked after three BasicAuth prompts | Cluster overview usable; every listed Pod ready; API `/readyz=ok` |
| 15:37 | Namespaces/Pods navigation and refresh accepted | No further BasicAuth challenge reported |

## Diagnosis and confidence

Observed: original issuer key ID and public material matched from the laptop and
control-plane host. Live issuer/client/claim/prefix/CA arguments and issuer host
alias matched the intended configuration. Direct TokenReview reproduced the
failure independently of Traefik and Headlamp. Local signature verification
passed, and the same token passed TokenReview after the API-server restart.

Likely explanation: stale in-memory OIDC verification state after switching
between independently rotating providers under one issuer URL. **The exact cache,
key-refresh or transport mechanism was not proven.** A successful restart is
mitigation evidence, not proof of a particular upstream defect.

The browser `/config` JSON parsing error and native BasicAuth dialog were not
sufficient to identify the cryptographic failure. Gateway credentials could fetch
`/config` with HTTP 200. Windows curl also needed `--ssl-revoke-best-effort` for
the private PKI's unavailable revocation information; certificate/hostname
verification remained enabled. This TLS diagnostic issue was distinct from OIDC.

## Commands and remediation

Use [the OIDC troubleshooting runbook](../runbooks/headlamp-oidc-troubleshooting.md)
for bounded private log capture, TokenReview, local signature verification,
restart prerequisites and recovery checks. The accepted restart used `ctr` in
containerd's `k8s.io` namespace, exact Kubernetes container/pod/namespace labels,
one running task, and SIGTERM. No manifest edit or key replacement was performed.
The baseline manifest SHA-256 was
`b74502957d83a7d3f67f51b1e351d4c000e8922a2ded34bf957b87d3821a34d2`.

The attempted `crictl` procedure failed before mutation because the binary was
absent. Do not install tools or repeatedly restart components as a diagnostic loop.
If the API does not return, inspect runtime tasks and kubelet logs using SSH;
restoring an unchanged manifest is not a meaningful rollback for this restart.

## Recovery rehearsal and cleanup limits

The recovered namespace used copied configuration/signing state, namespaced
storage RBAC, default-deny ingress, and initially zero replicas. Content and
expected permission/denial checks passed before startup. A temporary narrowly
scoped gateway policy and higher-priority ingress enabled the browser test.
Both temporary resources were removed on rollback. Recovery Dex was subsequently
scaled down; the final Pod inventory contained no recovery Pod. Namespace and
restored objects have **not** been confirmed deleted. Private exports remain.
This proves a running Dex logical recovery rehearsal, not whole-cluster etcd
recovery, restoration of PVs, or seamless continuity of all sessions across rotation.

## After-action review

What helped: retained off-node backups, isolated restore namespace, public-key
comparison without private-key disclosure, and a same-token before/after test.
What delayed diagnosis: repeated console parse errors instead of HTTP/authenticator
errors, browser cookie capture difficulties, shell quoting pitfalls, unavailable
crictl, and logs not collected centrally for these components.

A full bearer token was inadvertently shared during diagnosis. It is deliberately
excluded from this record. Logout or closing a browser must not be described as
revoking an already issued JWT; no token-revocation outcome is claimed.

| Follow-up | Owner | Acceptance criterion | Status |
| --- | --- | --- | --- |
| Expand identity logging | Mike / Codex | Scoped sources searchable with timestamps; ingestion and sensitive-data handling verified | [Plan](../runbooks/identity-logging-plan.md), not deployed |
| Investigate initial BasicAuth prompts | Mike / Codex | Fresh login succeeds without repeated challenges; failing path/status/realm captured safely if reproduced | Open; subsequent navigation stable |
| Explain verifier state after issuer switch | Mike / Codex | Reproducible isolated evidence or upstream explanation; avoid another live issuer switch solely to reproduce | Open hypothesis |
| Finish rehearsal cleanup | Mike | Confirm zero replicas, temporary routes absent, then inventory/review namespace deletion; retained private exports verified | Pod stopped; namespace deletion pending |
| Establish backup cadence | Mike | Destination, retention, schedule/owner and restore checks accepted and first run recorded | Proposal below; not automated |

Proposed cadence: daily private Dex configuration/storage capture, weekly verified
off-node etcd and control-plane backups, and fresh backups before/after identity
or control-plane changes. Retain seven daily Dex sets and four weekly recovery
sets plus the last known-good pre-change set until replacement recovery is tested.
Review a restore quarterly and after major identity changes. These are proposals,
not guarantees or configured jobs. Confirm storage capacity, confidentiality,
availability when the laptop is offline, and an acceptable recovery point first.
A signing-key backup alone cannot preserve sessions created after that backup.
