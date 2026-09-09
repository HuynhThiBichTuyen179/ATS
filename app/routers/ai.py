from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.rbac import require_hr_or_above
from app.models.ai_analysis import AIAnalysis
from app.models.application import Application
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ai import AIAnalysisOut
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


def _check_scope(current_user: User, application: Application) -> None:
    if current_user.role == UserRole.HR and application.assigned_hr_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "NOT_YOUR_ASSIGNED_APPLICATION")


@router.post("/analyze/{application_business_id}")
def analyze(
    application_business_id: str,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    _check_scope(current_user, application)

    try:
        analysis = ai_service.run_screening(db, application, current_user)
    except ai_service.AIAnalysisError as e:
        # chua cau hinh key hoac goi that bai deu bao loi CU THE cho nguoi dung
        raise HTTPException(e.status_code, e.detail)
    if analysis is None:
        # AI khong chay duoc (khong co CV text) -> 202, khong phai loi 500, de frontend hien dung trang thai thay vi coi la bug.
        response.status_code = status.HTTP_202_ACCEPTED
        return {"needs_manual_review": True, "detail": "NO_RESUME_TEXT_AVAILABLE"}
    return AIAnalysisOut.from_model(analysis)


@router.get("/analysis/{application_business_id}", response_model=list[AIAnalysisOut])
def get_analysis_history(
    application_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    _check_scope(current_user, application)

    analyses = (
        db.query(AIAnalysis)
        .filter(AIAnalysis.application_id == application.id)
        .order_by(AIAnalysis.id.desc())
        .all()
    )
    return [AIAnalysisOut.from_model(a) for a in analyses]
