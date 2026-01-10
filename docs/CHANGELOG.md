# Changelog AI Orchestrator

## [6.2.1] - 2026-01-09

### 🚀 Nouvelles fonctionnalités

#### Nouvel outil list_llm_models
- **Catégorisation automatique** : Classe les modèles en General, Code, Vision, Embedding, Safety, Cloud
- **Statistiques** : Total, modèles locaux vs cloud, taille totale
- **Format structuré** : Réponse JSON prête pour le frontend ModelsDisplay

#### Auto-récupération E_DIR_NOT_FOUND
- **Recherche automatique** : Quand un chemin n'existe pas, search_directory est appelé automatiquement
- **Suggestions** : Le LLM reçoit des alternatives de chemins pour retenter
- **Intégré à engine.py** : Fonctionne pour E_DIR_NOT_FOUND, E_FILE_NOT_FOUND, E_PATH_NOT_FOUND

#### WebSocket Re-verify et Force Repair
- **run_qa_checks()** : Nouvelle méthode workflow_engine pour exécuter des checks sans TaskSpec
- **handle_rerun_verify()** : Corrigé pour utiliser run_qa_checks()
- **handle_force_repair()** : Opérationnel avec prompt de réparation

#### Frontend amélioré
- **RunInspector** : Nouveau design avec icônes de phases, onglet Thinking, meilleure visualisation
- **ModelsDisplay** : Meilleure détection du format JSON structuré
- **CategorySection** : Affichage propre par catégorie de LLM

### 📁 Fichiers modifiés
- `backend/app/services/react_engine/tools.py` : +list_llm_models
- `backend/app/services/react_engine/engine.py` : +auto-recovery
- `backend/app/services/react_engine/workflow_engine.py` : +run_qa_checks()
- `backend/app/api/v1/chat.py` : Correction handle_rerun_verify
- `frontend/src/components/chat/RunInspector.vue` : Design amélioré
- `frontend/src/components/chat/MessageList.vue` : Meilleure détection modèles

---

## [6.2.0] - 2026-01-08

### 🚀 Nouvelles fonctionnalités

#### Erreurs récupérables
- **Classification des erreurs** : RECOVERABLE_ERRORS vs erreurs fatales
- **is_recoverable_error()** : Fonction pour vérifier si une erreur est récupérable
- **fail() amélioré** : Inclut maintenant le flag `recoverable` dans la réponse

#### Nouvel outil search_directory
- **Recherche sécurisée** de répertoires dans le système
- **Allowlist de bases** : /home, /workspace, /tmp, /var/www, /opt, WORKSPACE_DIR
- **Limites de sécurité** : max_depth=3, max_results=5
- **Auto-correction** : Appelé automatiquement sur E_DIR_NOT_FOUND

#### WebSocket enrichi
- **Événement `phase`** : Changement de phase du workflow (spec/plan/execute/verify/repair/complete)
- **Événement `verification_item`** : Item de vérification QA (running/passed/failed)
- **run_id** : Identifiant unique pour chaque exécution

#### Frontend Orchestrator UI
- **Workflow Stepper** : Visualisation des 6 phases avec état courant
- **Tabs Tools/QA/Raw** : Organisation des informations d'exécution
- **Verification Display** : Liste des checks QA avec statut
- **Verdict Display** : PASS (vert) / FAIL (rouge) avec issues
- **Actions** : Re-verify, Force Repair, Export Report

### 📁 Fichiers modifiés
- `app/services/react_engine/tools.py` (+80 lignes)
- `app/services/react_engine/workflow_engine.py` (+40 lignes)
- `frontend/src/services/wsClient.js` (+10 lignes)
- `frontend/src/stores/chat.js` (+60 lignes)
- `frontend/src/components/chat/RunInspector.vue` (réécriture complète)
- `docs/WORKFLOW_CONVENTIONS.md` (nouveau)
- `tests/test_tools.py` (+50 lignes)

### 📝 Documentation
- `WORKFLOW_CONVENTIONS.md` : Conventions du pipeline workflow et WebSocket

---

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
