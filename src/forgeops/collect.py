"""Collect the fixed SignalForge evidence set without evaluating health."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Callable

from .constants import (
    COLLECTION_TIMEOUT_SECONDS,
    EXPECTED_NODES,
    RESTAURANT_ENDPOINTS,
    SCHEMA_VERSION,
    SERVICES,
    WORKBENCH_ENDPOINTS,
    WORKLOADS,
)
from .models import CollectionError, Evidence, RawSnapshot, utc_now
from .runners import HttpRunner, KubectlRunner, Operation, RunnerFailure


def _error_evidence(evidence_id: str, source: str, error: CollectionError) -> Evidence:
    return Evidence(evidence_id=evidence_id, source=source, error=error)


def _select_http(path: str, body: bytes) -> dict[str, Any]:
    if path == "/healthz":
        return {"body": body.decode("utf-8", errors="replace").strip()}
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerFailure("malformed-json", "HTTP endpoint returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise RunnerFailure("unexpected-shape", "HTTP endpoint did not return an object")
    fields = {
        "/version": ("app", "version"),
        "/health": ("status",),
        "/ready": ("status", "service"),
        "/status": ("status", "district", "version", "analyze_enabled"),
    }[path]
    return {field: payload.get(field) for field in fields}


def _as_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunnerFailure("unexpected-shape", "kubectl JSON did not contain the expected object")
    return value


def _normalize_kubernetes(operation: Operation, payload: Any) -> dict[str, Any]:
    """Discard all fields outside the accepted normalized evidence model."""

    value = _as_mapping(payload)
    if operation is Operation.VERSION:
        client = _as_mapping(value.get("clientVersion"))
        server = _as_mapping(value.get("serverVersion"))
        return {
            "clientVersion": {"gitVersion": client.get("gitVersion")},
            "serverVersion": {"gitVersion": server.get("gitVersion")},
        }
    if operation is Operation.NODES:
        items = value.get("items")
        if not isinstance(items, list):
            raise RunnerFailure("unexpected-shape", "Node list did not contain items")
        return {"items": [
            {
                "metadata": {"name": _as_mapping(item).get("metadata", {}).get("name")},
                "status": {"conditions": [
                    {"type": condition.get("type"), "status": condition.get("status"), "reason": condition.get("reason")}
                    for condition in _as_mapping(item).get("status", {}).get("conditions", [])
                    if isinstance(condition, dict) and condition.get("type") == "Ready"
                ]},
            }
            for item in items
            if _as_mapping(item).get("metadata", {}).get("name") in EXPECTED_NODES
        ]}
    if operation is Operation.DEPLOYMENT:
        metadata = _as_mapping(value.get("metadata"))
        spec = _as_mapping(value.get("spec"))
        state = _as_mapping(value.get("status"))
        template = _as_mapping(spec.get("template")) if isinstance(spec.get("template"), dict) else {}
        pod_spec = _as_mapping(template.get("spec")) if isinstance(template.get("spec"), dict) else {}
        containers = pod_spec.get("containers", [])
        return {
            "metadata": {"namespace": metadata.get("namespace"), "name": metadata.get("name")},
            "spec": {
                "replicas": spec.get("replicas"),
                "images": [item.get("image") for item in containers if isinstance(item, dict)],
            },
            "status": {
                "updatedReplicas": state.get("updatedReplicas", 0),
                "readyReplicas": state.get("readyReplicas", 0),
                "availableReplicas": state.get("availableReplicas", 0),
            },
        }
    if operation is Operation.PODS:
        items = value.get("items")
        if not isinstance(items, list):
            raise RunnerFailure("unexpected-shape", "Pod list did not contain items")
        selected = []
        for raw_item in items:
            item = _as_mapping(raw_item)
            metadata = _as_mapping(item.get("metadata"))
            spec = _as_mapping(item.get("spec"))
            state = _as_mapping(item.get("status"))
            containers = spec.get("containers", [])
            statuses = state.get("containerStatuses", [])
            selected.append({
                "metadata": {"name": metadata.get("name")},
                "spec": {
                    "nodeName": spec.get("nodeName"),
                    "containers": [
                        {"image": container.get("image")}
                        for container in containers if isinstance(container, dict)
                    ],
                },
                "status": {
                    "phase": state.get("phase"),
                    "containerStatuses": [
                        {
                            "ready": status.get("ready"),
                            "restartCount": status.get("restartCount", 0),
                            "imageID": status.get("imageID"),
                            "waitingReason": (status.get("state", {}).get("waiting") or {}).get("reason"),
                            "terminatedReason": (status.get("state", {}).get("terminated") or {}).get("reason"),
                        }
                        for status in statuses if isinstance(status, dict)
                    ],
                },
            })
        return {"items": selected}
    if operation is Operation.ENDPOINT_SLICES:
        items = value.get("items")
        if not isinstance(items, list):
            raise RunnerFailure("unexpected-shape", "EndpointSlice list did not contain items")
        return {"items": [
            {"endpoints": [
                {"conditions": {"ready": (endpoint.get("conditions") or {}).get("ready")}}
                for endpoint in _as_mapping(item).get("endpoints", [])
                if isinstance(endpoint, dict)
            ]}
            for item in items
        ]}
    if operation is Operation.METRICS_API_SERVICE:
        state = _as_mapping(value.get("status"))
        return {"status": {"conditions": [
            {"type": condition.get("type"), "status": condition.get("status"), "reason": condition.get("reason")}
            for condition in state.get("conditions", [])
            if isinstance(condition, dict) and condition.get("type") == "Available"
        ]}}
    raise RunnerFailure("unsafe-operation", "normalization operation is not allowlisted")


class Collector:
    def __init__(
        self,
        kubectl: KubectlRunner,
        http: HttpRunner | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.kubectl = kubectl
        self.http = http or HttpRunner()
        self.clock = clock

    def collect(
        self,
        restaurant_url: str | None = None,
        workbench_url: str | None = None,
    ) -> RawSnapshot:
        started = self.clock()
        collected_at = utc_now()
        evidence: list[Evidence] = []

        def within_budget() -> None:
            if self.clock() - started >= COLLECTION_TIMEOUT_SECONDS:
                raise RunnerFailure("collection-timeout", "collection exceeded its 90-second budget")

        try:
            resolved = self.kubectl.run_text(Operation.CURRENT_CONTEXT)
            evidence.append(Evidence("context", "kubectl config current-context", resolved))
        except RunnerFailure as exc:
            evidence.append(_error_evidence("context", "kubectl config current-context", exc.detail))
            return RawSnapshot(SCHEMA_VERSION, collected_at, self.kubectl.context, tuple(evidence))
        if resolved != self.kubectl.context:
            evidence[-1] = Evidence(
                "context", "kubectl config current-context", resolved,
                CollectionError("context-mismatch", "resolved context did not exactly match the requested context"),
            )
            return RawSnapshot(SCHEMA_VERSION, collected_at, self.kubectl.context, tuple(evidence))

        operations: list[tuple[str, str, Operation, tuple[str, str] | None]] = [
            ("kubernetes.version", "kubectl version -o json", Operation.VERSION, None),
            ("nodes", "kubectl get nodes -o json", Operation.NODES, None),
        ]
        operations.extend(
            (
                f"deployment.{target.namespace}.{target.deployment}",
                f"Deployment {target.namespace}/{target.deployment}",
                Operation.DEPLOYMENT,
                (target.namespace, target.deployment),
            )
            for target in WORKLOADS
        )
        operations.extend(
            (
                f"pods.{target.namespace}.{target.deployment}",
                f"Pods for {target.namespace}/{target.deployment}",
                Operation.PODS,
                (target.namespace, target.deployment),
            )
            for target in WORKLOADS
        )
        operations.extend(
            (
                f"routing.{target.namespace}.{target.service}",
                f"EndpointSlices for {target.namespace}/{target.service}",
                Operation.ENDPOINT_SLICES,
                (target.namespace, target.service),
            )
            for target in SERVICES
        )
        operations.append((
            "metrics-api-service", "APIService v1beta1.metrics.k8s.io",
            Operation.METRICS_API_SERVICE, None,
        ))

        for evidence_id, source, operation, target in operations:
            try:
                within_budget()
                value = _normalize_kubernetes(operation, self.kubectl.run_json(operation, target))
                within_budget()
                evidence.append(Evidence(evidence_id, source, value))
            except RunnerFailure as exc:
                evidence.append(_error_evidence(evidence_id, source, exc.detail))
            except (AttributeError, TypeError, ValueError) as exc:
                evidence.append(_error_evidence(
                    evidence_id, source,
                    CollectionError("unexpected-shape", "kubectl JSON did not match the expected shape"),
                ))

        endpoint_sets = (
            ("restaurant-api", restaurant_url, RESTAURANT_ENDPOINTS),
            ("forge-yaml-workbench", workbench_url, WORKBENCH_ENDPOINTS),
        )
        for application, base_url, paths in endpoint_sets:
            if base_url is None:
                continue
            for path in paths:
                evidence_id = f"http.{application}{path}"
                try:
                    within_budget()
                    response = self.http.get(base_url, path)
                    selected = _select_http(path, response.body)
                    within_budget()
                    evidence.append(Evidence(
                        evidence_id,
                        f"explicit HTTP GET {application}{path}",
                        {"status_code": response.status_code, "selected": selected},
                    ))
                except RunnerFailure as exc:
                    evidence.append(_error_evidence(
                        evidence_id, f"explicit HTTP GET {application}{path}", exc.detail,
                    ))

        return RawSnapshot(SCHEMA_VERSION, collected_at, self.kubectl.context, tuple(evidence))


def validate_kubeconfig(path_text: str) -> Path:
    """Resolve an explicit kubeconfig without exposing its path in output."""

    path = Path(path_text).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RunnerFailure("invalid-kubeconfig", "kubeconfig is not an accessible regular file") from exc
    if not resolved.is_file():
        raise RunnerFailure("invalid-kubeconfig", "kubeconfig is not an accessible regular file")
    return resolved
