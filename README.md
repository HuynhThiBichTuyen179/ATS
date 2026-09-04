# ATS — Backend Implementation

> Cap nhat 2026-08-23: README dong bo lai theo trang thai code thuc te sau dot ra
> soat/lam sach (bo hoan toan che do STUB cua AI Screening, sua loi lech gio audit
> log/timestamp, them .env.example, don dep dead code). Xem `docs/20_GAP_ANALYSIS.md`
> muc F va `docs/22_FINAL_CONSISTENCY_REVIEW.md` muc 6 de biet phan nao cua bo tai
> lieu `docs/00-22` (BRD/SRS/UML - dac ta hinh thuc) van la anh chup cu (2026-08-14)
> chua duoc dong bo lai voi code hien tai; bo tai lieu do KHONG nam trong pham vi dot
> ra soat nay (xem ghi chu cuoi file).

Implementation that (khong phai chi tai lieu) cua `ats_system_design_v2.md`, xay moi
tu dau, tich hop san 3 thay doi nghiep vu CHANGE 01/02/03, cong Dashboard, AI
Screening, Email Automation, va Resume Upload that. Xem `CONFLICT_REPORT_AND_BACKLOG.md`
de biet vi sao day la thu muc rieng (khong dung `backend/`, `frontend/` cu) va phan
nao con thieu so voi spec day du.

## Chay thu

```bash
cd ats-v2
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env

python -m app.seed_data       # tao du lieu mau (Department/Admin/HR Manager x2/HR/1 Job PUBLISHED)
uvicorn app.main:app --reload --port 8000
```

Mo `http://localhost:8000` — frontend (`app/static/index.html`) duoc serve tai `/`,
goi thang API that (khong mock data).

He thong **bat buoc dung MySQL** (khong con che do SQLite cho ung dung that). Dien vao
`.env`:

```bash
USE_MYSQL=true
MYSQL_USER=root
MYSQL_PASSWORD=...
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=ten_database_cua_ban
```

Neu khong ket noi duoc MySQL luc khoi dong (sai thong tin/server chua chay), ung dung se
bao loi ro rang va dung lai ngay - khong con tu dong fallback sang CSDL khac. SQLite chi
con duoc dung noi bo boi bo test tu dong (`tests/conftest.py` tu co lap khoi MySQL that
de tranh xoa nham du lieu that moi lan chay `pytest`), khong lien quan den cau hinh chay
ung dung.

### Bat AI Screening / Email SMTP that (tuy chon)

AI Screening **bat buoc** phai co `AI_API_KEY` hop le - khong con che do gia lap
(STUB da bi bo hoan toan theo yeu cau nghiep vu), neu chua cau hinh thi
`POST /ai/analyze/{id}` tra loi 400 kem thong bao ro rang. Email cung khong con
che do gia lap - luon thu gui that qua SMTP, neu chua cau hinh `SMTP_USER`/
`SMTP_PASSWORD` (hoac sai thong tin) thi viec gui se that bai that (ghi audit
log voi ket qua that bai cu the), khong am tham coi la da xu ly. De
chay that, dien vao `.env`:

```bash
AI_PROVIDER=gemini        # hoac claude
AI_API_KEY=...            # Gemini: https://aistudio.google.com/apikey
                           # Claude: https://console.anthropic.com/settings/keys
AI_MODEL=                 # de trong de dung model mac dinh cua provider da chon
                           # (gemini-flash-lite-latest / claude-haiku-4-5-20251001),
                           # hoac ghi ten model cu the (VD gemini-3.7-flash - da test
                           # goi that thanh cong 2026-08-18)
SMTP_USER=ban@gmail.com
SMTP_PASSWORD=...         # App Password 16 ky tu, tao tai https://myaccount.google.com/apppasswords
                           # (mat khau Gmail thuong KHONG dang nhap SMTP duoc neu da bat 2FA)
```

Khong can sua code — service tu dong chuyen sang che do that khi thay key duoc cau hinh.
Luu y: neu bat SMTP that, **bat buoc** phai co it nhat 1 `EmailTemplate` loai `PASSWORD_RESET`
dang `ACTIVE` thi chuc nang Quen mat khau moi thuc su gui duoc email (xem muc Forgot/Reset
Password ben duoi) — `python -m app.seed_data` da tu seed san mau nay.

## Chay test

```bash
pytest tests/ -v                        # 106/106 unit/integration test (SQLite, tu reset DB) - cap nhat 2026-08-23
python scripts/smoke_e2e.py             # E2E Offer 4-eyes qua HTTP that
python scripts/smoke_audit_fixes.py     # E2E cac fix tu dot audit code-vs-spec
python scripts/smoke_new_features.py    # E2E Dashboard/Upload CV/AI/Email/Filter
python -m scripts.migrate_v2_2          # Migration thu cong V2.2 (idempotent, khong co Alembic)
python -m scripts.migrate_v2_3          # Migration thu cong V2.3 (source_id FK + index, idempotent)
python -m scripts.migrate_v2_4          # Migration thu cong V2.4 (bo sung 2 FK constraint con thieu
                                         # tren MySQL - applications.department_id/source_id da co cot
                                         # tu migrate_v2_2/v2_3 nhung chua tung co constraint that,
                                         # idempotent, chi can chay tren MySQL - SQLite bo qua)
python -m scripts.migrate_v2_5          # Migration thu cong V2.5 (xoa 4 cot "chet" o candidates:
                                         # address/current_salary/expected_salary/date_of_birth -
                                         # chua tung co schema/endpoint nao doc/ghi, idempotent,
                                         # chi can chay tren MySQL - SQLite bo qua)
python -m scripts.migrate_v2_6          # Migration thu cong V2.6 (xoa 5 cot "chet" o interviews:
                                         # rating/feedback/hiring_manager_name/hiring_manager_email/
                                         # hiring_manager_feedback - chua tung co schema/endpoint nao
                                         # doc/ghi, idempotent, chi can chay tren MySQL - SQLite bo qua)
```

Ca 3 script E2E can server dang chay tren `:8123` va deu dung `RUN_ID` ngau nhien moi
lan chay de an toan khi chay lai nhieu lan tren cung 1 DB dev. Chi tiet ket qua o
`CONFLICT_REPORT_AND_BACKLOG.md`.

## Tai khoan seed

| Role | Email | Mat khau |
|---|---|---|
| Admin/BGD | admin@example.com | Admin@123 |
| HR Manager A | hrmanager.a@example.com | HrManager@123 |
| HR Manager B | hrmanager.b@example.com | HrManager@123 |
| HR | hr.a@example.com | Hr@123456 |

Candidate tu dang ky qua `POST /auth/register`. Quen mat khau? Dung "Quen mat khau?"
o man dang nhap (xem muc Forgot/Reset Password ben duoi) - khong con hien mat khau seed
truc tiep tren giao dien dang nhap (da bo dong hint nay 2026-08-18).

## Cau truc

```
app/
├── main.py                # FastAPI app, lifespan (create_all cho dev), CORS, static mount
├── static/index.html      # Frontend that (vanilla JS + Tailwind + Chart.js CDN), goi API that
├── core/                  # config, database, security (JWT/bcrypt), id_generator
├── models/                # 13 bang nghiep vu + id_sequences (Business ID) = 14 file model
├── schemas/                # Pydantic request/response
├── deps/rbac.py            # get_current_user, get_current_user_optional, require_roles(...)
├── services/
│   ├── application_service.py  # state machine, re-apply, idempotency
│   ├── offer_service.py        # 4-eyes approval, Rule 2 auto-close
│   ├── ai_service.py           # AI Screening (chi Gemini/Claude that qua AI_API_KEY, khong stub)
│   ├── email_service.py        # Email Automation (SMTP that/simulate)
│   ├── resume_parser.py        # trich xuat text tu PDF/DOCX
│   ├── resume_service.py       # luu file + resume vao DB
│   ├── candidate_service.py    # tao/sua Candidate (form "Them ung vien")
│   ├── password_reset_service.py  # Forgot/Reset Password qua email
│   └── audit_service.py
├── routers/                # auth, users, departments, jobs, applications, offers,
│                            # email_templates, ai, dashboard, audit, candidates,
│                            # candidate_sources, resumes, interview
└── seed_data.py
uploads/resumes/            # file CV that da upload (gitignored)
tests/                      # pytest, tu reset DB truoc moi test
scripts/smoke_*.py          # 3 script E2E qua HTTP that
scripts/migrate_v2_*.py     # migration thu cong idempotent (khong co Alembic - xem G-TECH-01)
```

## Business ID (CHANGE 03)

`app/core/id_generator.py` — bang `id_sequences` + row lock (`SELECT ... FOR UPDATE`
tren MySQL/Postgres; `threading.Lock` bo sung cho SQLite dev/test). Moi entity co
`business_id` (VD `UV0001`, `OFF0001`) la identifier duy nhat expose qua API/URL;
`id` (INT autoincrement) van la PK/FK ky thuat noi bo — dung theo phuong an tai
lieu v2 cho phep ("co the dung technical_id + business_id").

## Offer 4-eyes approval (CHANGE 01)

`app/services/offer_service.py`. Invariant `creator_id != approver_id` duoc
enforce **2 lop**: service layer (`approve_offer`) va DB (`CheckConstraint` tren
model `Offer`). Xem `tests/test_offer_approval.py`.

## Re-apply khong cooldown + Idempotency (CHANGE 02)

`app/services/application_service.py::apply_for_job`. Khong co bat ky check ngay
thang nao. Idempotency dua tren header `Idempotency-Key` + unique constraint
`(candidate_id, idempotency_key)`. Xem `tests/test_reapply.py`.

## Dashboard

`GET /dashboard/summary` — cong thuc dung dung theo `ats_system_design_v2.md` Phan
12.2: funnel theo trang thai, ty le nhan Offer, thoi gian tuyen trung binh, phan
tich theo nguon, hieu suat tung HR (chi HR_MANAGER/ADMIN). Scope theo role giong
`GET /applications`. Frontend ve bang Chart.js (bar/doughnut) o tab Dashboard.

## AI Screening

`app/services/ai_service.py` — `POST /ai/analyze/{application_id}`. Goi AI Provider
that (Gemini hoac Claude, chon qua `AI_PROVIDER`), retry toi da 3 lan (delay 2s giua
cac lan) de vuot qua loi qua tai tam thoi. **Khong con che do STUB** - da bo hoan
toan theo yeu cau nghiep vu: neu chua cau hinh `AI_API_KEY` (400) hoac goi that bai
sau 3 lan thu (502), API tra ve thong bao loi CU THE (het quota/sai key/model khong
ton tai/qua tai...) qua `AIAnalysisError`/`_classify_ai_error`, khong bao gio tra ve
du lieu gia. Luu lich su vao `ai_analyses` voi co `is_latest` (khong xoa cac lan
phan tich cu). Neu Application chua co CV text (`extracted_text` rong), tra ve
`202 Accepted` + `needs_manual_review: true` thay vi loi (day khong phai loi AI
Provider nen khong throw `AIAnalysisError`). Xem `tests/test_ai_screening.py`.

## Email Automation

`app/services/email_service.py` + `app/routers/email_templates.py`. Luon gui that qua
SMTP (Gmail) - khong con che do gia lap; neu `SMTP_USER`/`SMTP_PASSWORD` chua cau hinh
hoac sai, viec gui se that bai that va duoc ghi nhan cu the vao `audit_logs`
(`EMAIL_SENT`/`EMAIL_FAILED`). Tu dong kich hoat theo giai doan:
`APPLICATION_RECEIVED` (luc Apply), `SHORTLISTED`/`INTERVIEW_INVITATION`/`REJECTION`
(luc doi trang thai Application), `OFFER` (luc gui Offer), `ONBOARDING` (luc Candidate
Accept Offer) — best-effort, khong lam fail luong nghiep vu chinh neu gui loi hoac
chua co template ACTIVE cho giai doan do. HR Manager/Admin quan ly template qua tab
"Mau Email"; moi role HR+ co the gui thu cong qua nut "Gui Email" o modal chi tiet ho so.

## Resume Upload (PDF/DOCX that)

`app/services/resume_parser.py` + `resume_service.py` — `POST /applications/{id}/resume`
(multipart). Validate extension + magic-bytes + gioi han 10MB, luu file that vao
`uploads/resumes/{application_id}_{uuid4}.{ext}`, trich xuat text that bang `pypdf`
(PDF) / `python-docx` (DOCX). Neu khong trich xuat duoc text (vd PDF anh scan), van
luu file nhung gan co `needs_manual_review`. **Chua co** antivirus scan that (ClamAV
can daemon ngoai, khong cai duoc trong moi truong build nay). Xem `tests/test_resume_upload.py`.

## Kanban + Search/Filter

`GET /applications` ho tro `job_business_id`, `candidate_business_id` va `search`
(ten/email/SDT ung vien); `GET /jobs` ho tro `search` (tieu de) va `department_business_id`.
Kanban card hien day du ten/email/SDT ung vien, vi tri ung tuyen, AI match score (badge
mau), va trang thai CV (co/chua co, can xem thu cong). Tab "Ung vien" (doi ten tu
"Ung vien (Kanban)" 2026-08-18) co ca 2 che do xem: Kanban va Bang - o che do Bang co
the sua truc tiep Giai doan/Nguon ho so, xem AI Screening day du, va mo Ho so ung vien
chi tiet (lich su tat ca Application, khong bi ghi de).

Tin tuyen dung sua duoc qua `PUT /jobs/{id}` (HR_MANAGER/ADMIN) bat ke dang o trang
thai DRAFT hay da PUBLISHED - khong con gioi han chi sua duoc luc con nhap.

## Candidate Sources (System Configuration)

`app/routers/candidate_sources.py` — CRUD "Nguon ho so" (VD Website/Facebook/Referral),
HR_MANAGER/ADMIN toan quyen quan ly, HR+Candidate chi xem duoc cac nguon `ACTIVE` (Candidate
can xem de chon luc Ung tuyen - **bat buoc**, khong con la text tu do). `Application.source_id`
(FK) luu tham chieu that toi nguon; `Application.source` (text) la snapshot ten nguon tai
thoi diem nop don, khong doi ngay ca khi nguon sau nay bi doi ten/vo hieu hoa. Migration:
`scripts/migrate_v2_3.py`.

## Interview

`app/routers/interview.py` — CRUD lich phong van (`POST`/`GET`/`GET /me`/`GET /{id}`/`PUT`/`DELETE`),
scope theo `assigned_hr_id` giong cac module khac (HR chi thao tac Interview cua Application
duoc gan). Tu dong gui email `INTERVIEW_INVITATION` neu co template ACTIVE tuong ung.
Danh sach nguoi phong van de chon luc tao lich lay tu `GET /users/interviewers`
(rieng, khong dung `GET /users` vi endpoint do chi HR_MANAGER/ADMIN moi goi duoc) -
tra ve moi user co role HR/HR_MANAGER/ADMIN dang ACTIVE, ca 3 role deu chon duoc.

## Audit Log

`app/routers/audit.py` (`GET /audit-logs`, chi ADMIN) + `app/services/audit_service.py`.
Ghi nhan hanh dong/doi tuong/nguoi thuc hien bang tieng Viet co dau (xem
`AUDIT_ACTION_LABEL`/`AUDIT_ENTITY_LABEL` trong `app/static/index.html`), hien ten
that cua nguoi thuc hien (khong hien business_id ky thuat). Moi truong DateTime tra
ve qua API deu di qua `app/core/time_utils.py::to_iso_utc()` truoc khi serialize -
MySQL/SQLAlchemy doc DateTime ve dang "naive" (mat timezone) du da ghi bang UTC that,
neu serialize truc tiep bang `.isoformat()` thi thieu hau to `+00:00` khien
`new Date(...)` phia frontend hieu nham la gio dia phuong (lech dung bang chenh lech
UTC that, VD Viet Nam UTC+7 se hien thi som hon 7 tieng). Frontend dung chung ham
`formatDate`/`formatTime`/`formatDateTime` (dinh dang `dd/mm/yyyy`, co zero-pad) cho
moi noi hien thi ngay gio, thay vi `toLocaleString('vi-VN')` (khong dam bao zero-pad).

## Forgot / Reset Password

`app/routers/auth.py` (`POST /auth/forgot-password`, `POST /auth/reset-password`) +
`app/services/password_reset_service.py`. Ap dung cho **moi role** (khong rieng Candidate).
Luong: nhap email → token random (SHA-256 hash luu DB, het han 30 phut mac dinh, dung 1 lan) →
email chua link `{api_url}/reset-password?token=...` → frontend tu doc `?token=` tren URL va mo
modal dat mat khau moi. Phan hoi API luon trung tinh (khong tiet lo email co ton tai hay khong).
**Luu y quan trong**: can co san 1 `EmailTemplate` loai `PASSWORD_RESET` dang `ACTIVE` thi email
moi thuc su duoc gui (neu khong, API van tra "thanh cong" nhung khong gui gi ca - da tung la 1
bug thuc te, xem `docs/20_GAP_ANALYSIS.md` muc AUTH-9) — `python -m app.seed_data` da seed san.

## Ve bo tai lieu `docs/00-22` va `CONFLICT_REPORT_AND_BACKLOG.md`

README nay la tai lieu "song" (dong bo theo code moi lan co thay doi lon). Nguoc
lai, `docs/00_PROJECT_DISCOVERY.md` → `docs/22_FINAL_CONSISTENCY_REVIEW.md` la bo
dac ta hinh thuc (BRD/SRS/Use Case/BPMN/UML/Database Design...) va
`CONFLICT_REPORT_AND_BACKLOG.md` la bao cao chot moc v2.1 - ca hai deu la **anh
chup tai 1 thoi diem** (2026-08-13/14), khong duoc dot ra soat/lam sach nay chinh
sua lai noi dung nghiep vu, vi day co the la tai lieu dac ta chinh thuc dung de nop/
bao ve do an. Neu can dong bo lai toan bo 22 file theo dung trang thai code hien
tai, do la mot quyet dinh pham vi lon (co the anh huong noi dung da nop) nen can
xac nhan truoc khi thuc hien.
