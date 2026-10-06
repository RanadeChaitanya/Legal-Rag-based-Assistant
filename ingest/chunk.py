from typing import Any, Dict, List

from ingest.clean import clean_for_embedding


def create_structured_chunk(
    doc_id: str,
    ref: str,
    hierarchy_path: List[str],
    heading: str,
    text_raw: str,
    applies: str = "current",
    authority: str = "A1",
    part_index: int = 0,
    verified: bool = False,
) -> Dict[str, Any]:
    """
    Constructs a dual-representation chunk payload for ingestion.

    `applies`: pass "post-2024-07-01" for BNS/BNSS/BSA, "current" for older Acts still in force.
    `verified`: set True only after validate_corpus confirms the text against the official source.
    """
    text_clean = clean_for_embedding(text_raw)
    prefix_parts = [doc_id, " > ".join(p for p in hierarchy_path if p), heading]
    prefix = " | ".join(p for p in prefix_parts if p)

    return {
        "chunk_id": f"{ref}#{part_index}",
        "ref": ref,
        "doc_type": "act",
        "authority": authority,
        "act_alias": doc_id,
        "path": hierarchy_path,
        "heading": heading,
        "text": text_clean,
        "text_raw": text_raw,
        "embedding_text": f"{prefix} | {text_clean}",
        "parent_text": text_raw,
        "applies": applies,
        "jurisdiction": "IN",
        "verified": verified,
    }
