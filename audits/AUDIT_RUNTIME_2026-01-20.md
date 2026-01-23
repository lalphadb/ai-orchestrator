# Audit Runtime Infrastructure – 2026-01-20

## 1. Résumé exécutif
- L’infrastructure active est cohérente et fonctionnelle autour de Traefik (ports 80/443/8080) sur le réseau `unified-net` (192.168.200.0/24).
- Les services clés actifs: Traefik, CrowdSec, Grafana, Prometheus, Redis, Postgres, ChromaDB, Multimedia (frontend + API), AI Orchestrator (frontend Docker + backend systemd).
- Aucune collision critique de ports détectée sur l’hôte; une alerte notable: conteneur `jsr-dev` non raccordé à `unified-net` (Traefik bascule sur `traefik-net`).
- ACME Traefik opérationnel; stockage `/certs/acme.json` présent avec permissions 600; pas d’erreurs ACME significatives.
- Points d’attention: cohérence des réseaux (attacher tous les services reverse-proxy au réseau Traefik cible), éviter l’usage de `container_name` génériques réutilisables (ex: `postgres`) dans plusieurs stacks.

## 2. Liste Actif / Passif (périmètre demandé)

### Actif
- infrastructure/unified-stack (stack docker)
  - Services: Traefik, CrowdSec, Grafana, Prometheus, Redis, Postgres, ChromaDB, code-server, node-exporter, cadvisor, nvidia-gpu-exporter
  - Réseaux: `unified-net`, `traefik-net`
  - Entrypoints: `web` (80), `websecure` (443), `:8080`
- multimedia/backend (app API) + multimedia/frontend (frontend)
  - Intégrés via `unified-net` et Traefik (labels)
- ai-tools/ai-orchestrator
  - Frontend actif: conteneur `ai-orchestrator-frontend` (port hôte 8002→80)
  - Backend actif: service système (host) 0.0.0.0:8001 (gateway 192.168.200.1 pour Traefik)
- clients/jsr/JSR-solutions (web app)
  - Conteneurs: `jsr-dev`, `jsr-solutions` (ports internes 80)
  - Traefik routage `jsr.4lb.ca` actif (voir remarques réseau)
- ai-tools/agent-zero
  - Conteneur `agent-zero` (ports: 8888→80, 2222→22)

### Passif (exclus explicitement, mais mentionnés)
- Robin_IA (Docker/Streamlit): présent (Dockerfile/.env) mais aucun conteneur en cours d’exécution
- web-apps/4lb-welcome: compose présent, pas de conteneur en cours d’exécution
- Dossiers médias: multimedia/videos, thumbnails, output (montés en read-only côté frontend/API)
- Backups/dumps/assets statiques: divers chemins sous `/home/lalpha/projets` (non-services)

## 3. Tableau des ports (hôte)
- 80: Traefik (reverse-proxy)
- 443: Traefik (TLS)
- 8080: Traefik (API/metrics)
- 8002: `ai-orchestrator-frontend` (Nginx)
- 8001: Backend AI Orchestrator (service système Python)
- 8000: ChromaDB (exposé), Multimedia API interne (vers Traefik, non exposé hôte)
- 9835: nvidia-gpu-exporter
- 2222: agent-zero SSH
- 8888: agent-zero web
- 3000: Grafana (interne au conteneur, non exposé hôte)
- 9090: Prometheus (interne au conteneur, non exposé hôte)
- 5432: Postgres (non exposé hôte)
- 6379: Redis (non exposé hôte)

Collisions réelles/potentielles:
- Aucune collision hôte observée.
- Attention: le compose `ai-orchestrator` (legacy) publie `backend` sur 8002 → conflit potentiel avec `ai-orchestrator-frontend` actuel; garder 8002 pour le frontend, ou harmoniser les ports (voir correctifs).

## 4. Tableau Traefik Domaine → Route → Service → Port
- traefik.4lb.ca → `/` → `api@internal` → 8080 (entrypoint websecure, TLS letsencrypt)
- files.4lb.ca → `/` → `multimedia-frontend` → 80 (middlewares: crowdsec, geoblock, security-headers)
- files.4lb.ca → `/api` → `media-api` → 8000
- ai.4lb.ca → `/` → `ai-orchestrator-frontend` → 80 (middlewares: crowdsec, geoblock, security-headers, rate-limit)
- ai.4lb.ca → `/api` → backend host → 8001 (via 192.168.200.1)
- ai.4lb.ca → `/ws` → backend host → 8001
- jsr.4lb.ca → `/` → `jsr-dev` → 80 (warning: pas sur `unified-net`, Traefik bascule sur `traefik-net`)

ACME
- Stockage: `/certs/acme.json` (permissions `-rw-------`, propriétaire root)
- Logs: pas d’erreurs critiques; messages de renouvellement OK; mise à jour Traefik disponible (3.6.7)

## 5. État DB
- Postgres (postgres:16-alpine)
  - Port: 5432 (non exposé hôte)
  - Volume: `unified-stack_postgres_data`
  - Utilisateur/DB: `lalpha` / `main`
  - Healthcheck: `pg_isready -U lalpha -d main`
  - Commandes de test:
    - `docker exec -it postgres psql -U lalpha -d main -c "\l"`
    - `docker exec -it postgres psql -U lalpha -d main -c "SELECT now();"`
- Redis (redis:7-alpine)
  - Port: 6379 (non exposé hôte)
  - Volume: `unified-stack_redis_data`
  - Commandes de test:
    - `docker exec -it redis redis-cli PING`
- ChromaDB (chromadb/chroma)
  - Port: 8000 (exposé hôte)
  - Volume: `unified-stack_chromadb_data`
  - Commandes de test:
    - `curl -sS http://127.0.0.1:8000/api/v1/heartbeat`
- MySQL (host)
  - 127.0.0.1:3306 actif (hors Docker), usage non critique pour stacks auditées

## 6. Problèmes bloquants + correctifs précis
- Traefik provider réseau: `providers.docker.network=unified-net`
  - Problème: conteneur `jsr-dev` non attaché à `unified-net` → logs warning et fallback `traefik-net`.
  - Correctif: attacher les services routés par Traefik au réseau `unified-net` (ou retirer l’option provider si multi-réseaux voulu).
    - Exemple compose: `networks: { unified-net: { external: true } }` et `networks: [unified-net]` pour le service.
- AI Orchestrator ports
  - Problème: compose legacy publie `backend` sur 8002, conflit potentiel avec frontend actuel sur 8002.
  - Correctif: fixer `backend` à un autre port hôte (ex: 8003) si le backend Docker est réutilisé, ou ne pas publier si backend host reste en usage.
- Container names génériques
  - Problème: `container_name: postgres`, `redis` peuvent créer des collisions en multi-stacks.
  - Correctif: préfixer par projet (ex: `unified-postgres`) ou laisser Compose générer les noms de projet.

## 7. Recommandations d’architecture
- Réseaux
  - Standardiser: Tous les services exposés via Traefik doivent partager `unified-net`.
  - Option: retirer `providers.docker.network` si vous souhaitez laisser Traefik choisir automatiquement le 1er réseau partagé avec le conteneur.
- Routage
  - Centraliser les règles Traefik par labels Docker pour les apps simples (réduire la duplication avec le provider file quand non nécessaire).
  - Conserver provider file pour les cas spécifiques (backend host via gateway, middlewares partagés).
- Sécurité
  - Middlewares actifs OK (crowdsec, geoblock, security-headers, rate-limit).
  - Garder `/var/run/docker.sock` en `read_only` (déjà fait) et limiter dashboards (8080) si exposés.
- Observabilité
  - Prometheus/Grafana OK; ajouter health endpoints homogènes (`/health`) pour frontend si utile.

## 8. Procédure “check global” réexécutable

Commande unique de vérification (à lancer sur l’hôte):

```bash
# État des conteneurs + health
docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}'

# Réseaux Docker
docker network ls
docker network inspect unified-net | head -n 80

docker network inspect traefik-net | head -n 80

# Traefik: logs et ACME
docker exec traefik ls -l /certs/acme.json

docker exec traefik sh -lc "tail -n 100 /var/log/traefik/traefik.log"

# Scan ports hôte
ss -tulpn | sed -n '1,200p'

# Tests HTTP (proxy local)
curl -k -I -H "Host: ai.4lb.ca" https://127.0.0.1/

curl -k -I -H "Host: files.4lb.ca" https://127.0.0.1/

# DB checks
docker exec -it postgres psql -U lalpha -d main -c "SELECT now();"

docker exec -it redis redis-cli PING

curl -sS http://127.0.0.1:8000/api/v1/heartbeat
```

## 9. Plan de corrections – étapes par étapes
1. Attacher toutes les apps web routées par Traefik au réseau `unified-net`.
   - Modifier les `docker-compose.yml` (ex: `jsr-dev`) pour ajouter `networks: [unified-net]` et déclarer le réseau `external: true`.
   - Redéployer: `docker compose up -d` dans les dossiers concernés.
2. Harmoniser AI Orchestrator
   - Conserver `ai-orchestrator-frontend` sur 8002 (hôte) pour compatibilité actuelle.
   - Si backend Docker est requis, publier sur 8003 (hôte) ou ne pas publier et laisser Traefik accéder via réseau.
   - Valider les routes: `/` (frontend), `/api` et `/ws` (backend 8001 via gateway).
3. Noms de conteneurs
   - Retirer `container_name` génériques ou préfixer par projet pour éviter collisions à l’avenir.
4. Traefik
   - Optionnel: mettre à jour Traefik vers 3.6.7.
   - Vérifier et consolider les règles (labels vs provider file) pour éviter redondances.
5. Documentation & Procédure
   - Ajouter ce rapport à la documentation opératoire.
   - Script de vérification à exécuter avant chaque déploiement.

---

Notes d’exclusion (runtime):
- Médias (*.mp4, *.jpg), backups (*.backup*, *.bak), dumps et assets statiques ne sont pas audités comme services.
- Dossiers historiques/conceptuels sans service réseau exclus.
