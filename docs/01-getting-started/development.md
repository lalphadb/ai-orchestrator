# Guide de Démarrage - Mode Développement

Guide complet pour démarrer l'application AI Orchestrator en mode développement.

---

## 📋 Prérequis

### Logiciels Requis
- **Python 3.11+** - Backend FastAPI
- **Node.js 18+** - Frontend Vue 3
- **Ollama** (optionnel) - Pour modèles IA locaux
- **Git** - Gestion de version

### Vérification
```bash
python --version  # Doit afficher 3.11+
node --version    # Doit afficher 18+
npm --version     # Doit afficher 9+
```

---

## 🚀 Démarrage Rapide (2 minutes)

### 1. Backend
```bash
cd backend

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Créer fichier .env
cp .env.example .env
# Éditer .env et définir JWT_SECRET (générer avec: openssl rand -hex 32)

# Démarrer le serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Vérification Backend**: http://localhost:8001/health  
**Réponse attendue**: `{"status":"healthy","version":"7.0"}`

### 2. Frontend
```bash
# Nouveau terminal
cd frontend

# Installer dépendances
npm install

# Démarrer serveur de développement
npm run dev
# OU si erreur:
npx vite
```

**Vérification Frontend**: http://localhost:5173  
**Réponse attendue**: Interface de connexion AI Orchestrator

---

## 🔧 Configuration Détaillée

### Backend (.env)
```bash
# backend/.env
JWT_SECRET=votre_secret_genere_avec_openssl  # OBLIGATOIRE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Base de données
DATABASE_URL=sqlite:///./data/ai_orchestrator.db

# Ollama (optionnel)
OLLAMA_BASE_URL=http://localhost:11434

# Logs
LOG_LEVEL=INFO
LOG_FORMAT=text  # ou 'json' pour production
```

### Frontend (Environnement)
Le frontend utilise les variables d'environnement via `import.meta.env`:
- `import.meta.env.DEV` - True en mode développement
- `import.meta.env.PROD` - True en production

Pour activer les logs de debug en développement:
```javascript
// Dans la console du navigateur
localStorage.setItem('debug', 'true')
// Puis recharger la page
```

---

## ✅ Vérifications Post-Démarrage

### 1. Backend Health Check
```bash
curl http://localhost:8001/health
# Attendu: {"status":"healthy","version":"7.0"}

curl http://localhost:8001/api/v1/system/health
# Attendu: {"status":"healthy","version":"7.0","database":"connected",...}
```

### 2. Frontend Accessible
- Ouvrir: http://localhost:5173
- Vérifier: Page de connexion s'affiche
- Console dev: Aucune erreur 404/502

### 3. Créer un Compte
1. Aller sur http://localhost:5173/login
2. Cliquer "Créer un compte"
3. Remplir username + password
4. Se connecter

### 4. Tester le Chat
1. Aller sur http://localhost:5173/v8/chat
2. Envoyer un message: "Hello"
3. Vérifier:
   - Message utilisateur s'affiche
   - Icône de chargement apparaît
   - Réponse IA arrive (si modèle Ollama configuré)
   - WebSocket état: Connecté (voyant vert)

---

## 🐛 Troubleshooting

### Backend ne démarre pas

#### Erreur: `ModuleNotFoundError: No module named 'slowapi'`
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

#### Erreur: Port 8001 déjà utilisé
```bash
# Trouver le processus
lsof -i :8001
# Ou
ps aux | grep uvicorn

# Tuer le processus
kill -9 <PID>

# Ou changer le port
uvicorn main:app --reload --port 8002
# Et mettre à jour frontend/vite.config.js proxy
```

#### Erreur: Database locked
```bash
# Supprimer le fichier de verrou
rm backend/data/ai_orchestrator.db-journal
```

### Frontend ne démarre pas

#### Erreur: `npm ERR! Missing script: "dev"`
```bash
# Vérifier que package.json contient le script
cat frontend/package.json | grep '"dev"'

# Si absent, utiliser npx directement
npx vite
```

#### Erreur: Port 5173 déjà utilisé
```bash
# Tuer le processus
lsof -i :5173
kill -9 <PID>

# Ou utiliser un autre port
npx vite --port 5174
```

#### Erreur: `Error: Cannot find module ...`
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### WebSocket ne se connecte pas

#### Symptôme: Voyant rouge "Déconnecté"
1. Vérifier que le backend est actif: `curl http://localhost:8001/health`
2. Vérifier le token JWT:
   - Console dev → Application → Session Storage → `token`
   - Doit être présent et non expiré
3. Se reconnecter si nécessaire

#### Erreur: 403 Forbidden sur /ws
- Token JWT manquant ou invalide
- Se déconnecter puis reconnecter

### Chat ne répond pas

#### Aucun modèle configuré
```bash
# Vérifier Ollama
ollama list

# Télécharger un modèle léger
ollama pull qwen:0.5b

# Sélectionner dans l'interface: /v8/models
```

#### Erreur 500 Internal Server Error
- Vérifier les logs backend:
  ```bash
  cd backend
  tail -f logs/app.log
  ```
- Redémarrer le backend

---

## 📊 Ports Utilisés

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8001 | http://localhost:8001 |
| Frontend Dev | 5173 | http://localhost:5173 |
| Ollama | 11434 | http://localhost:11434 |
| ChromaDB (optionnel) | 8000 | http://localhost:8000 |

---

## 🔄 Workflow de Développement

### 1. Démarrage Quotidien
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8001

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 2. Modifications Code

#### Backend (Python)
- Uvicorn recharge automatiquement avec `--reload`
- Tests: `cd backend && pytest`

#### Frontend (Vue/JS)
- Vite recharge automatiquement (Hot Module Replacement)
- Tests: `cd frontend && npm run test`

### 3. Avant un Commit
```bash
# Backend: Linter + Tests
cd backend
black app/
flake8 app/
pytest

# Frontend: Linter + Format
cd frontend
npm run lint:fix
npm run format
npm run test
```

---

## 🔐 Sécurité en Développement

### Générer un JWT Secret sécurisé
```bash
openssl rand -hex 32
# Copier le résultat dans backend/.env
```

### Ne JAMAIS committer
- `backend/.env` (secrets)
- `backend/data/*.db` (données locales)
- `frontend/.env.local` (config locale)
- `**/node_modules/` (dépendances)
- `**/__pycache__/` (cache Python)

### Gitignore vérifié
```bash
# Vérifier que les fichiers sensibles sont ignorés
git status --ignored
```

---

## 📚 Ressources Supplémentaires

- **Architecture**: [docs/02-architecture/overview.md](../02-architecture/overview.md)
- **API REST**: [docs/03-api/rest.md](../03-api/rest.md)
- **WebSocket**: [docs/03-api/websocket.md](../03-api/websocket.md)
- **Tests**: [docs/06-development/testing.md](../06-development/testing.md)
- **Sécurité**: [docs/04-security/overview.md](../04-security/overview.md)

---

## ✨ Commandes Utiles

### Backend
```bash
# Créer migration DB
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Shell interactif
python -i -c "from app.core.database import SessionLocal; db = SessionLocal()"

# Nettoyer cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Frontend
```bash
# Build production
npm run build

# Preview build
npm run preview

# Analyser bundle
npm run build -- --report

# Tests E2E
npm run test:e2e

# Mise à jour dépendances
npm outdated
npm update
```

---

## 🎓 Workflow Recommandé

1. **Matin**: 
   - Pull dernier code: `git pull`
   - Démarrer backend + frontend
   - Vérifier health checks

2. **Développement**:
   - Créer branche feature: `git checkout -b feature/ma-feature`
   - Coder avec rechargement auto
   - Tester au fur et à mesure

3. **Avant commit**:
   - Linter + tests: `npm run lint && npm run test`
   - Backend tests: `pytest`
   - Vérifier console dev: 0 erreur

4. **Soir**:
   - Commit + push: `git add . && git commit -m "..." && git push`
   - Arrêter serveurs: Ctrl+C dans chaque terminal

---

**Dernière mise à jour**: 2026-01-30  
**Version**: AI Orchestrator v8.0
