from __future__ import annotations

import re

class PIIMasker:
    # Regex patterns for common PII
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b')

    @classmethod
    def mask_text(cls, text: str) -> str:
        text = cls.SSN_PATTERN.sub('[REDACTED_SSN]', text)
        text = cls.EMAIL_PATTERN.sub('[REDACTED_EMAIL]', text)
        text = cls.PHONE_PATTERN.sub('[REDACTED_PHONE]', text)
        return text
