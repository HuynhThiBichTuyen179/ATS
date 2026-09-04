import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.models.audit_log import AuditLog
from app.models.user import User


def log(
    db: Session,
    actor: User,
    action: str,
    entity_type: str,
    entity_business_id: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> AuditLog:
    """Ghi 1 dong audit_logs. KHONG commit - nam trong cung transaction voi
    hanh dong nghiep vu goi no, de dam bao audit va thay doi du lieu la atomic.
    """
    entry = AuditLog(
        business_id=generate_business_id(db, "audit_log"),
        actor_user_id=actor.id,
        action=action,
        entity_type=entity_type,
        entity_business_id=entity_business_id,
        before_data=json.dumps(before, default=str) if before is not None else None,
        after_data=json.dumps(after, default=str) if after is not None else None,
        reason=reason,
    )
    db.add(entry)
    db.flush()
    return entry
