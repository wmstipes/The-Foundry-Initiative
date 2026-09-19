# ForgeOps synthetic scenario corpus

These fixtures are deterministic, disclosure-minimized examples for exercising the
existing ForgeOps offline evidence-validation and comparison interfaces. They are
synthetic evaluation data, not captured SignalForge evidence, current-health claims,
training data, provenance records, or operational recommendations.

Each scenario contains one deliberately isolated check so the expected transition is
unambiguous:

| Scenario | Transition | Expected comparison exit |
| --- | --- | ---: |
| `stable-baseline` | `PASS` to `PASS`, timestamp only | `0` |
| `pod-restart-warning` | `PASS` to `WARN` | `1` |
| `routing-regression` | `PASS` to `FAIL` | `1` |
| `incomplete-evidence` | `PASS` to `UNKNOWN` | `1` |
| `routing-recovery` | `FAIL` to `PASS` | `1` |

The artifacts intentionally contain only the check needed for the named scenario.
Their contained overall status describes that focused artifact only; it is not a
complete statement of cluster health. All identifiers and observations are synthetic.
No file contains a real address, kubeconfig path, credential, UID, captured response,
or complete Kubernetes object.

Each directory contains:

- `before.json`: a valid `forgeops.snapshot/v1alpha1` artifact;
- `after.json`: a later valid artifact; and
- `expected-comparison.json`: the exact deterministic
  `forgeops.comparison/v1alpha1` output; and
- `expected-incident-brief.json`: the exact deterministic
  `forgeops.incident-brief/v1alpha1` output after canonical runbook mapping; and
- `expected-incident-brief.txt`: the exact deterministic operator-facing view
  of that same brief model.

Use the existing offline interfaces to inspect a scenario:

~~~powershell
forgeops evidence validate --input .\before.json
forgeops evidence validate --input .\after.json
forgeops evidence compare --before .\before.json --after .\after.json
forgeops evidence compare --before .\before.json --after .\after.json --format json
forgeops scenario replay `
  --before .\before.json `
  --after .\after.json `
  --expected .\expected-comparison.json
~~~

Incident replay additionally requires an explicitly rendered mapping for the
same comparison and never discovers one from the directory:

~~~powershell
forgeops incident replay `
  --comparison .\expected-comparison.json `
  --mapping .\mapping.json `
  --expected .\expected-incident-brief.json
~~~

An exit code of `1` from a valid comparison means the artifacts differ. It does not
mean that a recovery failed. ForgeOps does not collect, diagnose, recommend, retain,
or mutate anything while validating, comparing, or replaying these files. Replay
exit `0` means the deterministic actual comparison exactly matched the validated
expectation; it is independent of the expected comparison's contained exit.
Incident replay has the same separation: replay exit `0` means an exact brief
match, not that the contained incident state is healthy.
