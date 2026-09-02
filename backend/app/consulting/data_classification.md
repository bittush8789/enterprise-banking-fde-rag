# 🔐 Banking Data Classification Framework & Governance
**Project:** BankAssist AI Enterprise RAG  
**Standard:** ISO/IEC 27001, NIST SP 800-53, GDPR, Indian DPDP Act  
**Classification Level:** Enterprise Architecture  

---

## 1. Four-Tier Banking Data Classification Model

BankAssist AI implements strict taxonomy rules across all ingested knowledge assets and user queries:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PUBLIC                                                              │
│    • Product marketing brochures, published branch branch list        │
│    • Access: Unrestricted, guest-facing                                │
├────────────────────────────────────────────────────────────────────────┤
│ 2. INTERNAL                                                            │
│    • Standard Operating Procedures (SOPs), holiday schedules, forms    │
│    • Access: All authenticated bank employees                          │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CONFIDENTIAL                                                        │
│    • Underwriting limits, credit risk pricing, credit card dispute SOP │
│    • Access: Department staff, officers, managers                      │
├────────────────────────────────────────────────────────────────────────┤
│ 4. RESTRICTED                                                          │
│    • KYC/AML PEP lists, cybersecurity password policy, treasury limits │
│    • Access: Compliance, Risk, Security, and Executive Management      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Classification Matrix & Handling Rules

| Tier | Sensitivity | Encryption (At-Rest / In-Transit) | Masking Mandate | Allowed Export / Share |
|---|---|---|---|---|
| **PUBLIC** | Low | TLS 1.3 | None | Unrestricted |
| **INTERNAL** | Moderate | AES-256 / TLS 1.3 | Standard PII Redaction | Internal Portal Only |
| **CONFIDENTIAL** | High | AES-256 / TLS 1.3 | Full PII & Account Redaction | Role-gated RAG context |
| **RESTRICTED** | Critical | AES-256-GCM / TLS 1.3 | Full PII, Auth tokens, Secrets | Zero-Trust Audit Stream |

---

## 3. PII Redaction & Entity Protection Standards

All user inputs and extracted document contexts pass through real-time entity detectors with regex patterns and Microsoft Presidio engines:

| Entity Type | Regex / Pattern Rule | Replacement Token | Example Input | Masked Output |
|---|---|---|---|---|
| **Credit/Debit Card** | `\b(?:\d{4}[-\s]?){3}\d{4}\b` (Luhn Validated) | `[CARD: XXXXXXXXXXXX$4]` | `4532-1234-5678-9012` | `[CARD: XXXXXXXXXXXX9012]` |
| **Indian PAN Card** | `\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b` | `[PAN: ABXXXXXX4F]` | `ABCDE1234F` | `[PAN: ABXXXXXX4F]` |
| **Aadhaar Number** | `\b[2-9]{1}[0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b` | `[AADHAAR: XXXX-XXXX-9012]` | `2345 6789 9012` | `[AADHAAR: XXXX-XXXX-9012]` |
| **Bank Account** | `\b\d{9,18}\b` | `[ACCOUNT: XXXXXXX890]` | `123456789012` | `[ACCOUNT: XXXXXXXXX012]` |
| **Email Address** | `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+` | `[EMAIL: REDACTED]` | `john.doe@bank.com` | `[EMAIL: REDACTED]` |
| **Phone Number** | `(?:\+?91[\s-]?)?[6789]\d{9}` | `[PHONE: +91-XXXXXX1234]` | `+91 9876543210` | `[PHONE: +91-XXXXXX3210]` |
