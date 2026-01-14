# API — v7.1

Cette section documente les endpoints HTTP attendus côté backend. Référence : OpenAPI si disponible.

## Health

`GET /api/v1/system/health`

Recommandé (observabilité) :

```json
{
  "status": "healthy",
  "version": "7.1",
  "execute_mode": "sandbox",
  "sandbox_available": true,
  "verify_required": false
}
```

## Runs / Chat (HTTP)

Selon implémentation, un endpoint HTTP peut exister pour exécuter un run sans WebSocket (mode robuste).

- `POST /api/v1/chat` (exemple)
  - input : message, model, conversation_id
  - output : réponse + preuves

## Tools

Si exposé :
- `GET /api/v1/tools` : liste des outils
- `GET /api/v1/tools/<name>` : schema/params

## Notes

- L’UI ne doit pas “inventer” la vérité : elle doit afficher ce que l’API renvoie.
