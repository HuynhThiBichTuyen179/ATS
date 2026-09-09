# (1) Quan ly tai khoan HR qua API; (2) dan text CV luc Apply, luu that vao
# bang resumes.

from tests.conftest import auth_headers, register_and_login_candidate


def test_hr_manager_can_create_hr_but_not_admin(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])

    r = client.post(
        "/users",
        json={
            "full_name": "HR Moi",
            "email": "hr.moi@example.com",
            "password": "Password@123",
            "role": "HR",
            "department_business_id": seed["department_business_id"],
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["business_id"].startswith("USR")
    assert r.json()["role"] == "HR"

    r = client.post(
        "/users",
        json={"full_name": "Admin Moi", "email": "admin.moi@example.com", "password": "Password@123", "role": "ADMIN"},
        headers=headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "NOT_ALLOWED_TO_CREATE_THIS_ROLE"


def test_admin_can_create_hr_manager(client, seed):
    headers = auth_headers(client, seed["admin"]["email"])
    r = client.post(
        "/users",
        json={"full_name": "HRM Moi", "email": "hrm.moi@example.com", "password": "Password@123", "role": "HR_MANAGER"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "HR_MANAGER"


def test_hr_cannot_create_user(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    r = client.post(
        "/users",
        json={"full_name": "X", "email": "x@example.com", "password": "Password@123", "role": "HR"},
        headers=headers,
    )
    assert r.status_code == 403


def test_list_users_filter_by_role_excludes_candidates(client, seed):
    headers = auth_headers(client, seed["hrm_a"]["email"])
    r = client.get("/users", params={"role": "HR"}, headers=headers)
    assert r.status_code == 200, r.text
    assert all(u["role"] == "HR" for u in r.json())

    r = client.get("/users", headers=headers)
    assert all(u["role"] != "CANDIDATE" for u in r.json())


def test_apply_with_pasted_resume_text_is_saved(client, seed):
    headers = register_and_login_candidate(client, "uv-resume@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV Resume",
            "candidate_email": "uv-resume@example.com",
            "candidate_phone": "0900000123",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
            "resume_text": "5 nam kinh nghiem Python, FastAPI, PostgreSQL.",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["resume_text"] == "5 nam kinh nghiem Python, FastAPI, PostgreSQL."

    app_id = resp.json()["business_id"]
    hr_headers = auth_headers(client, seed["hr"]["email"])
    detail = client.get(f"/applications/{app_id}", headers=hr_headers)
    assert detail.json()["resume_text"] == "5 nam kinh nghiem Python, FastAPI, PostgreSQL."


def test_hr_can_edit_only_assigned_candidate(client, seed):
    # RBAC: Sua Candidate = Own/Scoped/Full/Full. HR chi duoc sua ho so
    # Candidate co it nhat 1 Application dang assigned_hr_id cho minh - HR
    # khong duoc gan phai bi tu choi o backend (khong chi an nut FE).
    candidate_headers = register_and_login_candidate(client, "uv-scope1@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV Scope",
            "candidate_email": "uv-scope1@example.com",
            "candidate_phone": "0900000500",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=candidate_headers,
    )
    candidate_id = resp.json()["candidate_business_id"]

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    client.post(
        "/users",
        json={"full_name": "HR Khac Scope", "email": "hr.other-scope@example.com", "password": "Password@123",
              "role": "HR", "department_business_id": seed["department_business_id"]},
        headers=hrm_headers,
    )
    other_hr_headers = auth_headers(client, "hr.other-scope@example.com")

    resp = client.put(f"/candidates/{candidate_id}", json={"phone": "0911111111"}, headers=other_hr_headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "NOT_ASSIGNED_TO_THIS_CANDIDATE"

    # seed["hr"] la assigned_hr_id cua Job -> duoc phep sua.
    assigned_hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.put(f"/candidates/{candidate_id}", json={"phone": "0922222222"}, headers=assigned_hr_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["phone"] == "0922222222"

    # HR_MANAGER khong bi scoping - sua duoc moi Candidate.
    resp = client.put(f"/candidates/{candidate_id}", json={"phone": "0933333333"}, headers=hrm_headers)
    assert resp.status_code == 200, resp.text


def test_apply_accepts_optional_profile_fields(client, seed):
    # Candidate tu ung tuyen duoc phep (khong bat buoc) khai bao them gioi
    # tinh/tom tat ky nang/tom tat kinh nghiem/luong mong muon - truoc day
    # cac truong nay chi HR nhap ho duoc qua 'Them ung vien'.
    headers = register_and_login_candidate(client, "uv-optional-fields@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV Optional",
            "candidate_email": "uv-optional-fields@example.com",
            "candidate_phone": "0900000555",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
            "candidate_gender": "FEMALE",
            "candidate_skills_summary": "Python, FastAPI, SQL",
            "candidate_experience_summary": "3 nam Backend Developer",
            "desired_salary": 25000000,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidate_gender"] == "FEMALE"
    assert body["candidate_skills_summary"] == "Python, FastAPI, SQL"
    assert body["candidate_experience_summary"] == "3 nam Backend Developer"
    assert body["desired_salary"] == 25000000

    # Ung tuyen lai (cung Job, khong cooldown) nhung LAN NAY bo trong het cac
    # truong tuy chon - profile da co san tu lan truoc KHONG bi ghi de thanh rong.
    resp2 = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV Optional",
            "candidate_email": "uv-optional-fields@example.com",
            "candidate_phone": "0900000555",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=headers,
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["candidate_gender"] == "FEMALE"
    assert resp2.json()["candidate_skills_summary"] == "Python, FastAPI, SQL"
    assert resp2.json()["candidate_experience_summary"] == "3 nam Backend Developer"
    # desired_salary nam tren Application (khong phai Candidate) nen KHONG ke
    # thua qua lan ung tuyen moi - dung, vi moi Application co the co muc
    # luong mong muon rieng cho tung lan/tung vi tri khac nhau.
    assert resp2.json()["desired_salary"] is None


def test_apply_rejects_invalid_gender(client, seed):
    headers = register_and_login_candidate(client, "uv-badgender@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV Bad Gender",
            "candidate_email": "uv-badgender@example.com",
            "candidate_phone": "0900000556",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
            "candidate_gender": "NOT_A_GENDER",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "INVALID_GENDER"


def test_apply_without_resume_text_has_none(client, seed):
    headers = register_and_login_candidate(client, "uv-noresume@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"],
            "candidate_full_name": "UV",
            "candidate_email": "uv-noresume@example.com",
            "candidate_phone": "0900000124",
            "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["resume_text"] is None
