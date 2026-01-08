# Troubleshooting

Guide de dépannage pour les problèmes courants d'AI Orchestrator v6.

---

## Problèmes de démarrage

### Le backend ne démarre pas

**Symptôme**: `systemctl status ai-orchestrator` affiche "failed"

**Diagnostic**:
```bash
sudo journalctl -u ai-orchestrator -n 50
```

**Solutions courantes**:

1. **Module manquant**
   ```bash
   cd backend
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Erreur de syntaxe Python**
   ```bash
   python -m py_compile main.py
   python -m py_compile app/core/config.py
   ```

3. **Port déjà utilisé**
   ```bash
   sudo lsof -i :8001
   sudo kill -9 <PID>
   ```

4. **Fichier .env manquant**
   ```bash
   cp .env.example .env
   nano .env  # Configurer
   ```

---

### Ollama non connecté

**Symptôme**: "Ollama non disponible" dans les logs

**Diagnostic**:
```bash
curl http://localhost:11434/api/tags
```

**Solutions**:

1. **Démarrer Ollama**
   ```bash
   sudo systemctl start ollama
   sudo systemctl status ollama
   ```

2. **Vérifier les modèles**
   ```bash
   ollama list
   ollama pull qwen2.5-coder:32b-instruct-q4_K_M
   ```

3. **Vérifier la configuration**
   ```bash
   # Dans backend/.env
   OLLAMA_URL=http://localhost:11434
   ```

---

### Frontend ne charge pas

**Symptôme**: Page blanche ou erreur 502

**Diagnostic**:
```bash
curl http://localhost:3003
sudo journalctl -u ai-orchestrator-frontend -f
```

**Solutions**:

1. **Rebuild le frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Vérifier le service**
   ```bash
   sudo systemctl restart ai-orchestrator-frontend
   ```

3. **Port bloqué**
   ```bash
   sudo ufw allow 3003
   ```

---

## Problèmes d'authentification

### "Identifiants invalides"

**Causes possibles**:
- Mauvais mot de passe
- Utilisateur inexistant
- Base de données corrompue

**Solutions**:

1. **Vérifier l'utilisateur existe**
   ```bash
   cd backend
   source .venv/bin/activate
   python3 -c "
   from app.core.database import SessionLocal
   from app.core.database import User
   db = SessionLocal()
   users = db.query(User).all()
   for u in users:
       print(f'{u.username} - {u.email}')
   "
   ```

2. **Recréer l'utilisateur admin**
   ```bash
   python3 -c "
   from app.core.database import SessionLocal, User
   from app.core.security import get_password_hash
   import uuid
   
   db = SessionLocal()
   # Supprimer l'ancien
   db.query(User).filter(User.username == 'admin').delete()
   # Créer nouveau
   user = User(
       id=str(uuid.uuid4()),
       username='admin',
       email='admin@local',
       hashed_password=get_password_hash('nouveaumotdepasse'),
       is_admin=True,
       is_active=True
   )
   db.add(user)
   db.commit()
   print('Admin recréé')
   "
   ```

### Token expiré

**Symptôme**: Déconnecté automatiquement

**Solution**: Augmenter la durée du token
```bash
# Dans .env
ACCESS_TOKEN_EXPIRE_MINUTES=2880  # 48h
```

---

## Problèmes WebSocket

### "WebSocket connection failed"

**Diagnostic**:
```bash
# Test direct
python3 -c "
import asyncio
import websockets
async def test():
    async with websockets.connect('ws://localhost:8001/api/v1/chat/ws') as ws:
        print('OK')
asyncio.run(test())
"
```

**Solutions**:

1. **Vérifier Traefik**
   ```bash
   # Traefik doit supporter WebSocket
   docker logs traefik 2>&1 | grep websocket
   ```

2. **Désactiver le buffering Nginx** (si utilisé)
   ```nginx
   location /api/v1/chat/ws {
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_buffering off;
   }
   ```

### Déconnexions fréquentes

**Causes**:
- Timeout proxy trop court
- Réseau instable

**Solutions**:
```yaml
# Traefik - augmenter timeout
http:
  middlewares:
    ws-timeout:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
```

---

## Problèmes de performance

### Réponses lentes

**Diagnostic**:
```bash
# Temps de réponse Ollama
time curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5-coder:32b-instruct-q4_K_M","prompt":"test","stream":false}'
```

**Solutions**:

1. **Utiliser un modèle plus léger**
   ```bash
   # Dans .env
   DEFAULT_MODEL=llama3.2:8b
   ```

2. **Augmenter les ressources Ollama**
   ```bash
   # Overload systemd
   sudo mkdir -p /etc/systemd/system/ollama.service.d
   echo "[Service]
   Environment=\"OLLAMA_NUM_PARALLEL=2\"
   Environment=\"OLLAMA_MAX_LOADED_MODELS=1\"" | sudo tee /etc/systemd/system/ollama.service.d/override.conf
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   ```

3. **Vérifier la mémoire GPU**
   ```bash
   nvidia-smi
   ```

### "Limite d'itérations atteinte"

**Cause**: Le modèle boucle sur les outils sans répondre

**Solutions**:

1. **Augmenter la limite temporairement**
   ```bash
   # Dans .env
   MAX_ITERATIONS=15
   ```

2. **Améliorer le prompt système** (déjà fait dans cette session)

3. **Utiliser un meilleur modèle**

---

## Problèmes de base de données

### Base de données corrompue

**Symptôme**: Erreurs SQLite

**Solution**:
```bash
cd backend

# Backup
cp ai_orchestrator.db ai_orchestrator.db.corrupt

# Vérifier
sqlite3 ai_orchestrator.db "PRAGMA integrity_check;"

# Si corrompu, recréer
rm ai_orchestrator.db
python3 -c "
from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print('DB recréée')
"
```

### Migrations

```bash
# Pas de système de migration automatique
# Pour ajouter une colonne:
sqlite3 ai_orchestrator.db "ALTER TABLE users ADD COLUMN new_column TEXT;"
```

---

## Logs utiles

### Où trouver les logs

| Service | Commande |
|---------|----------|
| Backend | `sudo journalctl -u ai-orchestrator -f` |
| Frontend | `sudo journalctl -u ai-orchestrator-frontend -f` |
| Ollama | `sudo journalctl -u ollama -f` |
| Traefik | `docker logs traefik -f` |

### Activer le mode debug

```bash
# Dans .env
DEBUG=true
LOG_LEVEL=DEBUG

# Redémarrer
sudo systemctl restart ai-orchestrator
```

---

## Commandes de diagnostic

```bash
# État général
sudo systemctl status ai-orchestrator ai-orchestrator-frontend ollama

# Ports
ss -tlnp | grep -E "8001|3003|11434"

# Ressources
htop
nvidia-smi

# Espace disque
df -h

# Test API
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/system/stats

# Test Ollama
curl http://localhost:11434/api/tags
```
