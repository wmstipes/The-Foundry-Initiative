import sys
import runpy
from pathlib import Path

import yaml

RESTAURANT_MANIFEST_DIR = Path("k8s/fastapi-restaurant")
PROMETHEUS_MANIFEST_DIR = Path("k8s/prometheus")
METRICS_SERVER_MANIFEST_DIR = Path("k8s/metrics-server")

RESTAURANT_NAMESPACE = "forge-restaurant"
RESTAURANT_APP = "restaurant-api"
EXPECTED_IMAGE_PREFIX = "wmstipes/signalforge-restaurant-api:"
EXPECTED_NODEPORT = 30080
EXPECTED_VERSION = "0.7.0"
EXPECTED_RESTAURANT_IMAGE = f"{EXPECTED_IMAGE_PREFIX}{EXPECTED_VERSION}"

PROMETHEUS_NAMESPACE = "forge-observability"
PROMETHEUS_APP = "prometheus"
PROMETHEUS_IMAGE = "prom/prometheus:v3.13.2"
PROMETHEUS_ROLE = "prometheus-restaurant-pod-reader"
PROMETHEUS_STORAGE_CLASS = "signalforge-local-nvme"
PROMETHEUS_PERSISTENT_VOLUME = "prometheus-local-nvme"
PROMETHEUS_PERSISTENT_VOLUME_CLAIM = "prometheus-data"
PROMETHEUS_STORAGE_NODE = "forge-head"
PROMETHEUS_LOCAL_PATH = "/mnt/signalforge-prometheus/data"
PROMETHEUS_STORAGE_PREFLIGHT = "prometheus-storage-preflight"
PROMETHEUS_BACKUP_POD = "prometheus-backup"
PROMETHEUS_RESTORE_VALIDATION_POD = "prometheus-restore-validation"
PROMETHEUS_RESTORE_PATH = "/mnt/signalforge-prometheus/restore-validation"
PROMETHEUS_RULE_PATH = "/etc/prometheus/restaurant-scrape.rules.yaml"

METRICS_SERVER_NAMESPACE = "kube-system"
METRICS_SERVER_APP = "metrics-server"
METRICS_SERVER_IMAGE = "registry.k8s.io/metrics-server/metrics-server:v0.9.0"
METRICS_SERVER_CA_ARGUMENT = (
    "--kubelet-certificate-authority="
    "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
)

WORKBENCH_MANIFEST_DIR = Path("k8s/forge-yaml-workbench")
WORKBENCH_NAMESPACE = "forge-tools"
WORKBENCH_APP = "forge-yaml-workbench"
WORKBENCH_VERSION = "0.1.0"
WORKBENCH_IMAGE_DIGEST = (
    "sha256:dee700a8754c39f736b94f85c7ad484b2ebe6c41647cf7fa5d37c905c25ae190"
)
WORKBENCH_IMAGE = (
    f"wmstipes/signalforge-yaml-workbench:{WORKBENCH_VERSION}"
    f"@{WORKBENCH_IMAGE_DIGEST}"
)
WORKBENCH_CONTAINER_PORT = 8080
WORKBENCH_NODEPORT = 30081

REQUIRED_RESTAURANT_FILES = [
    "namespace.yaml",
    "restaurant-api-config.yaml",
    "restaurant-api-deployment.yaml",
    "restaurant-api-service.yaml",
    "restaurant-api-nodeport.yaml",
]

REQUIRED_PROMETHEUS_FILES = [
    "namespace.yaml",
    "prometheus-service-account.yaml",
    "restaurant-pod-reader-role.yaml",
    "restaurant-pod-reader-role-binding.yaml",
    "prometheus-config.yaml",
    "prometheus-storage-class.yaml",
    "prometheus-local-pv.yaml",
    "prometheus-data-pvc.yaml",
    "prometheus-storage-preflight-pod.yaml",
    "prometheus-backup-pod.yaml",
    "prometheus-restore-validation-pod.yaml",
    "prometheus-deployment.yaml",
    "prometheus-service.yaml",
]

REQUIRED_METRICS_SERVER_FILES = [
    "metrics-server-service-account.yaml",
    "metrics-server-rbac.yaml",
    "metrics-server-service.yaml",
    "metrics-server-deployment.yaml",
    "metrics-server-api-service.yaml",
]

REQUIRED_WORKBENCH_FILES = [
    "namespace.yaml",
    "forge-yaml-workbench-deployment.yaml",
    "forge-yaml-workbench-service.yaml",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = yaml.safe_load(file)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"{path} did not parse into a YAML object")

    return data


def load_yaml_documents(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            documents = [document for document in yaml.safe_load_all(file) if document is not None]
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    require(documents, f"{path} did not contain any YAML objects")
    require(
        all(isinstance(document, dict) for document in documents),
        f"{path} contained a YAML document that was not an object",
    )
    return documents


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_files(directory: Path, filenames: list[str]) -> None:
    require(directory.exists(), f"{directory} does not exist")

    for filename in filenames:
        require((directory / filename).exists(), f"Missing required manifest: {directory / filename}")


def has_relabel_rule(
    rules: list[dict],
    source_label: str,
    *,
    action: str,
    regex: str | None = None,
    target_label: str | None = None,
) -> bool:
    for rule in rules:
        if rule.get("action") != action:
            continue
        if rule.get("source_labels") != [source_label]:
            continue
        if regex is not None and rule.get("regex") != regex:
            continue
        if target_label is not None and rule.get("target_label") != target_label:
            continue
        return True

    return False


def validate_restaurant_manifests() -> None:
    require_files(RESTAURANT_MANIFEST_DIR, REQUIRED_RESTAURANT_FILES)
    ok("All required Restaurant API manifest files exist")

    namespace = load_yaml(RESTAURANT_MANIFEST_DIR / "namespace.yaml")
    config = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-config.yaml")
    deployment = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-deployment.yaml")
    service = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-service.yaml")
    nodeport = load_yaml(RESTAURANT_MANIFEST_DIR / "restaurant-api-nodeport.yaml")

    require(namespace.get("kind") == "Namespace", "Restaurant namespace manifest must be kind Namespace")
    require(namespace.get("metadata", {}).get("name") == RESTAURANT_NAMESPACE, "Restaurant namespace must be forge-restaurant")
    ok("Restaurant namespace manifest is valid")

    require(config.get("kind") == "ConfigMap", "restaurant-api-config.yaml must be kind ConfigMap")
    require(config.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant ConfigMap namespace mismatch")
    require(config.get("data", {}).get("APP_VERSION") == EXPECTED_VERSION, "ConfigMap APP_VERSION mismatch")
    require(config.get("data", {}).get("FEATURE_ANALYZE_ENABLED") == "true", "FEATURE_ANALYZE_ENABLED should be true")
    ok("Restaurant ConfigMap manifest is valid")

    require(deployment.get("kind") == "Deployment", "restaurant-api-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant Deployment namespace mismatch")
    require(deployment.get("metadata", {}).get("name") == RESTAURANT_APP, "Restaurant Deployment name mismatch")

    template = deployment.get("spec", {}).get("template", {})
    pod_labels = template.get("metadata", {}).get("labels", {})
    require(pod_labels.get("app") == RESTAURANT_APP, "Restaurant Deployment Pod label app mismatch")

    containers = template.get("spec", {}).get("containers", [])
    require(len(containers) == 1, "Restaurant Deployment should have exactly one container")

    container = containers[0]
    require(container.get("name") == RESTAURANT_APP, "Restaurant container name mismatch")
    require(container.get("image") == EXPECTED_RESTAURANT_IMAGE, "Restaurant container image/version mismatch")
    require("readinessProbe" in container, "Restaurant container missing readinessProbe")
    require("livenessProbe" in container, "Restaurant container missing livenessProbe")
    require("resources" in container, "Restaurant container missing resources block")
    ok("Restaurant Deployment manifest is valid")

    require(service.get("kind") == "Service", "restaurant-api-service.yaml must be kind Service")
    require(service.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Restaurant internal Service must be ClusterIP")
    require(service.get("spec", {}).get("selector", {}).get("app") == RESTAURANT_APP, "Restaurant internal Service selector mismatch")
    ok("Restaurant internal Service manifest is valid")

    require(nodeport.get("kind") == "Service", "restaurant-api-nodeport.yaml must be kind Service")
    require(nodeport.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Restaurant NodePort Service namespace mismatch")
    require(nodeport.get("spec", {}).get("type") == "NodePort", "Restaurant external Service must be NodePort")
    require(nodeport.get("spec", {}).get("selector", {}).get("app") == RESTAURANT_APP, "Restaurant NodePort Service selector mismatch")

    ports = nodeport.get("spec", {}).get("ports", [])
    require(len(ports) == 1, "Restaurant NodePort Service should have one port entry")
    require(ports[0].get("nodePort") == EXPECTED_NODEPORT, "Restaurant NodePort must be 30080")
    ok("Restaurant NodePort Service manifest is valid")


def validate_prometheus_manifests() -> None:
    require_files(PROMETHEUS_MANIFEST_DIR, REQUIRED_PROMETHEUS_FILES)
    ok("All required Prometheus manifest files exist")

    namespace = load_yaml(PROMETHEUS_MANIFEST_DIR / "namespace.yaml")
    service_account = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-service-account.yaml")
    role = load_yaml(PROMETHEUS_MANIFEST_DIR / "restaurant-pod-reader-role.yaml")
    role_binding = load_yaml(PROMETHEUS_MANIFEST_DIR / "restaurant-pod-reader-role-binding.yaml")
    config_map = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-config.yaml")
    storage_class = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-storage-class.yaml")
    persistent_volume = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-local-pv.yaml")
    persistent_volume_claim = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-data-pvc.yaml")
    storage_preflight = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-storage-preflight-pod.yaml")
    backup_pod = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-backup-pod.yaml")
    restore_validation_pod = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-restore-validation-pod.yaml")
    deployment = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-deployment.yaml")
    service = load_yaml(PROMETHEUS_MANIFEST_DIR / "prometheus-service.yaml")

    require(namespace.get("kind") == "Namespace", "Prometheus namespace manifest must be kind Namespace")
    require(namespace.get("metadata", {}).get("name") == PROMETHEUS_NAMESPACE, "Prometheus namespace must be forge-observability")
    ok("Prometheus namespace manifest is valid")

    require(service_account.get("kind") == "ServiceAccount", "Prometheus identity must be a ServiceAccount")
    require(service_account.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus ServiceAccount name mismatch")
    require(service_account.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus ServiceAccount namespace mismatch")
    ok("Prometheus ServiceAccount manifest is valid")

    require(role.get("kind") == "Role", "Restaurant Pod reader must be a namespace-scoped Role")
    require(role.get("metadata", {}).get("name") == PROMETHEUS_ROLE, "Prometheus Role name mismatch")
    require(role.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Prometheus Role must be scoped to forge-restaurant")
    role_rules = role.get("rules", [])
    require(len(role_rules) == 1, "Prometheus Role should contain exactly one rule")
    require(role_rules[0].get("apiGroups") == [""], "Prometheus Role should use the core API group")
    require(role_rules[0].get("resources") == ["pods"], "Prometheus Role should grant access only to Pods")
    require(set(role_rules[0].get("verbs", [])) == {"get", "list", "watch"}, "Prometheus Role should grant only get, list, and watch")
    ok("Prometheus least-privilege Role manifest is valid")

    require(role_binding.get("kind") == "RoleBinding", "Prometheus access grant must be a RoleBinding")
    require(role_binding.get("metadata", {}).get("namespace") == RESTAURANT_NAMESPACE, "Prometheus RoleBinding must be scoped to forge-restaurant")
    require(role_binding.get("roleRef", {}).get("kind") == "Role", "Prometheus RoleBinding must reference a Role")
    require(role_binding.get("roleRef", {}).get("name") == PROMETHEUS_ROLE, "Prometheus RoleBinding roleRef mismatch")
    subjects = role_binding.get("subjects", [])
    require(len(subjects) == 1, "Prometheus RoleBinding should have exactly one subject")
    require(subjects[0].get("kind") == "ServiceAccount", "Prometheus RoleBinding subject must be a ServiceAccount")
    require(subjects[0].get("name") == PROMETHEUS_APP, "Prometheus RoleBinding subject name mismatch")
    require(subjects[0].get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus RoleBinding subject namespace mismatch")
    ok("Prometheus RoleBinding manifest is valid")

    require(config_map.get("kind") == "ConfigMap", "prometheus-config.yaml must be kind ConfigMap")
    require(config_map.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus ConfigMap namespace mismatch")
    prometheus_text = config_map.get("data", {}).get("prometheus.yml")
    require(isinstance(prometheus_text, str), "Prometheus ConfigMap must contain prometheus.yml")
    rule_text = config_map.get("data", {}).get("restaurant-scrape.rules.yaml")
    require(isinstance(rule_text, str), "Prometheus ConfigMap must contain the Restaurant API alert rules")
    require(
        set(config_map.get("data", {})) == {"prometheus.yml", "restaurant-scrape.rules.yaml"},
        "Prometheus ConfigMap must contain only the approved server and rule files",
    )

    try:
        prometheus_config = yaml.safe_load(prometheus_text)
    except yaml.YAMLError as exc:
        fail(f"Embedded prometheus.yml could not be parsed: {exc}")

    global_config = prometheus_config.get("global", {})
    require(global_config.get("scrape_interval") == "30s", "Prometheus scrape interval must be 30s")
    require(global_config.get("scrape_timeout") == "10s", "Prometheus scrape timeout must be 10s")
    require(global_config.get("evaluation_interval") == "30s", "Prometheus evaluation interval must be 30s")
    require(
        prometheus_config.get("rule_files") == [PROMETHEUS_RULE_PATH],
        "Prometheus must load only the approved Restaurant API alert rule file",
    )
    require("alerting" not in prometheus_config, "Prometheus must not configure Alertmanager or receivers")

    try:
        embedded_rules = yaml.safe_load(rule_text)
        canonical_rules = load_yaml(Path("monitoring/alerts/restaurant-scrape.rules.yaml"))
    except yaml.YAMLError as exc:
        fail(f"Embedded alert rules could not be parsed: {exc}")

    require(embedded_rules == canonical_rules, "Embedded alert rules must match the canonical validated rules")

    scrape_jobs = prometheus_config.get("scrape_configs", [])
    restaurant_jobs = [job for job in scrape_jobs if job.get("job_name") == RESTAURANT_APP]
    require(len(restaurant_jobs) == 1, "Prometheus must define exactly one restaurant-api scrape job")
    restaurant_job = restaurant_jobs[0]
    require(restaurant_job.get("metrics_path") == "/metrics", "Restaurant API metrics path must be /metrics")

    discovery = restaurant_job.get("kubernetes_sd_configs", [])
    require(len(discovery) == 1, "Restaurant API scrape job should have one Kubernetes discovery configuration")
    require(discovery[0].get("role") == "pod", "Restaurant API scrape job must use Pod discovery")
    require(discovery[0].get("namespaces", {}).get("names") == [RESTAURANT_NAMESPACE], "Prometheus Pod discovery must be limited to forge-restaurant")

    relabel_rules = restaurant_job.get("relabel_configs", [])
    required_keep_rules = {
        "__meta_kubernetes_pod_label_app": RESTAURANT_APP,
        "__meta_kubernetes_pod_container_name": RESTAURANT_APP,
        "__meta_kubernetes_pod_container_port_name": "http",
    }

    for source_label, regex in required_keep_rules.items():
        require(
            has_relabel_rule(relabel_rules, source_label, action="keep", regex=regex),
            f"Prometheus scrape job missing keep rule for {source_label}",
        )

    required_target_labels = {
        "__meta_kubernetes_namespace": "namespace",
        "__meta_kubernetes_pod_name": "pod",
        "__meta_kubernetes_pod_node_name": "node",
        "__meta_kubernetes_pod_phase": "pod_phase",
        "__meta_kubernetes_pod_ready": "pod_ready",
    }

    for source_label, target_label in required_target_labels.items():
        require(
            has_relabel_rule(relabel_rules, source_label, action="replace", target_label=target_label),
            f"Prometheus scrape job missing target label {target_label}",
        )

    ok("Prometheus scrape configuration is valid")

    require(storage_class.get("kind") == "StorageClass", "Prometheus StorageClass manifest must be kind StorageClass")
    require(storage_class.get("metadata", {}).get("name") == PROMETHEUS_STORAGE_CLASS, "Prometheus StorageClass name mismatch")
    require(storage_class.get("provisioner") == "kubernetes.io/no-provisioner", "Prometheus StorageClass must use no-provisioner")
    require(storage_class.get("reclaimPolicy") == "Retain", "Prometheus StorageClass reclaim policy must be Retain")
    require(storage_class.get("volumeBindingMode") == "WaitForFirstConsumer", "Prometheus StorageClass must use WaitForFirstConsumer")
    storage_annotations = storage_class.get("metadata", {}).get("annotations", {})
    require(
        storage_annotations.get("storageclass.kubernetes.io/is-default-class") != "true"
        and storage_annotations.get("storageclass.beta.kubernetes.io/is-default-class") != "true",
        "Prometheus StorageClass must not be a default StorageClass",
    )
    ok("Prometheus non-default local StorageClass manifest is valid")

    require(persistent_volume.get("kind") == "PersistentVolume", "Prometheus PV manifest must be kind PersistentVolume")
    require(persistent_volume.get("metadata", {}).get("name") == PROMETHEUS_PERSISTENT_VOLUME, "Prometheus PV name mismatch")
    pv_spec = persistent_volume.get("spec", {})
    require(pv_spec.get("capacity", {}).get("storage") == "30Gi", "Prometheus PV capacity must be 30Gi")
    require(pv_spec.get("volumeMode") == "Filesystem", "Prometheus PV volumeMode must be Filesystem")
    require(pv_spec.get("accessModes") == ["ReadWriteOnce"], "Prometheus PV must use only ReadWriteOnce")
    require(pv_spec.get("persistentVolumeReclaimPolicy") == "Retain", "Prometheus PV reclaim policy must be Retain")
    require(pv_spec.get("storageClassName") == PROMETHEUS_STORAGE_CLASS, "Prometheus PV StorageClass mismatch")
    require(pv_spec.get("local", {}).get("path") == PROMETHEUS_LOCAL_PATH, "Prometheus PV local path mismatch")
    require(
        pv_spec.get("claimRef") == {
            "namespace": PROMETHEUS_NAMESPACE,
            "name": PROMETHEUS_PERSISTENT_VOLUME_CLAIM,
        },
        "Prometheus PV must be reserved for the intended PVC",
    )

    node_terms = pv_spec.get("nodeAffinity", {}).get("required", {}).get("nodeSelectorTerms", [])
    require(len(node_terms) == 1, "Prometheus PV must contain exactly one required node selector term")
    node_expressions = node_terms[0].get("matchExpressions", [])
    require(
        node_expressions == [
            {
                "key": "kubernetes.io/hostname",
                "operator": "In",
                "values": [PROMETHEUS_STORAGE_NODE],
            }
        ],
        "Prometheus PV must use exact forge-head hostname node affinity",
    )
    ok("Prometheus static local PersistentVolume manifest is valid")

    require(persistent_volume_claim.get("kind") == "PersistentVolumeClaim", "Prometheus PVC manifest must be kind PersistentVolumeClaim")
    require(persistent_volume_claim.get("metadata", {}).get("name") == PROMETHEUS_PERSISTENT_VOLUME_CLAIM, "Prometheus PVC name mismatch")
    require(persistent_volume_claim.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus PVC namespace mismatch")
    pvc_spec = persistent_volume_claim.get("spec", {})
    require(pvc_spec.get("accessModes") == ["ReadWriteOnce"], "Prometheus PVC must request only ReadWriteOnce")
    require(pvc_spec.get("volumeMode") == "Filesystem", "Prometheus PVC volumeMode must be Filesystem")
    require(pvc_spec.get("storageClassName") == PROMETHEUS_STORAGE_CLASS, "Prometheus PVC StorageClass mismatch")
    require(pvc_spec.get("volumeName") == PROMETHEUS_PERSISTENT_VOLUME, "Prometheus PVC must name the dedicated PV")
    require(pvc_spec.get("resources", {}).get("requests", {}).get("storage") == "30Gi", "Prometheus PVC request must be 30Gi")
    ok("Prometheus reserved PersistentVolumeClaim manifest is valid")

    require(storage_preflight.get("kind") == "Pod", "Prometheus storage preflight manifest must be kind Pod")
    require(storage_preflight.get("metadata", {}).get("name") == PROMETHEUS_STORAGE_PREFLIGHT, "Prometheus storage preflight Pod name mismatch")
    require(storage_preflight.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus storage preflight Pod namespace mismatch")
    preflight_spec = storage_preflight.get("spec", {})
    require(preflight_spec.get("restartPolicy") == "Never", "Prometheus storage preflight Pod restart policy must be Never")
    require("nodeSelector" not in preflight_spec, "Storage preflight placement must come from PV node affinity")
    require(
        preflight_spec.get("tolerations") == [
            {
                "key": "node-role.kubernetes.io/control-plane",
                "operator": "Exists",
                "effect": "NoSchedule",
            }
        ],
        "Storage preflight Pod must have only the exact control-plane toleration",
    )
    preflight_security_context = preflight_spec.get("securityContext", {})
    require(preflight_security_context.get("runAsNonRoot") is True, "Storage preflight Pod must run as non-root")
    require(preflight_security_context.get("runAsUser") == 65534, "Storage preflight UID must be 65534")
    require(preflight_security_context.get("runAsGroup") == 65534, "Storage preflight GID must be 65534")
    require(preflight_security_context.get("fsGroup") == 65534, "Storage preflight fsGroup must be 65534")
    require(
        preflight_security_context.get("fsGroupChangePolicy") == "OnRootMismatch",
        "Storage preflight must avoid unnecessary recursive ownership changes",
    )
    preflight_containers = preflight_spec.get("containers", [])
    require(len(preflight_containers) == 1, "Storage preflight Pod must have exactly one container")
    preflight_container = preflight_containers[0]
    require(preflight_container.get("image") == "busybox:1.37.0", "Storage preflight image must be pinned")
    require(
        ".signalforge-storage-preflight" in "\n".join(preflight_container.get("args", [])),
        "Storage preflight must write and verify its marker",
    )
    require("readinessProbe" in preflight_container, "Storage preflight container must gate readiness on its write test")
    preflight_mounts = [mount for mount in preflight_container.get("volumeMounts", []) if mount.get("name") == "storage"]
    require(
        preflight_mounts == [{"name": "storage", "mountPath": "/prometheus"}],
        "Storage preflight container must mount the PVC at /prometheus",
    )
    preflight_volumes = [volume for volume in preflight_spec.get("volumes", []) if volume.get("name") == "storage"]
    require(len(preflight_volumes) == 1, "Storage preflight Pod must define one storage volume")
    require(
        preflight_volumes[0].get("persistentVolumeClaim", {}).get("claimName")
        == PROMETHEUS_PERSISTENT_VOLUME_CLAIM,
        "Storage preflight Pod must mount the Prometheus PVC",
    )
    ok("Prometheus storage first-consumer preflight manifest is valid")

    require(backup_pod.get("kind") == "Pod", "Prometheus backup manifest must be kind Pod")
    require(backup_pod.get("metadata", {}).get("name") == PROMETHEUS_BACKUP_POD, "Prometheus backup Pod name mismatch")
    require(backup_pod.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus backup Pod namespace mismatch")
    backup_spec = backup_pod.get("spec", {})
    require(backup_spec.get("restartPolicy") == "Never", "Prometheus backup Pod restart policy must be Never")
    require("nodeSelector" not in backup_spec, "Backup Pod placement must come from PV node affinity")
    require(
        backup_spec.get("tolerations") == [
            {
                "key": "node-role.kubernetes.io/control-plane",
                "operator": "Exists",
                "effect": "NoSchedule",
            }
        ],
        "Backup Pod must have only the exact control-plane toleration",
    )
    backup_security_context = backup_spec.get("securityContext", {})
    require(backup_security_context.get("runAsNonRoot") is True, "Backup Pod must run as non-root")
    require(backup_security_context.get("runAsUser") == 65534, "Backup Pod UID must be 65534")
    require(backup_security_context.get("runAsGroup") == 65534, "Backup Pod GID must be 65534")
    require(backup_security_context.get("fsGroup") == 65534, "Backup Pod fsGroup must be 65534")
    backup_containers = backup_spec.get("containers", [])
    require(len(backup_containers) == 1, "Backup Pod must have exactly one container")
    backup_container = backup_containers[0]
    require(backup_container.get("image") == "busybox:1.37.0", "Backup Pod image must be pinned")
    require("readinessProbe" in backup_container, "Backup Pod must verify that the TSDB is readable")
    backup_mounts = [mount for mount in backup_container.get("volumeMounts", []) if mount.get("name") == "storage"]
    require(
        backup_mounts == [{"name": "storage", "mountPath": "/prometheus", "readOnly": True}],
        "Backup Pod must mount the TSDB read-only at /prometheus",
    )
    backup_volumes = [volume for volume in backup_spec.get("volumes", []) if volume.get("name") == "storage"]
    require(len(backup_volumes) == 1, "Backup Pod must define one storage volume")
    require(
        backup_volumes[0].get("persistentVolumeClaim")
        == {"claimName": PROMETHEUS_PERSISTENT_VOLUME_CLAIM, "readOnly": True},
        "Backup Pod must mount the Prometheus PVC read-only",
    )
    ok("Prometheus cold-backup Pod manifest is valid")

    require(restore_validation_pod.get("kind") == "Pod", "Prometheus restore-validation manifest must be kind Pod")
    require(
        restore_validation_pod.get("metadata", {}).get("name") == PROMETHEUS_RESTORE_VALIDATION_POD,
        "Prometheus restore-validation Pod name mismatch",
    )
    require(
        restore_validation_pod.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE,
        "Prometheus restore-validation Pod namespace mismatch",
    )
    restore_spec = restore_validation_pod.get("spec", {})
    require(restore_spec.get("restartPolicy") == "Never", "Restore-validation Pod restart policy must be Never")
    require(
        restore_spec.get("nodeSelector") == {"kubernetes.io/hostname": PROMETHEUS_STORAGE_NODE},
        "Restore-validation Pod must target only forge-head",
    )
    require(
        restore_spec.get("tolerations") == [
            {
                "key": "node-role.kubernetes.io/control-plane",
                "operator": "Exists",
                "effect": "NoSchedule",
            }
        ],
        "Restore-validation Pod must have only the exact control-plane toleration",
    )
    restore_security_context = restore_spec.get("securityContext", {})
    require(restore_security_context.get("runAsNonRoot") is True, "Restore-validation Pod must run as non-root")
    require(restore_security_context.get("runAsUser") == 65534, "Restore-validation Pod UID must be 65534")
    require(restore_security_context.get("runAsGroup") == 65534, "Restore-validation Pod GID must be 65534")
    restore_containers = restore_spec.get("containers", [])
    require(len(restore_containers) == 1, "Restore-validation Pod must have exactly one container")
    restore_container = restore_containers[0]
    require(restore_container.get("image") == PROMETHEUS_IMAGE, "Restore-validation image must match Prometheus")
    require("readinessProbe" in restore_container, "Restore-validation Pod must write-test its isolated directory")
    restore_mounts = [mount for mount in restore_container.get("volumeMounts", []) if mount.get("name") == "restored-data"]
    require(
        restore_mounts == [{"name": "restored-data", "mountPath": "/validation"}],
        "Restore-validation Pod must mount only the isolated restored copy at /validation",
    )
    restore_volumes = [volume for volume in restore_spec.get("volumes", []) if volume.get("name") == "restored-data"]
    require(len(restore_volumes) == 1, "Restore-validation Pod must define one restored-data volume")
    require(
        restore_volumes[0].get("hostPath") == {"path": PROMETHEUS_RESTORE_PATH, "type": "Directory"},
        "Restore-validation Pod hostPath must be the exact isolated restore directory",
    )
    require(
        restore_volumes[0].get("hostPath", {}).get("path") != PROMETHEUS_LOCAL_PATH,
        "Restore-validation Pod must never mount the active Prometheus data path",
    )
    ok("Prometheus isolated restore-validation Pod manifest is valid")

    require(deployment.get("kind") == "Deployment", "prometheus-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus Deployment name mismatch")
    require(deployment.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus Deployment namespace mismatch")
    require(deployment.get("spec", {}).get("replicas") == 1, "Prometheus must use one replica")
    require(deployment.get("spec", {}).get("strategy", {}).get("type") == "Recreate", "Prometheus must use the Recreate strategy")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    require(pod_spec.get("serviceAccountName") == PROMETHEUS_APP, "Prometheus Deployment ServiceAccount mismatch")
    require("nodeSelector" not in pod_spec, "Prometheus placement must come from PV node affinity, not a nodeSelector")
    require(
        pod_spec.get("tolerations") == [
            {
                "key": "node-role.kubernetes.io/control-plane",
                "operator": "Exists",
                "effect": "NoSchedule",
            }
        ],
        "Prometheus must have only the exact control-plane NoSchedule toleration",
    )

    pod_security_context = pod_spec.get("securityContext", {})
    require(pod_security_context.get("runAsNonRoot") is True, "Prometheus Pod must run as non-root")
    require(pod_security_context.get("runAsUser") == 65534, "Prometheus runtime UID must be 65534")
    require(pod_security_context.get("runAsGroup") == 65534, "Prometheus runtime GID must be 65534")
    require(pod_security_context.get("fsGroup") == 65534, "Prometheus fsGroup must be 65534")
    require(
        pod_security_context.get("fsGroupChangePolicy") == "OnRootMismatch",
        "Prometheus must avoid unnecessary recursive volume ownership changes",
    )

    containers = pod_spec.get("containers", [])
    require(len(containers) == 1, "Prometheus Deployment should have exactly one container")
    container = containers[0]
    require(container.get("name") == PROMETHEUS_APP, "Prometheus container name mismatch")
    require(container.get("image") == PROMETHEUS_IMAGE, "Prometheus image must be pinned to the approved version")
    require("--storage.tsdb.retention.time=30d" in container.get("args", []), "Prometheus retention time must be 30d")
    require("--storage.tsdb.retention.size=24GB" in container.get("args", []), "Prometheus retention size must be 24GB")
    require("readinessProbe" in container, "Prometheus container missing readinessProbe")
    require("livenessProbe" in container, "Prometheus container missing livenessProbe")

    resources = container.get("resources", {})
    require(resources.get("requests", {}).get("cpu") == "100m", "Prometheus CPU request must be 100m")
    require(resources.get("requests", {}).get("memory") == "256Mi", "Prometheus memory request must be 256Mi")
    require(resources.get("limits", {}).get("cpu") == "500m", "Prometheus CPU limit must be 500m")
    require(resources.get("limits", {}).get("memory") == "512Mi", "Prometheus memory limit must be 512Mi")

    storage_volumes = [volume for volume in pod_spec.get("volumes", []) if volume.get("name") == "storage"]
    require(len(storage_volumes) == 1, "Prometheus Deployment must define one storage volume")
    require(
        storage_volumes[0].get("persistentVolumeClaim", {}).get("claimName") == PROMETHEUS_PERSISTENT_VOLUME_CLAIM,
        "Prometheus storage volume must use the dedicated PVC",
    )
    require("emptyDir" not in storage_volumes[0], "Prometheus storage must not use emptyDir")
    ok("Prometheus Deployment manifest is valid")

    require(service.get("kind") == "Service", "prometheus-service.yaml must be kind Service")
    require(service.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus Service name mismatch")
    require(service.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Prometheus Service must remain ClusterIP-only")
    require(service.get("spec", {}).get("selector", {}).get("app") == PROMETHEUS_APP, "Prometheus Service selector mismatch")
    ports = service.get("spec", {}).get("ports", [])
    require(len(ports) == 1, "Prometheus Service should have one port entry")
    require(ports[0].get("port") == 9090, "Prometheus Service port must be 9090")
    require(ports[0].get("targetPort") == "web", "Prometheus Service targetPort must be web")
    ok("Prometheus ClusterIP Service manifest is valid")


def validate_metrics_server_manifests() -> None:
    require_files(METRICS_SERVER_MANIFEST_DIR, REQUIRED_METRICS_SERVER_FILES)
    ok("All required Metrics Server manifest files exist")

    service_account = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-service-account.yaml")
    rbac_documents = load_yaml_documents(METRICS_SERVER_MANIFEST_DIR / "metrics-server-rbac.yaml")
    service = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-service.yaml")
    deployment = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-deployment.yaml")
    api_service = load_yaml(METRICS_SERVER_MANIFEST_DIR / "metrics-server-api-service.yaml")

    require(service_account.get("kind") == "ServiceAccount", "Metrics Server identity must be a ServiceAccount")
    require(service_account.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server ServiceAccount name mismatch")
    require(service_account.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server ServiceAccount namespace mismatch")
    ok("Metrics Server ServiceAccount manifest is valid")

    rbac_resources = {
        (
            document.get("kind"),
            document.get("metadata", {}).get("name"),
            document.get("metadata", {}).get("namespace"),
        ): document
        for document in rbac_documents
    }
    expected_rbac_resources = {
        ("ClusterRole", "system:aggregated-metrics-reader", None),
        ("RoleBinding", "metrics-server-auth-reader", METRICS_SERVER_NAMESPACE),
        ("ClusterRoleBinding", "metrics-server:system:auth-delegator", None),
        ("ClusterRole", "system:metrics-server", None),
        ("ClusterRoleBinding", "system:metrics-server", None),
    }
    require(len(rbac_documents) == 5, "Metrics Server RBAC manifest must contain five resources")
    require(set(rbac_resources) == expected_rbac_resources, "Metrics Server RBAC resource set mismatch")

    for document in rbac_documents:
        for rule in document.get("rules", []):
            require("*" not in rule.get("apiGroups", []), "Metrics Server RBAC must not grant wildcard API groups")
            require("*" not in rule.get("resources", []), "Metrics Server RBAC must not grant wildcard resources")
            require("*" not in rule.get("verbs", []), "Metrics Server RBAC must not grant wildcard verbs")

    aggregated_reader = rbac_resources[("ClusterRole", "system:aggregated-metrics-reader", None)]
    aggregated_rules = aggregated_reader.get("rules", [])
    require(len(aggregated_rules) == 1, "Aggregated metrics reader must contain one rule")
    require(aggregated_rules[0].get("apiGroups") == ["metrics.k8s.io"], "Aggregated metrics reader API group mismatch")
    require(set(aggregated_rules[0].get("resources", [])) == {"nodes", "pods"}, "Aggregated metrics reader resources mismatch")
    require(set(aggregated_rules[0].get("verbs", [])) == {"get", "list", "watch"}, "Aggregated metrics reader verbs mismatch")

    metrics_role = rbac_resources[("ClusterRole", "system:metrics-server", None)]
    metrics_rules = metrics_role.get("rules", [])
    require(len(metrics_rules) == 2, "Metrics Server ClusterRole must contain two rules")
    require(
        any(rule.get("resources") == ["nodes/metrics"] and rule.get("verbs") == ["get"] for rule in metrics_rules),
        "Metrics Server ClusterRole must grant get on nodes/metrics",
    )
    require(
        any(
            set(rule.get("resources", [])) == {"nodes", "pods"}
            and set(rule.get("verbs", [])) == {"get", "list", "watch"}
            for rule in metrics_rules
        ),
        "Metrics Server ClusterRole must grant read-only Node and Pod discovery",
    )
    ok("Metrics Server upstream RBAC manifests are valid")

    require(service.get("kind") == "Service", "Metrics Server Service manifest must be kind Service")
    require(service.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server Service name mismatch")
    require(service.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Metrics Server Service must be ClusterIP")
    require(service.get("spec", {}).get("selector", {}).get("k8s-app") == METRICS_SERVER_APP, "Metrics Server Service selector mismatch")
    service_ports = service.get("spec", {}).get("ports", [])
    require(len(service_ports) == 1, "Metrics Server Service should contain one port")
    require(service_ports[0].get("port") == 443, "Metrics Server Service port must be 443")
    require(service_ports[0].get("targetPort") == "https", "Metrics Server Service targetPort must be https")
    ok("Metrics Server ClusterIP Service manifest is valid")

    require(deployment.get("kind") == "Deployment", "Metrics Server workload must be a Deployment")
    require(deployment.get("metadata", {}).get("name") == METRICS_SERVER_APP, "Metrics Server Deployment name mismatch")
    require(deployment.get("metadata", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics Server Deployment namespace mismatch")
    require(deployment.get("spec", {}).get("replicas") == 1, "Metrics Server must use one replica")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    require(pod_spec.get("serviceAccountName") == METRICS_SERVER_APP, "Metrics Server Deployment ServiceAccount mismatch")
    require(pod_spec.get("automountServiceAccountToken") is True, "Metrics Server requires its service-account CA and token mount")
    require("hostNetwork" not in pod_spec, "Metrics Server must not use host networking")
    require(
        not any("hostPath" in volume for volume in pod_spec.get("volumes", [])),
        "Metrics Server must not mount host paths",
    )

    containers = pod_spec.get("containers", [])
    require(len(containers) == 1, "Metrics Server Deployment should have exactly one container")
    container = containers[0]
    require(container.get("name") == METRICS_SERVER_APP, "Metrics Server container name mismatch")
    require(container.get("image") == METRICS_SERVER_IMAGE, "Metrics Server image must be pinned to v0.9.0")

    arguments = container.get("args", [])
    require(METRICS_SERVER_CA_ARGUMENT in arguments, "Metrics Server must validate kubelets with the service-account CA")
    require("--kubelet-insecure-tls" not in arguments, "Metrics Server must not disable kubelet TLS verification")
    require(
        "--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname" in arguments,
        "Metrics Server must prefer node InternalIP addresses",
    )
    require("--metric-resolution=15s" in arguments, "Metrics Server resolution must be 15 seconds")

    resources = container.get("resources", {})
    require(resources.get("requests", {}).get("cpu") == "100m", "Metrics Server CPU request must be 100m")
    require(resources.get("requests", {}).get("memory") == "200Mi", "Metrics Server memory request must be 200Mi")
    require("readinessProbe" in container, "Metrics Server container missing readinessProbe")
    require("livenessProbe" in container, "Metrics Server container missing livenessProbe")

    security_context = container.get("securityContext", {})
    require(security_context.get("allowPrivilegeEscalation") is False, "Metrics Server must forbid privilege escalation")
    require(security_context.get("readOnlyRootFilesystem") is True, "Metrics Server root filesystem must be read-only")
    require(security_context.get("runAsNonRoot") is True, "Metrics Server must run as non-root")
    require(security_context.get("seccompProfile", {}).get("type") == "RuntimeDefault", "Metrics Server must use RuntimeDefault seccomp")
    require(security_context.get("capabilities", {}).get("drop") == ["ALL"], "Metrics Server must drop all Linux capabilities")
    ok("Metrics Server Deployment manifest is valid and forbids insecure kubelet TLS")

    require(api_service.get("kind") == "APIService", "Metrics API registration must be kind APIService")
    require(api_service.get("metadata", {}).get("name") == "v1beta1.metrics.k8s.io", "Metrics APIService name mismatch")
    api_service_spec = api_service.get("spec", {})
    require(api_service_spec.get("group") == "metrics.k8s.io", "Metrics APIService group mismatch")
    require(api_service_spec.get("version") == "v1beta1", "Metrics APIService version mismatch")
    require(api_service_spec.get("service", {}).get("name") == METRICS_SERVER_APP, "Metrics APIService target Service mismatch")
    require(api_service_spec.get("service", {}).get("namespace") == METRICS_SERVER_NAMESPACE, "Metrics APIService target namespace mismatch")
    require(api_service_spec.get("insecureSkipTLSVerify") is True, "Metrics APIService must match the upstream ephemeral-serving-certificate model")
    ok("Metrics APIService manifest is valid")


def validate_workbench_manifests() -> None:
    require_files(WORKBENCH_MANIFEST_DIR, REQUIRED_WORKBENCH_FILES)
    ok("All required Forge YAML Workbench manifest files exist")

    namespace = load_yaml(WORKBENCH_MANIFEST_DIR / "namespace.yaml")
    deployment = load_yaml(
        WORKBENCH_MANIFEST_DIR / "forge-yaml-workbench-deployment.yaml"
    )
    service = load_yaml(
        WORKBENCH_MANIFEST_DIR / "forge-yaml-workbench-service.yaml"
    )

    require(
        namespace.get("kind") == "Namespace",
        "Workbench namespace manifest must be kind Namespace",
    )
    require(
        namespace.get("metadata", {}).get("name") == WORKBENCH_NAMESPACE,
        "Workbench namespace must be forge-tools",
    )
    namespace_labels = namespace.get("metadata", {}).get("labels", {})
    for mode in ("enforce", "audit", "warn"):
        require(
            namespace_labels.get(f"pod-security.kubernetes.io/{mode}")
            == "restricted",
            f"Workbench namespace must set Pod Security {mode} to restricted",
        )
        require(
            namespace_labels.get(f"pod-security.kubernetes.io/{mode}-version")
            == "v1.36",
            f"Workbench namespace must pin Pod Security {mode} to v1.36",
        )
    ok("Workbench restricted namespace manifest is valid")

    require(
        deployment.get("kind") == "Deployment",
        "forge-yaml-workbench-deployment.yaml must be kind Deployment",
    )
    deployment_metadata = deployment.get("metadata", {})
    require(
        deployment_metadata.get("name") == WORKBENCH_APP,
        "Workbench Deployment name mismatch",
    )
    require(
        deployment_metadata.get("namespace") == WORKBENCH_NAMESPACE,
        "Workbench Deployment namespace mismatch",
    )

    deployment_spec = deployment.get("spec", {})
    require(
        deployment_spec.get("replicas") == 1,
        "Workbench must use one replica",
    )
    require(
        deployment_spec.get("strategy", {}).get("type") == "RollingUpdate",
        "Workbench must use RollingUpdate",
    )
    require(
        deployment_spec.get("strategy", {}).get("rollingUpdate")
        == {"maxUnavailable": 0, "maxSurge": 1},
        "Workbench rolling-update bounds mismatch",
    )
    selector = deployment_spec.get("selector", {}).get("matchLabels", {})
    require(
        selector == {"app": WORKBENCH_APP},
        "Workbench Deployment selector mismatch",
    )

    template = deployment_spec.get("template", {})
    require(
        template.get("metadata", {}).get("labels", {}).get("app")
        == WORKBENCH_APP,
        "Workbench Pod label app mismatch",
    )
    pod_spec = template.get("spec", {})
    require(
        pod_spec.get("automountServiceAccountToken") is False,
        "Workbench must not mount a ServiceAccount token",
    )
    require(
        "serviceAccountName" not in pod_spec,
        "Workbench must not request a Kubernetes identity",
    )
    require(
        pod_spec.get("enableServiceLinks") is False,
        "Workbench must disable injected Service environment variables",
    )
    pod_security = pod_spec.get("securityContext", {})
    require(
        pod_security.get("runAsNonRoot") is True,
        "Workbench Pod must run as non-root",
    )
    require(
        pod_security.get("seccompProfile") == {"type": "RuntimeDefault"},
        "Workbench Pod must use RuntimeDefault seccomp",
    )

    containers = pod_spec.get("containers", [])
    require(
        len(containers) == 1,
        "Workbench Deployment must have exactly one container",
    )
    container = containers[0]
    require(
        container.get("name") == WORKBENCH_APP,
        "Workbench container name mismatch",
    )
    require(
        container.get("image") == WORKBENCH_IMAGE,
        "Workbench image must use the approved version and OCI index digest",
    )
    require(
        container.get("imagePullPolicy") == "IfNotPresent",
        "Workbench imagePullPolicy must be IfNotPresent",
    )
    require(
        container.get("ports")
        == [
            {
                "name": "http",
                "containerPort": WORKBENCH_CONTAINER_PORT,
                "protocol": "TCP",
            }
        ],
        "Workbench container port mismatch",
    )

    container_security = container.get("securityContext", {})
    require(
        container_security.get("allowPrivilegeEscalation") is False,
        "Workbench must forbid privilege escalation",
    )
    require(
        container_security.get("readOnlyRootFilesystem") is True,
        "Workbench root filesystem must be read-only",
    )
    require(
        container_security.get("capabilities") == {"drop": ["ALL"]},
        "Workbench must drop all Linux capabilities",
    )
    require(
        container.get("resources")
        == {
            "requests": {"cpu": "25m", "memory": "32Mi"},
            "limits": {"cpu": "250m", "memory": "128Mi"},
        },
        "Workbench resource requests or limits mismatch",
    )

    for probe_name in ("startupProbe", "readinessProbe", "livenessProbe"):
        probe = container.get(probe_name, {})
        require(
            probe.get("httpGet") == {"path": "/healthz", "port": "http"},
            f"Workbench {probe_name} must use /healthz on the named HTTP port",
        )

    require(
        container.get("volumeMounts") == [{"name": "tmp", "mountPath": "/tmp"}],
        "Workbench container must mount only the temporary writable directory",
    )
    require(
        pod_spec.get("volumes")
        == [{"name": "tmp", "emptyDir": {"sizeLimit": "32Mi"}}],
        "Workbench must use only a bounded ephemeral temporary volume",
    )
    ok("Workbench hardened Deployment manifest is valid")

    require(
        service.get("kind") == "Service",
        "forge-yaml-workbench-service.yaml must be kind Service",
    )
    service_metadata = service.get("metadata", {})
    require(
        service_metadata.get("name") == WORKBENCH_APP,
        "Workbench Service name mismatch",
    )
    require(
        service_metadata.get("namespace") == WORKBENCH_NAMESPACE,
        "Workbench Service namespace mismatch",
    )
    service_spec = service.get("spec", {})
    require(
        service_spec.get("type") == "NodePort",
        "Workbench Service must be NodePort",
    )
    require(
        service_spec.get("selector") == {"app": WORKBENCH_APP},
        "Workbench Service selector mismatch",
    )
    require(
        service_spec.get("ports")
        == [
            {
                "name": "http",
                "port": 80,
                "targetPort": "http",
                "nodePort": WORKBENCH_NODEPORT,
                "protocol": "TCP",
            }
        ],
        "Workbench NodePort Service mismatch",
    )
    ok("Workbench NodePort Service manifest is valid")


def main() -> None:
    validate_restaurant_manifests()
    validate_prometheus_manifests()
    validate_metrics_server_manifests()
    validate_workbench_manifests()
    runpy.run_path(str(Path(__file__).with_name('validate-grafana.py')), run_name='__main__')
    print()
    print("All Kubernetes manifest checks passed.")


if __name__ == "__main__":
    main()
