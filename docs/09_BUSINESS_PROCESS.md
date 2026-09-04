# 09 — BUSINESS PROCESS SPECIFICATION — ATS v2.1

**Nguồn**: `app/services/application_service.py`, `app/services/offer_service.py`, `app/services/ai_service.py`, `app/services/email_service.py` (đọc trực tiếp toàn bộ hàm nghiệp vụ). **ID Scheme**: `BP-<MOD>-XXX` (`01_MASTER_DOCUMENT_OUTLINE.md` mục A.3). Mỗi BP liên kết `FN-XXX` (`08`) và `FR-XXX` (`06`) liên quan.

---

## BP-JOB-001 — Vòng đời tin tuyển dụng

**Actor**: HR_MANAGER/ADMIN (chủ trì), ACT-SYSTEM (tự đóng tin)
**Trigger**: HR_MANAGER/ADMIN cần tuyển người cho 1 vị trí
**Tiền điều kiện**: Phòng ban liên quan đã tồn tại (`BP` phụ thuộc `FN-DEPT-01`)

**Các bước**:
1. HR_MANAGER/ADMIN tạo tin (`FN-JOB-01`) → `Job.status = DRAFT`.
2. (Tùy chọn) Gán `ACT-HR` phụ trách (`FN-JOB-02`) — có thể làm ngay lúc tạo hoặc sau.
3. HR_MANAGER/ADMIN đăng tin (`FN-JOB-03`) → `Job.status = DRAFT → PUBLISHED` **trong 1 bước** (không qua `PENDING_APPROVAL`/`APPROVED` dù 2 giá trị này tồn tại trong enum — Gap JOB-8, xem `20_GAP_ANALYSIS.md`).
4. Candidate tìm và xem tin đã đăng (`FN-JOB-04`, `FN-JOB-05`) → nộp hồ sơ (khởi động `BP-APP-001`).
5. **[ACT-SYSTEM, tự động]** Mỗi khi 1 Offer được Candidate Accept (`BP-OFFER-001` bước 7), hệ thống đếm số `Application.status=HIRED` của Job; nếu ≥ `Job.quantity` → tự chuyển `Job.status = CLOSED` (`offer_service._close_job_if_quota_reached`).

**Hậu điều kiện**: Tin ở trạng thái `PUBLISHED` (đang tuyển) hoặc `CLOSED` (đủ chỉ tiêu).
**Business Rule áp dụng**: BRULE-03 (tự đóng khi đủ quota).
**Ngoại lệ/Gap**: Không có bước hủy tin (`CANCELLED` tồn tại trong enum nhưng không có endpoint chuyển sang trạng thái này); không có quy trình duyệt nhiều cấp trước khi đăng (JOB-8).

---

## BP-APP-001 — Ứng viên nộp hồ sơ (kể cả tái ứng tuyển)

**Actor**: ACT-CANDIDATE
**Trigger**: Candidate quyết định ứng tuyển 1 vị trí đang `PUBLISHED`
**Tiền điều kiện**: Candidate đã có tài khoản (`BP` phụ thuộc đăng ký `FN-AUTH-01`); Job đang `PUBLISHED`

**Các bước**:
1. Candidate đồng ý xử lý AI (`ai_consent=true`) — bắt buộc, nếu không hệ thống từ chối ngay (`400 AI_CONSENT_REQUIRED`).
2. Candidate gửi request nộp hồ sơ (`FN-APP-01`), có thể kèm `Idempotency-Key` để chống nộp trùng do lỗi mạng/double-click.
3. **[ACT-SYSTEM]** Nếu `Idempotency-Key` trùng với 1 request trước đó của **chính Candidate này** → trả về bản ghi `Application` cũ, không tạo mới, ghi audit `APPLICATION_DUPLICATE_REQUEST`. Luồng dừng ở đây.
4. **[ACT-SYSTEM]** Nếu không trùng: tìm/tạo `Candidate` (dedupe theo email — nếu email đã tồn tại từ lần nộp trước, dùng lại record cũ, không tạo Candidate trùng).
5. **[ACT-SYSTEM]** Tạo `Application` mới, `status = NEW`, kế thừa `assigned_hr_id` từ `Job.assigned_hr_id`. **Không kiểm tra** Candidate này đã từng nộp cho Job này trước đó hay chưa, và **không có giới hạn thời gian** giữa các lần nộp (BRULE-02 — bỏ hoàn toàn cooldown theo quyết định nghiệp vụ CHANGE 02).
6. (Tùy chọn) Candidate dán text CV trực tiếp trong cùng request (`resume_text`), hoặc tải file CV sau đó qua `FN-APP-04` (PDF/DOCX, có xác thực magic-bytes).
7. **[ACT-SYSTEM]** Ghi audit (`APPLICATION_CREATED` hoặc `APPLICATION_REAPPLIED` nếu phát hiện đã có hồ sơ trước đó cho cùng Job) → **kích hoạt email tự động** loại `APPLICATION_RECEIVED` (im lặng bỏ qua nếu chưa có mẫu `ACTIVE`).

**Hậu điều kiện**: 1 bản ghi `Application` mới ở trạng thái `NEW`, các bản ghi `Application` cũ (nếu có, từ lần nộp trước) **không bị thay đổi**.
**Business Rule áp dụng**: BRULE-02 (không giới hạn tái ứng tuyển), APP-3 (chống trùng), APP-5 (immutable).
**Ngoại lệ**: Job không tồn tại/không `PUBLISHED` → `404`; không phải Candidate → `403`.

---

## BP-APP-002 — Sàng lọc & tiến trình hồ sơ (Screening Pipeline)

**Actor**: ACT-HR (chuyển tiến), ACT-HR-MANAGER/ACT-ADMIN (chuyển tiến hoặc lùi), ACT-SYSTEM (tự chuyển AI_SCREENING→SCREENING theo fallback)
**Trigger**: HR cần cập nhật kết quả sàng lọc/phỏng vấn cho 1 hồ sơ
**Tiền điều kiện**: `Application` tồn tại, chưa ở trạng thái kết thúc (`HIRED`/`REJECTED`/`WITHDRAWN`/`ARCHIVED`)

**Máy trạng thái `[CONFIRMED]`** (trích `application_service.py::FORWARD_EDGES`):

| Từ | Sang (hợp lệ) |
|---|---|
| `NEW` | `SCREENING` (cạnh fallback sàng lọc thủ công — dùng khi chưa gọi AI, hoặc AI service backlog) |
| `SCREENING` | `SHORTLISTED`, `REJECTED` |
| `SHORTLISTED` | `INTERVIEW` |
| `INTERVIEW` | `REJECTED` |

`AI_SCREENING` và `OFFER`/`HIRED` **không nằm trong `FORWARD_EDGES`** — `AI_SCREENING` chỉ đạt được qua `FN-AI-01` (không qua endpoint đổi trạng thái thủ công này); `OFFER`/`HIRED` chỉ đạt được qua `BP-OFFER-001` (`offer_service`), **không thể** set trực tiếp qua `PUT /applications/{id}/status` — đây là ràng buộc chủ đích để không ai "giả mạo" trạng thái Offer mà không qua quy trình 4-eyes thật.

**Các bước (chuyển tiến — forward)**:
1. HR (hoặc cấp cao hơn) gọi `FN-APP-05` với trạng thái đích hợp lệ theo bảng trên.
2. **[ACT-SYSTEM]** Xác thực cạnh chuyển hợp lệ → cập nhật `Application.status` → ghi audit `APPLICATION_STATUS_CHANGED`.
3. **[ACT-SYSTEM]** Nếu trạng thái mới ∈ {`SHORTLISTED`, `INTERVIEW`, `REJECTED`} → kích hoạt email tương ứng (`SHORTLISTED`/`INTERVIEW_INVITATION`/`REJECTION`).

**Các bước (lùi trạng thái — backward, chỉ HR_MANAGER/ADMIN)**:
1. Actor gọi `FN-APP-05` với trạng thái đích ở vị trí **trước** trạng thái hiện tại theo `PIPELINE_ORDER` (`NEW→AI_SCREENING→SCREENING→SHORTLISTED→INTERVIEW→OFFER→HIRED`).
2. **[ACT-SYSTEM]** Chặn nếu actor không phải HR_MANAGER/ADMIN, hoặc thiếu `reason`.
3. Cập nhật trạng thái, ghi audit `STATUS_REVERTED` kèm `reason`. **Không** kích hoạt email tự động khi lùi trạng thái (chỉ áp dụng khi `is_backward=False`).

**Business Rule áp dụng**: BRULE-06 (lùi trạng thái bắt buộc lý do + chỉ cấp cao); AI-6 (AI không tự quyết định — pipeline vẫn cần hành động thủ công của HR để rời khỏi `SCREENING`).
**Ngoại lệ**: Cạnh chuyển không hợp lệ → `409 INVALID_STATUS_TRANSITION`.

---

## BP-APP-003 — Rút hồ sơ / Lưu trữ hồ sơ

**Nhánh A — Candidate tự rút (`FN-APP-06`)**: hợp lệ khi trạng thái hiện tại ∈ `{NEW, AI_SCREENING, SCREENING, SHORTLISTED, INTERVIEW}` (tức là **trước** khi có Offer) → chuyển `WITHDRAWN`.

**Nhánh B — HR_MANAGER/ADMIN lưu trữ (`FN-APP-07`)**: hợp lệ ở **bất kỳ trạng thái nào trừ `HIRED`** → chuyển `ARCHIVED`, bắt buộc chọn `archive_reason` (`REJECTED_ARCHIVE` hoặc `TALENT_POOL`).

**Business Rule áp dụng**: BRULE-04 (không lưu trữ hồ sơ đã `HIRED`).

---

## BP-OFFER-001 — Quy trình Offer với 4-eyes Approval

**Actor**: ACT-HR (tạo/nộp/gửi), ACT-HR-MANAGER/ACT-ADMIN (duyệt/từ chối — **không được trùng người tạo**), ACT-CANDIDATE (phản hồi)
**Trigger**: HR quyết định mời 1 ứng viên (thường ở trạng thái `INTERVIEW`) nhận việc
**Tiền điều kiện**: `Application` tồn tại

**Các bước**:
1. **Tạo (`FN-OFFER-02`)**: HR+ tạo `Offer` (lương, lương thử việc, ngày bắt đầu) → `status = DRAFT`, `creator_id = actor`.
2. **Nộp duyệt (`FN-OFFER-03`)**: chủ Offer (hoặc HR_MANAGER/ADMIN) nộp → `DRAFT → PENDING_APPROVAL`.
3. **Duyệt hoặc Từ chối** — rẽ nhánh, chỉ HR_MANAGER/ADMIN:
   - **3a. Duyệt (`FN-OFFER-04`)**: **kiểm tra `actor.id != offer.creator_id`** (4-eyes — nếu vi phạm, chặn ngay + ghi audit `OFFER_SELF_APPROVAL_BLOCKED`, không commit thay đổi trạng thái) → `PENDING_APPROVAL → APPROVED`.
   - **3b. Từ chối (`FN-OFFER-05`)**: bắt buộc `reason` → `PENDING_APPROVAL → DRAFT` (**không phải trạng thái kết thúc** — quay lại bước 1/2, HR sửa và nộp lại được).
4. **Gửi (`FN-OFFER-06`)**: HR+ gửi Offer đã `APPROVED` → `status = SENT`, tính `expires_at = now + offer_validity_days` (mặc định 7 ngày), đồng thời `Application.status → OFFER` → **kích hoạt email `OFFER`**.
5. **Phản hồi (`FN-OFFER-07`)**: Candidate (chủ Offer) Accept hoặc Decline:
   - **Accept**: `Offer → ACCEPTED`, `Application → HIRED` → kiểm tra tự đóng Job (`BP-JOB-001` bước 5) → kích hoạt email `ONBOARDING`.
   - **Decline**: `Offer → DECLINED`, `Application → REJECTED`.

**Hậu điều kiện**: Offer ở trạng thái kết thúc (`ACCEPTED`/`DECLINED`/`EXPIRED`) hoặc đang chờ (`SENT`).
**Business Rule áp dụng**: BRULE-01 (4-eyes), BRULE-08 (hạn phản hồi).
**Ngoại lệ**: mọi bước đều có kiểm tra trạng thái nguồn hợp lệ (`409` nếu sai thứ tự).

---

## BP-OFFER-002 — Offer tự động hết hạn *(logic tồn tại, KHÔNG được kích hoạt tự động — Gap)*

**Actor dự kiến**: ACT-SYSTEM (theo lịch chạy nền)
**Trạng thái triển khai**: `[CONFIRMED logic — MISSING lịch chạy]`. Hàm `offer_service.expire_due_offers(db, system_actor)` **tồn tại đầy đủ và có test** (`tests/`), nhưng **không được gọi ở bất kỳ đâu trong `app/main.py` hay bất kỳ router nào** — không có APScheduler/Celery/cron wiring. Do đó tiến trình này **không bao giờ tự chạy** khi hệ thống vận hành thật; chỉ chạy nếu một đoạn code khác (VD script vận hành thủ công, hoặc test) chủ động gọi hàm.

**Logic (nếu được gọi)**:
1. Quét toàn bộ `Offer.status = SENT` có `expires_at < now`.
2. Với mỗi Offer: `status → EXPIRED`, `Application.status → REJECTED`, ghi audit `OFFER_EXPIRED`.

Xem `20_GAP_ANALYSIS.md` cho khuyến nghị khắc phục (bổ sung APScheduler hoặc cron job gọi định kỳ).

---

## BP-AI-001 — AI Screening hỗ trợ sàng lọc

**Actor**: ACT-HR (trong phạm vi được gán) / ACT-HR-MANAGER/ACT-ADMIN (không giới hạn phạm vi), ACT-SYSTEM (gọi AI Provider/fallback)
**Trigger**: HR muốn có gợi ý mức độ phù hợp giữa CV và JD trước khi quyết định Shortlist/Reject

**Các bước**:
1. HR+ gọi `FN-AI-01` cho 1 Application.
2. **[ACT-SYSTEM]** Kiểm tra phạm vi (HR chỉ được với Application `assigned_hr_id = mình`).
3. **[ACT-SYSTEM]** Lấy text CV mới nhất của Application. Nếu không có → trả `202 Accepted` + `needs_manual_review=true`, **dừng luồng, không coi là lỗi hệ thống**.
4. **[ACT-SYSTEM]** Nếu có text CV: kiểm tra `AI_API_KEY` đã cấu hình chưa.
   - **Có cấu hình**: gọi AI Provider đã chọn (`AI_PROVIDER=gemini` hoặc `claude`) so sánh CV với JD của Job. Nếu lỗi → thử lại 1 lần. Nếu vẫn lỗi → chuyển sang bước fallback.
   - **Không cấu hình, provider không được hỗ trợ, hoặc gọi thật thất bại cả 2 lần**: dùng thuật toán so khớp từ khóa nội bộ (stub) — **Graceful Degradation**, không trả lỗi cho người dùng.
5. **[ACT-SYSTEM]** Lưu bản ghi `AIAnalysis` mới với `is_latest=True`; đặt các bản ghi phân tích trước đó (nếu có) của cùng Application về `is_latest=False` — **giữ nguyên lịch sử, không xóa/ghi đè**.
6. **[ACT-SYSTEM]** Nếu `Application.status` đang ở `NEW` hoặc `AI_SCREENING` → tự chuyển sang `SCREENING`. **Điểm số AI không tự động Shortlist hay Reject** — quyết định tiếp theo luôn do HR thực hiện thủ công qua `BP-APP-002`.

**Business Rule áp dụng**: AI-6 (không tự quyết định số phận hồ sơ), Graceful Degradation (`02_CO_SO_LY_THUYET.md`).

---

## BP-EMAIL-001 — Email tự động theo giai đoạn

**Actor**: ACT-SYSTEM (kích hoạt), ACT-HR-MANAGER/ACT-ADMIN (cấu hình mẫu trước), ACT-HR (gửi thủ công khi cần)
**Trigger**: 1 trong 6 sự kiện nghiệp vụ xảy ra: nộp hồ sơ mới, chuyển `SHORTLISTED`, chuyển `INTERVIEW`, chuyển `REJECTED`, gửi Offer, Candidate Accept Offer

**Các bước**:
1. **[Tiền điều kiện, thực hiện trước, ngoài luồng]** HR_MANAGER/ADMIN đã tạo sẵn mẫu Email `ACTIVE` cho từng loại sự kiện cần dùng (`FN-EMAIL-01`).
2. **[ACT-SYSTEM]** Khi 1 trong 6 sự kiện xảy ra (tại các điểm neo trong `application_service.py`/`offer_service.py` đã liệt kê ở các BP trên), hệ thống gọi `trigger_stage_email()`.
3. **[ACT-SYSTEM]** Tra mẫu `ACTIVE` khớp loại sự kiện. **Nếu không có mẫu nào** → bỏ qua im lặng, **không throw lỗi**, không làm gián đoạn giao dịch chính (VD nộp hồ sơ vẫn thành công dù chưa cấu hình mẫu email).
4. **[ACT-SYSTEM]** Nếu có mẫu: thay thế biến `{{ten_bien}}` bằng giá trị thật (tên ứng viên, tên vị trí, tên công ty...) → gửi qua SMTP nếu đã cấu hình (`SMTP_USER`/`SMTP_PASSWORD`), ngược lại ghi log giả lập (Graceful Degradation) → ghi vào `audit_logs` (không có bảng log email riêng, chỉ lưu `{to, subject}`, không lưu `body` đầy đủ — Gap EMAIL-10).

**Nhánh gửi thủ công (`FN-EMAIL-05`)**: HR+ tự chọn mẫu và gửi bất kỳ lúc nào cho 1 Application, cùng cơ chế render + gửi ở bước 4, nhưng khởi động bởi hành động người dùng thay vì sự kiện hệ thống.

**Business Rule áp dụng**: EMAIL-7 (im lặng bỏ qua), Graceful Degradation.

---

*Tài liệu tiếp theo: `10_BPMN.md` (sơ đồ hóa các BP ở trên bằng Mermaid).*
