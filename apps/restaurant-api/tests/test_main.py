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
    assert "version" in body


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