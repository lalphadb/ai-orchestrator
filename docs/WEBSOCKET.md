# WebSocket — v7.1

## Objectif

Diffuser des **événements de workflow**, pas seulement des tokens.

## Connexion

`WS /api/v1/chat/ws` (exemple)

Le client envoie (exemple) :

```json
{
  "message": "uptime du serveur??",
  "conversation_id": null,
  "model": null,
  "stream": true
}
```

## Événements attendus

Tous les événements doivent inclure :
- `type`
- `timestamp`
- un identifiant de corrélation : `run_id` et/ou `conversation_id`

Types usuels :
- `conversation_created`
- `phase` (spec/plan/execute/verify/repair)
- `thinking`
- `token` (optionnel)
- `tool` (outil déclenché + params)
- `complete` (terminal)
- `error` (terminal)

## Invariant terminal

Chaque run doit finir par **exactement un** événement terminal :
- `complete` ou
- `error`

L’UI doit aussi avoir un watchdog anti‑stuck (si aucun event pendant X secondes → FAILED + message).
