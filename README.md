# Bulk Certificate Generator

A small FastAPI service that accepts one generation request for many recipients, creates one PDF certificate per recipient, and reports progress and individual failures.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

The default SQLite database is `data/certificates.db`; generated PDFs are written under `data/generated/`. Set `DATABASE_URL` in `.env` to use another relational database supported by SQLAlchemy.

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the Tailwind-powered web interface. API documentation is available at http://127.0.0.1:8000/docs.

## API usage

Create a job:

```bash
curl -X POST http://127.0.0.1:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Python Foundations",
    "issuer": "Northstar Academy",
    "issue_date": "2026-10-10",
    "recipients": [
      {"name": "Ada Lovelace", "email": "ada@example.com", "course": "Python", "completion_date": "2026-10-09"}
    ]
  }'
```

The response contains a job ID, counters, status, and certificate result records. Poll `GET /api/jobs/{job_id}` to track processing. A completed certificate includes a `download_url`; retrieve it with `GET /api/certificates/{certificate_id}`.

## Tests

```bash
pytest
```

Tests cover job creation, Pydantic input validation, PDF generation and retrieval, status counters, and isolation of an individual generation failure.

## Design decisions

- FastAPI `BackgroundTasks` keeps the HTTP request short while avoiding extra infrastructure for this focused service. SQLite stores job and recipient state durably. A production deployment with multiple workers or very large batches should move `process_job` to a dedicated queue such as Celery/RQ and use shared object storage for PDFs.
- Each recipient is persisted as a certificate record before processing. Generation errors are caught per record, allowing the remaining recipients to finish. Jobs end as `completed`, `partial`, or `failed` with success and failure counters.
- A small standard-library PDF writer creates a single predefined landscape A4 template. The template contains the recipient name, course, issuer, completion date, issue date, and certificate ID, keeping setup independent of native PDF packages.
- The browser UI uses Tailwind via its CDN for a zero-build frontend. The API remains the source of truth and can be used independently of the UI.
