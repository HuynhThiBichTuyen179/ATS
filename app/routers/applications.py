from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.core.time_utils import to_iso_utc
from app.deps.rbac import get_current_user, require_hr_manager_or_admin, require_hr_or_above
from app.models.application import Application
from app.models.candidate import Candidate, Gender
from app.models.candidate_source import CandidateSource
from app.models.department import Department
from app.models.enums import ApplicationStatus, ArchiveReason, CandidateSourceStatus, JobStatus, UserRole
from app.models.job import Job
from app.models.user import User
from app.schemas.application import (
    ApplicationOut,
    ApplicationUpdateRequest,
    ApplyRequest,
    ArchiveRequest,
    ResumeOut,
    UpdateStatusRequest,
)
from app.services import application_service, resume_service

router = APIRouter(prefix="/applications", tags=["applications"])


def _get_or_create_candidate(
    db: Session, user: User, full_name: str, email: str, phone: str,
    gender: str | None = None, skills_summary: str | None = None, experience_summary: str | None = None,
) -> Candidate:
    # gender/skills_summary/experience_summary: Candidate tu ung tuyen duoc
    # phep (khong bat buoc) tu khai bao them - truoc day chi HR nhap ho duoc
    # qua "Them ung vien" (candidate_service.py), luong tu ung tuyen nay
    # khong co cach nao dien duoc. Chi CAP NHAT neu Candidate da ton tai sẵn
    # va gia tri moi khac rong - khong ghi de thanh rong du lieu ho da co san
    # tu lan ung tuyen truoc chi vi lan nay bo trong.
    gender_enum = None
    if gender:
        try:
            gender_enum = Gender(gender)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_GENDER")

    candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
    if not candidate:
        # v2 changelog #16: dedupe theo email - neu da co Candidate voi email
        # nay (vd HR tao truoc do) thi dung lai, khong tao ban ghi trung.
        candidate = db.query(Candidate).filter(Candidate.email == email).first()
        if candidate and candidate.user_id is None:
            candidate.user_id = user.id
            db.flush()

    if candidate:
        if gender_enum is not None:
            candidate.gender = gender_enum
        if skills_summary:
            candidate.skills_summary = skills_summary
        if experience_summary:
            candidate.experience_summary = experience_summary
        db.flush()
        return candidate

    candidate = Candidate(
        business_id=generate_business_id(db, "candidate"),
        user_id=user.id,
        full_name=full_name,
        email=email,
        phone=phone,
        gender=gender_enum,
        skills_summary=skills_summary,
        experience_summary=experience_summary,
    )
    db.add(candidate)
    db.flush()
    return candidate


def _to_out(application: Application, is_new: bool = True) -> ApplicationOut:
    latest_analysis = next((a for a in application.ai_analyses if a.is_latest), None)
    return ApplicationOut(
        business_id=application.business_id,
        job_business_id=application.job.business_id,
        job_title=application.job.title,
        job_description=application.job.description,
        job_requirements=application.job.requirements,
        department_business_id=application.department.business_id if application.department else None,
        department_name=application.department.name if application.department else None,
        candidate_business_id=application.candidate.business_id,
        candidate_full_name=application.candidate.full_name,
        candidate_gender=application.candidate.gender.value if application.candidate.gender else None,
        candidate_email=application.candidate.email,
        candidate_phone=application.candidate.phone,
        candidate_skills_summary=application.candidate.skills_summary,
        candidate_experience_summary=application.candidate.experience_summary,
        desired_salary=float(application.desired_salary) if application.desired_salary is not None else None,
        status=application.status.value,
        is_new=is_new,
        source_business_id=application.candidate_source.business_id if application.candidate_source else None,
        source=application.source,
        match_score=latest_analysis.match_score if latest_analysis else None,
        needs_manual_review=bool(application.needs_manual_review),
        has_resume=application.resume is not None,
        resume_file_name=application.resume.file_name if application.resume else None,
        resume_text=application.resume.extracted_text if application.resume else None,
        applied_at=to_iso_utc(application.applied_at),
    )


@router.post("", response_model=ApplicationOut)
def apply(
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ONLY_CANDIDATE_CAN_APPLY")
    if not payload.ai_consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "AI_CONSENT_REQUIRED")

    job = db.query(Job).filter(Job.business_id == payload.job_business_id).first()
    if not job or job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND_OR_NOT_PUBLISHED")

    # v2.3 Section 9.2/21: bat buoc chon Nguon ho so hop le VA dang ACTIVE -
    # khong tin frontend, backend tu xac thuc lai (Section 9.4: TC-SOURCE-004
    # nguon INACTIVE khong duoc chon).
    candidate_source = (
        db.query(CandidateSource).filter(CandidateSource.business_id == payload.source_business_id).first()
    )
    if not candidate_source:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "SOURCE_REQUIRED")
    if candidate_source.status != CandidateSourceStatus.ACTIVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "SOURCE_NOT_ACTIVE")

    candidate = _get_or_create_candidate(
        db, current_user, payload.candidate_full_name, payload.candidate_email, payload.candidate_phone,
        gender=payload.candidate_gender, skills_summary=payload.candidate_skills_summary,
        experience_summary=payload.candidate_experience_summary,
    )

    application, is_new = application_service.apply_for_job(
        db, candidate, job, candidate_source, idempotency_key, actor=current_user,
        resume_text=payload.resume_text, desired_salary=payload.desired_salary,
    )
    return _to_out(application, is_new)


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    job_business_id: str | None = None,
    candidate_business_id: str | None = None,
    department_business_id: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HR: chi Job/Application duoc gan. HR Manager/Admin: toan bo. Candidate:
    chi Application cua chinh minh (phuc vu man hinh 'Ho so ung tuyen cua toi').
    job_business_id/search phuc vu bo loc + tim kiem tren Kanban.
    candidate_business_id (v2.3 Section 7.7): phuc vu Candidate Detail -
    "Application History" (toan bo Application cua 1 Candidate, khong overwrite
    Application cu) - van ap dung scoping HR/Candidate nhu tren, khong bypass.
    department_business_id/status_filter: phuc vu "Thanh vien phong ban" -
    liet ke ung vien da HIRED thuoc 1 phong ban cu the.
    """
    query = db.query(Application)
    if current_user.role == UserRole.HR:
        query = query.filter(Application.assigned_hr_id == current_user.id)
    elif current_user.role == UserRole.CANDIDATE:
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if not candidate:
            return []
        query = query.filter(Application.candidate_id == candidate.id)

    if job_business_id:
        job = db.query(Job).filter(Job.business_id == job_business_id).first()
        query = query.filter(Application.job_id == (job.id if job else -1))

    if candidate_business_id:
        candidate = db.query(Candidate).filter(Candidate.business_id == candidate_business_id).first()
        query = query.filter(Application.candidate_id == (candidate.id if candidate else -1))

    if department_business_id:
        department = db.query(Department).filter(Department.business_id == department_business_id).first()
        query = query.filter(Application.department_id == (department.id if department else -1))

    if status_filter:
        try:
            query = query.filter(Application.status == ApplicationStatus(status_filter))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    if search:
        like = f"%{search.strip()}%"
        query = query.join(Candidate).filter(
            (Candidate.full_name.ilike(like)) | (Candidate.email.ilike(like)) | (Candidate.phone.ilike(like))
        )

    return [_to_out(a) for a in query.order_by(Application.id.desc()).all()]


@router.get("/{application_business_id}", response_model=ApplicationOut)
def get_application(
    application_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    if current_user.role == UserRole.CANDIDATE and application.candidate.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_APPLICATION")
    return _to_out(application)


def _check_resume_access(current_user: User, application: Application) -> None:
    # Section 45: Candidate chi xem/upload CV cua chinh minh; HR chi trong
    # pham vi duoc gan; HR_MANAGER/ADMIN khong gioi han.
    if current_user.role == UserRole.CANDIDATE:
        if application.candidate.user_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_APPLICATION")
    elif current_user.role == UserRole.HR:
        if application.assigned_hr_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    elif current_user.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")


@router.post("/{application_business_id}/resume", response_model=ResumeOut)
async def upload_resume(
    application_business_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")

    # v2.2 Section 1/5: cho phep ca Candidate (ho so cua chinh minh) lan HR+
    # (trong pham vi duoc gan) upload CV thay ung vien luc tao ho so tu form
    # "Them ung vien" - truoc do chi Candidate tu upload duoc.
    _check_resume_access(current_user, application)

    resume = await resume_service.upload_resume_file(db, application, file, current_user)
    return ResumeOut(
        business_id=resume.business_id,
        file_name=resume.file_name,
        file_type=resume.file_type,
        extracted_text=resume.extracted_text,
        extracted_chars=len(resume.extracted_text or ""),
        uploaded_at=to_iso_utc(resume.uploaded_at),
    )


@router.get("/{application_business_id}/resume", response_model=ResumeOut)
def get_resume(
    application_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    _check_resume_access(current_user, application)
    if not application.resume:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "RESUME_NOT_FOUND")

    resume = application.resume
    return ResumeOut(
        business_id=resume.business_id,
        file_name=resume.file_name,
        file_type=resume.file_type,
        extracted_text=resume.extracted_text,
        extracted_chars=len(resume.extracted_text or ""),
        uploaded_at=to_iso_utc(resume.uploaded_at),
    )


@router.put("/{application_business_id}/status", response_model=ApplicationOut)
def update_status(
    application_business_id: str,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    new_status = ApplicationStatus(payload.status)
    application = application_service.update_status(db, application, new_status, current_user, payload.reason)
    return _to_out(application)


@router.put("/{application_business_id}", response_model=ApplicationOut)
def update_application(
    application_business_id: str,
    payload: ApplicationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    """v2.3 Section 5/18 - sua Luong mong muon / Nguon ho so tu Candidate
    Table. KHONG cho doi Job/Candidate (Section 5: khong pha vo relationship)."""
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    if current_user.role == UserRole.HR and application.assigned_hr_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")

    candidate_source = None
    if payload.source_business_id is not None:
        candidate_source = (
            db.query(CandidateSource).filter(CandidateSource.business_id == payload.source_business_id).first()
        )
        if not candidate_source:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "SOURCE_REQUIRED")
        if candidate_source.status != CandidateSourceStatus.ACTIVE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "SOURCE_NOT_ACTIVE")

    application = application_service.update_application(
        db, current_user, application, desired_salary=payload.desired_salary, candidate_source=candidate_source
    )
    return _to_out(application)


@router.put("/{application_business_id}/withdraw", response_model=ApplicationOut)
def withdraw(
    application_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ONLY_CANDIDATE_CAN_WITHDRAW")
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    if application.candidate.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_APPLICATION")
    application = application_service.withdraw(db, application, current_user)
    return _to_out(application)


@router.put("/{application_business_id}/archive", response_model=ApplicationOut)
def archive(
    application_business_id: str,
    payload: ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    try:
        reason = ArchiveReason(payload.archive_reason)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_ARCHIVE_REASON")
    application = application_service.archive(db, application, current_user, reason)
    return _to_out(application)
