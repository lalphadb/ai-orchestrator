# Tool Regression Test Suite

Pack de tests de régression pour les outils intégrés d'AI Orchestrator.

## Objectif

Garantir que les 10 outils les plus critiques respectent leurs contrats I/O et gèrent correctement les cas d'erreur.

## Outils testés (Top 10)

| # | Outil | Catégorie | Priorité | Tests |
|---|-------|-----------|----------|-------|
| 1 | `read_file` | filesystem | CRITICAL | 6 scénarios |
| 2 | `write_file` | filesystem | CRITICAL | 6 scénarios |
| 3 | `list_directory` | filesystem | HIGH | 5 scénarios |
| 4 | `search_files` | filesystem | HIGH | 4 scénarios |
| 5 | `execute_command` | system | CRITICAL | 7 scénarios |
| 6 | `git_status` | qa | HIGH | 3 scénarios |
| 7 | `git_diff` | qa | HIGH | 3 scénarios |
| 8 | `run_tests` | qa | MEDIUM | 3 scénarios |
| 9 | `http_request` | network | HIGH | 5 scénarios |
| 10 | `list_llm_models` | system | MEDIUM | 3 scénarios |

**Total**: 45 scénarios de test

## Contrats I/O

Tous les outils respectent le contrat standardisé:

```python
{
  "success": bool,         # True si l'opération a réussi
  "data": dict | None,     # Données retournées (si success=True)
  "error": {               # Détails de l'erreur (si success=False)
    "code": str,           # Code d'erreur (E_FILE_NOT_FOUND, E_PERMISSION, etc.)
    "message": str,        # Message d'erreur lisible
    "recoverable": bool    # True si l'erreur peut être récupérée automatiquement
  } | None,
  "meta": {                # Métadonnées d'exécution
    "duration_ms": int,    # Durée d'exécution
    "command": str,        # Commande exécutée (pour execute_command)
    "sandbox": bool        # Si exécuté dans sandbox (pour execute_command)
  }
}
```

### Codes d'erreur standardisés

| Code | Recoverable | Description |
|------|-------------|-------------|
| `E_FILE_NOT_FOUND` | ✅ Yes | Fichier introuvable (peut chercher alternatives) |
| `E_DIR_NOT_FOUND` | ✅ Yes | Répertoire introuvable |
| `E_PATH_NOT_FOUND` | ✅ Yes | Chemin générique introuvable |
| `E_PERMISSION` | ❌ No | Permission refusée |
| `E_CMD_NOT_ALLOWED` | ❌ No | Commande non autorisée |
| `E_PATH_FORBIDDEN` | ❌ No | Accès à un chemin interdit |
| `E_NETWORK_ERROR` | ⚠️ Maybe | Erreur réseau (timeout, DNS, etc.) |
| `E_VALIDATION` | ❌ No | Validation des paramètres échouée |
| `E_EXECUTION` | ❌ No | Erreur d'exécution générique |

## Structure des tests

```
tool_regression/
├── README.md                    # Ce fichier
├── conftest.py                  # Fixtures communes + mode mock
├── contracts.py                 # Définition des contrats I/O
├── test_filesystem_tools.py     # read_file, write_file, list_directory, search_files
├── test_system_tools.py         # execute_command, list_llm_models
├── test_qa_tools.py             # git_status, git_diff, run_tests
└── test_network_tools.py        # http_request
```

## Exécution des tests

### Tous les tests de régression
```bash
cd backend
.venv/bin/python -m pytest tests/tool_regression/ -v
```

### Par catégorie
```bash
# Filesystem
pytest tests/tool_regression/test_filesystem_tools.py -v

# System
pytest tests/tool_regression/test_system_tools.py -v

# QA
pytest tests/tool_regression/test_qa_tools.py -v

# Network
pytest tests/tool_regression/test_network_tools.py -v
```

### Test spécifique
```bash
pytest tests/tool_regression/test_filesystem_tools.py::test_read_file_success -v
```

### Avec coverage
```bash
pytest tests/tool_regression/ --cov=app.services.react_engine.tools --cov-report=html
```

## Mode Mock

Les tests utilisent des mocks pour les dépendances externes:

- **Ollama**: Réponses mockées pour `list_llm_models`
- **HTTP**: Requêtes mockées pour `http_request`
- **Git**: Commandes git mockées si pas de repo

Configuration via `conftest.py`:

```python
@pytest.fixture
def mock_ollama(monkeypatch):
    """Mock Ollama API responses"""
    # ... configuration
```

## Scénarios de test par outil

### 1. read_file (6 scénarios)
- ✅ Lecture fichier existant dans workspace
- ✅ Lecture fichier avec encodage spécial (UTF-8, Latin-1)
- ❌ Fichier inexistant → `E_FILE_NOT_FOUND` (recoverable)
- ❌ Chemin hors workspace → `E_PATH_FORBIDDEN`
- ❌ Path traversal (..) → `E_PATH_FORBIDDEN`
- ❌ Permission refusée → `E_PERMISSION`

### 2. write_file (6 scénarios)
- ✅ Écriture fichier nouveau dans workspace
- ✅ Écrasement fichier existant
- ✅ Création répertoires parents (mkdir -p)
- ❌ Chemin hors workspace → `E_PATH_FORBIDDEN`
- ❌ Path traversal → `E_PATH_FORBIDDEN`
- ❌ Répertoire parent introuvable → `E_DIR_NOT_FOUND` (recoverable)

### 3. list_directory (5 scénarios)
- ✅ Liste répertoire workspace
- ✅ Liste répertoire vide
- ✅ Liste avec filtres (*.py)
- ❌ Répertoire inexistant → `E_DIR_NOT_FOUND` (recoverable)
- ❌ Chemin hors workspace → `E_PATH_FORBIDDEN`

### 4. search_files (4 scénarios)
- ✅ Recherche par pattern (*.py)
- ✅ Recherche récursive
- ✅ Aucun fichier trouvé (succès avec data vide)
- ❌ Pattern invalide → `E_VALIDATION`

### 5. execute_command (7 scénarios)
- ✅ Commande allowlist (ls, pwd)
- ✅ Commande avec arguments
- ✅ Mode sandbox vs operator
- ❌ Commande blocklist (rm -rf /) → `E_CMD_NOT_ALLOWED`
- ❌ Dangerous pattern ($(curl)) → `E_CMD_NOT_ALLOWED`
- ❌ Admin tool sans permission → `E_PERMISSION`
- ❌ Timeout dépassé → `E_EXECUTION`

### 6. git_status (3 scénarios)
- ✅ Workspace avec git repo
- ✅ Fichiers modifiés détectés
- ⚠️ Pas de repo git (fallback gracieux)

### 7. git_diff (3 scénarios)
- ✅ Diff fichiers modifiés
- ✅ Aucune modification (sortie vide)
- ⚠️ Pas de repo git (fallback gracieux)

### 8. run_tests (3 scénarios)
- ✅ Tests passent (exit 0)
- ❌ Tests échouent (exit 1, avec détails)
- ❌ Outil de test non installé → `E_EXECUTION`

### 9. http_request (5 scénarios)
- ✅ GET request succès (200)
- ✅ POST avec body JSON
- ❌ URL SSRF bloquée (localhost, 169.254.x.x) → `E_VALIDATION`
- ❌ Timeout → `E_NETWORK_ERROR`
- ❌ HTTP 404 → Succès avec status_code dans data

### 10. list_llm_models (3 scénarios)
- ✅ Liste modèles avec catégorisation
- ✅ Modèles vides (Ollama démarré mais aucun modèle)
- ❌ Ollama non disponible → `E_EXECUTION`

## Vérifications automatiques

Chaque test vérifie:

1. **Structure de réponse**:
   - Présence de `success`, `data`, `error`, `meta`
   - Types corrects (bool, dict|None, dict|None, dict)

2. **Contrat success=True**:
   - `data` est un dict non-None
   - `error` est None
   - `meta` contient au moins `duration_ms`

3. **Contrat success=False**:
   - `data` est None
   - `error` contient `code`, `message`, `recoverable`
   - `error.code` est dans la liste des codes standardisés

4. **Sécurité**:
   - Path traversal bloqué
   - Commandes dangereuses bloquées
   - SSRF protection active
   - Workspace isolation respectée

## Métriques attendues

Après exécution, les tests doivent atteindre:

- **Coverage**: >85% pour `tools.py`
- **Success rate**: 100% (0 test échoué)
- **Duration**: <30s pour la suite complète
- **Flakiness**: 0% (tests déterministes)

## Intégration CI/CD

Ajouter au pipeline:

```yaml
# .github/workflows/tests.yml
- name: Tool Regression Tests
  run: |
    cd backend
    .venv/bin/python -m pytest tests/tool_regression/ -v --tb=short
```

## Maintenance

- **Ajouter un outil**: Créer scénarios dans le fichier de test correspondant
- **Modifier contrat**: Mettre à jour `contracts.py` + tests impactés
- **Nouveau code d'erreur**: Ajouter dans `RECOVERABLE_ERRORS` (tools.py) + documenter ici

## Références

- Tool implementation: `backend/app/services/react_engine/tools.py`
- Tool result contract: `tools.py:168-200`
- Security validation: `tools.py:118-166`
- Error codes: `tools.py:214-222`

---

**Créé**: 2026-01-25
**Dernière mise à jour**: 2026-01-25
**Mainteneur**: AI Orchestrator Team
