from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import InterviewStatus, InterviewType


def _utcnow():
    return datetime.now(timezone.utc)


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # scheduled_at = gio bat dau (start_time). v2.2 bo sung end_time de kiem
    # tra conflict (Section 32: Start < End, trung lich Candidate/Interviewer).
    scheduled_at = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    interview_type = Column(Enum(InterviewType), nullable=False, default=InterviewType.ONLINE)
    location = Column(String(255), nullable=True)
    meeting_link = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(InterviewStatus), nullable=False, default=InterviewStatus.SCHEDULED)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    application = relationship("Application", back_populates="interviews")
    interviewer = relationship("User")
