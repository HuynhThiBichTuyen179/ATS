# Re-apply khong gioi han 90 ngay; Idempotency chong duplicate submit, khong
# duoc chan re-apply hop le.

from tests.conftest import auth_headers, register_and_login_candidate


def _apply(client, headers, job_business_id, source_business_id, idem_key=None, email="ungvien@example.com"):
    request_headers = dict(headers)
    if idem_key:
        request_headers["Idempotency-Key"] = idem_key
    return client.post(
        "/applications",
        json={
            "job_business_id": job_business_id,
            "candidate_full_name": "Nguyen Van Ung Vien",
            "candidate_email": email,
            "candidate_phone": "0900000002",
            "source_business_id": source_business_id,
            "ai_consent": True,
        },
        headers=request_headers,
    )


def test_application_business_id_has_app_prefix(client, seed):
    cand_headers = register_and_login_candidate(client, "uv1@example.com")
    resp = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], email="uv1@example.com")
    assert resp.status_code == 200, resp.text
    assert resp.json()["business_id"].startswith("APP")
    assert resp.json()["status"] == "NEW"


def test_reapply_immediately_after_rejection_is_allowed(client, db, seed):
    # Khong con cooldown 90 ngay: Candidate bi REJECTED co the Apply lai NGAY,
    # khong can cho.
    cand_headers = register_and_login_candidate(client, "uv2@example.com")
    resp1 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="req-1", email="uv2@example.com")
    assert resp1.status_code == 200, resp1.text
    app1_id = resp1.json()["business_id"]

    # HR day pipeline toi REJECTED (SCREENING -> REJECTED)
    from app.models.application import Application
    from app.models.enums import ApplicationStatus

    app1 = db.query(Application).filter(Application.business_id == app1_id).first()
    app1.status = ApplicationStatus.SCREENING
    db.commit()

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(f"/applications/{app1_id}/status", json={"status": "REJECTED"}, headers=hr_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "REJECTED"

    # Apply lai NGAY LAP TUC, cung Job - PHAI duoc phep, khong co cooldown check
    resp2 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="req-2", email="uv2@example.com")
    assert resp2.status_code == 200, resp2.text
    app2_id = resp2.json()["business_id"]

    assert app2_id != app1_id
    assert resp2.json()["status"] == "NEW"

    # Application cu van con nguyen, khong bi overwrite
    db.refresh(app1)
    assert app1.status == ApplicationStatus.REJECTED
    assert app1.business_id == app1_id


def test_duplicate_idempotency_key_does_not_create_new_application(client, seed):
    cand_headers = register_and_login_candidate(client, "uv3@example.com")
    resp1 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="same-key", email="uv3@example.com")
    resp2 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="same-key", email="uv3@example.com")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["business_id"] == resp2.json()["business_id"]
    assert resp2.json()["is_new"] is False


def test_reapply_blocked_while_active_application_in_screening(client, db, seed):
    # Candidate KHONG duoc nop THEM ho so vao cung 1 Job neu ho so truoc do
    # da qua buoc sang loc (SCREENING tro di) va chua ket thuc - tranh 2 ho
    # so trung nhau cung duoc xu ly song song.
    cand_headers = register_and_login_candidate(client, "uv5@example.com")
    resp1 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="scr-1", email="uv5@example.com")
    assert resp1.status_code == 200, resp1.text
    app1_id = resp1.json()["business_id"]

    from app.models.application import Application
    from app.models.enums import ApplicationStatus

    app1 = db.query(Application).filter(Application.business_id == app1_id).first()
    app1.status = ApplicationStatus.SCREENING
    db.commit()

    resp2 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="scr-2", email="uv5@example.com")
    assert resp2.status_code == 409, resp2.text
    assert resp2.json()["detail"].startswith("ALREADY_HAS_ACTIVE_APPLICATION_FOR_THIS_JOB")


def test_reapply_still_allowed_while_previous_still_new(client, seed):
    # Ho so cu con o NEW (chua qua sang loc) - van cho nop them binh thuong,
    # dung tinh than tai ung tuyen khong gioi han.
    cand_headers = register_and_login_candidate(client, "uv6@example.com")
    resp1 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="new-1", email="uv6@example.com")
    assert resp1.status_code == 200, resp1.text
    assert resp1.json()["status"] == "NEW"

    resp2 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="new-2", email="uv6@example.com")
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["business_id"] != resp1.json()["business_id"]


def test_different_idempotency_key_allows_new_application(client, db, seed):
    cand_headers = register_and_login_candidate(client, "uv4@example.com")
    resp1 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="key-a", email="uv4@example.com")
    app1_id = resp1.json()["business_id"]

    from app.models.application import Application
    from app.models.enums import ApplicationStatus

    app1 = db.query(Application).filter(Application.business_id == app1_id).first()
    app1.status = ApplicationStatus.WITHDRAWN
    db.commit()

    resp2 = _apply(client, cand_headers, seed["job_business_id"], seed["source_business_id"], idem_key="key-b", email="uv4@example.com")
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["business_id"] != app1_id
    assert resp2.json()["is_new"] is True
