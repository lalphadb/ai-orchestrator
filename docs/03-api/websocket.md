# API WebSocket

## Connexion

```javascript
const ws = new WebSocket(`wss://api/ws/${conversationId}?token=${jwt}`)
```

## Events v8

Tous les events suivent ce format:

```typescript
interface V8Event {
  type: string;        // Type d'event
  timestamp: string;   // ISO timestamp
  run_id: string;      // Identifiant du run
  data?: any;          // Payload spécifique
}
```

### Types d'events

| Type | Description |
|------|-------------|
| `conversation_created` | Nouvelle conversation |
| `phase` | Transition de phase (SPEC/PLAN/EXECUTE/VERIFY/REPAIR) |
| `thinking` | Étape de raisonnement LLM |
| `tool` | Résultat d'exécution d'outil |
| `verification_item` | Résultat de vérification QA |
| `complete` | Run terminé avec succès |
| `error` | Run terminé en erreur |

### Invariants

1. Chaque run émet exactement UN `complete` OU `error`
2. Aucun run ne reste en état `RUNNING` après event terminal
3. Les events sont append-only

## Exemple client

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  switch (data.type) {
    case 'phase':
      console.log(`Phase: ${data.data.phase}`)
      break
    case 'tool':
      console.log(`Tool: ${data.data.tool_name} - ${data.data.success}`)
      break
    case 'complete':
      console.log('Run terminé:', data.data.response)
      break
    case 'error':
      console.error('Erreur:', data.data.message)
      break
  }
}
```
