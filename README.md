# AI Orchestrator v6.2

Un orchestrateur IA autonome avec pipeline Workflow complet, exécution d'outils sécurisée, et interface Orchestrator UI professionnelle.

## 🎯 Fonctionnalités

- **Pipeline Workflow** : SPEC → PLAN → EXECUTE → VERIFY → REPAIR → COMPLETE
- **17 outils** intégrés (système, fichiers, QA, utilitaires, réseau)
- **7 outils QA** : git_status, git_diff, run_tests, run_lint, run_format, run_build, run_typecheck
- **Erreurs récupérables** : auto-correction via search_directory/search_files
- **Streaming WebSocket** temps réel avec run_id et phases
- **Run Inspector** : stepper workflow, tabs Tools/QA/Raw, verdict PASS/FAIL
- **Sécurité** : allowlist commandes, sandbox Docker, workspace isolé
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
