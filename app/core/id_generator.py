"""Business ID generator - xem ats_system_design_v2.md CHANGE 03.

TUYET DOI khong dung SELECT MAX(id)+1 hoac last_id+1 (race condition).
Co che: bang dem rieng `id_sequences` + row lock (SELECT...FOR UPDATE) trong
cung transaction voi viec tao entity. Tren SQLite (dev/test), SQLAlchemy khong
emit FOR UPDATE that nen bo sung mot threading.Lock lam lop bao ve thu hai -
du de chay concurrency test dung trong 1 process.
"""

import threading

from sqlalchemy.orm import Session

from app.core.database import is_sqlite
from app.models.id_sequence import IDSequence

PREFIX_MAP = {
    "user": "USR",
    "department": "DEP",
    "job": "JOB",
    "candidate": "UV",
    "application": "APP",
    "resume": "CV",
    "ai_analysis": "AI",
    "interview": "INT",
    "offer": "OFF",
    "email_template": "EMT",
    "audit_log": "AUD",
    "candidate_source": "SRC",
}

_sqlite_lock = threading.Lock()


def _increment(db: Session, entity_type: str) -> int:
    seq = (
        db.query(IDSequence)
        .filter(IDSequence.entity_type == entity_type)
        .with_for_update()
        .first()
    )
    if seq is None:
        seq = IDSequence(entity_type=entity_type, last_number=0)
        db.add(seq)
        db.flush()
    seq.last_number += 1
    db.flush()
    return seq.last_number


def generate_business_id(db: Session, entity_type: str) -> str:
    if entity_type not in PREFIX_MAP:
        raise ValueError(f"Unknown entity_type for Business ID: {entity_type}")

    if is_sqlite:
        with _sqlite_lock:
            number = _increment(db, entity_type)
    else:
        number = _increment(db, entity_type)

    return f"{PREFIX_MAP[entity_type]}{number:04d}"
