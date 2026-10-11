from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="queued", index=True)
    total_recipients = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    recipients = relationship("CertificateRecipient", back_populates="job", cascade="all, delete-orphan")


class CertificateRecipient(Base):
    __tablename__ = "certificate_recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    certificate_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    job = relationship("GenerationJob", back_populates="recipients")
