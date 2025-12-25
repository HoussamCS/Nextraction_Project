"""
Tests for API routes.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.job_queue import job_queue

client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        """Test /health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestIngest:
    def test_ingest_valid_request(self):
        """Test POST /ingest with valid request"""
        payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": ["example.com"],
            "max_pages": 10,
            "max_depth": 1
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["accepted_pages"] == 1

    def test_ingest_missing_seed_urls(self):
        """Test POST /ingest without seed_urls"""
        payload = {
            "domain_allowlist": ["example.com"]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422  # Validation error

    def test_ingest_empty_domain_allowlist(self):
        """Test POST /ingest with empty domain_allowlist"""
        payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": []
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 400

    def test_ingest_default_max_pages(self):
        """Test POST /ingest uses default max_pages"""
        payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": ["example.com"]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 200


class TestStatus:
    def test_status_valid_job(self):
        """Test GET /status with valid job_id"""
        # Create a job first
        payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": ["example.com"]
        }
        ingest_response = client.post("/ingest", json=payload)
        job_id = ingest_response.json()["job_id"]

        # Get status
        response = client.get(f"/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] in ["queued", "running", "done", "failed"]
        assert data["pages_fetched"] >= 0
        assert data["pages_indexed"] >= 0

    def test_status_invalid_job(self):
        """Test GET /status with invalid job_id"""
        response = client.get("/status/nonexistent_job_id")
        assert response.status_code == 404


class TestAsk:
    def test_ask_job_not_found(self):
        """Test POST /ask with nonexistent job_id"""
        payload = {
            "job_id": "nonexistent",
            "question": "What is this about?"
        }
        response = client.post("/ask", json=payload)
        assert response.status_code == 404

    def test_ask_empty_question(self):
        """Test POST /ask with empty question"""
        # Create a job
        ingest_payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": ["example.com"]
        }
        ingest_response = client.post("/ingest", json=ingest_payload)
        job_id = ingest_response.json()["job_id"]

        # Try to ask with empty question
        ask_payload = {
            "job_id": job_id,
            "question": ""
        }
        response = client.post("/ask", json=ask_payload)
        assert response.status_code == 400

    def test_ask_requires_done_job(self):
        """Test POST /ask requires job to be in DONE state"""
        # Create a job (which starts in QUEUED state)
        ingest_payload = {
            "seed_urls": ["https://example.com"],
            "domain_allowlist": ["example.com"]
        }
        ingest_response = client.post("/ingest", json=ingest_payload)
        job_id = ingest_response.json()["job_id"]

        # Try to ask before job is done
        ask_payload = {
            "job_id": job_id,
            "question": "What is this?"
        }
        response = client.post("/ask", json=ask_payload)
        assert response.status_code == 400


class TestRootEndpoint:
    def test_root_returns_message(self):
        """Test GET / returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data