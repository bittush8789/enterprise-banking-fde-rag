from typing import Dict, Any, List
from backend.app.guardrails.pii_masker import PIIMasker
from backend.app.schemas.chat import SourceCitation

class OutputGuardrail:
    """
    Validates LLM generated answers before returning them to the user.
    """

    FALLBACK_NO_INFO = "I could not find sufficient information in the approved banking documents to answer this question."

    @classmethod
    def validate_output(cls, raw_answer: str, sources: List[SourceCitation]) -> Dict[str, Any]:
        """
        Validates the output against PII leakage and grounding rules.
        """
        if not raw_answer or not raw_answer.strip():
            return {
                "is_valid": False,
                "sanitized_answer": cls.FALLBACK_NO_INFO,
                "sources": [],
                "event": "EMPTY_LLM_OUTPUT"
            }

        # Check if the model explicitly returned no-info phrase
        if "could not find sufficient information" in raw_answer.lower() or "not sufficient" in raw_answer.lower():
            return {
                "is_valid": True,
                "sanitized_answer": raw_answer.strip(),
                "sources": sources,
                "event": "NO_INFO_RETURNED"
            }

        # 1. Output PII Scan and Masking
        masked_answer, pii_findings = PIIMasker.mask_text(raw_answer)
        pii_leaked = len(pii_findings) > 0

        # 2. Source Grounding Rule: If answer provides policy details but has 0 retrieved sources, flag or fallback
        if not sources and not any(phrase in raw_answer.lower() for phrase in ["hello", "hi", "how can i help", "welcome"]):
            # If not a simple greeting and no sources were retrieved, enforce safe response
            return {
                "is_valid": True,
                "sanitized_answer": cls.FALLBACK_NO_INFO,
                "sources": [],
                "event": "NO_SOURCES_FALLBACK"
            }

        return {
            "is_valid": True,
            "sanitized_answer": masked_answer,
            "sources": sources,
            "pii_leaked": pii_leaked,
            "pii_findings": pii_findings,
            "event": "PII_MASKED_IN_OUTPUT" if pii_leaked else "SUCCESS"
        }
