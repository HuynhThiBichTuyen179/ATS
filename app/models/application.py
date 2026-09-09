from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus, ArchiveReason


def _utcnow():
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        # Idempotency: cung candidate + cung Idempotency-Key
        # header -> tra ve application da tao, khong tao ban ghi moi. NULL duoc
        # phep lap lai (nhieu request khong gui header van tao application binh thuong) 
        # vi UNIQUE coi nhieu NULL la khac nhau tren ca SQLite lan MySQL.
        UniqueConstraint("candidate_id", "idempotency_key", name="uq_application_candidate_idem"),
    )

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    # index tren cac cot dung de loc/join thuong xuyen
    # (Pipeline/Kanban loc theo job_id+status, Candidate Table/scoping loc
    # theo candidate_id, bao cao Nguon loc theo source_id).
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    # mac dinh ke thua tu Job.department_id luc tao ("Job Department =
    # Application Department"), khong cho override tu do o form.
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    desired_salary = Column(Numeric(12, 2), nullable=True)
    
    source_id = Column(Integer, ForeignKey("candidate_sources.id"), nullable=True, index=True)
    source = Column(String(100), nullable=True)

    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.NEW, index=True)
    match_score = Column(Integer, nullable=True)
    assigned_hr_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Re-apply cung mot Job luon duoc phep - moi lan Apply hop le tao 1 dong moi,
    # khong overwrite Application cu (immutable historical record).
    needs_manual_review = Column(Integer, default=0, nullable=False)  # 0/1 (bool cho SQLite)
    archive_reason = Column(Enum(ArchiveReason), nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)

    applied_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    department = relationship("Department")
    candidate_source = relationship("CandidateSource")
    resume = relationship("Resume", back_populates="application", uselist=False)
    ai_analyses = relationship("AIAnalysis", back_populates="application")
    interviews = relationship("Interview", back_populates="application")
    offers = relationship("Offer", back_populates="application")
