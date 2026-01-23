# Corrections Infrastructure Appliquées - 2026-01-20

## ✅ Vérifications Préalables

### 1.1 Router parasite Traefik - **CONFIRMÉ ET CORRIGÉ**
- **Constat**: Router `ai-orchestrator-frontend-unified-stack@docker` existait avec règle `Host('ai-orchestrator-frontend-unified-stack')`
- **Cause**: `traefik.enable=true` dans unified-stack/docker-compose.yml sans règles router spécifiques
- **Correction**: Changé `traefik.enable=false` car routage géré par `configs/traefik/dynamic/ai-orchestrator.yml`
- **Vérification**: `curl -s http://127.0.0.1:8080/api/http/routers | jq -r '.[] | select(.name | contains("ai-orchestrator-frontend")) | .name'` → aucun résultat ✅

### 1.2 Conteneur backend orphelin - **CONFIRMÉ ET CORRIGÉ**
- **Constat**: Conteneur `ai-orchestrator-backend` en état "Created" (jamais démarré)
- **Cause**: Port 8001 déjà utilisé par service systemd `ai-orchestrator.service`
- **Corrections appliquées**:
  1. Supprimé conteneur: `docker rm ai-orchestrator-backend` ✅
  2. Commenté service complet dans docker-compose.yml ✅
  3. Ajouté note explicite: "OBSOLÈTE - Backend géré par systemd"
- **Vérification**: `docker ps -a --filter "status=created"` → aucun résultat ✅

### 2.1 Erreurs CrowdSec - **CONFIRMÉ, NON CORRIGÉ**
- **Constat**: Erreurs 403 récurrentes dans logs Traefik:
  ```
  ERROR: CrowdsecBouncerTraefikPlugin: statusCode:403
  - /v1/decisions/stream
  - /v1/usage-metrics
  ```
- **Impact**: Logs bruités, mais fonctionnalité de blocage OK (pas bloquant)
- **Cause**: Clé bouncer nécessite permissions supplémentaires
- **Action**: Non appliquée (nécessite régénération clé bouncer + mise à jour middlewares.yml)
- **Recommandation**: Correction optionnelle, faible priorité

### 2.2 ChromaDB API v1 vs v2 - **VÉRIFIÉ, NON APPLICABLE**
- **Constat**: ChromaDB n'expose PAS le port 8000 sur l'hôte
- **Vérification**: `docker ps | grep chroma` → `8000/tcp` (pas de publish)
- **Conclusion**: Pas de clients externes → correction inutile
- **Recommandation**: Aucune action requise

### 3.1 Ports inconnus - **IDENTIFIÉS**
Tous les processus identifiés et légitimes:
- Port 5000: `python3 -m http.server 5000` (simple HTTP server, usage local)
- Port 9102: `/home/lalpha/projets/ai-tools/ollama-exporter/ollama_exporter.py` (metrics Ollama)
- Port 9101: `/home/lalpha/projets/ai-tools/self-improvement/metrics_exporter.py` (metrics auto-amélioration)

**Recommandation**: Documenter ces services dans la config principale

---

## 📝 Fichiers Modifiés

### unified-stack/docker-compose.yml
**Backup créé**: `docker-compose.yml.before-corrections-20260120-HHMMSS`

**Modifications**:
1. Ligne 260: `traefik.enable=false` pour `ai-orchestrator-frontend`
   - Commentaire ajouté: "Routage géré par configs/traefik/dynamic/ai-orchestrator.yml"

2. Lignes 201-246: Service `ai-orchestrator-backend` entièrement commenté
   - En-tête ajouté: "OBSOLÈTE - Backend géré par systemd (ai-orchestrator.service sur port 8001)"
   - Instructions de réactivation conservées mais déconseillées

---

## ✅ Validation Post-Corrections

### Conteneurs
```bash
docker ps -a --filter "status=created"
# Résultat: aucun conteneur en état "created" ✅
```

### Routage Traefik
```bash
curl -s http://127.0.0.1:8080/api/http/routers | jq -r '.[] | .name' | grep ai-orchestrator
# Résultat:
# - ai-orchestrator@file ✅
# - ai-orchestrator-api@file ✅
# - ai-orchestrator-ws@file ✅
# PAS de: ai-orchestrator-frontend-unified-stack@docker ✅
```

### Services AI Orchestrator
```bash
# Frontend via Traefik
curl -k -I https://ai.4lb.ca/
# HTTP/2 200 ✅

# API via Traefik
curl -k -I https://ai.4lb.ca/api/v1/system/health
# HTTP/2 200 ✅

# Backend systemd
systemctl is-active ai-orchestrator
# active ✅
```

---

## 📊 Récapitulatif

| Correction | Statut | Impact | Vérification |
|------------|--------|--------|--------------|
| 1.1 Router parasite supprimé | ✅ Appliquée | Nettoyage config Traefik | Aucun router parasite détecté |
| 1.2 Conteneur orphelin supprimé | ✅ Appliquée | Nettoyage Docker | Aucun conteneur "created" |
| 1.2 Service compose commenté | ✅ Appliquée | Évite conflit port 8001 | Compose valide, service commenté |
| 2.1 Erreurs CrowdSec | ⏸️ Reportée | Logs bruités (non bloquant) | Fonctionnalité OK |
| 2.2 ChromaDB v1→v2 | ❌ Non applicable | ChromaDB non exposé | Aucun client externe |
| 3.1 Ports inconnus | ℹ️ Documentés | Identification | Services légitimes |

---

## 🎯 Recommandations Finales

### Architecture Confirmée (2026-01-20)
- **Backend AI Orchestrator**: systemd sur port 8001 (hôte)
- **Frontend AI Orchestrator**: Docker nginx sur unified-net (interne 80, exposé via Traefik)
- **Routage Traefik**: Provider file `configs/traefik/dynamic/ai-orchestrator.yml`
- **DB**: SQLite locale dans backend (pas de service DB externe pour AI Orchestrator)

### Actions Futures (Optionnelles)
1. **CrowdSec**: Régénérer clé bouncer avec permissions `/v1/decisions/stream` et `/v1/usage-metrics`
2. **Documentation**: Ajouter ports 5000, 9101, 9102 dans docs infrastructure
3. **Monitoring**: Créer dashboards Grafana pour ollama-exporter et metrics-exporter

---

## 📅 Prochaines Étapes

- [ ] Tester déploiement unified-stack avec `--profile ai` (devrait ignorer backend commenté)
- [ ] Documenter services metrics (ports 9101, 9102) dans README infrastructure
- [ ] (Optionnel) Corriger CrowdSec si logs verbeux deviennent problématiques
- [ ] Valider que les backups docker-compose sont bien exclus du git

---

**Date**: 2026-01-20  
**Temps total**: ~25 minutes  
**Risque**: Faible (backups créés, validations complètes)  
**Impact**: Positif (nettoyage config, clarification architecture)
