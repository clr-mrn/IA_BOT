# IA_BOT
Agent conversationnel spécialisé dans le tourisme à Lyon, basé sur le site officiel :
https://www.visiterlyon.com/

Le projet est composé de deux services :
- **Backend** : agent IA (FastAPI) qui gère la logique conversationnelle et les appels aux tools
- **MCP** : service de scraping qui expose des tools (catégories, lieux, événements)

## Prérequis
- Python 3.10+
- Un environnement virtuel Python
- Ollama installé et lancé en local

## Installation

Depuis la racine du projet :

```bash
python -m venv .venv
source .venv/Scripts/activate

pip install -r backend/requirements.txt
pip install -r mcp/requirements.txt

uvicorn mcp.app:app --reload --port 8001

uvicorn backend.app:app --reload --port 8000

curl http://localhost:8001/health
curl http://localhost:8000/health
```

```bash
npm install
npm run dev
```
