from pathlib import Path
import sys

import yaml


RESTAURANT_MANIFEST_DIR = Path("k8s/fastapi-restaurant")
PROMETHEUS_MANIFEST_DIR = Path("k8s/prometheus")

RESTAURANT_NAMESPACE = "forge-restaurant"
RESTAURANT_APP = "restaurant-api"
EXPECTED_IMAGE_PREFIX = "wmstipes/signalforge-restaurant-api:"
EXPECTED_NODEPORT = 30080
EXPECTED_VERSION = "0.6.0"

PROMETHEUS_NAMESPACE = "forge-observability"
PROMETHEUS_APP = "prometheus"
PROMETHEUS_IMAGE = "prom/prometheus:v3.13.2"
PROMETHEUS_ROLE = "prometheus-restaurant-pod-reader"

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
    "prometheus-deployment.yaml",
    "prometheus-service.yaml",
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
    except Exception as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"{path} did not parse into a YAML object")

    return data


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
    require(container.get("image", "").startswith(EXPECTED_IMAGE_PREFIX), "Restaurant container image prefix mismatch")
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

    try:
        prometheus_config = yaml.safe_load(prometheus_text)
    except Exception as exc:
        fail(f"Embedded prometheus.yml could not be parsed: {exc}")

    global_config = prometheus_config.get("global", {})
    require(global_config.get("scrape_interval") == "30s", "Prometheus scrape interval must be 30s")
    require(global_config.get("scrape_timeout") == "10s", "Prometheus scrape timeout must be 10s")

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

    require(deployment.get("kind") == "Deployment", "prometheus-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("name") == PROMETHEUS_APP, "Prometheus Deployment name mismatch")
    require(deployment.get("metadata", {}).get("namespace") == PROMETHEUS_NAMESPACE, "Prometheus Deployment namespace mismatch")
    require(deployment.get("spec", {}).get("replicas") == 1, "Prometheus must use one replica")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    require(pod_spec.get("serviceAccountName") == PROMETHEUS_APP, "Prometheus Deployment ServiceAccount mismatch")
    containers = pod_spec.get("containers", [])
    require(len(containers) == 1, "Prometheus Deployment should have exactly one container")
    container = containers[0]
    require(container.get("name") == PROMETHEUS_APP, "Prometheus container name mismatch")
    require(container.get("image") == PROMETHEUS_IMAGE, "Prometheus image must be pinned to the approved version")
    require("--storage.tsdb.retention.time=48h" in container.get("args", []), "Prometheus retention time must be 48h")
    require("--storage.tsdb.retention.size=750MB" in container.get("args", []), "Prometheus retention size must be 750MB")
    require("readinessProbe" in container, "Prometheus container missing readinessProbe")
    require("livenessProbe" in container, "Prometheus container missing livenessProbe")

    resources = container.get("resources", {})
    require(resources.get("requests", {}).get("cpu") == "100m", "Prometheus CPU request must be 100m")
    require(resources.get("requests", {}).get("memory") == "256Mi", "Prometheus memory request must be 256Mi")
    require(resources.get("limits", {}).get("cpu") == "500m", "Prometheus CPU limit must be 500m")
    require(resources.get("limits", {}).get("memory") == "512Mi", "Prometheus memory limit must be 512Mi")

    storage_volumes = [volume for volume in pod_spec.get("volumes", []) if volume.get("name") == "storage"]
    require(len(storage_volumes) == 1, "Prometheus Deployment must define one storage volume")
    require(storage_volumes[0].get("emptyDir", {}).get("sizeLimit") == "1Gi", "Prometheus emptyDir size limit must be 1Gi")
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


def main() -> None:
    validate_restaurant_manifests()
    validate_prometheus_manifests()
    print("")
    print("All Kubernetes manifest checks passed.")


if __name__ == "__main__":
    main()
