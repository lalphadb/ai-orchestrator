# Deployment

## Production with nginx + Traefik

### nginx Configuration

The `nginx.conf` at the project root provides:
- Reverse proxy to backend (port 8001)
- WebSocket upgrade support
- Rate limiting (API, auth, global)
- Security headers (HSTS, CSP, X-Frame-Options)
- Gzip compression

### systemd Service

```ini
# /etc/systemd/system/ai-orchestrator.service
[Unit]
Description=AI Orchestrator Backend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/path/to/ai-orchestrator/backend
ExecStart=/path/to/ai-orchestrator/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator
sudo systemctl status ai-orchestrator
```

### Docker

Backend and frontend both include Dockerfiles with non-root users:
- Backend: `appuser` user
- Frontend: `nginx` user

```bash
# Build
docker build -t ai-orchestrator-backend ./backend
docker build -t ai-orchestrator-frontend ./frontend

# Run
docker run -d -p 8001:8001 ai-orchestrator-backend
docker run -d -p 80:80 ai-orchestrator-frontend
```

## Monitoring

See [observability.md](observability.md) for the Grafana/Prometheus/Loki stack.

```bash
cd monitoring
docker compose up -d
```

Grafana: http://localhost:3000
