import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MIN_QUOTE_CHARS = 10
MIN_QUOTE_WORDS = 2

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_QUOTE_MAP = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                            "\u2013": "-", "\u2014": "-", "\u00a0": " "})
_NUM_UNIT = re.compile(r"(\d+)\s*-?\s*(?:hours?|days?|months?|years?)", re.IGNORECASE)


def _normalize(text: str) -> str:
    """Whitespace, quote and dash normalisation only. Case is preserved on purpose."""
    text = unicodedata.normalize("NFKC", text or "").translate(_QUOTE_MAP)
    return re.sub(r"\s+", " ", text).strip()


def _number_words(n: int) -> List[str]:
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        t, o = divmod(n, 10)
        return [_TENS[t]] if o == 0 else [f"{_TENS[t]}-{_ONES[o]}", f"{_TENS[t]} {_ONES[o]}"]
    return []


@dataclass
class VerificationResult:
    ok: bool
    failures: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


class GroundingVerifier:
    """
    5-Point Citation Warrant & Quote Verifier (Fail-Closed).
      1. Existence      - cited chunk_id was in the evidence set.
      2. Verbatim quote - quote is a substring of that chunk's text_raw.
      3. Identity       - citation ref matches the chunk's own ref.
      4. Warrant        - quote is substantive and the chunk is not repealed/superseded.
      5. Numbers        - day/hour/month/year figures are backed by timelines or cited text.
    Additionally every section must carry at least one citation.
    """

    def __init__(self, evidence_chunks: List[Dict[str, Any]]):
        self.evidence_map = {c["chunk_id"]: c for c in evidence_chunks}

    def verify_quote(self, chunk_id: str, quote: Optional[str]) -> bool:
        """Point 2: verbatim quote existence inside raw text (whitespace/quote-char normalised)."""
        if chunk_id not in self.evidence_map or not isinstance(quote, str):
            return False
        norm_quote = _normalize(quote)
        if not norm_quote:  # "" is a substring of everything; never accept it
            return False
        norm_raw = _normalize(self.evidence_map[chunk_id].get("text_raw", ""))
        return norm_quote in norm_raw

    def _number_supported(self, n_str: str, timeline_text: str, cited_raw: str) -> bool:
        if re.search(rf"(?<!\d){re.escape(n_str)}(?!\d)", timeline_text):
            return True
        if re.search(rf"(?<!\d){re.escape(n_str)}(?!\d)", cited_raw):
            return True
        lowered = cited_raw.lower()
        return any(w in lowered for w in _number_words(int(n_str)))

    def verify_answer(self, sections: List[Dict[str, Any]],
                      computed_timelines: Optional[Dict[str, Any]] = None) -> VerificationResult:
        failures: List[str] = []
        timeline_text = str(computed_timelines or {})

        if not sections:
            return VerificationResult(False, ["no_sections"])

        for i, sec in enumerate(sections):
            citations = sec.get("citations") or []
            if not citations:
                failures.append(f"section[{i}]: no citations")
            cited_raw_parts: List[str] = []

            for cit in citations:
                chunk_id = cit.get("chunk_id")
                quote = cit.get("quote")
                chunk = self.evidence_map.get(chunk_id)

                # Point 1
                if chunk is None:
                    failures.append(f"section[{i}]: unknown chunk_id {chunk_id!r}")
                    continue
                cited_raw_parts.append(chunk.get("text_raw", ""))

                # Point 2
                if not self.verify_quote(chunk_id, quote):
                    failures.append(f"section[{i}]: quote not verbatim in {chunk_id}")

                # Point 3
                if not cit.get("ref") or cit.get("ref") != chunk.get("ref"):
                    failures.append(f"section[{i}]: ref mismatch for {chunk_id}")

                # Point 4
                nq = _normalize(quote or "")
                if len(nq) < MIN_QUOTE_CHARS or len(nq.split()) < MIN_QUOTE_WORDS:
                    failures.append(f"section[{i}]: quote too short to warrant claim ({chunk_id})")
                if chunk.get("repealed_by") or chunk.get("applies") == "superseded":
                    failures.append(f"section[{i}]: {chunk_id} is repealed/superseded")

            # Point 5
            cited_raw = " ".join(cited_raw_parts)
            for m in _NUM_UNIT.finditer(sec.get("content") or ""):
                if not self._number_supported(m.group(1), timeline_text, cited_raw):
                    failures.append(f"section[{i}]: unsupported figure {m.group(0)!r}")

        return VerificationResult(not failures, failures)


def build_abstain_response(evidence_chunks: List[Dict[str, Any]], disclaimer: str,
                           failures: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generates a safe fail-closed abstain response displaying raw statutory text.
    `failures` is accepted for logging by the caller and is deliberately not shown to the user.
    """
    raw_provisions = []
    for c in evidence_chunks[:3]:
        text = (c.get("text_raw") or "")[:1500]
        raw_provisions.append(f"\u2022 {c.get('ref')}: {text}")

    body = "The system could not verify the generated summary against the source text."
    if raw_provisions:
        body += " Below is the verbatim statute text for reference:\n\n" + "\n\n".join(raw_provisions)

    return {
        "status": "abstained",
        "case_type": "general_statute",
        "sections": [
            {
                "heading": "NOTICE: ANSWER COULD NOT BE VERIFIED",
                "content": body,
                "citations": [],
            }
        ],
        "computed_timelines": {},
        "missing_slots": [],
        "rights": [],
        "helplines": [
            {"name": "NALSA Free Legal Aid", "number": "15100"},
            {"name": "National Emergency", "number": "112"},
        ],
        "disclaimer": disclaimer,
    }
