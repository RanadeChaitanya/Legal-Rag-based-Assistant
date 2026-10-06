import re
import unicodedata


def clean_for_embedding(text_raw: str) -> str:
    """
    Cleans text formatting noise for embedding generation.
    CRITICAL: Does NOT touch or alter the original text_raw string,
    preserving exact substring matching for the verifier.
    """
    if not text_raw:
        return ""
    cleaned = unicodedata.normalize("NFC", text_raw)
    # Strip orphan amendment brackets and omission asterisks (incl. spaced "* * *")
    cleaned = re.sub(r"[\[\]]|(?:\*\s*){3,}", " ", cleaned)
    # Collapse run-together whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
