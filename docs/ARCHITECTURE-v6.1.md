# AI Orchestrator v6.1 - Architecture

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
│  POST /chat  │  WS /chat/ws  │  POST /chat/simple               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW ENGINE                               │
│  ┌─────┐  ┌──────┐  ┌─────────┐  ┌────────┐  ┌────────┐        │
│  │SPEC │→│ PLAN │→│ EXECUTE │→│ VERIFY │→│ REPAIR │→ COMPLETE │
│  └─────┘  └──────┘  └─────────┘  └────────┘  └────────┘        │
│                         │              │          │             │
│                         ▼              ▼          │             │
│                   ┌──────────┐  ┌───────────┐    │             │
│                   │  ReAct   │  │  Verifier │◄───┘             │
│                   │  Engine  │  │  Service  │                   │
│                   └──────────┘  └───────────┘                   │
│                         │              │                        │
│           EXECUTOR_MODEL│    VERIFIER_MODEL                     │
│              (qwen2.5)  │    (deepseek)                         │
└─────────────────────────┼──────────────┼────────────────────────┘
                          │              │
                          ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TOOLS (16)                                  │
│  ┌──────────┐ ┌────────────┐ ┌─────────┐ ┌──────┐ ┌──────────┐ │
│  │ system(2)│ │filesystem(4)│ │utility(2)│ │net(1)│ │  qa(7)   │ │
│  └──────────┘ └────────────┘ └─────────┘ └──────┘ └──────────┘ │
│                                                                  │
│  Sécurité: ALLOWLIST → SANDBOX Docker → WORKSPACE isolé         │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Workflow

### 1. SPEC (Spécification)
```python
TaskSpec:
  - objective: str          # Objectif clair
  - assumptions: List[str]  # Hypothèses
  - acceptance: AcceptanceCriteria  # Critères de validation
  - risks: List[str]        # Risques identifiés
  - out_of_scope: List[str] # Hors périmètre
```

### 2. PLAN (Planification)
```python
TaskPlan:
  - steps: List[PlanStep]   # Étapes avec outils
  - estimated_duration_s: int
```

### 3. EXECUTE (Exécution)
- Utilise le ReAct Engine existant
- Boucle Reason→Act→Observe
- Max 10 itérations

### 4. VERIFY (Vérification)
- Exécute outils QA automatiquement
- Génère VerificationReport avec preuves
- Appelle Verifier LLM pour verdict

### 5. REPAIR (Réparation)
- Si verdict = FAIL
- Max 3 cycles de réparation
- Re-vérifie après chaque correction

## Sécurité

### Allowlist (31 commandes autorisées)
```
git, python, python3, pip, pip3, pytest, node, npm, pnpm, npx,
ruff, black, mypy, flake8, uvicorn, alembic, ls, cat, head, tail,
grep, find, wc, echo, date, pwd, env, mkdir, cp, mv, touch
```

### Blocklist (31 commandes interdites)
```
rm, rmdir, mkfs, dd, chmod, chown, wget, curl, ssh, scp, rsync,
sudo, su, passwd, useradd, userdel, systemctl, service, init,
shutdown, reboot, mount, umount, fdisk, parted, iptables, ufw...
```

### Sandbox Docker
```bash
docker run --rm \
  --network=none \
  --read-only \
  --memory=1024m \
  --cpus=1 \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -v $WORKSPACE_DIR:/workspace:rw \
  -w /workspace \
  ubuntu:24.04 \
  bash -lc "$COMMAND"
```

## Outils QA

| Outil | Commande | Timeout |
|-------|----------|---------|
| git_status | `git status --porcelain` | 10s |
| git_diff | `git diff [--staged]` | 30s |
| run_tests | `pytest -q --tb=short` | 120s |
| run_lint | `ruff check .` | 60s |
| run_format | `black --check --diff .` | 60s |
| run_build | `python3 -m py_compile` | 180s |
| run_typecheck | `mypy .` | 120s |

## Configuration

```env
# Modèles
EXECUTOR_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
VERIFIER_MODEL=deepseek-coder:33b

# Workflow
VERIFY_REQUIRED=true
MAX_REPAIR_CYCLES=3

# Sécurité
EXECUTE_MODE=sandbox
WORKSPACE_DIR=/home/lalpha/orchestrator-workspace
```
