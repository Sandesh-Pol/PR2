from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CertificateStatus, JobStatus


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    course: str = Field(min_length=1, max_length=200)
    completion_date: date


class GenerationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    issuer: str = Field(min_length=1, max_length=200)
    issue_date: date
    recipients: list[RecipientInput] = Field(min_length=1, max_length=1000)


class CertificateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_name: str
    recipient_email: EmailStr
    course: str
    completion_date: date
    status: CertificateStatus
    download_url: str | None = None
    error_message: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    issuer: str
    issue_date: date
    status: JobStatus
    total: int
    succeeded: int
    failed: int
    created_at: datetime
    updated_at: datetime
    certificates: list[CertificateResult]
