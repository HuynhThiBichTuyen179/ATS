# 21 — OPEN QUESTIONS — ATS v2.1

Tổng hợp **toàn bộ** câu hỏi mở phát sinh từ `00` đến `20` vào 1 danh sách duy nhất (đúng RULE 5 — không tự bịa câu trả lời cho các mục này). Đánh số lại liên tục `OQ-01`...`OQ-11`, giữ nguyên nội dung gốc, bổ sung trạng thái.

| ID | Câu hỏi | Nguồn gốc | Trạng thái |
|---|---|---|---|
| OQ-01 | Phạm vi phân tích: chỉ `ats-v2/` hay gồm cả hệ thống `backend/`/`frontend/` cũ? | `00` mục 13 | ✅ **ĐÃ XÁC NHẬN** — người dùng trả lời "Phạm vi chỉ ats v2" — chỉ phân tích `ats-v2/` |
| OQ-02 | `app/static/css/style.css` và `app/static/js/app.js` tồn tại nhưng không được `index.html` tham chiếu (Gap G-DOC-01) — giữ lại (phòng khi cần dùng lại sau) hay xóa (dọn dẹp code chết)? | `00` mục 12 | ⏳ Còn mở |
| OQ-03 | ~~`.env` có chứa dòng `GEMINI_API_KEY=`, `SMTP_USER=`, `SMTP_PASSWORD=` — giá trị hiện tại là thật hay vẫn để trống?~~ | `00` mục 12 | ✅ **ĐÃ XÁC NHẬN VÀ KÍCH HOẠT THẬT** (ngoài phạm vi 23-file gốc, ở lượt làm việc sau) — SMTP Gmail thật đã cấu hình + test gửi thành công; AI Provider đổi tên biến thành `AI_API_KEY` (tổng quát hóa đa provider), hiện cấu hình Claude thật |
| OQ-04 | Bảng `interviews` có model đầy đủ nhưng không có API (APP-20/Gap mục B). Đây là: (a) tính năng đang phát triển dở, cần hoàn thiện router, hay (b) đã chủ động dừng lại, cần loại bỏ bảng khỏi schema, hay (c) giữ nguyên as-is cho giai đoạn hiện tại? | `00` mục 12, `20` mục B | ⏳ Còn mở |
| OQ-05 | ~~README/tài liệu nội bộ nhắc MySQL là mục tiêu production nhưng không có driver/migration nào trong code...~~ | `00` mục 12, `14` mục 6 | ✅ **ĐÃ XÁC NHẬN VÀ TRIỂN KHAI THẬT** (ngoài phạm vi 23-file gốc) — đã bổ sung driver `pymysql`, cấu hình `USE_MYSQL`/`MYSQL_*` với fallback tự động về SQLite, kiểm chứng chạy schema + E2E thật trên MySQL. Alembic vẫn `[MISSING]` (chưa yêu cầu bổ sung) |
| OQ-06 | Tần suất dừng xác nhận khi làm tài liệu: sau mỗi 1/23 file hay sau mỗi Đợt (7 lần)? | `01` mục C | ✅ **ĐÃ XÁC NHẬN NGẦM** — người dùng phản hồi "tiếp tục" liên tục sau mỗi Đợt mà không phản đối cách chia — áp dụng theo Đợt cho đến hết |
| OQ-07 | 3 lỗ hổng row-level scope phát hiện ở `07`/`20` (G-07-1, G-07-2, G-07-3) — người dùng có muốn **giao 1 task riêng để sửa code** (ngoài phạm vi bộ tài liệu thuần phân tích này, vì RULE 3 cấm sửa code trong lúc phân tích) hay chỉ ghi nhận vào backlog? | `07` mục 4, `20` mục A | 🟡 **MỘT PHẦN ĐÃ TRẢ LỜI QUA HÀNH ĐỘNG THỰC TẾ** (2026-08-18) — người dùng chưa phản hồi trực tiếp câu hỏi này, nhưng ở lượt làm việc V2.3 đã yêu cầu sửa code cho khu vực liên quan, và G-07-1 đã được sửa như một tác dụng phụ (khi làm "Job Detail phải public"). G-07-2/G-07-3 **vẫn còn mở, chưa có yêu cầu tường minh nào để sửa** — xem `20` mục A để biết trạng thái verify mới nhất |
| OQ-08 | `apscheduler` đã có sẵn trong `requirements.txt` nhưng chưa từng wiring — có nên ưu tiên hoàn thiện việc lên lịch `expire_due_offers()` ngay, hay đây là công việc đã cố ý hoãn lại? | `17`, `20` mục B | ⏳ Còn mở |
| OQ-09 | `JobStatus` có đủ 6 giá trị (gồm `PENDING_APPROVAL`/`APPROVED`/`CANCELLED`) nhưng chỉ 2 giá trị được dùng thực tế — việc đăng tin 1 bước là **chủ đích đơn giản hóa lâu dài** hay chỉ là **MVP tạm thời**, cần làm quy trình duyệt nhiều bước sau? | `04` JOB-8, `20` mục B | ⏳ Còn mở |
| OQ-10 | Cấu trúc bộ tài liệu đã gộp từ 25 phase gốc xuống 23 file (gộp 16-19→`16_DATABASE_DESIGN.md`, gộp 11-14 UML→`15_UML.md`) — đề xuất này đưa ra ở `01` với ghi chú "chờ phản đối", người dùng chưa từng phản hồi trực tiếp câu hỏi này (chỉ nói "tiếp tục") — xác nhận cấu trúc 23 file là quyết định cuối? | `01` mục B | ⏳ Còn mở (không chặn tiến độ — đã triển khai theo đề xuất này xuyên suốt Đợt 1-7) |
| OQ-11 | Category NFR mở rộng từ 6 lên 8 (`SCA`, `AVA` thêm mới) ở `06_SRS.md` để bao phủ đủ 12 nhóm NFR quan sát được — có cần điều chỉnh lại cách phân nhóm này không, hay giữ nguyên như đã áp dụng? | `06` (ghi chú "CẬP NHẬT ở Đợt 2") | ⏳ Còn mở (mức ảnh hưởng thấp — chỉ là quy ước đặt tên tài liệu) |

## Tổng kết trạng thái

- **Đã xác nhận**: 4/11 (OQ-01, OQ-03, OQ-05, OQ-06) — OQ-03/OQ-05 được giải quyết ở các lượt làm việc sau khi bộ tài liệu 00-22 hoàn tất (triển khai MySQL thật + SMTP/AI Provider thật), không phải trong lúc phân tích ban đầu.
- **Một phần đã trả lời qua hành động thực tế**: 1/11 (OQ-07 — cập nhật 2026-08-18, xem chi tiết ở dòng tương ứng).
- **Còn mở**: 6/11 — không có câu hỏi nào trong số này **chặn** việc hoàn thành bộ tài liệu 00-22, vì mọi tài liệu đã mô tả trung thực trạng thái hiện tại kèm nhãn bằng chứng phù hợp bất kể câu trả lời cuối cùng là gì.

---

*Tài liệu tiếp theo (cuối cùng): `22_FINAL_CONSISTENCY_REVIEW.md`.*
