# Tests

## Backend

```bash
cd backend
source .venv/bin/activate

# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_agents.py -v
pytest tests/test_ws_events.py -v
pytest tests/test_web_tools.py -v

# Avec couverture
pytest tests/ --cov=app --cov-report=html
```

### Structure des tests

```
tests/
├── test_agents.py          # Tests système d'agents v8
├── test_ws_events.py       # Tests events WebSocket
├── test_ws_event_emitter.py # Tests EventEmitter
├── test_web_tools.py       # Tests web_search/web_read
├── test_api_chat.py        # Tests API chat
├── test_conversational_memory.py
└── tool_regression/        # Tests de régression outils
    ├── test_filesystem_tools.py
    ├── test_network_tools.py
    ├── test_qa_tools.py
    └── test_system_tools.py
```

## Frontend

```bash
cd frontend

# Tests unitaires
npm test

# Mode watch
npm run test:watch

# Couverture
npm run test:coverage
```

### Structure des tests

```
tests/
├── stores/
│   ├── chat-multirun.spec.js  # Tests multi-run store
│   ├── chat-ws-routing.spec.js
│   └── chat.test.js
├── components/
│   ├── RunInspector.test.js
│   └── Toast.test.js
├── services/
│   └── normalizeEvent.test.js
└── router/
    └── routes.test.js
```

## Résultats actuels

| Suite | Tests | Status |
|-------|-------|--------|
| Backend | 313 | ✅ Passed |
| Frontend | 158 | ✅ Passed |
