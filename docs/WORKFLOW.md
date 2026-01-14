# Workflow — v7.1

## Phases

1. **SPEC** : reformulation + critères d’acceptation.
2. **PLAN** : plan d’actions outillées et validations attendues.
3. **EXECUTE** : exécution d’outils (filesystem, commandes, QA, etc.).
4. **VERIFY** : preuve (tests/lint/build/health) + verdict.
5. **REPAIR** (optionnel) : corrections limitées et re‑vérification.
6. **COMPLETE** : réponse finale + preuves.

## Règles

- **Simple request fast‑path** : les demandes “système/ops” simples peuvent passer directement en EXECUTE.
  - Exemple : “uptime”, “status service”, “liste des modèles”.
- **VERIFY progressif** : VERIFY peut être conditionnel (obligatoire pour actions sensibles/risquées).
- **Cycles de réparation** : bornés (`MAX_REPAIR_CYCLES`).
- **Timeouts** : outillage et WS ont des timeouts pour éviter les runs infinis.

## Définition de “succès”

- Réponse utile + action effectuée
- Verdict / preuves accessibles dans l’inspector
- Audit trail complet (outils + durée + résultats)
