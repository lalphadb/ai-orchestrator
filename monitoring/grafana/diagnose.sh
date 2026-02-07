#!/bin/bash
# Script de diagnostic Grafana - Identifier pourquoi les dashboards affichent "No data"
# Usage: ./diagnose.sh

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "════════════════════════════════════════════════════════════"
echo "  🔍 DIAGNOSTIC GRAFANA - Dashboards 'No data'"
echo "════════════════════════════════════════════════════════════"
echo ""

# ============================================
# 1. DATASOURCES GRAFANA
# ============================================
echo -e "${BLUE}📊 1. Vérification des Datasources Grafana${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:3000/api/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} Grafana accessible"

    # Lister datasources
    datasources=$(curl -s -u admin:ChangeMe123! http://localhost:3000/api/datasources 2>/dev/null)

    if echo "$datasources" | jq -e '. | length > 0' &>/dev/null; then
        echo -e "${GREEN}✓${NC} Datasources configurés:"
        echo "$datasources" | jq -r '.[] | "  - \(.name) (\(.type)) - \(.url)"'

        # Tester chaque datasource
        echo ""
        echo "Test des datasources:"
        echo "$datasources" | jq -r '.[].uid' | while read uid; do
            result=$(curl -s -u admin:ChangeMe123! "http://localhost:3000/api/datasources/uid/$uid" | jq -r '.name')
            echo "  - Testing $result..."
        done
    else
        echo -e "${RED}✗${NC} Aucun datasource configuré!"
        echo "  Solution: Configurer Prometheus et Loki dans Grafana"
    fi
else
    echo -e "${RED}✗${NC} Grafana non accessible"
fi

echo ""

# ============================================
# 2. PROMETHEUS
# ============================================
echo -e "${BLUE}📈 2. Vérification Prometheus${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:9090/-/healthy &>/dev/null; then
    echo -e "${GREEN}✓${NC} Prometheus accessible (http://localhost:9090)"

    # Targets
    targets=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | jq -r '.data.activeTargets[] | "\(.job) - \(.health)"')

    if [ -n "$targets" ]; then
        echo -e "${GREEN}✓${NC} Targets Prometheus:"
        echo "$targets" | while read line; do
            job=$(echo "$line" | cut -d' ' -f1)
            health=$(echo "$line" | cut -d' ' -f3)

            if [ "$health" = "up" ]; then
                echo -e "  ${GREEN}✓${NC} $job"
            else
                echo -e "  ${RED}✗${NC} $job (DOWN)"
            fi
        done
    else
        echo -e "${YELLOW}⚠${NC} Aucun target configuré"
    fi

    # Test query
    echo ""
    echo "Test de requête Prometheus:"
    metrics=$(curl -s "http://localhost:9090/api/v1/query?query=up" | jq -r '.data.result | length')
    if [ "$metrics" -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Métriques disponibles ($metrics targets)"
    else
        echo -e "  ${RED}✗${NC} Aucune métrique disponible"
    fi

else
    echo -e "${RED}✗${NC} Prometheus non accessible"
    echo "  Solution: Démarrer Prometheus (docker-compose up -d prometheus)"
fi

echo ""

# ============================================
# 3. LOKI
# ============================================
echo -e "${BLUE}📝 3. Vérification Loki${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:3100/ready &>/dev/null; then
    echo -e "${GREEN}✓${NC} Loki accessible (http://localhost:3100)"

    # Labels disponibles
    labels=$(curl -s "http://localhost:3100/loki/api/v1/labels" 2>/dev/null | jq -r '.data[]' 2>/dev/null)

    if [ -n "$labels" ]; then
        echo -e "${GREEN}✓${NC} Labels disponibles:"
        echo "$labels" | head -10 | while read label; do
            echo "  - $label"
        done
    else
        echo -e "${YELLOW}⚠${NC} Aucun label trouvé (logs non ingérés)"
    fi

else
    echo -e "${RED}✗${NC} Loki non accessible"
    echo "  Solution: Démarrer Loki (docker-compose up -d loki)"
fi

echo ""

# ============================================
# 4. PROMTAIL
# ============================================
echo -e "${BLUE}📦 4. Vérification Promtail${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:9080/ready &>/dev/null; then
    echo -e "${GREEN}✓${NC} Promtail accessible (http://localhost:9080)"

    # Métriques Promtail
    sent=$(curl -s http://localhost:9080/metrics 2>/dev/null | grep promtail_sent_entries_total | tail -1)

    if [ -n "$sent" ]; then
        echo -e "${GREEN}✓${NC} Promtail envoie des logs:"
        echo "  $sent"
    else
        echo -e "${YELLOW}⚠${NC} Aucune métrique d'envoi trouvée"
    fi

else
    echo -e "${RED}✗${NC} Promtail non accessible"
    echo "  Solution: Démarrer Promtail (docker-compose up -d promtail)"
fi

echo ""

# ============================================
# 5. TRAEFIK METRICS
# ============================================
echo -e "${BLUE}🚦 5. Vérification Traefik Metrics${NC}"
echo "────────────────────────────────────────────────────────────"

if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓${NC} Traefik est démarré"

    # Vérifier métriques Traefik
    if curl -s http://localhost:8082/metrics &>/dev/null; then
        echo -e "${GREEN}✓${NC} Métriques Traefik exposées (http://localhost:8082/metrics)"

        # Compter métriques
        metric_count=$(curl -s http://localhost:8082/metrics | grep -c "^traefik_" || echo 0)
        echo "  - $metric_count métriques Traefik disponibles"
    else
        echo -e "${RED}✗${NC} Métriques Traefik non accessibles"
        echo "  Solution: Activer métriques dans traefik.yml"
    fi
else
    echo -e "${RED}✗${NC} Traefik non démarré"
fi

echo ""

# ============================================
# 6. AI-ORCHESTRATOR BACKEND
# ============================================
echo -e "${BLUE}🤖 6. Vérification AI-Orchestrator Backend${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:8001/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} Backend accessible (http://localhost:8001)"

    # Vérifier /metrics
    if curl -s http://localhost:8001/metrics &>/dev/null; then
        echo -e "${GREEN}✓${NC} Endpoint /metrics disponible"

        metric_count=$(curl -s http://localhost:8001/metrics | grep -c "^# HELP" || echo 0)
        echo "  - $metric_count métriques exposées"
    else
        echo -e "${RED}✗${NC} Endpoint /metrics non disponible"
        echo "  Solution: Vérifier que FastAPI expose les métriques"
    fi
else
    echo -e "${RED}✗${NC} Backend non accessible"
    echo "  Solution: Démarrer le backend (systemctl start ai-orchestrator)"
fi

echo ""

# ============================================
# 7. GPU METRICS (NVIDIA)
# ============================================
echo -e "${BLUE}🖥️  7. Vérification GPU Metrics${NC}"
echo "────────────────────────────────────────────────────────────"

if command -v nvidia-smi &>/dev/null; then
    echo -e "${GREEN}✓${NC} nvidia-smi disponible"

    # Vérifier si nvidia_gpu_exporter est installé
    if command -v nvidia_gpu_prometheus_exporter &>/dev/null; then
        echo -e "${GREEN}✓${NC} nvidia_gpu_prometheus_exporter installé"
    elif curl -s http://localhost:9835/metrics &>/dev/null; then
        echo -e "${GREEN}✓${NC} nvidia_gpu_prometheus_exporter actif (http://localhost:9835)"
    else
        echo -e "${YELLOW}⚠${NC} nvidia_gpu_prometheus_exporter non trouvé"
        echo "  Solution: Installer nvidia_gpu_prometheus_exporter"
        echo "  $ docker run -d --gpus all -p 9835:9835 mindprince/nvidia_gpu_prometheus_exporter:latest"
    fi
else
    echo -e "${RED}✗${NC} nvidia-smi non trouvé (GPU non détecté)"
fi

echo ""

# ============================================
# 8. CHROMADB
# ============================================
echo -e "${BLUE}🧠 8. Vérification ChromaDB${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:8000/api/v1/heartbeat &>/dev/null; then
    echo -e "${GREEN}✓${NC} ChromaDB accessible (http://localhost:8000)"
else
    echo -e "${YELLOW}⚠${NC} ChromaDB non accessible"
    echo "  Note: ChromaDB n'expose pas de métriques Prometheus par défaut"
fi

echo ""

# ============================================
# 9. RÉSUMÉ ET RECOMMANDATIONS
# ============================================
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}📋 RÉSUMÉ${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Problèmes identifiés:"
echo ""

# Compter les problèmes
problems=0

if ! curl -s http://localhost:9090/-/healthy &>/dev/null; then
    echo -e "${RED}✗${NC} Prometheus non accessible"
    problems=$((problems + 1))
fi

if ! curl -s http://localhost:3100/ready &>/dev/null; then
    echo -e "${RED}✗${NC} Loki non accessible"
    problems=$((problems + 1))
fi

if ! curl -s http://localhost:8082/metrics &>/dev/null; then
    echo -e "${RED}✗${NC} Traefik metrics non exposées"
    problems=$((problems + 1))
fi

if ! curl -s http://localhost:8001/metrics &>/dev/null; then
    echo -e "${RED}✗${NC} Backend metrics non disponibles"
    problems=$((problems + 1))
fi

if ! curl -s http://localhost:9835/metrics &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} GPU exporter non trouvé"
    problems=$((problems + 1))
fi

echo ""

if [ $problems -eq 0 ]; then
    echo -e "${GREEN}✅ Aucun problème majeur détecté!${NC}"
    echo "Si des dashboards affichent 'No data', vérifiez les requêtes dans les panels."
else
    echo -e "${YELLOW}⚠️ $problems problème(s) détecté(s)${NC}"
    echo ""
    echo "Solutions:"
    echo "1. Démarrer la stack monitoring: cd monitoring && docker-compose up -d"
    echo "2. Configurer datasources dans Grafana"
    echo "3. Vérifier que Traefik expose les métriques (port 8082)"
    echo "4. Installer GPU exporter si nécessaire"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Pour plus de détails, consultez monitoring/grafana/FIX_DASHBOARDS.md"
echo "════════════════════════════════════════════════════════════"
