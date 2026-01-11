# CHANGELOG — Phase 4.0: Frontend Baseline
**Date:** 2026-01-11 13:00
**Objectif:** Documenter état actuel frontend avant refonte v7.0

---

## 1. Structure actuelle

### Fichiers clés:
```
frontend/src/
├── App.vue                          # Layout principal (TopBar + RouterView)
├── main.js                          # Entry point (Vue 3 + Pinia + Router)
├── router/index.js                  # Routes (/, /tools, /settings, /login)
├── stores/
│   ├── auth.js                      # Authentification JWT
│   ├── chat.js                      # Conversations + messages
│   ├── learning.js                  # Learning memory
│   ├── system.js                    # System config + health
│   └── tools.js                     # Tools catalog
├── services/
│   ├── api.js                       # API HTTP client (axios)
│   └── wsClient.js                  # WebSocket client
├── views/
│   ├── ChatView.vue                 # Vue principale chat
│   ├── ToolsView.vue                # Catalogue outils
│   ├── SettingsView.vue             # Settings
│   └── LoginView.vue                # Login page
└── components/
    ├── common/
    │   └── StatusBar.vue            # Status bar backend
    └── chat/
        ├── ChatInput.vue
        ├── MessageInput.vue
        ├── MessageList.vue
        ├── ConversationSidebar.vue
        ├── RunInspector.vue
        ├── FeedbackButtons.vue
        ├── CategorySection.vue
        └── ModelsDisplay.vue
```

---

## 2. Architecture actuelle

### Stores Pinia (5):

#### auth.js
- JWT token management
- Login/logout
- User state

#### chat.js
- Conversations list
- Messages
- Current conversation
- Send message action

#### learning.js
- Learning memory query
- Examples retrieval

#### system.js
- System health
- Models list
- Config (EXECUTE_MODE, VERIFY_REQUIRED)

#### tools.js
- Tools catalog
- Tool execution

### Services (2):

#### api.js
- Axios client
- Base URL config
- JWT interceptor
- Endpoints: /chat, /tools, /system, /learning

#### wsClient.js
- WebSocket connection
- Event routing
- Message parsing

### Views (4):

#### ChatView.vue
- Main chat interface
- ConversationSidebar (left)
- MessageList (center)
- ChatInput (bottom)
- RunInspector (right, optional)

#### ToolsView.vue
- Tools catalog display
- Category filters
- Tool details

#### SettingsView.vue
- System settings
- Model selection
- Config display

#### LoginView.vue
- Login form
- JWT authentication

---

## 3. Gaps identifiés (par rapport à spec v7.0)

### Architecture:
- ❌ Pas de notion de "Run" (seulement conversation + messages)
- ❌ Pas de workflow phases visible (SPEC/PLAN/EXECUTE/VERIFY)
- ❌ Pas d'inspector avec tabs (Summary/Tools/Verification/Diff/Raw)
- ❌ Pas de timeline avec tool calls détaillés
- ❌ Pas de système de Run status (RUNNING/SUCCESS/FAILED)
- ❌ Pas de deep-link `/runs/:runId`

### Stores:
- ❌ chat.js ne gère pas les Runs comme entités
- ❌ Pas de store runs.store dédié
- ❌ Pas de store ws.store pour routing events
- ❌ Pas de store ui.store pour prefs

### Components:
- ❌ Pas de LeftRail avec RunCard
- ❌ Pas de WorkflowStepper
- ❌ Pas de RunTimeline
- ❌ Pas de InspectorPanel avec tabs
- ❌ Pas de RunActions (Re-verify, Force repair)
- ❌ Pas de System badge (EXECUTE_MODE visible)

### Types:
- ❌ Pas de TypeScript
- ❌ Pas de types Run/RunPhase/ToolCall/WsEvent

---

## 4. Points forts à conserver

### Ce qui fonctionne bien:
- ✅ WebSocket connexion stable
- ✅ API client avec JWT interceptor
- ✅ Store system.js récupère config backend
- ✅ ConversationSidebar (bon pattern pour LeftRail)
- ✅ RunInspector existe (base pour nouveau Inspector)
- ✅ StatusBar affiche mode backend

### Composants réutilisables:
- ✅ StatusBar.vue → Peut devenir System badge
- ✅ ConversationSidebar.vue → Pattern pour LeftRail
- ✅ RunInspector.vue → Base pour InspectorPanel
- ✅ MessageList.vue → Pattern pour RunTimeline

---

## 5. Stratégie de migration

### Approche:
1. **Garder ancien code** en l'état (pas de suppression)
2. **Créer nouvelle structure** parallèle (stores/runs.js, views/RunsView.vue)
3. **Refactor progressif** (Phase 4.1 → 4.4)
4. **Tester après chaque phase** (npm run dev)

### Plan de migration:
- **Phase 4.1:** Architecture (stores, types, API, AppShell)
- **Phase 4.2:** Runs & Timeline
- **Phase 4.3:** Inspector
- **Phase 4.4:** Actions & Polish

---

## 6. Backup créé

### Localisation:
```bash
audits/changesets/20260111_1051/frontend_baseline/src/
```

### Contenu:
- Copie complète de `frontend/src/` avant modifications
- Permet rollback si nécessaire

### Restauration (si besoin):
```bash
cd /home/lalpha/projets/ai-tools/ai-orchestrator
rm -rf frontend/src
cp -r audits/changesets/20260111_1051/frontend_baseline/src frontend/
npm --prefix frontend run dev
```

---

## 7. Dépendances npm actuelles

### package.json principal:
```bash
# Lire dependencies actuelles
cat frontend/package.json | grep -A 20 "dependencies"
```

### Dépendances attendues pour v7.0:
- Vue 3 (déjà présent)
- Pinia (déjà présent)
- Vue Router (déjà présent)
- Axios (déjà présent)
- @vueuse/core (à vérifier/installer)
- TypeScript support (à ajouter si manquant)

---

## 8. Tests de validation baseline

### Test 1: Frontend démarre
```bash
cd frontend
npm run dev
# Attendu: Dev server démarre sur port 5173
```

### Test 2: Chat fonctionne
- Ouvrir http://localhost:5173
- Envoyer message "Bonjour"
- Vérifier réponse reçue

### Test 3: WebSocket connecté
- Ouvrir DevTools Network → WS
- Vérifier connexion active à ws://localhost:8001/api/v1/chat/ws

### Test 4: Store system récupère config
- Ouvrir Vue DevTools
- Vérifier store system contient EXECUTE_MODE, VERIFY_REQUIRED

---

## 9. Résultat Phase 4.0

| Critère | Status |
|---------|--------|
| Backup frontend créé | ✅ OK |
| Structure documentée | ✅ OK |
| Gaps identifiés | ✅ OK |
| Stratégie migration définie | ✅ OK |
| Frontend actuel fonctionnel | ⏳ À vérifier |

**Verdict:** ✅ **BASELINE FRONTEND DOCUMENTÉE**

---

## 10. Prochaine étape

→ **PHASE 4.1**: Architecture de base (stores, types, API, AppShell)

**Objectifs Phase 4.1:**
- Créer stores/runs.js (source vérité Runs)
- Créer stores/ws.js (routing events)
- Créer stores/ui.js (prefs UI)
- Créer types/run.js, types/ws.js (si TypeScript supporté, sinon JSDoc)
- Créer components/layout/AppShell.vue (3-zone layout)
- Créer utils/normalize.js (events → Run state)

**Critères de succès:**
- Stores créés et fonctionnels
- AppShell affiche 3 zones (LeftRail / Main / Inspector)
- Types définis (JSDoc ou TS)
- npm run dev démarre sans erreurs

---

**FIN BASELINE FRONTEND v7.0**
