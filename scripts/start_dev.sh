#!/bin/bash
# Script de démarrage pour AI Orchestrator (développement)
# Date: 2026-01-25

PROJECT_ROOT="/home/lalpha/projets/ai-tools/ai-orchestrator"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  AI ORCHESTRATOR - DÉMARRAGE DÉVELOPPEMENT                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Vérifier si le backend est déjà lancé
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${GREEN}✅${NC} Backend déjà lancé sur port 8001"
else
    echo -e "${YELLOW}⚠️${NC}  Backend non lancé"
    echo "Pour lancer le backend dans un autre terminal:"
    echo "  cd $PROJECT_ROOT/backend"
    echo "  source .venv/bin/activate"
    echo "  uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
    echo ""
fi

# Vérifier si le frontend est déjà lancé
if pgrep -f "vite.*dev" > /dev/null; then
    echo -e "${GREEN}✅${NC} Frontend déjà lancé"
else
    echo -e "${YELLOW}⚠️${NC}  Frontend non lancé, démarrage..."
    cd "$PROJECT_ROOT/frontend"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Frontend va démarrer sur http://localhost:5173"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔑 IDENTIFIANTS:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "   OU"
    echo ""
    echo "   Username: lalpha"
    echo "   Password: lalpha123"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    npm run dev
fi
