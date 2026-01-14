# Frontend — v7.1

## Rôle

Le frontend est une **UI d’orchestrator**, pas un simple chat :
- notion de **Run**
- phases visibles
- inspector (events, tools, verification, raw)
- actions (re‑verify / force repair) si supportées côté backend

## État minimal d’un Run

- `run_id` (ou `conversation_id`)
- `status` : RUNNING | COMPLETE | FAILED
- `phases` : pending/running/done/failed (+ durées)
- `events_count`, `tools_count`, `duration`
- `final_response` ou `error`

## Anti-stuck

Le frontend doit :
- afficher les erreurs WS
- clôturer un run si aucun événement n’arrive après un délai raisonnable (watchdog)

## Débogage

- DevTools → Network → WS frames
- Vérifier que `complete` arrive et que le store met à jour le run.
