# AUDIT DE CONFORMITÉ — AI ORCHESTRATOR v6.1

> **ℹ️ PRINCIPE FONDAMENTAL D'AUDIT**
> Ce rapport applique le protocole strict : **Doc → Config → Code → Flux réel**.
> Toute capacité non vérifiée sur ces 4 plans est déclarée **NON CONFORME**.
> L'audit adopte une posture **pessimiste par défaut** (sécurité sous-évaluée, fonctions présumées cassées).

---

## 0️⃣ Pré-audit & Méthodologie

* **Version auditée** : v6.1 (Commit/Tag implicite via documentation)
* **Périmètre** : Backend (FastAPI/Python), Frontend (Vue.js), Documentation.
* **Fichiers critiques analysés** :
    * `backend/app/core/config.py` (Vérité Configuration)
    * `backend/app/api/v1/chat.py` (Vérité Flux)
    * `backend/app/services/react_engine/tools.py` (Vérité Outils)

---

## 1️⃣ Audit Documentaire (Les Promesses)

Selon `docs/`, le système promet :
1.  **Sécurité par défaut** : Exécution en Sandbox Docker (`SECURITY.md`).
2.  **Workflow Complet** : Pipeline Spec → Plan → Execute → Verify → Repair.
3.  **Pilotage Utilisateur** : Possibilité de relancer une vérification ("Re-verify") ou de forcer une réparation ("Force Repair").
4.  **Robustesse** : Récupération "automatique" (Plan B) sur erreurs fichiers (`TOOLS.md`).

---

## 2️⃣ Audit de Configuration (La Réalité par défaut)

Analyse de `backend/app/core/config.py` :

| Variable | Valeur par défaut | Verdict | Impact |
| :--- | :--- | :---: | :--- |
| `EXECUTE_MODE` | **`"direct"`** | ❌ **FAIL** | **Danger Critique**. Le système s'exécute sur le **HOST** par défaut, contredisant la promesse de Sandbox. |
| `COMMAND_ALLOWLIST` | Contient `bash`, `python`, `sh` | ⚠️ **RISK** | En mode `direct`, autoriser `bash` = accès total au système utilisateur. |
| `VERIFY_REQUIRED` | `True` | ✅ OK | Conforme à la promesse de qualité. |

> **Conclusion Phase 2** : La configuration par défaut est **insécurisée**. La documentation ment sur l'état "sécurisé par défaut".

---

## 3️⃣ Audit du Code & Flux (Existence vs Usage)

### 3.1 Les Boutons "Fantômes" (Pilotage)
* **Promesse** : Boutons "Re-verify" et "Repair" dans l'UI.
* **Frontend** : `stores/chat.js` envoie `{ action: 'rerun_verify' }` via WebSocket.
* **Backend** : `api/v1/chat.py` (handler `websocket_chat`) attend `{ message: "..." }`.
* **Analyse** : Le backend **ne vérifie jamais** le champ `action`. Si `message` est vide (cas d'une action bouton), il renvoie `{"type": "error", "data": "Message vide"}`.
* **Verdict** : ❌ **NON FONCTIONNEL**. Les boutons de pilotage sont des **placebos UX**.

### 3.2 La Récupération "Automatique" (Robustesse)
* **Promesse** : Plan B automatique sur `E_DIR_NOT_FOUND`.
* **Code** : `search_directory` existe dans `tools.py`.
* **Flux** : Aucune interception dans `engine.py` pour appeler cet outil *systématiquement* en cas d'erreur. L'erreur est renvoyée au LLM qui *peut* décider de l'utiliser.
* **Verdict** : ⚠️ **PARTIEL**. C'est une récupération "Agentique" (incertaine, coûteuse), pas "Automatique/Système".

### 3.3 Le Bypass de Workflow (Workflow)
* **Code** : `_is_simple_request` dans `workflow_engine.py` contourne SPEC et PLAN pour les messages courts.
* **Observation** : C'est une optimisation non documentée explicitement comme un "bypass" dans l'architecture principale, mais acceptable fonctionnellement.

---

## 4️⃣ Audit Sécurité (Pessimiste)

### 4.1 Mode d'exécution
Le système tournant par défaut en `EXECUTE_MODE="direct"`, toute la sécurité repose sur l'`allowlist`.

### 4.2 Allowlist vs Réalité
L'`allowlist` contient :
* `python`, `python3`
* `bash`, `sh`
* `node`

**Scénario d'attaque trivial** :
L'utilisateur demande : *"Exécute ce script python"*.
Le système génère un fichier `.py` et lance `python script.py`.
En mode `direct`, ce script a **tous les droits de l'utilisateur système** (lecture clés SSH, accès réseau local, variables d'env).

> **Verdict Sécurité** : ❌ **CRITIQUE**. L'`allowlist` est inefficace sans Sandbox obligatoire.

---

## 5️⃣ UX vs Réalité

* **L'Inspecteur de Run** : Affiche des statuts QA réels (✅).
* **Les Actions de Correction** : Sont affichées mais ne font rien (❌).
* **La Console** : Donne l'illusion d'un système robuste, alors que le backend rejette les commandes de pilotage avancées.

---

## 6️⃣ VERDICT FINAL

**Statut : ❌ NON CONFORME**

### Justification
1.  **Sécurité Trompeuse** : La documentation vend une "Sandbox", la config livre un "Accès Host Direct".
2.  **Fonctionnalités Cassées** : Les boutons de pilotage (Verify/Repair) ne sont pas câblés au backend.
3.  **Sur-promesse Robustesse** : La récupération d'erreur n'est pas automatisée au niveau système.

### Synthèse des Écarts

| Domaine | Promesse | Réalité | Gravité |
| :--- | :--- | :--- | :---: |
| **Sécurité** | Sandbox Docker par défaut | Mode Direct (Host) | 🔴 **CRITIQUE** |
| **Pilotage** | Boutons Re-verify/Repair | Backend ignore l'action | 🔴 **CRITIQUE** |
| **Robustesse** | Récupération Auto (Plan B) | Récupération Agentique (LLM) | 🟠 **MOYEN** |
| **Config** | Secure by default | Insecure by default | 🔴 **CRITIQUE** |

---

*Audit réalisé par Gemini (Senior Dev) - le 08 Janvier 2026*
