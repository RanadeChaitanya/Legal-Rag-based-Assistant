import re
import unicodedata
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple

EMERGENCY_YAML_PATH = Path(__file__).parent / "emergency.yaml"


class EmergencyRulesError(RuntimeError):
    """Raised when the offline emergency rules cannot be loaded (fail loudly, never silently)."""


def _normalize(text: str) -> str:
    """NFKC-normalise, casefold and collapse whitespace so matching is stable across scripts."""
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return re.sub(r"\s+", " ", text).strip()


class EmergencyGate:
    """
    Zero-network local matcher that evaluates incoming queries against offline emergency rules.
    """

    def __init__(self, yaml_path: Path = EMERGENCY_YAML_PATH):
        self.rules = self._load_rules(Path(yaml_path))
        self._patterns: List[Tuple[str, str, Pattern[str]]] = self._compile(self.rules)

    @staticmethod
    def _load_rules(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise EmergencyRulesError(f"Emergency rules file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data.get("emergencies"), dict) or not data["emergencies"]:
            raise EmergencyRulesError(f"No 'emergencies' defined in {path}")
        return data

    @staticmethod
    def _compile(rules: Dict[str, Any]) -> List[Tuple[str, str, Pattern[str]]]:
        compiled = []
        for category_id, data in rules["emergencies"].items():
            for kw in data.get("keywords", []):
                tokens = _normalize(kw).split(" ")
                body = r"\s+".join(re.escape(t) for t in tokens if t)
                # Lookarounds instead of \b: \b misbehaves after Devanagari vowel signs (matras).
                compiled.append((category_id, kw, re.compile(r"(?<!\w)" + body + r"(?!\w)")))
        return compiled

    def evaluate(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = _normalize(text)
        for category_id, kw, pattern in self._patterns:
            if pattern.search(text_clean):
                data = self.rules["emergencies"][category_id]
                return {
                    "category": category_id,
                    "title": data.get("title", category_id),
                    "matched_keyword": kw,
                    "rights": data.get("rights", []),
                    "helplines": data.get("helplines", []),
                }
        return None
