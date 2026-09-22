# C5 offline operator exercise

## Purpose and source

Use the accepted [C5 plan](../milestones/forgeops-console-c5-evidence-boundary-planning.md)
to decide whether Console observations need a portable evidence contract.
The starting laptop checkout is `da9acddb64a2535c55b011274669e388315d78cb`.
The four scenarios are synthetic and do not describe current SignalForge
health. No cluster connection, production Console launch, or fault injection
is part of this exercise.

The assistant's offline rehearsal validated and regenerated all four briefs
through existing commands, with exact replay matches. The operator may inspect
the checked-in expected text for the first discussion; reading it is not a
claim that the operator personally ran the CLI pipeline.

## First discussion: routing regression

From the laptop repository root:

```powershell
Get-Content .\tests\fixtures\forgeops\scenarios\routing-regression\expected-incident-brief.txt
```

The result reports DEGRADED, a routing check changing PASS to FAIL, and an
informational Service-endpoint runbook reference. Its uncertainty explicitly
states that cause is not established and the evidence is point-in-time only.
The underlying after fixture contains two ready and one not-ready endpoint
against an expectation of three ready. This is not evidence that a selector
was broken or that all endpoints disappeared. A runbook title is not a diagnosis.

Ask the operator: What would you want to inspect next? Does the brief make
that choice clear? Would viewing that information in Console be sufficient,
or is there a concrete need to save/share it with another consumer?

## Remaining cases

Read each scenario's `expected-incident-brief.txt` in the same fixture directory
structure, or repeat the full offline sequence from the
[demonstration guide](forgeops-incident-copilot-demonstration.md#track-a--rehearse-a-synthetic-incident-offline)
with the scenario path changed. Keep generated files outside the repository.

| Scenario | Discussion prompt | Operator response |
| --- | --- | --- |
| routing-regression | What observation would help investigate the changed routing check? Is viewing enough, or does it need a consumer outside Console? | Operator would inspect Pod Events/logs first, then Service/EndpointSlice details; wants save/share support for help, incident records, and future ForgeOps use. |
| incomplete-evidence | Can you distinguish unavailable Metrics API evidence from a proved workload failure? Current Console views do not fill this gap. | Operator would inspect logs, configuration YAML, network connections and ports; other resources might help. The synthetic Metrics API check timed out, so UNKNOWN is incomplete evidence, not a proved workload failure. Console has selected-Pod logs/Events and bounded Service/EndpointSlice projections, but no raw configuration YAML, connection tests or Metrics APIService view. |
| routing-recovery | What does RECOVERED tell you, and what remains unknown about cause and durability? | Operator would confirm data flow, review affected Pod logs, check reachability to previously unreachable data sources, and possibly trace the network route. Console can show selected-Pod logs but does not run connectivity or traceroute tests. One point-in-time PASS does not prove durable recovery. |
| stable-baseline | Is STABLE useful even without a new incident? What question remains unanswered, if any? | Operator wants exact version, release date and a verifiable hash for both the running application and the evidence-producing ForgeOps build, labeled separately. The current brief does not carry all of those identities. Missing values must be explicit; a digest does not prove a live workload is healthy or authenticate its publisher. |

For each response record the baseline answer and steps, Console contribution
and steps, remaining uncertainty, and disclosure concerns. Do not infer
feedback or improved investigation speed from the successful replays.
The three later answers were given in conversation on 2026-09-22 after reading
brief summaries. They are requirements feedback, not observed Console use or
timed execution of these scenarios by the operator.

## Console-assisted illustration

If visual inspection would help the discussion, use the existing synthetic
demo documented in the [Console README](../../apps/forgeops-console/README.md).
With browser assets already built, the laptop command is:

```powershell
cd C:\Users\wmsti\The-Foundry-Initiative\apps\forgeops-console
& 'C:\Program Files\Go\bin\go.exe' run ./cmd/forgeops-console-demo --web-dir ./web/dist --listen 127.0.0.1:9090
```

Open `http://127.0.0.1:9090`, verify the synthetic banner, activate
`synthetic-demo`, and select namespace `signalforge`. Inspect a Pod's readiness,
ownership, and diagnostics, then Service and EndpointSlice details. Record
which views clarify an investigation question. Stop with Ctrl+C afterward.

The default demo has different identities and counts from the ForgeOps corpus.
It illustrates available UI operations only; it cannot corroborate the brief
or measure accuracy against that scenario. Do not execute preview commands.

## Aligned synthetic routing illustration

The later source demo can show two explicitly selected synthetic states for
the routing-regression fixture. This is a separate exercise from the original
default demo above, which still has different identities and counts. Build the
browser from this checkout first (`npm ci` and `npm run build` in
`apps/forgeops-console/web`). Then, in PowerShell from
`apps/forgeops-console`, start the first stage:

```powershell
& 'C:\Program Files\Go\bin\go.exe' run ./cmd/forgeops-console-demo --web-dir ./web/dist --listen 127.0.0.1:9090 --scenario routing-before
```

Open `http://127.0.0.1:9090`, verify the synthetic banner, activate
`synthetic-routing-before`, and select `forge-restaurant`. Inspect the
`synthetic-service` Service and `synthetic-service-demo` EndpointSlice. The
projected slice should say `3/3 ready`. Stop with Ctrl+C. Start the same
command with `--scenario routing-after`, activate
`synthetic-routing-after`, and select `forge-restaurant`. The same Service and
slice should now say `2/3 ready`. You can inspect the three selected Pods,
generic synthetic logs and Events, but the data deliberately does not encode
a cause. Stop with Ctrl+C when finished.

The matching namespace, Service name and endpoint counts allow a bounded
side-by-side discussion with the fixture's `PASS → FAIL` routing check. The
Console contexts differ from the fixture's `kubernetes-admin@kubernetes` on
purpose: these are independently constructed fake-client objects, not captured
Kubernetes evidence, the source of the ForgeOps fixture, or a validation of
the brief. No before/after comparison, elapsed-time benefit or operator
acceptance is established by an automated test. Record the operator's actual
steps and whether the UI clarified a question before claiming workflow value.

The requested version, release date and verifiable hash for both products are
separately scoped in the [release-identity source contract](../design/forgeops-brief-release-identity-sources.md).
The synthetic image names are not release identities.

## Decision worksheet

- Operator questions: investigate a degraded routing check; distinguish missing
  Metrics API evidence from workload failure; verify recovery; identify the
  releases behind a stable baseline. Recurrence and measured workflow benefit
  have not been demonstrated.
- Baseline answer: the CLI identifies the changed check, state, uncertainty,
  and runbook reference. It does not establish cause.
- Desired Console contribution: inspect Pod Events/logs first, then routing
  details. This is the operator's chosen sequence, not an observed timed run.
- Additional needs: configuration and port inspection, connectivity checks,
  and separately labeled application and ForgeOps release identities. These are
  operator requests, not implemented Console capabilities or validated
  evidence fields. Define the exact artifact, source, release date semantics,
  digest algorithm and unavailable state before adding identity to a brief.
- Requested consumers: a human helper, later incident review, and future
  ForgeOps comparison/briefing. Only the first two have a defined human
  consumption path today; machine intake remains unsupported.
- Disclosure concern: useful diagnostic text may contain sensitive data.
  The operator liked the proposed split between structured facts and optional
  human-only reviewed excerpts. No live excerpts were collected for C5.
- Design: [bounded observation contract](../design/forgeops-console-observation-contract.md).
- Decision: admit the design for a reviewed human handoff; defer exporter
  implementation and automatic ForgeOps integration until contract review,
  implementation acceptance, and an aligned end-to-end exercise.
- Evidence limit: no comparative click counts, elapsed times, or aligned
  Console fixture run were obtained. Answers for all four scenarios are now
  recorded; only the first was discussed when the C5 design was accepted.

This records the requirements discussion for the design candidate, not proof
that an integrated product improves investigation. The unperformed aligned
exercise and acceptance checks remain prerequisites for any export
implementation. Live access,
ForgeFire, and the proposed Istio learning milestone remain separate.
