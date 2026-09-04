# 13 — SYSTEM MODELING (Business → Requirement → Use Case → Process → Design → Code → Database)

**Mục đích**: cầu nối ở mức **module** (10 module) giữa toàn bộ tài liệu 05–12 đã hoàn thành, giúp người đọc thấy được bức tranh tổng thể trước khi đi vào chi tiết kiến trúc (`14`) và UML (`15`). Đây **không phải** ma trận truy vết đầy đủ ở mức từng dòng — ma trận đầy đủ (`BR-XXX` → `FR-XXX` → `UC-XXX` → API → Entity → dòng code) được dựng ở `19_TRACEABILITY_MATRIX.md` (Đợt 7), sau khi toàn bộ tài liệu 05–18 đã hoàn tất.

| Module | BR liên quan (05) | Số FR (06) | Actor chính (07) | Số UC (11/12) | BP liên quan (09/10) | Router/Service file (Design→Code) | Bảng CSDL chính (16) |
|---|---|---|---|---|---|---|---|
| MOD-AUTH | BR-007 | 8 | Tất cả | 4 | (nền tảng, không có BP riêng) | `routers/auth.py` → `services/auth_service.py` | `users` |
| MOD-USER | BR-007 | 4 | HR_MANAGER, ADMIN | 2 | (nền tảng) | `routers/users.py` | `users` |
| MOD-DEPT | BR-001 | 2 | HR_MANAGER, ADMIN | 2 | BP-JOB-001 (gián tiếp) | `routers/departments.py` | `departments` |
| MOD-JOB | BR-001, BR-003 | 6 | HR_MANAGER, ADMIN, CANDIDATE | 5 | BP-JOB-001 | `routers/jobs.py` | `jobs`, `departments` |
| MOD-APP | BR-001, BR-003, BR-007, BR-008 | 19 | CANDIDATE, HR, HR_MANAGER, ADMIN | 7 | BP-APP-001, BP-APP-002, BP-APP-003 | `routers/applications.py` → `services/application_service.py`, `services/resume_service.py` | `applications`, `candidates`, `resumes` |
| MOD-OFFER | BR-002, BR-003 | 12 | HR, HR_MANAGER, ADMIN, CANDIDATE | 8 | BP-OFFER-001, BP-OFFER-002 | `routers/offers.py` → `services/offer_service.py` | `offers` |
| MOD-EMAIL | BR-005 | 9 | HR_MANAGER, ADMIN, HR | 5 | BP-EMAIL-001 | `routers/email_templates.py` → `services/email_service.py` | `email_templates`, `audit_logs` |
| MOD-AI | BR-004 | 7 | HR, HR_MANAGER, ADMIN | 2 | BP-AI-001 | `routers/ai.py` → `services/ai_service.py` | `ai_analyses` |
| MOD-DASH | BR-006 | 4 | HR, HR_MANAGER, ADMIN | 1 | (tổng hợp, không có BP riêng — chỉ đọc) | `routers/dashboard.py` | (đọc tổng hợp `applications`, `jobs`, `offers`) |
| MOD-AUDIT | BR-008 | 3 | HR_MANAGER, ADMIN | 1 | (xuyên suốt, ghi từ mọi service khác) | `routers/audit.py` → `services/audit_service.py` | `audit_logs` |

## Quan sát liên module quan trọng

`[CONFIRMED]` — 3 điểm mấu chốt kết nối các module với nhau, không thể thấy nếu chỉ đọc từng module riêng lẻ:

1. **MOD-APP ↔ MOD-OFFER**: `Application.status` chỉ chuyển sang `OFFER`/`HIRED`/`REJECTED` (do Offer) thông qua `offer_service.py`, **không đi qua** `PUT /applications/{id}/status` của MOD-APP — đây là ràng buộc kiến trúc bảo vệ tính toàn vẹn của quy trình 4-eyes (nếu không, HR có thể "giả lập" một Offer đã duyệt mà không hề tồn tại).
2. **MOD-APP/MOD-OFFER → MOD-EMAIL**: Cả 2 module không tự gửi email — chúng đều **gọi vào** `email_service.trigger_stage_email()` tại các điểm neo cụ thể (6 điểm, liệt kê ở BP-EMAIL-001). MOD-EMAIL là module bị động (reactive), không có tiến trình tự khởi động.
3. **MOD-APP/MOD-OFFER/MOD-JOB/MOD-USER/MOD-EMAIL → MOD-AUDIT**: Tương tự, `audit_service.log()` được gọi rải rác từ nhiều service khác — MOD-AUDIT không có logic nghiệp vụ riêng, chỉ là 1 bảng ghi nhận (write sink) dùng chung.

## Điểm dữ liệu mới phát hiện khi đọc models (Đợt 5) — bổ sung cho `04`/`06`

`[CONFIRMED — bổ sung]`: khi đọc trực tiếp `app/models/department.py` để chuẩn bị Class Diagram (`15`), phát hiện `DepartmentStatus` (`ACTIVE`/`INACTIVE`) — một enum **không nằm trong `app/models/enums.py`** (nơi tập trung mọi enum khác) mà định nghĩa cục bộ ngay trong `department.py`. Đây là điểm chưa từng ghi nhận ở `00`/`04`/`06`. Không có endpoint nào đọc/ghi trường này (không route nào set `Department.status = INACTIVE`) — trường tồn tại nhưng không được sử dụng nghiệp vụ, tương tự tình trạng của `Job.slug` (JOB-7). Bổ sung vào `20_GAP_ANALYSIS.md`.

Tương tự, `app/models/candidate.py` có enum `Gender` (`MALE`/`FEMALE`/`OTHER`) cũng định nghĩa cục bộ ngoài `enums.py`, và các trường `gender`, `date_of_birth`, `address`, `current_salary`, `expected_salary` trên `Candidate` **không có trường nào trong số này được ghi nhận bởi bất kỳ endpoint nào** (không có trong `ApplyRequest`, không có route sửa hồ sơ Candidate) — dữ liệu tồn tại ở tầng CSDL nhưng không có đường nghiệp vụ nào để nhập liệu qua API hiện tại. Bổ sung vào `20_GAP_ANALYSIS.md`.

---

*Tài liệu tiếp theo: `14_SYSTEM_ARCHITECTURE.md`, `15_UML.md`.*
