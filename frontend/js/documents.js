// ==============================================================================
// BankAssist AI — Document Management Client
// ==============================================================================

const DocumentsApp = {
  async init() {
    this.bindEvents();
    await this.loadDocuments();
  },

  bindEvents() {
    const uploadForm = document.getElementById("document-upload-form");
    if (uploadForm) {
      uploadForm.addEventListener("submit", (e) => this.handleUpload(e));
    }
  },

  async loadDocuments() {
    const tableBody = document.getElementById("documents-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>`;

    try {
      const docs = await BankAPI.getDocuments();
      if (!docs || docs.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No banking documents found in vector index.</td></tr>`;
        return;
      }

      tableBody.innerHTML = docs.map(doc => {
        const statusClass = doc.status === "INDEXED" ? "success" : (doc.status === "FAILED" ? "blocked" : "warning");

        const deleteBtn = `
          <button class="btn btn-sm btn-outline-danger" onclick="DocumentsApp.deleteDocument(${doc.id}, '${escapeHtml(doc.document_name)}')" title="Delete Document & Vectors">
            <i class="bi bi-trash"></i> Delete
          </button>
        `;

        return `
          <tr>
            <td class="fw-semibold text-main">${escapeHtml(doc.document_name)}</td>
            <td><span class="badge bg-secondary">${doc.document_type}</span></td>
            <td><span class="text-muted">${doc.department || 'General'}</span></td>
            <td><span class="badge bg-dark border border-secondary">${doc.classification || 'Internal'}</span></td>
            <td><span class="badge-status ${statusClass}">${doc.status}</span></td>
            <td class="text-end">${deleteBtn}</td>
          </tr>
        `;
      }).join("");

    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load documents: ${err.message}</td></tr>`;
    }
  },

  async handleUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("doc-file-input");
    const nameInput = document.getElementById("doc-name-input");
    const typeSelect = document.getElementById("doc-type-select");
    const deptInput = document.getElementById("doc-dept-input");
    const classSelect = document.getElementById("doc-class-select");
    const versionInput = document.getElementById("doc-version-input");
    const submitBtn = document.getElementById("doc-upload-submit-btn");

    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Please select a document file (.pdf, .docx, or .txt).");
      return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_name", nameInput.value.trim());
    formData.append("document_type", typeSelect.value);
    formData.append("department", deptInput.value.trim());
    formData.append("classification", classSelect.value);
    formData.append("version", versionInput.value.trim());
    formData.append("allowed_roles", JSON.stringify(["LOAN_OFFICER", "COMPLIANCE_OFFICER", "CUSTOMER_SUPPORT", "MANAGER", "ADMIN"]));

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Extracting & Indexing into Pinecone...';

    try {
      const result = await BankAPI.uploadDocument(formData);
      alert(`Success! Document "${result.document_name}" indexed successfully with ${result.chunks_count} chunks into Pinecone.`);
      
      const modalEl = document.getElementById("uploadDocumentModal");
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      
      document.getElementById("document-upload-form").reset();
      await this.loadDocuments();
    } catch (err) {
      alert(`Upload Error: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Upload & Vectorize Document';
    }
  },

  async deleteDocument(id, name) {
    if (!confirm(`Are you sure you want to permanently delete document "${name}" and purge all its chunks from Pinecone?`)) {
      return;
    }

    try {
      await BankAPI.deleteDocument(id);
      alert(`Document "${name}" deleted successfully.`);
      await this.loadDocuments();
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  }
};

window.DocumentsApp = DocumentsApp;
