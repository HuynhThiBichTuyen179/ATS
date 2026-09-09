from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.candidate_source import CandidateSource
from app.models.enums import ApplicationStatus, ArchiveReason, EmailTemplateType, UserRole
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.services import audit_service, email_service

# Anh xa trang thai Application -> loai Email Template tu dong kich hoat.
# INTERVIEW_INVITATION gan vao luc chuyen sang INTERVIEW (chua co
# Interview API rieng - backlog #2) thay vi luc tao lich phong van that.
_STATUS_TO_EMAIL_EVENT = {
    ApplicationStatus.SHORTLISTED: EmailTemplateType.SHORTLISTED,
    ApplicationStatus.INTERVIEW: EmailTemplateType.INTERVIEW_INVITATION,
    ApplicationStatus.REJECTED: EmailTemplateType.REJECTION,
}

# Canh chuyen forward hop le do HR/HR Manager/Admin thuc hien qua
# PUT /applications/{id}/status. application.status chi duoc phep chuyen sang
# OFFER thong qua offer_service.send_offer() (sau khi Offer that da qua du
# DRAFT->PENDING_APPROVAL->APPROVED - dung quy trinh 4-eyes), KHONG duoc phep
# set truc tiep qua endpoint nay - neu khong HR co the "gia mao" status=OFFER
# ma khong he co Offer nao duoc tao/duyet, pha vo toan bo 4-eyes approval va
# lam ket hon so (khong con cach nao tao Offer that vi UI/nghiep vu chi cho
# tao Offer khi status dang la INTERVIEW). Tuong tu, HIRED/REJECTED tu OFFER
# do offer_service quan ly (respond_offer/expire_due_offers), khong di qua
# ham update_status nay.
#
# NEW->SCREENING: AI Screening service that (goi AI Provider) la BACKLOG - xem
# CONFLICT_REPORT_AND_BACKLOG.md #1. Neu khong co canh nay, moi Application se
# ket vinh vien o NEW vi khong co gi day no toi AI_SCREENING. Day chinh la
# nhanh "AI khong kha dung -> can sang loc thu cong", chi khac la o day no la
# truong hop thuong truc (chua co AI that) chu khong phai truong hop loi tam
# thoi. Khi AI Screening service duoc xay that, canh nay VAN giu nguyen lam
# fallback, chi thay doi la se co them mot duong system-driven
# NEW->AI_SCREENING->SCREENING chay song song.
MANUAL_SCREENING_FALLBACK_EDGE = (ApplicationStatus.NEW, ApplicationStatus.SCREENING)

# Cac trang thai duoc coi la "da qua sang loc, con dang xu ly" - dung de chan
# nop THEM ho so vao cung 1 tin khi da co san 1 ho so dang o cac trang thai
# nay (xem apply_for_job). Khong gom NEW/AI_SCREENING (chua sang loc) va
# REJECTED/WITHDRAWN/ARCHIVED (da ket thuc, van cho tai ung tuyen binh thuong).
_BLOCKED_REAPPLY_STATUSES = {
    ApplicationStatus.SCREENING,
    ApplicationStatus.SHORTLISTED,
    ApplicationStatus.INTERVIEW,
    ApplicationStatus.OFFER,
    ApplicationStatus.HIRED,
}

FORWARD_EDGES: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.NEW: {ApplicationStatus.SCREENING},
    ApplicationStatus.SCREENING: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED},
    ApplicationStatus.SHORTLISTED: {ApplicationStatus.INTERVIEW},
    ApplicationStatus.INTERVIEW: {ApplicationStatus.REJECTED},
}

# Thu tu pipeline dung de xac dinh mot chuyen trang thai la "lui" (backward)
PIPELINE_ORDER = [
    ApplicationStatus.NEW,
    ApplicationStatus.AI_SCREENING,
    ApplicationStatus.SCREENING,
    ApplicationStatus.SHORTLISTED,
    ApplicationStatus.INTERVIEW,
    ApplicationStatus.OFFER,
    ApplicationStatus.HIRED,
]

WITHDRAWABLE_STATUSES = {
    ApplicationStatus.NEW,
    ApplicationStatus.AI_SCREENING,
    ApplicationStatus.SCREENING,
    ApplicationStatus.SHORTLISTED,
    ApplicationStatus.INTERVIEW,
}


def _to_dict(app: Application) -> dict:
    return {"status": app.status.value, "assigned_hr_id": app.assigned_hr_id}


def apply_for_job(
    db: Session,
    candidate: Candidate,
    job: Job,
    candidate_source: CandidateSource,
    idempotency_key: str | None,
    actor: User,
    resume_text: str | None = None,
    desired_salary: float | None = None,
) -> tuple[Application, bool]:
    # Tao Application moi cho moi lan Apply hop le, khong co cooldown 90-ngay
    # o bat ky dau trong ham nay. Application cu (neu co, vi du REJECTED/
    # WITHDRAWN) duoc giu nguyen, khong overwrite. Tra ve (application, is_new):
    # is_new=False khi trung Idempotency-Key voi 1 request truoc do cua chinh
    # candidate nay.
    if idempotency_key:
        existing = (
            db.query(Application)
            .filter(
                Application.candidate_id == candidate.id,
                Application.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            audit_service.log(
                db,
                actor=actor,
                action="APPLICATION_DUPLICATE_REQUEST",
                entity_type="application",
                entity_business_id=existing.business_id,
                reason="Trung Idempotency-Key voi request truoc do - khong tao Application moi",
            )
            db.commit()
            return existing, False

    # Chan nop THEM ho so vao CUNG 1 tin neu candidate dang co san 1
    # Application khac cho tin nay da qua buoc sang loc (tu SCREENING tro di)
    # va CHUA ket thuc - tranh 2 ho so trung nhau cung tin cung duoc xu ly
    # song song, gay nham lan cho HR. KHONG ap dung cho Application con o
    # NEW/AI_SCREENING (chua sang loc) hay da ket thuc (REJECTED/WITHDRAWN/
    # ARCHIVED) - van giu dung tinh than "tai ung tuyen khong gioi han" cho
    # cac truong hop do, chi chan khi thuc su co 1 ho so con "song" dang duoc
    # xu ly dang do.
    active_application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id,
            Application.job_id == job.id,
            Application.status.in_(_BLOCKED_REAPPLY_STATUSES),
        )
        .first()
    )
    if active_application:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"ALREADY_HAS_ACTIVE_APPLICATION_FOR_THIS_JOB: {active_application.business_id}",
        )

    is_reapply = (
        db.query(Application)
        .filter(Application.candidate_id == candidate.id, Application.job_id == job.id)
        .first()
        is not None
    )

    application = Application(
        business_id=generate_business_id(db, "application"),
        candidate_id=candidate.id,
        job_id=job.id,
        # source_id la FK "song" vao candidate_sources (rename/disable/
        # reporting dung theo master data); source (text) la snapshot ten
        # nguon tai thoi diem nop don, khong doi ngay ca khi CandidateSource
        # sau nay bi doi ten.
        source_id=candidate_source.id,
        source=candidate_source.name,
        desired_salary=Decimal(str(desired_salary)) if desired_salary is not None else None,
        status=ApplicationStatus.NEW,
        idempotency_key=idempotency_key,
        # Ke thua HR phu trach tu Job (neu Job da duoc gan) - thieu dong nay thi
        # scope "HR chi xu ly Application duoc gan" khong bao gio dung vi
        # assigned_hr_id luon NULL cho moi Application moi tao.
        assigned_hr_id=job.assigned_hr_id,
        # Job Department = Application Department mac dinh, khong cho form
        # override tu do.
        department_id=job.department_id,
    )
    db.add(application)
    db.flush()

    if resume_text and resume_text.strip():
        # Chua co API upload file CV that (backlog #8) - luu text CV duoc dan
        # truc tiep vao bang resumes (1 resume rieng cho tung application,
        # dung theo quyet dinh o v2 changelog #13), khong phai gia lap.
        resume = Resume(
            business_id=generate_business_id(db, "resume"),
            candidate_id=candidate.id,
            application_id=application.id,
            file_name="pasted_cv.txt",
            file_path="",
            file_type="text/plain",
            extracted_text=resume_text.strip(),
        )
        db.add(resume)
        db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="APPLICATION_REAPPLIED" if is_reapply else "APPLICATION_CREATED",
        entity_type="application",
        entity_business_id=application.business_id,
        after=_to_dict(application),
    )
    db.commit()
    db.refresh(application)
    email_service.trigger_stage_email(db, actor, application, EmailTemplateType.APPLICATION_RECEIVED)
    return application, True


def update_status(
    db: Session,
    application: Application,
    new_status: ApplicationStatus,
    actor: User,
    reason: str | None = None,
) -> Application:
    # Validate transition theo dung state machine truoc khi ghi DB (giai quyet
    # xung dot giua Kanban keo-tha-tu-do vs state machine 1 chieu).
    current = application.status
    is_forward = new_status in FORWARD_EDGES.get(current, set())

    is_backward = False
    if not is_forward and current in PIPELINE_ORDER and new_status in PIPELINE_ORDER:
        if PIPELINE_ORDER.index(new_status) < PIPELINE_ORDER.index(current):
            is_backward = True

    if not is_forward and not is_backward:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"INVALID_STATUS_TRANSITION: {current.value} -> {new_status.value}",
        )

    if is_forward and actor.role not in (UserRole.HR, UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")

    if is_backward:
        # v2 4.1: chi HR Manager/Admin duoc lui trang thai, bat buoc co ly do
        if actor.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "ONLY_HR_MANAGER_OR_ADMIN_CAN_REVERT")
        if not reason:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "REASON_REQUIRED_FOR_REVERT")

    before = _to_dict(application)
    application.status = new_status
    application.updated_at = datetime.now(timezone.utc)
    if (current, new_status) == MANUAL_SCREENING_FALLBACK_EDGE:
        application.needs_manual_review = 1
    db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="STATUS_REVERTED" if is_backward else "APPLICATION_STATUS_CHANGED",
        entity_type="application",
        entity_business_id=application.business_id,
        before=before,
        after=_to_dict(application),
        reason=reason,
    )
    db.commit()
    db.refresh(application)

    email_event = _STATUS_TO_EMAIL_EVENT.get(new_status)
    if email_event and not is_backward:
        email_service.trigger_stage_email(db, actor, application, email_event)

    return application


def withdraw(db: Session, application: Application, actor: User) -> Application:
    if application.status not in WITHDRAWABLE_STATUSES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"CANNOT_WITHDRAW_FROM_STATUS: {application.status.value}",
        )
    before = _to_dict(application)
    application.status = ApplicationStatus.WITHDRAWN
    application.updated_at = datetime.now(timezone.utc)
    db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="APPLICATION_WITHDRAWN",
        entity_type="application",
        entity_business_id=application.business_id,
        before=before,
        after=_to_dict(application),
    )
    db.commit()
    db.refresh(application)
    return application


def archive(
    db: Session, application: Application, actor: User, archive_reason: ArchiveReason
) -> Application:
    # Cho phep chuyen tu bat ky trang thai nao (tru HIRED) sang ARCHIVED, chi
    # HR Manager/Admin thuc hien duoc.
    if application.status == ApplicationStatus.HIRED:
        raise HTTPException(status.HTTP_409_CONFLICT, "CANNOT_ARCHIVE_HIRED_APPLICATION")
    if actor.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ONLY_HR_MANAGER_OR_ADMIN_CAN_ARCHIVE")

    before = _to_dict(application)
    application.status = ApplicationStatus.ARCHIVED
    application.archive_reason = archive_reason
    application.updated_at = datetime.now(timezone.utc)
    db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="APPLICATION_ARCHIVED",
        entity_type="application",
        entity_business_id=application.business_id,
        before=before,
        after=_to_dict(application),
        reason=f"archive_reason={archive_reason.value}",
    )
    db.commit()
    db.refresh(application)
    return application


def update_application(
    db: Session, actor: User, application: Application,
    desired_salary: float | None, candidate_source: CandidateSource | None,
) -> Application:
    # Sua Luong mong muon va Nguon ho so. KHONG cho doi job_id/candidate_id
    # qua day - tranh pha vo relationship co dinh; doi Job can nghiep vu rieng
    # phuc tap hon.
    before = {
        "desired_salary": str(application.desired_salary) if application.desired_salary is not None else None,
        "source": application.source,
    }
    if desired_salary is not None:
        application.desired_salary = Decimal(str(desired_salary))
    if candidate_source is not None:
        application.source_id = candidate_source.id
        application.source = candidate_source.name

    application.updated_at = datetime.now(timezone.utc)
    db.flush()
    audit_service.log(
        db, actor=actor, action="APPLICATION_UPDATED",
        entity_type="application", entity_business_id=application.business_id,
        before=before,
        after={
            "desired_salary": str(application.desired_salary) if application.desired_salary is not None else None,
            "source": application.source,
        },
    )
    db.commit()
    db.refresh(application)
    return application
