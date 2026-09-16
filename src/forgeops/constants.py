"""Closed SignalForge collection scope and resource identities."""

from dataclasses import dataclass

SCHEMA_VERSION = "forgeops.snapshot/v1alpha1"
EXPECTED_CONTEXT = "kubernetes-admin@kubernetes"
KUBECTL_TIMEOUT_SECONDS = 10
HTTP_TIMEOUT_SECONDS = 5
COLLECTION_TIMEOUT_SECONDS = 90
KUBECTL_OUTPUT_LIMIT = 2 * 1024 * 1024
HTTP_BODY_LIMIT = 64 * 1024
ERROR_TEXT_LIMIT = 2 * 1024

EXPECTED_NODES = (
    "forge-head",
    "forge-node-01",
    "forge-node-02",
    "forge-node-03",
)


@dataclass(frozen=True, slots=True)
class WorkloadTarget:
    namespace: str
    deployment: str
    replicas: int
    selector: str
    image: str


WORKLOADS = (
    WorkloadTarget(
        "forge-restaurant", "restaurant-api", 3, "app=restaurant-api",
        "wmstipes/signalforge-restaurant-api:0.7.0",
    ),
    WorkloadTarget(
        "forge-observability", "prometheus", 1, "app=prometheus",
        "prom/prometheus:v3.13.2",
    ),
    WorkloadTarget(
        "forge-observability", "grafana", 1, "app=grafana",
        "grafana/grafana:13.2.1@sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283",
    ),
    WorkloadTarget(
        "forge-tools", "forge-yaml-workbench", 1, "app=forge-yaml-workbench",
        "wmstipes/signalforge-yaml-workbench:0.10.0@sha256:2afd73f4da3aa9862aabd0f532194da92bf37dbd196b03d9abfa1079f86e0206",
    ),
    WorkloadTarget(
        "kube-system", "metrics-server", 1, "k8s-app=metrics-server",
        "registry.k8s.io/metrics-server/metrics-server:v0.9.0",
    ),
)


@dataclass(frozen=True, slots=True)
class ServiceTarget:
    namespace: str
    service: str
    ready_endpoints: int


SERVICES = (
    ServiceTarget("forge-restaurant", "restaurant-api", 3),
    ServiceTarget("forge-observability", "prometheus", 1),
    ServiceTarget("forge-observability", "grafana", 1),
    ServiceTarget("forge-tools", "forge-yaml-workbench", 1),
)

RESTAURANT_ENDPOINTS = ("/version", "/health", "/ready", "/status")
WORKBENCH_ENDPOINTS = ("/healthz",)
