import os
import pytest
from pypdf import PdfReader

from app.services.certificate_service import certificate_service
from app.templates.certificate_template import generate_pdf_certificate


def test_pdf_generation_file_creation(setup_test_environment):
    """Test direct PDF generation using ReportLab template (Requirement 6)."""
    output_dir = setup_test_environment
    file_path = os.path.join(output_dir, "test_cert_direct.pdf")

    generate_pdf_certificate(
        output_path=file_path,
        recipient_name="Aditya Verma",
        event_name="Cloud Security Workshop",
        organization_name="Security Org",
        issue_date="2026-10-10",
        certificate_id="CERT-DIRECT-001",
    )

    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 1000  # Non-empty PDF file


def test_pdf_content_text_extraction(setup_test_environment):
    """Test that generated PDF contains recipient-specific text (Requirement 7)."""
    output_dir = setup_test_environment
    file_path = os.path.join(output_dir, "test_cert_content.pdf")

    recipient_name = "Kavya Swaminathan"
    event_name = "Advanced Machine Learning"
    organization_name = "AI Research Lab"
    issue_date = "2026-10-10"
    certificate_id = "CERT-AI-999"

    generate_pdf_certificate(
        output_path=file_path,
        recipient_name=recipient_name,
        event_name=event_name,
        organization_name=organization_name,
        issue_date=issue_date,
        certificate_id=certificate_id,
    )

    # Read and inspect generated PDF content using pypdf
    reader = PdfReader(file_path)
    assert len(reader.pages) == 1

    page = reader.pages[0]
    extracted_text = page.extract_text()

    assert recipient_name in extracted_text
    assert event_name in extracted_text
    assert organization_name.upper() in extracted_text or organization_name in extracted_text
    assert issue_date in extracted_text
    assert certificate_id in extracted_text
    assert "CERTIFICATE OF COMPLETION" in extracted_text


def test_certificate_service_generation(setup_test_environment):
    """Test certificate_service wrapper method and safe file path generation."""
    file_path = certificate_service.generate_certificate_file(
        job_id="job-12345",
        recipient_name="Rahul Nair",
        event_name="System Design",
        organization_name="Tech Academy",
        issue_date="2026-10-10",
        certificate_id="CERT-SYS-101",
    )

    assert os.path.exists(file_path)
    assert "job-12345_CERT-SYS-101.pdf" in file_path
