# Plan d’audit (template) — v7.1

**But :** audit reproductible, rapide, sans suppositions.

## 0) Préparation
- [ ] Identifier version backend (health) et frontend (UI)
- [ ] Exporter `.env` (sans secrets)
- [ ] Activer logs (30 min)

## 1) Docs → Promesses
- [ ] Sandbox par défaut
- [ ] Fail-closed (pas de fallback direct)
- [ ] VERIFY (strict ou progressif) expliqué
- [ ] WS: `complete`/`error` terminal garanti
- [ ] UI: run inspector + erreurs visibles

## 2) Config
- [ ] EXECUTE_MODE
- [ ] ALLOW_DIRECT_FALLBACK
- [ ] VERIFY_REQUIRED
- [ ] secrets forts

## 3) Backend (preuves)
- [ ] logs WS connect/complete/error
- [ ] audit trail outils
- [ ] sandbox_used observé

## 4) Frontend (preuves)
- [ ] run se clôture
- [ ] erreurs affichées
- [ ] watchdog anti-stuck

## 5) Scénarios E2E
- [ ] uptime
- [ ] list models
- [ ] write_file (doit déclencher VERIFY)
- [ ] commande interdite (doit être bloquée)
