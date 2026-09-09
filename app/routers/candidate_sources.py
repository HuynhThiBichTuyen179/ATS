from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.deps.rbac import get_current_user, require_hr_manager_or_admin
from app.models.candidate_source import CandidateSource
from app.models.enums import CandidateSourceStatus
from app.models.user import User
from app.schemas.candidate_source import (
    CandidateSourceCreateRequest,
    CandidateSourceOut,
    CandidateSourceUpdateRequest,
)
from app.services import audit_service

router = APIRouter(prefix="/candidate-sources", tags=["candidate-sources"])


def _to_out(s: CandidateSource) -> CandidateSourceOut:
    return CandidateSourceOut(business_id=s.business_id, name=s.name, status=s.status.value)


@router.post("", response_model=CandidateSourceOut)
def create_source(
    payload: CandidateSourceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    if db.query(CandidateSource).filter(CandidateSource.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "SOURCE_NAME_ALREADY_EXISTS")
    source = CandidateSource(business_id=generate_business_id(db, "candidate_source"), name=payload.name)
    db.add(source)
    db.flush()
    audit_service.log(
        db, actor=current_user, action="SOURCE_CREATED",
        entity_type="candidate_source", entity_business_id=source.business_id,
        after={"name": source.name},
    )
    db.commit()
    db.refresh(source)
    return _to_out(source)


@router.get("", response_model=list[CandidateSourceOut])
def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # HR/HR_MANAGER "View", Admin "CRUD" - moi vai tro noi bo deu xem duoc de
    # dung trong dropdown form Them ung vien.
    # Candidate PHAI xem duoc danh sach Nguon ho so (chi cac nguon ACTIVE,
    # khong xem duoc nguon da INACTIVE/quan ly) de chon o form Ung tuyen - day
    # la quyen XEM read-only de tu phuc vu, khong phai quyen "Candidate Source
    # Management" (van chi HR+ trong RBAC table). Neu chan hoan toan CANDIDATE
    # thi dropdown "Nguon ho so" se luon rong khi Candidate mo form Ung
    # tuyen, du da cau hinh san nguon.
    if current_user.role.value == "CANDIDATE":
        return [_to_out(s) for s in db.query(CandidateSource).filter(CandidateSource.status == CandidateSourceStatus.ACTIVE).order_by(CandidateSource.id).all()]
    return [_to_out(s) for s in db.query(CandidateSource).order_by(CandidateSource.id).all()]


@router.put("/{source_business_id}", response_model=CandidateSourceOut)
def update_source(
    source_business_id: str,
    payload: CandidateSourceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    source = db.query(CandidateSource).filter(CandidateSource.business_id == source_business_id).first()
    if not source:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SOURCE_NOT_FOUND")

    before = {"name": source.name, "status": source.status.value}
    if payload.name is not None and payload.name != source.name:
        if db.query(CandidateSource).filter(CandidateSource.name == payload.name, CandidateSource.id != source.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "SOURCE_NAME_ALREADY_EXISTS")
        source.name = payload.name
    if payload.status is not None:
        try:
            source.status = CandidateSourceStatus(payload.status)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    db.flush()
    audit_service.log(
        db, actor=current_user, action="SOURCE_UPDATED",
        entity_type="candidate_source", entity_business_id=source.business_id,
        before=before, after={"name": source.name, "status": source.status.value},
    )
    db.commit()
    db.refresh(source)
    return _to_out(source)


@router.delete("/{source_business_id}")
def delete_source(
    source_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Soft-delete (INACTIVE), khong xoa cung - Application.source_id (FK) van
    # tro toi ban ghi nay de bao toan lich su/bao cao, Application.source la
    # snapshot text tai thoi diem nop don nen cung khong bi anh huong; nhat quan
    # voi cach soft-delete cua Department/User.
    source = db.query(CandidateSource).filter(CandidateSource.business_id == source_business_id).first()
    if not source:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SOURCE_NOT_FOUND")

    before = {"status": source.status.value}
    source.status = CandidateSourceStatus.INACTIVE
    db.flush()
    audit_service.log(
        db, actor=current_user, action="SOURCE_DELETED",
        entity_type="candidate_source", entity_business_id=source.business_id,
        before=before, after={"status": source.status.value}, reason="Soft-delete (INACTIVE)",
    )
    db.commit()
    return {"business_id": source.business_id, "status": source.status.value}
