"""v2.2 Section 17/47 - System Configuration: CRUD Candidate Source."""

from tests.conftest import auth_headers


def test_admin_crud_candidate_source(client, seed):
    headers = auth_headers(client, seed["admin"]["email"])

    resp = client.post("/candidate-sources", json={"name": "TopCV"}, headers=headers)
    assert resp.status_code == 200, resp.text
    source_id = resp.json()["business_id"]

    resp = client.get("/candidate-sources", headers=headers)
    assert any(s["name"] == "TopCV" for s in resp.json())

    resp = client.put(f"/candidate-sources/{source_id}", json={"status": "INACTIVE"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INACTIVE"

    resp = client.delete(f"/candidate-sources/{source_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INACTIVE"


def test_duplicate_source_name_blocked(client, seed):
    headers = auth_headers(client, seed["admin"]["email"])
    client.post("/candidate-sources", json={"name": "VietnamWorks"}, headers=headers)
    resp = client.post("/candidate-sources", json={"name": "VietnamWorks"}, headers=headers)
    assert resp.status_code == 409


def test_hr_can_view_but_not_manage_sources(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/candidate-sources", headers=hr_headers)
    assert resp.status_code == 200

    resp = client.post("/candidate-sources", json={"name": "Referral"}, headers=hr_headers)
    assert resp.status_code == 403


def test_candidate_can_view_active_sources_but_not_manage(client, seed):
    """BUG FIX: Candidate PHAI xem duoc danh sach Nguon ho so ACTIVE de chon o
    form Ung tuyen (bat buoc tu v2.3) - truoc day endpoint nay chan hoan toan
    CANDIDATE, khien dropdown "Nguon ho so" luon rong du Admin da cau hinh san
    nguon. Candidate van KHONG duoc quan ly (tao/sua/xoa) va KHONG thay nguon
    da INACTIVE."""
    from tests.conftest import register_and_login_candidate

    admin_headers = auth_headers(client, seed["admin"]["email"])
    inactive = client.post("/candidate-sources", json={"name": "Old Source Inactive"}, headers=admin_headers).json()
    client.put(f"/candidate-sources/{inactive['business_id']}", json={"status": "INACTIVE"}, headers=admin_headers)

    cand_headers = register_and_login_candidate(client, "uv-src@example.com")
    resp = client.get("/candidate-sources", headers=cand_headers)
    assert resp.status_code == 200, resp.text
    names = [s["name"] for s in resp.json()]
    assert seed["source_business_id"]  # sanity: seed fixture always has 1 ACTIVE source
    assert "Website" in names
    assert "Old Source Inactive" not in names
    assert all(s["status"] == "ACTIVE" for s in resp.json())

    resp = client.post("/candidate-sources", json={"name": "Referral2"}, headers=cand_headers)
    assert resp.status_code == 403
