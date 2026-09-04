"""Email Template CRUD, gui thu cong, va tu dong gui theo giai doan (v2 Phan
9). email_service.send_raw_email() da duoc conftest.py monkeypatch gia lap
thanh cong (xem fixture _fake_smtp) - test xac nhan qua audit_logs thay vi
hop thu that, khong goi SMTP that."""

from app.models.application import Application
from app.models.audit_log import AuditLog
from tests.conftest import auth_headers, register_and_login_candidate


def _create_template(client, headers, type_, subject="Xin chao {{candidate_name}}", content="Vi tri: {{job_title}} tai {{company_name}}"):
    return client.post(
        "/email-templates",
        json={"name": f"Mau {type_}", "type": type_, "subject": subject, "content": content},
        headers=headers,
    )


def test_hr_manager_can_create_and_list_templates(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = _create_template(client, headers, "SHORTLISTED")
    assert resp.status_code == 200, resp.text
    assert resp.json()["business_id"].startswith("EMT")

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/email-templates", headers=hr_headers)
    assert resp.status_code == 200
    assert any(t["type"] == "SHORTLISTED" for t in resp.json())


def test_hr_cannot_create_template(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    resp = _create_template(client, headers, "REJECTION")
    assert resp.status_code == 403


def test_deactivate_template_is_soft_delete(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(client, headers, "OFFER").json()["business_id"]

    resp = client.post(f"/email-templates/{template_id}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INACTIVE"

    # Van con trong danh sach (khong bi xoa vat ly), chi doi trang thai
    resp = client.get("/email-templates", headers=headers)
    assert any(t["business_id"] == template_id and t["status"] == "INACTIVE" for t in resp.json())


"""v2.3 Section 2/24 - HR_MANAGER va ADMIN deu duoc sua Email Template (TC-EMAIL-001..007)."""


def test_hr_manager_can_view_and_edit_template(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(client, headers, "OFFER").json()["business_id"]

    resp = client.get(f"/email-templates/{template_id}", headers=headers)
    assert resp.status_code == 200  # TC-EMAIL-001

    resp = client.put(f"/email-templates/{template_id}", json={"subject": "Tieu de moi"}, headers=headers)
    assert resp.status_code == 200, resp.text  # TC-EMAIL-002
    assert resp.json()["subject"] == "Tieu de moi"


def test_admin_can_edit_template(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(client, hrm_headers, "REJECTION").json()["business_id"]

    admin_headers = auth_headers(client, seed["admin"]["email"])
    resp = client.put(f"/email-templates/{template_id}", json={"content": "Noi dung moi"}, headers=admin_headers)
    assert resp.status_code == 200, resp.text  # TC-EMAIL-003
    assert resp.json()["content"] == "Noi dung moi"


def test_hr_cannot_edit_template(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(client, hrm_headers, "ONBOARDING").json()["business_id"]

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(f"/email-templates/{template_id}", json={"subject": "Khong duoc phep"}, headers=hr_headers)
    assert resp.status_code == 403  # TC-EMAIL-004


def test_candidate_cannot_access_email_templates(client, seed):
    cand_headers = register_and_login_candidate(client, "uv-emailtest@example.com")
    resp = client.get("/email-templates", headers=cand_headers)
    assert resp.status_code == 403  # TC-EMAIL-005


def test_duplicate_template_name_rejected(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    client.post("/email-templates", json={"name": "Mau Trung Ten", "type": "SHORTLISTED", "subject": "s", "content": "c"}, headers=headers)
    resp = client.post("/email-templates", json={"name": "Mau Trung Ten", "type": "REJECTION", "subject": "s2", "content": "c2"}, headers=headers)
    assert resp.status_code == 409  # TC-EMAIL-006
    assert resp.json()["detail"] == "TEMPLATE_NAME_ALREADY_EXISTS"


def test_update_template_creates_audit_log(client, db, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(client, headers, "INTERVIEW_INVITATION").json()["business_id"]

    resp = client.put(f"/email-templates/{template_id}", json={"subject": "Sua de audit"}, headers=headers)
    assert resp.status_code == 200

    log = db.query(AuditLog).filter(
        AuditLog.action == "EMAIL_TEMPLATE_UPDATED", AuditLog.entity_business_id == template_id
    ).first()
    assert log is not None  # TC-EMAIL-007
    assert "Sua de audit" in log.after_data


def test_manual_send_email_renders_variables_and_logs_audit(client, db, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    template_id = _create_template(
        client, hrm_headers, "OFFER",
        subject="Offer cho {{candidate_name}}", content="Vi tri {{job_title}} - {{company_name}}",
    ).json()["business_id"]

    cand_headers = register_and_login_candidate(client, "uv-email1@example.com")
    app_resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV Email",
            "candidate_email": "uv-email1@example.com", "candidate_phone": "0900000300", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    app_id = app_resp.json()["business_id"]

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(f"/email-templates/send/{app_id}", json={"template_business_id": template_id}, headers=hr_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True  # gia lap thanh cong qua fixture _fake_smtp
    assert "UV Email" in body["subject"]
    assert body["to"] == "uv-email1@example.com"

    logs = db.query(AuditLog).filter(AuditLog.entity_business_id == app_id, AuditLog.action == "EMAIL_SENT").all()
    assert len(logs) >= 1


def test_apply_auto_triggers_application_received_email(client, db, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    _create_template(client, hrm_headers, "APPLICATION_RECEIVED", subject="Da nhan ho so {{candidate_name}}")

    cand_headers = register_and_login_candidate(client, "uv-email2@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV Auto",
            "candidate_email": "uv-email2@example.com", "candidate_phone": "0900000301", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    app_id = resp.json()["business_id"]

    logs = db.query(AuditLog).filter(AuditLog.entity_business_id == app_id, AuditLog.action == "EMAIL_SENT").all()
    assert len(logs) == 1
    assert "UV Auto" in (logs[0].after_data or "")


def test_status_change_to_shortlisted_triggers_email(client, db, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    _create_template(client, hrm_headers, "SHORTLISTED", subject="Chuc mung {{candidate_name}}")

    cand_headers = register_and_login_candidate(client, "uv-email3@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV Shortlist",
            "candidate_email": "uv-email3@example.com", "candidate_phone": "0900000302", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    app_id = resp.json()["business_id"]

    app = db.query(Application).filter(Application.business_id == app_id).first()
    from app.models.enums import ApplicationStatus

    app.status = ApplicationStatus.SCREENING
    db.commit()

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(f"/applications/{app_id}/status", json={"status": "SHORTLISTED"}, headers=hr_headers)
    assert resp.status_code == 200

    logs = db.query(AuditLog).filter(AuditLog.entity_business_id == app_id, AuditLog.action == "EMAIL_SENT").all()
    assert any("UV Shortlist" in (log_.after_data or "") for log_ in logs)


def test_no_template_configured_does_not_break_flow(client, db, seed):
    """Khong co template ACTIVE cho loai su kien -> khong gui, khong loi."""
    cand_headers = register_and_login_candidate(client, "uv-email4@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV NoTemplate",
            "candidate_email": "uv-email4@example.com", "candidate_phone": "0900000303", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    assert resp.status_code == 200
