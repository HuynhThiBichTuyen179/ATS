from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.models.enums import EmailTemplateStatus, EmailTemplateType


def _utcnow():
    return datetime.now(timezone.utc)


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    type = Column(Enum(EmailTemplateType), nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(EmailTemplateStatus), nullable=False, default=EmailTemplateStatus.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
