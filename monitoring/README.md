# 🔭 Observabilité AI-Orchestrator

Stack complète d'observabilité type "Laravel Telescope" pour infrastructure Traefik + Docker + services Ubuntu.

**Stack**: Traefik + Prometheus + Loki + Grafana + Promtail + Exporters

---

## 🚀 Quick Start (5 minutes)

```bash
cd monitoring/

# 1. Rendre le script exécutable
chmod +x setup.sh

# 2. Démarrer la stack
./setup.sh start

# 3. Accéder à Grafana
# URL: https://grafana.4lb.ca
# Login: admin / ChangeMe123!
```

**C'est tout!** Vous avez maintenant:
- ✅ Tous les logs HTTP de Traefik dans Loki
- ✅ Métriques Prometheus de tous les services
- ✅ Dashboards Grafana prêts à l'emploi

---

## 📊 Accès aux services

### URLs publiques (via Traefik)
- **Grafana**: https://grafana.4lb.ca
- **Prometheus**: https://prometheus.4lb.ca
- **Traefik Dashboard**: https://traefik.4lb.ca

### Ports locaux (localhost)
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Promtail**: http://localhost:9080
- **Traefik Dashboard**: http://localhost:8080

### Credentials
- **Grafana**: `admin` / `ChangeMe123!`
- **Traefik**: `admin` / `password` (à changer dans docker-compose.yml)

---

## 📁 Structure des fichiers

```
monitoring/
├── docker-compose.yml          # Stack complète
├── setup.sh                    # Script de gestion
├── traefik/
│   ├── traefik.yml            # Config Traefik avec access logs JSON
│   ├── dynamic/               # Configs dynamiques (middlewares, etc.)
│   └── logs/                  # Logs Traefik (access.log, traefik.log)
├── prometheus/
│   ├── prometheus.yml         # Scrape configs
│   └── alerts/
│       └── http_errors.yml    # Alertes HTTP 4xx/5xx
├── loki/
│   └── loki.yml              # Config Loki (rétention 30j)
├── promtail/
│   └── promtail.yml          # Collection logs (Traefik, Docker, AI-backend)
└── grafana/
    ├── provisioning/
    │   └── datasources/
    │       └── datasources.yml  # Prometheus + Loki auto-config
    └── dashboards/             # Dashboards JSON
```

---

## 🎯 Requêtes prêtes à l'emploi

### LogQL (Loki - pour les logs)

Copier-coller dans **Grafana → Explore → Loki**:

#### Toutes les requêtes HTTP
```logql
{job="traefik", log_type="access"}
```

#### Erreurs 5xx uniquement
```logql
{job="traefik", log_type="access"} | json | status_code >= 500
```

#### Requêtes vers AI-Orchestrator backend
```logql
{job="traefik", log_type="access"} | json | backend_name =~ ".*ai.*"
```

#### Top 10 URLs les plus lentes
```logql
topk(10,
  sum by (request_path) (
    avg_over_time({job="traefik"} | json | unwrap duration [5m])
  )
)
```

#### Suivre une requête spécifique (via request_id)
```logql
{job=~"traefik|ai-orchestrator"} | json | request_id = "abc-123"
```

### PromQL (Prometheus - pour les métriques)

Copier-coller dans **Grafana → Explore → Prometheus**:

#### Requêtes HTTP par seconde
```promql
sum(rate(traefik_service_requests_total[5m]))
```

#### Latence p95 par service
```promql
histogram_quantile(0.95,
  sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le, service)
)
```

#### Taux d'erreur 5xx
```promql
sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
/
sum(rate(traefik_service_requests_total[5m]))
```

---

## 🛠️ Commandes utiles

### Gestion de la stack

```bash
# Démarrer
./setup.sh start

# Arrêter
./setup.sh stop

# Redémarrer
./setup.sh restart

# Voir les logs
./setup.sh logs                 # Tous les logs
./setup.sh logs grafana         # Logs Grafana seulement
./setup.sh logs promtail        # Logs Promtail seulement

# Valider que tout fonctionne
./setup.sh validate

# Tests end-to-end
./setup.sh test

# Backup dashboards Grafana
./setup.sh backup
```

### Docker Compose direct

```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f grafana

# Reconstruire un service
docker-compose up -d --force-recreate grafana

# Voir les ressources
docker stats
```

---

## 🔍 Validation

### 1. Vérifier que Traefik écrit les logs

```bash
# Les logs doivent être en JSON
tail -f traefik/logs/access.log

# Devrait afficher des lignes comme:
# {"level":"info","RequestMethod":"GET","RequestPath":"/api/v1/health",...}
```

### 2. Vérifier que Promtail envoie à Loki

```bash
# Métriques Promtail (nombre de lignes envoyées)
curl -s http://localhost:9080/metrics | grep promtail_sent_entries_total

# Devrait montrer un compteur qui augmente
```

### 3. Vérifier que Loki reçoit les logs

```bash
# Via API Loki
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="traefik"}' \
  --data-urlencode 'limit=5' | jq

# Via logcli (si installé)
logcli --addr=http://localhost:3100 query '{job="traefik"}' --limit=10
```

### 4. Vérifier les datasources Grafana

```bash
curl -s http://localhost:3000/api/datasources -u admin:ChangeMe123! | jq

# Devrait lister Prometheus et Loki
```

---

## 📊 Dashboards recommandés

### Importer dashboards officiels

**Grafana → Dashboards → Import → Par ID**:

| ID | Nom | Description |
|----|-----|-------------|
| **17346** | Traefik Official | Dashboard complet Traefik v2 |
| **11462** | Traefik v2.2 | Métriques détaillées |
| **1860** | Node Exporter Full | Métriques système (CPU, RAM, Disk) |
| **893** | Docker Monitoring | Métriques containers |
| **13665** | Loki Dashboard | Monitoring Loki lui-même |

### Dashboard custom "HTTP Observatory"

Créer un nouveau dashboard avec ces panels:

**Panel 1: Requêtes/sec**
```promql
sum(rate(traefik_service_requests_total[5m]))
```

**Panel 2: Codes HTTP (pie chart)**
```logql
sum by (status_code) (count_over_time({job="traefik"} | json [5m]))
```

**Panel 3: Latence p95**
```promql
histogram_quantile(0.95,
  sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le)
)
```

**Panel 4: Logs temps réel (table)**
```logql
{job="traefik", log_type="access"} | json
```

**Panel 5: Top URLs**
```logql
topk(20,
  sum by (request_path) (rate({job="traefik"} | json [5m]))
)
```

---

## 🔧 Configuration backend AI-Orchestrator

### 1. Activer les métriques Prometheus

Le backend expose déjà `/metrics` sur le port 8001. Prometheus est configuré pour le scraper.

**Vérifier**:
```bash
curl http://localhost:8001/metrics

# Devrait afficher des métriques Prometheus
```

### 2. Logs structurés JSON

**Fichier**: `backend/.env`
```bash
LOG_FORMAT=json
LOG_LEVEL=INFO
```

**Redémarrer le backend**:
```bash
sudo systemctl restart ai-orchestrator
```

**Vérifier**:
```bash
journalctl -u ai-orchestrator -f --output=cat

# Les logs doivent être en JSON:
# {"timestamp":"2026-01-26T...","level":"INFO",...}
```

### 3. Configurer Promtail pour lire les logs backend

**Option A**: Via journald (si systemd)
```yaml
# Déjà configuré dans promtail.yml
- job_name: systemd
  journal:
    labels:
      job: systemd
  relabel_configs:
    - source_labels: ['__journal__systemd_unit']
      regex: 'ai-orchestrator.service'
      target_label: 'unit'
```

**Option B**: Via fichiers logs
```yaml
- job_name: ai-orchestrator
  static_configs:
    - targets: [localhost]
      labels:
        job: ai-orchestrator
        __path__: /var/log/ai-orchestrator/*.log
```

---

## ⚡ Performance

### Ressources utilisées (typique)

| Service | RAM | CPU | Disque |
|---------|-----|-----|--------|
| Traefik | 50-100 MB | 1-5% | - |
| Prometheus | 200-500 MB | 2-5% | 1-5 GB (30j) |
| Loki | 100-300 MB | 1-3% | 2-10 GB (30j) |
| Promtail | 50-100 MB | 1-2% | - |
| Grafana | 100-200 MB | 1-3% | 500 MB |
| **Total** | **~1 GB** | **~10%** | **~5-15 GB** |

### Optimisations

**Si disque faible**, réduire la rétention:

```yaml
# loki/loki.yml
limits_config:
  retention_period: 7d  # Au lieu de 30d

# prometheus/prometheus.yml (dans docker-compose)
command:
  - '--storage.tsdb.retention.time=7d'  # Au lieu de 30d
```

**Si RAM faible**, limiter les caches:

```yaml
# loki/loki.yml
query_range:
  results_cache:
    cache:
      embedded_cache:
        max_size_mb: 100  # Au lieu de 500
```

---

## 🚨 Alerting (optionnel)

### Configuration Alertmanager

**1. Décommenter dans docker-compose.yml**:
```yaml
alertmanager:
  image: prom/alertmanager:latest
  # ...
```

**2. Créer alertmanager.yml**:
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@4lb.ca'
  smtp_auth_username: 'alerts@4lb.ca'
  smtp_auth_password: 'your_password'

route:
  receiver: 'email'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@4lb.ca'
        headers:
          Subject: '[AI-Orchestrator] {{ .GroupLabels.alertname }}'
```

**3. Redémarrer**:
```bash
docker-compose up -d alertmanager
```

Les alertes définies dans `prometheus/alerts/http_errors.yml` seront envoyées par email.

---

## 🐛 Troubleshooting

### Problème: Pas de logs dans Loki

**Diagnostic**:
```bash
# 1. Vérifier que Traefik écrit les logs
ls -lh traefik/logs/
tail traefik/logs/access.log

# 2. Vérifier que Promtail lit le fichier
docker logs promtail | grep traefik

# 3. Vérifier métriques Promtail
curl http://localhost:9080/metrics | grep promtail_file_bytes_total
```

**Solution**: Vérifier les permissions sur `traefik/logs/`.

---

### Problème: Prometheus ne scrape pas AI-Orchestrator

**Diagnostic**:
```bash
# 1. Vérifier que le backend expose /metrics
curl http://192.168.200.1:8001/metrics

# 2. Vérifier targets Prometheus
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="ai-orchestrator-backend")'
```

**Solution**: Vérifier que le backend est accessible depuis le conteneur Prometheus.

---

### Problème: Grafana ne se connecte pas aux datasources

**Diagnostic**:
```bash
# Tester depuis le conteneur Grafana
docker exec grafana curl -s http://prometheus:9090/-/healthy
docker exec grafana curl -s http://loki:3100/ready
```

**Solution**: Vérifier que les services sont sur le même réseau Docker (`monitoring`).

---

## 📚 Ressources

### Documentation officielle
- **Traefik Observability**: https://doc.traefik.io/traefik/observability/
- **Prometheus**: https://prometheus.io/docs/
- **Loki**: https://grafana.com/docs/loki/
- **LogQL**: https://grafana.com/docs/loki/latest/logql/
- **PromQL**: https://prometheus.io/docs/prometheus/latest/querying/basics/

### Dashboards Grafana
- **Traefik**: https://grafana.com/grafana/dashboards/17346
- **Node Exporter**: https://grafana.com/grafana/dashboards/1860
- **Docker**: https://grafana.com/grafana/dashboards/893

### Tutoriels
- LogQL Cheat Sheet: https://megamorf.gitlab.io/cheat-sheets/loki/
- PromQL Cheat Sheet: https://promlabs.com/promql-cheat-sheet/

---

## ✅ Checklist de déploiement

- [ ] `./setup.sh start` exécuté avec succès
- [ ] Grafana accessible (https://grafana.4lb.ca)
- [ ] Prometheus accessible (https://prometheus.4lb.ca)
- [ ] Traefik dashboard accessible (https://traefik.4lb.ca)
- [ ] Logs Traefik visibles dans Loki (requête LogQL)
- [ ] Métriques Traefik dans Prometheus
- [ ] Backend AI-Orchestrator scrapé par Prometheus
- [ ] Dashboard Traefik importé (ID 17346)
- [ ] Dashboard custom créé
- [ ] Mot de passe Grafana changé (`ChangeMe123!` → votre mot de passe)
- [ ] Basic auth Traefik configuré
- [ ] Rétention configurée (Loki 30j, Prometheus 30j)
- [ ] Alerting configuré (optionnel)
- [ ] Backup automatique configuré (optionnel)

---

**Support**: Consultez `docs/OBSERVABILITY_SETUP.md` pour le guide complet.
