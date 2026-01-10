# AI Orchestrator v6.5

Un orchestrateur IA autonome avec pipeline Workflow complet, exécution d'outils directe, et interface Orchestrator UI professionnelle.

## 🎯 Fonctionnalités

- **Pipeline Workflow** : SPEC → PLAN → EXECUTE → VERIFY → REPAIR → COMPLETE
- **72 outils** intégrés (système, fichiers, QA, utilitaires, réseau)
- **7 outils QA** : git_status, git_diff, run_tests, run_lint, run_format, run_build, run_typecheck
- **Erreurs récupérables** : auto-correction via search_directory/search_files
- **Streaming WebSocket** temps réel avec run_id et phases
- **Run Inspector** : stepper workflow, tabs Tools/Thinking/QA/Raw, verdict PASS/FAIL
- **Exécution directe** : commandes sur le système hôte (pas de sandbox)
- **Multi-modèles** : Ollama local + proxies cloud

## 🏗️ Architecture v6.5

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVEUR (lalpha-server-1)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Frontend      │    │   Backend       │                │
│  │   (Docker)      │    │   (systemd)     │                │
│  │   nginx:alpine  │───▶│   Python/FastAPI│                │
│  │   Port 8002     │    │   Port 8001     │                │
│  └─────────────────┘    └────────┬────────┘                │
│                                  │                          │
│                                  ▼                          │
│                         ┌─────────────────┐                │
│                         │    Ollama       │                │
│                         │   (systemd)     │                │
│                         │   Port 11434    │                │
│                         └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Pourquoi pas Docker pour le backend ?

- **Connexion Ollama simplifiée** : localhost:11434 direct
- **Accès système complet** : git, python3, npm sans restrictions
- **Pas de problèmes réseau** : plus de host.docker.internal
- **Performance** : pas d'overhead conteneur

## 🚀 Installation

### Prérequis

- Ubuntu 22.04+ / Debian 12+
- Python 3.11+
- Node.js 18+
- Ollama installé et fonctionnel
- Docker (uniquement pour le frontend)

### Backend (systemd)

```bash
cd /home/lalpha/projets/ai-tools/ai-orchestrator/backend

# Installer les dépendances
pip install -r requirements.txt --break-system-packages

# Configurer
cp .env.example .env
nano .env  # Éditer les valeurs

# Créer le service systemd
sudo tee /etc/systemd/system/ai-orchestrator.service << 'SYSTEMD'
[Unit]
Description=AI Orchestrator Backend v6.5
After=network.target ollama.service

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/backend
Environment=PATH=/home/lalpha/.local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SYSTEMD

# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator
```

### Frontend (Docker)

```bash
cd /home/lalpha/projets/ai-tools/ai-orchestrator/frontend

# Build
npm install
npm run build

# Le conteneur nginx est géré par unified-stack
# Voir /home/lalpha/projets/infrastructure/unified-stack/
```

## 🔧 Configuration

### Variables d'environnement (backend/.env)

```env
# AI Orchestrator Backend v6.5
APP_VERSION=6.5
APP_NAME=AI Orchestrator

# Ollama - connexion directe
OLLAMA_URL=http://localhost:11434

# Modèles
DEFAULT_MODEL=kimi-k2:1t-cloud
EXECUTOR_MODEL=kimi-k2:1t-cloud

# Sécurité
JWT_SECRET_KEY=your-secret-key
ADMIN_PASSWORD=your-password

# Base de données
DATABASE_URL=sqlite:///./ai_orchestrator.db

# Workflow
VERIFY_REQUIRED=false
MAX_REPAIR_CYCLES=2
MAX_ITERATIONS=10

# Exécution directe (pas de sandbox Docker)
EXECUTE_MODE=direct
```

### Configuration nginx (frontend)

Le frontend utilise nginx pour servir les fichiers statiques et proxy vers le backend :

```nginx
location /api/ {
    proxy_pass http://10.10.10.46:8001/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## 📋 Commandes de gestion

### Backend (systemd)

```bash
# Status
sudo systemctl status ai-orchestrator

# Logs en temps réel
journalctl -u ai-orchestrator -f

# Redémarrer
sudo systemctl restart ai-orchestrator

# Arrêter
sudo systemctl stop ai-orchestrator
```

### Frontend (Docker via unified-stack)

```bash
cd /home/lalpha/projets/infrastructure/unified-stack

# Redémarrer le frontend
docker restart ai-orchestrator-frontend

# Logs
docker logs -f ai-orchestrator-frontend
```

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | Authentification |
| `GET /api/v1/conversations` | Liste conversations |
| `WS /api/v1/chat/ws` | Chat streaming |
| `GET /api/v1/system/health` | Health check |
| `GET /api/v1/system/models` | Modèles disponibles |
| `GET /api/v1/tools` | Liste des outils |

## 🔒 Sécurité

### Mode d'exécution

| Mode | Description | Usage |
|------|-------------|-------|
| `direct` | Exécution sur le système hôte | **Recommandé** pour serveur personnel |
| `sandbox` | Conteneur Docker isolé | Pour environnements multi-utilisateurs |

### Allowlist de commandes

Les commandes sont filtrées par une allowlist dans `config.py`. Commandes autorisées :
- Système : `uname`, `hostname`, `uptime`, `free`, `df`, `ps`
- Fichiers : `ls`, `cat`, `head`, `tail`, `grep`, `find`
- Dev : `python3`, `pip3`, `node`, `npm`, `git`
- QA : `ruff`, `black`, `mypy`, `pytest`

## 📚 Documentation

- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Tools](docs/TOOLS.md)
- [WebSocket Protocol](docs/WEBSOCKET.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 📝 Changelog

### v6.5 (2026-01-09)
- **Architecture** : Backend en systemd (plus de Docker)
- **Exécution** : Mode direct par défaut
- **Ollama** : Connexion localhost directe
- **Fix** : Dropdown modèles affiche les noms correctement
- **Fix** : normalize_model() pour SQLite

Voir [CHANGELOG.md](docs/CHANGELOG.md) pour l'historique complet.

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)
