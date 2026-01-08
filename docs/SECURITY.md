# Sécurité

Guide des bonnes pratiques de sécurité pour AI Orchestrator v6.

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

### execute_command

L'outil le plus risqué - mesures de protection:

```python
BLOCKED_COMMANDS = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",  # Fork bomb
    "chmod 777",
    "wget", "curl",  # Téléchargements arbitraires
]

async def execute_command(command: str, timeout: int = 30):
    # Vérifier les commandes bloquées
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return {"error": "Commande non autorisée"}

    # Timeout obligatoire
    process = await asyncio.wait_for(
        asyncio.create_subprocess_shell(command, ...),
        timeout=timeout
    )
```

### Sandbox recommandé

Pour une sécurité maximale, exécuter les commandes dans un conteneur Docker isolé:

```bash
docker run --rm --network=none \
  --memory=512m --cpus=0.5 \
  --read-only \
  ubuntu:24.04 \
  /bin/bash -c "commande"
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

## Checklist de sécurité

### Avant déploiement

- [ ] SECRET_KEY unique et forte (64+ chars)
- [ ] DEBUG=false
- [ ] CORS configuré (pas de wildcard)
- [ ] HTTPS forcé
- [ ] Rate limiting activé
- [ ] Logs activés

### Maintenance régulière

- [ ] Mise à jour des dépendances
- [ ] Rotation des secrets
- [ ] Revue des logs
- [ ] Tests de pénétration
- [ ] Backups vérifiés

---

## Signalement de vulnérabilités

Si vous découvrez une vulnérabilité, contactez:
- Email: security@4lb.ca
- Ne publiez pas publiquement avant correction
