```mermaid
flowchart LR
  U[Utilisateur - Navigateur] -->|UI chat| F[Front React Vite]
  F -->|POST /chat| B[Backend FastAPI :8000]

  subgraph Backend
    B --> A[Agent]
    A -->|search| KB[KnowledgeBase]
    A -->|generate| O[Ollama llama3.1:8b]
    A -->|call_tool| MCPC[MCP Client]
  end

  MCPC -->|HTTP JSON| M[MCP FastAPI :8001]

  subgraph MCP
    M --> T1[scrape_category]
    M --> T2[scrape_place]
    M --> T3[scrape_events]
  end

  T1 -->|GET| V[visiterlyon.com]
  T2 -->|GET| V
  T3 -->|GET| V

  B -->|JSON answer| F
  F -->|Affichage| U
