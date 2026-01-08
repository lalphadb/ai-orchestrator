# Guide d'Installation

Guide complet pour installer AI Orchestrator v6 sur Ubuntu/Debian.

---

## Prérequis

### Système

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04+ |
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 32+ GB |
| Disque | 50 GB | 200+ GB SSD |
| GPU | - | NVIDIA RTX (pour LLM local) |

### Logiciels

- Python 3.11+
- Node.js 18+
- Git
- Ollama (pour inference locale)

---

## Installation pas à pas

### 1. Dépendances système

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs git curl wget build-essential
```

### 2. Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
ollama pull qwen2.5-coder:32b-instruct-q4_K_M
```

### 3. Cloner le projet

```bash
mkdir -p ~/projets/ai-tools && cd ~/projets/ai-tools
git clone <repository-url> ai-orchestrator
cd ai-orchestrator
```

### 4. Backend Python

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Frontend Vue.js

```bash
cd ../frontend
npm install
npm run build
```

### 6. Configuration

Créer le fichier `.env` dans le dossier backend:

```env
APP_NAME=AI Orchestrator
VERSION=6.0.0
DEBUG=false
SECRET_KEY=votre-clé-secrète-générer-avec-secrets
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
DATABASE_URL=sqlite:///./ai_orchestrator.db
MAX_ITERATIONS=10
```

### 7. Démarrage

```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001

# Frontend (autre terminal)
cd frontend && npm run dev
```

---

## Production (systemd)

### Backend Service

Créer `/etc/systemd/system/ai-orchestrator.service`:

```ini
[Unit]
Description=AI Orchestrator v6 Backend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/backend
ExecStart=/home/lalpha/projets/ai-tools/ai-orchestrator/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### Frontend Service

Créer `/etc/systemd/system/ai-orchestrator-frontend.service`:

```ini
[Unit]
Description=AI Orchestrator v6 Frontend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3003
Restart=always

[Install]
WantedBy=multi-user.target
```

### Activation

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-orchestrator ai-orchestrator-frontend
sudo systemctl start ai-orchestrator ai-orchestrator-frontend
```

---

## Vérification

```bash
sudo systemctl status ai-orchestrator
curl http://localhost:8001/health
curl http://localhost:3003
```
