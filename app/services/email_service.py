"""Email Automation Engine - v2 Phan 9/13. Luon gui that qua SMTP (Gmail) -
KHONG con che do gia lap (SIMULATE) da bo theo yeu cau nghiep vu, giong
nguyen tac da ap dung cho AI Screening: neu SMTP chua cau hinh dung
(SMTP_USER/SMTP_PASSWORD trong .env), viec gui se that bai that va duoc ghi
nhan la that bai that (FAILED), khong am tham coi la "da xu ly" qua nhan
SIMULATED.
"""

import smtplib
import ssl
from email.message import EmailMessage
from email.policy import default as default_email_policy

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import EmailTemplateStatus, EmailTemplateType
from app.models.email_template import EmailTemplate
from app.models.user import User
from app.services import audit_service


# BUG FIX: policy mac dinh cua email.message gioi han moi dong header 78 ky
# tu (max_line_length), buoc phai "fold" (ngat dong) tieu de tieng Viet dai
# thanh nhieu doan ma hoa RFC 2047 rieng biet - qua kiem chung thuc te, thuat
# toan fold nay co the LAM MAT 1 KY TU KHOANG TRANG dung tai diem ngat (vd
# "gia nhap" bi gui di thanh "gianhap", da xac nhan qua email That nhan duoc).
# Clone policy voi max_line_length=998 (gioi han toi da 1 dong header theo
# RFC 5322) de tieu de o do dai thong thuong luon nam gon trong 1 doan ma hoa
# duy nhat, khong bao gio can ngat dong - loai bo hoan toan nguy co mat ky tu.
_EMAIL_POLICY = default_email_policy.clone(max_line_length=998)


def render_template(subject_template: str, content_template: str, variables: dict) -> tuple[str, str]:
    subject, content = subject_template, content_template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        subject = subject.replace(placeholder, str(value))
        content = content.replace(placeholder, str(value))
    return subject, content


def send_raw_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """Gui email that qua SMTP. Tra ve (success, status_message). Neu
    SMTP_USER/SMTP_PASSWORD chua cau hinh, smtplib se tu bao loi xac thuc that
    (khong can kiem tra truoc) - loi do duoc bat lai o khoi except ben duoi va
    tra ve FAILED voi thong diep cu the, dung im lang coi nhu da xu ly."""
    msg = EmailMessage(policy=_EMAIL_POLICY)
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = to_email
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls(context=context)
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True, "SENT (SMTP that)"
    except Exception as e:
        return False, f"FAILED (SMTP error: {e})"


def send_email(
    db: Session,
    actor: User,
    to_email: str,
    subject: str,
    body: str,
    application_business_id: str | None = None,
) -> tuple[bool, str]:
    """Gui email + luon ghi audit_logs (thay cho bang email_logs rieng - v2
    khong co bang nay trong 11 bang, tai su dung audit_logs cho gon, dung tinh
    than KISS). Khong bao gio raise exception ra ngoai - loi gui mail khong
    duoc phep lam hong luong nghiep vu chinh (vd doi trang thai Application).
    """
    success, status_message = send_raw_email(to_email, subject, body)
    audit_service.log(
        db,
        actor=actor,
        action="EMAIL_SENT" if success else "EMAIL_FAILED",
        entity_type="application" if application_business_id else "email",
        entity_business_id=application_business_id or to_email,
        after={"to": to_email, "subject": subject},
        reason=status_message,
    )
    db.commit()
    return success, status_message


def trigger_stage_email(
    db: Session,
    actor: User,
    application,
    event_type: EmailTemplateType,
    extra_vars: dict | None = None,
) -> None:
    """Tu dong gui email theo giai doan (v2 Phan 9). Best-effort: neu chua co
    Email Template ACTIVE cho loai su kien nay, bo qua trong im lang (khong
    phai loi - HR Manager co the chua cau hinh template cho giai doan do).
    """
    template = (
        db.query(EmailTemplate)
        .filter(EmailTemplate.type == event_type, EmailTemplate.status == EmailTemplateStatus.ACTIVE)
        .first()
    )
    if not template:
        return

    variables = {
        "candidate_name": application.candidate.full_name,
        "job_title": application.job.title,
        "company_name": settings.company_name,
    }
    if extra_vars:
        variables.update(extra_vars)

    subject, body = render_template(template.subject, template.content, variables)
    try:
        send_email(db, actor, application.candidate.email, subject, body, application.business_id)
    except Exception:
        # Khong de loi gui mail lam fail transaction nghiep vu chinh.
        pass
