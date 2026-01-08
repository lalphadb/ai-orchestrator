# Guide de Développement

Guide pour contribuer au développement d'AI Orchestrator v6.

---

## Setup développement

### 1. Cloner le repo

```bash
git clone <repository-url> ai-orchestrator
cd ai-orchestrator
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Outils dev

# Lancer en mode dev
uvicorn main:app --reload --port 8001
```

### 3. Frontend

```bash
cd frontend
npm install

# Mode développement avec hot-reload
npm run dev
```

---

## Structure du projet

```
ai-orchestrator/
├── backend/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── app/
│   │   ├── api/v1/          # Routes API
│   │   ├── core/            # Config, DB, Security
│   │   ├── models/          # Schemas Pydantic
│   │   └── services/        # Logique métier
│   ├── tests/               # Tests unitaires
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── views/           # Pages Vue.js
│   │   ├── stores/          # Pinia stores
│   │   ├── components/      # Composants
│   │   └── router/          # Routes
│   └── package.json
│
└── docs/                    # Documentation
```

---

## Conventions de code

### Python (Backend)

- **Style**: PEP 8
- **Formatter**: Black
- **Linter**: Ruff
- **Type hints**: Requis

```bash
# Formatter
black app/

# Linter
ruff check app/

# Type checking
mypy app/
```

### JavaScript/Vue (Frontend)

- **Style**: ESLint + Prettier
- **Framework**: Vue 3 Composition API

```bash
# Lint
npm run lint

# Format
npm run format
```

---

## Tests

### Backend

```bash
cd backend
source .venv/bin/activate

# Tous les tests
pytest

# Avec couverture
pytest --cov=app

# Tests spécifiques
pytest tests/test_auth.py -v
```

### Frontend

```bash
cd frontend

# Tests unitaires
npm run test

# Tests e2e
npm run test:e2e
```

---

## Ajouter une fonctionnalité

### Nouvel endpoint API

1. Créer le fichier route dans `app/api/v1/`
2. Ajouter les schemas dans `app/models/`
3. Implémenter la logique dans `app/services/`
4. Enregistrer la route dans `main.py`
5. Écrire les tests
6. Documenter dans `docs/API.md`

### Nouvel outil

1. Créer la fonction dans `app/services/react_engine/tools.py`
2. Enregistrer avec `BUILTIN_TOOLS.register()`
3. Documenter dans `docs/TOOLS.md`
4. Tester avec le ReAct Engine

```python
# Exemple
async def mon_outil(param: str) -> Dict[str, Any]:
    """Description pour le LLM"""
    return {"result": "..."}

BUILTIN_TOOLS.register(
    name="mon_outil",
    func=mon_outil,
    description="Description",
    category="custom",
    parameters={"param": "string"}
)
```

---

## Git workflow

### Branches

- `main` - Production stable
- `develop` - Développement
- `feature/*` - Nouvelles fonctionnalités
- `fix/*` - Corrections de bugs

### Commits

Format: `type(scope): message`

Types:
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Maintenance

```bash
git commit -m "feat(tools): add http_request tool"
git commit -m "fix(auth): handle expired tokens"
git commit -m "docs(api): update websocket examples"
```

---

## API Documentation

La documentation OpenAPI est générée automatiquement:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## Debugging

### Backend

```python
# Dans le code
import logging
logger = logging.getLogger(__name__)
logger.debug("Message debug")

# Ou avec breakpoint
breakpoint()  # Python 3.7+
```

### Frontend

```javascript
// Console
console.log('Debug:', data)

// Vue DevTools
// Installer l'extension navigateur
```

---

## Performance

### Profiling Backend

```bash
# Avec py-spy
pip install py-spy
py-spy top --pid <PID>
```

### Profiling Frontend

```bash
# Build avec analyse
npm run build -- --report
```
