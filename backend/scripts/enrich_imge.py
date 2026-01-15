import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# chemins RELATIFS à backend/scripts/
KB_IN = Path(__file__).resolve().parent.parent / "data" / "kb.json"
KB_OUT = Path(__file__).resolve().parent.parent / "data" / "kb_with_images.json"


HEADERS = {
    "User-Agent": "Epitech-IA-Agent-Project/1.0",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

TIMEOUT = 15
SLEEP_S = 0.4  # évite de spammer le site


def _abs_url(base: str, maybe_rel: str | None) -> str | None:
    if not maybe_rel:
        return None
    return urljoin(base, maybe_rel)


def extract_main_image(page_url: str) -> str | None:
    """
    Stratégie (ordre):
    1) meta[property="og:image"]
    2) meta[name="twitter:image"]
    3) link[rel="image_src"]
    4) première image "grande" trouvée dans le contenu
    """
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 1) og:image
    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        return _abs_url(page_url, og["content"])

    # 2) twitter:image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return _abs_url(page_url, tw["content"])

    # 3) rel image_src
    img_src = soup.find("link", attrs={"rel": "image_src"})
    if img_src and img_src.get("href"):
        return _abs_url(page_url, img_src["href"])

    # 4) fallback : première <img> qui ressemble à une vraie image
    # (on évite logos/icônes trop petits en filtrant un peu)
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy")
        if not src:
            continue

        src_abs = _abs_url(page_url, src)
        if not src_abs:
            continue

        # filtre simple : ignore svg, favicons, petites icônes
        low = src_abs.lower()
        if low.endswith(".svg"):
            continue
        if any(x in low for x in ["logo", "icon", "sprite", "favicon"]):
            continue

        return src_abs

    return None


def main():
    data = json.loads(KB_IN.read_text(encoding="utf-8"))

    # ta KB peut être soit {"places":[...]} soit directement une liste
    if isinstance(data, dict):
        places = data.get("places", [])
    elif isinstance(data, list):
        places = data
        data = {"places": places}
    else:
        raise ValueError("Format KB inattendu")

    total = len(places)
    ok = 0

    for i, p in enumerate(places, start=1):
        url = p.get("url")
        if not url or not isinstance(url, str):
            p["image_url"] = None
            continue

        img = extract_main_image(url)
        p["image_url"] = img
        if img:
            ok += 1

        print(f"[{i}/{total}] {p.get('name','(no name)')[:40]} -> {img}")
        time.sleep(SLEEP_S)

    KB_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. images trouvées: {ok}/{total}")
    print(f"Sortie: {KB_OUT}")


if __name__ == "__main__":
    main()
