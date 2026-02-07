# Sécurité

## Principes

AI Orchestrator suit une posture "fail-closed":
- Mode sandbox par défaut
- Validation obligatoire des entrées
- Restrictions d'outils par agent

## Protection SSRF

Toutes les requêtes HTTP sont filtrées:

```python
# IPs bloquées
- 127.0.0.0/8      # Localhost
- 10.0.0.0/8       # Privé classe A
- 172.16.0.0/12    # Privé classe B
- 192.168.0.0/16   # Privé classe C
- 169.254.0.0/16   # Link-local
```

## Authentification

- JWT avec expiration configurable
- Tokens rafraîchis automatiquement
- WebSocket authentifié via query param

## Agents et Tools

Chaque agent a une liste blanche d'outils:

| Agent | Outils autorisés |
|-------|------------------|
| web.researcher | web_search, web_read |
| system.health | read_file, list_directory, bash |
| self_improve | read_file, write_file, patch_file, run_tests, git_* |

## Mode Sandbox

En mode sandbox (`SANDBOX_MODE=true`):
- Commandes bash limitées
- Pas d'accès réseau direct
- Écriture restreinte

## Audit

Toutes les actions sont journalisées:
- Exécutions d'outils
- Modifications de fichiers
- Erreurs de sécurité

Voir `audits/AUDIT_SECURITE_2026-01-27.md` pour le dernier audit.
