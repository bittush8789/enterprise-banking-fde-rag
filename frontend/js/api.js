// ==============================================================================
// BankAssist AI — Unified API Service Client
// ==============================================================================

const API_BASE = "/api";

class BankAPI {
  static getAuthToken() {
    return localStorage.getItem("bankassist_token");
  }

  static setAuthToken(token) {
    localStorage.setItem("bankassist_token", token);
  }

  static removeAuthToken() {
    localStorage.removeItem("bankassist_token");
    localStorage.removeItem("bankassist_user");
  }

  static getUserData() {
    try {
      return JSON.parse(localStorage.getItem("bankassist_user"));
    } catch {
      return null;
    }
  }

  static setUserData(user) {
    localStorage.setItem("bankassist_user", JSON.stringify(user));
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const token = this.getAuthToken();

    const headers = {
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        // Token expired or invalid
        this.removeAuthToken();
        if (!window.location.pathname.includes("login")) {
          window.location.href = "/login";
        }
        throw new Error("Session expired. Please log in again.");
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.message || data.detail || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
      throw err;
    }
  }

  // Auth APIs
  static login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  static getCurrentUser() {
    return this.request("/auth/me");
  }

  // Chat APIs
  static askQuestion(query, sessionId = null) {
    return this.request("/chat", {
      method: "POST",
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  }

  static getSessions() {
    return this.request("/chat/sessions");
  }

  static getSessionHistory(sessionId) {
    return this.request(`/chat/history/${sessionId}`);
  }

  static deleteSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  // Documents APIs
  static getDocuments() {
    return this.request("/documents");
  }

  static uploadDocument(formData) {
    return this.request("/documents/upload", {
      method: "POST",
      body: formData,
    });
  }

  static deleteDocument(docId) {
    return this.request(`/documents/${docId}`, {
      method: "DELETE",
    });
  }

  // Admin APIs
  static getUsers() {
    return this.request("/admin/users");
  }

  static updateUserRole(userId, roles) {
    return this.request(`/admin/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({ roles }),
    });
  }

  static updateUserStatus(userId, isActive) {
    return this.request(`/admin/users/${userId}/status`, {
      method: "PUT",
      body: JSON.stringify({ is_active: isActive }),
    });
  }

  static getAuditLogs(eventType = null) {
    const query = eventType ? `?event_type=${encodeURIComponent(eventType)}` : "";
    return this.request(`/admin/audit-logs${query}`);
  }

  static getSecurityStats() {
    return this.request("/admin/security-events");
  }
}

window.BankAPI = BankAPI;
