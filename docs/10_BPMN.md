# 10 — BPMN DIAGRAMS (Mermaid) — ATS v2.1

**Ghi chú kỹ thuật**: Mermaid không có ký hiệu BPMN Pool/Lane hay Gateway chuẩn (◇). Tài liệu này dùng `flowchart` với `subgraph` để mô phỏng **Lane theo Actor**, hình thoi (`{...}`) mô phỏng **Exclusive Gateway**, và `stateDiagram-v2` cho các máy trạng thái đầy đủ. Toàn bộ nội dung sơ đồ bám sát đúng logic đã đặc tả bằng chữ ở `09_BUSINESS_PROCESS.md` — không thêm bước nào không có trong code.

---

## 10.1 BP-JOB-001 — Vòng đời tin tuyển dụng

```mermaid
flowchart TD
    subgraph LANE_HRM["Lane: HR_MANAGER / ADMIN"]
        A1([Bắt đầu: cần tuyển vị trí]) --> A2[Tạo tin - FN-JOB-01\nstatus=DRAFT]
        A2 --> A3[Gán HR phụ trách - FN-JOB-02]
        A3 --> A4[Đăng tin - FN-JOB-03\nstatus: DRAFT to PUBLISHED]
    end
    subgraph LANE_SYS["Lane: ACT-SYSTEM"]
        A4 --> A5{Có Offer nào vừa\nAccept cho Job này?}
        A5 -- Không --> A5
        A5 -- Có --> A6{HIRED count\n>= quantity?}
        A6 -- Chưa đủ --> A5
        A6 -- Đủ --> A7[Tự đóng tin\nstatus to CLOSED]
        A7 --> A8([Kết thúc: đủ chỉ tiêu])
    end
    subgraph LANE_CAND["Lane: CANDIDATE"]
        A4 --> B1[Xem / tìm tin đã đăng - FN-JOB-04/05]
        B1 --> B2[[Nộp hồ sơ - xem BP-APP-001]]
    end
```

## 10.2 BP-APP-001 — Ứng viên nộp hồ sơ (kể cả tái ứng tuyển)

```mermaid
flowchart TD
    subgraph LANE_CAND["Lane: CANDIDATE"]
        S1([Bắt đầu]) --> S2{ai_consent = true?}
        S2 -- Không --> S3[["400 AI_CONSENT_REQUIRED"]]
        S2 -- Có --> S4[Gửi request nộp hồ sơ\n+ Idempotency-Key tùy chọn - FN-APP-01]
    end
    subgraph LANE_SYS["Lane: ACT-SYSTEM"]
        S4 --> S5{Job tồn tại và\nstatus = PUBLISHED?}
        S5 -- Không --> S6[["404 JOB_NOT_FOUND_OR_NOT_PUBLISHED"]]
        S5 -- Có --> S7{Idempotency-Key\ntrùng request trước?}
        S7 -- Có --> S8[Trả lại Application cũ\naudit APPLICATION_DUPLICATE_REQUEST]
        S8 --> S9([Kết thúc - is_new=false])
        S7 -- Không --> S10[Tìm/tạo Candidate\ndedupe theo email]
        S10 --> S11[Tạo Application mới\nstatus=NEW, ke thua assigned_hr_id\nKHÔNG kiểm tra cooldown - BRULE-02]
        S11 --> S12{resume_text\nđược gửi kèm?}
        S12 -- Có --> S13[Lưu Resume text]
        S12 -- Không --> S14
        S13 --> S14[Ghi audit\nAPPLICATION_CREATED / REAPPLIED]
        S14 --> S15[["Kích hoạt email\nAPPLICATION_RECEIVED - BP-EMAIL-001"]]
        S15 --> S16([Kết thúc - is_new=true])
    end
```

## 10.3 BP-APP-002 — Máy trạng thái Application (đầy đủ 10 giá trị)

```mermaid
stateDiagram-v2
    [*] --> NEW: FN-APP-01 (nộp hồ sơ)
    NEW --> SCREENING: HR chuyển tiến (fallback thủ công)\nhoặc FN-AI-01 tự chuyển
    NEW --> AI_SCREENING: FN-AI-01 (đang gọi AI)
    AI_SCREENING --> SCREENING: FN-AI-01 hoàn tất
    SCREENING --> SHORTLISTED: HR+ (FN-APP-05, forward)
    SCREENING --> REJECTED: HR+ (FN-APP-05, forward)
    SHORTLISTED --> INTERVIEW: HR+ (FN-APP-05, forward)
    INTERVIEW --> REJECTED: HR+ (FN-APP-05, forward)
    INTERVIEW --> OFFER: chỉ qua offer_service.send_offer()\n(BP-OFFER-001, KHÔNG qua FN-APP-05)
    OFFER --> HIRED: Candidate Accept Offer\n(BP-OFFER-001 bước 5)
    OFFER --> REJECTED: Candidate Decline Offer\nhoặc Offer EXPIRED
    NEW --> WITHDRAWN: Candidate tự rút (FN-APP-06)
    AI_SCREENING --> WITHDRAWN: Candidate tự rút
    SCREENING --> WITHDRAWN: Candidate tự rút
    SHORTLISTED --> WITHDRAWN: Candidate tự rút
    INTERVIEW --> WITHDRAWN: Candidate tự rút
    NEW --> ARCHIVED: HR_MANAGER/ADMIN (FN-APP-07)
    SCREENING --> ARCHIVED: HR_MANAGER/ADMIN
    SHORTLISTED --> ARCHIVED: HR_MANAGER/ADMIN
    INTERVIEW --> ARCHIVED: HR_MANAGER/ADMIN
    REJECTED --> ARCHIVED: HR_MANAGER/ADMIN
    note right of HIRED
        Trạng thái duy nhất
        KHÔNG thể Archive
        (BRULE-04)
    end note
    HIRED --> [*]
    WITHDRAWN --> [*]
    ARCHIVED --> [*]
    REJECTED --> [*]
```

**Ghi chú đối chiếu code**: các cạnh lùi (VD `SHORTLISTED → SCREENING`) không vẽ riêng từng cạnh trong sơ đồ trên vì áp dụng đồng loạt theo `PIPELINE_ORDER` (bất kỳ cặp `(hiện tại, đích)` nào mà đích đứng trước hiện tại trong thứ tự `NEW→AI_SCREENING→SCREENING→SHORTLISTED→INTERVIEW→OFFER→HIRED` đều hợp lệ về mặt kỹ thuật, với điều kiện actor là HR_MANAGER/ADMIN và có `reason` — xem `09_BUSINESS_PROCESS.md` BP-APP-002). Đây là khác biệt so với BPMN chuẩn (thường vẽ tường minh từng cạnh) — chọn cách chú thích gộp để sơ đồ không bị rối bởi ~15 cạnh lùi khả dĩ.

## 10.4 BP-OFFER-001 — Quy trình Offer 4-eyes Approval

```mermaid
flowchart TD
    subgraph LANE_HR["Lane: HR (creator)"]
        O1([Bắt đầu: quyết định mời nhận việc]) --> O2[Tạo Offer - FN-OFFER-02\nstatus=DRAFT, creator_id=HR]
        O2 --> O3[Nộp duyệt - FN-OFFER-03\nstatus to PENDING_APPROVAL]
    end
    subgraph LANE_MGR["Lane: HR_MANAGER / ADMIN (approver)"]
        O3 --> O4{actor.id ==\noffer.creator_id?}
        O4 -- Đúng --------> O5[["409 OFFER_SELF_APPROVAL_NOT_ALLOWED\naudit OFFER_SELF_APPROVAL_BLOCKED"]]
        O4 -- Khác nhau: OK --> O6{Quyết định duyệt?}
        O6 -- Duyệt - FN-OFFER-04 --> O7[status to APPROVED\napprover_id = actor]
        O6 -- Từ chối - FN-OFFER-05\nbắt buộc reason --> O8[status to DRAFT\nkhông phải trạng thái kết thúc]
        O8 -.quay lại nộp duyệt.-> O3
    end
    subgraph LANE_HR2["Lane: HR (bất kỳ, đủ quyền gửi)"]
        O7 --> O9[Gửi Offer - FN-OFFER-06\nstatus to SENT, expires_at = +7 ngày\nApplication to OFFER]
        O9 --> O10[["Kích hoạt email OFFER - BP-EMAIL-001"]]
    end
    subgraph LANE_CAND["Lane: CANDIDATE"]
        O10 --> O11{Phản hồi - FN-OFFER-07}
        O11 -- Accept --> O12[Offer to ACCEPTED\nApplication to HIRED]
        O12 --> O13[["Kiểm tra tự đóng Job - BP-JOB-001"]]
        O13 --> O14[["Kích hoạt email ONBOARDING"]]
        O14 --> O15([Kết thúc: tuyển dụng thành công])
        O11 -- Decline --> O16[Offer to DECLINED\nApplication to REJECTED]
        O16 --> O17([Kết thúc: ứng viên từ chối])
    end
```

## 10.5 BP-OFFER-002 — Offer tự động hết hạn *(chưa được lịch hóa — Gap)*

```mermaid
flowchart TD
    T1([Trigger dự kiến: lịch chạy nền định kỳ]) -.KHÔNG TỒN TẠI\ntrong app hiện tại.-> T2
    T2[Quét Offer status=SENT\nvà expires_at < now] --> T3[Với mỗi Offer:\nstatus to EXPIRED]
    T3 --> T4[Application tương ứng\nto REJECTED]
    T4 --> T5[Ghi audit OFFER_EXPIRED]
    style T1 stroke-dasharray: 5 5,fill:#fff3cd
```

## 10.6 BP-AI-001 — AI Screening (Graceful Degradation)

```mermaid
flowchart TD
    subgraph LANE_HR["Lane: HR+"]
        I1([Bắt đầu: cần đánh giá phù hợp]) --> I2[Gọi phân tích - FN-AI-01]
    end
    subgraph LANE_SYS["Lane: ACT-SYSTEM"]
        I2 --> I3{HR có nằm trong\nphạm vi được gán?}
        I3 -- Không --> I4[["403 NOT_YOUR_ASSIGNED_APPLICATION"]]
        I3 -- Có --> I5{Có text CV\nkhả dụng?}
        I5 -- Không --> I6[["202 Accepted\nneeds_manual_review=true"]]
        I5 -- Có --> I7{AI_API_KEY\nđã cấu hình?}
        I7 -- Có --> I8[Gọi AI Provider that\nGemini hoac Claude]
        I8 --> I9{Lỗi?}
        I9 -- Có, lần 1 --> I8b[Thử lại 1 lần]
        I9 -- Không --> I10
        I8b --> I9b{Vẫn lỗi?}
        I9b -- Có --> I11
        I9b -- Không --> I10
        I7 -- Không --> I11[Fallback: so khớp\ntừ khóa nội bộ - stub]
        I10[Lưu AIAnalysis is_latest=true\ncác bản cũ to is_latest=false] --> I12
        I11 --> I10
        I12{status hiện tại\ntrong NEW/AI_SCREENING?}
        I12 -- Có --> I13[Tự chuyển to SCREENING]
        I12 -- Không --> I14
        I13 --> I14([Kết thúc\nKHÔNG tự Shortlist/Reject - AI-6])
    end
```

## 10.7 BP-EMAIL-001 — Email tự động theo giai đoạn

```mermaid
flowchart TD
    subgraph LANE_TRIGGER["Lane: ACT-SYSTEM (6 điểm neo sự kiện)"]
        E1[Nộp hồ sơ mới] --> E7
        E2[Chuyển SHORTLISTED] --> E7
        E3[Chuyển INTERVIEW] --> E7
        E4[Chuyển REJECTED] --> E7
        E5[Gửi Offer] --> E7
        E6[Candidate Accept Offer] --> E7
        E7[trigger_stage_email]
    end
    subgraph LANE_SYS["Lane: ACT-SYSTEM (xử lý)"]
        E7 --> E8{Có mẫu ACTIVE\nkhớp loại sự kiện?}
        E8 -- Không --> E9[["Bỏ qua im lặng\nEMAIL-7 - không lỗi giao dịch chính"]]
        E8 -- Có --> E10[Thay thế biến trong nội dung]
        E10 --> E11{SMTP đã\ncấu hình?}
        E11 -- Có --> E12[Gửi thật qua SMTP]
        E11 -- Không --> E13[Ghi log giả lập]
        E12 --> E14[Ghi audit_logs\nchỉ luu to, subject - Gap EMAIL-10]
        E13 --> E14
    end
    subgraph LANE_HR["Lane: HR+ (nhánh thủ công, song song)"]
        M1([HR chọn mẫu + Application]) --> M2[Gửi thủ công - FN-EMAIL-05]
        M2 --> E10
    end
```

---

*Kết thúc Đợt 3 (`08_FUNCTIONAL_SPECIFICATION.md`, `09_BUSINESS_PROCESS.md`, `10_BPMN.md`). Tài liệu tiếp theo (Đợt 4): `11_USE_CASE.md`, `12_USE_CASE_SPECIFICATION.md`.*
