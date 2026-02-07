# AI Orchestrator - Instructions pour Claude Code

## ⚠️ RÈGLES NON-NÉGOCIABLES

### AVANT de modifier quoi que ce soit :
1. **LIRE** le fichier concerné EN ENTIER avant de le modifier
2. **COMPRENDRE** les dépendances (imports, appelants, tests associés)
3. **VÉRIFIER** qu'un test existe pour ce fichier (`tests/test_<module>.py`)
4. **CRÉER un backup** si le fichier fait plus de 50 lignes : `cp fichier.py fichier.py.bak`

### INTERDICTIONS ABSOLUES :
- ❌ **NE JAMAIS réécrire un fichier entier** — modifier uniquement les lignes nécessaires
- ❌ **NE JAMAIS supprimer une fonction/classe** sans vérifier qu'elle n'est importée nulle part
- ❌ **NE JAMAIS modifier plus de 3 fichiers** dans une même intervention sans validation
- ❌ **NE JAMAIS modifier la sécurité** (secure_executor.py, governance.py, security.py) sans demander confirmation
- ❌ **NE JAMAIS modifier les modèles Pydantic** (schemas.py, ws_events.py, workflow.py) sans vérifier les dépendants
- ❌ **NE JAMAIS toucher à tools.py** (2260 lignes) sans raison critique documentée
- ❌ **NE JAMAIS utiliser `datetime.utcnow()`** — utiliser `datetime.now(timezone.utc)`
- ❌ **NE JAMAIS utiliser `class Config:` dans Pydantic** — utiliser `model_config = ConfigDict(...)`

### AVANT chaque commit :
1. Lancer `cd backend && python -m pytest tests/ -x -q` (stop au premier échec)
2. Lancer `cd frontend && npx vitest run` si des fichiers frontend ont été modifiés
3. Vérifier que le nombre de tests passants n'a PAS diminué
4. Message de commit au format : `fix(module): description courte`

## Version actuelle
v8.0.5 backend / v8.1-ui-refactor (branche courante)

## Architecture

### Backend (FastAPI) — `/backend/app/`
```
app/
├── api/              # Routes REST + middleware
│   ├── v1/           # auth, chat, conversations, learning, system, tools
│   └── routes/       # agents
├── core/             # Config, DB, logging, security, metrics, scheduler
├── models/           # schemas.py, workflow.py, ws_events.py
└── services/
    ├── agents/       # base.py, registry.py (5 agents définis)
    ├── learning/     # context_enricher, evaluator, feedback, memory
    ├── ollama/       # client.py, categorizer.py
    ├── react_engine/ # engine, tools (34), governance, secure_executor, 
    │                 # verifier, workflow_engine, self_improve, memory,
    │                 # prompt_injection_detector, runbooks, learning_wrapper
    └── websocket/    # event_emitter.py, exceptions.py
```

### Frontend (Vue 3 + Pinia) — `/frontend/src/`
```
src/
├── assets/css/       # main.css
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
# Tests backend (depuis la racine du projet)
cd backend && ../.venv/bin/python -m pytest tests/ -x -q

# Tests backend sans les fichiers cassés (temporaire)
cd backend && ../.venv/bin/python -m pytest tests/ -x -q \
  --ignore=tests/test_correlation_id.py \
  --ignore=tests/test_strict_csp.py

# Tests frontend
cd frontend && npx vitest run

# Démarrer backend
cd backend && ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001

# Démarrer frontend dev
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Lint backend
cd backend && ../.venv/bin/ruff check app/
```

## Points critiques — NE PAS MODIFIER SANS COMPRENDRE

### WebSocket Events (invariants stricts)
- Tout event DOIT avoir : `type`, `timestamp` (ISO 8601), `run_id`
- Tout run DOIT se terminer par EXACTEMENT UN `complete` OU `error`
- Fichiers : `ws_events.py` (modèles), `event_emitter.py` (émission)

### Sécurité (fail-closed)
- `secure_executor.py` — sandbox argv, allowlist/blocklist commandes
- `governance.py` — approbation actions, fail-closed par défaut
- `prompt_injection_detector.py` — détection injections prompt
- `security.py` — JWT, HttpOnly cookies, CSP headers

### Agents (isolation)
- Chaque agent a un set `allowed_tools` — vérification dans `registry.py`
- 5 agents définis : system.health, docker.monitor, unifi.monitor, web.researcher, self_improve

### Learning (ChromaDB)
- `memory.py` — mémoire durable avec cleanup automatique
- `feedback.py` — système de feedback utilisateur
- `evaluator.py` — évaluation qualité des réponses

## Tests — État actuel (février 2026)

### Backend : 403 passés, 0 échoués
- ⚠️ `test_correlation_id.py` — ignoré (erreur collection import)
- ⚠️ `test_strict_csp.py` — ignoré (erreur collection import)
- ✅ Tous les autres tests passent (y compris tool_regression, api_chat, robustness)

### Frontend : 158 passés, 0 échoués
- ✅ Tous les 8 fichiers de tests passent

## Fichiers clés par tâche

| Tâche | Fichiers | Tests associés |
|-------|----------|----------------|
| Corriger test backend | `backend/tests/test_*.py` | — |
| Nouvel outil | `backend/app/services/react_engine/tools.py` | `tests/test_tools.py`, `tests/tool_regression/` |
| Nouvel agent | `backend/app/services/agents/registry.py` | `tests/test_agents.py` |
| Event WS | `backend/app/services/websocket/event_emitter.py` | `tests/test_ws_*.py` |
| Vue UI | `frontend/src/views/v8/` | `frontend/tests/` |
| Store Pinia | `frontend/src/stores/chat.js` | `frontend/tests/stores/chat*.js` |
| Sécurité | ⚠️ DEMANDER CONFIRMATION AVANT | `tests/test_security.py`, `tests/test_secure_executor.py` |

## Workflow de correction recommandé

```
1. Identifier le problème exact (message d'erreur complet)
2. Lire le fichier source ET le fichier de test
3. Comprendre ce qui a changé (git diff, git log)
4. Modifier LE MINIMUM nécessaire
5. Lancer les tests ciblés : pytest tests/test_<module>.py -v
6. Vérifier qu'aucun autre test n'a cassé
7. Commit avec message descriptif
```

## NE PAS UTILISER

- `docker compose` — utiliser `./stack.sh` depuis unified-stack/
- L'ancienne stack `4lb-docker-stack` — archivée
- `pip install` sans `--break-system-packages`
- `source` dans sh — utiliser `. .venv/bin/activate` ou appeler directement `.venv/bin/python`
