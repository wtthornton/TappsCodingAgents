"""
I/O guardrails: sanitization and optional prompt-injection heuristics (plan 2.2).

Use sanitize_for_log when logging user-provided strings to audit/event logs.
"""

from __future__ import annotations

import re


def sanitize_for_log(s: str, max_len: int = 500) -> str:
    """
    Sanitize a string for safe logging: truncate and strip control characters.

    Use in audit_log, event_log, and similar when logging user-provided content.

    Args:
        s: Raw string (e.g. user input, error message)
        max_len: Maximum length (default 500)

    Returns:
        Sanitized string safe for logs
    """
    if not isinstance(s, str):
        s = str(s)
    # Strip ASCII control characters (0x00-0x1f except tab/newline) and C1 (0x80-0x9f)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", s)
    s = s.strip()
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s


def detect_likely_prompt_injection(prefix: str, user_input: str) -> bool:
    """
    Heuristic to detect likely prompt-injection patterns. Optional; implement
    after sanitize_for_log and path allowlist. When used: log a warning only,
    do not block.

    Args:
        prefix: System/context prefix (e.g. instruction)
        user_input: User-supplied string

    Returns:
        True if the combination looks like a potential prompt injection
    """
    if not user_input or not isinstance(user_input, str):
        return False
    u = user_input.strip().lower()
    # Simple heuristics: ignore / override / system-style instructions
    patterns = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|above)",
        r"you\s+are\s+now\s+",
        r"new\s+instructions?\s*:",
        r"system\s*:\s*",
        r"\[INST\]",
        r"<\|im_start\|>",
        r"human\s*:\s*.*\s*assistant\s*:",
        r"pretend\s+you\s+are",
        r"act\s+as\s+if\s+you",
        r"output\s+(only|just)\s+",
        r"respond\s+only\s+with\s+",
    ]
    for p in patterns:
        if re.search(p, u, re.IGNORECASE | re.DOTALL):
            return True
    return False
