"""GET /applications (scope cho Candidate) va GET /offers (list de HR Manager
tim offer cho duyet) - bo sung khi xay frontend phat hien thieu."""

from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.candidate import Candidate
from tests.conftest import auth_headers, register_and_login_candidate


def test_candidate_can_list_own_applications_only(client, db, seed):
    headers_1 = register_and_login_candidate(client, "list-uv1@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV1",
            "candidate_email": "list-uv1@example.com",
            "candidate_phone": "0900000010",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=headers_1,
    )
    assert resp.status_code == 200, resp.text

    headers_2 = register_and_login_candidate(client, "list-uv2@example.com")
    client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV2",
            "candidate_email": "list-uv2@example.com",
            "candidate_phone": "0900000011",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=headers_2,
    )

    resp = client.get("/applications", headers=headers_1)
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) == 1
    assert results[0]["candidate_business_id"] != ""


def test_hr_manager_can_list_pending_approval_offers(client, db, seed):
    from app.models.job import Job

    job = db.query(Job).filter(Job.business_id == seed["job_business_id"]).first()
    candidate = Candidate(
        business_id=generate_business_id(db, "candidate"),
        full_name="UV Offer List",
        email="uv-offer-list@example.com",
        phone="0900000012",
    )
    db.add(candidate)
    db.flush()
    application = Application(business_id=generate_business_id(db, "application"), candidate_id=candidate.id, job_id=job.id)
    db.add(application)
    db.commit()

    hrm_a_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.post(
        "/offers",
        json={
            "application_business_id": application.business_id,
            "salary": "25000000",
            "probation_salary": "22000000",
            "start_date": "2026-10-01",
        },
        headers=hrm_a_headers,
    )
    offer_id = resp.json()["business_id"]
    client.post(f"/offers/{offer_id}/submit", headers=hrm_a_headers)

    hrm_b_headers = auth_headers(client, seed["hrm_b"]["email"])
    resp = client.get("/offers", params={"status": "PENDING_APPROVAL"}, headers=hrm_b_headers)
    assert resp.status_code == 200, resp.text
    ids = [o["business_id"] for o in resp.json()]
    assert offer_id in ids

    # HR Manager A la creator - khong duoc thay chinh minh trong danh sach can duyet cua nguoi khac
    # (endpoint van tra ve toan bo PENDING_APPROVAL, UI se tu loc; backend van chan approve o buoc /approve)
    resp = client.post(f"/offers/{offer_id}/approve", headers=hrm_a_headers)
    assert resp.status_code == 409


def test_candidate_cannot_list_offers_without_application_filter(client, seed):
    headers = register_and_login_candidate(client, "uv-noapp@example.com")
    resp = client.get("/offers", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "APPLICATION_BUSINESS_ID_REQUIRED"
