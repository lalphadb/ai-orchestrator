#!/bin/bash
# Script de démarrage nginx avec substitution de variables d'environnement
# AI Orchestrator v7.0

set -e

# Valeurs par défaut
export BACKEND_HOST="${BACKEND_HOST:-10.10.10.46}"
export BACKEND_PORT="${BACKEND_PORT:-8001}"

echo "🔧 Configuration nginx:"
echo "   BACKEND_HOST = $BACKEND_HOST"
echo "   BACKEND_PORT = $BACKEND_PORT"

# Créer le fichier nginx.conf avec les variables substituées
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' < nginx.conf > /tmp/nginx.conf.rendered

echo "✅ nginx.conf généré avec les variables d'environnement"

# Tester la configuration
nginx -t -c /tmp/nginx.conf.rendered

# Démarrer nginx
echo "🚀 Démarrage nginx..."
nginx -c /tmp/nginx.conf.rendered -g 'daemon off;'
