from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings.generated_dir = tmp_path / "generated"
    settings.generated_dir.mkdir()
    with TestClient(app) as test_client:
        yield test_client


def payload():
    return {
        "title": "Python Foundations",
        "issuer": "Northstar Academy",
        "issue_date": "2026-10-10",
        "recipients": [
            {"name": "Ada Lovelace", "email": "ada@example.com", "course": "Python", "completion_date": "2026-10-09"},
            {"name": "Grace Hopper", "email": "grace@example.com", "course": "Python", "completion_date": "2026-10-09"},
        ],
    }


def test_create_job_and_track_completion(client):
    response = client.post("/api/jobs", json=payload())
    assert response.status_code == 202
    job = response.json()
    assert job["total"] == 2

    status = client.get(f"/api/jobs/{job['id']}")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["status"] == "completed"
    assert status_data["succeeded"] == 2
    assert {item["status"] for item in status_data["certificates"]} == {"completed"}


def test_input_validation(client):
    invalid = payload()
    invalid["recipients"][0]["email"] = "not-an-email"
    assert client.post("/api/jobs", json=invalid).status_code == 422

    invalid = payload()
    invalid["recipients"] = []
    assert client.post("/api/jobs", json=invalid).status_code == 422


def test_individual_failure_does_not_stop_other_certificates(client, monkeypatch):
    from app.services import jobs

    original = jobs.generate_certificate

    def fail_one(*args, **kwargs):
        if kwargs["recipient_name"] == "Grace Hopper":
            raise RuntimeError("template render failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(jobs, "generate_certificate", fail_one)
    response = client.post("/api/jobs", json=payload())
    job = client.get(f"/api/jobs/{response.json()['id']}").json()

    assert job["status"] == "partial"
    assert job["succeeded"] == 1
    assert job["failed"] == 1
    failed = next(item for item in job["certificates"] if item["recipient_name"] == "Grace Hopper")
    assert failed["status"] == "failed"
    assert failed["error_message"] == "template render failed"


def test_retrieve_generated_certificate(client):
    response = client.post("/api/jobs", json=payload())
    job = client.get(f"/api/jobs/{response.json()['id']}").json()
    certificate = job["certificates"][0]
    download = client.get(certificate["download_url"])

    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
