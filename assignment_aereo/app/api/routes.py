from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import (
    BulkJobCreate,
    BulkJobResponse,
    JobStatusResponse,
    JobResultsResponse,
)
from app.services.job_service import job_service

router = APIRouter(prefix=settings.API_V1_STR)


@router.post(
    "/certificate-jobs",
    response_model=BulkJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a bulk certificate generation job",
    description="Submits a bulk certificate generation request. Validates data, creates a background job, and returns the job ID.",
)
def create_certificate_job(
    payload: BulkJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        job = job_service.create_job(db=db, payload=payload)
        background_tasks.add_task(job_service.process_job, job_id=job.id)

        status_url = f"{settings.API_V1_STR}/certificate-jobs/{job.id}"
        return BulkJobResponse(
            job_id=job.id,
            status=job.status,
            total_recipients=job.total_recipients,
            status_url=status_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create bulk certificate job: {str(e)}",
        )


@router.get(
    "/certificate-jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Check job status and progress",
    description="Retrieves status, recipient metrics, and overall progress percentage for a generation job.",
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    status_data = job_service.get_job_status(db=db, job_id=job_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return status_data


@router.get(
    "/certificate-jobs/{job_id}/results",
    response_model=JobResultsResponse,
    summary="Retrieve recipient-level results",
    description="Returns processing status, error messages, and download URLs for each recipient in a job.",
)
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    results_data = job_service.get_job_results(db=db, job_id=job_id)
    if not results_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return results_data


@router.get(
    "/certificate-jobs/{job_id}/certificates/{certificate_id}",
    summary="Download a generated certificate PDF",
    description="Streams the generated PDF file for a specific certificate ID.",
)
def download_certificate(job_id: str, certificate_id: str, db: Session = Depends(get_db)):
    try:
        file_path, filename = job_service.get_certificate_download(
            db=db, job_id=job_id, certificate_id=certificate_id
        )
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e).strip("'\""),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
