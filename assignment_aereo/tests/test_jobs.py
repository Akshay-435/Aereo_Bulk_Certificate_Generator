import os
import pytest
from app.services.job_service import job_service


def test_health_check(client):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_create_bulk_job_success(client, TestSessionLocal):
    """Test successful creation of a bulk generation job (Requirement 1 & 9)."""
    payload = {
        "event_name": "Python Backend Masterclass",
        "organization_name": "Aereo Tech Institute",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Aarav Sharma",
                "email": "aarav@example.com",
                "certificate_id": "CERT-101",
            },
            {
                "name": "Priya Patel",
                "email": "priya@example.com",
                "certificate_id": "CERT-102",
            },
        ],
    }

    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["total_recipients"] == 2
    assert f"/api/v1/certificate-jobs/{data['job_id']}" in data["status_url"]

    job_id = data["job_id"]

    # Process job synchronously using worker function
    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal)

    # Check job status endpoint (Requirement 8 & 12)
    status_response = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "completed"
    assert status_data["total_recipients"] == 2
    assert status_data["successful_generations"] == 2
    assert status_data["failed_generations"] == 0
    assert status_data["progress_percentage"] == 100.0
    assert status_data["completed_at"] is not None


def test_get_recipient_level_results(client, TestSessionLocal):
    """Test retrieving recipient-level results (Requirement 14)."""
    payload = {
        "event_name": "FastAPI Workshop",
        "organization_name": "Dev Academy",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Rohan Gupta",
                "email": "rohan@example.com",
                "certificate_id": "CERT-201",
            }
        ],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]

    # Execute processing
    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal)

    results_resp = client.get(f"/api/v1/certificate-jobs/{job_id}/results")
    assert results_resp.status_code == 200
    res_data = results_resp.json()
    assert res_data["job_id"] == job_id
    assert res_data["total_recipients"] == 1
    assert len(res_data["results"]) == 1

    item = res_data["results"][0]
    assert item["name"] == "Rohan Gupta"
    assert item["email"] == "rohan@example.com"
    assert item["certificate_id"] == "CERT-201"
    assert item["status"] == "success"
    assert item["error_message"] is None
    assert f"/api/v1/certificate-jobs/{job_id}/certificates/CERT-201" in item["certificate_download_url"]


def test_download_generated_certificate(client, TestSessionLocal):
    """Test downloading a generated PDF certificate (Requirement 15)."""
    payload = {
        "event_name": "Web Architecture",
        "organization_name": "Engineering League",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Sneha Reddy",
                "email": "sneha@example.com",
                "certificate_id": "CERT-301",
            }
        ],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]

    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal)

    download_resp = client.get(f"/api/v1/certificate-jobs/{job_id}/certificates/CERT-301")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in download_resp.headers.get("content-disposition", "").lower()
    assert len(download_resp.content) > 1000  # PDF binary content returned


def test_database_persistence(client, db_session, TestSessionLocal):
    """Test that job state remains persisted across database reads (Requirement 19)."""
    payload = {
        "event_name": "Persistence Check",
        "organization_name": "Database Corp",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Vikram Singh",
                "email": "vikram@example.com",
                "certificate_id": "CERT-PERSIST-1",
            }
        ],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]
    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal)

    # Open a fresh independent DB session to query persisted state
    new_db = TestSessionLocal()
    try:
        status_data = job_service.get_job_status(db=new_db, job_id=job_id)
        assert status_data is not None
        assert status_data["status"] == "completed"
        assert status_data["successful_generations"] == 1
    finally:
        new_db.close()
