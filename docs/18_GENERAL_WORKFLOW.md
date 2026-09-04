# 18 — GENERAL WORKFLOW — ATS v2.1

**Mục đích**: mô tả luồng xử lý **tổng quát** áp dụng cho cả 37 endpoint (khác với `15_UML.md` mục 2, vốn chỉ minh họa 3 luồng cụ thể). Nguồn: đối chiếu cấu trúc lặp lại giữa toàn bộ `app/routers/*.py` đã đọc ở các Đợt trước.

## 1. Luồng xử lý 1 HTTP Request (tổng quát)

```mermaid
sequenceDiagram
    participant Client
    participant CORS as CORSMiddleware
    participant Route as FastAPI Router
    participant DI as Dependency Injection
    participant Auth as get_current_user / require_*
    participant Pydantic as Pydantic Schema (Request)
    participant Handler as Router Function
    participant Service as Service Layer (neu co)
    participant ORM as SQLAlchemy Session
    participant DB as SQLite
    participant Resp as Pydantic Schema (Response)

    Client->>CORS: HTTP Request (method, path, headers, body)
    CORS->>CORS: kiem tra Origin (allow_origins=["*"])
    CORS->>Route: forward request
    Route->>DI: resolve dependencies (get_db, current_user...)
    DI->>Auth: neu endpoint yeu cau xac thuc/phan quyen
    Auth->>Auth: giai ma JWT tu header Authorization
    alt Token thieu/sai/het han
        Auth-->>Client: 401 (dung tai day)
    else Token hop le
        Auth->>Auth: kiem tra role trong danh sach cho phep (neu co require_roles)
        alt Role khong du quyen
            Auth-->>Client: 403 (dung tai day)
        else Du quyen
            DI->>Pydantic: validate request body/query theo schema khai bao
            alt Validate that bai
                Pydantic-->>Client: 422 Unprocessable Entity (dung tai day)
            else Validate thanh cong
                DI->>Handler: goi ham router voi cac tham so da resolve
                alt Co Service Layer (module APP/OFFER/AI/EMAIL/AUTH)
                    Handler->>Service: goi ham nghiep vu tuong ung
                    Service->>ORM: truy van/ghi du lieu
                    ORM->>DB: SQL thuc te
                    DB-->>ORM: ket qua
                    Service->>Service: kiem tra business rule, state machine, 4-eyes...
                    alt Vi pham business rule
                        Service-->>Handler: raise HTTPException (409/400...)
                        Handler-->>Client: JSON loi {"detail": "MA_LOI"}
                    else Hop le
                        Service->>ORM: commit
                        Service-->>Handler: entity/tuple ket qua
                    end
                else Khong co Service Layer (module DEPT/DASH don gian)
                    Handler->>ORM: truy van/ghi truc tiep
                    ORM->>DB: SQL thuc te
                    DB-->>ORM: ket qua
                    Handler->>ORM: commit (neu co ghi)
                end
                Handler->>Resp: serialize ket qua theo response_model
                Resp-->>Client: 200/201 JSON
            end
        end
    end
```

## 2. Quy ước lỗi (Error Handling Convention)

`[CONFIRMED]` — toàn bộ lỗi nghiệp vụ dùng `fastapi.HTTPException(status_code, detail)`, `detail` luôn là 1 chuỗi **mã lỗi dạng SCREAMING_SNAKE_CASE** (VD `AI_CONSENT_REQUIRED`, `OFFER_SELF_APPROVAL_NOT_ALLOWED`), không phải câu văn tự nhiên — thiết kế để client (frontend) so khớp chuỗi và hiển thị thông báo phù hợp theo ngôn ngữ người dùng, tách biệt "mã lỗi kỹ thuật" khỏi "thông điệp hiển thị". Không có exception handler tùy chỉnh toàn cục (`@app.exception_handler`) — dùng nguyên cơ chế mặc định của FastAPI (`HTTPException` → JSON `{"detail": "..."}`, lỗi validate Pydantic → `422` với cấu trúc lỗi chi tiết từng field).

**Nhóm mã lỗi theo tầng**:

| Tầng phát sinh | HTTP Status thường gặp | Ví dụ |
|---|---|---|
| CORS/Auth (trước routing) | `401` | `NOT_AUTHENTICATED`, `INVALID_OR_EXPIRED_TOKEN` |
| RBAC (dependency) | `403` | `INSUFFICIENT_PERMISSION` |
| Pydantic (tự động, không phải HTTPException) | `422` | Lỗi định dạng field |
| Router (kiểm tra tồn tại/sở hữu) | `404`/`403` | `APPLICATION_NOT_FOUND`, `NOT_YOUR_APPLICATION` |
| Service (business rule/state machine) | `400`/`409` | `INVALID_STATUS_TRANSITION`, `OFFER_SELF_APPROVAL_NOT_ALLOWED` |

## 3. Luồng khởi động ứng dụng (Application Startup Workflow)

`[CONFIRMED]` — `app/main.py`:
1. Python import `app.main` → import toàn bộ router modules (đăng ký route vào FastAPI app instance).
2. Import `app.models` (side-effect: đăng ký toàn bộ model class với `Base.metadata`).
3. `lifespan()` context manager chạy khi `uvicorn` khởi động: gọi `Base.metadata.create_all(bind=engine)` — tạo bảng nếu chưa có (không migrate nếu đã có và schema đổi).
4. Đăng ký `CORSMiddleware`.
5. `include_router()` cho 10 router theo thứ tự cố định trong code (auth → users → departments → jobs → applications → offers → email_templates → ai → dashboard → audit) — thứ tự này **không ảnh hưởng hành vi** vì các router dùng prefix path khác nhau, không có route trùng path.
6. Mount `/static` (nếu thư mục tồn tại) + route `GET /` trả `index.html`.
7. `uvicorn` bắt đầu lắng nghe HTTP.

## 4. Luồng ghi Audit Log (Cross-cutting, áp dụng cho nhiều Use Case)

`[CONFIRMED]` — không phải middleware/interceptor tự động; mỗi service function **chủ động gọi** `audit_service.log(db, actor, action, entity_type, entity_business_id, before=..., after=..., reason=...)` tại đúng điểm cần ghi nhận, luôn **trong cùng transaction** với thay đổi dữ liệu chính (gọi trước `db.commit()` — xem `application_service.py`/`offer_service.py`, các lệnh `audit_service.log()` luôn đứng trước `db.commit()`), đảm bảo audit log và dữ liệu nghiệp vụ **commit hoặc rollback cùng nhau** (atomicity), không có tình huống ghi audit thành công nhưng dữ liệu chính rollback hoặc ngược lại.

---

*Kết thúc Đợt 6 (`16_DATABASE_DESIGN.md`, `17_TECHNOLOGY_STACK.md`, `18_GENERAL_WORKFLOW.md`). Tài liệu tiếp theo (Đợt 7 — đợt cuối): `19_TRACEABILITY_MATRIX.md`, `20_GAP_ANALYSIS.md`, `21_OPEN_QUESTIONS.md`, `22_FINAL_CONSISTENCY_REVIEW.md`.*
