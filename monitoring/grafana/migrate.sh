#!/bin/bash
# Script simplifié pour la migration Grafana
# Usage: ./migrate.sh [dry-run|execute|export|help]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/migrate_dashboards.py"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration par défaut
export GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
export GRAFANA_USER="${GRAFANA_USER:-admin}"
export GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-ChangeMe123!}"

show_help() {
    cat << EOF
📦 Migration Grafana - AI-Orchestrator

Usage: ./migrate.sh [COMMAND]

Commands:
  dry-run    Simuler la migration (aucune modification)
  execute    Exécuter la migration
  export     Exporter tous les dashboards en backup
  help       Afficher cette aide

Exemples:
  ./migrate.sh dry-run    # Voir ce qui sera fait
  ./migrate.sh execute    # Appliquer les changements
  ./migrate.sh export     # Backup des dashboards

Configuration:
  GRAFANA_URL=$GRAFANA_URL
  GRAFANA_USER=$GRAFANA_USER
  GRAFANA_PASSWORD=****

Pour changer la configuration:
  export GRAFANA_URL="http://your-grafana:3000"
  export GRAFANA_USER="admin"
  export GRAFANA_PASSWORD="your_password"

Documentation complète: MIGRATION_GUIDE.md
EOF
}

check_dependencies() {
    # Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
        exit 1
    fi

    # Module requests
    if ! python3 -c "import requests" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Module 'requests' manquant${NC}"
        echo "Installation: pip3 install requests"
        exit 1
    fi

    echo -e "${GREEN}✓ Dépendances OK${NC}"
}

test_connection() {
    echo "🔌 Test de connexion à Grafana..."

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/health")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ Connexion Grafana OK${NC}"
    else
        echo -e "${RED}❌ Connexion Grafana échouée (HTTP $response)${NC}"
        echo "Vérifiez: URL, username, password"
        exit 1
    fi
}

main() {
    command=${1:-help}

    case "$command" in
        dry-run)
            echo "🔍 Migration en mode DRY-RUN (simulation)"
            echo "Aucune modification ne sera appliquée"
            echo ""
            check_dependencies
            test_connection
            echo ""
            python3 "$PYTHON_SCRIPT" --dry-run
            echo ""
            echo -e "${YELLOW}⚠️  Mode simulation - Aucune modification appliquée${NC}"
            echo "Pour appliquer: ./migrate.sh execute"
            ;;

        execute)
            echo "🚀 Migration en mode EXECUTION"
            echo "Les modifications seront appliquées!"
            echo ""

            # Confirmation
            read -p "Continuer? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Migration annulée"
                exit 0
            fi

            check_dependencies
            test_connection

            # Backup automatique avant migration
            echo ""
            echo "📦 Backup automatique avant migration..."
            python3 "$PYTHON_SCRIPT" --export
            echo ""

            # Migration
            python3 "$PYTHON_SCRIPT" --execute
            echo ""
            echo -e "${GREEN}✅ Migration terminée!${NC}"
            echo "Vérifiez: $GRAFANA_URL/dashboards"
            ;;

        export)
            echo "📦 Export des dashboards"
            echo ""
            check_dependencies
            test_connection
            echo ""
            python3 "$PYTHON_SCRIPT" --export
            echo ""
            echo -e "${GREEN}✓ Export terminé${NC}"
            echo "Backups dans: backups/dashboards/"
            ;;

        help|--help|-h)
            show_help
            ;;

        *)
            echo -e "${RED}Commande inconnue: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
