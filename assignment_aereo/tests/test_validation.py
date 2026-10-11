import pytest


def test_missing_required_top_level_fields(client):
    """Test validation when top-level fields are missing."""
    payload = {
        "event_name": "Python Workshop",
        # organization_name missing
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Ananya Roy",
                "email": "ananya@example.com",
                "certificate_id": "CERT-999",
            }
        ],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data or "detail" in data


def test_invalid_email_handling(client):
    """Test rejection of malformed email addresses (Requirement 3)."""
    payload = {
        "event_name": "Email Validation Test",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Invalid User",
                "email": "invalid-email-address-format",
                "certificate_id": "CERT-BAD-EMAIL",
            }
        ],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_empty_recipients_list(client):
    """Test rejection when recipients list is empty (Requirement 4)."""
    payload = {
        "event_name": "Empty Recipients Test",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": [],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_duplicate_certificate_ids_within_request(client):
    """Test rejection when duplicate certificate IDs are present in payload (Requirement 4)."""
    payload = {
        "event_name": "Duplicate ID Test",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "User One",
                "email": "user1@example.com",
                "certificate_id": "DUP-CERT-01",
            },
            {
                "name": "User Two",
                "email": "user2@example.com",
                "certificate_id": "DUP-CERT-01",  # Duplicate ID
            },
        ],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_maximum_batch_size_enforcement(client):
    """Test enforcement of max batch size limit (Requirement 5)."""
    # Note: setup_test_environment monkeypatches MAX_BATCH_SIZE to 10
    recipients = [
        {
            "name": f"Recipient {i}",
            "email": f"user{i}@example.com",
            "certificate_id": f"CERT-BATCH-{i}",
        }
        for i in range(15)  # 15 exceeds limit of 10
    ]
    payload = {
        "event_name": "Max Batch Size Test",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": recipients,
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_invalid_issue_date_format(client):
    """Test rejection of unsupported date format."""
    payload = {
        "event_name": "Date Test",
        "organization_name": "Tech Corp",
        "issue_date": "10/10/2026",  # Not YYYY-MM-DD
        "recipients": [
            {
                "name": "Date User",
                "email": "date@example.com",
                "certificate_id": "CERT-DATE-1",
            }
        ],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_whitespace_only_fields(client):
    """Test rejection of whitespace-only string inputs."""
    payload = {
        "event_name": "   ",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "   ",
                "email": "user@example.com",
                "certificate_id": "CERT-WS-1",
            }
        ],
    }
    response = client.post("/api/v1/certificate-jobs", json=payload)
    assert response.status_code == 422


def test_unknown_job_id(client):
    """Test 404 response for non-existent job ID (Requirement 16)."""
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    resp1 = client.get(f"/api/v1/certificate-jobs/{fake_job_id}")
    assert resp1.status_code == 404

    resp2 = client.get(f"/api/v1/certificate-jobs/{fake_job_id}/results")
    assert resp2.status_code == 404

    resp3 = client.get(f"/api/v1/certificate-jobs/{fake_job_id}/certificates/CERT-001")
    assert resp3.status_code == 404


def test_unknown_certificate_id_in_valid_job(client, TestSessionLocal):
    """Test 404 response for non-existent certificate ID within an existing job (Requirement 16)."""
    payload = {
        "event_name": "Unknown Cert Test",
        "organization_name": "Tech Corp",
        "issue_date": "2026-10-10",
        "recipients": [
            {
                "name": "Valid User",
                "email": "valid@example.com",
                "certificate_id": "CERT-EXISTS-1",
            }
        ],
    }
    resp = client.post("/api/v1/certificate-jobs", json=payload)
    job_id = resp.json()["job_id"]

    resp_download = client.get(f"/api/v1/certificate-jobs/{job_id}/certificates/NON-EXISTENT-CERT")
    assert resp_download.status_code == 404
