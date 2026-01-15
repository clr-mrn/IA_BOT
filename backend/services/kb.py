import json
import re
from pathlib import Path
from typing import Any, Optional

# Detecte: "6e", "6eme", "6ème", "dans le 6", "6e arrondissement"
_ARR_RE = re.compile(
    r"\b(1er|2e|3e|4e|5e|6e|7e|8e|9e)\b"
    r"|\b([1-9])\s*(?:eme|ème)\b"
    r"|\bdans\s+le\s+([1-9])\b",
    re.IGNORECASE,
)

def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def extract_arrondissement(text: str) -> Optional[str]:
    q = _norm(text)
    m = _ARR_RE.search(q)
    if not m:
        return None
    if m.group(1):  # "6e"
        return m.group(1).lower()
    if m.group(2):  # "6eme"/"6ème"
        return f"{m.group(2)}e"
    if m.group(3):  # "dans le 6"
        return f"{m.group(3)}e"
    return None


class KnowledgeBase:
    """
    KB basée sur backend/data/kb.json

    Supporte 2 formats:
    - {"places":[ {...}, {...} ]}
    - [ {...}, {...} ]  (liste directe)
    """

    def __init__(self, path: str = "backend/data/kb.json"):
        p = Path(path)
        raw = p.read_text(encoding="utf-8")
        loaded = json.loads(raw)

        # Robustesse: si le JSON est une LISTE -> on la met dans "places"
        if isinstance(loaded, list):
            self.places: list[dict[str, Any]] = loaded
        elif isinstance(loaded, dict):
            self.places = loaded.get("places", []) or []
        else:
            self.places = []

    def _infer_type(self, q: str) -> Optional[str]:
        q = _norm(q)
        if any(w in q for w in ["restaurant", "resto", "manger", "déjeuner", "dejeuner", "diner", "dîner", "brasserie", "bouchon"]):
            return "restaurant"
        if any(w in q for w in ["musée", "musee", "expo", "exposition", "galerie"]):
            return "museum"
        if any(w in q for w in ["parc", "jardin", "nature", "balade", "promenade"]):
            return "park"
        if any(w in q for w in ["patrimoine", "monument", "basilique", "cathédrale", "cathedrale", "vieux lyon", "fourvière", "fourviere"]):
            return "heritage"
        return None

    def search(self, message: str, limit: int = 8) -> dict[str, Any]:
        q = _norm(message)
        want_type = self._infer_type(q)
        want_arr = extract_arrondissement(q)  # ex: "6e"

        tokens = [t for t in q.split() if len(t) >= 3]
        scored: list[tuple[int, dict[str, Any]]] = []

        for p in self.places:
            p_type = _norm(str(p.get("type", "")))
            p_district = _norm(str(p.get("district", "")))

            # filtre
            if want_type and p_type != want_type:
                continue

            if want_arr:
                ok_arr = (
                    want_arr in p_district
                    or f"lyon {want_arr}" in p_district
                    or f"{want_arr} arrondissement" in p_district
                    or (want_arr == "6e" and "69006" in p_district)
                    or (want_arr == "5e" and "69005" in p_district)
                    or (want_arr == "4e" and "69004" in p_district)
                    or (want_arr == "3e" and "69003" in p_district)
                    or (want_arr == "2e" and "69002" in p_district)
                    or (want_arr == "1er" and "69001" in p_district)
                    or (want_arr == "7e" and "69007" in p_district)
                    or (want_arr == "8e" and "69008" in p_district)
                    or (want_arr == "9e" and "69009" in p_district)
                )
                if not ok_arr:
                    continue

            hay = _norm(" ".join([
                str(p.get("name", "")),
                str(p.get("district", "")),
                " ".join(p.get("themes", []) or []),
                str(p.get("short_description", "")),
            ]))

            score = 0
            if want_type and p_type == want_type:
                score += 2
            if want_arr and want_arr in p_district:
                score += 2
            for t in tokens:
                if t in hay:
                    score += 1

            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        items = [p for _, p in scored[:limit]]
        return {"items": items}
