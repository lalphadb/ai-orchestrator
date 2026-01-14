# Observabilité — v7.1

## Objectifs

- Savoir en 1 minute : version, mode d’exécution, sandbox disponible, verify mode.
- Prouver les invariants sans lire les logs à la main.

## Recommandations

- Étendre `/system/health` pour inclure `execute_mode`, `sandbox_available`, `verify_required`.
- Logs structurés pour WebSocket : connect/recv/send/disconnect/error.
- Audit trail consultable (dernier N événements / actions).

## Artefacts d’audit

- Captures WS (frames)
- Logs systemd filtrés
- Résultats scripts posture (sandbox/verify/secrets)
