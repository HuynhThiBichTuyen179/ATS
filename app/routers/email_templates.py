from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.id_generator import generate_business_id
from app.deps.rbac import require_hr_manager_or_admin, require_hr_or_above
from app.models.application import Application
from app.models.email_template import EmailTemplate
from app.models.enums import EmailTemplateStatus, EmailTemplateType
from app.models.interview import Interview
from app.models.offer import Offer
from app.models.user import User
from app.schemas.email_template import (
    EmailTemplateCreateRequest,
    EmailTemplateOut,
    EmailTemplateUpdateRequest,
    SendEmailRequest,
)
from app.services import audit_service, email_service

router = APIRouter(prefix="/email-templates", tags=["email-templates"])


def _to_out(t: EmailTemplate) -> EmailTemplateOut:
    return EmailTemplateOut(
        business_id=t.business_id, name=t.name, type=t.type.value, subject=t.subject, content=t.content,
        status=t.status.value,
    )


@router.post("", response_model=EmailTemplateOut)
def create_template(
    payload: EmailTemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # Template Code (= business_id, tu sinh, da unique qua generate_business_id)
    # khong duoc trung - bo sung them check trung TEN (name) vi day la dinh
    # danh nguoi dung nhin thay/chon khi gui email.
    try:
        email_type = EmailTemplateType(payload.type)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_TEMPLATE_TYPE")
    if db.query(EmailTemplate).filter(EmailTemplate.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "TEMPLATE_NAME_ALREADY_EXISTS")

    template = EmailTemplate(
        business_id=generate_business_id(db, "email_template"),
        name=payload.name,
        type=email_type,
        subject=payload.subject,
        content=payload.content,
        status=EmailTemplateStatus.ACTIVE,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()
    audit_service.log(
        db, actor=current_user, action="EMAIL_TEMPLATE_CREATED",
        entity_type="email_template", entity_business_id=template.business_id,
        after={"name": template.name, "type": template.type.value},
    )
    db.commit()
    db.refresh(template)
    return _to_out(template)


@router.get("", response_model=list[EmailTemplateOut])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(require_hr_or_above)):
    # RBAC 4.1: HR "Xem & dung"; HR Manager/Admin full - tat ca HR+ xem duoc.
    templates = db.query(EmailTemplate).order_by(EmailTemplate.id).all()
    return [_to_out(t) for t in templates]


@router.get("/{template_business_id}", response_model=EmailTemplateOut)
def get_template(
    template_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    template = db.query(EmailTemplate).filter(EmailTemplate.business_id == template_business_id).first()
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TEMPLATE_NOT_FOUND")
    return _to_out(template)


@router.put("/{template_business_id}", response_model=EmailTemplateOut)
def update_template(
    template_business_id: str,
    payload: EmailTemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # HR_MANAGER va ADMIN deu sua duoc. Khong cho sua business_id/created_at/
    # created_by/type (giu bat bien - type khong nam trong
    # EmailTemplateUpdateRequest nen khong the bi sua o day).
    template = db.query(EmailTemplate).filter(EmailTemplate.business_id == template_business_id).first()
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TEMPLATE_NOT_FOUND")

    before = {"name": template.name, "subject": template.subject, "content": template.content, "status": template.status.value}
    changed_fields = []
    if payload.name is not None and payload.name != template.name:
        if db.query(EmailTemplate).filter(EmailTemplate.name == payload.name, EmailTemplate.id != template.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "TEMPLATE_NAME_ALREADY_EXISTS")
        template.name = payload.name
        changed_fields.append("name")
    if payload.subject is not None:
        template.subject = payload.subject
        changed_fields.append("subject")
    if payload.content is not None:
        template.content = payload.content
        changed_fields.append("content")
    if payload.status is not None:
        try:
            template.status = EmailTemplateStatus(payload.status)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS")
        changed_fields.append("status")

    db.flush()
    # Audit EMAIL_TEMPLATE_UPDATED voi actor/template_id/timestamp (tu dong
    # qua AuditLog.created_at)/changed fields + before-after. Khong log thong
    # tin nhay cam (template khong chua password/token nen an toan).
    audit_service.log(
        db, actor=current_user, action="EMAIL_TEMPLATE_UPDATED",
        entity_type="email_template", entity_business_id=template.business_id,
        before=before,
        after={"name": template.name, "subject": template.subject, "content": template.content, "status": template.status.value},
        reason=f"changed_fields={','.join(changed_fields)}" if changed_fields else None,
    )
    db.commit()
    db.refresh(template)
    return _to_out(template)


@router.post("/{template_business_id}/deactivate", response_model=EmailTemplateOut)
def deactivate_template(
    template_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_manager_or_admin),
):
    # "Xoa" trong RBAC = soft-delete (INACTIVE), khong xoa vat ly - nhat quan
    # voi Rule 3 (khong xoa vat ly du lieu quan trong) va giu lich su.
    template = db.query(EmailTemplate).filter(EmailTemplate.business_id == template_business_id).first()
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TEMPLATE_NOT_FOUND")
    before = {"status": template.status.value}
    template.status = EmailTemplateStatus.INACTIVE
    db.flush()
    audit_service.log(
        db, actor=current_user, action="EMAIL_TEMPLATE_DELETED",
        entity_type="email_template", entity_business_id=template.business_id,
        before=before, after={"status": template.status.value}, reason="Soft-delete (INACTIVE)",
    )
    db.commit()
    db.refresh(template)
    return _to_out(template)


@router.post("/send/{application_business_id}")
def send_manual_email(
    application_business_id: str,
    payload: SendEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_above),
):
    application = db.query(Application).filter(Application.business_id == application_business_id).first()
    if not application:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "APPLICATION_NOT_FOUND")
    template = db.query(EmailTemplate).filter(EmailTemplate.business_id == payload.template_business_id).first()
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TEMPLATE_NOT_FOUND")

    from app.core.config import settings as app_settings

    variables = {
        "candidate_name": application.candidate.full_name,
        "job_title": application.job.title,
        "company_name": app_settings.company_name,
    }
    # Chi co 3 bien tren la khong du - mau nao co placeholder rieng cua tung
    # giai doan (VD {{start_date}}, {{offer_salary}}, {{interview_time}}) se
    # hien nguyen chuoi "{{...}}" khong duoc thay the khi gui thu cong. Bo
    # sung them bang cach tim ban ghi Offer/Interview GAN NHAT cua Application
    # nay (neu co) - dung best-effort, khong bat buoc phai ton tai (VD mau
    # OFFER duoc chon cho mot Application chua tung co Offer thi placeholder
    # do van hien nguyen, khong co gia tri nao hop ly de dien vao).
    latest_offer = (
        db.query(Offer).filter(Offer.application_id == application.id).order_by(Offer.id.desc()).first()
    )
    if latest_offer:
        variables["offer_salary"] = f"{latest_offer.salary:,.0f} VND"
        variables["start_date"] = latest_offer.start_date.isoformat()

    latest_interview = (
        db.query(Interview).filter(Interview.application_id == application.id).order_by(Interview.id.desc()).first()
    )
    if latest_interview:
        variables["interview_time"] = latest_interview.scheduled_at.strftime("%d/%m/%Y %H:%M")
        variables["interview_location"] = latest_interview.location or latest_interview.meeting_link or ""

    subject, body = email_service.render_template(template.subject, template.content, variables)
    success, status_message = email_service.send_email(
        db, current_user, application.candidate.email, subject, body, application.business_id
    )
    return {"success": success, "status_message": status_message, "to": application.candidate.email, "subject": subject}
