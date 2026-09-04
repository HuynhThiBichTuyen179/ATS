# 22 — FINAL CONSISTENCY REVIEW — ATS v2.1

Rà soát chéo cuối cùng toàn bộ bộ tài liệu `00`–`21` (23 file, gồm cả tài liệu này là file thứ 23) trước khi coi bộ tài liệu reverse-engineering là hoàn tất. Thực hiện bằng cách **grep trực tiếp toàn bộ ID** trên tất cả file `.md` trong `docs/` (không chỉ đọc lại bằng mắt) để đảm bảo số liệu tổng hợp khớp với số lượng ID thực tế đã dùng — đúng tinh thần RULE 6.

## 1. Bảng đối chiếu số liệu cuối cùng (đã verify bằng grep, không lấy từ trí nhớ)

| Loại ID | Số lượng thực tế (grep) | Nơi định nghĩa gốc | Trạng thái |
|---|---|---|---|
| `BR-XXX` | 9 (BR-001 → BR-009) | `05_BRD.md` | ✅ Khớp |
| `FR-XXX` | 74 | `06_SRS.md` | ⚠️ **Đã sửa** — tài liệu gốc ghi nhầm "73" (lỗi cộng tay), grep xác nhận thực tế là 74. Đã sửa lại `06_SRS.md` và `19_TRACEABILITY_MATRIX.md` (2 chỗ) trong chính đợt rà soát này |
| `NFR-XXX` | 20 (SEC 3, REL 5, MAIN 3, LOG 3, PERF 2, SCA 1, AVA 1, USA 2) | `06_SRS.md` | ⚠️ **Đã sửa** — tài liệu gốc ghi nhầm "19", thực tế 20. Đã sửa lại `06_SRS.md` |
| `UC-XXX` | 37 | `11_USE_CASE.md` | ✅ Khớp (đúng như công bố, ánh xạ 1:1 với FN) |
| `FN-<MOD>-XX` | 37 | `08_FUNCTIONAL_SPECIFICATION.md` | ✅ Khớp |
| Endpoint HTTP thật | 37 | `08` mục 11 (đã hiệu chỉnh từ 35 ở `00`) | ✅ Khớp — chênh lệch với `00` đã ghi nhận công khai (G-DOC-02) |
| `BP-<MOD>-XXX` | 8 | `09_BUSINESS_PROCESS.md` | ✅ Khớp |
| Module (`MOD-*`) | 10 | `01_MASTER_DOCUMENT_OUTLINE.md` | ✅ Khớp, dùng nhất quán 00→21 |
| Actor (`ACT-*`) | 5 (4 người dùng + `ACT-SYSTEM`) | `01_MASTER_DOCUMENT_OUTLINE.md` | ✅ Khớp |
| Bảng CSDL | 12 | `16_DATABASE_DESIGN.md` | ✅ Khớp, đúng số đã đếm từ `00` |
| Gap tổng hợp | 24 | `20_GAP_ANALYSIS.md` | ✅ Nội bộ nhất quán |
| Open Question tổng hợp | 11 | `21_OPEN_QUESTIONS.md` | ✅ Nội bộ nhất quán |

**Nhận xét về 2 lỗi vừa sửa**: cả hai đều là **lỗi cộng tổng thủ công** khi viết `06_SRS.md` (Đợt 2), không phải bất nhất về nội dung/ý nghĩa — bản thân từng `FR-XXX`/`NFR-XXX` riêng lẻ đều đúng và nhất quán ở mọi nơi khác trong bộ tài liệu; chỉ có dòng tổng kết cuối file bị tính sai. Việc phát hiện bằng grep thay vì đọc lại bằng mắt (vốn đã "đọc qua" nhiều lần ở các Đợt sau mà không phát hiện ra) minh họa đúng lý do RULE 6 yêu cầu một bước rà soát chéo độc lập cuối cùng thay vì tin tưởng self-review liên tục trong lúc viết.

## 2. Rà soát tuân thủ 6 RULE gốc

| Rule | Nội dung | Tự đánh giá | Bằng chứng |
|---|---|---|---|
| RULE 1 | Không bịa đặt | ✅ Tuân thủ | Mọi khẳng định đều trích dẫn file/dòng/hàm cụ thể; các mục không có bằng chứng đều gắn `[MISSING]` thay vì mô tả như thể tồn tại (VD Deployment Diagram ở `15` mục 5, Success Criteria ở `05` mục 17) |
| RULE 2 | Gắn nhãn FACT vs INFERENCE | ✅ Tuân thủ | 4 nhãn `[CONFIRMED]`/`[INFERRED]`/`[ASSUMED]`/`[MISSING]` dùng xuyên suốt 00-21; riêng `11_USE_CASE.md` có 1 nhãn đặc biệt `[CONFIRMED — quyết định mô hình hóa]` cho việc ánh xạ UC:FN 1:1 — đây là quyết định phương pháp luận (không phải fact từ code), đã ghi chú rõ ràng thay vì gắn nhầm `[CONFIRMED]` trơn |
| RULE 3 | Không sửa source code khi phân tích | ✅ Tuân thủ | Toàn bộ 23 file trong `docs/` là file **mới tạo**; không có `Edit` nào tác động tới `app/`, `tests/`, `scripts/`, `requirements.txt` trong suốt quá trình. 3 lỗ hổng RBAC phát hiện ở `07` (G-07-1/2/3) được **ghi nhận, không sửa** |
| RULE 4 | Không tự ý giải quyết mâu thuẫn — ghi nhận | ✅ Tuân thủ | VD: chênh lệch 35 vs 37 endpoint (`00` vs `08`) được ghi công khai thành Gap G-DOC-02 thay vì âm thầm sửa số cũ ở `00`; tương tự với việc phát hiện `73`/`19` sai ở mục 1 tài liệu này — sửa **có ghi chú**, không sửa lặng lẽ |
| RULE 5 | Tạo mục Open Questions thay vì bịa | ✅ Tuân thủ | `21_OPEN_QUESTIONS.md` tổng hợp 11 câu hỏi, 9 câu còn mở, không câu nào bị "lấp" bằng suy đoán ở tài liệu khác |
| RULE 6 | Nhất quán ID xuyên suốt | ✅ Tuân thủ (sau khi sửa 2 lỗi ở mục 1) | Đã verify bằng grep toàn bộ `docs/*.md`, không phát hiện ID nào bị đánh số lại/xung đột nghĩa |

## 3. Đối chiếu với yêu cầu gốc của người dùng (25 Phase → 23 File)

`[CONFIRMED]` — toàn bộ 25 phase trong prompt gốc đã được bao phủ, với 2 lần gộp file đã đề xuất từ `01` và áp dụng xuyên suốt (Phase 11-14 UML → `15_UML.md`; Phase 18-19 Database → `16_DATABASE_DESIGN.md`), cộng 1 tài liệu bổ sung không có trong 25 phase gốc: `00_PROJECT_DISCOVERY.md` (STEP 1) và `01_MASTER_DOCUMENT_OUTLINE.md` (STEP 2) — 2 tài liệu này là sản phẩm của chính quy trình khảo sát ban đầu theo yêu cầu, không phải phase nghiệp vụ, nên được đánh số 00/01 thay vì nằm trong dải 02-22.

| Yêu cầu gốc (STEP) | Đã hoàn thành | File |
|---|---|---|
| STEP 1 — Project Discovery | ✅ | `00` |
| STEP 2 — Master Document Outline | ✅ | `01` |
| Phase 3 — Phương pháp khảo sát | ✅ | `03` |
| Phase 4 — Khảo sát & BRD | ✅ | `04`, `05` |
| Phase 5 — SRS | ✅ | `06` |
| Phase 6 — User/Role/Permission | ✅ | `07` |
| Phase 7 — Function Catalog | ✅ | `08` |
| Phase 8 — Use Case Diagram + Spec | ✅ | `11`, `12` |
| Phase 9 — Business Process | ✅ | `09` |
| Phase 10 — BPMN | ✅ | `10` |
| Phase 11-14 — UML (Class/Sequence/Activity/Component/Deployment) | ✅ (Deployment đánh dấu `[MISSING]` có căn cứ) | `15` |
| Phase 15 — System Architecture | ✅ | `14` |
| Phase 16 — Cơ sở lý thuyết | ✅ | `02` |
| Phase 17 — System Modeling | ✅ | `13` |
| Phase 18-19 — Database/ERD/Data Dictionary | ✅ | `16` |
| Phase 20 — Technology Stack | ✅ | `17` |
| Phase 21 — General Workflow | ✅ | `18` |
| Phase 22 — Traceability Matrix | ✅ | `19` |
| Phase 23 — Gap Analysis | ✅ | `20` |
| Open Questions (xuyên suốt, không phải 1 phase riêng trong prompt gốc nhưng được yêu cầu ở RULE 5) | ✅ | `21` |
| Phase 25 / STEP 10 — Final Consistency Review | ✅ | `22` (tài liệu này) |

**Không có phase nào bị bỏ sót.**

## 4. Hạn chế còn tồn tại của bộ tài liệu (minh bạch, không che giấu)

1. **9 Open Question chưa có câu trả lời** (`21`) — không phải lỗi tài liệu, mà là các quyết định thuộc thẩm quyền Product Owner/người dùng, đúng theo RULE 5.
2. **Deployment Diagram không thể hoàn thiện** (`15` mục 5) vì thiếu bằng chứng hạ tầng — trạng thái này sẽ tiếp tục đúng cho đến khi dự án có Dockerfile/CI-CD thật.
3. **Success Criteria/KPI kinh doanh không xác định được** (`05` mục 17) — hệ thống không lưu trữ mục tiêu định lượng, chỉ số liệu thực đo; đây là giới hạn của chính đối tượng được phân tích (code), không phải giới hạn phương pháp.
4. Bộ tài liệu phản ánh **đúng trạng thái source code tại thời điểm phân tích** (2026-08-14 trở về trước theo lịch sử phiên làm việc) — nếu code thay đổi sau này (đặc biệt nếu người dùng quyết định sửa 3 lỗ hổng RBAC hoặc wiring APScheduler theo khuyến nghị ở `20`), các tài liệu liên quan (`06`, `07`, `08`, `09`, `19`, `20`) cần được cập nhật lại tương ứng — bộ tài liệu này **không tự động đồng bộ với code**.

## 5. Kết luận

Bộ 23 tài liệu (`00`–`22`) đã hoàn thành đầy đủ theo đúng cấu trúc đề xuất ở `01`, tuân thủ 6 RULE gốc, đã tự phát hiện và sửa 2 lỗi cộng tổng nội bộ trong chính đợt rà soát cuối này. Toàn bộ 24 Gap và 11 Open Question được tổng hợp tập trung tại `20`/`21`, sẵn sàng làm đầu vào cho bước tiếp theo (nếu người dùng muốn) là lên kế hoạch khắc phục theo mức ưu tiên đã đề xuất ở `20` mục E — nhưng bước đó nằm **ngoài phạm vi** nhiệm vụ phân tích/tài liệu hóa hiện tại (RULE 3) và cần yêu cầu tường minh mới.

---

*Kết thúc toàn bộ bộ tài liệu reverse-engineering ATS v2.1 (`00`–`22`, 23 file).*

## 6. Addendum — Cập nhật 2026-08-18 (ngoài phạm vi 23-file gốc)

Theo yêu cầu người dùng "cập nhật các file tài liệu", đã thực hiện 1 đợt refresh **có giới hạn phạm vi**, không phải rà soát lại toàn bộ 23 file:

**Đợt 1 (living-status docs)** — re-verify bằng grep/đọc code trực tiếp, không suy đoán:
- `20_GAP_ANALYSIS.md`: re-verify toàn bộ Gap nhóm A (bảo mật) và các Gap liên quan tài khoản/mật khẩu/Interview ở nhóm B/C. Kết quả: G-07-1 ✅ đã sửa, APP-20 ✅ đã sửa, AUTH-9 ✅ đã sửa (kèm phát hiện + sửa 1 bug ẩn khiến forgot-password câm lặng không gửi email), USER-5/6 và G-DB-06 sửa một phần, G-07-2/G-07-3/JOB-8/AUTH-10 xác nhận **vẫn còn mở**. Bổ sung 1 Gap mới phát hiện ngoài danh sách gốc (G-POST-01 — lỗi RBAC chặn Candidate xem Nguồn hồ sơ, đã sửa).
- `21_OPEN_QUESTIONS.md`: cập nhật OQ-07 (một phần đã trả lời qua hành động thực tế, chưa phải quyết định tường minh).
- `README.md`: cập nhật số lượng test, danh sách router/module mới, tài khoản seed, mục Forgot/Reset Password, mục AI Screening.

**Đợt 2 (refresh toàn diện, theo yêu cầu tường minh của người dùng sau khi được hỏi xác nhận phạm vi)** — dựng lại từ đầu bằng cách đọc trực tiếp toàn bộ 14 file router + 14 file model, đếm lại chính xác số liệu (không lấy từ trí nhớ hay suy đoán):
- `07_USER_ROLE_PERMISSION.md`: viết lại hoàn toàn — ma trận đầy đủ **63 endpoint** (tăng từ 37), thêm 4 module hoàn toàn mới (Candidate, Candidate Sources, Interview, Resume download), đối chiếu G-07-1/2/3 với trạng thái code hiện tại.
- `16_DATABASE_DESIGN.md`: viết lại hoàn toàn — **14 bảng** (tăng từ 12, thêm `candidate_sources`/`password_reset_tokens`), ERD cập nhật, migration thủ công (`scripts/migrate_v2_3.py`) ghi nhận ở mục riêng.
- `08_FUNCTIONAL_SPECIFICATION.md`: viết lại hoàn toàn — **63 Function** (tăng từ 37), khớp 1:1 với endpoint ở `07`.
- `19_TRACEABILITY_MATRIX.md`: giữ nguyên 74 `FR-XXX` gốc (không bịa ID mới vì `06`/`11` chưa refresh), bổ sung mục riêng liệt kê 26 endpoint mới chưa có FR/UC chính thức, cập nhật bảng Coverage Check phản ánh đúng thực tế (37/63 endpoint có FR, 12/14 bảng có FR).

**Vẫn chưa làm — cần yêu cầu tường minh riêng nếu muốn đầy đủ 1:1 UC:FN như phương pháp gốc**: `05_BRD.md`, `06_SRS.md` (thêm `FR-XXX` mới cho 26 Function mới), `09_BUSINESS_PROCESS.md`, `10_BPMN.md`, `11_USE_CASE.md`/`12_USE_CASE_SPECIFICATION.md` (thêm `UC-XXX` mới), `13`-`15` (System Modeling/UML — sequence/class diagram cho module mới). Đây là khối lượng công việc tương đương phần còn lại của đợt reverse-engineering gốc — cố tình không tự làm để tránh bịa `FR-XXX`/`UC-XXX` không có căn cứ nghiệp vụ thật (RULE 1), và vì người dùng chỉ xác nhận phạm vi 07/08/16/19 khi được hỏi.
