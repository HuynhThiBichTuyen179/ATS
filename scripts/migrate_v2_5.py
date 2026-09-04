"""Migration thu cong cho ATS v2.5 (tiep noi migrate_v2_2/v2_3/v2_4 - khong co Alembic).

BUG FIX: 4 cot cua bang `candidates` (address, current_salary, expected_salary,
date_of_birth) chua bao gio duoc bat ky schema/router nao doc hoac ghi - khong
xuat hien trong CandidateCreateRequest/CandidateUpdateRequest/CandidateOut,
khong co endpoint nao gan gia tri. Da kiem tra truc tiep tren MySQL dev truoc
khi viet script nay: ca 4 bang deu 100% NULL o toan bo ban ghi hien co (4/4),
nen xoa an toan, khong mat du lieu that. "Luong mong muon" hien thi that tren
giao dien lay tu `applications.desired_salary` (bang khac), khong phai
`candidates.expected_salary` - de ten gan giong nhau gay nham lan.

An toan: chi DROP COLUMN cac cot da xac nhan rong, khong dong toi du lieu
khac. Chay: python -m scripts.migrate_v2_5
Idempotent: kiem tra cot con ton tai truoc khi DROP, chay lai nhieu lan an toan.
"""

from sqlalchemy import inspect, text

from app.core.database import engine


def _drop_column_if_exists(conn, insp, table: str, column: str) -> None:
    existing_cols = {c["name"] for c in insp.get_columns(table)}
    if column not in existing_cols:
        print(f"[MIGRATE v2.5] {table}.{column} da khong con, bo qua")
        return
    conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))
    print(f"[MIGRATE v2.5] Da xoa cot {table}.{column}")


def run():
    if engine.dialect.name != "mysql":
        print("[MIGRATE v2.5] Bo qua - chi can thiet cho MySQL "
              "(SQLite trong test luon tao bang moi tu model hien tai, khong co cot cu).")
        return

    insp = inspect(engine)
    with engine.begin() as conn:
        for column in ("address", "current_salary", "expected_salary", "date_of_birth"):
            _drop_column_if_exists(conn, insp, "candidates", column)

    print("[MIGRATE v2.5] Hoan tat.")


if __name__ == "__main__":
    run()
