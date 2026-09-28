# Documentation and operations review — 2026-09-28

**Baseline:** `554f432ac5aeca881f6b536f95037cff4918ea9a`, merged PR #158.

## Scope and evidence

Reviewed the inventory of 138 tracked Markdown files, including 75 milestone
records, for links, historical/current-state boundaries, navigation, and
missing operational records. Current architecture, status, component READMEs,
process, testing, and recent platform records received a detailed consistency
pass against tracked manifests and the operator's reported deployments.
The live Wiki was cloned from its separate repository; both pages differed
from reviewed repository source at the start of this review.

This work changes documentation only. It does not perform new cluster probes,
disaster recovery, secret rotation, network isolation testing, or deployment.
The existing live acceptance and its limits remain attributed to their dated
records. External upstream references were checked where new operating
guidance depends on them; this is not a claim that every historical web URL
was revalidated.

## Findings and corrections

| Finding | Correction |
| --- | --- |
| Live Wiki still had older Console navigation | Reconcile Home and sidebar; add stable portal, Headlamp, Pulse, Istio, process and security navigation |
| No consolidated current operating entry point | Add documentation map, operations index, and identity operating notes |
| No dedicated record for the completed private access / OIDC work | Add a named acceptance record with observed results and explicit remaining work |
| Route failure guidance could lead to workload deletion | Add a protected-route runbook with credential prerequisites, anonymous HTTPS checks, and Ingress-only closure |
| PKI, Prometheus, Grafana and Pulse text described superseded access | Update current access and preserve dated pre-ingress observations |
| Completed Loki recovery still appeared as future work | Link the accepted backup/restart/restore record; retain the unverified retention limitation |
| Test totals omitted Loki and Pulse tests | Reconcile 259 top-level, 9 Restaurant, 7 Pulse, 275 total Python cases; focused ForgeOps 184; Go source functions 63 |
| Broken Console exercise link | Fix relative path to the existing guide |
| C3 scheduling-label fix still described as pending | Link the accepted C7 result and date the earlier C4 boundary |
| Architecture implied HTTPS between gateway and app backends | State TLS termination and current HTTP backend hops; show inspection, identity and logging flows |
| Manual API-server OIDC change could be lost on kubeadm upgrade | Record configuration/patch reconciliation as an open upgrade prerequisite |
| Legacy text encoding and obsolete preview ambiguity | Repair malformed punctuation and identify the local portal as a separate preview |

No numbered milestone was fabricated for the missing 031 record. Planned
ForgeOps 066-088 and Workbench W1-W7 remain future work. Historical releases,
test totals, image identities and original acceptance dates were preserved.

## Validation and publication

Validation of the reviewed tree passed:

- All 145 Markdown files were scanned for repository-local and current-main
  link paths and heading fragments: no missing targets or unmatched anchors.
- `python scripts/validate-wiki-front-door.py --wiki-dir ../forge-wiki-review`
  passed, including exact source-copy verification of both published pages.
- `python -m unittest tests.test_wiki_front_door tests.test_forgeops_console_design -q`
  passed all 15 existing tests.
- `python scripts/validate-k8s-manifests.py` and `git diff --check` passed.

The live Wiki Home and sidebar were synchronized through the browser editor
from the reviewed source and visually checked. A fresh pull of the separate
Wiki repository verified commit
`1bd59a652852d1890127904d0f0ea2c404bc7c6b` and the exact page contents.
All navigation destinations already existed on `main` when published.

Current test counts were reconciled using the successful
[PR #158 required workflow](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/36468840565)
and local suite discovery, without adding tests for these documentation edits.
The documentation PR's Actions results provide its independent CI status;
the inventory above is not a claim that the full runtime suite ran locally.

## Open operational follow-ups

- Preserve OIDC configuration through kubeadm upgrades and demonstrate
  identity-state/private-config recovery.
- Observe fresh login and session behavior after controlled restarts; the
  earlier ServiceAccount token path has not been retested since OIDC.
- Verify naturally elapsed Loki retention; maintain manual backup freshness.
- Complete NUC trust/name resolution if that device is to access the portal.
- Continue monitoring gateway/intermediate/root certificate lifetimes.

These are documented follow-ups, not successful tests performed by this review.
