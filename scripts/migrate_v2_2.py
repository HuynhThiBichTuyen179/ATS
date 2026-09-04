"""Migration thu cong cho ATS v2.2 (khong co Alembic - xem Gap G-TECH-01).

An toan: chi ADD COLUMN vao bang da co du lieu (candidates, applications),
khong DROP/khong sua cot cu. Rieng bang `interviews` dang RONG hoan toan (0
dong ca SQLite lan MySQL, da xac nhan truoc khi viet script nay) nen duoc
DROP + tao lai qua create_all() thay vi ALTER - don gian hon ma khong mat gi.

Chay: python -m scripts.migrate_v2_2
Idempotent: kiem tra cot da ton tai truoc khi ALTER, chay lai nhieu lan an toan.
"""

from sqlalchemy import inspect, text

from app.core.database import Base, engine
from app.models.enums import EmailTemplateType
import app.models  # noqa: F401 - dam bao moi model da dang ky voi Base


def _has_column(insp, table: str, column: str) -> bool:
    return column in {c["name"] for c in insp.get_columns(table)}


def run():
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())

    with engine.begin() as conn:
        # --- candidates: status, skills_summary, experience_summary ---
        if "candidates" in existing_tables:
            if not _has_column(insp, "candidates", "status"):
                conn.execute(text(
                    "ALTER TABLE candidates ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"
                ))
                print("[MIGRATE] candidates.status da them")
            if not _has_column(insp, "candidates", "skills_summary"):
                conn.execute(text("ALTER TABLE candidates ADD COLUMN skills_summary TEXT"))
                print("[MIGRATE] candidates.skills_summary da them")
            if not _has_column(insp, "candidates", "experience_summary"):
                conn.execute(text("ALTER TABLE candidates ADD COLUMN experience_summary TEXT"))
                print("[MIGRATE] candidates.experience_summary da them")

        # --- applications: department_id, desired_salary ---
        if "applications" in existing_tables:
            if not _has_column(insp, "applications", "department_id"):
                conn.execute(text("ALTER TABLE applications ADD COLUMN department_id INTEGER"))
                print("[MIGRATE] applications.department_id da them")
            if not _has_column(insp, "applications", "desired_salary"):
                conn.execute(text("ALTER TABLE applications ADD COLUMN desired_salary NUMERIC(12,2)"))
                print("[MIGRATE] applications.desired_salary da them")

    # Backfill: Job Department = Application Department (Section 3) cho cac
    # Application da ton tai truoc migration (chua co department_id).
    with engine.begin() as conn:
        # Khong dung alias bang trong UPDATE (SQLite khong ho tro cu phap
        # "UPDATE table alias SET ..." nhu MySQL) - dung ten bang truc tiep
        # trong subquery de tuong thich ca 2 dialect.
        result = conn.execute(text(
            "UPDATE applications "
            "SET department_id = (SELECT j.department_id FROM jobs j WHERE j.id = applications.job_id) "
            "WHERE department_id IS NULL"
        ))
        print(f"[MIGRATE] Backfill department_id cho {result.rowcount} Application")

    # --- interviews: rong hoan toan -> drop + tao lai voi schema moi (co
    # end_time, interview_type) thay vi ALTER nhieu buoc.
    if "interviews" in existing_tables:
        with engine.begin() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM interviews")).scalar()
        if count == 0:
            Base.metadata.tables["interviews"].drop(bind=engine)
            print("[MIGRATE] interviews (rong) da drop de tao lai schema moi")
        else:
            print(f"[MIGRATE CANH BAO] interviews co {count} dong, KHONG drop - can migration thu cong rieng")

    # Tao cac bang moi (candidate_sources, password_reset_tokens, interviews
    # neu vua drop) - create_all() bo qua bang da ton tai, an toan goi lai.
    Base.metadata.create_all(bind=engine)
    print("[MIGRATE] create_all() hoan tat - da tao cac bang con thieu.")

    # MySQL (khac SQLite) tao cot Enum() thanh native ENUM(...) co san list gia
    # tri co dinh luc tao bang - them EmailTemplateType.INTERVIEW_RESCHEDULED/
    # INTERVIEW_CANCELLED/PASSWORD_RESET vao enums.py KHONG tu dong cap nhat
    # ENUM da co san tren MySQL, phai ALTER MODIFY COLUMN thu cong.
    if engine.dialect.name == "mysql" and "email_templates" in existing_tables:
        all_values = ", ".join(f"'{v.value}'" for v in EmailTemplateType)
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE email_templates MODIFY COLUMN type ENUM({all_values}) NOT NULL"))
        print("[MIGRATE] email_templates.type (MySQL ENUM) da mo rong them gia tri moi")


if __name__ == "__main__":
    run()
