"""v2.2 Section 12-14/47 - HR Team edit/deactivate (PUT/DELETE /users/{id} moi bo sung)."""

from tests.conftest import auth_headers


def test_admin_edit_and_deactivate_hr(client, seed):
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    new_hr = client.post(
        "/users",
        json={"full_name": "HR Se Bi Sua", "email": "hr.editme@example.com", "password": "Password@123", "role": "HR"},
        headers=hrm_headers,
    ).json()

    admin_headers = auth_headers(client, seed["admin"]["email"])
    resp = client.put(f"/users/{new_hr['business_id']}", json={"full_name": "Ten Moi"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Ten Moi"

    # Password KHONG bao gio xuat hien trong response (Section 13).
    assert "password" not in resp.json()
    assert "password_hash" not in resp.json()

    resp = client.delete(f"/users/{new_hr['business_id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INACTIVE"


def test_hr_manager_cannot_manage_other_hr_manager_or_admin(client, seed):
    hrm_a_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.put(
        f"/users/{seed['hrm_b']['business_id']}", json={"full_name": "Khong Duoc Sua"}, headers=hrm_a_headers
    )
    assert resp.status_code == 403

    resp = client.delete(f"/users/{seed['admin']['business_id']}", headers=hrm_a_headers)
    assert resp.status_code == 403


def test_hr_cannot_manage_hr_team(client, seed):
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/users", headers=hr_headers)
    assert resp.status_code == 403
    resp = client.put(f"/users/{seed['hr']['business_id']}", json={"full_name": "x"}, headers=hr_headers)
    assert resp.status_code == 403


def test_cannot_deactivate_self(client, seed):
    admin_headers = auth_headers(client, seed["admin"]["email"])
    resp = client.delete(f"/users/{seed['admin']['business_id']}", headers=admin_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "CANNOT_DEACTIVATE_SELF"
