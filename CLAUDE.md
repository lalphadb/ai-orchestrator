# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI Orchestrator is a self-improving AI agent platform with a 6-phase workflow pipeline (SPEC → PLAN → EXECUTE → VERIFY → REPAIR → COMPLETE). It uses a ReAct (Reason-Act-Observe) engine with 18 integrated tools, dual-model architecture (executor + verifier), real-time WebSocket streaming, and automatic error recovery.

## Commands

### Backend (Python/FastAPI)
```bash
# Development
cd backend && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Run tests
pytest backend/tests/

# Single test
pytest backend/tests/test_tools.py::test_read_file -v
```

### Frontend (Vue 3/Vite)
```bash
# Development (proxies to backend:8001)
cd frontend && npm run dev

# Build
npm run build
```

### Docker
```bash
docker-compose up -d
# Backend: localhost:8002, Frontend: localhost:3002
```

## Architecture

```
Frontend (Vue 3 + Pinia)          Backend (FastAPI)
    │                                  │
    │ REST + WebSocket                 │
    └──────────────────────────────────┤
                                       │
                              ┌────────┴────────┐
                              │ Workflow Engine │
                              │   (6 phases)    │
                              └────────┬────────┘
                                       │
                              ┌────────┴────────┐
                              │  ReAct Engine   │
                              │ (17 tools, max  │
                              │  10 iterations) │
                              └────────┬────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                   Ollama        ChromaDB        SQLite
                  (LLMs)        (Learning)      (Data)
```

### Key Services

| Service | Location | Purpose |
|---------|----------|---------|
| `WorkflowEngine` | `backend/app/services/react_engine/workflow_engine.py` | Orchestrates 6-phase pipeline |
| `ReactEngine` | `backend/app/services/react_engine/engine.py` | Reason-Act-Observe loop |
| `BUILTIN_TOOLS` | `backend/app/services/react_engine/tools.py` | 18 tools registry |
| `Verifier` | `backend/app/services/react_engine/verifier.py` | LLM-based QA judge |
| `ollama_client` | `backend/app/services/ollama/client.py` | LLM HTTP client |
| `LearningMemory` | `backend/app/services/learning/memory.py` | ChromaDB experience storage |

### Workflow Pipeline

1. **SPEC**: Generate specification + acceptance criteria
2. **PLAN**: Break down into actionable steps
3. **EXECUTE**: Run ReAct engine (max 10 iterations)
4. **VERIFY**: Auto-run 7 QA tools (pytest, ruff, mypy, black, git_status, git_diff, run_build)
5. **REPAIR**: Auto-fix on failure (max 3 cycles)
6. **COMPLETE**: Return results + verdict (PASS/FAIL)

### Tool Result Contract

All tools return standardized results:
```python
{
  "success": bool,
  "data": dict | None,
  "error": {"code": str, "message": str, "recoverable": bool},
  "meta": {"duration_ms": int, "command": str, "sandbox": bool}
}
```

Error codes: `E_FILE_NOT_FOUND` (recoverable), `E_DIR_NOT_FOUND` (recoverable), `E_PERMISSION` (fatal), `E_CMD_NOT_ALLOWED` (fatal), `E_PATH_FORBIDDEN` (fatal)

### Auto-Recovery

When a tool returns a recoverable error (E_DIR_NOT_FOUND, E_FILE_NOT_FOUND, E_PATH_NOT_FOUND), the engine automatically:
1. Extracts the path name from the error message
2. Calls `search_directory()` to find alternatives
3. Injects suggestions into the next LLM prompt
4. Logs the recovery attempt in `tools_used` with `auto_recovery: true`

### WebSocket Events

Events sent during workflow execution:
- `phase`: Current phase name
- `thinking`: LLM thought process
- `tool`: Tool execution with args/result
- `verification_item`: QA check status
- `complete`: Final verdict + response
- `error`: Workflow errors

### Security Model

- **Command allowlist**: 185+ approved shell commands (`config.py:COMMAND_ALLOWLIST`)
- **Command blocklist**: 31 dangerous commands (`config.py:COMMAND_BLOCKLIST`)
- **Workspace isolation**: All execution in `WORKSPACE_DIR`
- **JWT auth**: 7-day token expiration

## Key Configuration

In `backend/app/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `EXECUTOR_MODEL` | kimi-k2:1t-cloud | LLM for planning/execution |
| `VERIFIER_MODEL` | deepseek-coder:33b | LLM for verification |
| `MAX_ITERATIONS` | 10 | ReAct loop limit |
| `MAX_REPAIR_CYCLES` | 3 | Auto-fix attempts |
| `WORKSPACE_DIR` | /home/lalpha/orchestrator-workspace | Execution sandbox |

## API Endpoints

- `POST /api/v1/chat` - Main workflow endpoint
- `WS /api/v1/chat/ws` - Real-time streaming
- `GET /api/v1/tools` - List available tools
- `GET /api/v1/system/models` - List Ollama models
- `GET /api/v1/system/health` - Health check

## Frontend State

Pinia stores in `frontend/src/stores/`:
- `chat.js`: Conversations, messages, run metadata
- `auth.js`: JWT tokens, user state
- `system.js`: Models, health, metrics
- `tools.js`: Available tools

## Documentation

Comprehensive docs in `/docs/`:
- `ARCHITECTURE.md` / `ARCHITECTURE-v6.1.md` - Technical architecture
- `API.md` - REST/WebSocket reference
- `TOOLS.md` - Tool documentation (18 tools)
- `WEBSOCKET.md` - Streaming protocol
- `WORKFLOW_CONVENTIONS.md` - Pipeline phases, event formats
- `CONFIGURATION.md` - Environment variables
- `SECURITY.md` - Security layers
