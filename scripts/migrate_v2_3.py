# Migration thu cong so 2.3 cho ATS (tiep noi migrate_v2_2.py - khong co Alembic).
#
# An toan: chi ADD COLUMN, khong DROP/khong mat du lieu. Backfill source_id
# best-effort tu ten source text cu (khong bat buoc khop 100%, du lieu source
# text cu van duoc giu nguyen lam snapshot du co khop duoc FK hay khong).
#
# Chay: python -m scripts.migrate_v2_3
# Idempotent: kiem tra cot da ton tai truoc khi ALTER, chay lai nhieu lan an toan.

from sqlalchemy import inspect, text

from app.core.database import Base, engine
import app.models  # noqa: F401 - dam bao moi model da dang ky voi Base


def _has_column(insp, table: str, column: str) -> bool:
    return column in {c["name"] for c in insp.get_columns(table)}


def _ensure_index(conn, insp, table: str, column: str) -> None:
    # Tao index don-cot neu chua co (kiem tra qua insp truoc, khong dung
    # 'IF NOT EXISTS' vi MySQL < 8.0.23 khong ho tro cu phap nay cho CREATE
    # INDEX - portable hon giua SQLite/MySQL cu-moi).
    existing_cols_indexed = {
        c for idx in insp.get_indexes(table) for c in idx["column_names"]
    }
    # Cot business_id/unique co san co the da tu tao index/unique-constraint
    # rieng - chi bo qua neu DA co index nao chua dung cot nay.
    if column in existing_cols_indexed:
        return
    index_name = f"ix_{table}_{column}"
    conn.execute(text(f"CREATE INDEX {index_name} ON {table} ({column})"))
    print(f"[MIGRATE v2.3] Index {index_name} da tao")


def run():
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())

    with engine.begin() as conn:
        if "applications" in existing_tables:
            if not _has_column(insp, "applications", "source_id"):
                conn.execute(text("ALTER TABLE applications ADD COLUMN source_id INTEGER"))
                print("[MIGRATE v2.3] applications.source_id da them")
            if engine.dialect.name == "mysql":
                
                conn.execute(text("ALTER TABLE applications MODIFY COLUMN source VARCHAR(100)"))
                print("[MIGRATE v2.3] applications.source (MySQL) da mo rong VARCHAR(50)->VARCHAR(100)")

 
    insp = inspect(engine)  # refresh sau khi co the vua ALTER them cot o tren
    with engine.begin() as conn:
        if "applications" in existing_tables:
            for col in ("candidate_id", "job_id", "source_id", "status"):
                _ensure_index(conn, insp, "applications", col)
        if "resumes" in existing_tables:
            _ensure_index(conn, insp, "resumes", "candidate_id")
        if "jobs" in existing_tables:
            _ensure_index(conn, insp, "jobs", "status")
            _ensure_index(conn, insp, "jobs", "department_id")
        if "candidate_sources" in existing_tables:
            _ensure_index(conn, insp, "candidate_sources", "status")

    # Backfill best-effort: neu source text cu (VD "LinkedIn") khop chinh xac
    # ten 1 CandidateSource da cau hinh, gan source_id tuong ung. Khong khop
    # duoc thi giu nguyen source_id = NULL, source (text) khong doi.
    with engine.begin() as conn:
        result = conn.execute(text(
            "UPDATE applications "
            "SET source_id = (SELECT cs.id FROM candidate_sources cs WHERE cs.name = applications.source) "
            "WHERE source_id IS NULL AND source IS NOT NULL "
            "AND EXISTS (SELECT 1 FROM candidate_sources cs WHERE cs.name = applications.source)"
        ))
        print(f"[MIGRATE v2.3] Backfill source_id cho {result.rowcount} Application (khop ten source co san)")

    Base.metadata.create_all(bind=engine)
    print("[MIGRATE v2.3] create_all() hoan tat.")


if __name__ == "__main__":
    run()
