"""CHANGE 03 - Business ID: prefix + so tuan tu, khong PII, concurrency-safe.
KHONG duoc dung SELECT MAX(id)+1 - test 27 kiem chung dieu nay bang concurrency
that (ThreadPoolExecutor + session rieng cho tung thread).
"""

import re
from concurrent.futures import ThreadPoolExecutor

from app.core.database import SessionLocal
from app.core.id_generator import generate_business_id


def test_candidate_id_format_and_sequential():
    db = SessionLocal()
    try:
        id1 = generate_business_id(db, "candidate")
        db.commit()
        id2 = generate_business_id(db, "candidate")
        db.commit()
    finally:
        db.close()

    assert re.fullmatch(r"UV\d{4}", id1)
    assert re.fullmatch(r"UV\d{4}", id2)
    assert int(id2[2:]) == int(id1[2:]) + 1


def test_job_and_offer_prefix():
    db = SessionLocal()
    try:
        job_id = generate_business_id(db, "job")
        offer_id = generate_business_id(db, "offer")
        db.commit()
    finally:
        db.close()
    assert job_id.startswith("JOB")
    assert offer_id.startswith("OFF")


def test_business_id_contains_no_pii():
    db = SessionLocal()
    try:
        candidate_id = generate_business_id(db, "candidate")
        db.commit()
    finally:
        db.close()
    # Chi la PREFIX + so, khong the chua ten/email/sdt/ngay sinh
    assert re.fullmatch(r"[A-Z]{2,3}\d{4,}", candidate_id)


def test_concurrent_generation_never_duplicates():
    """TUYET DOI khong duoc trung Business ID khi nhieu request chay dong thoi.
    Day la ly do KHONG duoc dung SELECT MAX(id)+1.
    """

    def _generate_one(_):
        db = SessionLocal()
        try:
            business_id = generate_business_id(db, "candidate")
            db.commit()
            return business_id
        finally:
            db.close()

    n = 30
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(_generate_one, range(n)))

    assert len(results) == n
    assert len(set(results)) == n, f"Phat hien Business ID trung lap: {results}"
