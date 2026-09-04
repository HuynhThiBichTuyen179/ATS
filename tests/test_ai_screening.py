"""AI Screening - BO HOAN TOAN che do STUB theo yeu cau nguoi dung (chi phan
tich bang AI Provider that qua AI_API_KEY, khong con fallback ve du lieu gia).
AI_API_KEY luon rong trong test env (conftest.py) nen phan lon test monkeypatch
truc tiep app.services.ai_service._call_ai_provider/_is_ai_configured de mo
phong 1 lan goi AI that thanh cong hoac that bai, thay vi phu thuoc network that."""

from tests.conftest import auth_headers, register_and_login_candidate


def _apply_with_resume(client, seed, email, resume_text="5 nam kinh nghiem Python FastAPI MySQL Docker"):
    cand_headers = register_and_login_candidate(client, email)
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV AI",
            "candidate_email": email, "candidate_phone": "0900000400", "ai_consent": True,
            "resume_text": resume_text, "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    return resp.json()["business_id"]


_FAKE_AI_RESULT = {
    "match_score": 82,
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Docker"],
    "strengths": ["Kinh nghiem backend vung"],
    "weaknesses": ["Chua co chung chi lien quan"],
    "experience_summary": "5 nam kinh nghiem Python/FastAPI.",
    "recommendation": "De xuat phong van.",
}


def test_ai_analyze_without_api_key_returns_clear_error(client, seed):
    """AI_API_KEY rong trong test env (conftest.py) -> phai bao loi 400 RO
    RANG (khong con am tham chay STUB tra 200 nhu truoc)."""
    app_id = _apply_with_resume(client, seed, "uv-ai-noconfig@example.com")
    hr_headers = auth_headers(client, seed["hr"]["email"])

    resp = client.post(f"/ai/analyze/{app_id}", headers=hr_headers)
    assert resp.status_code == 400, resp.text
    assert "AI_API_KEY" in resp.json()["detail"]

    # Khong tao AIAnalysis nao ca khi that bai o buoc chua cau hinh.
    history = client.get(f"/ai/analysis/{app_id}", headers=hr_headers)
    assert history.json() == []


def test_ai_analyze_success_creates_analysis_and_advances_status(client, seed, monkeypatch):
    """Mo phong 1 lan goi AI Provider THAT thanh cong (AI_API_KEY test env
    rong nen phai monkeypatch ca _is_ai_configured lan _call_ai_provider) -
    xac nhan toan bo pipeline: tao ai_analyses tu ket qua that (khong phai
    stub), cap nhat match_score, chuyen trang thai, is_latest."""
    from app.services import ai_service

    monkeypatch.setattr(ai_service, "_is_ai_configured", lambda: True)
    monkeypatch.setattr(ai_service, "_call_ai_provider", lambda prompt: dict(_FAKE_AI_RESULT))

    app_id = _apply_with_resume(client, seed, "uv-ai-success@example.com")
    hr_headers = auth_headers(client, seed["hr"]["email"])

    resp = client.post(f"/ai/analyze/{app_id}", headers=hr_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["business_id"].startswith("AI")
    assert body["provider"] == "gemini"
    assert body["match_score"] == 82
    assert body["is_latest"] is True
    assert "stub" not in body["provider"].lower()
    assert "STUB" not in body["recommendation"]

    app_detail = client.get(f"/applications/{app_id}", headers=hr_headers)
    assert app_detail.json()["status"] == "SCREENING"
    assert app_detail.json()["match_score"] == 82


def test_ai_provider_fails_after_retries_returns_specific_error(client, seed, monkeypatch, db):
    """AI_API_KEY CO cau hinh nhung provider luon that bai (VD het quota) ->
    phai thu du 3 lan (co delay, bo qua trong test) roi tra loi 502 voi thong
    bao CU THE (khong con fallback ve du lieu gia nhu truoc). Gia lap dung
    tinh huong 429 da xac nhan qua test that voi Gemini."""
    from app.services import ai_service

    monkeypatch.setattr(ai_service, "_is_ai_configured", lambda: True)
    monkeypatch.setattr(ai_service.time, "sleep", lambda *_: None)

    call_count = {"n": 0}

    def _always_429(prompt):
        call_count["n"] += 1
        ai_service._last_provider_error = 'HTTP 429: {"error": {"message": "Quota exceeded"}}'
        return None

    monkeypatch.setattr(ai_service, "_call_ai_provider", _always_429)

    app_id = _apply_with_resume(client, seed, "uv-ai-quota@example.com")
    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(f"/ai/analyze/{app_id}", headers=hr_headers)

    assert call_count["n"] == 3, "phai thu du 3 lan truoc khi bao loi"
    assert resp.status_code == 502, resp.text
    assert "quota" in resp.json()["detail"].lower() or "429" in resp.json()["detail"]

    # Khong tao AIAnalysis nao khi that bai - khac han voi hanh vi STUB cu.
    history = client.get(f"/ai/analysis/{app_id}", headers=hr_headers)
    assert history.json() == []

    from app.models.audit_log import AuditLog
    log = (
        db.query(AuditLog)
        .filter(AuditLog.action == "AI_SCREENING_FAILED", AuditLog.entity_business_id == app_id)
        .first()
    )
    assert log is not None, "phai ghi audit log rieng cho truong hop provider that bai"


def test_classify_ai_error_maps_known_status_codes():
    """Unit test thuan cho _classify_ai_error - khong can DB/HTTP, chi kiem
    tra dung nhan dien 429 (het quota) khac voi 401/403 (sai key) khac voi
    503 (qua tai) - 3 nguyen nhan can loi khac han nhau cho nguoi dung."""
    from app.services.ai_service import _classify_ai_error

    assert "quota" in _classify_ai_error("HTTP 429: quota exceeded").lower()
    assert "api key" in _classify_ai_error("HTTP 401: invalid key").lower()
    assert "api key" in _classify_ai_error("HTTP 403: forbidden").lower()
    assert "quá tải" in _classify_ai_error("HTTP 503: overloaded").lower()
    assert _classify_ai_error(None) != ""
    assert "timeout" in _classify_ai_error("Timeout: request timed out").lower() or "chờ" in _classify_ai_error("Timeout: request timed out").lower()


def test_ai_analyze_without_resume_returns_202(client, seed):
    cand_headers = register_and_login_candidate(client, "uv-ai2@example.com")
    resp = client.post(
        "/applications",
        json={
            "job_business_id": seed["job_business_id"], "candidate_full_name": "UV NoCV",
            "candidate_email": "uv-ai2@example.com", "candidate_phone": "0900000401", "ai_consent": True,
            "source_business_id": seed["source_business_id"],
        },
        headers=cand_headers,
    )
    app_id = resp.json()["business_id"]

    hr_headers = auth_headers(client, seed["hr"]["email"])
    resp = client.post(f"/ai/analyze/{app_id}", headers=hr_headers)
    assert resp.status_code == 202
    assert resp.json()["needs_manual_review"] is True

    detail = client.get(f"/applications/{app_id}", headers=hr_headers)
    assert detail.json()["needs_manual_review"] is True


def test_rerun_ai_keeps_history_with_is_latest_flag(client, seed, monkeypatch):
    from app.services import ai_service

    monkeypatch.setattr(ai_service, "_is_ai_configured", lambda: True)
    monkeypatch.setattr(ai_service, "_call_ai_provider", lambda prompt: dict(_FAKE_AI_RESULT))

    app_id = _apply_with_resume(client, seed, "uv-ai3@example.com")
    hr_headers = auth_headers(client, seed["hr"]["email"])

    client.post(f"/ai/analyze/{app_id}", headers=hr_headers)
    client.post(f"/ai/analyze/{app_id}", headers=hr_headers)

    history = client.get(f"/ai/analysis/{app_id}", headers=hr_headers)
    assert history.status_code == 200
    results = history.json()
    assert len(results) == 2
    latest_flags = [r["is_latest"] for r in results]
    assert latest_flags.count(True) == 1


def test_candidate_cannot_trigger_ai_analyze(client, seed):
    app_id = _apply_with_resume(client, seed, "uv-ai4@example.com")
    cand_headers = auth_headers(client, "uv-ai4@example.com")
    resp = client.post(f"/ai/analyze/{app_id}", headers=cand_headers)
    assert resp.status_code == 403
