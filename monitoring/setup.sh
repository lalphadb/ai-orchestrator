#!/bin/bash
# Setup script pour stack observabilité AI-Orchestrator
# Usage: ./setup.sh [start|stop|restart|logs|validate]

set -e

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_RESET='\033[0m'

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

# ============================================
# PRÉREQUIS
# ============================================
check_prerequisites() {
    log_info "Vérification des prérequis..."

    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi

    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi

    # Réseau web
    if ! docker network inspect web &> /dev/null; then
        log_warn "Réseau 'web' n'existe pas, création..."
        docker network create web
    fi

    # Réseau monitoring
    if ! docker network inspect monitoring &> /dev/null; then
        log_warn "Réseau 'monitoring' n'existe pas, création..."
        docker network create monitoring
    fi

    log_info "Prérequis OK"
}

# ============================================
# STRUCTURE DE RÉPERTOIRES
# ============================================
create_directories() {
    log_info "Création de la structure de répertoires..."

    mkdir -p traefik/{dynamic,logs}
    mkdir -p prometheus/alerts
    mkdir -p loki
    mkdir -p promtail
    mkdir -p grafana/{provisioning/datasources,provisioning/dashboards,dashboards}

    # Permissions
    chmod 755 traefik/logs
    chmod 600 letsencrypt/acme.json 2>/dev/null || touch letsencrypt/acme.json && chmod 600 letsencrypt/acme.json

    log_info "Répertoires créés"
}

# ============================================
# DÉMARRAGE
# ============================================
start_stack() {
    log_info "Démarrage de la stack observabilité..."

    check_prerequisites
    create_directories

    # Pull images
    log_info "Pull des images Docker..."
    docker-compose pull

    # Démarrage
    log_info "Démarrage des services..."
    docker-compose up -d

    # Attendre que les services soient prêts
    log_info "Attente du démarrage des services (30s)..."
    sleep 30

    # Vérification
    validate_stack

    log_info "Stack démarrée avec succès!"
    log_info ""
    log_info "Accès:"
    log_info "  - Grafana:    https://grafana.4lb.ca (admin / ChangeMe123!)"
    log_info "  - Prometheus: https://prometheus.4lb.ca"
    log_info "  - Traefik:    https://traefik.4lb.ca"
    log_info ""
    log_info "Localement:"
    log_info "  - Grafana:    http://localhost:3000"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Loki:       http://localhost:3100"
    log_info "  - Promtail:   http://localhost:9080"
}

# ============================================
# ARRÊT
# ============================================
stop_stack() {
    log_info "Arrêt de la stack observabilité..."
    docker-compose down
    log_info "Stack arrêtée"
}

# ============================================
# REDÉMARRAGE
# ============================================
restart_stack() {
    stop_stack
    sleep 5
    start_stack
}

# ============================================
# LOGS
# ============================================
show_logs() {
    service=${1:-}
    if [ -z "$service" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 "$service"
    fi
}

# ============================================
# VALIDATION
# ============================================
validate_stack() {
    log_info "Validation de la stack..."

    # Grafana
    if curl -s http://localhost:3000/api/health | grep -q "ok"; then
        log_info "✓ Grafana OK"
    else
        log_error "✗ Grafana KO"
    fi

    # Prometheus
    if curl -s http://localhost:9090/-/healthy | grep -q "Healthy"; then
        log_info "✓ Prometheus OK"
    else
        log_error "✗ Prometheus KO"
    fi

    # Loki
    if curl -s http://localhost:3100/ready | grep -q "ready"; then
        log_info "✓ Loki OK"
    else
        log_error "✗ Loki KO"
    fi

    # Promtail
    if curl -s http://localhost:9080/ready | grep -q "ready"; then
        log_info "✓ Promtail OK"
    else
        log_error "✗ Promtail KO"
    fi

    # Traefik
    if docker ps | grep -q traefik; then
        log_info "✓ Traefik OK"
    else
        log_error "✗ Traefik KO"
    fi

    log_info ""
    log_info "Validation terminée"
}

# ============================================
# TESTS
# ============================================
run_tests() {
    log_info "Exécution des tests..."

    # Test 1: Générer du trafic
    log_info "Test 1: Génération de trafic HTTP..."
    for i in {1..50}; do
        curl -s https://ai.4lb.ca/api/v1/system/health > /dev/null || true
        curl -s https://ai.4lb.ca/api/does-not-exist > /dev/null 2>&1 || true
    done

    sleep 10

    # Test 2: Vérifier logs dans Loki
    log_info "Test 2: Vérification des logs Loki..."
    result=$(curl -G -s "http://localhost:3100/loki/api/v1/query" \
        --data-urlencode 'query={job="traefik"}' \
        --data-urlencode 'limit=1')

    if echo "$result" | grep -q '"result"'; then
        log_info "✓ Logs Traefik présents dans Loki"
    else
        log_error "✗ Aucun log Traefik dans Loki"
    fi

    # Test 3: Vérifier métriques Prometheus
    log_info "Test 3: Vérification des métriques Prometheus..."
    result=$(curl -s "http://localhost:9090/api/v1/query?query=up")

    if echo "$result" | grep -q '"resultType"'; then
        log_info "✓ Métriques présentes dans Prometheus"
    else
        log_error "✗ Aucune métrique dans Prometheus"
    fi

    log_info "Tests terminés"
}

# ============================================
# BACKUP
# ============================================
backup_dashboards() {
    log_info "Backup des dashboards Grafana..."

    mkdir -p backups/dashboards-$(date +%Y%m%d)

    # Export via API
    curl -s http://localhost:3000/api/search | jq -r '.[] | .uid' | while read uid; do
        curl -s "http://localhost:3000/api/dashboards/uid/$uid" \
            -u admin:ChangeMe123! \
            > "backups/dashboards-$(date +%Y%m%d)/$uid.json"
        log_info "  - Dashboard $uid sauvegardé"
    done

    log_info "Backup terminé: backups/dashboards-$(date +%Y%m%d)/"
}

# ============================================
# MENU PRINCIPAL
# ============================================
case "${1:-}" in
    start)
        start_stack
        ;;
    stop)
        stop_stack
        ;;
    restart)
        restart_stack
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    validate)
        validate_stack
        ;;
    test)
        run_tests
        ;;
    backup)
        backup_dashboards
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs [service]|validate|test|backup}"
        echo ""
        echo "Exemples:"
        echo "  $0 start              - Démarrer la stack"
        echo "  $0 stop               - Arrêter la stack"
        echo "  $0 restart            - Redémarrer la stack"
        echo "  $0 logs               - Afficher tous les logs"
        echo "  $0 logs grafana       - Afficher logs Grafana uniquement"
        echo "  $0 validate           - Valider que tout fonctionne"
        echo "  $0 test               - Exécuter les tests"
        echo "  $0 backup             - Backup dashboards Grafana"
        exit 1
        ;;
esac
