from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class PasswordResetToken(Base):
    """Forgot/Reset Password (Section 22/23). Chi luu HASH (SHA-256) cua
    token, khong bao gio luu plaintext - giong nguyen tac da ap dung cho
    User.refresh_token_hash. token that (random, khong doan duoc) chi xuat
    hien trong link email gui cho candidate, khong luu lai trong DB.
    Khong co business_id: day la artifact bao mat noi bo, khong phai thuc the
    nghiep vu hien thi qua UI/URL business_id.
    """

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
