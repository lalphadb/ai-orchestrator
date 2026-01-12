# Configuration

Guide complet des variables de configuration d'AI Orchestrator v7.0.

---

## Fichier .env

Le fichier `.env` se trouve dans `backend/.env` et contient toutes les variables de configuration.

### Variables d'application

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `APP_NAME` | string | AI Orchestrator | Nom de l'application |
| `VERSION` | string | 7.0.0 | Version de l'application |
| `DEBUG` | bool | false | Mode debug (logs détaillés) |
| `LOG_LEVEL` | string | INFO | Niveau de log (DEBUG, INFO, WARNING, ERROR) |

### Variables de sécurité

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `SECRET_KEY` | string | **requis** | Clé secrète pour JWT (min 32 chars) |
| `ALGORITHM` | string | HS256 | Algorithme de signature JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 1440 | Durée de validité du token (24h) |
| `CORS_ORIGINS` | string | * | Origines autorisées (séparées par virgule) |
| `EXECUTE_MODE` | string | sandbox | Mode exécution (sandbox/direct) |
| `ALLOW_DIRECT_FALLBACK` | bool | false | Autoriser fallback direct si sandbox échoue |
| `VERIFY_REQUIRED` | bool | true | Vérification QA obligatoire |

**Générer une clé secrète:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Variables Ollama

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `OLLAMA_URL` | string | http://localhost:11434 | URL de l'API Ollama |
| `DEFAULT_MODEL` | string | qwen2.5-coder:32b | Modèle LLM par défaut |
| `OLLAMA_TIMEOUT` | int | 120 | Timeout pour les requêtes Ollama (sec) |

### Variables Base de données

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `DATABASE_URL` | string | sqlite:///./ai_orchestrator.db | URL de connexion |

**Exemples de DATABASE_URL:**
```bash
# SQLite (local)
DATABASE_URL=sqlite:///./ai_orchestrator.db

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/orchestrator

# PostgreSQL avec SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Variables ReAct Engine

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `MAX_ITERATIONS` | int | 10 | Nombre max d'itérations par requête |
| `TOOL_TIMEOUT` | int | 30 | Timeout pour l'exécution d'outils (sec) |

---

## Exemple complet

```env
# =================================
# AI Orchestrator v7.0 - Configuration
# =================================

# Application
APP_NAME=AI Orchestrator
VERSION=7.0.0
DEBUG=false
LOG_LEVEL=INFO

# Sécurité
SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire-64-chars-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://ai.4lb.ca,http://localhost:5173

# Ollama
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
OLLAMA_TIMEOUT=120

# Base de données
DATABASE_URL=sqlite:///./ai_orchestrator.db

# ReAct Engine
MAX_ITERATIONS=10
TOOL_TIMEOUT=30
```

---

## Production defaults (v7.0)

**Posture fail-closed** - En production, les valeurs par défaut v7.0 garantissent:

| Variable | Valeur prod | Effet |
|----------|-------------|-------|
| `EXECUTE_MODE` | sandbox | Toute commande s'exécute dans un conteneur Docker isolé |
| `ALLOW_DIRECT_FALLBACK` | false | Si sandbox indisponible, échec au lieu de fallback direct |
| `VERIFY_REQUIRED` | true | Aucun workflow ne se termine sans passer la phase VERIFY |
| `DEBUG` | false | Pas de logs sensibles exposés |

**Exemple .env production v7.0:**
```env
# Sécurité fail-closed v7.0
EXECUTE_MODE=sandbox
ALLOW_DIRECT_FALLBACK=false
VERIFY_REQUIRED=true
DEBUG=false
LOG_LEVEL=WARNING
```

**Vérification E2E obligatoire:**
Avant tout déploiement prod, valider que le rollback fonctionne:
```bash
./scripts/test-rollback.sh  # Doit retourner exit 0
```

---

## Configuration par environnement

### Développement

```env
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Production

```env
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://ai.4lb.ca
ACCESS_TOKEN_EXPIRE_MINUTES=1440
EXECUTE_MODE=sandbox
ALLOW_DIRECT_FALLBACK=false
VERIFY_REQUIRED=true
```

---

## Variables d'environnement système

Ces variables peuvent être définies au niveau système:

```bash
# Dans /etc/environment ou ~/.bashrc
export OLLAMA_HOST=0.0.0.0
export OLLAMA_MODELS=/mnt/ollama-models
```

---

## Configuration Ollama

### Modèles recommandés

| Modèle | VRAM | Usage |
|--------|------|-------|
| qwen2.5-coder:32b | 20GB | Code, raisonnement |
| llama3.2-vision:11b | 12GB | Vision + texte |
| deepseek-coder:33b | 18GB | Code alternatif |
| nomic-embed-text | 1GB | Embeddings RAG |

### Configuration Ollama (/etc/systemd/system/ollama.service.d/override.conf)

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=/mnt/ollama-models"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
```

---

## Validation de la configuration

```bash
cd backend
source .venv/bin/activate

# Vérifier que toutes les variables sont définies
python3 -c "
from app.core.config import settings
print(f'App: {settings.APP_NAME} v{settings.VERSION}')
print(f'Debug: {settings.DEBUG}')
print(f'Ollama: {settings.OLLAMA_URL}')
print(f'Model: {settings.DEFAULT_MODEL}')
print(f'Max iterations: {settings.MAX_ITERATIONS}')
"
```
