# AI Orchestrator v6.1

Un orchestrateur IA autonome avec boucle ReAct, exécution d'outils sécurisée, et interface cockpit professionnelle.

## 🎯 Fonctionnalités

- **Boucle ReAct** : Reason → Act → Observe → Repeat
- **72+ outils** intégrés (système, Docker, réseau, fichiers, etc.)
- **Streaming WebSocket** temps réel
- **Run Inspector** : traçabilité complète des exécutions
- **Sécurité** : allowlist de 175 commandes, JWT auth, rate limiting
- **Multi-modèles** : Ollama local + proxies cloud

## 🏗️ Architecture

```
ai-orchestrator/
├── backend/                 # FastAPI + ReAct Engine
│   ├── app/
│   │   ├── api/v1/         # Endpoints REST + WebSocket
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # ToolExecutor, ReActEngine, LLM
│   └── requirements.txt
│
├── frontend/               # Vue 3 + Tailwind
│   ├── src/
│   │   ├── components/     # Chat, RunInspector, StatusBar
│   │   ├── views/          # ChatView, ToolsView, Settings
│   │   ├── stores/         # Pinia (auth, chat, tools, system)
│   │   └── services/       # API client, WebSocket
│   └── package.json
│
└── docs/                   # Documentation
```

## 🚀 Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos valeurs
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Développement
npm run build    # Production
```

## 🔧 Configuration

Copier `backend/.env.example` vers `backend/.env` et configurer :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | SQLite ou PostgreSQL | `sqlite:///./data/orchestrator.db` |
| `JWT_SECRET` | Clé secrète JWT | (à définir) |
| `OLLAMA_URL` | URL Ollama | `http://localhost:11434` |
| `DEFAULT_MODEL` | Modèle par défaut | `kimi-k2:1t-cloud` |
| `MAX_ITERATIONS` | Max boucles ReAct | `10` |

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | Authentification |
| `GET /api/v1/conversations` | Liste conversations |
| `WS /api/v1/chat/ws` | Chat streaming |
| `GET /api/v1/tools` | Liste outils |
| `GET /api/v1/system/health` | État système |
| `GET /api/v1/system/models` | Modèles disponibles |

## 🎨 Interface

- **Cockpit 3 panneaux** : Conversations / Chat / Run Inspector
- **Run Inspector** : Visualisation temps réel thinking → tool → complete
- **Sélecteur modèle** : Switch entre modèles Ollama
- **Export** : JSON / Markdown

## 📝 License

MIT License - Lalpha 2025
