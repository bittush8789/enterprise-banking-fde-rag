import re
from typing import List, Dict, Any

# Regular Expression patterns for high-precision Banking PII detection
PII_PATTERNS = {
    "CREDIT_DEBIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b",
    "PAN_CARD": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "AADHAAR_NUMBER": r"\b\d{4}[-\s]\d{4}[-\s]\d{4}\b|\b[2-9]\d{11}\b",
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "PHONE_NUMBER": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b(?:\+91|91)?[6-9]\d{9}\b",
    "BANK_ACCOUNT": r"\b(?:account|acc|a/c|acct|no\.?|number)\s*[:#\-]?\s*(\d{9,18})\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
}

class PIIDetector:
    """
    Detects Personally Identifiable Information (PII) including Financial and National IDs.
    Uses regex matching and Presidio (when available).
    """

    @classmethod
    def detect_pii(cls, text: str) -> List[Dict[str, Any]]:
        """
        Returns a list of detected PII entities with type, text, start, end.
        """
        if not text:
            return []

        findings = []

        # 1. Regex Pattern Matching
        for entity_type, pattern_str in PII_PATTERNS.items():
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                # For BANK_ACCOUNT with prefix capturing group
                if entity_type == "BANK_ACCOUNT" and match.groups():
                    matched_value = match.group(1)
                    start = match.start(1)
                    end = match.end(1)
                else:
                    matched_value = match.group(0)
                    start = match.start(0)
                    end = match.end(0)

                # Avoid false positive year numbers for cards/accounts
                if entity_type in ["CREDIT_DEBIT_CARD", "AADHAAR_NUMBER"] and len(matched_value.replace("-", "").replace(" ", "")) < 12:
                    continue

                findings.append({
                    "entity_type": entity_type,
                    "value": matched_value,
                    "start": start,
                    "end": end,
                    "confidence": 0.95
                })

        # 2. Try Microsoft Presidio if available
        try:
            from presidio_analyzer import AnalyzerEngine
            analyzer = AnalyzerEngine()
            presidio_results = analyzer.analyze(text=text, language="en")
            for res in presidio_results:
                matched_val = text[res.start:res.end]
                # Avoid duplicates
                if not any(f["start"] == res.start and f["end"] == res.end for f in findings):
                    findings.append({
                        "entity_type": res.entity_type,
                        "value": matched_val,
                        "start": res.start,
                        "end": res.end,
                        "confidence": res.score
                    })
        except Exception:
            # Presidio analyzer not installed or spacy model missing; fallback regex is fully active
            pass

        return findings
