# 12 — USE CASE SPECIFICATION — ATS v2.1

Đặc tả chi tiết toàn bộ 37 Use Case đã liệt kê ở `11_USE_CASE.md`, theo template chuẩn: Actor, Tiền điều kiện, Luồng chính, Luồng thay thế/ngoại lệ, Hậu điều kiện, Business Rule, Tham chiếu. Nguồn bằng chứng cho mọi bước: `app/routers/*.py`, `app/services/*.py` (đã trích dẫn cụ thể ở `08`/`09`, không lặp lại đường dẫn dòng ở đây để tránh trùng lặp — xem 2 file đó khi cần đối chiếu dòng code).

---

## MOD-AUTH

### UC-AUTH-001 — Đăng ký tài khoản
- **Actor**: ACT-CANDIDATE (chưa có tài khoản)
- **Tiền điều kiện**: Email chưa từng đăng ký
- **Luồng chính**: (1) Người dùng nhập họ tên, email, mật khẩu, SĐT (tùy chọn). (2) Hệ thống kiểm tra định dạng mật khẩu (≥8 ký tự, có chữ+số). (3) Hệ thống kiểm tra email chưa tồn tại. (4) Hệ thống băm mật khẩu, tạo `User` role=CANDIDATE. (5) Hệ thống phát Access Token + Refresh Token, trả về.
- **Luồng thay thế/ngoại lệ**: 2a. Mật khẩu không đạt chuẩn → `422`, dừng. 3a. Email đã tồn tại → `409 EMAIL_ALREADY_REGISTERED`, dừng.
- **Hậu điều kiện**: 1 `User` mới ở trạng thái `ACTIVE`, đã đăng nhập sẵn (có token).
- **Business Rule**: Vai trò luôn bị ép cứng = CANDIDATE, client không chọn được.
- **Tham chiếu**: FN-AUTH-01, FR-AUTH-001, FR-AUTH-002.

### UC-AUTH-002 — Đăng nhập
- **Actor**: Tất cả (bất kỳ ai có tài khoản)
- **Tiền điều kiện**: Tài khoản tồn tại
- **Luồng chính**: (1) Nhập email + mật khẩu. (2) Hệ thống tra `User` theo email. (3) Xác thực mật khẩu bằng bcrypt. (4) Kiểm tra `status = ACTIVE`. (5) Phát token, lưu hash refresh token vào DB.
- **Luồng thay thế/ngoại lệ**: 2a/3a. Email/mật khẩu sai → `401`, dừng. 4a. Tài khoản `INACTIVE`/`LOCKED` → `403`, dừng.
- **Hậu điều kiện**: Client nhận cặp token hợp lệ.
- **Business Rule**: Chỉ tài khoản `ACTIVE` đăng nhập được (AUTH-8).
- **Tham chiếu**: FN-AUTH-02, FR-AUTH-003, FR-AUTH-008.

### UC-AUTH-003 — Làm mới Access Token
- **Actor**: Tất cả
- **Tiền điều kiện**: Có Refresh Token còn hiệu lực (≤30 ngày) từ lần đăng nhập trước
- **Luồng chính**: (1) Gửi `refresh_token`. (2) Hệ thống băm SHA-256, so khớp với `refresh_token_hash` đã lưu. (3) Kiểm tra chưa hết hạn. (4) Phát Access Token mới.
- **Luồng thay thế/ngoại lệ**: 2a/3a. Không khớp hoặc hết hạn → `401 INVALID_REFRESH_TOKEN`.
- **Hậu điều kiện**: Access Token mới, phiên đăng nhập được duy trì không cần nhập lại mật khẩu.
- **Tham chiếu**: FN-AUTH-03, FR-AUTH-006.

### UC-AUTH-004 — Xem hồ sơ tài khoản hiện tại
- **Actor**: Tất cả (đã đăng nhập)
- **Tiền điều kiện**: Access Token hợp lệ trong header
- **Luồng chính**: (1) Gửi request với Bearer token. (2) Hệ thống giải mã, tra `User`. (3) Trả thông tin tài khoản.
- **Luồng thay thế/ngoại lệ**: 2a. Token thiếu/hỏng/hết hạn → `401`.
- **Hậu điều kiện**: Không đổi trạng thái hệ thống (read-only).
- **Tham chiếu**: FN-AUTH-04, FR-AUTH-007.

## MOD-USER

### UC-USER-001 — Tạo tài khoản nội bộ
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: Actor đã đăng nhập với vai trò phù hợp
- **Luồng chính**: (1) Actor nhập họ tên, email, mật khẩu, `role`, phòng ban (tùy chọn). (2) Hệ thống kiểm tra `role` hợp lệ. (3) Kiểm tra actor được phép tạo `role` đó (HR_MANAGER→chỉ `HR`; ADMIN→`HR`/`HR_MANAGER`/`ADMIN`). (4) Kiểm tra email chưa tồn tại. (5) Tạo `User` trạng thái `ACTIVE`.
- **Luồng thay thế/ngoại lệ**: 2a. Role không hợp lệ → `400`. 3a. Không được phép tạo role này → `403 NOT_ALLOWED_TO_CREATE_THIS_ROLE`. 4a. Email trùng → `409`. Nếu truyền `department_business_id` không tồn tại → `404`.
- **Hậu điều kiện**: 1 tài khoản nội bộ mới, `status=ACTIVE` ngay (không cần kích hoạt email — đối lập AUTH-10 vốn `[MISSING]`).
- **Business Rule**: Ma trận tạo-role phân biệt theo actor (USER-1, USER-2).
- **Tham chiếu**: FN-USER-01, FR-USER-001..003.

### UC-USER-002 — Danh sách tài khoản nội bộ
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: —
- **Luồng chính**: (1) Actor gọi danh sách, có thể kèm filter `role`. (2) Hệ thống loại trừ `role=CANDIDATE`, áp filter nếu có. (3) Trả danh sách.
- **Luồng thay thế/ngoại lệ**: 2a. `role` filter không hợp lệ → `400`.
- **Hậu điều kiện**: Read-only. `ACT-HR` bị từ chối (`403`) — không có luồng thay thế cho HR vì đây là giới hạn tuyệt đối theo thiết kế.
- **Tham chiếu**: FN-USER-02, FR-USER-004.

## MOD-DEPT

### UC-DEPT-001 — Tạo phòng ban
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Nhập tên, mô tả. (2) Hệ thống tạo `Department` với Business ID tiền tố `DEP`.
- **Hậu điều kiện**: 1 phòng ban mới, có thể gán cho Job/User.
- **Tham chiếu**: FN-DEPT-01, FR-DEPT-001.

### UC-DEPT-002 — Danh sách phòng ban
- **Actor**: Công khai (không yêu cầu xác thực — xem Gap ở `07` mục 3.3)
- **Luồng chính**: (1) Gọi danh sách. (2) Hệ thống trả toàn bộ `Department`, không phân trang, không lọc.
- **Hậu điều kiện**: Read-only.
- **Tham chiếu**: FN-DEPT-02, FR-DEPT-002.

## MOD-JOB

### UC-JOB-001 — Tạo tin tuyển dụng
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Nhập tiêu đề, phòng ban, mô tả, yêu cầu, khoảng lương, số lượng, địa điểm, hình thức làm việc, HR phụ trách (tùy chọn). (2) Hệ thống tạo `Job` trạng thái `DRAFT`, tự sinh `slug`.
- **Luồng thay thế/ngoại lệ**: Phòng ban không tồn tại → `404`.
- **Hậu điều kiện**: 1 tin ở trạng thái `DRAFT`, chưa hiển thị cho Candidate.
- **Include**: có thể gọi UC-JOB-002 ngay trong cùng request (`assigned_hr_business_id`) hoặc thực hiện riêng sau.
- **Tham chiếu**: FN-JOB-01, FR-JOB-001.

### UC-JOB-002 — Gán HR phụ trách
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: Job tồn tại; User đích có `role=HR`
- **Luồng chính**: (1) Chọn Job + HR. (2) Hệ thống cập nhật `Job.assigned_hr_id`.
- **Luồng thay thế/ngoại lệ**: User không tồn tại/không phải HR → `400`/`404`.
- **Hậu điều kiện**: Mọi Application nộp sau đó cho Job này tự kế thừa `assigned_hr_id` (APP-16).
- **Tham chiếu**: FN-JOB-02, FR-JOB-002.

### UC-JOB-003 — Đăng tin
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: Job đang `DRAFT`
- **Luồng chính**: (1) Chọn "Đăng tin". (2) Hệ thống chuyển `DRAFT → PUBLISHED`, ghi `approved_by`.
- **Luồng thay thế/ngoại lệ**: Job không ở `DRAFT` → `409`.
- **Hậu điều kiện**: Candidate bắt đầu thấy tin trong danh sách công khai.
- **Business Rule**: Đơn giản hóa 1 bước, không qua `PENDING_APPROVAL`/`APPROVED` (Gap JOB-8).
- **Tham chiếu**: FN-JOB-03, FR-JOB-003.

### UC-JOB-004 — Danh sách tin tuyển dụng
- **Actor**: Đã đăng nhập (mọi vai trò)
- **Luồng chính**: (1) Gọi danh sách kèm `search`/`department_business_id`/`status_filter` (tùy chọn). (2) Nếu actor=CANDIDATE, hệ thống ép lọc `status=PUBLISHED`, bỏ qua `status_filter` client gửi. (3) Trả danh sách.
- **Luồng thay thế/ngoại lệ**: `status_filter` không hợp lệ (non-Candidate) → `400`.
- **Tham chiếu**: FN-JOB-04, FR-JOB-004, FR-JOB-005.

### UC-JOB-005 — Xem chi tiết 1 tin
- **Actor**: Công khai (không xác thực)
- **Luồng chính**: (1) Gọi theo `business_id`. (2) Hệ thống trả toàn bộ thông tin Job, **không kiểm tra `status`**.
- **Luồng thay thế/ngoại lệ**: Không tồn tại → `404`.
- **Ghi chú Gap**: Không lọc `status` → có thể lộ tin `DRAFT`/`CLOSED` cho người chưa đăng nhập (Gap G-07-1, `07` mục 4).
- **Tham chiếu**: FN-JOB-05, FR-JOB-004 (không đầy đủ).

## MOD-APP

### UC-APP-001 — Nộp hồ sơ ứng tuyển
- **Actor**: ACT-CANDIDATE
- **Tiền điều kiện**: Job đang `PUBLISHED`
- **Luồng chính**: (1) Candidate chọn Job, xác nhận `ai_consent=true`, điền thông tin liên hệ, tùy chọn dán CV text hoặc gửi kèm `Idempotency-Key`. (2) Hệ thống kiểm tra Job hợp lệ. (3) Kiểm tra trùng `Idempotency-Key` — nếu trùng, trả bản ghi cũ (dừng ở đây, xem luồng thay thế). (4) Tìm/tạo `Candidate` (dedupe email). (5) Tạo `Application` mới `status=NEW`, kế thừa `assigned_hr_id`. (6) Nếu có CV text, lưu `Resume`. (7) Ghi audit. (8) Kích hoạt email `APPLICATION_RECEIVED`.
- **Luồng thay thế/ngoại lệ**: 1a. `ai_consent=false` → `400 AI_CONSENT_REQUIRED`. 2a. Job không tồn tại/không `PUBLISHED` → `404`. 3a. Trùng Idempotency-Key → trả `Application` cũ, `is_new=false`, không tạo bản ghi mới, ghi audit `APPLICATION_DUPLICATE_REQUEST`, **kết thúc use case tại đây** (bỏ qua bước 4-8).
- **Hậu điều kiện**: 1 `Application` mới `status=NEW` (hoặc trả về bản ghi cũ nếu trùng key).
- **Include**: UC-APP-004 (tùy chọn, có thể thực hiện ngay hoặc sau).
- **Business Rule**: Không giới hạn tái ứng tuyển (BRULE-02); mỗi lần nộp hợp lệ luôn tạo bản ghi mới, không ghi đè (APP-5).
- **Tham chiếu**: FN-APP-01, FR-APP-001..006.

### UC-APP-002 — Danh sách hồ sơ ứng tuyển
- **Actor**: Đã đăng nhập (mọi vai trò)
- **Luồng chính**: (1) Gọi danh sách kèm `job_business_id`/`search` (tùy chọn). (2) Hệ thống áp phạm vi theo vai trò: HR→chỉ `assigned_hr_id=mình`; CANDIDATE→chỉ hồ sơ của mình; HR_MANAGER/ADMIN→toàn bộ. (3) Áp filter bổ sung. (4) Trả danh sách.
- **Business Rule**: Row-level scope theo APP-15.
- **Tham chiếu**: FN-APP-02, FR-APP-015, FR-APP-017.

### UC-APP-003 — Xem chi tiết 1 hồ sơ
- **Actor**: Đã đăng nhập (mọi vai trò)
- **Luồng chính**: (1) Gọi theo `business_id`. (2) Nếu actor=CANDIDATE, kiểm tra sở hữu. (3) Trả chi tiết.
- **Luồng thay thế/ngoại lệ**: Không tồn tại → `404`. CANDIDATE không sở hữu → `403 NOT_YOUR_APPLICATION`.
- **Ghi chú Gap**: Với actor=HR, **không có bước kiểm tra `assigned_hr_id`** — khác UC-APP-002 (Gap G-07-2, `07` mục 4).
- **Tham chiếu**: FN-APP-03, FR-APP-015 (không đầy đủ).

### UC-APP-004 — Tải lên CV
- **Actor**: ACT-CANDIDATE (chủ hồ sơ)
- **Tiền điều kiện**: Application đã tồn tại (đã thực hiện UC-APP-001)
- **Luồng chính**: (1) Chọn file PDF/DOCX. (2) Hệ thống kiểm tra chủ sở hữu. (3) Xác thực kích thước ≤10MB, magic-bytes khớp extension. (4) Trích xuất text. (5) Lưu file + bản ghi `Resume`.
- **Luồng thay thế/ngoại lệ**: 2a. Không phải chủ sở hữu → `403`. 3a. Sai định dạng/quá lớn → `400`. 4a. Trích xuất thất bại (VD PDF scan ảnh) → vẫn lưu file, đặt `needs_manual_review=1`, **không báo lỗi cho người dùng**.
- **Hậu điều kiện**: `Application.has_resume = true`.
- **Tham chiếu**: FN-APP-04, FR-APP-007..009.

### UC-APP-005 — Đổi trạng thái hồ sơ
- **Actor**: ACT-HR (chỉ chuyển tiến), ACT-HR-MANAGER/ACT-ADMIN (chuyển tiến hoặc lùi)
- **Luồng chính**: (1) Actor chọn trạng thái đích. (2) Hệ thống xác định là cạnh tiến hay lùi theo `FORWARD_EDGES`/`PIPELINE_ORDER`. (3a. Tiến) Kiểm tra actor ∈ {HR, HR_MANAGER, ADMIN} → cập nhật → kích hoạt email nếu đích ∈ {SHORTLISTED, INTERVIEW, REJECTED}. (3b. Lùi, xem Extend) Kiểm tra actor ∈ {HR_MANAGER, ADMIN} và có `reason` → cập nhật, ghi audit `STATUS_REVERTED`, **không** kích hoạt email.
- **Luồng thay thế/ngoại lệ**: Cạnh không hợp lệ (không tiến không lùi hợp lệ) → `409 INVALID_STATUS_TRANSITION`. HR cố lùi → `403`. Lùi thiếu `reason` → `400`.
- **Extend**: "Lùi trạng thái" (chỉ HR_MANAGER/ADMIN, bắt buộc `reason`).
- **Business Rule**: HR không set trực tiếp được `OFFER`/`HIRED` (chỉ qua BP-OFFER-001).
- **Tham chiếu**: FN-APP-05, FR-APP-010..012.

### UC-APP-006 — Rút hồ sơ
- **Actor**: ACT-CANDIDATE (chủ hồ sơ)
- **Tiền điều kiện**: Trạng thái ∈ {NEW, AI_SCREENING, SCREENING, SHORTLISTED, INTERVIEW} (trước khi có Offer)
- **Luồng chính**: (1) Candidate chọn rút hồ sơ. (2) Hệ thống kiểm tra sở hữu + trạng thái hợp lệ. (3) Chuyển `WITHDRAWN`.
- **Luồng thay thế/ngoại lệ**: Không sở hữu → `403`. Trạng thái không hợp lệ (VD đã có Offer) → `409 CANNOT_WITHDRAW_FROM_STATUS`.
- **Tham chiếu**: FN-APP-06, FR-APP-013.

### UC-APP-007 — Lưu trữ hồ sơ
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: Trạng thái ≠ `HIRED`
- **Luồng chính**: (1) Actor chọn `archive_reason` (`REJECTED_ARCHIVE`/`TALENT_POOL`). (2) Hệ thống chuyển `ARCHIVED`.
- **Luồng thay thế/ngoại lệ**: Đang `HIRED` → `409 CANNOT_ARCHIVE_HIRED_APPLICATION`. `archive_reason` không hợp lệ → `400`.
- **Business Rule**: BRULE-04.
- **Tham chiếu**: FN-APP-07, FR-APP-014.

## MOD-OFFER

### UC-OFFER-001 — Danh sách Offer
- **Actor**: Đã đăng nhập
- **Luồng chính**: (1) Gọi kèm `application_business_id`/`status` (tùy chọn). (2) Hệ thống áp phạm vi theo vai trò (giống Application). (3) Trả danh sách.
- **Luồng thay thế/ngoại lệ**: CANDIDATE không truyền `application_business_id` → `400`.
- **Tham chiếu**: FN-OFFER-01, FR-OFFER-012.

### UC-OFFER-002 — Tạo Offer
- **Actor**: ACT-HR trở lên
- **Tiền điều kiện**: Application tồn tại
- **Luồng chính**: (1) Nhập lương, lương thử việc, ngày bắt đầu. (2) Hệ thống tạo `Offer` `status=DRAFT`, `creator_id=actor`.
- **Tham chiếu**: FN-OFFER-02, FR-OFFER-001.

### UC-OFFER-003 — Nộp duyệt Offer
- **Actor**: Chủ Offer, hoặc ACT-HR-MANAGER/ACT-ADMIN
- **Tiền điều kiện**: Offer đang `DRAFT`
- **Luồng chính**: (1) Actor nộp duyệt. (2) Hệ thống chuyển `DRAFT → PENDING_APPROVAL`.
- **Luồng thay thế/ngoại lệ**: Không ở `DRAFT` → `409`.
- **Tham chiếu**: FN-OFFER-03, FR-OFFER-002.

### UC-OFFER-004 — Duyệt Offer
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN (khác người tạo)
- **Tiền điều kiện**: Offer đang `PENDING_APPROVAL`
- **Luồng chính**: (1) Actor duyệt. (2) Hệ thống kiểm tra `actor.id != offer.creator_id`. (3) Chuyển `APPROVED`, ghi `approver_id`.
- **Luồng thay thế/ngoại lệ (Extend "Chặn tự duyệt")**: 2a. `actor.id == creator_id` → ghi audit `OFFER_SELF_APPROVAL_BLOCKED`, trả `409 OFFER_SELF_APPROVAL_NOT_ALLOWED`, **không** đổi trạng thái Offer.
- **Business Rule**: BRULE-01 (4-eyes), thực thi kép service + DB CheckConstraint.
- **Tham chiếu**: FN-OFFER-04, FR-OFFER-003, FR-OFFER-004.

### UC-OFFER-005 — Từ chối duyệt Offer
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Tiền điều kiện**: Offer đang `PENDING_APPROVAL`
- **Luồng chính**: (1) Actor nhập `reason`. (2) Hệ thống chuyển `PENDING_APPROVAL → DRAFT` (không phải trạng thái kết thúc), ghi `rejection_reason`.
- **Luồng thay thế/ngoại lệ**: Thiếu `reason` → `400 REJECTION_REASON_REQUIRED`.
- **Hậu điều kiện**: Offer quay lại `DRAFT`, có thể nộp duyệt lại (UC-OFFER-003).
- **Tham chiếu**: FN-OFFER-05, FR-OFFER-005.

### UC-OFFER-006 — Gửi Offer
- **Actor**: ACT-HR trở lên
- **Tiền điều kiện**: Offer đang `APPROVED`
- **Luồng chính**: (1) Actor gửi. (2) Hệ thống chuyển `SENT`, tính `expires_at`, chuyển `Application.status=OFFER`. (3) Kích hoạt email `OFFER`.
- **Luồng thay thế/ngoại lệ**: Không ở `APPROVED` → `409`.
- **Tham chiếu**: FN-OFFER-06, FR-OFFER-006, FR-OFFER-007.

### UC-OFFER-007 — Ứng viên phản hồi Offer
- **Actor**: ACT-CANDIDATE (chủ Offer)
- **Tiền điều kiện**: Offer đang `SENT`
- **Luồng chính (Accept)**: (1) Candidate Accept. (2) Offer→`ACCEPTED`, Application→`HIRED`. (3) Kiểm tra tự đóng Job. (4) Kích hoạt email `ONBOARDING`.
- **Luồng thay thế (Decline)**: (1) Candidate Decline. (2) Offer→`DECLINED`, Application→`REJECTED`.
- **Luồng ngoại lệ**: Offer không ở `SENT` → `409 OFFER_NOT_SENT`. Giá trị `response` không hợp lệ → `400`.
- **Tham chiếu**: FN-OFFER-07, FR-OFFER-008..010.

### UC-OFFER-008 — Xem chi tiết 1 Offer
- **Actor**: Đã đăng nhập
- **Luồng chính**: (1) Gọi theo `business_id`. (2) Hệ thống thực thi `_check_can_view_offer` theo vai trò. (3) Trả chi tiết.
- **Luồng thay thế/ngoại lệ**: Không tồn tại → `404`. Ngoài phạm vi → `403`.
- **Tham chiếu**: FN-OFFER-08, FR-OFFER-012.

## MOD-EMAIL

### UC-EMAIL-001 — Tạo mẫu Email
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Nhập tên, chọn 1/7 loại sự kiện, tiêu đề, nội dung (có thể chứa biến `{{}}`). (2) Hệ thống tạo `EmailTemplate` `status=ACTIVE`.
- **Luồng thay thế/ngoại lệ**: Loại sự kiện không hợp lệ → `400`.
- **Tham chiếu**: FN-EMAIL-01, FR-EMAIL-001, FR-EMAIL-003.

### UC-EMAIL-002 — Danh sách mẫu Email
- **Actor**: ACT-HR trở lên
- **Luồng chính**: (1) Gọi danh sách. (2) Hệ thống trả toàn bộ mẫu (cả `ACTIVE` lẫn `INACTIVE`).
- **Tham chiếu**: FN-EMAIL-02, FR-EMAIL-001.

### UC-EMAIL-003 — Sửa mẫu Email
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Chọn mẫu, sửa 1 hoặc nhiều trường. (2) Hệ thống cập nhật từng phần.
- **Luồng thay thế/ngoại lệ**: Không tồn tại → `404`.
- **Tham chiếu**: FN-EMAIL-03, FR-EMAIL-001.

### UC-EMAIL-004 — Vô hiệu hóa mẫu Email
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Chọn "Xóa" mẫu. (2) Hệ thống đặt `status=INACTIVE` (soft-delete, không xóa vật lý).
- **Tham chiếu**: FN-EMAIL-04, FR-EMAIL-002.

### UC-EMAIL-005 — Gửi Email thủ công
- **Actor**: ACT-HR trở lên
- **Luồng chính**: (1) Chọn Application + mẫu. (2) Hệ thống render biến (`candidate_name`, `job_title`, `company_name`). (3) Gửi qua SMTP (thật/giả lập). (4) Ghi audit.
- **Luồng thay thế/ngoại lệ**: Application/Template không tồn tại → `404`.
- **Ghi chú Gap**: Không kiểm tra `assigned_hr_id` cho actor=HR (Gap G-07-3).
- **Tham chiếu**: FN-EMAIL-05, FR-EMAIL-004/005/008/009.

## MOD-AI

### UC-AI-001 — Phân tích AI Screening
- **Actor**: ACT-HR (trong phạm vi được gán), ACT-HR-MANAGER/ACT-ADMIN (không giới hạn)
- **Luồng chính**: (1) Actor chọn Application, kích hoạt phân tích. (2) Hệ thống kiểm tra phạm vi. (3) Lấy text CV mới nhất. (4) Gọi AI Provider đã cấu hình — Gemini hoặc Claude, chọn qua `AI_PROVIDER` — hoặc fallback từ khóa. (5) Lưu `AIAnalysis` mới `is_latest=true`, các bản cũ→`false`. (6) Nếu status ∈ {NEW, AI_SCREENING}, tự chuyển `SCREENING`.
- **Luồng thay thế/ngoại lệ**: 2a. Ngoài phạm vi HR → `403`. 3a. Không có text CV → `202 Accepted` + `needs_manual_review=true`, dừng (bỏ qua bước 4-6). 4a. AI Provider lỗi → thử lại 1 lần → nếu vẫn lỗi, dùng fallback (Include "Gọi AI Provider/Fallback").
- **Business Rule**: AI-6 — không tự Shortlist/Reject.
- **Tham chiếu**: FN-AI-01, FR-AI-001..006.

### UC-AI-002 — Lịch sử phân tích AI
- **Actor**: ACT-HR (phạm vi được gán), ACT-HR-MANAGER/ACT-ADMIN
- **Luồng chính**: (1) Gọi lịch sử theo Application. (2) Hệ thống trả toàn bộ `AIAnalysis`, mới nhất trước.
- **Luồng thay thế/ngoại lệ**: Ngoài phạm vi HR → `403`.
- **Tham chiếu**: FN-AI-02, FR-AI-005.

## MOD-DASH

### UC-DASH-001 — Xem số liệu tổng hợp
- **Actor**: ACT-HR trở lên
- **Luồng chính**: (1) Actor mở Dashboard. (2) Hệ thống tính số liệu theo phạm vi (HR: `assigned_hr_id`=mình; HR_MANAGER/ADMIN: toàn bộ + bảng hiệu suất từng HR).
- **Tham chiếu**: FN-DASH-01, FR-DASH-001..004.

## MOD-AUDIT

### UC-AUDIT-001 — Xem nhật ký Audit
- **Actor**: ACT-HR-MANAGER, ACT-ADMIN
- **Luồng chính**: (1) Actor gọi danh sách, kèm `entity_type`/`entity_business_id` (tùy chọn). (2) Hệ thống trả log đã ghi trước đó (chỉ hành động nhạy cảm được chọn lọc, không phải mọi CRUD).
- **Tham chiếu**: FN-AUDIT-01, FR-AUDIT-001..003.

---

*Kết thúc Đợt 4 (`11_USE_CASE.md`, `12_USE_CASE_SPECIFICATION.md`). Tài liệu tiếp theo (Đợt 5): `13_SYSTEM_MODELING.md`, `14_SYSTEM_ARCHITECTURE.md`, `15_UML.md`.*
