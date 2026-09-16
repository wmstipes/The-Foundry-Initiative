"""Bounded, deny-by-default subprocess and HTTP runners."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib import error, parse, request

from .constants import (
    ERROR_TEXT_LIMIT,
    HTTP_BODY_LIMIT,
    HTTP_TIMEOUT_SECONDS,
    KUBECTL_OUTPUT_LIMIT,
    KUBECTL_TIMEOUT_SECONDS,
    SERVICES,
    WORKLOADS,
)
from .models import CollectionError


class Operation(StrEnum):
    CURRENT_CONTEXT = "current-context"
    VERSION = "version"
    NODES = "nodes"
    DEPLOYMENT = "deployment"
    PODS = "pods"
    ENDPOINT_SLICES = "endpoint-slices"
    METRICS_API_SERVICE = "metrics-api-service"


class RunnerFailure(RuntimeError):
    def __init__(self, category: str, summary: str) -> None:
        super().__init__(summary)
        self.detail = CollectionError(category, summary)


def _bounded_error(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"(?i)(token|authorization|certificate-data|client-key-data)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
    text = " ".join(text.split())
    encoded = text.encode("utf-8")[:ERROR_TEXT_LIMIT]
    return encoded.decode("utf-8", errors="ignore") or "kubectl returned no diagnostic text"


class KubectlRunner:
    """Execute only the closed set of reviewed kubectl operations."""

    def __init__(self, kubeconfig: Path, context: str) -> None:
        self.kubeconfig = kubeconfig
        self.context = context

    def _command(self, operation: Operation, target: tuple[str, str] | None = None) -> list[str]:
        prefix = [
            "kubectl",
            "--kubeconfig", str(self.kubeconfig),
            "--context", self.context,
            f"--request-timeout={KUBECTL_TIMEOUT_SECONDS}s",
        ]
        if operation is Operation.CURRENT_CONTEXT:
            return prefix + ["config", "current-context"]
        if operation is Operation.VERSION:
            return prefix + ["version", "-o", "json"]
        if operation is Operation.NODES:
            return prefix + ["get", "nodes", "-o", "json"]
        if operation is Operation.METRICS_API_SERVICE:
            return prefix + ["get", "apiservice", "v1beta1.metrics.k8s.io", "-o", "json"]
        if target is None:
            raise RunnerFailure("unsafe-operation", "a fixed allowlisted target is required")
        namespace, name = target
        if operation is Operation.DEPLOYMENT:
            allowed = {(item.namespace, item.deployment) for item in WORKLOADS}
            if target not in allowed:
                raise RunnerFailure("unsafe-operation", "deployment target is not allowlisted")
            return prefix + ["get", "deployment", name, "-n", namespace, "-o", "json"]
        if operation is Operation.PODS:
            selectors = {(item.namespace, item.deployment): item.selector for item in WORKLOADS}
            if target not in selectors:
                raise RunnerFailure("unsafe-operation", "Pod target is not allowlisted")
            return prefix + ["get", "pods", "-n", namespace, "-l", selectors[target], "-o", "json"]
        if operation is Operation.ENDPOINT_SLICES:
            allowed = {(item.namespace, item.service) for item in SERVICES}
            if target not in allowed:
                raise RunnerFailure("unsafe-operation", "EndpointSlice target is not allowlisted")
            return prefix + [
                "get", "endpointslices", "-n", namespace,
                "-l", f"kubernetes.io/service-name={name}", "-o", "json",
            ]
        raise RunnerFailure("unsafe-operation", "kubectl operation is not allowlisted")

    def run_text(self, operation: Operation) -> str:
        try:
            return self._execute(self._command(operation)).decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise RunnerFailure("malformed-output", "kubectl returned non-UTF-8 text") from exc

    def run_json(self, operation: Operation, target: tuple[str, str] | None = None) -> Any:
        raw = self._execute(self._command(operation, target))
        try:
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RunnerFailure("malformed-json", "kubectl returned malformed JSON") from exc

    def _execute(self, command: list[str]) -> bytes:
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                timeout=KUBECTL_TIMEOUT_SECONDS,
                shell=False,
            )
        except OSError as exc:
            raise RunnerFailure("kubectl-unavailable", "kubectl is unavailable") from exc
        except subprocess.TimeoutExpired as exc:
            raise RunnerFailure("timeout", "kubectl exceeded its 10-second timeout") from exc
        if len(completed.stdout) > KUBECTL_OUTPUT_LIMIT:
            raise RunnerFailure("oversized-output", "kubectl output exceeded 2 MiB")
        if completed.returncode != 0:
            raise RunnerFailure("kubectl-error", _bounded_error(completed.stderr))
        return completed.stdout


class NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    body: bytes


class HttpRunner:
    """Perform bounded GETs to explicit operator-provided base URLs."""

    def __init__(self) -> None:
        self._opener = request.build_opener(request.ProxyHandler({}), NoRedirectHandler())

    @staticmethod
    def validate_base_url(base_url: str) -> str:
        candidate = base_url.rstrip("/")
        parsed = parse.urlsplit(candidate)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise RunnerFailure("invalid-url", "endpoint must be an absolute HTTP(S) URL")
        if parsed.username is not None or parsed.password is not None:
            raise RunnerFailure("invalid-url", "endpoint URL must not contain credentials")
        if parsed.path not in ("", "/"):
            raise RunnerFailure("invalid-url", "endpoint base URL must not contain a path")
        if parsed.query or parsed.fragment:
            raise RunnerFailure("invalid-url", "endpoint base URL must not contain a query or fragment")
        return candidate

    def get(self, base_url: str, path: str) -> HttpResponse:
        base = self.validate_base_url(base_url)
        uri = f"{base}{path}"
        try:
            with self._opener.open(uri, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = response.read(HTTP_BODY_LIMIT + 1)
                status = response.status
        except error.HTTPError as exc:
            raise RunnerFailure("http-status", f"HTTP GET returned status {exc.code}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise RunnerFailure("http-error", "HTTP GET failed or timed out") from exc
        if len(body) > HTTP_BODY_LIMIT:
            raise RunnerFailure("oversized-output", "HTTP response exceeded 64 KiB")
        return HttpResponse(status, body)
