# ForgeOps incident reasoning review — October 2, 2026

## Decision and baseline

The deterministic pipeline preserves its no-causation and no-remediation
boundary, but structurally valid evidence can still give an operator a
misleading impression. The highest priority is retaining the difference
between an unchanged incident, newly available evidence, and recovery. Adding
a model would not restore evidence discarded before briefing.

Reviewed main: `2ae9f5ebfceb703a7b9a688c6f9074e8b300b108`, after merged PR #168.
No `AGENTS.md` exists in the tracked repository. The current package is 1.0.0;
this review does not prepare or publish another release. All five runs on that
main commit completed successfully: [Required Validation](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/37062082416),
[Repository Security Validation](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/37062082443),
[ForgeOps CI](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/37062082518),
[CodeQL / Push on main](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/37062081853),
and [Dependabot graph update](https://github.com/wmstipes/The-Foundry-Initiative/actions/runs/37062088667).
Historical failed update runs are not current-main failures.

This review uses repository source, existing synthetic fixtures, and offline
experiments. It neither collects live cluster data nor changes workloads.

## Ranked findings

| Rank | Evidence and misleading interpretation | Disposition |
| --- | --- | --- |
| 1 — high | `classify_incident_state` reads only deltas. Identical failing or unknown snapshots yield `STABLE` with no facts. One check recovering can yield `RECOVERED` while another remains failed or unknown. The brief drops the comparison's overall statuses. | Text now says **deltas only** beside the state and directs the reviewer to both source summaries. The JSON limitation remains open; preserving aggregates and distinguishing regained evidence requires a versioned contract. |
| 2 — high | Node `Ready=Unknown` and Metrics APIService `Available=Unknown` became `FAIL`. Missing/invalid values also became `FAIL`; JSON boolean `true` became `PASS` through string conversion. These outputs passed snapshot validation and drove the brief. | Fixed: only literal string `True` passes and `False` fails. Kubernetes `Unknown` remains `UNKNOWN` with `condition-unknown`; unsupported/missing values remain `UNKNOWN` with `unexpected-shape`. New non-passing transitions yield `INCOMPLETE`. |
| 3 — high | Pod normalization retains container readiness but omits the Pod `Ready` condition. A synthetic Pod with all containers ready and `Ready=False` still reports `PASS`. Deployment normalization drops `generation`/`observedGeneration`; `2`/`1` with matching counts also reports `PASS`. | Reproduced, open. A later collection-contract change must preserve these fields, reconcile disagreeing observations, and test missing/stale status. Current evidence supports container/count checks, not complete rollout or Pod readiness. |
| 4 — medium | The catalog selected `http.restaurant-api.` while the collector emits IDs such as `http.restaurant-api/ready`. Every actual Restaurant HTTP failure remained unmapped despite an existing endpoint runbook. | Fixed with four exact selectors for `/health`, `/ready`, `/status`, `/version`. The dot-only prefix grammar and strict catalog loader stay unchanged. Lookalikes, unreviewed paths, and other applications remain unmapped. |
| 5 — medium | Kubernetes EndpointSlice counts and an application HTTP result do not identify an Istio failure. The fixed collector has no mesh objects, proxy flags/config, request-path identity, or matching telemetry window. HTTP is optional, so omitted probes produce no unknown check. | Explicit demonstration boundary. Do not translate routing counts into end-to-end reachability or an Istio cause. Admit a separate evidence profile only for a named operator question and independent negative cases. |
| 6 — medium | A non-JSON HTTP 503 is reduced to malformed-body `UNKNOWN`, losing the observed HTTP status. Snapshot time is a common collection timestamp; comparisons ignore check timestamps. Mapping linkage checks time windows, IDs and statuses, not catalog authenticity or snapshot byte identity. | Open contract work. Preserve response outcome separately from body validity, collection timing and trusted artifact/catalog linkage where the demonstration needs them. Existing validators and hashes do not authenticate supplied facts. |

Source anchors: [collector](../../src/forgeops/collect.py),
[evaluator](../../src/forgeops/evaluate.py),
[comparison](../../src/forgeops/comparison.py),
[brief model and parser](../../src/forgeops/incident.py),
[catalog](../reference/forgeops-runbook-catalog.json), and
[existing adversarial cases](../../tests/fixtures/forgeops/incident-adversarial-evaluation.json).

Ranks express review priority, not a computed operational severity. Finding 1
is mitigated in text, not solved by the patch. Finding 3 is a reproduced
collector limitation, not a claim that these conditions exist in SignalForge.

## Realistic scenario matrix

| Scenario | Supported conclusion | What remains unresolved | Verification |
| --- | --- | --- | --- |
| Node stops reporting; Ready changes from `True` to `Unknown` | Readiness evidence is unknown; brief is `INCOMPLETE` | Node failure, network loss, and control-plane observation failure are not distinguished | Automated collection-to-brief regression |
| Metrics APIService returns `Available=Unknown` | Availability is unknown, not an established service failure | Backend, API aggregation, transport, or collection cause | Automated regression, including malformed values |
| Restaurant readiness returns JSON 503 while EndpointSlices still match | Explicit HTTP result failed and the endpoint runbook matches | Application dependency, proxy, policy, and path failures require other evidence; endpoint counts do not select a cause | Automated regression for every collected path |
| Restaurant HTTP request times out or receives a non-JSON 503 | Evidence is incomplete; endpoint reference remains visible | Current contract cannot retain both malformed-body uncertainty and the observed status | Automated regression; response-outcome preservation remains open |
| Same failure persists across both snapshots | No recorded delta; state is `STABLE` | Health has not recovered; review snapshot summary | Automated regression with heading warning |
| HTTP readiness recovers while Metrics APIService remains failed/unknown | Only the changed HTTP check returned to `PASS` | Whole-snapshot recovery is unproven | Automated regression with heading warning |
| HTTP probes omitted and no mesh resources collected | No conclusion about those paths | Application or mesh may be broken despite a `STABLE` brief | Automated coverage/abstention regression |
| Pod containers ready but a readiness gate keeps Pod `Ready=False` | Container observations alone are insufficient | Pod readiness is misreported by the current collector/evaluator | Offline fixture mutation reproduced `PASS`; open |
| Deployment status reflects generation 1 while spec is generation 2 | Matching counts do not prove controller convergence | New rollout acceptance is unproven | Offline fixture mutation reproduced `PASS`; open |
| Kubernetes endpoints ready but an Istio client gets 503 `UF`, `NR`, or `UO` | Preserve the client symptom and the separate endpoint observation | Transport/mTLS, route selection, circuit breaking, and control/data-plane divergence need discriminating evidence | Design scenario only; no fixture claims mesh collection exists |

Istio's [traffic troubleshooting guide](https://istio.io/latest/docs/ops/common-problems/network-issues/)
distinguishes absent routes (`NR`), upstream overflow (`UO`), and connection
failures (`UF`), and describes eventual configuration propagation. Those are
useful next observations, not a license to diagnose mTLS from a 503 alone.
Kubernetes' [Node status reference](https://kubernetes.io/docs/reference/node/node-status/)
distinguishes `Ready=False` from `Ready=Unknown`. The patch preserves that
uncertainty instead of turning lack of readiness evidence into a factual
failure assertion.

## Smallest justified patch and compatibility

The patch serves two existing goals: improve the operator demonstration and
prove trustworthiness. It adds no milestone, model, retrieval service,
dependency, collection permission, network endpoint, or mutation capability.

- Preserve tri-state Node and APIService conditions through evaluation.
- Repair the existing Restaurant endpoint mapping with exact collected IDs.
- Qualify the text state at its point of display and update the operator guide.
- Add six semantic test functions using synthetic collection and strict
  snapshot → comparison → mapping → brief round trips.

Existing JSON schemas, field order, fixed limitation text, classification
rules, and golden brief JSON remain unchanged. Old valid JSON briefs still
load and replay. Text output changes intentionally. Newly collected unknown or
malformed conditions now produce snapshot exit 2 rather than a false exit 0/1;
runbook mapping for actual Restaurant HTTP failures now completes. Operators
must still read comparison and snapshot summaries for aggregate status.

The focused tests failed against the reviewed baseline before the fixes (31
subcase failures) and passed after the fixes. Failures included a real ID
mismatch and boolean readiness being incorrectly treated as passing evidence.
Run the semantic suite with:

~~~text
PYTHONPATH=src python -m unittest tests.test_forgeops_incident_semantics -v
~~~

Local validation passed all 190 ForgeOps unittest cases and all 276 top-level
unittest cases. The latter includes the former. Full repository pytest was
not run locally because this runtime has no pytest installation; hosted
Required Validation must confirm the 292-case complete discovery and its
other required checks. Synthetic passing tests do not establish live health,
complete diagnosis, or readiness for a new release.

## Next admission gate

Before expanding capabilities, define an explicit brief version that preserves
aggregate status and enough coverage to distinguish unchanged failure,
partial recovery, unknown-to-known evidence, and omitted evidence. Acceptance
must include disagreement between Pod/container readiness, stale deployment
generation, simultaneous symptoms, non-JSON proxy errors, and missing mesh
evidence. Existing v1 artifacts need a documented compatibility path.

Only then consider a narrowly scoped Kubernetes/Istio evidence profile that
answers one demonstrated question. A valid stopping result is: the supplied
evidence cannot distinguish the competing explanations, with the missing
observation stated explicitly. No ranked causal hypothesis should be emitted
solely because a schema, golden replay, or CI gate passed.
