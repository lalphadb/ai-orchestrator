#!/bin/bash
# Script d'application des corrections AI Orchestrator v6.2
# Usage: bash apply_corrections.sh

set -e

ORCHESTRATOR_DIR="/home/lalpha/projets/ai-tools/ai-orchestrator"
CORRECTIONS_DIR="/home/lalpha/corrections"
BACKUP_DIR="${ORCHESTRATOR_DIR}/backups/$(date +%Y%m%d_%H%M%S)"

echo "🔧 AI Orchestrator v6.1 → v6.2 Corrections"
echo "==========================================="
echo ""

# Créer le dossier de backup
mkdir -p "$BACKUP_DIR"
echo "📦 Backups dans: $BACKUP_DIR"

# 1. Backup des fichiers existants
echo ""
echo "📋 Étape 1: Sauvegarde des fichiers..."

files_to_backup=(
    "backend/app/api/v1/chat.py"
    "frontend/src/stores/chat.js"
    "frontend/src/components/chat/MessageList.vue"
    "frontend/src/components/chat/ModelsDisplay.vue"
    "frontend/src/components/chat/CategorySection.vue"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "${ORCHESTRATOR_DIR}/${file}" ]; then
        mkdir -p "${BACKUP_DIR}/$(dirname $file)"
        cp "${ORCHESTRATOR_DIR}/${file}" "${BACKUP_DIR}/${file}"
        echo "  ✓ $file"
    fi
done

# 2. Appliquer les corrections
echo ""
echo "📋 Étape 2: Application des corrections..."

# Correction 1: chat.py (WebSocket handlers)
if [ -f "${CORRECTIONS_DIR}/chat.py" ]; then
    cp "${CORRECTIONS_DIR}/chat.py" "${ORCHESTRATOR_DIR}/backend/app/api/v1/chat.py"
    echo "  ✓ chat.py (boutons WebSocket)"
fi

# Correction 2: chat.js (streaming fix)
if [ -f "${CORRECTIONS_DIR}/chat.js" ]; then
    cp "${CORRECTIONS_DIR}/chat.js" "${ORCHESTRATOR_DIR}/frontend/src/stores/chat.js"
    echo "  ✓ chat.js (streaming lisibilité)"
fi

# Correction 3: MessageList.vue (détection modèles)
if [ -f "${CORRECTIONS_DIR}/MessageList.vue" ]; then
    cp "${CORRECTIONS_DIR}/MessageList.vue" "${ORCHESTRATOR_DIR}/frontend/src/components/chat/MessageList.vue"
    echo "  ✓ MessageList.vue (affichage modèles)"
fi

# Correction 4: ModelsDisplay.vue (catégories)
if [ -f "${CORRECTIONS_DIR}/ModelsDisplay.vue" ]; then
    cp "${CORRECTIONS_DIR}/ModelsDisplay.vue" "${ORCHESTRATOR_DIR}/frontend/src/components/chat/ModelsDisplay.vue"
    echo "  ✓ ModelsDisplay.vue (catégories LLM)"
fi

# Correction 5: CategorySection.vue
if [ -f "${CORRECTIONS_DIR}/CategorySection.vue" ]; then
    cp "${CORRECTIONS_DIR}/CategorySection.vue" "${ORCHESTRATOR_DIR}/frontend/src/components/chat/CategorySection.vue"
    echo "  ✓ CategorySection.vue"
fi

# 3. Vérifier la syntaxe Python
echo ""
echo "📋 Étape 3: Vérification syntaxe Python..."
cd "${ORCHESTRATOR_DIR}/backend"
if python3 -m py_compile app/api/v1/chat.py 2>/dev/null; then
    echo "  ✓ chat.py syntaxe OK"
else
    echo "  ❌ Erreur syntaxe chat.py - restauration du backup"
    cp "${BACKUP_DIR}/backend/app/api/v1/chat.py" "${ORCHESTRATOR_DIR}/backend/app/api/v1/chat.py"
    exit 1
fi

# 4. Rebuild et redémarrer
echo ""
echo "📋 Étape 4: Rebuild des containers..."
cd /home/lalpha/projets/infrastructure/unified-stack

echo "  Arrêt des services..."
./stack.sh down ai-orchestrator-backend ai-orchestrator-frontend 2>/dev/null || true

echo "  Rebuild backend..."
docker compose build ai-orchestrator-backend --no-cache

echo "  Rebuild frontend..."
docker compose build ai-orchestrator-frontend --no-cache

echo "  Démarrage..."
./stack.sh up -d

# 5. Attendre et vérifier
echo ""
echo "📋 Étape 5: Vérification du démarrage..."
sleep 10

if curl -s http://localhost:8001/health | grep -q "ok"; then
    echo "  ✓ Backend healthy"
else
    echo "  ⚠️ Backend peut prendre plus de temps..."
fi

echo ""
echo "✅ Corrections appliquées avec succès!"
echo ""
echo "📝 Pour tester:"
echo "   1. Ouvrir https://ai.4lb.ca"
echo "   2. Envoyer un message et vérifier le streaming"
echo "   3. Cliquer sur Re-verify après un run"
echo "   4. Demander 'liste les modèles' pour voir les catégories"
echo ""
echo "📦 En cas de problème, restaurer avec:"
echo "   cp -r ${BACKUP_DIR}/* ${ORCHESTRATOR_DIR}/"
