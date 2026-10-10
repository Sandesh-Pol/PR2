from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import Certificate, GenerationJob
from app.schemas import CertificateResult, GenerationRequest, JobResponse
from app.services.jobs import process_job


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Bulk Certificate Generator", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def certificate_result(certificate: Certificate, request: Request) -> CertificateResult:
    return CertificateResult(
        id=certificate.id,
        recipient_name=certificate.recipient_name,
        recipient_email=certificate.recipient_email,
        course=certificate.course,
        completion_date=certificate.completion_date,
        status=certificate.status,
        download_url=(str(request.url_for("download_certificate", certificate_id=certificate.id)) if certificate.file_path else None),
        error_message=certificate.error_message,
    )


def job_response(job: GenerationJob, request: Request) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        issuer=job.issuer,
        issue_date=job.issue_date,
        status=job.status,
        total=job.total,
        succeeded=job.succeeded,
        failed=job.failed,
        created_at=job.created_at,
        updated_at=job.updated_at,
        certificates=[certificate_result(item, request) for item in job.certificates],
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.post("/api/jobs", response_model=JobResponse, status_code=202)
def create_job(payload: GenerationRequest, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    job = GenerationJob(
        title=payload.title,
        issuer=payload.issuer,
        issue_date=payload.issue_date,
        total=len(payload.recipients),
    )
    job.certificates = [
        Certificate(
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            course=recipient.course,
            completion_date=recipient.completion_date,
        )
        for recipient in payload.recipients
    ]
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    return job_response(job, request)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, request: Request, db: Session = Depends(get_db)) -> JobResponse:
    job = db.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return job_response(job, request)


@app.get("/api/certificates/{certificate_id}", name="download_certificate")
def download_certificate(certificate_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None or not certificate.file_path:
        raise HTTPException(status_code=404, detail="Generated certificate not found")
    path = Path(certificate.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Generated certificate file is unavailable")
    return FileResponse(path, media_type="application/pdf", filename=f"{certificate.recipient_name}.pdf")
