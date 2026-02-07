# Installation

## Prérequis

- **Python** 3.11+
- **Node.js** 18+
- **Ollama** avec modèles installés
- **ChromaDB** (optionnel, pour mémoire persistante)

## Installation rapide

```bash
# Cloner le repository
git clone https://github.com/lalpha/ai-orchestrator.git
cd ai-orchestrator

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
```

## Configuration

### Variables d'environnement Backend

Éditer `backend/.env`:

```env
# Base de données
DATABASE_URL=sqlite:///./ai_orchestrator.db

# Sécurité
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# ChromaDB (optionnel)
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Mode
SANDBOX_MODE=true
DEBUG=false
```

### Démarrage

```bash
# Terminal 1 - Backend
cd backend
./start.sh

# Terminal 2 - Frontend
cd frontend
npm run dev
```

L'application est accessible sur `http://localhost:5173`

## Vérification

```bash
# Santé API
curl http://localhost:8000/health

# Tests backend
cd backend && pytest tests/ -v

# Tests frontend
cd frontend && npm test
```
