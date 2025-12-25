from fastapi.testclient import TestClient
from src.main import app
from src.services.rag_pipeline import RAGPipeline

client = TestClient(app)

def test_ingest():
    response = client.post("/ingest", json={"url": "http://example.com"})
    assert response.status_code == 200
    assert "job_id" in response.json()

def test_status():
    job_id = "test_job_id"
    response = client.get(f"/status/{job_id}")
    assert response.status_code == 200
    assert "status" in response.json()

def test_ask():
    response = client.post("/ask", json={"question": "What is the capital of France?"})
    assert response.status_code == 200
    assert "answer" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}