"""BUG FIX: MySQL DATETIME (va SQLite tuong tu) khong luu timezone - moi cot
DateTime trong app deu ghi qua _utcnow() (datetime.now(timezone.utc), gio UTC
that) nhung khi doc lai tu DB, SQLAlchemy tra ve datetime NAIVE (tzinfo=None),
du gia tri thuc chat van la UTC. Khi serialize truc tiep bang .isoformat(),
chuoi ket qua KHONG co hau to timezone (VD "2026-08-23T13:00:23" thay vi
"2026-08-23T13:00:23+00:00") - phia frontend, `new Date(...)` doc chuoi
khong co timezone theo dung chuan ECMA-262 se hieu la GIO DIA PHUONG (local),
khong phai UTC, dan den lech dung bang chenh lech UTC that (VD Viet Nam
UTC+7 -> hien thi som hon gio may tinh that 7 tieng).

Dung to_iso_utc() thay vi goi truc tiep .isoformat() cho MOI DateTime field
tra ve qua API, de dam bao chuoi luon co hau to "+00:00" - frontend/
Intl.DateTimeString tu dong quy doi dung ve gio dia phuong cua may nguoi dung.
"""

from datetime import datetime, timezone


def to_iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
