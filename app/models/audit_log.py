from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # vd OFFER_APPROVED, APPLICATION_REAPPLIED
    entity_type = Column(String(50), nullable=False)  # vd "offer", "application"
    entity_business_id = Column(String(20), nullable=False)

    before_data = Column(Text, nullable=True)  # JSON string
    after_data = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
