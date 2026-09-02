# 📝 Statement of Work (SOW) — BankAssist AI Implementation
**Client:** Apex Global Bank  
**Contractor / Lead:** AI Solutions Architect & Forward Deployed Engineer (FDE)  
**Effective Date:** Q3 2026  
**Engagement Duration:** 12 Weeks  

---

## 1. Project Purpose & Objectives
The purpose of this engagement is to architect, configure, harden, and deploy **BankAssist AI**, an enterprise-grade AI knowledge assistant grounded strictly in approved banking documentation with zero-trust guardrails.

---

## 2. In-Scope vs. Out-of-Scope Work

### ✅ IN-SCOPE:
1. **RAG Architecture & Vector Indexing:** Automated ingestion, chunking, and embedding of 13 approved banking policy manuals into ChromaDB.
2. **AI Guardrails & Zero-Trust Gateway:** Implementation of real-time PII detection (Presidio/regex) and anti-prompt injection filters.
3. **Reasoning Integration:** Groq cloud API integration with `qwen/qwen3.6-27b` using strict grounded banking prompts and citation generation.
4. **Enterprise Web Application:** Responsive Single Page Application (SPA) with Dark/Light themes, chat session persistence, document repository management, user directory, and security audit log telemetry.
5. **Containerized Deployment:** Docker Compose configuration orchestrating FastAPI, ChromaDB, and MySQL 8.0 with persistent storage.
6. **Testing & UAT:** Comprehensive test suite (unit, integration, security guardrail tests) and formal UAT runbook execution.

### ❌ OUT-OF-SCOPE:
- Core banking mainframe transaction execution (e.g., automated wire transfers, ATM balance modifications).
- Direct customer credit disbursement without human underwriter approval.
- Modification of regulatory statutes or legal filing submission to central banks.

---

## 3. Project Milestones & Timeline

| Phase | Milestone | Duration | Key Deliverables |
|:---|:---|:---:|:---|
| **Phase 1** | Technical Discovery & Data Classification | Weeks 1-2 | Discovery Report, Data Catalog, Threat Model |
| **Phase 2** | Architecture & Security Guardrail Design | Weeks 3-4 | Solution Architecture, PII Masker, Prompt Filter |
| **Phase 3** | Core Application & RAG Pipeline Build | Weeks 5-8 | ChromaDB Ingestion, Groq Chain, SPA Dashboard |
| **Phase 4** | Automated Testing & UAT Execution | Weeks 9-10 | Pytest Suite (15/15 Pass), UAT Sign-off |
| **Phase 5** | Containerization & Production Handover | Weeks 11-12 | Docker Compose Stack, ROI Presentation, Runbook |
