import enum as _pyenum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import CandidateStatus


def _utcnow():
    return datetime.now(timezone.utc)


class Gender(str, _pyenum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    full_name = Column(String(100), nullable=False)
    # v2 changelog #16: email UNIQUE de dedupe candidate (upsert khi trung o service layer)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    gender = Column(Enum(Gender), nullable=True)

    # v2.2: ho so ung vien do HR/HR_MANAGER/ADMIN tao truc tiep (khac luong
    # ung tuyen tu than qua Candidate Portal) - Section 1/37.
    skills_summary = Column(Text, nullable=True)
    experience_summary = Column(Text, nullable=True)
    status = Column(Enum(CandidateStatus), nullable=False, default=CandidateStatus.ACTIVE)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    applications = relationship("Application", back_populates="candidate")
