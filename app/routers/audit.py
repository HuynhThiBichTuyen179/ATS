from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time_utils import to_iso_utc
from app.deps.rbac import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(
    entity_type: str | None = None,
    entity_business_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_business_id:
        query = query.filter(AuditLog.entity_business_id == entity_business_id)
    logs = query.order_by(AuditLog.id.desc()).all()
    # Fix: truoc day tra thang actor_user_id (khoa ky thuat noi bo, VD "3"),
    # khong ai doc hieu duoc "ai da lam" - nay resolve ra business_id + ten
    # that de UI hien thi ro "Doi tuong thuc hien".
    actor_ids = {log.actor_user_id for log in logs}
    actors = {u.id: u for u in db.query(User).filter(User.id.in_(actor_ids)).all()} if actor_ids else {}
    return [
        {
            "business_id": log.business_id,
            "actor_business_id": actors[log.actor_user_id].business_id if log.actor_user_id in actors else None,
            "actor_name": actors[log.actor_user_id].full_name if log.actor_user_id in actors else "Không xác định",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_business_id": log.entity_business_id,
            "reason": log.reason,
            "created_at": to_iso_utc(log.created_at),
        }
        for log in logs
    ]
