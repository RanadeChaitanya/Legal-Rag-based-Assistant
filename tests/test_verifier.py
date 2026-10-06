import pytest
from server.verifier import GroundingVerifier, build_abstain_response

RAW = ("No police officer shall detain in custody a person arrested without warrant "
       "for a longer period than twenty-four hours.")
CHUNKS = [{"chunk_id": "bnss:sec_58#0", "ref": "bnss:sec_58", "text_raw": RAW}]


def _sec(quote="twenty-four hours", ref="bnss:sec_58", chunk_id="bnss:sec_58#0",
         content="Detention is capped."):
    return [{"heading": "Rights", "content": content,
             "citations": [{"chunk_id": chunk_id, "ref": ref, "quote": quote}]}]


def test_verifier_pass():
    assert GroundingVerifier(CHUNKS).verify_quote("bnss:sec_58#0", "twenty-four hours") is True


def test_verifier_fail_modified_quote():
    assert GroundingVerifier(CHUNKS).verify_quote("bnss:sec_58#0", "forty-eight hours") is False


def test_verifier_fail_missing_chunk():
    assert GroundingVerifier([]).verify_quote("bnss:sec_99#0", "some text") is False


def test_empty_and_none_quote_rejected():
    v = GroundingVerifier(CHUNKS)
    assert v.verify_quote("bnss:sec_58#0", "") is False
    assert v.verify_quote("bnss:sec_58#0", None) is False


def test_answer_passes_all_points():
    assert GroundingVerifier(CHUNKS).verify_answer(_sec()).ok


def test_answer_without_citations_fails():
    res = GroundingVerifier(CHUNKS).verify_answer([{"heading": "x", "content": "claim", "citations": []}])
    assert not res and "no citations" in res.failures[0]


def test_ref_mismatch_fails():
    assert not GroundingVerifier(CHUNKS).verify_answer(_sec(ref="bnss:sec_57"))


def test_short_quote_fails_warrant():
    assert not GroundingVerifier(CHUNKS).verify_answer(_sec(quote="hours"))


def test_repealed_chunk_fails():
    chunks = [dict(CHUNKS[0], repealed_by="x")]
    assert not GroundingVerifier(chunks).verify_answer(_sec())


def test_unsupported_number_fails_and_supported_passes():
    v = GroundingVerifier(CHUNKS)
    assert not v.verify_answer(_sec(content="You must be released within 48 hours."))
    assert v.verify_answer(_sec(content="You must be produced within 24 hours."))  # words in cited text
    assert v.verify_answer(_sec(content="You have 15 days left."), {"deadline": "15 days"})


def test_abstain_response_shape():
    r = build_abstain_response(CHUNKS, "disc")
    assert r["status"] == "abstained" and r["disclaimer"] == "disc"
    assert RAW[:30] in r["sections"][0]["content"]
