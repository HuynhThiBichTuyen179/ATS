from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import EmploymentType, JobStatus


def _utcnow():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)
    # v2 Phan 20.2 / changelog #24: slug cho URL public /jobs/{job-slug}
    slug = Column(String(160), unique=True, nullable=True, index=True)

    title = Column(String(150), nullable=False)
    # v2.3 Section 16/17: index - Public Job List loc theo department_id,
    # publish/pipeline-filter loc theo status thuong xuyen.
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    salary_min = Column(Numeric(12, 2))
    salary_max = Column(Numeric(12, 2))
    quantity = Column(Integer, nullable=False, default=1)
    location = Column(String(150), nullable=False)
    employment_type = Column(Enum(EmploymentType), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.DRAFT, index=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_hr_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    published_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    department = relationship("Department", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
