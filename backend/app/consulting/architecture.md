# 🏗️ Solution Architecture & Technical Design Document
**System Name:** BankAssist AI Enterprise RAG  
**Target Deployment:** Multi-container Dockerized Architecture  

---

## 1. System Components Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER (Frontend SPA)                     │
│  • Vanilla JS + Bootstrap 5 + CSS Variable Design Tokens (Dark / Light)    │
│  • Corporate Landing (/), Auth Portal (/login), Enterprise Workspace (/dashboard)│
│  • Multi-Session Chat Controller, Real-time Citations Modal, Audit Telemetry│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST (JWT Bearer)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    API GATEWAY & APPLICATION SERVER (FastAPI)               │
│  • Router Modules: /api/auth, /api/chat, /api/documents, /api/admin        │
│  • Zero-Trust Middleware: PII Masking, Prompt Injection Filters             │
│  • Background Document Ingestion & Chunking Workers                         │
└──────────────────┬───────────────────────────────┬──────────────────────────┘
                   │                               │
┌──────────────────▼──────────────┐ ┌──────────────▼──────────────────────────┐
│   VECTOR STORE & RETRIEVAL      │ │       ENTERPRISE SQL DATABASE            │
│  • ChromaDB Container (8001)    │ │  • MySQL 8.0 (Port 3306) / Local SQLite  │
│  • HttpClient & Local Fallback  │ │  • Users, Roles, Documents, Sessions,    │
│  • BGE-Small Embeddings (384-d) │ │    Audit Logs, Security Telemetry Counts │
└──────────────────┬──────────────┘ └─────────────────────────────────────────┘
                   │ Context Injection
┌──────────────────▼──────────────────────────────────────────────────────────┐
│                   INFERENCE ENGINE (Groq Cloud API)                         │
│  • Model: qwen/qwen3.6-27b (High-speed enterprise reasoning)               │
│  • Grounded Banking System Prompt & Citation Mandate                        │
│  • Output Reasoning Cleaner & Cosine Confidence Threshold Filter            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema Design (SQLAlchemy ORM)

```text
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│     User        │       │      UserRole        │       │      Role       │
├─────────────────┤       ├──────────────────────┤       ├─────────────────┤
│ id (PK)         │◄─────►│ user_id (FK)         │◄─────►│ id (PK)         │
│ email (UQ)      │       │ role_id (FK)         │       │ name (UQ)       │
│ hashed_password │       └──────────────────────┘       │ description     │
│ name, department│                                      └─────────────────┘
│ is_active       │
└────────┬────────┘
         │ 1:N
         ├─────────────────────────────────────────┐
         ▼                                         ▼
┌─────────────────┐                       ┌─────────────────┐
│   ChatSession   │                       │    AuditLog     │
├─────────────────┤                       ├─────────────────┤
│ id (PK)         │                       │ id (PK)         │
│ session_id (UQ) │                       │ user_id (FK)    │
│ user_id (FK)    │                       │ action          │
│ title           │                       │ status          │
│ created_at      │                       │ ip_address      │
└────────┬────────┘                       │ details         │
         │ 1:N                            │ timestamp       │
         ▼                                └─────────────────┘
┌─────────────────┐
│   ChatMessage   │
├─────────────────┤
│ id (PK)         │
│ session_id (FK) │
│ role            │
│ content         │
│ citations_json  │
│ timestamp       │
└─────────────────┘
```
