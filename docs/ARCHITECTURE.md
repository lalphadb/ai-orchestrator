# Architecture Technique

## Vue d'ensemble

AI Orchestrator v6 suit une architecture modulaire composée de trois couches principales :

```
┌────────────────────────────────────────────────────────────────┐
│                      COUCHE PRÉSENTATION                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Frontend Vue.js 3                      │  │
│  │   • SPA (Single Page Application)                         │  │
│  │   • Pinia State Management                                │  │
│  │   • WebSocket Client                                      │  │
│  │   • Tailwind CSS                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / WSS
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                       COUCHE API                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Backend FastAPI                         │  │
│  │   • REST API v1                                           │  │
│  │   • WebSocket Endpoint                                    │  │
│  │   • JWT Authentication                                    │  │
│  │   • Pydantic Validation                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                     COUCHE SERVICES                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  ReAct Engine   │  │  Ollama Client  │  │   Database    │  │
│  │  • Reason       │  │  • Generate     │  │   • SQLite    │  │
│  │  • Act          │  │  • Stream       │  │   • SQLAlchemy│  │
│  │  • Observe      │  │  • Embeddings   │  │   • Migrations│  │
│  └────────┬────────┘  └────────┬────────┘  └───────────────┘  │
│           │                    │                               │
│           ▼                    ▼                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                     Tool Registry                        │  │
│  │  9 outils : execute_command, read_file, write_file,     │  │
│  │  list_directory, search_files, get_system_info,         │  │
│  │  get_datetime, calculate, http_request                  │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Composants Backend

### 1. Point d'entrée (`main.py`)

```python
# Initialisation FastAPI
app = FastAPI(
    title="AI Orchestrator",
    version="6.0.0",
    docs_url="/docs"
)

# Middleware
app.add_middleware(CORSMiddleware, ...)

# Routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

# Events
@app.on_event("startup")  # Init DB, Ollama check
@app.on_event("shutdown") # Cleanup
```

### 2. Module Core

#### `config.py` - Configuration
```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Orchestrator"
    VERSION: str = "6.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5-coder:32b-instruct-q4_K_M"
    
    # Database
    DATABASE_URL: str = "sqlite:///./orchestrator.db"
    
    # ReAct Engine
    MAX_ITERATIONS: int = 10
```

#### `database.py` - Modèles SQLAlchemy
```python
# Tables
- User: id, username, email, hashed_password, is_admin
- Conversation: id, user_id, title, model, created_at
- Message: id, conversation_id, role, content, tools_used
```

#### `security.py` - Authentification
```python
# Fonctions principales
- get_password_hash(password)      # Hachage bcrypt
- verify_password(plain, hashed)   # Vérification
- create_access_token(data)        # Génération JWT
- verify_token(token)              # Validation JWT
- get_current_user(credentials)    # Dependency injection
```

### 3. Module API (`app/api/v1/`)

| Fichier | Routes | Description |
|---------|--------|-------------|
| `auth.py` | `/auth/login`, `/auth/register` | Authentification |
| `chat.py` | `/chat`, `/chat/ws` | Chat HTTP + WebSocket |
| `conversations.py` | `/conversations` | CRUD conversations |
| `tools.py` | `/tools` | Liste et stats outils |
| `system.py` | `/system/stats`, `/system/models` | Infos système |

### 4. Services

#### ReAct Engine (`services/react_engine/`)

Le cœur du système - implémente la boucle ReAct :

```
┌──────────────────────────────────────────────────────────┐
│                    BOUCLE ReAct                          │
│                                                          │
│   ┌─────────┐                                           │
│   │  START  │                                           │
│   └────┬────┘                                           │
│        │                                                │
│        ▼                                                │
│   ┌─────────────────────────────────────────────────┐   │
│   │           THINK (Reason)                         │   │
│   │   • Analyser le message utilisateur              │   │
│   │   • Consulter l'historique                       │   │
│   │   • Déterminer l'action nécessaire               │   │
│   └───────────────────┬─────────────────────────────┘   │
│                       │                                 │
│                       ▼                                 │
│             ┌─────────────────┐                         │
│             │  Besoin outil?  │                         │
│             └────────┬────────┘                         │
│                      │                                  │
│         ┌───────────┴───────────┐                       │
│         │ OUI                   │ NON                   │
│         ▼                       ▼                       │
│   ┌──────────────┐      ┌──────────────┐               │
│   │     ACT      │      │   RESPOND    │               │
│   │ Exécuter     │      │   Réponse    │               │
│   │ l'outil      │      │   finale     │               │
│   └──────┬───────┘      └──────┬───────┘               │
│          │                     │                        │
│          ▼                     │                        │
│   ┌──────────────┐             │                        │
│   │   OBSERVE    │             │                        │
│   │   Analyser   │             │                        │
│   │   résultat   │             │                        │
│   └──────┬───────┘             │                        │
│          │                     │                        │
│          │ (loop)              │                        │
│          └──────────┬──────────┘                        │
│                     │                                   │
│                     ▼                                   │
│               ┌─────────┐                               │
│               │   END   │                               │
│               └─────────┘                               │
└──────────────────────────────────────────────────────────┘
```

**Format de réponse LLM :**
```
Pour utiliser un outil:
```tool
{"tool": "nom_outil", "params": {"param1": "valeur"}}
```

Pour répondre:
```response
Votre réponse ici
```
```

#### Ollama Client (`services/ollama/`)

```python
class OllamaClient:
    # Méthodes principales
    async def health_check() -> bool
    async def list_models() -> List[Dict]
    async def generate(prompt, model, system) -> Dict
    async def generate_stream(prompt, model, system) -> AsyncGenerator
    async def chat(messages, model) -> Dict
    async def embeddings(text, model) -> List[float]
```

---

## Composants Frontend

### 1. Structure Vue.js

```
frontend/src/
├── main.js              # Point d'entrée
├── App.vue              # Composant racine
├── router/
│   └── index.js         # Routes
├── stores/
│   ├── auth.js          # État authentification
│   └── chat.js          # État chat + WebSocket
├── views/
│   ├── ChatView.vue     # Interface chat
│   ├── LoginView.vue    # Connexion
│   ├── ToolsView.vue    # Liste outils
│   └── SettingsView.vue # Paramètres
└── components/          # Composants réutilisables
```

### 2. State Management (Pinia)

#### Auth Store (`stores/auth.js`)
```javascript
// État
- user: Object | null
- token: String | null
- isAuthenticated: computed

// Actions
- login(username, password)
- logout()
- getHeaders()  // Pour requêtes API
```

#### Chat Store (`stores/chat.js`)
```javascript
// État
- messages: Array
- conversations: Array
- currentConversation: Object
- isLoading: Boolean
- streamingContent: String
- currentTool: Object

// Actions
- connectWebSocket()
- sendMessage(content)
- selectConversation(id)
- newConversation()
```

### 3. Communication WebSocket

```javascript
// Connexion
const ws = new WebSocket('wss://ai.4lb.ca/api/v1/chat/ws')

// Messages reçus
{
  type: 'token' | 'thinking' | 'tool' | 'complete' | 'error',
  data: Any,
  timestamp: ISO8601
}

// Message envoyé
{
  message: String,
  conversation_id: String?,
  model: String
}
```

---

## Infrastructure

### Déploiement Production

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS (443)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Traefik Reverse Proxy                     │
│                    (Docker, Let's Encrypt)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │ Frontend  │   │ Backend   │   │ WebSocket │
     │ :3003     │   │ :8001/api │   │ :8001/ws  │
     │ (serve)   │   │ (uvicorn) │   │ (uvicorn) │
     └───────────┘   └─────┬─────┘   └───────────┘
                           │
                           ▼
                    ┌───────────┐
                    │  Ollama   │
                    │  :11434   │
                    └───────────┘
```

### Services systemd

**Backend** (`/etc/systemd/system/ai-orchestrator.service`):
```ini
[Unit]
Description=AI Orchestrator Backend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/backend
ExecStart=/home/lalpha/.../uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend** (`/etc/systemd/system/ai-orchestrator-frontend.service`):
```ini
[Unit]
Description=AI Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=lalpha
WorkingDirectory=/home/lalpha/projets/ai-tools/ai-orchestrator/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3003
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Flux de données

### 1. Authentification

```
Client                    Backend                    Database
  │                          │                          │
  │  POST /auth/login        │                          │
  │  {username, password}    │                          │
  │─────────────────────────>│                          │
  │                          │  SELECT user             │
  │                          │─────────────────────────>│
  │                          │<─────────────────────────│
  │                          │  verify_password()       │
  │                          │  create_access_token()   │
  │  {access_token, user}    │                          │
  │<─────────────────────────│                          │
  │                          │                          │
```

### 2. Chat avec WebSocket

```
Client                    Backend                 ReAct Engine            Ollama
  │                          │                          │                    │
  │  WS Connect              │                          │                    │
  │─────────────────────────>│                          │                    │
  │  WS Message {message}    │                          │                    │
  │─────────────────────────>│                          │                    │
  │                          │  react_engine.run()      │                    │
  │                          │─────────────────────────>│                    │
  │                          │                          │  generate_stream() │
  │                          │                          │───────────────────>│
  │  {type: "token", data}   │                          │<───────────────────│
  │<─────────────────────────│<─────────────────────────│  (tokens)          │
  │  ... (streaming)         │                          │                    │
  │                          │                          │  tool detected     │
  │  {type: "tool", ...}     │                          │                    │
  │<─────────────────────────│<─────────────────────────│                    │
  │                          │                          │  execute tool      │
  │                          │                          │  ...               │
  │  {type: "complete", ...} │                          │                    │
  │<─────────────────────────│<─────────────────────────│                    │
```

---

## Sécurité

### Mesures implémentées

| Couche | Mesure | Description |
|--------|--------|-------------|
| Transport | TLS 1.3 | Chiffrement HTTPS via Traefik |
| Auth | JWT | Tokens signés HS256, expiration 24h |
| Passwords | bcrypt | Hachage avec salt (12 rounds) |
| Input | Pydantic | Validation stricte des entrées |
| CORS | Whitelist | Domaines autorisés uniquement |
| Tools | Sandbox | Timeout sur commandes (30s) |

### Headers de sécurité

```python
# Configurés via Traefik middleware
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

---

## Performance

### Optimisations

1. **Streaming WebSocket** - Réponses progressives, pas d'attente
2. **Connection pooling** - SQLAlchemy session management
3. **Async/await** - I/O non-bloquant partout
4. **Build optimisé** - Vite tree-shaking, minification

### Métriques cibles

| Métrique | Objectif |
|----------|----------|
| TTFB (Time to First Byte) | < 100ms |
| WebSocket latency | < 50ms |
| Tool execution | < 30s (timeout) |
| Memory footprint | < 200MB |

---

## Extensibilité

### Ajouter un nouvel outil

```python
# Dans tools.py
async def mon_nouvel_outil(param1: str, param2: int = 10) -> Dict:
    """Description de l'outil"""
    # Implémentation
    return {"result": "..."}

# Enregistrement
BUILTIN_TOOLS.register(
    name="mon_nouvel_outil",
    func=mon_nouvel_outil,
    description="Description pour le LLM",
    category="custom",
    parameters={"param1": "string", "param2": "int (optionnel)"}
)
```

### Ajouter un provider LLM

```python
# Créer nouveau client dans services/
class NouveauProvider:
    async def generate(self, prompt, model, **kwargs):
        # Implémentation
        pass
    
    async def generate_stream(self, prompt, model, **kwargs):
        # Implémentation streaming
        pass
```
