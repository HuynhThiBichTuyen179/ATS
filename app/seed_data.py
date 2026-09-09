# Seed du lieu toi thieu de chay thu API va lam co so cho manual test.
# Chay: python -m app.seed_data
#
# Idempotent THEO TUNG EMAIL CU THE (khong phai theo "co user nao chua") - neu
# ban da tu dang ky mot Candidate that truoc khi chay script nay, du lieu do
# van duoc giu nguyen; script chi tao them cac tai khoan demo con thieu.

from app.core.database import Base, SessionLocal, engine
from app.core.id_generator import generate_business_id
from app.core.security import hash_password
from app.models.department import Department
from app.models.email_template import EmailTemplate
from app.models.enums import EmailTemplateStatus, EmailTemplateType, EmploymentType, JobStatus, UserRole, UserStatus
from app.models.job import Job
from app.models.user import User

DEMO_DEPARTMENT_NAME = "Cong nghe thong tin"
DEMO_USERS = [
    ("admin@example.com", "Admin", "Admin@123", UserRole.ADMIN),
    ("hrmanager.a@example.com", "HR Manager A", "HrManager@123", UserRole.HR_MANAGER),
    ("hrmanager.b@example.com", "HR Manager B", "HrManager@123", UserRole.HR_MANAGER),
    ("hr.a@example.com", "HR Nguyen Van A", "Hr@123456", UserRole.HR),
]


DEMO_EMAIL_TEMPLATES = [
    (
        EmailTemplateType.APPLICATION_RECEIVED,
        "XÁC NHẬN HỒ SƠ",
        "[{{company_name}}] Đã nhận được hồ sơ ứng tuyển của bạn",
        "Chào {{candidate_name}},\n\n"
        "{{company_name}} xác nhận bạn đã nhận được hồ sơ ứng tuyển của bạn cho vị trí {{job_title}}.\n\n"
        "Bộ phận tuyển dụng sẽ xem xét và phản hồi trong thời gian sớm nhất.\n\n"
        "Trân trọng.\n{{company_name}}",
    ),
    (
        EmailTemplateType.SHORTLISTED,
        "VÀO VÒNG TIẾP THEO",
        "[{{company_name}}] Bạn đã được chọn vào vòng tiếp theo",
        "Chào {{candidate_name}},\n\n"
        "Chúc mừng bạn đã vượt qua vòng sàng lọc hồ sơ cho vị trí {{job_title}} tại {{company_name}}.\n"
        "Chúng tôi sẽ liên hệ để sắp xếp bước tiếp theo trong quy trình tuyển dụng.\n\n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        EmailTemplateType.INTERVIEW_INVITATION,
        "THƯ MỜI PHỎNG VẤN",
        "[{{company_name}}] Thư mời phỏng vấn vị trí{{job_title}}",
        "Chào {{candidate_name}},\n\n"
        "{{company_name}} trân trọng mời bạn tham gia phỏng vấn cho vị trí {{job_title}}.\n"
        "Bộ phận tuyển dụng sẽ sớm liên hệ để xác nhận thời gian và hình thức phỏng vấn cụ thể. \n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        EmailTemplateType.INTERVIEW_REMINDER,
        "NHẮC LỊCH PHỎNG VẤN",
        "[{{company_name}}] Nhắc lịch phỏng vấn cho vị trí {{job_title}}",
        "Chào {{candidate_name}},\n\n"
        "Đây là email nhắc lịch phỏng vấn cho vị trí {{job_title}} tại {{company_name}}.\n"
        "Mong bạn sắp xếp tham dự đúng giờ. Hẹn gặp lại bạn sau.\n\n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        EmailTemplateType.REJECTION,
        "THÔNG BÁO KẾT QUẢ TUYỂN DỤNG",
        "[{{company_name}}] Thông báo kết quả ứng tuyển vị trí {{job_title}}",
        "Chào {{candidate_name}},\n\n"
        "Cảm ơn bạn đã dành thời gian ứng tuyển cho vị trí {{job_title}} tại {{company_name}}.\n"
        "Sau khi xem xét, chúng tôi rất tiếc phải thông báo rằng bạn chưa phù hợp cho vị trí này ở thời điểm hiện tại. \n"
        "Chúng tôi sẽ lưu hồ sơ của bạn cho các cơ hội phù hợp trong tương lai. \n\n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        EmailTemplateType.OFFER,
        "THƯ MỜI NHẬN VIỆC",
        "[{{company_name}}] Thư mời nhận việc - {{job_title}}",
        "Chào {{candidate_name}},\n\n"
        "{{company_name}} trân trọng gửi thư mời nhận việc cho vị trí {{job_title}}.\n"
        "Mức lương đề xuất: {{offer_salary}}. Ngày bắt đầu dự kiến: {{start_date}}.\n"
        "Vui lòng phản hồi (Đồng ý /Từ chối) trước hạn quy định trong hệ thống.\n\n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        EmailTemplateType.ONBOARDING,
        "CHÀO MỪNG GIA NHẬP",
        "[{{company_name}}] Chào mừng bạn gia nhập {{company_name}}",
        "Chào {{candidate_name}},\n\n"
        "Chúc mừng bạn đã chính thức trở thành thành viên của {{company_name}} ở vị trí {{job_title}}.\n"
        "Ngày bắt đầu dự kiến: {{start_date}}. Bộ phận nhân sự sẽ liên hệ hướng dẫn các bước tiếp theo. \n\n"
        "Trân trọng,\n{{company_name}}",
    ),
    (
        
        EmailTemplateType.PASSWORD_RESET,
        "ĐẶT LẠI MẬT KHẨU",
        "[{{company_name}}] Yêu cầu đặt lại mật khẩu",
        "Chào {{user_name}},\n\n"
        "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn tại {{company_name}}.\n"
        "Vui lòng nhập vào liên kết sau để đặt lại mật khẩu mới (hết hạn sau {{expiry_minutes}} phút):\n"
        "{{reset_link}}\n\n"
        "Trân trọng,\n{{company_name}}",
    ),
]


def _get_or_create_department(db) -> Department:
    dept = db.query(Department).filter(Department.name == DEMO_DEPARTMENT_NAME).first()
    if dept:
        return dept
    dept = Department(business_id=generate_business_id(db, "department"), name=DEMO_DEPARTMENT_NAME)
    db.add(dept)
    db.flush()
    return dept


def _get_or_create_user(db, email, full_name, password, role, department_id) -> tuple[User, bool]:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user, False
    user = User(
        business_id=generate_business_id(db, "user"),
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        department_id=department_id if role != UserRole.ADMIN else None,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user, True


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        dept = _get_or_create_department(db)

        created_any = False
        users_by_email = {}
        for email, full_name, password, role in DEMO_USERS:
            user, was_created = _get_or_create_user(db, email, full_name, password, role, dept.id)
            users_by_email[email] = user
            created_any = created_any or was_created

        admin = users_by_email["admin@example.com"]
        hr_manager_a = users_by_email["hrmanager.a@example.com"]
        hr = users_by_email["hr.a@example.com"]

        job = db.query(Job).filter(Job.slug == "backend-engineer-demo").first()
        if not job:
            job = Job(
                business_id=generate_business_id(db, "job"),
                slug="backend-engineer-demo",
                title="Backend Engineer",
                department_id=dept.id,
                description="Phat trien API FastAPI",
                requirements="2+ nam Python, FastAPI, MySQL",
                salary_min=20000000,
                salary_max=35000000,
                quantity=2,
                location="Ha Noi",
                employment_type=EmploymentType.FULL_TIME,
                status=JobStatus.PUBLISHED,
                created_by=hr_manager_a.id,
                assigned_hr_id=hr.id,
                approved_by=admin.id,
            )
            db.add(job)
            created_any = True

        templates_created = 0
        for etype, name, subject, content in DEMO_EMAIL_TEMPLATES:
            exists = (
                db.query(EmailTemplate)
                .filter(EmailTemplate.type == etype, EmailTemplate.status == EmailTemplateStatus.ACTIVE)
                .first()
            )
            if exists:
                continue
            db.add(
                EmailTemplate(
                    business_id=generate_business_id(db, "email_template"),
                    name=name,
                    type=etype,
                    subject=subject,
                    content=content,
                    status=EmailTemplateStatus.ACTIVE,
                    created_by=admin.id,
                )
            )
            templates_created += 1
            created_any = True

        db.commit()

        if not created_any:
            print("Tat ca tai khoan/job demo da ton tai san, khong tao them gi.")
        else:
            print("Seed hoan tat (chi tao nhung gi con thieu, khong dong vao du lieu san co):")
        print(f"  Department: {dept.business_id} ({dept.name})")
        for email, full_name, password, role in DEMO_USERS:
            u = users_by_email[email]
            print(f"  {role.value}: {u.business_id} / {email} / {password}")
        print(f"  Job: {job.business_id} ({job.status.value})")
        print(f"  Email templates tao moi: {templates_created} (tong so mau ACTIVE hien co theo tung loai su kien).")

        total_users = db.query(User).count()
        print(f"\nTong so user hien co trong DB: {total_users} (bao gom ca tai khoan ban tu dang ky, neu co).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
