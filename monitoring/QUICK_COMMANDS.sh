#!/bin/bash
# Commandes rapides pour gérer Grafana et le monitoring

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║   Grafana & Monitoring - Quick Commands   ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "1. 🌐  Ouvrir Grafana dans le navigateur"
    echo "2. 📊  Status de la stack monitoring"
    echo "3. 🔄  Redémarrer Grafana"
    echo "4. 🔧  Reconfigurer tous les dashboards"
    echo "5. 📝  Voir logs Grafana"
    echo "6. 🔍  Vérifier métriques Prometheus"
    echo "7. 📋  Vérifier targets Prometheus"
    echo "8. 🔑  Changer mot de passe admin"
    echo "9. 💾  Backup Grafana"
    echo "10. 🚦 Tester métriques Traefik"
    echo "0. ❌  Quitter"
    echo ""
}

while true; do
    show_menu
    read -p "Choix: " choice
    
    case $choice in
        1)
            echo -e "${BLUE}Ouverture de Grafana...${NC}"
            xdg-open https://grafana.4lb.ca 2>/dev/null || open https://grafana.4lb.ca 2>/dev/null || echo "URL: https://grafana.4lb.ca"
            ;;
        2)
            echo -e "${BLUE}Status de la stack:${NC}"
            docker-compose ps
            ;;
        3)
            echo -e "${BLUE}Redémarrage Grafana...${NC}"
            docker-compose restart grafana
            sleep 5
            echo -e "${GREEN}✓ Grafana redémarré${NC}"
            ;;
        4)
            echo -e "${BLUE}Reconfiguration dashboards...${NC}"
            ./grafana/setup_grafana.sh
            ./grafana/create_http_dashboard.sh
            ;;
        5)
            echo -e "${BLUE}Logs Grafana (Ctrl+C pour quitter):${NC}"
            docker logs -f grafana
            ;;
        6)
            echo -e "${BLUE}Métriques Prometheus disponibles:${NC}"
            curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | head -20
            echo "..."
            ;;
        7)
            echo -e "${BLUE}Targets Prometheus:${NC}"
            curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"' | sort -u
            ;;
        8)
            read -p "Nouveau mot de passe: " newpass
            docker exec grafana grafana cli admin reset-admin-password "$newpass"
            echo -e "${GREEN}✓ Mot de passe changé${NC}"
            ;;
        9)
            backup_file="grafana-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
            docker-compose exec grafana tar -czf /tmp/backup.tar.gz /var/lib/grafana
            docker cp grafana:/tmp/backup.tar.gz "./$backup_file"
            echo -e "${GREEN}✓ Backup: $backup_file${NC}"
            ;;
        10)
            echo -e "${BLUE}Test métriques Traefik:${NC}"
            if curl -s http://localhost:8082/metrics | grep -q "traefik_service_requests_total"; then
                echo -e "${GREEN}✓ Traefik metrics OK${NC}"
                curl -s http://localhost:8082/metrics | grep traefik_service_requests_total | head -5
            else
                echo -e "⚠️  Traefik metrics non disponibles"
                echo "Voir: monitoring/GRAFANA_READY.md - Section 'Activer Traefik Metrics'"
            fi
            ;;
        0)
            echo "Au revoir!"
            exit 0
            ;;
        *)
            echo "❌ Choix invalide"
            ;;
    esac
    
    read -p "Appuyez sur Entrée pour continuer..."
done
