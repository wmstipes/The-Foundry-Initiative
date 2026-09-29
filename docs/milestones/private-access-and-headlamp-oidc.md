# Private service access and Headlamp OIDC acceptance

**Observation window:** 2026-09-27 through 2026-09-28

**Result:** Protected service access and interactive Headlamp OIDC login
accepted by the operator. These are user-supplied terminal and browser
observations; this record does not claim an independent remote cluster audit.

## Purpose and decisions

Complete the portal's service access and replace routine manual Headlamp
token creation with a local Forge account. Private HTTPS terminates at the
existing gateway. Headlamp and Service Pulse have distinct BasicAuth gates
and ingress policies; their Services remain ClusterIP. The Pulse probe
remains internal. Dex supplies OIDC to Headlamp, while the other applications
retain their existing authentication.

The Dex configuration, client credentials, Headlamp OIDC overlay, public CA
mount input, and API-server backup/candidate files are held outside Git.
The OIDC user's RBAC is separate from the Headlamp ServiceAccount. Both were
checked for the intended read-only access. The chart's binding name
`headlamp-admin` does not mean it grants `cluster-admin`; its role is `view`.

## Observed acceptance

| Step | Evidence supplied | Limit |
| --- | --- | --- |
| Gateway and CA | Gateway Certificate Ready, wildcard coverage; public root trusted on laptop | NUC trust setup deferred; no gateway HA claim |
| Headlamp route | Workload and endpoints ready; route/policy server dry-run and apply succeeded; anonymous HTTPS returned `401` | Does not independently test all NetworkPolicy bypass paths |
| Pulse route | Both workloads ready; anonymous `/api/status` returned `401`; operator reported board working | Probe sample history remains in memory |
| Portal | Two new portal replicas running; operator confirmed both cards active | Portal availability still depends on gateway and cluster |
| Dex | Chart `0.24.1` deployed; one Pod became Ready and stayed running after an initial restart; trusted HTTPS discovery matched the expected issuer | No long-term availability or restore test |
| Name resolution and trust | Windows and control-plane host resolution established; control-plane curl passed without disabling TLS verification; Headlamp received public CA via Secret | Host mapping and trust are private deployment inputs |
| API-server preparation | No earlier OIDC/authentication-config flags; original manifest and three copies had identical SHA-256 | A manifest backup is not an etcd/identity-state backup |
| API-server activation | Candidate added exactly five OIDC flags and one Pod host alias; staged candidate/restore hashes matched; `/readyz` returned `ok`; new API Pod was `1/1` Running | Single API restart briefly interrupted clients; Tigera recovered afterward |
| OIDC RBAC | Impersonation allowed Node and Pod lists and denied Secret reads and Deployment creation | Impersonation tests authorization for a supplied identity, not token authentication |
| Headlamp login | Chart `0.45.0` revision 2 deployed, rollout succeeded; operator confirmed authentication and access working | Token-level negative authorization and full cold-start recovery were not separately exercised |

The accepted API-server backup SHA-256 was
`39a9140a8554e000b1f8c0882f7fee71620f7d47dd2653947a8d929f41df18e7`.
The accepted candidate SHA-256 was
`b74502957d83a7d3f67f51b1e351d4c000e8922a2ded34bf957b87d3821a34d2`.
Verified recovery copies were retained; no failed-start rollback was required.

## Repository reconciliation

[PR #156](https://github.com/wmstipes/The-Foundry-Initiative/pull/156) supplied
the protected route and policy groundwork. [PR #157](https://github.com/wmstipes/The-Foundry-Initiative/pull/157)
activated the two portal cards. [PR #158](https://github.com/wmstipes/The-Foundry-Initiative/pull/158)
updated the documentation and architecture after OIDC acceptance; it merged at
`554f432ac5aeca881f6b536f95037cff4918ea9a` with successful required validation.
The private Dex manifests and overlay were not published by that PR.

## Subsequent outcome — September 29

[Preservation and recovery work](identity-preservation-recovery-2026-09-29.md)
recorded the OIDC flags in kubeadm configuration, installed the explicit
host-alias patch, and verified regeneration without changing the live manifest.
Off-node etcd and host-file copies passed hash checks; offline etcd restoration
passed. Full running identity recovery remains untested. The remaining-work
list below records the September 28 handoff rather than current completion.

## Remaining work at September 28

- Preserve the manual API-server flags and host alias through the supported
  kubeadm configuration/patch workflow before any control-plane upgrade.
- Establish and rehearse identity-state recovery, private-config recovery,
  restart behavior, and client-secret rotation. No such acceptance is implied.
- Observe ordinary session renewal/expiry behavior; decide separately whether
  the additional Headlamp BasicAuth prompt should remain.
- Complete the NUC public-root and hostname setup when that client is needed.
- Maintain certificate expiry checks and the existing component backup cadence.

See [identity operations](../runbooks/headlamp-oidc.md) for current recovery
boundaries and [the operations index](../runbooks/README.md) for all services.
