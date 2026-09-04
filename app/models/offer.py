from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import OfferStatus


def _utcnow():
    return datetime.now(timezone.utc)


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        # CHANGE 01, muc 4/13: approver_id PHAI khac creator_id. NULL van hop le
        # (chua submit/chua duyet) vi so sanh voi NULL tra ve UNKNOWN, khong vi
        # pham CHECK. Day la lop bao ve o DB, ben canh enforce o service layer.
        CheckConstraint(
            "approver_id IS NULL OR approver_id != creator_id",
            name="ck_offer_approver_not_creator",
        ),
    )

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    # CHANGE 01: bat buoc phan biet nguoi tao va nguoi duyet
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    salary = Column(Numeric(12, 2), nullable=False)
    probation_salary = Column(Numeric(12, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    offer_file = Column(String(255), nullable=True)

    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.DRAFT)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    application = relationship("Application", back_populates="offers")
