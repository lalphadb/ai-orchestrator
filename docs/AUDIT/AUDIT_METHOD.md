# Méthode d’audit — v7.1

## Règle d’or

Un point est **CONFORME** seulement si au moins **2 preuves indépendantes** existent :
1) config runtime (.env / endpoint),
2) logs/audit trail,
3) test E2E (UI → WS → backend → réponse).

Sinon : **NON‑CONFORME** (approche pessimiste).

## Ordre d’audit

1. Docs (promesses)
2. Config (runtime)
3. Backend (preuves)
4. Frontend (preuves)
5. E2E (scénarios)

## Résultat

- tableau promesse → preuves → statut
- liste des écarts classés P0/P1/P2
- plan de correction minimal
