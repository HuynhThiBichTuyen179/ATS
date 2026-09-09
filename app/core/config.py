from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # CHI dung cho bo test tu dong (tests/conftest.py tu ghi de bien moi truong nay + DATABASE_URL de cach ly hoan toan khoi MySQL dev/production that)
    # ung dung that KHONG dung gia tri nay
    database_url: str = "sqlite:///./ats_v2.db"

    use_mysql: bool = True
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_host: str = "localhost"
    mysql_port: str = "3306"
    mysql_db: str = "recruitment_db"

    jwt_secret: str = "change-me-in-production"
    jwt_access_token_hours: int = 8
    jwt_refresh_token_days: int = 30
    
    password_reset_token_expiry_minutes: int = 30

    offer_validity_days: int = 7
    ai_monthly_budget_cap_usd: float = 50.0

    public_app_url: str = "http://localhost:3000"
    hr_app_url: str = "http://localhost:3001"
    api_url: str = "http://localhost:8000"

   
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "ATS Recruitment"
    company_name: str = "Công ty Demo ATS"

    
    ai_provider: str = "gemini"
    ai_api_key: str = ""
    ai_model: str = ""


settings = Settings()
