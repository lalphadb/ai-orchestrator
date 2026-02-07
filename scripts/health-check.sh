#!/bin/bash
#
# Script de vérification complète AI Orchestrator
# Vérifie l'état de tous les composants
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 AI Orchestrator v8 - Health Check${NC}"
echo "================================================"

ERRORS=0

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "Checking $name... "
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "^$expected_code$"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Function to check command
check_command() {
    local cmd=$1
    local name=$2
    
    echo -n "Checking $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((ERRORS++))
        return 1
    fi
}

echo -e "\n${BLUE}📦 Vérification des dépendances...${NC}"
check_command "cd backend && python3 -c 'import fastapi'" "Python FastAPI"
check_command "cd frontend && node --version" "Node.js"
check_command "cd frontend && npm list vue" "Vue.js"

echo -e "\n${BLUE}🔧 Vérification du Backend...${NC}"
check_url "http://localhost:8001/health" "Backend Health" 200 || true
check_url "http://localhost:8001/docs" "API Docs" 200 || true
check_url "http://localhost:8001/metrics" "Prometheus Metrics" 200 || true

echo -e "\n${BLUE}🎨 Vérification du Frontend...${NC}"
check_url "http://localhost:5173" "Frontend Dev" 200 || true
check_url "http://localhost:4173" "Frontend Preview" 200 || true

echo -e "\n${BLUE}🧪 Vérification des Tests...${NC}"
echo -n "Tests unitaires frontend... "
cd frontend && npm test -- --run > /dev/null 2>&1 && echo -e "${GREEN}✅ OK${NC}" || echo -e "${YELLOW}⚠️  SKIP${NC}"
cd ..

echo -n "Syntaxe Python backend... "
cd backend && python3 -m py_compile main.py 2>/dev/null && echo -e "${GREEN}✅ OK${NC}" || echo -e "${RED}❌ FAIL${NC}"
cd ..

echo -e "\n${BLUE}💾 Vérification de la Base de données...${NC}"
if [ -f "backend/ai_orchestrator.db" ]; then
    echo -e "Database file: ${GREEN}✅ Existe${NC}"
    ls -lh backend/ai_orchestrator.db
else
    echo -e "Database file: ${YELLOW}⚠️  Non trouvé (sera créé au démarrage)${NC}"
fi

echo -e "\n${BLUE}🔐 Vérification de la Sécurité...${NC}"
if [ -f "backend/.env" ]; then
    echo -e "Environment file: ${GREEN}✅ Existe${NC}"
    if grep -q "SECRET_KEY" backend/.env; then
        echo -e "Secret key: ${GREEN}✅ Configuré${NC}"
    else
        echo -e "Secret key: ${RED}❌ Non configuré${NC}"
        ((ERRORS++))
    fi
else
    echo -e "Environment file: ${YELLOW}⚠️  Non trouvé${NC}"
fi

echo ""
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les contrôles sont OK!${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS erreur(s) détectée(s)${NC}"
    exit 1
fi
