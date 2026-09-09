from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.core.time_utils import to_iso_utc
from app.deps.rbac import get_current_user, get_current_user_optional, require_hr_manager_or_admin
from app.models.department import Department
from app.models.enums import EmploymentType, JobStatus
from app.models.enums import UserRole
from app.models.job import Job
from app.models.user import User
from app.schemas.job import AssignHrRequest, JobCreateRequest, JobOut, JobUpdateRequest
from app.services import audit_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _slugify(title: str, business_id: str) -> str:
    base = "-".join(title.strip().lower().split())
    base = "".join(c for c in base if c.isalnum() or c == "-")
    return f"{base}-{business_id.lower()}"


def _to_out(db: Session, job: Job) -> JobOut:
    department = db.get(Department, job.department_id)
    assigned_hr = db.get(User, job.assigned_hr_id) if job.assigned_hr_id else None
    return JobOut(
        business_id=job.business_id,
        title=job.title,
        department_business_id=department.business_id if department else "",
        department_name=department.name if department else None,
        description=job.description,
        requirements=job.requirements,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        quantity=job.quantity,
        location=job.location,
        employment_type=job.employment_type.value,
        status=job.status.value,
        deadline=to_iso_utc(job.deadline),
        published_at=to_iso_utc(job.published_at),
        created_at=to_iso_utc(job.created_at),
        assigned_hr_business_id=assigned_hr.business_id if assigned_hr else None,
        assigned_hr_name=assigned_hr.full_name if assigned_hr else None,
    )


@router.post("", response_model=JobOut)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    department = db.query(Department).filter(Department.business_id == payload.department_business_id).first()
    if not department:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DEPARTMENT_NOT_FOUND")

    assigned_hr = None
    if payload.assigned_hr_business_id:
        assigned_hr = db.query(User).filter(User.business_id == payload.assigned_hr_business_id).first()
        if not assigned_hr or assigned_hr.role != UserRole.HR:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "ASSIGNED_HR_MUST_BE_A_VALID_HR_USER")

    business_id = generate_business_id(db, "job")
    job = Job(
        business_id=business_id,
        slug=_slugify(payload.title, business_id),
        title=payload.title,
        department_id=department.id,
        description=payload.description,
        requirements=payload.requirements,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        quantity=payload.quantity,
        location=payload.location,
        employment_type=EmploymentType(payload.employment_type),
        status=JobStatus.DRAFT,
        created_by=current_user.id,
        assigned_hr_id=assigned_hr.id if assigned_hr else None,
        # Han ung tuyen tinh den het ngay (23:59:59) thay vi 00:00:00, de
        # ung vien nop trong dung ngay hien thi lam han van duoc tinh la kip han.
        deadline=datetime.combine(payload.deadline, time(23, 59, 59)) if payload.deadline else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _to_out(db, job)


@router.post("/{job_business_id}/assign-hr", response_model=JobOut)
def assign_hr(
    job_business_id: str,
    payload: AssignHrRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Phan cong/doi HR phu trach Job. Thieu endpoint nay thi RBAC row-level
    # scope "HR chi xu ly Job duoc gan" khong the hoat dong voi bat ky Job nao
    # tao qua API that.
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")
    hr_user = db.query(User).filter(User.business_id == payload.hr_business_id).first()
    if not hr_user or hr_user.role != UserRole.HR:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ASSIGNED_HR_MUST_BE_A_VALID_HR_USER")
    job.assigned_hr_id = hr_user.id
    db.commit()
    db.refresh(job)
    return _to_out(db, job)


@router.post("/{job_business_id}/publish", response_model=JobOut)
def publish_job(
    job_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Don gian hoa: HR Manager/Admin duyet va dang tin trong 1 buoc. Quy trinh
    # day du DRAFT->PENDING_APPROVAL->APPROVED->PUBLISHED la backlog. Cho phep
    # ca DRAFT->PUBLISHED (dang tin lan dau) va CLOSED->PUBLISHED (mo lai tin
    # da dong) - 2 truong hop ghi audit action khac nhau de phan biet.
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")
    if job.status not in (JobStatus.DRAFT, JobStatus.CLOSED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JOB_STATUS_NOT_ELIGIBLE_FOR_PUBLISH")

    from datetime import datetime, timezone

    is_reopen = job.status == JobStatus.CLOSED
    before = {"status": job.status.value}
    job.status = JobStatus.PUBLISHED
    job.approved_by = current_user.id
    job.published_at = datetime.now(timezone.utc)
    db.flush()
    audit_service.log(
        db, actor=current_user, action="JOB_REOPENED" if is_reopen else "JOB_PUBLISHED",
        entity_type="job", entity_business_id=job.business_id,
        before=before, after={"status": job.status.value},
    )
    db.commit()
    db.refresh(job)
    return _to_out(db, job)


@router.post("/{job_business_id}/close", response_model=JobOut)
def close_job(
    job_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Dong tin tuyen dung thu cong (HR Manager/Admin) - ngoai truong hop tu
    # dong dong khi du chi tieu (xem offer_service.py::_close_job_if_quota_reached,
    # action JOB_AUTO_CLOSED_QUOTA_REACHED). Chi cho dong tin dang PUBLISHED -
    # dong tin DRAFT/CLOSED/CANCELLED khong co y nghia nghiep vu. Sau khi
    # CLOSED, POST /applications se tu chan ung vien nop moi (da kiem tra
    # job.status == PUBLISHED san co o applications.py).
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")
    if job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JOB_NOT_PUBLISHED")

    before = {"status": job.status.value}
    job.status = JobStatus.CLOSED
    db.flush()
    audit_service.log(
        db, actor=current_user, action="JOB_CLOSED_MANUALLY",
        entity_type="job", entity_business_id=job.business_id,
        before=before, after={"status": job.status.value},
    )
    db.commit()
    db.refresh(job)
    return _to_out(db, job)


@router.put("/{job_business_id}", response_model=JobOut)
def update_job(
    job_business_id: str,
    payload: JobUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Sua tin tuyen dung - cho phep bat ke dang DRAFT hay da PUBLISHED. Khong
    # doi department/status/assigned_hr qua day - da co route rieng
    # (/assign-hr, /publish).
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")

    if payload.title is not None:
        job.title = payload.title
    if payload.description is not None:
        job.description = payload.description
    if payload.requirements is not None:
        job.requirements = payload.requirements
    if payload.salary_min is not None:
        job.salary_min = payload.salary_min
    if payload.salary_max is not None:
        job.salary_max = payload.salary_max
    if payload.quantity is not None:
        job.quantity = payload.quantity
    if payload.location is not None:
        job.location = payload.location
    if payload.employment_type is not None:
        try:
            job.employment_type = EmploymentType(payload.employment_type)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_EMPLOYMENT_TYPE")
    if payload.deadline is not None:
        job.deadline = datetime.combine(payload.deadline, time(23, 59, 59))

    db.commit()
    db.refresh(job)
    return _to_out(db, job)


@router.get("", response_model=list[JobOut])
def list_jobs(
    search: str | None = None,
    department_business_id: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Job)
    if current_user.role.value == "CANDIDATE":
        query = query.filter(Job.status == JobStatus.PUBLISHED)
    elif status_filter:
        try:
            query = query.filter(Job.status == JobStatus(status_filter))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    if search:
        query = query.filter(Job.title.ilike(f"%{search.strip()}%"))

    if department_business_id:
        department = db.query(Department).filter(Department.business_id == department_business_id).first()
        query = query.filter(Job.department_id == (department.id if department else -1))

    return [_to_out(db, j) for j in query.order_by(Job.id.desc()).all()]


@router.get("/{job_business_id}", response_model=JobOut)
def get_job(
    job_business_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    # Endpoint nay phai xac thuc va loc theo status - neu khong, Job DRAFT/
    # CLOSED (kem khoang luong noi bo) se lo cho nguoi chua dang nhap neu doan
    # duoc business_id. Nguoi chua dang nhap hoac CANDIDATE chi xem duoc Job
    # PUBLISHED (giong het logic list_jobs); HR+ xem duoc moi trang thai.
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")

    is_hr_plus = current_user is not None and current_user.role != UserRole.CANDIDATE
    if not is_hr_plus and job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")

    return _to_out(db, job)
