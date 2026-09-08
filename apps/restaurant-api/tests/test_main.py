from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "restaurant-api"
    assert body["version"] == "0.7.0"


def test_analyze():
    response = client.post(
        "/analyze",
        json={
            "incident": "ImagePullBackOff after deployment",
            "service": "restaurant-api",
            "environment": "signalforge-lab",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "restaurant-api"
    assert body["environment"] == "signalforge-lab"
    assert "likely_causes" in body
    assert "recommended_next_steps" in body


def test_metrics():
    client.get("/health")
    client.get("/status")
    client.get("/metrics")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "restaurant_api_info" in response.text
    assert "restaurant_api_analyze_enabled" in response.text
    assert "restaurant_api_requests_total" in response.text
    assert "restaurant_api_request_duration_seconds_bucket" in response.text
    assert (
        'restaurant_api_requests_total{method="GET",path="/status",status="200",traffic="application"}'
        in response.text
    )
    assert (
        'restaurant_api_requests_total{method="GET",path="/health",status="200",traffic="synthetic"}'
        in response.text
    )
    assert (
        'restaurant_api_requests_total{method="GET",path="/metrics",status="200",traffic="synthetic"}'
        in response.text
    )
    assert (
        'restaurant_api_request_duration_seconds_count{method="GET",path="/status",'
        'status="200",traffic="application"}'
        in response.text
    )


def test_unmatched_paths_use_bounded_metric_label():
    missing_path = "/missing/12345"

    response = client.get(missing_path)
    assert response.status_code == 404

    metrics_response = client.get("/metrics")

    assert (
        'restaurant_api_requests_total{method="GET",path="unmatched",status="404",traffic="application"}'
        in metrics_response.text
    )
    assert missing_path not in metrics_response.text
