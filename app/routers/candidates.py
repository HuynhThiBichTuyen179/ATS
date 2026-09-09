from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.rbac import get_current_user, require_hr_or_above
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.candidate import CandidateCreateRequest, CandidateOut, CandidateUpdateRequest
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _to_out(c: Candidate) -> CandidateOut:
    return CandidateOut(
        business_id=c.business_id,
        full_name=c.full_name,
        gender=c.gender.value if c.gender else None,
        email=c.email,
        phone=c.phone,
        skills_summary=c.skills_summary,
        experience_summary=c.experience_summary,
        status=c.status.value,
    )


@router.post("")
def create_candidate(
    payload: CandidateCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    # HR/HR_MANAGER/ADMIN duoc tao; Candidate KHONG duoc tao ho so ung vien
    # khac (da chan qua require_hr_or_above - CANDIDATE khong nam trong danh
    # sach role duoc phep cua dependency nay).
    candidate, application = candidate_service.create_candidate_with_application(
        db, current_user,
        full_name=payload.full_name, email=payload.email, phone=payload.phone, gender=payload.gender,
        job_business_id=payload.job_business_id, desired_salary=payload.desired_salary, source=payload.source,
        skills_summary=payload.skills_summary, experience_summary=payload.experience_summary,
    )
    # Tra ve ca application_business_id de frontend upload CV ngay sau khi tao
    # ma khong can query lai - CandidateOut khong the mo rong field nay vi 1
    # Candidate co the co nhieu Application, chi Application VUA TAO o day
    # moi co y nghia truc tiep.
    return {**_to_out(candidate).model_dump(), "application_business_id": application.business_id}


@router.get("", response_model=list[CandidateOut])
def list_candidates(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    # Search theo ten/email/SDT.
    query = db.query(Candidate)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (Candidate.full_name.ilike(like)) | (Candidate.email.ilike(like)) | (Candidate.phone.ilike(like))
        )
    return [_to_out(c) for c in query.order_by(Candidate.id.desc()).all()]


def _get_candidate_or_404(db: Session, candidate_business_id: str) -> Candidate:
    candidate = db.query(Candidate).filter(Candidate.business_id == candidate_business_id).first()
    if not candidate:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CANDIDATE_NOT_FOUND")
    return candidate


@router.get("/{candidate_business_id}", response_model=CandidateOut)
def get_candidate(
    candidate_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = _get_candidate_or_404(db, candidate_business_id)
    if current_user.role == UserRole.CANDIDATE and candidate.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_PROFILE")
    return _to_out(candidate)


@router.put("/{candidate_business_id}", response_model=CandidateOut)
def update_candidate(
    candidate_business_id: str,
    payload: CandidateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = _get_candidate_or_404(db, candidate_business_id)
    if current_user.role == UserRole.CANDIDATE and candidate.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_PROFILE")
    # RBAC "Sua Candidate" = Own/Scoped/Full/Full - HR chi duoc sua Candidate
    # co it nhat 1 Application dang assigned_hr_id cho minh (cung 1 quy uoc
    # "Scoped" dung xuyen suot applications/interview/ai/resumes router).
    if current_user.role == UserRole.HR:
        has_assigned = (
            db.query(Application)
            .filter(Application.candidate_id == candidate.id, Application.assigned_hr_id == current_user.id)
            .first()
        )
        if not has_assigned:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_ASSIGNED_TO_THIS_CANDIDATE")
    candidate = candidate_service.update_candidate(
        db, current_user, candidate,
        full_name=payload.full_name, gender=payload.gender, phone=payload.phone,
        skills_summary=payload.skills_summary, experience_summary=payload.experience_summary,
    )
    return _to_out(candidate)


@router.delete("/{candidate_business_id}")
def delete_candidate(
    candidate_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    candidate = _get_candidate_or_404(db, candidate_business_id)
    candidate = candidate_service.archive_candidate(db, current_user, candidate)
    return {"business_id": candidate.business_id, "status": candidate.status.value}
