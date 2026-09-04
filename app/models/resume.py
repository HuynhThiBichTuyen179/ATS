from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    # v2.3 Section 16/17: index cho query "CV cua 1 Candidate" (Candidate
    # Detail - Application History). application_id da co index tu unique=True.
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    # 1 Resume rieng cho tung Application (v2 changelog #13) - khong reuse file cu
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, unique=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)  # JSON string (SQLite khong co JSON type rieng)

    uploaded_at = Column(DateTime, default=_utcnow, nullable=False)

    application = relationship("Application", back_populates="resume")
