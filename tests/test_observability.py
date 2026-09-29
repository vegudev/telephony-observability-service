from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"

def test_metrics_scrape():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"telephony_events_total" in response.content

def test_telemetry_ingestion():
    payload = {
        "call_sid": "CA_test_12345",
        "sip_status": "200 OK",
        "event_type": "MEDIA_STREAMING",
        "latency_ms": 42.5,
        "jitter_ms": 1.2,
        "packet_loss_pct": 0.05
    }
    response = client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"
