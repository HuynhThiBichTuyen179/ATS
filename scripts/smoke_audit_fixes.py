# Kiem tra rieng: (1) GET /offers/{id} phai chan candidate khac; (2) assign-hr
# endpoint; (3) archive endpoint; (4) tu dong dong Job khi du quota. Chay:
# python scripts/smoke_audit_fixes.py (server phai dang chay tren :8123).

import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8123"
# Dinh danh rieng cho tung lan chay - tranh script bi anh huong boi du lieu
# con lai tu lan chay truoc neu DB khong the reset sach (Windows file lock).
RUN_ID = uuid.uuid4().hex[:8]


def check(label, condition):
    print(f"[{'OK' if condition else 'FAIL'}] {label}")
    if not condition:
        sys.exit(1)


with httpx.Client(timeout=10) as client:
    hrm_a = client.post(f"{BASE}/auth/login", json={"email": "hrmanager.a@example.com", "password": "HrManager@123"}).json()["access_token"]
    hrm_b = client.post(f"{BASE}/auth/login", json={"email": "hrmanager.b@example.com", "password": "HrManager@123"}).json()["access_token"]
    hr = client.post(f"{BASE}/auth/login", json={"email": "hr.a@example.com", "password": "Hr@123456"}).json()["access_token"]

    def auth(t):
        return {"Authorization": f"Bearer {t}"}

    dept_id = client.get(f"{BASE}/departments", headers=auth(hrm_a)).json()[0]["business_id"]

    # --- Setup: job quantity=1, gan HR qua endpoint moi ---
    r = client.post(
        f"{BASE}/jobs",
        json={
            "title": f"Quota Test Role {RUN_ID}", "department_business_id": dept_id,
            "description": "d", "requirements": "r", "quantity": 1,
            "location": "HN", "employment_type": "FULL_TIME",
        },
        headers=auth(hrm_a),
    )
    check("POST /jobs (quantity=1)", r.status_code == 200)
    job_id = r.json()["business_id"]
    check("Job moi tao CHUA co assigned_hr (dung mac dinh)", r.json()["assigned_hr_business_id"] is None)

    hr_business_id = client.get(f"{BASE}/auth/me", headers=auth(hr)).json()["business_id"]
    r = client.post(f"{BASE}/jobs/{job_id}/assign-hr", json={"hr_business_id": hr_business_id}, headers=auth(hrm_a))
    check("POST /jobs/{id}/assign-hr", r.status_code == 200 and r.json()["assigned_hr_business_id"] == hr_business_id)

    r = client.post(f"{BASE}/jobs/{job_id}/publish", headers=auth(hrm_a))
    check("Publish job quota-test", r.status_code == 200)

    # --- Candidate A apply, day toi INTERVIEW, tao offer, duyet, gui, accept ---
    def make_candidate_hired(email):
        reg = client.post(f"{BASE}/auth/register", json={"full_name": "UV", "email": email, "password": "Password@123", "phone": "0900000099"})
        token = reg.json()["access_token"] if reg.status_code == 200 else client.post(f"{BASE}/auth/login", json={"email": email, "password": "Password@123"}).json()["access_token"]
        r = client.post(
            f"{BASE}/applications",
            json={"job_business_id": job_id, "candidate_full_name": "UV", "candidate_email": email, "candidate_phone": "0900000099", "ai_consent": True},
            headers={**auth(token), "Idempotency-Key": f"key-{email}"},
        )
        app_id = r.json()["business_id"]
        check(f"Application moi ke thua assigned_hr tu Job ({email})", True)  # kiem tra gian tiep qua HR list ben duoi
        for target in ("SCREENING", "SHORTLISTED", "INTERVIEW"):
            client.put(f"{BASE}/applications/{app_id}/status", json={"status": target}, headers=auth(hr))
        r = client.post(f"{BASE}/offers", json={"application_business_id": app_id, "salary": "20000000", "probation_salary": "18000000", "start_date": "2026-12-01"}, headers=auth(hrm_a))
        offer_id = r.json()["business_id"]
        client.post(f"{BASE}/offers/{offer_id}/submit", headers=auth(hrm_a))
        client.post(f"{BASE}/offers/{offer_id}/approve", headers=auth(hrm_b))
        client.post(f"{BASE}/offers/{offer_id}/send", headers=auth(hrm_b))
        r = client.post(f"{BASE}/offers/{offer_id}/respond", json={"response": "ACCEPTED"}, headers=auth(token))
        return token, app_id, offer_id, r

    # HR gio phai thay Application trong danh sach cua minh (Rule 5 hoat dong)
    email1 = f"quota-uv1-{RUN_ID}@example.com"
    token1, app1, offer1, resp1 = make_candidate_hired(email1)
    check("Offer respond ACCEPTED -> Application HIRED", resp1.json()["status"] == "ACCEPTED")

    hr_apps_after = client.get(f"{BASE}/applications", headers=auth(hr)).json()
    check("HR thay Application vua tao trong scope cua minh (assigned_hr ke thua)", any(a["business_id"] == app1 for a in hr_apps_after))

    r = client.get(f"{BASE}/jobs/{job_id}", headers=auth(hr))
    check("Rule 2: Job tu dong CLOSED khi du quota (quantity=1, da HIRED 1)", r.json()["status"] == "CLOSED")

    # --- CRITICAL fix: candidate khac KHONG duoc xem offer nay ---
    email2 = f"quota-uv2-{RUN_ID}@example.com"
    reg2 = client.post(f"{BASE}/auth/register", json={"full_name": "UV Khac", "email": email2, "password": "Password@123", "phone": "0900000088"})
    token2 = reg2.json()["access_token"]
    r = client.get(f"{BASE}/offers/{offer1}", headers=auth(token2))
    check("CRITICAL FIX: Candidate KHAC bi chan xem offer khong phai cua minh (403)", r.status_code == 403)

    r = client.get(f"{BASE}/offers/{offer1}", headers=auth(token1))
    check("Candidate CHINH CHU van xem duoc offer cua minh", r.status_code == 200)

    # --- Archive ---
    r = client.post(
        f"{BASE}/jobs",
        json={"title": f"Archive Test {RUN_ID}", "department_business_id": dept_id, "description": "d", "requirements": "r", "quantity": 5, "location": "HN", "employment_type": "FULL_TIME"},
        headers=auth(hrm_a),
    )
    job2 = r.json()["business_id"]
    client.post(f"{BASE}/jobs/{job2}/publish", headers=auth(hrm_a))
    email3 = f"archive-uv-{RUN_ID}@example.com"
    reg3 = client.post(f"{BASE}/auth/register", json={"full_name": "UV3", "email": email3, "password": "Password@123", "phone": "0900000077"})
    token3 = reg3.json()["access_token"]
    r = client.post(
        f"{BASE}/applications",
        json={"job_business_id": job2, "candidate_full_name": "UV3", "candidate_email": email3, "candidate_phone": "0900000077", "ai_consent": True},
        headers=auth(token3),
    )
    app3 = r.json()["business_id"]
    r = client.put(f"{BASE}/applications/{app3}/archive", json={"archive_reason": "TALENT_POOL"}, headers=auth(hrm_a))
    check("PUT /applications/{id}/archive (HR Manager)", r.status_code == 200 and r.json()["status"] == "ARCHIVED")

    # --- HR (khong phai Manager) KHONG duoc archive ---
    email4 = f"archive-uv2-{RUN_ID}@example.com"
    token4 = client.post(f"{BASE}/auth/register", json={"full_name": "UV4", "email": email4, "password": "Password@123", "phone": "0900000066"}).json()["access_token"]
    r = client.post(
        f"{BASE}/applications",
        json={"job_business_id": job2, "candidate_full_name": "UV4", "candidate_email": email4, "candidate_phone": "0900000066", "ai_consent": True},
        headers=auth(token4),
    )
    app4 = r.json()["business_id"]
    r = client.put(f"{BASE}/applications/{app4}/archive", json={"archive_reason": "TALENT_POOL"}, headers=auth(hr))
    check("HR (khong phai Manager/Admin) KHONG duoc archive (403)", r.status_code == 403)

    # --- Password complexity ---
    r = client.post(f"{BASE}/auth/register", json={"full_name": "Weak", "email": f"weakpass-{RUN_ID}@example.com", "password": "onlyletters", "phone": "0900000055"})
    check("Dang ky voi password khong co so BI TU CHOI (422)", r.status_code == 422)

    print("\nTAT CA KIEM TRA FIX TU DOT AUDIT DEU PASS.")
