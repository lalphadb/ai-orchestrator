# Sécurité

Guide des bonnes pratiques de sécurité pour AI Orchestrator v7.

**Changements v7:**
- Sandbox par défaut (Docker)
- SecureExecutor avec argv explicite (jamais `shell=True`)
- Outils système spécialisés avec capabilities
- Audit complet et traçabilité

---

## Posture sécurité v7.0 (fail-closed)

**Principe fondamental:** En cas de doute ou d'erreur, le système refuse l'action plutôt que de tenter un fallback potentiellement dangereux.

### Variables runtime critiques

| Variable | Valeur prod | Description |
|----------|-------------|-------------|
| `EXECUTE_MODE` | sandbox | Exécution isolée dans conteneur Docker |
| `ALLOW_DIRECT_FALLBACK` | false | **Jamais** de fallback vers exécution directe |
| `VERIFY_REQUIRED` | true | Phase VERIFY obligatoire avant `complete` |
| `SANDBOX_NETWORK` | none | Réseau désactivé dans le sandbox |
| `SANDBOX_READONLY` | true | Workspace en lecture seule pour viewer |

### Comportement fail-closed

```python
# Pseudo-code du comportement v7.0
def execute_command(cmd, role):
    if EXECUTE_MODE == "sandbox":
        result = run_in_docker(cmd)
        if result.failed and ALLOW_DIRECT_FALLBACK:
            # v7.0: INTERDIT en prod
            raise SecurityError("Direct fallback disabled")
        return result
    else:
        # Mode direct - uniquement dev local
        return run_direct(cmd)
```

### Vérification de conformité

```bash
# Script de vérification posture v7.0
#!/bin/bash
set -e

# Vérifier variables runtime
grep -q "EXECUTE_MODE=sandbox" .env || exit 1
grep -q "ALLOW_DIRECT_FALLBACK=false" .env || exit 1
grep -q "VERIFY_REQUIRED=true" .env || exit 1

# Vérifier Docker disponible
docker info > /dev/null 2>&1 || exit 1

# Vérifier sandbox fonctionnel
docker run --rm --network=none alpine echo "OK" || exit 1

echo "✅ Posture v7.0 conforme"
```

### Exceptions autorisées

| Contexte | EXECUTE_MODE | ALLOW_DIRECT_FALLBACK |
|----------|--------------|----------------------|
| Production | sandbox | false |
| Staging | sandbox | false |
| Développement local | direct | N/A |
| Tests CI | sandbox | false |

---

## Vue d'ensemble

AI Orchestrator implémente plusieurs couches de sécurité pour protéger l'application et les données utilisateurs.

```
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE TRANSPORT                          │
│  • TLS 1.3 (HTTPS)                                          │
│  • Certificats Let's Encrypt                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   COUCHE APPLICATION                         │
│  • Authentification JWT                                      │
│  • CORS whitelist                                           │
│  • Rate limiting                                            │
│  • Validation Pydantic                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE DONNÉES                            │
│  • Hachage bcrypt (passwords)                               │
│  • SQLite chiffré (optionnel)                               │
│  • Sanitization des entrées                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentification

### JWT (JSON Web Tokens)

- **Algorithme**: HS256
- **Expiration**: 24 heures (configurable)
- **Secret**: Clé de 64+ caractères aléatoires

```python
# Génération du token
token = jwt.encode(
    {"sub": user_id, "exp": datetime.utcnow() + timedelta(minutes=1440)},
    SECRET_KEY,
    algorithm="HS256"
)
```

### Bonnes pratiques

1. **Ne jamais stocker le token en localStorage** (vulnérable XSS)
2. **Utiliser httpOnly cookies** en production
3. **Rafraîchir les tokens** avant expiration
4. **Invalider les tokens** à la déconnexion

---

## Hachage des mots de passe

### bcrypt

- **Rounds**: 12 (par défaut)
- **Salt**: Automatique et unique par utilisateur

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hachage
hashed = pwd_context.hash("password123")

# Vérification
pwd_context.verify("password123", hashed)  # True
```

### Politique de mots de passe recommandée

| Critère | Minimum |
|---------|---------|
| Longueur | 8 caractères |
| Majuscules | 1 |
| Minuscules | 1 |
| Chiffres | 1 |
| Caractères spéciaux | 1 |

---

## CORS (Cross-Origin Resource Sharing)

### Configuration production

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai.4lb.ca"],  # Uniquement le domaine
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### ⚠️ À éviter

```python
# DANGEREUX - N'utilisez jamais en production
allow_origins=["*"]
```

---

## Rate Limiting

### Limites recommandées

| Endpoint | Limite | Fenêtre |
|----------|--------|---------|
| `/auth/login` | 5 | 1 minute |
| `/auth/register` | 3 | 1 heure |
| `/chat` | 20 | 1 minute |
| `/tools/*/execute` | 10 | 1 minute |

### Implémentation

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    pass
```

---

## Validation des entrées

### Pydantic

Toutes les entrées sont validées via Pydantic:

```python
from pydantic import BaseModel, validator, constr

class ChatRequest(BaseModel):
    message: constr(min_length=1, max_length=10000)
    conversation_id: Optional[UUID4] = None
    model: Optional[str] = None

    @validator('message')
    def sanitize_message(cls, v):
        # Supprimer les caractères dangereux
        return v.strip()
```

### Protection contre les injections

1. **SQL Injection**: SQLAlchemy ORM avec paramètres
2. **Command Injection**: Validation stricte des commandes
3. **XSS**: Échappement HTML côté frontend

---

## Sécurité des outils

### Exécution sécurisée (SecureExecutor v7)

**Principes non négociables:**

1. **Jamais `shell=True`** - parsing argv explicite via `shlex`
2. **Blocage d'injection** - refuse `;`, `&&`, `||`, `|`, backticks, `$()`
3. **Sandbox par défaut** - exécution dans conteneur Docker isolé
4. **Audit complet** - trace timestamp, rôle, command, résultat

```python
from app.services.react_engine.secure_executor import secure_executor, ExecutionRole

# Exécution sécurisée
result = await secure_executor.execute(
    command="ls -lah /workspace",
    role=ExecutionRole.VIEWER,
    timeout=30
)

if result.success:
    print(result.stdout)
else:
    print(f"Erreur: {result.error_code} - {result.error_message}")
```

### Sandbox automatique

Mode par défaut (`EXECUTE_MODE=sandbox`):

```bash
docker run --rm --network=none \
  --cpus=0.5 --memory=512m \
  -v /workspace:/workspace:ro \
  ubuntu:24.04 \
  ls -lah /workspace
```

**Protections:**
- Réseau désactivé (`--network=none`)
- Limites CPU/Mem (0.5 CPU, 512Mi)
- Workspace en lecture seule pour `viewer`
- Pas de montages système (`/etc`, `/root`, etc.)
- Timeout obligatoire

### Outils spécialisés (capabilities)

Plutôt que des commandes brutes, utilisez les outils dédiés:

```python
# Systemd
await systemd_status("nginx")           # viewer
await systemd_logs("nginx", lines=50)   # viewer
await systemd_restart("nginx")          # admin + justification

# Docker
await docker_list_containers()          # operator
await docker_logs("traefik", tail=100)  # operator
await docker_restart("traefik")         # admin + justification

# Réseau & Disque
await network_listeners()               # viewer
await disk_usage()                      # viewer

# Système
await apt_update()                      # admin + justification
await apt_install("package")            # admin + justification
```

### Caractères interdits

```python
FORBIDDEN_CHARS = [
    ';', '&&', '||', '|',      # Chaînage
    '`', '$(',                 # Substitution
    '>', '>>', '<', '<<',      # Redirections
    '\n', '\r', '\x00'         # Contrôle
]
```

### Audit et traçabilité

```python
# Récupérer l'historique d'audit
from app.services.react_engine.tools import BUILTIN_TOOLS

result = await BUILTIN_TOOLS.execute("get_audit_log", last_n=20)

for entry in result["data"]["entries"]:
    print(f"{entry['timestamp']}: {entry['role']} - {' '.join(entry['command'])}")
    print(f"  Allowed: {entry['allowed']}, Reason: {entry['reason']}")
```

---

## Headers de sécurité

### Configuration Traefik

```yaml
http:
  middlewares:
    security-headers:
      headers:
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        customResponseHeaders:
          X-Robots-Tag: "noindex,nofollow"
```

### Headers recommandés

| Header | Valeur |
|--------|--------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | `default-src 'self'` |

---

## Audit et logging

### Événements à logger

- Tentatives de connexion (succès/échec)
- Changements de mot de passe
- Exécution d'outils sensibles
- Erreurs d'authentification
- Rate limiting déclenché

### Format de log

```json
{
  "timestamp": "2026-01-08T14:30:00Z",
  "level": "WARNING",
  "event": "login_failed",
  "user": "unknown",
  "ip": "192.168.1.100",
  "details": "Invalid password"
}
```

---

## Gouvernance & Rôles

### Classification des actions

| Catégorie | Description | Vérification | Rollback |
|-----------|-------------|--------------|----------|
| `READ` | Lecture seule | Non | Non |
| `SAFE` | Actions sûres | Non | Non |
| `MODERATE` | Actions modérées | Recommandé | Optionnel |
| `SENSITIVE` | Actions sensibles | Obligatoire | Obligatoire |
| `CRITICAL` | Actions critiques | Approbation manuelle | Obligatoire |

### Rôles et capabilities

```python
from app.services.react_engine.secure_executor import ExecutionRole

# VIEWER - Lecture seule
role = ExecutionRole.VIEWER
commands = ["ls", "cat", "grep", "git status", "docker ps", "df"]

# OPERATOR - Actions sûres
role = ExecutionRole.OPERATOR
commands = ["systemctl restart", "docker restart", "git pull"]

# ADMIN - Actions sensibles (justification requise)
role = ExecutionRole.ADMIN
commands = ["apt update", "write_file", "chmod", "docker build"]
```

### Justification obligatoire

```python
from app.services.react_engine.governance import governance_manager

# Préparer une action sensible
approved, context, msg = await governance_manager.prepare_action(
    "write_file",
    {"path": "/etc/config.yaml", "content": "..."},
    justification="Mise à jour configuration pour déploiement v7"
)

if approved:
    # Exécuter l'action
    result = await tool_function(**params)
    
    # Enregistrer le résultat
    await governance_manager.record_result(
        context.action_id,
        success=result["success"],
        result=result
    )
else:
    print(f"Action refusée: {msg}")
```

### Rollback

```python
# Rollback automatique si échec
success, message = await governance_manager.rollback(action_id)
```

---

## Checklist de sécurité

### Avant déploiement

- [ ] SECRET_KEY unique et forte (64+ chars)
- [ ] DEBUG=false
- [ ] CORS configuré (pas de wildcard)
- [ ] HTTPS forcé
- [ ] Rate limiting activé
- [ ] Logs activés
- [ ] **EXECUTE_MODE=sandbox**
- [ ] **Docker disponible pour sandbox**
- [ ] **Tests de sécurité passés**

### Maintenance régulière

- [ ] Mise à jour des dépendances
- [ ] Rotation des secrets
- [ ] Revue des logs d'audit
- [ ] Tests de pénétration
- [ ] Backups vérifiés
- [ ] **Audit des actions sensibles**
- [ ] **Vérification des rollbacks disponibles**

---

## Signalement de vulnérabilités

Si vous découvrez une vulnérabilité, contactez:
- Email: security@4lb.ca
- Ne publiez pas publiquement avant correction
