from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.core.database import Base
from app.models.enums import CandidateSourceStatus


def _utcnow():
    return datetime.now(timezone.utc)


class CandidateSource(Base):
    """v2.2 System Configuration - danh muc "Nguon tuyen" quan ly qua DB thay
    vi hard-code o frontend (Section 17). Application.source (String tu do,
    da co san) tiep tuc luu ten nguon dang text de khong pha vo du lieu cu -
    bang nay chi la nguon "danh sach hop le" cho dropdown, khong doi kieu cot
    Application.source.
    """

    __tablename__ = "candidate_sources"

    id = Column(Integer, primary_key=True)
    business_id = Column(String(20), unique=True, nullable=False, index=True)

    name = Column(String(100), unique=True, nullable=False)
    # v2.3 Section 16/17: index - dropdown "Nguon ho so" luon loc status=ACTIVE.
    status = Column(Enum(CandidateSourceStatus), nullable=False, default=CandidateSourceStatus.ACTIVE, index=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
