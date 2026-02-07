# Architecture

## Vue d'ensemble

AI Orchestrator est une plateforme d'orchestration IA autonome composée de:

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Dashboard │ │  Runs    │ │  Agents  │ │ Tools/Memory │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│                         ↓ WebSocket                          │
├─────────────────────────────────────────────────────────────┤
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Workflow Engine                      │   │
│  │  SPEC → PLAN → EXECUTE → VERIFY → REPAIR             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │   Tools   │ │  Agents   │ │  Memory   │ │ Security  │   │
│  │ Registry  │ │ Registry  │ │ ChromaDB  │ │  SSRF/    │   │
│  │   34+     │ │    6+     │ │ Durable   │ │ Sandbox   │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Ollama  │ │ ChromaDB │ │ SQLite/  │ │   Traefik   │   │
│  │   LLM    │ │  Vector  │ │ Postgres │ │   Proxy     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Composants principaux

### Backend (`backend/`)

| Dossier | Description |
|---------|-------------|
| `app/api/` | Routes REST et WebSocket |
| `app/core/` | Configuration, database, auth |
| `app/models/` | Modèles SQLAlchemy et Pydantic |
| `app/services/` | Logique métier |
| `app/services/react_engine/` | Moteur d'exécution et tools |
| `app/services/agents/` | Système d'agents v8 |
| `tests/` | Tests unitaires et d'intégration |

### Frontend (`frontend/`)

| Dossier | Description |
|---------|-------------|
| `src/views/` | Vues principales |
| `src/views/v8/` | Vues v8 (Dashboard, Runs, Agents) |
| `src/components/` | Composants réutilisables |
| `src/stores/` | State Pinia (chat, auth) |
| `src/composables/` | Hooks réutilisables |

## Flux de données

1. **Requête utilisateur** → Frontend envoie message via WebSocket
2. **Workflow Engine** → Parse, planifie, exécute avec phases
3. **Tool Execution** → Exécute outils avec validation sécurité
4. **Events WebSocket** → Stream résultats en temps réel
5. **Mémoire** → Persiste contexte dans ChromaDB

## Phases d'exécution

| Phase | Description |
|-------|-------------|
| **SPEC** | Analyse et spécification de la tâche |
| **PLAN** | Planification des actions |
| **EXECUTE** | Exécution des tools |
| **VERIFY** | Validation des résultats |
| **REPAIR** | Correction si échec (optionnel) |
