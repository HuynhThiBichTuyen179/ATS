from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class JobCreateRequest(BaseModel):
    title: str
    department_business_id: str
    description: str
    requirements: str
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    quantity: int = 1
    location: str
    employment_type: str
    assigned_hr_business_id: str | None = None  # optional luc tao, co the gan sau qua /assign-hr
    deadline: date | None = None  # han ung tuyen - tuy chon, khong gioi han neu de trong


class AssignHrRequest(BaseModel):
    hr_business_id: str


class JobUpdateRequest(BaseModel):
    """Sua tin tuyen dung - cho phep bat ke Job dang DRAFT hay da PUBLISHED
    (theo yeu cau nguoi dung). Khong cho doi department/status/assigned_hr qua
    day - da co route rieng (/assign-hr, /publish) tranh lam vo quy trinh."""

    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    quantity: int | None = None
    location: str | None = None
    employment_type: str | None = None
    deadline: date | None = None


class JobOut(BaseModel):
    business_id: str
    title: str
    department_business_id: str
    department_name: str | None = None
    description: str
    requirements: str
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    quantity: int
    location: str
    employment_type: str
    status: str
    deadline: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    assigned_hr_business_id: str | None = None
    assigned_hr_name: str | None = None

    model_config = {"from_attributes": True}
