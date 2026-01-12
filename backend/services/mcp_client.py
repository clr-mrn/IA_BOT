import httpx
from typing import Any

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    async def call_tool(self, tool_name: str, args: dict[str, Any], timeout_s: float = 30.0) -> dict[str, Any]:
        """
        Convention simple: POST /tools/{tool_name}
        Le dev MCP doit exposer ce contrat.
        """
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.post(f"{self.base_url}/tools/{tool_name}", json=args)
            r.raise_for_status()
            return r.json()
