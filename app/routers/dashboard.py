from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.rbac import require_hr_or_above
from app.models.application import Application
from app.models.enums import ApplicationStatus, JobStatus, OfferStatus, UserRole
from app.models.job import Job
from app.models.offer import Offer
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryOut, HrPerformanceOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(require_hr_or_above)):
    # HR chi thay so lieu trong scope duoc gan (assigned_hr_id); HR
    # Manager/Admin thay toan bo he thong.
    job_query = db.query(Job)
    app_query = db.query(Application)
    if current_user.role == UserRole.HR:
        job_query = job_query.filter(Job.assigned_hr_id == current_user.id)
        app_query = app_query.filter(Application.assigned_hr_id == current_user.id)

    jobs = job_query.all()
    applications = app_query.all()

    status_breakdown: dict[str, int] = {}
    source_breakdown: dict[str, int] = {}
    for a in applications:
        status_breakdown[a.status.value] = status_breakdown.get(a.status.value, 0) + 1
        # Fix: gom nhom theo TEN CHUAN cua CandidateSource (qua source_id, quan
        # he song) thay vi text tho a.source - truoc day 2 Application cung 1
        # nguon that (source_id giong nhau) nhung snapshot text khac hoa/thuong
        # ("Website" vs "website") bi tach thanh 2 cot rieng tren Dashboard.
        # Application chua co source_id (du lieu cu truoc khi co module Nguon
        # ho so) van fallback ve text tho, khong tu suy doan/gop nham.
        if a.candidate_source is not None:
            src = a.candidate_source.name
        else:
            src = a.source or "Khong xac dinh"
        source_breakdown[src] = source_breakdown.get(src, 0) + 1

    hired_count = status_breakdown.get(ApplicationStatus.HIRED.value, 0)

    offer_query = db.query(Offer)
    if current_user.role == UserRole.HR:
        offer_query = offer_query.join(Application).filter(Application.assigned_hr_id == current_user.id)
    offers = offer_query.filter(
        Offer.status.in_([OfferStatus.ACCEPTED, OfferStatus.DECLINED, OfferStatus.EXPIRED])
    ).all()
    accepted = sum(1 for o in offers if o.status == OfferStatus.ACCEPTED)
    offer_acceptance_rate = round(accepted / len(offers), 4) if offers else None

    hired_apps = [a for a in applications if a.status == ApplicationStatus.HIRED]
    time_to_hire_days = []
    for a in hired_apps:
        offer = db.query(Offer).filter(Offer.application_id == a.id, Offer.status == OfferStatus.ACCEPTED).first()
        if offer and offer.responded_at:
            applied_at = a.applied_at
            delta = offer.responded_at - (applied_at if applied_at.tzinfo else applied_at.replace(tzinfo=offer.responded_at.tzinfo))
            time_to_hire_days.append(delta.total_seconds() / 86400)
    avg_time_to_hire_days = round(sum(time_to_hire_days) / len(time_to_hire_days), 1) if time_to_hire_days else None

    hr_performance: list[HrPerformanceOut] = []
    if current_user.role in (UserRole.HR_MANAGER, UserRole.ADMIN):
        hr_users = db.query(User).filter(User.role == UserRole.HR).all()
        for hr in hr_users:
            hr_apps = [a for a in applications if a.assigned_hr_id == hr.id]
            if not hr_apps:
                continue
            hr_performance.append(
                HrPerformanceOut(
                    hr_business_id=hr.business_id,
                    hr_name=hr.full_name,
                    candidates_processed=len(hr_apps),
                    hired=sum(1 for a in hr_apps if a.status == ApplicationStatus.HIRED),
                )
            )

    return DashboardSummaryOut(
        total_jobs=len(jobs),
        published_jobs=sum(1 for j in jobs if j.status == JobStatus.PUBLISHED),
        total_applications=len(applications),
        status_breakdown=status_breakdown,
        hired_count=hired_count,
        offer_acceptance_rate=offer_acceptance_rate,
        source_breakdown=source_breakdown,
        avg_time_to_hire_days=avg_time_to_hire_days,
        hr_performance=hr_performance,
    )
