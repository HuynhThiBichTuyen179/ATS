import enum as _pyenum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class DepartmentStatus(str, _pyenum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(Enum(DepartmentStatus), nullable=False, default=DepartmentStatus.ACTIVE)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    users = relationship("User", back_populates="department")
    jobs = relationship("Job", back_populates="department")
