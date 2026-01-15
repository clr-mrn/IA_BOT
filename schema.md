```mermaid
flowchart LR
  U[Utilisateur] --> F[Front React]
  F --> B[Backend FastAPI]
  B --> A[Agent]
  A --> KB[KB JSON]
  A --> O[LLM Ollama]
  A --> MCP[MCP Tools]
  MCP --> V[visiterlyon.com]
  B --> F

