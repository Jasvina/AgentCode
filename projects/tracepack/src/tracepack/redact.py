from __future__ import annotations

import re

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TOKEN_RE = re.compile(r"\b(?:sk|ghp)_[A-Za-z0-9]+\b")
INVOICE_RE = re.compile(r"\bINV-[A-Za-z0-9-]+\b")


def contains_sensitive_text(text: str) -> bool:
    return bool(EMAIL_RE.search(text) or TOKEN_RE.search(text) or INVOICE_RE.search(text))


def redact_text(text: str) -> tuple[str, bool]:
    redacted = text
    changed = False
    for pattern, replacement in [
        (EMAIL_RE, "[REDACTED_EMAIL]"),
        (TOKEN_RE, "[REDACTED_TOKEN]"),
        (INVOICE_RE, "[REDACTED_ID]"),
    ]:
        new_text = pattern.sub(replacement, redacted)
        if new_text != redacted:
            changed = True
            redacted = new_text
    return redacted, changed
