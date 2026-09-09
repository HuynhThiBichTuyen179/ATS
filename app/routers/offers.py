from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.rbac import get_current_user, require_hr_or_above, require_offer_approver
from app.models.application import Application
from app.models.enums import OfferStatus, UserRole
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCreateRequest, OfferOut, OfferRejectRequest, OfferRespondRequest
from app.services import offer_service

router = APIRouter(prefix="/offers", tags=["offers"])


def _to_out(db: Session, offer: Offer) -> OfferOut:
    creator = db.get(User, offer.creator_id)
    approver = db.get(User, offer.approver_id) if offer.approver_id else None
    application = offer.application
    candidate = application.candidate
    job = application.job
    return OfferOut(
        business_id=offer.business_id,
        application_business_id=application.business_id,
        candidate_business_id=candidate.business_id,
        candidate_full_name=candidate.full_name,
        candidate_email=candidate.email,
        job_business_id=job.business_id,
        job_title=job.title,
        department_name=job.department.name if job.department else None,
        creator_business_id=creator.business_id,
        creator_name=creator.full_name,
        approver_business_id=approver.business_id if approver else None,
        approver_name=approver.full_name if approver else None,
        status=offer.status.value,
        salary=offer.salary,
        probation_salary=offer.probation_salary,
        start_date=offer.start_date.isoformat(),
    )


def _get_offer(db: Session, business_id: str) -> Offer:
    offer = db.query(Offer).filter(Offer.business_id == business_id).first()
    if not offer:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "OFFER_NOT_FOUND")
    return offer


def _check_can_view_offer(current_user: User, offer: Offer) -> None:
    # Ownership/scope check cho GET /offers/{id} - khong co check nay, bat ky
    # user dang nhap nao cung doc duoc offer bat ky vi business_id tuan tu de
    # doan.
    if current_user.role in (UserRole.HR_MANAGER, UserRole.ADMIN):
        return
    if current_user.role == UserRole.HR:
        if offer.application.assigned_hr_id == current_user.id or offer.creator_id == current_user.id:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    if current_user.role == UserRole.CANDIDATE:
        if offer.application.candidate.user_id == current_user.id:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_OFFER")
    raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")


@router.get("", response_model=list[OfferOut])
def list_offers(
    application_business_id: str | None = None,
    offer_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Can thiet de HR Manager/Admin tim Offer dang PENDING_APPROVAL can duyet,
    # va de Candidate xem Offer cua chinh minh gan voi 1 Application cu the.
    query = db.query(Offer)

    if application_business_id:
        application = db.query(Application).filter(Application.business_id == application_business_id).first()
        if not application:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
        if current_user.role == UserRole.CANDIDATE and application.candidate.user_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_APPLICATION")
        if current_user.role == UserRole.HR and application.assigned_hr_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
        query = query.filter(Offer.application_id == application.id)
    elif current_user.role == UserRole.CANDIDATE:
        # Candidate khong duoc liet ke toan bo Offer - phai chi ro application
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "APPLICATION_BUSINESS_ID_REQUIRED")
    elif current_user.role == UserRole.HR:
        # HR (khong phai Manager/Admin) chi thay Offer minh tao hoac thuoc
        # Application duoc gan cho minh - khop Rule 5 / RBAC 4.2 row-level scope
        query = query.join(Application).filter(
            (Offer.creator_id == current_user.id) | (Application.assigned_hr_id == current_user.id)
        )

    if offer_status:
        query = query.filter(Offer.status == OfferStatus(offer_status))

    offers = query.order_by(Offer.id.desc()).all()
    return [_to_out(db, o) for o in offers]


@router.post("", response_model=OfferOut)
def create_offer(
    payload: OfferCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_hr_or_above)
):
    application = db.query(Application).filter(Application.business_id == payload.application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    offer = offer_service.create_offer(
        db, application, current_user, payload.salary, payload.probation_salary, payload.start_date
    )
    return _to_out(db, offer)


@router.post("/{offer_business_id}/submit", response_model=OfferOut)
def submit_offer(
    offer_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_hr_or_above)
):
    offer = _get_offer(db, offer_business_id)
    offer = offer_service.submit_offer(db, offer, current_user)
    return _to_out(db, offer)


@router.post("/{offer_business_id}/approve", response_model=OfferOut)
def approve_offer(
    offer_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_offer_approver)
):
    offer = _get_offer(db, offer_business_id)
    offer = offer_service.approve_offer(db, offer, current_user)
    return _to_out(db, offer)


@router.post("/{offer_business_id}/reject", response_model=OfferOut)
def reject_offer(
    offer_business_id: str,
    payload: OfferRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_offer_approver),
):
    offer = _get_offer(db, offer_business_id)
    offer = offer_service.reject_offer(db, offer, current_user, payload.reason)
    return _to_out(db, offer)


@router.post("/{offer_business_id}/send", response_model=OfferOut)
def send_offer(
    offer_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_hr_or_above)
):
    offer = _get_offer(db, offer_business_id)
    offer = offer_service.send_offer(db, offer, current_user)
    return _to_out(db, offer)


@router.post("/{offer_business_id}/respond", response_model=OfferOut)
def respond_offer(
    offer_business_id: str,
    payload: OfferRespondRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = _get_offer(db, offer_business_id)
    if offer.application.candidate.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_OFFER")
    if payload.response not in ("ACCEPTED", "DECLINED"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_RESPONSE")
    offer = offer_service.respond_offer(db, offer, current_user, accept=(payload.response == "ACCEPTED"))
    return _to_out(db, offer)


@router.get("/{offer_business_id}", response_model=OfferOut)
def get_offer(offer_business_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    offer = _get_offer(db, offer_business_id)
    _check_can_view_offer(current_user, offer)
    return _to_out(db, offer)
