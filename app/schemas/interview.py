from pydantic import BaseModel


class InterviewCreateRequest(BaseModel):
    application_business_id: str
    start_time: str  # ISO datetime
    end_time: str  # ISO datetime
    interview_type: str = "ONLINE"  # "ONSITE" | "ONLINE"
    location: str | None = None
    meeting_link: str | None = None
    interviewer_business_id: str
    notes: str | None = None


class InterviewUpdateRequest(BaseModel):
    # Khong cho sua interview_id/application_id tuy tien - doi Application
    # gan voi Interview can business rule rieng, chua co endpoint doi
    # Application.

    start_time: str | None = None
    end_time: str | None = None
    interview_type: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    interviewer_business_id: str | None = None
    notes: str | None = None
    status: str | None = None  # cho phep chuyen sang COMPLETED/CANCELLED


class InterviewOut(BaseModel):
    business_id: str
    application_business_id: str
    candidate_full_name: str
    candidate_email: str
    job_title: str
    start_time: str
    end_time: str
    interview_type: str
    location: str | None = None
    meeting_link: str | None = None
    interviewer_business_id: str
    interviewer_name: str
    notes: str | None = None
    status: str
