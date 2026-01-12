import json
from pathlib import Path
from typing import Any

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "kb.json"

class KnowledgeBase:
    def __init__(self, path: Path = KB_PATH):
        self.path = path
        self.data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def search(self, text: str) -> dict:
        """Retourne des 'hits' KB simples, pour guider la réponse ou éviter un tool."""
        t = text.lower()
        hits = {"districts": [], "rules": []}

        for d in self.data.get("districts", []):
            if any(k.lower() in t for k in d.get("keywords", [])) or d.get("name", "").lower() in t:
                hits["districts"].append(d)

        for r in self.data.get("rules", []):
            if any(k.lower() in t for k in r.get("if_keywords", [])):
                hits["rules"].append(r)

        return hits
