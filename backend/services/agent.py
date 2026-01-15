import time
import re
from datetime import date, datetime, timedelta
from typing import Any

from backend.services.kb import KnowledgeBase
from backend.services.ollama import OllamaClient
from backend.services.mcp_client import MCPClient
from backend.services.toolcall import parse_tool_call_loose


SYSTEM_PROMPT = """
Tu es LYON-ASSIST, un agent conversationnel spécialisé dans le tourisme à Lyon.

Objectif
- Comprendre la question.
- Décider si tu réponds avec la KB/connaissances fournies ou si tu dois appeler un tool.
- N’appeler un tool que si c’est nécessaire pour répondre correctement.
- Analyser le résultat du tool (données structurées) et répondre clairement.

Tools disponibles
1) scrape_place(url): récupère les informations d’un lieu touristique précis.
2) scrape_category(query): récupère une liste de lieux correspondant à une recherche.
3) scrape_events(limit): récupère des événements à Lyon.

Schémas d'arguments (obligatoires)
- scrape_category: {"query": "<texte>", "limit": 5}
- scrape_place: {"url": "https://www.visiterlyon.com/..."}
- scrape_events: {"limit": 5}
N'utilise jamais d'autres noms de champs (ex: "categorie" est interdit).

Périmètre:
- Tu es spécialisé UNIQUEMENT sur Lyon.
- Si l’utilisateur demande une autre ville (ex: Paris), tu refuses poliment et tu proposes de revenir sur Lyon.
- Dans ce cas, tu n'appelles aucun tool.

Règles de décision
- Si l’utilisateur demande des infos précises sur un lieu (horaires, accès, prix, description officielle) ET que tu n’as pas ces infos dans la KB/contexte → utilise scrape_place.
- Si l’utilisateur demande “que faire”, “quoi visiter”, “idées”, “lieux à voir” → utilise scrape_category.
- Si l’utilisateur demande des événements (aujourd’hui, ce week-end, agenda, concerts, expos temporaires) → utilise scrape_events.
- Si tu peux répondre correctement avec la KB/contexte fourni → réponds directement sans tool.
- N’invente jamais de liens/URL : uniquement ceux fournis (KB ou tools).

Appels d’outils (format strict)
- Quand tu dois appeler un tool, tu réponds UNIQUEMENT avec un objet JSON (aucun texte autour) :
{
  "tool": "nom_du_tool",
  "args": { ... }
}

Réponse finale
- Réponds en français.
- Format naturel (comme un chatbot), pas de préfixe “Décision: …”.
- Si tu as utilisé un tool : utilise uniquement les items du tool, et ne génère pas de JSON.
- Si tu réponds avec la KB : cite uniquement des lieux présents dans KB_ITEMS.
"""


# Détection contexte

TOURISM_KEYWORDS = {
    # intention générale
    "visiter", "visite", "voir", "découvrir", "decouvrir", "faire", "sortir", "idées", "idees",
    "programme", "itinéraire", "itineraire", "plan", "conseil", "recommandation", "reco",
    "top", "meilleur", "incontournable", "must", "que faire", "quoi faire",

    # temps / planning
    "aujourd'hui", "aujourdhui", "demain", "ce soir", "ce midi", "cet après-midi", "cet apres midi",
    "ce week-end", "ce weekend", "week-end", "weekend", "cette semaine", "la semaine",
    "samedi", "dimanche", "matin", "après-midi", "apres-midi", "soir", "nuit",
    "2 jours", "deux jours", "3 jours", "trois jours",

    # culture / sorties
    "musée", "musee", "musées", "musees", "expo", "exposition", "expositions", "galerie",
    "théâtre", "theatre", "spectacle", "cinéma", "cinema", "opéra", "opera",
    "concert", "festival", "événement", "evenement", "événements", "evenements", "agenda",

    # manger / boire
    "restaurant", "resto", "bouchon", "brasserie", "bar", "pub", "café", "cafe", "terrasse",
    "manger", "bouffer", "déjeuner", "dejeuner", "dîner", "diner", "goûter", "gouter",
    "petit-déj", "petit dej", "petit déjeuner", "petit dejeuner",
    "menu", "carte", "réserver", "reserver", "apéro", "apero", "cocktail", "bière", "biere",
    "végétarien", "vegetarien", "vegan", "halal", "sans gluten",

    # balades / nature
    "balade", "promenade", "rando", "randonnée", "randonnee", "marche", "courir",
    "parc", "jardin", "forêt", "foret", "nature", "point de vue", "coucher de soleil",
    "quais", "berges", "rive", "pont",

    # shopping / loisirs
    "shopping", "boutique", "marché", "marche", "brocante", "vide-grenier", "vide grenier",
    "loisir", "activité", "activite", "escape game", "bowling", "patinoire",

    # patrimoine
    "patrimoine", "monument", "basilique", "cathédrale", "cathedrale", "église", "eglise",
    "place", "rue", "quartier", "traboule", "fourvière", "fourviere", "vieux-lyon", "vieux lyon",
    "histoire", "architecture",

    # infos variables
    "adresse", "horaires", "horaire", "ouverture", "ouvert", "fermé", "ferme",
    "tarif", "tarifs", "prix", "billet", "tickets", "réservation", "reservation",
}

# Lyon / quartiers
LYON_KEYWORDS = {
    "lyon", "grand lyon", "métropole", "metropole",
    "presqu'île", "presquile", "vieux-lyon", "vieux lyon", "croix-rousse", "croix rousse",
    "confluence", "part-dieu", "part dieu", "bellecour", "terreaux", "hotel de ville",
    "fourvière", "fourviere", "saône", "saone", "rhône", "rhone", "tête d'or", "tete d'or",
    "guillotière", "guillotiere", "brotteaux", "monplaisir", "gerland", "vaise", "perrache",
    "saint-jean", "saint paul", "saint-georges", "saint georges",
    "caluire", "villeurbanne", "oullins", "bron", "venissieux",
    "vaulx-en-velin", "vaulx", "decines", "meyzieu",
}

ARR_RE = re.compile(r"\b(1er|2e|3e|4e|5e|6e|7e|8e|9e)\b|\b([1-9])\s*(?:eme|ème)\b", re.IGNORECASE)

_CITY_HINT = re.compile(
    r"\b(?:a|à|au|aux|sur|dans)\s+([A-ZÉÈÊËÀÂÎÏÔÙÛÜÇ][A-Za-zÉÈÊËÀÂÎÏÔÙÛÜÇ\-']{2,})\b"
)

_DECISION_RE = re.compile(r"^\s*d[ée]cision\s*:\s*\w+\s*\n*", re.IGNORECASE)

_SMALL_TALK = re.compile(
    r"\b(salut|hello|hey|yo|coucou|bonsoir|bonjour|ça va|ca va|merci|mdr|ok|d'accord|super|nickel|parfait|bye|au revoir)\b",
    re.IGNORECASE
)


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _contains_any(needle_set: set[str], text: str) -> bool:
    return any(k in text for k in needle_set)


def _extract_city_hint(msg: str) -> str | None:
    m = _CITY_HINT.search(msg)
    if not m:
        return None
    return m.group(1).strip()


def _is_lyon(city: str) -> bool:
    return city.lower() == "lyon"


def _strip_decision_prefix(text: str) -> str:
    if not text:
        return ""
    return _DECISION_RE.sub("", text.strip()).strip()


def _looks_like_tool_json(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if not (t.startswith("{") and t.endswith("}")):
        return False
    return '"tool"' in t and '"args"' in t


def _needs_live_data(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in [
        "horaire", "horaires", "ouvert", "ouverture",
        "adresse", "où se trouve", "comment y aller", "accès", "acces",
        "tarif", "tarifs", "prix", "billet", "tickets",
        "événement", "evenement", "événements", "evenements", "agenda",
        "aujourd", "ce week", "ce weekend", "ce week-end", "demain"
    ])


def _is_small_talk(msg: str) -> bool:
    m = msg.strip().lower()
    if len(m) <= 20 and _SMALL_TALK.search(m):
        return True
    return m in {"salut", "bonjour", "bonsoir", "merci", "ok", "daccord", "d'accord", "hello", "bye"}


def _small_talk_answer(msg: str) -> str:
    m = msg.strip().lower()
    if "merci" in m:
        return "Avec plaisir."
    if any(w in m for w in ["salut", "bonjour", "bonsoir", "hello", "coucou", "hey"]):
        return "Salut ! Je peux t’aider à trouver des idées de sorties à Lyon. Tu veux plutôt musées, restaurants, parcs ou patrimoine ?"
    if any(w in m for w in ["bye", "au revoir"]):
        return "À bientôt ! Si tu reviens, dis-moi ce que tu veux faire à Lyon."
    return "Je suis là pour t’aider à trouver des activités à Lyon. Tu cherches quoi ?"


def _is_lyon_context(text: str) -> bool:
    return ("lyon" in text) or bool(ARR_RE.search(text)) or _contains_any(LYON_KEYWORDS, text)


def _is_tourism_request(text: str) -> bool:
    if _contains_any(TOURISM_KEYWORDS, text):
        return True
    if _is_lyon_context(text) and any(w in text for w in ["dans", "à", "au", "aux", "vers", "près", "proche"]):
        return True
    return False


# Events

def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def _filter_events_for_query(user_message: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    txt = user_message.lower()
    today = date.today()

    # demain
    if "demain" in txt:
        target = today + timedelta(days=1)
        return [it for it in items if _parse_iso_date(it.get("startDate")) == target]

    # aujourd'hui
    if "aujourd" in txt:
        return [it for it in items if _parse_iso_date(it.get("startDate")) == today]

    # ce week-end
    if "week-end" in txt or "weekend" in txt:
        d = today
        while d.weekday() != 5:  # samedi
            d += timedelta(days=1)
        saturday = d
        sunday = d + timedelta(days=1)
        out: list[dict[str, Any]] = []
        for it in items:
            sd = _parse_iso_date(it.get("startDate"))
            if sd and (sd == saturday or sd == sunday):
                out.append(it)
        return out

    return items


def _format_event_line(it: dict[str, Any]) -> str:
    title = it.get("title") or "Événement"
    url = it.get("url") or ""
    sd = it.get("startDate")
    loc = it.get("location")

    parts = [title]
    if sd:
        parts.append(sd)
    if loc:
        parts.append(loc)

    left = " — ".join(parts)
    return f"* {left} : {url}" if url else f"* {left}"


# Agent

class Agent:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.ollama = OllamaClient(base_url="http://localhost:11434", model="llama3.1:8b")
        self.mcp = MCPClient(base_url="http://localhost:8001")
        self.memory: dict[str, list[dict[str, str]]] = {}

    def _build_prompt(self, history: list[dict[str, str]], user_block: str) -> str:
        hist = history[-6:]
        hist_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in hist])
        return f"{hist_text}\nUSER: {user_block}\nASSISTANT:"

    async def run(self, conversation_id: str, user_message: str) -> dict[str, Any]:
        t0 = time.time()
        steps: list[str] = []
        sources: list[dict] = []
        history = self.memory.get(conversation_id, [])

        # 0) Small talk
        if _is_small_talk(user_message):
            answer = _small_talk_answer(user_message)
            history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
            self.memory[conversation_id] = history[-12:]
            return {
                "answer": answer,
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": ["small_talk"],
                    "errors": {},
                },
            }

        # 1) Scope ville
        city = _extract_city_hint(user_message)
        if city and not _is_lyon(city):
            answer = (
                f"Je suis spécialisé sur le tourisme à Lyon (données visiterlyon.com). "
                f"Je ne peux pas répondre de manière fiable pour {city}.\n\n"
                "Si tu veux, je peux te proposer des idées à Lyon (musées, activités, événements)."
            )
            return {
                "answer": answer,
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": ["scope_guardrail"],
                    "errors": {},
                },
            }

        # 2) Allowlist tourisme
        txt = _norm(user_message)
        if not _is_tourism_request(txt):
            answer = (
                "Je peux t’aider surtout pour organiser des sorties à Lyon "
                "(musées, restos, balades, patrimoine, événements). "
                "Tu cherches quoi ?"
            )
            history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
            self.memory[conversation_id] = history[-12:]
            return {
                "answer": answer,
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": ["allowlist_block"],
                    "errors": {},
                },
            }

        # 3) KB search
        steps.append("kb_search")
        kb_hits = self.kb.search(user_message)
        kb_items = kb_hits.get("items", []) or []
        have_kb_answer = len(kb_items) > 0
        need_live = _needs_live_data(user_message)

        # 3bis) Priorité KB si pas besoin d'info variable
        if have_kb_answer and not need_live:
            steps.append("kb_direct_answer")
            lines = ["Voici quelques idées :"]
            for it in kb_items[:8]:
                name = it.get("name") or it.get("title") or "Lieu"
                url = it.get("url")
                if url:
                    lines.append(f"* {name} : {url}")
                    sources.append({"type": "web", "url": url})
                else:
                    lines.append(f"* {name}")

            answer = _strip_decision_prefix("\n".join(lines))

            history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
            self.memory[conversation_id] = history[-12:]

            return {
                "answer": answer,
                "sources": sources,
                "trace": {
                    "kb_used": True,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": steps,
                    "errors": {},
                },
            }

        # 4) Résumé KB dans le prompt LLM (si besoin)
        kb_summary_parts: list[str] = []
        if kb_items:
            kb_summary_parts.append("KB_ITEMS (utilise uniquement ces items si tu cites un lieu) :")
            for it in kb_items[:8]:
                kb_summary_parts.append(
                    f"- name={it.get('name')} | type={it.get('type')} | district={it.get('district')} | url={it.get('url')}"
                )
        kb_summary = "\n".join(kb_summary_parts) if kb_summary_parts else "KB: aucun résultat."
        force_no_tool = have_kb_answer and (not need_live)

        # 5) PASS 1 LLM: tool-call ou réponse
        steps.append("llm_pass1")
        user_block_pass1 = f"""Message utilisateur: {user_message}

{kb_summary}

IMPORTANT:
- {"Tu DOIS répondre sans tool." if force_no_tool else "Tu peux appeler un tool uniquement si nécessaire."}
- Si tu appelles un tool, réponds UNIQUEMENT avec le JSON tool-call.
- Sinon, réponds directement (format naturel).
- Si tu réponds avec la KB: cite UNIQUEMENT des lieux présents dans KB_ITEMS.
- Ne crée jamais de lien : uniquement ceux fournis.
"""
        prompt1 = self._build_prompt(history, user_block_pass1)

        try:
            out1 = await self.ollama.generate(prompt=prompt1, system=SYSTEM_PROMPT)
        except Exception as e:
            return {
                "answer": "Désolé, le modèle IA est indisponible (Ollama).",
                "sources": [],
                "trace": {
                    "kb_used": have_kb_answer,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": steps + ["ollama_error_pass1"],
                    "errors": {"ollama_error": str(e)},
                },
            }

        if not out1 or not out1.strip():
            return {
                "answer": "Désolé, je n'ai pas réussi à générer une réponse.",
                "sources": [],
                "trace": {
                    "kb_used": have_kb_answer,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": steps + ["empty_llm_pass1"],
                    "errors": {},
                },
            }

        out1 = _strip_decision_prefix(out1)
        tool_call = parse_tool_call_loose(out1)

        if force_no_tool:
            tool_call = None

        if tool_call is None and _looks_like_tool_json(out1):
            out1 = "Je peux t’aider, mais j’ai besoin que tu précises un peu (type de lieu, quartier, ou ce que tu veux exactement)."

        # 6) Tool execution
        tool_called = None
        tool_payload: dict[str, Any] | None = None

        if tool_call:
            tool_called = tool_call["tool"]
            args = tool_call["args"]
            steps.append(f"tool_call:{tool_called}")

            if tool_called == "scrape_category":
                if "query" not in args and "categorie" in args:
                    args["query"] = args.pop("categorie")
                args.setdefault("limit", 8)

            if tool_called == "scrape_events":
                args.setdefault("limit", 20)

            try:
                tool_payload = await self.mcp.call_tool(tool_called, args)
            except Exception as e:
                tool_payload = {"error": str(e)}
                steps.append("tool_error")

            # --- Cas EVENTS : réponse directe sans LLM (plus fiable)
            if tool_called == "scrape_events" and isinstance(tool_payload, dict):
                items = tool_payload.get("items") or []
                if isinstance(items, list):
                    items = _filter_events_for_query(user_message, items)

                if not items:
                    answer = "Je n’ai trouvé aucun événement pour la période demandée."
                else:
                    lines = ["Voici les événements correspondants :"]
                    for it in items[:8]:
                        if isinstance(it, dict):
                            lines.append(_format_event_line(it))
                    answer = "\n".join(lines)

                answer = _strip_decision_prefix(answer)

                history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
                self.memory[conversation_id] = history[-12:]

                return {
                    "answer": answer,
                    "sources": [{"type": "web", "url": it["url"]} for it in items if isinstance(it, dict) and it.get("url")],
                    "trace": {
                        "kb_used": False,
                        "tool_called": "scrape_events",
                        "model": self.ollama.model,
                        "latency_ms": int((time.time() - t0) * 1000),
                        "steps": steps + ["events_direct_answer"],
                        "errors": {},
                    },
                }

            # Ajout sources depuis tool
            if isinstance(tool_payload, dict):
                for it in (tool_payload.get("items") or []):
                    if isinstance(it, dict) and it.get("url"):
                        sources.append({"type": "web", "url": it["url"]})
                if isinstance(tool_payload.get("item"), dict) and tool_payload["item"].get("url"):
                    sources.append({"type": "web", "url": tool_payload["item"]["url"]})

            steps.append("llm_pass2")
            user_block_pass2 = f"""Message utilisateur: {user_message}

{kb_summary}

Résultat du tool ({tool_called}) (JSON):
{tool_payload}

Tâche:
- Produis UNIQUEMENT la réponse finale pour l'utilisateur.
- NE PRODUIS AUCUN JSON.
- NE FAIS AUCUN appel de tool.
- Utilise UNIQUEMENT les éléments du tool_payload (items ou item).
- Ne crée jamais de liens : uniquement ceux fournis.
"""
            prompt2 = self._build_prompt(history, user_block_pass2)

            try:
                answer = await self.ollama.generate(prompt=prompt2, system=SYSTEM_PROMPT)
            except Exception as e:
                answer = "Le modèle IA est indisponible pour formuler la réponse. Réessaie dans un instant."
                steps.append("ollama_error_pass2")
                err2 = str(e)

        else:
            steps.append("final_from_pass1")
            answer = out1

        answer = _strip_decision_prefix(answer)

        # Update mémoire
        history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
        self.memory[conversation_id] = history[-12:]

        trace_errors: dict[str, str] = {}
        if isinstance(tool_payload, dict) and tool_payload.get("error"):
            trace_errors["tool_error"] = str(tool_payload.get("error"))
        if "err2" in locals():
            trace_errors["ollama_error"] = err2

        # Filtrer sources réellement citées dans answer
        used_urls = set()
        for s in sources:
            if s.get("type") == "web" and s.get("url") and s["url"] in answer:
                used_urls.add(s["url"])
        sources = [s for s in sources if s.get("type") != "web" or s.get("url") in used_urls]

        return {
            "answer": answer,
            "sources": sources,
            "trace": {
                "kb_used": have_kb_answer,
                "tool_called": tool_called,
                "model": self.ollama.model,
                "latency_ms": int((time.time() - t0) * 1000),
                "steps": steps,
                "errors": trace_errors,
            },
        }
