# 📊 Banking Data Inventory & Ingestion Catalog
**Project:** BankAssist AI Enterprise RAG  
**Classification:** Confidential — Internal Banking Inventory  
**Version:** 2026.1  

---

## 1. Comprehensive Banking Data Asset Inventory

The following approved banking policy documents and standard operating procedures (SOPs) are indexed and maintained within the BankAssist AI vector repository:

| ID | Document Name | Type | Department | Classification | Allowed Roles | Version | File Format | Status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **DOC-01** | Apex Home Loan Underwriting Policy (2026) | Policy | Retail Lending | CONFIDENTIAL | LOAN_OFFICER, MANAGER, ADMIN | v2.4 | TXT/PDF | INDEXED (5 Chunks) |
| **DOC-02** | KYC & Anti-Money Laundering Master Directive | Compliance | Compliance & Risk | RESTRICTED | COMPLIANCE_OFFICER, MANAGER, ADMIN | v4.1 | TXT/PDF | INDEXED (5 Chunks) |
| **DOC-03** | Retail Savings, Deposits & Fixed Deposit Guide | Guide | Retail Banking | INTERNAL | ALL STAFF, ADMIN | v1.8 | TXT/PDF | INDEXED (4 Chunks) |
| **DOC-04** | Internal IT & Cybersecurity Operational Standard | SOP | Information Security | RESTRICTED | ALL STAFF, ADMIN | v3.0 | TXT/PDF | INDEXED (4 Chunks) |
| **DOC-05** | Credit Card Issuance, Rewards & Dispute Policy (2026) | Policy | Cards & Payments | CONFIDENTIAL | CUSTOMER_SUPPORT, MANAGER, ADMIN | v2.1 | TXT/PDF | INDEXED (5 Chunks) |
| **DOC-06** | Commercial Lending & MSME Business Financing Directive | Policy | Commercial Lending | CONFIDENTIAL | LOAN_OFFICER, MANAGER, ADMIN | v3.2 | TXT/PDF | INDEXED (5 Chunks) |
| **DOC-07** | Digital Fraud Defense & Customer Zero-Liability Mandate | Policy | Fraud & Risk | CONFIDENTIAL | CUSTOMER_SUPPORT, COMPLIANCE, ADMIN | v2.0 | TXT/PDF | INDEXED (4 Chunks) |
| **DOC-08** | Foreign Exchange & Cross-Border Remittance SOP (LRS) | SOP | Forex & Trade | RESTRICTED | COMPLIANCE, BRANCH STAFF, ADMIN | v2.5 | TXT/PDF | INDEXED (3 Chunks) |
| **DOC-09** | Wealth Management, Mutual Funds & Sovereign Gold Bonds SOP | SOP | Wealth Advisory | INTERNAL | ALL STAFF, ADMIN | v1.5 | TXT/PDF | INDEXED (3 Chunks) |
| **DOC-10** | Personal & Higher Education Loan Underwriting Policy (2026) | Policy | Retail Lending | CONFIDENTIAL | LOAN_OFFICER, MANAGER, ADMIN | v2.2 | TXT/PDF | INDEXED (4 Chunks) |
| **DOC-11** | Trade Finance, Letters of Credit (LC) & Bank Guarantees (BG) Manual | Manual | Trade Finance | CONFIDENTIAL | TRADE_FINANCE, MANAGER, ADMIN | v3.0 | TXT/PDF | INDEXED (4 Chunks) |
| **DOC-12** | Safe Deposit Lockers & Deceased Depositor Settlement Directive | Directive | Branch Operations | INTERNAL | CUSTOMER_SUPPORT, MANAGER, ADMIN | v1.9 | TXT/PDF | INDEXED (3 Chunks) |
| **DOC-13** | Treasury Derivatives & Market Risk Management Policy | Policy | Treasury & Markets | RESTRICTED | TREASURY, RISK, ADMIN | v4.0 | TXT/PDF | INDEXED (3 Chunks) |

---

## 2. Ingestion & Chunking Specification

- **Text Extraction:** Multi-format parser supporting `.txt`, `.pdf` (PyPDF/pdfplumber), and `.docx` (python-docx).
- **Chunking Strategy:** `RecursiveCharacterTextSplitter` with `chunk_size = 1000` characters and `chunk_overlap = 200` characters.
- **Metadata Enriched per Vector:**
  ```json
  {
    "document_id": "1",
    "document_name": "Apex Home Loan Underwriting Policy (2026)",
    "document_type": "policy",
    "department": "Retail Lending",
    "classification": "CONFIDENTIAL",
    "allowed_roles": ["LOAN_OFFICER", "MANAGER", "ADMIN"],
    "version": "v2.4",
    "chunk_index": 0
  }
  ```
- **Embedding Generation:** 384-dimensional dense vectors generated via `BAAI/bge-small-en-v1.5` with deterministic token fallback for cross-platform resilience.
- **Storage Target:** ChromaDB Collection `bank_documents`.
