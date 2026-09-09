import enum


class UserRole(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    HR = "HR"
    HR_MANAGER = "HR_MANAGER"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"


class ApplicationStatus(str, enum.Enum):
    NEW = "NEW"
    AI_SCREENING = "AI_SCREENING"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ARCHIVED = "ARCHIVED"


class ArchiveReason(str, enum.Enum):
    REJECTED_ARCHIVE = "REJECTED_ARCHIVE"
    TALENT_POOL = "TALENT_POOL"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InterviewType(str, enum.Enum):
    ONSITE = "ONSITE"
    ONLINE = "ONLINE"


# soft-delete cho Candidate (khong co field status truoc do) - ARCHIVED
# thay cho xoa vat ly, giu nguyen lich su Application/Interview/Offer/AI lien quan.
class CandidateStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class CandidateSourceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# Offer.status khong co gia tri REJECTED (bi trung nghia voi "tu choi luc duyet"
# - nay chi con la buoc PENDING_APPROVAL -> DRAFT, khong terminal). Trang thai
# Candidate tu choi Offer dat ten la DECLINED de tranh nham lan.
class OfferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class EmailTemplateType(str, enum.Enum):
    APPLICATION_RECEIVED = "APPLICATION_RECEIVED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_INVITATION = "INTERVIEW_INVITATION"
    INTERVIEW_REMINDER = "INTERVIEW_REMINDER"
    # 2 su kien rieng cho Interview Calendar (khac INTERVIEW_INVITATION luc tao
    # lich, dung de phan biet doi lich vs huy).
    INTERVIEW_RESCHEDULED = "INTERVIEW_RESCHEDULED"
    INTERVIEW_CANCELLED = "INTERVIEW_CANCELLED"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    ONBOARDING = "ONBOARDING"
    PASSWORD_RESET = "PASSWORD_RESET"


class EmailTemplateStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
