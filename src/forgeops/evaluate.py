"""Deterministically evaluate normalized ForgeOps evidence."""

from __future__ import annotations

from typing import Any

from .constants import EXPECTED_NODES, SERVICES, WORKLOADS
from .models import CheckResult, EvaluatedSnapshot, Evidence, RawSnapshot, Status


def _result(snapshot: RawSnapshot, check_id: str, status: Status, observation: str, source: str,
            expected: str | None = None, observed: str | None = None,
            error_category: str | None = None) -> CheckResult:
    return CheckResult(
        check_id, status, observation, source, snapshot.collected_at_utc,
        expected, observed, error_category,
    )


def _mapping(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def evaluate(snapshot: RawSnapshot) -> EvaluatedSnapshot:
    by_id = {item.evidence_id: item for item in snapshot.evidence}
    checks: list[CheckResult] = []

    context = by_id.get("context")
    if context is None:
        context = Evidence("context", "kubectl config current-context")
    if context.error or context.value != snapshot.context:
        checks.append(_result(
            snapshot, "context", Status.UNKNOWN, "Exact context validation failed",
            context.source, snapshot.context, str(context.value or "unavailable"),
            context.error.category if context.error else "context-mismatch",
        ))
        return EvaluatedSnapshot(snapshot.schema, snapshot.collected_at_utc, snapshot.context, tuple(checks))
    checks.append(_result(
        snapshot, "context", Status.PASS, "Exact Kubernetes context matched",
        context.source, snapshot.context, str(context.value),
    ))

    version = by_id.get("kubernetes.version", Evidence("kubernetes.version", "kubectl version -o json"))
    value = _mapping(version.value)
    client = _mapping(value.get("clientVersion")) if value else None
    server = _mapping(value.get("serverVersion")) if value else None
    if version.error or not client or not server or not client.get("gitVersion") or not server.get("gitVersion"):
        checks.append(_result(
            snapshot, "kubernetes.version", Status.UNKNOWN, "Kubernetes versions are unavailable",
            version.source, error_category=version.error.category if version.error else "unexpected-shape",
        ))
    else:
        observed = f"client={client['gitVersion']}, server={server['gitVersion']}"
        checks.append(_result(snapshot, "kubernetes.version", Status.PASS, "Kubernetes versions collected", version.source, observed=observed))

    nodes = by_id.get("nodes", Evidence("nodes", "kubectl get nodes -o json"))
    node_items = _mapping(nodes.value)
    items = node_items.get("items") if node_items else None
    if nodes.error or not isinstance(items, list):
        for name in EXPECTED_NODES:
            checks.append(_result(
                snapshot, f"node.{name}", Status.UNKNOWN, "Node evidence is unavailable", nodes.source,
                expected="one identity with Ready=True",
                error_category=nodes.error.category if nodes.error else "unexpected-shape",
            ))
    else:
        for name in EXPECTED_NODES:
            matches = [item for item in items if _mapping(item) and _mapping(item.get("metadata")) and item["metadata"].get("name") == name]
            ready = []
            if len(matches) == 1:
                status = _mapping(matches[0].get("status"))
                conditions = status.get("conditions") if status else None
                if isinstance(conditions, list):
                    ready = [condition for condition in conditions if _mapping(condition) and condition.get("type") == "Ready"]
            if len(matches) != 1 or len(ready) != 1:
                checks.append(_result(
                    snapshot, f"node.{name}", Status.UNKNOWN, "Node identity or Ready condition is incomplete",
                    nodes.source, "one identity with one Ready condition", f"identities={len(matches)}, readyConditions={len(ready)}",
                    "incomplete-evidence",
                ))
            else:
                observed = str(ready[0].get("status"))
                status_value = Status.PASS if observed == "True" else Status.FAIL
                checks.append(_result(
                    snapshot, f"node.{name}", status_value,
                    "Node is Ready" if status_value is Status.PASS else "Node is not Ready",
                    nodes.source, "Ready=True", f"Ready={observed}",
                ))

    for target in WORKLOADS:
        evidence_id = f"deployment.{target.namespace}.{target.deployment}"
        deployment = by_id.get(evidence_id, Evidence(evidence_id, f"Deployment {target.namespace}/{target.deployment}"))
        value = _mapping(deployment.value)
        metadata = _mapping(value.get("metadata")) if value else None
        spec = _mapping(value.get("spec")) if value else None
        state = _mapping(value.get("status")) if value else None
        fields = (spec.get("replicas") if spec else None, state.get("updatedReplicas", 0) if state else None,
                  state.get("readyReplicas", 0) if state else None, state.get("availableReplicas", 0) if state else None)
        identity_ok = metadata and metadata.get("name") == target.deployment and metadata.get("namespace") == target.namespace
        if deployment.error or not identity_ok or any(not isinstance(item, int) for item in fields):
            checks.append(_result(
                snapshot, evidence_id, Status.UNKNOWN, "Deployment evidence is unavailable or malformed", deployment.source,
                expected=f"{target.replicas} desired/updated/ready/available",
                error_category=deployment.error.category if deployment.error else "unexpected-shape",
            ))
        else:
            observed = "/".join(str(item) for item in fields)
            images = spec.get("images", [])
            healthy = all(item == target.replicas for item in fields) and images == [target.image]
            checks.append(_result(
                snapshot, evidence_id, Status.PASS if healthy else Status.FAIL,
                "Deployment replica state matches" if healthy else "Deployment replica state does not match",
                deployment.source,
                f"{target.replicas}/{target.replicas}/{target.replicas}/{target.replicas}, images={[target.image]}",
                f"{observed}, images={images}",
            ))

    for target in WORKLOADS:
        evidence_id = f"pods.{target.namespace}.{target.deployment}"
        pods = by_id.get(evidence_id, Evidence(evidence_id, f"Pods for {target.namespace}/{target.deployment}"))
        value = _mapping(pods.value)
        items = value.get("items") if value else None
        if pods.error or not isinstance(items, list):
            checks.append(_result(
                snapshot, evidence_id, Status.UNKNOWN, "Pod evidence is unavailable", pods.source,
                error_category=pods.error.category if pods.error else "unexpected-shape",
            ))
            continue
        names = [
            (_mapping(item.get("metadata")) or {}).get("name")
            for item in items if _mapping(item)
        ]
        identities_valid = (
            len(names) == len(items)
            and all(isinstance(name, str) and name for name in names)
            and len(set(names)) == len(names)
        )
        if not identities_valid:
            checks.append(_result(
                snapshot, evidence_id, Status.UNKNOWN, "Pod identities are incomplete or duplicated", pods.source,
                expected=f"{target.replicas} unique Pod identities", observed=f"identities={len(set(names))}",
                error_category="incomplete-evidence",
            ))
        else:
            pod_count_healthy = len(items) == target.replicas
            checks.append(_result(
                snapshot, evidence_id, Status.PASS if pod_count_healthy else Status.FAIL,
                "Selected Pod count matches" if pod_count_healthy else "Selected Pod count does not match",
                pods.source, str(target.replicas), str(len(items)),
            ))
        for pod in sorted(items, key=lambda item: str((_mapping(item.get("metadata")) or {}).get("name", "")) if _mapping(item) else ""):
            item = _mapping(pod)
            metadata = _mapping(item.get("metadata")) if item else None
            spec = _mapping(item.get("spec")) if item else None
            state = _mapping(item.get("status")) if item else None
            name = metadata.get("name") if metadata else None
            statuses = state.get("containerStatuses") if state else None
            containers = spec.get("containers") if spec else None
            if (
                not name
                or not isinstance(statuses, list)
                or not statuses
                or not isinstance(containers, list)
                or not containers
            ):
                checks.append(_result(
                    snapshot, f"pod.{target.namespace}.{name or 'unknown'}", Status.UNKNOWN,
                    "Pod evidence is incomplete", pods.source, error_category="unexpected-shape",
                ))
                continue
            status_maps = [_mapping(status) for status in statuses]
            container_maps = [_mapping(container) for container in containers]
            valid_statuses = all(
                status is not None
                and isinstance(status.get("ready"), bool)
                and isinstance(status.get("restartCount"), int)
                and status.get("restartCount") >= 0
                and isinstance(status.get("imageID"), str)
                for status in status_maps
            )
            valid_containers = all(
                container is not None and isinstance(container.get("image"), str)
                for container in container_maps
            )
            if not valid_statuses or not valid_containers:
                checks.append(_result(
                    snapshot, f"pod.{target.namespace}.{name}", Status.UNKNOWN,
                    "Pod container evidence is malformed", pods.source,
                    error_category="unexpected-shape",
                ))
                continue
            phase = state.get("phase")
            ready = all(status["ready"] is True for status in status_maps if status)
            restarts = sum(status["restartCount"] for status in status_maps if status)
            configured = [container["image"] for container in container_maps if container]
            runtime = [status["imageID"] for status in status_maps if status]
            configured_match = configured == [target.image]
            digest_match = True
            for image in configured:
                if isinstance(image, str) and "@sha256:" in image:
                    digest = image.split("@", 1)[1]
                    digest_match = digest_match and any(isinstance(image_id, str) and image_id.endswith(digest) for image_id in runtime)
            status_value = Status.PASS
            observation = "Pod is Running, ready, and has not restarted"
            if phase != "Running" or not ready or not configured_match or not digest_match:
                status_value = Status.FAIL
                observation = "Pod runtime state does not match expectations"
            elif restarts > 0:
                status_value = Status.WARN
                observation = "Pod is ready but has restarted"
            checks.append(_result(
                snapshot, f"pod.{target.namespace}.{name}", status_value, observation, pods.source,
                f"phase=Running, ready=true, restarts=0, configuredImages={[target.image]}, "
                "pinned digest matched when present",
                f"phase={phase}, ready={str(ready).lower()}, restarts={restarts}, "
                f"configuredImages={configured}, runtimeImageIDs={runtime}, "
                f"configuredMatched={str(configured_match).lower()}, "
                f"digestMatched={str(digest_match).lower()}",
            ))

    for target in sorted(SERVICES, key=lambda item: (item.namespace, item.service)):
        evidence_id = f"routing.{target.namespace}.{target.service}"
        routing = by_id.get(evidence_id, Evidence(evidence_id, f"EndpointSlices for {target.namespace}/{target.service}"))
        value = _mapping(routing.value)
        items = value.get("items") if value else None
        if routing.error or not isinstance(items, list):
            checks.append(_result(
                snapshot, evidence_id, Status.UNKNOWN, "EndpointSlice evidence is unavailable", routing.source,
                error_category=routing.error.category if routing.error else "unexpected-shape",
            ))
            continue
        endpoints: list[Any] = []
        malformed = False
        for item in items:
            item_map = _mapping(item)
            endpoint_list = item_map.get("endpoints") if item_map else None
            if not isinstance(endpoint_list, list):
                malformed = True
                break
            endpoints.extend(endpoint_list)
        if malformed:
            checks.append(_result(snapshot, evidence_id, Status.UNKNOWN, "EndpointSlice evidence is malformed", routing.source, error_category="unexpected-shape"))
            continue
        states = [(_mapping((_mapping(endpoint) or {}).get("conditions")) or {}).get("ready") for endpoint in endpoints]
        ready_count = sum(state is True for state in states)
        not_ready = sum(state is False for state in states)
        unknown = sum(state is None for state in states)
        healthy = len(items) > 0 and ready_count == target.ready_endpoints and not_ready == 0 and unknown == 0
        checks.append(_result(
            snapshot, evidence_id, Status.PASS if healthy else Status.FAIL,
            "Service routing matches" if healthy else "Service routing does not match",
            routing.source, f"ready={target.ready_endpoints}, notReady=0, unknown=0",
            f"slices={len(items)}, ready={ready_count}, notReady={not_ready}, unknown={unknown}",
        ))

    metrics = by_id.get("metrics-api-service", Evidence("metrics-api-service", "APIService v1beta1.metrics.k8s.io"))
    value = _mapping(metrics.value)
    state = _mapping(value.get("status")) if value else None
    conditions = state.get("conditions") if state else None
    available = [item for item in conditions if _mapping(item) and item.get("type") == "Available"] if isinstance(conditions, list) else []
    if metrics.error or len(available) != 1:
        checks.append(_result(
            snapshot, "metrics-api-service", Status.UNKNOWN, "Metrics APIService evidence is incomplete", metrics.source,
            error_category=metrics.error.category if metrics.error else "incomplete-evidence",
        ))
    else:
        observed = str(available[0].get("status"))
        checks.append(_result(
            snapshot, "metrics-api-service", Status.PASS if observed == "True" else Status.FAIL,
            "Metrics APIService is available" if observed == "True" else "Metrics APIService is unavailable",
            metrics.source, "Available=True", f"Available={observed}",
        ))

    for evidence in snapshot.evidence:
        if not evidence.evidence_id.startswith("http."):
            continue
        expected_fields: dict[str, Any]
        if evidence.evidence_id.endswith("/version"):
            expected_fields = {"app": "restaurant-api", "version": "0.7.0"}
        elif evidence.evidence_id.endswith("/health"):
            expected_fields = {"status": "healthy"}
        elif evidence.evidence_id.endswith("/ready"):
            expected_fields = {"status": "ready", "service": "restaurant-api"}
        elif evidence.evidence_id.endswith("/status"):
            expected_fields = {
                "status": "open", "district": "SignalForge Restaurant District",
                "version": "0.7.0", "analyze_enabled": True,
            }
        else:
            expected_fields = {"body": "ok"}
        value = _mapping(evidence.value)
        selected = _mapping(value.get("selected")) if value else None
        if evidence.error or not value or not selected:
            checks.append(_result(
                snapshot, evidence.evidence_id, Status.UNKNOWN, "HTTP evidence is unavailable", evidence.source,
                error_category=evidence.error.category if evidence.error else "unexpected-shape",
            ))
            continue
        healthy = value.get("status_code") == 200 and all(selected.get(key) == expected for key, expected in expected_fields.items())
        checks.append(_result(
            snapshot, evidence.evidence_id, Status.PASS if healthy else Status.FAIL,
            "HTTP endpoint matched" if healthy else "HTTP endpoint did not match",
            evidence.source, f"status=200, fields={expected_fields}",
            f"status={value.get('status_code')}, fields={selected}",
        ))

    return EvaluatedSnapshot(snapshot.schema, snapshot.collected_at_utc, snapshot.context, tuple(checks))
