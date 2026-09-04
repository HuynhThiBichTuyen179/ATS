"""GET /audit-logs - chi ADMIN (BGD) duoc xem, theo yeu cau nguoi dung thu hep
tu HR_MANAGER+ADMIN xuong chi ADMIN."""

from tests.conftest import auth_headers


def test_only_admin_can_view_audit_logs(client, seed):
    admin_headers = auth_headers(client, seed["admin"]["email"])
    resp = client.get("/audit-logs", headers=admin_headers)
    assert resp.status_code == 200, resp.text

    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    resp = client.get("/audit-logs", headers=hrm_headers)
    assert resp.status_code == 403

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.get("/audit-logs", headers=hr_headers)
    assert resp.status_code == 403


def test_audit_log_resolves_actor_name(client, seed):
    admin_headers = auth_headers(client, seed["admin"]["email"])
    # Tao 1 audit log that qua hanh dong tao phong ban.
    client.post(
        "/departments",
        params={"name": "Phong ban test audit", "description": "x"},
        headers=admin_headers,
    )
    resp = client.get("/audit-logs", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    logs = resp.json()
    assert len(logs) >= 1
    log = logs[0]
    assert "actor_business_id" in log
    assert "actor_name" in log
    assert log["actor_name"] != "Không xác định"
