# BASELINE — Phase 0
**Date:** 2026-01-11 10:51
**Objectif:** Établir une baseline avant corrections v7.0

---

## 1. Configuration sauvegardée

### Fichiers copiés:
- ✅ `backend/.env` → `.env.baseline`
- ✅ `backend/app/core/config.py` → `config.py.baseline`

### Configuration actuelle (.env):
```
APP_VERSION=7.0
EXECUTE_MODE=direct         # ← Mode direct (pas sandbox)
VERIFY_REQUIRED=false       # ← QA désactivée
JWT_SECRET_KEY=your-secret-key-change-in-production  # ← Secret par défaut
ADMIN_PASSWORD=admin123     # ← Password faible
```

---

## 2. État du service

### Service systemd:
```bash
systemctl is-active ai-orchestrator
# Résultat: active ✅
```

### Health endpoint:
```bash
curl http://localhost:8001/api/v1/system/health
# Résultat: {"status":"healthy","version":"7.0"} ✅
```

### Docker disponibilité:
```bash
docker --version
# Résultat: Docker version 28.2.2, build 2a0ec1a ✅
# DOCKER_AVAILABLE=true
```

---

## 3. Smoke tests baseline

### Test 1: Health check
**Commande:** `curl http://localhost:8001/api/v1/system/health`
**Résultat:** ✅ SUCCESS
**Réponse:** `{"status":"healthy","version":"7.0"}`

### Test 2: Service actif
**Commande:** `systemctl is-active ai-orchestrator`
**Résultat:** ✅ SUCCESS
**Status:** `active`

### Test 3: Docker disponible
**Commande:** `docker --version`
**Résultat:** ✅ SUCCESS
**Version:** Docker 28.2.2

---

## 4. État initial vérifié

| Composant | État | Notes |
|-----------|------|-------|
| Service AI Orchestrator | ✅ Running | systemd active |
| Health endpoint | ✅ OK | Port 8001 accessible |
| Docker | ✅ Disponible | Version 28.2.2 |
| Mode exécution | ⚠️ direct | Devrait être sandbox |
| QA Verification | ⚠️ disabled | VERIFY_REQUIRED=false |
| Secrets | ⚠️ default | JWT + admin password |

---

## 5. Capacité de rollback

**Rollback possible via:**
```bash
# Restaurer .env original
cp audits/changesets/20260111_1051/.env.baseline backend/.env

# Restaurer config.py original
cp audits/changesets/20260111_1051/config.py.baseline backend/app/core/config.py

# Redémarrer service
sudo systemctl restart ai-orchestrator
```

---

## 6. Prochaine étape

✅ Baseline établie et validée
→ Prêt pour **PHASE 1.1**: Activer mode sandbox

**Critères de succès Phase 1.1:**
- EXECUTE_MODE=sandbox dans .env
- Vérification docker disponible
- Service redémarre sans erreur
- Health endpoint répond
- Smoke tests passent
