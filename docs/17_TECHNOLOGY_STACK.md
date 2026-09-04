# 17 — TECHNOLOGY STACK — ATS v2.1

**Nguồn**: `requirements.txt` (đọc verbatim, không suy đoán version), `app/static/index.html` (thẻ `<script src>`/`<link href>`), cấu trúc thư mục gốc `ats-v2/`.

## 1. Backend — Python (`requirements.txt`, 16 dependency trực tiếp — 15 ban đầu + `pymysql` bổ sung sau STEP 1)

| Thư viện | Version | Vai trò | Bằng chứng sử dụng trong code |
|---|---|---|---|
| `fastapi` | 0.115.0 | Web framework, routing, dependency injection, OpenAPI tự sinh | `app/main.py`, toàn bộ `app/routers/*.py` |
| `uvicorn[standard]` | 0.30.6 | ASGI server chạy ứng dụng | Lệnh khởi động `uvicorn app.main:app` (README) |
| `sqlalchemy` | 2.0.35 | ORM, định nghĩa model, Session, CheckConstraint/UniqueConstraint | `app/core/database.py`, toàn bộ `app/models/*.py` |
| `pydantic` | 2.9.2 | Validate input/output, định nghĩa DTO (schema) | `app/schemas/*.py` |
| `pydantic-settings` | 2.5.2 | Đọc cấu hình từ `.env` có type-safety | `app/core/config.py::Settings` |
| `email-validator` | 2.2.0 | Validate định dạng email trong Pydantic (`EmailStr`) | `app/schemas/auth.py`, `user.py` |
| `python-jose[cryptography]` | 3.3.0 | Tạo/giải mã JWT (thuật toán HS256) | `app/core/security.py::create_access_token/decode_access_token` |
| `passlib` | 1.7.4 | Hash/verify mật khẩu | `app/core/security.py::hash_password/verify_password` |
| `bcrypt` | 4.0.1 | Thuật toán băm cụ thể dùng bởi `passlib` | Backend của `passlib.CryptContext` |
| `python-multipart` | 0.0.9 | Parse `multipart/form-data` (upload file) | `app/routers/applications.py::upload_resume` |
| `apscheduler` | 3.10.4 | Thư viện lên lịch chạy job nền | **`[CONFIRMED — KHÔNG được sử dụng]`** — không có bất kỳ `import apscheduler`/`BackgroundScheduler` nào trong toàn bộ `app/` (grep xác nhận 0 kết quả). Đây là **bằng chứng trực tiếp, mạnh nhất** cho Gap OFFER-11 (`expire_due_offers()` có logic nhưng không bao giờ tự chạy) — thư viện đã được thêm vào dependency, cho thấy **có chủ đích lên lịch nhưng chưa hoàn thiện việc wiring**, không phải bị quên hoàn toàn |
| `pypdf` | 5.0.1 | Trích xuất text từ file PDF | `app/services/resume_parser.py::extract_text_from_pdf` |
| `python-docx` | 1.1.2 | Trích xuất text từ file DOCX | `app/services/resume_parser.py::extract_text_from_docx` (import là `docx`, gói PyPI là `python-docx`) |
| `httpx` | 0.27.2 | HTTP client — gọi AI Provider API (Gemini hoặc Claude), và dùng trong test E2E | `app/services/ai_service.py::_call_gemini/_call_claude`, `scripts/smoke_*.py` |
| `pytest` | 8.3.3 | Framework kiểm thử tự động | `tests/*.py` |
| `pymysql` | 1.1.1 | Driver kết nối MySQL cho SQLAlchemy (`mysql+pymysql://`) | `app/core/database.py` — **[BỔ SUNG sau STEP 1]**, trước đó `[MISSING]` |

**Thư viện được import nhưng KHÔNG có trong `requirements.txt`** — `[MISSING — rủi ro reproducibility]`: không có SDK chính thức nào của các nhà cung cấp AI (`google-generativeai`, `anthropic`) xuất hiện trong dependency; `ai_service.py` gọi cả Gemini lẫn Claude qua `httpx` trực tiếp tới REST endpoint (không dùng SDK riêng của từng hãng) — đây là lựa chọn thiết kế nhất quán (giảm phụ thuộc, cùng 1 pattern cho mọi provider), không phải thiếu sót, ghi chú lại để không gây nhầm lẫn khi đối chiếu.

## 2. Cơ sở dữ liệu

| Thành phần | Đã xác nhận | Ghi chú |
|---|---|---|
| SQLite | `[CONFIRMED]` | File `ats_v2.db`, dùng mặc định (`USE_MYSQL=false`) và làm fallback tự động nếu MySQL không kết nối được |
| MySQL | `[CONFIRMED — đã triển khai sau STEP 1]` | Driver `pymysql` đã bổ sung; kích hoạt qua `USE_MYSQL=true` + `MYSQL_*` (`app/core/config.py`, `app/core/database.py`); đã kiểm chứng tạo schema + chạy E2E thật. Trước STEP 1 tài liệu này ghi `[ASSUMED — chưa triển khai]` |
| Alembic (migration) | `[MISSING]` | Không có trong dependency, không có thư mục `migrations/`/`alembic/` — áp dụng cho cả 2 engine |

## 3. Frontend

| Thành phần | Nguồn | Ghi chú |
|---|---|---|
| Tailwind CSS | CDN (`cdn.tailwindcss.com`) | Không qua build step/PostCSS — dùng trực tiếp bản JIT runtime, không tối ưu cho production (khuyến cáo chính thức của Tailwind là dùng CLI/PostCSS cho production, không dùng CDN) |
| Chart.js | CDN (`cdn.jsdelivr.net/npm/chart.js`) | Vẽ biểu đồ Dashboard |
| Font Awesome 6.4.0 | CDN (`cdnjs.cloudflare.com`) | Icon |
| Google Fonts (Inter) | CDN (`fonts.googleapis.com`) | Font chữ |
| JavaScript thuần | `app/static/index.html` (inline `<script>`) | Không dùng framework (React/Vue/Angular), không có bundler (Webpack/Vite), gọi API trực tiếp bằng `fetch` |

**Rủi ro đã ghi nhận**: mọi thư viện frontend load qua CDN công cộng — nếu mất kết nối Internet hoặc CDN downtime, giao diện hỏng hoàn toàn (không có fallback nội bộ/self-host). Đây là điểm hợp lý cho giai đoạn demo/MVP nhưng cần thay đổi trước khi production thật.

## 4. Công cụ phát triển & Kiểm thử

| Công cụ | Trạng thái | Ghi chú |
|---|---|---|
| `pytest` | `[CONFIRMED]` | Thư mục `tests/` |
| 3 script E2E smoke test | `[CONFIRMED]` | `scripts/smoke_e2e.py`, `smoke_audit_fixes.py`, `smoke_new_features.py` — dùng `httpx` gọi thẳng API đang chạy |
| Linter/Formatter (ruff/black/flake8) | `[MISSING]` | Không có file cấu hình (`pyproject.toml`, `.flake8`, `ruff.toml`) ở gốc `ats-v2/` |
| Type checker (mypy) | `[MISSING]` | Không có cấu hình |
| Pre-commit hook | `[MISSING]` | Không có `.pre-commit-config.yaml` |
| `.gitignore` | `[CONFIRMED]` | Có loại trừ `.env`, `*.db`, `.venv/`, `__pycache__/`, `uploads/` — cấu hình hợp lý, giảm rủi ro lộ secret/dữ liệu khi commit (liên quan OQ-03 ở `00`: dù không xác nhận được giá trị thật trong `.env`, cơ chế loại trừ khỏi git đã đúng) |

## 5. Hạ tầng triển khai

`[MISSING]` toàn bộ — không Dockerfile, không docker-compose, không CI/CD config (`.github/workflows/`), không IaC (Terraform...). Xem chi tiết `14_SYSTEM_ARCHITECTURE.md` mục 10.

---

*Tài liệu tiếp theo: `18_GENERAL_WORKFLOW.md`.*
