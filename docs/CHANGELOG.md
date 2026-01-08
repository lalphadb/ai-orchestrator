# Changelog AI Orchestrator

## [6.1.0] - 2026-01-08

### 🚀 Nouvelles fonctionnalités

#### Pipeline Workflow complet
- **Workflow Engine** : Orchestre Spec→Plan→Execute→Verify→Repair
- **Verifier Service** : Second modèle LLM pour validation critique
- **7 outils QA** : git_status, git_diff, run_tests, run_lint, run_format, run_build, run_typecheck

#### Sécurité renforcée
- Allowlist obligatoire (31 commandes)
- Blocklist de sécurité (31 commandes dangereuses)
- Sandbox Docker par défaut (--network=none, --read-only)
- Workspace isolé (/home/lalpha/orchestrator-workspace)
- ToolResult standardisé {success, data, error, meta}

### ⚙️ Configuration
```env
EXECUTOR_MODEL, VERIFIER_MODEL, VERIFY_REQUIRED, MAX_REPAIR_CYCLES
WORKSPACE_DIR, EXECUTE_MODE, SANDBOX_IMAGE
COMMAND_ALLOWLIST, COMMAND_BLOCKLIST
```

### 📡 API enrichie
- `/api/v1/chat` retourne verification + verdict
- `/api/v1/chat/simple` endpoint legacy
- WebSocket avec phases en temps réel

### 📁 Fichiers
- `app/models/workflow.py` (nouveau)
- `app/services/react_engine/verifier.py` (nouveau)
- `app/services/react_engine/workflow_engine.py` (nouveau)
- `app/core/config.py` (modifié)
- `app/services/react_engine/tools.py` (modifié)
- `app/api/v1/chat.py` (modifié)

---

## [6.0.0] - 2026-01-07

### 🚀 Refonte complète
- Backend FastAPI + SQLAlchemy
- Frontend Vue.js 3 + Pinia + Tailwind
- WebSocket streaming
- ReAct Engine avec 9 outils
- Authentification JWT
