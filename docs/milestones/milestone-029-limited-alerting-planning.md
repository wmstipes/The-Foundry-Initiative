# Milestone 029 Limited Alerting Planning

Started: 2026-09-10

Status: Complete. Design accepted and merged on 2026-09-10.

## Goal

Design a deliberately small scrape-coverage alert set from the Milestone 028 baseline without changing the cluster or deploying alerting.

## Baseline and scope

The operator confirmed clean `main` at `8011740`, synchronized with `origin/main`, then created `codex/milestone-029-limited-alerting-planning`. The supplied Git archive identifies full baseline commit `801174052d7eef801920870946f75dfa978768cd`.

The [limited-alerting specification](../observability/limited-alerting-specification.md) proposes two mutually exclusive service-level conditions: reduced healthy scrape coverage for five minutes and no healthy scrape targets for two minutes. Both delays remain provisional. It defines missing-data semantics, response guidance, coverage gaps, deferred signals, and a future offline validation matrix.

## Documentation reconciliation

- Align the older error-percentage query with the accepted dashboard expression so low rates are not biased by a denominator floor and idle intervals remain unobserved rather than successful.
- Correct the dashboard specification's stale validation status while preserving its historical design baseline and acceptance requirements.
- Record planning in progress in the roadmap and project status. Milestones 001-028 remain the completed set.

## Validation and limitations

This is a documentation-only proposal. No executable alert rules, manifests, dashboards, application code, scripts, tests, or dependencies are changed. No cluster access, reload, deployment, traffic generation, or failure injection is part of this work. Draft alert expressions require future pinned-promtool tests; no runtime result or observed alert timing is claimed.

The archive permits source review but is not current live-cluster evidence. The prior Milestone 028 record supplies the accepted runtime baseline. On 2026-09-10, Mike explicitly accepted the planning design, including the provisional delays, manual three-target baseline, monitoring blind spots, and future validation requirements. This acceptance does not authorize implementation or activation.

The operator applied the documentation patch successfully and reported a clean staged whitespace check with six Markdown files changed (195 insertions, 14 deletions before this acceptance update). Local checks also verified patch application against the supplied archive, relative links, and equivalence of the revised error-percentage expression to the existing dashboard source. No promtool execution is claimed.

Completion evidence: commit `037d7c1` was merged through [PR #4](https://github.com/wmstipes/The-Foundry-Initiative/pull/4) at `1837868`. The operator confirmed clean, synchronized `main`; GitHub independently confirms the merged PR. Planning completion does not claim promtool execution or alert activation.

Next: [Milestone 030](milestone-030-limited-alerting-implementation.md) begins with offline rule preparation and validation. Live wiring and activation remain behind a separate review/approval gate; notification design remains deferred.

## Acceptance checklist

- [x] Inspect supplied observability configuration, dashboard specification, implementation evidence, and roadmap.
- [x] Draft bounded conditions, limitations, response guidance, and future offline test cases.
- [x] Keep changes confined to Markdown documentation.
- [x] Operator accepts the scope, provisional delays, blind spots, and validation contract.
- [x] Documentation patch is applied, reviewed, and version controlled on the intended branch.
- [x] Record planning acceptance and a separately scoped next step; do not silently activate rules.
