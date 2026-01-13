import json
from typing import Any, Optional, TypedDict

class ToolCall(TypedDict):
    tool: str
    args: dict[str, Any]

def parse_tool_call_loose(text: str) -> Optional[ToolCall]:
    s = text.strip()
    i = s.find("{")
    j = s.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None
    candidate = s[i:j+1]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    if not isinstance(obj.get("tool"), str):
        return None
    if not isinstance(obj.get("args"), dict):
        return None
    return {"tool": obj["tool"], "args": obj["args"]}
