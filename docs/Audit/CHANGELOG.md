# 🛠️ PLAN DE CORRECTION CONSOLIDÉ — AI ORCHESTRATOR v6.2

**Date:** 2026-01-08  
**Basé sur:** 6 audits indépendants (Claude Opus, Claude Code, Gemini x2, GitHub Copilot)  
**Contexte:** Environnement **AUTOHOME** (orchestrateur autonome sur serveur personnel)

---

## ⚠️ CONTEXTE CRUCIAL : Mode Autohome

> **L'AI Orchestrator est conçu pour gérer ton serveur de manière autonome.**
> 
> Cela signifie que certaines "vulnérabilités" identifiées par les audits sont en fait des **fonctionnalités requises** :
> - Accès à `docker`, `docker-compose` → Gestion de la stack
> - Accès à `bash`, `sh` → Scripts d'automatisation
> - Accès à `kill`, `systemctl` → Gestion des services
> - Mode `direct` → Interaction réelle avec le système

### Distinction Critique

| Aspect | Système Multi-User Public | Système Autohome Personnel |
|--------|---------------------------|---------------------------|
| Sandbox obligatoire | ✅ Oui | ❌ Non (empêcherait l'autogestion) |
| Allowlist restrictive | ✅ Oui | ❌ Non (nécessite accès complet) |
| Isolation workspace | ✅ Oui | ⚠️ Optionnel (besoin d'accès global) |
| Auth externe | ✅ Critique | ⚠️ Réseau local + VPN suffisant |

**Conclusion :** On ne corrige PAS la sécurité comme pour un SaaS public, mais on corrige les **vrais bugs** et on améliore la **documentation honnête**.

---

## 📊 Synthèse des 6 Audits

| Auditeur | Score | Problèmes Critiques Identifiés |
|----------|-------|-------------------------------|
| Claude Opus (détaillé) | 45/100 | 12 écarts, sécurité, boutons |
| Claude Code | 65/100 | 2 écarts, auto-recovery |
| Gemini (optimiste) | 75/100 | 2 écarts, agentique vs système |
| Gemini (strict) | ❌ Non conforme | 4 critiques, sécurité, boutons |
| Claude Opus (strict) | ⚠️ Partiel | Boutons, auto-recovery, doc |
| GitHub Copilot | 35/100 | 4 CVE, config mismatch |

### Consensus des 6 Audits (100% d'accord)

| Problème | Tous d'accord | Type |
|----------|---------------|------|
| Boutons Re-verify/Force Repair non fonctionnels | ✅ 6/6 | 🔴 Bug |
| Auto-recovery E_DIR_NOT_FOUND absente | ✅ 6/6 | 🔴 Bug |
| Documentation obsolète/incohérente | ✅ 6/6 | 🟠 Doc |
| 2 fichiers config.py (confusion) | ✅ 4/6 | 🟠 Maintenance |

### Faux Problèmes (pour contexte autohome)

| "Problème" Identifié | Pourquoi c'est OK en Autohome |
|---------------------|-------------------------------|
| EXECUTE_MODE=direct | Requis pour gérer le serveur |
| Allowlist permissive (185 cmds) | Requis pour automatisation complète |
| docker/bash dans allowlist | Requis pour gestion stack |
| CORS wildcard | Réseau local, pas d'exposition externe |

---

## 🎯 Plan de Correction Priorisé

### 🔴 P0 — BUGS CRITIQUES (Semaine 1)

Ces problèmes cassent des fonctionnalités promises.

---

#### P0.1 — Câbler les Boutons Re-verify / Force Repair

**Problème :** Le frontend envoie `{action: 'rerun_verify'}`, le backend attend `{message: '...'}` et ignore l'action.

**Fichier :** `backend/app/api/v1/chat.py`

**Correction :**

```python
@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # === CORRECTION: Gérer les actions de pilotage ===
            action = data.get("action")
            
            if action == "rerun_verify":
                await handle_rerun_verify(data, websocket, db)
                continue
            elif action == "force_repair":
                await handle_force_repair(data, websocket, db)
                continue
            
            # Flux standard (message chat)
            message = data.get("message", "")
            if not message:
                await websocket.send_json({"type": "error", "data": "Message vide"})
                continue
            
            # ... reste du code existant ...
    except WebSocketDisconnect:
        pass


async def handle_rerun_verify(data: dict, ws: WebSocket, db: Session):
    """Relance uniquement la phase VERIFY sur le dernier run."""
    conversation_id = data.get("conversation_id")
    
    # Récupérer le dernier message assistant
    last_response = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.role == "assistant"
    ).order_by(Message.created_at.desc()).first()
    
    if not last_response:
        await ws.send_json({"type": "error", "data": "Aucun run à re-vérifier"})
        return
    
    await ws.send_json({"type": "phase", "data": {"phase": "verify", "status": "running"}})
    
    # Relancer la vérification
    verification = await workflow_engine._run_verification(
        response=last_response.content,
        tools_used=json.loads(last_response.tools_used or "[]"),
        websocket=ws
    )
    
    # Obtenir nouveau verdict
    verdict = await verifier_service.judge(
        original_request="(re-verification)",
        spec=None,
        execution_result=last_response.content,
        verification=verification
    )
    
    await ws.send_json({
        "type": "verification_complete",
        "data": {
            "verification": verification,
            "verdict": verdict.model_dump(),
            "action": "rerun_verify"
        }
    })


async def handle_force_repair(data: dict, ws: WebSocket, db: Session):
    """Force un cycle de réparation même si PASS."""
    conversation_id = data.get("conversation_id")
    
    await ws.send_json({"type": "phase", "data": {"phase": "repair", "status": "running"}})
    
    # Logique de réparation forcée
    repair_result = await workflow_engine._repair(
        conversation_id=conversation_id,
        force=True,
        websocket=ws
    )
    
    await ws.send_json({
        "type": "repair_complete",
        "data": repair_result
    })
```

**Tests requis :**
- [ ] Clic Re-verify → Phase VERIFY se relance
- [ ] Clic Force Repair → Phase REPAIR se déclenche
- [ ] UI mise à jour en temps réel via WebSocket

**Effort :** 4h

---

#### P0.2 — Implémenter Auto-Recovery Système (E_DIR_NOT_FOUND)

**Problème :** La récupération est "agentique" (le LLM doit décider) au lieu de "systémique" (automatique).

**Fichier :** `backend/app/services/react_engine/engine.py`

**Correction :**

```python
# Dans la boucle ReAct, après exécution de l'outil

async def _execute_tool(self, tool_name: str, tool_params: dict) -> dict:
    """Exécute un outil avec auto-recovery sur erreurs récupérables."""
    
    tool_result = await self.tools.execute(tool_name, **tool_params)
    
    # === AUTO-RECOVERY SYSTÈME ===
    if not tool_result.get("success"):
        error = tool_result.get("error", {})
        error_code = error.get("code")
        
        if error.get("recoverable"):
            recovery_result = await self._attempt_recovery(error_code, error, tool_params)
            if recovery_result:
                # Enrichir le résultat avec la suggestion de recovery
                tool_result["recovery"] = recovery_result
                self._log_thinking(f"🔄 System Recovery: {recovery_result['tool']} triggered")
    
    return tool_result


async def _attempt_recovery(self, error_code: str, error: dict, original_params: dict) -> Optional[dict]:
    """Tente une récupération automatique selon le type d'erreur."""
    
    recovery_strategies = {
        "E_DIR_NOT_FOUND": self._recover_dir_not_found,
        "E_FILE_NOT_FOUND": self._recover_file_not_found,
        "E_PATH_NOT_FOUND": self._recover_path_not_found,
    }
    
    strategy = recovery_strategies.get(error_code)
    if strategy:
        return await strategy(error, original_params)
    return None


async def _recover_dir_not_found(self, error: dict, params: dict) -> Optional[dict]:
    """Récupération automatique pour E_DIR_NOT_FOUND."""
    
    # Extraire le nom du dossier depuis l'erreur ou les params
    dir_name = self._extract_dir_name(error.get("message", ""), params)
    if not dir_name:
        return None
    
    # Appeler search_directory automatiquement
    search_result = await self.tools.execute("search_directory", name=dir_name)
    
    if search_result.get("success") and search_result.get("data", {}).get("matches"):
        suggestion = search_result["data"]["matches"][0]  # Meilleur match
        return {
            "tool": "search_directory",
            "success": True,
            "suggestion": suggestion,
            "message": f"Dossier '{dir_name}' trouvé: {suggestion}"
        }
    
    return {
        "tool": "search_directory",
        "success": False,
        "message": f"Aucun dossier correspondant à '{dir_name}' trouvé"
    }


def _extract_dir_name(self, error_message: str, params: dict) -> Optional[str]:
    """Extrait le nom de dossier depuis le message d'erreur ou les paramètres."""
    import os
    import re
    
    # Essayer depuis les params
    if "path" in params:
        return os.path.basename(params["path"].rstrip("/"))
    
    # Essayer depuis le message d'erreur
    patterns = [
        r"[Rr]épertoire[^:]*:\s*(.+)",
        r"[Dd]irectory[^:]*:\s*(.+)",
        r"'([^']+)'.*not found",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_message)
        if match:
            path = match.group(1).strip()
            return os.path.basename(path.rstrip("/"))
    
    return None
```

**Tests requis :**
- [ ] `list_directory("/nonexistent")` → Auto-appel `search_directory`
- [ ] Suggestion injectée dans le contexte LLM
- [ ] Log "System Recovery" visible dans thinking_log

**Effort :** 4h

---

#### P0.3 — Supprimer le Fichier Config Mort

**Problème :** 2 fichiers `config.py` créent de la confusion. Le fix Pydantic a été appliqué au mauvais fichier.

**Action :**

```bash
# Depuis le dossier ai-orchestrator/backend/
mv config.py config.py.deprecated
# OU
rm config.py
```

**Fichier actif (à garder) :** `backend/app/core/config.py`

**Effort :** 5min

---

### 🟠 P1 — AMÉLIORATIONS IMPORTANTES (Semaine 2)

---

#### P1.1 — Réduire l'Agressivité du Bypass Workflow

**Problème :** `_is_simple_request()` bypasse SPEC/PLAN trop souvent.

**Fichier :** `backend/app/services/react_engine/workflow_engine.py`

**Correction :**

```python
def _is_simple_request(self, message: str) -> bool:
    """Détecte UNIQUEMENT les salutations pures."""
    message_lower = message.lower().strip()
    
    # STRICTEMENT conversationnel (pas d'action implicite)
    PURE_GREETINGS = {
        "bonjour", "salut", "hello", "hi", "hey",
        "merci", "thanks", "ok", "d'accord", "oui", "non",
        "au revoir", "bye", "ciao", "bonne nuit",
    }
    
    # Seulement si le message EST une salutation (pas "contient")
    if message_lower in PURE_GREETINGS:
        return True
    
    # Message très court SANS verbe d'action
    words = message_lower.split()
    action_verbs = {
        "crée", "créer", "fait", "faire", "lance", "lancer",
        "exécute", "exécuter", "modifie", "modifier", "change",
        "ajoute", "ajouter", "supprime", "supprimer", "installe",
        "liste", "lister", "montre", "affiche", "vérifie",
    }
    
    if len(words) <= 2 and not any(verb in message_lower for verb in action_verbs):
        return True
    
    return False
```

**Effort :** 1h

---

#### P1.2 — Gérer le Statut "SKIPPED" pour Phases Optionnelles

**Problème :** Si `VERIFY_REQUIRED=false`, l'UI ne montre pas que VERIFY a été sauté.

**Fichier Backend :** `backend/app/models/workflow.py`

```python
class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # NOUVEAU
```

**Fichier Frontend :** `frontend/src/components/chat/RunInspector.vue`

```vue
<!-- Dans le stepper -->
<div
  v-for="phase in phases"
  :key="phase.id"
  :class="[
    'phase-step',
    phase.status === 'completed' && 'bg-green-500',
    phase.status === 'running' && 'bg-blue-500 animate-pulse',
    phase.status === 'failed' && 'bg-red-500',
    phase.status === 'skipped' && 'bg-gray-500 opacity-50',  // NOUVEAU
  ]"
>
  <span v-if="phase.status === 'skipped'" class="text-xs">⏭️</span>
</div>
```

**Effort :** 2h

---

#### P1.3 — Uniformiser les Versions

**Problème :** v3.0.0 dans un fichier, v6.1.0 dans l'autre.

**Fichier :** `backend/app/core/config.py`

```python
APP_VERSION: str = "6.2.0"  # Après corrections
```

**Effort :** 5min

---

### 🟡 P2 — AMÉLIORATIONS UX (Semaine 3)

---

#### P2.1 — Workflow Stepper Visible dans le Header

**Fichier :** `frontend/src/views/ChatView.vue`

```vue
<template>
  <div class="h-screen flex flex-col">
    <!-- NOUVEAU: Header avec workflow stepper toujours visible -->
    <header v-if="chat.currentRun" class="border-b border-gray-700 p-3 bg-gray-900">
      <div class="flex items-center justify-between">
        <WorkflowStepper
          :phases="WORKFLOW_PHASES"
          :current="chat.currentRun.workflowPhase"
          :statuses="chat.currentRun.phaseStatuses"
        />
        <RunBadge :run="chat.currentRun" />
      </div>
    </header>
    
    <!-- Reste du layout -->
    <div class="flex-1 flex overflow-hidden">
      <!-- ... -->
    </div>
  </div>
</template>
```

**Effort :** 4h

---

#### P2.2 — run_id Complet et Copiable

**Fichier :** `frontend/src/components/chat/RunInspector.vue`

```vue
<button
  v-if="run?.id"
  @click="copyRunId"
  class="text-xs text-gray-400 font-mono hover:text-white flex items-center gap-1 transition-colors"
  :title="'Cliquer pour copier: ' + run.id"
>
  <span>Run #{{ run.id }}</span>
  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
  </svg>
  <span v-if="copied" class="text-green-400">✓</span>
</button>

<script setup>
import { ref } from 'vue'

const copied = ref(false)

function copyRunId() {
  navigator.clipboard.writeText(props.run.id)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}
</script>
```

**Effort :** 30min

---

#### P2.3 — Exemples de Démarrage Orientés Workflow

**Fichier :** `frontend/src/components/chat/MessageList.vue`

```javascript
const examples = [
  // AVANT (conversationnel)
  // "Quel est le status du serveur ?",
  
  // APRÈS (workflow complet)
  "Crée un script Python qui monitore l'utilisation CPU et envoie une alerte si > 80%",
  "Analyse les logs Docker des dernières 24h et génère un rapport des erreurs",
  "Refactore le fichier config.py pour utiliser des dataclasses avec validation",
  "Exécute les tests du projet ai-orchestrator et corrige les erreurs trouvées",
]
```

**Effort :** 15min

---

### 🟢 P3 — DOCUMENTATION HONNÊTE (Semaine 4)

---

#### P3.1 — Mettre à Jour SECURITY.md

**Problème :** La doc promet "sandbox par défaut" alors que c'est "direct".

**Correction :**

```markdown
# SECURITY.md

## Mode d'Exécution

### Configuration Autohome (défaut)

L'AI Orchestrator est conçu pour un usage **personnel/autohome** avec accès complet au système :

```env
EXECUTE_MODE=direct  # Exécution directe sur l'hôte
```

**Pourquoi ?** L'orchestrateur doit pouvoir :
- Gérer les conteneurs Docker
- Exécuter des scripts système
- Contrôler les services (systemctl)
- Accéder aux fichiers de configuration

### Mode Sandbox (optionnel)

Pour un environnement multi-utilisateur ou exposé publiquement :

```env
EXECUTE_MODE=sandbox
```

Les commandes s'exécutent dans un conteneur Docker isolé avec :
- `--network=none` (pas de réseau)
- `--read-only` (système de fichiers en lecture seule)
- Mémoire limitée à 512MB

## Allowlist Commandes

L'allowlist contient **130+ commandes** nécessaires à l'autogestion :

### Catégories
- **Développement** : python, pip, npm, node, git
- **Docker** : docker, docker-compose
- **Système** : systemctl, journalctl, df, free
- **Fichiers** : ls, cat, find, grep, sed, awk
- **Réseau** : ping, curl (via docker si besoin)

### Commandes Bloquées (60)
- Commandes destructives : `rm -rf /`, `mkfs`, `dd`
- Accès réseau direct : `wget`, `nc` (utilisez docker si besoin)
- Modification système : `passwd`, `useradd`, `visudo`
```

**Effort :** 2h

---

#### P3.2 — Créer AUTOHOME.md

Nouveau fichier documentant le mode autohome :

```markdown
# MODE AUTOHOME — AI Orchestrator

## Concept

L'AI Orchestrator en mode **autohome** est un assistant IA autonome capable de :
- Gérer l'infrastructure Docker
- Monitorer le système
- Exécuter des scripts de maintenance
- Auto-corriger les problèmes détectés

## Prérequis Sécurité

1. **Réseau isolé** : L'orchestrateur ne doit pas être exposé sur Internet
2. **VPN/Firewall** : Accès uniquement via VPN (WireGuard) ou réseau local
3. **Utilisateur dédié** : Exécution sous l'utilisateur `lalpha`, pas root
4. **Audit logs** : Toutes les commandes sont loguées

## Permissions Requises

| Permission | Raison |
|------------|--------|
| Docker socket | Gestion conteneurs |
| Lecture /var/log | Analyse logs système |
| Écriture workspace | Création fichiers/scripts |
| systemctl | Gestion services |

## Ce que l'Orchestrateur PEUT faire

- ✅ Redémarrer un conteneur Docker
- ✅ Analyser les logs système
- ✅ Créer/modifier des fichiers de config
- ✅ Exécuter des tests
- ✅ Installer des packages npm/pip

## Ce que l'Orchestrateur NE PEUT PAS faire

- ❌ Modifier les mots de passe système
- ❌ Accéder aux fichiers hors workspace (sauf lecture)
- ❌ Supprimer des partitions
- ❌ Modifier le bootloader
```

**Effort :** 1h

---

## 📅 Planning de Déploiement

```
SEMAINE 1 — P0 (Bugs Critiques)
├── Jour 1-2 : P0.1 — Câbler boutons Re-verify/Force Repair
├── Jour 3-4 : P0.2 — Auto-recovery système
└── Jour 5 : P0.3 — Supprimer config.py mort + Tests

SEMAINE 2 — P1 (Améliorations)
├── Jour 1 : P1.1 — Bypass moins agressif
├── Jour 2 : P1.2 — Statut SKIPPED
└── Jour 3 : P1.3 — Uniformiser versions

SEMAINE 3 — P2 (UX)
├── Jour 1-2 : P2.1 — Stepper dans header
├── Jour 3 : P2.2 — run_id copiable
└── Jour 4 : P2.3 — Exemples workflow

SEMAINE 4 — P3 (Documentation)
├── Jour 1-2 : P3.1 — SECURITY.md honnête
└── Jour 3 : P3.2 — AUTOHOME.md
```

---

## ✅ Métriques de Succès

| Métrique | Avant | Après |
|----------|-------|-------|
| Boutons Re-verify/Repair | ❌ Non fonctionnels | ✅ Fonctionnels |
| Auto-recovery E_DIR_NOT_FOUND | ❌ Agentique | ✅ Systémique |
| Fichiers config | 2 (confusion) | 1 (clair) |
| Bypass workflow | Trop agressif | Salutations seulement |
| Documentation sécurité | Mensongère | Honnête (autohome) |
| Workflow visible | Panneau latéral | Header + panneau |
| Checklist audit | 2-3/5 | 5/5 |

---

## 🎯 Résumé Exécutif

### Ce qu'on corrige (vrais bugs)

1. **Boutons Re-verify/Force Repair** — Backend doit gérer l'action WebSocket
2. **Auto-recovery** — Passer de agentique à systémique
3. **Config morte** — Supprimer le fichier qui crée la confusion
4. **Bypass** — Moins agressif pour montrer le workflow
5. **UX** — Stepper visible, run_id copiable

### Ce qu'on NE corrige PAS (fonctionnalités autohome)

1. **EXECUTE_MODE=direct** — Requis pour autogestion
2. **Allowlist permissive** — Requis pour accès complet
3. **CORS wildcard** — Réseau local uniquement
4. **Commandes docker/bash** — Requis pour gestion stack

### Ce qu'on documente honnêtement

1. **SECURITY.md** — Mode autohome clairement expliqué
2. **AUTOHOME.md** — Nouveau fichier dédié
3. **Versions** — Uniformisées à v6.2.0

---

*Plan de correction généré le 2026-01-08*  
*Basé sur 6 audits indépendants, adapté au contexte autohome*
