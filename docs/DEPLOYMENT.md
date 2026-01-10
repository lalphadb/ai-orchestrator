# Déploiement - AI Orchestrator v6.5

## Architecture de déploiement

Le backend tourne en service systemd local (pas Docker).
Le frontend reste en Docker via nginx.

## Prérequis

- Ubuntu 22.04+ ou Debian 12+
- Python 3.11+
- Node.js 18+ et npm
- Ollama installé
- Docker (frontend uniquement)

## Installation Backend (systemd)

### 1. Dépendances
```bash
cd /home/lalpha/projets/ai-tools/ai-orchestrator/backend
pip install -r requirements.txt --break-system-packages
```

### 2. Service systemd
```bash
sudo tee /etc/systemd/system/ai-orchestrator.service << 'SERVICE'
[Unit]
Description=AI Orchestrator Backend v6.5
After=network.target ollama.service

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator
```

## Commandes de gestion

### Backend
```bash
sudo systemctl status ai-orchestrator
journalctl -u ai-orchestrator -f
sudo systemctl restart ai-orchestrator
```

### Frontend
```bash
docker restart ai-orchestrator-frontend
docker logs -f ai-orchestrator-frontend
```

## Vérification
```bash
curl http://localhost:8001/api/v1/system/health
curl http://localhost:8002/
```
