"""E2E cho cac tinh nang moi: Dashboard, Upload CV that (DOCX), AI Screening
(stub mode), Email Template + gui thu cong + tu dong theo giai doan, filter/
search. Chay: python scripts/smoke_new_features.py (server phai dang chay
tren :8123)."""

import io
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8123"
RUN_ID = uuid.uuid4().hex[:8]


def check(label, condition):
    print(f"[{'OK' if condition else 'FAIL'}] {label}")
    if not condition:
        sys.exit(1)


def make_docx_bytes(text: str) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


with httpx.Client(timeout=15) as client:
    hrm_a = client.post(f"{BASE}/auth/login", json={"email": "hrmanager.a@example.com", "password": "HrManager@123"}).json()["access_token"]
    hr = client.post(f"{BASE}/auth/login", json={"email": "hr.a@example.com", "password": "Hr@123456"}).json()["access_token"]

    def auth(t):
        return {"Authorization": f"Bearer {t}"}

    # Tao Job rieng cho lan chay nay va gan ro rang cho HR - tranh lay nham
    # mot Job cu (tu lan chay script khac) chua duoc gan cho HR nay, se bi
    # RBAC chan dung nhu thiet ke (403) chu khong phai loi.
    dept_id = client.get(f"{BASE}/departments", headers=auth(hrm_a)).json()[0]["business_id"]
    hr_business_id = client.get(f"{BASE}/auth/me", headers=auth(hr)).json()["business_id"]
    r = client.post(
        f"{BASE}/jobs",
        json={
            "title": f"New Features Test Role {RUN_ID}", "department_business_id": dept_id,
            "description": "d", "requirements": "r", "quantity": 5,
            "location": "HN", "employment_type": "FULL_TIME",
            "assigned_hr_business_id": hr_business_id,
        },
        headers=auth(hrm_a),
    )
    check("POST /jobs (co gan assigned_hr_business_id luc tao)", r.status_code == 200 and r.json()["assigned_hr_business_id"] == hr_business_id)
    job_id = r.json()["business_id"]
    client.post(f"{BASE}/jobs/{job_id}/publish", headers=auth(hrm_a))

    # --- Dashboard ---
    r = client.get(f"{BASE}/dashboard/summary", headers=auth(hrm_a))
    check("GET /dashboard/summary", r.status_code == 200 and "status_breakdown" in r.json())

    # --- Email template ---
    email_addr = f"new-features-{RUN_ID}@example.com"
    r = client.post(
        f"{BASE}/email-templates",
        json={"name": f"Mau test {RUN_ID}", "type": "APPLICATION_RECEIVED", "subject": "Da nhan ho so {{candidate_name}}", "content": "Cam on {{candidate_name}} da ung tuyen {{job_title}} tai {{company_name}}."},
        headers=auth(hrm_a),
    )
    check("POST /email-templates", r.status_code == 200)
    template_id = r.json()["business_id"]

    # --- Apply (kich hoat auto-trigger APPLICATION_RECEIVED) ---
    reg = client.post(f"{BASE}/auth/register", json={"full_name": "UV New Features", "email": email_addr, "password": "Password@123", "phone": "0900000600"})
    cand_token = reg.json()["access_token"]
    r = client.post(
        f"{BASE}/applications",
        json={"job_business_id": job_id, "candidate_full_name": "UV New Features", "candidate_email": email_addr, "candidate_phone": "0900000600", "ai_consent": True},
        headers={**auth(cand_token), "Idempotency-Key": f"nf-{RUN_ID}"},
    )
    check("POST /applications", r.status_code == 200)
    app_id = r.json()["business_id"]

    r = client.get(f"{BASE}/audit-logs", params={"entity_type": "application", "entity_business_id": app_id}, headers=auth(hrm_a))
    check("Auto-trigger APPLICATION_RECEIVED da ghi audit_logs", any(log["action"] in ("EMAIL_SENT", "EMAIL_FAILED") for log in r.json()))

    # --- Upload CV that (DOCX) ---
    docx_bytes = make_docx_bytes("Ung vien co 3 nam kinh nghiem Python FastAPI MySQL Docker CI/CD.")
    r = client.post(f"{BASE}/applications/{app_id}/resume", files={"file": ("cv.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, headers=auth(cand_token))
    check("POST /applications/{id}/resume (upload DOCX that)", r.status_code == 200 and "kinh nghiem" in r.json()["extracted_text"])

    r = client.get(f"{BASE}/applications/{app_id}", headers=auth(hr))
    check("Application.has_resume = true sau upload", r.json()["has_resume"] is True)

    # --- AI Screening (stub mode - khong co AI_API_KEY trong .env cua moi truong test nay) ---
    r = client.post(f"{BASE}/ai/analyze/{app_id}", headers=auth(hr))
    check("POST /ai/analyze (stub mode)", r.status_code == 200 and r.json()["provider"] == "stub")
    match_score = r.json()["match_score"]

    r = client.get(f"{BASE}/applications/{app_id}", headers=auth(hr))
    check("match_score dong bo vao ApplicationOut", r.json()["match_score"] == match_score)
    check("Status tu dong SCREENING sau AI", r.json()["status"] == "SCREENING")

    # --- Gui email thu cong ---
    r = client.post(f"{BASE}/email-templates/send/{app_id}", json={"template_business_id": template_id}, headers=auth(hr))
    check("POST /email-templates/send (thu cong)", r.status_code == 200 and r.json()["status_message"])

    # --- Filter/search ---
    r = client.get(f"{BASE}/applications", params={"search": "New Features"}, headers=auth(hrm_a))
    check("GET /applications?search= tim dung ung vien", any(a["business_id"] == app_id for a in r.json()))

    r = client.get(f"{BASE}/jobs", params={"search": "xyz-khong-ton-tai-999"}, headers=auth(hrm_a))
    check("GET /jobs?search= tra ve rong khi khong khop", r.json() == [])

    print("\nTAT CA KIEM TRA TINH NANG MOI DEU PASS.")
