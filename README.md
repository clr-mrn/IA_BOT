# IA_BOT
Agent conversationnel spécialisé dans le tourisme à Lyon, basé sur le site officiel :
https://www.visiterlyon.com/

Le projet est composé de deux services :
- **Backend** : agent IA (FastAPI) qui gère la logique conversationnelle et les appels aux tools
- **MCP** : service de scraping qui expose des tools (catégories, lieux, événements)

## Prérequis
- Python 3.12 ou 3.13
- Un environnement virtuel Python
- Ollama installé et lancé en local

## Installation

Depuis la racine du projet :
dans un terminal git bash

```bash
python -m venv .venv
source .venv/Scripts/activate

pip install -r backend/requirements.txt
pip install -r mcp/requirements.txt

uvicorn mcp.app:app --reload --port 8001
```
dans un nouveau terminal :
```bash
uvicorn backend.app:app --reload --port 8000
```

pour tester dans un autre terminal :
```
curl http://localhost:8001/health
curl http://localhost:8000/health
```
Pour lancer l'interface
```bash
npm install
npm run dev
```
