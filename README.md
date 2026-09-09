# ATS - Backend Implementation

## Yêu cầu hệ thống

- **Python 3.11+** (khuyến nghị dùng đúng bản 3.11 như dự án này đã test, tránh
  lỗi tương thích thư viện trên bản quá mới/quá cũ).
- **MySQL 8.0+** đang chạy sẵn (local hoặc remote) — hệ thống **bắt buộc** dùng
  MySQL, không còn chế độ SQLite cho ứng dụng thật (xem giải thích ở dưới).
- Trình duyệt hiện đại (Chrome/Edge/Firefox) để mở giao diện web — frontend là
  vanilla JS + Tailwind CDN, không cần build/npm gì cả.

## Chạy thử (hướng dẫn chi tiết)

### Bước 1 - Vào thư mục dự án và tạo môi trường ảo Python

```bash
cd ats
python -m venv .venv
```

Kích hoạt môi trường ảo (chọn dòng phù hợp hệ điều hành):

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt / cmd.exe)
.venv\Scripts\activate.bat

# macOS / Linux (bash/zsh)
source .venv/bin/activate
```

Sau khi kích hoạt thành công, đầu dòng lệnh sẽ hiện `(.venv)`. **Lưu ý quan
trọng**: môi trường ảo trên Windows lưu đường dẫn tuyệt đối lúc tạo — nếu sau
này di chuyển/đổi tên thư mục dự án, phải xoá `.venv` rồi tạo lại (xem mục
Xử lý lỗi thường gặp bên dưới).

### Bước 2 - Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 3 - Tạo database MySQL

Đăng nhập MySQL (VD qua `mysql -u root -p` hoặc MySQL Workbench/DBeaver) và tạo
một database rỗng — tên tuỳ chọn, sẽ khai báo lại ở bước 4:

```sql
CREATE DATABASE recruitment_db CHARACTER SET utf8mb4;
```

Ứng dụng **không tự tạo database** lúc khởi động — chỉ tự tạo các BẢNG bên trong
database đã tồn tại (qua `Base.metadata.create_all`, xem `app/main.py`). Nếu
database chưa tồn tại, bước 6 (chạy server) sẽ báo lỗi kết nối và dừng lại
ngay.

### Bước 4 - Tạo file cấu hình `.env`

```bash
cp .env.example .env       # Windows CMD: copy .env.example .env
```

Mở `.env` vừa tạo, điền ít nhất 5 biến MySQL bắt buộc (khớp với database vừa
tạo ở bước 3):

```bash
USE_MYSQL=true
MYSQL_USER=root
MYSQL_PASSWORD=...              # mật khẩu MySQL của bạn, để trống nếu không có
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=recruitment_db
```

`JWT_SECRET`, `SMTP_*`, `AI_*` có thể để nguyên mặc định để chạy thử (đăng nhập/
CRUD bình thường) — chỉ cần cấu hình khi muốn bật thật email/AI Screening (xem
mục "Bật AI Screening / Email SMTP thật" bên dưới). Tất cả biến và giá trị mặc
định được liệt kê đầy đủ trong `.env.example` và `app/core/config.py`.

### Bước 5 - Tạo dữ liệu mẫu (seed)

```bash
python -m app.seed_data
```

Lệnh này tạo sẵn: 1 Department, 1 Admin, 2 HR Manager, 1 HR, 1 Job đã
`PUBLISHED` và các Email Template mẫu (bao gồm template `PASSWORD_RESET` bắt
buộc phải có để chức năng Quên mật khẩu hoạt động). Script **idempotent theo
từng email cụ thể** — chạy lại nhiều lần an toàn, không tạo trùng tài khoản đã
có, không đụng tới dữ liệu Candidate bạn đã tự đăng ký qua giao diện.

### Bước 6 - Chạy server

```bash
uvicorn app.main:app --reload --port 8000
```

Thấy trên console hiện dòng `[DATABASE] Kết nối MySQL thành công (...)` nghĩa
là đã chạy đúng. Mở trình duyệt tới `http://localhost:8000` - frontend
(`app/static/index.html`) được serve tại `/`, gọi thẳng API thật (không mock
data). Xem tài liệu API tự động (Swagger UI) tại `http://localhost:8000/docs`.

Cờ `--reload` nghĩa là server sẽ tự khởi động lại mỗi khi sửa code - tiện lợi
lúc dev, **không dùng cờ này khi deploy thật**.


## Xử lý lỗi thường gặp

**`Fatal error in launcher: Unable to create process using "...\.venv\Scripts\
python.exe" ...`** - thư mục dự án vừa bị di chuyển/đổi tên. Môi trường ảo
Windows ghi cứng đường dẫn tuyệt đối vào các file `.venv/Scripts/*.exe` và
`.venv/pyvenv.cfg` lúc tạo, nên không thể "chuyển" theo thư mục — phải xoá và
tạo lại:

```bash
rm -rf .venv                       # Windows: rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\Activate.ps1         # kích hoạt lại (xem Bước 1)
pip install -r requirements.txt    # cài lại dependencies
```

**Terminal vẫn báo lỗi dù đã tạo lại `.venv` mới** — cửa sổ terminal đang mở
vẫn còn giữ biến môi trường (`VIRTUAL_ENV`, `PATH`) trỏ tới `.venv` cũ đã xoá.
Đóng terminal và mở lại (hoặc `deactivate` rồi kích hoạt lại `.venv` mới).

**`sqlalchemy.exc.OperationalError` / không kết nối được MySQL lúc khởi
động** — kiểm tra: (1) MySQL server đã chạy chưa (`mysql -u root -p` thử đăng
nhập trước); (2) `MYSQL_USER`/`MYSQL_PASSWORD`/`MYSQL_HOST`/`MYSQL_PORT` trong
`.env` có đúng không; (3) database ở `MYSQL_DB` đã được `CREATE DATABASE`
chưa (xem Bước 3) — ứng dụng không tự tạo database.

**Đăng nhập không được / không thấy tài khoản mẫu nào** — chưa chạy
`python -m app.seed_data` (Bước 5), hoặc đang trỏ nhầm database (kiểm tra lại
`MYSQL_DB` trong `.env`).

### Bật AI Screening / Email SMTP thật (tuỳ chọn)

AI Screening **bắt buộc** phải có `AI_API_KEY` hợp lệ - không còn chế độ giả lập
(STUB đã bị bỏ hoàn toàn theo yêu cầu nghiệp vụ), nếu chưa cấu hình thì
`POST /ai/analyze/{id}` trả lời 400 kèm thông báo rõ ràng. Email cũng không còn
chế độ giả lập - luôn thử gửi thật qua SMTP, nếu chưa cấu hình `SMTP_USER`/
`SMTP_PASSWORD` (hoặc sai thông tin) thì việc gửi sẽ thất bại thật (ghi audit
log với kết quả thất bại cụ thể), không âm thầm coi là đã xử lý. Để
chạy thật, điền vào `.env`:

```bash
AI_PROVIDER=gemini        # hoặc claude
AI_API_KEY=...            # Gemini: https://aistudio.google.com/apikey
                           # Claude: https://console.anthropic.com/settings/keys
AI_MODEL=                 # để trống để dùng model mặc định của provider đã chọn
                           # (gemini-flash-lite-latest / claude-haiku-4-5-20251001),
                           # hoặc ghi tên model cụ thể (VD gemini-3.7-flash - đã test
                           # gọi thật thành công 2026-08-18)
SMTP_USER=ban@gmail.com
SMTP_PASSWORD=...         # App Password 16 ký tự, tạo tại https://myaccount.google.com/apppasswords
                           # (mật khẩu Gmail thường KHÔNG đăng nhập SMTP được nếu đã bật 2FA)
```

Không cần sửa code — service tự động chuyển sang chế độ thật khi thấy key được cấu hình.
Lưu ý: nếu bật SMTP thật, **bắt buộc** phải có ít nhất 1 `EmailTemplate` loại `PASSWORD_RESET`
đang `ACTIVE` thì chức năng Quên mật khẩu mới thực sự gửi được email (xem mục Forgot/Reset
Password bên dưới) — `python -m app.seed_data` đã tự seed sẵn mẫu này.

## Chạy test

```bash
pytest tests/ -v                        # 113/113 unit/integration test (SQLite, tự reset DB)
python scripts/smoke_e2e.py             # E2E Offer 4-eyes qua HTTP thật
python scripts/smoke_audit_fixes.py     # E2E các fix từ đợt audit code-vs-spec
python scripts/smoke_new_features.py    # E2E Dashboard/Upload CV/AI/Email/Filter
python -m scripts.migrate_v2_2          # Migration thủ công V2.2 (idempotent, không có Alembic)
python -m scripts.migrate_v2_3          # Migration thủ công V2.3 (source_id FK + index, idempotent)
python -m scripts.migrate_v2_4          # Migration thủ công V2.4 (bổ sung 2 FK constraint còn thiếu
                                         # trên MySQL - applications.department_id/source_id đã có cột
                                         # từ migrate_v2_2/v2_3 nhưng chưa từng có constraint thật,
                                         # idempotent, chỉ cần chạy trên MySQL - SQLite bỏ qua)
python -m scripts.migrate_v2_5          # Migration thủ công V2.5 (xoá 4 cột "chết" ở candidates:
                                         # address/current_salary/expected_salary/date_of_birth -
                                         # chưa từng có schema/endpoint nào đọc/ghi, idempotent,
                                         # chỉ cần chạy trên MySQL - SQLite bỏ qua)
python -m scripts.migrate_v2_6          # Migration thủ công V2.6 (xoá 5 cột "chết" ở interviews:
                                         # rating/feedback/hiring_manager_name/hiring_manager_email/
                                         # hiring_manager_feedback - chưa từng có schema/endpoint nào
                                         # đọc/ghi, idempotent, chỉ cần chạy trên MySQL - SQLite bỏ qua)
```

Cả 3 script E2E cần server đang chạy trên `:8123` và đều dùng `RUN_ID` ngẫu nhiên mỗi
lần chạy để an toàn khi chạy lại nhiều lần trên cùng 1 DB dev.

## Tài khoản seed

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin/BGĐ | admin@example.com | Admin@123 |
| HR Manager A | hrmanager.a@example.com | HrManager@123 |
| HR Manager B | hrmanager.b@example.com | HrManager@123 |
| HR | hr.a@example.com | Hr@123456 |

Candidate tự đăng ký qua `POST /auth/register`. Quên mật khẩu? Dùng "Quên mật khẩu?"
ở màn đăng nhập (xem mục Forgot/Reset Password bên dưới) - không còn hiện mật khẩu seed
trực tiếp trên giao diện đăng nhập (đã bỏ dòng hint này 2026-08-18).

## Cấu trúc

```
app/
├── main.py                # FastAPI app, lifespan (create_all cho dev), CORS, static mount
├── static/index.html      # Frontend thật (vanilla JS + Tailwind + Chart.js CDN), gọi API thật
├── core/                  # config, database, security (JWT/bcrypt), id_generator
├── models/                # 13 bảng nghiệp vụ + id_sequences (Business ID) = 14 file model
├── schemas/                # Pydantic request/response
├── deps/rbac.py            # get_current_user, get_current_user_optional, require_roles(...)
├── services/
│   ├── application_service.py  # state machine, re-apply, idempotency
│   ├── offer_service.py        # 4-eyes approval, Rule 2 auto-close
│   ├── ai_service.py           # AI Screening (chỉ Gemini/Claude thật qua AI_API_KEY, không stub)
│   ├── email_service.py        # Email Automation (SMTP thật/simulate)
│   ├── resume_parser.py        # trích xuất text từ PDF/DOCX
│   ├── resume_service.py       # lưu file + resume vào DB
│   ├── candidate_service.py    # tạo/sửa Candidate (form "Thêm ứng viên")
│   ├── password_reset_service.py  # Forgot/Reset Password qua email
│   └── audit_service.py
├── routers/                # auth, users, departments, jobs, applications, offers,
│                            # email_templates, ai, dashboard, audit, candidates,
│                            # candidate_sources, resumes, interview
└── seed_data.py
uploads/resumes/            # file CV thật đã upload (gitignored)
tests/                      # pytest, tự reset DB trước mỗi test
scripts/smoke_*.py          # 3 script E2E qua HTTP thật
scripts/migrate_v2_*.py     # migration thủ công idempotent (không có Alembic - xem G-TECH-01)
```

## Business ID

`app/core/id_generator.py` — bảng `id_sequences` + row lock (`SELECT ... FOR UPDATE`
trên MySQL/Postgres; `threading.Lock` bổ sung cho SQLite dev/test). Mỗi entity có
`business_id` (VD `UV0001`, `OFF0001`) là identifier duy nhất expose qua API/URL;
`id` (INT autoincrement) vẫn là PK/FK kỹ thuật nội bộ.

## Offer 4-eyes approval

`app/services/offer_service.py`. Invariant `creator_id != approver_id` được
enforce **2 lớp**: service layer (`approve_offer`) và DB (`CheckConstraint` trên
model `Offer`). Xem `tests/test_offer_approval.py`.

## Re-apply không cooldown + Idempotency

`app/services/application_service.py::apply_for_job`. Không có bất kỳ check ngày
tháng nào. Idempotency dựa trên header `Idempotency-Key` + unique constraint
`(candidate_id, idempotency_key)`. Xem `tests/test_reapply.py`.

## Dashboard

`GET /dashboard/summary` — công thức dùng đúng theo `ats_system_design_v2.md` Phần
12.2: funnel theo trạng thái, tỷ lệ nhận Offer, thời gian tuyển trung bình, phân
tích theo nguồn, hiệu suất từng HR (chỉ HR_MANAGER/ADMIN). Scope theo role giống
`GET /applications`. Frontend vẽ bảng Chart.js (bar/doughnut) ở tab Dashboard.

## AI Screening

`app/services/ai_service.py` — `POST /ai/analyze/{application_id}`. Gọi AI Provider
thật (Gemini hoặc Claude, chọn qua `AI_PROVIDER`), retry tối đa 3 lần (delay 2s giữa
các lần) để vượt qua lỗi quá tải tạm thời. **Không còn chế độ STUB** - đã bỏ hoàn
toàn theo yêu cầu nghiệp vụ: nếu chưa cấu hình `AI_API_KEY` (400) hoặc gọi thất bại
sau 3 lần thử (502), API trả về thông báo lỗi CỤ THỂ (hết quota/sai key/model không
tồn tại/quá tải...) qua `AIAnalysisError`/`_classify_ai_error`, không bao giờ trả về
dữ liệu giả. Lưu lịch sử vào `ai_analyses` với cờ `is_latest` (không xoá các lần
phân tích cũ). Nếu Application chưa có CV text (`extracted_text` rỗng), trả về
`202 Accepted` + `needs_manual_review: true` thay vì lỗi (đây không phải lỗi AI
Provider nên không throw `AIAnalysisError`). Xem `tests/test_ai_screening.py`.

## Email Automation

`app/services/email_service.py` + `app/routers/email_templates.py`. Luôn gửi thật qua
SMTP (Gmail) - không còn chế độ giả lập; nếu `SMTP_USER`/`SMTP_PASSWORD` chưa cấu hình
hoặc sai, việc gửi sẽ thất bại thật và được ghi nhận cụ thể vào `audit_logs`
(`EMAIL_SENT`/`EMAIL_FAILED`). Tự động kích hoạt theo giai đoạn:
`APPLICATION_RECEIVED` (lúc Apply), `SHORTLISTED`/`INTERVIEW_INVITATION`/`REJECTION`
(lúc đổi trạng thái Application), `OFFER` (lúc gửi Offer), `ONBOARDING` (lúc Candidate
Accept Offer) — best-effort, không làm fail luồng nghiệp vụ chính nếu gửi lỗi hoặc
chưa có template ACTIVE cho giai đoạn đó. HR Manager/Admin quản lý template qua tab
"Mẫu Email"; mọi role HR+ có thể gửi thủ công qua nút "Gửi Email" ở modal chi tiết hồ sơ.

## Resume Upload (PDF/DOCX thật)

`app/services/resume_parser.py` + `resume_service.py` — `POST /applications/{id}/resume`
(multipart). Validate extension + magic-bytes + giới hạn 10MB, lưu file thật vào
`uploads/resumes/{application_id}_{uuid4}.{ext}`, trích xuất text thật bằng `pypdf`
(PDF) / `python-docx` (DOCX). Nếu không trích xuất được text (vd PDF ảnh scan), vẫn
lưu file nhưng gắn cờ `needs_manual_review`. **Chưa có** antivirus scan thật (ClamAV
cần daemon ngoài, không cài được trong môi trường build này). Xem `tests/test_resume_upload.py`.

## Kanban + Search/Filter

`GET /applications` hỗ trợ `job_business_id`, `candidate_business_id` và `search`
(tên/email/SĐT ứng viên); `GET /jobs` hỗ trợ `search` (tiêu đề) và `department_business_id`.
Kanban card hiện đầy đủ tên/email/SĐT ứng viên, vị trí ứng tuyển, AI match score (badge
màu), và trạng thái CV (có/chưa có, cần xem thủ công). Tab "Ứng viên" có cả 2 chế độ xem:
Kanban và Bảng - ở chế độ Bảng có thể sửa trực tiếp Giai đoạn/Nguồn hồ sơ, xem AI Screening
đầy đủ, và mở Hồ sơ ứng viên chi tiết (lịch sử tất cả Application, không bị ghi đè).

Tin tuyển dụng sửa được qua `PUT /jobs/{id}` (HR_MANAGER/ADMIN) bất kể đang ở trạng
thái DRAFT hay đã PUBLISHED - không còn giới hạn chỉ sửa được lúc còn nháp.

## Candidate Sources (System Configuration)

`app/routers/candidate_sources.py` — CRUD "Nguồn hồ sơ" (VD Website/Facebook/Referral),
HR_MANAGER/ADMIN toàn quyền quản lý, HR+Candidate chỉ xem được các nguồn `ACTIVE` (Candidate
cần xem để chọn lúc Ứng tuyển - **bắt buộc**, không còn là text tự do). `Application.source_id`
(FK) lưu tham chiếu thật tới nguồn; `Application.source` (text) là snapshot tên nguồn tại
thời điểm nộp đơn, không đổi ngay cả khi nguồn sau này bị đổi tên/vô hiệu hoá. Migration:
`scripts/migrate_v2_3.py`.

## Interview

`app/routers/interview.py` — CRUD lịch phỏng vấn (`POST`/`GET`/`GET /me`/`GET /{id}`/`PUT`/`DELETE`),
scope theo `assigned_hr_id` giống các module khác (HR chỉ thao tác Interview của Application
được gán). Tự động gửi email `INTERVIEW_INVITATION` nếu có template ACTIVE tương ứng.
Danh sách người phỏng vấn để chọn lúc tạo lịch lấy từ `GET /users/interviewers`
(riêng, không dùng `GET /users` vì endpoint đó chỉ HR_MANAGER/ADMIN mới gọi được) -
trả về mọi user có role HR/HR_MANAGER/ADMIN đang ACTIVE, cả 3 role đều chọn được.

## Audit Log

`app/routers/audit.py` (`GET /audit-logs`, chỉ ADMIN) + `app/services/audit_service.py`.
Ghi nhận hành động/đối tượng/người thực hiện bằng tiếng Việt có dấu (xem
`AUDIT_ACTION_LABEL`/`AUDIT_ENTITY_LABEL` trong `app/static/index.html`), hiện tên
thật của người thực hiện (không hiện business_id kỹ thuật). Mọi trường DateTime trả
về qua API đều đi qua `app/core/time_utils.py::to_iso_utc()` trước khi serialize -
MySQL/SQLAlchemy đọc DateTime về dạng "naive" (mất timezone) dù đã ghi bằng UTC thật,
nếu serialize trực tiếp bằng `.isoformat()` thì thiếu hậu tố `+00:00` khiến
`new Date(...)` phía frontend hiểu nhầm là giờ địa phương (lệch đúng bằng chênh lệch
UTC thật, VD Việt Nam UTC+7 sẽ hiển thị sớm hơn 7 tiếng). Frontend dùng chung hàm
`formatDate`/`formatTime`/`formatDateTime` (định dạng `dd/mm/yyyy`, có zero-pad) cho
mọi nơi hiển thị ngày giờ, thay vì `toLocaleString('vi-VN')` (không đảm bảo zero-pad).

## Forgot / Reset Password

`app/routers/auth.py` (`POST /auth/forgot-password`, `POST /auth/reset-password`) +
`app/services/password_reset_service.py`. Áp dụng cho **mọi role** (không riêng Candidate).
Luồng: nhập email → token random (SHA-256 hash lưu DB, hết hạn 30 phút mặc định, dùng 1 lần) →
email chứa link `{api_url}/reset-password?token=...` → frontend tự đọc `?token=` trên URL và mở
modal đặt mật khẩu mới. Phản hồi API luôn trung tính (không tiết lộ email có tồn tại hay không).
**Lưu ý quan trọng**: cần có sẵn 1 `EmailTemplate` loại `PASSWORD_RESET` đang `ACTIVE` thì email
mới thực sự được gửi (nếu không, API vẫn trả "thành công" nhưng không gửi gì cả - đã từng là 1
bug thực tế) — `python -m app.seed_data` đã seed sẵn.

