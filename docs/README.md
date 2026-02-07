# Documentation AI Orchestrator v8

## Structure

| Section | Description |
|---------|-------------|
| [01-getting-started](01-getting-started/) | Installation et configuration |
| [02-architecture](02-architecture/) | Architecture et composants |
| [03-api](03-api/) | API REST et WebSocket |
| [04-security](04-security/) | Sécurité et audit |
| [05-operations](05-operations/) | Déploiement et monitoring |
| [06-development](06-development/) | Tests et développement |
| [07-learning](07-learning/) | Système d'apprentissage |
| [08-reference](08-reference/) | Référence des outils |

## Documents clés

- [MIGRATION_V8.md](MIGRATION_V8.md) - Guide de migration vers v8
- [V8_CERTIFICATION.md](V8_CERTIFICATION.md) - Certification des tests v8

## Quick Links

### Installation
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend  
cd frontend && npm install

# Démarrage
cd backend && ./start.sh
cd frontend && npm run dev
```

### Tests
```bash
# Backend: 313 tests
cd backend && pytest tests/ -v

# Frontend: 158 tests
cd frontend && npm test
```

## Changelog v8

- ✅ WebSocket EventEmitter centralisé
- ✅ Multi-run store avec isolation
- ✅ Système d'agents avec restrictions outils
- ✅ Tools web_search et web_read
- ✅ Self-improve engine
- ✅ UI v8 (Dashboard, Runs, Agents)
