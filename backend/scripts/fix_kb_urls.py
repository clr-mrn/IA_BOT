import json
import time
import re
from pathlib import Path
from difflib import SequenceMatcher

import requests

MCP_BASE = "http://localhost:8001"
KB_PATH = Path("backend/data/kb.json")

ROOT_URLS = {
    "https://www.visiterlyon.com",
    "https://www.visiterlyon.com/",
}

def norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("’", "'")
    return s

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

def mcp_search(query: str, limit: int = 5) -> list[dict]:
    r = requests.post(
        f"{MCP_BASE}/tools/scrape_category",
        json={"query": query, "limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("items", []) or []

def best_match(place_name: str, candidates: list[dict]) -> dict | None:
    best = None
    best_score = 0.0
    for c in candidates:
        title = c.get("title") or ""
        score = similarity(place_name, title)
        if score > best_score:
            best_score = score
            best = c
    # seuil minimum pour éviter les liens hors sujet
    return best if best and best_score >= 0.55 else None

def load_places(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return obj.get("places", []) or []
    return []

def save_same_shape(original, places):
    if isinstance(original, list):
        return places
    if isinstance(original, dict):
        out = dict(original)
        out["places"] = places
        return out
    return {"places": places}

def main():
    raw = KB_PATH.read_text(encoding="utf-8")
    original = json.loads(raw)
    places = load_places(original)

    fixed = 0
    skipped = 0

    for i, p in enumerate(places):
        name = p.get("name") or p.get("title")
        if not name:
            skipped += 1
            continue

        url = (p.get("url") or "").strip()
        if url and url not in ROOT_URLS:
            skipped += 1
            continue

        try:
            candidates = mcp_search(name, limit=5)
            match = best_match(name, candidates)
            if match and match.get("url"):
                p["url"] = match["url"]
                fixed += 1
                print(f"[OK] {name} -> {p['url']}")
            else:
                # pas de bon match : on laisse vide plutôt que mettre la racine
                p["url"] = None
                print(f"[NO MATCH] {name}")
        except Exception as e:
            print(f"[ERR] {name}: {e}")
        time.sleep(0.25)  # petite pause pour éviter de spam

    out = save_same_shape(original, places)
    KB_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTerminé. fixed={fixed}, skipped={skipped}, total={len(places)}")

if __name__ == "__main__":
    main()
