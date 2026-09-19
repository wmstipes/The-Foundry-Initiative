# ForgeOps deterministic incident-copilot demonstration

This guide demonstrates the current ForgeOps evidence-to-brief path without
adding a new command, a model, broader collection, or remediation authority.
It deliberately separates two kinds of evidence:

- a **synthetic incident track** proves deterministic degraded-state behavior
  against reviewed fixtures and exact expectations; and
- a **live read-only track** proves bounded collection against SignalForge
  without injecting a failure or claiming that a point-in-time observation is
  complete cluster health.

Run both tracks from a clean checkout at the reviewed commit. Generated
artifacts belong in an operator-controlled temporary directory and must not be
committed. Review every artifact before retaining or sharing it.

## Governing boundaries

- Run `provenance` before relying on any output.
- Use only the repository-owned source launcher or a separately verified
  isolated non-editable installation.
- Supply one explicit kubeconfig, the exact accepted context, and explicit
  application URLs for live collection.
- Treat exit codes according to their command domain. In particular,
  comparison exit `1` means valid evidence differs, and mapping exit `1` means
  valid deltas remain unmapped.
- Do not inject an outage, restart a workload, change configuration, broaden
  RBAC, discover other endpoints, or execute a referenced runbook merely to
  make the demonstration more dramatic.
- Treat a live `STABLE` brief as a truthful successful result when no natural
  change occurs.
- Keep model and retrieval integration deferred unless the completed
  demonstration identifies a concrete operator question that the deterministic
  brief cannot answer.

## Prepare the exact checkout

From the repository root in PowerShell:

~~~powershell
git status --short
git rev-parse HEAD
python .\scripts\run-forgeops-dev.py provenance
~~~

Stop if the checkout is dirty, the commit is not the reviewed milestone commit,
or provenance is not consistent. Provenance output includes local paths; review
it before sharing.

Create an untracked temporary workspace outside the repository:

~~~powershell
$demoRoot = Join-Path `
  ([System.IO.Path]::GetTempPath()) `
  ("forgeops-m062-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $demoRoot | Out-Null
$demoRoot

function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][object[]]$Lines
  )

  $text = if ($Lines.Count -eq 0) { "" } else {
    ($Lines -join "`n") + "`n"
  }
  [System.IO.File]::WriteAllText(
    $Path,
    $text,
    [System.Text.UTF8Encoding]::new($false)
  )
}
~~~

The helper avoids version-dependent PowerShell redirection encodings. ForgeOps
strictly loads UTF-8 JSON, so the demonstration writes captured native-command
output explicitly as UTF-8 without a byte-order mark.

## Track A — Rehearse a synthetic incident offline

The routing-regression scenario is reviewed synthetic evaluation data. It is
not captured SignalForge evidence and makes no current-health claim.

~~~powershell
$scenario = ".\tests\fixtures\forgeops\scenarios\routing-regression"
$catalog = ".\docs\reference\forgeops-runbook-catalog.json"

python .\scripts\run-forgeops-dev.py evidence validate `
  --input "$scenario\before.json"
if ($LASTEXITCODE -ne 0) { throw "Before evidence validation failed." }

python .\scripts\run-forgeops-dev.py evidence validate `
  --input "$scenario\after.json"
if ($LASTEXITCODE -ne 0) { throw "After evidence validation failed." }

python .\scripts\run-forgeops-dev.py runbook catalog validate `
  --input $catalog
if ($LASTEXITCODE -ne 0) { throw "Runbook catalog validation failed." }

$syntheticComparison = python .\scripts\run-forgeops-dev.py evidence compare `
  --before "$scenario\before.json" `
  --after "$scenario\after.json" `
  --format json
$syntheticComparisonExit = $LASTEXITCODE
if ($syntheticComparisonExit -notin 0, 1) {
  throw "Synthetic comparison failed validation."
}
Write-Utf8NoBom `
  -Path "$demoRoot\synthetic-comparison.json" `
  -Lines $syntheticComparison

$syntheticMapping = python .\scripts\run-forgeops-dev.py runbook map `
  --comparison "$demoRoot\synthetic-comparison.json" `
  --catalog $catalog `
  --format json
$syntheticMappingExit = $LASTEXITCODE
if ($syntheticMappingExit -notin 0, 1) {
  throw "Synthetic runbook mapping failed validation."
}
Write-Utf8NoBom `
  -Path "$demoRoot\synthetic-mapping.json" `
  -Lines $syntheticMapping

python .\scripts\run-forgeops-dev.py runbook mapping validate `
  --input "$demoRoot\synthetic-mapping.json"
if ($LASTEXITCODE -ne 0) { throw "Synthetic mapping validation failed." }

$syntheticBrief = python .\scripts\run-forgeops-dev.py incident brief `
  --comparison "$demoRoot\synthetic-comparison.json" `
  --mapping "$demoRoot\synthetic-mapping.json" `
  --format json
if ($LASTEXITCODE -ne 0) { throw "Synthetic JSON brief failed." }
Write-Utf8NoBom `
  -Path "$demoRoot\synthetic-brief.json" `
  -Lines $syntheticBrief

python .\scripts\run-forgeops-dev.py incident brief `
  --comparison "$demoRoot\synthetic-comparison.json" `
  --mapping "$demoRoot\synthetic-mapping.json" `
  --format text
if ($LASTEXITCODE -ne 0) { throw "Synthetic text brief failed." }

python .\scripts\run-forgeops-dev.py incident replay `
  --comparison "$demoRoot\synthetic-comparison.json" `
  --mapping "$demoRoot\synthetic-mapping.json" `
  --expected "$scenario\expected-incident-brief.json"
if ($LASTEXITCODE -ne 0) { throw "Synthetic incident replay did not match." }
~~~

The accepted routing-regression result is a valid comparison difference,
complete runbook mapping, `DEGRADED` deterministic brief, and exact replay
match. This proves expected implementation behavior, not a live incident.

## Track B — Demonstrate the live read-only path

This track requires a separate approval before execution. Confirm that
`KUBECONFIG` resolves to one intended regular file and that the current context
is exactly `kubernetes-admin@kubernetes`. Do not display or copy kubeconfig
contents into demonstration evidence.

~~~powershell
$kubeconfig = $env:KUBECONFIG
$context = "kubernetes-admin@kubernetes"
$restaurantUrl = "http://192.168.243.112:30080"
$workbenchUrl = "http://192.168.243.112:30081"

$kubeconfig
kubectl config current-context
~~~

Collect the first bounded snapshot:

~~~powershell
$liveBefore = python .\scripts\run-forgeops-dev.py snapshot `
  --kubeconfig $kubeconfig `
  --context $context `
  --restaurant-url $restaurantUrl `
  --workbench-url $workbenchUrl `
  --format json
$liveBeforeExit = $LASTEXITCODE
if ($liveBeforeExit -notin 0, 1) { throw "First live snapshot is incomplete." }
Write-Utf8NoBom -Path "$demoRoot\live-before.json" -Lines $liveBefore

python .\scripts\run-forgeops-dev.py evidence validate `
  --input "$demoRoot\live-before.json"
if ($LASTEXITCODE -ne 0) { throw "First live snapshot is invalid." }

$liveBeforeIntegrity = python .\scripts\run-forgeops-dev.py `
  evidence integrity create --input "$demoRoot\live-before.json"
if ($LASTEXITCODE -ne 0) { throw "First integrity record failed." }
Write-Utf8NoBom `
  -Path "$demoRoot\live-before.integrity.json" `
  -Lines $liveBeforeIntegrity
~~~

At a naturally chosen later point, collect the second snapshot without changing
the cluster to manufacture a delta:

~~~powershell
$liveAfter = python .\scripts\run-forgeops-dev.py snapshot `
  --kubeconfig $kubeconfig `
  --context $context `
  --restaurant-url $restaurantUrl `
  --workbench-url $workbenchUrl `
  --format json
$liveAfterExit = $LASTEXITCODE
if ($liveAfterExit -notin 0, 1) { throw "Second live snapshot is incomplete." }
Write-Utf8NoBom -Path "$demoRoot\live-after.json" -Lines $liveAfter

python .\scripts\run-forgeops-dev.py evidence validate `
  --input "$demoRoot\live-after.json"
if ($LASTEXITCODE -ne 0) { throw "Second live snapshot is invalid." }

$liveAfterIntegrity = python .\scripts\run-forgeops-dev.py `
  evidence integrity create --input "$demoRoot\live-after.json"
if ($LASTEXITCODE -ne 0) { throw "Second integrity record failed." }
Write-Utf8NoBom `
  -Path "$demoRoot\live-after.integrity.json" `
  -Lines $liveAfterIntegrity
~~~

Immediate verification proves only that the current bytes match the generated
records. It does not create independent trusted retention or authenticity:

~~~powershell
python .\scripts\run-forgeops-dev.py evidence integrity verify `
  --input "$demoRoot\live-before.json" `
  --record "$demoRoot\live-before.integrity.json"
if ($LASTEXITCODE -ne 0) { throw "First integrity verification failed." }

python .\scripts\run-forgeops-dev.py evidence integrity verify `
  --input "$demoRoot\live-after.json" `
  --record "$demoRoot\live-after.integrity.json"
if ($LASTEXITCODE -ne 0) { throw "Second integrity verification failed." }
~~~

Build the deterministic comparison, mapping, and brief:

~~~powershell
$liveComparison = python .\scripts\run-forgeops-dev.py evidence compare `
  --before "$demoRoot\live-before.json" `
  --after "$demoRoot\live-after.json" `
  --format json
$liveComparisonExit = $LASTEXITCODE
if ($liveComparisonExit -notin 0, 1) { throw "Live comparison is invalid." }
Write-Utf8NoBom `
  -Path "$demoRoot\live-comparison.json" `
  -Lines $liveComparison

$liveMapping = python .\scripts\run-forgeops-dev.py runbook map `
  --comparison "$demoRoot\live-comparison.json" `
  --catalog $catalog `
  --format json
$liveMappingExit = $LASTEXITCODE
if ($liveMappingExit -notin 0, 1) { throw "Live mapping is invalid." }
Write-Utf8NoBom -Path "$demoRoot\live-mapping.json" -Lines $liveMapping

python .\scripts\run-forgeops-dev.py runbook mapping validate `
  --input "$demoRoot\live-mapping.json"
if ($LASTEXITCODE -ne 0) { throw "Live mapping validation failed." }

$liveBrief = python .\scripts\run-forgeops-dev.py incident brief `
  --comparison "$demoRoot\live-comparison.json" `
  --mapping "$demoRoot\live-mapping.json" `
  --format json
if ($LASTEXITCODE -ne 0) { throw "Live JSON brief failed." }
Write-Utf8NoBom -Path "$demoRoot\live-brief.json" -Lines $liveBrief

python .\scripts\run-forgeops-dev.py incident brief `
  --comparison "$demoRoot\live-comparison.json" `
  --mapping "$demoRoot\live-mapping.json" `
  --format text
if ($LASTEXITCODE -ne 0) { throw "Live text brief failed." }
~~~

## Acceptance questions

Record answers without overstating the evidence:

1. Did provenance identify the exact reviewed source?
2. Did both live snapshots validate, and what contained statuses did they
   report?
3. Did exact bytes match their integrity records?
4. Was the comparison equivalent or different, independent of health?
5. Were all deltas mapped, and were matches presented only as informational
   catalog rules?
6. Did text and JSON preserve the same bounded state, facts, uncertainty, and
   authority limitations?
7. What operator question, if any, remained unanswered by the deterministic
   brief?

An unanswered question is evidence for later planning, not automatic approval
for a model, broader collection, or remediation authority.

## Cleanup

After recording only the approved disclosure-minimized results, remove the
temporary directory deliberately:

~~~powershell
Remove-Item -LiteralPath $demoRoot -Recurse -Force
~~~

This deletes locally generated demonstration artifacts. It does not delete or
change any repository, cluster, application, or monitoring object.
