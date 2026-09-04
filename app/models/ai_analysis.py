from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    # v2 Phan 5.7: KHONG con Unique 1-1 - cho phep nhieu lan re-run AI cho cung 1
    # application, giu lai lich su de audit khi doi model/prompt.
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    is_latest = Column(Boolean, nullable=False, default=True)

    provider = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    match_score = Column(Integer, nullable=False)
    matched_skills = Column(Text, nullable=True)  # JSON string
    missing_skills = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    experience_summary = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    analysis_result = Column(Text, nullable=True)  # raw JSON payload

    created_at = Column(DateTime, default=_utcnow, nullable=False)

    application = relationship("Application", back_populates="ai_analyses")
