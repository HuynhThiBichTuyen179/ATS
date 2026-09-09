from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.id_generator import generate_business_id
from app.models.application import Application
from app.models.enums import ApplicationStatus, EmailTemplateType, JobStatus, OfferStatus, UserRole
from app.models.job import Job
from app.models.offer import Offer
from app.models.user import User
from app.services import audit_service, email_service


def _to_dict(offer: Offer) -> dict:
    return {
        "status": offer.status.value,
        "creator_id": offer.creator_id,
        "approver_id": offer.approver_id,
    }


def create_offer(
    db: Session,
    application: Application,
    creator: User,
    salary: Decimal,
    probation_salary: Decimal,
    start_date: date,
) -> Offer:
    offer = Offer(
        business_id=generate_business_id(db, "offer"),
        application_id=application.id,
        creator_id=creator.id,
        salary=salary,
        probation_salary=probation_salary,
        start_date=start_date,
        status=OfferStatus.DRAFT,
    )
    db.add(offer)
    db.flush()
    audit_service.log(
        db,
        actor=creator,
        action="OFFER_CREATED",
        entity_type="offer",
        entity_business_id=offer.business_id,
        after=_to_dict(offer),
    )
    db.commit()
    db.refresh(offer)
    return offer


def submit_offer(db: Session, offer: Offer, actor: User) -> Offer:
    if offer.status != OfferStatus.DRAFT:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_NOT_IN_DRAFT")
    if actor.id != offer.creator_id and actor.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")

    before = _to_dict(offer)
    offer.status = OfferStatus.PENDING_APPROVAL
    offer.submitted_at = datetime.now(timezone.utc)
    db.flush()
    audit_service.log(
        db,
        actor=actor,
        action="OFFER_SUBMITTED",
        entity_type="offer",
        entity_business_id=offer.business_id,
        before=before,
        after=_to_dict(offer),
    )
    db.commit()
    db.refresh(offer)
    return offer


def approve_offer(db: Session, offer: Offer, actor: User) -> Offer:
    # Trai tim cua 4-eyes approval. creator_id != approver_id la business
    # invariant BAT BUOC, enforce o day (service layer) va o DB qua
    # CheckConstraint ck_offer_approver_not_creator (xem app/models/offer.py).
    if actor.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")
    if offer.status != OfferStatus.PENDING_APPROVAL:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_NOT_PENDING_APPROVAL")

    if actor.id == offer.creator_id:
        audit_service.log(
            db,
            actor=actor,
            action="OFFER_SELF_APPROVAL_BLOCKED",
            entity_type="offer",
            entity_business_id=offer.business_id,
        )
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_SELF_APPROVAL_NOT_ALLOWED")

    before = _to_dict(offer)
    offer.status = OfferStatus.APPROVED
    offer.approver_id = actor.id
    offer.approved_at = datetime.now(timezone.utc)
    db.flush()
    audit_service.log(
        db,
        actor=actor,
        action="OFFER_APPROVED",
        entity_type="offer",
        entity_business_id=offer.business_id,
        before=before,
        after=_to_dict(offer),
    )
    db.commit()
    db.refresh(offer)
    return offer


def reject_offer(db: Session, offer: Offer, actor: User, reason: str) -> Offer:
    if actor.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")
    if offer.status != OfferStatus.PENDING_APPROVAL:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_NOT_PENDING_APPROVAL")
    if not reason:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "REJECTION_REASON_REQUIRED")

    before = _to_dict(offer)
    # PENDING_APPROVAL -> DRAFT (khong phai trang thai terminal): creator sua
    # va submit lai duoc.
    offer.status = OfferStatus.DRAFT
    offer.approver_id = actor.id
    offer.rejected_at = datetime.now(timezone.utc)
    offer.rejection_reason = reason
    db.flush()
    audit_service.log(
        db,
        actor=actor,
        action="OFFER_REJECTED",
        entity_type="offer",
        entity_business_id=offer.business_id,
        before=before,
        after=_to_dict(offer),
        reason=reason,
    )
    db.commit()
    db.refresh(offer)
    return offer


def send_offer(db: Session, offer: Offer, actor: User) -> Offer:
    if actor.role not in (UserRole.HR, UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")
    if offer.status != OfferStatus.APPROVED:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_NOT_APPROVED")

    before = _to_dict(offer)
    now = datetime.now(timezone.utc)
    offer.status = OfferStatus.SENT
    offer.sent_at = now
    offer.expires_at = now + timedelta(days=settings.offer_validity_days)
    db.flush()

    application = db.get(Application, offer.application_id)
    application.status = ApplicationStatus.OFFER
    db.flush()

    audit_service.log(
        db,
        actor=actor,
        action="OFFER_SENT",
        entity_type="offer",
        entity_business_id=offer.business_id,
        before=before,
        after=_to_dict(offer),
    )
    db.commit()
    db.refresh(offer)

    email_service.trigger_stage_email(
        db, actor, application, EmailTemplateType.OFFER,
        extra_vars={"offer_salary": f"{offer.salary:,.0f} VND", "start_date": offer.start_date.isoformat()},
    )
    return offer


def respond_offer(db: Session, offer: Offer, actor: User, accept: bool) -> Offer:
    if offer.status != OfferStatus.SENT:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_NOT_SENT")

    before = _to_dict(offer)
    offer.responded_at = datetime.now(timezone.utc)
    application = db.get(Application, offer.application_id)

    if accept:
        offer.status = OfferStatus.ACCEPTED
        application.status = ApplicationStatus.HIRED
        action = "OFFER_ACCEPTED"
    else:
        offer.status = OfferStatus.DECLINED
        application.status = ApplicationStatus.REJECTED
        action = "OFFER_DECLINED"

    db.flush()
    audit_service.log(
        db,
        actor=actor,
        action=action,
        entity_type="offer",
        entity_business_id=offer.business_id,
        before=before,
        after=_to_dict(offer),
    )

    if accept:
        _close_job_if_quota_reached(db, application, actor)

    db.commit()
    db.refresh(offer)

    if accept:
        # ONBOARDING gui khi Candidate Accept Offer (Application HIRED)
        email_service.trigger_stage_email(
            db, actor, application, EmailTemplateType.ONBOARDING,
            extra_vars={"start_date": offer.start_date.isoformat()},
        )
    return offer


def _close_job_if_quota_reached(db: Session, application: Application, actor: User) -> None:
    # Du so luong HIRED >= jobs.quantity thi tu dong dong Job.
    job = db.get(Job, application.job_id)
    hired_count = (
        db.query(Application)
        .filter(Application.job_id == job.id, Application.status == ApplicationStatus.HIRED)
        .count()
    )
    if hired_count >= job.quantity and job.status != JobStatus.CLOSED:
        before = {"status": job.status.value}
        job.status = JobStatus.CLOSED
        db.flush()
        audit_service.log(
            db,
            actor=actor,
            action="JOB_AUTO_CLOSED_QUOTA_REACHED",
            entity_type="job",
            entity_business_id=job.business_id,
            before=before,
            after={"status": job.status.value},
            reason=f"HIRED count ({hired_count}) >= quantity ({job.quantity})",
        )


def expire_due_offers(db: Session, system_actor: User) -> list[Offer]:
    # Scheduler job: offer SENT qua expires_at -> EXPIRED, application tuong
    # ung -> REJECTED.
    now = datetime.now(timezone.utc)
    due = (
        db.query(Offer)
        .filter(Offer.status == OfferStatus.SENT, Offer.expires_at < now)
        .all()
    )
    for offer in due:
        before = _to_dict(offer)
        offer.status = OfferStatus.EXPIRED
        application = db.get(Application, offer.application_id)
        application.status = ApplicationStatus.REJECTED
        db.flush()
        audit_service.log(
            db,
            actor=system_actor,
            action="OFFER_EXPIRED",
            entity_type="offer",
            entity_business_id=offer.business_id,
            before=before,
            after=_to_dict(offer),
        )
    db.commit()
    return due
