#!/bin/bash
# Configuration automatique de Grafana
# Crée datasources et dashboards professionnels

set -e

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Grafana4lb2025"

echo "🔧 Configuration Grafana..."
echo ""

# Attendre que Grafana soit prêt
echo "⏳ Attente de Grafana..."
for i in {1..30}; do
    if curl -s "${GRAFANA_URL}/api/health" | grep -q "ok"; then
        echo "✅ Grafana prêt!"
        break
    fi
    sleep 2
done

# ============================================
# 1. CRÉER DATASOURCES
# ============================================
echo ""
echo "📊 Création des datasources..."

# Prometheus
curl -X POST "${GRAFANA_URL}/api/datasources" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true,
    "jsonData": {
      "timeInterval": "15s",
      "httpMethod": "POST"
    }
  }' 2>&1 | grep -q "Datasource added" && echo "✅ Prometheus créé" || echo "⚠️  Prometheus existe déjà"

# Loki
curl -X POST "${GRAFANA_URL}/api/datasources" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://loki:3100",
    "access": "proxy",
    "jsonData": {
      "maxLines": 1000
    }
  }' 2>&1 | grep -q "Datasource added" && echo "✅ Loki créé" || echo "⚠️  Loki existe déjà"

# ============================================
# 2. CRÉER DOSSIERS
# ============================================
echo ""
echo "📁 Création des dossiers..."

# Infrastructure
INFRA_UID=$(curl -X POST "${GRAFANA_URL}/api/folders" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d '{"title": "Infrastructure"}' 2>/dev/null | jq -r '.uid')
echo "✅ Dossier Infrastructure: ${INFRA_UID}"

# AI-Orchestrator
AI_UID=$(curl -X POST "${GRAFANA_URL}/api/folders" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d '{"title": "AI-Orchestrator"}' 2>/dev/null | jq -r '.uid')
echo "✅ Dossier AI-Orchestrator: ${AI_UID}"

# ============================================
# 3. CRÉER DASHBOARDS
# ============================================
echo ""
echo "📈 Création des dashboards..."

# Dashboard 1: System Overview
cat > /tmp/dashboard_system.json <<'EOF'
{
  "dashboard": {
    "title": "System Overview",
    "tags": ["system", "infrastructure"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          }
        ]
      },
      {
        "id": 2,
        "title": "Memory Usage",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)",
            "legendFormat": "Memory Usage %"
          }
        ]
      },
      {
        "id": 3,
        "title": "Disk Usage",
        "type": "gauge",
        "gridPos": {"x": 0, "y": 8, "w": 8, "h": 6},
        "targets": [
          {
            "expr": "100 - ((node_filesystem_avail_bytes{mountpoint=\"/\"} * 100) / node_filesystem_size_bytes{mountpoint=\"/\"})",
            "legendFormat": "Disk %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 70, "color": "yellow"},
                {"value": 90, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Network Traffic",
        "type": "timeseries",
        "gridPos": {"x": 8, "y": 8, "w": 16, "h": 6},
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m])",
            "legendFormat": "RX {{device}}"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m])",
            "legendFormat": "TX {{device}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "Bps"
          }
        }
      }
    ]
  },
  "overwrite": true
}
EOF

curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @/tmp/dashboard_system.json 2>&1 | grep -q "success" && echo "✅ Dashboard System Overview créé" || echo "⚠️  Erreur System Overview"

# Dashboard 2: Docker Containers
cat > /tmp/dashboard_docker.json <<'EOF'
{
  "dashboard": {
    "title": "Docker Containers",
    "tags": ["docker", "containers"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Container CPU Usage",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{name!=\"\"}[5m]) * 100",
            "legendFormat": "{{name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "id": 2,
        "title": "Container Memory Usage",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "container_memory_usage_bytes{name!=\"\"} / 1024 / 1024",
            "legendFormat": "{{name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "decmbytes"
          }
        }
      },
      {
        "id": 3,
        "title": "Container Network I/O",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
        "targets": [
          {
            "expr": "rate(container_network_receive_bytes_total{name!=\"\"}[5m])",
            "legendFormat": "RX {{name}}"
          },
          {
            "expr": "rate(container_network_transmit_bytes_total{name!=\"\"}[5m])",
            "legendFormat": "TX {{name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "Bps"
          }
        }
      }
    ]
  },
  "overwrite": true
}
EOF

curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @/tmp/dashboard_docker.json 2>&1 | grep -q "success" && echo "✅ Dashboard Docker Containers créé" || echo "⚠️  Erreur Docker"

# Dashboard 3: AI-Orchestrator Backend
cat > /tmp/dashboard_backend.json <<'EOF'
{
  "dashboard": {
    "title": "AI-Orchestrator Backend",
    "tags": ["backend", "ai-orchestrator"],
    "timezone": "browser",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Rate",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"ai-orchestrator-backend\"}[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time (p95)",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"ai-orchestrator-backend\"}[5m]))",
            "legendFormat": "p95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 3,
        "title": "Active Connections",
        "type": "stat",
        "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "process_open_fds{job=\"ai-orchestrator-backend\"}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Memory Usage",
        "type": "gauge",
        "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "process_resident_memory_bytes{job=\"ai-orchestrator-backend\"} / 1024 / 1024"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "decmbytes"
          }
        }
      },
      {
        "id": 5,
        "title": "Python GC Collections",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 4},
        "targets": [
          {
            "expr": "rate(python_gc_collections_total{job=\"ai-orchestrator-backend\"}[5m])",
            "legendFormat": "Gen {{generation}}"
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
  -d @/tmp/dashboard_backend.json 2>&1 | grep -q "success" && echo "✅ Dashboard AI-Orchestrator Backend créé" || echo "⚠️  Erreur Backend"

# Dashboard 4: Logs
cat > /tmp/dashboard_logs.json <<'EOF'
{
  "dashboard": {
    "title": "Logs - All Services",
    "tags": ["logs", "loki"],
    "timezone": "browser",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "Recent Logs",
        "type": "logs",
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 20},
        "targets": [
          {
            "expr": "{job=~\".+\"}",
            "refId": "A",
            "datasource": {
              "type": "loki",
              "uid": "loki"
            }
          }
        ],
        "options": {
          "showTime": true,
          "showLabels": true,
          "sortOrder": "Descending",
          "wrapLogMessage": true,
          "prettifyLogMessage": false,
          "enableLogDetails": true
        }
      }
    ]
  },
  "overwrite": true
}
EOF

curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @/tmp/dashboard_logs.json 2>&1 | grep -q "success" && echo "✅ Dashboard Logs créé" || echo "⚠️  Erreur Logs"

echo ""
echo "✨ Configuration terminée!"
echo ""
echo "📊 Dashboards créés:"
echo "  - System Overview (CPU, RAM, Disque, Réseau)"
echo "  - Docker Containers (Métriques par container)"
echo "  - AI-Orchestrator Backend (Performance app)"
echo "  - Logs - All Services (Logs temps réel)"
echo ""
echo "🌐 Accès: https://grafana.4lb.ca"
echo "👤 User: admin"
echo "🔑 Pass: Grafana4lb2025"
