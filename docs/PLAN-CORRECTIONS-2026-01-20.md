# 🔧 Plan de Corrections Infrastructure - 20 Janvier 2026

> **Basé sur**: Audit factuel comparé à l'analyse Codex
> **Serveur**: lalpha-server-1 (Ubuntu 25.10)
> **Criticité globale**: Moyenne - Infrastructure fonctionnelle avec anomalies à corriger

---

## 📋 Résumé Exécutif

| Catégorie | Problèmes | Criticité |
|-----------|-----------|-----------|
| Configuration Traefik | 2 | 🟡 Moyenne |
| Conteneurs Docker | 1 | 🟢 Faible |
| CrowdSec | 1 | 🟢 Faible |
| ChromaDB | 1 | 🟡 Moyenne |
| Nettoyage | 2 | 🟢 Faible |

**Temps estimé total**: 30-45 minutes

---

## 🔴 Priorité 1 - Corrections Immédiates

### 1.1 Supprimer le router parasite Traefik

**Problème**: Le conteneur `ai-orchestrator-frontend` a `traefik.enable=true` sans règles de routage, créant un router parasite `ai-orchestrator-frontend-unified-stack@docker` avec la règle `Host('ai-orchestrator-frontend-unified-stack')`.

**Impact**: Pollution de la configuration Traefik, confusion potentielle.

**Solution**:

```bash
# Depuis unified-stack
cd /home/lalpha/projets/infrastructure/unified-stack/

# Backup
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)

# Éditer docker-compose.yml
# Chercher le service ai-orchestrator-frontend et modifier les labels
```

**Modification dans `docker-compose.yml`**:

```yaml
  ai-orchestrator-frontend:
    image: nginx:alpine
    container_name: ai-orchestrator-frontend
    labels:
      - "traefik.enable=false"  # Changé de true à false
    # ... reste de la config
```

**Justification**: Le routage vers le frontend est géré par le fichier `configs/traefik/dynamic/ai-orchestrator.yml`, pas par les labels Docker. Le label `traefik.enable=true` est donc inutile et crée un router par défaut non désiré.

**Vérification**:
```bash
# Après redémarrage
curl -s http://127.0.0.1:8080/api/http/routers | grep -c "ai-orchestrator-frontend-unified-stack"
# Doit retourner 0
```

---

### 1.2 Nettoyer le conteneur ai-orchestrator-backend orphelin

**Problème**: Le conteneur `ai-orchestrator-backend` est en état "created" (jamais démarré) car le port 8001 est utilisé par le service systemd `ai-orchestrator.service`.

**Impact**: Conteneur zombie, confusion sur l'architecture.

**Contexte**: L'architecture actuelle utilise un **backend systemd natif** (pas Docker) qui fonctionne correctement. Le conteneur Docker est redondant.

**Solution A - Recommandée** (supprimer le conteneur Docker):

```bash
# 1. Supprimer le conteneur orphelin
docker rm ai-orchestrator-backend

# 2. Commenter ou supprimer le service dans docker-compose.yml
cd /home/lalpha/projets/infrastructure/unified-stack/
```

**Modification dans `docker-compose.yml`**:

```yaml
  # COMMENTÉ - Backend géré par systemd (ai-orchestrator.service)
  # ai-orchestrator-backend:
  #   build:
  #     context: ../../ai-tools/ai-orchestrator/backend
  #   container_name: ai-orchestrator-backend
  #   ... etc
```

**Solution B - Alternative** (migrer vers Docker complet):

```bash
# 1. Arrêter le service systemd
sudo systemctl stop ai-orchestrator
sudo systemctl disable ai-orchestrator

# 2. Retirer le port mapping du conteneur (Traefik route via réseau interne)
# Éditer docker-compose.yml: retirer "ports: - 8001:8001"

# 3. Redémarrer la stack
./stack.sh restart ai-orchestrator-backend
```

**Recommandation**: Solution A - garder l'architecture systemd actuelle qui fonctionne bien.

---

## 🟡 Priorité 2 - Améliorations

### 2.1 Corriger les erreurs CrowdSec dans les logs

**Problème**: Erreurs récurrentes dans les logs Traefik:
```
ERROR: CrowdsecBouncerTraefikPlugin: statusCode:403 (expected: 2xx)
- /v1/decisions/stream
- /v1/usage-metrics
```

**Impact**: Bruit dans les logs, pas d'impact fonctionnel (les décisions de blocage fonctionnent).

**Cause**: Le bouncer Traefik tente d'accéder à des endpoints qui nécessitent des permissions supplémentaires.

**Solution**:

```bash
# Vérifier la config du bouncer
docker exec crowdsec cscli bouncers list

# Regénérer la clé API avec les bonnes permissions
docker exec crowdsec cscli bouncers delete traefik-bouncer
docker exec crowdsec cscli bouncers add traefik-bouncer --key "$(openssl rand -base64 32)"
```

**Puis mettre à jour** `configs/traefik/dynamic/middlewares.yml`:

```yaml
    crowdsec:
      plugin:
        crowdsec:
          crowdsecLapiHost: "crowdsec:8080"
          crowdsecLapiKey: "NOUVELLE_CLE_ICI"
          # Désactiver les metrics si non nécessaires
          forwardedHeadersTrustedIPs:
            - "192.168.200.0/24"
```

**Vérification**:
```bash
docker logs traefik 2>&1 | grep -i crowdsec | tail -5
# Ne doit plus afficher d'erreurs 403
```

---

### 2.2 Mettre à jour les clients ChromaDB vers API v2

**Problème**: L'API v1 de ChromaDB est dépréciée (`410 Gone`), mais l'API v2 fonctionne.

**Impact**: Les anciens clients utilisant `/api/v1/` échoueront.

**Vérification des clients à mettre à jour**:

```bash
# Chercher les références à l'API v1 dans le code
grep -r "api/v1" /home/lalpha/projets/ai-tools/ --include="*.py" --include="*.js" --include="*.ts"
grep -r "api/v1" /home/lalpha/projets/ai-tools/mcp-servers/ --include="*.py" --include="*.js" --include="*.ts"
```

**Modification type**:

```python
# Avant
CHROMA_URL = "http://chromadb:8000/api/v1"

# Après
CHROMA_URL = "http://chromadb:8000/api/v2"
```

**Fichiers probables à vérifier**:
- `/home/lalpha/projets/ai-tools/mcp-servers/chromadb-mcp/`
- `/home/lalpha/projets/ai-tools/ai-orchestrator/backend/`

---

## 🟢 Priorité 3 - Nettoyage

### 3.1 Identifier les processus inconnus sur les ports hôte

**Problème**: Plusieurs processus Python écoutent sur des ports non documentés.

| Port | PID | À identifier |
|------|-----|--------------|
| 5000 | 2700561 | ? |
| 9101 | 2888504 | ? |
| 9102 | 2888503 | ? |

**Diagnostic**:

```bash
# Identifier les processus
ps aux | grep -E "2700561|2888504|2888503"
ls -la /proc/2700561/cwd
cat /proc/2700561/cmdline | tr '\0' ' '
```

**Action**: Documenter ou arrêter si non nécessaires.

---

### 3.2 Supprimer les fichiers backup obsolètes

**Fichiers à nettoyer**:

```bash
# Lister les backups dans unified-stack
ls -la /home/lalpha/projets/infrastructure/unified-stack/*.backup* 
ls -la /home/lalpha/projets/infrastructure/unified-stack/*.bak*
ls -la /home/lalpha/projets/infrastructure/unified-stack/configs/traefik/dynamic/*.backup*

# Supprimer les backups de plus de 7 jours
find /home/lalpha/projets/infrastructure/unified-stack/ -name "*.backup*" -mtime +7 -delete
find /home/lalpha/projets/infrastructure/unified-stack/ -name "*.bak*" -mtime +7 -delete
```

---

## 📝 Script de Correction Automatisé

```bash
#!/bin/bash
# correction-infrastructure-2026-01-20.sh
# Exécuter depuis /home/lalpha/projets/infrastructure/unified-stack/

set -e

echo "=== Correction Infrastructure - $(date) ==="

# 1. Backup préalable
echo "[1/5] Création backup..."
cp docker-compose.yml "docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)"

# 2. Supprimer conteneur orphelin
echo "[2/5] Suppression conteneur orphelin..."
docker rm ai-orchestrator-backend 2>/dev/null || echo "Conteneur déjà supprimé"

# 3. Désactiver traefik.enable sur ai-orchestrator-frontend
echo "[3/5] Modification docker-compose.yml..."
sed -i 's/traefik.enable=true/traefik.enable=false/g' docker-compose.yml
# Note: Vérifier manuellement que seul ai-orchestrator-frontend est affecté

# 4. Redémarrer les services affectés
echo "[4/5] Redémarrage services..."
docker compose up -d ai-orchestrator-frontend

# 5. Vérification
echo "[5/5] Vérification..."
sleep 5
curl -s http://127.0.0.1:8080/api/http/routers | grep -c "ai-orchestrator-frontend-unified-stack" && echo "⚠️ Router parasite encore présent" || echo "✅ Router parasite supprimé"
docker ps --filter "status=created" --format "{{.Names}}" | grep -q "ai-orchestrator-backend" && echo "⚠️ Conteneur orphelin encore présent" || echo "✅ Conteneur orphelin supprimé"

echo "=== Correction terminée ==="
```

---

## ✅ Checklist de Validation Post-Correction

```bash
# 1. Tous les domaines répondent
for d in ai.4lb.ca llm.4lb.ca files.4lb.ca grafana.4lb.ca prometheus.4lb.ca code.4lb.ca jsr.4lb.ca jsr-solutions.ca 4lb.ca a0.4lb.ca; do
  echo -n "$d: "
  curl -k -sS -o /dev/null -w "%{http_code}\n" --max-time 5 "https://$d"
done

# 2. API AI Orchestrator fonctionne
curl -k -s https://ai.4lb.ca/api/v1/system/health | jq .

# 3. Pas de conteneurs en état "created"
docker ps -a --filter "status=created" --format "{{.Names}}"

# 4. Pas de router parasite
curl -s http://127.0.0.1:8080/api/http/routers | jq '.[].name' | grep -v "@" | sort

# 5. Logs Traefik sans erreurs critiques
docker logs traefik 2>&1 | tail -50 | grep -iE "error|fatal" || echo "OK - Pas d'erreurs"

# 6. Services DB fonctionnels
docker exec postgres psql -U lalpha -d main -c "SELECT 1;" >/dev/null && echo "PostgreSQL: OK"
docker exec redis redis-cli ping | grep -q PONG && echo "Redis: OK"
```

---

## 📊 Tableau Récapitulatif

| # | Correction | Fichier/Service | Temps | Risque |
|---|------------|-----------------|-------|--------|
| 1.1 | Désactiver router parasite | docker-compose.yml | 5 min | Faible |
| 1.2 | Supprimer conteneur orphelin | Docker | 2 min | Nul |
| 2.1 | Corriger CrowdSec | middlewares.yml | 10 min | Faible |
| 2.2 | Migrer ChromaDB v2 | Code clients | 15 min | Moyen |
| 3.1 | Identifier ports inconnus | Système | 10 min | Nul |
| 3.2 | Nettoyer backups | Fichiers | 5 min | Nul |

---

## 📅 Suivi

- [ ] Correction 1.1 appliquée
- [ ] Correction 1.2 appliquée
- [ ] Correction 2.1 appliquée
- [ ] Correction 2.2 appliquée
- [ ] Nettoyage 3.1 effectué
- [ ] Nettoyage 3.2 effectué
- [ ] Validation post-correction passée
- [ ] Documentation mise à jour

---

*Document généré le 20 janvier 2026 - Infrastructure lalpha-server-1*
