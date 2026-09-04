# 08 — FUNCTIONAL SPECIFICATION (FUNCTION CATALOG) — ATS v2

> **REFRESH TOÀN DIỆN 2026-08-18** (ngoài phạm vi 23-file gốc). Bản gốc (2026-08-14) liệt kê 37 Function ánh xạ 1:1 với 37 `UC-XXX` ở `11_USE_CASE.md`/`12_USE_CASE_SPECIFICATION.md`. Đợt refresh này **chỉ cập nhật 07/08/16/19** theo xác nhận của người dùng — **không** đụng tới `09`–`15` (Business Process/BPMN/Use Case/UML). Hệ quả: **26 Function mới** thêm ở đợt này (4 module hoàn toàn mới + mở rộng 4 module cũ) **chưa có `UC-XXX` tương ứng** — quy ước 1:1 UC:FN của bản gốc **tạm thời không còn đúng cho phần mới** cho đến khi có 1 đợt làm riêng cho `09`-`15`. Đây là 1 hạn chế đã biết, ghi nhận công khai (RULE 4) thay vì âm thầm bỏ qua hoặc tự bịa `UC-XXX` mới.

**Mục đích**: quy đổi **63 endpoint** hiện có (tăng từ 37) thành **63 chức năng nghiệp vụ** (Function). Mỗi chức năng liên kết 1-1 với đúng 1 endpoint và, nếu có, 1 `FR-XXX` ở `06_SRS.md` — endpoint mới hoàn toàn đánh dấu `[MỚI]` thay vì gán FR bịa.

**Quy ước Function Code**: `FN-<MOD>-<số thứ tự theo endpoint trong router>`, độc lập với `FR-XXX`.

---

## 1. FN-AUTH (6 chức năng, +2)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-AUTH-01` Đăng ký tài khoản Candidate | `POST /auth/register` | Không cần đăng nhập | Họ tên, email, mật khẩu, SĐT (tùy chọn) | Validate → kiểm tra email trùng → hash bcrypt → tạo `User` role=CANDIDATE → phát token | `TokenResponse` | Mật khẩu ≥8 ký tự, có chữ+số | `409 EMAIL_ALREADY_REGISTERED`; `422` | FR-AUTH-001, FR-AUTH-002 |
| `FN-AUTH-02` Đăng nhập | `POST /auth/login` | Không cần đăng nhập | Email, mật khẩu | Tra `User` → verify bcrypt → kiểm tra `status=ACTIVE` → phát token | `TokenResponse` | Chỉ `ACTIVE` đăng nhập được | `401`; `403` | FR-AUTH-003, FR-AUTH-008 |
| `FN-AUTH-03` Làm mới Access Token | `POST /auth/refresh` | Refresh token trong body | `refresh_token` | Băm SHA-256 → so khớp hash lưu sẵn + hạn 30 ngày → phát Access Token mới | `TokenResponse` | — | `401 INVALID_REFRESH_TOKEN` | FR-AUTH-006 |
| `FN-AUTH-04` Xem hồ sơ tài khoản hiện tại | `GET /auth/me` | Tất cả (đã đăng nhập) | — | Giải mã JWT → tra `User` | `UserOut` | — | `401` | FR-AUTH-007 |
| `FN-AUTH-05` Quên mật khẩu *(mới)* | `POST /auth/forgot-password` | Không cần đăng nhập | Email | Tra `User` theo email (không raise nếu không tồn tại) → tạo token random (SHA-256 hash lưu DB, hạn 30 phút) → tìm `EmailTemplate` loại `PASSWORD_RESET` `ACTIVE` → render + gửi email chứa link `{api_url}/reset-password?token=...` | `{message}` (luôn cùng 1 nội dung) | Không tiết lộ email có tồn tại hay không (chống account enumeration); **im lặng bỏ qua** nếu chưa có `EmailTemplate PASSWORD_RESET ACTIVE` — từng là bug thật khiến tính năng không gửi được email nào (đã vá 2026-08-18, xem `20_GAP_ANALYSIS.md` AUTH-9) | Không raise lỗi ra ngoài — best-effort | `[MỚI]` |
| `FN-AUTH-06` Đặt lại mật khẩu *(mới)* | `POST /auth/reset-password` | Token trong body (không cần Bearer) | `token`, `new_password` | Băm SHA-256 token → tìm `PasswordResetToken` khớp hash, còn hạn, `used_at IS NULL` → hash mật khẩu mới → xóa `refresh_token_hash`/`refresh_token_expires_at` hiện có (buộc đăng nhập lại mọi thiết bị) → đánh dấu token đã dùng | `{message}` | Token 1 lần dùng, có hạn | `400 INVALID_OR_EXPIRED_RESET_TOKEN`; `422` mật khẩu yếu | `[MỚI]` |

## 2. FN-USER (5 chức năng, +3)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-USER-01` Tạo tài khoản nội bộ | `POST /users` | HR_MANAGER, ADMIN | Họ tên, email, mật khẩu, role, department (tùy chọn) | Kiểm tra role hợp lệ + actor được phép tạo role đó → kiểm tra email trùng → hash mật khẩu → tạo `User` | `UserOut` | HR_MANAGER chỉ tạo `HR`; ADMIN tạo `HR`/`HR_MANAGER`/`ADMIN` | `403 NOT_ALLOWED_TO_CREATE_THIS_ROLE`; `409`; `404` | FR-USER-001, FR-USER-002, FR-USER-003 |
| `FN-USER-02` Liệt kê tài khoản nội bộ | `GET /users` | HR_MANAGER, ADMIN | `role` (tùy chọn) | Query loại trừ `role=CANDIDATE` | Danh sách `UserOut` | — | `400 INVALID_ROLE` | FR-USER-004 |
| `FN-USER-03` Xem chi tiết 1 tài khoản nội bộ *(mới)* | `GET /users/{id}` | HR_MANAGER, ADMIN | — | Query 1 `User` (loại trừ CANDIDATE) | `UserOut` | — | `404 USER_NOT_FOUND` | `[MỚI]` |
| `FN-USER-04` Sửa tài khoản nội bộ *(mới)* | `PUT /users/{id}` | HR_MANAGER, ADMIN | Họ tên/SĐT/department/status (tùy chọn) | Kiểm tra actor được phép quản lý role của target (cùng ranh giới với `FN-USER-01`) → cập nhật từng phần → audit `HR_USER_UPDATED` | `UserOut` | Không sửa được role qua endpoint này | `403`; `404` | `[MỚI]` |
| `FN-USER-05` Khóa tài khoản nội bộ *(mới, thực chất soft-delete)* | `DELETE /users/{id}` | HR_MANAGER, ADMIN | — | Kiểm tra scope quản lý + không tự khóa mình → `status → INACTIVE` → audit `HR_USER_DELETED` | `{business_id, status}` | Soft-delete — giữ lịch sử Audit/Job/Application/Interview/Offer đã gắn | `403`; `400 CANNOT_DEACTIVATE_SELF` | `[MỚI]` |

## 3. FN-DEPT (4 chức năng, +2)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-DEPT-01` Tạo phòng ban | `POST /departments` | HR_MANAGER, ADMIN | Tên, mô tả | Kiểm tra tên trùng → tạo `Department` | `DepartmentOut` | Tên duy nhất | `409 DEPARTMENT_NAME_ALREADY_EXISTS` | FR-DEPT-001 |
| `FN-DEPT-02` Danh sách phòng ban | `GET /departments` | Công khai (không xác thực) | — | Query toàn bộ | Danh sách `DepartmentOut` | — | — | FR-DEPT-002 |
| `FN-DEPT-03` Sửa phòng ban *(mới)* | `PUT /departments/{id}` | HR_MANAGER, ADMIN | Tên/mô tả/status (tùy chọn) | Kiểm tra tên trùng nếu đổi tên → cập nhật từng phần → audit `DEPARTMENT_UPDATED` | `DepartmentOut` | — | `404`; `409`; `400 INVALID_STATUS` | `[MỚI]` |
| `FN-DEPT-04` Xóa phòng ban *(mới, thực chất soft-delete)* | `DELETE /departments/{id}` | HR_MANAGER, ADMIN | — | Kiểm tra đang được Job/Application dùng (chỉ ghi chú, không chặn) → `status → INACTIVE` → audit `DEPARTMENT_DELETED` | `{business_id, status, in_use}` | Không xóa vật lý — tránh vỡ FK | `404` | `[MỚI]` |

## 4. FN-JOB (5 chức năng)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-JOB-01` Tạo tin tuyển dụng | `POST /jobs` | HR_MANAGER, ADMIN | Tiêu đề, phòng ban, mô tả, yêu cầu, lương min/max, số lượng, địa điểm, hình thức, HR phụ trách (tùy chọn) | Tạo `Job` trạng thái `DRAFT`, tự sinh `slug` | `JobOut` | — | `404 DEPARTMENT_NOT_FOUND` | FR-JOB-001 |
| `FN-JOB-02` Gán HR phụ trách | `POST /jobs/{id}/assign-hr` | HR_MANAGER, ADMIN | `assigned_hr_business_id` | Cập nhật `Job.assigned_hr_id` | `JobOut` | Chỉ gán được User role `HR` | `404`; `400` | FR-JOB-002 |
| `FN-JOB-03` Đăng tin | `POST /jobs/{id}/publish` | HR_MANAGER, ADMIN | — | `DRAFT → PUBLISHED`, ghi `approved_by` **và `published_at`** (bổ sung 2026-08-18 — trước đó cột `published_at` tồn tại nhưng không được gán giá trị) | `JobOut` | Đơn giản hóa — không qua duyệt trung gian (Gap JOB-8, chưa đổi) | `409` | FR-JOB-003 |
| `FN-JOB-04` Danh sách tin tuyển dụng | `GET /jobs` | Tất cả (đã đăng nhập) | `search`, `department_business_id`, `status_filter` | Query; Candidate ép `status=PUBLISHED` | Danh sách `JobOut` (đầy đủ field public: mô tả/yêu cầu/lương/địa điểm/hình thức/hạn nộp/ngày đăng — mở rộng 2026-08-18) | Candidate chỉ thấy tin đã đăng | `400 INVALID_STATUS` | FR-JOB-004, FR-JOB-005 |
| `FN-JOB-05` Xem chi tiết 1 tin | `GET /jobs/{id}` | Tất cả, **kể cả chưa đăng nhập** (dùng `get_current_user_optional`, sửa 2026-08-18) | — | Query theo `business_id`; nếu không phải HR+ và job không `PUBLISHED` → `404` (không phân biệt "không tồn tại" vs "không đủ quyền") | `JobOut` đầy đủ field | ✅ **Gap G-07-1 đã vá** — trước đây không lọc status cho người chưa đăng nhập | `404 JOB_NOT_FOUND` | FR-JOB-004 |

## 5. FN-APP (9 chức năng, +2)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-APP-01` Nộp hồ sơ ứng tuyển | `POST /applications` | CANDIDATE | `job_business_id`, thông tin liên hệ, **`source_business_id` (bắt buộc, mới)**, `ai_consent`, `resume_text` (tùy chọn), header `Idempotency-Key` (tùy chọn) | Kiểm tra `ai_consent` → kiểm tra Job `PUBLISHED` → **kiểm tra `CandidateSource` tồn tại và `ACTIVE`** (mới) → tìm/tạo `Candidate` → tạo `Application` (lưu cả `source_id` FK và `source` text snapshot) → audit → email `APPLICATION_RECEIVED` | `ApplicationOut` | Không giới hạn tái ứng tuyển; Nguồn hồ sơ bắt buộc và phải `ACTIVE` (mới 2026) | `403`; `400 AI_CONSENT_REQUIRED`; `404`; `400 SOURCE_REQUIRED`/`SOURCE_NOT_ACTIVE` (mới) | FR-APP-001..006 |
| `FN-APP-02` Danh sách hồ sơ ứng tuyển | `GET /applications` | Tất cả (đã đăng nhập) | `job_business_id`, **`candidate_business_id` (mới)**, `search` | Query, lọc theo phạm vi actor + filter mới (phục vụ "Application History" ở Candidate Detail) | Danh sách `ApplicationOut` | Row-level scope theo vai trò | — | FR-APP-015, FR-APP-017 |
| `FN-APP-03` Xem chi tiết 1 hồ sơ | `GET /applications/{id}` | Tất cả (đã đăng nhập) | — | Query; chỉ chặn CANDIDATE không sở hữu | `ApplicationOut` | ⚠️ Vẫn không chặn HR ngoài phạm vi — Gap G-07-2 chưa vá | `404`; `403` | FR-APP-015 (không đầy đủ) |
| `FN-APP-04` Tải lên file CV | `POST /applications/{id}/resume` | CANDIDATE (chủ hồ sơ), **HR được gán (mới)** | File PDF/DOCX | Kiểm tra quyền → validate extension + magic-bytes (quét trong 1024 byte đầu, không bắt buộc đúng byte 0 — sửa 2026-08-18 để chấp nhận PDF có BOM/khoảng trắng đầu file) → trích xuất text → lưu | `ResumeOut` | ≤10MB, PDF/DOCX | `403`; `400` | FR-APP-007, FR-APP-008, FR-APP-009 |
| `FN-APP-05` Xem thông tin CV đã nộp *(mới)* | `GET /applications/{id}/resume` | CANDIDATE (chủ hồ sơ), HR được gán, HR_MANAGER/ADMIN | — | Query `Resume` theo Application | `ResumeOut` (kèm `uploaded_at`, mới) | Cùng scope với upload | `404 RESUME_NOT_FOUND` | `[MỚI]` |
| `FN-APP-06` Đổi trạng thái hồ sơ | `PUT /applications/{id}/status` | HR, HR_MANAGER, ADMIN | `status` mới, `reason` (bắt buộc nếu lùi) | Xác thực cạnh chuyển hợp lệ → cập nhật → audit → email tương ứng | `ApplicationOut` | Máy trạng thái server-side | `409`; `403`; `400` | FR-APP-010, FR-APP-011, FR-APP-012 |
| `FN-APP-07` Sửa Lương mong muốn / Nguồn hồ sơ *(mới)* | `PUT /applications/{id}` | HR được gán, HR_MANAGER, ADMIN | `desired_salary`, `source_business_id` (đều tùy chọn) | Kiểm tra scope → nếu đổi nguồn, xác thực nguồn `ACTIVE` → cập nhật → audit `APPLICATION_UPDATED` (kèm before/after) | `ApplicationOut` | KHÔNG cho đổi `job_id`/`candidate_id` qua route này (tránh phá vỡ relationship) | `403`; `400 SOURCE_REQUIRED`/`SOURCE_NOT_ACTIVE` | `[MỚI]` |
| `FN-APP-08` Rút hồ sơ | `PUT /applications/{id}/withdraw` | CANDIDATE (chủ hồ sơ) | — | Kiểm tra trạng thái thuộc `WITHDRAWABLE_STATUSES` → `WITHDRAWN` | `ApplicationOut` | Chỉ rút được trước `OFFER` | `409`; `403` | FR-APP-013 |
| `FN-APP-09` Lưu trữ hồ sơ | `PUT /applications/{id}/archive` | HR_MANAGER, ADMIN | `archive_reason` | Chặn nếu `HIRED` → `ARCHIVED` | `ApplicationOut` | Không lưu trữ được hồ sơ đã `HIRED` | `409`; `400` | FR-APP-014 |

## 6. FN-CANDIDATE (5 chức năng, module hoàn toàn mới)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-CAND-01` Thêm ứng viên (do HR tạo hộ) | `POST /candidates` | HR, HR_MANAGER, ADMIN | Họ tên/giới tính/email/SĐT, `job_business_id` (bắt buộc), lương mong muốn, nguồn (text tự do), skills/experience summary | Tạo đồng thời 1 `Candidate` + 1 `Application` (liên kết Job ngay từ lúc tạo, best-effort match `CandidateSource` theo tên) | `CandidateOut` + `application_business_id` | Dùng cho luồng HR chủ động thêm hồ sơ (khác với Candidate tự ứng tuyển) | `404` | `[MỚI]` |
| `FN-CAND-02` Danh sách ứng viên | `GET /candidates` | HR, HR_MANAGER, ADMIN | `search` (tùy chọn) | Query theo tên/email/SĐT | Danh sách `CandidateOut` | — | — | `[MỚI]` |
| `FN-CAND-03` Xem chi tiết 1 ứng viên | `GET /candidates/{id}` | CANDIDATE (chính mình), HR+ | — | Query; chỉ chặn CANDIDATE khác | `CandidateOut` | ⚠️ Chưa có scoping cho HR (đọc được mọi Candidate, không chỉ được gán) — mức rủi ro thấp hơn sửa vì chỉ đọc | `404`; `403` | `[MỚI]` |
| `FN-CAND-04` Sửa thông tin ứng viên | `PUT /candidates/{id}` | CANDIDATE (chính mình), HR **được gán** (sửa 2026-08-18), HR_MANAGER, ADMIN | Họ tên/giới tính/SĐT/skills/experience (tùy chọn) | Kiểm tra quyền sở hữu (Candidate) hoặc có Application đang gán cho actor (HR, **mới bổ sung** — trước đó mọi HR đều sửa được mọi Candidate) → cập nhật | `CandidateOut` | Không sửa được `candidate_id`/`created_at`/audit field | `403 NOT_ASSIGNED_TO_THIS_CANDIDATE` (mới); `403 NOT_YOUR_PROFILE` | `[MỚI]` |
| `FN-CAND-05` Lưu trữ ứng viên | `DELETE /candidates/{id}` | HR, HR_MANAGER, ADMIN | — | `status → ARCHIVED` (soft-delete) | `{business_id, status}` | — | `404` | `[MỚI]` |

## 7. FN-SOURCE (4 chức năng, module hoàn toàn mới)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-SOURCE-01` Tạo Nguồn hồ sơ | `POST /candidate-sources` | HR_MANAGER, ADMIN | Tên | Kiểm tra tên trùng → tạo `CandidateSource` `ACTIVE` | `CandidateSourceOut` | Tên duy nhất | `409 SOURCE_NAME_ALREADY_EXISTS` | `[MỚI]` |
| `FN-SOURCE-02` Danh sách Nguồn hồ sơ | `GET /candidate-sources` | CANDIDATE (**chỉ `ACTIVE`**, sửa 2026-08-18), HR/HR_MANAGER/ADMIN (tất cả) | — | Query, lọc theo role | Danh sách `CandidateSourceOut` | ✅ Bug đã vá — trước đây chặn cứng Candidate `403`, khiến dropdown "Nguồn hồ sơ" ở form Ứng tuyển luôn rỗng dù đã cấu hình | `403` (Candidate không còn gặp lỗi này) | `[MỚI]` |
| `FN-SOURCE-03` Sửa Nguồn hồ sơ | `PUT /candidate-sources/{id}` | HR_MANAGER, ADMIN | Tên/status (tùy chọn) | Kiểm tra tên trùng nếu đổi → cập nhật | `CandidateSourceOut` | — | `404`; `409`; `400 INVALID_STATUS` | `[MỚI]` |
| `FN-SOURCE-04` Vô hiệu hóa Nguồn hồ sơ | `DELETE /candidate-sources/{id}` | HR_MANAGER, ADMIN | — | `status → INACTIVE` (soft-delete — `Application.source_id` vẫn giữ tham chiếu lịch sử) | `{business_id, status}` | Không xóa vật lý | `404` | `[MỚI]` |

## 8. FN-INTERVIEW (6 chức năng, module hoàn toàn mới — đóng Gap APP-20)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-INT-01` Lên lịch phỏng vấn | `POST /interviews` | HR **được gán**, HR_MANAGER, ADMIN | `application_business_id`, `interviewer_business_id`, thời gian bắt đầu/kết thúc, hình thức, địa điểm/link, ghi chú | Kiểm tra Application tồn tại + scope HR → kiểm tra interviewer không phải Candidate → tạo `Interview` | `InterviewOut` | Interview phải gắn với 1 Application hợp lệ | `404`; `403 NOT_YOUR_ASSIGNED_APPLICATION` | `[MỚI]` |
| `FN-INT-02` Danh sách lịch phỏng vấn (nội bộ) | `GET /interviews` | HR **được gán**, HR_MANAGER, ADMIN | `interviewer_business_id`/`department_business_id`/`application_status`/`date_from`/`date_to` (tùy chọn) | Query có scope + nhiều filter | Danh sách `InterviewOut` | — | — | `[MỚI]` |
| `FN-INT-03` Lịch phỏng vấn của tôi (Candidate) | `GET /interviews/me` | CANDIDATE | — | Query Interview theo `Application.candidate_id` của actor | Danh sách `InterviewOut` (không lộ `notes`/`feedback` nội bộ) | Chỉ Candidate gọi được | `403 ONLY_CANDIDATE_HAS_MY_INTERVIEWS` | `[MỚI]` |
| `FN-INT-04` Xem chi tiết 1 lịch phỏng vấn | `GET /interviews/{id}` | CANDIDATE (của mình), HR **được gán**, HR_MANAGER, ADMIN | — | Query + scope theo role | `InterviewOut` | — | `404`; `403` | `[MỚI]` |
| `FN-INT-05` Sửa lịch phỏng vấn | `PUT /interviews/{id}` | HR **được gán**, HR_MANAGER, ADMIN | Các trường cần sửa (tùy chọn), `status` mới | Kiểm tra scope → cập nhật | `InterviewOut` | — | `404`; `403` | `[MỚI]` |
| `FN-INT-06` Hủy lịch phỏng vấn | `DELETE /interviews/{id}` | HR **được gán**, HR_MANAGER, ADMIN | — | `status → CANCELLED` (không hard-delete) | `{business_id, status}` | — | `404`; `403` | `[MỚI]` |

## 9. FN-RESUME (1 chức năng, module hoàn toàn mới)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-RESUME-01` Tải file CV gốc | `GET /resumes/{id}/download` | CANDIDATE (chủ hồ sơ), HR **được gán**, HR_MANAGER, ADMIN | — | Kiểm tra scope → trả file thật (`FileResponse`) từ `resume.file_path` | File PDF/DOCX gốc | Ưu tiên authorization trước khi cho tải | `404 RESUME_NOT_FOUND`/`RESUME_HAS_NO_DOWNLOADABLE_FILE`; `403` | `[MỚI]` |

## 10. FN-OFFER (8 chức năng, không đổi)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-OFFER-01` Danh sách Offer | `GET /offers` | Tất cả (đã đăng nhập) | `application_business_id`, `status` | Query theo phạm vi actor | Danh sách `OfferOut` | Candidate bắt buộc truyền `application_business_id` | `400`; `403`; `404` | FR-OFFER-012 |
| `FN-OFFER-02` Tạo Offer | `POST /offers` | HR, HR_MANAGER, ADMIN | `application_business_id`, lương, `probation_salary`, `start_date` | Tạo `Offer` `DRAFT` | `OfferOut` | — | `404` | FR-OFFER-001 |
| `FN-OFFER-03` Nộp duyệt Offer | `POST /offers/{id}/submit` | HR+ | — | `DRAFT → PENDING_APPROVAL` | `OfferOut` | — | `409`; `403` | FR-OFFER-002 |
| `FN-OFFER-04` Duyệt Offer | `POST /offers/{id}/approve` | HR_MANAGER, ADMIN | — | Chặn tự duyệt → `PENDING_APPROVAL → APPROVED` | `OfferOut` | 4-eyes (service + DB CheckConstraint) | `409` | FR-OFFER-003, FR-OFFER-004 |
| `FN-OFFER-05` Từ chối duyệt Offer | `POST /offers/{id}/reject` | HR_MANAGER, ADMIN | `reason` | `PENDING_APPROVAL → DRAFT` | `OfferOut` | — | `400` | FR-OFFER-005 |
| `FN-OFFER-06` Gửi Offer | `POST /offers/{id}/send` | HR+ | — | `APPROVED → SENT`, tính hạn, email `OFFER` | `OfferOut` | — | `409` | FR-OFFER-006, FR-OFFER-007 |
| `FN-OFFER-07` Ứng viên phản hồi Offer | `POST /offers/{id}/respond` | CANDIDATE (chủ Offer) | `response` | Accept/Decline → cập nhật Offer + Application, email `ONBOARDING` nếu accept | `OfferOut` | Chỉ khi `SENT` | `409`; `400` | FR-OFFER-008..010 |
| `FN-OFFER-08` Xem chi tiết 1 Offer | `GET /offers/{id}` | Tất cả (đã đăng nhập) | — | `_check_can_view_offer()` | `OfferOut` | Scope nhất quán | `404`; `403` | FR-OFFER-012 |

*(`expire_due_offers()` vẫn không có endpoint HTTP riêng — chưa wiring APScheduler, không đổi so với bản gốc, xem `OFFER-11` ở `20_GAP_ANALYSIS.md`.)*

## 11. FN-EMAIL (6 chức năng, +1)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-EMAIL-01` Tạo mẫu Email | `POST /email-templates` | HR_MANAGER, ADMIN | Tên, loại (1/8 — thêm `PASSWORD_RESET`), tiêu đề, nội dung | Kiểm tra tên trùng (mới) → tạo `ACTIVE` → audit `EMAIL_TEMPLATE_CREATED` (mới) | `EmailTemplateOut` | Tên duy nhất (mới) | `400`; `409 TEMPLATE_NAME_ALREADY_EXISTS` (mới) | FR-EMAIL-001, FR-EMAIL-003 |
| `FN-EMAIL-02` Danh sách mẫu Email | `GET /email-templates` | HR+ | — | Query toàn bộ | Danh sách `EmailTemplateOut` | — | — | FR-EMAIL-001 |
| `FN-EMAIL-03` Xem chi tiết 1 mẫu Email *(mới)* | `GET /email-templates/{id}` | HR+ | — | Query 1 template | `EmailTemplateOut` | — | `404` | `[MỚI]` |
| `FN-EMAIL-04` Sửa mẫu Email | `PUT /email-templates/{id}` | HR_MANAGER, ADMIN | Các trường cần sửa | Kiểm tra tên trùng (trừ chính nó, mới) → cập nhật → audit `EMAIL_TEMPLATE_UPDATED` kèm before/after + `changed_fields` (mới) | `EmailTemplateOut` | Không sửa được ID/`created_at`/`created_by` | `404`; `409` (mới) | FR-EMAIL-001 |
| `FN-EMAIL-05` Vô hiệu hóa mẫu Email | `POST /email-templates/{id}/deactivate` | HR_MANAGER, ADMIN | — | `status → INACTIVE` → audit `EMAIL_TEMPLATE_DELETED` (mới) | `EmailTemplateOut` | Không xóa vật lý | `404` | FR-EMAIL-002 |
| `FN-EMAIL-06` Gửi Email thủ công | `POST /email-templates/send/{application_id}` | HR+ | `template_business_id` | Render biến → gửi SMTP (thật/giả lập) → ghi audit | `{success, status_message,...}` | ⚠️ Vẫn không kiểm tra `assigned_hr_id` — Gap G-07-3 chưa vá | `404` | FR-EMAIL-004, FR-EMAIL-005, FR-EMAIL-008, FR-EMAIL-009 |

## 12. FN-AI (2 chức năng, không đổi)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-AI-01` Phân tích AI Screening | `POST /ai/analyze/{application_id}` | HR+ (scope) | — | Lấy CV text mới nhất; nếu không có → `202`; nếu có → gọi AI Provider thật (Gemini/Claude, retry 1 lần) hoặc fallback stub → lưu `AIAnalysis` mới | `AIAnalysisOut` hoặc `202` | AI không tự quyết định số phận hồ sơ | `404`; `403` | FR-AI-001..006 |
| `FN-AI-02` Lịch sử phân tích AI | `GET /ai/analysis/{application_id}` | HR+ (scope) | — | Query toàn bộ lịch sử | Danh sách `AIAnalysisOut` | Giữ toàn bộ lịch sử | `404`; `403` | FR-AI-005 |

## 13. FN-DASH (1 chức năng, không đổi)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-DASH-01` Xem số liệu tổng hợp | `GET /dashboard/summary` | HR+ | — | Tổng hợp theo phạm vi actor | `DashboardSummaryOut` | Row-level scope | — | FR-DASH-001..004 |

## 14. FN-AUDIT (1 chức năng, không đổi)

| Function | Endpoint | Actor | Input | Xử lý chính | Output | Business Rule | Lỗi có thể | FR |
|---|---|---|---|---|---|---|---|---|
| `FN-AUDIT-01` Xem nhật ký Audit | `GET /audit` | HR_MANAGER, ADMIN | `entity_type`, `entity_business_id` (tùy chọn) | Query có lọc | Danh sách `AuditLogOut` | — | — | FR-AUDIT-001..003 |

---

## 15. Tổng kết

**Tổng số Function**: 6+5+4+5+9+5+4+6+1+8+6+2+1+1 = **63**, khớp đúng số endpoint HTTP thực tế đếm được ở `07_USER_ROLE_PERMISSION.md` (2026-08-18). Tăng **26 Function** so với bản gốc (37→63): 16 Function thuộc 4 module hoàn toàn mới (`FN-CANDIDATE` 5, `FN-SOURCE` 4, `FN-INTERVIEW` 6, `FN-RESUME` 1) + 10 Function mở rộng trong các module cũ (`FN-AUTH` +2, `FN-USER` +3, `FN-DEPT` +2, `FN-APP` +2, `FN-EMAIL` +1).

**Hạn chế đã biết** (nhắc lại từ đầu file): 26 Function mới chưa có `UC-XXX`/`FR-XXX` chính thức tương ứng vì đợt refresh này không đụng tới `09`-`15`. Nếu cần đầy đủ 1:1 UC:FN như phương pháp gốc, cần 1 đợt làm việc riêng.

*Tài liệu liên quan: `07_USER_ROLE_PERMISSION.md`, `16_DATABASE_DESIGN.md`, `19_TRACEABILITY_MATRIX.md`.*
