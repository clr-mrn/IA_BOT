# mcp/tools.py
import sys
import time
import json
import re
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# (Optionnel) Fix UTF-8 pour affichage console Windows
# N'impacte pas FastAPI
# ----------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://www.visiterlyon.com"

# ----------------------------------------------------------------------
# Cache TTL simple (évite de rescraper en boucle)
# ----------------------------------------------------------------------
_CACHE: dict[str, tuple[float, str]] = {}  # url -> (timestamp, html)
CACHE_TTL_S = 300  # 5 minutes


def _cache_get(url: str) -> Optional[str]:
    val = _CACHE.get(url)
    if not val:
        return None
    ts, html = val
    if time.time() - ts > CACHE_TTL_S:
        _CACHE.pop(url, None)
        return None
    return html


def _cache_set(url: str, html: str) -> None:
    _CACHE[url] = (time.time(), html)


# ----------------------------------------------------------------------
# HTTP + soup
# ----------------------------------------------------------------------
def get_page_soup(url: str) -> Optional[BeautifulSoup]:
    headers = {
        "User-Agent": "Epitech-IA-Agent-Project/1.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    cached = _cache_get(url)
    if cached is not None:
        return BeautifulSoup(cached, "html.parser")

    try:
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()
        html = r.text
        _cache_set(url, html)
        return BeautifulSoup(html, "html.parser")
    except requests.Timeout:
        return None
    except requests.RequestException:
        return None


# ----------------------------------------------------------------------
# Helpers parsing
# ----------------------------------------------------------------------
def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _first_text(el: Any) -> Optional[str]:
    if not el:
        return None
    t = el.get_text(" ", strip=True)
    t = _clean_text(t)
    return t or None


def _extract_jsonld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.get_text(strip=True))
            if isinstance(data, dict):
                out.append(data)
            elif isinstance(data, list):
                out.extend([x for x in data if isinstance(x, dict)])
        except Exception:
            continue
    return out


def _extract_section_text(soup: BeautifulSoup, keywords: list[str]) -> Optional[str]:
    """
    Cherche une section par titre (h2/h3) contenant un mot-clé
    et récupère le texte qui suit.
    """
    for heading in soup.find_all(["h2", "h3"]):
        htxt = (_first_text(heading) or "").lower()
        if any(k in htxt for k in keywords):
            texts = []
            node = heading.find_next()
            steps = 0
            while node and steps < 12:
                if node.name in ["h2", "h3"]:
                    break
                t = _first_text(node)
                if t and len(t) > 2:
                    texts.append(t)
                node = node.find_next_sibling() or node.find_next()
                steps += 1

            joined = _clean_text(" ".join(texts))
            return joined if joined and len(joined) > 10 else None
    return None


# ----------------------------------------------------------------------
# Standard output shapes
# ----------------------------------------------------------------------
def _ok_items(source_url: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"ok": True, "source_url": source_url, "items": items, "error": None}


def _ok_item(source_url: str, item: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "source_url": source_url, "item": item, "error": None}


def _err_items(source_url: str, msg: str) -> dict[str, Any]:
    return {"ok": False, "source_url": source_url, "items": [], "error": msg}


def _err_item(source_url: str, msg: str) -> dict[str, Any]:
    return {"ok": False, "source_url": source_url, "item": None, "error": msg}


# ==============================================================================
# TOOL: scrape_category(query)
# ==============================================================================
def scrape_category(query: str, limit: int = 10) -> dict[str, Any]:
    """
    Recherche simple sur visiterlyon.com.
    Retour: {ok, source_url, items:[{title,url,type}], error}
    """
    source_url = f"{BASE}/app_search?simple_search%5BsearchText%5D={query}"
    search_url = f"{BASE}/app_search"
    params = {"simple_search[searchText]": query}

    headers = {
        "User-Agent": "Epitech-IA-Agent-Project/1.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    try:
        r = requests.get(search_url, headers=headers, params=params, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return _err_items(source_url, "Impossible de contacter le site pour la recherche.")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Heuristique: on garde les liens internes vers contenu
    for a in soup.select('a[href^="/"]'):
        href = a.get("href", "")
        if not href:
            continue

        if not ("/lieux-a-visiter/" in href or "/sortir/" in href):
            continue

        url = urljoin(BASE, href)
        if url in seen:
            continue

        title = _first_text(a.find(["h3", "h2"])) or _first_text(a) or ""
        title = title[:200]

        if not title or title.lower() in {"en savoir plus", "découvrir", "voir"}:
            continue

        typ = "place" if "/lieux-a-visiter/" in href else "activity"

        seen.add(url)
        items.append({"title": title, "url": url, "type": typ})

        if len(items) >= limit:
            break

    return _ok_items(source_url, items)


# ==============================================================================
# TOOL: scrape_place(url)
# ==============================================================================
def scrape_place(url: str) -> dict[str, Any]:
    """
    Extrait les détails pratiques d'un lieu.
    Retour: {ok, source_url, item:{...}, error}
    """
    if not url.startswith(BASE):
        return _err_item(url, "URL invalide. L'URL doit provenir de visiterlyon.com")

    soup = get_page_soup(url)
    if not soup:
        return _err_item(url, "Impossible de récupérer la page (timeout ou erreur réseau).")

    jsonld = _extract_jsonld(soup)

    item: dict[str, Any] = {"url": url}
    item["name"] = _first_text(soup.find("h1"))

    phone = soup.select_one('a[href^="tel:"]')
    item["phone"] = _first_text(phone)

    # Site externe (premier lien externe)
    website = None
    for a in soup.select('a[href^="http"]'):
        href = a.get("href", "")
        if href and "visiterlyon.com" not in href:
            website = href
            break
    item["website"] = website

    # Adresse
    address = _first_text(soup.find("address") or soup.select_one("[itemprop='address']"))

    if not address:
        for cand in soup.select("div, p, span"):
            txt = _first_text(cand)
            if not txt:
                continue
            if re.search(r"\b69\d{3}\b", txt) and ("lyon" in txt.lower()):
                address = txt
                break

    if not address:
        for obj in jsonld:
            addr = obj.get("address")
            if isinstance(addr, dict):
                parts = [addr.get("streetAddress"), addr.get("postalCode"), addr.get("addressLocality")]
                parts = [p for p in parts if isinstance(p, str) and p.strip()]
                if parts:
                    address = _clean_text(" ".join(parts))
                    break

    item["address"] = address

    # Horaires
    opening = None
    for obj in jsonld:
        oh = obj.get("openingHours")
        if isinstance(oh, (list, str)):
            opening = oh
            break
    if not opening:
        opening = _extract_section_text(soup, ["horaire", "horaires", "ouverture"])
    item["opening_hours"] = opening

    # Tarifs
    prices = None
    for obj in jsonld:
        offers = obj.get("offers")
        if isinstance(offers, dict):
            p = offers.get("price")
            if isinstance(p, (str, int, float)):
                prices = str(p)
                break
    if not prices:
        prices = _extract_section_text(soup, ["tarif", "tarifs", "prix", "billet", "tickets"])
    item["prices"] = prices

    # Description courte (meta description)
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        item["short_description"] = _clean_text(meta_desc["content"])

    return _ok_item(url, item)


# ==============================================================================
# TOOL: scrape_events(limit)
# ==============================================================================
def scrape_events(limit: int = 10) -> dict[str, Any]:
    """
    Récupère des événements de l'agenda.
    Retour: {ok, source_url, items:[{title,url,info_pratique}], error}
    """
    source_url = f"{BASE}/sortir/l-agenda/tous-les-evenements"
    soup = get_page_soup(source_url)
    if not soup:
        return _err_items(source_url, "Agenda inaccessible (timeout ou erreur réseau).")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Heuristique: liens qui ressemblent à des pages d'événements
    candidates = soup.select(
        'a[href*="/sortir/l-agenda/"], a[href*="/evenement"], a[href*="/evenements"]'
    )

    for a in candidates:
        href = a.get("href", "")
        if not href:
            continue

        url = urljoin(source_url, href)
        if url in seen:
            continue

        title = _first_text(a.find(["h2", "h3"])) or _first_text(a) or ""
        title = title[:220]
        if not title or len(title) < 4:
            continue

        info = None
        parent = a.find_parent(["article", "li", "div"])
        if parent:
            txt = _first_text(parent)
            if txt and txt != title and len(txt) < 500:
                info = txt

        seen.add(url)
        items.append({"title": title, "url": url, "info_pratique": info})

        if len(items) >= limit:
            break

    # Fallback si la page change
    if not items:
        for a in soup.select('a[href^="/"]'):
            href = a.get("href", "")
            if "/agenda" not in href and "even" not in href:
                continue
            url = urljoin(BASE, href)
            if url in seen:
                continue
            title = _first_text(a) or ""
            if len(title) < 6:
                continue
            seen.add(url)
            items.append({"title": title[:220], "url": url, "info_pratique": None})
            if len(items) >= limit:
                break

    return _ok_items(source_url, items)
