// ==============================================================================
// BankAssist AI — Clean ChatBot Logic
// ==============================================================================

let currentSessionId = null;

const ChatApp = {
  async init() {
    this.bindEvents();
    await this.loadSessions();
  },

  bindEvents() {
    const sendBtn = document.getElementById("chat-send-btn");
    const textarea = document.getElementById("chat-input");
    const newChatBtn = document.getElementById("new-chat-btn");

    if (sendBtn && textarea) {
      sendBtn.addEventListener("click", () => this.sendMessage());
      textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      // Auto-resize
      textarea.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = Math.min(this.scrollHeight, 120) + "px";
      });
    }

    if (newChatBtn) {
      newChatBtn.addEventListener("click", () => this.startNewChat());
    }
  },

  async loadSessions() {
    const listEl = document.getElementById("sessions-list");
    if (!listEl) return;

    try {
      const sessions = await BankAPI.getSessions();
      if (!sessions || sessions.length === 0) {
        listEl.innerHTML = `<div class="text-muted p-2 small">No previous chats.</div>`;
        return;
      }

      listEl.innerHTML = sessions.map(s => `
        <div class="session-item ${s.id === currentSessionId ? 'active' : ''}" onclick="ChatApp.switchSession(${s.id})">
          <i class="bi bi-chat-left-text me-2"></i>
          <span class="title" title="${s.title}">${s.title}</span>
          <button class="delete-btn" onclick="event.stopPropagation(); ChatApp.deleteSession(${s.id})" title="Delete">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      `).join("");
    } catch (err) {
      console.error("Error loading chat sessions:", err);
    }
  },

  async switchSession(sessionId) {
    currentSessionId = sessionId;
    const items = document.querySelectorAll(".session-item");
    items.forEach(el => el.classList.remove("active"));

    const chatArea = document.getElementById("chat-messages-area");
    chatArea.innerHTML = `<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div></div>`;

    try {
      const history = await BankAPI.getSessionHistory(sessionId);
      chatArea.innerHTML = "";
      if (history.length === 0) {
        chatArea.innerHTML = `<div class="text-center text-muted py-5">Start chatting below.</div>`;
      } else {
        history.forEach(msg => {
          this.appendMessage(msg.role, msg.content, msg.sources, false);
        });
      }
      this.scrollToBottom();
      await this.loadSessions();
    } catch (err) {
      chatArea.innerHTML = `<div class="alert alert-danger small">Failed to load conversation history.</div>`;
    }
  },

  startNewChat() {
    currentSessionId = null;
    const chatArea = document.getElementById("chat-messages-area");
    if (chatArea) {
      chatArea.innerHTML = `
        <div class="welcome-screen">
          <div class="logo-box">
            <i class="bi bi-bank2"></i>
          </div>
          <h3>How can I help you today?</h3>
          <p>Ask any question regarding loan policies, KYC &amp; AML compliance, savings accounts, credit cards, or banking SOPs.</p>
        </div>
      `;
    }
    const input = document.getElementById("chat-input");
    if (input) {
      input.value = "";
      input.focus();
    }
    const items = document.querySelectorAll(".session-item");
    items.forEach(el => el.classList.remove("active"));
  },

  async deleteSession(sessionId) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await BankAPI.deleteSession(sessionId);
      if (currentSessionId === sessionId) {
        this.startNewChat();
      }
      await this.loadSessions();
    } catch (err) {
      alert("Failed to delete chat: " + err.message);
    }
  },

  async sendMessage() {
    const textarea = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send-btn");
    const query = textarea.value.trim();

    if (!query) return;

    textarea.value = "";
    textarea.style.height = "auto";
    sendBtn.disabled = true;

    const welcome = document.querySelector(".welcome-screen");
    if (welcome) welcome.remove();

    this.appendMessage("user", query, [], false);
    this.scrollToBottom();

    const typingId = this.showTypingIndicator();

    try {
      const response = await BankAPI.askQuestion(query, currentSessionId);
      this.removeTypingIndicator(typingId);

      if (!currentSessionId && response.session_id) {
        currentSessionId = response.session_id;
        await this.loadSessions();
      }

      this.appendMessage(
        "assistant",
        response.answer,
        response.sources,
        response.is_blocked,
        response.security_event
      );

      this.scrollToBottom();
    } catch (err) {
      this.removeTypingIndicator(typingId);
      this.appendMessage("assistant", `Error: ${err.message}`, [], true, "ERROR");
      this.scrollToBottom();
    } finally {
      sendBtn.disabled = false;
      textarea.focus();
    }
  },

  appendMessage(role, content, sources = [], isBlocked = false, securityEvent = null) {
    const chatArea = document.getElementById("chat-messages-area");
    if (!chatArea) return;

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const avatarIcon = role === "user" ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-bank2"></i>';
    const blockedClass = isBlocked ? 'msg-blocked' : '';

    let formatted = formatMarkdown(content);

    let citationsHtml = "";
    if (sources && sources.length > 0) {
      const tags = sources.map((s, idx) => `
        <span class="citation-tag" onclick="ChatApp.openCitation(${idx})">
          <i class="bi bi-file-earmark-text"></i>
          <span>${s.document_name}</span>
          <span class="text-muted">(p. ${s.page_number})</span>
        </span>
      `).join("");

      citationsHtml = `
        <div class="citation-box">
          <small class="text-warning fw-bold d-block w-100" style="font-size: 0.72rem;">
            <i class="bi bi-patch-check-fill me-1"></i>VERIFIED SOURCES:
          </small>
          ${tags}
        </div>
      `;
    }

    row.innerHTML = `
      <div class="msg-avatar">${avatarIcon}</div>
      <div class="msg-content ${blockedClass}">
        <div>${formatted}</div>
        ${citationsHtml}
      </div>
    `;

    if (sources && sources.length > 0) {
      window.lastSources = sources;
    }

    chatArea.appendChild(row);
  },

  openCitation(index) {
    if (!window.lastSources || !window.lastSources[index]) return;
    const s = window.lastSources[index];

    document.getElementById("citation-modal-title").innerText = s.document_name;
    document.getElementById("citation-modal-body").innerHTML = `
      <div class="mb-2">
        <span class="badge bg-primary me-1">Page ${s.page_number}</span>
        <span class="badge bg-success">${s.score ? Math.round(s.score * 100) + '% match' : 'Verified'}</span>
      </div>
      <p class="fw-bold mb-1">${s.section || 'General Section'}</p>
      <div class="p-3 bg-dark rounded text-light border border-secondary border-opacity-50" style="white-space: pre-wrap; font-family: monospace;">
${s.excerpt || 'Verified policy text indexed in vector store.'}
      </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById("citationModal"));
    modal.show();
  },

  showTypingIndicator() {
    const chatArea = document.getElementById("chat-messages-area");
    const id = "typing-" + Date.now();
    const row = document.createElement("div");
    row.id = id;
    row.className = "message-row assistant";
    row.innerHTML = `
      <div class="msg-avatar"><i class="bi bi-bank2"></i></div>
      <div class="msg-content">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatArea.appendChild(row);
    this.scrollToBottom();
    return id;
  },

  removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  },

  scrollToBottom() {
    const chatArea = document.getElementById("chat-messages-area");
    if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
  }
};

function formatMarkdown(text) {
  if (!text) return "";
  let clean = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  clean = clean.replace(/^• (.*$)/gim, '<li class="ms-3">$1</li>');
  clean = clean.replace(/^- (.*$)/gim, '<li class="ms-3">$1</li>');
  clean = clean.replace(/\n/g, '<br/>');
  return clean;
}

function escapeHtml(str) {
  return str.replace(/'/g, "\\'");
}

window.ChatApp = ChatApp;
