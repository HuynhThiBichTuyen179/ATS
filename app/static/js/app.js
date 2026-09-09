/* ==========================================================================
   ATS — Frontend Application Logic & API Client
   ========================================================================== */

const API_BASE = ""; // Relative to same origin (e.g. http://127.0.0.1:8000)

// Seed Accounts for Quick Role Switcher
const SEED_ACCOUNTS = {
  "candidate": { email: "candidate@example.com", password: "Candidate@123", role: "CANDIDATE", name: "Candidate User" },
  "admin": { email: "admin@example.com", password: "Admin@123", role: "ADMIN", name: "System Admin (BGD)" },
  "hrm_a": { email: "hrmanager.a@example.com", password: "HrManager@123", role: "HR_MANAGER", name: "HR Manager A" },
  "hrm_b": { email: "hrmanager.b@example.com", password: "HrManager@123", role: "HR_MANAGER", name: "HR Manager B" },
  "hr_a": { email: "hr.a@example.com", password: "Hr@123456", role: "HR", name: "HR Staff A" }
};

// Global App State
const state = {
  userKey: "hrm_a", // Default active seed account
  token: null,
  currentUser: null,
  activeView: "jobs-view",
  jobs: [],
  applications: [],
  offers: {},
  departments: [],
  auditLogs: []
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  switchRole(state.userKey);
});

function initEventListeners() {
  // Navigation Tabs
  document.querySelectorAll(".nav-btn[data-view]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const viewId = e.currentTarget.getAttribute("data-view");
      switchView(viewId);
    });
  });

  // Quick Role Switcher
  const roleSelect = document.getElementById("role-select");
  if (roleSelect) {
    roleSelect.addEventListener("change", (e) => {
      switchRole(e.target.value);
    });
  }

  // Theme Toggle
  const themeBtn = document.getElementById("btn-theme");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      themeBtn.innerHTML = next === "dark" ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
    });
  }
}

// ==========================================================================
// Authentication & Role Switching
// ==========================================================================
async function switchRole(accountKey) {
  state.userKey = accountKey;
  const account = SEED_ACCOUNTS[accountKey];
  
  if (!account) return;

  try {
    // Attempt Login to get Access Token
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: account.email, password: account.password })
    });

    if (!res.ok) {
      // If candidate account doesn't exist yet, attempt registration
      if (account.role === "CANDIDATE") {
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: account.name,
            email: account.email,
            password: account.password,
            phone: "0901234567"
          })
        });
        if (regRes.ok) {
          const data = await regRes.json();
          state.token = data.access_token;
        }
      }
    } else {
      const data = await res.json();
      state.token = data.access_token;
    }

    // Fetch /auth/me info
    if (state.token) {
      const meRes = await apiFetch("/auth/me");
      if (meRes.ok) {
        state.currentUser = await meRes.json();
        showToast(`Đã chuyển sang tài khoản: <b>${state.currentUser.full_name}</b> (${state.currentUser.role})`, "info");
        updateUserUI();
        refreshCurrentView();
      }
    }
  } catch (err) {
    console.error("Auth error:", err);
    showToast("Lỗi đăng nhập tài khoản seed: " + err.message, "danger");
  }
}

function updateUserUI() {
  const badge = document.getElementById("user-role-badge");
  if (badge && state.currentUser) {
    badge.textContent = `${state.currentUser.business_id} — ${state.currentUser.role}`;
  }
}

// Helper API Fetch with JWT Authorization
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }
  if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  options.headers = headers;
  return fetch(`${API_BASE}${endpoint}`, options);
}

// ==========================================================================
// View Routing
// ==========================================================================
function switchView(viewId) {
  state.activeView = viewId;
  
  // Highlight active nav tab
  document.querySelectorAll(".nav-btn[data-view]").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewId);
  });

  // Toggle view sections
  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.toggle("active", sec.id === viewId);
  });

  refreshCurrentView();
}

function refreshCurrentView() {
  if (state.activeView === "jobs-view") {
    loadJobs();
  } else if (state.activeView === "my-applications-view") {
    loadCandidateApplications();
  } else if (state.activeView === "dashboard-view") {
    loadDashboardData();
  } else if (state.activeView === "audit-view") {
    loadAuditLogs();
  }
}

// ==========================================================================
// Candidate View: Public Job Board & Application
// ==========================================================================
async function loadJobs() {
  const grid = document.getElementById("jobs-grid");
  if (!grid) return;
  grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin fa-2x"></i></div>`;

  try {
    const res = await apiFetch("/jobs");
    if (!res.ok) throw new Error("Không thể tải danh sách việc làm");
    state.jobs = await res.json();

    if (state.jobs.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">Chưa có tin tuyển dụng nào phát hành.</div>`;
      return;
    }

    grid.innerHTML = state.jobs.map(job => `
      <div class="job-card">
        <div>
          <div class="job-card-header">
            <div>
              <h3 class="job-title">${escapeHtml(job.title)}</h3>
              <span class="job-id-badge">${job.business_id}</span>
            </div>
            <span class="tag" style="background: rgba(16,185,129,0.15); color: #10b981; font-weight:700;">${job.status}</span>
          </div>
          <div class="job-tags">
            <span class="tag"><i class="fas fa-map-marker-alt"></i> ${escapeHtml(job.location || 'Toàn quốc')}</span>
            <span class="tag"><i class="fas fa-building"></i> ${escapeHtml(job.department_business_id)}</span>
          </div>
        </div>
        <div class="job-card-footer">
          <button class="btn btn-secondary" onclick="viewJobDetail('${job.business_id}')">
            <i class="fas fa-info-circle"></i> Chi tiết
          </button>
          <button class="btn" onclick="openApplyModal('${job.business_id}', '${escapeHtml(job.title)}')">
            <i class="fas fa-paper-plane"></i> Ứng tuyển ngay
          </button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<div style="grid-column: 1/-1; color: var(--status-rejected);">Lỗi: ${err.message}</div>`;
  }
}

function openApplyModal(jobBusinessId, jobTitle) {
  if (!state.currentUser || state.currentUser.role !== "CANDIDATE") {
    showToast("Vui lòng chuyển sang tài khoản Candidate để nộp hồ sơ!", "warning");
    return;
  }

  const modal = document.getElementById("apply-modal");
  document.getElementById("apply-job-id").value = jobBusinessId;
  document.getElementById("apply-job-title").textContent = jobTitle;
  document.getElementById("apply-name").value = state.currentUser.full_name || "";
  document.getElementById("apply-email").value = state.currentUser.email || "";
  
  // Auto-generate unique Idempotency Key
  const idempotencyKey = "IK-" + Date.now() + "-" + Math.random().toString(36).substring(2, 7);
  document.getElementById("apply-idempotency-key").value = idempotencyKey;

  modal.classList.add("active");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

async function submitApplication(e) {
  e.preventDefault();
  const jobBusinessId = document.getElementById("apply-job-id").value;
  const fullName = document.getElementById("apply-name").value;
  const email = document.getElementById("apply-email").value;
  const phone = document.getElementById("apply-phone").value;
  const source = document.getElementById("apply-source").value;
  const aiConsent = document.getElementById("apply-ai-consent").checked;
  const idempotencyKey = document.getElementById("apply-idempotency-key").value;

  if (!aiConsent) {
    showToast("Bạn cần đồng ý điều khoản xử lý hồ sơ tự động để nộp bài!", "warning");
    return;
  }

  try {
    const res = await apiFetch("/applications", {
      method: "POST",
      headers: {
        "Idempotency-Key": idempotencyKey
      },
      body: JSON.stringify({
        job_business_id: jobBusinessId,
        candidate_full_name: fullName,
        candidate_email: email,
        candidate_phone: phone,
        source: source,
        ai_consent: aiConsent
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Nộp ứng tuyển thất bại");
    }

    const appData = await res.json();
    closeModal("apply-modal");

    if (appData.is_new) {
      showToast(`🎉 Nộp hồ sơ thành công! Mã hồ sơ: <b>${appData.business_id}</b>`, "success");
    } else {
      showToast(`⚠️ Request lặp (Idempotency Active): Trả về hồ sơ cũ <b>${appData.business_id}</b>`, "info");
    }

    switchView("my-applications-view");
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

// ==========================================================================
// Candidate View: My Applications & Offers
// ==========================================================================
async function loadCandidateApplications() {
  const container = document.getElementById("my-apps-list");
  if (!container) return;
  container.innerHTML = `<div style="text-align:center; padding: 2rem;"><i class="fas fa-spinner fa-spin fa-2x"></i></div>`;

  try {
    // Candidates view their applications by listing jobs/apps
    const res = await apiFetch("/applications");
    if (!res.ok) {
      container.innerHTML = `<div style="color: var(--text-muted); text-align:center;">Vui lòng chọn vai trò HR hoặc đăng nhập Candidate để xem danh sách.</div>`;
      return;
    }
    const apps = await res.json();

    if (apps.length === 0) {
      container.innerHTML = `<div style="text-align:center; color: var(--text-muted); padding: 3rem;">Bạn chưa nộp hồ sơ ứng tuyển nào.</div>`;
      return;
    }

    container.innerHTML = apps.map(app => `
      <div class="job-card" style="margin-bottom: 1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h4 style="margin-bottom: 0.25rem;">Hồ sơ: <span style="color:var(--primary);">${app.business_id}</span></h4>
            <div style="font-size: 0.85rem; color: var(--text-muted);">Mã Job: ${app.job_business_id}</div>
          </div>
          <span class="tag" style="font-weight:700; background:rgba(99,102,241,0.2); color:var(--primary);">${app.status}</span>
        </div>
        <div style="margin-top: 1rem; display:flex; gap: 0.5rem;">
          ${app.status !== 'WITHDRAWN' && app.status !== 'REJECTED' ? `
            <button class="btn btn-secondary" onclick="withdrawApplication('${app.business_id}')">
              <i class="fas fa-times-circle"></i> Rút hồ sơ
            </button>
          ` : ''}
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--status-rejected);">Lỗi: ${err.message}</div>`;
  }
}

async function withdrawApplication(appBusinessId) {
  if (!confirm("Bạn có chắc chắn muốn rút hồ sơ này không?")) return;
  try {
    const res = await apiFetch(`/applications/${appBusinessId}/withdraw`, { method: "PUT" });
    if (!res.ok) throw new Error("Không thể rút hồ sơ");
    showToast("Đã rút hồ sơ thành công", "success");
    loadCandidateApplications();
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

// ==========================================================================
// HR & Admin Dashboard & Kanban Pipeline
// ==========================================================================
async function loadDashboardData() {
  if (!state.currentUser || state.currentUser.role === "CANDIDATE") {
    document.getElementById("kanban-board").innerHTML = `
      <div style="width:100%; text-align:center; padding: 4rem; color: var(--text-muted);">
        <h3><i class="fas fa-lock" style="font-size:2rem; margin-bottom: 1rem; color:var(--status-pending);"></i></h3>
        Yêu cầu quyền HR Staff, HR Manager hoặc Admin để truy cập Dashboard Quản lý Tuyển dụng.
      </div>`;
    return;
  }

  try {
    const [jobsRes, appsRes] = await Promise.all([
      apiFetch("/jobs"),
      apiFetch("/applications")
    ]);

    const jobs = jobsRes.ok ? await jobsRes.json() : [];
    const apps = appsRes.ok ? await appsRes.json() : [];

    // Update Stats Bar
    document.getElementById("stat-jobs-count").textContent = jobs.length;
    document.getElementById("stat-apps-count").textContent = apps.length;

    renderKanbanBoard(apps);
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function renderKanbanBoard(apps) {
  const board = document.getElementById("kanban-board");
  if (!board) return;

  const columns = [
    { id: "APPLIED", title: "APPLIED (Mới Nộp)", color: "#3b82f6" },
    { id: "SCREENING", title: "SCREENING (Vòng Sơ Loại)", color: "#8b5cf6" },
    { id: "INTERVIEWING", title: "INTERVIEWING (Phỏng Vấn)", color: "#06b6d4" },
    { id: "OFFER_PENDING", title: "OFFER PENDING (Chờ Duyệt)", color: "#f59e0b" },
    { id: "OFFER_APPROVED", title: "OFFER APPROVED (Đã Duyệt)", color: "#10b981" },
    { id: "OFFER_SENT", title: "OFFER SENT (Đã Gửi UV)", color: "#ec4899" },
    { id: "HIRED", title: "HIRED (Đã Tuyển)", color: "#10b981" },
    { id: "REJECTED", title: "REJECTED (Từ Chối)", color: "#ef4444" }
  ];

  board.innerHTML = columns.map(col => {
    const colApps = apps.filter(a => a.status === col.id);
    return `
      <div class="kanban-column">
        <div class="kanban-column-header" style="border-top: 3px solid ${col.color}">
          <span>${col.title}</span>
          <span class="column-count">${colApps.length}</span>
        </div>
        <div class="kanban-cards-wrapper">
          ${colApps.map(app => `
            <div class="kanban-card" onclick="openApplicationDetailModal('${app.business_id}')">
              <div style="font-weight:700; color:var(--text-main);">${app.business_id}</div>
              <div style="font-size:0.78rem; color:var(--text-muted); margin-top:4px;">
                Job: <span style="color:var(--primary);">${app.job_business_id}</span>
              </div>
              <div style="font-size:0.75rem; color:var(--text-dim); margin-top:4px;">
                UV: ${app.candidate_business_id}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }).join("");
}

// Application & Offer Approval Modal (4-Eyes Approval)
async function openApplicationDetailModal(appBusinessId) {
  const modal = document.getElementById("app-detail-modal");
  document.getElementById("modal-app-id").textContent = appBusinessId;

  try {
    const res = await apiFetch(`/applications/${appBusinessId}`);
    if (!res.ok) throw new Error("Không thể tải thông tin hồ sơ");
    const app = await res.json();

    const body = document.getElementById("app-detail-body");
    
    // Check if an offer exists or create offer action
    body.innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <div class="form-group">
          <label class="form-label">Mã Job Tuyển Dụng</label>
          <input type="text" class="form-control" value="${app.job_business_id}" readonly />
        </div>
        <div class="form-group">
          <label class="form-label">Trạng thái Hồ sơ hiện tại</label>
          <select class="form-control" id="change-app-status">
            <option value="APPLIED" ${app.status === 'APPLIED' ? 'selected' : ''}>APPLIED</option>
            <option value="SCREENING" ${app.status === 'SCREENING' ? 'selected' : ''}>SCREENING</option>
            <option value="INTERVIEWING" ${app.status === 'INTERVIEWING' ? 'selected' : ''}>INTERVIEWING</option>
            <option value="OFFER_PENDING" ${app.status === 'OFFER_PENDING' ? 'selected' : ''}>OFFER_PENDING</option>
            <option value="HIRED" ${app.status === 'HIRED' ? 'selected' : ''}>HIRED</option>
            <option value="REJECTED" ${app.status === 'REJECTED' ? 'selected' : ''}>REJECTED</option>
          </select>
        </div>
        <button class="btn btn-secondary" onclick="updateAppStatus('${app.business_id}')">
          <i class="fas fa-save"></i> Cập nhật trạng thái Hồ sơ
        </button>
      </div>

      <hr style="border-color: var(--border-color); margin: 1.5rem 0;" />

      <h4 style="margin-bottom: 1rem;"><i class="fas fa-file-signature" style="color:var(--primary);"></i> Quản Lý Offer (Phê Duyệt 4 Mắt)</h4>
      
      <div id="offer-management-section">
        <button class="btn" onclick="openCreateOfferForm('${app.business_id}')">
          <i class="fas fa-plus-circle"></i> Tạo Offer Mới cho Hồ sơ này
        </button>
      </div>
    `;

    modal.classList.add("active");
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

async function updateAppStatus(appBusinessId) {
  const newStatus = document.getElementById("change-app-status").value;
  try {
    const res = await apiFetch(`/applications/${appBusinessId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: newStatus, reason: "HR cập nhật từ giao diện Dashboard" })
    });
    if (!res.ok) throw new Error("Cập nhật thất bại");
    showToast("Cập nhật trạng thái hồ sơ thành công", "success");
    closeModal("app-detail-modal");
    loadDashboardData();
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

function openCreateOfferForm(appBusinessId) {
  const sec = document.getElementById("offer-management-section");
  sec.innerHTML = `
    <div style="background: rgba(0,0,0,0.2); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
      <div class="form-group">
        <label class="form-label">Mức lương chính thức (VND/Tháng)</label>
        <input type="number" id="offer-salary" class="form-control" value="25000000" />
      </div>
      <div class="form-group">
        <label class="form-label">Mức lương thử việc (VND/Tháng)</label>
        <input type="number" id="offer-probation" class="form-control" value="21500000" />
      </div>
      <div class="form-group">
        <label class="form-label">Ngày bắt đầu đi làm (YYYY-MM-DD)</label>
        <input type="date" id="offer-start-date" class="form-control" value="2026-09-01" />
      </div>
      <button class="btn btn-success" onclick="submitCreateOffer('${appBusinessId}')">
        <i class="fas fa-check"></i> Xác nhận Tạo Offer
      </button>
    </div>
  `;
}

async function submitCreateOffer(appBusinessId) {
  const salary = parseFloat(document.getElementById("offer-salary").value);
  const probation = parseFloat(document.getElementById("offer-probation").value);
  const startDate = document.getElementById("offer-start-date").value;

  try {
    const res = await apiFetch("/offers", {
      method: "POST",
      body: JSON.stringify({
        application_business_id: appBusinessId,
        salary: salary,
        probation_salary: probation,
        start_date: startDate
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Tạo Offer thất bại");
    }

    const offer = await res.json();
    showToast(`Đã tạo Offer <b>${offer.business_id}</b> (Trạng thái: DRAFT)`, "success");
    renderOfferDetailView(offer);
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

// 4-Eyes Offer Approval View Guard
function renderOfferDetailView(offer) {
  const sec = document.getElementById("offer-management-section");
  const isCreator = state.currentUser && state.currentUser.business_id === offer.creator_business_id;
  const isApproverRole = state.currentUser && ["HR_MANAGER", "ADMIN"].includes(state.currentUser.role);

  sec.innerHTML = `
    <div style="background: var(--bg-card); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem;">
        <h4>Offer ID: <span style="color:var(--primary);">${offer.business_id}</span></h4>
        <span class="tag" style="font-weight:700; background:rgba(245,158,11,0.2); color:#f59e0b;">${offer.status}</span>
      </div>

      <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom: 1rem;">
        <div>Người tạo (Creator): <b>${offer.creator_business_id}</b></div>
        <div>Người duyệt (Approver): <b>${offer.approver_business_id || 'Chưa duyệt'}</b></div>
        <div>Lương chính thức: <b>${offer.salary.toLocaleString()} VND</b></div>
      </div>

      <!-- Visual Guard Indicator -->
      ${offer.status === 'PENDING_APPROVAL' ? (
        isCreator ? `
          <div class="offer-guard-alert blocked">
            <i class="fas fa-lock fa-lg"></i>
            <div>
              <b>🔒 QUY TẮC 4 MẮT: BỊ KHÓA</b><br/>
              Bạn là <b>người tạo Offer này</b> (${offer.creator_business_id}). Hệ thống chặn không cho bạn tự duyệt Offer của chính mình!
            </div>
          </div>
        ` : (
          isApproverRole ? `
            <div class="offer-guard-alert allowed">
              <i class="fas fa-user-check fa-lg"></i>
              <div>
                <b>✅ CÓ QUYỀN PHÊ DUYỆT</b><br/>
                Bạn là Manager khác/Admin (${state.currentUser.business_id}). Bạn có thể tiến hành Duyệt hoặc Từ chối Offer này.
              </div>
            </div>
          ` : `
            <div class="offer-guard-alert blocked">
              <i class="fas fa-shield-alt fa-lg"></i>
              <div>Chỉ HR Manager khác hoặc Admin mới có quyền duyệt Offer. (Vai trò hiện tại: ${state.currentUser.role})</div>
            </div>
          `
        )
      ) : ''}

      <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin-top: 1rem;">
        ${offer.status === 'DRAFT' ? `
          <button class="btn" onclick="actionSubmitOffer('${offer.business_id}')">
            <i class="fas fa-paper-plane"></i> Trình Duyệt Offer (Submit)
          </button>
        ` : ''}

        ${offer.status === 'PENDING_APPROVAL' ? `
          <button class="btn btn-success" ${isCreator || !isApproverRole ? 'disabled' : ''} onclick="actionApproveOffer('${offer.business_id}')">
            <i class="fas fa-check-circle"></i> Approve (Phê Duyệt)
          </button>
          <button class="btn btn-danger" ${!isApproverRole ? 'disabled' : ''} onclick="actionRejectOffer('${offer.business_id}')">
            <i class="fas fa-times-circle"></i> Reject (Từ Chối)
          </button>
        ` : ''}

        ${offer.status === 'APPROVED' ? `
          <button class="btn btn-success" onclick="actionSendOffer('${offer.business_id}')">
            <i class="fas fa-envelope-open-text"></i> Gửi Offer Cho Ứng Viên (Send)
          </button>
        ` : ''}
      </div>
    </div>
  `;
}

async function actionSubmitOffer(offerId) {
  try {
    const res = await apiFetch(`/offers/${offerId}/submit`, { method: "POST" });
    if (!res.ok) throw new Error("Submit thất bại");
    const offer = await res.json();
    showToast("Đã trình duyệt Offer thành công", "success");
    renderOfferDetailView(offer);
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

async function actionApproveOffer(offerId) {
  try {
    const res = await apiFetch(`/offers/${offerId}/approve`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Approve thất bại");
    }
    const offer = await res.json();
    showToast("🎉 Đã duyệt Offer thành công!", "success");
    renderOfferDetailView(offer);
  } catch (err) {
    showToast("⛔ Lỗi: " + err.message, "danger");
  }
}

async function actionRejectOffer(offerId) {
  const reason = prompt("Nhập lý do từ chối Offer:");
  if (!reason) return;
  try {
    const res = await apiFetch(`/offers/${offerId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: reason })
    });
    if (!res.ok) throw new Error("Reject thất bại");
    const offer = await res.json();
    showToast("Đã từ chối Offer (chuyển về DRAFT)", "info");
    renderOfferDetailView(offer);
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

async function actionSendOffer(offerId) {
  try {
    const res = await apiFetch(`/offers/${offerId}/send`, { method: "POST" });
    if (!res.ok) throw new Error("Send thất bại");
    const offer = await res.json();
    showToast("Đã gửi Offer cho ứng viên", "success");
    renderOfferDetailView(offer);
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

// Create Job Modal
function openCreateJobModal() {
  if (!state.currentUser || !["HR_MANAGER", "ADMIN"].includes(state.currentUser.role)) {
    showToast("Chỉ HR Manager hoặc Admin mới có quyền tạo Requisition/Job mới!", "warning");
    return;
  }
  document.getElementById("create-job-modal").classList.add("active");
}

async function submitCreateJob(e) {
  e.preventDefault();
  const title = document.getElementById("job-title").value;
  const deptId = document.getElementById("job-dept-id").value;
  const salaryMin = parseFloat(document.getElementById("job-salary-min").value);
  const salaryMax = parseFloat(document.getElementById("job-salary-max").value);
  const location = document.getElementById("job-location").value;
  const description = document.getElementById("job-desc").value;

  try {
    const res = await apiFetch("/jobs", {
      method: "POST",
      body: JSON.stringify({
        title: title,
        department_business_id: deptId || "DEP0001",
        description: description,
        requirements: "Yêu cầu kinh nghiệm 2+ năm",
        salary_min: salaryMin,
        salary_max: salaryMax,
        quantity: 1,
        location: location,
        employment_type: "FULL_TIME"
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Tạo Job thất bại");
    }

    const job = await res.json();
    closeModal("create-job-modal");
    
    // Automatically Publish the job
    await apiFetch(`/jobs/${job.business_id}/publish`, { method: "POST" });
    showToast(`Đã tạo và đăng tin tuyển dụng mới: <b>${job.business_id}</b>`, "success");
    loadJobs();
  } catch (err) {
    showToast("Lỗi: " + err.message, "danger");
  }
}

// ==========================================================================
// Audit Logs View
// ==========================================================================
async function loadAuditLogs() {
  const container = document.getElementById("audit-list-container");
  if (!container) return;
  container.innerHTML = `<div style="text-align:center; padding: 2rem;"><i class="fas fa-spinner fa-spin fa-2x"></i></div>`;

  try {
    const res = await apiFetch("/audit-logs");
    if (!res.ok) {
      container.innerHTML = `<div style="color:var(--text-muted); text-align:center;">Yêu cầu quyền HR Manager hoặc Admin để xem Audit Log.</div>`;
      return;
    }

    const logs = await res.json();
    if (logs.length === 0) {
      container.innerHTML = `<div style="text-align:center; color:var(--text-muted); padding:2rem;">Chưa có nhật ký hệ thống nào.</div>`;
      return;
    }

    container.innerHTML = `
      <table class="audit-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Hành Động (Action)</th>
            <th>Thực Thể (Entity)</th>
            <th>Actor User ID</th>
            <th>Ghi Chú (Reason)</th>
            <th>Thời Gian</th>
          </tr>
        </thead>
        <tbody>
          ${logs.map(log => `
            <tr>
              <td><span style="font-family:monospace; font-weight:700;">${log.business_id}</span></td>
              <td><span class="tag" style="background:rgba(99,102,241,0.15); color:var(--primary); font-weight:700;">${log.action}</span></td>
              <td>${log.entity_type} / ${log.entity_business_id}</td>
              <td>User #${log.actor_user_id}</td>
              <td>${escapeHtml(log.reason || '-')}</td>
              <td>${new Date(log.created_at).toLocaleString()}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--status-rejected);">Lỗi: ${err.message}</div>`;
  }
}

// ==========================================================================
// Utilities
// ==========================================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  const icon = type === "success" ? "check-circle" : type === "danger" ? "exclamation-triangle" : "info-circle";
  toast.innerHTML = `<i class="fas fa-${icon}" style="font-size:1.2rem; color:var(--primary);"></i> <div>${message}</div>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, match => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[match]);
}
