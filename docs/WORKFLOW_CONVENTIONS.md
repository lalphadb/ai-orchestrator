# AI Orchestrator - Conventions Workflow v6.2

## Vue d'ensemble

Ce document decrit les conventions utilisees pour le pipeline Workflow et les evenements WebSocket.

## Pipeline Workflow

Le systeme execute un pipeline en 6 phases:

```
SPEC -> PLAN -> EXECUTE -> VERIFY -> REPAIR -> COMPLETE
```

### Phases

| Phase | Description | Modele |
|-------|-------------|--------|
| `spec` | Generation de la specification et criteres d'acceptation | EXECUTOR_MODEL |
| `plan` | Generation du plan d'execution | EXECUTOR_MODEL |
| `execute` | Execution via ReAct Engine | EXECUTOR_MODEL |
| `verify` | Execution des outils QA | N/A (outils) |
| `repair` | Correction des problemes identifies | EXECUTOR_MODEL |
| `complete` | Workflow termine avec succes | N/A |
| `failed` | Workflow termine en echec | N/A |

## Evenements WebSocket

### Format general

```json
{
  "type": "<event_type>",
  "data": { ... },
  "timestamp": "2024-01-08T12:00:00.000Z",
  "run_id": "abc12345"
}
```

### Types d'evenements

#### `phase`
Changement de phase du workflow.

```json
{
  "type": "phase",
  "data": {
    "phase": "verify",
    "status": "in_progress",
    "message": "Verification QA..."
  },
  "run_id": "abc12345"
}
```

#### `thinking`
Reflexion du modele (legacy + enrichi).

```json
{
  "type": "thinking",
  "data": {
    "phase": "execute",
    "message": "Je vais utiliser git_status...",
    "iteration": 3
  }
}
```

#### `tool`
Execution d'un outil.

```json
{
  "type": "tool",
  "data": {
    "tool": "run_tests",
    "params": { "target": "backend" },
    "iteration": 2
  }
}
```

#### `verification_item`
Item de verification QA.

```json
{
  "type": "verification_item",
  "data": {
    "check_name": "run_tests:backend",
    "status": "running" | "passed" | "failed",
    "output": "5 tests passed",
    "error": null
  },
  "run_id": "abc12345"
}
```

#### `complete`
Workflow termine.

```json
{
  "type": "complete",
  "data": {
    "response": "Voici le resultat...",
    "verification": { ... },
    "verdict": {
      "status": "PASS" | "FAIL",
      "confidence": 0.95,
      "issues": [],
      "suggested_fixes": []
    },
    "tools_used": ["git_status", "run_tests"],
    "iterations": 5,
    "duration_ms": 12000,
    "repair_cycles": 0
  }
}
```

#### `error`
Erreur dans le workflow.

```json
{
  "type": "error",
  "data": {
    "message": "Timeout...",
    "phase": "execute"
  }
}
```

## Structure ToolResult

Tous les outils retournent un format uniforme:

```json
{
  "success": true | false,
  "data": { ... } | null,
  "error": {
    "code": "E_FILE_NOT_FOUND",
    "message": "Fichier non trouve: /path/to/file",
    "recoverable": true
  } | null,
  "meta": {
    "duration_ms": 150,
    "command": "...",
    "sandbox": true
  }
}
```

### Codes d'erreur

#### Recuperables (plan B automatique)
- `E_FILE_NOT_FOUND`: Fichier non trouve -> tente search_files
- `E_DIR_NOT_FOUND`: Repertoire non trouve -> tente search_directory
- `E_PATH_NOT_FOUND`: Chemin non trouve

#### Non-recuperables
- `E_PERMISSION`: Permission refusee
- `E_CMD_NOT_ALLOWED`: Commande non autorisee
- `E_PATH_FORBIDDEN`: Chemin hors workspace
- `E_WRITE_DISABLED`: Ecriture desactivee

## Verdict et Verification

### VerificationReport

```json
{
  "passed": true,
  "checks_run": ["run_tests:backend", "run_lint:backend"],
  "results": [
    {
      "name": "run_tests:backend",
      "passed": true,
      "output": "5 tests passed",
      "error": null
    }
  ],
  "evidence": {
    "run_tests:backend": { "stdout": "...", "returncode": 0 }
  },
  "failures": [],
  "duration_ms": 5000
}
```

### JudgeVerdict

```json
{
  "status": "PASS" | "FAIL",
  "confidence": 0.95,
  "issues": ["Test X echoue", "Lint errors"],
  "suggested_fixes": ["Corriger la fonction Y"],
  "reasoning": "Tous les tests passent..."
}
```

## Outil search_directory

Nouvel outil pour recuperation automatique sur E_DIR_NOT_FOUND.

### Securite

- **Bases allowlistees**: /home, /workspace, /tmp, /var/www, /opt, WORKSPACE_DIR
- **Profondeur max**: 3
- **Resultats max**: 5

### Parametres

```json
{
  "name": "backend",          // Nom a chercher (exact ou partiel)
  "base": "/home/user",       // Base de recherche (optionnel)
  "max_depth": 3              // Profondeur max (optionnel, max=3)
}
```

### Reponse

```json
{
  "success": true,
  "data": {
    "query": "backend",
    "base": "/home/user",
    "max_depth": 3,
    "matches": [
      { "path": "/home/user/projects/backend", "name": "backend", "depth": 2 }
    ],
    "count": 1,
    "suggestion": "/home/user/projects/backend"
  }
}
```

## Configuration

### Variables d'environnement

| Variable | Description | Defaut |
|----------|-------------|--------|
| `EXECUTOR_MODEL` | Modele pour execution | kimi-k2:1t-cloud |
| `VERIFIER_MODEL` | Modele pour verification | deepseek-coder:33b |
| `MAX_ITERATIONS` | Iterations max ReAct | 10 |
| `MAX_REPAIR_CYCLES` | Cycles repair max | 3 |
| `VERIFY_REQUIRED` | Verification obligatoire | true |
| `EXECUTE_MODE` | Mode execution (sandbox/direct) | direct |
| `WORKSPACE_DIR` | Repertoire de travail | /home/lalpha/orchestrator-workspace |

## Actions Frontend

### Re-verify
Relance uniquement la verification QA sans re-executer.

### Force Repair
Force un cycle de reparation meme si le verdict est PASS.

### Export Report
Exporte le rapport de run complet en JSON.
