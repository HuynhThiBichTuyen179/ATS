from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class OfferCreateRequest(BaseModel):
    application_business_id: str
    salary: Decimal
    probation_salary: Decimal
    start_date: date


class OfferRejectRequest(BaseModel):
    reason: str


class OfferRespondRequest(BaseModel):
    response: str  # "ACCEPTED" | "DECLINED"


class OfferOut(BaseModel):
    business_id: str
    application_business_id: str
    # bo sung du thong tin ung vien + Job de nguoi duyet quyet dinh duoc ma khong phai mo rieng Application.
    candidate_business_id: str
    candidate_full_name: str
    candidate_email: str
    job_business_id: str
    job_title: str
    department_name: str | None = None
    creator_business_id: str
    creator_name: str
    approver_business_id: str | None = None
    approver_name: str | None = None
    status: str
    salary: Decimal
    probation_salary: Decimal
    start_date: str

    model_config = {"from_attributes": True}
