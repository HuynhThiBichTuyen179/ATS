# 02 — CƠ SỞ LÝ THUYẾT

Chỉ trình bày các lý thuyết **thực sự được áp dụng** trong `ats-v2/` — mỗi mục đều có phần "Cách project áp dụng" trỏ về bằng chứng cụ thể trong source code, theo đúng yêu cầu không đưa lý thuyết vào chỉ để làm tài liệu dài hơn.

## Mục lục

1. Kiến trúc phân lớp (Layered Architecture)
2. REST API & Kiến trúc Client-Server
3. Object-Relational Mapping (ORM)
4. Cơ sở dữ liệu quan hệ & ERD
5. Xác thực (Authentication) bằng JWT
6. Phân quyền (Authorization) — RBAC
7. State Machine (Máy trạng thái hữu hạn)
8. Idempotency trong thiết kế API
9. Graceful Degradation (chế độ dự phòng khi dịch vụ ngoài không khả dụng)
10. UML (Unified Modeling Language)
11. BPMN (Business Process Model and Notation)
12. Data Transfer Object (DTO) qua Pydantic Schema

---

## 1. Kiến trúc phân lớp (Layered Architecture)

**Khái niệm**: chia hệ thống thành các lớp (layer) độc lập, mỗi lớp chỉ giao tiếp với lớp liền kề, giảm coupling và tăng khả năng bảo trì.

**Mục đích**: tách biệt logic trình bày (presentation), logic nghiệp vụ (business logic), và logic truy xuất dữ liệu (data access).

**Đặc điểm**: mỗi lớp có trách nhiệm rõ ràng; lớp trên gọi lớp dưới qua interface/hàm, không có chiều ngược lại; dễ thay thế 1 lớp mà không ảnh hưởng lớp khác.

**Cách project áp dụng — `[CONFIRMED]`**: `ats-v2/` chia 3 lớp rõ rệt:
- **Router layer** (`app/routers/*.py`) — nhận HTTP request, validate input qua Pydantic schema, gọi RBAC dependency, gọi service, trả response. Xác nhận: không có router nào chứa câu lệnh SQLAlchemy trực tiếp thao tác nghiệp vụ phức tạp — mọi router `import` hàm từ `app/services/`.
- **Service layer** (`app/services/*.py`) — chứa toàn bộ business logic (state machine, 4-eyes approval, sinh Business ID...). Đây là lớp duy nhất chứa quyết định nghiệp vụ.
- **Model layer** (`app/models/*.py`) — định nghĩa entity qua SQLAlchemy ORM, ánh xạ trực tiếp tới bảng.

Không phát hiện lớp Repository/DAO tách biệt khỏi Service — Service layer gọi trực tiếp SQLAlchemy `Session` (không qua lớp trung gian riêng) — `[CONFIRMED]`, xác nhận qua mọi file trong `app/services/` đều `import Session` và gọi `db.query(...)` trực tiếp.

## 2. REST API & Kiến trúc Client-Server

**Khái niệm**: REST (Representational State Transfer) là kiểu kiến trúc dùng HTTP method (GET/POST/PUT/DELETE) tác động lên "resource" định danh bằng URL, trao đổi dữ liệu dạng JSON.

**Mục đích**: tách biệt Client (nơi hiển thị) và Server (nơi xử lý), giao tiếp qua giao thức chuẩn, không phụ thuộc công nghệ 2 phía.

**Cách project áp dụng — `[CONFIRMED]`**: 35 endpoint (`00_PROJECT_DISCOVERY.md` mục 7) đều theo mẫu `<METHOD> /<resource>[/{id}][/<action>]`, dùng JSON cho request/response (trừ 2 endpoint multipart: `POST /applications`... thực chất JSON, chỉ riêng `POST /applications/{id}/resume` dùng `multipart/form-data` vì truyền file). Client (`app/static/index.html`) và Server (FastAPI) là 2 thành phần tách biệt, giao tiếp thuần qua `fetch()`.

## 3. Object-Relational Mapping (ORM)

**Khái niệm**: kỹ thuật ánh xạ giữa đối tượng lập trình hướng đối tượng và bảng quan hệ trong CSDL, cho phép thao tác CSDL bằng code thay vì viết SQL thuần.

**Mục đích**: giảm code lặp, tăng an toàn (tránh SQL Injection do tự động tham số hóa câu lệnh), độc lập tương đối với hệ quản trị CSDL cụ thể.

**Cách project áp dụng — `[CONFIRMED]`**: dùng **SQLAlchemy 2.0.35** (`requirements.txt`). Mỗi model kế thừa `Base` (`app/core/database.py`), định nghĩa qua `Column`, quan hệ qua `relationship()`/`ForeignKey`. Toàn bộ truy vấn trong `app/services/` dùng `db.query(Model)...` — không tìm thấy câu lệnh SQL thô (raw SQL) nào trong `app/`.

## 4. Cơ sở dữ liệu quan hệ & ERD

**Khái niệm**: mô hình dữ liệu tổ chức thành các bảng có quan hệ với nhau qua khóa chính (Primary Key)/khóa ngoại (Foreign Key); Entity-Relationship Diagram (ERD) biểu diễn trực quan các bảng và quan hệ.

**Cách project áp dụng — `[CONFIRMED]`**: 11 bảng nghiệp vụ + 1 bảng phụ trợ (`id_sequences`), có đầy đủ PK/FK/UNIQUE/CHECK constraint (VD `ck_offer_approver_not_creator` trên bảng `offers` — `app/models/offer.py`). Chi tiết đầy đủ ở `16_DATABASE_DESIGN.md` (Đợt 6).

## 5. Xác thực (Authentication) bằng JWT

**Khái niệm**: JSON Web Token (JWT) là chuỗi mã hóa chứa thông tin định danh người dùng (payload), được ký số (signature) để chống giả mạo; Client gửi kèm token trong header `Authorization: Bearer <token>` ở mỗi request.

**Nguyên lý**: Server cấp token sau khi xác thực thành công (login); token có thời hạn (expiry); Server xác minh chữ ký + hạn dùng ở mỗi request, không cần lưu session phía server (stateless).

**Cách project áp dụng — `[CONFIRMED]`**: `app/core/security.py` dùng thư viện `python-jose` để tạo/giải mã JWT (thuật toán HS256, xác nhận qua `ALGORITHM = "HS256"`). Access Token sống **8 giờ** (`settings.jwt_access_token_hours`). Kèm theo cơ chế **Refresh Token** (chuỗi ngẫu nhiên, lưu dạng hash SHA-256 trong cột `users.refresh_token_hash`, sống **30 ngày**) để cấp lại Access Token mà không cần đăng nhập lại — `[CONFIRMED]` qua `app/services/auth_service.py::refresh_access_token`.

## 6. Phân quyền (Authorization) — Role-Based Access Control (RBAC)

**Khái niệm**: mô hình phân quyền dựa trên vai trò (role); mỗi người dùng được gán 1 hoặc nhiều role, mỗi role có tập quyền xác định; hệ thống kiểm tra role của người dùng trước khi cho phép thực hiện hành động.

**Cách project áp dụng — `[CONFIRMED]`**: 4 role cố định (`UserRole` enum), **không có bảng `roles`/`permissions` riêng** — đây là mô hình RBAC đơn giản hóa (role hard-code, không có ma trận permission động trong DB). Kiểm tra quyền qua FastAPI dependency (`app/deps/rbac.py::require_roles(*roles)`), áp dụng ở tầng router (chặn truy cập endpoint) **và** tầng service (chặn theo phạm vi dữ liệu — VD `HR` chỉ thao tác được `Application` có `assigned_hr_id` trùng chính mình, xác nhận qua nhiều hàm trong `app/services/`, `app/routers/offers.py::_check_can_view_offer`). Đây là **Row-Level Security** kết hợp RBAC, không chỉ RBAC thuần túy ở mức chức năng.

## 7. State Machine (Máy trạng thái hữu hạn)

**Khái niệm**: mô hình gồm tập hữu hạn trạng thái (state) và các phép chuyển (transition) hợp lệ giữa chúng; một đối tượng tại một thời điểm chỉ ở đúng 1 trạng thái, chỉ được chuyển sang trạng thái khác qua các cạnh (edge) đã định nghĩa trước.

**Mục đích**: đảm bảo tính toàn vẹn nghiệp vụ — ngăn đối tượng rơi vào trạng thái/chuyển đổi vô nghĩa.

**Cách project áp dụng — `[CONFIRMED]`**: cả 2 entity trung tâm đều có state machine tường minh trong code:
- `Application.status` (10 giá trị enum `ApplicationStatus`) — cạnh hợp lệ định nghĩa tại `app/services/application_service.py::FORWARD_EDGES` (dict) + `PIPELINE_ORDER` (list, dùng xác định chiều lùi). Mọi request đổi trạng thái đều được validate qua hàm `update_status()` trước khi ghi CSDL — không tin tưởng client.
- `Offer.status` (7 giá trị enum `OfferStatus`) — cạnh hợp lệ được validate rải rác trong từng hàm của `app/services/offer_service.py` (`submit_offer`, `approve_offer`...), mỗi hàm kiểm tra `offer.status` hiện tại trước khi cho phép chuyển.

## 8. Idempotency trong thiết kế API

**Khái niệm**: một API là idempotent nếu gọi nhiều lần với cùng tham số cho kết quả như gọi 1 lần (không tạo thêm bản ghi/side-effect trùng lặp).

**Mục đích**: chống lỗi do double-submit (VD người dùng bấm nút 2 lần, mất kết nối rồi client tự động thử lại).

**Cách project áp dụng — `[CONFIRMED]`**: `POST /applications` hỗ trợ header `Idempotency-Key`; nếu trùng `(candidate_id, idempotency_key)` với 1 request trước đó (ràng buộc UNIQUE `uq_application_candidate_idem` trên bảng `applications`), hệ thống trả về bản ghi đã tồn tại thay vì tạo mới — `app/services/application_service.py::apply_for_job`.

## 9. Graceful Degradation (chế độ dự phòng khi dịch vụ ngoài không khả dụng)

**Khái niệm**: nguyên lý thiết kế cho phép hệ thống tiếp tục hoạt động (ở mức giảm tính năng) khi một thành phần phụ thuộc bên ngoài gặp sự cố hoặc chưa được cấu hình, thay vì toàn bộ hệ thống ngừng hoạt động.

**Cách project áp dụng — `[CONFIRMED]`**: 2 tích hợp bên ngoài đều có cơ chế fallback nội bộ:
- `app/services/ai_service.py` — nếu không có `AI_API_KEY` hoặc gọi AI Provider (Gemini/Claude, chọn qua `AI_PROVIDER`) thất bại (kể cả sau 1 lần retry), tự động chuyển sang **chế độ STUB** (so khớp từ khóa nội bộ, không phụ thuộc mạng).
- `app/services/email_service.py` — nếu không có `SMTP_USER`/`SMTP_PASSWORD`, tự động chuyển sang **chế độ SIMULATE** (chỉ ghi `audit_logs`, không gửi thật).

## 10. UML (Unified Modeling Language)

**Khái niệm**: bộ ký hiệu chuẩn hóa để mô hình hóa hệ thống hướng đối tượng, gồm nhiều loại diagram (Use Case, Class, Sequence, Activity...) biểu diễn các góc nhìn khác nhau (cấu trúc tĩnh, hành vi động).

**Vai trò trong project**: dùng ở `11_USE_CASE.md`, `12_USE_CASE_SPECIFICATION.md`, `15_UML.md` (Đợt 4-5) để mô hình hóa hệ thống dựa trên source code thực tế đã khảo sát.

## 11. BPMN (Business Process Model and Notation)

**Khái niệm**: ký hiệu chuẩn mô hình hóa tiến trình nghiệp vụ, gồm Pool (tổ chức/hệ thống), Lane (vai trò/actor), Task, Gateway (điểm rẽ nhánh), Event.

**Vai trò trong project**: dùng ở `10_BPMN.md` (Đợt 3) mô hình hóa các tiến trình chính (Apply → Screening → Offer → Hired).

## 12. Data Transfer Object (DTO) qua Pydantic Schema

**Khái niệm**: đối tượng trung gian dùng để truyền dữ liệu giữa các lớp/qua network, tách biệt khỏi entity nội bộ — cho phép validate/định hình dữ liệu vào-ra độc lập với cấu trúc CSDL.

**Cách project áp dụng — `[CONFIRMED]`**: `app/schemas/*.py` định nghĩa các class kế thừa Pydantic `BaseModel` (VD `ApplicationOut`, `OfferCreateRequest`) — tách biệt hoàn toàn khỏi SQLAlchemy model. Ví dụ cụ thể cho thấy DTO **không phản chiếu 1-1 entity**: `ApplicationOut` gộp field từ 3 bảng khác nhau (`applications`, `candidates`, `jobs`, và gián tiếp `ai_analyses`/`resumes`) thành 1 response phẳng — `app/routers/applications.py::_to_out()`.

---

*Tài liệu tiếp theo: `03_PHUONG_PHAP_KHAO_SAT.md`.*
