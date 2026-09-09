# Offer 4-eyes approval - bao phu cac tinh huong quan trong nhat.

from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.candidate import Candidate
from tests.conftest import auth_headers


def _make_application(db, job_business_id: str) -> str:
    from app.models.job import Job

    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    candidate = Candidate(
        business_id=generate_business_id(db, "candidate"),
        full_name="Ung Vien Test",
        email=f"candidate-{job.id}-{job_business_id}@example.com",
        phone="0900000001",
    )
    db.add(candidate)
    db.flush()
    application = Application(
        business_id=generate_business_id(db, "application"),
        candidate_id=candidate.id,
        job_id=job.id,
    )
    db.add(application)
    db.commit()
    return application.business_id


def _create_and_submit_offer(client, db, seed, creator_email) -> str:
    app_business_id = _make_application(db, seed["job_business_id"])
    headers = auth_headers(client, creator_email)
    resp = client.post(
        "/offers",
        json={
            "application_business_id": app_business_id,
            "salary": "30000000",
            "probation_salary": "27000000",
            "start_date": "2026-09-01",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    offer_id = resp.json()["business_id"]

    resp = client.post(f"/offers/{offer_id}/submit", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PENDING_APPROVAL"
    return offer_id


def test_offer_business_id_has_off_prefix(client, db, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    app_business_id = _make_application(db, seed["job_business_id"])
    resp = client.post(
        "/offers",
        json={
            "application_business_id": app_business_id,
            "salary": "30000000",
            "probation_salary": "27000000",
            "start_date": "2026-09-01",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["business_id"].startswith("OFF")
    assert resp.json()["status"] == "DRAFT"


def test_hr_cannot_approve_offer(client, db, seed):
    # HR khong bao gio co quyen Approve, bat ke ai tao Offer (Permission Matrix).
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(f"/offers/{offer_id}/approve", headers=headers)
    assert resp.status_code == 403


def test_creator_cannot_approve_own_offer(client, db, seed):
    # Trai tim cua 4-eyes approval: creator_id != approver_id.
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.post(f"/offers/{offer_id}/approve", headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "OFFER_SELF_APPROVAL_NOT_ALLOWED"


def test_another_hr_manager_can_approve(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers = auth_headers(client, seed["hrm_b"]["email"])
    resp = client.post(f"/offers/{offer_id}/approve", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "APPROVED"
    assert resp.json()["approver_business_id"] == seed["hrm_b"]["business_id"]


def test_admin_can_approve_but_not_own_offer(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["admin"]["email"])
    admin_headers = auth_headers(client, seed["admin"]["email"])
    resp = client.post(f"/offers/{offer_id}/approve", headers=admin_headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "OFFER_SELF_APPROVAL_NOT_ALLOWED"

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.post(f"/offers/{offer_id}/approve", headers=hrm_headers)
    assert resp.status_code == 200, resp.text


def test_rejected_offer_goes_back_to_draft_and_can_resubmit(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers_b = auth_headers(client, seed["hrm_b"]["email"])
    resp = client.post(f"/offers/{offer_id}/reject", json={"reason": "Luong chua phu hop ngan sach"}, headers=headers_b)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "DRAFT"

    headers_a = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.post(f"/offers/{offer_id}/submit", headers=headers_a)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PENDING_APPROVAL"


def test_cannot_send_offer_before_approved(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.post(f"/offers/{offer_id}/send", headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "OFFER_NOT_APPROVED"


def test_cannot_approve_already_sent_offer(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers_b = auth_headers(client, seed["hrm_b"]["email"])
    client.post(f"/offers/{offer_id}/approve", headers=headers_b)
    client.post(f"/offers/{offer_id}/send", headers=headers_b)

    resp = client.post(f"/offers/{offer_id}/approve", headers=headers_b)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "OFFER_NOT_PENDING_APPROVAL"


def test_full_happy_path_approve_send_accept(client, db, seed):
    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers_b = auth_headers(client, seed["hrm_b"]["email"])

    resp = client.post(f"/offers/{offer_id}/approve", headers=headers_b)
    assert resp.json()["status"] == "APPROVED"

    resp = client.post(f"/offers/{offer_id}/send", headers=headers_b)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "SENT"

    # Candidate accept - can dang nhap dung candidate gan voi application do
    from app.models.offer import Offer

    offer = db.query(Offer).filter(Offer.business_id == offer_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == offer.application.candidate_id).first()
    # Gan candidate voi 1 user CANDIDATE moi de co the goi API /offers/{id}/respond
    from app.core.security import hash_password
    from app.models.enums import UserRole, UserStatus
    from app.models.user import User

    cand_user = User(
        business_id=generate_business_id(db, "user"),
        full_name=candidate.full_name,
        email=candidate.email,
        password_hash=hash_password("Password@123"),
        role=UserRole.CANDIDATE,
        status=UserStatus.ACTIVE,
    )
    db.add(cand_user)
    db.flush()
    candidate.user_id = cand_user.id
    db.commit()

    cand_headers = auth_headers(client, candidate.email)
    resp = client.post(f"/offers/{offer_id}/respond", json={"response": "ACCEPTED"}, headers=cand_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "ACCEPTED"

    app_resp = client.get(f"/applications/{offer.application.business_id}", headers=headers_b)
    assert app_resp.json()["status"] == "HIRED"


def test_offer_expiry_scheduler(client, db, seed):
    from datetime import datetime, timedelta, timezone

    from app.models.enums import ApplicationStatus, UserRole
    from app.models.offer import Offer
    from app.models.user import User
    from app.services import offer_service

    offer_id = _create_and_submit_offer(client, db, seed, seed["hrm_a"]["email"])
    headers_b = auth_headers(client, seed["hrm_b"]["email"])
    client.post(f"/offers/{offer_id}/approve", headers=headers_b)
    client.post(f"/offers/{offer_id}/send", headers=headers_b)

    offer = db.query(Offer).filter(Offer.business_id == offer_id).first()
    offer.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    system_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
    expired = offer_service.expire_due_offers(db, system_user)
    assert any(o.business_id == offer_id for o in expired)

    db.refresh(offer)
    assert offer.status.value == "EXPIRED"
    assert offer.application.status == ApplicationStatus.REJECTED
