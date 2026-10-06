import pytest
from emergency.gate import EmergencyGate, EmergencyRulesError


def test_emergency_gate_match():
    hit = EmergencyGate().evaluate("My brother was arrested by police")
    assert hit is not None
    assert hit["category"] == "arrest_custody"
    assert hit["helplines"] and hit["rights"]


def test_emergency_gate_no_false_positive():
    assert EmergencyGate().evaluate("What is the process to issue a cheque notice?") is None


def test_hindi_keyword_with_trailing_text():
    assert EmergencyGate().evaluate("मेरे भाई को पुलिस ने गिरफ्तार कर लिया")["category"] == "arrest_custody"


def test_domestic_violence_category():
    assert EmergencyGate().evaluate("my husband beats me every night")["category"] == "domestic_violence"


def test_word_boundary():
    assert EmergencyGate().evaluate("the arrestee list") is None


def test_missing_rules_file_fails_loudly(tmp_path):
    with pytest.raises(EmergencyRulesError):
        EmergencyGate(tmp_path / "nope.yaml")
