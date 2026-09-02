from typing import Dict, Any
from backend.app.guardrails.prompt_injection import PromptInjectionDetector
from backend.app.guardrails.pii_masker import PIIMasker

class InputGuardrail:
    """
    Validates user query before entering the RAG pipeline.
    """

    SAFE_REFUSAL_MESSAGE = "I cannot process this request because it violates the application's security policy."

    @classmethod
    def validate_and_sanitize(cls, query: str) -> Dict[str, Any]:
        """
        Runs injection checks, PII detection, and sanitization.
        Returns a dictionary with result metadata.
        """
        # 1. Prompt Injection & Jailbreak Check
        is_injection, injection_reasons = PromptInjectionDetector.detect(query)
        if is_injection:
            return {
                "is_safe": False,
                "reason": "PROMPT_INJECTION_DETECTED",
                "details": injection_reasons,
                "sanitized_query": None,
                "response_message": cls.SAFE_REFUSAL_MESSAGE,
                "pii_detected": False,
                "pii_entities": [],
            }

        # 2. PII Detection and Masking
        masked_query, pii_entities = PIIMasker.mask_text(query)
        pii_detected = len(pii_entities) > 0

        return {
            "is_safe": True,
            "reason": None,
            "details": [],
            "sanitized_query": masked_query,
            "response_message": None,
            "pii_detected": pii_detected,
            "pii_entities": pii_entities,
        }
