# Observabilité Complète - Traefik + Grafana + Prometheus + Loki

Guide production-grade pour une observabilité type "Laravel Telescope" sur infrastructure Ubuntu + Docker + Traefik.

**Objectif**: Voir toutes les requêtes HTTP (codes status, URLs, backends, latence, erreurs) via Grafana.

---

## 📋 Table des matières

1. [Diagnostic de l'existant](#1-diagnostic-de-lexistant)
2. [Configuration Traefik](#2-configuration-traefik)
3. [Configuration Promtail](#3-configuration-promtail)
4. [Configuration Prometheus](#4-configuration-prometheus)
5. [Requêtes LogQL](#5-requêtes-logql)
6. [Dashboards Grafana](#6-dashboards-grafana)
7. [Validation](#7-validation)

---

## 1. Diagnostic de l'existant

### 1.1 Vérifier la stack Grafana/Prometheus/Loki

```bash
# Vérifier que les services sont actifs
docker ps | grep -E "(grafana|prometheus|loki|promtail)"

# Tester Grafana
curl -s http://localhost:3000/api/health | jq

# Tester Prometheus
curl -s http://localhost:9090/-/healthy

# Tester Loki
curl -s http://localhost:3100/ready

# Vérifier datasources Grafana
curl -s -u admin:admin http://localhost:3000/api/datasources | jq
```

**Expected**:
- Grafana: `{"database":"ok"}`
- Prometheus: `Healthy`
- Loki: `ready`

---

### 1.2 Vérifier Traefik

```bash
# Vérifier version Traefik
docker exec traefik traefik version

# Vérifier config actuelle
docker exec traefik cat /etc/traefik/traefik.yml

# Vérifier logs actuels
docker logs traefik --tail 50
```

---

## 2. Configuration Traefik

### 2.1 Activer les access logs JSON

**Fichier**: `/etc/traefik/traefik.yml` (ou dans votre config Traefik)

```yaml
# Traefik Static Configuration
global:
  checkNewVersion: true
  sendAnonymousUsage: false

# API et Dashboard
api:
  dashboard: true
  insecure: false  # Utiliser Traefik pour sécuriser le dashboard

# Entrypoints
entryPoints:
  web:
    address: ":80"
    # Redirect HTTP → HTTPS (optionnel)
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https

  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt

# Providers
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: web

  file:
    directory: /etc/traefik/dynamic
    watch: true

# Certificats Let's Encrypt
certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@4lb.ca
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

# LOGS - CRUCIAL POUR OBSERVABILITÉ
log:
  level: INFO
  filePath: /var/log/traefik/traefik.log
  format: json

# ACCESS LOGS - TOUTES LES REQUÊTES HTTP
accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  bufferingSize: 100

  filters:
    statusCodes:
      - "200-599"  # Tous les codes
    retryAttempts: true
    minDuration: 0

  fields:
    defaultMode: keep
    names:
      ClientUsername: drop
    headers:
      defaultMode: keep
      names:
        User-Agent: keep
        Authorization: drop
        Cookie: drop

# Métriques Prometheus
metrics:
  prometheus:
    addEntryPointsLabels: true
    addRoutersLabels: true
    addServicesLabels: true
    entryPoint: metrics
    buckets:
      - 0.1
      - 0.3
      - 1.0
      - 3.0
      - 10.0

entryPoints:
  metrics:
    address: ":8082"
```

---

### 2.2 Docker Compose pour Traefik

Si Traefik est en Docker, utilisez cette config:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - web
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard (localhost only)
      - "8082:8082"  # Métriques Prometheus
    environment:
      - TZ=America/Toronto
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - ./traefik/letsencrypt:/letsencrypt
      - ./traefik/logs:/var/log/traefik  # IMPORTANT: Logs persistés
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.4lb.ca`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"

networks:
  web:
    external: true
```

**Créer le répertoire de logs**:
```bash
mkdir -p ./traefik/logs
chmod 755 ./traefik/logs
```

---

### 2.3 Redémarrer Traefik

```bash
# Si Docker Compose
docker-compose restart traefik

# Ou
docker restart traefik

# Vérifier que les logs sont créés
ls -lh ./traefik/logs/
tail -f ./traefik/logs/access.log
```

---

## 3. Configuration Promtail

### 3.1 Promtail config complète

**Fichier**: `promtail/promtail.yml`

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # 1. TRAEFIK ACCESS LOGS (JSON)
  - job_name: traefik-access
    static_configs:
      - targets:
          - localhost
        labels:
          job: traefik
          log_type: access
          __path__: /var/log/traefik/access.log

    pipeline_stages:
      # Parser JSON
      - json:
          expressions:
            level: level
            time: time
            request_method: RequestMethod
            request_path: RequestPath
            request_protocol: RequestProtocol
            status_code: DownstreamStatus
            duration: Duration
            client_host: ClientHost
            backend_name: RouterName
            backend_addr: DownstreamContentSize

      # Extraire le code HTTP
      - labels:
          status_code:
          request_method:
          backend_name:

      # Timestamp
      - timestamp:
          source: time
          format: RFC3339

  # 2. TRAEFIK ERROR LOGS
  - job_name: traefik-error
    static_configs:
      - targets:
          - localhost
        labels:
          job: traefik
          log_type: error
          __path__: /var/log/traefik/traefik.log

    pipeline_stages:
      - json:
          expressions:
            level: level
            msg: msg
            time: time
      - labels:
          level:
      - timestamp:
          source: time
          format: RFC3339

  # 3. LOGS DOCKER CONTAINERS
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s

    relabel_configs:
      # Nom du container
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container_name'

      # Image
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'

    pipeline_stages:
      # Détecter si c'est du JSON
      - match:
          selector: '{container_name=~"ai-orchestrator.*"}'
          stages:
            - json:
                expressions:
                  level: level
                  timestamp: timestamp
                  request_id: request_id
                  duration_ms: duration_ms
            - labels:
                level:
                request_id:

  # 4. AI-ORCHESTRATOR BACKEND (systemd, pas Docker)
  - job_name: ai-orchestrator
    static_configs:
      - targets:
          - localhost
        labels:
          job: ai-orchestrator
          service: backend
          __path__: /var/log/ai-orchestrator/*.log  # Adapter selon votre config

    pipeline_stages:
      - json:
          expressions:
            level: level
            timestamp: timestamp
            logger: logger
            request_id: request_id
            duration_ms: duration_ms
            status_code: status_code

      - labels:
          level:
          logger:
          status_code:

      - timestamp:
          source: timestamp
          format: RFC3339
```

---

### 3.2 Docker Compose pour Promtail

```yaml
version: '3.8'

services:
  promtail:
    image: grafana/promtail:2.9.3
    container_name: promtail
    restart: unless-stopped
    volumes:
      - ./promtail/promtail.yml:/etc/promtail/promtail.yml:ro
      - /var/log:/var/log:ro  # Tous les logs système
      - /var/lib/docker/containers:/var/lib/docker/containers:ro  # Logs Docker
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Discovery Docker
      - ./traefik/logs:/var/log/traefik:ro  # Logs Traefik
    command: -config.file=/etc/promtail/promtail.yml
    networks:
      - monitoring

networks:
  monitoring:
    external: true
```

**Démarrer Promtail**:
```bash
docker-compose up -d promtail

# Vérifier les logs
docker logs -f promtail
```

---

## 4. Configuration Prometheus

### 4.1 Prometheus config

**Fichier**: `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    monitor: 'ai-orchestrator'

# Alertmanager (optionnel)
# alerting:
#   alertmanagers:
#     - static_configs:
#         - targets: ['alertmanager:9093']

# Règles d'alerte (optionnel)
# rule_files:
#   - "alerts/*.yml"

scrape_configs:
  # 1. Prometheus lui-même
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # 2. TRAEFIK MÉTRIQUES
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8082']  # Port métriques Traefik
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: traefik

  # 3. AI-ORCHESTRATOR BACKEND
  - job_name: 'ai-orchestrator'
    static_configs:
      - targets: ['192.168.200.1:8001']  # Backend sur hôte
    metrics_path: '/metrics'  # Endpoint métriques
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: ai-orchestrator-backend

  # 4. OLLAMA (si expose des métriques)
  - job_name: 'ollama'
    static_configs:
      - targets: ['192.168.200.1:11434']
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: ollama

  # 5. Node Exporter (pour métriques système)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # 6. cAdvisor (pour métriques Docker)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

---

### 4.2 Services complémentaires (optionnel mais recommandé)

**Docker Compose**:
```yaml
version: '3.8'

services:
  # Node Exporter - Métriques système
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring
    ports:
      - "9100:9100"

  # cAdvisor - Métriques Docker
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    restart: unless-stopped
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    networks:
      - monitoring
    ports:
      - "8080:8080"
    privileged: true
    devices:
      - /dev/kmsg

networks:
  monitoring:
    external: true
```

---

## 5. Requêtes LogQL

### 5.1 Requêtes de base

#### Toutes les requêtes HTTP (Traefik)
```logql
{job="traefik", log_type="access"}
```

#### Filtrer par code HTTP
```logql
# Toutes les erreurs 4xx
{job="traefik", log_type="access"} | json | status_code >= 400 and status_code < 500

# Toutes les erreurs 5xx
{job="traefik", log_type="access"} | json | status_code >= 500

# Seulement 200 OK
{job="traefik", log_type="access"} | json | status_code = 200

# 404 uniquement
{job="traefik", log_type="access"} | json | status_code = 414
```

---

### 5.2 Filtrer par route/backend

```logql
# Requêtes vers le backend AI
{job="traefik", log_type="access"} | json | backend_name =~ ".*ai-orchestrator.*"

# Requêtes vers une URL spécifique
{job="traefik", log_type="access"} | json | request_path =~ "/api/v1/chat.*"

# Filtrer par méthode HTTP
{job="traefik", log_type="access"} | json | request_method = "POST"
```

---

### 5.3 Analyse de latence

```logql
# Requêtes lentes (> 1 seconde)
{job="traefik", log_type="access"} | json | duration > 1000000000

# Latence moyenne par backend
sum by (backend_name) (rate({job="traefik"} | json | __error__="" [5m]))

# Top 10 requêtes les plus lentes
topk(10,
  sum by (request_path) (
    avg_over_time({job="traefik", log_type="access"} | json | unwrap duration [5m])
  )
)
```

---

### 5.4 Logs AI-Orchestrator

```logql
# Tous les logs backend
{job="ai-orchestrator"}

# Erreurs uniquement
{job="ai-orchestrator"} | json | level = "ERROR"

# Suivre une requête spécifique (via request_id)
{job="ai-orchestrator"} | json | request_id = "abc-123-def"

# Logs avec durée > 5 secondes
{job="ai-orchestrator"} | json | duration_ms > 5000
```

---

### 5.5 Requêtes combinées (Traefik + Backend)

```logql
# Corréler Traefik + Backend via request_id
{job=~"traefik|ai-orchestrator"} | json | request_id = "abc-123"

# Erreurs 5xx + logs backend
{job="traefik", status_code >= 500} or {job="ai-orchestrator", level="ERROR"}
```

---

## 6. Dashboards Grafana

### 6.1 Importer dashboards officiels

**Via Grafana UI**:
1. Grafana → Dashboards → Import
2. Importer par ID:

| Dashboard | ID | Description |
|-----------|----|----|
| **Traefik Official** | 17346 | Dashboard complet Traefik v2 |
| **Traefik v2.2** | 11462 | Métriques détaillées |
| **Docker Monitoring** | 893 | Métriques containers |
| **Node Exporter Full** | 1860 | Métriques système |

**Ou via API**:
```bash
# Importer dashboard Traefik
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{
    "dashboard": {
      "id": null,
      "uid": null,
      "title": "Traefik",
      "tags": ["traefik"],
      "timezone": "browser"
    },
    "overwrite": false,
    "inputs": [{
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    }]
  }'
```

---

### 6.2 Dashboard custom "HTTP Observatory"

**Fichier**: `grafana/dashboards/http-observatory.json`

```json
{
  "title": "HTTP Observatory - AI Orchestrator",
  "panels": [
    {
      "title": "Requêtes HTTP par code",
      "targets": [
        {
          "expr": "sum by (status_code) (rate({job=\"traefik\", log_type=\"access\"} | json [5m]))"
        }
      ],
      "type": "timeseries"
    },
    {
      "title": "Latence p95",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le, service))"
        }
      ],
      "type": "timeseries"
    },
    {
      "title": "Erreurs 5xx",
      "targets": [
        {
          "expr": "sum(rate({job=\"traefik\", log_type=\"access\"} | json | status_code >= 500 [5m]))"
        }
      ],
      "type": "stat"
    },
    {
      "title": "Top URLs",
      "targets": [
        {
          "expr": "topk(10, sum by (request_path) (rate({job=\"traefik\"} | json [5m])))"
        }
      ],
      "type": "table"
    },
    {
      "title": "Logs Temps Réel",
      "targets": [
        {
          "expr": "{job=\"traefik\", log_type=\"access\"}"
        }
      ],
      "type": "logs"
    }
  ]
}
```

**Importer**:
```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @grafana/dashboards/http-observatory.json
```

---

### 6.3 Panels recommandés

**Pour un dashboard "Laravel Telescope-like"**, créez ces panels:

1. **Request Rate** (requêtes/sec)
   ```promql
   sum(rate(traefik_service_requests_total[5m]))
   ```

2. **Status Codes Distribution**
   ```logql
   sum by (status_code) (count_over_time({job="traefik"} | json [5m]))
   ```

3. **Response Time (p50, p95, p99)**
   ```promql
   histogram_quantile(0.95,
     sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le)
   )
   ```

4. **Error Rate**
   ```promql
   sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
   ```

5. **Top Slow Requests**
   ```logql
   topk(20,
     avg_over_time({job="traefik"} | json | unwrap duration [10m])
   ) by (request_path)
   ```

6. **Real-time Logs Table**
   - Query: `{job="traefik", log_type="access"} | json`
   - Afficher: time, status_code, request_method, request_path, duration, client_host

---

## 7. Validation

### 7.1 Tests de connectivité

```bash
# 1. Vérifier que Promtail envoie à Loki
curl -s http://localhost:9080/metrics | grep promtail_sent_entries_total

# 2. Vérifier que Loki reçoit des logs
curl -s "http://localhost:3100/loki/api/v1/label/__name__/values" | jq

# 3. Vérifier que Prometheus scrape Traefik
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="traefik")'

# 4. Tester requête LogQL via Loki API
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="traefik"}' \
  --data-urlencode 'limit=10' | jq
```

---

### 7.2 Test end-to-end

```bash
# 1. Générer du trafic HTTP
for i in {1..100}; do
  curl -s https://ai.4lb.ca/api/v1/system/health > /dev/null
  curl -s https://ai.4lb.ca/api/does-not-exist > /dev/null  # 404
done

# 2. Attendre 10 secondes (ingestion)
sleep 10

# 3. Vérifier dans Loki
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="traefik", status_code="404"}' \
  --data-urlencode 'limit=1' | jq '.data.result[0]'

# 4. Vérifier dans Prometheus
curl -s "http://localhost:9090/api/v1/query?query=traefik_service_requests_total" | jq
```

**Expected**: Vous devriez voir les 100 requêtes dans Loki et les compteurs dans Prometheus.

---

### 7.3 Checklist finale

- [ ] Traefik access logs en JSON activés
- [ ] Logs Traefik écrits dans `/var/log/traefik/access.log`
- [ ] Promtail lit les logs Traefik
- [ ] Promtail envoie à Loki (vérifier métriques `promtail_sent_entries_total`)
- [ ] Loki reçoit les logs (tester requête LogQL)
- [ ] Prometheus scrape Traefik métriques (port 8082)
- [ ] Grafana connecté à Prometheus + Loki
- [ ] Dashboard Traefik importé
- [ ] Dashboard custom créé
- [ ] Logs en temps réel visibles dans Grafana

---

## 8. Bonnes pratiques

### 8.1 Sécurité

```yaml
# Traefik - Protéger le dashboard
labels:
  - "traefik.http.routers.dashboard.middlewares=auth"
  - "traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$..."

# Prometheus - Activer authentication
global:
  external_labels:
    security_realm: 'production'

# Grafana - Changer le mot de passe par défaut
docker exec -it grafana grafana-cli admin reset-admin-password NEW_PASSWORD
```

---

### 8.2 Rétention

```yaml
# Loki - Limiter la rétention (éviter de remplir le disque)
limits_config:
  retention_period: 30d  # 30 jours

chunk_store_config:
  max_look_back_period: 30d

table_manager:
  retention_deletes_enabled: true
  retention_period: 30d

# Prometheus - Rétention
command:
  - '--storage.tsdb.retention.time=30d'
  - '--storage.tsdb.path=/prometheus'
```

---

### 8.3 Performance

```yaml
# Traefik - Buffering pour réduire I/O
accessLog:
  bufferingSize: 100  # Buffer 100 lignes avant d'écrire

# Promtail - Batch
clients:
  - url: http://loki:3100/loki/api/v1/push
    batchwait: 1s
    batchsize: 1048576  # 1 MB

# Prometheus - Scrape interval adapté
global:
  scrape_interval: 15s  # Pas trop fréquent
```

---

### 8.4 Alerting (optionnel)

**Fichier**: `prometheus/alerts/http_errors.yml`

```yaml
groups:
  - name: http_errors
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
          /
          sum(rate(traefik_service_requests_total[5m]))
          > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taux d'erreur 5xx élevé ({{ $value | humanizePercentage }})"
          description: "Plus de 5% des requêtes retournent une erreur 5xx"

      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95,
            sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le, service)
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latence p95 > 5s sur {{ $labels.service }}"
```

---

## 9. Commandes utiles

### 9.1 Diagnostics

```bash
# Logs Traefik
docker logs -f traefik

# Logs Promtail
docker logs -f promtail

# Tester LogQL directement
logcli --addr=http://localhost:3100 query '{job="traefik"}' --limit=10

# Tester PromQL
curl -s "http://localhost:9090/api/v1/query?query=up" | jq

# Vérifier taille des logs
du -sh /var/log/traefik/
du -sh /var/lib/docker/volumes/loki_data/
```

---

### 9.2 Maintenance

```bash
# Nettoyer anciens logs Traefik
find /var/log/traefik/ -name "*.log.*" -mtime +30 -delete

# Compacter Prometheus
docker exec prometheus promtool tsdb analyze /prometheus

# Backup Grafana dashboards
curl -s http://localhost:3000/api/search | jq -r '.[] | .uid' | while read uid; do
  curl -s "http://localhost:3000/api/dashboards/uid/$uid" > "backup-$uid.json"
done
```

---

## 10. Ressources

**Documentation officielle**:
- Traefik Observability: https://doc.traefik.io/traefik/observability/
- Promtail Configuration: https://grafana.com/docs/loki/latest/clients/promtail/configuration/
- LogQL Syntax: https://grafana.com/docs/loki/latest/logql/
- PromQL Basics: https://prometheus.io/docs/prometheus/latest/querying/basics/

**Dashboards Grafana**:
- https://grafana.com/grafana/dashboards/17346 (Traefik v2)
- https://grafana.com/grafana/dashboards/11462 (Traefik metrics)

---

**Prêt pour Phase 6 (métriques Prometheus enrichies dans AI-Orchestrator)?**
