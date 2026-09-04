# STEP 2 — MASTER DOCUMENT OUTLINE

**Phạm vi**: hệ thống `ats-v2/` (đã xác nhận). Tài liệu này định nghĩa cấu trúc, nội dung dự kiến, và **Master Terminology & ID Registry** dùng xuyên suốt toàn bộ bộ tài liệu 01–25, đảm bảo RULE 6 (tính nhất quán) — mọi ID được tạo ở đây sẽ được tái sử dụng nguyên vẹn ở mọi tài liệu sau, không được đổi tên/đánh số lại.

---

## A. MASTER TERMINOLOGY & ID REGISTRY

### A.1. Actor Registry (4 actor — [CONFIRMED] `app/models/enums.py::UserRole`)

| Actor Code | Tên hiển thị | Nguồn |
|---|---|---|
| `ACT-CANDIDATE` | Ứng viên | `UserRole.CANDIDATE` |
| `ACT-HR` | Nhân viên Tuyển dụng | `UserRole.HR` |
| `ACT-HR-MANAGER` | Trưởng phòng Tuyển dụng | `UserRole.HR_MANAGER` |
| `ACT-ADMIN` | Quản trị hệ thống | `UserRole.ADMIN` |
| `ACT-SYSTEM` | Hệ thống (tự động) | [INFERRED] — các hành động không do actor người dùng trực tiếp kích hoạt: tự sinh Business ID, tự đóng Job khi đủ quota, tự gửi email theo giai đoạn |

### A.2. Module Registry (10 module — [CONFIRMED] theo `app/routers/*.py`)

| Module Code | Tên | Router file |
|---|---|---|
| `MOD-AUTH` | Xác thực & Tài khoản | `auth.py` |
| `MOD-USER` | Quản lý Người dùng nội bộ | `users.py` |
| `MOD-DEPT` | Phòng ban | `departments.py` |
| `MOD-JOB` | Tin tuyển dụng | `jobs.py` |
| `MOD-APP` | Hồ sơ ứng tuyển | `applications.py` |
| `MOD-OFFER` | Thư mời nhận việc | `offers.py` |
| `MOD-EMAIL` | Email Tự động | `email_templates.py` |
| `MOD-AI` | AI Screening | `ai.py` |
| `MOD-DASH` | Dashboard | `dashboard.py` |
| `MOD-AUDIT` | Nhật ký Audit | `audit.py` |

### A.3. ID Scheme (áp dụng cho toàn bộ tài liệu 05–25)

| Loại | Format | Ví dụ | Ghi chú |
|---|---|---|---|
| Business Requirement (BRD) | `BR-XXX` | `BR-001` | Tuần tự toàn hệ thống, không theo module |
| Functional Requirement (SRS) | `FR-<MOD>-XXX` | `FR-APP-003` | Theo module để dễ truy vết; mỗi FR liên kết ngược 1 `BR-XXX` |
| Non-functional Requirement | `NFR-<CATEGORY>-XXX` | `NFR-SEC-001` | CATEGORY ∈ {SEC (Security), PERF (Performance), REL (Reliability, gồm cả Data Integrity), MAIN (Maintainability), USA (Usability, gồm cả Compatibility), LOG (Logging/Audit, gồm cả Auditability/Monitoring), SCA (Scalability), AVA (Availability)} — **[CẬP NHẬT ở Đợt 2/06_SRS]**: mở rộng từ 6 lên 8 category để bao phủ đủ 12 nhóm NFR quan sát được ở `04_KHAO_SAT_YEU_CAU.md` mục 11, gộp các nhóm quan hệ gần (Data Integrity vào REL, Auditability/Monitoring vào LOG, Compatibility vào USA) thay vì tạo category mới cho mỗi nhóm quan sát |
| Use Case | `UC-<MOD>-XXX` | `UC-OFFER-002` | 1 FR có thể ứng với 1-nhiều UC; 1 UC luôn thuộc đúng 1 module |
| Business Process | `BP-<MOD>-XXX` | `BP-APP-001` | Dùng cho đặc tả tiến trình nghiệp vụ + BPMN |
| Entity (Database) | Tên bảng thật, không đánh số | `applications`, `offers` | Giữ nguyên tên `__tablename__` để tra cứu trực tiếp trong code |
| API Endpoint | `<METHOD> <path>` thật | `POST /offers/{id}/approve` | Không đặt mã riêng — dùng nguyên path đã liệt kê ở `00_PROJECT_DISCOVERY.md` mục 7 |

### A.4. Trạng thái bằng chứng (nhắc lại RULE 2, áp dụng trong mọi tài liệu)

`[CONFIRMED]` — có trong source/DB/config · `[INFERRED]` — suy luận hợp lý từ code · `[ASSUMED]` — giả định cần xác nhận · `[MISSING]` — không tìm thấy bằng chứng.

---

## B. CẤU TRÚC BỘ TÀI LIỆU (24 file — đã gộp 16-19 theo đề xuất ở Discovery, chờ phản đối nếu không đồng ý)

| # | File | Phase gốc | Mục đích | Input chính | Output chính |
|---|---|---|---|---|---|
| 00 | `00_PROJECT_DISCOVERY.md` | — | Kết quả khảo sát (đã xong) | Toàn bộ source | Feature/API/DB map |
| 01 | `01_MASTER_DOCUMENT_OUTLINE.md` | — | Tài liệu này | 00 | ID Registry |
| 02 | `02_CO_SO_LY_THUYET.md` | 16 | Nền tảng lý thuyết áp dụng đúng công nghệ project dùng (Layered Architecture, REST, JWT, RBAC, ORM, UML, BPMN, ERD) | Tech stack đã xác nhận ở 00 | Cơ sở tham chiếu cho phần Architecture |
| 03 | `03_PHUONG_PHAP_KHAO_SAT.md` | 3 | Phương pháp luận: vì đây là reverse-engineering từ source code có sẵn (không phải dự án mới khảo sát người dùng thật), phần này sẽ mô tả đúng phương pháp đã dùng (code analysis, test analysis) và ghi rõ giới hạn (không phỏng vấn/quan sát thật được) | 00 | Minh bạch về giới hạn phương pháp |
| 04 | `04_KHAO_SAT_YEU_CAU.md` | 4 | Tổng hợp yêu cầu phân loại theo CONFIRMED/INFERRED/ASSUMED/MISSING trước khi hệ thống hóa thành BRD/SRS | 00, source | Danh sách yêu cầu thô |
| 05 | `05_BRD.md` | 4 | Business Requirements Document đầy đủ | 04 | `BR-XXX` |
| 06 | `06_SRS.md` | 5 | Software Requirements Specification đầy đủ | 05, source | `FR-XXX`, `NFR-XXX` |
| 07 | `07_USER_ROLE_PERMISSION.md` | 6 | Ma trận Actor/Role/Permission chi tiết (mở rộng mục 5 ở 00) | `app/deps/rbac.py`, mọi router | Bảng RBAC đầy đủ |
| 08 | `08_FUNCTIONAL_SPECIFICATION.md` | 7 | Function Catalog đầy đủ (35 endpoint → chức năng nghiệp vụ) | 00 mục 7, routers | Bảng Function Catalog |
| 09 | `09_BUSINESS_PROCESS.md` | 9 | Đặc tả từng tiến trình nghiệp vụ chính (Apply, Screening, Offer 4-eyes, Re-apply...) | services/*.py | `BP-XXX` |
| 10 | `10_BPMN.md` | 10 | Sơ đồ BPMN (Mermaid) cho các BP ở 09 | 09 | BPMN diagrams |
| 11 | `11_USE_CASE.md` | 8 | Use Case Diagram tổng thể + theo module | 06, 08 | `UC-XXX`, Use Case Diagram |
| 12 | `12_USE_CASE_SPECIFICATION.md` | 8 | Đặc tả chi tiết từng Use Case (template đầy đủ) | 11 | Đặc tả UC đầy đủ |
| 13 | `13_SYSTEM_MODELING.md` | 17 | Tổng hợp mối liên hệ Business → Requirement → Use Case → Process → Design → Code → Database | 05-12 | Bảng liên kết mô hình |
| 14 | `14_SYSTEM_ARCHITECTURE.md` | 15 | Kiến trúc hệ thống chi tiết (mở rộng mục 9 ở 00) | 00 mục 9, source | Architecture Diagram chi tiết |
| 15 | `15_UML.md` | 11-14 | Class/Sequence/Activity/Component Diagram (gộp 1 file, chia theo heading — Deployment Diagram đánh dấu MISSING vì không có bằng chứng hạ tầng triển khai thật) | models/*.py, services/*.py, routers/*.py | UML diagrams |
| 16 | `16_DATABASE_DESIGN.md` | 18+19 | ERD + Data Dictionary + Table Specification (gộp, xem lý do ở 00 mục 14) | models/*.py | ERD, đặc tả 11 bảng |
| 17 | `17_TECHNOLOGY_STACK.md` | 20 | Bảng công nghệ đầy đủ có version + evidence (mở rộng mục 3 ở 00) | requirements.txt | Bảng Technology Stack |
| 18 | `18_GENERAL_WORKFLOW.md` | 21 | Workflow tổng quát Request→Response qua các layer | 14 | Sequence tổng quát |
| 19 | `19_TRACEABILITY_MATRIX.md` | 22 | Ma trận BR→FR→UC→API→Entity→Source | 05-16 | Traceability Matrix |
| 20 | `20_GAP_ANALYSIS.md` | 23 | Bảng Gap Analysis (Confirmed/Inferred/Assumed/Missing/Contradicted) | Toàn bộ | Gap Analysis |
| 21 | `21_OPEN_QUESTIONS.md` | — | Tổng hợp toàn bộ Open Question phát sinh xuyên suốt 00-20 (không chỉ của riêng 00) | Toàn bộ | Danh sách câu hỏi tổng hợp |
| 22 | `22_FINAL_CONSISTENCY_REVIEW.md` | 25 | Rà soát chéo cuối cùng theo checklist ở prompt gốc (STEP 10) | Toàn bộ | Kết luận consistency |

**Khác biệt so với cấu trúc 25 mục gốc**: gộp 16-19 → còn 4 mục (14 STT), gộp 11-14 UML → 1 file (15). Tổng số file giảm từ 25 xuống **23**, nội dung không giảm — chỉ giảm số file vật lý để tránh trùng lặp đầu-mục khi mỗi bảng chỉ có ~10 cột.

---

## C. THỨ TỰ TRIỂN KHAI ĐỀ XUẤT (STEP 3–10 gốc, gộp thành các đợt giao)

| Đợt | Tài liệu | Lý do gộp |
|---|---|---|
| Đợt 1 | 02, 03, 04 | Nền tảng — ngắn, ít rủi ro sai lệch, nên làm nhanh 1 lượt |
| Đợt 2 | 05 (BRD), 06 (SRS), 07 (RBAC) | Requirement Engineering — lõi quan trọng nhất, cần bạn review kỹ trước khi dùng làm nền cho Use Case |
| Đợt 3 | 08, 09, 10 | Business Process + BPMN |
| Đợt 4 | 11, 12 | Use Case + đặc tả (khối lượng lớn nhất — 35 endpoint) |
| Đợt 5 | 13, 14, 15 | System Modeling + Architecture + UML |
| Đợt 6 | 16, 17, 18 | Database + Technology + Workflow |
| Đợt 7 | 19, 20, 21, 22 | Traceability + Gap + Open Questions + Consistency Review (bắt buộc làm sau cùng) |

**Đề xuất**: dừng xác nhận sau **mỗi Đợt** (7 lần dừng) thay vì sau mỗi 1 trong 23 file (sẽ mất quá nhiều lượt qua lại) — vẫn giữ đúng tinh thần "không làm ẩu một lần" của prompt gốc, nhưng thực tế hơn cho khối lượng công việc này. Nếu bạn muốn dừng dày hơn (sau từng file) hoặc thưa hơn (gộp nhiều đợt), báo tôi điều chỉnh.

---

*Nếu outline này ổn, tôi sẽ bắt đầu **Đợt 1** (file 02, 03, 04) ngay. Nếu cần điều chỉnh cấu trúc/thứ tự trước, hãy cho biết.*
