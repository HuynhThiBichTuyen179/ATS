# BUSINESS REQUIREMENTS DOCUMENT (BRD) — ATS v2.1

**Hệ thống**: `ats-v2/` (Applicant Tracking System)
**Phiên bản tài liệu**: 1.0
**Phạm vi phân tích**: `ats-v2/` (đã xác nhận, xem `00_PROJECT_DISCOVERY.md`)
**Phương pháp xây dựng**: reverse-engineering từ source code (xem `03_PHUONG_PHAP_KHAO_SAT.md`) — các Business Requirement dưới đây được **suy luận `[INFERRED]`** từ các quyết định thiết kế đã hiện thực trong code (VD: cơ chế 4-eyes approval chỉ có ý nghĩa nếu mục tiêu kinh doanh là kiểm soát rủi ro tài chính/gian lận), trừ khi có ghi chú khác.

## Mục lục
1. Giới thiệu · 2. Bối cảnh nghiệp vụ · 3. Vấn đề cần giải quyết · 4. Mục tiêu Business · 5. Phạm vi · 6. Ngoài phạm vi · 7. Stakeholder · 8. Nhóm người dùng · 9. Business Process · 10. Business Rules · 11. Business Requirements · 12. Functional Requirements (mức business) · 13. Non-functional Requirements (mức business) · 14. Assumptions · 15. Constraints · 16. Risks · 17. Success Criteria · 18. Traceability sơ bộ (BR → FR)

---

## 1. Giới thiệu

Tài liệu này đặc tả yêu cầu nghiệp vụ (Business Requirements) của hệ thống ATS v2.1, được xây dựng bằng phương pháp reverse-engineering — nghĩa là yêu cầu được **suy ngược** từ hệ thống đã hiện thực, không phải thu thập trước từ khách hàng rồi mới xây dựng (thứ tự thông thường của một dự án mới). Do đó, mọi mục tiêu/yêu cầu nghiệp vụ trình bày dưới đây phải luôn được đọc kèm với bằng chứng nguồn (source evidence) tương ứng ở `04_KHAO_SAT_YEU_CAU.md`.

## 2. Bối cảnh nghiệp vụ

`[INFERRED]` — Từ tập tính năng đã hiện thực (đăng tin tuyển dụng công khai, ứng viên tự nộp hồ sơ qua cổng riêng, sàng lọc có hỗ trợ AI, quy trình Offer có kiểm soát 2 người duyệt, tự động gửi email theo giai đoạn), hệ thống được xây dựng cho một **doanh nghiệp có hoạt động tuyển dụng thường xuyên, với đội ngũ tuyển dụng gồm nhiều nhân viên (HR) do 1 hoặc nhiều Trưởng phòng (HR Manager) quản lý**, cần: (a) tự phục vụ (self-service) cho ứng viên tránh phụ thuộc hoàn toàn vào email/excel thủ công, và (b) có cơ chế kiểm soát nội bộ đối với quyết định tài chính quan trọng (Offer lương).

## 3. Vấn đề cần giải quyết

`[INFERRED]`, suy từ các quyết định thiết kế cụ thể:

| Vấn đề | Bằng chứng cho thấy hệ thống giải quyết vấn đề này |
|---|---|
| Quy trình tuyển dụng phân tán, khó theo dõi trạng thái từng ứng viên | Máy trạng thái (`APP-10`) tập trung hóa trạng thái mỗi hồ sơ |
| Rủi ro một cá nhân tự ý duyệt Offer do chính mình đề xuất (gian lận/sai sót lương) | Cơ chế 4-eyes approval bắt buộc ở cả tầng ứng dụng và CSDL (`OFFER-3`) |
| Ứng viên bị chặn tái ứng tuyển do quy tắc cứng nhắc (VD cooldown thời gian) làm mất cơ hội tuyển người phù hợp | Loại bỏ hoàn toàn giới hạn thời gian tái ứng tuyển (`APP-4`) — đây là một thay đổi nghiệp vụ tường minh (xem `CONFLICT_REPORT_AND_BACKLOG.md`, mục CHANGE 02) |
| Định danh nội bộ (số ID tự tăng) không thân thiện khi trao đổi nghiệp vụ giữa người với người | Business ID có tiền tố dễ đọc theo loại đối tượng (`UV0001`, `APP0002`...) |
| Tốn thời gian nhân sự đọc thủ công từng CV để sàng lọc sơ bộ | Module AI Screening hỗ trợ chấm điểm phù hợp tự động (`AI-1`) |
| Thiếu số liệu tổng quan để quản lý đánh giá hiệu quả tuyển dụng | Module Dashboard (`DASH-1`) |

## 4. Mục tiêu Business

`[INFERRED]`:
1. Số hóa toàn bộ vòng đời tuyển dụng từ đăng tin đến khi ứng viên chính thức được tuyển (HIRED).
2. Giảm thiểu rủi ro quản trị/tài chính trong khâu phê duyệt Offer.
3. Tối đa hóa nguồn ứng viên tiềm năng bằng cách không giới hạn tái ứng tuyển.
4. Rút ngắn thời gian sàng lọc hồ sơ đầu vào bằng công cụ hỗ trợ AI, nhưng **không giao quyền quyết định tuyển dụng cho AI** (con người luôn là người quyết định cuối — xem `AI-6`).
5. Cải thiện trải nghiệm ứng viên qua giao tiếp tự động, kịp thời theo từng giai đoạn.
6. Cung cấp minh bạch số liệu vận hành tuyển dụng cho cấp quản lý.

## 5. Phạm vi

`[CONFIRMED]` — dựa trên tập module đã hiện thực (`04_KHAO_SAT_YEU_CAU.md`):
- Đăng tin tuyển dụng và quản lý vòng đời tin (Job).
- Cổng ứng tuyển cho Candidate (đăng ký, nộp hồ sơ, theo dõi trạng thái, phản hồi Offer).
- Quản lý pipeline ứng viên nội bộ cho HR (đổi trạng thái, sàng lọc, lưu trữ).
- Sàng lọc hỗ trợ AI (tùy chọn kích hoạt thủ công bởi HR).
- Quản lý và phê duyệt Offer với cơ chế 4-eyes.
- Tự động hóa email theo giai đoạn + gửi thủ công.
- Dashboard số liệu tổng hợp.
- Quản lý tài khoản nội bộ (HR/HR Manager/Admin), phòng ban.
- Nhật ký audit cho hành động nhạy cảm.

## 6. Ngoài phạm vi

`[CONFIRMED — MISSING trong hệ thống hiện tại]`, liệt kê theo bằng chứng "không tìm thấy" ở `04_KHAO_SAT_YEU_CAU.md`:
- Lên lịch và ghi nhận kết quả phỏng vấn qua giao diện/API riêng (`APP-20`).
- Khôi phục mật khẩu, xác thực email (`AUTH-9`, `AUTH-10`).
- Sửa/khóa/xóa tài khoản nội bộ sau khi tạo (`USER-5`).
- Giới hạn chi phí gọi AI theo ngân sách thực tế (`AI-7`).
- Quét virus file CV tải lên.
- Quy trình duyệt Requisition nhiều bước (hiện chỉ có 1 bước Đăng tin — `JOB-8`).
- Tự động chuyển Offer hết hạn khi không có ai gọi thủ công (thiếu lịch chạy nền — `OFFER-11`).
- Hạ tầng triển khai production thật (container hóa, CI/CD, giám sát vận hành) — không có bằng chứng trong `ats-v2/`.

## 7. Stakeholder

`[INFERRED/ASSUMED]` — hệ thống không lưu trữ thông tin về stakeholder ngoài hệ thống (Sponsor, Ban Giám đốc với tư cách người phê duyệt ngân sách dự án) vì đây là phạm vi quản lý dự án, không phải dữ liệu nghiệp vụ vận hành:

| Stakeholder | Vai trò suy luận | Nhãn |
|---|---|---|
| Ban Giám đốc / Cấp quản lý cao nhất | Người thụ hưởng số liệu Dashboard, gián tiếp qua vai trò ADMIN | `[INFERRED]` |
| Trưởng phòng Tuyển dụng (HR Manager) | Người vận hành chính, chịu trách nhiệm phê duyệt và giám sát | `[CONFIRMED]` — có vai trò `HR_MANAGER` riêng trong hệ thống |
| Nhân viên Tuyển dụng (HR) | Người thao tác nghiệp vụ hàng ngày | `[CONFIRMED]` — vai trò `HR` |
| Ứng viên (Candidate) | Người dùng cuối bên ngoài doanh nghiệp | `[CONFIRMED]` — vai trò `CANDIDATE` |
| Quản trị hệ thống (Admin/IT) | Người cấu hình hệ thống, quản lý tài khoản | `[CONFIRMED]` — vai trò `ADMIN` (gộp chung với vai trò điều hành cấp cao trong 1 role duy nhất — xem Constraint C-04) |

## 8. Nhóm người dùng

Xem chi tiết đầy đủ tại `07_USER_ROLE_PERMISSION.md`. Tóm tắt: 4 nhóm cố định — `ACT-CANDIDATE`, `ACT-HR`, `ACT-HR-MANAGER`, `ACT-ADMIN` (Registry đã định nghĩa ở `01_MASTER_DOCUMENT_OUTLINE.md`).

## 9. Business Process

Tóm tắt (đặc tả đầy đủ + BPMN ở `09_BUSINESS_PROCESS.md`, `10_BPMN.md` — Đợt 3):

**Quy trình tuyển dụng end-to-end**: Đăng tin → Ứng viên nộp hồ sơ → Sàng lọc (thủ công hoặc có hỗ trợ AI) → Shortlist/Từ chối → Phỏng vấn (ghi nhận thủ công, ngoài hệ thống) → Tạo Offer → Nộp duyệt → Duyệt (người khác) → Gửi Offer → Ứng viên phản hồi → Tuyển dụng thành công (tự đóng tin nếu đủ chỉ tiêu) hoặc Từ chối.

## 10. Business Rules

`[CONFIRMED]`, trích từ `04_KHAO_SAT_YEU_CAU.md` (các rule có tính bất biến nghiệp vụ, không phải chỉ là hành vi API đơn thuần):

| Mã | Business Rule | Nguồn |
|---|---|---|
| BRULE-01 | Người duyệt Offer phải khác người tạo Offer | `OFFER-3` |
| BRULE-02 | Không giới hạn thời gian giữa các lần ứng tuyển lại cùng một Job | `APP-4` |
| BRULE-03 | Job tự động đóng khi đủ số lượng đã tuyển theo chỉ tiêu | `JOB-6` |
| BRULE-04 | Hồ sơ đã đạt trạng thái Tuyển dụng thành công (HIRED) không được lưu trữ (archive) | `APP-14` |
| BRULE-05 | Nhân viên HR chỉ được thao tác trên Job/Hồ sơ được phân công; Trưởng phòng/Quản trị viên không giới hạn | `APP-15`, `JOB-*` |
| BRULE-06 | Việc lùi trạng thái hồ sơ (đưa về bước trước) chỉ Trưởng phòng/Quản trị viên được thực hiện, và bắt buộc ghi lý do | `APP-12` |
| BRULE-07 | Kết quả đánh giá AI không tự động quyết định số phận hồ sơ ứng viên | `AI-6` |
| BRULE-08 | Offer có hạn phản hồi xác định (mặc định 7 ngày) | `OFFER-7` |

## 11. Business Requirements

| ID | Business Requirement | Mục tiêu liên quan (mục 4) | Bằng chứng |
|---|---|---|---|
| `BR-001` | Hệ thống phải cho phép số hóa toàn bộ vòng đời một hồ sơ ứng tuyển, từ lúc nộp đến khi có kết quả cuối cùng, với trạng thái được kiểm soát chặt chẽ (không cho phép chuyển trạng thái tùy tiện) | Mục tiêu 1 | `APP-10, APP-11, APP-12` |
| `BR-002` | Hệ thống phải ngăn chặn một cá nhân đơn phương vừa tạo vừa phê duyệt Offer tuyển dụng | Mục tiêu 2 | `OFFER-3, OFFER-4` |
| `BR-003` | Hệ thống không được áp đặt giới hạn thời gian đối với việc ứng viên nộp lại hồ sơ cho cùng vị trí | Mục tiêu 3 | `APP-4, APP-5` |
| `BR-004` | Hệ thống phải hỗ trợ đánh giá sơ bộ mức độ phù hợp của hồ sơ so với yêu cầu công việc bằng công cụ tự động, nhưng quyết định cuối luôn thuộc về con người | Mục tiêu 4 | `AI-1, AI-6` |
| `BR-005` | Hệ thống phải tự động thông báo cho ứng viên khi trạng thái hồ sơ có thay đổi quan trọng (được chọn, mời phỏng vấn, từ chối, nhận Offer, trúng tuyển) | Mục tiêu 5 | `EMAIL-6` |
| `BR-006` | Hệ thống phải cung cấp số liệu tổng hợp về hiệu quả tuyển dụng theo thời gian thực cho cấp quản lý | Mục tiêu 6 | `DASH-1, DASH-2` |
| `BR-007` | Hệ thống phải phân quyền truy cập dữ liệu theo phạm vi công việc được giao, không cho phép truy cập ngoài phạm vi | (hỗ trợ mục tiêu 1-6) | `APP-15, OFFER-12, DASH-3` |
| `BR-008` | Hệ thống phải ghi nhận dấu vết cho các quyết định/hành động có ảnh hưởng quan trọng để phục vụ truy vết trách nhiệm sau này | (hỗ trợ mục tiêu 2) | `AUDIT-1` |
| `BR-009` | Định danh nghiệp vụ hiển thị cho người dùng (mã ứng viên, mã hồ sơ, mã offer...) phải ở dạng dễ đọc/dễ trao đổi, không lộ cấu trúc khóa kỹ thuật nội bộ | (hỗ trợ vận hành) | `id_generator.py`, Business ID có tiền tố |

## 12. Functional Requirements (mức Business — chi tiết hóa đầy đủ thành `FR-XXX` ở `06_SRS.md`)

Mỗi `BR-XXX` ở mục 11 được hiện thực hóa bởi 1 nhóm Functional Requirement mức hệ thống, đặc tả đầy đủ ở SRS. Bảng liên kết sơ bộ:

| Business Requirement | Nhóm FR tương ứng (module) |
|---|---|
| `BR-001` | `FR-APP-*` |
| `BR-002` | `FR-OFFER-*` |
| `BR-003` | `FR-APP-*` (nhóm ứng tuyển lại) |
| `BR-004` | `FR-AI-*` |
| `BR-005` | `FR-EMAIL-*` |
| `BR-006` | `FR-DASH-*` |
| `BR-007` | `FR-AUTH-*`, phân quyền lồng trong mọi `FR-*` khác |
| `BR-008` | `FR-AUDIT-*` |
| `BR-009` | Xuyên suốt mọi module (không tách riêng FR) |

## 13. Non-functional Requirements (mức business)

`[INFERRED]` từ mục 11 ở `04_KHAO_SAT_YEU_CAU.md`, diễn giải theo ngôn ngữ business: hệ thống cần đảm bảo **an toàn dữ liệu nhạy cảm** (lương, đánh giá AI), **toàn vẹn nghiệp vụ** (không cho sai trạng thái), và **khả năng truy vết**. Các nhóm chưa có bằng chứng (hiệu năng, khả năng chịu tải, độ sẵn sàng) được ghi `[MISSING]` — không giả định mục tiêu kinh doanh cụ thể (VD "phải chịu được 10.000 người dùng") vì không có căn cứ.

## 14. Assumptions

`[ASSUMED]`:
1. Doanh nghiệp sử dụng hệ thống có quy mô nhỏ đến vừa (dựa trên thiết kế CSDL không có cơ chế phân vùng/sharding, và giới hạn nguyên tắc thiết kế "10 bảng" được nhắc tới trong `CONFLICT_REPORT_AND_BACKLOG.md`).
2. Vai trò `ADMIN` trong thực tế đại diện đồng thời cho cả bộ phận IT (quản trị hệ thống) và Ban Giám đốc (phê duyệt cấp cao) — đây là gộp vai trò có chủ đích ở giai đoạn hiện tại, không phải thiếu sót.
3. Tổ chức chấp nhận việc quyết định phỏng vấn/đánh giá phỏng vấn được thực hiện **ngoài hệ thống** (qua họp/email) rồi HR nhập lại kết quả tóm tắt (suy từ việc `interviews` có field `hiring_manager_feedback` nhập tự do nhưng không có vai trò `HIRING_MANAGER` hay module lên lịch riêng).

## 15. Constraints

| Mã | Constraint | Bằng chứng |
|---|---|---|
| C-01 | Chỉ có đúng 4 vai trò cố định, không có cơ chế phân quyền động (không có bảng `roles`/`permissions`) | `app/models/enums.py::UserRole` |
| C-02 | Cơ sở dữ liệu giới hạn ở 11 bảng nghiệp vụ (nguyên tắc thiết kế đã tuyên bố trong lịch sử phát triển) | `CONFLICT_REPORT_AND_BACKLOG.md` |
| C-03 | AI Screening và Email phụ thuộc dịch vụ bên thứ ba (AI Provider — Gemini hoặc Claude tùy cấu hình `AI_PROVIDER`; SMTP Gmail) — khi không cấu hình, hệ thống chỉ hoạt động ở chế độ mô phỏng | `ai_service.py`, `email_service.py` |
| C-04 | Vai trò `ADMIN` kiêm nhiệm cả trách nhiệm kỹ thuật (IT) và điều hành (BGĐ), không tách bạch | `app/models/enums.py::UserRole` chỉ có 1 giá trị `ADMIN` |

## 16. Risks

`[INFERRED]`, dựa trên các `[MISSING]` đã xác nhận:

| Mã | Rủi ro | Nguồn gốc |
|---|---|---|
| R-01 | Offer quá hạn không tự động chuyển trạng thái do thiếu lịch chạy nền → ứng viên/HR không được thông báo kịp thời khi Offer hết hiệu lực | `OFFER-11` |
| R-02 | Chi phí gọi AI không được kiểm soát nếu khối lượng ứng tuyển tăng cao (chưa có cost cap) | `AI-7` |
| R-03 | Không có xác thực email/khôi phục mật khẩu → rủi ro vận hành khi người dùng quên mật khẩu hoặc đăng ký sai email | `AUTH-9, AUTH-10` |
| R-04 | File CV tải lên chưa được quét virus → rủi ro an ninh nếu triển khai công khai trên Internet | `04_KHAO_SAT_YEU_CAU.md` mục 11 |
| R-05 | Vai trò `ADMIN` kiêm nhiệm quá nhiều trách nhiệm (constraint C-04) tạo rủi ro thiếu tách bạch nhiệm vụ (segregation of duties) ở cấp cao nhất | Constraint C-04 |

## 17. Success Criteria

`[MISSING]` — hệ thống **không lưu trữ bất kỳ chỉ tiêu/mục tiêu định lượng nào** (VD "giảm X% thời gian tuyển dụng", "tăng Y% tỷ lệ nhận Offer") trong code hay cấu hình. Không có bảng hay cấu hình nào đại diện cho KPI mục tiêu — Dashboard (`DASH-1`) chỉ hiển thị **số liệu thực tế đo được**, không so sánh với mục tiêu đã đặt ra. Đây là khoảng trống cần Sponsor/BGĐ xác định trong `21_OPEN_QUESTIONS.md`.

## 18. Traceability sơ bộ (Business Requirement → System Requirement)

Bảng đầy đủ `BR → FR → UC → API → Entity` sẽ tổng hợp ở `19_TRACEABILITY_MATRIX.md` (Đợt 7) sau khi toàn bộ `FR-XXX`/`UC-XXX` được định danh. Mục 12 ở trên là bước trung gian đầu tiên.

---

*Tài liệu tiếp theo: `06_SRS.md`.*
