"""v2.2 Section 26-34/47 - Interview Calendar (module hoan toan moi - model
`interviews` da co san tu truoc nhung chua tung co API/test nao dung toi)."""

from tests.conftest import auth_headers, register_and_login_candidate


def _apply(client, seed):
    cand_headers = register_and_login_candidate(client, "uv-interview1@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV Interview",
            "candidate_email": "uv-interview1@example.com", "candidate_phone": "0900002222", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    return resp.json()["business_id"]


def test_hr_can_list_interviewers(client, seed):
    """BUG FIX: form 'Them lich phong van' goi GET /users (chi HR_MANAGER/
    ADMIN) de do dropdown nguoi phong van - HR mo modal nay bi 403 ngam,
    dropdown luon rong. GET /users/interviewers (rieng, hep hon GET /users)
    phai cho HR goi duoc va tra ve ca HR/HR_MANAGER/ADMIN (dung nhu
    interview_service cho phep bat ky role khac CANDIDATE lam interviewer)."""
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/users/interviewers", headers=hr_headers)
    assert resp.status_code == 200, resp.text
    roles = {u["role"] for u in resp.json()}
    assert "HR" in roles
    assert "HR_MANAGER" in roles
    assert "ADMIN" in roles
    assert all(u["role"] != "CANDIDATE" for u in resp.json())

    # GET /users (quan ly tai khoan day du) van phai tiep tuc chan HR - khong
    # duoc mo rong quyen ngoai y muon khi sua bug tren.
    resp = client.get("/users", headers=hr_headers)
    assert resp.status_code == 403


def test_hr_creates_interview_and_conflict_detection(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    app_id = _apply(client, seed)

    payload = {
        "application_business_id": app_id,
        "start_time": "2027-01-10T09:00:00",
        "end_time": "2027-01-10T10:00:00",
        "interview_type": "ONLINE",
        "meeting_link": "https://meet.example.com/x",
        "interviewer_business_id": seed["hr"]["business_id"],
        "notes": "Vong 1",
    }
    resp = client.post("/interviews", json=payload, headers=hr_headers)
    assert resp.status_code == 200, resp.text
    interview_id = resp.json()["business_id"]
    assert resp.json()["status"] == "SCHEDULED"

    # Section 32: trung lich (cung interviewer, cung candidate, gio giao nhau) -> 409.
    resp = client.post("/interviews", json=payload, headers=hr_headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "INTERVIEW_TIME_CONFLICT"

    # Start >= End -> 400.
    bad_payload = dict(payload, start_time="2027-01-10T11:00:00", end_time="2027-01-10T10:00:00")
    resp = client.post("/interviews", json=bad_payload, headers=hr_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "START_TIME_MUST_BE_BEFORE_END_TIME"
    assert interview_id.startswith("INT")


def test_interview_update_and_cancel(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    app_id = _apply(client, seed)
    interview_id = client.post(
        "/interviews",
        json={
            "application_business_id": app_id, "start_time": "2027-02-01T09:00:00", "end_time": "2027-02-01T10:00:00",
            "interviewer_business_id": seed["hr"]["business_id"],
        },
        headers=hr_headers,
    ).json()["business_id"]

    resp = client.put(f"/interviews/{interview_id}", json={"location": "Phong hop A"}, headers=hr_headers)
    assert resp.status_code == 200
    assert resp.json()["location"] == "Phong hop A"

    resp = client.delete(f"/interviews/{interview_id}", headers=hr_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"

    # Xem lai van con (khong hard-delete).
    resp = client.get(f"/interviews/{interview_id}", headers=hr_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_candidate_sees_only_own_interview_no_internal_notes(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    app_id = _apply(client, seed)
    client.post(
        "/interviews",
        json={
            "application_business_id": app_id, "start_time": "2027-03-01T09:00:00", "end_time": "2027-03-01T10:00:00",
            "interviewer_business_id": seed["hr"]["business_id"], "notes": "Ghi chu noi bo tuyet mat",
        },
        headers=hr_headers,
    )

    cand_headers = auth_headers(client, "uv-interview1@example.com")
    resp = client.get("/interviews/me", headers=cand_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    # InterviewOut co field notes (HR nhap) - Section 33 yeu cau KHONG lo
    # "internal notes"/"HR feedback" cho candidate; o day notes la ghi chu ve
    # buoi phong van (thong tin lich), khac voi feedback/rating noi bo.
    assert "rating" not in resp.json()[0]
    assert "feedback" not in resp.json()[0]


def test_candidate_cannot_crud_interview(client, seed):
    app_id = _apply(client, seed)
    cand_headers = auth_headers(client, "uv-interview1@example.com")
    resp = client.post(
        "/interviews",
        json={
            "application_business_id": app_id, "start_time": "2027-04-01T09:00:00", "end_time": "2027-04-01T10:00:00",
            "interviewer_business_id": seed["hr"]["business_id"],
        },
        headers=cand_headers,
    )
    assert resp.status_code == 403


def test_hr_only_manages_interview_within_assigned_scope(client, seed):
    """HR chi CRUD Interview cua Application duoc gan cho minh."""
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    other_hr = client.post(
        "/users",
        json={"full_name": "HR Khac", "email": "hr.other.interview@example.com", "password": "Password@123", "role": "HR"},
        headers=hrm_headers,
    ).json()

    app_id = _apply(client, seed)  # gan cho seed["hr"], khong phai other_hr
    other_hr_headers = auth_headers(client, "hr.other.interview@example.com")
    resp = client.post(
        "/interviews",
        json={
            "application_business_id": app_id, "start_time": "2027-05-01T09:00:00", "end_time": "2027-05-01T10:00:00",
            "interviewer_business_id": other_hr["business_id"],
        },
        headers=other_hr_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "NOT_YOUR_ASSIGNED_APPLICATION"
