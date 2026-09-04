# 04 — KHẢO SÁT VÀ XÁC ĐỊNH YÊU CẦU

Đây là bảng kiểm kê yêu cầu **thô** (raw requirement inventory), tổ chức theo module (`01_MASTER_DOCUMENT_OUTLINE.md` mục A.2), làm nguyên liệu đầu vào để hệ thống hóa thành `BR-XXX` (05_BRD) và `FR-XXX`/`NFR-XXX` (06_SRS) ở Đợt 2. Mỗi dòng đều gắn nhãn bằng chứng theo RULE 2.

## 1. MOD-AUTH — Xác thực & Tài khoản

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| AUTH-1 | Candidate tự đăng ký tài khoản (họ tên, email, mật khẩu, SĐT tùy chọn) | `[CONFIRMED]` | `app/routers/auth.py::register`, `app/services/auth_service.py::register_candidate` |
| AUTH-2 | Mật khẩu bắt buộc ≥8 ký tự, có ít nhất 1 chữ và 1 số | `[CONFIRMED]` | `app/schemas/auth.py::password_must_have_letter_and_digit` |
| AUTH-3 | Đăng nhập bằng email + mật khẩu, nhận Access Token (JWT) + Refresh Token | `[CONFIRMED]` | `app/services/auth_service.py::authenticate`, `issue_tokens` |
| AUTH-4 | Access Token có hạn 8 giờ | `[CONFIRMED]` | `app/core/config.py::jwt_access_token_hours` |
| AUTH-5 | Refresh Token có hạn 30 ngày, lưu dạng hash SHA-256 (không lưu plaintext) | `[CONFIRMED]` | `app/core/security.py::generate_refresh_token`, `app/models/user.py::refresh_token_hash` |
| AUTH-6 | Dùng Refresh Token để lấy Access Token mới mà không cần đăng nhập lại | `[CONFIRMED]` | `app/routers/auth.py::refresh`, `auth_service.py::refresh_access_token` |
| AUTH-7 | Xem thông tin tài khoản hiện tại | `[CONFIRMED]` | `app/routers/auth.py::me` |
| AUTH-8 | Chỉ tài khoản trạng thái ACTIVE mới đăng nhập được | `[CONFIRMED]` | `auth_service.py::authenticate` kiểm tra `UserStatus.ACTIVE` |
| AUTH-9 | Chức năng "Quên mật khẩu" / đặt lại mật khẩu | `[MISSING]` | Không tìm thấy route `/auth/forgot-password` hay tương đương |
| AUTH-10 | Xác thực email khi đăng ký (email verification) | `[MISSING]` | Không có cơ chế gửi mã xác thực/kích hoạt tài khoản |
| AUTH-11 | Chỉ vai trò CANDIDATE được tạo qua `/auth/register`; HR/HR_MANAGER/ADMIN phải qua module riêng | `[INFERRED]` | `register_candidate()` hard-code `role=UserRole.CANDIDATE`, không nhận tham số role từ client |

## 2. MOD-USER — Quản lý người dùng nội bộ

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| USER-1 | ADMIN tạo được tài khoản vai trò HR, HR_MANAGER, hoặc ADMIN | `[CONFIRMED]` | `app/routers/users.py::_ROLES_ADMIN_CAN_CREATE` |
| USER-2 | HR_MANAGER chỉ tạo được tài khoản vai trò HR | `[CONFIRMED]` | `_ROLES_HR_MANAGER_CAN_CREATE = {UserRole.HR}` |
| USER-3 | HR không có quyền tạo tài khoản nào | `[CONFIRMED]` | Endpoint yêu cầu `require_hr_manager_or_admin` — HR bị 403 |
| USER-4 | Liệt kê tài khoản nội bộ, lọc theo vai trò; không hiển thị tài khoản CANDIDATE | `[CONFIRMED]` | `list_users()` filter `User.role != UserRole.CANDIDATE` |
| USER-5 | Sửa thông tin / khóa / xóa tài khoản đã tạo | `[MISSING]` | Không có route PUT/DELETE trên `/users` |
| USER-6 | Người dùng tự đổi mật khẩu (khác với mật khẩu tạm do người tạo đặt) | `[MISSING]` | Không có route liên quan |

## 3. MOD-DEPT — Phòng ban

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| DEPT-1 | HR_MANAGER/ADMIN tạo phòng ban (tên, mô tả) | `[CONFIRMED]` | `app/routers/departments.py::create_department` |
| DEPT-2 | Mọi vai trò đã đăng nhập xem được danh sách phòng ban | `[CONFIRMED]` | `list_departments()` không giới hạn role cụ thể ngoài `get_current_user` không bắt buộc (endpoint không có dependency xác thực — xem 12_GAP) |
| DEPT-3 | Sửa/xóa phòng ban | `[MISSING]` | Không có route |

## 4. MOD-JOB — Tin tuyển dụng

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| JOB-1 | HR_MANAGER/ADMIN tạo tin tuyển dụng đầy đủ thông tin (tiêu đề, phòng ban, mô tả, yêu cầu, lương min/max, số lượng, địa điểm, hình thức làm việc) | `[CONFIRMED]` | `app/routers/jobs.py::create_job`, `app/schemas/job.py::JobCreateRequest` |
| JOB-2 | Có thể gán HR phụ trách ngay lúc tạo hoặc sau đó qua endpoint riêng | `[CONFIRMED]` | `create_job(assigned_hr_business_id)`, `assign_hr()` |
| JOB-3 | Đăng tin (chuyển PUBLISHED) trong 1 bước duy nhất | `[CONFIRMED, đơn giản hóa]` | `publish_job()` — comment trong code tự ghi nhận đây là đơn giản hóa so với quy trình duyệt nhiều bước |
| JOB-4 | Candidate chỉ xem được Job trạng thái PUBLISHED | `[CONFIRMED]` | `list_jobs()` filter theo role CANDIDATE |
| JOB-5 | Tìm kiếm theo tiêu đề, lọc theo phòng ban, lọc theo trạng thái (non-candidate) | `[CONFIRMED]` | `list_jobs(search, department_business_id, status_filter)` |
| JOB-6 | Job tự động chuyển CLOSED khi số lượng HIRED đạt đủ `quantity` | `[CONFIRMED]` | `app/services/offer_service.py::_close_job_if_quota_reached` |
| JOB-7 | Job có `slug` tự sinh dùng cho URL công khai | `[CONFIRMED một phần]` | Trường tồn tại (`app/models/job.py::slug`) nhưng **không có route nào truy cập Job theo slug** — chỉ dùng `business_id` |
| JOB-8 | Quy trình duyệt Requisition nhiều bước (DRAFT→PENDING_APPROVAL→APPROVED→PUBLISHED) | `[CONFIRMED — MISSING implementation]` | Enum `JobStatus` có đủ 6 giá trị nhưng code chỉ dùng 2 (`DRAFT`→`PUBLISHED` trực tiếp) |

## 5. MOD-APP — Hồ sơ ứng tuyển

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| APP-1 | Chỉ CANDIDATE nộp hồ sơ ứng tuyển | `[CONFIRMED]` | `apply()` kiểm tra `role != CANDIDATE` → 403 |
| APP-2 | Bắt buộc đồng ý xử lý AI (`ai_consent=true`) mới cho nộp hồ sơ | `[CONFIRMED]` | `apply()` → 400 `AI_CONSENT_REQUIRED` nếu thiếu |
| APP-3 | Chống nộp trùng ngoài ý muốn qua header `Idempotency-Key` | `[CONFIRMED]` | `apply_for_job()`, UNIQUE constraint `(candidate_id, idempotency_key)` |
| APP-4 | Không giới hạn thời gian giữa các lần ứng tuyển lại cùng 1 Job | `[CONFIRMED]` | Không có logic kiểm tra ngày tháng nào trong `apply_for_job()` |
| APP-5 | Mỗi lần ứng tuyển hợp lệ tạo bản ghi Application mới, bản ghi cũ giữ nguyên (immutable) | `[CONFIRMED]` | Luôn `INSERT`, không có `UPDATE` application cũ trong `apply_for_job()` |
| APP-6 | Dán text CV trực tiếp lúc nộp hồ sơ | `[CONFIRMED]` | `ApplyRequest.resume_text` |
| APP-7 | Upload file CV thật (PDF/DOCX) lúc nộp hoặc sau đó | `[CONFIRMED]` | `POST /applications/{id}/resume`, `app/services/resume_parser.py` |
| APP-8 | File CV giới hạn PDF/DOCX, ≤10MB, kiểm tra magic-bytes khớp phần mở rộng | `[CONFIRMED]` | `resume_parser.py::save_and_extract` |
| APP-9 | Nếu không trích xuất được text từ file (VD PDF ảnh scan), vẫn lưu file nhưng đánh dấu cần xem thủ công | `[CONFIRMED]` | `resume_service.py::upload_resume_file` set `needs_manual_review=1` |
| APP-10 | Trạng thái Application theo máy trạng thái 10 giá trị, mọi lần đổi trạng thái được validate phía server | `[CONFIRMED]` | `application_service.py::update_status`, `FORWARD_EDGES` |
| APP-11 | HR chỉ chuyển tiến (forward) hoặc sang REJECTED; không được lùi trạng thái | `[CONFIRMED]` | `update_status()` kiểm tra role khi `is_backward=True` |
| APP-12 | HR_MANAGER/ADMIN được lùi trạng thái nhưng bắt buộc nhập lý do, ghi vào Audit Log | `[CONFIRMED]` | `update_status()`, action `STATUS_REVERTED` |
| APP-13 | Candidate tự rút hồ sơ (withdraw) khi chưa có Offer | `[CONFIRMED]` | `application_service.py::withdraw`, `WITHDRAWABLE_STATUSES` |
| APP-14 | HR_MANAGER/ADMIN lưu trữ (archive) hồ sơ bất kỳ lúc nào trừ khi đã HIRED, bắt buộc chọn lý do (từ chối lưu trữ / đưa vào Talent Pool) | `[CONFIRMED]` | `application_service.py::archive` |
| APP-15 | HR chỉ xem/thao tác Application được gán (`assigned_hr_id`); HR_MANAGER/ADMIN xem toàn bộ | `[CONFIRMED]` | `list_applications()`, nhiều điểm kiểm tra rải rác |
| APP-16 | `assigned_hr_id` của Application tự kế thừa từ Job lúc tạo hồ sơ | `[CONFIRMED]` | `apply_for_job(assigned_hr_id=job.assigned_hr_id)` |
| APP-17 | Tìm kiếm theo tên/email/SĐT ứng viên, lọc theo Job | `[CONFIRMED]` | `list_applications(job_business_id, search)` |
| APP-18 | Không có chức năng xóa vật lý Application | `[CONFIRMED, tích cực]` | Không tìm thấy route DELETE nào trên `/applications` |
| APP-19 | Candidate trùng email (đã tồn tại từ lần nộp trước) được tái sử dụng, không tạo bản ghi Candidate trùng | `[CONFIRMED]` | `_get_or_create_candidate()` |
| APP-20 | Lên lịch phỏng vấn, ghi kết quả phỏng vấn qua API riêng | `[MISSING]` | Model `interviews` tồn tại, **không có router `interview.py`** |

## 6. MOD-OFFER — Thư mời nhận việc

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| OFFER-1 | HR+ tạo Offer (lương chính thức, lương thử việc, ngày bắt đầu) cho 1 Application | `[CONFIRMED]` | `offer_service.py::create_offer` |
| OFFER-2 | Offer phải qua bước "Nộp duyệt" (Submit) trước khi được duyệt | `[CONFIRMED]` | `submit_offer()`, `OfferStatus.DRAFT → PENDING_APPROVAL` |
| OFFER-3 | Người duyệt Offer bắt buộc khác người tạo (4-eyes approval) | `[CONFIRMED — 2 lớp]` | Service: `approve_offer()` kiểm tra `actor.id == offer.creator_id`; DB: `CheckConstraint ck_offer_approver_not_creator` |
| OFFER-4 | Chỉ HR_MANAGER/ADMIN được duyệt/từ chối Offer | `[CONFIRMED]` | `require_offer_approver = require_roles(HR_MANAGER, ADMIN)` |
| OFFER-5 | Offer bị từ chối duyệt quay về DRAFT (không phải trạng thái kết thúc), bắt buộc nhập lý do | `[CONFIRMED]` | `reject_offer()` |
| OFFER-6 | Chỉ gửi (Send) được Offer khi đã APPROVED | `[CONFIRMED]` | `send_offer()` kiểm tra `OfferStatus.APPROVED` |
| OFFER-7 | Offer có hạn phản hồi (mặc định 7 ngày kể từ lúc gửi, cấu hình qua `.env`) | `[CONFIRMED]` | `send_offer()`, `settings.offer_validity_days` |
| OFFER-8 | Candidate phản hồi Accept/Decline, chỉ với Offer của chính mình | `[CONFIRMED]` | `respond_offer()`, kiểm tra chủ sở hữu ở router |
| OFFER-9 | Accept → Application chuyển HIRED, tự kiểm tra và đóng Job nếu đủ quota | `[CONFIRMED]` | `respond_offer()` → `_close_job_if_quota_reached()` |
| OFFER-10 | Decline → Application chuyển REJECTED | `[CONFIRMED]` | `respond_offer()` |
| OFFER-11 | Tự động chuyển Offer quá hạn sang EXPIRED (và Application → REJECTED) | `[CONFIRMED logic, MISSING lịch chạy]` | Hàm `expire_due_offers()` tồn tại và có test, nhưng không được gọi tự động ở đâu (không có APScheduler wiring trong `app/main.py`) |
| OFFER-12 | Chỉ Candidate liên quan, HR được gán/người tạo, hoặc HR_MANAGER/ADMIN mới xem được 1 Offer cụ thể | `[CONFIRMED]` | `_check_can_view_offer()` |

## 7. MOD-EMAIL — Email Tự động

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| EMAIL-1 | HR_MANAGER/ADMIN tạo/sửa mẫu Email; HR chỉ xem | `[CONFIRMED]` | `email_templates.py::create_template` (`require_hr_manager_or_admin`), `list_templates` (`require_hr_or_above`) |
| EMAIL-2 | "Xóa" mẫu Email thực chất là vô hiệu hóa (soft-delete), không xóa vật lý | `[CONFIRMED]` | `deactivate_template()` chỉ đổi `status=INACTIVE` |
| EMAIL-3 | Mỗi mẫu gắn với đúng 1 trong 7 loại sự kiện cố định | `[CONFIRMED]` | `EmailTemplateType` enum (7 giá trị) |
| EMAIL-4 | Nội dung mẫu hỗ trợ biến `{{ten_bien}}`, được thay thế lúc gửi | `[CONFIRMED]` | `email_service.py::render_template` |
| EMAIL-5 | HR+ gửi email thủ công tới ứng viên của 1 Application, chọn mẫu có sẵn | `[CONFIRMED]` | `POST /email-templates/send/{id}` |
| EMAIL-6 | Tự động gửi khi: nộp hồ sơ, chuyển SHORTLISTED, chuyển INTERVIEW, chuyển REJECTED, gửi Offer, Candidate Accept Offer | `[CONFIRMED]` | `trigger_stage_email()` được gọi từ `application_service.py` và `offer_service.py` tại các điểm tương ứng |
| EMAIL-7 | Nếu chưa có mẫu ACTIVE cho loại sự kiện, bỏ qua im lặng, không gây lỗi giao dịch chính | `[CONFIRMED]` | `trigger_stage_email()` return sớm nếu `template is None` |
| EMAIL-8 | Gửi thật qua SMTP nếu có cấu hình; ngược lại ghi log giả lập | `[CONFIRMED]` | `email_service.py::_is_smtp_configured`, `send_raw_email` |
| EMAIL-9 | Không có bảng log gửi email riêng — dùng chung `audit_logs` | `[CONFIRMED]` | `send_email()` gọi `audit_service.log(entity_type="application"...)` |
| EMAIL-10 | Xem lại nội dung đầy đủ (đã render) của email đã gửi trước đó | `[MISSING]` | `audit_logs.after_data` chỉ lưu `{to, subject}`, không lưu `body` |

## 8. MOD-AI — AI Screening

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| AI-1 | HR+ kích hoạt phân tích AI cho 1 Application, so sánh CV với JD của Job | `[CONFIRMED]` | `ai_service.py::run_screening` |
| AI-2 | HR chỉ phân tích được Application được gán cho mình | `[CONFIRMED]` | `ai.py::_check_scope` |
| AI-3 | Nếu chưa có text CV, trả `202 Accepted` + cờ cần xem thủ công thay vì báo lỗi | `[CONFIRMED]` | `ai.py::analyze` |
| AI-4 | Gọi AI Provider thật (Gemini hoặc Claude, chọn qua `AI_PROVIDER`) nếu có `AI_API_KEY`; nếu lỗi, thử lại 1 lần; nếu vẫn lỗi hoặc chưa cấu hình, dùng chế độ so khớp từ khóa nội bộ. **[CẬP NHẬT sau STEP 1]** Ban đầu chỉ hỗ trợ Gemini (`_call_gemini`); đã tổng quát hóa thành kiến trúc đa provider (`PROVIDER_CALLERS`), hiện cấu hình dùng Claude | `[CONFIRMED]` | `ai_service.py::_call_ai_provider`, `_call_gemini`, `_call_claude`, `_stub_analysis` |
| AI-5 | Giữ toàn bộ lịch sử các lần phân tích (không ghi đè), đánh dấu bản mới nhất qua cờ `is_latest` | `[CONFIRMED]` | `run_screening()` update `is_latest=False` cho bản cũ trước khi insert |
| AI-6 | Kết quả AI (điểm số) không tự động quyết định số phận hồ sơ — chỉ chuyển trạng thái kỹ thuật NEW/AI_SCREENING → SCREENING, các bước tiếp theo (Shortlist/Reject) vẫn do HR quyết định thủ công | `[CONFIRMED]` | `run_screening()` chỉ set status nếu đang ở NEW/AI_SCREENING |
| AI-7 | Giới hạn chi phí gọi AI theo tháng (cost cap) | `[MISSING]` | Có field cấu hình `AI_MONTHLY_BUDGET_CAP_USD` nhưng không có logic đếm/chặn nào trong code |
| AI-8 | Candidate xem được kết quả phân tích AI về hồ sơ của mình | `[CONFIRMED — không cho phép]` | Không có endpoint AI nào mở cho role CANDIDATE (`require_hr_or_above` trên cả 2 route) |

## 9. MOD-DASH — Dashboard

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| DASH-1 | Xem số liệu tổng hợp: tổng Job/Job đã đăng, tổng Application, phân bố theo trạng thái, số đã tuyển, tỷ lệ nhận Offer, thời gian tuyển trung bình, phân bố theo nguồn | `[CONFIRMED]` | `dashboard.py::get_summary`, `DashboardSummaryOut` |
| DASH-2 | HR_MANAGER/ADMIN thấy thêm bảng hiệu suất từng nhân viên HR | `[CONFIRMED]` | `get_summary()` chỉ tính `hr_performance` khi role ∈ {HR_MANAGER, ADMIN} |
| DASH-3 | HR chỉ xem số liệu trong phạm vi Job/Application được gán | `[CONFIRMED]` | `get_summary()` filter theo `assigned_hr_id` khi role=HR |
| DASH-4 | Candidate không truy cập được Dashboard | `[CONFIRMED]` | `require_hr_or_above` |

## 10. MOD-AUDIT — Nhật ký Audit

| # | Yêu cầu quan sát được | Nhãn | Bằng chứng |
|---|---|---|---|
| AUDIT-1 | Ghi log cho các hành động nhạy cảm được chọn lọc (không ghi mọi thao tác CRUD) | `[CONFIRMED]` | Comment trong `app/models/audit_log.py`/thiết kế; các lệnh gọi `audit_service.log()` rải rác trong service, không có ở mọi hàm |
| AUDIT-2 | Xem log, lọc theo loại đối tượng (`entity_type`) và mã đối tượng (`entity_business_id`) | `[CONFIRMED]` | `audit.py::list_audit_logs` |
| AUDIT-3 | Chỉ HR_MANAGER/ADMIN xem được Audit Log | `[CONFIRMED]` | `require_hr_manager_or_admin` |

---

## 11. Non-functional Requirements — quan sát sơ bộ (chi tiết hóa thành `NFR-XXX` ở 06_SRS)

| Nhóm | Quan sát | Nhãn |
|---|---|---|
| Security | JWT + Refresh Token; mật khẩu hash bằng bcrypt (`passlib`); RBAC theo role + phạm vi dữ liệu; validate file upload (magic-bytes); CHECK constraint DB cho bất biến nghiệp vụ quan trọng (4-eyes) | `[CONFIRMED]` |
| Security | CORS cấu hình `allow_origins=["*"]` kèm `allow_credentials=True` — tổ hợp không hợp lệ theo chuẩn CORS của trình duyệt nếu dùng cookie, hiện không gây lỗi vì frontend dùng Bearer token chứ không dùng cookie | `[CONFIRMED — điểm cần lưu ý]` |
| Security | Antivirus scan cho file upload | `[MISSING]` |
| Reliability | Cơ chế retry (AI) + graceful degradation (AI, Email) khi dịch vụ ngoài lỗi/chưa cấu hình | `[CONFIRMED]` |
| Reliability | Offer tự động hết hạn — logic có sẵn nhưng không có lịch chạy nền | `[CONFIRMED một phần]` |
| Data Integrity | State machine validate server-side; UNIQUE/CHECK constraint ở DB; sinh Business ID an toàn với truy cập đồng thời (row lock) | `[CONFIRMED]` |
| Maintainability | Kiến trúc phân lớp rõ ràng; 48 test tự động (pytest) + 3 script E2E; đặt tên nhất quán (Business ID có tiền tố theo entity) | `[CONFIRMED]` |
| Auditability | Bảng `audit_logs` ghi actor, action, before/after data cho hành động nhạy cảm | `[CONFIRMED]` |
| Performance | Benchmark, chỉ số thời gian phản hồi, chiến lược cache | `[MISSING]` |
| Scalability | Kiểm thử tải, cấu hình chạy nhiều instance, connection pooling nâng cao | `[MISSING]` |
| Availability | SLA, cơ chế tự khởi động lại, giám sát uptime | `[MISSING]` |
| Usability | Giao diện có responsive layout cơ bản (class Tailwind `sm:`/`lg:` xuất hiện trong `index.html`) | `[CONFIRMED một phần]` |
| Compatibility | Kiểm thử đa trình duyệt | `[MISSING]` |
| Monitoring | Có endpoint `/health` đơn giản; không có APM, không có structured logging tập trung | `[CONFIRMED một phần / MISSING phần còn lại]` |
| Logging | Không có logging framework riêng (VD Python `logging` module có cấu hình) ngoài `audit_logs` (là audit trail nghiệp vụ, không phải application log kỹ thuật) | `[MISSING]` cho application-level logging |

---

*Kết thúc Đợt 1. Tài liệu tiếp theo (Đợt 2): `05_BRD.md`, `06_SRS.md`, `07_USER_ROLE_PERMISSION.md`.*
