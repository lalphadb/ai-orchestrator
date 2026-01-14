# Architecture — v7.1

## Vue d’ensemble

AI Orchestrator est un **moteur de workflow agentique** auditable :

`SPEC → PLAN → EXECUTE → VERIFY → (REPAIR) → COMPLETE`

- **Backend** : FastAPI + moteur workflow + outils (filesystem, commandes, QA).
- **Exécution outillée** : via un exécuteur sécurisé (argv strict, allowlist, rôles).
- **Gouvernance** : classification des actions, justification requise, vérification/rollback selon risque.
- **Frontend** : UI “orchestrator” (runs, phases, inspector) plutôt qu’un simple chat.

## Composants principaux

- **Workflow Engine** : orchestre les phases, impose les invariants (verdict, preuves).
- **SecureExecutor** : exécute des commandes de manière sûre (pas de `shell=True`), avec sandbox Docker si activée.
- **Governance Manager** : applique règles de risque (READ/SAFE/MODERATE/SENSITIVE/CRITICAL), bloque si justification manquante.
- **Runbooks** : procédures standardisées (déploiement, diagnostic, recovery, sécurité).
- **WebSocket** : streaming d’événements (phases, outils, tokens, verdict).

## Invariants runtime (à auditer)

- Sandbox : si `EXECUTE_MODE=sandbox` et Docker indisponible → **échec** (pas de direct fallback).
- Un run se termine toujours par `complete` ou `error`.
- Toute action sensible déclenche VERIFY (au minimum progressif).
- Les événements WS incluent un identifiant de corrélation (`run_id` / `conversation_id`) de bout en bout.
