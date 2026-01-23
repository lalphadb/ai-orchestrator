# ⚠️ DOCKER-COMPOSE.YML OBSOLÈTE

**Date d'archivage**: 2026-01-20
**Raison**: Migration vers architecture hybride v7 + unified-stack

---

## 🚨 NE PAS UTILISER LE FICHIER docker-compose.yml DE CE RÉPERTOIRE

Le docker-compose.yml présent dans ce répertoire est **obsolète et non fonctionnel**.

---

## 📍 Nouvelle Configuration Opérationnelle

### Backend (Port 8001)
**Gestion**: Service systemd (pas Docker)
```bash
# Status
sudo systemctl status ai-orchestrator

# Logs
sudo journalctl -u ai-orchestrator -f

# Configuration
/etc/systemd/system/ai-orchestrator.service
Working Dir: /home/lalpha/projets/ai-tools/ai-orchestrator/backend
```

### Frontend (Port 80 interne, HTTPS via Traefik)
**Gestion**: Docker via unified-stack
```bash
# Status
cd /home/lalpha/projets/infrastructure/unified-stack
docker compose ps ai-orchestrator-frontend

# Accès
curl -sk https://ai.4lb.ca/health

# Configuration
Container: ai-orchestrator-frontend (nginx:alpine)
Source: /home/lalpha/projets/ai-tools/ai-orchestrator/frontend/dist
```

---

## 🔄 Architecture Actuelle (v7 Hybride)

```
AI Orchestrator v7
├── Backend (systemd)
│   ├── Service: ai-orchestrator.service
│   ├── Port: 0.0.0.0:8001
│   └── Command: uvicorn main:app --reload
│
└── Frontend (Docker)
    ├── Container: ai-orchestrator-frontend
    ├── Image: nginx:alpine
    ├── Network: unified-net (192.168.200.0/24)
    └── Accès: https://ai.4lb.ca (via Traefik)
```

---

## 📖 Pourquoi cette Architecture ?

1. **Backend systemd**: Meilleure stabilité, auto-restart natif, intégration OS
2. **Frontend Docker**: Facilité de mise à jour, isolation, intégration Traefik
3. **Unified-stack**: Gestion centralisée de tous les services Docker

---

## 📂 Fichier Archivé

L'ancien docker-compose.yml a été déplacé vers:
```
/home/lalpha/projets/.archive/obsolete-compose-configs/ai-orchestrator-docker-compose.yml
```

**Ne pas restaurer** - Créerait des conflits de ports et containers.

---

## 📚 Documentation

- **Architecture**: `/home/lalpha/documentation/ARCHITECTURE.md`
- **Unified Stack**: `/home/lalpha/projets/infrastructure/unified-stack/docker-compose.yml`
- **Archive**: `/home/lalpha/projets/.archive/obsolete-compose-configs/README.md`
