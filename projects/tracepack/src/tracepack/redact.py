from __future__ import annotations

import re
from typing import Any

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


def contains_sensitive_value(value: Any) -> bool:
    if isinstance(value, str):
        return contains_sensitive_text(value)
    if isinstance(value, dict):
        return any(contains_sensitive_value(key) or contains_sensitive_value(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_sensitive_value(item) for item in value)
    if isinstance(value, tuple):
        return any(contains_sensitive_value(item) for item in value)
    return contains_sensitive_text(str(value)) if value is not None else False


def redact_value(value: Any) -> tuple[Any, bool]:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        changed = False
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            redacted_key, key_changed = redact_value(key)
            redacted_item, item_changed = redact_value(item)
            redacted[redacted_key] = redacted_item
            changed = changed or key_changed or item_changed
        return redacted, changed
    if isinstance(value, list):
        changed = False
        items = []
        for item in value:
            redacted_item, item_changed = redact_value(item)
            items.append(redacted_item)
            changed = changed or item_changed
        return items, changed
    if isinstance(value, tuple):
        changed = False
        items = []
        for item in value:
            redacted_item, item_changed = redact_value(item)
            items.append(redacted_item)
            changed = changed or item_changed
        return tuple(items), changed
    return value, False
