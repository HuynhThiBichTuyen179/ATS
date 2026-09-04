from pydantic import BaseModel, EmailStr


class CandidateCreateRequest(BaseModel):
    """v2.2 Section 1 - form "Them ung vien" danh cho HR/HR_MANAGER/ADMIN.
    Tao dong thoi 1 Candidate + 1 Application (job_business_id bat buoc, vi
    Section 2 yeu cau lien ket Job bang ID ngay tu luc tao, khong chi luu ten).
    """

    full_name: str
    gender: str | None = None  # "MALE" | "FEMALE" | "OTHER"
    email: EmailStr
    phone: str

    job_business_id: str
    desired_salary: float | None = None
    source: str | None = None  # ten CandidateSource (tu do nhap ho tro "Other")

    skills_summary: str | None = None
    experience_summary: str | None = None


class CandidateUpdateRequest(BaseModel):
    """Chi cho sua thong tin ho so - KHONG cho sua candidate_id/created_at/
    audit info/AI history (Section 9)."""

    full_name: str | None = None
    gender: str | None = None
    phone: str | None = None
    skills_summary: str | None = None
    experience_summary: str | None = None


class CandidateOut(BaseModel):
    business_id: str
    full_name: str
    gender: str | None = None
    email: str
    phone: str
    skills_summary: str | None = None
    experience_summary: str | None = None
    status: str
