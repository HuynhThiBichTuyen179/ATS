# 03 — PHƯƠNG PHÁP KHẢO SÁT VÀ THU THẬP YÊU CẦU

## 1. Mục tiêu khảo sát

Xác định đầy đủ và chính xác các yêu cầu nghiệp vụ, chức năng, phi chức năng của hệ thống `ats-v2/` **dựa trên bằng chứng khách quan** (source code, database, test, cấu hình đang tồn tại), làm nền tảng xây dựng BRD/SRS/UML/ERD nhất quán với hệ thống thực tế — không dựa trên suy đoán về "một ATS điển hình nên có gì".

## 2. Đối tượng khảo sát

`[CONFIRMED]` — khác với một dự án khảo sát yêu cầu mới (nơi đối tượng là con người: người dùng nghiệp vụ, quản lý), đối tượng khảo sát của bài tập reverse-engineering này là:

| Đối tượng | Vai trò trong khảo sát |
|---|---|
| Source code (`app/`) | Nguồn sự thật chính (Source of Truth) — mọi hành vi hệ thống được suy ra trực tiếp từ đây |
| Test suite (`tests/`, `scripts/smoke_*.py`) | Đóng vai trò "đặc tả thực thi được" (executable specification) — test pass xác nhận hành vi đã được implement đúng như mô tả trong test |
| Configuration (`.env.example`, `app/core/config.py`) | Xác định tham số vận hành, tích hợp bên ngoài |
| Database schema (định nghĩa qua SQLAlchemy model) | Xác định cấu trúc dữ liệu thật |
| Tài liệu có sẵn (`README.md`, `CONFLICT_REPORT_AND_BACKLOG.md`) | Bổ sung ngữ cảnh — đối chiếu chéo với code để phát hiện mâu thuẫn |
| Người dùng (trong phiên trao đổi hiện tại) | Đóng vai trò stakeholder xác nhận phạm vi và các quyết định mở (VD OQ-01) |

`[MISSING]` — không có: người dùng nghiệp vụ thật (HR/Candidate thật), tài liệu yêu cầu gốc do khách hàng cung cấp trước khi code, biên bản họp/phỏng vấn.

## 3. Phương pháp khảo sát

`[CONFIRMED]` — phương pháp chủ đạo là **Static Code Analysis** kết hợp **Dynamic/Test-based Verification**:

1. **Đọc trực tiếp source code** theo từng lớp (router → service → model), lần theo luồng gọi hàm để suy ra business logic thật.
2. **Chạy thử hệ thống** (`uvicorn`) và test suite (`pytest`, 3 script E2E) để xác nhận hành vi mô tả trong code thực sự diễn ra khi chạy (không chỉ đọc tĩnh).
3. **Đối chiếu chéo** giữa các nguồn (code vs. test vs. tài liệu có sẵn) để phát hiện mâu thuẫn (Documentation Mismatch — xem `00_PROJECT_DISCOVERY.md` mục 12).
4. **Trích xuất bằng chứng có thể tham chiếu** (file + tên hàm/class/biến) cho mỗi khẳng định, thay vì mô tả chung chung.

## 4. Phỏng vấn

`[MISSING]` — không thực hiện được vì không có stakeholder nghiệp vụ thật (HR, Candidate, Ban Giám đốc) tham gia bài tập này. Thay thế một phần bằng việc người dùng hiện tại (đóng vai trò Product Owner/Sponsor trong toàn bộ quá trình xây dựng `ats-v2/`) xác nhận trực tiếp các quyết định thiết kế trong lịch sử trao đổi (VD: quyết định 4-eyes approval cho Offer, quyết định bỏ cooldown 90 ngày, quyết định Business ID có tiền tố).

## 5. Quan sát nghiệp vụ

`[MISSING]` — không có môi trường vận hành thật với người dùng thật để quan sát. Thay thế bằng việc chạy thử các luồng nghiệp vụ qua 3 script E2E (`scripts/smoke_e2e.py`, `smoke_audit_fixes.py`, `smoke_new_features.py`) mô phỏng đúng trình tự thao tác một người dùng thật sẽ thực hiện qua giao diện, xác nhận hành vi hệ thống phản hồi đúng như thiết kế.

## 6. Phân tích tài liệu

`[CONFIRMED]` — đã đọc và đối chiếu:
- `README.md` — mô tả tính năng, hướng dẫn chạy, tài khoản seed.
- `CONFLICT_REPORT_AND_BACKLOG.md` — lịch sử các thay đổi nghiệp vụ (CHANGE 01/02/03), audit phát hiện lỗi, backlog còn lại.
- `.env.example` — danh sách biến cấu hình đầy đủ kèm chú thích mục đích.

## 7. Phân tích hệ thống hiện tại

`[CONFIRMED]` — hệ thống đã được khởi chạy thật bằng `uvicorn app.main:app` trong quá trình phát triển (xác nhận qua sự tồn tại của `ats_v2.db` — dữ liệu runtime), không chỉ tồn tại dưới dạng mã nguồn tĩnh chưa từng chạy.

## 8. Phân tích source code

`[CONFIRMED]` — phương pháp chính, đã thực hiện ở `00_PROJECT_DISCOVERY.md`: đọc toàn bộ 45 file Python trong `app/` (routers, services, models, schemas, deps, core), trích xuất route, entity, business rule.

## 9. Phân tích dữ liệu

`[CONFIRMED]` — phân tích qua `app/seed_data.py` (dữ liệu mẫu: 1 Department, 4 User với 3 role khác Candidate, 1 Job) để hiểu cấu hình tối thiểu cần có để hệ thống vận hành; phân tích qua `app/models/enums.py` để liệt kê đầy đủ domain value (trạng thái, loại) hệ thống hỗ trợ.

## 10. Xác thực yêu cầu (Requirement Validation)

`[CONFIRMED]` — mỗi yêu cầu chức năng được đối chiếu với **test case tương ứng** (nếu có) trong `tests/`. Một yêu cầu chỉ được đánh dấu `[CONFIRMED]` khi có bằng chứng kép: (a) code hiện thực hành vi đó, và (b) không mâu thuẫn với hành vi quan sát được khi chạy test/script. Yêu cầu chỉ có code nhưng không có test tương ứng vẫn được ghi nhận `[CONFIRMED]` (vì code là bằng chứng đủ) nhưng gắn chú thích "chưa có test tự động bao phủ".

## 11. Ưu tiên yêu cầu (Requirement Prioritization)

`[CONFIRMED]` — mức ưu tiên không tự suy diễn mà lấy trực tiếp từ phân loại đã có sẵn trong `CONFLICT_REPORT_AND_BACKLOG.md` mục 5 (cột "Ưu tiên còn lại": Cao / Phase 2 / Phase 3...), và từ trạng thái triển khai thực tế: tính năng đã có code + test hoàn chỉnh mặc định có độ ưu tiên đã-thực-hiện cao nhất (P0 thực tế), tính năng còn trong backlog giữ nguyên mức ưu tiên đã ghi.

## 12. Xử lý yêu cầu mâu thuẫn

`[CONFIRMED]` — áp dụng đúng RULE 4 của quy trình: khi phát hiện mâu thuẫn (ví dụ mục 12 ở `00_PROJECT_DISCOVERY.md` — file CSS/JS không được `index.html` dùng), quy trình xử lý là:
1. Ghi nhận mâu thuẫn kèm bằng chứng (đường dẫn file, dòng).
2. Không tự quyết định xóa/sửa.
3. Ưu tiên hành vi implementation thực tế (đang chạy) khi mô tả "hệ thống hiện tại" trong BRD/SRS.
4. Đưa vào `21_OPEN_QUESTIONS.md` để người dùng xác nhận hướng xử lý.

## 13. Xác nhận yêu cầu với stakeholder

`[CONFIRMED]` — thực hiện qua cơ chế hỏi-đáp trực tiếp với người dùng tại các checkpoint đã định nghĩa ở `01_MASTER_DOCUMENT_OUTLINE.md` (dừng sau mỗi Đợt). Quyết định đã xác nhận: phạm vi tài liệu giới hạn `ats-v2/` (OQ-01).

---

## Bảng phân loại nguồn gốc yêu cầu (áp dụng xuyên suốt 05_BRD và 06_SRS)

| Cấp độ | Định nghĩa | Cách nhận biết trong tài liệu này |
|---|---|---|
| Yêu cầu xác nhận từ source/document | Có route/model/hàm cụ thể hiện thực đúng hành vi | `[CONFIRMED]` + trích dẫn file |
| Yêu cầu suy luận | Hành vi hệ thống ngụ ý một yêu cầu nghiệp vụ cao hơn không được viết thành comment/docstring rõ ràng | `[INFERRED]` + giải thích suy luận |
| Yêu cầu giả định | Cần giả định để mô hình hoàn chỉnh (VD mục tiêu KPI kinh doanh — hệ thống không lưu trữ mục tiêu, chỉ có số liệu) | `[ASSUMED]` + lý do |
| Yêu cầu còn thiếu | Không tìm thấy bằng chứng nào | `[MISSING]` — liệt kê ở Gap Analysis / Open Questions, không bịa nội dung thay thế |

---

*Tài liệu tiếp theo: `04_KHAO_SAT_YEU_CAU.md`.*
