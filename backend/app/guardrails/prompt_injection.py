import re
from typing import Tuple, List

# Patterns targeting common prompt injection, jailbreaks, system prompt extraction, and security overrides
INJECTION_PATTERNS = [
    # System prompt extraction
    r"(?i)\b(reveal|show|print|display|tell|expose|leak|what\s+is|what\s+are)\b.*\b(system\s+prompt|system\s+instructions|internal\s+instructions|base\s+prompt|initial\s+prompt)\b",
    r"(?i)\brepeat\s+(all\s+)?(the\s+)?(words\s+above|text\s+above|previous\s+instructions)\b",
    
    # Instruction override & jailbreak
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above|former)\s+(instructions|prompts|rules|commands|constraints|directives)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above|former|security)\s+(rules|guidelines|instructions|policy|policies)\b",
    r"(?i)\b(act\s+as\s+DAN|act\s+as\s+an\s+unrestricted|you\s+are\s+now\s+in\s+DAN|developer\s+mode)\b",
    r"(?i)\bpretend\s+you\s+have\s+no\s+(rules|restrictions|filters|guidelines)\b",
    
    # Sensitive credential & data exfiltration
    r"(?i)\b(show|dump|give|extract|leak)\b.*\b(database\s+credentials|passwords|api\s+keys|secret\s+keys|env\s+variables|connection\s+strings)\b",
    r"(?i)\b(show|give|extract|list)\b.*\b(all\s+)?(customer\s+data|account\s+numbers|passwords|ssn|pan\s+numbers)\b",
    r"(?i)\bignore\s+security\b",
    
    # Dangerous roleplay / simulator tags
    r"(?i)\[system\]|\<system\>|\[developer\s+mode\]|\<instruction\>",
    r"(?i)\boverride\s+permission(s)?\b",
]

COMPILED_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]

class PromptInjectionDetector:
    """
    Multi-rule prompt injection, jailbreak, and system override detector.
    """

    @classmethod
    def detect(cls, query: str) -> Tuple[bool, List[str]]:
        """
        Returns (is_detected, list_of_matching_reasons)
        """
        if not query or not query.strip():
            return False, []

        reasons = []
        normalized_query = query.strip()

        for pattern in COMPILED_INJECTION_PATTERNS:
            if pattern.search(normalized_query):
                reasons.append(f"Prompt injection / security override pattern matched: {pattern.pattern[:40]}...")

        # Heuristic check for delimiter smuggling or repeated override keywords
        override_keywords = ["ignore previous", "reveal prompt", "bypass security", "developer mode", "override rules"]
        for kw in override_keywords:
            if kw in normalized_query.lower() and not reasons:
                reasons.append(f"Heuristic keyword detected: '{kw}'")

        is_malicious = len(reasons) > 0
        return is_malicious, reasons
