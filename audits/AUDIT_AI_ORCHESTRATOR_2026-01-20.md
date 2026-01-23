# Audit complet – AI Orchestrator (2026-01-20)

## 1) Résumé exécutif
- Backend FastAPI (systemd) actif sur 0.0.0.0:8001, healthy.
- Frontend nginx (Docker) actif sur hôte 0.0.0.0:8002 (service `ai-orchestrator-frontend`).
- Traefik (unified-stack) route `ai.4lb.ca` vers frontend (80) et `/api`/`/ws` vers backend (192.168.200.1:8001) via fichier dynamique.
- Compose local est obsolète (`docker-compose.yml.OBSOLETE`) et non utilisé; l’architecture courante est mixte systemd + conteneur unique.
- Aucune collision de ports constatée, mais risque si on relance l’ancien compose (backend publierait 8002).
- Secrets dans `.env.example` et `.env.baseline` sont des placeholders en clair; à remplacer en prod.

## 2) Périmètre & état runtime
- Backend: systemd `ai-orchestrator` actif (`systemctl is-active ai-orchestrator` → active).
- Frontend: conteneur Docker `ai-orchestrator-frontend` (nginx:alpine) exposé 8002→80 sur réseau `unified-net`.
- Traefik: provider file depuis `infrastructure/unified-stack/configs/traefik/dynamic/ai-orchestrator.yml` (routers `ai-orchestrator`, `ai-orchestrator-api`, `ai-orchestrator-ws`).
- DB: SQLite locale (fichier `ai_orchestrator.db`) stockée dans `backend` (pas de service DB externe).

## 3) Architecture & configs clés
- Backend service: FastAPI/uvicorn, health `/health`, metrics `/metrics` (voir [backend/main.py](../backend/main.py)).
- Settings (env-first): voir [backend/app/core/config.py](../backend/app/core/config.py) – CORS restreint, secret fallback auto-généré si `.env` absent, EXECUTE_MODE=direct par défaut.
- Env exemples:
  - [backend/.env.example](../backend/.env.example) (placeholders, SQLite locale).
  - [audits/changesets/20260111_1051/.env.baseline](changesets/20260111_1051/.env.baseline) (v7.0, direct mode, admin password en clair à changer).
- Frontend build/proxy:
  - Dockerfile: [frontend/Dockerfile](../frontend/Dockerfile) – proxy `/api` et `/ws` vers `backend:8001` dans le même réseau.
  - Nginx conf hors build: [nginx.conf](../nginx.conf) – proxy vers IP 10.10.10.46:8001 (legacy host-mode), health `/health`.
- Compose obsolète: [docker-compose.yml.OBSOLETE](../docker-compose.yml.OBSOLETE) – ne pas lancer tel quel; publierait backend sur 8002.

## 4) Traefik (routes actives)
- Host `ai.4lb.ca` → service `ai-orchestrator` (frontend) port 80.
- Host `ai.4lb.ca` + PathPrefix `/api` → service `ai-orchestrator-backend` port 8001 (gateway 192.168.200.1).
- Host `ai.4lb.ca` + PathPrefix `/ws` → `ai-orchestrator-backend` port 8001.
- Middlewares: `geoblock`, `crowdsec` (selon dynamic file). Certresolver letsencrypt.

## 5) Réseaux & ports
- Hôte: 8001 (backend), 8002 (frontend), 80/443/8080 (Traefik), autres services unified-stack.
- Docker: `ai-orchestrator-frontend` sur `unified-net` (192.168.200.0/24), exposé 8002→80. Backend n’est pas en conteneur.
- Pas de collision observée; garder 8002 réservé au frontend.

## 6) Sécurité / conformité
- Secrets en clair dans fichiers exemple/baseline; exiger override `.env` avec valeurs fortes.
- EXECUTE_MODE=direct (risque d’exécution hôte); commande allowlist/blocklist définie dans [backend/app/core/config.py](../backend/app/core/config.py).
- CORS limité à domaines explicites (OK). JWT expiré à 24h.
- Traefik socket monté en RO dans unified-stack (ok). Dashboard ouvert sur 8080 (via Traefik) – à restreindre si exposé.

## 7) Risques / écarts
1. Relancer l’ancien compose publierait backend sur 8002 et entrerait en conflit avec le frontend existant.
2. Nginx conf legacy pointe vers 10.10.10.46:8001; à aligner avec l’arch actuelle (gateway 192.168.200.1 ou backend:8001 en réseau Docker selon mode).
3. Secrets par défaut dans `.env.example`/`.env.baseline` (JWT/ADMIN) doivent être remplacés en prod.
4. EXECUTE_MODE=direct sur hôte: vérifier que l’usage est volontaire et que l’allowlist couvre les commandes autorisées.

## 8) Actions correctives proposées (ordre)
1) Verrouiller les secrets
- Créer/mettre à jour `backend/.env` avec JWT_SECRET_KEY fort et ADMIN_PASSWORD robuste; supprimer les valeurs par défaut des fichiers partagés si publié.

2) Stabiliser le port mapping
- Ne pas relancer `docker-compose.yml.OBSOLETE`. Si un compose est requis, changer le publish backend à 8003 (ou ne pas publier) et laisser Traefik router via réseau.

3) Aligner la config nginx
- Si le frontend s’appuie sur nginx.conf externe, mettre l’upstream sur 192.168.200.1:8001 (gateway unified-net) ou sur `backend:8001` si vous dockerisez aussi le backend.

4) Documentation / SOP
- Documenter que le backend est systemd (port 8001) et le frontend Docker (port 8002, réseau unified-net) pour éviter tout déploiement compose non désiré.

5) Durcissement optionnel
- Restreindre l’accès Traefik dashboard 8080 (auth ou firewall) si ouvert.
- Si multi-utilisateur, passer EXECUTE_MODE=sandbox et activer le conteneur sandbox avec quotas.

## 9) Commandes de vérification (rapide)
```bash
# Backend status
systemctl is-active ai-orchestrator
curl -sS http://127.0.0.1:8001/health

# Frontend via Traefik
curl -k -I -H "Host: ai.4lb.ca" https://127.0.0.1/

# API via Traefik
curl -k -i -H "Host: ai.4lb.ca" https://127.0.0.1/api/health || true

# Container frontend
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep ai-orchestrator-frontend
```

---
Ce rapport exclut explicitement médias, backups et artefacts statiques (non-services).
