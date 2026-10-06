import re
from pathlib import Path
import yaml
from cli.render import render_response, emergency_hit_to_response
from emergency.gate import EmergencyGate

ROOT = Path(__file__).resolve().parent.parent
REF = re.compile(r"^[a-z]+:(sec|art)_[0-9A-Za-z]+$")


def test_case_type_schemas_valid():
    files = list((ROOT / "schemas" / "case_types").glob("*.yaml"))
    assert len(files) == 4
    for f in files:
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        assert d["case_type"] == f.stem
        ids = [s["id"] for s in d["slots"]]
        assert len(ids) == len(set(ids))
        assert all(REF.match(p["ref"]) for p in d["pinned_provisions"])


def test_24_hour_rule_pinned_to_sec_58():
    d = yaml.safe_load((ROOT / "schemas/case_types/arrest_rights.yaml").read_text(encoding="utf-8"))
    titles = {p["ref"]: p["title"] for p in d["pinned_provisions"]}
    assert "twenty-four" in titles["bnss:sec_58"]


def test_render_survives_markup_like_text(capsys):
    hit = EmergencyGate().evaluate("he was arrested")
    render_response(emergency_hit_to_response(hit, "disc [/dim]"))
    render_response({"status": "answered", "disclaimer": "d",
                     "sections": [{"heading": "[bold]H", "content": "text [/red] [x]",
                                   "citations": [{"ref": "r", "quote": "q [y]"}]}]})
    out = capsys.readouterr().out
    assert "112" in out and "text [/red] [x]" in out
