# 07 — USER / ROLE / PERMISSION MATRIX — ATS v2

> **REFRESH TOÀN DIỆN 2026-08-18** (ngoài phạm vi 23-file gốc, theo yêu cầu người dùng "cập nhật các file tài liệu" + xác nhận làm lại toàn bộ 07/08/16/19). Toàn bộ ma trận dưới đây được dựng lại từ đầu bằng cách đọc trực tiếp **14 file router** hiện có trong `app/routers/` (tăng từ 10 file ở bản gốc 2026-08-14 lên 14 — thêm `candidates.py`, `candidate_sources.py`, `resumes.py`, `interview.py`), đếm lại chính xác **63 endpoint** thật (tăng từ 37). Bản gốc (2026-08-14, 37 endpoint, 10 router) được giữ nguyên trong lịch sử Git nếu cần đối chiếu; không phục dựng lại ở đây vì tài liệu này thay thế hoàn toàn.

**Nguồn**: `app/deps/rbac.py`, toàn bộ 63 endpoint trong `app/routers/*.py` (đọc trực tiếp từng file, không suy đoán, xem `endpoints_raw` grep 2026-08-18). **Actor Registry**: `01_MASTER_DOCUMENT_OUTLINE.md` mục A.1. `FR-XXX` giữ nguyên tham chiếu gốc ở `06_SRS.md` khi endpoint đã tồn tại lúc đó; endpoint mới hoàn toàn (xuất hiện sau 2026-08-14) đánh dấu `[MỚI]` — **không tự bịa FR-ID mới**, để ở `21_OPEN_QUESTIONS.md` nếu người dùng muốn chính thức hóa.

## 1. Mô hình phân quyền tổng quát

`[CONFIRMED]` — `app/deps/rbac.py`:
- `get_current_user`: giải mã JWT từ header `Authorization: Bearer`, tra `User` theo `business_id` trong claim `sub`. Không có token → `401 NOT_AUTHENTICATED`. Token sai/hết hạn → `401 INVALID_OR_EXPIRED_TOKEN`.
- **`get_current_user_optional`** *(MỚI 2026-08-18)*: biến thể không raise 401 — trả `None` nếu không có token/token không hợp lệ, thay vì chặn request. Dùng riêng cho `GET /jobs/{id}` để hỗ trợ xem Job Detail công khai (không đăng nhập) nhưng vẫn phân biệt được HR+ với người ẩn danh để áp logic lọc `status` khác nhau.
- 1 factory kiểm tra vai trò (`require_roles(*roles)`) và 3 dependency dựng sẵn: `require_hr_or_above` = {HR, HR_MANAGER, ADMIN}; `require_hr_manager_or_admin` = {HR_MANAGER, ADMIN}; `require_offer_approver` = {HR_MANAGER, ADMIN} (đặt tên riêng cho rõ nghĩa ở `offers.py`).
- Không có phân quyền cấp field chung — ẩn/hiện field xử lý thủ công trong từng Pydantic response schema / hàm `_to_out()`.
- Không có bảng `roles`/`permissions` động trong CSDL — 4 vai trò là `enum` cố định (`UserRole`).
- **Mẫu row-level scope lặp lại nhất quán** ở phần lớn module (trừ 2 ngoại lệ còn tồn đọng, xem mục 4): `if current_user.role == UserRole.HR and <resource>.assigned_hr_id != current_user.id: raise 403`. Xuất hiện ở: `applications.py` (`update_application`, `upload_resume`/`get_resume` qua `_check_resume_access`), `ai.py` (`_check_scope`), `offers.py` (`_check_can_view_offer`), `interview.py` (4/6 endpoint), `resumes.py` (`download_resume`), `candidates.py` (`update_candidate`, **thêm 2026-08-18**), `dashboard.py`, `email_templates.py` (chỉ 4/6 endpoint — 1 endpoint còn thiếu, xem mục 4).

## 2. Ma trận Actor × Module (tổng quan)

| Module | ACT-CANDIDATE | ACT-HR | ACT-HR-MANAGER | ACT-ADMIN |
|---|---|---|---|---|
| MOD-AUTH | Đăng ký, đăng nhập, refresh, xem hồ sơ mình, quên/đặt lại mật khẩu | (như CANDIDATE, trừ đăng ký công khai) | (như HR) | (như HR) |
| MOD-USER | ✗ | ✗ | Tạo/xem/sửa/khóa tài khoản HR | Tạo/xem/sửa/khóa tài khoản HR/HR_MANAGER/ADMIN |
| MOD-DEPT | Xem (không cần đăng nhập) | Xem | Tạo/Sửa/Xóa (soft) | Tạo/Sửa/Xóa (soft) |
| MOD-JOB | Xem Job đã đăng (kể cả không đăng nhập cho Job Detail) | Xem tất cả + lọc | Tạo/gán HR/đăng tin | (như HR_MANAGER) |
| MOD-APP | Nộp hồ sơ, xem/sửa hồ sơ mình, rút hồ sơ, tải/xem CV | Xem/đổi trạng thái/sửa Lương-Nguồn hồ sơ **được gán** | Toàn quyền + lùi trạng thái + lưu trữ | (như HR_MANAGER) |
| MOD-CANDIDATE *(mới)* | Xem hồ sơ mình (qua `/applications`, không có endpoint Candidate riêng) | Tạo/xem/sửa Candidate **được gán** (qua Application) | Toàn quyền | (như HR_MANAGER) |
| MOD-SOURCE *(mới)* | Xem (chỉ `ACTIVE`, để chọn lúc Ứng tuyển) | Xem (tất cả trạng thái) | Toàn quyền CRUD | (như HR_MANAGER) |
| MOD-INTERVIEW *(mới)* | Xem lịch phỏng vấn của mình (`GET /me`) | Tạo/xem/sửa/hủy **được gán** | Toàn quyền | (như HR_MANAGER) |
| MOD-RESUME *(mới)* | Tải CV của mình | Tải CV **được gán** | Toàn quyền | (như HR_MANAGER) |
| MOD-OFFER | Xem/phản hồi Offer của mình | Tạo/nộp duyệt/gửi Offer thuộc phạm vi mình | Toàn quyền + duyệt/từ chối | (như HR_MANAGER) |
| MOD-EMAIL | ✗ | Xem mẫu + gửi thủ công (**không giới hạn phạm vi** — xem mục 4) | Toàn quyền (tạo/sửa/vô hiệu hóa) | (như HR_MANAGER) |
| MOD-AI | ✗ | Phân tích hồ sơ **được gán** | Phân tích bất kỳ | (như HR_MANAGER) |
| MOD-DASH | ✗ | Xem số liệu phạm vi mình | Xem toàn bộ + hiệu suất từng HR | (như HR_MANAGER) |
| MOD-AUDIT | ✗ | ✗ | Xem log | Xem log |

`✗` = không có endpoint nào cho phép vai trò này truy cập module đó.

## 3. Ma trận chi tiết theo Endpoint (63 endpoint — [CONFIRMED] từng dòng đọc trực tiếp từ router, 2026-08-18)

### 3.1 MOD-AUTH (6 endpoint, +2 so với bản gốc)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | Chưa đăng nhập | FR |
|---|---|---|---|---|---|---|
| `POST /auth/register` | ✓ (tạo chính vai trò CANDIDATE) | — | — | — | ✓ (công khai) | FR-AUTH-001 |
| `POST /auth/login` | ✓ | ✓ | ✓ | ✓ | ✓ (công khai) | FR-AUTH-003 |
| `POST /auth/refresh` | ✓ | ✓ | ✓ | ✓ | ✓ (xác thực bằng refresh token trong body) | FR-AUTH-006 |
| `GET /auth/me` | ✓ | ✓ | ✓ | ✓ | ✗ 401 | FR-AUTH-007 |
| `POST /auth/forgot-password` *(mới)* | ✓ | ✓ | ✓ | ✓ | ✓ (công khai — áp dụng mọi role, không riêng Candidate) | `[MỚI]` |
| `POST /auth/reset-password` *(mới)* | ✓ | ✓ | ✓ | ✓ | ✓ (xác thực bằng token trong body, không cần Bearer) | `[MỚI]` |

`[CONFIRMED]` Cả 2 endpoint mới không có `Depends` phân quyền nào (đúng thiết kế — phải dùng được trước khi đăng nhập lại), nhưng `forgot_password()` **luôn trả cùng 1 response bất kể email tồn tại hay không** (chống account enumeration — `app/routers/auth.py:43-47`), và `reset_password()` yêu cầu token hợp lệ + còn hạn + chưa dùng (`app/services/password_reset_service.py:63-70`). Không có endpoint đổi mật khẩu chủ động khi đã đăng nhập (biết mật khẩu cũ) — xem `USER-5/6` ở `20_GAP_ANALYSIS.md`.

### 3.2 MOD-USER (5 endpoint, +3 so với bản gốc)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /users` | ✗ 403 | ✗ 403 | ✓ (chỉ tạo `HR`) | ✓ (tạo `HR`/`HR_MANAGER`/`ADMIN`) | FR-USER-001/002/003 |
| `GET /users` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-USER-004 |
| `GET /users/{id}` *(mới)* | ✗ 403 | ✗ 403 | ✓ | ✓ | `[MỚI]` |
| `PUT /users/{id}` *(mới)* | ✗ 403 | ✗ 403 | ✓ (chỉ sửa `HR`) | ✓ (sửa `HR`/`HR_MANAGER`/`ADMIN`) | `[MỚI]` |
| `DELETE /users/{id}` *(mới, thực chất soft-delete)* | ✗ 403 | ✗ 403 | ✓ (chỉ khóa `HR`, không tự khóa mình) | ✓ (khóa `HR`/`HR_MANAGER`/`ADMIN`, không tự khóa mình) | `[MỚI]` |

`require_hr_manager_or_admin` áp dụng cho **cả 5** endpoint. `_check_manage_scope()` (`app/routers/users.py:36-39`) là ranh giới thật: HR_MANAGER chỉ quản lý được role `HR`; ADMIN quản lý được `HR`/`HR_MANAGER`/`ADMIN`. Cả 3 endpoint truy vấn 1 user cụ thể (`GET/PUT/DELETE /{id}`) đều lọc `User.role != CANDIDATE` — không route nào trong module này thao tác được tài khoản Candidate (đúng chủ đích, Candidate tự quản lý qua `/auth`). `DELETE` là soft-delete (`status=INACTIVE`), không xóa vật lý — giữ nguyên lịch sử Audit/Job/Application/Interview/Offer/Email đã gắn với user.

### 3.3 MOD-DEPT (4 endpoint, +2 so với bản gốc)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | Chưa đăng nhập | FR |
|---|---|---|---|---|---|---|
| `POST /departments` | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | FR-DEPT-001 |
| `GET /departments` | ✓ | ✓ | ✓ | ✓ | **✓ — không có dependency xác thực nào** | FR-DEPT-002 |
| `PUT /departments/{id}` *(mới)* | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | `[MỚI]` |
| `DELETE /departments/{id}` *(mới, thực chất soft-delete)* | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | `[MỚI]` |

**`[CONFIRMED]`** — `list_departments()` vẫn công khai hoàn toàn (không đổi từ bản gốc, xem `20_GAP_ANALYSIS.md` — không phải Gap nghiêm trọng vì dữ liệu không nhạy cảm). `delete_department()` kiểm tra `in_use` (đang được Job/Application tham chiếu) và **vẫn soft-delete dù đang dùng** (chỉ ghi chú lý do, không chặn) — chủ đích tránh vỡ FK, không phải lỗi.

### 3.4 MOD-JOB (5 endpoint)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | Chưa đăng nhập | FR |
|---|---|---|---|---|---|---|
| `POST /jobs` | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | FR-JOB-001 |
| `POST /jobs/{id}/assign-hr` | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | FR-JOB-002 |
| `POST /jobs/{id}/publish` | ✗ 403 | ✗ 403 | ✓ | ✓ | ✗ 401 | FR-JOB-003 |
| `GET /jobs` | ✓ (chỉ `PUBLISHED`) | ✓ (tất cả, lọc `status_filter`) | ✓ (như HR) | ✓ (như HR) | ✗ 401 | FR-JOB-004, FR-JOB-005 |
| `GET /jobs/{id}` | ✓ | ✓ | ✓ | ✓ | ✅ **cho phép, có lọc** (xem ghi chú) | FR-JOB-004 |

**`[CONFIRMED — ĐÃ SỬA so với bản gốc 2026-08-14]`**: `get_job()` (`app/routers/jobs.py`) trước đây (G-07-1) không yêu cầu xác thực **và không lọc status** — lỗ hổng để lộ Job `DRAFT`/`CLOSED` cho người chưa đăng nhập. Nay dùng `get_current_user_optional`: cho phép ẩn danh (đúng yêu cầu nghiệp vụ mới "Job Detail public phải xem không cần đăng nhập"), nhưng **vẫn lọc** — chỉ trả `200` nếu người dùng là HR+ hoặc `job.status == PUBLISHED`, ngược lại `404 JOB_NOT_FOUND` (không phân biệt "không tồn tại" với "không đủ quyền xem" — tránh lộ thông tin tồn tại của tin DRAFT). Đây là 1 trong 3 Gap bảo mật từ đợt rà soát gốc; 2 Gap còn lại (G-07-2, G-07-3, xem mục 4) **vẫn chưa sửa**.

### 3.5 MOD-APP (9 endpoint, +4 so với bản gốc)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /applications` | ✓ (chỉ hồ sơ của chính mình, **bắt buộc chọn Nguồn hồ sơ `ACTIVE`**) | ✗ 403 | ✗ 403 | ✗ 403 | FR-APP-001..009 |
| `GET /applications` | ✓ (chỉ hồ sơ của mình) | ✓ (chỉ `assigned_hr_id = mình`) | ✓ (toàn bộ) | ✓ (toàn bộ) | FR-APP-015, FR-APP-017 |
| `GET /applications/{id}` | ✓ (chỉ hồ sơ của mình — có check) | ⚠️ **vẫn không giới hạn phạm vi** (xem mục 4 — CHƯA sửa) | ✓ | ✓ | FR-APP-015 (không đầy đủ) |
| `POST /applications/{id}/resume` | ✓ (chỉ hồ sơ của mình) | ✓ (chỉ **được gán**, qua `_check_resume_access`) | ✓ | ✓ | FR-APP-007 |
| `GET /applications/{id}/resume` *(mới)* | ✓ (chỉ hồ sơ của mình) | ✓ (chỉ **được gán**) | ✓ | ✓ | `[MỚI]` |
| `PUT /applications/{id}/status` | ✗ 403 | ✓ (forward-only qua `require_hr_or_above`, giới hạn thật nằm ở `application_service.update_status`) | ✓ (kể cả lùi trạng thái) | ✓ | FR-APP-010/011/012 |
| `PUT /applications/{id}` *(mới)* | ✗ 403 | ✓ (chỉ **được gán** — có check trong route; sửa Lương mong muốn/Nguồn hồ sơ, KHÔNG đổi Job/Candidate) | ✓ | ✓ | `[MỚI]` |
| `PUT /applications/{id}/withdraw` | ✓ (chỉ hồ sơ của mình) | ✗ 403 | ✗ 403 | ✗ 403 | FR-APP-013 |
| `PUT /applications/{id}/archive` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-APP-014 |

**`[CONFIRMED — GAP row-level scope, VẪN CÒN TỒN TẠI]`**: `get_application()` (`app/routers/applications.py:160-168`) vẫn chỉ kiểm tra ràng buộc phạm vi cho `CANDIDATE`, **không có nhánh kiểm tra cho `HR`** — trong khi `list_applications()`, `PUT /applications/{id}` (endpoint mới), và `PUT /candidates/{id}` (xem mục 3.6) đều đã có scoping đúng. Đây là gap duy nhất còn sót lại trong module này — cùng 1 khuyến nghị sửa như bản gốc (đối chiếu `offers.py::_check_can_view_offer`).

`POST /applications` giờ **bắt buộc** field `source_business_id` (trước đây `source` là text tự do, tùy chọn) — backend xác thực nguồn tồn tại và đang `ACTIVE`, trả `400 SOURCE_REQUIRED`/`400 SOURCE_NOT_ACTIVE` nếu không hợp lệ.

### 3.6 MOD-CANDIDATE *(module hoàn toàn mới, 5 endpoint)*

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /candidates` | ✗ 403 | ✓ | ✓ | ✓ | `[MỚI]` |
| `GET /candidates` | ✗ 403 | ✓ | ✓ | ✓ | `[MỚI]` |
| `GET /candidates/{id}` | ✓ (chỉ hồ sơ của mình) | ✓ (**không giới hạn** — chỉ chặn Candidate khác, không chặn HR khác) | ✓ | ✓ | `[MỚI]` |
| `PUT /candidates/{id}` | ✓ (chỉ hồ sơ của mình) | ✓ (chỉ Candidate có ít nhất 1 Application **được gán** cho mình — sửa 2026-08-18, xem ghi chú) | ✓ | ✓ | `[MỚI]` |
| `DELETE /candidates/{id}` *(thực chất archive)* | ✗ 403 | ✓ | ✓ | ✓ | `[MỚI]` |

**`[CONFIRMED — vá 2026-08-18, không phải phát hiện từ đợt rà soát gốc vì module này chưa tồn tại lúc đó]**: `update_candidate()` trước đây **không có scoping cho HR** — bất kỳ HR nào cũng sửa được thông tin của bất kỳ Candidate nào. Đã bổ sung kiểm tra `db.query(Application).filter(candidate_id=..., assigned_hr_id=current_user.id).first()` — HR chỉ sửa được Candidate có ít nhất 1 Application đang gán cho mình, cùng quy ước "Scoped" đã dùng xuyên suốt các module khác. `GET /candidates/{id}` **chưa** áp dụng scoping tương tự cho HR (chỉ chặn Candidate xem hồ sơ người khác) — mức độ rủi ro thấp hơn PUT (chỉ đọc, không sửa được), nhưng là một điểm bất nhất tương tự G-07-2, chưa được ghi thành Gap riêng — xem `21_OPEN_QUESTIONS.md` nếu cần quyết định có nên vá tiếp không.

### 3.7 MOD-SOURCE *(module hoàn toàn mới, 4 endpoint)*

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /candidate-sources` | ✗ 403 | ✗ 403 | ✓ | ✓ | `[MỚI]` |
| `GET /candidate-sources` | ✓ (**chỉ `ACTIVE`** — sửa 2026-08-18, xem ghi chú) | ✓ (tất cả trạng thái) | ✓ | ✓ | `[MỚI]` |
| `PUT /candidate-sources/{id}` | ✗ 403 | ✗ 403 | ✓ | ✓ | `[MỚI]` |
| `DELETE /candidate-sources/{id}` *(thực chất soft-delete)* | ✗ 403 | ✗ 403 | ✓ | ✓ | `[MỚI]` |

**`[CONFIRMED — bug phát hiện + sửa 2026-08-18, báo cáo trực tiếp từ người dùng]`**: `list_sources()` trước đây chặn cứng `403` với `CANDIDATE`. Vì form "Ứng tuyển" của chính Candidate gọi đúng endpoint này để đổ dropdown "Nguồn hồ sơ" (nay là trường bắt buộc), lỗi 403 bị nuốt lặng lẽ ở frontend khiến dropdown luôn rỗng — hiển thị nhầm thành "chưa cấu hình Nguồn hồ sơ" dù Admin đã cấu hình sẵn. Đã sửa: Candidate được xem — **chỉ các mục `ACTIVE`** (read-only, không quản lý được). Xem `20_GAP_ANALYSIS.md` mục G-POST-01, test hồi quy `tests/test_candidate_sources.py::test_candidate_can_view_active_sources_but_not_manage`.

### 3.8 MOD-INTERVIEW *(module hoàn toàn mới, 6 endpoint)*

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /interviews` | ✗ 403 | ✓ (chỉ Application **được gán**) | ✓ | ✓ | `[MỚI]` |
| `GET /interviews` | ✗ 403 | ✓ (chỉ Application **được gán**) | ✓ (toàn bộ, lọc theo interviewer/dept/status/khoảng ngày) | ✓ | `[MỚI]` |
| `GET /interviews/me` | ✓ (chỉ lịch phỏng vấn của Application thuộc chính mình) | ✗ 403 (route dành riêng CANDIDATE) | ✗ 403 | ✗ 403 | `[MỚI]` |
| `GET /interviews/{id}` | ✓ (chỉ của mình) | ✓ (chỉ **được gán**) | ✓ | ✓ | `[MỚI]` |
| `PUT /interviews/{id}` | ✗ 403 | ✓ (chỉ **được gán**) | ✓ | ✓ | `[MỚI]` |
| `DELETE /interviews/{id}` *(thực chất hủy — status CANCELLED)* | ✗ 403 | ✓ (chỉ **được gán**) | ✓ | ✓ | `[MỚI]` |

`[CONFIRMED]` Module này thực thi scoping **đúng và nhất quán** ở mọi endpoint có liên quan HR (đối chứng tốt, cùng nhóm với `offers.py`/`ai.py`). `InterviewOut` (`_to_out()`) không map field `notes` nội bộ ra cho Candidate xem qua `GET /interviews/me` — đúng nguyên tắc "Candidate không xem được ghi chú/đánh giá nội bộ".

### 3.9 MOD-RESUME *(module hoàn toàn mới, 1 endpoint)*

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `GET /resumes/{id}/download` | ✓ (chỉ CV của Application thuộc chính mình) | ✓ (chỉ **được gán**) | ✓ | ✓ | `[MỚI]` |

`[CONFIRMED]` Trả file thật qua `FileResponse` (không phải chỉ text đã trích xuất) — nếu `resume.file_path` không tồn tại trên đĩa hoặc CV chỉ là text dán trực tiếp (không có file), trả `404 RESUME_HAS_NO_DOWNLOADABLE_FILE` thay vì lỗi 500.

### 3.10 MOD-OFFER (8 endpoint)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `GET /offers` | ✓ (bắt buộc `application_business_id`, chỉ của mình) | ✓ (chỉ Offer mình tạo hoặc Application được gán) | ✓ (toàn bộ) | ✓ (toàn bộ) | FR-OFFER-012 |
| `POST /offers` | ✗ 403 | ✓ | ✓ | ✓ | FR-OFFER-001 |
| `POST /offers/{id}/submit` | ✗ 403 | ✓ | ✓ | ✓ | FR-OFFER-002 |
| `POST /offers/{id}/approve` | ✗ 403 | ✗ 403 | ✓ (trừ chính người tạo — 4-eyes) | ✓ (trừ chính người tạo) | FR-OFFER-003, FR-OFFER-004 |
| `POST /offers/{id}/reject` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-OFFER-005 |
| `POST /offers/{id}/send` | ✗ 403 | ✓ | ✓ | ✓ | FR-OFFER-006 |
| `POST /offers/{id}/respond` | ✓ (chỉ Offer của mình) | ✗ 403 | ✗ 403 | ✗ 403 | FR-OFFER-008 |
| `GET /offers/{id}` | ✓ (chỉ của mình, qua `_check_can_view_offer`) | ✓ (chỉ mình tạo hoặc được gán) | ✓ | ✓ | FR-OFFER-012 |

Không đổi so với bản gốc. Vẫn là module đối chứng tốt nhất cho pattern scoping tập trung (`_check_can_view_offer`).

### 3.11 MOD-EMAIL (6 endpoint, +1 so với bản gốc)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /email-templates` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-EMAIL-001 |
| `GET /email-templates` | ✗ 403 | ✓ | ✓ | ✓ | FR-EMAIL-001 |
| `GET /email-templates/{id}` *(mới)* | ✗ 403 | ✓ | ✓ | ✓ | `[MỚI]` |
| `PUT /email-templates/{id}` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-EMAIL-001 |
| `POST /email-templates/{id}/deactivate` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-EMAIL-002 |
| `POST /email-templates/send/{application_id}` | ✗ 403 | ✓ (**vẫn không giới hạn theo `assigned_hr_id`** — CHƯA sửa) | ✓ | ✓ | FR-EMAIL-005 |

**`[CONFIRMED — GAP phạm vi nhẹ, VẪN CÒN TỒN TẠI]`**: `send_manual_email()` (`app/routers/email_templates.py:160-186`) vẫn chỉ yêu cầu `require_hr_or_above`, chưa có scoping `assigned_hr_id`. Không đổi so với bản gốc — chưa có yêu cầu tường minh nào để sửa (xem OQ-07 ở `21_OPEN_QUESTIONS.md`). `update_template()`/`create_template()` nay có thêm kiểm tra trùng tên (`409 TEMPLATE_NAME_ALREADY_EXISTS`) và ghi audit `EMAIL_TEMPLATE_CREATED`/`EMAIL_TEMPLATE_UPDATED`/`EMAIL_TEMPLATE_DELETED` — bổ sung 2026-08-18 (không đổi RBAC, chỉ thêm validation/audit).

### 3.12 MOD-AI (2 endpoint)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `POST /ai/analyze/{application_id}` | ✗ 403 | ✓ (chỉ Application được gán — `_check_scope`) | ✓ | ✓ | FR-AI-001, FR-AI-002 |
| `GET /ai/analysis/{application_id}` | ✗ 403 | ✓ (như trên) | ✓ | ✓ | FR-AI-005 |

Không đổi so với bản gốc. AI Provider nay có thể cấu hình model cụ thể qua `AI_MODEL` (đã test gọi Gemini thật `gemini-3.7-flash` thành công 2026-08-18) — không ảnh hưởng RBAC.

### 3.13 MOD-DASH (1 endpoint)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `GET /dashboard/summary` | ✗ 403 | ✓ (giới hạn `assigned_hr_id`) | ✓ (toàn bộ + hiệu suất từng HR) | ✓ (như HR_MANAGER) | FR-DASH-001..004 |

Không đổi so với bản gốc.

### 3.14 MOD-AUDIT (1 endpoint)

| Method & Path | CANDIDATE | HR | HR_MGR | ADMIN | FR |
|---|---|---|---|---|---|
| `GET /audit` | ✗ 403 | ✗ 403 | ✓ | ✓ | FR-AUDIT-002, FR-AUDIT-003 |

Không đổi so với bản gốc.

## 4. Tổng kết Row-Level Scope — đối chiếu bản gốc (2026-08-14) vs hiện tại (2026-08-18)

| # | Endpoint | Trạng thái 2026-08-14 | Trạng thái 2026-08-18 |
|---|---|---|---|
| G-07-1 | `GET /jobs/{id}` | 🔴 Không xác thực, không lọc status | ✅ **ĐÃ SỬA** — `get_current_user_optional` + lọc status đúng |
| G-07-2 | `GET /applications/{id}` (HR) | 🔴 Không kiểm tra `assigned_hr_id` | 🔴 **VẪN CÒN TỒN TẠI** — chưa sửa |
| G-07-3 | `POST /email-templates/send/{id}` (HR) | 🔴 Không kiểm tra `assigned_hr_id` | 🔴 **VẪN CÒN TỒN TẠI** — chưa sửa |
| G-POST-01 *(mới)* | `GET /candidate-sources` (CANDIDATE) | *(module chưa tồn tại)* | ✅ **ĐÃ SỬA** — phát hiện + sửa cùng ngày 2026-08-18, xem chi tiết mục 3.7 |
| *(chưa đặt mã)* | `PUT /candidates/{id}` (HR) | *(module chưa tồn tại)* | ✅ **ĐÃ SỬA** — xem chi tiết mục 3.6 |
| *(chưa đặt mã, mức rủi ro thấp)* | `GET /candidates/{id}` (HR) | *(module chưa tồn tại)* | ⚠️ Chưa có scoping cho HR (chỉ đọc, không sửa) — xem mục 3.6 |

Đối chứng: các module xử lý đúng ngay từ đầu và vẫn đúng — `offers.py` (`_check_can_view_offer`), `ai.py` (`_check_scope`), `interview.py` (scoping ở 4/6 endpoint liên quan HR), `resumes.py`, `dashboard.py`. 2 gap còn tồn đọng (G-07-2, G-07-3) đều có sẵn 1 mẫu code để copy lại (`_check_can_view_offer`/`_check_scope`) — chi phí sửa thấp, chỉ chưa có yêu cầu tường minh để thực hiện (xem `21_OPEN_QUESTIONS.md` OQ-07).

---

*Tài liệu liên quan: `08_FUNCTIONAL_SPECIFICATION.md` (danh sách đầy đủ 63 endpoint + mô tả chức năng), `16_DATABASE_DESIGN.md` (14 bảng), `19_TRACEABILITY_MATRIX.md`, `20_GAP_ANALYSIS.md`, `21_OPEN_QUESTIONS.md`.*
