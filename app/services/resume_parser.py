# Trich xuat text tu file CV that (PDF/DOCX). Khong co antivirus scan that
# (ClamAV can dung service ngoai, khong the cai dat trong moi truong build nay)
# - chi validate mimetype/extension/magic-bytes + gioi han dung luong nhu mot
# lop bao ve toi thieu, va ghi ro day la GAP con lai trong backlog.

import os
import uuid

from fastapi import HTTPException, UploadFile, status

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads", "resumes")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)


def _validate_magic_bytes(content: bytes, ext: str) -> bool:
    if ext == ".pdf":
        # PDF that tu nhieu cong cu (Word "Save as PDF", trinh duyet "In ra
        # PDF", scanner, cac dich vu export CV...) co the chen vai byte thua
        # (BOM UTF-8 \xef\xbb\xbf, dong trong, whitespace) TRUOC header "%PDF"
        # - van la PDF hop le 100%, mo binh thuong trong moi PDF reader that.
        # Spec PDF (ISO 32000-1, 7.5.2) khuyen nghi doc quet header trong 1024
        # byte dau thay vi bat buoc dung byte 0 - chi check content[:4] ==
        # b"%PDF" se tu choi nham nhung PDF hop le co leading bytes nay. Quet
        # trong cua so 1024 byte dau, khop hanh vi PDF reader that (bao gom
        # pypdf dung de trich xuat text ngay ben duoi).
        return b"%PDF" in content[:1024]
    if ext == ".docx":
        # DOCX la file ZIP (Office Open XML) - signature ZIP la "PK"
        return content[:2] == b"PK"
    return False


def extract_text_from_pdf(content: bytes) -> str:
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def extract_text_from_docx(content: bytes) -> str:
    import io

    from docx import Document

    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs).strip()


async def save_and_extract(file: UploadFile, application_business_id: str) -> tuple[str, str, str, str]:
    # Validate, luu file that vao uploads/resumes/, tra ve
    # (file_name, file_path, file_type, extracted_text).
    original_name = file.filename or "resume"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ONLY_PDF_OR_DOCX_ALLOWED")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "EMPTY_FILE")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "FILE_TOO_LARGE_MAX_10MB")
    if not _validate_magic_bytes(content, ext):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "FILE_CONTENT_DOES_NOT_MATCH_EXTENSION")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # {application_id}_{uuid4}.{ext} - tranh trung/path traversal
    stored_name = f"{application_business_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        if ext == ".pdf":
            extracted_text = extract_text_from_pdf(content)
        else:
            extracted_text = extract_text_from_docx(content)
    except Exception:
        # Parse that bai (vd PDF dang anh scan, khong co text layer) - khong
        # chan upload, chi de extracted_text rong; AI Screening service (khi
        # xay) se tu dua vao nhanh needs_manual_review giong nhu AI fail.
        extracted_text = ""

    file_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return original_name, file_path, file_type, extracted_text
