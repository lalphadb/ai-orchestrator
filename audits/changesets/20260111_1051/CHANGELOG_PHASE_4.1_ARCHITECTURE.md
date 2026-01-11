# CHANGELOG — Phase 4.1: Architecture Frontend v7.0
**Date:** 2026-01-11 14:00
**Objectif:** Créer architecture de base (stores, types, AppShell)

---

## 1. Fichiers créés

### Types (JSDoc):
- ✅ `frontend/src/types/run.js` - Types Run, RunStatus, PhaseState, ToolCall, etc.
- ✅ `frontend/src/types/ws.js` - Types WebSocket events + parsers

### Utils:
- ✅ `frontend/src/utils/normalize.js` - Normalisation events WS → Run state

### Stores Pinia:
- ✅ `frontend/src/stores/runs.js` - Source vérité Runs (CRUD + events)
- ✅ `frontend/src/stores/ws.js` - Connexion WebSocket + routing events
- ✅ `frontend/src/stores/ui.js` - Préférences UI + toasts

### Components Layout:
- ✅ `frontend/src/components/layout/AppShell.vue` - Layout 3 zones
- ✅ `frontend/src/components/layout/LeftRail.vue` - Liste runs + filters
- ✅ `frontend/src/components/layout/InspectorPanel.vue` - Inspector avec tabs

### Views:
- ✅ `frontend/src/views/RunsView.vue` - Vue principale v7.0

---

## 2. Fichiers modifiés

### Router:
- ✅ `frontend/src/router/index.js`
  - Ajout route `/` → RunsView
  - Ajout route `/runs/:runId` → RunsView
  - Déplacement `/legacy` → ChatView (ancien)

### Main:
- ✅ `frontend/src/main.js`
  - Initialisation stores (ws, system, ui) après montage
  - Connexion WebSocket auto
  - Chargement config système
  - Chargement préférences UI

### System Store:
- ✅ `frontend/src/stores/system.js`
  - Ajout state `config`
  - Ajout action `fetchConfigSummary()`
  - Extraction config depuis health endpoint

---

## 3. Architecture implémentée

### Stores:

#### runs.store.js (Source vérité)
- State: `runsById`, `runOrder`, `activeRunId`
- Getters: `activeRun`, `runsList`, `runById()`, `runsFiltered()`
- Actions:
  - CRUD: `createRun()`, `updateRun()`, `deleteRun()`
  - Events: `applyEvent()`, `appendToolCall()`, `appendEvent()`
  - Phases: `setPhase()`, `setFinal()`
  - User actions: `reVerify()`, `forceRepair()`, `exportReport()`

#### ws.store.js (WebSocket)
- State: `socket`, `connected`, `lastError`, `reconnectAttempts`
- Actions:
  - Connection: `connect()`, `disconnect()`, `attemptReconnect()`
  - Messages: `send()`, `handleMessage()`, `routeEvent()`
  - Convenience: `sendMessage()` (create run + send WS message)

#### ui.store.js (UI Pure)
- State: Inspector (open, tab), Preferences (compact, theme), Toasts, Filters
- Actions:
  - Inspector: `toggleInspector()`, `setInspectorTab()`
  - Toasts: `addToast()`, `removeToast()`, `clearToasts()`
  - Filters: `setRunFilterStatus()`, `setRunFilterModel()`, `setRunSearchQuery()`
  - Preferences: `loadPreferences()`, `savePreferences()`

### Components:

#### AppShell.vue
- 3-zone layout: LeftRail (240px) / Main (flex) / Inspector (420px)
- Slots: `#topbar`, `#left-rail`, `#main`, `#inspector`
- Toast notifications (bottom-right)
- Collapsible panels

#### LeftRail.vue
- Run list (cards)
- Search + filters (status, model)
- System badge (EXECUTE_MODE, VERIFY_REQUIRED, version)
- New Run button

#### InspectorPanel.vue
- 5 tabs: Summary, Tools, Verification, Diff, Raw
- Summary: Status, duration, tools count, phases état
- Tools: Tool calls list + details
- Verification: QA results
- Diff: File changes (placeholder)
- Raw: JSON viewer + copy button

#### RunsView.vue
- Main view using AppShell
- Run header (prompt, status, model, duration)
- Run content (placeholder)
- Message input (bottom)

---

## 4. Dépendances installées

```bash
npm install axios @vueuse/core
```

Packages ajoutés:
- `axios` - Client HTTP (API calls)
- `@vueuse/core` - Composables Vue (useLocalStorage, etc.)

---

## 5. Tests de validation

### Test 1: Compilation
```bash
npm run dev
# ✅ SUCCESS: Dev server démarre sans erreurs
```

### Test 2: Frontend accessible
```bash
curl http://localhost:5173
# ✅ SUCCESS: Page HTML servie
```

### Test 3: Stores initialisés
- ✅ ws.connect() appelé au montage
- ✅ system.fetchConfigSummary() appelé au montage
- ✅ ui.loadPreferences() appelé au montage

### Test 4: Routes fonctionnelles
- ✅ `/` → RunsView (nouveau)
- ✅ `/legacy` → ChatView (ancien)
- ✅ `/tools` → ToolsView
- ✅ `/settings` → SettingsView

---

## 6. Résultat Phase 4.1

| Critère | Status |
|---------|--------|
| Types créés (run, ws) | ✅ OK |
| Utils créés (normalize) | ✅ OK |
| Stores créés (runs, ws, ui) | ✅ OK |
| AppShell 3 zones | ✅ OK |
| LeftRail | ✅ OK |
| InspectorPanel (tabs) | ✅ OK |
| RunsView | ✅ OK |
| Router mis à jour | ✅ OK |
| Dependencies installées | ✅ OK |
| Frontend compile | ✅ OK |

**Verdict:** ✅ **PHASE 4.1 COMPLÈTE**

---

## 7. Prochaine étape

→ **PHASE 4.2**: Runs & Timeline (WorkflowStepper, RunTimeline, RunCard amélioré)

**Objectifs Phase 4.2:**
- Créer WorkflowStepper.vue (6 phases visualisées)
- Créer RunTimeline.vue (timeline avec tool calls)
- Améliorer RunCard.vue (composant réutilisable)
- Créer RunHeader.vue (header run détaillé)
- Créer RunActions.vue (Re-verify, Export, etc.)

**Critères de succès:**
- WorkflowStepper affiche 6 phases avec états
- Timeline montre tool calls expandables
- Run cards compacts et informatifs
- Actions fonctionnelles (au moins export)

---

**FIN PHASE 4.1 - Architecture Frontend v7.0**
