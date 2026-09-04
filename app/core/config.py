from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # CHI dung cho bo test tu dong (tests/conftest.py tu ghi de bien moi
    # truong nay + DATABASE_URL de cach ly hoan toan khoi MySQL dev/production
    # that) - ung dung that KHONG dung gia tri nay, xem use_mysql/database.py.
    database_url: str = "sqlite:///./ats_v2.db"

    # Bat buoc True cho ung dung that (dev/production) - he thong CHI dung
    # MySQL, khong con che do fallback ve SQLite khi ket noi that bai (da bo
    # theo yeu cau nghiep vu: tranh am tham chuyen sang mot CSDL khac voi cau
    # hinh da khai bao). Gia tri False chi duoc dung noi bo boi bo test tu
    # dong (xem database_url o tren va tests/conftest.py).
    use_mysql: bool = True
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_host: str = "localhost"
    mysql_port: str = "3306"
    mysql_db: str = "recruitment_db"

    jwt_secret: str = "change-me-in-production"
    jwt_access_token_hours: int = 8
    jwt_refresh_token_days: int = 30
    # v2.2 Section 23: han Reset Password Token (phut) - khuyen nghi 15-30.
    password_reset_token_expiry_minutes: int = 30

    offer_validity_days: int = 7
    ai_monthly_budget_cap_usd: float = 50.0

    public_app_url: str = "http://localhost:3000"
    hr_app_url: str = "http://localhost:3001"
    api_url: str = "http://localhost:8000"

    # SMTP (Gmail App Password khuyen nghi neu dung Gmail - tai khoan Gmail bat
    # 2FA thi mat khau thuong se KHONG dang nhap SMTP duoc, phai tao App
    # Password rieng tai myaccount.google.com/apppasswords). email_service
    # luon thu gui that qua SMTP - khong con che do gia lap; neu de trong hoac
    # sai thong tin, viec gui se that bai that (ghi audit_logs voi ket qua
    # that bai cu the) nhung khong lam fail luong nghiep vu chinh (vd nop ho so).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "ATS v2 Recruitment"
    company_name: str = "Công ty Demo ATS"

    # AI Provider - khong gan cung 1 nha cung cap: ai_provider chon nha cung
    # cap ("gemini" | "claude"), ai_api_key/ai_model dung chung cho moi
    # provider (xem PROVIDER_CALLERS/DEFAULT_MODELS trong ai_service.py). Neu
    # de trong ai_api_key, endpoint POST /ai/analyze tra loi 400 voi thong
    # bao ro rang (khong con che do stub/phan tich gia lap - da bo hoan toan
    # theo yeu cau nghiep vu, xem ai_service.py). Neu ai_model de trong, dung
    # model mac dinh cua provider da chon.
    ai_provider: str = "gemini"
    ai_api_key: str = ""
    ai_model: str = ""


settings = Settings()
