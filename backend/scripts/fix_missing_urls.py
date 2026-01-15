import json
from pathlib import Path

DEFAULT_URL = "https://www.visiterlyon.com/"
KB_PATH = Path("backend/data/kb_with_images.json")


def main():
    if not KB_PATH.exists():
        raise FileNotFoundError(f"KB introuvable : {KB_PATH}")

    data = json.loads(KB_PATH.read_text(encoding="utf-8"))

    # Cas 1 : kb.json = liste directe
    if isinstance(data, list):
        places = data
    # Cas 2 : kb.json = {"places": [...]}
    elif isinstance(data, dict):
        places = data.get("places", [])
    else:
        raise ValueError("Format de kb.json non reconnu")

    fixed = 0

    for place in places:
        url = place.get("url")
        if not url or not isinstance(url, str) or not url.strip():
            place["url"] = DEFAULT_URL
            fixed += 1

    KB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ URLs ajoutées par défaut : {fixed}")


if __name__ == "__main__":
    main()
