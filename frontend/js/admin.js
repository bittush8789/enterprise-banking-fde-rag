// ==============================================================================
// BankAssist AI — Admin & Security Dashboard Client
// ==============================================================================

const AdminApp = {
  async init() {
    this.bindEvents();
    await Promise.all([
      this.loadUsers(),
      this.loadSecurityStats(),
      this.loadAuditLogs()
    ]);
  },

  bindEvents() {
    const filterSelect = document.getElementById("audit-filter-select");
    if (filterSelect) {
      filterSelect.addEventListener("change", (e) => {
        this.loadAuditLogs(e.target.value);
      });
    }

    const refreshBtn = document.getElementById("refresh-audit-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        this.loadSecurityStats();
        this.loadAuditLogs(document.getElementById("audit-filter-select")?.value);
      });
    }
  },

  // 1. User Management
  async loadUsers() {
    const tableBody = document.getElementById("users-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4"><div class="spinner-border text-primary"></div></td></tr>`;

    try {
      const users = await BankAPI.getUsers();
      if (!users || users.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No users found.</td></tr>`;
        return;
      }

      tableBody.innerHTML = users.map(user => {
        const rolePills = (user.roles || []).map(r => {
          const rname = typeof r === "string" ? r : r.name;
          return `<span class="role-pill ${rname.toLowerCase()} me-1">${rname}</span>`;
        }).join("");

        const statusBadge = user.is_active 
          ? `<span class="badge-status success">Active</span>` 
          : `<span class="badge-status blocked">Inactive</span>`;

        const userRolesJson = JSON.stringify((user.roles || []).map(r => typeof r === "string" ? r : r.name));

        return `
          <tr>
            <td class="fw-semibold text-light">${escapeHtml(user.name)}</td>
            <td class="text-muted">${escapeHtml(user.email)}</td>
            <td>${rolePills}</td>
            <td>${statusBadge}</td>
            <td class="small text-muted">${new Date(user.created_at).toLocaleDateString()}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-warning me-2" onclick='AdminApp.openRoleModal(${user.id}, "${escapeHtml(user.name)}", ${userRolesJson})' title="Edit Roles">
                <i class="bi bi-pencil-square"></i> Roles
              </button>
              <button class="btn btn-sm ${user.is_active ? 'btn-outline-danger' : 'btn-outline-success'}" onclick="AdminApp.toggleUserStatus(${user.id}, ${!user.is_active})" title="${user.is_active ? 'Deactivate' : 'Activate'}">
                <i class="bi ${user.is_active ? 'bi-person-x' : 'bi-person-check'}"></i>
              </button>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load users: ${err.message}</td></tr>`;
    }
  },

  openRoleModal(userId, userName, currentRoles) {
    document.getElementById("role-modal-user-id").value = userId;
    document.getElementById("role-modal-user-name").innerText = userName;

    const checkboxes = document.querySelectorAll("input[name='user_edit_roles']");
    checkboxes.forEach(cb => {
      cb.checked = currentRoles.includes(cb.value);
    });

    const modal = new bootstrap.Modal(document.getElementById("editRoleModal"));
    modal.show();
  },

  async saveUserRoles() {
    const userId = document.getElementById("role-modal-user-id").value;
    const checkboxes = document.querySelectorAll("input[name='user_edit_roles']:checked");
    const selectedRoles = Array.from(checkboxes).map(cb => cb.value);

    if (selectedRoles.length === 0) {
      alert("User must have at least one role.");
      return;
    }

    try {
      await BankAPI.updateUserRole(userId, selectedRoles);
      const modalEl = document.getElementById("editRoleModal");
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      await this.loadUsers();
    } catch (err) {
      alert("Failed to update user roles: " + err.message);
    }
  },

  async toggleUserStatus(userId, newStatus) {
    const action = newStatus ? "activate" : "deactivate";
    if (!confirm(`Are you sure you want to ${action} this user?`)) return;

    try {
      await BankAPI.updateUserStatus(userId, newStatus);
      await this.loadUsers();
    } catch (err) {
      alert(`Failed to ${action} user: ` + err.message);
    }
  },

  // 2. Security Dashboard & Stats
  async loadSecurityStats() {
    try {
      const stats = await BankAPI.getSecurityStats();

      document.getElementById("stat-blocked").innerText = stats.total_blocked_requests || 0;
      document.getElementById("stat-injections").innerText = stats.prompt_injection_attempts || 0;
      document.getElementById("stat-pii").innerText = stats.pii_detection_events || 0;
      document.getElementById("stat-unauthorized").innerText = stats.unauthorized_access_attempts || 0;
      document.getElementById("stat-lowscore").innerText = stats.low_score_fallbacks || 0;
      document.getElementById("stat-queries").innerText = stats.total_queries || 0;
    } catch (err) {
      console.error("Failed to load security statistics:", err);
    }
  },

  async loadAuditLogs(eventType = null) {
    const tableBody = document.getElementById("audit-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4"><div class="spinner-border text-primary"></div></td></tr>`;

    try {
      const logs = await BankAPI.getAuditLogs(eventType === "ALL" ? null : eventType);
      if (!logs || logs.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No audit events recorded for this filter.</td></tr>`;
        return;
      }

      tableBody.innerHTML = logs.map(log => {
        let statusClass = "success";
        if (log.event_status === "BLOCKED") statusClass = "blocked";
        else if (log.event_status === "WARNING" || log.event_status === "FAILED") statusClass = "warning";

        const timeStr = new Date(log.created_at).toLocaleString();

        let detailsDisplay = log.details || "-";
        if (detailsDisplay.length > 90) {
          detailsDisplay = `<span title="${escapeHtml(detailsDisplay)}">${escapeHtml(detailsDisplay.substring(0, 90))}...</span>`;
        } else {
          detailsDisplay = escapeHtml(detailsDisplay);
        }

        return `
          <tr>
            <td class="small text-muted font-monospace">${timeStr}</td>
            <td class="fw-semibold text-light">${escapeHtml(log.user_email || 'System')}</td>
            <td><span class="badge bg-dark border border-secondary">${escapeHtml(log.event_type)}</span></td>
            <td><span class="badge-status ${statusClass}">${escapeHtml(log.event_status)}</span></td>
            <td class="small text-muted font-monospace">${detailsDisplay}</td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Failed to load audit logs: ${err.message}</td></tr>`;
    }
  }
};

window.AdminApp = AdminApp;
