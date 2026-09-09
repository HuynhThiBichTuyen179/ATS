from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time_utils import to_iso_utc
from app.deps.rbac import get_current_user, require_hr_or_above
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.department import Department
from app.models.enums import UserRole
from app.models.interview import Interview
from app.models.job import Job
from app.models.user import User
from app.schemas.interview import InterviewCreateRequest, InterviewOut, InterviewUpdateRequest
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_DATETIME_FORMAT")


def _to_out(interview: Interview) -> InterviewOut:
    application = interview.application
    return InterviewOut(
        business_id=interview.business_id,
        application_business_id=application.business_id,
        candidate_full_name=application.candidate.full_name,
        candidate_email=application.candidate.email,
        job_title=application.job.title,
        start_time=to_iso_utc(interview.scheduled_at),
        end_time=to_iso_utc(interview.end_time),
        interview_type=interview.interview_type.value,
        location=interview.location,
        meeting_link=interview.meeting_link,
        interviewer_business_id=interview.interviewer.business_id,
        interviewer_name=interview.interviewer.full_name,
        notes=interview.notes,
        status=interview.status.value,
    )


def _get_interview_or_404(db: Session, interview_business_id: str) -> Interview:
    interview = db.query(Interview).filter(Interview.business_id == interview_business_id).first()
    if not interview:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "INTERVIEW_NOT_FOUND")
    return interview


@router.post("", response_model=InterviewOut)
def create_interview(
    payload: InterviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    # Candidate phai duoc chon TU Application hop le - khong tao Interview
    # khong gan Application.
    application = db.query(Application).filter(Application.business_id == payload.application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    if current_user.role == UserRole.HR and application.assigned_hr_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    interviewer = db.query(User).filter(User.business_id == payload.interviewer_business_id).first()
    if not interviewer or interviewer.role == UserRole.CANDIDATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "INTERVIEWER_NOT_FOUND")

    interview = interview_service.create_interview(
        db, current_user, application, interviewer,
        start_time=_parse_dt(payload.start_time), end_time=_parse_dt(payload.end_time),
        interview_type=payload.interview_type, location=payload.location,
        meeting_link=payload.meeting_link, notes=payload.notes,
    )
    return _to_out(interview)


@router.get("", response_model=list[InterviewOut])
def list_interviews(
    interviewer_business_id: str | None = None,
    department_business_id: str | None = None,
    application_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    # Filter theo HR/Interviewer/Department/Application Status/Date Range.
    query = db.query(Interview).join(Application, Interview.application_id == Application.id)

    if current_user.role == UserRole.HR:
        query = query.filter(Application.assigned_hr_id == current_user.id)
    if interviewer_business_id:
        interviewer = db.query(User).filter(User.business_id == interviewer_business_id).first()
        query = query.filter(Interview.interviewer_id == (interviewer.id if interviewer else -1))
    if department_business_id:
        query = query.join(Job, Application.job_id == Job.id).join(Department, Job.department_id == Department.id)
        query = query.filter(Department.business_id == department_business_id)
    if application_status:
        query = query.filter(Application.status == application_status)
    if date_from:
        query = query.filter(Interview.scheduled_at >= _parse_dt(date_from))
    if date_to:
        query = query.filter(Interview.scheduled_at <= _parse_dt(date_to))

    return [_to_out(i) for i in query.order_by(Interview.scheduled_at).all()]


@router.get("/me", response_model=list[InterviewOut])
def list_my_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Candidate Dashboard - chi xem Interview cua chinh minh, khong xem duoc
    # noi bo notes/feedback (da loai bo o InterviewOut - chi map field cong
    # khai, xem _to_out).
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ONLY_CANDIDATE_HAS_MY_INTERVIEWS")
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        return []
    interviews = (
        db.query(Interview)
        .join(Application, Interview.application_id == Application.id)
        .filter(Application.candidate_id == candidate.id)
        .order_by(Interview.scheduled_at)
        .all()
    )
    return [_to_out(i) for i in interviews]


@router.get("/{interview_business_id}", response_model=InterviewOut)
def get_interview(
    interview_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = _get_interview_or_404(db, interview_business_id)
    application = interview.application
    if current_user.role == UserRole.CANDIDATE:
        if application.candidate.user_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_INTERVIEW")
    elif current_user.role == UserRole.HR:
        if application.assigned_hr_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    return _to_out(interview)


@router.put("/{interview_business_id}", response_model=InterviewOut)
def update_interview(
    interview_business_id: str,
    payload: InterviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    interview = _get_interview_or_404(db, interview_business_id)
    if current_user.role == UserRole.HR and interview.application.assigned_hr_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")

    interviewer = None
    if payload.interviewer_business_id:
        interviewer = db.query(User).filter(User.business_id == payload.interviewer_business_id).first()
        if not interviewer or interviewer.role == UserRole.CANDIDATE:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "INTERVIEWER_NOT_FOUND")

    interview = interview_service.update_interview(
        db, current_user, interview,
        start_time=_parse_dt(payload.start_time) if payload.start_time else None,
        end_time=_parse_dt(payload.end_time) if payload.end_time else None,
        interview_type=payload.interview_type, location=payload.location,
        meeting_link=payload.meeting_link, interviewer=interviewer,
        notes=payload.notes, new_status=payload.status,
    )
    return _to_out(interview)


@router.delete("/{interview_business_id}")
def delete_interview(
    interview_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    # "Xoa" = huy (CANCELLED), khong hard-delete.
    interview = _get_interview_or_404(db, interview_business_id)
    if current_user.role == UserRole.HR and interview.application.assigned_hr_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    interview = interview_service.cancel_interview(db, current_user, interview)
    return {"business_id": interview.business_id, "status": interview.status.value}
