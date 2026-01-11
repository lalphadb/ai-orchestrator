# 🔍 AUDIT — AI Orchestrator v7.0

**Date :** 2026-01-11  
**Auditeur :** Codex (GPT-5)  
**Version auditée (commit/tag) :** 020877e739f233ddaa105fa5f63d3d2a0ee48278

---

## 1️⃣ Résumé exécutif
**Verdict global :**
- [ ] Conforme
- [ ] Partiellement conforme
- [x] Non conforme

**Écart principal (docs ↔ config ↔ code ↔ flux réel) :**
> La documentation promet un SecureExecutor sandboxé et une gouvernance obligatoire (docs/INDEX.md, docs/SECURITY.md, docs/AUDIT-REPORT-v7.0.md), mais la configuration force `EXECUTE_MODE=direct`, autorise `docker/systemctl/curl` même pour le rôle viewer, et aucune action n’est soumise au GovernanceManager sur le flux réel (`backend/.env`, `backend/app/services/react_engine/secure_executor.py`, `backend/app/services/react_engine/tools.py`).

**Risques majeurs :**
- L’agent peut redémarrer services, conteneurs ou exécuter `apt` directement sur l’hôte sans sandbox ni veto.
- Les runbooks annoncés comme « sécurisés » exécutent des commandes `sudo`, des pipes et des redirections non bloqués et ne sont pas intégrés au workflow.

---

## 2️⃣ Documentation de référence analysée (docs/)
> ⚠️ La documentation n’est PAS une preuve de fonctionnement.

| Fichier | Promesse clé |
|--------|---------------|
| docs/INDEX.md | Vue d’ensemble v7.0 : SecureExecutor sandbox, 28 outils catégorisés, gouvernance obligatoire, mémoire durable, UI contrôlée. |
| docs/ARCHITECTURE.md | Architecture réseau + modules (SecureExecutor, GovernanceManager, RunbookRegistry, 28 outils, sandbox Docker). |
| docs/ARCHITECTURE-v6.1.md | Pipeline SPEC→PLAN→EXECUTE→VERIFY→REPAIR présenté comme séquentiel obligatoire avec allowlist stricte et sandbox Docker. |
| docs/SECURITY.md | Définit SecureExecutor v7 (jamais `shell=True`, sandbox par défaut, `FORBIDDEN_CHARS`, rôles VIEWER→ADMIN, bloque `; && || |`), gouvernance (classification READ→CRITICAL, justification, rollback) et outils à capacités (systemd/docker). |
| docs/TOOLS.md | Inventorie 18 outils v6.2.1, insiste sur allowlist/blocklist centralisée et sur l’usage d’outils spécialisés (pas de commandes brutes). |
| docs/RUNBOOKS.md | 9 runbooks « atomiques » : chaque étape doit utiliser un outil spécialisé, sans shell chaining, avec vérification/rollback. |
| docs/API.md | API REST/WebSocket v6 (auth, chat, conversations, outils, WS streaming). |
| docs/WEBSOCKET.md | Protocole WS v6 : événements `phase`, `verification_item`, `tool`, `complete`, `run_id` constant. |
| docs/CONFIGURATION.md | Guide `.env` v6 : `SECRET_KEY` obligatoire, sandbox par défaut, variables MAX_ITERATIONS, TOOL_TIMEOUT. |
| docs/INSTALLATION.md | Installation manuelle v6 (Python + Node, uvicorn, npm). |
| docs/DEPLOYMENT.md | Déploiement systemd backend v6.5 + frontend nginx, commandes `systemctl`, `docker`. |
| docs/DEVELOPMENT.md | Conventions dev (Black, Ruff, mypy, npm), structure du repo, instructions tests. |
| docs/ROADMAP.md | Objectifs v6.2→v7 (SecureExecutor, gouvernance, streaming QA, 30+ outils). |
| docs/WORKFLOW_CONVENTIONS.md | Workflow SPEC→PLAN→EXECUTE→VERIFY→REPAIR, événements WS, ToolResult contract, codes erreurs récupérables. |
| docs/CHANGELOG.md | Journal v7 : SecureExecutor sans `shell=True`, classification gouvernance, 28 outils, sandbox par défaut. |
| docs/CHANGELOG-RECENT.md | Focus v7.0 : mode sandbox, rôles, rollback, 39 outils, runbooks sécurisés. |
| docs/AUDIT-REPORT-v7.0.md | Audit précédent : confirme sandbox obligatoire, gouvernance effective, runbooks refactorés, 97 tests passés. |
| docs/AUDIT-REPORT-v6.1.md | Audit v6.1 : allowlist de 31 commandes, sandbox Docker, workspace isolé, 48 tests PASS. |
| docs/TROUBLESHOOTING.md | Procédures de dépannage (service, Ollama, frontend, auth, WebSocket). |
| docs/INSTRUCTION_CLAUDE.md | Mandat audit-only : ne pas modifier le code, produire AUDIT_v7.0.md, vérifier doc/config/code/UI pessimiste. |
| docs/Audit/PLAN_CORRECTION_CONSOLIDE_v6.2.md | Plan de correction multi-audits : reconnaît boutons Re-verify/Force repair à câbler, auto-recovery à implémenter, doc honnête requise. |
| docs/AUDIT_PLAN_TEMPLATE.md | Checklist d’audit obligatoire (docs → config → code → flux → sécurité). |
| docs/AUDIT_TEMPLATE.md | Modèle de rapport (présent document). |
| docs/META_AUDIT_TEMPLATE.md | Modèle meta-audit (à ne pas remplir). |

---

## 3️⃣ Périmètre réellement audité
### Backend
- Fichiers lus :
  - `backend/app/core/config.py`
  - `backend/.env`
  - `backend/app/api/v1/chat.py`, `system.py`, `tools.py`
  - `backend/app/services/react_engine/{secure_executor.py,tools.py,runbooks.py,governance.py,workflow_engine.py,engine.py,verifier.py}`
  - `backend/app/services/ollama/client.py`
  - `backend/main.py`

### Frontend
- Fichiers lus :
  - `frontend/src/stores/chat.js`
  - `frontend/src/components/chat/RunInspector.vue`
  - `frontend/src/components/chat/MessageInput.vue`
  - `frontend/src/services/wsClient.js`
  - `frontend/src/views/ChatView.vue`
  - `frontend/src/services/api.js`

### Configuration (OBLIGATOIRE)
- [x] config.py
- [x] .env
- [ ] overrides runtime (non fournis)

### ⚠️ Non audité (déclaré)
- Répertoires docs/api/, docs/examples/, docs/files.zip, docs/guides (non requis par mandat).
- Modules backend `app/services/learning/*`, jobs externes.
- Tests automatisés non ré-exécutés (lecture uniquement).

---

## 4️⃣ Audit BACKEND — Conformité v7.0

### 4.1 Workflow réel (SPEC→PLAN→EXECUTE→VERIFY→REPAIR→COMPLETE)
| Phase | Existe | Exécutée | Obligatoire | Observations |
|------|--------|----------|-------------|--------------|
| SPEC | ☑ | ☐ | ☐ | `_is_simple_request()` saute SPEC pour messages courts ou `skip_spec=True` (force repair) ; aucune preuve que toutes les requêtes passent par SPEC (`backend/app/services/react_engine/workflow_engine.py:130-153`). |
| PLAN | ☑ | ☐ | ☐ | PLAN n’est généré que si SPEC est exécuté ; toute question « simple » part directement en EXECUTE (`workflow_engine.py:165-183`). |
| EXECUTE | ☑ | ☑ | ☐ | Toujours utilisé (ReAct Engine), mais dépend entièrement du LLM ; aucun garde-fou gouvernance. |
| VERIFY | ☑ | ☐ | ☐ | `VERIFY_REQUIRED=False` (config.py:74-76 + backend/.env:21), donc la vérification QA complète est désactivée et remplacée par `quick_check`. |
| REPAIR | ☑ | ☐ | ☐ | REPAIR ne s’active que si VERIFY a tourné et renvoie FAIL ; sinon le bouton « Force repair » ré-exécute un nouveau run `skip_spec=True` au lieu de passer par ce cycle (`chat.py:264-325`). |

### 4.2 SecureExecutor (sécurité déclarée by design)
- `shell=True` absent : ☑ Oui (utilise `asyncio.create_subprocess_exec`, secure_executor.py:297-322)
- Parsing argv strict (shlex) : ☑ Oui (`_parse_command_safe`, secure_executor.py:150-176)
- Blocage injections (`; && || | \` $()`) : ☑ Oui (`FORBIDDEN_CHARS`, secure_executor.py:63-78)
- Mode effectif (sandbox/direct) : ☒ Direct (`backend/.env:25-26`)

Observations :
> - `.env` force `EXECUTE_MODE=direct`, contournant la promesse sandbox (docs/SECURITY.md, docs/CHANGELOG.md). Les commandes s’exécutent donc sur l’hôte (`secure_executor.py:284-323`).
> - L’allowlist réelle est celle de `ALLOWED_COMMANDS` (secure_executor.py:82-114) qui autorise `docker`, `systemctl`, `curl`, `wget` même pour VIEWER, alors que `settings.COMMAND_BLOCKLIST` interdit ces binaires (config.py:118-153) mais n’est jamais consultée par SecureExecutor.
> - Aucune isolation workspace : `systemctl restart`, `docker restart`, `apt install` fonctionnent directement via `execute_command` (tools.py:322-335, 338-348).

### 4.3 GovernanceManager
- Classification READ→CRITICAL : ☒ Non (la fonction existe mais n’est jamais appelée dans les outils réels ; aucun `prepare_action` hors tests)
- Veto réel sur CRITICAL : ☒ Non (aucun appel à `governance_manager.prepare_action` avant `execute_command`, tools.py:272-319)
- Audit trail exploitable : ☒ Non (history n’est alimenté que si `prepare_action` est invoqué ; flux réel n’utilise que `secure_executor.audit_log` sans notion de catégorie)
- Rollback actionnel : ☒ Non (`rollback_action` existe mais dépend d’un `action_id` inexistant car aucune action n’enregistre de rollback, tools.py:1099-1147)

Observations :
> - La documentation (docs/SECURITY.md) impose justification et rollback pour actions SENSITIVE/CRITICAL, mais aucun outil ne demande de justification ni n’appelle le GovernanceManager. Tous les boutons UI et le moteur ReAct contournent totalement ce module.

### 4.4 RunbookRegistry
- Nombre annoncé : 9 → ☑ 9 runbooks enregistrés (`runbooks.py:302-438`)
- Appelés via registre (pas contournés) : ☒ Non (aucun composant ne consomme `runbook_registry` hormis les outils de listage `list_runbooks/get_runbook/search_runbooks`, tools.py:1299-1457)
- Bloquants si échec : ☒ Non (les steps sont de simples chaînes `command="sudo ..."`, aucun lien avec un exécuteur ou un rollback).

Observations :
> - Les runbooks contiennent des commandes `sudo systemctl restart ai-orchestrator`, `docker system prune -f`, `sudo journalctl --vacuum-time=7d`, `sudo journalctl ... | grep ...` (runbooks.py:325-368, 420-438). Cela contredit la doc « étapes atomiques via outils spécialisés » (docs/RUNBOOKS.md) et fait sortir de la workspace/allowlist.

### 4.5 Outils (28 annoncés)
| Catégorie | Existent | Appel auto | Bloquants | Observations |
|----------|----------|------------|-----------|--------------|
| system | ☑ | ☐ | ☐ | 40 `BUILTIN_TOOLS.register` (rg -c) incluent `systemd_*`, `docker_*`, `apt_*`, `execute_command` ; aucun n’est invoqué automatiquement par le workflow, l’agent doit les choisir. |
| filesystem | ☑ | ☐ | ☐ | `read_file/write_file/list_directory/search_*` valident le workspace mais ne sont pas imposés. |
| qa | ☑ | ☐ | ☐ | QA tools (`run_tests`, `run_lint`, etc.) ne tournent que si `VERIFY_REQUIRED=True` ou via re-verify manuel limité (`workflow_engine.py:472-519`). |
| governance | ☑ | ☐ | ☐ | Seulement `get_action_history/get_pending_verifications/rollback_action`, aucune intégration exécutoire. |
| memory | ☑ | ☐ | ☐ | `memory_remember/recall/context` disponibles mais jamais appelés automatiquement. |
| runbook | ☑ | ☐ | ☐ | `list/get/search_runbooks` uniquement, pas d’exécution. |
| network | ☑ | ☐ | ☐ | `http_request` autorisé, pas contrôlé par gouvernance. |
| utility | ☑ | ☐ | ☐ | `calculate`, `list_llm_models`, simple lecture. |

### 4.6 Erreurs récupérables (cas obligatoire)
**Cas testé :** chemin invalide (`E_DIR_NOT_FOUND`)
- Arrêt immédiat : ☒ (le moteur n’arrête pas mais n’exécute pas de nouvelle commande utile)
- Tentative alternative (système) : ☑ (déclenche `search_directory` interne, engine.py:230-333)
- Suggestion utilisateur : ☑ (ajoute `recovery_hint` au prompt suivant, engine.py:280-333)

Conclusion :
> L’« auto-recovery » se limite à lancer `search_directory` côté serveur puis à insérer un paragraphe suggérant des chemins. Aucun re-run automatique ni fallback outil n’est exécuté ; on reste dépendant du LLM pour décider quoi faire ensuite.

---

## 5️⃣ Audit FRONTEND — Orchestrator UI

### 5.1 Notion de RUN
- run_id bout-en-bout : ☒ Non — l’UI crée un `run.id = Date.now()` local et ignore `run_id` envoyé par le backend (`frontend/src/stores/chat.js:334-357`, `wsClient.js:105-166`).
- Statut global : ☑ Oui — `RunInspector` affiche `workflowPhase`/`verdict` (`RunInspector.vue:285-305`).
- Durée : ☑ Oui — calcul local `endTime - startTime` (chat.js:146-165) mais pas synchronisé avec le backend.
- Verdict visible : ☑ Oui — badge PASS/FAIL affiché (RunInspector.vue:275-307).
- Modèles affichés : ☑ Oui — sélecteur de modèles lit `chat.availableModels` (MessageInput.vue:5-28), basé sur `/system/models` ou WS `models`.

### 5.2 Visualisation du workflow
- Stepper/timeline : ☑ Oui (`RunInspector.vue`: workflow phases + icons).
- Phases visibles : ☑ Oui (Spec/Plan/Exec/QA/Fix/Done labels, RunInspector.vue:360-434).
- États/durées : ☒ Partiel — aucun minuteur par phase, seulement durée totale estimée.

### 5.3 Run Inspector
| Onglet | Présent | Fonctionnel | Observations |
|------|---------|-------------|--------------|
| Tools | ☑ | ☑ | Liste les `toolCalls` enregistrées localement. |
| Verification | ☑ | ☒ | UI affiche un onglet QA mais `verificationItems` reste vide si VERIFY_REQUIRED=False ; les re-verify n’y réinjectent que deux checks (`git_status`, `run_lint`). |
| Diff | ☒ | ☒ | Aucun onglet Diff dans `tabs` (RunInspector.vue:381-385) malgré la présence attendue dans le modèle audit. |
| Raw | ☑ | ☑ | JSON brut du run courant (`RunInspector.vue:259-268`). |

### 5.4 Actions utilisateur
| Action | Visible | Handler backend | Conforme |
|------|---------|------------------|----------|
| Re-verify | ☑ | ☑ (`chat.rerunVerification()` envoie `action: 'rerun_verify'`, chat.js:500-520) | ☒ Limité — le backend ne relance que `git_status` et `run_lint` (workflow_engine.py:471-519) au lieu du pipeline complet promis. |
| Force repair | ☑ (seulement si verdict FAIL) | ☑ (`chat.forceRepair()` → `action: 'force_repair'`, chat.js:528-550) | ☒ L’UI incrémente `repairCycles` localement sans se synchroniser sur `run_id`; le backend relance un run `skip_spec=True` qui n’apparaît pas comme cycle REPAIR (workflow_engine.py:133-151). |

---

## 6️⃣ Tableau de conformité
| Promesse (docs) | Config | Code | Flux réel | Statut |
|-----------------|--------|------|-----------|--------|
| SecureExecutor sandbox + allowlist restrictive (docs/INDEX.md, docs/SECURITY.md, docs/CHANGELOG.md) | `.env` force `EXECUTE_MODE=direct` (backend/.env:25-26) | `secure_executor.ALLOWED_COMMANDS` autorise `docker/systemctl/curl` pour VIEWER (secure_executor.py:82-114) | Commandes critiques s’exécutent sur l’hôte via `execute_command` (tools.py:272-337) | ❌ Non conforme |
| Gouvernance obligatoire sur actions CRITICAL (docs/SECURITY.md, docs/AUDIT-REPORT-v7.0.md) | Aucun paramètre d’activation | `execute_command` n’appelle jamais `governance_manager.prepare_action` (tools.py:272-319) | Aucun veto/rollback observé ; seuls les outils de lecture exposent l’historique | ❌ Non conforme |
| Runbooks sécurisés utilisant outils spécialisés sans shell chaining (docs/RUNBOOKS.md) | N/A | `RunbookRegistry` stocke des `command="sudo ..."` et des pipes (`runbooks.py:325-438`) | Runbooks non exécutés automatiquement ; si lancés, ils contourneraient allowlist et sandbox inexistante | ❌ Non conforme |
| Workflow complet SPEC→PLAN→EXECUTE→VERIFY→REPAIR obligatoire (docs/ARCHITECTURE.md, docs/WORKFLOW_CONVENTIONS.md) | `VERIFY_REQUIRED=false`, `MAX_REPAIR_CYCLES=2` (config.py:74-76, backend/.env:21-23) | `_is_simple_request` saute SPEC/PLAN, `verify_required` court-circuite QA (workflow_engine.py:130-235) | UI affiche un stepper mais la majorité des runs ne passent qu’en EXECUTE + quick check | ⚠️ Partiel |
| 28 outils catalogués (docs/INDEX.md, docs/TOOLS.md) | — | 40 enregistrements `BUILTIN_TOOLS.register` (tools.py) dont certains redondants | UI/agent voient des noms non documentés ; doc obsolète (18 outils v6.2.1) | ⚠️ Partiel |
| WS `run_id` bout-en-bout (docs/WEBSOCKET.md) | — | Backend envoie `run_id` (workflow_engine.py:696-719) | UI ignore `run_id` et affiche un timestamp local (chat.js:334-357), empêchant la traçabilité | ❌ Non conforme |

---

## 7️⃣ Écarts critiques (sans correction)
- **Fait :** L’exécution se fait en mode direct, sans sandbox, avec des commandes privilégiées autorisées pour le rôle viewer (`backend/.env:25-26`, `secure_executor.py:82-114`).  
  **Impact :** L’agent peut modifier des services système, gérer Docker ou installer des paquets sans supervision, contrairement aux promesses de confinement.  
  **Gravité :** 🔴 Critique.

- **Fait :** La gouvernance n’est jamais invoquée sur les actions réelles ; aucune justification ni rollback n’est enregistrée (`tools.py:272-319`, absence totale de `governance_manager.prepare_action`).  
  **Impact :** Les actions CRITICAL (écriture disque, redémarrages) passent sans veto, ce qui annule l’objectif de conformité/traçabilité.  
  **Gravité :** 🔴 Critique.

- **Fait :** Les runbooks décrits comme « procédures sécurisées » ne sont que des chaînes shell (`sudo`, pipes, redirections) non exécutées via des outils contrôlés (`runbooks.py:302-438`).  
  **Impact :** Aucun garde-fou lors des automatisations : si un agent applique ces runbooks, il sort de toute allowlist et peut provoquer des dégâts irréversibles.  
  **Gravité :** 🟠 Majeur.

---

## 8️⃣ Verdict final
> Le système audité ne respecte pas les promesses v7 : la configuration runtime force l’exécution directe, l’allowlist réelle autorise les commandes critiques, la gouvernance/rollback documentée n’est jamais appliquée, et les runbooks/UI ne garantissent pas le workflow annoncé. La conformité v7.0 est donc **refusée** tant que la sandbox, la gouvernance et les contrôles d’exécution ne sont pas effectifs.
