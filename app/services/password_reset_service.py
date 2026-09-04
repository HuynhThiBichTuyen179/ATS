"""v2.2 Section 22-25 - Forgot/Reset Password. Ap dung cho MOI role (Section
26: "Forgot Password: Own | Own | Own | Own"), khong chi rieng Candidate.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_password_reset_token, hash_password, hash_password_reset_token
from app.models.email_template import EmailTemplate
from app.models.enums import EmailTemplateStatus, EmailTemplateType
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services import audit_service, email_service


def request_password_reset(db: Session, email: str) -> None:
    """Section 24: KHONG leak account existence - luon xu ly nhu nhau (khong
    raise loi/tra thong tin khac nhau) du email co ton tai hay khong."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return

    raw_token, token_hash, expires_at = generate_password_reset_token()
    reset = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.add(reset)
    db.flush()
    audit_service.log(
        db, actor=user, action="PASSWORD_RESET_REQUESTED",
        entity_type="user", entity_business_id=user.business_id,
    )
    db.commit()

    template = (
        db.query(EmailTemplate)
        .filter(EmailTemplate.type == EmailTemplateType.PASSWORD_RESET, EmailTemplate.status == EmailTemplateStatus.ACTIVE)
        .first()
    )
    if not template:
        # Section EMAIL-7 (nguyen tac da co): chua co mau -> bo qua im lang,
        # khong lam fail luong forgot-password chinh.
        return

    # Dung api_url (not public_app_url) vi frontend v2 duoc chinh server FastAPI
    # nay serve truc tiep (app/static/index.html tai "/"), khong phai 1
    # frontend tach rieng chay port 3000 nhu public_app_url gia dinh.
    reset_link = f"{settings.api_url}/reset-password?token={raw_token}"
    variables = {
        "user_name": user.full_name,
        "reset_link": reset_link,
        "company_name": settings.company_name,
        "expiry_minutes": settings.password_reset_token_expiry_minutes,
    }
    subject, body = email_service.render_template(template.subject, template.content, variables)
    try:
        email_service.send_email(db, user, user.email, subject, body)
    except Exception:
        pass


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    token_hash = hash_password_reset_token(raw_token)
    reset = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    # Section 23: token phai con han VA chua tung duoc dung (one-time use).
    if not reset or reset.used_at is not None or reset.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_OR_EXPIRED_RESET_TOKEN")

    user = db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_OR_EXPIRED_RESET_TOKEN")

    user.password_hash = hash_password(new_password)
    # Section 25: invalidate refresh sessions dang co - buoc dang nhap lai
    # tren moi thiet bi sau khi doi mat khau.
    user.refresh_token_hash = None
    user.refresh_token_expires_at = None
    reset.used_at = now
    db.flush()

    audit_service.log(
        db, actor=user, action="PASSWORD_RESET_COMPLETED",
        entity_type="user", entity_business_id=user.business_id,
    )
    db.commit()
