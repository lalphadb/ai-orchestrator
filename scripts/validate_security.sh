#!/bin/bash
# Script de validation sécurité après mises à jour
# Date: 2026-01-25

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  VALIDATION SÉCURITÉ - AI ORCHESTRATOR                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Compteurs
PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAILED++))
    fi
}

# Navigate to project root
cd "$(dirname "$0")/.."

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Vérification des dépendances"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Frontend
cd frontend
echo -n "Frontend - Vue 3.5.27: "
npm list vue 2>/dev/null | grep -q "vue@3.5.27"
check "Vue 3.5.27"

# Backend
cd ../backend
source .venv/bin/activate

echo -n "Backend - ChromaDB 1.4.1: "
pip show chromadb 2>/dev/null | grep -q "Version: 1.4.1"
check "ChromaDB 1.4.1"

echo -n "Backend - SQLAlchemy 2.0.46: "
pip show SQLAlchemy 2>/dev/null | grep -q "Version: 2.0.46"
check "SQLAlchemy 2.0.46"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Vérification configuration JWT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ALGORITHM=$(grep "ALGORITHM" app/core/config.py | grep -oP '(?<=")[^"]+' | head -1)
echo "Algorithme JWT: $ALGORITHM"

if [ "$ALGORITHM" = "HS256" ]; then
    echo -e "${GREEN}✅ SAFE${NC}: HS256 n'est pas affecté par CVE-2024-23342"
    ((PASSED++))
else
    echo -e "${RED}⚠️  VULNERABLE${NC}: Nécessite migration"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RÉSUMÉ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Tests passés:  $PASSED"
echo "Tests échoués: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ VALIDATION RÉUSSIE${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  ACTIONS REQUISES${NC}"
    exit 1
fi
