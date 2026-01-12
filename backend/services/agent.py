import time
from typing import Any

from services.kb import KnowledgeBase
from services.ollama import OllamaClient
from services.mcp_client import MCPClient
from services.toolcall import parse_tool_call

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
- Si tu ne fais pas de tool-call : commence par "Décision: KB" puis donne la réponse.
- Si tu as utilisé un tool : commence par "Décision: TOOL" puis donne la réponse.
- Réponse en français, structurée en puces, concise, et orientée action.
- Si le tool ne renvoie rien ou échoue : explique-le brièvement et propose une alternative (ex: reformuler, autre catégorie).
"""


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
        errors: dict[str, str] = []
        sources: list[dict] = []

        history = self.memory.get(conversation_id, [])

        # --- KB search (optionnel, mais utile)
        steps.append("kb_search")
        kb_hits = self.kb.search(user_message)

        kb_summary_parts = []
        if kb_hits.get("rules"):
            kb_summary_parts.append("KB (règles pertinentes):")
            for r in kb_hits["rules"]:
                kb_summary_parts.append(f"- {r.get('id')}: suggère {', '.join(r.get('suggest', []))}")
                sources.append({"type": "kb", "id": r.get("id")})

        if kb_hits.get("districts"):
            kb_summary_parts.append("KB (quartiers pertinents):")
            for d in kb_hits["districts"]:
                kb_summary_parts.append(f"- {d.get('name')}: {', '.join(d.get('best_for', []))}")

        kb_summary = "\n".join(kb_summary_parts) if kb_summary_parts else "KB: rien de directement pertinent."

        # --- PASS 1 : le modèle décide (réponse finale OU tool-call JSON strict)
        steps.append("llm_pass1")
        user_block_pass1 = f"""Message utilisateur: {user_message}

{kb_summary}

Si tu dois appeler un tool, réponds UNIQUEMENT avec le JSON tool-call.
Sinon réponds directement (Décision: KB...).
"""
        prompt1 = self._build_prompt(history, user_block_pass1)

        try:
            out1 = await self.ollama.generate(prompt=prompt1, system=SYSTEM_PROMPT)
        except Exception as e:
            # Pas de 500 : fallback propre
            ms = int((time.time() - t0) * 1000)
            return {
                "answer": "Décision: KB\nDésolé, le modèle IA est indisponible (Ollama).",
                "sources": sources,
                "trace": {
                    "kb_used": bool(kb_hits.get("rules") or kb_hits.get("districts")),
                    "tool_called": None,
                    "model": self.ollama.model,
                    "latency_ms": ms,
                    "steps": steps,
                    "errors": {"ollama_error": str(e)},
                },
            }

        tool_call = parse_tool_call(out1)
        tool_called = None
        tool_payload = None

        if tool_call:
            # --- TOOL EXEC
            tool_called = tool_call["tool"]
            steps.append(f"tool_call:{tool_called}")

            try:
                tool_payload = await self.mcp.call_tool(tool_called, tool_call["args"])
                # si le tool renvoie des URLs, tu peux les exposer comme sources
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
- Produis la réponse finale.
- Commence par "Décision: TOOL".
- N'invente jamais de liens. Utilise uniquement ceux présents dans les sources/outils.
"""
            prompt2 = self._build_prompt(history, user_block_pass2)

            try:
                answer = await self.ollama.generate(prompt=prompt2, system=SYSTEM_PROMPT)
            except Exception as e:
                answer = (
                    "Décision: TOOL\n"
                    "Le tool a été exécuté mais le modèle IA est indisponible pour formuler la réponse. "
                    "Réessaie dans un instant."
                )
                steps.append("ollama_error_pass2")
                # Note: on met l'erreur dans le trace
                err2 = str(e)
        else:
            # --- Réponse directe
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
            "kb_used": bool(kb_hits.get("rules") or kb_hits.get("districts")),
            "tool_called": tool_called,
            "model": self.ollama.model,
            "latency_ms": ms,
            "steps": steps,
            "errors": trace_errors,
        }

        return {"answer": answer, "sources": sources, "trace": trace}
