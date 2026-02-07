# AI Orchestrator v8

Plateforme d'orchestration IA autonome avec workflow engine, agents modulaires et interface temps réel.

## Fonctionnalités

- **Workflow Engine** - Exécution en phases (SPEC → PLAN → EXECUTE → VERIFY → REPAIR)
- **34+ Tools** - Filesystem, network, QA, git, memory, web search
- **Agents v8** - Agents modulaires avec restrictions d'outils
- **WebSocket temps réel** - Events normalisés avec run tracking
- **Self-Improve** - Auto-amélioration avec validation QA et rollback
- **Sécurité** - SSRF protection, sandbox mode, audit logging
- **V8 Architecture** - Contrat de run standardisé, watchdog avancé, authentification robuste

## Quick Start

```bash
# Clone
git clone https://github.com/lalpha/ai-orchestrator.git
cd ai-orchestrator

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./start.sh

# Frontend (autre terminal)
cd frontend
npm install
npm run dev
```

Application: http://localhost:5173

## Architecture

```
ai-orchestrator/
├── backend/           # FastAPI + Workflow Engine
│   ├── app/
│   │   ├── api/       # Routes REST/WS
│   │   ├── services/  # Logique métier
│   │   │   ├── react_engine/  # Tools + Engine
│   │   │   ├── agents/        # Système agents v8
│   │   │   └── websocket/     # EventEmitter
│   │   └── models/    # Schemas
│   └── tests/         # 313 tests
├── frontend/          # Vue 3 + Pinia
│   ├── src/views/v8/  # UI v8
│   └── tests/         # 158 tests
├── monitoring/        # Grafana/Prometheus
├── docs/              # Documentation
└── audits/            # Rapports sécurité
```

## Tests

```bash
# Backend
cd backend && pytest tests/ -v
# 313 passed

# Frontend
cd frontend && npm test
# 158 passed
```

## Documentation

Voir [docs/README.md](docs/README.md) pour la documentation complète.

## Agents v8

| Agent | Description | Tools |
|-------|-------------|-------|
| system.health | Monitoring système | read_file, bash |
| docker.monitor | Containers Docker | read_file, bash |
| web.researcher | Recherche web | web_search, web_read |
| self_improve | Auto-amélioration | file ops, git, tests |

## Licence

MIT
