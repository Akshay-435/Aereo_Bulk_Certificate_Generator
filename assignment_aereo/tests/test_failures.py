import pytest
from unittest.mock import MagicMock
from app.services.job_service import job_service
from app.services.certificate_service import CertificateService


def test_partial_failure_processing_continues(client, TestSessionLocal, monkeypatch):
    """Test that when one recipient certificate generation fails, processing continues for others

    and job status becomes 'completed_with_errors' (Requirement 10, 11, 13, 14).
    """
    payload = {
        "event_name": "Failure Simulation Workshop",
        "organization_name": "QA Institute",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Success User One",
                "email": "user1@example.com",
                "certificate_id": "CERT-FAIL-01",
            },
            {
                "name": "Failing User Two",
                "email": "user2@example.com",
                "certificate_id": "CERT-FAIL-02",  # Will be mocked to fail
            },
            {
                "name": "Success User Three",
                "email": "user3@example.com",
                "certificate_id": "CERT-FAIL-03",
            },
        ],
    }

    resp = client.post("/api/v1/certificate-jobs", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # Create mock CertificateService that raises an Exception only for CERT-FAIL-02
    real_service = CertificateService()

    def mock_generate(job_id, recipient_name, event_name, organization_name, issue_date, certificate_id):
        if certificate_id == "CERT-FAIL-02":
            raise RuntimeError("Simulated PDF Rendering Engine Error")
        return real_service.generate_certificate_file(
            job_id=job_id,
            recipient_name=recipient_name,
            event_name=event_name,
            organization_name=organization_name,
            issue_date=issue_date,
            certificate_id=certificate_id,
        )

    mock_cert_service = MagicMock()
    mock_cert_service.generate_certificate_file.side_effect = mock_generate

    # Run job processing with mock service
    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal, cert_service=mock_cert_service)

    # Verify status
    status_resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "completed_with_errors"
    assert status_data["total_recipients"] == 3
    assert status_data["successful_generations"] == 2
    assert status_data["failed_generations"] == 1
    assert status_data["progress_percentage"] == 100.0

    # Verify results list
    results_resp = client.get(f"/api/v1/certificate-jobs/{job_id}/results")
    assert results_resp.status_code == 200
    res_items = results_resp.json()["results"]
    assert len(res_items) == 3

    item2 = next(r for r in res_items if r["certificate_id"] == "CERT-FAIL-02")
    assert item2["status"] == "failed"
    assert "Simulated PDF Rendering Engine Error" in item2["error_message"]
    assert item2["certificate_download_url"] is None

    # Verify successful items can still be downloaded
    item1 = next(r for r in res_items if r["certificate_id"] == "CERT-FAIL-01")
    assert item1["status"] == "success"
    assert item1["certificate_download_url"] is not None


def test_reject_download_for_failed_certificate(client, TestSessionLocal):
    """Test that attempting to download a failed certificate returns 404 (Requirement 17)."""
    payload = {
        "event_name": "Failed Download Test",
        "organization_name": "QA Institute",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Bad Recipient",
                "email": "bad@example.com",
                "certificate_id": "CERT-BAD-DOWNLOAD",
            }
        ],
    }

    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]

    mock_cert_service = MagicMock()
    mock_cert_service.generate_certificate_file.side_effect = RuntimeError("Generation failed")

    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal, cert_service=mock_cert_service)

    # Attempt download of failed certificate
    download_resp = client.get(f"/api/v1/certificate-jobs/{job_id}/certificates/CERT-BAD-DOWNLOAD")
    assert download_resp.status_code == 404
    assert "Download unavailable" in download_resp.json()["detail"]


def test_full_failure_job_status(client, TestSessionLocal):
    """Test job status when all recipients fail."""
    payload = {
        "event_name": "Full Failure Test",
        "organization_name": "QA Institute",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Fail 1",
                "email": "fail1@example.com",
                "certificate_id": "CERT-ALL-FAIL-1",
            },
            {
                "name": "Fail 2",
                "email": "fail2@example.com",
                "certificate_id": "CERT-ALL-FAIL-2",
            },
        ],
    }

    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]

    mock_cert_service = MagicMock()
    mock_cert_service.generate_certificate_file.side_effect = Exception("System Crash")

    job_service.process_job(job_id=job_id, db_factory=TestSessionLocal, cert_service=mock_cert_service)

    status_resp = client.get(f"/api/v1/certificate-jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "failed"
    assert status_resp.json()["failed_generations"] == 2


def test_path_traversal_prevention(setup_test_environment):
    """Test path traversal rejection in certificate_service (Security requirement)."""
    service = CertificateService(output_dir=setup_test_environment)
    with pytest.raises((ValueError, Exception)):
        service.generate_certificate_file(
            job_id="job123",
            recipient_name="Attacker",
            event_name="Exploit",
            organization_name="Hacker Org",
            issue_date="2026-10-10",
            certificate_id="../../etc/passwd",
        )
