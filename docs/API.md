# API Reference

Documentation complète de l'API REST et WebSocket d'AI Orchestrator v6.

**Base URL:** `https://ai.4lb.ca/api/v1`

---

## Table des matières

1. [Authentification](#authentification)
2. [Chat](#chat)
3. [Conversations](#conversations)
4. [Outils](#outils)
5. [Système](#système)
6. [WebSocket](#websocket)
7. [Codes d'erreur](#codes-derreur)

---

## Authentification

### POST `/auth/login`

Authentifie un utilisateur et retourne un token JWT.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "lalpha",
    "email": "lalpha@4lb.ca",
    "is_admin": true
  }
}
```

**Response 401:**
```json
{
  "detail": "Identifiants invalides"
}
```

**Exemple cURL:**
```bash
curl -X POST https://ai.4lb.ca/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "lalpha", "password": "secret"}'
```

---

### POST `/auth/register`

Crée un nouveau compte utilisateur.

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "username": "newuser",
  "email": "newuser@example.com",
  "is_admin": false,
  "created_at": "2026-01-08T12:00:00Z"
}
```

**Response 400:**
```json
{
  "detail": "Username déjà utilisé"
}
```

---

### GET `/auth/me`

Retourne les informations de l'utilisateur connecté.

**Headers:**
```
Authorization: Bearer <token>
```

**Response 200:**
```json
{
  "id": "uuid",
  "username": "lalpha",
  "email": "lalpha@4lb.ca",
  "is_admin": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## Chat

### POST `/chat`

Envoie un message et reçoit une réponse (mode synchrone).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "message": "Quelle heure est-il?",
  "conversation_id": "uuid (optionnel)",
  "model": "qwen2.5-coder:32b-instruct-q4_K_M (optionnel)"
}
```

**Response 200:**
```json
{
  "response": "Il est actuellement 14h30.",
  "conversation_id": "uuid",
  "model_used": "qwen2.5-coder:32b-instruct-q4_K_M",
  "tools_used": [
    {
      "tool": "get_datetime",
      "input": {},
      "output": {"datetime": "2026-01-08T14:30:00"},
      "duration_ms": 5
    }
  ],
  "iterations": 2,
  "thinking": "[1] Analyse...\n[Tool] get_datetime...",
  "duration_ms": 3500
}
```

**Exemple cURL:**
```bash
curl -X POST https://ai.4lb.ca/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour!"}'
```

---

## Conversations

### GET `/conversations`

Liste toutes les conversations de l'utilisateur.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Nombre max de résultats |
| `offset` | int | 0 | Pagination offset |

**Response 200:**
```json
[
  {
    "id": "uuid",
    "title": "Question sur l'heure",
    "model": "qwen2.5-coder:32b-instruct-q4_K_M",
    "message_count": 4,
    "created_at": "2026-01-08T10:00:00Z",
    "updated_at": "2026-01-08T14:30:00Z"
  }
]
```

---

### GET `/conversations/{id}`

Récupère une conversation avec tous ses messages.

**Response 200:**
```json
{
  "id": "uuid",
  "title": "Question sur l'heure",
  "model": "qwen2.5-coder:32b-instruct-q4_K_M",
  "created_at": "2026-01-08T10:00:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Quelle heure est-il?",
      "created_at": "2026-01-08T14:29:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Il est actuellement 14h30.",
      "model": "qwen2.5-coder:32b-instruct-q4_K_M",
      "tools_used": "[\"get_datetime\"]",
      "created_at": "2026-01-08T14:30:00Z"
    }
  ]
}
```

---

### DELETE `/conversations/{id}`

Supprime une conversation et tous ses messages.

**Response 204:** No Content

---

### PATCH `/conversations/{id}`

Met à jour le titre d'une conversation.

**Request:**
```json
{
  "title": "Nouveau titre"
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "title": "Nouveau titre",
  "updated_at": "2026-01-08T15:00:00Z"
}
```

---

## Outils

### GET `/tools`

Liste tous les outils disponibles.

**Response 200:**
```json
{
  "tools": [
    {
      "id": "execute_command",
      "name": "execute_command",
      "description": "Exécute une commande shell",
      "category": "system",
      "parameters": {
        "command": "string (required)",
        "timeout": "int (default: 30)"
      }
    },
    {
      "id": "read_file",
      "name": "read_file",
      "description": "Lit le contenu d'un fichier",
      "category": "files",
      "parameters": {
        "path": "string (required)"
      }
    }
  ],
  "categories": ["system", "files", "utility", "network"],
  "total": 9
}
```

---

### GET `/tools/{name}`

Récupère les détails d'un outil spécifique.

**Response 200:**
```json
{
  "id": "execute_command",
  "name": "execute_command",
  "description": "Exécute une commande shell sur le système",
  "category": "system",
  "parameters": {
    "command": "string - Commande à exécuter",
    "timeout": "int - Timeout en secondes (défaut: 30)"
  },
  "usage_count": 42,
  "examples": [
    {
      "input": {"command": "ls -la"},
      "description": "Liste les fichiers du répertoire courant"
    }
  ]
}
```

---

### POST `/tools/{name}/execute`

Exécute un outil manuellement (admin only).

**Request:**
```json
{
  "params": {
    "command": "uptime"
  }
}
```

**Response 200:**
```json
{
  "result": {
    "stdout": " 14:30:00 up 5 days...",
    "stderr": "",
    "returncode": 0
  },
  "duration_ms": 15
}
```

---

## Système

### GET `/system/stats`

Retourne les statistiques du système.

**Response 200:**
```json
{
  "cpu_percent": 15.2,
  "memory": {
    "total_gb": 64.0,
    "used_gb": 23.5,
    "percent": 36.7
  },
  "disk": {
    "total_gb": 2000,
    "used_gb": 244,
    "percent": 12.2
  },
  "uptime_hours": 120,
  "python_version": "3.13.0",
  "app_version": "6.0.0"
}
```

---

### GET `/system/models`

Liste les modèles Ollama disponibles.

**Response 200:**
```json
{
  "models": [
    {
      "name": "qwen2.5-coder:32b-instruct-q4_K_M",
      "size_gb": 19.2,
      "modified_at": "2026-01-01T00:00:00Z",
      "family": "qwen2.5"
    },
    {
      "name": "llama3.2-vision:11b",
      "size_gb": 12.0,
      "modified_at": "2025-12-15T00:00:00Z",
      "family": "llama"
    }
  ],
  "default_model": "qwen2.5-coder:32b-instruct-q4_K_M",
  "ollama_version": "0.5.4"
}
```

---

### GET `/system/health`

Health check pour monitoring.

**Response 200:**
```json
{
  "status": "healthy",
  "ollama": "connected",
  "database": "connected",
  "timestamp": "2026-01-08T14:30:00Z"
}
```

---

## WebSocket

### WS `/chat/ws`

Connexion WebSocket pour chat en temps réel avec streaming.

**URL:** `wss://ai.4lb.ca/api/v1/chat/ws`

#### Messages Client → Serveur

```json
{
  "message": "Quelle heure est-il?",
  "conversation_id": "uuid (optionnel)",
  "model": "qwen2.5-coder:32b-instruct-q4_K_M (optionnel)"
}
```

#### Messages Serveur → Client

**Type: `conversation_created`**
```json
{
  "type": "conversation_created",
  "data": {"id": "uuid"},
  "timestamp": "2026-01-08T14:30:00Z"
}
```

**Type: `thinking`**
```json
{
  "type": "thinking",
  "data": {"message": "Analyse...", "iteration": 0},
  "timestamp": "2026-01-08T14:30:00Z"
}
```

**Type: `token`** (streaming)
```json
{
  "type": "token",
  "data": "Il",
  "timestamp": "2026-01-08T14:30:00Z"
}
```

**Type: `tool`**
```json
{
  "type": "tool",
  "data": {
    "tool": "get_datetime",
    "params": {},
    "iteration": 1
  },
  "timestamp": "2026-01-08T14:30:00Z"
}
```

**Type: `complete`**
```json
{
  "type": "complete",
  "data": {
    "response": "Il est actuellement 14h30.",
    "tools_used": [...],
    "iterations": 2,
    "duration_ms": 3500
  },
  "timestamp": "2026-01-08T14:30:00Z"
}
```

**Type: `error`**
```json
{
  "type": "error",
  "data": "Message d'erreur",
  "timestamp": "2026-01-08T14:30:00Z"
}
```

#### Exemple JavaScript

```javascript
const ws = new WebSocket('wss://ai.4lb.ca/api/v1/chat/ws');

ws.onopen = () => {
  console.log('Connecté');
  ws.send(JSON.stringify({
    message: "Quelle heure est-il?",
    model: "qwen2.5-coder:32b-instruct-q4_K_M"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'token':
      process.stdout.write(data.data); // Streaming
      break;
    case 'tool':
      console.log(`\n🔧 Outil: ${data.data.tool}`);
      break;
    case 'complete':
      console.log(`\n✅ Terminé en ${data.data.duration_ms}ms`);
      break;
    case 'error':
      console.error(`❌ Erreur: ${data.data}`);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

#### Exemple Python

```python
import asyncio
import websockets
import json

async def chat():
    uri = "wss://ai.4lb.ca/api/v1/chat/ws"
    
    async with websockets.connect(uri) as ws:
        # Envoyer message
        await ws.send(json.dumps({
            "message": "Quelle heure est-il?"
        }))
        
        # Recevoir réponses
        while True:
            response = await ws.recv()
            data = json.loads(response)
            
            if data["type"] == "token":
                print(data["data"], end="", flush=True)
            elif data["type"] == "complete":
                print(f"\n✅ {data['data']['duration_ms']}ms")
                break
            elif data["type"] == "error":
                print(f"❌ {data['data']}")
                break

asyncio.run(chat())
```

---

## Codes d'erreur

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Créé |
| 204 | Supprimé (no content) |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès interdit |
| 404 | Ressource non trouvée |
| 422 | Validation échouée |
| 429 | Rate limit atteint |
| 500 | Erreur serveur |

### Format d'erreur

```json
{
  "detail": "Description de l'erreur",
  "code": "ERROR_CODE (optionnel)",
  "field": "nom_du_champ (si validation)"
}
```

---

## Rate Limiting

| Endpoint | Limite |
|----------|--------|
| `/auth/login` | 5 req/min |
| `/chat` | 20 req/min |
| `/tools/*/execute` | 10 req/min |
| Autres | 100 req/min |

**Headers de réponse:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704729600
```

---

## Pagination

Les endpoints qui retournent des listes supportent la pagination.

**Query Parameters:**
- `limit`: Nombre d'éléments (défaut: 50, max: 100)
- `offset`: Index de départ (défaut: 0)

**Headers de réponse:**
```
X-Total-Count: 150
X-Page: 1
X-Per-Page: 50
```

---

## Versioning

L'API est versionnée via le préfixe URL : `/api/v1/`

Les versions futures seront accessibles via `/api/v2/`, etc.

La version actuelle est toujours disponible sans préfixe pour compatibilité.
