# SOFTWARE REQUIREMENTS SPECIFICATION (SRS) — ATS v2.1

**Phạm vi**: `ats-v2/`. **Nguồn**: `04_KHAO_SAT_YEU_CAU.md` (yêu cầu thô) + `05_BRD.md` (mục tiêu business). **ID Scheme**: `FR-<MOD>-XXX`, `NFR-<CATEGORY>-XXX` — xem `01_MASTER_DOCUMENT_OUTLINE.md` mục A.3 (đã cập nhật thêm 2 category `SCA`, `AVA` ở Đợt 2 này).

**Nguyên tắc gán ID**: Chỉ những yêu cầu có nhãn `[CONFIRMED]` hoặc `[INFERRED]` ở `04` mới được gán `FR-XXX` chính thức (vì đây là năng lực **thực sự tồn tại** trong hệ thống). Yêu cầu `[MISSING]` **không được gán FR** (tránh đặc tả một chức năng không tồn tại như thể nó tồn tại — vi phạm RULE 1) — thay vào đó được liệt kê ở cột "Ghi chú/Gap" của mục tương ứng và tổng hợp đầy đủ ở `20_GAP_ANALYSIS.md`.

---

## 1. FR-AUTH — Xác thực & Tài khoản (nguồn: `AUTH-1..11`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-AUTH-001` | Hệ thống phải cho phép `ACT-CANDIDATE` tự đăng ký tài khoản bằng họ tên, email, mật khẩu, SĐT (tùy chọn); vai trò được gán cứng là `CANDIDATE`, client không thể chọn vai trò khác | CANDIDATE | Đã triển khai (P0) | BR-007 | AUTH-1, AUTH-11 |
| `FR-AUTH-002` | Hệ thống phải từ chối mật khẩu không đạt: tối thiểu 8 ký tự, có ít nhất 1 chữ cái và 1 chữ số | CANDIDATE | Đã triển khai (P0) | BR-007 | AUTH-2 |
| `FR-AUTH-003` | Hệ thống phải xác thực bằng email + mật khẩu và trả về cặp Access Token (JWT) + Refresh Token khi thành công | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-3 |
| `FR-AUTH-004` | Access Token phải có thời hạn hiệu lực 8 giờ | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-4 |
| `FR-AUTH-005` | Refresh Token phải có hạn 30 ngày và được lưu trữ dưới dạng băm SHA-256, không lưu plaintext | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-5 |
| `FR-AUTH-006` | Hệ thống phải cho phép dùng Refresh Token hợp lệ để cấp Access Token mới mà không cần đăng nhập lại | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-6 |
| `FR-AUTH-007` | Hệ thống phải cho phép người dùng đã đăng nhập xem thông tin tài khoản hiện tại của chính mình | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-7 |
| `FR-AUTH-008` | Hệ thống chỉ cho phép đăng nhập nếu trạng thái tài khoản là `ACTIVE` | Tất cả | Đã triển khai (P0) | BR-007 | AUTH-8 |

**Gap (không gán FR)**: khôi phục mật khẩu (AUTH-9, `[MISSING]`), xác thực email lúc đăng ký (AUTH-10, `[MISSING]`).

## 2. FR-USER — Quản lý người dùng nội bộ (nguồn: `USER-1..6`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-USER-001` | `ACT-ADMIN` phải tạo được tài khoản nội bộ với vai trò `HR`, `HR_MANAGER`, hoặc `ADMIN` | ADMIN | Đã triển khai (P0) | BR-007 | USER-1 |
| `FR-USER-002` | `ACT-HR-MANAGER` chỉ được tạo tài khoản vai trò `HR` | HR_MANAGER | Đã triển khai (P0) | BR-007 | USER-2 |
| `FR-USER-003` | `ACT-HR` không được phép tạo bất kỳ tài khoản nào (hệ thống phải từ chối với lỗi phân quyền) | HR | Đã triển khai (P0) | BR-007 | USER-3 |
| `FR-USER-004` | Hệ thống phải liệt kê được tài khoản nội bộ, hỗ trợ lọc theo vai trò, và loại trừ tài khoản `CANDIDATE` khỏi danh sách này | HR_MANAGER, ADMIN (endpoint yêu cầu `require_hr_manager_or_admin` — `ACT-HR` không xem được danh sách này) | Đã triển khai (P1) | BR-007 | USER-4 |

**Gap**: sửa/khóa/xóa tài khoản đã tạo (USER-5, `[MISSING]`), tự đổi mật khẩu (USER-6, `[MISSING]`).

## 3. FR-DEPT — Phòng ban (nguồn: `DEPT-1..3`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-DEPT-001` | `ACT-HR-MANAGER`/`ACT-ADMIN` phải tạo được phòng ban với tên và mô tả | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-001 | DEPT-1 |
| `FR-DEPT-002` | Mọi vai trò phải xem được danh sách phòng ban | Tất cả | Đã triển khai (P1) | BR-001 | DEPT-2 |

**Gap**: sửa/xóa phòng ban (DEPT-3, `[MISSING]`).

## 4. FR-JOB — Tin tuyển dụng (nguồn: `JOB-1..8`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-JOB-001` | `ACT-HR-MANAGER`/`ACT-ADMIN` phải tạo được tin tuyển dụng đầy đủ (tiêu đề, phòng ban, mô tả, yêu cầu, khoảng lương, số lượng, địa điểm, hình thức làm việc) | HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-001 | JOB-1 |
| `FR-JOB-002` | Hệ thống phải cho phép gán `ACT-HR` phụ trách 1 tin, lúc tạo hoặc sau đó | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-001 | JOB-2 |
| `FR-JOB-003` | Hệ thống phải cho phép chuyển 1 tin từ `DRAFT` sang `PUBLISHED` trong một bước duy nhất | HR_MANAGER, ADMIN | Đã triển khai — đơn giản hóa so với quy trình duyệt nhiều bước (P0) | BR-001 | JOB-3 |
| `FR-JOB-004` | `ACT-CANDIDATE` chỉ được xem các tin ở trạng thái `PUBLISHED` | CANDIDATE | Đã triển khai (P0) | BR-001 | JOB-4 |
| `FR-JOB-005` | Hệ thống phải hỗ trợ tìm kiếm theo tiêu đề, lọc theo phòng ban, và (với vai trò không phải Candidate) lọc theo trạng thái | Tất cả | Đã triển khai (P1) | BR-001 | JOB-5 |
| `FR-JOB-006` | Hệ thống phải tự động chuyển tin sang `CLOSED` khi số lượng ứng viên `HIRED` đạt đủ chỉ tiêu (`quantity`) | ACT-SYSTEM | Đã triển khai (P0) | BR-003 (BRULE-03) | JOB-6 |

**Gap**: route công khai theo `slug` (JOB-7, `[CONFIRMED một phần]` — trường tồn tại nhưng không dùng), quy trình duyệt Requisition nhiều bước (JOB-8, `[CONFIRMED enum — MISSING logic]`).

## 5. FR-APP — Hồ sơ ứng tuyển (nguồn: `APP-1..20`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-APP-001` | Chỉ `ACT-CANDIDATE` được nộp hồ sơ ứng tuyển cho 1 Job | CANDIDATE | Đã triển khai (P0) | BR-001 | APP-1 |
| `FR-APP-002` | Hệ thống phải bắt buộc `ai_consent=true` mới cho phép nộp hồ sơ | CANDIDATE | Đã triển khai (P0) | BR-001, BR-004 | APP-2 |
| `FR-APP-003` | Hệ thống phải chống nộp trùng ngoài ý muốn thông qua `Idempotency-Key`, đảm bảo cùng 1 key không tạo 2 bản ghi | CANDIDATE | Đã triển khai (P0) | BR-001 | APP-3 |
| `FR-APP-004` | Hệ thống không được áp đặt giới hạn thời gian giữa các lần ứng tuyển lại cùng 1 Job | CANDIDATE | Đã triển khai (P0) | BR-003 (BRULE-02) | APP-4 |
| `FR-APP-005` | Mỗi lần ứng tuyển hợp lệ phải tạo 1 bản ghi Application mới; bản ghi cũ không bị ghi đè | ACT-SYSTEM | Đã triển khai (P0) | BR-001 | APP-5 |
| `FR-APP-006` | Hệ thống phải cho phép Candidate dán trực tiếp nội dung CV dạng text lúc nộp hồ sơ | CANDIDATE | Đã triển khai (P1) | BR-001 | APP-6 |
| `FR-APP-007` | Hệ thống phải cho phép Candidate tải lên file CV thật (PDF/DOCX) lúc nộp hoặc sau đó | CANDIDATE | Đã triển khai (P0) | BR-001 | APP-7 |
| `FR-APP-008` | Hệ thống phải giới hạn file CV ở định dạng PDF/DOCX, dung lượng ≤10MB, và xác thực bằng magic-bytes khớp với phần mở rộng khai báo | CANDIDATE | Đã triển khai (P0) | BR-007 (an toàn dữ liệu) | APP-8 |
| `FR-APP-009` | Nếu không trích xuất được text từ file CV, hệ thống vẫn phải lưu file nhưng đánh dấu `needs_manual_review` | ACT-SYSTEM | Đã triển khai (P1) | BR-001 | APP-9 |
| `FR-APP-010` | Trạng thái Application phải tuân theo máy trạng thái 10 giá trị; mọi thay đổi trạng thái phải được xác thực phía server | HR+ | Đã triển khai (P0) | BR-001 | APP-10 |
| `FR-APP-011` | `ACT-HR` chỉ được chuyển trạng thái tiến (forward) hoặc sang `REJECTED`; không được lùi trạng thái | HR | Đã triển khai (P0) | BR-001 | APP-11 |
| `FR-APP-012` | `ACT-HR-MANAGER`/`ACT-ADMIN` được lùi trạng thái nhưng bắt buộc nhập lý do và hệ thống phải ghi vào Audit Log | HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-001, BR-008 (BRULE-06) | APP-12 |
| `FR-APP-013` | `ACT-CANDIDATE` phải tự rút được hồ sơ của mình khi hồ sơ chưa có Offer | CANDIDATE | Đã triển khai (P1) | BR-001 | APP-13 |
| `FR-APP-014` | `ACT-HR-MANAGER`/`ACT-ADMIN` phải lưu trữ (archive) được hồ sơ bất kỳ lúc nào trừ khi đã `HIRED`, bắt buộc chọn lý do | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-001 (BRULE-04) | APP-14 |
| `FR-APP-015` | `ACT-HR` chỉ được xem/thao tác Application được gán cho mình; `ACT-HR-MANAGER`/`ACT-ADMIN` không giới hạn | HR, HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-007 (BRULE-05) | APP-15 |
| `FR-APP-016` | Trường `assigned_hr_id` của Application phải tự kế thừa từ Job tại thời điểm nộp hồ sơ | ACT-SYSTEM | Đã triển khai (P1) | BR-007 | APP-16 |
| `FR-APP-017` | Hệ thống phải hỗ trợ tìm kiếm theo tên/email/SĐT ứng viên và lọc theo Job | HR+ | Đã triển khai (P1) | BR-001 | APP-17 |
| `FR-APP-018` | Hệ thống không được cung cấp chức năng xóa vật lý Application | ACT-SYSTEM | Đã triển khai — chủ đích (P0) | BR-008 | APP-18 |
| `FR-APP-019` | Candidate có email trùng với lần nộp trước phải được tái sử dụng bản ghi Candidate, không tạo bản ghi trùng | ACT-SYSTEM | Đã triển khai (P1) | BR-001 | APP-19 |

**Gap**: lên lịch/ghi kết quả phỏng vấn qua API (APP-20, `[MISSING]` — model tồn tại, không có router).

## 6. FR-OFFER — Thư mời nhận việc (nguồn: `OFFER-1..12`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-OFFER-001` | `ACT-HR`+ phải tạo được Offer (lương chính thức, lương thử việc, ngày bắt đầu) gắn với 1 Application | HR+ | Đã triển khai (P0) | BR-002 | OFFER-1 |
| `FR-OFFER-002` | Offer phải được "Nộp duyệt" (Submit) trước khi có thể duyệt | HR+ | Đã triển khai (P0) | BR-002 | OFFER-2 |
| `FR-OFFER-003` | Hệ thống phải ngăn người tạo Offer tự duyệt Offer của chính mình, thực thi ở cả tầng service và ràng buộc CSDL | HR_MANAGER, ADMIN | Đã triển khai — 2 lớp (P0) | BR-002 (BRULE-01) | OFFER-3 |
| `FR-OFFER-004` | Chỉ `ACT-HR-MANAGER`/`ACT-ADMIN` được duyệt/từ chối Offer | HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-002 | OFFER-4 |
| `FR-OFFER-005` | Offer bị từ chối duyệt phải quay về `DRAFT` (không phải trạng thái kết thúc) và bắt buộc nhập lý do | HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-002 | OFFER-5 |
| `FR-OFFER-006` | Hệ thống chỉ cho gửi (Send) Offer khi trạng thái đã là `APPROVED` | HR+ | Đã triển khai (P0) | BR-002 | OFFER-6 |
| `FR-OFFER-007` | Offer phải có hạn phản hồi xác định, mặc định 7 ngày kể từ lúc gửi, cấu hình được | ACT-SYSTEM | Đã triển khai (P1) | BR-002 (BRULE-08) | OFFER-7 |
| `FR-OFFER-008` | `ACT-CANDIDATE` phải phản hồi được Accept/Decline, chỉ với Offer của chính mình | CANDIDATE | Đã triển khai (P0) | BR-002 | OFFER-8 |
| `FR-OFFER-009` | Khi Candidate Accept, Application phải chuyển `HIRED` và hệ thống phải tự kiểm tra đóng Job nếu đủ quota | ACT-SYSTEM | Đã triển khai (P0) | BR-002, BR-003 | OFFER-9 |
| `FR-OFFER-010` | Khi Candidate Decline, Application phải chuyển `REJECTED` | ACT-SYSTEM | Đã triển khai (P0) | BR-002 | OFFER-10 |
| `FR-OFFER-011` | Hệ thống phải cung cấp logic chuyển Offer quá hạn sang `EXPIRED` (và Application liên quan sang `REJECTED`) | ACT-SYSTEM | Logic đã triển khai — **kích hoạt tự động còn thiếu (Gap)** (P1) | BR-002 | OFFER-11 |
| `FR-OFFER-012` | Chỉ Candidate liên quan, HR được gán/người tạo, hoặc `ACT-HR-MANAGER`/`ACT-ADMIN` được xem 1 Offer cụ thể | Tất cả | Đã triển khai (P0) | BR-007 | OFFER-12 |

## 7. FR-EMAIL — Email Tự động (nguồn: `EMAIL-1..10`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-EMAIL-001` | `ACT-HR-MANAGER`/`ACT-ADMIN` phải tạo/sửa được mẫu Email; `ACT-HR` chỉ xem | HR+ | Đã triển khai (P1) | BR-005 | EMAIL-1 |
| `FR-EMAIL-002` | "Xóa" mẫu Email phải là vô hiệu hóa (soft-delete), không xóa vật lý | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-005 | EMAIL-2 |
| `FR-EMAIL-003` | Mỗi mẫu phải gắn với đúng 1 trong 7 loại sự kiện cố định | HR+ | Đã triển khai (P1) | BR-005 | EMAIL-3 |
| `FR-EMAIL-004` | Nội dung mẫu phải hỗ trợ biến `{{ten_bien}}`, được thay thế lúc gửi | ACT-SYSTEM | Đã triển khai (P1) | BR-005 | EMAIL-4 |
| `FR-EMAIL-005` | `ACT-HR`+ phải gửi được email thủ công tới ứng viên của 1 Application bằng mẫu có sẵn | HR+ | Đã triển khai (P1) | BR-005 | EMAIL-5 |
| `FR-EMAIL-006` | Hệ thống phải tự động gửi email khi: nộp hồ sơ, chuyển `SHORTLISTED`, chuyển `INTERVIEW`, chuyển `REJECTED`, gửi Offer, Candidate Accept Offer | ACT-SYSTEM | Đã triển khai (P0) | BR-005 | EMAIL-6 |
| `FR-EMAIL-007` | Nếu chưa có mẫu `ACTIVE` cho loại sự kiện, hệ thống phải bỏ qua im lặng, không làm gián đoạn giao dịch chính | ACT-SYSTEM | Đã triển khai (P0) | BR-005 | EMAIL-7 |
| `FR-EMAIL-008` | Hệ thống phải gửi thật qua SMTP nếu có cấu hình; ngược lại ghi log giả lập (graceful degradation) | ACT-SYSTEM | Đã triển khai (P0) | BR-005 | EMAIL-8 |
| `FR-EMAIL-009` | Hệ thống phải ghi nhận việc gửi email vào `audit_logs` (không có bảng log riêng) | ACT-SYSTEM | Đã triển khai (P2) | BR-008 | EMAIL-9 |

**Gap**: xem lại nội dung đầy đủ (đã render) của email đã gửi (EMAIL-10, `[MISSING]` — chỉ lưu `{to, subject}`).

## 8. FR-AI — AI Screening (nguồn: `AI-1..8`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-AI-001` | `ACT-HR`+ phải kích hoạt được phân tích AI cho 1 Application, so sánh CV với JD của Job | HR+ | Đã triển khai (P0) | BR-004 | AI-1 |
| `FR-AI-002` | `ACT-HR` chỉ phân tích được Application được gán cho mình | HR | Đã triển khai (P0) | BR-007 | AI-2 |
| `FR-AI-003` | Nếu chưa có text CV, hệ thống phải trả `202 Accepted` kèm cờ cần xem thủ công thay vì báo lỗi | ACT-SYSTEM | Đã triển khai (P1) | BR-004 | AI-3 |
| `FR-AI-004` | Hệ thống phải gọi AI Provider thật (chọn được nhà cung cấp qua cấu hình — hiện hỗ trợ Gemini và Claude) nếu có cấu hình API key; thử lại 1 lần khi lỗi; nếu vẫn lỗi hoặc chưa cấu hình, chuyển sang chế độ so khớp từ khóa nội bộ (graceful degradation) | ACT-SYSTEM | Đã triển khai (P0) | BR-004 | AI-4 |
| `FR-AI-005` | Hệ thống phải giữ toàn bộ lịch sử các lần phân tích (không ghi đè), đánh dấu bản mới nhất bằng cờ `is_latest` | ACT-SYSTEM | Đã triển khai (P1) | BR-008 | AI-5 |
| `FR-AI-006` | Kết quả AI không được tự động quyết định số phận hồ sơ; chỉ được phép tự chuyển trạng thái kỹ thuật `NEW`/`AI_SCREENING` → `SCREENING`, các quyết định Shortlist/Reject vẫn do con người thực hiện thủ công | ACT-SYSTEM | Đã triển khai (P0) | BR-004 (BRULE-07) | AI-6 |
| `FR-AI-007` | `ACT-CANDIDATE` không được phép truy cập kết quả phân tích AI về hồ sơ của chính mình (giới hạn chủ đích) | — (ràng buộc phủ định) | Đã triển khai (P1) | BR-007 | AI-8 |

**Gap**: giới hạn chi phí gọi AI theo tháng (AI-7, `[MISSING]` — có field cấu hình nhưng không có logic đếm/chặn).

## 9. FR-DASH — Dashboard (nguồn: `DASH-1..4`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-DASH-001` | Hệ thống phải hiển thị số liệu tổng hợp: tổng Job/Job đã đăng, tổng Application, phân bố theo trạng thái, số đã tuyển, tỷ lệ nhận Offer, thời gian tuyển trung bình, phân bố theo nguồn | HR+ | Đã triển khai (P0) | BR-006 | DASH-1 |
| `FR-DASH-002` | `ACT-HR-MANAGER`/`ACT-ADMIN` phải thấy thêm bảng hiệu suất theo từng nhân viên HR | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-006 | DASH-2 |
| `FR-DASH-003` | `ACT-HR` chỉ được xem số liệu trong phạm vi Job/Application được gán cho mình | HR | Đã triển khai (P0) | BR-007 | DASH-3 |
| `FR-DASH-004` | `ACT-CANDIDATE` không được truy cập Dashboard | — (ràng buộc phủ định) | Đã triển khai (P0) | BR-007 | DASH-4 |

## 10. FR-AUDIT — Nhật ký Audit (nguồn: `AUDIT-1..3`)

| ID | Yêu cầu chức năng | Actor | Ưu tiên | BR liên quan | Nguồn |
|---|---|---|---|---|---|
| `FR-AUDIT-001` | Hệ thống phải ghi log cho các hành động nhạy cảm được chọn lọc trước (không ghi mọi thao tác CRUD) | ACT-SYSTEM | Đã triển khai (P0) | BR-008 | AUDIT-1 |
| `FR-AUDIT-002` | Hệ thống phải cho xem log, lọc theo loại đối tượng và mã đối tượng | HR_MANAGER, ADMIN | Đã triển khai (P1) | BR-008 | AUDIT-2 |
| `FR-AUDIT-003` | Chỉ `ACT-HR-MANAGER`/`ACT-ADMIN` được xem Audit Log | HR_MANAGER, ADMIN | Đã triển khai (P0) | BR-008 | AUDIT-3 |

---

## 11. NON-FUNCTIONAL REQUIREMENTS

### 11.1 `NFR-SEC` — Security

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-SEC-001` | Xác thực phải dùng JWT + Refresh Token; mật khẩu phải băm bằng bcrypt (`passlib`); phân quyền phải theo role + phạm vi dữ liệu (row-level); file upload phải được xác thực bằng magic-bytes; các bất biến nghiệp vụ quan trọng (4-eyes) phải được ràng buộc thêm ở tầng CSDL (CHECK constraint), không chỉ ở tầng service | `[CONFIRMED]` Đã triển khai |
| `NFR-SEC-002` | Cấu hình CORS không được kết hợp `allow_origins=["*"]` với `allow_credentials=True` (tổ hợp không hợp lệ theo chuẩn CORS trình duyệt khi dùng cookie) | `[CONFIRMED — VI PHẠM hiện tại]` `app/main.py` đang cấu hình tổ hợp này; hiện chưa gây lỗi vì frontend dùng Bearer token (không dùng cookie), nhưng là nợ kỹ thuật cần sửa nếu sau này chuyển sang cookie-based session — xem `20_GAP_ANALYSIS.md` |
| `NFR-SEC-003` | File CV tải lên phải được quét virus trước khi lưu trữ | `[MISSING]` |

### 11.2 `NFR-REL` — Reliability (gồm Data Integrity)

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-REL-001` | Các tích hợp bên ngoài (AI, Email) phải có cơ chế retry và graceful degradation khi dịch vụ lỗi hoặc chưa cấu hình | `[CONFIRMED]` Đã triển khai |
| `NFR-REL-002` | Offer quá hạn phải tự động chuyển trạng thái mà không cần can thiệp thủ công | `[CONFIRMED logic — MISSING lịch chạy nền]` Hàm tồn tại, không được gọi tự động |
| `NFR-REL-003` | Máy trạng thái nghiệp vụ (Application, Offer) phải được xác thực phía server, không tin tưởng client | `[CONFIRMED]` Đã triển khai |
| `NFR-REL-004` | Các ràng buộc duy nhất/toàn vẹn (UNIQUE, CHECK) phải được thực thi ở tầng CSDL, không chỉ ở tầng ứng dụng | `[CONFIRMED]` Đã triển khai |
| `NFR-REL-005` | Sinh Business ID phải an toàn khi có truy cập đồng thời (concurrency-safe) | `[CONFIRMED]` Đã triển khai qua row lock trên `id_sequences` |

### 11.3 `NFR-MAIN` — Maintainability

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-MAIN-001` | Kiến trúc phải phân lớp rõ ràng (Router/Service/Model) | `[CONFIRMED]` Đã triển khai |
| `NFR-MAIN-002` | Phải có bộ kiểm thử tự động bao phủ các luồng nghiệp vụ chính | `[CONFIRMED]` 48 test pytest + 3 script E2E |
| `NFR-MAIN-003` | Định danh nghiệp vụ hiển thị phải có tiền tố nhất quán theo loại thực thể | `[CONFIRMED]` Đã triển khai |

### 11.4 `NFR-LOG` — Logging & Auditability & Monitoring

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-LOG-001` | Hành động nhạy cảm phải ghi actor, hành động, dữ liệu trước/sau vào `audit_logs` | `[CONFIRMED]` Đã triển khai |
| `NFR-LOG-002` | Hệ thống phải có application-level logging có cấu hình (không chỉ audit trail nghiệp vụ) | `[MISSING]` |
| `NFR-LOG-003` | Hệ thống phải cung cấp endpoint kiểm tra sức khỏe (`/health`) | `[CONFIRMED một phần]` Có endpoint đơn giản, không có APM/structured logging tập trung |

### 11.5 `NFR-PERF` — Performance

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-PERF-001` | Hệ thống phải đáp ứng mục tiêu thời gian phản hồi đã đo lường (benchmark) | `[MISSING]` |
| `NFR-PERF-002` | Hệ thống phải có chiến lược cache cho dữ liệu truy vấn thường xuyên | `[MISSING]` |

### 11.6 `NFR-SCA` — Scalability

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-SCA-001` | Hệ thống phải được kiểm thử tải và có cấu hình chạy nhiều instance | `[MISSING]` |

### 11.7 `NFR-AVA` — Availability

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-AVA-001` | Hệ thống phải có SLA xác định và cơ chế giám sát uptime | `[MISSING]` |

### 11.8 `NFR-USA` — Usability & Compatibility

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| `NFR-USA-001` | Giao diện phải có responsive layout cơ bản | `[CONFIRMED một phần]` Có class Tailwind `sm:`/`lg:` trong `index.html` |
| `NFR-USA-002` | Giao diện phải được kiểm thử đa trình duyệt | `[MISSING]` |

---

## 12. Ghi chú tổng kết

Tổng số `FR-XXX` đã gán trong tài liệu này: **74** (AUTH 8, USER 4, DEPT 2, JOB 6, APP 19, OFFER 12, EMAIL 9, AI 7, DASH 4, AUDIT 3 = 74; `[MISSING]` — không tính). Tổng số `NFR-XXX`: **20** (SEC 3, REL 5, MAIN 3, LOG 3, PERF 2, SCA 1, AVA 1, USA 2), trong đó 7 mục `[MISSING]` hoàn toàn (`NFR-SEC-003`, `NFR-LOG-002`, `NFR-PERF-001/002`, `NFR-SCA-001`, `NFR-AVA-001`, `NFR-USA-002`) và 3 mục `[CONFIRMED một phần]` (`NFR-REL-002`, `NFR-LOG-003`, `NFR-USA-001`). Toàn bộ ID trên sẽ được tái sử dụng nguyên vẹn ở `07`–`19` theo RULE 6, không đánh số lại.

*Tài liệu tiếp theo: `07_USER_ROLE_PERMISSION.md`.*
