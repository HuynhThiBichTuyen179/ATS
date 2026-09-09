# Migration thu cong so 2.4 cho ATS (tiep noi migrate_v2_2.py/migrate_v2_3.py -
# khong co Alembic).
#
# migrate_v2_2.py them cot `applications.department_id` va migrate_v2_3.py
# them cot `applications.source_id` bang `ALTER TABLE ... ADD COLUMN` thuan -
# KHONG kem `ADD CONSTRAINT ... FOREIGN KEY`. Model (app/models/application.py)
# khai bao ca 2 cot nay la ForeignKey() tu dau, nhung
# `Base.metadata.create_all()` CHI tao constraint cho bang/cot con thieu luc
# khoi dong lan dau, KHONG tu dong ALTER them constraint cho cot da ton tai
# tren bang da co du lieu - nen 2 khoa ngoai nay chua bao gio thuc su duoc
# tao tren MySQL dev/production dang chay, du code Python van "tin" la co.
# Script nay bo sung 2 constraint FK con thieu do.
#
# An toan: chi ADD CONSTRAINT, khong DROP/khong mat du lieu. Da kiem tra truoc
# khi viet script nay: 0 ban ghi `applications.source_id`/`department_id` mo
# coi (khong khop ban ghi cha) tren du lieu dev hien tai, nen ADD CONSTRAINT
# chac chan khong bi MySQL tu choi.
#
# Chay: python -m scripts.migrate_v2_4
# Idempotent: kiem tra constraint da ton tai truoc khi ALTER, chay lai nhieu lan an toan.

from sqlalchemy import inspect, text

from app.core.database import engine


def _has_fk(insp, table: str, column: str) -> bool:
    for fk in insp.get_foreign_keys(table):
        if column in fk.get("constrained_columns", []):
            return True
    return False


def _add_fk(conn, insp, table: str, column: str, ref_table: str, ref_column: str = "id") -> None:
    if _has_fk(insp, table, column):
        print(f"[MIGRATE v2.4] {table}.{column} da co FK constraint, bo qua")
        return
    constraint_name = f"fk_{table}_{column}"
    conn.execute(text(
        f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} "
        f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
    ))
    print(f"[MIGRATE v2.4] Da them FK {constraint_name}: {table}.{column} -> {ref_table}.{ref_column}")


def run():
    if engine.dialect.name != "mysql":
        print("[MIGRATE v2.4] Bo qua - chi can thiet cho MySQL "
              "(SQLite luon tao du FK ngay tu create_all() dau tien vi khong co du lieu cu).")
        return

    insp = inspect(engine)
    with engine.begin() as conn:
        _add_fk(conn, insp, "applications", "department_id", "departments")
        _add_fk(conn, insp, "applications", "source_id", "candidate_sources")

    print("[MIGRATE v2.4] Hoan tat.")


if __name__ == "__main__":
    run()
