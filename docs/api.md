# API Reference

Base URL: `http://localhost:8001/api/v1`

## Authentication

### POST /auth/login
```json
{ "username": "admin", "password": "password" }
```
Returns JWT token via HttpOnly cookie.

### POST /auth/register
```json
{ "username": "newuser", "password": "password" }
```

### POST /auth/logout
Clears authentication cookie.

## Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /conversations | List all conversations |
| POST | /conversations | Create conversation |
| GET | /conversations/{id} | Get conversation |
| DELETE | /conversations/{id} | Delete conversation |

## Chat

### POST /chat/message
```json
{
  "conversation_id": "uuid",
  "content": "Analyze this file"
}
```
Starts a workflow run. Events streamed via WebSocket.

## Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /agents | List all agents |
| GET | /agents/{id} | Get agent details |
| GET | /agents/capability/{cap} | Filter by capability |
| GET | /agents/{id}/validate/{tool} | Check tool access |

## Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tools | List all tools |
| GET | /tools/{name} | Get tool details |

## System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /system/status | Full system status |
| GET | /system/health | Detailed health with DB status |

## Learning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /learning/feedback | Submit feedback (rating + comment) |
| GET | /learning/feedback | List feedback entries |
| GET | /learning/similar | Find similar conversations |

## WebSocket

```javascript
const ws = new WebSocket(`wss://host/api/ws/${conversationId}?token=${jwt}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // data.type: phase, thinking, tool, verification_item, complete, error
}
```

### Event Types

| Type | Description |
|------|-------------|
| `conversation_created` | New conversation |
| `phase` | Phase transition |
| `thinking` | LLM reasoning step |
| `tool` | Tool execution result |
| `verification_item` | QA verification result |
| `complete` | Run succeeded |
| `error` | Run failed |
