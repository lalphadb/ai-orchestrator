#!/bin/bash
# Dashboard HTTP/Traefik - Vue complète du trafic HTTP

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Grafana4lb2025"

echo "📊 Création dashboard HTTP/Traefik..."

cat > /tmp/dashboard_http.json <<'EOF'
{
  "dashboard": {
    "title": "🌐 HTTP Traffic - Traefik & Services",
    "tags": ["http", "traefik", "requests"],
    "timezone": "browser",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "Total HTTP Requests/sec",
        "type": "stat",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate(traefik_service_requests_total[1m]))",
            "legendFormat": "Total req/s"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "color": {"mode": "thresholds"},
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 10, "color": "yellow"},
                {"value": 50, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "HTTP Status Codes",
        "type": "stat",
        "gridPos": {"x": 6, "y": 0, "w": 18, "h": 4},
        "targets": [
          {
            "expr": "sum(rate(traefik_service_requests_total{code=~\"2..\"}[5m]))",
            "legendFormat": "2xx Success"
          },
          {
            "expr": "sum(rate(traefik_service_requests_total{code=~\"3..\"}[5m]))",
            "legendFormat": "3xx Redirect"
          },
          {
            "expr": "sum(rate(traefik_service_requests_total{code=~\"4..\"}[5m]))",
            "legendFormat": "4xx Client Error"
          },
          {
            "expr": "sum(rate(traefik_service_requests_total{code=~\"5..\"}[5m]))",
            "legendFormat": "5xx Server Error"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          },
          "overrides": [
            {
              "matcher": {"id": "byName", "options": "2xx Success"},
              "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "green"}}]
            },
            {
              "matcher": {"id": "byName", "options": "4xx Client Error"},
              "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "yellow"}}]
            },
            {
              "matcher": {"id": "byName", "options": "5xx Server Error"},
              "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]
            }
          ]
        }
      },
      {
        "id": 3,
        "title": "Requests by Service",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum by (service) (rate(traefik_service_requests_total[5m]))",
            "legendFormat": "{{service}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "id": 4,
        "title": "Request Duration (p95)",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum by (service, le) (rate(traefik_service_request_duration_seconds_bucket[5m])))",
            "legendFormat": "{{service}} p95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 5,
        "title": "Error Rate by Service",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum by (service) (rate(traefik_service_requests_total{code=~\"5..\"}[5m]))",
            "legendFormat": "5xx {{service}}"
          },
          {
            "expr": "sum by (service) (rate(traefik_service_requests_total{code=~\"4..\"}[5m]))",
            "legendFormat": "4xx {{service}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Requests by Status Code",
        "type": "piechart",
        "gridPos": {"x": 12, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum by (code) (rate(traefik_service_requests_total[5m]))",
            "legendFormat": "{{code}}"
          }
        ]
      },
      {
        "id": 7,
        "title": "Top URLs by Request Count",
        "type": "table",
        "gridPos": {"x": 0, "y": 20, "w": 24, "h": 8},
        "targets": [
          {
            "expr": "topk(20, sum by (service, code) (rate(traefik_service_requests_total[5m])))",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "service": "Service",
                "code": "Status Code",
                "Value": "Req/s"
              }
            }
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF

curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @/tmp/dashboard_http.json 2>&1 | grep -q "success" && echo "✅ Dashboard HTTP Traffic créé" || echo "⚠️  Erreur HTTP Dashboard"

echo ""
echo "📊 Dashboard HTTP créé avec:"
echo "  - Requêtes totales/sec"
echo "  - Status codes (200, 404, 500, etc.)"
echo "  - Latence par service"
echo "  - Taux d'erreur"
echo "  - Top URLs"
