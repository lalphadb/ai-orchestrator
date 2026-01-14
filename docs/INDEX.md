# Documentation — AI Orchestrator v7.1

Dernière mise à jour: 2026-01-13

Cette documentation décrit **le comportement réel attendu** de l’orchestrator (backend + frontend), et fournit les **procédures d’audit** pour vérifier que *doc ↔ config ↔ runtime ↔ UI* sont alignés.

## Démarrage rapide

1. Installation : `INSTALLATION.md`
2. Configuration : `CONFIGURATION.md`
3. Lancer en dev : `DEVELOPMENT.md`
4. Déployer : `DEPLOYMENT.md`
5. Utiliser le workflow : `WORKFLOW.md`
6. Interfaces temps réel : `WEBSOCKET.md` et `FRONTEND.md`
7. Sécurité : `SECURITY.md`
8. Débogage : `TROUBLESHOOTING.md`
9. Auditer : `AUDIT/AUDIT_METHOD.md` + `AUDIT/AUDIT_PLAN_TEMPLATE.md`

## Principes non négociables

- **Présent ≠ fonctionnel** : une promesse n’est “OK” que si elle est prouvée en runtime.
- **Fail‑closed** : si la sandbox est requise mais indisponible, on **échoue fort** (pas de fallback silencieux).
- **Événement terminal obligatoire** : chaque run doit finir par `complete` ou `error` (jamais “RUNNING infini”).
- **Traçabilité** : chaque action outillée doit être auditée (outil, input, output, durée).

## Structure recommandée du dossier docs

- Guides : `ARCHITECTURE.md`, `WORKFLOW.md`, `SECURITY.md`, `API.md`, `WEBSOCKET.md`, `FRONTEND.md`
- Ops : `DEPLOYMENT.md`, `OBSERVABILITY.md`, `TROUBLESHOOTING.md`
- Audit : `AUDIT/` (méthode + templates + checklists)
