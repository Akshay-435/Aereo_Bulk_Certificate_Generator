import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import GenerationJob, CertificateRecipient
from app.schemas import BulkJobCreate
from app.services.certificate_service import certificate_service, CertificateService


class JobService:
    def create_job(self, db: Session, payload: BulkJobCreate) -> GenerationJob:
        """Creates and persists a new bulk certificate generation job with recipient records."""
        job = GenerationJob(
            event_name=payload.event_name,
            organization_name=payload.organization_name,
            issue_date=payload.issue_date,
            status="queued",
            total_recipients=len(payload.recipients),
        )
        db.add(job)
        db.flush()  # Populates job.id (UUID)

        for rec in payload.recipients:
            recipient_record = CertificateRecipient(
                job_id=job.id,
                name=rec.name,
                email=rec.email,
                certificate_id=rec.certificate_id,
                status="pending",
            )
            db.add(recipient_record)

        db.commit()
        db.refresh(job)
        return job

    def process_job(
        self,
        job_id: str,
        db_factory=SessionLocal,
        cert_service: Optional[CertificateService] = None,
    ) -> None:
        """Background worker function that processes recipients individually and updates job progress.

        Catches errors per recipient so one failure does not halt remaining recipients.
        """
        service = cert_service or certificate_service
        db: Session = db_factory()

        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                return

            job.status = "processing"
            db.commit()

            recipients = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()

            for recipient in recipients:
                recipient.status = "processing"
                db.commit()

                try:
                    file_path = service.generate_certificate_file(
                        job_id=job.id,
                        recipient_name=recipient.name,
                        event_name=job.event_name,
                        organization_name=job.organization_name,
                        issue_date=job.issue_date,
                        certificate_id=recipient.certificate_id,
                    )
                    recipient.status = "success"
                    recipient.file_path = file_path
                    recipient.error_message = None
                except Exception as e:
                    recipient.status = "failed"
                    recipient.file_path = None
                    recipient.error_message = f"Certificate generation failed: {str(e)}"

                db.commit()

            # Refresh recipient counts to determine final job status
            recipients = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()
            total = len(recipients)
            success_count = sum(1 for r in recipients if r.status == "success")
            failed_count = sum(1 for r in recipients if r.status == "failed")

            if total == 0:
                job.status = "completed"
            elif failed_count == 0:
                job.status = "completed"
            elif failed_count == total:
                job.status = "failed"
            else:
                job.status = "completed_with_errors"

            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        finally:
            db.close()

    def get_job_status(self, db: Session, job_id: str) -> Optional[Dict[str, Any]]:
        """Calculates and returns status details and progress percentage for a job."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        recipients = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()
        total = job.total_recipients or len(recipients)

        pending_count = sum(1 for r in recipients if r.status == "pending")
        processing_count = sum(1 for r in recipients if r.status == "processing")
        success_count = sum(1 for r in recipients if r.status == "success")
        failed_count = sum(1 for r in recipients if r.status == "failed")

        completed_recipients = success_count + failed_count
        progress = round((completed_recipients / total) * 100.0, 2) if total > 0 else 100.0

        return {
            "job_id": job.id,
            "status": job.status,
            "total_recipients": total,
            "pending_recipients": pending_count,
            "processing_recipients": processing_count,
            "successful_generations": success_count,
            "failed_generations": failed_count,
            "progress_percentage": progress,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }

    def get_job_results(self, db: Session, job_id: str) -> Optional[Dict[str, Any]]:
        """Returns recipient-level status and download URLs for a job."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        recipients = db.query(CertificateRecipient).filter(CertificateRecipient.job_id == job_id).all()
        results = []

        for r in recipients:
            download_url = None
            if r.status == "success":
                download_url = f"{settings.API_V1_STR}/certificate-jobs/{job_id}/certificates/{r.certificate_id}"

            results.append({
                "name": r.name,
                "email": r.email,
                "certificate_id": r.certificate_id,
                "status": r.status,
                "error_message": r.error_message,
                "certificate_download_url": download_url,
            })

        return {
            "job_id": job.id,
            "total_recipients": len(recipients),
            "results": results,
        }

    def get_certificate_download(self, db: Session, job_id: str, certificate_id: str) -> Tuple[str, str]:
        """Validates existence of generated certificate and returns safe file path & filename.

        Raises KeyError if job/certificate recipient does not exist.
        Raises ValueError if certificate is not generated or file is missing on disk.
        """
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise KeyError(f"Job with ID '{job_id}' not found.")

        recipient = (
            db.query(CertificateRecipient)
            .filter(CertificateRecipient.job_id == job_id, CertificateRecipient.certificate_id == certificate_id)
            .first()
        )
        if not recipient:
            raise KeyError(f"Certificate with ID '{certificate_id}' not found in job '{job_id}'.")

        if recipient.status != "success" or not recipient.file_path:
            raise ValueError(f"Certificate '{certificate_id}' generation status is '{recipient.status}'. Download unavailable.")

        if not os.path.isfile(recipient.file_path):
            raise ValueError(f"Generated PDF file for certificate '{certificate_id}' is missing from storage.")

        download_filename = f"certificate_{certificate_id}.pdf"
        return recipient.file_path, download_filename


job_service = JobService()
