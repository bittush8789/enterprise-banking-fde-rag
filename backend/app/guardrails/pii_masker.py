import re
from typing import Tuple, List, Dict, Any
from backend.app.guardrails.pii_detector import PIIDetector

class PIIMasker:
    """
    Masks sensitive Personally Identifiable Information (PII) before processing and logging.
    """

    @classmethod
    def mask_token(cls, entity_type: str, value: str) -> str:
        clean_val = value.strip()
        if entity_type in ["CREDIT_DEBIT_CARD", "CREDIT_CARD"]:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) >= 4:
                return "X" * (len(digits) - 4) + digits[-4:]
            return "XXXXXXXXXXXX"
        
        elif entity_type in ["PAN_CARD"]:
            if len(clean_val) == 10:
                return clean_val[:2] + "XXXXXX" + clean_val[-2:]
            return "XXXXXXXXXX"

        elif entity_type in ["AADHAAR_NUMBER"]:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) >= 4:
                return "XXXX-XXXX-" + digits[-4:]
            return "XXXX-XXXX-XXXX"

        elif entity_type in ["EMAIL_ADDRESS", "EMAIL"]:
            parts = clean_val.split("@")
            if len(parts) == 2:
                name, domain = parts
                masked_name = name[0] + "***" if len(name) > 1 else "***"
                return f"{masked_name}@{domain}"
            return "***@email.com"

        elif entity_type in ["PHONE_NUMBER", "PHONE"]:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) >= 4:
                return "X" * (len(digits) - 4) + digits[-4:]
            return "XXXXXXXXXX"

        elif entity_type in ["BANK_ACCOUNT", "IBAN_CODE"]:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) >= 4:
                return "X" * (len(digits) - 4) + digits[-4:]
            return "XXXXXXXXX"

        elif entity_type in ["SSN"]:
            return "XXX-XX-XXXX"

        # Default fallback masking
        return f"[MASKED_{entity_type}]"

    @classmethod
    def mask_text(cls, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Detects and replaces all PII tokens with masked equivalents.
        Returns (masked_text, detected_entities)
        """
        if not text:
            return text, []

        findings = PIIDetector.detect_pii(text)
        if not findings:
            return text, []

        # Sort findings in reverse order of start position to replace cleanly without offset collisions
        sorted_findings = sorted(findings, key=lambda x: x["start"], reverse=True)
        masked_text = text

        for entity in sorted_findings:
            start = entity["start"]
            end = entity["end"]
            orig_value = text[start:end]
            masked_replacement = cls.mask_token(entity["entity_type"], orig_value)
            masked_text = masked_text[:start] + masked_replacement + masked_text[end:]

        return masked_text, findings
