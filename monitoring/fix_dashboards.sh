#!/bin/bash
# Fix automatique des dashboards Grafana
# Démarre la stack et applique les corrections

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "════════════════════════════════════════════════════════════"
echo "  🔧 FIX DASHBOARDS GRAFANA"
echo "════════════════════════════════════════════════════════════"
echo ""

# ============================================
# 1. DÉMARRER LA STACK
# ============================================
echo -e "${BLUE}📦 Étape 1: Démarrage de la stack monitoring${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    cd "$SCRIPT_DIR"

    echo "Démarrage des services..."
    docker-compose up -d

    echo -e "${GREEN}✓${NC} Services démarrés"

    echo "Attente du démarrage complet (30 secondes)..."
    sleep 30

    # Vérifier services
    echo ""
    echo "Vérification des services:"

    services=("prometheus" "loki" "promtail" "grafana")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service"; then
            echo -e "  ${GREEN}✓${NC} $service"
        else
            echo -e "  ${RED}✗${NC} $service (non démarré)"
        fi
    done
else
    echo -e "${RED}✗${NC} docker-compose.yml non trouvé"
    echo "Exécutez ce script depuis le dossier monitoring/"
    exit 1
fi

echo ""

# ============================================
# 2. CONFIGURER PROMETHEUS
# ============================================
echo -e "${BLUE}📈 Étape 2: Configuration Prometheus${NC}"
echo "────────────────────────────────────────────────────────────"

PROM_CONFIG="$SCRIPT_DIR/prometheus/prometheus.yml"

if [ -f "$PROM_CONFIG" ]; then
    # Vérifier si backend déjà configuré
    if ! grep -q "ai-orchestrator-backend" "$PROM_CONFIG"; then
        echo "Ajout du backend AI-Orchestrator dans Prometheus..."

        # Backup
        cp "$PROM_CONFIG" "$PROM_CONFIG.backup"

        # Ajouter config backend (à la fin du fichier)
        cat >> "$PROM_CONFIG" << 'EOF'

  # AI-Orchestrator Backend (ajouté automatiquement)
  - job_name: 'ai-orchestrator-backend'
    static_configs:
      - targets: ['192.168.200.1:8001']
    metrics_path: '/metrics'
    scrape_interval: 15s
EOF

        echo -e "${GREEN}✓${NC} Backend ajouté à Prometheus"

        # Redémarrer Prometheus
        docker-compose restart prometheus
        sleep 10
    else
        echo -e "${GREEN}✓${NC} Backend déjà configuré dans Prometheus"
    fi
else
    echo -e "${YELLOW}⚠${NC} Fichier prometheus.yml non trouvé"
fi

echo ""

# ============================================
# 3. INSTALLER GPU EXPORTER (SI GPU DÉTECTÉ)
# ============================================
echo -e "${BLUE}🖥️  Étape 3: Configuration GPU Exporter${NC}"
echo "────────────────────────────────────────────────────────────"

if command -v nvidia-smi &>/dev/null; then
    echo "GPU NVIDIA détecté"

    # Vérifier si exporter déjà installé
    if docker ps | grep -q nvidia-gpu-exporter; then
        echo -e "${GREEN}✓${NC} GPU exporter déjà installé"
    else
        echo "Installation du GPU exporter..."

        docker run -d \
          --name nvidia-gpu-exporter \
          --gpus all \
          --restart unless-stopped \
          -p 9835:9835 \
          mindprince/nvidia_gpu_prometheus_exporter:latest

        echo -e "${GREEN}✓${NC} GPU exporter installé"

        # Ajouter à Prometheus
        if ! grep -q "nvidia-gpu" "$PROM_CONFIG"; then
            cat >> "$PROM_CONFIG" << 'EOF'

  # NVIDIA GPU Exporter (ajouté automatiquement)
  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['192.168.200.1:9835']
    scrape_interval: 15s
EOF

            echo -e "${GREEN}✓${NC} GPU ajouté à Prometheus"
            docker-compose restart prometheus
            sleep 10
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} Aucun GPU NVIDIA détecté (nvidia-smi non trouvé)"
fi

echo ""

# ============================================
# 4. VÉRIFIER TRAEFIK METRICS
# ============================================
echo -e "${BLUE}🚦 Étape 4: Vérification Traefik Metrics${NC}"
echo "────────────────────────────────────────────────────────────"

if curl -s http://localhost:8082/metrics &>/dev/null; then
    echo -e "${GREEN}✓${NC} Traefik metrics accessibles (http://localhost:8082/metrics)"
else
    echo -e "${YELLOW}⚠${NC} Traefik metrics non accessibles"
    echo ""
    echo "Action requise:"
    echo "1. Vérifier que Traefik expose le port 8082"
    echo "2. Activer métriques dans traefik.yml:"
    echo ""
    echo "metrics:"
    echo "  prometheus:"
    echo "    entryPoint: metrics"
    echo ""
    echo "entryPoints:"
    echo "  metrics:"
    echo "    address: \":8082\""
    echo ""
    echo "3. Redémarrer Traefik: docker restart traefik"
fi

echo ""

# ============================================
# 5. VÉRIFIER DATASOURCES GRAFANA
# ============================================
echo -e "${BLUE}📊 Étape 5: Vérification Datasources Grafana${NC}"
echo "────────────────────────────────────────────────────────────"

# Attendre que Grafana soit prêt
sleep 10

if curl -s http://localhost:3000/api/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} Grafana accessible"

    # Vérifier datasources
    datasources=$(curl -s -u admin:ChangeMe123! http://localhost:3000/api/datasources 2>/dev/null)

    if echo "$datasources" | jq -e '. | length > 0' &>/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Datasources configurés:"
        echo "$datasources" | jq -r '.[] | "  - \(.name) (\(.type))"' 2>/dev/null || echo "  - Erreur lecture datasources"
    else
        echo -e "${YELLOW}⚠${NC} Aucun datasource configuré"
        echo ""
        echo "Configuration manuelle requise:"
        echo "1. Ouvrir Grafana: https://grafana.4lb.ca"
        echo "2. Configuration → Data Sources → Add data source"
        echo "3. Ajouter Prometheus (URL: http://prometheus:9090)"
        echo "4. Ajouter Loki (URL: http://loki:3100)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Grafana non accessible (localhost:3000)"
    echo "Vérifiez que Grafana est démarré et attend quelques secondes"
fi

echo ""

# ============================================
# 6. RÉSUMÉ
# ============================================
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}📋 RÉSUMÉ${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Services démarrés:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}"

echo ""
echo "Tests de connectivité:"

# Prometheus
if curl -s http://localhost:9090/-/healthy &>/dev/null; then
    echo -e "${GREEN}✓${NC} Prometheus: http://localhost:9090"
else
    echo -e "${RED}✗${NC} Prometheus: Non accessible"
fi

# Loki
if curl -s http://localhost:3100/ready &>/dev/null; then
    echo -e "${GREEN}✓${NC} Loki: http://localhost:3100"
else
    echo -e "${RED}✗${NC} Loki: Non accessible"
fi

# Grafana
if curl -s http://localhost:3000/api/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} Grafana: http://localhost:3000"
else
    echo -e "${RED}✗${NC} Grafana: Non accessible"
fi

# Traefik metrics
if curl -s http://localhost:8082/metrics &>/dev/null; then
    echo -e "${GREEN}✓${NC} Traefik Metrics: http://localhost:8082/metrics"
else
    echo -e "${YELLOW}⚠${NC} Traefik Metrics: Non accessible (config manuelle requise)"
fi

# Backend
if curl -s http://localhost:8001/metrics &>/dev/null; then
    echo -e "${GREEN}✓${NC} Backend AI: http://localhost:8001/metrics"
else
    echo -e "${RED}✗${NC} Backend AI: Non accessible"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

echo "🎯 Prochaines étapes:"
echo ""
echo "1. Ouvrir Grafana: https://grafana.4lb.ca (ou http://localhost:3000)"
echo "2. Vérifier les datasources: Configuration → Data Sources"
echo "3. Tester les dashboards"
echo "4. Si 'No data' persiste:"
echo "   - Vérifier les queries dans les panels"
echo "   - Attendre 1-2 minutes que les métriques arrivent"
echo "   - Consulter: monitoring/grafana/FIX_DASHBOARDS.md"
echo ""

echo "Pour un diagnostic complet:"
echo "  $ cd monitoring/grafana && ./diagnose.sh"
echo ""

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Fix terminé!${NC}"
echo "════════════════════════════════════════════════════════════"
