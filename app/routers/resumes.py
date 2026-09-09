import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.rbac import get_current_user
from app.models.enums import UserRole
from app.models.resume import Resume
from app.models.user import User

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("/{resume_business_id}/download")
def download_resume(
    resume_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Tai file CV that. Uu tien authorization TRUOC khi cho download -
    # Candidate chi tai CV cua chinh minh; HR chi trong pham vi duoc gan;
    # HR_MANAGER/ADMIN khong gioi han.
    resume = db.query(Resume).filter(Resume.business_id == resume_business_id).first()
    if not resume:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "RESUME_NOT_FOUND")
    application = resume.application

    if current_user.role == UserRole.CANDIDATE:
        if application.candidate.user_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_APPLICATION")
    elif current_user.role == UserRole.HR:
        if application.assigned_hr_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")
    elif current_user.role not in (UserRole.HR_MANAGER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_PERMISSION")

    if not resume.file_path or not os.path.isfile(resume.file_path):
        # CV dang duoc dan text truc tiep (khong co file that) - khong the tai.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "RESUME_HAS_NO_DOWNLOADABLE_FILE")

    return FileResponse(
        path=resume.file_path,
        media_type=resume.file_type,
        filename=resume.file_name,  # ten hien thi khi tai ve - KHONG lo storage key noi bo
    )
