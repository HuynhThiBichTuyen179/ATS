from pydantic import BaseModel


class ApplyRequest(BaseModel):
    job_business_id: str
    candidate_full_name: str
    candidate_email: str
    candidate_phone: str
    # v2.3 Section 9.2: bat buoc chon Nguon ho so tu danh muc da cau hinh
    # (candidate_sources), khong con la text tu do/tuy chon nhu truoc.
    source_business_id: str
    ai_consent: bool
    # Cho phep (khong bat buoc) Candidate tu khai bao them thong tin luc ung
    # tuyen - truoc day cac truong nay chi HR nhap ho duoc qua "Them ung vien",
    # Candidate tu ung tuyen khong co cach nao dien duoc.
    candidate_gender: str | None = None  # "MALE" | "FEMALE" | "OTHER"
    candidate_skills_summary: str | None = None
    candidate_experience_summary: str | None = None
    desired_salary: float | None = None
    # Dan noi dung CV truc tiep - luu THAT vao bang resumes. Upload file that
    # (PDF/DOCX) dung endpoint rieng POST /applications/{id}/resume sau khi tao.
    resume_text: str | None = None


class ApplicationOut(BaseModel):
    business_id: str
    job_business_id: str
    job_title: str
    # v2.3 fix: Candidate xem "Ho so cua toi" phai thay duoc mo ta/yeu cau cong
    # viec - khong dung GET /jobs/{id} rieng vi endpoint do co the 404 neu Job
    # da chuyen khoi PUBLISHED sau khi ung tuyen (VD CLOSED); day la du lieu
    # lich su cua chinh Application nay, luon phai xem duoc bat ke Job hien tai
    # con public hay khong.
    job_description: str
    job_requirements: str
    department_business_id: str | None = None
    department_name: str | None = None
    candidate_business_id: str
    candidate_full_name: str
    candidate_gender: str | None = None
    candidate_email: str
    candidate_phone: str
    candidate_skills_summary: str | None = None
    candidate_experience_summary: str | None = None
    desired_salary: float | None = None
    status: str
    is_new: bool
    source_business_id: str | None = None
    source: str | None = None
    match_score: int | None = None
    needs_manual_review: bool = False
    has_resume: bool = False
    resume_file_name: str | None = None
    resume_text: str | None = None
    applied_at: str

    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    business_id: str
    file_name: str
    file_type: str
    extracted_text: str | None = None
    extracted_chars: int = 0
    uploaded_at: str | None = None


class UpdateStatusRequest(BaseModel):
    status: str
    reason: str | None = None


class ArchiveRequest(BaseModel):
    archive_reason: str  # "REJECTED_ARCHIVE" | "TALENT_POOL"


class ApplicationUpdateRequest(BaseModel):
    """v2.3 Section 18 - PUT /applications/{id} (moi). Chi cho sua cac field
    KHONG lam vo relationship co dinh: khong doi job_id/candidate_id qua day
    (Section 5: "Neu field bi rang buoc boi Application/Job: khong duoc pha
    vo relationship" - doi Job/Candidate can nghiep vu rieng, ngoai pham vi
    1 form sua don gian)."""

    desired_salary: float | None = None
    source_business_id: str | None = None
