# Déploiement — v7.1

## Pré-requis

- Ubuntu (systemd)
- Docker (obligatoire si `EXECUTE_MODE=sandbox`)
- Node + Python

## Service backend (systemd)

- Vérifier :
  - `systemctl status ai-orchestrator`
  - `journalctl -u ai-orchestrator -n 200 --no-pager`

⚠️ Après mise à jour code backend, **redémarrer** le service :
- `sudo systemctl restart ai-orchestrator`

## Frontend

- Build : `npm run build`
- Déployer le dossier `dist/` via votre méthode (nginx, rsync, etc.)
- Vider cache/CDN si nécessaire (sinon version UI incohérente)

## Post-deploy checks

- `GET /api/v1/system/health`
- Test WS minimal : un run doit finir par `complete` en < 15s sur une requête simple.
