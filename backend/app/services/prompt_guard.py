"""Prompt injection detection and sanitization."""
import re
from app.core.logging import logger

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|previous\s+|above\s+)?instructions",
    r"disregard\s+(all\s+|previous\s+|above\s+)?instructions",
    r"you\s+are\s+now",
    r"new\s+persona",
    r"system\s+prompt",
    r"jailbreak",
    r"DAN\s+mode",
    r"pretend\s+you",
    r"forget\s+everything",
    r"forget\s+all\s+previous",
    r"override\s+instructions",
    r"bypass\s+security",
]


def detect_injection(text: str) -> bool:
    """Detect potential prompt injection patterns in text."""
    if not text:
        return False
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            logger.warning(f"Potential injection detected: {pattern}")
            return True
    return False


def sanitize_query(text: str) -> str:
    """Wrap user query in structural delimiters to prevent role confusion."""
    return f"<user_query>\n{text}\n</user_query>"


def sanitize_chunk(text: str) -> str:
    """Wrap document chunk in delimiters to signal external content."""
    return f"<document_content>\n{text}\n</document_content>"
