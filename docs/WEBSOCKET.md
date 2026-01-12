# WebSocket Streaming

Documentation complète du système de streaming WebSocket temps réel.

---

## Vue d'ensemble

AI Orchestrator v7.0 utilise WebSocket pour le streaming des réponses token par token, offrant une expérience similaire à ChatGPT.

```
┌─────────────┐                    ┌─────────────┐
│   Client    │◄───WebSocket───────│   Backend   │
│  (Browser)  │    bidirectionnel  │  (FastAPI)  │
└─────────────┘                    └──────┬──────┘
                                          │
                                   ┌──────▼──────┐
                                   │ ReAct Engine│
                                   │  + Ollama   │
                                   └─────────────┘
```

---

## Connexion

### URL

| Environnement | URL |
|---------------|-----|
| Production | `wss://ai.4lb.ca/api/v1/chat/ws` |
| Développement | `ws://localhost:8001/api/v1/chat/ws` |

### Authentification

Le WebSocket n'utilise pas de token dans les headers (limitation navigateur). L'authentification se fait via le premier message ou cookies.

---

## Protocole

### Messages Client → Serveur

**Envoyer un message:**
```json
{
  "message": "Quelle heure est-il?",
  "conversation_id": "uuid (optionnel)",
  "model": "qwen2.5-coder:32b-instruct-q4_K_M (optionnel)"
}
```

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `message` | string | ✅ | Message utilisateur |
| `conversation_id` | string | ❌ | UUID conversation existante |
| `model` | string | ❌ | Modèle Ollama à utiliser |

### Messages Serveur → Client

Tous les messages suivent ce format:
```json
{
  "type": "token|thinking|tool|phase|verification_item|complete|error",
  "data": "...",
  "timestamp": "2026-01-08T14:30:00.000Z",
  "run_id": "abc12345"
}
```

---

## run_id - Traçabilité v7.0

**Obligatoire depuis v7.0:** Chaque événement WebSocket contient un champ `run_id` pour traçabilité complète.

```json
{
  "type": "...",
  "data": {...},
  "timestamp": "2026-01-08T14:30:00.000Z",
  "run_id": "abc12345"  // ← Toujours présent
}
```

**Format:** 8 caractères alphanumériques (UUIDv4 tronqué)

**Utilisation:**
- Corréler tous les événements d'un même workflow
- Rechercher dans les logs: `grep "abc12345" audit.log`
- API: `GET /api/v1/runs/abc12345`

---

## Événements minimum (v7.0)

Pour une implémentation conforme, le client **doit** gérer ces événements:

| Type | Obligatoire | Description |
|------|-------------|-------------|
| `phase` | ✅ | Changement de phase workflow |
| `tool` | ✅ | Exécution d'outil (avec run_id) |
| `verification_item` | ✅ | Résultat check QA |
| `complete` | ✅ | Fin du workflow avec verdict |
| `error` | ✅ | Erreur fatale |
| `token` | ❌ | Streaming (optionnel) |
| `thinking` | ❌ | Debug (optionnel) |

**Séquence typique v7.0:**
```
phase(spec) → phase(plan) → phase(execute) → tool(...) → 
phase(verify) → verification_item(...) → complete
```

---

## Types de messages

### 1. `conversation_created`

Envoyé au début si nouvelle conversation.

```json
{
  "type": "conversation_created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2026-01-08T14:30:00.000Z"
}
```

### 2. `thinking`

L'IA analyse la demande.

```json
{
  "type": "thinking",
  "data": {
    "message": "Analyse...",
    "iteration": 0
  },
  "timestamp": "2026-01-08T14:30:00.000Z"
}
```

### 3. `token`

Un token de la réponse (streaming).

```json
{
  "type": "token",
  "data": "Il",
  "timestamp": "2026-01-08T14:30:00.100Z"
}
```

Les tokens arrivent un par un et doivent être concaténés côté client.

### 4. `tool`

Un outil est en cours d'exécution.

```json
{
  "type": "tool",
  "data": {
    "tool": "get_datetime",
    "params": {},
    "iteration": 1
  },
  "timestamp": "2026-01-08T14:30:01.000Z",
  "run_id": "abc12345"
}
```

### 5. `phase` (v6.2)

Changement de phase du workflow.

```json
{
  "type": "phase",
  "data": {
    "phase": "verify",
    "status": "in_progress",
    "message": "Vérification QA..."
  },
  "timestamp": "2026-01-08T14:30:02.000Z",
  "run_id": "abc12345"
}
```

**Phases possibles:**
- `spec` - Génération de la spécification
- `plan` - Génération du plan d'exécution
- `execute` - Exécution via ReAct Engine
- `verify` - Exécution des outils QA
- `repair` - Correction des problèmes identifiés
- `complete` - Workflow terminé avec succès
- `failed` - Workflow terminé en échec

### 6. `verification_item` (v6.2)

Item de vérification QA.

```json
{
  "type": "verification_item",
  "data": {
    "check_name": "run_tests:backend",
    "status": "running",
    "output": null,
    "error": null
  },
  "timestamp": "2026-01-08T14:30:02.500Z",
  "run_id": "abc12345"
}
```

**Statuts possibles:**
- `running` - Check en cours
- `passed` - Check réussi
- `failed` - Check échoué

### 7. `complete`

Réponse terminée avec métadonnées.

```json
{
  "type": "complete",
  "data": {
    "response": "Il est actuellement 14h30.",
    "tools_used": ["get_datetime"],
    "iterations": 2,
    "duration_ms": 3500,
    "verification": {
      "passed": true,
      "checks_run": ["run_tests:backend", "run_lint:backend"],
      "results": [
        {"name": "run_tests:backend", "passed": true, "output": "5 tests passed"}
      ],
      "failures": []
    },
    "verdict": {
      "status": "PASS",
      "confidence": 0.95,
      "issues": [],
      "suggested_fixes": []
    },
    "repair_cycles": 0
  },
  "timestamp": "2026-01-08T14:30:03.500Z",
  "run_id": "abc12345"
}
```

### 8. `error`

Une erreur s'est produite.

```json
{
  "type": "error",
  "data": "Ollama non disponible",
  "timestamp": "2026-01-08T14:30:00.000Z"
}
```

---

## Implémentation client

### JavaScript (Browser)

```javascript
class AIWebSocket {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.messageCallback = null;
    this.reconnectAttempts = 0;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connecté');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('❌ WebSocket déconnecté');
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'conversation_created':
        console.log('Conversation:', data.data.id);
        break;

      case 'thinking':
        this.showStatus('🤔 ' + data.data.message);
        break;

      case 'token':
        this.appendToken(data.data);
        break;

      case 'tool':
        this.showStatus('🔧 ' + data.data.tool);
        break;

      case 'complete':
        this.onComplete(data.data);
        break;

      case 'error':
        this.showError(data.data);
        break;
    }
  }

  send(message, conversationId = null, model = null) {
    if (this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket non connecté');
    }

    this.ws.send(JSON.stringify({
      message,
      conversation_id: conversationId,
      model
    }));
  }

  reconnect() {
    if (this.reconnectAttempts < 5) {
      this.reconnectAttempts++;
      console.log(`Reconnexion ${this.reconnectAttempts}/5...`);
      setTimeout(() => this.connect(), 3000);
    }
  }

  // Méthodes à implémenter selon l'UI
  showStatus(status) { console.log(status); }
  appendToken(token) { process.stdout.write(token); }
  onComplete(data) { console.log('\n✅ Terminé'); }
  showError(error) { console.error('❌', error); }
}

// Utilisation
const ai = new AIWebSocket('wss://ai.4lb.ca/api/v1/chat/ws');
ai.connect();
ai.send('Bonjour!');
```

### Python (asyncio)

```python
import asyncio
import websockets
import json

class AIWebSocket:
    def __init__(self, url: str):
        self.url = url
        self.ws = None
        self.response_buffer = ""

    async def connect(self):
        self.ws = await websockets.connect(self.url)
        print("✅ Connecté")

    async def send(self, message: str, conversation_id: str = None):
        await self.ws.send(json.dumps({
            "message": message,
            "conversation_id": conversation_id
        }))

    async def receive(self):
        while True:
            response = await self.ws.recv()
            data = json.loads(response)

            if data["type"] == "token":
                print(data["data"], end="", flush=True)
                self.response_buffer += data["data"]

            elif data["type"] == "thinking":
                print(f"\n🤔 {data['data']['message']}")

            elif data["type"] == "tool":
                print(f"\n🔧 {data['data']['tool']}")

            elif data["type"] == "complete":
                print(f"\n✅ Terminé en {data['data']['duration_ms']}ms")
                return data["data"]

            elif data["type"] == "error":
                print(f"\n❌ Erreur: {data['data']}")
                return None

    async def chat(self, message: str):
        self.response_buffer = ""
        await self.send(message)
        return await self.receive()

    async def close(self):
        await self.ws.close()


async def main():
    ai = AIWebSocket("wss://ai.4lb.ca/api/v1/chat/ws")
    await ai.connect()

    result = await ai.chat("Quelle heure est-il?")
    print(f"\nRéponse: {result['response']}")

    await ai.close()

asyncio.run(main())
```

### Vue.js (Pinia Store)

```javascript
// stores/chat.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const currentTool = ref(null)

  let ws = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/chat/ws`)

    ws.onopen = () => { isConnected.value = true }
    ws.onclose = () => {
      isConnected.value = false
      setTimeout(connect, 3000)
    }
    ws.onmessage = (event) => handleMessage(JSON.parse(event.data))
  }

  function handleMessage(data) {
    switch (data.type) {
      case 'token':
        streamingContent.value += data.data
        break
      case 'tool':
        currentTool.value = data.data.tool
        break
      case 'complete':
        finishMessage(data.data)
        break
    }
  }

  function sendMessage(content) {
    messages.value.push({ role: 'user', content })
    messages.value.push({ role: 'assistant', content: '', streaming: true })
    streamingContent.value = ''
    isStreaming.value = true

    ws.send(JSON.stringify({ message: content }))
  }

  function finishMessage(data) {
    const lastMsg = messages.value[messages.value.length - 1]
    lastMsg.content = data.response
    lastMsg.streaming = false
    lastMsg.tools_used = data.tools_used
    isStreaming.value = false
    currentTool.value = null
  }

  return {
    messages, isConnected, isStreaming, streamingContent,
    currentTool, connect, sendMessage
  }
})
```

---

## Gestion des erreurs

### Reconnexion automatique

```javascript
let reconnectAttempts = 0;
const maxAttempts = 5;
const baseDelay = 1000;

function reconnect() {
  if (reconnectAttempts >= maxAttempts) {
    console.error('Échec de reconnexion');
    return;
  }

  const delay = baseDelay * Math.pow(2, reconnectAttempts);
  reconnectAttempts++;

  console.log(`Reconnexion dans ${delay}ms...`);
  setTimeout(connect, delay);
}
```

### Timeout

```javascript
function sendWithTimeout(message, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error('Timeout'));
    }, timeout);

    // Attendre le message 'complete'
    const handler = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'complete') {
        clearTimeout(timer);
        ws.removeEventListener('message', handler);
        resolve(data.data);
      }
    };

    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ message }));
  });
}
```

---

## Performance

### Optimisations

1. **Compression WebSocket** - Activée côté serveur
2. **Heartbeat** - Ping/pong toutes les 30s
3. **Buffer tokens** - Regrouper les tokens courts
4. **Déconnexion propre** - Fermer avec code 1000

### Métriques

| Métrique | Valeur typique |
|----------|----------------|
| Latence token | < 50ms |
| Temps connexion | < 100ms |
| Overhead message | ~50 bytes |
