# Incident management and after-action records

Use this directory for real operational incidents. Keep reusable commands in
[runbooks](../runbooks/README.md), dated evidence here, and actionable follow-ups
in GitHub Issues. This is a lightweight operator workflow, not a new application
or a change to ForgeOps' automated reasoning authority.

## Workflow

1. Open an **Operational incident** issue with impact, start time/timezone,
   owner, and current state. Use private security reporting for vulnerabilities
   or sensitive disclosures; a public issue is not a private evidence vault.
2. Track states: **Investigating → Mitigated → Monitoring → Resolved**.
   Record timestamped observations, hypotheses, commands and their effects.
   Severity is based on observed impact: SEV1 = cluster management unavailable
   or data integrity at risk; SEV2 = an important service/access path unusable;
   SEV3 = degraded behavior with a usable workaround. Reassess as evidence changes.
3. Preserve bounded evidence before disruptive changes. Keep raw logs, tokens,
   cookies, Secrets, kubeconfigs and recovery exports outside Git. Record only
   sanitized results and private evidence references, not credential contents.
4. Verify recovery at both infrastructure and user levels. Readiness alone is
   insufficient. Record side effects, fallback access, and remaining uncertainty.
5. Copy [TEMPLATE.md](TEMPLATE.md) to `YYYY-MM-DD-short-description.md`; link the
   issue and fix PR when they exist. Do not invent ticket IDs or measured timings.
6. Add the record to this index, update the relevant runbook, and assign each
   follow-up an owner, acceptance criterion and status. Close the incident issue
   after service recovery is accepted; separate improvement issues may remain open.

## Records

| Date | Incident | Service state | Follow-up state |
| --- | --- | --- | --- |
| 2026-09-30 | [Headlamp OIDC rejection after Dex recovery rehearsal](2026-09-30-headlamp-oidc-signature-rejection.md) | Resolved; navigation and refresh accepted | Exact mechanism, initial BasicAuth prompts, logging scope and backup cadence open |

A resolved incident does not establish future availability or prove a root cause.
These records are not automatically added to the ForgeOps runbook catalog or
used as automated remediation instructions.
