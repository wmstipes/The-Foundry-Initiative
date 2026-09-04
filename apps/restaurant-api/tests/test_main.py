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
    assert body["version"] == "0.6.0"


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
    client.get("/status")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "restaurant_api_info" in response.text
    assert "restaurant_api_analyze_enabled" in response.text
    assert "restaurant_api_requests_total" in response.text
