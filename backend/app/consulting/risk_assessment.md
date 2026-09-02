# 🛡️ AI Security & Risk Assessment (Threat Model)
**Project:** BankAssist AI Enterprise RAG  
**Standard:** OWASP Top 10 for LLM Applications (2025/2026), NIST AI Risk Management Framework (AI RMF 1.0)  

---

## 1. Enterprise AI Threat Matrix

| Threat ID | Threat Vector | OWASP LLM Ref | Likelihood | Impact | Mitigation Strategy | Detection & Telemetry |
|:---|:---|:---|:---:|:---:|:---|:---|
| **THR-01** | **Direct Prompt Injection & Jailbreak** | LLM01 | High | High | Multi-layer regex & semantic injection detector in `prompt_injection.py` blocking DAN, developer overrides, and roleplay bypasses. | Real-time audit event `PROMPT_INJECTION_BLOCKED` recorded with client IP and user ID. |
| **THR-02** | **Sensitive PII & Financial Leakage** | LLM02 / LLM06 | High | Critical | Edge masking in `pii_masker.py` and output validation in `output_guardrail.py` before rendering context to LLM or client. | Masked entity counts incremented on Security Telemetry Dashboard. |
| **THR-03** | **Hallucination & Policy Misinformation** | LLM09 | High | Critical | Strict RAG pipeline grounding with cosine similarity threshold (`0.15`). System refuses to answer unindexed topics. | Low confidence fallback triggered: *"I could not find sufficient information in the approved banking documents..."* |
| **THR-04** | **System Prompt Exfiltration** | LLM07 | Medium | Moderate | Prompt shielding rules prohibiting the output of meta-prompts, internal `<think>` reasoning tags, or DB schemas. | Regex detector intercepts phrases like *"Repeat your initial prompt"* or *"What are your system rules"*. |
| **THR-05** | **Unauthorized Document Access** | LLM08 | Medium | High | Multi-tenant vector retrieval metadata filtering and JWT authentication verification on all API routes. | `401 Unauthorized` / `403 Forbidden` logged to MySQL audit log table. |
| **THR-06** | **Denial of Service / Token Flooding** | LLM04 | Moderate | Moderate | Input query truncation (max 500 characters) and rate limiting on `/api/chat` endpoints. | HTTP `429 Too Many Requests` status codes. |
| **THR-07** | **Insecure Output Handling / XSS** | LLM03 | Low | High | HTML character escaping (`escapeHtml()`) across client message bubbles and markdown renderer. | Sanitized DOM elements. |

---

## 2. Zero-Trust Defense in Depth Architecture

```text
[ Incoming Query ]
       │
       ▼
[ Layer 1: Input Guardrail ] ──► (Block Jailbreaks, Injection, Script Tags)
       │ Pass
       ▼
[ Layer 2: PII Redaction ] ───► (Mask Cards, PAN, Aadhaar, Accounts, Emails)
       │ Masked Query
       ▼
[ Layer 3: Vector Retrieval ] ─► (ChromaDB Cosine Threshold >= 0.15)
       │ Chunks Found?
       ├─► No: Return Safe Refusal Fallback (No LLM Call)
       ▼ Yes
[ Layer 4: Grounded Prompt ] ──► (Strict Banking System Prompt + Ingested Chunks)
       │
       ▼
[ Layer 5: Groq Qwen Inference]► (Temperature 0.1, Max Tokens 3000)
       │
       ▼
[ Layer 6: Output Guardrail ] ─► (Reasoning Tag Stripper, PII Out-Filter, Citation Verification)
       │
       ▼
[ Grounded Answer + Citations to Staff ]
```
