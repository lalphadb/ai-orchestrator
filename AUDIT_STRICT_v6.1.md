# AUDIT STRICT — AI ORCHESTRATOR v6.1

**Méthodologie:** Plan d'audit en 9 phases (post-méta-audit)
**Date:** 2026-01-08
**Auditeur:** Claude Opus 4.5

> **Principe fondamental:**
> Toute capacité doit être validée sur 4 plans simultanément:
> **Documentation → Configuration → Code → Flux réel**
> Si un seul plan n'est pas vérifié, la capacité est **NON CONFORME**.

---

## PHASE 0 — PRÉ-AUDIT (Verrouillage méthodologique)

### Version auditée

| Élément | Valeur |
|---------|--------|
| Commit | `1804469d34cdf9606eb5d152e31bf5d2e550c1d1` |
| Message | "Self-Learning System - Auto-amélioration IA" |
| Fichiers modifiés non commités | 17 |

### Configuration active (.env)

```bash
EXECUTE_MODE=direct          # ⚠️ Mode direct, pas sandbox
VERIFY_REQUIRED=true         # ✅ Vérification obligatoire
MAX_REPAIR_CYCLES=3          # ✅ 3 cycles max
WORKSPACE_DIR=/home/lalpha/orchestrator-workspace
```

### Hypothèses interdites

> *"La documentation n'est PAS une preuve de fonctionnement."*
> *"Présent dans le code" ≠ "utilisé"*
> *"Bouton visible" ≠ "fonctionnel"*

### Zones à haut risque

1. **Sécurité d'exécution** — Mode direct vs sandbox
2. **Boutons de pilotage** — Re-verify / Force Repair
3. **Récupération automatique** — E_DIR_NOT_FOUND

---

## PHASE 1 — AUDIT DOCUMENTAIRE (Promesses)

### Promesses extraites

| ID | Promesse | Source |
|----|----------|--------|
| P01 | Pipeline 6 phases: SPEC→PLAN→EXECUTE→VERIFY→REPAIR→COMPLETE | ARCHITECTURE-v6.1.md:14-16 |
| P02 | EXECUTE_MODE=sandbox par défaut | ARCHITECTURE-v6.1.md:127 |
| P03 | 31 commandes dans allowlist | ARCHITECTURE-v6.1.md:75-79 |
| P04 | 31 commandes dans blocklist | ARCHITECTURE-v6.1.md:82-87 |
| P05 | Récupération automatique sur E_DIR_NOT_FOUND | TOOLS.md:635, WORKFLOW_CONVENTIONS.md:161-162 |
| P06 | Actions frontend: Re-verify, Force Repair | WORKFLOW_CONVENTIONS.md:261-265 |
| P07 | 17 outils intégrés | TOOLS.md:3 |
| P08 | Verifier avec verdict PASS/FAIL | WORKFLOW_CONVENTIONS.md:195-204 |

### Conflit documentaire détecté

| Document | EXECUTE_MODE par défaut |
|----------|------------------------|
| ARCHITECTURE-v6.1.md:127 | `sandbox` |
| WORKFLOW_CONVENTIONS.md:256 | `direct` |
| .env (réel) | `direct` |

➡️ **ARCHITECTURE-v6.1.md est obsolète.**

---

## PHASE 2 — AUDIT CONFIGURATION (Valeurs effectives)

### Tableau comparatif: Doc vs Config

| Paramètre | Documentation | config.py défaut | .env effectif | Conformité |
|-----------|---------------|------------------|---------------|------------|
| EXECUTE_MODE | sandbox | direct | direct | ⚠️ Doc obsolète |
| Allowlist | 31 commandes | 185+ commandes | - | ❌ Doc obsolète |
| Blocklist | 31 commandes | 48 commandes | - | ✅ Plus strict |
| VERIFY_REQUIRED | true | True | true | ✅ Conforme |
| MAX_REPAIR_CYCLES | 3 | 3 | 3 | ✅ Conforme |
| CORS_ORIGINS | domaine unique | ["*"] | - | ⚠️ Wildcard |

### Fausses sécurités documentaires

1. **"Sandbox par défaut"** — Faux, mode `direct` configuré
2. **"31 commandes autorisées"** — Faux, 185+ commandes
3. **"CORS whitelist"** — Faux, wildcard "*" utilisé

---

## PHASE 3 — AUDIT CODE (Existence ET appel réel)

### P01: Pipeline 6 phases

| Phase | Méthode | Appelée dans `run()` | Ligne |
|-------|---------|---------------------|-------|
| SPEC | `_generate_spec()` | ✅ Oui (si !simple) | 162 |
| PLAN | `_generate_plan()` | ✅ Oui (si !simple) | 169 |
| EXECUTE | `_execute()` | ✅ Oui | 181 |
| VERIFY | `_run_verification()` | ✅ Oui (si VERIFY_REQUIRED) | 191 |
| REPAIR | `_repair()` | ✅ Oui (boucle while FAIL) | 214 |
| COMPLETE | `_build_response()` | ✅ Oui | 245 |

**Condition de bypass:** `_is_simple_request()` skip SPEC/PLAN pour messages ≤5 mots ou conversationnels.

➡️ **Statut P01: ✅ CONFORME** (phases existent et sont appelées)

---

### P05: Récupération automatique E_DIR_NOT_FOUND

**Analyse du flux:**

1. `list_directory()` retourne `{"error": {"code": "E_DIR_NOT_FOUND", "recoverable": true}}`
2. `engine.py:217` reçoit le résultat et le renvoie au LLM
3. **Aucune logique conditionnelle** du type:
   ```python
   if error.code == "E_DIR_NOT_FOUND":
       await tools.execute("search_directory", ...)
   ```

**Grep confirmant l'absence:**
```bash
grep -r "if.*E_DIR_NOT_FOUND" backend/  # Aucun résultat
```

**Documentation vs Code:**

| Source | Promesse |
|--------|----------|
| TOOLS.md:635 | "Action automatique: Appel search_directory" |
| WORKFLOW_CONVENTIONS.md:162 | "tente search_directory" |
| engine.py | Aucun code de récupération automatique |

➡️ **Statut P05: ❌ NON CONFORME**
La récupération est **agent-driven** (le LLM doit décider), pas **system-driven** (automatique).

---

### P06: Actions frontend Re-verify / Force Repair

**Traçage E2E:**

| Étape | Fichier | Code | Résultat |
|-------|---------|------|----------|
| 1. Clic bouton | RunInspector.vue:197 | `@click="chat.rerunVerification()"` | ✅ Appel |
| 2. Méthode store | chat.js:430-440 | `wsClient.send({action: 'rerun_verify', ...})` | ✅ Envoi WS |
| 3. Handler backend | chat.py:129-138 | `message = data.get("message")` | ❌ Ignore `action` |
| 4. Condition | chat.py:136 | `if not message: error` | ❌ Retourne erreur |

**Code backend problématique (chat.py:127-138):**
```python
data = await websocket.receive_json()
message = data.get("message", "")  # ⚠️ Pas de check "action"
conversation_id = data.get("conversation_id")

if not message:
    await websocket.send_json({"type": "error", "data": "Message vide"})
    continue
```

**Le backend NE GÈRE PAS le champ `action`.**

➡️ **Statut P06: ❌ NON CONFORME**
Les boutons sont **non fonctionnels** — ils envoient une action que le backend ignore.

---

## PHASE 4 — AUDIT FLUX E2E

### Cas obligatoire: Bouton Re-verify

```
[Utilisateur] Clic "Re-verify"
     ↓
[Frontend] wsClient.send({action: 'rerun_verify', conversation_id: 'xxx'})
     ↓
[Backend] data = receive_json()
     ↓
[Backend] message = data.get("message")  // message = undefined
     ↓
[Backend] if not message: return error("Message vide")
     ↓
[Frontend] Reçoit: {type: "error", data: "Message vide"}
```

**Résultat:** Le bouton déclenche une erreur côté backend.

### Cas obligatoire: Erreur E_DIR_NOT_FOUND

```
[Utilisateur] "Liste le contenu de /nonexistent"
     ↓
[ReAct Engine] Appel list_directory("/nonexistent")
     ↓
[tools.py] return {"success": false, "error": {"code": "E_DIR_NOT_FOUND", "recoverable": true}}
     ↓
[engine.py] tool_result = await tools.execute(...)
     ↓
[engine.py] current_prompt = f"Résultat: {tool_result}"  // Pas de récupération auto
     ↓
[LLM] Doit décider seul d'appeler search_directory (ou pas)
```

**Résultat:** Récupération dépend du LLM, pas du système.

---

## PHASE 5 — AUDIT SÉCURITÉ (Approche pessimiste)

### Mode d'exécution réel

| Aspect | Valeur | Risque |
|--------|--------|--------|
| EXECUTE_MODE | `direct` | 🔴 Élevé — Commandes sur l'hôte |
| Sandbox disponible | Oui (code existe) | Non activé |
| Docker requis | Non (mode direct) | - |

### Allowlist effective (185+ commandes)

**Commandes sensibles dans allowlist:**

| Commande | Risque |
|----------|--------|
| `bash`, `sh`, `zsh` | Shell complet |
| `docker`, `docker-compose` | Accès conteneurs |
| `kill`, `pkill` | Terminer processus |
| `nc`, `netcat` | Connexions réseau |
| `env`, `export` | Variables d'environnement |

### Blocklist (48 commandes)

La blocklist est plus stricte que la documentation (48 > 31). ✅

### CORS

```python
CORS_ORIGINS: List[str] = ["*"]  # ⚠️ Wildcard
```

La documentation SECURITY.md:112-114 dit explicitement:
> "DANGEREUX - N'utilisez jamais en production: allow_origins=["*"]"

➡️ **La configuration viole sa propre documentation de sécurité.**

---

## PHASE 6 — ANALYSE UX vs RÉALITÉ

### Ce que l'UI montre

| Élément | Visible | Fonctionnel |
|---------|---------|-------------|
| Stepper phases | ✅ | ✅ |
| run_id | ✅ (tronqué) | ✅ |
| Verdict PASS/FAIL | ✅ | ✅ |
| Bouton Re-verify | ✅ | ❌ |
| Bouton Force Repair | ✅ | ❌ |
| Onglet QA | ✅ | ✅ |
| Export JSON | ✅ | ✅ |

### Signaux d'alerte

1. **Fausses affordances** — Boutons visibles mais non fonctionnels
2. **Promesse non tenue** — "Action automatique" qui ne l'est pas
3. **Mode direct caché** — L'utilisateur ne sait pas que les commandes s'exécutent sans sandbox

---

## PHASE 7 — CONVERGENCE MULTI-AUDITEURS

### Comparaison: Audit 1 (optimiste) vs Audit 2 (strict)

| Point | Audit 1 | Audit 2 (strict) | Verdict final |
|-------|---------|------------------|---------------|
| Workflow 6 phases | ✅ OK | ✅ OK | ✅ CONFORME |
| Verifier distinct | ✅ OK | ✅ OK | ✅ CONFORME |
| Re-verify bouton | ✅ "Présent" | ❌ "Non fonctionnel" | ❌ NON CONFORME |
| Force Repair bouton | ✅ "Présent" | ❌ "Non fonctionnel" | ❌ NON CONFORME |
| Auto-recovery | ⚠️ "Agentique" | ❌ "Pas automatique" | ⚠️ PARTIEL |
| Sandbox | ✅ "Présent" | ❌ "Non activé" | ⚠️ PARTIEL |

**Règle appliquée:**
> En cas de divergence, le verdict le plus pessimiste prévaut.

---

## PHASE 8 — VERDICT STRUCTURÉ

### Verdict global: ⚠️ PARTIELLEMENT CONFORME

| Catégorie | Conformité | Justification |
|-----------|------------|---------------|
| Architecture workflow | ✅ | 6 phases implémentées et appelées |
| Verifier / Judge | ✅ | Service distinct, verdict structuré |
| Outils QA (7) | ✅ | Tous présents et utilisés |
| Récupération erreurs | ⚠️ | Agent-driven, pas system-driven |
| Boutons pilotage | ❌ | Non fonctionnels (backend ignore action) |
| Sécurité sandbox | ⚠️ | Code existe mais non activé |
| Documentation | ❌ | Conflits et informations obsolètes |

### Écarts critiques (sans correction)

| # | Écart | Impact | Sévérité |
|---|-------|--------|----------|
| 1 | Boutons Re-verify/Force Repair non fonctionnels | Pilotage impossible | 🔴 Critique |
| 2 | EXECUTE_MODE=direct (pas sandbox) | Risque sécurité | 🟠 Élevé |
| 3 | Récupération E_DIR_NOT_FOUND non automatique | Promesse doc non tenue | 🟡 Moyen |
| 4 | CORS wildcard "*" | Vulnérabilité CORS | 🟠 Élevé |
| 5 | Doc ARCHITECTURE-v6.1.md obsolète | Confusion auditeur | 🟡 Moyen |

---

## PHASE 9 — RECOMMANDATIONS MÉTHODOLOGIQUES

### Leçons de cet audit

1. **Un seul audit ne suffit pas** — L'audit optimiste a manqué les boutons non fonctionnels
2. **La config est aussi importante que le code** — EXECUTE_MODE=direct change tout
3. **Les flux bout-en-bout sont non négociables** — Sans tracer le WebSocket, impossible de détecter le problème
4. **Présent ≠ fonctionnel** — Les boutons existent mais ne font rien
5. **Le pessimiste a statistiquement raison** — L'audit strict a trouvé plus de problèmes

### Indicateur de qualité de cet audit

- [x] Trouve au moins un problème critique (boutons non fonctionnels)
- [x] Remet en cause la documentation (ARCHITECTURE obsolète)
- [x] Invalide une "évidence apparente" (boutons visibles = fonctionnels)
- [x] Explicite ce qui n'a pas été audité (tests unitaires, performance)

➡️ **Audit de qualité suffisante.**

---

## CHECKLIST FINALE

- [x] Le système n'est pas un simple chat
- [x] Le workflow est visible côté UI
- [x] Les preuves QA sont accessibles
- [ ] Les erreurs récupérables sont gérées intelligemment — **Agentique, pas système**
- [ ] Un échec est compréhensible sans logs serveur — **Boutons pilotage non fonctionnels**
- [ ] Les actions utilisateur (Re-verify, Repair) fonctionnent — **NON**

---

## RÉPONSE À LA QUESTION FINALE

> **"Est-ce que ce système correspond réellement à ce que sa documentation promet ?"**

**Réponse:** PARTIELLEMENT.

- ✅ Le pipeline workflow fonctionne (SPEC→PLAN→EXECUTE→VERIFY→REPAIR)
- ✅ Le Verifier produit un verdict PASS/FAIL avec preuves
- ❌ Les boutons Re-verify / Force Repair sont non fonctionnels
- ❌ La récupération d'erreurs n'est pas "automatique" mais agent-driven
- ❌ La documentation contient des informations obsolètes (sandbox, allowlist)

---

*Audit réalisé le 2026-01-08 selon méthodologie stricte en 9 phases*
*Aucune correction appliquée — Observation uniquement*
