# 🔍 Technical Discovery Report — BankAssist AI
**Client Engagement:** Apex Global Bank Enterprise Modernization  
**Author:** AI Forward Deployed Engineer (FDE) & Solutions Architect  
**Classification:** Confidential — Internal Advisory  
**Date:** September 2026 | Version: 1.0  

---

## 1. Executive Summary & Business Problem Analysis

Apex Global Bank operates retail banking, commercial lending, trade finance, wealth management, and treasury operations with over 500 branch and corporate employees. Currently, bank employees spend an average of **20 to 35 minutes per day** manually searching across fragmented document repositories (SharePoint drives, PDF folders, email attachments) to answer policy questions regarding loan eligibility, KYC/AML thresholds, deposit interest rates, and internal security SOPs.

### Problem Impacts:
1. **Operational Inefficiency:** High cumulative staff time wasted on basic policy lookups (over 35,000 hours annually across 500 staff).
2. **Knowledge Bottlenecks:** Subject Matter Experts (SMEs), Senior Credit Officers, and Legal/Compliance Leads are constantly interrupted with repetitive questions.
3. **Inconsistent Customer Guidance:** Differing interpretations of loan LTV limits or KYC due diligence create audit vulnerabilities and customer friction.
4. **Compliance & Regulatory Risks:** Strict regulatory frameworks (FEMA, UCP 600, RBI, GDPR, ISO 27001) penalize errors caused by outdated documents.

---

## 2. Stakeholder Requirements & Mapping

```text
┌─────────────────────────┐
│     Business Sponsor    │ ◄── Executive Oversight & Budget Sign-off
└────────────┬────────────┘
             │
   ┌─────────┴────────────────────────────────────────┐
   │                                                  │
┌──▼──────────────────────┐               ┌───────────▼──────────────┐
│  Bank Operations & Loan │               │ Compliance & Legal Teams │
│  (Underwriting, Rates)  │               │ (KYC/AML, LRS, Reporting)│
└──┬──────────────────────┘               └───────────┬──────────────┘
   │                                                  │
   └─────────────────────────┬────────────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │   IT & Information Security     │ ◄── Zero-Trust, PII, DLP, RBAC
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │   AI FDE & Solutions Team       │ ◄── RAG Architecture & Delivery
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │   Branch Staff & End Users      │ ◄── Speed, Citations, Ease of Use
            └─────────────────────────────────┘
```

### Stakeholder Requirements Matrix:
- **Business Sponsor (COO / Head of Transformation):** Measurable operational ROI (> 250%), reduction in turnaround time (TAT), and zero hallucination risk.
- **Loan Department (Officers & Underwriters):** Immediate access to LTV tiers, FOIR formulas, credit score prime interest benchmarks, and MSME drawing power calculations.
- **Compliance & AML Officers:** Instant retrieval of customer risk categorizations (PEPs), Re-KYC cycles, CTR/STR thresholds, and overseas remittance TCS rates.
- **Customer Support Staff:** Quick lookup for fixed deposit tenors, credit card APR/waiver rules, and safe deposit locker deceased claim settlement timelines.
- **CISO / IT Security Team:** Absolute zero-trust data pipeline, on-premise/isolated vector storage, client and server-side PII masking, and anti-jailbreak input guardrails.

---

## 3. Technical Discovery Findings

| Dimension | Current State | Target State with BankAssist AI |
|---|---|---|
| **Document Formats** | PDFs, DOCX, Text files in unstructured folders | Centralized vectorized repository in ChromaDB |
| **Search Mechanism** | Keyword search in Adobe Acrobat / File Explorer | Semantic Vector Retriever with Cosine Threshold (0.15) |
| **Response Format** | Reading multi-page PDFs manually | Structured bullet points with exact page/section citations |
| **PII & Data Safety** | Manual caution by staff | Automated regex/Presidio entity redaction at edge |
| **Auditability** | None (untracked file opens) | Real-time immutable audit trail (User, Query, Citations, PII events) |
| **Deployment Mode** | Desktop silos | Dockerized microservices (FastAPI, ChromaDB, MySQL/SQLite) |

---

## 4. Current vs. Future State Workflow

### As-Is Workflow:
```text
Employee receives question ──► Opens file folder ──► Manually reads 40-page PDF ──► High TAT (15-30 mins) ──► Risk of Outdated Info
```

### To-Be Workflow (BankAssist AI):
```text
Employee inputs question ──► PII/Injection Guardrail ──► Semantic Vector Search ──► Grounded LLM Response with Source Citations (< 2 seconds)
```
