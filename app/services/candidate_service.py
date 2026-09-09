# HR/HR_MANAGER/ADMIN tao ho so ung vien truc tiep (khac luong tu-ung-tuyen
# qua Candidate Portal da co san o application_service). Tao dong thoi
# Candidate + Application, Job la COMBOBOX lien ket bang ID (khong luu ten tu
# do), Department luon ke thua tu Job (khong cho override).

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.candidate import Candidate, Gender
from app.models.candidate_source import CandidateSource
from app.models.enums import ApplicationStatus, CandidateStatus, EmailTemplateType, JobStatus
from app.models.job import Job
from app.models.user import User
from app.services import audit_service, email_service


def _get_or_create_candidate(
    db: Session, full_name: str, email: str, phone: str, gender: str | None,
    skills_summary: str | None, experience_summary: str | None,
) -> tuple[Candidate, bool]:
    # Da co san o application_service - ap dung lai dung nguyen tac dedupe
    # theo email de KHONG tao Candidate trung.
    candidate = db.query(Candidate).filter(Candidate.email == email).first()
    if candidate:
        return candidate, False

    gender_enum = None
    if gender:
        try:
            gender_enum = Gender(gender)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_GENDER")

    candidate = Candidate(
        business_id=generate_business_id(db, "candidate"),
        full_name=full_name,
        email=email,
        phone=phone,
        gender=gender_enum,
        skills_summary=skills_summary,
        experience_summary=experience_summary,
        status=CandidateStatus.ACTIVE,
    )
    db.add(candidate)
    db.flush()
    return candidate, True


def create_candidate_with_application(
    db: Session,
    actor: User,
    full_name: str,
    email: str,
    phone: str,
    gender: str | None,
    job_business_id: str,
    desired_salary: float | None,
    source: str | None,
    skills_summary: str | None,
    experience_summary: str | None,
) -> tuple[Candidate, Application]:
    job = db.query(Job).filter(Job.business_id == job_business_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "JOB_NOT_FOUND")
    # Chi cho chon Job hop le theo business rule hien tai (da dang -
    # PUBLISHED). Khong cho tao Application vao Job DRAFT/CLOSED.
    if job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JOB_NOT_PUBLISHED")

    candidate, candidate_is_new = _get_or_create_candidate(
        db, full_name, email, phone, gender, skills_summary, experience_summary
    )
    if not candidate_is_new:
        # Ho so da ton tai (dedupe theo email) - cap nhat cac field mo ta neu
        # HR nhap them thong tin moi, khong ghi de rong len du lieu da co.
        if skills_summary:
            candidate.skills_summary = skills_summary
        if experience_summary:
            candidate.experience_summary = experience_summary

    # Neu ten source khop 1 CandidateSource da cau hinh, gan ca source_id (FK
    # "song"). Form HR van cho phep nhap tu do ("Other"/ten khac chua co trong
    # danh muc) nen khong bat buoc phai khop (khac voi luong Candidate tu ung
    # tuyen o application_service.apply_for_job - noi source
    # BAT BUOC phai la 1 CandidateSource hop le).
    # So khop khong phan biet hoa/thuong + bo khoang trang thua - neu so khop
    # tuyet doi thi "website"/"Website " (HR go tu do) se khong khop voi
    # "Website" da cau hinh san, tao ra nguon "mo côi" (source_id=NULL) va lam
    # Dashboard hien thi trung lap nhieu bien the cua cung 1 nguon that.
    candidate_source = (
        db.query(CandidateSource).filter(func.lower(CandidateSource.name) == source.strip().lower()).first()
        if source and source.strip()
        else None
    )

    application = Application(
        business_id=generate_business_id(db, "application"),
        candidate_id=candidate.id,
        job_id=job.id,
        # Job Department = Application Department, luon ke thua.
        department_id=job.department_id,
        desired_salary=Decimal(str(desired_salary)) if desired_salary is not None else None,
        source_id=candidate_source.id if candidate_source else None,
        source=source,
        status=ApplicationStatus.NEW,
        assigned_hr_id=job.assigned_hr_id,
    )
    db.add(application)
    db.flush()

    audit_service.log(
        db, actor=actor,
        action="CANDIDATE_CREATED" if candidate_is_new else "APPLICATION_CREATED",
        entity_type="candidate" if candidate_is_new else "application",
        entity_business_id=candidate.business_id if candidate_is_new else application.business_id,
        after={"email": candidate.email, "job_business_id": job.business_id},
    )
    db.commit()
    db.refresh(candidate)
    db.refresh(application)

    email_service.trigger_stage_email(db, actor, application, EmailTemplateType.APPLICATION_RECEIVED)
    return candidate, application


def update_candidate(
    db: Session, actor: User, candidate: Candidate,
    full_name: str | None, gender: str | None, phone: str | None,
    skills_summary: str | None, experience_summary: str | None,
) -> Candidate:
    before = {"full_name": candidate.full_name, "phone": candidate.phone}
    if full_name is not None:
        candidate.full_name = full_name
    if phone is not None:
        candidate.phone = phone
    if gender is not None:
        try:
            candidate.gender = Gender(gender)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_GENDER")
    if skills_summary is not None:
        candidate.skills_summary = skills_summary
    if experience_summary is not None:
        candidate.experience_summary = experience_summary

    db.flush()
    audit_service.log(
        db, actor=actor, action="CANDIDATE_UPDATED",
        entity_type="candidate", entity_business_id=candidate.business_id,
        before=before, after={"full_name": candidate.full_name, "phone": candidate.phone},
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def archive_candidate(db: Session, actor: User, candidate: Candidate) -> Candidate:
    # Uu tien Soft Delete/Archive - khong bao gio xoa vat ly Candidate (se
    # keo theo mat Resume/Application/Interview/AI/Audit lien quan qua FK).
    before = {"status": candidate.status.value}
    candidate.status = CandidateStatus.ARCHIVED
    db.flush()
    audit_service.log(
        db, actor=actor, action="CANDIDATE_DELETED",
        entity_type="candidate", entity_business_id=candidate.business_id,
        before=before, after={"status": candidate.status.value}, reason="Soft-delete (ARCHIVED)",
    )
    db.commit()
    db.refresh(candidate)
    return candidate
