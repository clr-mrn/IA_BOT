import json
from typing import Any, Optional, TypedDict


class ToolCall(TypedDict):
    tool: str
    args: dict[str, Any]


def parse_tool_call(text: str) -> Optional[ToolCall]:
    """
    Attend un JSON strict uniquement.
    Retourne None si ce n'est pas un tool-call valide.
    """
    s = text.strip()

    # Cas simple: le modèle répond uniquement un JSON
    if not (s.startswith("{") and s.endswith("}")):
        return None

    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None

    if not isinstance(obj, dict):
        return None
    if "tool" not in obj or "args" not in obj:
        return None
    if not isinstance(obj["tool"], str):
        return None
    if not isinstance(obj["args"], dict):
        return None

    return {"tool": obj["tool"], "args": obj["args"]}
