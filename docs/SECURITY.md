# Sécurité — v7.1

## Posture

- **Fail‑closed** par défaut.
- Exécution outillée **sans interprétation shell** (argv strict).
- **Allowlist** de commandes et permissions par rôles.
- **Sandbox Docker** quand `EXECUTE_MODE=sandbox` (recommandé en production).
- Traçabilité systématique (audit entries).

## Paramètres essentiels (.env)

- `EXECUTE_MODE`: `sandbox` (prod) ou `direct` (dev contrôlé)
- `ALLOW_DIRECT_FALLBACK`: `false` en prod
- `JWT_SECRET_KEY`: secret fort (≥ 256 bits)
- `ADMIN_PASSWORD`: long, unique, stocké de façon sûre

## Exigences “prod ready”

- Si `EXECUTE_MODE=sandbox` et Docker absent/KO → **refuser l’exécution** (pas de fallback direct).
- Les commandes sensibles (admin) nécessitent justification et passent par gouvernance.
- Les outils d’écriture (write_file/build) doivent déclencher VERIFY (au minimum progressif).

## Vérification posture (script)

Voir `AUDIT/scripts/check_security_posture.sh` (fourni dans ce zip). Il doit échouer si :
- sandbox requise mais indisponible
- fallback direct autorisé en prod
- secrets faibles
