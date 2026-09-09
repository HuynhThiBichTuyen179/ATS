from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.deps.rbac import require_hr_manager_or_admin
from app.models.application import Application
from app.models.department import Department, DepartmentStatus
from app.models.job import Job
from app.models.user import User
from app.services import audit_service

router = APIRouter(prefix="/departments", tags=["departments"])


def _to_out(d: Department) -> dict:
    return {
        "business_id": d.business_id,
        "name": d.name,
        "description": d.description,
        "status": d.status.value,
    }


@router.post("")
def create_department(
    name: str,
    description: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Department Name khong duoc duplicate.
    if db.query(Department).filter(Department.name == name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "DEPARTMENT_NAME_ALREADY_EXISTS")

    department = Department(business_id=generate_business_id(db, "department"), name=name, description=description)
    db.add(department)
    db.flush()
    audit_service.log(
        db, actor=current_user, action="DEPARTMENT_CREATED",
        entity_type="department", entity_business_id=department.business_id,
        after=_to_out(department),
    )
    db.commit()
    db.refresh(department)
    return _to_out(department)


@router.get("")
def list_departments(db: Session = Depends(get_db)):
    return [_to_out(d) for d in db.query(Department).all()]


@router.put("/{department_business_id}")
def update_department(
    department_business_id: str,
    name: str | None = None,
    description: str | None = None,
    status_value: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    department = db.query(Department).filter(Department.business_id == department_business_id).first()
    if not department:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DEPARTMENT_NOT_FOUND")

    before = _to_out(department)
    if name is not None and name != department.name:
        if db.query(Department).filter(Department.name == name, Department.id != department.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "DEPARTMENT_NAME_ALREADY_EXISTS")
        department.name = name
    if description is not None:
        department.description = description
    if status_value is not None:
        try:
            department.status = DepartmentStatus(status_value)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    db.flush()
    audit_service.log(
        db, actor=current_user, action="DEPARTMENT_UPDATED",
        entity_type="department", entity_business_id=department.business_id,
        before=before, after=_to_out(department),
    )
    db.commit()
    db.refresh(department)
    return _to_out(department)


@router.delete("/{department_business_id}")
def delete_department(
    department_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Khong xoa "an toan" Department dang duoc Job/Application su dung - luon
    # soft-delete (status=INACTIVE) thay vi xoa vat ly, tranh vo FK va mat du
    # lieu tham chieu.
    department = db.query(Department).filter(Department.business_id == department_business_id).first()
    if not department:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DEPARTMENT_NOT_FOUND")

    in_use = (
        db.query(Job).filter(Job.department_id == department.id).first()
        or db.query(Application).filter(Application.department_id == department.id).first()
    )
    before = _to_out(department)
    department.status = DepartmentStatus.INACTIVE
    db.flush()
    audit_service.log(
        db, actor=current_user, action="DEPARTMENT_DELETED",
        entity_type="department", entity_business_id=department.business_id,
        before=before, after=_to_out(department),
        reason="Soft-delete (INACTIVE)" + (" - dang duoc Job/Application su dung" if in_use else ""),
    )
    db.commit()
    return {"business_id": department.business_id, "status": department.status.value, "in_use": bool(in_use)}
