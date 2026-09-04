from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None
    role: str  # "HR" | "HR_MANAGER" | "ADMIN"
    department_business_id: str | None = None

    @field_validator("password")
    @classmethod
    def password_must_have_letter_and_digit(cls, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT")
        return value


class UserUpdateRequest(BaseModel):
    """Section 13/14 - sua thong tin HR/HR_MANAGER/ADMIN. Khong cho sua qua
    day: password (co endpoint doi mat khau rieng qua reset flow), role doi
    tuy tien khong nam trong scope dot nay (giu nguyen RBAC tao-role hien co
    o create_user), business_id/created_at bat bien."""

    full_name: str | None = None
    phone: str | None = None
    department_business_id: str | None = None
    status: str | None = None  # "ACTIVE" | "INACTIVE" | "LOCKED"


class UserOut(BaseModel):
    business_id: str
    full_name: str
    email: str
    role: str
    status: str
    department_business_id: str | None = None
