#!/bin/bash

# Script de configuration pour ajouter Loki comme source de données dans Grafana
# Ce script peut être exécuté après le démarrage de Grafana pour s'assurer que Loki est correctement configuré

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="Gr@fana4lb2025!!"

echo "Configuration de Loki comme source de données dans Grafana..."

# Vérifier si Grafana est accessible
if ! curl -s -o /dev/null -w "%{http_code}" $GRAFANA_URL/api/health | grep -q "200"; then
    echo "Erreur : Grafana n'est pas accessible à $GRAFANA_URL"
    exit 1
fi

# Vérifier si la source de données Loki existe déjà
if curl -s -u $GRAFANA_USER:$GRAFANA_PASS "$GRAFANA_URL/api/datasources/name/Loki" | grep -q "Loki"; then
    echo "La source de données Loki existe déjà"
else
    # Créer la source de données Loki
    curl -X "POST" "$GRAFANA_URL/api/datasources" \
         -H 'Content-Type: application/json' \
         -u $GRAFANA_USER:$GRAFANA_PASS \
         -d '{
           "name": "Loki",
           "type": "loki",
           "access": "proxy",
           "url": "http://loki:3100",
           "jsonData": {
             "maxLines": 1000
           }
         }'
    
    if [ $? -eq 0 ]; then
        echo "Source de données Loki ajoutée avec succès"
    else
        echo "Erreur lors de l'ajout de la source de données Loki"
    fi
fi

# Vérifier si la source de données Loki-Traefik existe déjà
if curl -s -u $GRAFANA_USER:$GRAFANA_PASS "$GRAFANA_URL/api/datasources/name/Loki-Traefik" | grep -q "Loki-Traefik"; then
    echo "La source de données Loki-Traefik existe déjà"
else
    # Créer la source de données Loki-Traefik
    curl -X "POST" "$GRAFANA_URL/api/datasources" \
         -H 'Content-Type: application/json' \
         -u $GRAFANA_USER:$GRAFANA_PASS \
         -d '{
           "name": "Loki-Traefik",
           "type": "loki",
           "access": "proxy",
           "url": "http://loki:3100",
           "jsonData": {
             "maxLines": 5000
           }
         }'
    
    if [ $? -eq 0 ]; then
        echo "Source de données Loki-Traefik ajoutée avec succès"
    else
        echo "Erreur lors de l'ajout de la source de données Loki-Traefik"
    fi
fi

echo "Configuration terminée."