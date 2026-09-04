"""PUT /jobs/{id} - sua tin tuyen dung du dang DRAFT hay da PUBLISHED (theo
yeu cau nguoi dung), va truong deadline luc tao."""

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
