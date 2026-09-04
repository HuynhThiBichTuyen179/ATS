# 19 — TRACEABILITY MATRIX — ATS v2

> **REFRESH 2026-08-18** (ngoài phạm vi 23-file gốc). `06_SRS.md`/`05_BRD.md`/`11_USE_CASE.md`/`12_USE_CASE_SPECIFICATION.md` **không** nằm trong phạm vi đợt refresh này (chỉ 07/08/16/19 theo xác nhận người dùng) — nên **không tạo `FR-XXX`/`UC-XXX` mới** cho các endpoint mới (đúng RULE 1/RULE 6: không bịa ID). Toàn bộ 74 `FR-XXX` gốc bên dưới **giữ nguyên không đổi**. Mục mới (## Endpoint mới chưa có FR/UC) liệt kê riêng 26 Function mới từ `08` chưa có ID chính thức.

**Mục đích**: hợp nhất toàn bộ chuỗi `BR → FR → UC → API Endpoint → Entity/Table → Source Code` cho cả 74 `FR-XXX` đã định danh ở `06_SRS.md`, đối chiếu chéo với `05` (BR), `11`/`12` (UC), `08` (Function/Endpoint), `16` (Entity). Đây là tài liệu tổng hợp cuối — không tạo ID mới, chỉ liên kết ID đã có (đúng RULE 6).

## MOD-AUTH

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-AUTH-001 | BR-007 | UC-AUTH-001 | `POST /auth/register` | `users` | `routers/auth.py::register` → `services/auth_service.py::register_candidate` |
| FR-AUTH-002 | BR-007 | UC-AUTH-001 | `POST /auth/register` | `users` | `schemas/auth.py::password_must_have_letter_and_digit` |
| FR-AUTH-003 | BR-007 | UC-AUTH-002 | `POST /auth/login` | `users` | `routers/auth.py::login` → `auth_service.py::authenticate/issue_tokens` |
| FR-AUTH-004 | BR-007 | UC-AUTH-002 | `POST /auth/login` | `users` | `core/config.py::jwt_access_token_hours` |
| FR-AUTH-005 | BR-007 | UC-AUTH-002, UC-AUTH-003 | `POST /auth/login`, `POST /auth/refresh` | `users` | `core/security.py::generate_refresh_token` |
| FR-AUTH-006 | BR-007 | UC-AUTH-003 | `POST /auth/refresh` | `users` | `routers/auth.py::refresh` → `auth_service.py::refresh_access_token` |
| FR-AUTH-007 | BR-007 | UC-AUTH-004 | `GET /auth/me` | `users` | `routers/auth.py::me` |
| FR-AUTH-008 | BR-007 | UC-AUTH-002 | `POST /auth/login` | `users` | `auth_service.py::authenticate` |

## MOD-USER

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-USER-001 | BR-007 | UC-USER-001 | `POST /users` | `users` | `routers/users.py::create_user` (`_ROLES_ADMIN_CAN_CREATE`) |
| FR-USER-002 | BR-007 | UC-USER-001 | `POST /users` | `users` | `create_user` (`_ROLES_HR_MANAGER_CAN_CREATE`) |
| FR-USER-003 | BR-007 | UC-USER-001 | `POST /users` | `users` | `require_hr_manager_or_admin` (chặn HR) |
| FR-USER-004 | BR-007 | UC-USER-002 | `GET /users` | `users` | `routers/users.py::list_users` |

## MOD-DEPT

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-DEPT-001 | BR-001 | UC-DEPT-001 | `POST /departments` | `departments` | `routers/departments.py::create_department` |
| FR-DEPT-002 | BR-001 | UC-DEPT-002 | `GET /departments` | `departments` | `routers/departments.py::list_departments` |

## MOD-JOB

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-JOB-001 | BR-001 | UC-JOB-001 | `POST /jobs` | `jobs`, `departments` | `routers/jobs.py::create_job` |
| FR-JOB-002 | BR-001 | UC-JOB-002 | `POST /jobs/{id}/assign-hr` | `jobs`, `users` | `routers/jobs.py::assign_hr` |
| FR-JOB-003 | BR-001 | UC-JOB-003 | `POST /jobs/{id}/publish` | `jobs` | `routers/jobs.py::publish_job` |
| FR-JOB-004 | BR-001 | UC-JOB-004, UC-JOB-005 | `GET /jobs`, `GET /jobs/{id}` | `jobs` | `routers/jobs.py::list_jobs/get_job` |
| FR-JOB-005 | BR-001 | UC-JOB-004 | `GET /jobs` | `jobs` | `routers/jobs.py::list_jobs` |
| FR-JOB-006 | BR-003 | *(ACT-SYSTEM, không UC người dùng)* | — | `jobs`, `applications` | `services/offer_service.py::_close_job_if_quota_reached` |

## MOD-APP

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-APP-001 | BR-001 | UC-APP-001 | `POST /applications` | `applications` | `routers/applications.py::apply` |
| FR-APP-002 | BR-001, BR-004 | UC-APP-001 | `POST /applications` | `applications` | `apply` (kiểm tra `ai_consent`) |
| FR-APP-003 | BR-001 | UC-APP-001 | `POST /applications` | `applications` | `services/application_service.py::apply_for_job` (Idempotency-Key) |
| FR-APP-004 | BR-003 | UC-APP-001 | `POST /applications` | `applications` | `apply_for_job` (không check cooldown) |
| FR-APP-005 | BR-001 | UC-APP-001 | `POST /applications` | `applications` | `apply_for_job` (luôn INSERT) |
| FR-APP-006 | BR-001 | UC-APP-001 | `POST /applications` | `resumes` | `apply_for_job` (lưu `resume_text`) |
| FR-APP-007 | BR-001 | UC-APP-004 | `POST /applications/{id}/resume` | `resumes` | `routers/applications.py::upload_resume` → `services/resume_service.py` |
| FR-APP-008 | BR-007 | UC-APP-004 | `POST /applications/{id}/resume` | `resumes` | `services/resume_parser.py::save_and_extract` |
| FR-APP-009 | BR-001 | UC-APP-004 | `POST /applications/{id}/resume` | `applications` | `resume_service.py::upload_resume_file` |
| FR-APP-010 | BR-001 | UC-APP-005 | `PUT /applications/{id}/status` | `applications` | `application_service.py::update_status` (`FORWARD_EDGES`) |
| FR-APP-011 | BR-001 | UC-APP-005 | `PUT /applications/{id}/status` | `applications` | `update_status` (forward, role HR+) |
| FR-APP-012 | BR-001, BR-008 | UC-APP-005 | `PUT /applications/{id}/status` | `applications`, `audit_logs` | `update_status` (backward, `STATUS_REVERTED`) |
| FR-APP-013 | BR-001 | UC-APP-006 | `PUT /applications/{id}/withdraw` | `applications` | `application_service.py::withdraw` |
| FR-APP-014 | BR-001 | UC-APP-007 | `PUT /applications/{id}/archive` | `applications` | `application_service.py::archive` |
| FR-APP-015 | BR-007 | UC-APP-002, UC-APP-003 | `GET /applications`, `GET /applications/{id}` | `applications` | `list_applications`/`get_application` |
| FR-APP-016 | BR-007 | UC-APP-001 *(hệ quả)* | `POST /applications` | `applications` | `apply_for_job(assigned_hr_id=job.assigned_hr_id)` |
| FR-APP-017 | BR-001 | UC-APP-002 | `GET /applications` | `applications`, `candidates` | `list_applications` |
| FR-APP-018 | BR-008 | *(phủ định — không endpoint)* | — | `applications` | Không có route `DELETE /applications/{id}` |
| FR-APP-019 | BR-001 | UC-APP-001 | `POST /applications` | `candidates` | `_get_or_create_candidate` |

## MOD-OFFER

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-OFFER-001 | BR-002 | UC-OFFER-002 | `POST /offers` | `offers` | `services/offer_service.py::create_offer` |
| FR-OFFER-002 | BR-002 | UC-OFFER-003 | `POST /offers/{id}/submit` | `offers` | `submit_offer` |
| FR-OFFER-003 | BR-002 | UC-OFFER-004 | `POST /offers/{id}/approve` | `offers` | `approve_offer` + CheckConstraint `ck_offer_approver_not_creator` |
| FR-OFFER-004 | BR-002 | UC-OFFER-004 | `POST /offers/{id}/approve` | `offers` | `require_offer_approver` |
| FR-OFFER-005 | BR-002 | UC-OFFER-005 | `POST /offers/{id}/reject` | `offers` | `reject_offer` |
| FR-OFFER-006 | BR-002 | UC-OFFER-006 | `POST /offers/{id}/send` | `offers`, `applications` | `send_offer` |
| FR-OFFER-007 | BR-002 | UC-OFFER-006 | `POST /offers/{id}/send` | `offers` | `send_offer` (`settings.offer_validity_days`) |
| FR-OFFER-008 | BR-002 | UC-OFFER-007 | `POST /offers/{id}/respond` | `offers` | `respond_offer` |
| FR-OFFER-009 | BR-002, BR-003 | UC-OFFER-007 | `POST /offers/{id}/respond` | `offers`, `applications`, `jobs` | `respond_offer` → `_close_job_if_quota_reached` |
| FR-OFFER-010 | BR-002 | UC-OFFER-007 | `POST /offers/{id}/respond` | `offers`, `applications` | `respond_offer` |
| FR-OFFER-011 | BR-002 | *(không UC — không actor kích hoạt được)* | — | `offers`, `applications` | `expire_due_offers` (tồn tại, không được gọi — xem `20`) |
| FR-OFFER-012 | BR-007 | UC-OFFER-001, UC-OFFER-008 | `GET /offers`, `GET /offers/{id}` | `offers` | `list_offers`/`get_offer` + `_check_can_view_offer` |

## MOD-EMAIL

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-EMAIL-001 | BR-005 | UC-EMAIL-001, UC-EMAIL-002, UC-EMAIL-003 | `POST/GET/PUT /email-templates` | `email_templates` | `routers/email_templates.py` |
| FR-EMAIL-002 | BR-005 | UC-EMAIL-004 | `POST /email-templates/{id}/deactivate` | `email_templates` | `deactivate_template` |
| FR-EMAIL-003 | BR-005 | UC-EMAIL-001 | `POST /email-templates` | `email_templates` | `create_template` |
| FR-EMAIL-004 | BR-005 | UC-EMAIL-005 | `POST /email-templates/send/{id}` | `email_templates` | `services/email_service.py::render_template` |
| FR-EMAIL-005 | BR-005 | UC-EMAIL-005 | `POST /email-templates/send/{id}` | `applications` | `send_manual_email` |
| FR-EMAIL-006 | BR-005 | *(nhúng trong UC-APP-001/005, UC-OFFER-006/007)* | — | `applications`, `offers` | `application_service.py`, `offer_service.py` (6 điểm gọi `trigger_stage_email`) |
| FR-EMAIL-007 | BR-005 | *(hệ thống)* | — | `email_templates` | `email_service.py::trigger_stage_email` |
| FR-EMAIL-008 | BR-005 | *(hệ thống)* | — | — | `email_service.py::_is_smtp_configured/send_raw_email` |
| FR-EMAIL-009 | BR-008 | *(hệ thống)* | — | `audit_logs` | `email_service.py::send_email` |

## MOD-AI

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-AI-001 | BR-004 | UC-AI-001 | `POST /ai/analyze/{id}` | `ai_analyses` | `services/ai_service.py::run_screening` |
| FR-AI-002 | BR-007 | UC-AI-001 | `POST /ai/analyze/{id}` | `applications` | `ai.py::_check_scope` |
| FR-AI-003 | BR-004 | UC-AI-001 | `POST /ai/analyze/{id}` | — | `ai.py::analyze` (`202`) |
| FR-AI-004 | BR-004 | UC-AI-001 | `POST /ai/analyze/{id}` | — | `ai_service.py::_call_gemini/_stub_analysis` |
| FR-AI-005 | BR-008 | UC-AI-001, UC-AI-002 | `POST /ai/analyze/{id}`, `GET /ai/analysis/{id}` | `ai_analyses` | `run_screening` (`is_latest`) |
| FR-AI-006 | BR-004 | UC-AI-001 | `POST /ai/analyze/{id}` | `applications` | `run_screening` (chỉ set `SCREENING`) |
| FR-AI-007 | BR-007 | *(phủ định — không endpoint mở cho CANDIDATE)* | — | — | `require_hr_or_above` trên cả 2 route AI |

## MOD-DASH

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-DASH-001 | BR-006 | UC-DASH-001 | `GET /dashboard/summary` | `applications`, `jobs`, `offers` | `routers/dashboard.py::get_summary` |
| FR-DASH-002 | BR-006 | UC-DASH-001 | `GET /dashboard/summary` | `applications`, `users` | `get_summary` (`hr_performance`) |
| FR-DASH-003 | BR-007 | UC-DASH-001 | `GET /dashboard/summary` | `applications` | `get_summary` (filter `assigned_hr_id`) |
| FR-DASH-004 | BR-007 | *(phủ định)* | — | — | `require_hr_or_above` |

## MOD-AUDIT

| FR | BR | UC | Endpoint | Entity | Source |
|---|---|---|---|---|---|
| FR-AUDIT-001 | BR-008 | *(hệ thống, xuyên suốt)* | — | `audit_logs` | `services/audit_service.py::log` (gọi từ nhiều service) |
| FR-AUDIT-002 | BR-008 | UC-AUDIT-001 | `GET /audit` | `audit_logs` | `routers/audit.py::list_audit_logs` |
| FR-AUDIT-003 | BR-008 | UC-AUDIT-001 | `GET /audit` | — | `require_hr_manager_or_admin` |

## Endpoint mới chưa có FR/UC chính thức (bổ sung 2026-08-18)

`[CONFIRMED — hạn chế đã biết]`: 26 Function mới ở `08_FUNCTIONAL_SPECIFICATION.md` (module `FN-CANDIDATE`, `FN-SOURCE`, `FN-INTERVIEW`, `FN-RESUME` hoàn toàn mới + phần mở rộng của `FN-AUTH`/`FN-USER`/`FN-DEPT`/`FN-APP`/`FN-EMAIL`) **chưa có `FR-XXX`/`UC-XXX`** vì `06_SRS.md`/`11_USE_CASE.md` không thuộc phạm vi đợt refresh này. Liệt kê endpoint ↔ entity ↔ source (đủ 3 cột cuối của chuỗi truy vết, thiếu 2 cột đầu `BR`/`UC`):

| Endpoint | Entity | Source |
|---|---|---|
| `POST /auth/forgot-password`, `POST /auth/reset-password` | `password_reset_tokens`, `users` | `routers/auth.py`, `services/password_reset_service.py` |
| `GET/PUT/DELETE /users/{id}` | `users` | `routers/users.py` |
| `PUT/DELETE /departments/{id}` | `departments` | `routers/departments.py` |
| `GET /applications/{id}/resume`, `PUT /applications/{id}` | `applications`, `resumes`, `candidate_sources` | `routers/applications.py` |
| `POST/GET/GET{id}/PUT/DELETE /candidates` | `candidates`, `applications` | `routers/candidates.py`, `services/candidate_service.py` |
| `POST/GET/PUT/DELETE /candidate-sources` | `candidate_sources` | `routers/candidate_sources.py` |
| `POST/GET/GET "/me"/GET{id}/PUT/DELETE /interviews` | `interviews`, `applications` | `routers/interview.py`, `services/interview_service.py` |
| `GET /resumes/{id}/download` | `resumes` | `routers/resumes.py` |
| `GET /email-templates/{id}` | `email_templates` | `routers/email_templates.py` |

Nếu người dùng muốn chuỗi truy vết đầy đủ (gán `FR-XXX`/`UC-XXX` chính thức, viết Use Case Spec chi tiết), cần yêu cầu riêng 1 đợt cập nhật `05`/`06`/`11`/`12`.

---

## Kiểm tra độ phủ (Coverage Check)

`[CONFIRMED]`, cập nhật 2026-08-18 — số liệu cho phần **74 `FR-XXX` gốc** không đổi (nguồn `05`/`06`/`11` chưa refresh); số liệu cho **endpoint/bảng thực tế** cập nhật theo `07`/`08`/`16` mới:

- **9/9 `BR-XXX`** (05, chưa refresh) đều có ít nhất 1 `FR-XXX` trỏ tới — không đổi.
- **74/74 `FR-XXX`** (06, chưa refresh) đều xuất hiện trong bảng trên, có `BR-XXX` nguồn — không đổi.
- **37/37 `UC-XXX`** (11/12, chưa refresh) đều xuất hiện — không đổi. Cùng 9 FR phủ định/hệ thống như bản gốc.
- **37/63 endpoint** (08, đã refresh — tăng từ 37 lên 63) có `FR-XXX` chính thức; **26/63 endpoint mới chưa có FR/UC** — xem mục ngay trên. Đây là thay đổi số liệu duy nhất so với bản gốc, phát sinh vì `08` được refresh nhưng `06`/`11` thì chưa (lựa chọn phạm vi có chủ đích của người dùng, không phải sai sót).
- **12/14 bảng** (16, đã refresh — tăng từ 12 lên 14) được tham chiếu bởi ít nhất 1 FR gốc. `id_sequences` vẫn không có FR (bảng kỹ thuật thuần túy, đúng thiết kế). **`interviews` nay ĐÃ có Function/endpoint thật** (`FN-INTERVIEW`, 6 endpoint, đóng Gap APP-20) nhưng **vẫn chưa có `FR-XXX` chính thức** vì `06` chưa refresh — khác bản gốc (lúc đó `interviews` không có FR **vì** không có endpoint; nay không có FR **dù đã có** endpoint, thuần túy do giới hạn phạm vi tài liệu). `candidate_sources`/`password_reset_tokens` (2 bảng mới) cũng cùng tình trạng — có endpoint thật, chưa có FR chính thức.

---

*Tài liệu tiếp theo: `20_GAP_ANALYSIS.md`.*
