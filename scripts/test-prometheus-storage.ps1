param(
    [string]$Namespace = "forge-observability",
    [string]$StorageClass = "signalforge-local-nvme",
    [string]$PersistentVolume = "prometheus-local-nvme",
    [string]$PersistentVolumeClaim = "prometheus-data",
    [string]$Deployment = "prometheus",
    [string]$Service = "prometheus",
    [string]$ExpectedNode = "forge-head"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Equal {
    param(
        [object]$Actual,
        [object]$Expected,
        [string]$Message
    )

    if ($Actual -ne $Expected) {
        throw "$Message (expected '$Expected', found '$Actual')"
    }
}

function Get-KubernetesResource {
    param(
        [string]$Resource,
        [string]$Name,
        [string]$ResourceNamespace = ""
    )

    $KubectlArguments = @("get", $Resource, $Name)

    if ($ResourceNamespace) {
        $KubectlArguments += @("-n", $ResourceNamespace)
    }

    $KubectlArguments += @("-o", "json")
    $Json = & kubectl @KubectlArguments

    if ($LASTEXITCODE -ne 0 -or -not $Json) {
        throw "Could not read $Resource $Name"
    }

    return ($Json | Out-String | ConvertFrom-Json)
}

Write-Host "Checking Prometheus persistent-storage resources..."

$StorageClassObject = Get-KubernetesResource "storageclass" $StorageClass
Assert-Equal $StorageClassObject.provisioner "kubernetes.io/no-provisioner" "StorageClass provisioner mismatch"
Assert-Equal $StorageClassObject.reclaimPolicy "Retain" "StorageClass reclaim policy mismatch"
Assert-Equal $StorageClassObject.volumeBindingMode "WaitForFirstConsumer" "StorageClass binding mode mismatch"

$DefaultAnnotations = @(
    "storageclass.kubernetes.io/is-default-class",
    "storageclass.beta.kubernetes.io/is-default-class"
)

if ($StorageClassObject.metadata.PSObject.Properties.Name -contains "annotations") {
    foreach ($AnnotationName in $DefaultAnnotations) {
        $Annotation = $StorageClassObject.metadata.annotations.PSObject.Properties[$AnnotationName]

        if ($null -ne $Annotation -and $Annotation.Value -eq "true") {
            throw "StorageClass $StorageClass must not be the default StorageClass"
        }
    }
}

$PersistentVolumeObject = Get-KubernetesResource "pv" $PersistentVolume
Assert-Equal $PersistentVolumeObject.status.phase "Bound" "PersistentVolume is not Bound"
Assert-Equal $PersistentVolumeObject.spec.capacity.storage "30Gi" "PersistentVolume capacity mismatch"
Assert-Equal $PersistentVolumeObject.spec.volumeMode "Filesystem" "PersistentVolume volume mode mismatch"
Assert-Equal $PersistentVolumeObject.spec.storageClassName $StorageClass "PersistentVolume StorageClass mismatch"
Assert-Equal $PersistentVolumeObject.spec.persistentVolumeReclaimPolicy "Retain" "PersistentVolume reclaim policy mismatch"
Assert-Equal $PersistentVolumeObject.spec.local.path "/mnt/signalforge-prometheus/data" "PersistentVolume local path mismatch"
Assert-Equal $PersistentVolumeObject.spec.claimRef.namespace $Namespace "PersistentVolume claim namespace mismatch"
Assert-Equal $PersistentVolumeObject.spec.claimRef.name $PersistentVolumeClaim "PersistentVolume claim name mismatch"

$PvAccessModes = @($PersistentVolumeObject.spec.accessModes)

if ($PvAccessModes.Count -ne 1 -or $PvAccessModes[0] -ne "ReadWriteOnce") {
    throw "PersistentVolume must have only ReadWriteOnce access"
}

$HostnameExpressions = @(
    $PersistentVolumeObject.spec.nodeAffinity.required.nodeSelectorTerms |
        ForEach-Object { $_.matchExpressions } |
        Where-Object {
            $_.key -eq "kubernetes.io/hostname" -and
            $_.operator -eq "In"
        }
)

if ($HostnameExpressions.Count -ne 1) {
    throw "PersistentVolume must contain exactly one hostname node-affinity expression"
}

$HostnameValues = @($HostnameExpressions[0].values)

if ($HostnameValues.Count -ne 1 -or $HostnameValues[0] -ne $ExpectedNode) {
    throw "PersistentVolume node affinity must target only $ExpectedNode"
}

$PersistentVolumeClaimObject = Get-KubernetesResource "pvc" $PersistentVolumeClaim $Namespace
Assert-Equal $PersistentVolumeClaimObject.status.phase "Bound" "PersistentVolumeClaim is not Bound"
Assert-Equal $PersistentVolumeClaimObject.spec.storageClassName $StorageClass "PersistentVolumeClaim StorageClass mismatch"
Assert-Equal $PersistentVolumeClaimObject.spec.volumeName $PersistentVolume "PersistentVolumeClaim volume reservation mismatch"
Assert-Equal $PersistentVolumeClaimObject.spec.resources.requests.storage "30Gi" "PersistentVolumeClaim capacity mismatch"

$PvcAccessModes = @($PersistentVolumeClaimObject.spec.accessModes)

if ($PvcAccessModes.Count -ne 1 -or $PvcAccessModes[0] -ne "ReadWriteOnce") {
    throw "PersistentVolumeClaim must request only ReadWriteOnce access"
}

$DeploymentObject = Get-KubernetesResource "deployment" $Deployment $Namespace
Assert-Equal $DeploymentObject.spec.replicas 1 "Prometheus replica count mismatch"
Assert-Equal $DeploymentObject.spec.strategy.type "Recreate" "Prometheus strategy mismatch"

$PodSpec = $DeploymentObject.spec.template.spec

if ($PodSpec.PSObject.Properties.Name -contains "nodeSelector") {
    throw "Prometheus must derive node placement from PV affinity, not a Deployment nodeSelector"
}

$ControlPlaneTolerations = @(
    $PodSpec.tolerations | Where-Object {
        $_.key -eq "node-role.kubernetes.io/control-plane" -and
        $_.operator -eq "Exists" -and
        $_.effect -eq "NoSchedule"
    }
)

if (@($PodSpec.tolerations).Count -ne 1 -or $ControlPlaneTolerations.Count -ne 1) {
    throw "Prometheus must have only the narrowly scoped control-plane NoSchedule toleration"
}

$StorageVolumes = @($PodSpec.volumes | Where-Object { $_.name -eq "storage" })

if ($StorageVolumes.Count -ne 1) {
    throw "Prometheus Deployment must contain exactly one storage volume"
}

Assert-Equal $StorageVolumes[0].persistentVolumeClaim.claimName $PersistentVolumeClaim "Prometheus PVC mount mismatch"

$PrometheusContainers = @($PodSpec.containers | Where-Object { $_.name -eq "prometheus" })

if ($PrometheusContainers.Count -ne 1) {
    throw "Prometheus Deployment must contain exactly one prometheus container"
}

$PrometheusArguments = @($PrometheusContainers[0].args)

if ($PrometheusArguments -notcontains "--storage.tsdb.retention.time=30d") {
    throw "Prometheus retention time must be 30d"
}

if ($PrometheusArguments -notcontains "--storage.tsdb.retention.size=24GB") {
    throw "Prometheus retention size must be 24GB"
}

$PodListJson = kubectl get pods -n $Namespace -l app=prometheus -o json

if ($LASTEXITCODE -ne 0 -or -not $PodListJson) {
    throw "Could not read Prometheus Pods"
}

$Pods = @(($PodListJson | Out-String | ConvertFrom-Json).items)

if ($Pods.Count -ne 1) {
    throw "Expected exactly one Prometheus Pod, found $($Pods.Count)"
}

Assert-Equal $Pods[0].spec.nodeName $ExpectedNode "Prometheus Pod is on the wrong node"
Assert-Equal $Pods[0].status.phase "Running" "Prometheus Pod is not Running"

$PodStorageVolumes = @($Pods[0].spec.volumes | Where-Object { $_.name -eq "storage" })

if ($PodStorageVolumes.Count -ne 1) {
    throw "Running Prometheus Pod does not contain exactly one storage volume"
}

Assert-Equal $PodStorageVolumes[0].persistentVolumeClaim.claimName $PersistentVolumeClaim "Running Prometheus Pod PVC mismatch"

$ReadyConditions = @(
    $Pods[0].status.conditions | Where-Object {
        $_.type -eq "Ready" -and $_.status -eq "True"
    }
)

if ($ReadyConditions.Count -ne 1) {
    throw "Prometheus Pod is not Ready"
}

$ServiceObject = Get-KubernetesResource "service" $Service $Namespace
Assert-Equal $ServiceObject.spec.type "ClusterIP" "Prometheus Service must remain ClusterIP-only"

Write-Host "StorageClass: non-default, no-provisioner, WaitForFirstConsumer, Retain"
Write-Host "PV/PVC: Bound, 30Gi, ReadWriteOnce, Retain, explicitly reserved"
Write-Host "Placement: Prometheus is Ready on $ExpectedNode through PV node affinity"
Write-Host "Retention: 30d or 24GB"
Write-Host "Access: ClusterIP-only"
Write-Host "PASS: Prometheus persistent-storage configuration is valid."
