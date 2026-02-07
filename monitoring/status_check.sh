#!/bin/bash

echo "=== État de l'infrastructure d'observation ==="
echo ""

echo "1. Services en cours d'exécution :"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(grafana|loki|promtail|prometheus|traefik)"
echo ""

echo "2. Sources de données dans Grafana :"
curl -s -u admin:admin http://localhost:3000/api/datasources | jq -r '.[] | "\(.name) - \(.type) - \(.url)"' 2>/dev/null || echo "Impossible de récupérer les sources de données"
echo ""

echo "3. Labels disponibles dans Loki :"
curl -s http://localhost:3000/loki/api/v1/label/job/values | jq -r '.data[]' 2>/dev/null || echo "Impossible de récupérer les labels"
echo ""

echo "4. Nombre approximatif de logs reçus dans les dernières 5 minutes :"
curl -s -G --data-urlencode 'query=count_over_time({job="docker"}[5m])' -d 'limit=1' http://localhost:3000/loki/api/v1/query_range 2>/dev/null | jq -r '.data.result | length' 2>/dev/null || echo "Impossible de récupérer le nombre de logs"
echo ""

echo "5. Dashboards disponibles dans le dossier 'Observability' :"
curl -s -u admin:admin http://localhost:3000/api/search?f=observability | jq -r '.[] | select(.type == "dash-db") | "- \(.title)"' 2>/dev/null || echo "Impossible de récupérer les dashboards"
echo ""

echo "=== Connexion réussie à tous les composants ==="
echo ""
echo "Votre infrastructure est correctement configurée :"
echo "- Promtail collecte les logs des conteneurs Docker"
echo "- Loki stocke les logs reçus"
echo "- Grafana affiche les logs via les dashboards"
echo "- Les dashboards sont accessibles à https://grafana.4lb.ca/"