from datetime import datetime, timezone
import os
import socket
from typing import List

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest


app = FastAPI(
    title="SignalForge Restaurant API",
    description="A containerized FastAPI service for the SignalForge Kubernetes lab.",
    version="0.6.0",
)

APP_VERSION = os.getenv("APP_VERSION", "0.6.0")
RESTAURANT_NAME = os.getenv("RESTAURANT_NAME", "SignalForge Grill")
DISTRICT_NAME = os.getenv("DISTRICT_NAME", "SignalForge Restaurant District")
FEATURE_ANALYZE_ENABLED = os.getenv("FEATURE_ANALYZE_ENABLED", "false").lower() == "true"

REQUEST_COUNTER = Counter(
    "restaurant_api_requests_total",
    "Total HTTP requests handled by the Restaurant API.",
    ["method", "path", "status"],
)

APP_INFO = Gauge(
    "restaurant_api_info",
    "Restaurant API application metadata.",
    ["version", "restaurant", "district"],
)

ANALYZE_ENABLED_GAUGE = Gauge(
    "restaurant_api_analyze_enabled",
    "Whether the analyze feature is enabled. 1 means enabled, 0 means disabled.",
)

APP_INFO.labels(
    version=APP_VERSION,
    restaurant=RESTAURANT_NAME,
    district=DISTRICT_NAME,
).set(1)

ANALYZE_ENABLED_GAUGE.set(1 if FEATURE_ANALYZE_ENABLED else 0)


@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    response = await call_next(request)

    REQUEST_COUNTER.labels(
        method=request.method,
        path=request.url.path,
        status=str(response.status_code),
    ).inc()

    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)



class AnalyzeRequest(BaseModel):
    incident: str = Field(
        ...,
        min_length=5,
        description="Short description of the incident or symptom.",
    )
    service: str = Field(
        default="unknown",
        description="Service, app, or workload involved.",
    )
    environment: str = Field(
        default="lab",
        description="Environment where the issue is happening.",
    )


class AnalyzeResponse(BaseModel):
    service: str
    environment: str
    summary: str
    likely_causes: List[str]
    recommended_next_steps: List[str]
    severity: str
    confidence: float
    hostname: str
    version: str


@app.get("/")
def root():
    return {
        "message": f"Welcome to the {DISTRICT_NAME}.",
        "restaurant": RESTAURANT_NAME,
        "version": APP_VERSION,
        "hostname": socket.gethostname(),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "hostname": socket.gethostname()}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "restaurant-api"}


@app.get("/version")
def version():
    return {
        "app": "restaurant-api",
        "version": APP_VERSION,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/menu")
def menu():
    return {
        "restaurant": RESTAURANT_NAME,
        "specials": [
            "Kubernetes Kettle Soup",
            "Pod Replica Pasta",
            "Calico Network Nachos",
            "Containerd Club Sandwich",
        ],
    }


@app.get("/status")
def status():
    return {
        "status": "open",
        "message": f"{RESTAURANT_NAME} is serving traffic from Kubernetes.",
        "district": DISTRICT_NAME,
        "version": APP_VERSION,
        "analyze_enabled": FEATURE_ANALYZE_ENABLED,
        "hostname": socket.gethostname(),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if not FEATURE_ANALYZE_ENABLED:
        return AnalyzeResponse(
            service=request.service,
            environment=request.environment,
            summary="Analyze feature is currently disabled by configuration.",
            likely_causes=[
                "FEATURE_ANALYZE_ENABLED is set to false",
                "The endpoint is deployed but gated by a feature flag",
            ],
            recommended_next_steps=[
                "Set FEATURE_ANALYZE_ENABLED=true in the ConfigMap",
                "Restart or roll out the Deployment so Pods receive the updated environment variable",
            ],
            severity="info",
            confidence=1.0,
            hostname=socket.gethostname(),
            version=APP_VERSION,
        )

    text = request.incident.lower()

    likely_causes = []
    recommended_next_steps = []
    severity = "medium"
    confidence = 0.65

    if "crashloop" in text or "crashloopbackoff" in text:
        likely_causes.extend([
            "Application process is exiting after startup",
            "Missing environment variable or bad startup configuration",
            "Container command or entrypoint may be failing",
        ])
        recommended_next_steps.extend([
            "Run kubectl describe pod for recent events",
            "Run kubectl logs for the failing container",
            "Check ConfigMap and Secret references",
            "Verify the container command and startup arguments",
        ])
        severity = "high"
        confidence = 0.8

    elif "imagepull" in text or "image pull" in text or "imagepullbackoff" in text:
        likely_causes.extend([
            "Image name or tag is incorrect",
            "Registry credentials are missing or invalid",
            "The image may not exist for the node architecture",
        ])
        recommended_next_steps.extend([
            "Check the image name and tag in the Deployment",
            "Confirm the image exists in the registry",
            "Verify the image supports linux/arm64",
            "Inspect pod events with kubectl describe pod",
        ])
        severity = "high"
        confidence = 0.82

    elif "pending" in text:
        likely_causes.extend([
            "Scheduler cannot place the Pod",
            "Insufficient CPU or memory resources",
            "Node selector, affinity, or taints may prevent scheduling",
        ])
        recommended_next_steps.extend([
            "Run kubectl describe pod to inspect scheduling events",
            "Check node capacity with kubectl describe nodes",
            "Review requests, limits, tolerations, and node selectors",
        ])
        severity = "medium"
        confidence = 0.72

    elif "network" in text or "dns" in text or "service" in text:
        likely_causes.extend([
            "Service selector may not match Pod labels",
            "CoreDNS or CNI networking may be unhealthy",
            "NetworkPolicy may be blocking traffic",
        ])
        recommended_next_steps.extend([
            "Check Service selectors and Pod labels",
            "Test DNS from a temporary curl Pod",
            "Check CoreDNS and Calico Pods",
            "Review any NetworkPolicy objects in the namespace",
        ])
        severity = "medium"
        confidence = 0.7

    else:
        likely_causes.extend([
            "The symptom does not match a known rule yet",
            "More logs, events, or resource details are needed",
        ])
        recommended_next_steps.extend([
            "Collect kubectl describe output",
            "Collect recent application logs",
            "Check Deployment rollout status",
            "Check node and namespace events",
        ])
        severity = "low"
        confidence = 0.45

    return AnalyzeResponse(
        service=request.service,
        environment=request.environment,
        summary=f"Initial analysis for {request.service} in {request.environment}.",
        likely_causes=likely_causes,
        recommended_next_steps=recommended_next_steps,
        severity=severity,
        confidence=confidence,
        hostname=socket.gethostname(),
        version=APP_VERSION,
    )
