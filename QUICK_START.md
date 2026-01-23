# Quick Start - AI Orchestrator v7.0

Guide de démarrage rapide pour l'AI Orchestrator v7.0.

---

## ⚡ Démarrage Rapide (< 5 minutes)

### Prérequis
```bash
# Vérifier les prérequis
python3 --version  # 3.11+
ollama --version   # Ollama installé
ollama list        # Au moins 1 modèle disponible
```

### Installation Backend

```bash
cd /home/lalpha/projets/ai-tools/ai-orchestrator

# Activer l'environnement virtuel
source .venv/bin/activate
# ou si pas encore créé:
python3 -m venv .venv && source .venv/bin/activate

# Installer les dépendances
pip install -r backend/requirements.txt

# Configurer (optionnel - les défauts fonctionnent)
cp backend/.env.example backend/.env
# Éditer backend/.env si nécessaire

# Lancer le backend
python backend/main.py
```

Le backend démarre sur **http://localhost:8001**

### Tests Rapides

```bash
# Dans un autre terminal
curl http://localhost:8001/api/v1/system/health

# Ou avec Python
python -c "import requests; print(requests.get('http://localhost:8001/api/v1/system/health').json())"
```

### Installation Frontend

```bash
cd frontend

# Installer les dépendances (première fois seulement)
npm install

# Lancer en dev
npm run dev
```

Le frontend démarre sur **http://localhost:3000** (ou 3001 si 3000 occupé)

---

## 🧪 Tester l'Orchestrator

### Via l'Interface Web

1. Ouvrir http://localhost:3000
2. Cliquer "Nouvelle conversation"
3. Essayer:
   - **Conversationnel:** "bonjour"
   - **Question simple:** "quelle heure est-il?"
   - **Question système:** "uptime du serveur?"
   - **Avec recherche:** "liste les fichiers dans /var/log"

### Via l'API

```bash
# Message conversationnel
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"bonjour", "model":"kimi-k2:1t-cloud"}'

# Question avec outil
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"quelle heure est-il?", "model":"kimi-k2:1t-cloud"}'

# Voir les modèles disponibles
curl http://localhost:8001/api/v1/system/models

# Voir les outils disponibles
curl http://localhost:8001/api/v1/tools
```

---

## 🔍 Vérifier que Tout Fonctionne

### Backend
```bash
# Tests unitaires
python -m pytest backend/tests -v

# Santé de l'API
curl http://localhost:8001/api/v1/system/health
# Devrait retourner: {"status":"healthy","version":"7.0"}

# Connexion Ollama
curl http://localhost:8001/api/v1/system/stats
# Devrait montrer "ollama_status":"connected"
```

### Frontend
- Ouvrir http://localhost:3000
- Vérifier que "Opérationnel" est affiché en vert
- Tester l'envoi d'un message
- Vérifier que le Run Inspector s'affiche

---

## 🛠️ Configuration Avancée

### Changer le Modèle LLM

```bash
# backend/.env
DEFAULT_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
EXECUTOR_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
```

### Activer la Vérification QA

```bash
# backend/.env
VERIFY_REQUIRED=true
MAX_REPAIR_CYCLES=2
```

### Mode Sandbox Docker

```bash
# backend/.env
EXECUTE_MODE=sandbox
SANDBOX_IMAGE=ubuntu:24.04
SANDBOX_MEMORY=512m
```

---

## 📊 Monitoring

### Logs Backend
```bash
# En dev
tail -f backend.log

# Avec systemd
journalctl -u ai-orchestrator -f
```

### Métriques Prometheus
```bash
curl http://localhost:8001/metrics
```

### Logs Frontend
```bash
# Console navigateur (F12)
# ou
docker logs -f ai-orchestrator-frontend
```

---

## 🚨 Dépannage

### Backend ne démarre pas

**Problème:** Port 8001 déjà utilisé
```bash
# Trouver le processus
lsof -i :8001
# Ou changer le port
# backend/.env
PORT=8002
```

**Problème:** Ollama non connecté
```bash
# Vérifier Ollama
systemctl status ollama
# Démarrer si nécessaire
systemctl start ollama
```

### Frontend ne se connecte pas

**Problème:** CORS
```bash
# Vérifier backend/.env
CORS_ORIGINS=["http://localhost:3000"]
```

**Problème:** URL backend incorrecte
```bash
# frontend/.env ou frontend/src/services/api.js
VITE_API_URL=http://localhost:8001
```

### Réponses lentes ou absentes

Voir [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) section "Aucune réponse ou réponses lentes (v7.0)"

**Quick fix:**
- Questions doivent contenir "?" ou mots interrogatifs
- Éviter commandes ambiguës sans contexte

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Vue d'ensemble |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture détaillée |
| [API.md](docs/API.md) | Documentation API |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Résolution problèmes |
| [SECURITY.md](docs/SECURITY.md) | Sécurité et isolation |
| [TEST_REPORT_2026-01-21.md](TEST_REPORT_2026-01-21.md) | Rapport de tests |

---

## 🎯 Prochaines Étapes

1. **Explorer l'UI:** Tester différentes requêtes
2. **Voir le Run Inspector:** Observer les phases du workflow
3. **Tester les outils:** Essayer les 72 outils disponibles
4. **Configurer les modèles:** Ajouter d'autres modèles LLM
5. **Lire la doc:** Approfondir avec [docs/](docs/)

---

## 💡 Exemples de Requêtes

### Questions Simples (Fast Path)
```
- "bonjour"
- "quelle heure est-il?"
- "uptime du serveur?"
- "quels modèles sont disponibles?"
- "liste les outils"
```

### Actions (Full Workflow)
```
- "crée un fichier test.txt avec 'hello world'"
- "liste les fichiers Python dans le projet"
- "analyse les logs du serveur"
- "vérifie le code avec ruff"
```

### Avec Vérification QA
```
- "écris un test unitaire pour calculate()"
- "formate le code Python"
- "exécute les tests pytest"
```

---

## 🆘 Support

- **Issues:** https://github.com/lalphadb/ai-orchestrator/issues
- **Docs:** [docs/INDEX.md](docs/INDEX.md)
- **Tests:** Voir [TEST_REPORT_2026-01-21.md](TEST_REPORT_2026-01-21.md)

---

**Version:** 7.0  
**Date:** 2026-01-21  
**Status:** ✅ Production Ready
