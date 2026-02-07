# AI Orchestrator - Instructions pour Claude Code

## REGLES NON-NEGOCIABLES

### AVANT de modifier quoi que ce soit :
1. **LIRE** le fichier concerne EN ENTIER avant de le modifier
2. **COMPRENDRE** les dependances (imports, appelants, tests associes)
3. **VERIFIER** qu'un test existe pour ce fichier (`tests/test_<module>.py`)

### INTERDICTIONS ABSOLUES :
- NE JAMAIS reecrire un fichier entier - modifier uniquement les lignes necessaires
- NE JAMAIS supprimer une fonction/classe sans verifier qu'elle n'est importee nulle part
- NE JAMAIS modifier la securite (secure_executor.py, governance.py, security.py) sans confirmation
- NE JAMAIS modifier les modeles Pydantic (schemas.py, ws_events.py, workflow.py) sans verifier les dependants
- NE JAMAIS toucher a tools.py (2260 lignes) sans raison critique documentee
- NE JAMAIS utiliser `datetime.utcnow()` - utiliser `datetime.now(timezone.utc)`
- NE JAMAIS utiliser `class Config:` dans Pydantic - utiliser `model_config = ConfigDict(...)`

### AVANT chaque commit :
1. Lancer `cd backend && ../.venv/bin/python -m pytest tests/ -x -q`
2. Lancer `cd frontend && npx vitest run` si des fichiers frontend ont ete modifies
3. Verifier que le nombre de tests passants n'a PAS diminue
4. Message de commit au format : `fix(module): description courte`

## Version actuelle
v8.1 - branche `main`

## Architecture

### Backend (FastAPI) - `/backend/app/`
```
app/
├── api/              # Routes REST + middleware
│   ├── v1/           # auth, chat, conversations, learning, system, tools
│   └── routes/       # agents
├── core/             # Config, DB, logging, security, metrics, scheduler
├── models/           # schemas.py, workflow.py, ws_events.py
└── services/
    ├── agents/       # base.py, registry.py (6 agents)
    ├── learning/     # context_enricher, evaluator, feedback, memory
    ├── ollama/       # client.py, categorizer.py
    ├── react_engine/ # engine, tools (30), governance, secure_executor,
    │                 # verifier, workflow_engine, self_improve, memory,
    │                 # prompt_injection_detector, runbooks, learning_wrapper
    └── websocket/    # event_emitter.py, exceptions.py
```

### Frontend (Vue 3 + Pinia) - `/frontend/src/`
```
src/
├── assets/           # main.css
├── styles/           # tokens.css, typography.css, animations.css,
│                     # responsive.css, accessibility.css (Neural Glow)
├── components/
│   ├── chat/         # CategorySection, ConversationSidebar, FeedbackButtons,
│   │                 # MessageInput, MessageList, ModelsDisplay, RunInspector
│   ├── common/       # LoadingBar, StatusBar, Toast, ToastContainer
│   ├── layout/       # SidebarNav, TopBar
│   └── ui/           # GlassCard, StatusOrb, ModernButton, MetricCard,
│                     # AgentCard, CodeBlock, EmptyState, SkeletonLoader,
│                     # PipelineSteps, ModalDialog, Tooltip, Dropdown,
│                     # ErrorBoundary, ChatInput, ThinkingDots
├── composables/      # useAccessibility, useModelDetection
├── layouts/          # V8Layout.vue
├── services/         # api.js, wsClient.js, ws/normalizeEvent.js
├── stores/           # auth, chat, learning, loading, runTypes, system, toast, tools
├── views/            # ChatView, LoginView, LearningView, SettingsView, ToolsView
└── views/v8/         # DashboardView, ChatView, RunsView, RunConsoleView,
                      # AgentsView, ModelsView, MemoryView, AuditView, SystemView
```

## Commandes

```bash
# Tests backend
cd backend && ../.venv/bin/python -m pytest tests/ -x -q

# Tests frontend
cd frontend && npx vitest run

# Demarrer backend
cd backend && ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001

# Demarrer frontend dev
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Lint backend
cd backend && ../.venv/bin/ruff check app/
```

## Points critiques - NE PAS MODIFIER SANS COMPRENDRE

### WebSocket Events (invariants stricts)
- Tout event DOIT avoir : `type`, `timestamp` (ISO 8601), `run_id`
- Tout run DOIT se terminer par EXACTEMENT UN `complete` OU `error`
- Fichiers : `ws_events.py` (modeles), `event_emitter.py` (emission)

### Securite (fail-closed)
- `secure_executor.py` - sandbox argv, allowlist/blocklist commandes
- `governance.py` - approbation actions, fail-closed par defaut
- `prompt_injection_detector.py` - detection injections prompt
- `security.py` - JWT, HttpOnly cookies, CSP headers

### Agents (isolation)
- Chaque agent a un set `allowed_tools` - verification dans `registry.py`
- 6 agents : system.health, docker.monitor, unifi.monitor, web.researcher, self_improve, qa.runner

### Learning (ChromaDB)
- `memory.py` - memoire durable avec cleanup automatique
- `feedback.py` - systeme de feedback utilisateur
- `evaluator.py` - evaluation qualite des reponses

## Tests - Etat actuel (fevrier 2026)

### Backend : 424 passes, 0 echoues
- Tous les tests passent (y compris tool_regression, api_chat, robustness)

### Frontend : 158 passes, 0 echoues
- Tous les 8 fichiers de tests passent

## Fichiers cles par tache

| Tache | Fichiers | Tests associes |
|-------|----------|----------------|
| Corriger test backend | `backend/tests/test_*.py` | - |
| Nouvel outil | `backend/app/services/react_engine/tools.py` | `tests/test_tools.py`, `tests/tool_regression/` |
| Nouvel agent | `backend/app/services/agents/registry.py` | `tests/test_agents.py` |
| Event WS | `backend/app/services/websocket/event_emitter.py` | `tests/test_ws_*.py` |
| Vue UI | `frontend/src/views/v8/` | `frontend/tests/` |
| Store Pinia | `frontend/src/stores/chat.js` | `frontend/tests/stores/chat*.js` |
| Securite | DEMANDER CONFIRMATION AVANT | `tests/test_security.py`, `tests/test_secure_executor.py` |

## Workflow de correction recommande

```
1. Identifier le probleme exact (message d'erreur complet)
2. Lire le fichier source ET le fichier de test
3. Comprendre ce qui a change (git diff, git log)
4. Modifier LE MINIMUM necessaire
5. Lancer les tests cibles : pytest tests/test_<module>.py -v
6. Verifier qu'aucun autre test n'a casse
7. Commit avec message descriptif
```

## NE PAS UTILISER

- `pip install` sans `--break-system-packages`
- `source` dans sh - utiliser `. .venv/bin/activate` ou appeler directement `.venv/bin/python`
