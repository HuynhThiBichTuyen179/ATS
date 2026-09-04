"""v2.2 Section 26-34 - Interview Calendar. Model `interviews` da ton tai san
trong schema tu truoc nhung chua tung co router/service nao su dung (Gap
APP-20 da ghi nhan trong tai lieu reverse-engineering) - dot nay xay dung day
du CRUD + kiem tra trung lich + email thong bao, khong tao bang moi.
"""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.core.time_utils import to_iso_utc
from app.models.application import Application
from app.models.enums import EmailTemplateType, InterviewStatus, InterviewType
from app.models.interview import Interview
from app.models.user import User
from app.services import audit_service, email_service


def _check_conflict(
    db: Session, candidate_id: int, interviewer_id: int, start: datetime, end: datetime,
    exclude_interview_id: int | None = None,
) -> None:
    """Section 32: Start < End; Candidate/Interviewer khong duoc trung lich.
    Overlap: [start,end) giao [existing_start,existing_end) khi
    start < existing_end AND existing_start < end.
    """
    if start >= end:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "START_TIME_MUST_BE_BEFORE_END_TIME")

    overlap_condition = and_(Interview.scheduled_at < end, start < Interview.end_time)
    active = Interview.status != InterviewStatus.CANCELLED

    query = (
        db.query(Interview)
        .join(Application, Interview.application_id == Application.id)
        .filter(
            active,
            overlap_condition,
            or_(Application.candidate_id == candidate_id, Interview.interviewer_id == interviewer_id),
        )
    )
    if exclude_interview_id is not None:
        query = query.filter(Interview.id != exclude_interview_id)

    conflict = query.first()
    if conflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "INTERVIEW_TIME_CONFLICT")


def create_interview(
    db: Session, actor: User, application: Application, interviewer: User,
    start_time: datetime, end_time: datetime, interview_type: str,
    location: str | None, meeting_link: str | None, notes: str | None,
) -> Interview:
    try:
        itype = InterviewType(interview_type)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_INTERVIEW_TYPE")

    _check_conflict(db, application.candidate_id, interviewer.id, start_time, end_time)

    interview = Interview(
        business_id=generate_business_id(db, "interview"),
        application_id=application.id,
        interviewer_id=interviewer.id,
        scheduled_at=start_time,
        end_time=end_time,
        interview_type=itype,
        location=location,
        meeting_link=meeting_link,
        notes=notes,
        status=InterviewStatus.SCHEDULED,
    )
    db.add(interview)
    db.flush()
    audit_service.log(
        db, actor=actor, action="INTERVIEW_CREATED",
        entity_type="interview", entity_business_id=interview.business_id,
        after={"application_business_id": application.business_id, "start_time": to_iso_utc(start_time)},
    )
    db.commit()
    db.refresh(interview)

    email_service.trigger_stage_email(
        db, actor, application, EmailTemplateType.INTERVIEW_INVITATION,
        extra_vars={"interview_time": start_time.strftime("%d/%m/%Y %H:%M"), "interview_location": location or meeting_link or ""},
    )
    return interview


def update_interview(
    db: Session, actor: User, interview: Interview,
    start_time: datetime | None, end_time: datetime | None, interview_type: str | None,
    location: str | None, meeting_link: str | None, interviewer: User | None,
    notes: str | None, new_status: str | None,
) -> Interview:
    before = {
        "start_time": to_iso_utc(interview.scheduled_at), "end_time": to_iso_utc(interview.end_time),
        "status": interview.status.value,
    }
    time_changed = False

    new_start = start_time or interview.scheduled_at
    new_end = end_time or interview.end_time
    new_interviewer_id = interviewer.id if interviewer else interview.interviewer_id
    if start_time or end_time or interviewer:
        _check_conflict(
            db, interview.application.candidate_id, new_interviewer_id, new_start, new_end,
            exclude_interview_id=interview.id,
        )
        time_changed = bool(start_time or end_time)

    if start_time:
        interview.scheduled_at = start_time
    if end_time:
        interview.end_time = end_time
    if interviewer:
        interview.interviewer_id = interviewer.id
    if interview_type is not None:
        try:
            interview.interview_type = InterviewType(interview_type)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_INTERVIEW_TYPE")
    if location is not None:
        interview.location = location
    if meeting_link is not None:
        interview.meeting_link = meeting_link
    if notes is not None:
        interview.notes = notes
    if new_status is not None:
        try:
            interview.status = InterviewStatus(new_status)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")

    db.flush()
    audit_service.log(
        db, actor=actor, action="INTERVIEW_UPDATED",
        entity_type="interview", entity_business_id=interview.business_id,
        before=before,
        after={"start_time": to_iso_utc(interview.scheduled_at), "end_time": to_iso_utc(interview.end_time), "status": interview.status.value},
    )
    db.commit()
    db.refresh(interview)

    if time_changed:
        email_service.trigger_stage_email(
            db, actor, interview.application, EmailTemplateType.INTERVIEW_RESCHEDULED,
            extra_vars={"interview_time": interview.scheduled_at.strftime("%d/%m/%Y %H:%M")},
        )
    return interview


def cancel_interview(db: Session, actor: User, interview: Interview) -> Interview:
    """Section 31: khong hard-delete - luon chuyen CANCELLED, giu nguyen
    audit/feedback da co."""
    before = {"status": interview.status.value}
    interview.status = InterviewStatus.CANCELLED
    db.flush()
    audit_service.log(
        db, actor=actor, action="INTERVIEW_DELETED",
        entity_type="interview", entity_business_id=interview.business_id,
        before=before, after={"status": interview.status.value}, reason="Cancel (khong hard-delete)",
    )
    db.commit()
    db.refresh(interview)

    email_service.trigger_stage_email(db, actor, interview.application, EmailTemplateType.INTERVIEW_CANCELLED)
    return interview
