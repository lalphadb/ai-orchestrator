# Observability

Production-grade monitoring stack with Traefik, Grafana, Prometheus, and Loki.

## Stack

| Service | Purpose | Port |
|---------|---------|------|
| Grafana | Dashboards and visualization | 3000 |
| Prometheus | Metrics collection | 9090 |
| Loki | Log aggregation | 3100 |
| Promtail | Log shipping | 9080 |

## Setup

```bash
cd monitoring
docker compose up -d
```

## Traefik Access Logs

Enable JSON access logs in Traefik for full HTTP observability:

```yaml
accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  bufferingSize: 100
```

## LogQL Queries

```logql
# All HTTP requests
{job="traefik", log_type="access"}

# 5xx errors
{job="traefik", log_type="access"} | json | status_code >= 500

# AI Orchestrator backend errors
{job="ai-orchestrator"} | json | level = "ERROR"

# Trace by request ID
{job=~"traefik|ai-orchestrator"} | json | request_id = "abc-123"
```

## PromQL Metrics

```promql
# Request rate
sum(rate(traefik_service_requests_total[5m]))

# Latency p95
histogram_quantile(0.95, sum(rate(traefik_service_request_duration_seconds_bucket[5m])) by (le))

# Error rate
sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
```

## Grafana Dashboards

Import by ID:
- **17346** - Traefik Official
- **1860** - Node Exporter Full
- **893** - Docker Monitoring

Custom dashboards are provisioned from `monitoring/grafana/dashboards/`.

## Alerts

Alert rules in `monitoring/prometheus/alerts/http_errors.yml`:
- High error rate (>5% 5xx for 2 min)
- Slow response time (p95 > 5s for 5 min)
