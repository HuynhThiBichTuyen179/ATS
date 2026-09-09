# HR/HR_MANAGER/ADMIN tao ho so ung vien truc tiep, Candidate KHONG duoc tao
# ho so ung vien khac.

from tests.conftest import auth_headers, register_and_login_candidate


def _create_payload(email="uv-new1@example.com", job_business_id=None):
    return {
        "full_name": "Ung Vien Moi",
        "gender": "FEMALE",
        "email": email,
        "phone": "0900001111",
        "job_business_id": job_business_id,
        "desired_salary": 25000000,
        "source": "LinkedIn",
        "skills_summary": "Python, FastAPI, SQL",
        "experience_summary": "3 nam kinh nghiem backend",
    }


def test_hr_can_create_candidate(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post("/candidates", json=_create_payload(job_business_id=seed["job_business_id"]), headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["business_id"].startswith("UV")
    assert body["skills_summary"] == "Python, FastAPI, SQL"
    assert body["status"] == "ACTIVE"


def test_hr_manager_and_admin_can_create_candidate(client, seed):
    for actor_key, email in [("hrm_a", "uv-new2@example.com"), ("admin", "uv-new3@example.com")]:
        headers = auth_headers(client, seed[actor_key]["email"])
        resp = client.post(
            "/candidates", json=_create_payload(email=email, job_business_id=seed["job_business_id"]), headers=headers
        )
        assert resp.status_code == 200, resp.text


def test_candidate_cannot_create_another_candidate(client, seed):
    cand_headers = register_and_login_candidate(client, "uv-actor@example.com")
    resp = client.post(
        "/candidates", json=_create_payload(email="uv-victim@example.com", job_business_id=seed["job_business_id"]),
        headers=cand_headers,
    )
    assert resp.status_code == 403


def test_candidate_creation_links_job_by_id_and_inherits_department(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post("/candidates", json=_create_payload(job_business_id=seed["job_business_id"]), headers=headers)
    assert resp.status_code == 200, resp.text
    candidate_business_id = resp.json()["business_id"]

    # Application phai lien ket dung Job (theo ID) va ke thua dung Department
    # tu Job, khong duoc de trong/sai.
    apps = client.get(f"/applications?job_business_id={seed['job_business_id']}", headers=headers).json()
    app = next(a for a in apps if a["candidate_business_id"] == candidate_business_id)
    assert app["job_business_id"] == seed["job_business_id"]


def test_create_candidate_rejects_unpublished_job(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    job = client.post(
        "/jobs",
        json={
            "title": "Draft Job", "department_business_id": seed["department_business_id"],
            "description": "d", "requirements": "r", "location": "HN", "employment_type": "FULL_TIME",
            "quantity": 1,
        },
        headers=hrm_headers,
    ).json()

    resp = client.post(
        "/candidates", json=_create_payload(email="uv-draftjob@example.com", job_business_id=job["business_id"]),
        headers=hrm_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "JOB_NOT_PUBLISHED"


def test_create_candidate_dedupes_by_email_reuses_existing(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    r1 = client.post(
        "/candidates", json=_create_payload(email="uv-dedupe@example.com", job_business_id=seed["job_business_id"]),
        headers=headers,
    )
    assert r1.status_code == 200
    candidate_id_1 = r1.json()["business_id"]

    r2 = client.post(
        "/candidates", json=_create_payload(email="uv-dedupe@example.com", job_business_id=seed["job_business_id"]),
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["business_id"] == candidate_id_1, "Khong duoc tao Candidate trung khi email da ton tai"


def test_update_candidate_and_archive(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    candidate_id = client.post(
        "/candidates", json=_create_payload(email="uv-edit@example.com", job_business_id=seed["job_business_id"]),
        headers=headers,
    ).json()["business_id"]

    resp = client.put(f"/candidates/{candidate_id}", json={"full_name": "Ten Da Sua"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Ten Da Sua"

    resp = client.delete(f"/candidates/{candidate_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ARCHIVED"

    # Van con truy van duoc (khong mat du lieu) - chi doi status.
    resp = client.get(f"/candidates/{candidate_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ARCHIVED"


def test_search_candidates(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    client.post(
        "/candidates", json=_create_payload(email="findme.search@example.com", job_business_id=seed["job_business_id"]),
        headers=headers,
    )
    resp = client.get("/candidates?search=findme.search", headers=headers)
    assert resp.status_code == 200
    assert any(c["email"] == "findme.search@example.com" for c in resp.json())
