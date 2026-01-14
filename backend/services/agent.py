import time
import re
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
2) scrape_category(url): récupère une liste de lieux d’une catégorie.
3) scrape_events(args): récupère des événements à Lyon (ex: date, thème, limite).

Schémas d'arguments (obligatoires)
- scrape_category: {"query": "<texte>", "limit": 5}
- scrape_place: {"url": "https://www.visiterlyon.com/..."}
- scrape_events: {"limit": 5}
N'utilise jamais d'autres noms de champs (ex: "categorie" est interdit).

Périmètre:
- Tu ne dois répondre qu'aux questions qui concernent les restaurants, musées, parcs et patrimoines. Si la question n'est pas sur ces sujets tu dois recentrer la conversation, et préciser les sujets sur les quels tu peux appoerter une réponse pertinente.
- Tu es spécialisé UNIQUEMENT sur Lyon.
- Si l’utilisateur demande une autre ville (ex: Paris), tu refuses poliment et tu proposes de revenir sur Lyon.
- Dans ce cas, tu n'appelles aucun tool.

Règles de décision (obligatoires)
- Si l’utilisateur demande des infos précises sur un lieu (horaires, accès, prix, description officielle) ET que tu n’as pas ces infos dans la KB/contexte → utilise scrape_place.
- Si l’utilisateur demande “que faire”, “quoi visiter”, “idées d’activités”, “lieux à voir” (sans date précise) → utilise scrape_category.
- Si l’utilisateur demande des événements (aujourd’hui, ce week-end, dates, agenda, concerts, expos temporaires) → utilise scrape_events.
- Si tu peux répondre correctement avec la KB/contexte fourni → réponds directement sans tool.
- Ne fais jamais d’hypothèses : si une info n’est pas certaine, dis-le.
- N’invente jamais de liens/URL, ni de noms de sites. Les liens ne doivent venir que des résultats tool ou des sources fournies dans le contexte.

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
- Ne crée jamais de liens : uniquement ceux fournis (KB ou tools).
"""

# --- mots-clés "tourisme / sortie" (large)
TOURISM_KEYWORDS = {
    # intention générale
    "visiter", "visite", "voir", "découvrir", "decouvrir", "faire", "sortir", "idées", "idees",
    "programme", "itinéraire", "itineraire", "plan", "conseil", "recommandation", "reco",
    "top", "meilleur", "incontournable", "must", "que faire", "quoi faire",

    # temps / planning
    "aujourd'hui", "aujourdhui", "demain", "ce soir", "ce midi", "cet après-midi", "cet apres midi",
    "ce week-end", "ce weekend", "week-end", "weekend", "cette semaine", "la semaine", "samedi", "dimanche",
    "matin", "après-midi", "apres-midi", "soir", "nuit", "2 jours", "deux jours", "3 jours", "trois jours",

    # catégories culture
    "musée", "musee", "musées", "musees", "expo", "exposition", "expositions", "galerie",
    "théâtre", "theatre", "spectacle", "cinéma", "cinema", "opéra", "opera",
    "concert", "festival", "événement", "evenement", "événements", "evenements", "agenda",

    # manger / boire
    "restaurant", "resto", "bouchon", "brasserie", "bar", "pub", "café", "cafe", "terrasse",
    "manger", "bouffer", "déjeuner", "dejeuner", "dîner", "diner", "goûter", "gouter",
    "petit-dej", "petit dej", "petit déjeuner", "petit dejeuner",
    "menu", "carte", "réserver", "reserver", "apéro", "apero", "cocktail", "bière", "biere",
    "végétarien", "vegetarien", "vegan", "halal", "sans gluten",

    # balades / nature
    "balade", "promenade", "rando", "randonnée", "randonnee", "marche", "courir",
    "parc", "jardin", "forêt", "foret", "nature", "point de vue", "coucher de soleil",
    "quais", "berges", "rive", "pont",

    # shopping / loisirs
    "shopping", "boutique", "marché", "marche", "brocante", "vide-grenier", "vide grenier",
    "loisir", "activité", "activite", "escape game", "bowling", "patinoire",

    # patrimoine / architecture
    "patrimoine", "monument", "basilique", "cathédrale", "cathedrale", "église", "eglise",
    "place", "rue", "quartier", "traboule", "fourvière", "fourviere", "vieux-lyon", "vieux lyon",
    "histoire", "architecture",

    # transport / accès (utile même si tu ne scrapes pas)
    "y aller", "comment aller", "accès", "acces", "transport", "métro", "metro", "tram", "bus",
    "vélo", "velo", "parking",

    # infos variables (déclenchement tool éventuel)
    "adresse", "horaires", "horaire", "ouverture", "ouvert", "fermé", "ferme",
    "tarif", "tarifs", "prix", "billet", "tickets", "réservation", "reservation"
}

# --- mots-clés "Lyon / zones" (large)
LYON_KEYWORDS = {
    "lyon", "grand lyon", "métropole", "metropole",

    # quartiers / lieux connus
    "presqu'île", "presquile", "vieux-lyon", "vieux lyon", "croix-rousse", "croix rousse",
    "confluence", "part-dieu", "part dieu", "bellecour", "terreaux", "hotel de ville",
    "fourvière", "fourviere", "saône", "saone", "rhône", "rhone", "tête d'or", "tete d'or",
    "guillotière", "guillotiere", "brotteaux", "monplaisir", "gerland", "vaise", "perrache",
    "saint-jean", "saint paul", "saint-georges", "saint georges", "caluire", "villeurbanne",
    "oullins", "bron", "venissieux", "vaulx-en-velin", "vaulx", "decines", "meyzieu",

    # grandes institutions (tu peux en ajouter)
    "musée des confluences", "musee des confluences",
    "musée des beaux-arts", "musee des beaux-arts",
    "parc de la tête d'or", "parc tete d'or",
}

# regexs utiles
ARR_RE = re.compile(r"\b(1er|2e|3e|4e|5e|6e|7e|8e|9e)\b|\b([1-9])\s*(?:eme|ème)\b", re.IGNORECASE)
DATE_HINT_RE = re.compile(r"\b(aujourd|demain|ce\s+week|week[- ]end|samedi|dimanche)\b", re.IGNORECASE)

def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _contains_any(needle_set: set[str], text: str) -> bool:
    # on teste présence substring (suffisant et rapide)
    return any(k in text for k in needle_set)

def _is_lyon_context(text: str) -> bool:
    # Lyon explicite, ou arrondissement, ou un mot-clé quartier
    return ("lyon" in text) or bool(ARR_RE.search(text)) or _contains_any(LYON_KEYWORDS, text)

def _is_tourism_request(text: str) -> bool:
    # question tourisme = mots-clés tourisme OU mots-clés lyon (quartier) + formulation de demande
    if _contains_any(TOURISM_KEYWORDS, text):
        return True
    # ex: "dans le 6e" (sans dire musée) -> on veut quand même traiter comme tourisme
    if _is_lyon_context(text) and any(w in text for w in ["dans", "à", "au", "aux", "vers", "près", "proche"]):
        return True
    return False


_CITY_HINT = re.compile(r"\b(?:a|à|au|aux|sur|dans)\s+([A-ZÉÈÊËÀÂÎÏÔÙÛÜÇ][A-Za-zÉÈÊËÀÂÎÏÔÙÛÜÇ\-']{2,})\b")

def _extract_city_hint(msg: str) -> str | None:
    """
    Repère un motif du type 'à Paris', 'dans Berlin', 'sur Marseille'.
    Retourne le nom détecté, ou None.
    """
    m = _CITY_HINT.search(msg)
    if not m:
        return None
    return m.group(1).strip()

def _is_lyon(city: str) -> bool:
    return city.lower() == "lyon"

def _needs_live_data(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in [
        "horaire", "horaires", "ouvert", "ouverture",
        "adresse", "où se trouve", "comment y aller", "accès", "acces",
        "tarif", "tarifs", "prix", "billet", "tickets",
        "événement", "evenement", "événements", "evenements", "agenda",
        "aujourd", "ce week", "ce weekend", "ce week-end", "demain"
    ])

_DECISION_RE = re.compile(r"^\s*d[ée]cision\s*:\s*\w+\s*\n*", re.IGNORECASE)

def _strip_decision_prefix(text: str) -> str:
    if not text:
        return ""
    return _DECISION_RE.sub("", text.strip()).strip()

def _looks_like_tool_json(text: str) -> bool:
    # Détecte si le modèle a renvoyé un tool-call JSON en plein texte
    if not text:
        return False
    t = text.strip()
    if not (t.startswith("{") and t.endswith("}")):
        return False
    return '"tool"' in t and '"args"' in t


_SMALL_TALK = re.compile(
    r"\b("
    r"salut|hello|hey|yo|coucou|bonsoir|bonjour|ça va|ca va|merci|"
    r"mdr|ok|d'accord|super|nickel|parfait|bye|au revoir"
    r")\b",
    re.IGNORECASE
)

def _is_small_talk(msg: str) -> bool:
    m = msg.strip().lower()
    if len(m) <= 20 and _SMALL_TALK.search(m):
        return True
    # messages ultra courts typiques
    return m in {"salut", "bonjour", "bonsoir", "merci", "ok", "daccord", "d'accord", "hello", "bye"}

def _small_talk_answer(msg: str) -> str:
    m = msg.strip().lower()
    if "merci" in m:
        return "Avec plaisir."
    if any(w in m for w in ["salut", "bonjour", "bonsoir", "hello", "coucou", "hey"]):
        return "Salut ! Je peux t’aider à trouver des idées de sorties à Lyon. Tu veux plutôt musées, restaurants, parcs ou patrimoine ?"
    if any(w in m for w in ["bye", "au revoir"]):
        return "À bientôt ! Si tu reviens, dis-moi ce que tu veux faire à Lyon"
    return "Je suis là pour t'aider à trouver des activités à faire à lyon. Dis moi ce que tu recherches"


class Agent:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.ollama = OllamaClient(base_url="http://localhost:11434", model="llama3.1:8b")
        self.mcp = MCPClient(base_url="http://localhost:8001")
        self.memory: dict[str, list[dict[str, str]]] = {}

    def _build_prompt(self, history: list[dict[str, str]], user_block: str) -> str:
        # Limite l'historique pour éviter d’exploser le prompt
        hist = history[-6:]
        hist_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in hist])
        return f"{hist_text}\nUSER: {user_block}\nASSISTANT:"

    async def run(self, conversation_id: str, user_message: str) -> dict[str, Any]:
        t0 = time.time()
        steps: list[str] = []
        errors: dict[str, str] = {}
        sources: list[dict] = []

        history = self.memory.get(conversation_id, [])

        # 0) Small talk -> réponse directe, sans KB, sans LLM, sans tools
        if _is_small_talk(user_message):
            ms = int((time.time() - t0) * 1000)
            answer = _small_talk_answer(user_message)

            history = history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer},
            ]
            self.memory[conversation_id] = history[-12:]

            return {
                "answer": answer,
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": ["small_talk"],
                    "errors": {},
                },
            }

        city = _extract_city_hint(user_message)

        # Si l'utilisateur mentionne une ville explicite et que ce n'est pas Lyon -> on refuse
        if city and not _is_lyon(city):
            ms = int((time.time() - t0) * 1000)
            return {
                "answer": (
                    f"Je suis spécialisé sur le tourisme à Lyon (données visiterlyon.com). "
                    f"Je ne peux pas répondre de manière fiable pour {city}.\n\n"
                    "Si tu veux, je peux te proposer des idées à Lyon (musées, activités, événements)."
                ),
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": ["scope_guardrail"],
                    "errors": {},
                },
            }
        
        txt = _norm(user_message)

        # 0bis) on ne traite que ce qui ressemble au tourisme / sorties à Lyon
        if not _is_tourism_request(txt):
            answer = (
                "Je peux t’aider surtout pour organiser des sorties à Lyon "
                "(musées, restos, balades, patrimoine, événements). "
                "Tu cherches quoi ?"
            )
            history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
            self.memory[conversation_id] = history[-12:]
            ms = int((time.time() - t0) * 1000)

            return {
                "answer": answer,
                "sources": [],
                "trace": {
                    "kb_used": False,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": ["allowlist_block"],
                    "errors": {},
                },
            }



        # --- KB search (optionnel, mais utile)
        steps.append("kb_search")
        kb_hits = self.kb.search(user_message)
        kb_items = kb_hits.get("items", []) or []
        have_kb_answer = len(kb_items) > 0
        need_live = _needs_live_data(user_message)

        if have_kb_answer and not need_live:
            steps.append("kb_direct_answer")
            lines = ["Voici quelques idées :"]
            for it in kb_items:
                if it.get("url"):
                    lines.append(f"* {it['name']} : {it['url']}")
                else:
                    lines.append(f"* {it['name']}")

            answer = "\n".join(lines)
            answer = _strip_decision_prefix(answer)
            
            return {
                "answer": answer,
                "sources": [
                    {"type": "web", "url": it["url"]}
                    for it in kb_items
                    if it.get("url")
                ],
                "trace": {
                    "kb_used": True,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "steps": steps,
                    "errors": {},
                },
            }


        kb_summary_parts = []
        if kb_items:
            kb_summary_parts.append("KB_ITEMS (utilise uniquement ces items) :")
        for it in kb_items[:8]:
            kb_summary_parts.append(
                f"- name={it.get('name')} | type={it.get('type')} | district={it.get('district')} | url={it.get('url')}"
            )


        kb_summary = "\n".join(kb_summary_parts) if kb_summary_parts else "KB: aucun résultat."
        # Si KB a des résultats et qu'on ne demande pas d'info variable => interdiction d'appeler un tool
        force_no_tool = have_kb_answer and (not need_live)

        # --- PASS 1 : le modèle décide (réponse finale OU tool-call JSON strict)
        steps.append("llm_pass1")

        user_block_pass1 = f"""Message utilisateur: {user_message}

{kb_summary}

IMPORTANT:
- {"Tu DOIS répondre UNIQUEMENT avec la KB ci-dessus et tu N'APPELLES AUCUN tool." if force_no_tool else "Tu peux appeler un tool uniquement si nécessaire."}
- Si tu appelles un tool, réponds UNIQUEMENT avec le JSON tool-call.
- Sinon, réponds directement.
- Si tu réponds avec la KB: tu cites UNIQUEMENT des lieux présents dans KB_ITEMS.
- Pour chaque lieu: affiche "name : url".
- Si aucun item ne correspond exactement (ex: 6ème), dis-le et propose des alternatives.

"""
        prompt1 = self._build_prompt(history, user_block_pass1)

        out1 = None
        try:
            out1 = await self.ollama.generate(prompt=prompt1, system=SYSTEM_PROMPT)
        except Exception as e:
            ms = int((time.time() - t0) * 1000)
            return {
                "answer": "Désolé, le modèle IA est indisponible (Ollama).",
                "sources": sources,
                "trace": {
                    "kb_used": have_kb_answer,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": steps + ["ollama_error_pass1"],
                    "errors": {"ollama_error": str(e)},
                },
            }

        if not out1 or not out1.strip():
            ms = int((time.time() - t0) * 1000)
            return {
                "answer": "Désolé, je n'ai pas réussi à générer une réponse.",
                "sources": sources,
                "trace": {
                    "kb_used": have_kb_answer,
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": steps + ["empty_llm_pass1"],
                    "errors": {},
                },
            }
        
        out1 = _strip_decision_prefix(out1)

        tool_call = parse_tool_call_loose(out1)
                # Si le modèle renvoie un JSON tool-call mais qu'on force_no_tool -> on l'ignore
        if force_no_tool:
            tool_call = None

        # Si le modèle renvoie un JSON tool-call brut (et parse_tool_call_loose échoue),
        # on évite de renvoyer ça au front
        if tool_call is None and _looks_like_tool_json(out1):
            out1 = "Je peux t’aider là-dessus, mais j’ai besoin que tu précises un peu (type de lieu, quartier, ou ce que tu veux exactement)."


        # Priorité KB : interdit tool si KB suffit et pas besoin de live data
        if force_no_tool:
            tool_call = None

        tool_called = None
        tool_payload = None


        if tool_call:
            # --- TOOL EXEC
            tool_called = tool_call["tool"]
            args = tool_call["args"]  # <-- AJOUTE ÇA
            steps.append(f"tool_call:{tool_called}")

            # --- Normalisation des args (safety net)  <-- AJOUTE ÇA
            if tool_called == "scrape_category":
                if "query" not in args and "categorie" in args:
                    args["query"] = args.pop("categorie")
                args.setdefault("limit", 5)

            if tool_called == "scrape_events":
                args.setdefault("limit", 5)

            try:
                tool_payload = await self.mcp.call_tool(tool_called, args)  # <-- utilise args ici
                for it in (tool_payload.get("items") or []):
                    if isinstance(it, dict) and it.get("url"):
                        sources.append({"type": "web", "url": it["url"]})
            except Exception as e:
                tool_payload = {"error": str(e)}
                steps.append("tool_error")

            # --- PASS 2 : on redonne résultat tool au modèle → réponse finale
            steps.append("llm_pass2")
            user_block_pass2 = f"""Message utilisateur: {user_message}

{kb_summary}

Résultat du tool ({tool_called}) (JSON):
{tool_payload}

Tâche:
- Produis UNIQUEMENT la réponse finale pour l'utilisateur.
- NE PRODUIS AUCUN JSON.
- NE FAIS AUCUN appel de tool.
- Utilise UNIQUEMENT les éléments de tool_payload.items.
- Pour chaque item : affiche "title : url".
- N'invente pas de noms de lieux (si un musée précis n'est pas dans items, ne le cite pas).
- N'invente jamais de liens.
"""
            prompt2 = self._build_prompt(history, user_block_pass2)

            try:
                answer = await self.ollama.generate(prompt=prompt2, system=SYSTEM_PROMPT)
            except Exception as e:
                answer = (
                    "Le modèle IA est indisponible pour formuler la réponse. "
                    "Réessaie dans un instant."
                )
                steps.append("ollama_error_pass2")
                # Note: on met l'erreur dans le trace
                err2 = str(e)
        else:
            steps.append("final_from_pass1")
            answer = out1

        # --- update mémoire
        history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]
        self.memory[conversation_id] = history[-12:]

        ms = int((time.time() - t0) * 1000)
        trace_errors: dict[str, str] = {}
        if isinstance(tool_payload, dict) and tool_payload.get("error"):
            trace_errors["tool_error"] = str(tool_payload.get("error"))
        if "err2" in locals():
            trace_errors["ollama_error"] = err2

        trace = {
            "kb_used": have_kb_answer,
            "tool_called": tool_called,
            "model": self.ollama.model,
            "latency_ms": ms,
            "steps": steps,
            "errors": trace_errors,
        }

        # garde uniquement les sources réellement citées dans la réponse
        used_urls = set()
        for s in sources:
            if s.get("type") == "web" and s.get("url") and s["url"] in answer:
                used_urls.add(s["url"])
        sources = [s for s in sources if s.get("type") != "web" or s.get("url") in used_urls]

        answer = _strip_decision_prefix(answer)

        return {"answer": answer, "sources": sources, "trace": trace}
