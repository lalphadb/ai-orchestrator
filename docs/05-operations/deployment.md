# Déploiement

## Production avec Traefik

### Configuration nginx

```nginx
# Voir nginx.conf à la racine du projet
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name ai.4lb.ca;
    
    location /api {
        proxy_pass http://backend;
    }
    
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd Service

```ini
# /etc/systemd/system/ai-orchestrator.service
[Unit]
Description=AI Orchestrator Backend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/backend
ExecStart=/home/lalpha/projets/ai-tools/ai-orchestrator/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Commandes

```bash
# Démarrer
sudo systemctl start ai-orchestrator

# Status
sudo systemctl status ai-orchestrator

# Logs
journalctl -u ai-orchestrator -f
```

## Monitoring

Voir `monitoring/` pour la stack Grafana/Prometheus/Loki.

```bash
cd monitoring
docker compose up -d
```

Dashboards disponibles sur `http://localhost:3000`
