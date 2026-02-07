#!/bin/bash
# AI Orchestrator Doctor Script
# Détecte les problèmes de configuration courants qui causent des bugs

# Note: Ne pas utiliser 'set -e' car on veut continuer même si certains checks échouent
set -u

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🏥 AI Orchestrator Health Check"
echo "================================"
echo ""

# Function pour afficher les résultats
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

# 1. Vérifier qu'on n'utilise pas l'ancien docker-compose
echo "📦 Checking Docker configuration..."
if docker ps 2>/dev/null | grep -q "ai-orchestrator-backend"; then
    check_fail "OLD docker-compose détecté! Le backend NE DOIT PAS tourner dans Docker."
    echo "   → Arrêtez avec: docker-compose down"
    echo "   → Utilisez systemd pour le backend (voir README-OBSOLETE-DOCKER-COMPOSE.md)"
elif docker ps 2>/dev/null | grep -q "orchestrator"; then
    check_warn "Conteneurs 'orchestrator' détectés. Vérifiez que c'est bien unified-stack."
else
    check_ok "Pas d'ancien docker-compose détecté"
fi
echo ""

# 2. Vérifier les ports critiques
echo "🔌 Checking critical ports..."
PORTS_TO_CHECK=(8001 3000 8080 11434)
PORT_NAMES=("Backend API" "Frontend Dev" "Traefik (si prod)" "Ollama")

for i in "${!PORTS_TO_CHECK[@]}"; do
    PORT="${PORTS_TO_CHECK[$i]}"
    NAME="${PORT_NAMES[$i]}"

    # Essayer lsof d'abord, puis ss en fallback
    PORT_IN_USE=false
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORT_IN_USE=true
    elif ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        PORT_IN_USE=true
    fi

    if [ "$PORT_IN_USE" = true ]; then
        check_ok "Port $PORT ($NAME) is in use"
    else
        if [ "$PORT" = "8001" ]; then
            check_fail "Port $PORT ($NAME) is FREE - backend not running!"
        elif [ "$PORT" = "11434" ]; then
            check_fail "Port $PORT ($NAME) is FREE - Ollama not running!"
        else
            check_warn "Port $PORT ($NAME) is free"
        fi
    fi
done
echo ""

# 3. Vérifier les services essentiels
echo "🔧 Checking essential services..."

# Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    check_ok "Ollama API accessible"
else
    check_fail "Ollama API NOT accessible on http://localhost:11434"
    echo "   → Start with: systemctl start ollama (or ollama serve)"
fi

# Backend API
if curl -s http://localhost:8001/api/v1/system/health >/dev/null 2>&1; then
    check_ok "Backend API accessible"
    # Vérifier la version
    VERSION=$(curl -s http://localhost:8001/api/v1/system/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$VERSION" ]; then
        check_ok "Backend version: $VERSION"
    fi
else
    check_fail "Backend API NOT accessible on http://localhost:8001/api/v1/system/health"
    echo "   → Start with: cd backend && uvicorn main:app --host 0.0.0.0 --port 8001"
fi
echo ""

# 4. Vérifier la configuration
echo "⚙️  Checking configuration..."

# .env file
if [ -f "backend/.env" ]; then
    check_ok "backend/.env exists"

    # Vérifier les variables critiques
    if grep -q "OLLAMA_URL" backend/.env; then
        OLLAMA_URL=$(grep "OLLAMA_URL" backend/.env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        check_ok "OLLAMA_URL configured: $OLLAMA_URL"
    else
        check_warn "OLLAMA_URL not found in backend/.env (using default)"
    fi

    if grep -q "WORKSPACE_DIR" backend/.env; then
        WORKSPACE_DIR=$(grep "WORKSPACE_DIR" backend/.env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -d "$WORKSPACE_DIR" ]; then
            check_ok "WORKSPACE_DIR exists: $WORKSPACE_DIR"
        else
            check_fail "WORKSPACE_DIR configured but doesn't exist: $WORKSPACE_DIR"
        fi
    fi
else
    check_warn "backend/.env not found (using defaults from config.py)"
fi

# frontend .env
if [ -f "frontend/.env" ]; then
    check_ok "frontend/.env exists"

    if grep -q "VITE_API_URL" frontend/.env; then
        VITE_API_URL=$(grep "VITE_API_URL" frontend/.env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        check_ok "VITE_API_URL configured: $VITE_API_URL"
    fi
else
    check_warn "frontend/.env not found (will use default http://localhost:8001)"
fi
echo ""

# 5. Vérifier l'espace disque
echo "💾 Checking disk space..."
WORKSPACE_DIR="${WORKSPACE_DIR:-/home/lalpha/orchestrator-workspace}"
if [ -d "$WORKSPACE_DIR" ]; then
    DISK_USAGE=$(df -h "$WORKSPACE_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 80 ]; then
        check_ok "Disk usage: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        check_warn "Disk usage: ${DISK_USAGE}% - Consider cleanup"
    else
        check_fail "Disk usage: ${DISK_USAGE}% - CRITICAL!"
    fi
fi
echo ""

# 6. Vérifier les dépendances Python
echo "🐍 Checking Python dependencies..."
if [ -f "backend/requirements.txt" ]; then
    # Vérifier que les packages critiques sont installés
    # Note: 'ollama' package n'est PAS requis (backend utilise httpx directement)
    CRITICAL_PACKAGES=("fastapi" "uvicorn" "httpx" "chromadb")
    for pkg in "${CRITICAL_PACKAGES[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            check_ok "Python package '$pkg' installed"
        else
            check_fail "Python package '$pkg' NOT installed"
            echo "   → Install with: cd backend && pip install -r requirements.txt"
        fi
    done
fi
echo ""

# Résumé
echo "================================"
echo "Summary:"
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! AI Orchestrator is healthy.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ All critical checks passed, but there are $WARNINGS warnings.${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS critical issues. Please fix them before running.${NC}"
    exit 1
fi
