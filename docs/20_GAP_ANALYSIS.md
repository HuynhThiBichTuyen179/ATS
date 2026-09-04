# 20 — GAP ANALYSIS — ATS v2.1

Tổng hợp **toàn bộ** khoảng trống/bất nhất phát hiện xuyên suốt `00`–`19` vào 1 danh sách duy nhất, phân loại theo mức độ nghiêm trọng. Mỗi Gap giữ nguyên mã tham chiếu gốc (nếu có) để truy ngược tài liệu nguồn.

> **CẬP NHẬT 2026-08-18** (ngoài phạm vi bộ 23-file gốc, ở lượt làm việc sau — theo đúng cách OQ-03/OQ-05 ở `21` đã làm): đã re-verify từng Gap ở nhóm A/B bằng grep/đọc trực tiếp code hiện tại (không lấy từ trí nhớ). Trạng thái mới nhất đánh dấu bằng ✅/🔵 ngay dưới từng dòng gốc — **giữ nguyên dòng gốc**, không sửa/xóa, đúng RULE 4. Từ lượt làm việc này trở đi codebase còn có thêm các module hoàn toàn mới không nằm trong phạm vi rà soát gốc (Candidate Sources, Interview, Resume download, Forgot/Reset Password) — **chưa** được đưa vào ma trận endpoint chi tiết ở `07`/`08`/`16`; xem ghi chú cuối file.

**Thang mức độ**: 🔴 Cao (ảnh hưởng bảo mật/toàn vẹn dữ liệu) · 🟠 Trung bình (thiếu tính năng đã thiết kế sẵn hạ tầng, hoặc rủi ro vận hành) · 🟡 Thấp (nợ kỹ thuật, dữ liệu/schema chưa dùng, không ảnh hưởng vận hành hiện tại).

## A. Nhóm Bảo mật / Row-level Scope (🔴 Cao)

| Gap ID | Mô tả | Bằng chứng | Tác động | Khuyến nghị |
|---|---|---|---|---|
| G-07-1 | `GET /jobs/{id}` không yêu cầu xác thực và không lọc `status` | `app/routers/jobs.py:144-149` | Người chưa đăng nhập đọc được tin `DRAFT`/`CLOSED` (kèm khoảng lương nội bộ) nếu đoán được `business_id` tuần tự (`JOB0003`...) | Thêm `Depends(get_current_user)` + áp cùng logic lọc `status=PUBLISHED` cho Candidate như `list_jobs()` |
| | ✅ **ĐÃ SỬA** (2026-08-18, ngoài phạm vi gốc) — `get_job()` (`app/routers/jobs.py`, dùng `get_current_user_optional` mới thêm ở `app/deps/rbac.py`) giờ **cho phép ẩn danh** (đúng nhu cầu Public Job Detail) nhưng **vẫn lọc**: chỉ HR+ hoặc job đang `PUBLISHED` mới trả 200, còn lại `404 JOB_NOT_FOUND` — vá đúng lỗ hổng mà vẫn giữ được yêu cầu nghiệp vụ mới "Job Detail public phải xem được không cần đăng nhập". | | | |
| G-07-2 | `GET /applications/{id}` không kiểm tra `assigned_hr_id` cho vai trò HR | `app/routers/applications.py:125-134` | HR bất kỳ đọc được chi tiết Application (thông tin cá nhân ứng viên) ngoài phạm vi được gán, mâu thuẫn với `list_applications()` cùng router | Bổ sung nhánh kiểm tra `current_user.role == HR and application.assigned_hr_id != current_user.id → 403`, theo đúng mẫu đã có ở `offers.py::_check_can_view_offer` |
| | 🔵 **VẪN CÒN TỒN TẠI** — verify lại 2026-08-18 bằng grep: `get_application()` (`app/routers/applications.py:160-168`, số dòng đã dịch chuyển do file phình to hơn) vẫn chỉ kiểm tra `CANDIDATE`, chưa có nhánh `HR`. Trong lượt làm việc V2.3 vừa qua đã áp đúng mẫu scoping này cho `PUT /applications/{id}` (endpoint mới) và `PUT /candidates/{id}`, nhưng **chưa lan sang** `GET /applications/{id}` hiện có — cùng 1 khuyến nghị sửa như dòng gốc vẫn còn nguyên giá trị. | | | |
| G-07-3 | `POST /email-templates/send/{id}` không kiểm tra `assigned_hr_id` cho vai trò HR | `app/routers/email_templates.py:107-133` | HR gửi được email cho Application ngoài phạm vi được gán | Áp dụng lại mẫu `_check_scope` đã có ở `app/routers/ai.py` |
| | 🔵 **VẪN CÒN TỒN TẠI** — verify lại 2026-08-18: `send_manual_email()` (`app/routers/email_templates.py:160-186`) chỉ dùng `require_hr_or_above`, chưa có `_check_scope`. Chưa được sửa trong các lượt làm việc gần đây; khuyến nghị gốc vẫn đúng. | | | |
| G-NFR-SEC-002 | `jwt_secret` mặc định `"change-me-in-production"` nếu `.env` không override | `app/core/config.py:9` | Nếu deploy thật mà quên đặt `JWT_SECRET`, toàn bộ token có thể bị giả mạo (secret công khai trong source) | Bắt buộc fail-fast khi khởi động nếu `jwt_secret` vẫn là giá trị mặc định và môi trường không phải `dev` |
| G-NFR-SEC-003 | `CORSMiddleware` cấu hình `allow_origins=["*"]` + `allow_credentials=True` cùng lúc | `app/main.py:32-38` | Tổ hợp không hợp lệ theo chuẩn CORS trình duyệt nếu sau này chuyển sang cookie-based session; hiện tại không khai thác được vì dùng Bearer token | Đổi `allow_origins` thành danh sách domain cụ thể trước khi cấu hình `allow_credentials=True`, hoặc bỏ `allow_credentials` nếu tiếp tục dùng Bearer-only |
| G-POST-01 | **[MỚI, phát hiện + sửa 2026-08-18]** `GET /candidate-sources` chặn cứng `403` với role `CANDIDATE` — bug tự tạo ra ở lượt làm việc V2.3 khi thêm yêu cầu "chọn Nguồn hồ sơ bắt buộc lúc Ứng tuyển": form Apply của chính Candidate gọi đúng endpoint bị chặn này để đổ dropdown, lỗi 403 bị nuốt lặng lẽ ở frontend (`try {...} catch(e){}`) nên hiển thị nhầm thành "Hệ thống chưa cấu hình Nguồn hồ sơ nào" dù Admin đã cấu hình sẵn | `app/routers/candidate_sources.py::list_sources` (trước sửa) | Candidate không thể ứng tuyển được (trường bắt buộc luôn rỗng) dù dữ liệu cấu hình đúng — phát hiện qua báo cáo trực tiếp của người dùng, không phải do rà soát chủ động | ✅ **ĐÃ SỬA** — Candidate giờ được xem danh sách Nguồn **chỉ các mục `ACTIVE`** (read-only, không quản lý được — tạo/sửa/xóa vẫn `403` như cũ). Test hồi quy: `tests/test_candidate_sources.py::test_candidate_can_view_active_sources_but_not_manage` (thay thế test cũ đang khóa sai hành vi 403) |

## B. Nhóm Reliability / Tính năng đã thiết kế nhưng chưa kích hoạt (🟠 Trung bình)

| Gap ID | Mô tả | Bằng chứng | Tác động | Khuyến nghị |
|---|---|---|---|---|
| OFFER-11 | Offer quá hạn không tự động chuyển `EXPIRED` | `offer_service.py::expire_due_offers` tồn tại + có test, nhưng 0 lời gọi trong `app/`; `apscheduler==3.10.4` có trong `requirements.txt` nhưng 0 import trong toàn bộ `app/` (`17_TECHNOLOGY_STACK.md`) | Offer hết hạn "treo" ở `SENT` vô thời hạn nếu không có ai gọi thủ công; Candidate/HR không được thông báo | Wiring `APScheduler` (`BackgroundScheduler`) trong `lifespan()` của `app/main.py`, chạy `expire_due_offers` định kỳ (VD mỗi giờ) |
| APP-20 | Không có API lên lịch/ghi nhận kết quả phỏng vấn | Bảng `interviews` đầy đủ 14 cột, `InterviewStatus` enum tồn tại, nhưng không có `app/routers/interview.py` | HR phải quản lý lịch phỏng vấn hoàn toàn ngoài hệ thống (email/lịch riêng); dữ liệu phỏng vấn không truy vết được trong ATS | Xây `interview.py` router theo đúng mẫu CRUD các module khác (backlog đã có sẵn schema) |
| | ✅ **ĐÃ SỬA** — verify 2026-08-18: `app/routers/interview.py` **đã tồn tại** với đầy đủ CRUD (`POST/GET/GET "/me"/GET "/{id}"/PUT/DELETE`, 6 endpoint), có scoping theo `assigned_hr_id`. Được xây ở 1 lượt làm việc trước 2026-08-18, ngoài phạm vi audit gốc — **chưa** được đưa vào ma trận endpoint `07`/`08` (số endpoint công bố "37" ở `22` mục 1 nay đã lạc hậu, cần đếm lại nếu làm 1 đợt refresh đầy đủ). | | | |
| AI-7 | Không có logic giới hạn chi phí gọi AI theo tháng | `ai_monthly_budget_cap_usd` tồn tại trong `config.py` nhưng không đọc ở đâu trong `ai_service.py` | Nếu khối lượng ứng tuyển tăng đột biến, chi phí gọi AI Provider (Gemini/Claude) không được kiểm soát | Đếm số lần gọi AI Provider thành công/tháng, so với cap, chặn hoặc cảnh báo khi vượt |
| USER-5/6 | Không sửa/khóa/xóa được tài khoản nội bộ đã tạo; không tự đổi mật khẩu | Không có route PUT/DELETE `/users`, không có route đổi mật khẩu | HR_MANAGER/ADMIN không thu hồi quyền được khi nhân viên nghỉ việc; người dùng phải nhờ Admin tạo lại nếu quên mật khẩu (không có AUTH-9) | Bổ sung `PUT /users/{id}` (sửa/đổi `status`), `PUT /auth/change-password` |
| | 🟡 **MỘT PHẦN ĐÃ SỬA** — verify 2026-08-18: `PUT /{user_business_id}` và `DELETE /{user_business_id}` **đã có** (`app/routers/users.py:114,153`, sửa ở lượt làm việc trước 2026-08-18) — phần "sửa/khóa/xóa tài khoản" đã giải quyết. Phần **"tự đổi mật khẩu" (đã đăng nhập, biết mật khẩu cũ) vẫn CHƯA có** — không tìm thấy route `change-password` nào trong `app/routers/`. Lưu ý: khác với AUTH-9 (quên mật khẩu) đã giải quyết riêng ở dòng dưới — đây là 2 luồng nghiệp vụ khác nhau (đổi mật khẩu chủ động vs quên mật khẩu), USER-5/6 chỉ còn thiếu luồng đổi chủ động. | | | |
| AUTH-9/10 | Không có khôi phục mật khẩu, không xác thực email đăng ký | Không tìm thấy route liên quan | Rủi ro vận hành khi người dùng quên mật khẩu hoặc nhập sai email lúc đăng ký | Backlog chuẩn — cần trước khi mở đăng ký công khai thật |
| | ✅ **AUTH-9 ĐÃ SỬA HOÀN TOÀN** (2026-08-18) — `POST /auth/forgot-password` + `POST /auth/reset-password` (`app/routers/auth.py`) đã được xây ở lượt làm việc trước đó, nhưng **có bug ẩn khiến tính năng câm lặng không hoạt động**: `password_reset_service.request_password_reset()` chỉ gửi email khi tìm được 1 `EmailTemplate` loại `PASSWORD_RESET` đang `ACTIVE`, mà `app/seed_data.py` **chưa từng seed loại này** (chỉ có 7/8 loại) — kết quả là API luôn trả `200 "thành công"` (đúng thiết kế chống lộ thông tin tài khoản) nhưng **không có email nào được gửi thật**. Đã sửa: thêm mẫu `PASSWORD_RESET` vào `DEMO_EMAIL_TEMPLATES`, chạy lại `python -m app.seed_data` (idempotent) vào DB MySQL dev thật. Verify bằng cách gọi trực tiếp flow thật — `audit_logs` ghi nhận `EMAIL_SENT \| SENT (SMTP that)`, tức email đã đi qua Gmail SMTP thật. AUTH-10 (xác thực email đăng ký) **vẫn còn mở** — chưa có route liên quan. | | | |
| JOB-8 | Quy trình duyệt tin nhiều bước chưa hiện thực dù enum đã có đủ 6 giá trị | `JobStatus` có `PENDING_APPROVAL`/`APPROVED`/`CANCELLED` nhưng không route nào set các giá trị này | Đăng tin hiện là hành động 1 bước của chính người tạo — không có kiểm soát chéo như Offer (4-eyes) | Xác nhận với Product Owner đây là chủ đích đơn giản hóa hay backlog thật sự cần làm (xem `21_OPEN_QUESTIONS.md`) |

## C. Nhóm Dữ liệu chưa sử dụng / Nợ kỹ thuật (🟡 Thấp)

| Gap ID | Mô tả | Bằng chứng |
|---|---|---|
| G-DB-01 | `Application.match_score` không bao giờ được ghi giá trị — API thực tế đọc điểm số từ `AIAnalysis.match_score` mới nhất qua relationship, bỏ qua hoàn toàn cột này | `app/routers/applications.py:57` join `latest_analysis.match_score`; không có `application.match_score = ` ở bất kỳ đâu trong `app/` |
| G-DB-02 | `resumes.parsed_data` (JSON dự phòng) không bao giờ được ghi | `app/models/resume.py:27`, không có assignment trong `resume_service.py`/`resume_parser.py` |
| G-DB-03 | `offers.offer_file` (đính kèm file Offer) không bao giờ được ghi | `app/models/offer.py:49`, không có endpoint upload file cho Offer |
| G-DB-04 | `jobs.deadline` tồn tại nhưng không có logic nào đọc/kiểm tra hạn nộp hồ sơ | `app/models/job.py:38` |
| G-DB-05 | `jobs.slug` tự sinh nhưng không route nào dùng để truy vấn (JOB-7) | `app/models/job.py:20`, `app/routers/jobs.py` chỉ dùng `business_id` |
| G-DB-06 | `candidates.gender/date_of_birth/address/current_salary/expected_salary` không có endpoint nào ghi | `app/models/candidate.py`, `ApplyRequest` không có các field này |
| | 🟡 **MỘT PHẦN ĐÃ SỬA** — verify 2026-08-18: `gender` **đã ghi được** qua `CandidateCreateRequest`/`CandidateUpdateRequest` (`app/schemas/candidate.py`) từ lượt làm việc V2.2/V2.3. `date_of_birth`/`address`/`current_salary`/`expected_salary` **vẫn chưa có endpoint nào ghi** — vẫn là cột chết trong `app/models/candidate.py:34-37`. |
| G-DB-07 | `departments.status` (`DepartmentStatus`) không route nào set khác `ACTIVE` | `app/models/department.py:14-17` |
| G-DB-08 | Kiểu dữ liệu không nhất quán: `Application.needs_manual_review` dùng `Integer` (0/1) trong khi `AIAnalysis.is_latest` dùng `Boolean` cho cùng ngữ nghĩa cờ bool | `app/models/application.py:46` vs `app/models/ai_analysis.py:22` |
| G-TECH-01 | Không có Alembic — thay đổi schema sau này không migrate được dữ liệu đã có | `requirements.txt` không có `alembic`; `app/main.py::lifespan` chỉ gọi `create_all()` |
| G-TECH-02 | Không có linter/formatter/type-checker/pre-commit config | Không tìm thấy `pyproject.toml`/`ruff.toml`/`.flake8`/`.pre-commit-config.yaml` |
| G-TECH-03 | Frontend phụ thuộc hoàn toàn CDN công cộng (Tailwind, Chart.js, Font Awesome, Google Fonts), không có fallback tự host | `app/static/index.html` dòng 7-10 |
| G-DOC-01 | `app/static/css/style.css` (699 dòng) và `app/static/js/app.js` (804 dòng) tồn tại nhưng không được `index.html` tham chiếu | Xác nhận bằng grep ở `00_PROJECT_DISCOVERY.md` |
| G-DOC-02 | Số endpoint đếm ban đầu ở `00` là 35, đếm lại chính xác qua từng router ở `08` là 37 | `08_FUNCTIONAL_SPECIFICATION.md` mục 11 |
| G-INFRA-01 | Không có Dockerfile/CI-CD/IaC — không thể xác nhận kiến trúc triển khai production | `14_SYSTEM_ARCHITECTURE.md` mục 10 |
| EMAIL-10 | Không lưu lại nội dung đầy đủ (`body`) của email đã gửi, chỉ lưu `{to, subject}` trong `audit_logs.after_data` | `app/services/email_service.py::send_email` |

## D. Tổng hợp theo Nhãn bằng chứng (đối chiếu RULE 2)

| Nhãn | Số lượng Gap tương ứng |
|---|---|
| `[CONFIRMED]` (có bằng chứng trực tiếp cho từng Gap — chính Gap là 1 phát hiện CONFIRMED, dù đối tượng Gap mô tả là 1 tính năng MISSING) | 24/24 |
| `[INFERRED]` | 0 |
| `[ASSUMED]` | 0 |

Toàn bộ 24 Gap trong tài liệu này đều được xác nhận bằng grep/đọc trực tiếp source code — không có Gap nào dựa trên suy đoán, đúng tinh thần RULE 1/RULE 2 áp dụng ngay cả khi đi tìm "cái không tồn tại".

## E. Ưu tiên khắc phục đề xuất (không phải quyết định cuối — cần Product Owner xác nhận ở `21_OPEN_QUESTIONS.md`)

1. **Ngay lập tức** (bảo mật, chi phí sửa thấp): G-07-1, G-07-2, G-07-3, G-NFR-SEC-002.
2. **Trước khi mở rộng người dùng thật**: OFFER-11 (wiring APScheduler đã cài sẵn), AUTH-9/10, USER-5/6.
3. **Trước khi lên production**: G-TECH-01 (Alembic), G-INFRA-01 (Docker/CI), G-NFR-SEC-003 (CORS).
4. **Backlog dài hạn / cần quyết định nghiệp vụ trước**: ~~APP-20 (Interview module)~~ (✅ đã sửa, xem ghi chú), JOB-8 (quy trình duyệt tin nhiều bước), AI-7 (cost cap).
5. **Dọn dẹp kỹ thuật, không khẩn cấp**: toàn bộ nhóm C (G-DB-*, G-DOC-*, G-TECH-02/03).

## F. Ghi chú phạm vi (bổ sung 2026-08-18)

Bộ tài liệu `00`–`22` là **ảnh chụp trạng thái code tại 2026-08-14** (đúng như cảnh báo ở `22` mục 4.4: "không tự động đồng bộ với code"). Từ thời điểm đó đến nay, ngoài các Gap đã re-verify ở trên, codebase còn có **các module/tính năng hoàn toàn mới chưa từng nằm trong phạm vi rà soát gốc**, nên **chưa** được phản ánh trong ma trận endpoint chi tiết `07_USER_ROLE_PERMISSION.md`/`08_FUNCTIONAL_SPECIFICATION.md`/`16_DATABASE_DESIGN.md`:

- **Candidate Sources** (`app/routers/candidate_sources.py`, bảng `candidate_sources`) — System Configuration cho "Nguồn hồ sơ", CRUD đầy đủ + `Application.source_id` (FK) mới.
- **Interview** (`app/routers/interview.py`, đã nêu ở APP-20 trên).
- **Resume download** (`GET /resumes/{id}/download`, `app/routers/resumes.py`).
- **Forgot/Reset Password** (`POST /auth/forgot-password`, `POST /auth/reset-password`, bảng `password_reset_tokens`).
- **`PUT /applications/{id}`** (sửa Lương mong muốn/Nguồn hồ sơ từ Candidate Table, tách biệt với `PUT /applications/{id}/status`).

Việc cập nhật đầy đủ, chính xác 07/08/16 (và các file liên quan 09/11/12/14/15/19) theo đúng phương pháp gốc (đọc trực tiếp từng router, đếm lại số endpoint thật, vẽ lại ERD/sequence nếu cần) là **một khối lượng công việc tương đương 1 phần đáng kể của đợt reverse-engineering ban đầu** (ước lượng nhiều giờ/nhiều lượt làm việc, không phải một chỉnh sửa nhỏ) — nằm **ngoài phạm vi** của lượt cập nhật nhanh này. Lượt này chỉ re-verify và cập nhật các tài liệu "trạng thái sống" (`20`, `21`, `22`, `README.md`) theo đúng bằng chứng thực tế hiện tại.

---

*Tài liệu tiếp theo: `21_OPEN_QUESTIONS.md`.*
