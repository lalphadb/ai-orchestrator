# Troubleshooting — v7.1

## Run bloqué “RUNNING” dans l’UI

1. Vérifier WS frames (DevTools → Network → WS)
2. Vérifier logs backend (`journalctl`)
3. Vérifier que le backend a été redémarré après update
4. Vérifier mismatch versions (UI affiche ancienne version)

## Sandbox non utilisée

- Vérifier `.env` : `EXECUTE_MODE=sandbox`
- Vérifier Docker OK : `docker info`
- Vérifier qu’un log/audit indique `sandbox_used=true` (si instrumenté)

## Aucune réponse ou réponses lentes (v7.0)

Symptômes:
- Les requêtes simples comme "uptime du serveur?" restent bloquées.
- Le système passe systématiquement par SPEC/PLAN, entraînant des délais.

Correctif appliqué:
- Détection des requêtes simples renforcée dans backend/app/services/react_engine/workflow_engine.py.
- Les questions (avec `?` ou mots interrogatifs) passent en mode rapide.
- Les commandes d'action ("crée", "modifie", "supprime", "install", "update", "create"…) restent complexes (SPEC/PLAN).

Vérifications rapides:
- Santé: GET /api/v1/system/health → 200
- Modèles: GET /api/v1/system/models → état d'Ollama
- Chat: POST /api/v1/chat avec { "message": "uptime du serveur?" } → réponse rapide

Pré-requis:
- Ollama disponible sur http://localhost:11434 (configurable dans app/core/config.py).
- Backend lancé sur le port configuré (8001 par défaut).
