# 🔍 AUDIT — AI Orchestrator v7.0

**Date :** 2026-01-11
**Auditeur :** Claude (MCP)
**Version auditée :** v7.0 (commit 020877e)

---

## 1️⃣ Résumé exécutif

**Verdict global :**
- [ ] Conforme
- [x] Partiellement conforme
- [ ] Non conforme

**Écart principal (docs ↔ config ↔ code ↔ flux réel) :**
> Le système promet une sécurité "by design" avec sandbox par défaut, gouvernance obligatoire et vérification QA systématique. **En réalité**, le mode est configuré en "direct" (pas de sandbox), la gouvernance n'est pas intégrée aux outils, et la vérification QA est désactivée par défaut.

**Risques majeurs :**
- **CRITIQUE**: Mode d'exécution en "direct" malgré la promesse de sandbox par défaut
- **CRITIQUE**: Vérification QA désactivée (VERIFY_REQUIRED=false) → pas de tests automatiques
- **ÉLEVÉ**: Gouvernance non intégrée → justifications acceptées mais jamais vérifiées
- **ÉLEVÉ**: Runbooks non imposés → procédures optionnelles, pas obligatoires
- **MOYEN**: Secrets par défaut non changés (JWT_SECRET_KEY, ADMIN_PASSWORD)

---

## 2️⃣ Documentation de référence analysée (docs/)

> ⚠️ La documentation n'est PAS une preuve de fonctionnement.

| Fichier | Promesse clé | Observation |
|---------|--------------|-------------|
| docs/INDEX.md | v7.0 avec SecureExecutor (no shell=True), GovernanceManager (rollback), 28 outils | ✅ SecureExecutor conforme, ❌ Governance non intégrée, ⚠️ 40 outils (pas 28) |
| docs/ARCHITECTURE.md | Workflow 6 phases (SPEC→PLAN→EXECUTE→VERIFY→REPAIR→COMPLETE) | ⚠️ Phases conditionnelles, VERIFY désactivée par défaut |
| docs/SECURITY.md | Sandbox par défaut, shell=False, argv strict, blocage injections, gouvernance avec veto | ✅ shell=False conforme, ❌ Sandbox NOT default (mode=direct), ❌ Veto non implémenté |
| docs/TOOLS.md | 18 outils (doc obsolète v6.2.1) | ⚠️ Documentation obsolète, 40 outils actuellement |
| docs/WEBSOCKET.md | Streaming avec events phase, verification_item, complete avec verdict | ✅ Implémentation conforme dans workflow_engine.py |
| docs/RUNBOOKS.md | 9 procédures standardisées imposées | ⚠️ 9 runbooks présents mais NON imposés |

**Conclusion docs:** Documentation v7.0 décrit un système sécurisé "by design" avec sandbox, gouvernance stricte et QA obligatoire. La réalité est différente.

---

## 3️⃣ Périmètre réellement audité

### Backend
**Fichiers lus :**
- `backend/app/core/config.py` - Configuration par défaut
- `backend/.env` - Configuration runtime (PRIORITÉ)
- `backend/app/services/react_engine/workflow_engine.py` - Workflow 6 phases
- `backend/app/services/react_engine/secure_executor.py` - Exécution sécurisée
- `backend/app/services/react_engine/governance.py` - Gouvernance
- `backend/app/services/react_engine/runbooks.py` - Runbooks
- `backend/app/services/react_engine/tools.py` - 40 outils (1480 lignes)

### Frontend
**Non audité** (focus sur backend/config/flow)

### Configuration (OBLIGATOIRE)
- [x] config.py (lignes 1-178)
- [x] backend/.env (27 lignes)
- [x] Valeurs runtime vérifiées

### ⚠️ Non audité (déclaré)
- Frontend Vue.js (HTML/CSS/JS)
- Tests unitaires (backend/tests/)
- Base de données SQLite
- Intégration Ollama/ChromaDB

---

## 4️⃣ Audit BACKEND — Conformité v7.0

### 4.1 Workflow réel (SPEC→PLAN→EXECUTE→VERIFY→REPAIR→COMPLETE)

| Phase | Existe | Exécutée | Obligatoire | Observations |
|------|--------|----------|-------------|--------------|
| SPEC | ☑ | ⚠️ Conditionnel | ☐ | Ligne 131-152: Skippé si `is_simple_request()` ou `skip_spec` |
| PLAN | ☑ | ⚠️ Conditionnel | ☐ | Ligne 165-170: Skippé pour requêtes simples |
| EXECUTE | ☑ | ☑ | ☑ | Ligne 172-182: Toujours exécuté |
| VERIFY | ☑ | ☐ | ☐ | **Ligne 185: `if self.verify_required:` → Désactivé (.env: VERIFY_REQUIRED=false)** |
| REPAIR | ☑ | ☐ | ☐ | Ligne 201-225: Uniquement si VERIFY activé ET verdict=FAIL |
| COMPLETE | ☑ | ☑ | ☑ | Ligne 238-263: Toujours exécuté |

**Écart critique:**
- **workflow_engine.py:92-94**: Constructor lit `settings.VERIFY_REQUIRED`
- **backend/.env:21**: `VERIFY_REQUIRED=false`
- **Conséquence**: Phase VERIFY (tests, lint, format, typecheck, git_status, git_diff) JAMAIS exécutée

**Verdict:** ❌ **NON CONFORME** - Workflow promis 6 phases obligatoires, réalité: VERIFY désactivée

---

### 4.2 SecureExecutor (sécurité déclarée by design)

**secure_executor.py - Lignes 126-416**

- `shell=True` absent : ☑ **OUI** (Ligne 300-305, 318-322: `asyncio.create_subprocess_exec(*argv)`)
- Parsing argv strict (shlex) : ☑ **OUI** (Ligne 162: `shlex.split(command)`)
- Blocage injections (`; && || | \` $()`) : ☑ **OUI** (Lignes 64-78: FORBIDDEN_CHARS + FORBIDDEN_PATTERNS)
- Mode effectif (sandbox/direct) : ☑ **DIRECT** ❌

**Mode d'exécution:**
- **config.py:83**: `EXECUTE_MODE: str = "sandbox"` (défaut promis)
- **backend/.env:26**: `EXECUTE_MODE=direct` ⚠️ **OVERRIDE vers direct**
- **secure_executor.py:284**: `if settings.EXECUTE_MODE == "sandbox":`
- **Conséquence**: Exécution DIRECTE sur l'hôte (lignes 316-322), pas de sandbox Docker

**Observations:**
```python
# secure_executor.py:284-322
if settings.EXECUTE_MODE == "sandbox":
    docker_path = shutil.which("docker")
    if docker_path:
        # Sandbox Docker (lignes 288-306)
        # --network=none, --cpus=0.5, --memory=512m
        sandbox_used = True
    else:
        # Fallback direct si docker indisponible (lignes 307-315)
        sandbox_used = False
else:
    # Mode direct - exécution sur l'hôte (lignes 316-322)
    process = await asyncio.create_subprocess_exec(*argv, ...)
```

**Verdict:** ⚠️ **PARTIELLEMENT CONFORME**
- ✅ Implémentation SecureExecutor excellente (no shell=True, argv strict, audit complet)
- ❌ Configuration runtime en mode "direct" contredit la promesse "sandbox by default"

---

### 4.3 GovernanceManager

**governance.py - Lignes 59-341**

- Classification READ→CRITICAL : ☑ **OUI** (Lignes 78-137: `classify_action()`)
- Veto réel sur CRITICAL : ☐ **NON** (Code existe mais jamais appelé)
- Audit trail exploitable : ☑ **OUI** (Lignes 64-67: action_history, rollback_registry)
- Rollback actionnel : ☑ **OUI** (Lignes 263-304: file_restore, command_inverse)

**Intégration dans tools.py:**
```bash
# Vérification si governance_manager est appelé
$ grep -c 'governance_manager.prepare_action' tools.py
0  # ❌ JAMAIS APPELÉ

$ grep -c 'governance_manager.classify_action' tools.py
0  # ❌ JAMAIS APPELÉ
```

**Observations:**
- **governance.py:147-190**: `prepare_action()` - Vérifie justification, prépare rollback
- **governance.py:176-178**: Rejette actions SENSITIVE/CRITICAL sans justification
- **tools.py:329-331**: `systemd_restart()` - Commentaire dit "governance justification expected" mais **ne vérifie rien**
- **tools.py:349**: `docker_restart()` - Accepte `justification` param mais **ne valide rien**
- **tools.py:1052-1053**: `apt_update()`, `apt_install()` - Idem, params non validés

**Verdict:** ❌ **NON CONFORME**
- ✅ Code GovernanceManager bien conçu (classification, veto, rollback)
- ❌ Gouvernance JAMAIS intégrée aux outils → justifications acceptées mais non vérifiées
- ❌ Aucun veto réel sur actions CRITICAL

---

### 4.4 RunbookRegistry

**runbooks.py - Lignes 51-447**

- Nombre annoncé : **9** (docs/RUNBOOKS.md)
- Nombre réel : **9** ✅ (Ligne 443: "9 runbooks enregistrés")
- Appelés via registre (pas contournés) : ☐ **NON** (Jamais imposés)
- Bloquants si échec : ☐ **NON** (Jamais exécutés automatiquement)

**Runbooks enregistrés:**
1. `diag-service-down` (lignes 106-142)
2. `diag-docker-container` (lignes 144-176)
3. `recover-service-restart` (lignes 180-222)
4. `recover-docker-restart` (lignes 224-255)
5. `deploy-stack-update` (lignes 259-299)
6. `deploy-ai-orchestrator` (lignes 301-337)
7. `maint-disk-cleanup` (lignes 341-376)
8. `maint-backup-create` (lignes 378-408)
9. `sec-check-services` (lignes 412-441)

**Utilisation dans tools.py:**
```python
# tools.py:1349 - Seul usage détecté
rb = runbook_registry.get(runbook_id)  # ← Récupération de métadonnées uniquement
```

**Observations:**
- Runbooks existent et sont bien structurés ✅
- Outils `list_runbooks()`, `get_runbook()`, `search_runbooks()` permettent de les consulter ✅
- **Aucune imposition** des runbooks → procédures **optionnelles**, pas obligatoires ❌
- Aucune vérification que les étapes d'un runbook sont suivies ❌

**Verdict:** ⚠️ **PARTIELLEMENT CONFORME**
- ✅ 9 runbooks présents et bien documentés
- ❌ Runbooks non imposés → procédures de référence, pas de gouvernance obligatoire

---

### 4.5 Outils (28 annoncés → 40 réels)

**tools.py - 1480 lignes, 40 registrations**

```bash
$ grep -c '^BUILTIN_TOOLS.register(' tools.py
40  # ← 40 outils, pas 28
```

| Catégorie | Annoncé | Réel | Outils | Observations |
|----------|---------|------|--------|--------------|
| **system** | 4 | 15 | execute_command, get_system_info, list_llm_models, systemd_{status,restart,logs}, docker_{list_containers,logs,restart,inspect}, network_listeners, disk_usage, apt_{update,install}, get_audit_log | ☑ Existent / ☑ Appel auto possible / ⚠️ Justifications non validées |
| **filesystem** | 5 | 5 | read_file, write_file, list_directory, search_files, search_directory | ☑ Existent / ☑ Appel auto possible / ☑ Validation workspace OK |
| **qa** | 7 | 7 | git_status, git_diff, run_tests, run_lint, run_format, run_build, run_typecheck | ☑ Existent / ☐ **Jamais appelés (VERIFY_REQUIRED=false)** |
| **governance** | 3 | 3 | get_action_history, get_pending_verifications, rollback_action | ☑ Existent / ☐ **Jamais appelés (non intégrés)** |
| **memory** | 3 | 3 | memory_remember, memory_recall, memory_context | ☑ Existent / ☑ Appel auto possible |
| **runbook** | 3 | 3 | list_runbooks, get_runbook, search_runbooks | ☑ Existent / ☑ Appel auto possible / ☐ Non bloquants |
| **network** | 1 | 2 | http_request, web_search | ☑ Existent / ☑ Appel auto possible |
| **utility** | 2 | 2 | calculate, get_datetime | ☑ Existent / ☑ Appel auto possible |
| **TOTAL** | **28** | **40** | +12 outils | ⚠️ Divergence docs ↔ code |

**Verdict:** ⚠️ **PARTIELLEMENT CONFORME**
- ✅ Tous les outils promis existent
- ⚠️ 40 outils réels vs 28 annoncés (+12 outils non documentés)
- ❌ Outils QA désactivés (VERIFY_REQUIRED=false)
- ❌ Outils governance non intégrés

---

### 4.6 Erreurs récupérables (cas obligatoire)

**tools.py - Lignes 67-84**

```python
# Erreurs récupérables - le système peut tenter un plan B
RECOVERABLE_ERRORS = {
    "E_FILE_NOT_FOUND",
    "E_DIR_NOT_FOUND",
    "E_PATH_NOT_FOUND",
}

# Erreurs non récupérables - arrêt immédiat
FATAL_ERRORS = {
    "E_PERMISSION",
    "E_CMD_NOT_ALLOWED",
    "E_PATH_FORBIDDEN",
    "E_WRITE_DISABLED",
}

def is_recoverable_error(error_code: str) -> bool:
    return error_code in RECOVERABLE_ERRORS
```

**Cas testé :** Chemin invalide (`E_DIR_NOT_FOUND`)
- Arrêt immédiat : ☐
- Tentative alternative (système) : ☑ **OUI** (tool `search_directory` appelable)
- Suggestion utilisateur : ☑ **OUI** (ToolResult inclut `recoverable: true`)

**Mécanisme:**
- **tools.py:114-125**: `fail()` retourne `error.recoverable = is_recoverable_error(code)`
- **tools.py:965-971**: Tool `search_directory` disponible pour auto-recovery
- Intégration auto-recovery non vérifiée dans workflow (nécessiterait tests E2E)

**Conclusion:**
> ☑ Infrastructure d'erreurs récupérables présente et bien conçue

---

## 5️⃣ Audit FRONTEND — Orchestrator UI

> **NON AUDITÉ** (focus backend/config/sécurité)

**Raison:** Audit backend a révélé écarts critiques (sandbox, verify, governance). Frontend audit serait cosmétique tant que backend n'est pas conforme.

---

## 6️⃣ Tableau de conformité

| Promesse (docs) | Config | Code | Flux réel | Statut |
|-----------------|--------|------|-----------|--------|
| **Sandbox par défaut** | ❌ direct | ✅ Implémenté | ❌ Direct | ❌ NON CONFORME |
| **shell=True absent** | N/A | ✅ Absent | ✅ Absent | ✅ CONFORME |
| **Argv strict (shlex)** | N/A | ✅ Présent | ✅ Utilisé | ✅ CONFORME |
| **Workflow 6 phases obligatoires** | ❌ VERIFY_REQUIRED=false | ⚠️ Conditionnel | ❌ VERIFY skippé | ❌ NON CONFORME |
| **Gouvernance avec veto CRITICAL** | N/A | ✅ Code présent | ❌ Jamais appelé | ❌ NON CONFORME |
| **Runbooks imposés (9)** | N/A | ✅ 9 présents | ❌ Optionnels | ⚠️ PARTIEL |
| **28 outils** | N/A | ⚠️ 40 outils | ✅ Fonctionnels | ⚠️ PARTIEL (+12) |
| **Allowlist/Blocklist** | ✅ Définis | ✅ Implémentés | ✅ Appliqués | ✅ CONFORME |
| **Audit complet** | N/A | ✅ Présent | ✅ Actif | ✅ CONFORME |
| **Rollback actions sensibles** | N/A | ✅ Implémenté | ❌ Jamais appelé | ❌ NON CONFORME |

**Taux de conformité:** 5/10 = **50%**

---

## 7️⃣ Écarts critiques (sans correction)

### Écart 1: Mode d'exécution direct au lieu de sandbox

**Fait:**
- **config.py:83**: `EXECUTE_MODE: str = "sandbox"` (défaut)
- **backend/.env:26**: `EXECUTE_MODE=direct` (override)
- Documentation promet "sandbox by default" (SECURITY.md:206, INDEX.md:24)

**Impact:**
- Exécution DIRECTE sur l'hôte sans isolation Docker
- Pas de limite CPU/RAM (sandbox: 0.5 CPU, 512Mi)
- Pas de réseau désactivé (sandbox: --network=none)
- Risque d'accès non contrôlé aux ressources système

**Gravité:** 🔴 **CRITIQUE**

---

### Écart 2: Vérification QA désactivée par défaut

**Fait:**
- **backend/.env:21**: `VERIFY_REQUIRED=false`
- **workflow_engine.py:185**: Phase VERIFY conditionnelle `if self.verify_required:`
- Phase VERIFY inclut: run_tests, run_lint, run_format, run_typecheck, git_status, git_diff

**Impact:**
- Aucun test automatique exécuté après modifications
- Aucune vérification lint/format/typecheck
- Risque de déploiement de code défectueux
- Workflow promis 6 phases → 4 phases réelles (SPEC, PLAN, EXECUTE, COMPLETE)

**Gravité:** 🔴 **CRITIQUE**

---

### Écart 3: Gouvernance non intégrée

**Fait:**
- Code GovernanceManager présent et fonctionnel (governance.py)
- Aucun appel à `governance_manager.prepare_action()` dans tools.py
- Justifications acceptées en params mais jamais validées
- Exemples: `systemd_restart(justification="...")`, `apt_install(justification="...")`

**Impact:**
- Actions SENSITIVE/CRITICAL exécutées sans vérification
- Pas de veto réel sur actions dangereuses
- Historique governance vide (jamais alimenté)
- Rollback disponible mais jamais enregistré

**Gravité:** 🟠 **ÉLEVÉ**

---

### Écart 4: Runbooks non imposés

**Fait:**
- 9 runbooks enregistrés (runbooks.py:101-443)
- Runbooks disponibles via outils `get_runbook()`, `list_runbooks()`
- Aucune vérification que les procédures sont suivies

**Impact:**
- Procédures optionnelles au lieu d'obligatoires
- Risque de déviations non contrôlées
- Pas de garantie de reproductibilité

**Gravité:** 🟡 **MOYEN**

---

### Écart 5: Secrets par défaut non changés

**Fait:**
- **backend/.env:14**: `JWT_SECRET_KEY=your-secret-key-change-in-production`
- **backend/.env:15**: `ADMIN_PASSWORD=admin123`

**Impact:**
- Tokens JWT prévisibles (clé par défaut)
- Mot de passe admin faible et connu
- Risque d'accès non autorisé

**Gravité:** 🟠 **ÉLEVÉ**

---

## 8️⃣ Verdict final

### Conclusion factuelle

L'AI Orchestrator v7.0 présente une **architecture de sécurité bien conçue** (SecureExecutor, GovernanceManager, Runbooks, Workflow) mais **partiellement implémentée**:

**Points conformes (5/10):**
1. ✅ SecureExecutor élimine shell=True, parsing argv strict
2. ✅ Allowlist/Blocklist de commandes appliqués
3. ✅ Audit trail complet de toutes les exécutions
4. ✅ 40 outils fonctionnels (au-delà des 28 promis)
5. ✅ Infrastructure erreurs récupérables présente

**Points non conformes (5/10):**
1. ❌ Mode d'exécution en "direct" contredit "sandbox by default"
2. ❌ Phase VERIFY désactivée → pas de tests/lint automatiques
3. ❌ GovernanceManager non intégré aux outils → veto absent
4. ❌ Runbooks non imposés → procédures optionnelles
5. ❌ Secrets par défaut non changés (JWT, admin password)

**Posture adoptée:**
Audit **pessimiste** selon consigne. Tout point "probablement OK" mais non prouvé par config + code + flux réel → marqué NON CONFORME.

### Réponse à la question centrale

**"Est-ce que ce système fait réellement ce que la doc v7.0 promet ?"**

> ⚠️ **Partiellement**. Le code implémente toutes les capacités promises (SecureExecutor, Governance, Runbooks, Workflow 6 phases), mais la **configuration runtime** (.env) désactive les protections clés:
> - Sandbox désactivé (mode=direct)
> - Vérification QA désactivée (VERIFY_REQUIRED=false)
> - Gouvernance non intégrée (justifications acceptées mais non validées)
>
> Le système est **techniquement capable** d'être conforme, mais nécessite reconfiguration + intégration governance pour respecter les promesses de la documentation v7.0.

**Classification finale:** **Partiellement conforme** (50%)

---

**Audit réalisé le 2026-01-11 par Claude (MCP) sans modification de code.**
