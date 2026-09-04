"""v2.2 Section 22-25/47 - Forgot/Reset Password."""

from app.models.password_reset_token import PasswordResetToken
from tests.conftest import register_and_login_candidate


def _get_raw_token_for_latest_request(monkeypatch_capture=None):
    """Test khong the doc raw token tu response (dung theo Section 24 - khong
    leak thong tin qua API). Doc truc tiep tu DB bang cach patch security de
    lay raw token that trong luc test, giu nguyen hanh vi san xuat."""
    pass


def test_forgot_password_never_leaks_account_existence(client, seed):
    resp_exists = client.post("/auth/forgot-password", json={"email": seed["hr"]["email"]})
    resp_not_exists = client.post("/auth/forgot-password", json={"email": "khong-ton-tai@example.com"})
    assert resp_exists.status_code == 200
    assert resp_not_exists.status_code == 200
    assert resp_exists.json() == resp_not_exists.json(), "Response phai giong het nhau, khong duoc tiet lo email co ton tai"


def test_forgot_password_creates_hashed_token_with_expiry(client, seed, db):
    register_and_login_candidate(client, "uv-forgot1@example.com")
    resp = client.post("/auth/forgot-password", json={"email": "uv-forgot1@example.com"})
    assert resp.status_code == 200

    token_row = db.query(PasswordResetToken).order_by(PasswordResetToken.id.desc()).first()
    assert token_row is not None
    assert token_row.used_at is None
    assert len(token_row.token_hash) == 64  # sha256 hex digest
    assert token_row.expires_at is not None


def test_reset_password_end_to_end_with_real_token(client, seed, db):
    import secrets

    from app.core.security import hash_password_reset_token
    from app.models.password_reset_token import PasswordResetToken as PRT
    from app.models.user import User

    register_and_login_candidate(client, "uv-forgot2@example.com")
    user = db.query(User).filter(User.email == "uv-forgot2@example.com").first()

    # Tao token that (giong request_password_reset lam) de kiem tra full flow
    # reset ma khong phu thuoc vao viec doc token tu email that.
    from datetime import datetime, timedelta, timezone
    raw = secrets.token_urlsafe(48)
    token = PRT(user_id=user.id, token_hash=hash_password_reset_token(raw), expires_at=datetime.now(timezone.utc) + timedelta(minutes=30))
    db.add(token)
    db.commit()

    resp = client.post("/auth/reset-password", json={"token": raw, "new_password": "NewPass123"})
    assert resp.status_code == 200, resp.text

    # Mat khau cu khong con dung.
    resp = client.post("/auth/login", json={"email": "uv-forgot2@example.com", "password": "Password@123"})
    assert resp.status_code == 401
    # Mat khau moi dung.
    resp = client.post("/auth/login", json={"email": "uv-forgot2@example.com", "password": "NewPass123"})
    assert resp.status_code == 200

    # Token one-time-use: dung lai lan 2 phai that bai.
    resp = client.post("/auth/reset-password", json={"token": raw, "new_password": "AnotherPass123"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "INVALID_OR_EXPIRED_RESET_TOKEN"


def test_reset_password_expired_token_rejected(client, seed, db):
    import secrets
    from datetime import datetime, timedelta, timezone

    from app.core.security import hash_password_reset_token
    from app.models.password_reset_token import PasswordResetToken as PRT
    from app.models.user import User

    register_and_login_candidate(client, "uv-forgot3@example.com")
    user = db.query(User).filter(User.email == "uv-forgot3@example.com").first()

    raw = secrets.token_urlsafe(48)
    token = PRT(user_id=user.id, token_hash=hash_password_reset_token(raw), expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    db.add(token)
    db.commit()

    resp = client.post("/auth/reset-password", json={"token": raw, "new_password": "NewPass123"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "INVALID_OR_EXPIRED_RESET_TOKEN"


def test_reset_password_weak_password_rejected(client, seed):
    resp = client.post("/auth/reset-password", json={"token": "gia-vi-du", "new_password": "12345678"})
    assert resp.status_code == 422


def test_seed_data_includes_password_reset_template():
    """BUG FIX: truoc day DEMO_EMAIL_TEMPLATES (app/seed_data.py) khong co
    loai PASSWORD_RESET nao ca -> request_password_reset() luon tim thay
    template=None va return som, khong bao gio thuc su goi send_email() (xem
    'if not template: return' trong password_reset_service.py) - forgot
    password luon phan hoi 'thanh cong' nhung KHONG GUI EMAIL NAO CA. Test
    nay khoa lai: danh sach seed BAT BUOC phai co 1 mau PASSWORD_RESET."""
    from app.models.enums import EmailTemplateType
    from app.seed_data import DEMO_EMAIL_TEMPLATES

    types = [t[0] for t in DEMO_EMAIL_TEMPLATES]
    assert EmailTemplateType.PASSWORD_RESET in types


def test_forgot_password_actually_attempts_send_when_template_exists(client, seed, db):
    """Neu co mau PASSWORD_RESET ACTIVE, request_password_reset() phai thuc
    su goi toi email_service.send_email() (ghi 1 dong audit_log EMAIL_SENT
    hoac EMAIL_FAILED) thay vi im lang bo qua."""
    from app.core.id_generator import generate_business_id
    from app.models.audit_log import AuditLog
    from app.models.email_template import EmailTemplate
    from app.models.enums import EmailTemplateStatus, EmailTemplateType
    from app.models.user import User

    admin = db.query(User).filter(User.business_id == seed["admin"]["business_id"]).first()
    db.add(EmailTemplate(
        business_id=generate_business_id(db, "email_template"),
        name="Dat lai mat khau", type=EmailTemplateType.PASSWORD_RESET,
        subject="[{{company_name}}] Dat lai mat khau",
        content="Chao {{user_name}}, {{reset_link}}, het han sau {{expiry_minutes}} phut.",
        status=EmailTemplateStatus.ACTIVE, created_by=admin.id,
    ))
    db.commit()

    before = db.query(AuditLog).filter(AuditLog.action.in_(["EMAIL_SENT", "EMAIL_FAILED"])).count()
    resp = client.post("/auth/forgot-password", json={"email": seed["hr"]["email"]})
    assert resp.status_code == 200
    after = db.query(AuditLog).filter(AuditLog.action.in_(["EMAIL_SENT", "EMAIL_FAILED"])).count()
    assert after == before + 1
