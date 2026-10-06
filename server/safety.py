import re
from typing import Any, Dict, List

_PHONE = re.compile(r"(?<!\d)(?:(?:\+?91|0)[\-\s]?)?[6-9]\d{9}(?!\d)")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
_AADHAAR = re.compile(r"(?<!\d)[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)")


def redact_pii(text: str) -> str:
    """
    Redacts phone numbers, email addresses, and Indian identity numbers (PAN/Aadhaar patterns).
    Note: long digit strings (e.g. 10+ digit account numbers) may also be redacted; this is intentional.
    """
    if not text:
        return ""
    redacted = _PHONE.sub("[PHONE REDACTED]", text)
    redacted = _EMAIL.sub("[EMAIL REDACTED]", redacted)
    redacted = _PAN.sub("[PAN REDACTED]", redacted)
    redacted = _AADHAAR.sub("[AADHAAR REDACTED]", redacted)
    return redacted


def _defang(text: str) -> str:
    """Prevent evidence text from forging our fence delimiters."""
    return (text or "").replace("===", "= = =")


def fence_evidence(chunks: List[Dict[str, Any]]) -> str:
    """
    Fences retrieved legal chunks into sandboxed blocks to prevent prompt injection.
    The generation prompt must state that text inside these blocks is data, never instructions.
    """
    formatted = []
    for idx, c in enumerate(chunks, 1):
        formatted.append(
            f"=== EVIDENCE CHUNK [{idx}] (ID: {_defang(str(c.get('chunk_id')))}) ===\n"
            f"REF: {_defang(str(c.get('ref')))}\n"
            f"TEXT: {_defang(c.get('text_raw', ''))}\n"
            f"=== END CHUNK [{idx}] ==="
        )
    return "\n\n".join(formatted)
