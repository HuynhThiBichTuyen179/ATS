import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DB_PATH = ROOT / "tests" / "test_ats_v2.db"

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OFFER_VALIDITY_DAYS"] = "7"
# Bat buoc tat MySQL trong test, bat ke .env dang cau hinh gi (VD USE_MYSQL=true
# cho moi truong dev that) - neu khong, fixture _reset_db se drop_all/create_all
# thang vao MySQL dev/production that truoc MOI test case, xoa sach du lieu that.
os.environ["USE_MYSQL"] = "false"
# Ep AI_API_KEY rong trong test, bat ke .env dang co credential that gi - neu
# khong, test se goi AI Provider that (ton chi phi API that, flaky vi phu
# thuoc mang/quota moi lan chay test). Khong con che do STUB - test nao can
# gia lap ket qua AI thi tu monkeypatch rieng (xem test_ai_screening.py).
os.environ["AI_API_KEY"] = ""
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.id_generator import generate_business_id  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models.candidate_source import CandidateSource  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.enums import EmploymentType, JobStatus, UserRole, UserStatus  # noqa: E402
from app.models.job import Job  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(autouse=True)
def _fake_smtp(monkeypatch):
    """email_service.py khong con che do gia lap rieng - luon thu goi SMTP
    that. Trong test, tu gia lap ket qua gui thanh cong tai day (khong dung
    het thoi gian cho ket noi SMTP that/that bai xac thuc that ~15 giay moi
    lan goi), thay vi de production code phai tu biet no "dang chay trong
    test" - danh dau ro rang trong status_message de phan biet voi gui that."""
    from app.services import email_service

    def _fake_send_raw_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
        return True, "SENT (gia lap trong moi truong test, khong goi SMTP that)"

    monkeypatch.setattr(email_service, "send_raw_email", _fake_send_raw_email)


@pytest.fixture(autouse=True)
def _reset_db():
    """Reset toan bo DB truoc MOI test de dam bao cach ly hoan toan (bao gom
    ca bo dem id_sequences) - tranh test truoc anh huong test sau.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(fastapi_app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seed(db):
    """Tao du lieu toi thieu: 1 department, 1 admin, 2 hr_manager, 1 hr, 1 job
    PUBLISHED. Tra ve dict chua business_id + password moi user de dang nhap
    qua API trong test.
    """
    dept = Department(business_id=generate_business_id(db, "department"), name="Cong nghe thong tin")
    db.add(dept)
    db.flush()

    def make_user(role, email, full_name):
        u = User(
            business_id=generate_business_id(db, "user"),
            full_name=full_name,
            email=email,
            password_hash=hash_password("Password@123"),
            role=role,
            department_id=dept.id,
            status=UserStatus.ACTIVE,
        )
        db.add(u)
        db.flush()
        return u

    admin = make_user(UserRole.ADMIN, "admin@example.com", "Admin BGD")
    hrm_a = make_user(UserRole.HR_MANAGER, "hrm.a@example.com", "HR Manager A")
    hrm_b = make_user(UserRole.HR_MANAGER, "hrm.b@example.com", "HR Manager B")
    hr = make_user(UserRole.HR, "hr.a@example.com", "HR Nguyen Van A")

    job = Job(
        business_id=generate_business_id(db, "job"),
        slug="backend-engineer-test",
        title="Backend Engineer",
        department_id=dept.id,
        description="desc",
        requirements="req",
        salary_min=20000000,
        salary_max=30000000,
        quantity=5,
        location="Ha Noi",
        employment_type=EmploymentType.FULL_TIME,
        status=JobStatus.PUBLISHED,
        created_by=hrm_a.id,
        assigned_hr_id=hr.id,
    )
    db.add(job)

    # v2.3 Section 9: Candidate Apply bat buoc chon Candidate Source - seed
    # san 1 source ACTIVE de cac test hien co (va test moi) dung lam gia tri
    # hop le mac dinh, khong can moi test tu tao rieng.
    source = CandidateSource(business_id=generate_business_id(db, "candidate_source"), name="Website")
    db.add(source)
    db.commit()

    return {
        "department_business_id": dept.business_id,
        "admin": {"email": admin.email, "business_id": admin.business_id},
        "hrm_a": {"email": hrm_a.email, "business_id": hrm_a.business_id},
        "hrm_b": {"email": hrm_b.email, "business_id": hrm_b.business_id},
        "hr": {"email": hr.email, "business_id": hr.business_id},
        "job_business_id": job.business_id,
        "source_business_id": source.business_id,
    }


def auth_headers(client: TestClient, email: str, password: str = "Password@123") -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_and_login_candidate(client: TestClient, email: str, full_name: str = "Nguyen Van Ung Vien") -> dict:
    resp = client.post(
        "/auth/register",
        json={"full_name": full_name, "email": email, "password": "Password@123", "phone": "0900000000"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
