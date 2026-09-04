"""AI Screening Service - v2 Phan 7/8 (retry, cost cap, is_latest history).

CAP NHAT theo yeu cau nguoi dung: BO HOAN TOAN che do STUB (phan tich gia lap).
Chi phan tich bang AI Provider that (Gemini/Claude qua AI_API_KEY that trong
.env) - neu chua cau hinh HOAC goi that bai (het quota, sai key, qua tai...)
thi bao loi CU THE cho nguoi dung (vi du "Het quota API", "API Key khong hop
le") thay vi am tham tra ket qua gia. Xem AIAnalysisError/_classify_ai_error.

Them nha cung cap moi: viet 1 ham _call_<provider>(prompt) -> dict | None theo
dung mau _call_gemini/_call_claude, roi dang ky vao PROVIDER_CALLERS va
DEFAULT_MODELS ben duoi.
"""

import json
import re
import time

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.id_generator import generate_business_id
from app.models.ai_analysis import AIAnalysis
from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.services import audit_service

REQUEST_TIMEOUT_SECONDS = 30


class AIAnalysisError(Exception):
    """Loi phan tich AI can bao CU THE cho nguoi dung, khong duoc am tham
    fallback ve du lieu gia. `status_code` de router quyet dinh HTTP status
    tra ve (400 = loi cau hinh nguoi dung tu sua duoc; 502 = loi phia
    provider, thu lai sau)."""

    def __init__(self, detail: str, status_code: int = 502):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

# Model mac dinh cho tung provider khi AI_MODEL de trong trong .env.
DEFAULT_MODELS = {
    # "*-latest" - alias luon tro toi phien ban on dinh moi nhat cua Google,
    # tranh bi lac hau/ngung ho tro nhu cac model ghi cung version cu the
    # (vd gemini-1.5-flash, gemini-2.5-flash da bi rut khoi tai khoan moi).
    "gemini": "gemini-flash-lite-latest",
    "claude": "claude-haiku-4-5-20251001",
}


def _is_ai_configured() -> bool:
    return bool(settings.ai_api_key)


def _active_model() -> str:
    return settings.ai_model or DEFAULT_MODELS.get(settings.ai_provider.lower(), settings.ai_provider)


def _build_prompt(job_title: str, job_description: str, job_requirements: str, cv_text: str) -> dict:
    # v2 Phan 8.3 - Structured Prompt, va 8.6 - CHI gui cv_text + thong tin
    # job, KHONG gui phone/address/date_of_birth/salary/email day du.
    return {
        "system_instruction": (
            "Ban la Chuyen gia Tuyen dung Senior AI. Nhiem vu cua ban la phan tich CV cua ung vien "
            "va so sanh voi Yeu cau tuyen dung (JD). Hay tra ve ket qua dinh dang JSON chinh xac theo Schema quy dinh."
        ),
        "input_data": {
            "job_title": job_title,
            "job_description": job_description,
            "job_requirements": job_requirements,
            "cv_text": cv_text,
        },
        "output_format_instructions": (
            "Tra ve duy nhat 1 doi tuong JSON co cac truong: match_score (int 0-100), "
            "matched_skills (array string), missing_skills (array string), strengths (array string), "
            "weaknesses (array string), experience_summary (string), recommendation (string)."
        ),
    }


def _prompt_to_text(prompt: dict) -> str:
    """Ghep prompt co cau truc thanh 1 doan text don - dung chung cho moi
    provider vi ca Gemini lan Claude deu nhan noi dung dang text/message.
    """
    return (
        f"{prompt['system_instruction']}\n\n"
        f"Job Title: {prompt['input_data']['job_title']}\n"
        f"Job Description: {prompt['input_data']['job_description']}\n"
        f"Job Requirements: {prompt['input_data']['job_requirements']}\n"
        f"CV:\n{prompt['input_data']['cv_text']}\n\n"
        f"{prompt['output_format_instructions']}"
    )


def _extract_json(text: str) -> dict | None:
    """Cac model AI thuong boc JSON trong ```json ... ``` hoac kem giai thich
    truoc/sau - boc phan JSON dau tien ra truoc khi parse.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# Luu lai ly do that bai gan nhat (HTTP status + trich doan body) de ghi vao
# audit log - truoc day khi that bai chi biet "khong phan hoi duoc", phai tu
# curl thu công moi biet duoc that ra la 429 QUOTA_EXCEEDED (het han ngach mien
# phi 20 request/ngay/model) chu khong phai 503 qua tai nhat thoi nhu doan dau
# tien phat hien - 2 nguyen nhan can xu ly hoan toan khac nhau (doi qua ngay
# hom sau vs. cho vai giay roi thu lai), nen can phan biet duoc qua log.
_last_provider_error: str | None = None


def _call_gemini(prompt: dict) -> dict | None:
    """Goi that Google Gemini API. Tra ve None neu that bai (de caller retry/fallback)."""
    global _last_provider_error
    try:
        import httpx

        model = _active_model()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.ai_api_key}"
        )
        payload = {"contents": [{"parts": [{"text": _prompt_to_text(prompt)}]}]}
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
        if resp.status_code != 200:
            _last_provider_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            return None
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        _last_provider_error = None
        return _extract_json(text)
    except Exception as e:
        _last_provider_error = f"{type(e).__name__}: {e}"
        return None


def _call_claude(prompt: dict) -> dict | None:
    """Goi that Anthropic Claude API (Messages API). Tra ve None neu that bai
    (de caller retry/fallback). Goi truc tiep qua httpx (khong dung SDK
    `anthropic`) - dung nguyen tac giam phu thuoc da ap dung cho Gemini.
    """
    global _last_provider_error
    try:
        import httpx

        headers = {
            "x-api-key": settings.ai_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": _active_model(),
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": _prompt_to_text(prompt)}],
        }
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        if resp.status_code != 200:
            _last_provider_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            return None
        data = resp.json()
        text = data["content"][0]["text"]
        _last_provider_error = None
        return _extract_json(text)
    except Exception as e:
        _last_provider_error = f"{type(e).__name__}: {e}"
        return None


# Dang ky nha cung cap tai day - key phai khop settings.ai_provider (khong phan
# biet hoa/thuong, xem _active_model/run_screening).
PROVIDER_CALLERS = {
    "gemini": _call_gemini,
    "claude": _call_claude,
}


def _call_ai_provider(prompt: dict) -> dict | None:
    global _last_provider_error
    caller = PROVIDER_CALLERS.get(settings.ai_provider.lower())
    if caller is None:
        _last_provider_error = f"AI_PROVIDER='{settings.ai_provider}' khong duoc ho tro (hop le: {sorted(PROVIDER_CALLERS)})"
        return None
    return caller(prompt)


def _classify_ai_error(raw: str | None) -> str:
    """Dich loi ky thuat (HTTP status/exception) tu _last_provider_error thanh
    thong bao tieng Viet CU THE cho nguoi dung - theo yeu cau khong duoc bao
    chung chung "khong phan hoi duoc" nua. Da xac nhan qua test that voi
    Gemini: 429 = het quota mien phi (20 request/ngay/model), 503 = qua tai
    tam thoi - 2 nguyen nhan nay can loi khac han nhau."""
    if not raw:
        return "Gọi AI Provider thất bại không rõ nguyên nhân. Vui lòng thử lại sau."

    match = re.match(r"HTTP (\d+)", raw)
    if match:
        code = int(match.group(1))
        if code == 429:
            return "Đã hết quota/giới hạn số lượt gọi AI Provider (429). Vui lòng thử lại sau hoặc nâng cấp gói tại nhà cung cấp AI."
        if code in (401, 403):
            return "API Key AI không hợp lệ, đã hết hạn, hoặc không có quyền truy cập. Vui lòng kiểm tra lại AI_API_KEY trong .env."
        if code == 404:
            return "Model AI không tồn tại hoặc đã ngừng hỗ trợ. Vui lòng kiểm tra lại AI_MODEL trong .env."
        if code in (500, 502, 503, 504):
            return "Dịch vụ AI Provider đang quá tải hoặc gặp sự cố tạm thời. Vui lòng thử lại sau ít phút."
        return f"AI Provider trả về lỗi HTTP {code}. Chi tiết: {raw[:200]}"

    if "Timeout" in raw:
        return "Hết thời gian chờ phản hồi từ AI Provider (timeout). Vui lòng thử lại."
    if "Connect" in raw:
        return "Không kết nối được tới AI Provider (lỗi mạng). Vui lòng kiểm tra kết nối Internet và thử lại."
    return f"Gọi AI Provider thất bại: {raw[:200]}"


def run_screening(db: Session, application: Application, actor: User) -> AIAnalysis:
    """v2 Phan 8.5: goi AI, retry toi da 2 lan (3 lan goi tong cong) co delay
    ngan giua cac lan de vuot qua loi qua tai tam thoi (VD Gemini 503 "high
    demand" - da xac nhan qua test that: 1 lan 503 nhung lan ke tiep 200 chi
    sau vai giay).

    KHONG con fallback ve STUB (theo yeu cau nguoi dung: chi phan tich bang
    AI Provider that). Neu chua cau hinh AI_API_KEY hoac goi that bai sau 3
    lan thu, raise AIAnalysisError voi thong bao CU THE (het quota/sai key/
    qua tai...) thay vi tra ve du lieu gia - router se convert thanh HTTP
    error tuong ung. Truong hop khong co CV text van giu nguyen hanh vi cu
    (needs_manual_review=True, tra None) vi day khong phai loi AI Provider.
    """
    job = application.job
    resume = application.resume
    cv_text = (resume.extracted_text if resume else "") or ""

    if not cv_text.strip():
        application.needs_manual_review = 1
        db.commit()
        audit_service.log(
            db, actor=actor, action="AI_SCREENING_SKIPPED_NO_CV_TEXT",
            entity_type="application", entity_business_id=application.business_id,
            reason="Khong co extracted_text (chua upload/dan CV, hoac PDF khong trich xuat duoc text)",
        )
        db.commit()
        return None

    if not _is_ai_configured():
        raise AIAnalysisError(
            "Chưa cấu hình AI_API_KEY trong .env — vui lòng liên hệ quản trị viên để bật tính năng AI Screening.",
            status_code=400,
        )

    provider = settings.ai_provider.lower()
    prompt = _build_prompt(job.title, job.description, job.requirements, cv_text)
    result = None
    for attempt in range(3):
        result = _call_ai_provider(prompt)
        if result is not None:
            break
        if attempt < 2:
            time.sleep(2)

    if result is None:
        error_detail = _classify_ai_error(_last_provider_error)
        audit_service.log(
            db, actor=actor, action="AI_SCREENING_FAILED",
            entity_type="application", entity_business_id=application.business_id,
            reason=f"{provider} that bai sau 3 lan thu: {_last_provider_error or 'khong ro nguyen nhan'}",
        )
        db.commit()
        raise AIAnalysisError(error_detail, status_code=502)

    # v2 Phan 5.7: is_latest - danh dau cac ban ghi cu la khong con moi nhat
    # truoc khi insert ban ghi moi, giu lai toan bo lich su (khong xoa).
    db.query(AIAnalysis).filter(AIAnalysis.application_id == application.id).update({"is_latest": False})

    analysis = AIAnalysis(
        business_id=generate_business_id(db, "ai_analysis"),
        application_id=application.id,
        is_latest=True,
        provider=provider,
        model=_active_model(),
        match_score=int(result.get("match_score", 0)),
        matched_skills=json.dumps(result.get("matched_skills", []), ensure_ascii=False),
        missing_skills=json.dumps(result.get("missing_skills", []), ensure_ascii=False),
        strengths=json.dumps(result.get("strengths", []), ensure_ascii=False),
        weaknesses=json.dumps(result.get("weaknesses", []), ensure_ascii=False),
        experience_summary=result.get("experience_summary", ""),
        recommendation=result.get("recommendation", ""),
        analysis_result=json.dumps(result, ensure_ascii=False),
    )
    db.add(analysis)
    db.flush()

    # v2 Phan 3.2: AI_SCREENING -> SCREENING khi AI hoan tat (chi chuyen neu
    # dang o NEW/AI_SCREENING - khong dam len cac trang thai HR da xu ly tay).
    if application.status in (ApplicationStatus.NEW, ApplicationStatus.AI_SCREENING):
        application.status = ApplicationStatus.SCREENING
    application.needs_manual_review = 0
    db.flush()

    audit_service.log(
        db, actor=actor, action="AI_SCREENING_COMPLETED",
        entity_type="application", entity_business_id=application.business_id,
        after={"match_score": analysis.match_score, "provider": provider},
    )
    db.commit()
    db.refresh(analysis)
    return analysis
