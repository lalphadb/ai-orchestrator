# Configuration — v7.1

Ce guide décrit les variables `.env` importantes. Les noms exacts peuvent varier selon le code, mais **les invariants doivent rester audités**.

## Emplacement

- Backend : `backend/.env`

## Variables clés

### Modèles
- `DEFAULT_MODEL`
- `EXECUTOR_MODEL` (si séparation)

### Workflow
- `MAX_ITERATIONS`
- `MAX_REPAIR_CYCLES`
- `VERIFY_REQUIRED`
  - Recommandation : documenter clairement la sémantique :
    - `VERIFY_REQUIRED=true` : VERIFY global (strict)
    - `false` : VERIFY progressif (selon action)

### Exécution
- `EXECUTE_MODE` : `sandbox` | `direct`
- `ALLOW_DIRECT_FALLBACK` : `false` en prod
- Paramètres sandbox (si présents) : image, CPU, mémoire, network none

### Sécurité
- `JWT_SECRET_KEY`
- `ADMIN_PASSWORD`

## Checklist config (prod)

- [ ] `EXECUTE_MODE=sandbox`
- [ ] `ALLOW_DIRECT_FALLBACK=false`
- [ ] `JWT_SECRET_KEY` fort
- [ ] `ADMIN_PASSWORD` fort
- [ ] Docker présent et fonctionnel
