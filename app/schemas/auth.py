import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_must_have_letter_and_digit(cls, value: str) -> str:
        # v2 Phan 4.4: "toi thieu 8 ky tu, co it nhat 1 chu va 1 so" - truoc ban
        # vá nay chi check min_length, thieu dieu kien complexity.
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_must_have_letter_and_digit(cls, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT")
        return value


class UserOut(BaseModel):
    business_id: str
    full_name: str
    email: str
    role: str

    model_config = {"from_attributes": True}
