# Installation — v7.1

## Dépendances

- Python 3.11+ (selon projet)
- Node 18+ (selon projet)
- Docker (si sandbox)

## Installation (exemple)

1. Cloner le dépôt
2. Backend :
   - créer venv, installer requirements
   - configurer `backend/.env`
3. Frontend :
   - `npm ci`
   - `npm run dev` (dev) ou `npm run build` (prod)

## Vérification

- Health endpoint retourne `healthy`
- WebSocket répond et envoie `complete` sur une requête simple
