# AI Orchestrator v8.1

Autonomous AI orchestration platform with workflow engine, modular agents, and real-time interface.

## Features

- **Workflow Engine** - Phased execution: SPEC, PLAN, EXECUTE, VERIFY, REPAIR
- **32 Built-in Tools** - Filesystem, network, QA, git, memory, web search, governance
- **6 Agents** - Modular agents with tool isolation and capability filtering
- **Real-time WebSocket** - Normalized events with run tracking and watchdog
- **Learning System** - ChromaDB-powered memory with pattern detection and feedback
- **Security** - SSRF protection, sandbox mode, prompt injection detection, audit logging
- **Governance** - Fail-closed action approval with justification requirements

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit SECRET_KEY
uvicorn main:app --host 0.0.0.0 --port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend API: http://localhost:8001 | Frontend: http://localhost:5173

## Architecture

```
ai-orchestrator/
├── backend/             # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/         # REST routes + middleware
│   │   ├── core/        # Config, DB, security, metrics
│   │   ├── models/      # Pydantic v2 schemas
│   │   └── services/
│   │       ├── react_engine/   # Tools, engine, governance, security
│   │       ├── agents/         # Agent registry (6 agents)
│   │       ├── learning/       # ChromaDB memory + feedback
│   │       ├── ollama/         # LLM client + categorizer
│   │       └── websocket/      # Event emitter
│   └── tests/           # 424 tests
├── frontend/            # Vue 3 + Pinia + Vite
│   ├── src/
│   │   ├── components/  # 28 components (chat, ui, layout)
│   │   ├── stores/      # 8 Pinia stores
│   │   ├── views/v8/    # 9 views (Neural Glow design)
│   │   └── styles/      # Design tokens, typography, animations
│   └── tests/           # 158 tests
├── monitoring/          # Grafana + Prometheus + Loki
├── docs/                # Documentation
└── nginx.conf           # Production reverse proxy
```

## Agents

| Agent | Description | Allowed Tools |
|-------|-------------|---------------|
| `system.health` | System monitoring | read_file, list_directory, execute_command |
| `docker.monitor` | Docker containers | read_file, list_directory, execute_command |
| `unifi.monitor` | UniFi network | read_file, list_directory, http_request |
| `web.researcher` | Web research | web_search, web_read |
| `self_improve` | Self-improvement | file ops, git, tests, memory |
| `qa.runner` | QA test runner | run_tests, run_lint, git_status |

## Tests

```bash
# Backend (424 tests)
cd backend && ../.venv/bin/python -m pytest tests/ -x -q

# Frontend (158 tests)
cd frontend && npx vitest run
```

## Documentation

See [docs/](docs/) for detailed documentation:
- [Getting Started](docs/getting-started.md) - Installation and development setup
- [Architecture](docs/architecture.md) - System design and components
- [API Reference](docs/api.md) - REST and WebSocket endpoints
- [Security](docs/security.md) - Security model and protections
- [Tools Reference](docs/tools.md) - All 32 tools with examples
- [Learning System](docs/learning.md) - ChromaDB memory and feedback
- [Deployment](docs/deployment.md) - Production deployment with Traefik/nginx
- [Observability](docs/observability.md) - Monitoring with Grafana/Prometheus/Loki

## License

MIT
