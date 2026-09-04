"""Upload CV that (PDF/DOCX) - phan hoi cau hoi 'cho phep ung vien upload file
CV PDF' cua nguoi dung."""

import io

from docx import Document

from tests.conftest import auth_headers, register_and_login_candidate


def _apply(client, headers, job_business_id, email, source_business_id):
    return client.post(
        "/applications",
        json={
            "job_business_id": job_business_id,
            "candidate_full_name": "UV Upload",
            "candidate_email": email,
            "candidate_phone": "0900000200",
            "ai_consent": True,
            "source_business_id": source_business_id,
        },
        headers=headers,
    )


def _make_docx_bytes(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_upload_docx_extracts_real_text(client, seed):
    headers = register_and_login_candidate(client, "uv-upload1@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload1@example.com", seed["source_business_id"]).json()["business_id"]

    docx_bytes = _make_docx_bytes("Nguyen Van A - 4 nam kinh nghiem Backend Python.")
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["business_id"].startswith("CV")
    assert "4 nam kinh nghiem" in resp.json()["extracted_text"]

    detail = client.get(f"/applications/{app_id}", headers=headers)
    assert detail.json()["has_resume"] is True
    assert detail.json()["resume_file_name"] == "cv.docx"


def test_upload_accepts_pdf_with_bom_or_leading_whitespace(client, seed):
    """v2.3 Section 1 (PDF Upload Root Cause): PDF that xuat ra tu Word 'Save
    as PDF', trinh duyet 'In ra PDF', hoac cac cong cu export CV thuong chen
    BOM UTF-8 (\\xef\\xbb\\xbf) hoac dong trong/whitespace TRUOC header "%PDF"
    - van la file PDF hop le 100% nhung truoc day bi tu choi vi
    _validate_magic_bytes() chi kiem tra dung 4 byte dau tien. Fix: quet
    "%PDF" trong 1024 byte dau (dung ISO 32000-1 Section 7.5.2)."""
    headers = register_and_login_candidate(client, "uv-upload-bom@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload-bom@example.com", seed["source_business_id"]).json()["business_id"]

    bom_pdf = b"\xef\xbb\xbf%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv_bom.pdf", bom_pdf, "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["business_id"].startswith("CV")


def test_upload_still_rejects_pdf_header_too_far_from_start(client, seed):
    """Bo di kem voi fix o tren: PDF header nam QUA XA dau file (> 1024 byte,
    vuot muc dung sai theo spec) van phai bi tu choi - tranh fix qua long leo
    chap nhan ca file gia mao chen '%PDF' o dau bat ky."""
    headers = register_and_login_candidate(client, "uv-upload-farpdf@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload-farpdf@example.com", seed["source_business_id"]).json()["business_id"]

    padding = b"\x00" * 2000
    fake_pdf = padding + b"%PDF-1.4\n%%EOF"
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv_far.pdf", fake_pdf, "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "FILE_CONTENT_DOES_NOT_MATCH_EXTENSION"


def test_upload_rejects_wrong_extension(client, seed):
    headers = register_and_login_candidate(client, "uv-upload2@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload2@example.com", seed["source_business_id"]).json()["business_id"]

    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv.txt", b"plain text resume", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "ONLY_PDF_OR_DOCX_ALLOWED"


def test_upload_rejects_content_not_matching_extension(client, seed):
    headers = register_and_login_candidate(client, "uv-upload3@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload3@example.com", seed["source_business_id"]).json()["business_id"]

    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("fake.pdf", b"this is not really a pdf file", "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "FILE_CONTENT_DOES_NOT_MATCH_EXTENSION"


def test_upload_pdf_with_no_extractable_text_flags_manual_review(client, seed):
    headers = register_and_login_candidate(client, "uv-upload4@example.com")
    app_id = _apply(client, headers, seed["job_business_id"], "uv-upload4@example.com", seed["source_business_id"]).json()["business_id"]

    # PDF hop le ve magic bytes nhung khong co noi dung text that su (mo phong
    # CV dang anh scan / PDF hong) - upload van thanh cong, chi flag can xem thu cong.
    minimal_pdf = b"%PDF-1.4\n%%EOF"
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("scan.pdf", minimal_pdf, "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    detail = client.get(f"/applications/{app_id}", headers=headers)
    assert detail.json()["needs_manual_review"] is True


def test_only_owning_candidate_or_assigned_hr_can_upload(client, seed):
    """v2.2 Section 1/5: HR duoc gan (assigned_hr_id) gio duoc phep upload CV
    thay ung vien (phuc vu form 'Them ung vien'); Candidate khac va HR KHONG
    duoc gan van bi chan 403 nhu truoc."""
    headers1 = register_and_login_candidate(client, "uv-upload5@example.com")
    app_id = _apply(client, headers1, seed["job_business_id"], "uv-upload5@example.com", seed["source_business_id"]).json()["business_id"]

    headers2 = register_and_login_candidate(client, "uv-upload6@example.com")
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv.docx", _make_docx_bytes("x"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers2,
    )
    assert resp.status_code == 403

    # HR khong duoc gan cho Job/Application nay -> van bi chan.
    hrm_headers = auth_headers(client, seed["hrm_a"]["email"])
    client.post(
        "/users",
        json={"full_name": "HR Khong Duoc Gan", "email": "hr.unassigned@example.com", "password": "Password@123", "role": "HR"},
        headers=hrm_headers,
    )
    unassigned_hr_headers = auth_headers(client, "hr.unassigned@example.com")
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv.docx", _make_docx_bytes("x"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=unassigned_hr_headers,
    )
    assert resp.status_code == 403, resp.text

    # HR duoc gan (seed["hr"] la assigned_hr_id cua Job trong conftest) -> duoc phep.
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(
        f"/applications/{app_id}/resume",
        files={"file": ("cv.docx", _make_docx_bytes("x"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=hr_headers,
    )
    assert resp.status_code == 200, resp.text
