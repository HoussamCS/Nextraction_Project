from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ingest():
    response = client.post("/ingest", json={"url": "http://example.com"})
    assert response.status_code == 202
    assert "job_id" in response.json()

def test_status():
    # Assuming a job_id of '123' for testing purposes
    response = client.get("/status/123")
    assert response.status_code == 200
    assert "status" in response.json()

def test_ask():
    response = client.post("/ask", json={"question": "What is the capital of France?"})
    assert response.status_code == 200
    assert "answer" in response.json()