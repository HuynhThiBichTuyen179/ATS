# PUT /jobs/{id} - sua tin tuyen dung du dang DRAFT hay da PUBLISHED, va
# truong deadline luc tao.

from tests.conftest import auth_headers


def _create_job(client, headers, seed, **overrides):
    payload = {
        "title": "Backend Engineer Test",
        "department_business_id": seed["department_business_id"],
        "description": "Mo ta ban dau",
        "requirements": "Yeu cau ban dau",
        "location": "Ha Noi",
        "employment_type": "FULL_TIME",
    }
    payload.update(overrides)
    return client.post("/jobs", json=payload, headers=headers)


def test_create_job_with_deadline(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = _create_job(client, hrm_headers, seed, deadline="2026-12-31")
    assert resp.status_code == 200, resp.text
    assert resp.json()["deadline"].startswith("2026-12-31")


def test_update_job_while_draft(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    assert job["status"] == "DRAFT"

    resp = client.put(
        f"/jobs/{job['business_id']}",
        json={"title": "Backend Engineer Updated", "description": "Mo ta moi"},
        headers=hrm_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "Backend Engineer Updated"
    assert resp.json()["description"] == "Mo ta moi"
    assert resp.json()["status"] == "DRAFT"


def test_update_job_while_published(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    client.post(f"/jobs/{job['business_id']}/publish", headers=hrm_headers)

    resp = client.put(
        f"/jobs/{job['business_id']}",
        json={"salary_min": 20000000, "salary_max": 30000000, "quantity": 3},
        headers=hrm_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PUBLISHED"
    assert float(resp.json()["salary_min"]) == 20000000
    assert resp.json()["quantity"] == 3


def test_hr_cannot_update_job(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(f"/jobs/{job['business_id']}", json={"title": "x"}, headers=hr_headers)
    assert resp.status_code == 403


def test_hr_manager_can_close_published_job(client, seed):
    # HR Manager/Admin dong tin tuyen dung thu cong - khac voi dong tu dong
    # khi du chi tieu (offer_service). Sau khi dong, ung vien khong con nop
    # duoc ho so moi (da chan san o applications.py qua status != PUBLISHED).
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    client.post(f"/jobs/{job['business_id']}/publish", headers=hrm_headers)

    resp = client.post(f"/jobs/{job['business_id']}/close", headers=hrm_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "CLOSED"

    from tests.conftest import register_and_login_candidate

    cand_headers = register_and_login_candidate(client, "uv-close-job@example.com")
    apply_resp = client.post(
        "/applications",
        json={
            "job_business_id": job["business_id"],
            "candidate_full_name": "Ung Vien Test",
            "candidate_email": "uv-close-job@example.com",
            "candidate_phone": "0900000099",
            "source_business_id": seed["source_business_id"],
            "ai_consent": True,
        },
        headers=cand_headers,
    )
    assert apply_resp.status_code == 404
    assert apply_resp.json()["detail"] == "JOB_NOT_FOUND_OR_NOT_PUBLISHED"


def test_cannot_close_job_that_is_not_published(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    assert job["status"] == "DRAFT"

    resp = client.post(f"/jobs/{job['business_id']}/close", headers=hrm_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "JOB_NOT_PUBLISHED"


def test_hr_cannot_close_job(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = _create_job(client, hrm_headers, seed).json()
    client.post(f"/jobs/{job['business_id']}/publish", headers=hrm_headers)

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(f"/jobs/{job['business_id']}/close", headers=hr_headers)
    assert resp.status_code == 403
