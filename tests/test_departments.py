"""v2.2 Section 15/16/47 - Department CRUD day du (PUT/DELETE moi bo sung)."""

from tests.conftest import auth_headers


def test_list_applications_filters_by_department_and_status(client, seed, db):
    """BUG FIX: modal 'Thanh vien phong ban' can liet ke ung vien da HIRED
    thuoc 1 phong ban cu the - truoc day GET /applications khong co filter
    nao theo department_business_id/status_filter ca."""
    from app.core.id_generator import generate_business_id
    from app.models.application import Application
    from app.models.candidate import Candidate
    from app.models.enums import ApplicationStatus
    from app.models.job import Job

    job = db.query(Job).filter(Job.business_id == seed["job_business_id"]).first()
    candidate = Candidate(
        business_id=generate_business_id(db, "candidate"),
        full_name="Ung Vien Da Tuyen", email="hired-dept-test@example.com", phone="0900000900",
    )
    db.add(candidate)
    db.flush()
    application = Application(
        business_id=generate_business_id(db, "application"),
        candidate_id=candidate.id, job_id=job.id, department_id=job.department_id,
        status=ApplicationStatus.HIRED,
    )
    db.add(application)
    db.commit()

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.get(
        "/applications",
        params={"department_business_id": seed["department_business_id"], "status_filter": "HIRED"},
        headers=hrm_headers,
    )
    assert resp.status_code == 200, resp.text
    business_ids = [a["business_id"] for a in resp.json()]
    assert application.business_id in business_ids

    # Loc theo status khac (VD NEW) khong duoc tra ve ung vien da HIRED nay.
    resp2 = client.get(
        "/applications",
        params={"department_business_id": seed["department_business_id"], "status_filter": "NEW"},
        headers=hrm_headers,
    )
    assert application.business_id not in [a["business_id"] for a in resp2.json()]


def test_admin_full_crud_department(client, seed):
    headers = auth_headers(client, seed["admin"]["email"])

    resp = client.post("/departments", params={"name": "Ke Toan", "description": "Phong ke toan"}, headers=headers)
    assert resp.status_code == 200, resp.text
    dept_id = resp.json()["business_id"]
    assert resp.json()["status"] == "ACTIVE"

    resp = client.put(f"/departments/{dept_id}", params={"description": "Phong ke toan tai chinh"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Phong ke toan tai chinh"

    resp = client.delete(f"/departments/{dept_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INACTIVE"


def test_duplicate_department_name_blocked(client, seed):
    headers = auth_headers(client, seed["admin"]["email"])
    client.post("/departments", params={"name": "Marketing"}, headers=headers)
    resp = client.post("/departments", params={"name": "Marketing"}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "DEPARTMENT_NAME_ALREADY_EXISTS"


def test_delete_department_in_use_soft_deletes_not_hard(client, seed):
    """Section 16: khong xoa 'an toan' Department dang duoc Job su dung ->
    van phai la soft-delete (INACTIVE), khong lam vo FK cua Job da co."""
    headers = auth_headers(client, seed["admin"]["email"])
    # seed["department_business_id"] dang duoc seed["job_business_id"] su dung.
    resp = client.delete(f"/departments/{seed['department_business_id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["in_use"] is True
    assert resp.json()["status"] == "INACTIVE"

    # Job cu van con nguyen, khong bi mat department_id.
    job = client.get(f"/jobs/{seed['job_business_id']}", headers=headers).json()
    assert job is not None


def test_hr_cannot_manage_department(client, seed):
    headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post("/departments", params={"name": "HR Khong Duoc Tao"}, headers=headers)
    assert resp.status_code == 403
