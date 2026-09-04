# 15 — UML DIAGRAMS — ATS v2.1

Gộp Class + Sequence + Activity + Component + Deployment Diagram theo đề xuất ở `01_MASTER_DOCUMENT_OUTLINE.md` mục B. Nguồn: `app/models/*.py` (12 file, đọc trực tiếp toàn bộ ở Đợt 5), `app/services/*.py`.

---

## 1. CLASS DIAGRAM

`[CONFIRMED]` — trích xuất trực tiếp từ SQLAlchemy model (không suy đoán thuộc tính). Không vẽ `id` (PK kỹ thuật nội bộ) trong diagram để đỡ rối — chỉ giữ `business_id` (định danh nghiệp vụ hiển thị, theo CHANGE 03).

```mermaid
classDiagram
    class User {
        +String business_id
        +String full_name
        +String email
        +String password_hash
        +UserRole role
        +UserStatus status
        +String refresh_token_hash
        +DateTime refresh_token_expires_at
    }
    class Department {
        +String business_id
        +String name
        +String description
        +DepartmentStatus status
    }
    class Job {
        +String business_id
        +String slug
        +String title
        +Text description
        +Text requirements
        +Decimal salary_min
        +Decimal salary_max
        +Integer quantity
        +String location
        +EmploymentType employment_type
        +JobStatus status
        +DateTime published_at
        +DateTime deadline
    }
    class Candidate {
        +String business_id
        +String full_name
        +String email
        +String phone
        +Gender gender
        +Date date_of_birth
        +String address
        +Decimal current_salary
        +Decimal expected_salary
    }
    class Application {
        +String business_id
        +String source
        +ApplicationStatus status
        +Integer match_score
        +Integer needs_manual_review
        +ArchiveReason archive_reason
        +String idempotency_key
        +DateTime applied_at
    }
    class Resume {
        +String business_id
        +String file_name
        +String file_path
        +String file_type
        +Text extracted_text
        +Text parsed_data
    }
    class AIAnalysis {
        +String business_id
        +Boolean is_latest
        +String provider
        +String model
        +Integer match_score
        +Text matched_skills
        +Text missing_skills
        +Text strengths
        +Text weaknesses
        +Text recommendation
    }
    class Interview {
        +String business_id
        +DateTime scheduled_at
        +String location
        +String meeting_link
        +Integer rating
        +Text feedback
        +InterviewStatus status
        +String hiring_manager_name
        +String hiring_manager_email
    }
    class Offer {
        +String business_id
        +Decimal salary
        +Decimal probation_salary
        +Date start_date
        +OfferStatus status
        +DateTime expires_at
        +Text rejection_reason
    }
    class EmailTemplate {
        +String business_id
        +String name
        +EmailTemplateType type
        +String subject
        +Text content
        +EmailTemplateStatus status
    }
    class AuditLog {
        +String business_id
        +String action
        +String entity_type
        +String entity_business_id
        +Text before_data
        +Text after_data
        +Text reason
    }
    class IDSequence {
        +String entity_type
        +Integer last_number
    }

    Department "1" --> "0..*" User : department_id
    Department "1" --> "0..*" Job : department_id
    User "1" --> "0..*" Job : created_by
    User "0..1" --> "0..*" Job : assigned_hr_id
    User "0..1" --> "0..*" Job : approved_by
    User "0..1" --> "0..1" Candidate : user_id (Candidate co the chua co User)
    Job "1" --> "0..*" Application : job_id
    Candidate "1" --> "0..*" Application : candidate_id
    User "0..1" --> "0..*" Application : assigned_hr_id
    Application "1" --> "0..1" Resume : application_id (UNIQUE)
    Candidate "1" --> "0..*" Resume : candidate_id
    Application "1" --> "0..*" AIAnalysis : application_id
    Application "1" --> "0..*" Interview : application_id
    User "1" --> "0..*" Interview : interviewer_id
    Application "1" --> "0..*" Offer : application_id
    User "1" --> "0..*" Offer : creator_id
    User "0..1" --> "0..*" Offer : approver_id
    User "1" --> "0..*" EmailTemplate : created_by
    User "1" --> "0..*" AuditLog : actor_user_id

    note for Offer "CheckConstraint ck_offer_approver_not_creator:\napprover_id IS NULL OR approver_id != creator_id\n(4-eyes - CHANGE 01)"
    note for Application "UniqueConstraint uq_application_candidate_idem:\n(candidate_id, idempotency_key)\n(chong nop trung - CHANGE 02)"
```

**Quan hệ đáng chú ý phát hiện khi đọc code** (không tự nhiên thấy nếu chỉ đọc ERD):
- `User.department_id` là **tùy chọn** (`nullable=True` — không thấy trong code trích) — một User (kể cả HR/HR_MANAGER/ADMIN) có thể không gắn phòng ban.
- `Candidate.user_id` là **tùy chọn** (`nullable=True`) — về lý thuyết CSDL cho phép tồn tại `Candidate` không gắn `User` nào (dấu vết của khả năng "HR tạo hồ sơ Candidate hộ" được nhắc trong comment code `app/routers/applications.py` dòng dedupe, dù không có endpoint nào hiện thực việc HR tự tạo Candidate).
- `Job` có **3 quan hệ riêng biệt** tới `User` (`created_by`, `assigned_hr_id`, `approved_by`) — 3 vai trò khác nhau của "người tạo/người phụ trách/người duyệt" cùng trỏ vào 1 bảng `users`, không phải 3 bảng riêng.

## 2. SEQUENCE DIAGRAM

### 2.1 UC-APP-001 — Nộp hồ sơ ứng tuyển (kèm nhánh Idempotency)

```mermaid
sequenceDiagram
    actor Candidate
    participant Router as applications.py::apply
    participant Svc as application_service.py
    participant DB as SQLAlchemy Session
    participant EmailSvc as email_service.py

    Candidate->>Router: POST /applications (ai_consent, job_id, Idempotency-Key)
    Router->>Router: kiem tra role == CANDIDATE
    Router->>Router: kiem tra ai_consent == true
    Router->>DB: query Job (business_id, status=PUBLISHED)
    DB-->>Router: Job hoac None
    alt Job khong ton tai/khong PUBLISHED
        Router-->>Candidate: 404 JOB_NOT_FOUND_OR_NOT_PUBLISHED
    else Job hop le
        Router->>Svc: apply_for_job(candidate, job, idempotency_key, ...)
        Svc->>DB: query Application WHERE candidate_id + idempotency_key
        alt Trung Idempotency-Key
            DB-->>Svc: Application da ton tai
            Svc->>DB: audit_service.log(APPLICATION_DUPLICATE_REQUEST)
            Svc-->>Router: (existing_application, is_new=False)
        else Khong trung
            Svc->>DB: tim/tao Candidate (dedupe email)
            Svc->>DB: INSERT Application (status=NEW)
            opt resume_text duoc gui kem
                Svc->>DB: INSERT Resume
            end
            Svc->>DB: audit_service.log(APPLICATION_CREATED/REAPPLIED)
            Svc->>DB: commit
            Svc->>EmailSvc: trigger_stage_email(APPLICATION_RECEIVED)
            EmailSvc->>DB: query EmailTemplate WHERE type=APPLICATION_RECEIVED, status=ACTIVE
            alt Co mau ACTIVE
                EmailSvc->>EmailSvc: render_template + gui (SMTP that/gia lap)
                EmailSvc->>DB: audit_service.log(gui email)
            else Khong co mau
                EmailSvc-->>Svc: bo qua im lang (khong loi)
            end
            Svc-->>Router: (new_application, is_new=True)
        end
        Router-->>Candidate: 200 ApplicationOut
    end
```

### 2.2 UC-OFFER-004 — Duyệt Offer (4-eyes approval)

```mermaid
sequenceDiagram
    actor Approver as HR_MANAGER/ADMIN
    participant Router as offers.py::approve_offer
    participant Svc as offer_service.py::approve_offer
    participant DB as SQLAlchemy Session + CheckConstraint

    Approver->>Router: POST /offers/{id}/approve
    Router->>Router: require_offer_approver (role check)
    Router->>Svc: approve_offer(offer, actor)
    Svc->>Svc: kiem tra offer.status == PENDING_APPROVAL
    alt actor.id == offer.creator_id
        Svc->>DB: audit_service.log(OFFER_SELF_APPROVAL_BLOCKED)
        Svc->>DB: commit (chi audit, KHONG doi status)
        Svc-->>Router: raise 409 OFFER_SELF_APPROVAL_NOT_ALLOWED
        Router-->>Approver: 409
    else actor.id != offer.creator_id
        Svc->>DB: UPDATE Offer SET status=APPROVED, approver_id=actor.id
        DB->>DB: CheckConstraint ck_offer_approver_not_creator (lop bao ve thu 2)
        DB-->>Svc: OK (constraint thoa man)
        Svc->>DB: audit_service.log(OFFER_APPROVED)
        Svc->>DB: commit
        Svc-->>Router: Offer (status=APPROVED)
        Router-->>Approver: 200 OfferOut
    end
```

### 2.3 UC-AI-001 — Phân tích AI Screening (Graceful Degradation)

```mermaid
sequenceDiagram
    actor HR
    participant Router as ai.py::analyze
    participant Svc as ai_service.py::run_screening
    participant AIProvider as AI Provider API (Gemini/Claude)
    participant DB as SQLAlchemy Session

    HR->>Router: POST /ai/analyze/{application_id}
    Router->>Router: require_hr_or_above + _check_scope (assigned_hr_id)
    Router->>Svc: run_screening(application, actor)
    Svc->>DB: lay text CV moi nhat cua Application
    alt Khong co text CV
        Svc-->>Router: None
        Router-->>HR: 202 Accepted (needs_manual_review=true)
    else Co text CV
        Svc->>Svc: kiem tra AI_API_KEY + dispatch theo AI_PROVIDER (PROVIDER_CALLERS)
        alt Co cau hinh, provider hop le
            Svc->>AIProvider: goi API so sanh CV vs JD (_call_gemini hoac _call_claude)
            alt Loi lan 1
                Svc->>AIProvider: thu lai 1 lan
                alt Van loi
                    Svc->>Svc: fallback stub (so khop tu khoa)
                else Thanh cong lan 2
                    AIProvider-->>Svc: ket qua that
                end
            else Thanh cong ngay
                AIProvider-->>Svc: ket qua that
            end
        else Khong cau hinh, hoac AI_PROVIDER khong duoc ho tro
            Svc->>Svc: fallback stub (so khop tu khoa)
        end
        Svc->>DB: UPDATE AIAnalysis cu SET is_latest=False
        Svc->>DB: INSERT AIAnalysis moi (is_latest=True)
        opt status hien tai trong {NEW, AI_SCREENING}
            Svc->>DB: UPDATE Application SET status=SCREENING
        end
        Svc->>DB: commit
        Svc-->>Router: AIAnalysis
        Router-->>HR: 200 AIAnalysisOut
    end
```

## 3. ACTIVITY DIAGRAM — Thuật toán xác thực chuyển trạng thái Application (`update_status`)

`[CONFIRMED]` — mô tả chi tiết thuật toán bên trong `application_service.py::update_status` (bổ sung góc nhìn "activity/thuật toán" cho phần đã mô tả bằng state machine ở `10_BPMN.md` mục 10.3):

```mermaid
flowchart TD
    Start([Nhan yeu cau doi status]) --> Step1[Xac dinh current = application.status]
    Step1 --> Step2{new_status trong\nFORWARD_EDGES current?}
    Step2 -- Co --> ForwardFlag[is_forward = True]
    Step2 -- Khong --> Step3{current va new_status\ndeu trong PIPELINE_ORDER?}
    Step3 -- Khong --> Reject1[["409 INVALID_STATUS_TRANSITION"]]
    Step3 -- Co --> Step4{index new_status\n< index current?}
    Step4 -- Khong --> Reject1
    Step4 -- Co --> BackwardFlag[is_backward = True]
    ForwardFlag --> Step5{actor.role trong\nHR/HR_MANAGER/ADMIN?}
    Step5 -- Khong --> Reject2[["403 INSUFFICIENT_PERMISSION"]]
    Step5 -- Co --> Apply[Cap nhat status, ghi audit\nAPPLICATION_STATUS_CHANGED]
    BackwardFlag --> Step6{actor.role trong\nHR_MANAGER/ADMIN?}
    Step6 -- Khong --> Reject3[["403 ONLY_HR_MANAGER_OR_ADMIN_CAN_REVERT"]]
    Step6 -- Co --> Step7{reason duoc\ncung cap?}
    Step7 -- Khong --> Reject4[["400 REASON_REQUIRED_FOR_REVERT"]]
    Step7 -- Co --> Apply2[Cap nhat status, ghi audit\nSTATUS_REVERTED]
    Apply --> Step8{new_status trong\nSTATUS_TO_EMAIL_EVENT?}
    Step8 -- Co --> Email[Kich hoat email tuong ung]
    Step8 -- Khong --> End([Ket thuc])
    Email --> End
    Apply2 --> End2([Ket thuc - KHONG kich hoat email])
```

## 4. COMPONENT DIAGRAM

`[CONFIRMED]` — mở rộng góc nhìn thành phần từ `14_SYSTEM_ARCHITECTURE.md` mục 2, tập trung vào interface giữa các thành phần:

```mermaid
flowchart LR
    subgraph "Component: API Layer"
        direction TB
        Auth[[auth]] 
        Users[[users]]
        Depts[[departments]]
        Jobs[[jobs]]
        Apps[[applications]]
        Offers[[offers]]
        Emails[[email-templates]]
        AI[[ai]]
        Dash[[dashboard]]
        Audit[[audit]]
    end
    subgraph "Component: RBAC"
        RBAC{{app/deps/rbac.py}}
    end
    subgraph "Component: Business Services"
        AppSvc([application_service])
        OfferSvc([offer_service])
        EmailSvc([email_service])
        AISvc([ai_service])
        AuditSvc([audit_service])
        ResumeSvc([resume_service + resume_parser])
        AuthSvc([auth_service])
    end
    subgraph "Component: Core Infrastructure"
        DBCore[(database.py)]
        SecCore{{security.py}}
        IDCore{{id_generator.py}}
        CfgCore{{config.py}}
    end

    Apps -.uses.-> RBAC
    Offers -.uses.-> RBAC
    Emails -.uses.-> RBAC
    AI -.uses.-> RBAC
    Dash -.uses.-> RBAC
    Audit -.uses.-> RBAC
    Users -.uses.-> RBAC
    Depts -.uses.-> RBAC
    Jobs -.uses.-> RBAC

    Apps --> AppSvc
    Apps --> ResumeSvc
    Offers --> OfferSvc
    Emails --> EmailSvc
    AI --> AISvc
    Auth --> AuthSvc

    AppSvc --> AuditSvc
    AppSvc --> EmailSvc
    OfferSvc --> AuditSvc
    OfferSvc --> EmailSvc
    AppSvc --> IDCore
    OfferSvc --> IDCore
    AuthSvc --> SecCore
    AppSvc --> DBCore
    OfferSvc --> DBCore
    EmailSvc --> CfgCore
    AISvc --> CfgCore
```

## 5. DEPLOYMENT DIAGRAM — `[MISSING]`

`[CONFIRMED — không đủ bằng chứng để vẽ]`. Như đã nêu ở `14_SYSTEM_ARCHITECTURE.md` mục 10, `ats-v2/` không chứa Dockerfile, file compose, cấu hình CI/CD, hay tài liệu vận hành production. Vẽ 1 Deployment Diagram đầy đủ (node, artifact, giao thức mạng giữa các node) tại thời điểm này sẽ là **suy đoán không có căn cứ**, vi phạm RULE 1 và RULE 5. Thay vào đó, ghi nhận trạng thái triển khai **duy nhất có bằng chứng**:

```mermaid
flowchart TB
    subgraph NODE["1 Node duy nhất (đã xác nhận qua uvicorn) - [CONFIRMED]"]
        P[Python process: uvicorn app.main:app]
        F[(SQLite - ats_v2.db\nfallback mac dinh)]
        S[(Thư mục: app/static - file CV upload)]
        P --> F
        P --> S
    end
    subgraph EXT_DB["Node CSDL rieng (tuy chon) - [CONFIRMED, khi USE_MYSQL=true]"]
        MYSQL[(MySQL Server\nrecruitment_db)]
    end
    Browser -->|HTTP| P
    P -.TCP 3306, fallback ve SQLite neu loi.-> MYSQL
    P -.HTTPS, da cau hinh that.-> AIProvider[[AI Provider API\nGemini hoac Claude]]
    P -.SMTP, da cau hinh that.-> SMTP[[SMTP Gmail]]
```

**[CẬP NHẬT sau STEP 1]** Khác với nhận định ban đầu ("chưa cấu hình"), cả AI Provider và SMTP hiện đã được cấu hình bằng credential thật và kiểm chứng hoạt động; MySQL cũng đã được thêm như 1 lựa chọn triển khai CSDL thật (không còn chỉ là SQLite). Đây vẫn là mô tả trạng thái **1 node duy nhất chạy `uvicorn`** cục bộ — chưa có bằng chứng triển khai multi-node/container hóa thật (giữ nguyên đánh giá `[MISSING]` cho Deployment Diagram production đầy đủ).

Đây được ghi nhận là Gap ở `20_GAP_ANALYSIS.md` (Deployment Diagram không thể hoàn thiện do thiếu bằng chứng hạ tầng), không phải một sơ đồ triển khai production thật.

---

*Kết thúc Đợt 5 (`13_SYSTEM_MODELING.md`, `14_SYSTEM_ARCHITECTURE.md`, `15_UML.md`). Tài liệu tiếp theo (Đợt 6): `16_DATABASE_DESIGN.md`, `17_TECHNOLOGY_STACK.md`, `18_GENERAL_WORKFLOW.md`.*
