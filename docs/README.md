# Documentation map

Use current guidance for operation and dated records for the evidence behind
it. A historical successful check does not establish today's cluster health.

| Need | Authoritative entry point |
| --- | --- |
| What is deployed and what remains open | [Project status](project-status.md) |
| Components, identities, traffic, and availability limits | [Architecture](architecture.md) |
| Service access, routine checks, upgrades, and recovery | [Operations index](runbooks/README.md) |
| Kubernetes manifests and component runbooks | [Kubernetes index](../k8s/README.md) |
| Operational incidents, after-action reviews and follow-ups | [Incident management](incidents/README.md) |
| Reasoning, acceptance, and historical results | [Milestone records](milestones/README.md) |
| Direction and planned work | [Roadmap](../ROADMAP.md) |
| Test counts and what each check establishes | [Testing and validation](testing-and-validation.md) |
| How changes and documentation are maintained | [Contributing](../CONTRIBUTING.md) |
| Security reporting and repository controls | [Security policy](../SECURITY.md), [October review and settings checklist](security/review-2026-10-01.md) |

## Learning and product guides

- [TokenReview and signature verification: why, when, how and results](guides/tokenreview-and-signature-verification.md)

- [ForgeOps operator learning guide](guides/forgeops-operator-learning-guide.md)
- [Incident-copilot demonstration](guides/forgeops-incident-copilot-demonstration.md)
- [Console operator exercise](guides/forgeops-console-c5-operator-exercise.md)
- [Istio learning lab](../k8s/istio-lab/README.md)
- [ForgeOps release procedure](guides/forgeops-release.md)
- [Console Windows preview](releases/forgeops-console-v0.1.0-rc.1.md)
- [Git patch reference](reference/git-patch-files.md)

## Maintaining the record

The root README is an overview, the roadmap owns direction, and the status
page owns the current deployment summary. Component READMEs and runbooks own
repeatable operating instructions. Milestones and the learning journal retain
dated observations, including superseded configurations and past test counts.
When one could be mistaken for a current instruction, add a subsequent-outcome
note and link to the current runbook.

The [Wiki source](wiki/Home.md) is a navigation layer copied to a separate Git
repository. Its live files must match the reviewed source. It does not own
commands, release state, or independent operational evidence.

Private identity configuration, credentials, kubeconfigs, certificates and
recovery exports have a separate storage boundary. Public documentation can
describe their purpose and ownership without making a fresh deployment
possible from Git alone. See [identity operations](runbooks/headlamp-oidc.md).
