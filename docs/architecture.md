# Architecture

## Overview

```
┌────────────────────────────────────────────────────────┐
│                  Frontend (Vue 3 + Pinia)               │
│  Dashboard │ Chat │ Runs │ Agents │ Models │ Memory    │
│                      ↕ WebSocket                        │
├────────────────────────────────────────────────────────┤
│                  Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Workflow Engine                       │  │
│  │  SPEC → PLAN → EXECUTE → VERIFY → REPAIR         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Tools   │ │  Agents  │ │ Learning │ │ Security │  │
│  │  32 ops  │ │ 6 agents │ │ ChromaDB │ │ Sandbox  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├────────────────────────────────────────────────────────┤
│                  Infrastructure                         │
│  Ollama (LLM) │ ChromaDB (Vector) │ SQLite │ Traefik  │
└────────────────────────────────────────────────────────┘
```

## Backend (`backend/app/`)

| Directory | Description |
|-----------|-------------|
| `api/v1/` | REST routes: auth, chat, conversations, learning, system, tools |
| `api/routes/` | Agent routes |
| `core/` | Config, database, security, logging, metrics, scheduler |
| `models/` | Pydantic v2 schemas, workflow models, WebSocket event types |
| `services/react_engine/` | Workflow engine, 32 tools, governance, secure executor, verifier |
| `services/agents/` | Agent base class and registry (6 agents) |
| `services/learning/` | Context enricher, evaluator, feedback, ChromaDB memory |
| `services/ollama/` | Ollama client and model categorizer |
| `services/websocket/` | Event emitter and exception handling |

## Frontend (`frontend/src/`)

| Directory | Description |
|-----------|-------------|
| `components/chat/` | MessageList, MessageInput, ConversationSidebar, RunInspector |
| `components/ui/` | GlassCard, StatusOrb, ModernButton, MetricCard, CodeBlock, etc. |
| `components/layout/` | SidebarNav, TopBar |
| `stores/` | Pinia stores: auth, chat, learning, loading, runTypes, system, toast, tools |
| `views/v8/` | Dashboard, Chat, Runs, RunConsole, Agents, Models, Memory, Audit, System |
| `styles/` | Design tokens, typography, animations, responsive, accessibility |
| `services/` | API client, WebSocket client, event normalizer |

## Workflow Phases

| Phase | Description | Timeout |
|-------|-------------|---------|
| STARTING | Initialization | 30s |
| SPEC | Task analysis and specification | 60s |
| PLAN | Action planning | 60s |
| EXECUTE | Tool execution | 90s |
| VERIFY | Result validation | 120s |
| REPAIR | Error correction (if needed) | 120s |
| COMPLETE | Run finished | - |

## WebSocket Events

All events follow this structure:

```json
{
  "type": "phase|thinking|tool|verification_item|complete|error",
  "timestamp": "2026-02-06T15:30:00.000Z",
  "run_id": "run-abc-123",
  "data": {}
}
```

**Invariants:**
- Every run emits exactly one `complete` or `error` event
- No run stays in `running` state after a terminal event
- Events are append-only
