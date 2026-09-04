"""v2.3 Section 5/18 - PUT /applications/{id}: sua Luong mong muon / Nguon
ho so tu Candidate Table (khong phai qua Kanban drag-drop)."""

from tests.conftest import auth_headers, register_and_login_candidate


def _apply(client, headers, job_business_id, email, source_business_id):
    return client.post(
        "/applications",
        json={
            "job_business_id": job_business_id,
            "candidate_full_name": "UV Update",
            "candidate_email": email,
            "candidate_phone": "0900000300",
            "ai_consent": True,
            "source_business_id": source_business_id,
        },
        headers=headers,
    )


def test_hr_can_update_salary_and_source(client, seed):
    candidate_headers = register_and_login_candidate(client, "uv-update1@example.com")
    app_id = _apply(client, candidate_headers, seed["job_business_id"], "uv-update1@example.com", seed["source_business_id"]).json()["business_id"]

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    new_source = client.post("/candidate-sources", json={"name": "Referral"}, headers=hrm_headers).json()

    hr_headers = auth_headers(client, seed["hr"]["email"])  # seed["hr"] is the assigned HR for this Job
    resp = client.put(
        f"/applications/{app_id}",
        json={"desired_salary": 25000000, "source_business_id": new_source["business_id"]},
        headers=hr_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["desired_salary"] == 25000000
    assert body["source_business_id"] == new_source["business_id"]
    assert body["source"] == "Referral"


def test_unassigned_hr_cannot_update_application(client, seed):
    candidate_headers = register_and_login_candidate(client, "uv-update2@example.com")
    app_id = _apply(client, candidate_headers, seed["job_business_id"], "uv-update2@example.com", seed["source_business_id"]).json()["business_id"]

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    client.post(
        "/users",
        json={"full_name": "HR Khac", "email": "hr.other-update@example.com", "password": "Password@123", "role": "HR",
              "department_business_id": seed["department_business_id"]},
        headers=hrm_headers,
    )
    other_hr_headers = auth_headers(client, "hr.other-update@example.com")

    resp = client.put(f"/applications/{app_id}", json={"desired_salary": 10000000}, headers=other_hr_headers)
    assert resp.status_code == 403


def test_update_rejects_inactive_source(client, seed):
    candidate_headers = register_and_login_candidate(client, "uv-update3@example.com")
    app_id = _apply(client, candidate_headers, seed["job_business_id"], "uv-update3@example.com", seed["source_business_id"]).json()["business_id"]

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    inactive_source = client.post("/candidate-sources", json={"name": "Old Source"}, headers=hrm_headers).json()
    client.put(f"/candidate-sources/{inactive_source['business_id']}", json={"status": "INACTIVE"}, headers=hrm_headers)

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(
        f"/applications/{app_id}",
        json={"source_business_id": inactive_source["business_id"]},
        headers=hr_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "SOURCE_NOT_ACTIVE"


def test_candidate_cannot_call_application_update(client, seed):
    candidate_headers = register_and_login_candidate(client, "uv-update4@example.com")
    app_id = _apply(client, candidate_headers, seed["job_business_id"], "uv-update4@example.com", seed["source_business_id"]).json()["business_id"]

    resp = client.put(f"/applications/{app_id}", json={"desired_salary": 10000000}, headers=candidate_headers)
    assert resp.status_code == 403
