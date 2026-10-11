import os

from app.config import settings
from app.templates.certificate_template import generate_pdf_certificate


class CertificateService:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or settings.OUTPUT_DIR

    def generate_certificate_file(
        self,
        job_id: str,
        recipient_name: str,
        event_name: str,
        organization_name: str,
        issue_date: str,
        certificate_id: str,
    ) -> str:
        """Generates a PDF certificate for a recipient and returns the stored file path.

        Prevents path traversal by resolving absolute paths.
        """
        base_dir = os.path.abspath(self.output_dir)
        os.makedirs(base_dir, exist_ok=True)

        # Sanitize and validate certificate_id against path traversal
        if os.path.basename(certificate_id) != certificate_id or ".." in certificate_id or "/" in certificate_id or "\\" in certificate_id:
            raise ValueError(f"Security error: Invalid certificate ID '{certificate_id}' contains forbidden path traversal characters.")

        safe_cert_id = os.path.basename(certificate_id)
        filename = f"{job_id}_{safe_cert_id}.pdf"
        file_path = os.path.abspath(os.path.join(base_dir, filename))

        # Security check: ensure target file resides inside base output directory
        if not file_path.startswith(base_dir):
            raise ValueError(f"Security error: Certificate path '{file_path}' is outside base directory '{base_dir}'.")

        # Generate the PDF file
        generate_pdf_certificate(
            output_path=file_path,
            recipient_name=recipient_name,
            event_name=event_name,
            organization_name=organization_name,
            issue_date=issue_date,
            certificate_id=certificate_id,
        )

        return file_path


certificate_service = CertificateService()
