"""Dashboard summary (cong thuc theo v2 Phan 12.2) va bo loc/tim kiem cho
GET /jobs, GET /applications - phan hoi cau hoi 'Dashboard dau', 'phai co loc
tim kiem chu' cua nguoi dung."""

from tests.conftest import auth_headers, register_and_login_candidate


def test_dashboard_summary_counts_correctly(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    linkedin_source_id = client.post("/candidate-sources", json={"name": "LinkedIn"}, headers=hrm_headers).json()["business_id"]

    cand_headers = register_and_login_candidate(client, "uv-dash1@example.com")
    client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV Dash",
            "candidate_email": "uv-dash1@example.com", "candidate_phone": "0900000500",
            "ai_consent": True, "source_business_id": linkedin_source_id,
        },
        headers=cand_headers,
    )

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.get("/dashboard/summary", headers=hrm_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_applications"] >= 1
    assert body["status_breakdown"].get("NEW", 0) >= 1
    assert body["source_breakdown"].get("LinkedIn", 0) >= 1
    assert body["total_jobs"] >= 1


def test_dashboard_scoped_for_hr_role(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/dashboard/summary", headers=hr_headers)
    assert resp.status_code == 200
    # HR khong thay hr_performance cua nguoi khac (chi HR Manager/Admin moi co)
    assert resp.json()["hr_performance"] == []


def test_candidate_cannot_view_dashboard(client, seed):
    headers = register_and_login_candidate(client, "uv-dash2@example.com")
    resp = client.get("/dashboard/summary", headers=headers)
    assert resp.status_code == 403


def test_jobs_search_filter(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    client.post(
        "/jobs",
        json={
            "title": "Senior Data Engineer Unique123", "department_business_id": seed["department_business_id"],
            "description": "d", "requirements": "r", "quantity": 1, "location": "HN", "employment_type": "FULL_TIME",
        },
        headers=hrm_headers,
    )
    resp = client.get("/jobs", params={"search": "Unique123"}, headers=hrm_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "Unique123" in resp.json()[0]["title"]


def test_applications_search_filter_by_candidate_name(client, seed):
    headers = register_and_login_candidate(client, "uv-searchme@example.com")
    client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "Nguyen Van SearchTarget",
            "candidate_email": "uv-searchme@example.com", "candidate_phone": "0900000501", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=headers,
    )
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.get("/applications", params={"search": "SearchTarget"}, headers=hrm_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["candidate_full_name"] == "Nguyen Van SearchTarget"

    resp = client.get("/applications", params={"search": "khong-ton-tai-xyz"}, headers=hrm_headers)
    assert resp.json() == []
