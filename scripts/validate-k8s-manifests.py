from pathlib import Path
import sys
import yaml

MANIFEST_DIR = Path("k8s/fastapi-restaurant")
EXPECTED_NAMESPACE = "forge-restaurant"
EXPECTED_APP = "restaurant-api"
EXPECTED_IMAGE_PREFIX = "wmstipes/signalforge-restaurant-api:"
EXPECTED_NODEPORT = 30080
EXPECTED_VERSION = "0.5.0"

REQUIRED_FILES = [
    "namespace.yaml",
    "restaurant-api-config.yaml",
    "restaurant-api-deployment.yaml",
    "restaurant-api-service.yaml",
    "restaurant-api-nodeport.yaml",
]

def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)

def ok(message: str) -> None:
    print(f"OK: {message}")

def load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        fail(f"{path} could not be parsed as YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"{path} did not parse into a YAML object")

    return data

def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)

def main() -> None:
    require(MANIFEST_DIR.exists(), f"{MANIFEST_DIR} does not exist")

    for filename in REQUIRED_FILES:
        require((MANIFEST_DIR / filename).exists(), f"Missing required manifest: {filename}")
    ok("All required manifest files exist")

    namespace = load_yaml(MANIFEST_DIR / "namespace.yaml")
    config = load_yaml(MANIFEST_DIR / "restaurant-api-config.yaml")
    deployment = load_yaml(MANIFEST_DIR / "restaurant-api-deployment.yaml")
    service = load_yaml(MANIFEST_DIR / "restaurant-api-service.yaml")
    nodeport = load_yaml(MANIFEST_DIR / "restaurant-api-nodeport.yaml")

    require(namespace.get("kind") == "Namespace", "namespace.yaml must be kind Namespace")
    require(namespace.get("metadata", {}).get("name") == EXPECTED_NAMESPACE, "Namespace must be forge-restaurant")
    ok("Namespace manifest is valid")

    require(config.get("kind") == "ConfigMap", "restaurant-api-config.yaml must be kind ConfigMap")
    require(config.get("metadata", {}).get("namespace") == EXPECTED_NAMESPACE, "ConfigMap namespace mismatch")
    require(config.get("data", {}).get("APP_VERSION") == EXPECTED_VERSION, "ConfigMap APP_VERSION mismatch")
    require(config.get("data", {}).get("FEATURE_ANALYZE_ENABLED") == "true", "FEATURE_ANALYZE_ENABLED should be true")
    ok("ConfigMap manifest is valid")

    require(deployment.get("kind") == "Deployment", "restaurant-api-deployment.yaml must be kind Deployment")
    require(deployment.get("metadata", {}).get("namespace") == EXPECTED_NAMESPACE, "Deployment namespace mismatch")
    require(deployment.get("metadata", {}).get("name") == EXPECTED_APP, "Deployment name mismatch")

    template = deployment.get("spec", {}).get("template", {})
    pod_labels = template.get("metadata", {}).get("labels", {})
    require(pod_labels.get("app") == EXPECTED_APP, "Deployment Pod label app mismatch")

    containers = template.get("spec", {}).get("containers", [])
    require(len(containers) == 1, "Deployment should have exactly one container")

    container = containers[0]
    require(container.get("name") == EXPECTED_APP, "Container name mismatch")
    require(container.get("image", "").startswith(EXPECTED_IMAGE_PREFIX), "Container image prefix mismatch")
    require("readinessProbe" in container, "Container missing readinessProbe")
    require("livenessProbe" in container, "Container missing livenessProbe")
    require("resources" in container, "Container missing resources block")
    ok("Deployment manifest is valid")

    require(service.get("kind") == "Service", "restaurant-api-service.yaml must be kind Service")
    require(service.get("metadata", {}).get("namespace") == EXPECTED_NAMESPACE, "Service namespace mismatch")
    require(service.get("spec", {}).get("type") == "ClusterIP", "Internal service must be ClusterIP")
    require(service.get("spec", {}).get("selector", {}).get("app") == EXPECTED_APP, "Internal service selector mismatch")
    ok("Internal Service manifest is valid")

    require(nodeport.get("kind") == "Service", "restaurant-api-nodeport.yaml must be kind Service")
    require(nodeport.get("metadata", {}).get("namespace") == EXPECTED_NAMESPACE, "NodePort service namespace mismatch")
    require(nodeport.get("spec", {}).get("type") == "NodePort", "External service must be NodePort")
    require(nodeport.get("spec", {}).get("selector", {}).get("app") == EXPECTED_APP, "NodePort service selector mismatch")

    ports = nodeport.get("spec", {}).get("ports", [])
    require(len(ports) == 1, "NodePort service should have one port entry")
    require(ports[0].get("nodePort") == EXPECTED_NODEPORT, "NodePort must be 30080")
    ok("NodePort Service manifest is valid")

    print("")
    print("All Kubernetes manifest checks passed.")

if __name__ == "__main__":
    main()
