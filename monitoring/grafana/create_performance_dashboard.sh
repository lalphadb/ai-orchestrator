#!/bin/bash

# Configuration
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Grafana4lb2025"

echo "🎨 Creating AI-Orchestrator Performance Dashboard..."

# Create dashboard JSON
cat > /tmp/dashboard_ai_performance.json <<'DASHBOARD_EOF'
{
  "dashboard": {
    "title": "🤖 AI-Orchestrator - Performance Détaillée",
    "tags": ["ai-orchestrator", "performance", "llm", "tools", "workflow"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "type": "timeseries",
        "title": "Tool Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(tool_execution_duration_seconds_bucket[5m])) by (tool_name, le))",
            "legendFormat": "{{tool_name}} (p95)",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "color": {"mode": "palette-classic"},
            "custom": {
              "axisLabel": "Duration (seconds)",
              "drawStyle": "line",
              "fillOpacity": 10,
              "showPoints": "auto"
            }
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "calcs": ["lastNotNull", "max"]
          },
          "tooltip": {"mode": "multi"}
        }
      },
      {
        "id": 2,
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "type": "timeseries",
        "title": "Tool Errors Rate",
        "targets": [
          {
            "expr": "sum(rate(tool_errors_total[5m])) by (error_code)",
            "legendFormat": "{{error_code}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "color": {"mode": "palette-classic"},
            "custom": {
              "axisLabel": "Errors/sec",
              "drawStyle": "line",
              "fillOpacity": 10
            }
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "calcs": ["lastNotNull", "sum"]
          },
          "tooltip": {"mode": "multi"}
        }
      },
      {
        "id": 3,
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8},
        "type": "stat",
        "title": "LLM Calls/sec",
        "targets": [
          {
            "expr": "sum(rate(llm_calls_total[1m]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "color": {"mode": "thresholds"},
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": null, "color": "green"},
                {"value": 5, "color": "yellow"},
                {"value": 10, "color": "red"}
              ]
            }
          }
        },
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "textMode": "auto"
        }
      },
      {
        "id": 4,
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 8},
        "type": "piechart",
        "title": "LLM Tokens (Prompt vs Completion)",
        "targets": [
          {
            "expr": "sum(rate(llm_tokens_total[1h])) by (type)",
            "legendFormat": "{{type}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "values": ["value", "percent"]
          },
          "pieType": "pie",
          "displayLabels": ["percent"]
        }
      },
      {
        "id": 5,
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 8},
        "type": "bargauge",
        "title": "Workflow Phases Duration (avg)",
        "targets": [
          {
            "expr": "avg(rate(workflow_phase_duration_seconds_sum[5m]) / rate(workflow_phase_duration_seconds_count[5m])) by (phase)",
            "legendFormat": "{{phase}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "color": {"mode": "continuous-GrYlRd"},
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": null, "color": "green"},
                {"value": 5, "color": "yellow"},
                {"value": 10, "color": "orange"},
                {"value": 20, "color": "red"}
              ]
            }
          }
        },
        "options": {
          "orientation": "horizontal",
          "displayMode": "gradient",
          "showUnfilled": true
        }
      },
      {
        "id": 6,
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 14},
        "type": "timeseries",
        "title": "LLM Calls by Model",
        "targets": [
          {
            "expr": "sum(rate(llm_calls_total[5m])) by (model, success)",
            "legendFormat": "{{model}} ({{success}})",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "color": {"mode": "palette-classic"},
            "custom": {
              "axisLabel": "Calls/sec",
              "drawStyle": "line",
              "fillOpacity": 10
            }
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "calcs": ["lastNotNull", "mean"]
          },
          "tooltip": {"mode": "multi"}
        }
      },
      {
        "id": 7,
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 14},
        "type": "timeseries",
        "title": "LLM Token Consumption",
        "targets": [
          {
            "expr": "sum(rate(llm_tokens_total[1h])) by (model, type)",
            "legendFormat": "{{model}} - {{type}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "color": {"mode": "palette-classic"},
            "custom": {
              "axisLabel": "Tokens/hour",
              "drawStyle": "line",
              "fillOpacity": 10,
              "lineWidth": 2
            }
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "calcs": ["lastNotNull", "sum"]
          },
          "tooltip": {"mode": "multi"}
        }
      },
      {
        "id": 8,
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 22},
        "type": "table",
        "title": "Tool Execution Summary",
        "targets": [
          {
            "expr": "sum(rate(tool_execution_duration_seconds_count[5m])) by (tool_name, success)",
            "legendFormat": "",
            "refId": "A",
            "format": "table",
            "instant": true
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "align": "auto",
              "displayMode": "auto"
            }
          },
          "overrides": [
            {
              "matcher": {"id": "byName", "options": "Value"},
              "properties": [
                {"id": "unit", "value": "reqps"},
                {"id": "custom.displayMode", "value": "color-background"}
              ]
            }
          ]
        },
        "options": {
          "showHeader": true,
          "sortBy": [{"displayName": "Value", "desc": true}]
        },
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "renameByName": {
                "tool_name": "Tool",
                "success": "Success",
                "Value": "Exec/sec"
              }
            }
          }
        ]
      }
    ]
  },
  "folderId": 0,
  "overwrite": false
}
DASHBOARD_EOF

# Import dashboard
echo "📊 Importing dashboard..."
response=$(curl -s -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -d @/tmp/dashboard_ai_performance.json)

# Check response
if echo "$response" | grep -q '"status":"success"'; then
  echo "✅ Dashboard created successfully!"
  dashboard_url=$(echo "$response" | jq -r '.url')
  echo "🔗 Dashboard URL: ${GRAFANA_URL}${dashboard_url}"
else
  echo "❌ Failed to create dashboard"
  echo "Response: $response"
  exit 1
fi

# Cleanup
rm -f /tmp/dashboard_ai_performance.json

echo ""
echo "🎉 Dashboard Setup Complete!"
echo ""
echo "📊 Dashboard includes:"
echo "  1. Tool Latency (p95) - Timeseries"
echo "  2. Tool Errors Rate - Timeseries"
echo "  3. LLM Calls/sec - Stat panel"
echo "  4. LLM Tokens Distribution - Pie chart"
echo "  5. Workflow Phases Duration - Bar gauge"
echo "  6. LLM Calls by Model - Timeseries"
echo "  7. LLM Token Consumption - Timeseries"
echo "  8. Tool Execution Summary - Table"
echo ""
echo "🔍 Access: https://grafana.4lb.ca"
echo "🔑 Credentials: admin / Grafana4lb2025"
