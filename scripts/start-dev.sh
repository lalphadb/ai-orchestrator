#!/bin/bash
#
# Script de démarrage développement AI Orchestrator
# Démarre le backend et le frontend en parallèle
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Orchestrator v8 - Démarrage développement${NC}"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des serveurs...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM

# Start Backend
echo -e "${BLUE}🔧 Démarrage Backend...${NC}"
cd backend
source .venv/bin/activate
python -c "from app.core.database import init_db; init_db()" 2>/dev/null || true
python main.py &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✅ Backend démarré (PID: $BACKEND_PID)${NC}"
echo -e "   URL: http://localhost:8001"
echo -e "   API Docs: http://localhost:8001/docs"
echo -e "   Health: http://localhost:8001/health"

# Wait for backend to be ready
echo -e "${BLUE}⏳ Attente du backend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend prêt!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend timeout${NC}"
        exit 1
    fi
done

# Start Frontend
echo -e "${BLUE}🎨 Démarrage Frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend démarré (PID: $FRONTEND_PID)${NC}"
echo -e "   URL: http://localhost:5173"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}🚀 AI Orchestrator v8 démarré avec succès!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "🔗 URLs disponibles:"
echo -e "   Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "   Backend:  ${BLUE}http://localhost:8001${NC}"
echo -e "   API Docs: ${BLUE}http://localhost:8001/docs${NC}"
echo -e "   Metrics:  ${BLUE}http://localhost:8001/metrics${NC}"
echo ""
echo -e "📝 Commandes utiles:"
echo -e "   Tests:    ${YELLOW}cd frontend && npm test${NC}"
echo -e "   E2E:      ${YELLOW}cd frontend && npm run test:e2e${NC}"
echo -e "   Lint:     ${YELLOW}cd frontend && npm run lint${NC}"
echo ""
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"

# Wait for processes
wait
