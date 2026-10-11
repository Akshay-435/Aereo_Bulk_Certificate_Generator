from datetime import datetime, date
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.config import settings

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RecipientCreate(BaseModel):
    name: str = Field(..., description="Full name of the recipient")
    email: str = Field(..., description="Email address of the recipient")
    certificate_id: str = Field(..., description="Unique certificate ID for this recipient")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Recipient name cannot be empty or whitespace only.")
        if len(s) > settings.MAX_STRING_LENGTH:
            raise ValueError(f"Recipient name exceeds maximum length of {settings.MAX_STRING_LENGTH} characters.")
        return s

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Recipient email cannot be empty.")
        if not EMAIL_REGEX.match(s):
            raise ValueError(f"Invalid email address format: '{v}'")
        if len(s) > settings.MAX_STRING_LENGTH:
            raise ValueError(f"Recipient email exceeds maximum length of {settings.MAX_STRING_LENGTH} characters.")
        return s

    @field_validator("certificate_id")
    @classmethod
    def validate_certificate_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Certificate ID cannot be empty or whitespace only.")
        if len(s) > settings.MAX_STRING_LENGTH:
            raise ValueError(f"Certificate ID exceeds maximum length of {settings.MAX_STRING_LENGTH} characters.")
        # Ensure certificate_id contains safe characters for filenames/URLs
        if not re.match(r"^[a-zA-Z0-9_.-]+$", s):
            raise ValueError("Certificate ID must contain only alphanumeric characters, dashes, underscores, and dots.")
        return s


class BulkJobCreate(BaseModel):
    event_name: str = Field(..., description="Name of the event or course")
    organization_name: str = Field(..., description="Name of the issuing organization")
    issue_date: str = Field(..., description="Issue date in YYYY-MM-DD format")
    recipients: List[RecipientCreate] = Field(..., description="List of recipient details")

    @field_validator("event_name", "organization_name")
    @classmethod
    def validate_non_empty_string(cls, v: str, info) -> str:
        s = v.strip()
        if not s:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace only.")
        if len(s) > settings.MAX_STRING_LENGTH:
            raise ValueError(f"Field '{info.field_name}' exceeds maximum length of {settings.MAX_STRING_LENGTH} characters.")
        return s

    @field_validator("issue_date")
    @classmethod
    def validate_issue_date(cls, v: str) -> str:
        s = v.strip()
        try:
            date.fromisoformat(s)
        except ValueError:
            raise ValueError("Invalid issue_date format. Must be a valid date in YYYY-MM-DD format.")
        return s

    @field_validator("recipients")
    @classmethod
    def validate_recipients_list(cls, v: List[RecipientCreate]) -> List[RecipientCreate]:
        if not v:
            raise ValueError("Recipients list cannot be empty.")
        if len(v) > settings.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds maximum limit of {settings.MAX_BATCH_SIZE} recipients.")

        # Check for duplicate certificate IDs within request payload
        seen_ids = set()
        duplicates = set()
        for r in v:
            if r.certificate_id in seen_ids:
                duplicates.add(r.certificate_id)
            seen_ids.add(r.certificate_id)

        if duplicates:
            raise ValueError(f"Duplicate certificate_id(s) found in request payload: {', '.join(sorted(duplicates))}")

        return v


class BulkJobResponse(BaseModel):
    job_id: str
    status: str
    total_recipients: int
    status_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_recipients: int
    pending_recipients: int
    processing_recipients: int
    successful_generations: int
    failed_generations: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None


class RecipientResultItem(BaseModel):
    name: str
    email: str
    certificate_id: str
    status: str
    error_message: Optional[str] = None
    certificate_download_url: Optional[str] = None


class JobResultsResponse(BaseModel):
    job_id: str
    total_recipients: int
    results: List[RecipientResultItem]
