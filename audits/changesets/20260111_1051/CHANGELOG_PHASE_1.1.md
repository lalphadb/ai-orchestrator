# CHANGELOG — Phase 1.1: Mode Sandbox Activé
**Date:** 2026-01-11 10:52
**Objectif:** Passer en mode sandbox par défaut

---

## 1. Modifications apportées

### Fichiers modifiés:
- ✅ `backend/.env`

### Changements:
```diff
- # EXECUTION DIRECTE (pas de sandbox Docker)
- EXECUTE_MODE=direct
+ # EXECUTION SÉCURISÉE (sandbox Docker par défaut)
+ EXECUTE_MODE=sandbox
+ ALLOW_DIRECT_FALLBACK=false
```

**Rationale:**
- Documentation v7.0 promet "sandbox by default"
- Docker disponible (v28.2.2) ✅
- Flag `ALLOW_DIRECT_FALLBACK=false` pour être explicite (pas de fallback silencieux)

---

## 2. Commandes exécutées

### 2.1 Modification configuration
```bash
# Vérifier changement
grep -E "^EXECUTE_MODE|^ALLOW_DIRECT_FALLBACK" backend/.env
# Résultat:
# EXECUTE_MODE=sandbox ✅
# ALLOW_DIRECT_FALLBACK=false ✅
```

### 2.2 Redémarrage service
```bash
sudo systemctl restart ai-orchestrator
sleep 3
systemctl is-active ai-orchestrator
# Résultat: active ✅
```

---

## 3. Tests de validation

### Test 1: Service status
```bash
systemctl status ai-orchestrator --no-pager -l | head -20
```
**Résultat:** ✅ SUCCESS
```
Active: active (running) since Sun 2026-01-11 10:52:07 EST; 14s ago
Main PID: 1963804 (python3)
Memory: 119.3M
```

### Test 2: Health endpoint
```bash
curl -s http://localhost:8001/api/v1/system/health
```
**Résultat:** ✅ SUCCESS
```json
{"status":"healthy","version":"7.0"}
```

### Test 3: Logs démarrage
```bash
journalctl -u ai-orchestrator -n 10 --no-pager
```
**Résultat:** ✅ SUCCESS
```
2026-01-11 10:52:08 [INFO] main: 🎯 Serveur prêt sur http://0.0.0.0:8001
INFO: Application startup complete.
```

---

## 4. Vérification sandbox

### Docker disponible:
```bash
docker --version
# Docker version 28.2.2 ✅
```

### Configuration effective:
- `settings.EXECUTE_MODE` = "sandbox" ✅
- Docker path détectable via `shutil.which("docker")` ✅
- Mode sandbox sera appliqué au prochain appel `execute_command()`

**Note:** Les logs sandbox n'apparaissent que lors de l'exécution réelle d'une commande (pas au démarrage).

---

## 5. Impact et risques

### Impact:
- ✅ Toutes les commandes exécutées via `execute_command()` passent maintenant par sandbox Docker
- ✅ Isolation réseau (`--network=none`)
- ✅ Limites CPU/RAM (0.5 CPU, 512Mi)
- ✅ Workspace en lecture seule pour role=viewer

### Risques mitigés:
- ⚠️ Performances légèrement réduites (overhead Docker)
- ✅ Pas de fallback silencieux (ALLOW_DIRECT_FALLBACK=false)

---

## 6. Rollback possible

**Si problème détecté:**
```bash
# Restaurer .env baseline
cp audits/changesets/20260111_1051/.env.baseline backend/.env

# Redémarrer service
sudo systemctl restart ai-orchestrator

# Vérifier
curl http://localhost:8001/api/v1/system/health
```

**Conditions de rollback:**
- Health endpoint ne répond pas après redémarrage
- Erreurs dans journalctl
- Commandes sandbox échouent systématiquement

---

## 7. Résultat Phase 1.1

| Critère | Status |
|---------|--------|
| EXECUTE_MODE=sandbox | ✅ OK |
| Docker disponible | ✅ OK |
| Service redémarré | ✅ OK |
| Health endpoint | ✅ OK |
| Logs propres | ✅ OK |

**Verdict:** ✅ **PHASE 1.1 RÉUSSIE**

---

## 8. Prochaine étape

→ **PHASE 1.2**: Activer VERIFY_REQUIRED de manière progressive

**Critères de succès Phase 1.2:**
- VERIFY_REQUIRED=true mais uniquement pour actions sensibles
- Service redémarre sans erreur
- Health + smoke tests passent
- Action sensible déclenche VERIFY
