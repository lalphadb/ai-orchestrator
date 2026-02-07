# API REST

Base URL: `http://localhost:8000/api/v1`

## Authentification

### POST /auth/login

```json
{
  "username": "admin",
  "password": "password"
}
```

Réponse:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Conversations

### GET /conversations
Liste toutes les conversations.

### POST /conversations
Crée une nouvelle conversation.

### GET /conversations/{id}
Récupère une conversation par ID.

### DELETE /conversations/{id}
Supprime une conversation.

## Chat

### POST /chat/message
Envoie un message (déclenche un run).

```json
{
  "conversation_id": "uuid",
  "content": "Analyse ce fichier"
}
```

## Agents (v8)

### GET /agents
Liste tous les agents enregistrés.

### GET /agents/{id}
Récupère un agent par ID.

### GET /agents/capability/{capability}
Filtre les agents par capacité.

### GET /agents/{id}/validate/{tool}
Vérifie si un agent peut utiliser un outil.

## Tools

### GET /tools
Liste tous les outils disponibles.

### GET /tools/{name}
Récupère les détails d'un outil.

## System

### GET /health
Vérifie la santé de l'API.

### GET /system/status
État complet du système.
