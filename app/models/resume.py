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

    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, unique=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)  # JSON string 

    uploaded_at = Column(DateTime, default=_utcnow, nullable=False)

    application = relationship("Application", back_populates="resume")
