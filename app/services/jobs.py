from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Certificate, CertificateStatus, GenerationJob, JobStatus
from app.services.certificate import generate_certificate


def process_job(job_id: UUID) -> None:
    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        if job is None:
            return
        job.status = JobStatus.PROCESSING
        db.commit()

        certificates = db.scalars(select(Certificate).where(Certificate.job_id == job_id)).all()
        for certificate in certificates:
            try:
                output_path = Path(settings.generated_dir) / str(job_id) / f"{certificate.id}.pdf"
                generate_certificate(
                    output_path=output_path,
                    recipient_name=certificate.recipient_name,
                    course=certificate.course,
                    issuer=job.issuer,
                    title=job.title,
                    issue_date=job.issue_date,
                    completion_date=certificate.completion_date,
                    certificate_id=certificate.id,
                )
                certificate.status = CertificateStatus.COMPLETED
                certificate.file_path = str(output_path)
                job.succeeded += 1
            except Exception as error:  # keep processing the remaining recipients
                certificate.status = CertificateStatus.FAILED
                certificate.error_message = str(error)
                job.failed += 1
            db.commit()

        if job.succeeded == job.total:
            job.status = JobStatus.COMPLETED
        elif job.succeeded:
            job.status = JobStatus.PARTIAL
        else:
            job.status = JobStatus.FAILED
        db.commit()
