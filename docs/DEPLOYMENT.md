# Guide de Déploiement

Guide complet pour déployer AI Orchestrator v6 en production.

---

## Architecture de production

```
┌─────────────────────────────────────────────────────────────┐
│                       INTERNET                               │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS (443)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Reverse Proxy (Traefik/Nginx)                │
│                 - SSL/TLS Termination                        │
│                 - Let's Encrypt                              │
│                 - Load Balancing                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │ Frontend  │   │ Backend   │   │ Ollama    │
     │ :3003     │   │ :8001     │   │ :11434    │
     └───────────┘   └───────────┘   └───────────┘
```

---

## Checklist pré-déploiement

- [ ] Clé SECRET_KEY unique et sécurisée
- [ ] DEBUG=false
- [ ] CORS configuré correctement
- [ ] Certificats SSL valides
- [ ] Firewall configuré (UFW)
- [ ] Backups automatiques configurés
- [ ] Monitoring en place

---

## Déploiement avec systemd

### 1. Services

```bash
# Copier les fichiers de service
sudo cp docs/systemd/*.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer au démarrage
sudo systemctl enable ai-orchestrator ai-orchestrator-frontend

# Démarrer
sudo systemctl start ai-orchestrator ai-orchestrator-frontend
```

### 2. Configuration Traefik

Créer `configs/traefik/dynamic/ai-orchestrator.yml`:

```yaml
http:
  routers:
    ai-frontend:
      rule: "Host(`ai.example.com`)"
      entryPoints: [websecure]
      service: ai-frontend
      tls:
        certResolver: letsencrypt
    
    ai-api:
      rule: "Host(`ai.example.com`) && PathPrefix(`/api`)"
      entryPoints: [websecure]
      service: ai-backend
      tls:
        certResolver: letsencrypt

  services:
    ai-frontend:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:3003"
    
    ai-backend:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8001"
```

### 3. Firewall (UFW)

```bash
# Règles de base
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 22/tcp

# HTTP/HTTPS (via reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activer
sudo ufw enable
```

---

## Monitoring

### Health checks

```bash
# Script de monitoring
cat > /home/lalpha/scripts/health-check.sh << 'EOF'
#!/bin/bash
BACKEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3003)
OLLAMA=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags)

if [ "$BACKEND" != "200" ]; then
  echo "Backend DOWN" | logger -t ai-orchestrator
  systemctl restart ai-orchestrator
fi
EOF

chmod +x /home/lalpha/scripts/health-check.sh
```

### Cron job

```bash
# Ajouter au crontab
crontab -e

# Health check toutes les 5 minutes
*/5 * * * * /home/lalpha/scripts/health-check.sh
```

---

## Backups

### Script de backup

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
BACKUP_DIR=/home/lalpha/backups
DB_FILE=/home/lalpha/projets/ai-tools/ai-orchestrator/backend/ai_orchestrator.db

mkdir -p $BACKUP_DIR

# Backup base de données
cp $DB_FILE $BACKUP_DIR/ai_orchestrator_$DATE.db

# Compression
gzip $BACKUP_DIR/ai_orchestrator_$DATE.db

# Garder 7 jours de backups
find $BACKUP_DIR -name "*.db.gz" -mtime +7 -delete
```

### Cron backup quotidien

```bash
# Backup à 3h du matin
0 3 * * * /home/lalpha/scripts/backup-db.sh
```

---

## Mise à jour

```bash
#!/bin/bash
# Script de mise à jour

set -e

cd /home/lalpha/projets/ai-tools/ai-orchestrator

# Arrêter les services
sudo systemctl stop ai-orchestrator ai-orchestrator-frontend

# Backup
cp backend/ai_orchestrator.db backend/ai_orchestrator.db.backup

# Pull des changements
git pull origin main

# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

# Redémarrer
sudo systemctl start ai-orchestrator ai-orchestrator-frontend

echo "✅ Mise à jour terminée"
```

---

## Rollback

```bash
#!/bin/bash
# Rollback en cas de problème

cd /home/lalpha/projets/ai-tools/ai-orchestrator

# Arrêter
sudo systemctl stop ai-orchestrator ai-orchestrator-frontend

# Restaurer la base de données
cp backend/ai_orchestrator.db.backup backend/ai_orchestrator.db

# Rollback git
git checkout HEAD~1

# Rebuild frontend
cd frontend && npm run build

# Redémarrer
sudo systemctl start ai-orchestrator ai-orchestrator-frontend
```

---

## Logs

```bash
# Backend logs
sudo journalctl -u ai-orchestrator -f

# Frontend logs
sudo journalctl -u ai-orchestrator-frontend -f

# Logs combinés
sudo journalctl -u ai-orchestrator -u ai-orchestrator-frontend -f
```
