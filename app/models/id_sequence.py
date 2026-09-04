from sqlalchemy import Column, Integer, String

from app.core.database import Base


class IDSequence(Base):
    """Bo dem rieng cho tung entity_type, dung de sinh Business ID
    (vd USR0001, JOB0001) an toan voi concurrency. Xem app/core/id_generator.py.
    """

    __tablename__ = "id_sequences"

    entity_type = Column(String(20), primary_key=True)
    last_number = Column(Integer, nullable=False, default=0)
