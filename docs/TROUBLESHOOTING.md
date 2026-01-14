# Troubleshooting — v7.1

## Run bloqué “RUNNING” dans l’UI

1. Vérifier WS frames (DevTools → Network → WS)
2. Vérifier logs backend (`journalctl`)
3. Vérifier que le backend a été redémarré après update
4. Vérifier mismatch versions (UI affiche ancienne version)

## Sandbox non utilisée

- Vérifier `.env` : `EXECUTE_MODE=sandbox`
- Vérifier Docker OK : `docker info`
- Vérifier qu’un log/audit indique `sandbox_used=true` (si instrumenté)
