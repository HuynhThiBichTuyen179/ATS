from pydantic import BaseModel


class EmailTemplateCreateRequest(BaseModel):
    name: str
    type: str  # APPLICATION_RECEIVED | SHORTLISTED | INTERVIEW_INVITATION | INTERVIEW_REMINDER | REJECTION | OFFER | ONBOARDING
    subject: str
    content: str


class EmailTemplateUpdateRequest(BaseModel):
    name: str | None = None
    subject: str | None = None
    content: str | None = None
    status: str | None = None  # ACTIVE | INACTIVE


class EmailTemplateOut(BaseModel):
    business_id: str
    name: str
    type: str
    subject: str
    content: str
    status: str


class SendEmailRequest(BaseModel):
    template_business_id: str
