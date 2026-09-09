# Kich ban E2E mo phong dung cac loi goi ma frontend (app/static/index.html)
# thuc hien, chay qua HTTP that (khong phai TestClient) de xac nhan hop dong
# API dung nhu JS da viet. Chay: python scripts/smoke_e2e.py (server phai
# dang chay tren localhost:8123).

import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8123"
# Dinh danh rieng cho tung lan chay - tranh script bi anh huong boi du lieu
# con lai tu lan chay truoc neu DB khong the reset sach (Windows file lock).
RUN_ID = uuid.uuid4().hex[:8]
CANDIDATE_EMAIL = f"e2e-candidate-{RUN_ID}@example.com"


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        sys.exit(1)


def login(client, email, password):
    r = client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    check(f"login {email}", r.status_code == 200)
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


with httpx.Client(timeout=10) as client:
    hrm_a = login(client, "hrmanager.a@example.com", "HrManager@123")
    hrm_b = login(client, "hrmanager.b@example.com", "HrManager@123")
    hr = login(client, "hr.a@example.com", "Hr@123456")

    r = client.get(f"{BASE}/departments", headers=auth(hrm_a))
    check("GET /departments", r.status_code == 200 and len(r.json()) >= 1)
    dept_id = r.json()[0]["business_id"]

    r = client.get(f"{BASE}/jobs", headers=auth(hr))
    check("GET /jobs (list)", r.status_code == 200)
    published = [j for j in r.json() if j["status"] == "PUBLISHED"]
    check("co it nhat 1 job PUBLISHED tu seed_data", len(published) >= 1)
    job_id = published[0]["business_id"]

    r = client.post(
        f"{BASE}/auth/register",
        json={"full_name": "E2E Candidate", "email": CANDIDATE_EMAIL, "password": "Password@123", "phone": "0909000000"},
    )
    if r.status_code == 409:
        r = client.post(f"{BASE}/auth/login", json={"email": CANDIDATE_EMAIL, "password": "Password@123"})
    check("register/login candidate", r.status_code == 200)
    cand_token = r.json()["access_token"]

    r = client.post(
        f"{BASE}/applications",
        json={
            "job_business_id": job_id,
            "candidate_full_name": "E2E Candidate",
            "candidate_email": CANDIDATE_EMAIL,
            "candidate_phone": "0909000000",
            "source": "Website",
            "ai_consent": True,
        },
        headers={**auth(cand_token), "Idempotency-Key": f"e2e-key-{RUN_ID}"},
    )
    check("POST /applications (apply)", r.status_code == 200)
    app_id = r.json()["business_id"]

    r = client.get(f"{BASE}/applications", headers=auth(cand_token))
    check("GET /applications (candidate self-list)", r.status_code == 200 and any(a["business_id"] == app_id for a in r.json()))

    for target in ["AI_SCREENING", "SCREENING", "SHORTLISTED", "INTERVIEW"]:
        # AI_SCREENING->SCREENING la system-driven trong service that, o day
        # dung truc tiep API HR de mo phong pipeline toi INTERVIEW cho E2E.
        if target == "AI_SCREENING":
            continue
        r = client.put(f"{BASE}/applications/{app_id}/status", json={"status": target}, headers=auth(hr))
        check(f"PUT /applications/status -> {target}", r.status_code == 200, )

    r = client.post(
        f"{BASE}/offers",
        json={"application_business_id": app_id, "salary": "28000000", "probation_salary": "25000000", "start_date": "2026-11-01"},
        headers=auth(hrm_a),
    )
    check("POST /offers (create)", r.status_code == 200)
    offer_id = r.json()["business_id"]

    r = client.post(f"{BASE}/offers/{offer_id}/submit", headers=auth(hrm_a))
    check("POST /offers/submit", r.status_code == 200 and r.json()["status"] == "PENDING_APPROVAL")

    r = client.get(f"{BASE}/offers", params={"status": "PENDING_APPROVAL"}, headers=auth(hrm_b))
    check("GET /offers?status=PENDING_APPROVAL (HR Manager B tim thay)", any(o["business_id"] == offer_id for o in r.json()))

    r = client.post(f"{BASE}/offers/{offer_id}/approve", headers=auth(hrm_a))
    check("Self-approval BI CHAN dung nhu thiet ke (409)", r.status_code == 409 and r.json()["detail"] == "OFFER_SELF_APPROVAL_NOT_ALLOWED")

    r = client.post(f"{BASE}/offers/{offer_id}/approve", headers=auth(hrm_b))
    check("POST /offers/approve (HR Manager B, khac creator)", r.status_code == 200 and r.json()["status"] == "APPROVED")

    r = client.post(f"{BASE}/offers/{offer_id}/send", headers=auth(hrm_b))
    check("POST /offers/send", r.status_code == 200 and r.json()["status"] == "SENT")

    r = client.get(f"{BASE}/offers?application_business_id={app_id}", headers=auth(cand_token))
    check("GET /offers?application_business_id (candidate xem offer cua minh)", r.status_code == 200 and len(r.json()) == 1)

    r = client.post(f"{BASE}/offers/{offer_id}/respond", json={"response": "ACCEPTED"}, headers=auth(cand_token))
    check("POST /offers/respond ACCEPTED", r.status_code == 200 and r.json()["status"] == "ACCEPTED")

    r = client.get(f"{BASE}/applications/{app_id}", headers=auth(cand_token))
    check("Application chuyen sang HIRED", r.json()["status"] == "HIRED")

    r = client.get(f"{BASE}/audit-logs", headers=auth(hrm_b))
    check("GET /audit-logs (HR Manager)", r.status_code == 200 and len(r.json()) > 0)

    print("\nTAT CA KIEM TRA E2E QUA HTTP THAT DEU PASS.")
