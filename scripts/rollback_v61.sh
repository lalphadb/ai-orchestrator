#!/bin/bash
# Rollback AI Orchestrator v6.1 → v6.0
# Usage: ./rollback_v61.sh

set -e

BACKUP_DIR="/home/lalpha/projets/ai-tools/ai-orchestrator/backups/20260108_111058_v61_workflow"
TARGET_DIR="/home/lalpha/projets/ai-tools/ai-orchestrator/backend/app"

echo "🔄 Rollback AI Orchestrator v6.1 → v6.0"
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Dossier de backup non trouvé: $BACKUP_DIR"
    exit 1
fi

echo "📦 Backup source: $BACKUP_DIR"
echo ""

# Arrêter le service si actif
echo "⏹️  Arrêt du service..."
sudo systemctl stop ai-orchestrator-backend 2>/dev/null || true

# Restaurer les fichiers
echo "📂 Restauration des fichiers..."

cp "$BACKUP_DIR/config.py" "$TARGET_DIR/core/config.py"
echo "   ✅ config.py restauré"

cp "$BACKUP_DIR/tools.py" "$TARGET_DIR/services/react_engine/tools.py"
echo "   ✅ tools.py restauré"

cp "$BACKUP_DIR/chat.py" "$TARGET_DIR/api/v1/chat.py"
echo "   ✅ chat.py restauré"

# Supprimer les nouveaux fichiers v6.1
echo ""
echo "🗑️  Suppression des nouveaux fichiers v6.1..."
rm -f "$TARGET_DIR/services/react_engine/verifier.py" && echo "   ✅ verifier.py supprimé"
rm -f "$TARGET_DIR/services/react_engine/workflow_engine.py" && echo "   ✅ workflow_engine.py supprimé"
rm -f "$TARGET_DIR/models/workflow.py" && echo "   ✅ workflow.py supprimé"

# Vérifier la syntaxe
echo ""
echo "🔍 Vérification syntaxe..."
cd /home/lalpha/projets/ai-tools/ai-orchestrator/backend
python3 -m py_compile app/core/config.py && echo "   ✅ config.py OK"
python3 -m py_compile app/services/react_engine/tools.py && echo "   ✅ tools.py OK"
python3 -m py_compile app/api/v1/chat.py && echo "   ✅ chat.py OK"

# Redémarrer le service
echo ""
echo "▶️  Redémarrage du service..."
sudo systemctl start ai-orchestrator-backend 2>/dev/null || echo "   ⚠️  Service non configuré"

echo ""
echo "✅ Rollback terminé!"
echo ""
echo "Note: Le workspace /home/lalpha/orchestrator-workspace n'a pas été supprimé."
