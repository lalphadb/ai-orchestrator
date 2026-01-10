# Changelog - AI Orchestrator

## [6.5] - 2026-01-09

### 🏗️ Architecture majeure
- **Backend sans Docker** : Exécution via systemd au lieu de conteneur Docker
- **Connexion Ollama directe** : localhost:11434 (plus de host.docker.internal)
- **Mode direct par défaut** : EXECUTE_MODE=direct (pas de sandbox)

### ✨ Améliorations
- Frontend: Dropdown modèles affiche les noms correctement (plus de JSON)
- Backend: `normalize_model()` pour éviter erreur SQLite avec dict
- Configuration: VERIFY_REQUIRED=false par défaut

### 🐛 Corrections
- Fix affichage [object Object] dans le sélecteur de modèles
- Fix erreur "Interfaces dict not supported" SQLite
- Fix connexion WebSocket stable

### 📝 Documentation
- README.md réécrit pour architecture systemd
- Instructions d'installation sans Docker
- Commandes de gestion systemd

---

## [6.2] - 2026-01-08

### 🔒 Sécurité
- Audit de sécurité complet
- Allowlist de commandes étendue
- Mode sandbox Docker par défaut

### ✨ Améliorations
- 72 outils disponibles
- Run Inspector amélioré
- Pipeline Workflow complet

---

## [6.1] - 2026-01-07

### ✨ Nouvelles fonctionnalités
- Self-Learning System (auto-amélioration)
- Mémoire sémantique ChromaDB
- Pipeline SPEC → PLAN → EXECUTE → VERIFY → REPAIR

### 🔧 Technique
- ReAct Engine v2
- WebSocket streaming
- Multi-modèles (local + cloud)

---

## [6.0] - 2026-01-05

### 🎉 Version initiale
- Interface Vue 3 + Tailwind
- Backend FastAPI
- Intégration Ollama
- 34 outils de base
