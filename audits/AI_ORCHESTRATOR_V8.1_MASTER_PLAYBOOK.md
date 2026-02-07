# 🚀 AI ORCHESTRATOR v8.1 — MASTER PLAYBOOK
## Stabilisation + Refonte UI/UX Complète

**Document de référence unique pour l'évolution de v8.0 → v8.1**

---

| Métadonnée | Valeur |
|------------|--------|
| **Numéro CRQ** | CRQ-2026-0203-001-MASTER |
| **Version cible** | 8.1.0 |
| **Date création** | 2026-02-03 |
| **Auteur** | Lalpha (root3d) |
| **Environnement** | Production - ai.4lb.ca |
| **Statut** | 🔄 En cours (Phase 8 bugs) |

---

## ⚠️ RÈGLES ABSOLUES (LIRE AVANT TOUTE ACTION)

```
╔══════════════════════════════════════════════════════════════════╗
║  INTERDICTIONS STRICTES                                          ║
╠══════════════════════════════════════════════════════════════════╣
║  ❌ Sauter une phase                                             ║
║  ❌ Écrire du code sans plan validé                              ║
║  ❌ Modifier la sécurité ou le workflow v7.1                     ║
║  ❌ Livrer sans tests                                            ║
║  ❌ Casser la compatibilité existante                            ║
║  ❌ Commencer l'UI avant stabilisation complète                  ║
║  ❌ Refondre plusieurs composants simultanément                  ║
╠══════════════════════════════════════════════════════════════════╣
║  OBLIGATIONS                                                     ║
╠══════════════════════════════════════════════════════════════════╣
║  ✅ Chaque phase se termine par TESTS + VERDICT                  ║
║  ✅ Échec → REPAIR obligatoire avant continuer                   ║
║  ✅ Backup avant chaque modification                             ║
║  ✅ Commit atomique par correctif (1 PR = 1 fix)                 ║
║  ✅ Documentation mise à jour                                    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 📋 TABLE DES MATIÈRES

### PARTIE A — STABILISATION (v8.0 → v8.0.1)
- [Phase 0 : Inventaire & Cartographie](#phase-0--inventaire--cartographie)
- [Phase 1 : Stabilisation WebSocket v8](#phase-1--stabilisation-websocket-v8)
- [Phase 2 : Stabilisation Frontend (Run Store)](#phase-2--stabilisation-frontend-run-store)
- [Phase 3 : Correction Pages Cassées](#phase-3--correction-pages-cassées)
- [Phase 4 : Session Management](#phase-4--session-management)
- [Phase 5 : Tests Finaux Stabilisation](#phase-5--tests-finaux-stabilisation)

### PARTIE B — REFONTE UI/UX (v8.0.1 → v8.1.0)
- [Phase 6 : Design System "Neural Glow"](#phase-6--design-system-neural-glow)
- [Phase 7 : Composants Core](#phase-7--composants-core)
- [Phase 8 : Refonte Pages Principales](#phase-8--refonte-pages-principales)
- [Phase 9 : Animations & Micro-interactions](#phase-9--animations--micro-interactions)
- [Phase 10 : Polish & Optimisation](#phase-10--polish--optimisation)
- [Phase 11 : Tests Finaux & Release v8.1](#phase-11--tests-finaux--release-v81)

### ANNEXES
- [A. Inventaire des Bugs](#annexe-a--inventaire-des-bugs)
- [B. Design Tokens Complets](#annexe-b--design-tokens-complets)
- [C. Composants à Créer](#annexe-c--composants-à-créer)
- [D. Checklist de Validation](#annexe-d--checklist-de-validation)

---

# PARTIE A — STABILISATION (v8.0 → v8.0.1)

## 🎯 Objectif Partie A
Corriger tous les bugs critiques identifiés pour obtenir une base stable avant refonte UI.

**Durée estimée :** 3-5 jours  
**Livrable :** AI Orchestrator v8.0.1 STABLE

---

## Phase 0 — Inventaire & Cartographie

### Objectif
Comprendre le projet réel. Aucune hypothèse. Aucun code.

### Actions Obligatoires

| # | Action | Vérification |
|---|--------|--------------|
| 1 | Lister l'arborescence complète du repository | ☐ |
| 2 | Identifier Backend (FastAPI, WS, workflow engine) | ☐ |
| 3 | Identifier Frontend (Vue 3, Pinia, WS client) | ☐ |
| 4 | Identifier Tools (filesystem, network, QA) | ☐ |
| 5 | Identifier Modèles (Run, ToolResult, Conversation) | ☐ |
| 6 | Identifier Mémoire (SQLite, ChromaDB) | ☐ |
| 7 | Identifier Sécurité (allowlist, SSRF, sandbox) | ☐ |

### Sortie Attendue
```
✅ Mapping complet du projet documenté
✅ Aucune ligne de code modifiée
✅ Risques de régression identifiés
```

### Verdict Phase 0
- [ ] PASS → Continuer Phase 1
- [ ] FAIL → Compléter cartographie

---

## Phase 1 — Stabilisation WebSocket v8

### Objectif
Rendre les runs déterministes, traçables, et impossibles à bloquer.

### Bugs Adressés
| ID | Bug | Priorité |
|----|-----|----------|
| BUG-001 | Runs bloqués en état RUNNING | P0 |
| BUG-002 | Spinner de génération infini | P0 |
| BUG-006 | Run Inspector incomplet | P0 |

### Actions Obligatoires

#### 1.1 EventEmitter Centralisé
```python
# backend/core/event_emitter.py
class RunEventEmitter:
    """
    INVARIANTS:
    - Chaque run émet EXACTEMENT un 'complete' OU 'error'
    - Tous les events contiennent: type, timestamp, run_id
    - Ordre garanti: phase → thinking → tool → verification → complete/error
    """
```

#### 1.2 Events v8 à Implémenter
| Event | Description | Obligatoire |
|-------|-------------|-------------|
| `conversation_created` | Nouvelle conversation | ✅ |
| `phase` | Changement de phase (SPEC, PLAN, EXEC, QA, FIX) | ✅ |
| `thinking` | Réflexion en cours | ✅ |
| `tool` | Exécution d'un outil | ✅ |
| `verification_item` | Résultat QA | ✅ |
| `complete` | Run terminé avec succès | ✅ |
| `error` | Run terminé en erreur | ✅ |

#### 1.3 Compatibilité v7.1
```python
# Maintenir compat layer OU versioning WS
WS_VERSION = "v8"
COMPAT_MODE = True  # Support v7.1 events si nécessaire
```

### Interdictions Phase 1
```
❌ Emit WS sauvage (sans run_id)
❌ Streaming brut de tokens sans wrapper event
❌ Suppression d'events existants sans fallback
❌ Run sans complete/error final
```

### Tests Obligatoires Phase 1

| # | Test | Commande | Attendu |
|---|------|----------|---------|
| 1 | Happy path complet | Lancer un run simple | `complete` reçu |
| 2 | Ordre des events | Observer séquence | phase→tool→complete |
| 3 | Finalisation garantie | Tout run | JAMAIS "RUNNING" après fin |
| 4 | Exception backend | Simuler erreur | `error` event émis |
| 5 | Timeout | Run > 120s | `error` avec timeout |

### Verdict Phase 1
```
[ ] PASS → Tous tests verts, continuer Phase 2
[ ] FAIL → REPAIR obligatoire, re-test
```

---

## Phase 2 — Stabilisation Frontend (Run Store)

### Objectif
Éliminer définitivement : runs bloqués, incohérences UI, désynchronisations WS.

### Actions Obligatoires

#### 2.1 Refonte Store Pinia
```javascript
// stores/runs.js
export const useRunStore = defineStore('runs', {
  state: () => ({
    // INDEXED BY RUN_ID - jamais un array
    runs: {}, // { [run_id]: RunState }
    activeRunId: null,
  }),
  
  actions: {
    // Events append-only
    appendEvent(runId, event) {
      if (!this.runs[runId]) {
        this.runs[runId] = createEmptyRunState(runId)
      }
      this.runs[runId].events.push(event)
      this.processEvent(runId, event)
    },
    
    // Watchdog par run
    startWatchdog(runId, timeoutMs = 120000) {
      // Force FAILED si pas de complete/error après timeout
    }
  }
})
```

#### 2.2 Router Events WS
```javascript
// composables/useWebSocket.js
const eventHandlers = {
  'conversation_created': handleConversationCreated,
  'phase': handlePhase,
  'thinking': handleThinking,
  'tool': handleTool,
  'verification_item': handleVerification,
  'complete': handleComplete,
  'error': handleError,
}

// CHAQUE event routé vers le bon handler
ws.onmessage = (msg) => {
  const event = JSON.parse(msg.data)
  const handler = eventHandlers[event.type]
  if (handler) handler(event)
}
```

#### 2.3 Watchdog Timeout
```javascript
// Si pas de complete/error après 120s → forcer FAILED
const WATCHDOG_TIMEOUT = 120000

function startRunWatchdog(runId) {
  setTimeout(() => {
    const run = runStore.runs[runId]
    if (run && run.status === 'RUNNING') {
      runStore.forceStatus(runId, 'FAILED', 'Timeout: no response')
    }
  }, WATCHDOG_TIMEOUT)
}
```

### Interdictions Phase 2
```
❌ Logique métier dans les composants UI
❌ State global non indexé par run_id
❌ Mutation directe du state (toujours via actions)
```

### Tests Obligatoires Phase 2

| # | Test | Action | Attendu |
|---|------|--------|---------|
| 1 | Runs simultanés | Lancer 3 runs | Tous trackés séparément |
| 2 | Reconnexion WS | Déconnecter/reconnecter | État synchronisé |
| 3 | Watchdog timeout | Bloquer backend 130s | Run → FAILED |
| 4 | Refresh page | F5 pendant run | État cohérent restauré |
| 5 | Console propre | Toute navigation | 0 erreur JS |

### Verdict Phase 2
```
[ ] PASS → Continuer Phase 3
[ ] FAIL → REPAIR obligatoire
```

---

## Phase 3 — Correction Pages Cassées

### Objectif
Toutes les pages chargent sans erreur JavaScript.

### Bugs Adressés
| ID | Bug | Page | Erreur |
|----|-----|------|--------|
| BUG-003 | Page Models vide | `/models` | `Cannot read 'models'` |
| BUG-004 | Page Memory vide | `/memory` | `Cannot read 'collections'` |
| BUG-009 | Filtre Tools cassé | `/tools` | Liste ne filtre pas |
| BUG-011 | Sidebar conversations | `/chat` | "Aucune conversation" incorrect |

### Actions Obligatoires

#### 3.1 Pattern Défensif Obligatoire
```vue
<!-- AVANT (cassé) -->
<template>
  <div v-for="model in store.models">
    {{ model.name }}
  </div>
</template>

<!-- APRÈS (défensif) -->
<template>
  <!-- Loading state -->
  <SkeletonLoader v-if="isLoading" />
  
  <!-- Error state -->
  <ErrorDisplay v-else-if="error" :error="error" @retry="fetchData" />
  
  <!-- Empty state -->
  <EmptyState v-else-if="!models?.length" message="Aucun modèle" />
  
  <!-- Data state -->
  <div v-else v-for="model in models" :key="model.id">
    {{ model.name }}
  </div>
</template>

<script setup>
const models = computed(() => store.models ?? [])
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)
</script>
```

#### 3.2 Fichiers à Corriger

| Fichier | Action |
|---------|--------|
| `views/ModelsView.vue` | Optional chaining + loading state |
| `views/MemoryView.vue` | Optional chaining + loading state |
| `views/ToolsView.vue` | Fix filtre catégorie |
| `components/Sidebar.vue` | Sync conversations |
| `stores/models.js` | Initialiser state vide |
| `stores/memory.js` | Initialiser state vide |

#### 3.3 Composants Utilitaires à Créer
```
components/
  ui/
    SkeletonLoader.vue    ← États de chargement
    ErrorBoundary.vue     ← Capture erreurs JS
    EmptyState.vue        ← États vides élégants
    Toast.vue             ← Notifications
```

### Tests Obligatoires Phase 3

| # | Test | Page | Attendu |
|---|------|------|---------|
| 1 | Models charge | `/models` | Liste affichée ou empty state |
| 2 | Memory charge | `/memory` | Collections ou empty state |
| 3 | Tools filtre | `/tools` | Catégorie filtre la liste |
| 4 | Sidebar sync | `/chat` | Conversation active listée |
| 5 | Console propre | Toutes | 0 erreur JS |

### Verdict Phase 3
```
[ ] PASS → Continuer Phase 4
[ ] FAIL → REPAIR obligatoire
```

---

## Phase 4 — Session Management

### Objectif
Session maintenue pendant navigation sans expiration inattendue.

### Bug Adressé
| ID | Bug | Symptôme |
|----|-----|----------|
| BUG-005 | Expiration session inattendue | Déconnexion sans action user |

### Actions Obligatoires

#### 4.1 Refresh Token Automatique
```javascript
// services/auth.js
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000 // 5 min avant expiration

function setupTokenRefresh() {
  const token = getToken()
  const expiresAt = decodeToken(token).exp * 1000
  const refreshAt = expiresAt - TOKEN_REFRESH_BUFFER
  
  setTimeout(async () => {
    try {
      await refreshToken()
      setupTokenRefresh() // Reschedule
    } catch (error) {
      showSessionExpiredNotification()
    }
  }, refreshAt - Date.now())
}
```

#### 4.2 Notification Expiration
```vue
<!-- components/SessionExpiredModal.vue -->
<template>
  <Modal v-if="sessionExpired" :closable="false">
    <h2>Session expirée</h2>
    <p>Votre session a expiré. Veuillez vous reconnecter.</p>
    <Button @click="redirectToLogin">Se reconnecter</Button>
  </Modal>
</template>
```

#### 4.3 Indicateur de Session
```vue
<!-- Dans TopBar ou StatusBar -->
<StatusOrb 
  :status="isAuthenticated ? 'active' : 'error'"
  :label="isAuthenticated ? 'Connecté' : 'Déconnecté'"
  pulse
/>
```

### Tests Obligatoires Phase 4

| # | Test | Action | Attendu |
|---|------|--------|---------|
| 1 | Navigation longue | 30+ min d'utilisation | Session maintenue |
| 2 | Refresh auto | Attendre près expiration | Token rafraîchi silencieusement |
| 3 | Expiration réelle | Forcer expiration | Modal affiché, pas redirect silent |
| 4 | Reconnexion | Clic "Se reconnecter" | Retour à login propre |

### Verdict Phase 4
```
[ ] PASS → Continuer Phase 5
[ ] FAIL → REPAIR obligatoire
```

---

## Phase 5 — Tests Finaux Stabilisation

### Objectif
Certifier v8.0.1 stable avant refonte UI.

### Checklist Complète

#### 5.1 Tests Fonctionnels
| # | Test | Durée | Statut |
|---|------|-------|--------|
| 1 | Run simple (happy path) | 1 min | ☐ |
| 2 | Run avec tools multiples | 2 min | ☐ |
| 3 | Run avec erreur (gérée) | 1 min | ☐ |
| 4 | Runs simultanés (x3) | 3 min | ☐ |
| 5 | Navigation toutes pages | 5 min | ☐ |
| 6 | WebSocket stable 30 min | 30 min | ☐ |

#### 5.2 Tests de Non-Régression
| # | Test | Attendu | Statut |
|---|------|---------|--------|
| 1 | Compat workflow v7.1 | Fonctionne | ☐ |
| 2 | Tools existants | Tous opérationnels | ☐ |
| 3 | Auth existante | Fonctionne | ☐ |
| 4 | API endpoints | Tous répondent | ☐ |

#### 5.3 Tests Qualité
| # | Critère | Seuil | Statut |
|---|---------|-------|--------|
| 1 | Erreurs console | 0 | ☐ |
| 2 | Warnings console | < 5 | ☐ |
| 3 | Runs bloqués | 0 | ☐ |
| 4 | Taux succès runs | > 95% | ☐ |

### Livrables Phase 5
```
✅ CHANGELOG_v8.0.1.md
✅ Tests passés documentés
✅ Tag git v8.0.1
✅ Backup base de données
```

### Verdict Phase 5 — GO/NO-GO pour UI
```
[ ] GO → Tous critères verts, commencer Partie B (UI)
[ ] NO-GO → Retour phases 1-4 pour corrections
```

---

# PARTIE B — REFONTE UI/UX (v8.0.1 → v8.1.0)

## 🎯 Objectif Partie B
Transformer l'interface d'un "dashboard admin 2015" vers une "AI Platform 2025+".

**Durée estimée :** 6-8 semaines  
**Livrable :** AI Orchestrator v8.1.0 MODERNE

### Prérequis Partie B
```
⚠️ NE PAS COMMENCER AVANT:
✅ Phase 5 validée (GO)
✅ v8.0.1 taggé et déployé
✅ Backup complet effectué
```

---

## Phase 6 — Design System "Neural Glow"

### Objectif
Établir les fondations visuelles du nouveau design.

**Durée estimée :** 1-2 semaines

### 6.1 Fichiers à Créer

| Fichier | Description | Priorité |
|---------|-------------|----------|
| `src/styles/tokens.css` | Variables CSS design tokens | 🔴 |
| `src/styles/typography.css` | Classes typographiques | 🔴 |
| `src/styles/spacing.css` | Utilitaires d'espacement | 🔴 |
| `src/styles/animations.css` | Keyframes et transitions | 🟡 |
| `tailwind.config.js` | Intégration tokens | 🔴 |

### 6.2 Design Tokens Complets

```css
/* ===========================================
   src/styles/tokens.css
   AI ORCHESTRATOR - DESIGN TOKENS v2.0
   =========================================== */

:root {
  /* ─────────────────────────────────────────
     BACKGROUNDS - Profondeur et dimension
     ───────────────────────────────────────── */
  
  --bg-deep: linear-gradient(
    135deg, 
    #0a0a12 0%, 
    #12101f 25%,
    #1a1528 50%, 
    #12101f 75%,
    #0a0a12 100%
  );
  
  --bg-surface: rgba(255, 255, 255, 0.03);
  --bg-surface-hover: rgba(255, 255, 255, 0.06);
  --bg-surface-active: rgba(255, 255, 255, 0.08);
  
  --bg-glass: rgba(255, 255, 255, 0.05);
  --bg-glass-border: rgba(255, 255, 255, 0.08);
  
  --bg-sidebar: rgba(10, 10, 18, 0.95);
  --bg-sidebar-item-hover: rgba(139, 92, 246, 0.1);
  --bg-sidebar-item-active: rgba(139, 92, 246, 0.2);

  /* ─────────────────────────────────────────
     ACCENTS - Énergie et focus
     ───────────────────────────────────────── */
  
  --accent-primary: #8b5cf6;
  --accent-primary-hover: #a78bfa;
  --accent-primary-gradient: linear-gradient(
    135deg, 
    #6366f1 0%, 
    #8b5cf6 50%, 
    #a855f7 100%
  );
  
  --accent-glow-soft: 0 0 20px rgba(139, 92, 246, 0.2);
  --accent-glow-medium: 0 0 40px rgba(139, 92, 246, 0.3);
  --accent-glow-strong: 0 0 60px rgba(139, 92, 246, 0.4);
  
  --accent-secondary: #3b82f6;
  --accent-secondary-gradient: linear-gradient(
    135deg,
    #2563eb 0%,
    #3b82f6 100%
  );
  
  --accent-thinking: linear-gradient(
    90deg,
    #3b82f6 0%,
    #8b5cf6 25%,
    #ec4899 50%,
    #8b5cf6 75%,
    #3b82f6 100%
  );

  /* ─────────────────────────────────────────
     SEMANTIC - États et feedback
     ───────────────────────────────────────── */
  
  --color-success: #10b981;
  --color-success-bg: rgba(16, 185, 129, 0.1);
  --color-success-glow: 0 0 20px rgba(16, 185, 129, 0.3);
  
  --color-warning: #f59e0b;
  --color-warning-bg: rgba(245, 158, 11, 0.1);
  
  --color-error: #ef4444;
  --color-error-bg: rgba(239, 68, 68, 0.1);
  --color-error-glow: 0 0 20px rgba(239, 68, 68, 0.3);
  
  --color-info: #06b6d4;
  --color-info-bg: rgba(6, 182, 212, 0.1);

  /* ─────────────────────────────────────────
     TEXTE - Lisibilité et hiérarchie
     ───────────────────────────────────────── */
  
  --text-primary: #f8fafc;
  --text-secondary: rgba(248, 250, 252, 0.7);
  --text-tertiary: rgba(248, 250, 252, 0.5);
  --text-muted: rgba(248, 250, 252, 0.35);
  --text-on-accent: #ffffff;
  
  --text-gradient: linear-gradient(
    135deg,
    #f8fafc 0%,
    #a78bfa 100%
  );

  /* ─────────────────────────────────────────
     BORDERS
     ───────────────────────────────────────── */
  
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.15);
  --border-accent: rgba(139, 92, 246, 0.3);

  /* ─────────────────────────────────────────
     SHADOWS
     ───────────────────────────────────────── */
  
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.3);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.4);
  --shadow-glow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 40px rgba(139, 92, 246, 0.1);

  /* ─────────────────────────────────────────
     SPACING (base 4px)
     ───────────────────────────────────────── */
  
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */

  /* ─────────────────────────────────────────
     BORDER RADIUS
     ───────────────────────────────────────── */
  
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-2xl: 32px;
  --radius-full: 9999px;

  /* ─────────────────────────────────────────
     LAYOUT
     ───────────────────────────────────────── */
  
  --sidebar-width: 260px;
  --sidebar-width-collapsed: 72px;
  --header-height: 64px;
  
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;

  /* ─────────────────────────────────────────
     Z-INDEX SCALE
     ───────────────────────────────────────── */
  
  --z-base: 0;
  --z-dropdown: 1000;
  --z-sticky: 1100;
  --z-modal: 1200;
  --z-toast: 1300;
  --z-tooltip: 1400;

  /* ─────────────────────────────────────────
     TRANSITIONS
     ───────────────────────────────────────── */
  
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-bounce: 500ms cubic-bezier(0.68, -0.55, 0.265, 1.55);

  /* ─────────────────────────────────────────
     BREAKPOINTS (pour JS)
     ───────────────────────────────────────── */
  
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

### 6.3 Système Typographique

```css
/* ===========================================
   src/styles/typography.css
   =========================================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Font sizes - Échelle modulaire (1.25) */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.875rem;     /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */
  --text-5xl: 3rem;        /* 48px */
  
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
  
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}

/* Typography Classes */
.heading-1 {
  font-family: var(--font-sans);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.heading-2 {
  font-family: var(--font-sans);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--text-primary);
}

.heading-3 {
  font-family: var(--font-sans);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--text-primary);
}

.body-large {
  font-family: var(--font-sans);
  font-size: var(--text-lg);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
  color: var(--text-secondary);
}

.body-default {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--text-secondary);
}

.body-small {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--text-tertiary);
}

.label {
  font-family: var(--font-sans);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  line-height: var(--leading-normal);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--text-muted);
}

.code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
}
```

### Tests Phase 6

| # | Test | Attendu |
|---|------|---------|
| 1 | Tokens chargés | Pas d'erreur CSS |
| 2 | Fonts Inter/JetBrains | Chargées correctement |
| 3 | Variables accessibles | `getComputedStyle()` retourne valeurs |
| 4 | Pas de régression | UI existante fonctionne |

### Verdict Phase 6
```
[ ] PASS → Continuer Phase 7
[ ] FAIL → Corriger tokens
```

---

## Phase 7 — Composants Core

### Objectif
Créer les nouveaux composants réutilisables avec le design system.

**Durée estimée :** 2-3 semaines

### 7.1 Composants à Créer (Par Priorité)

#### 🔴 Priorité Haute (Semaine 1)

| Composant | Fichier | Description |
|-----------|---------|-------------|
| GlassCard | `components/ui/GlassCard.vue` | Carte glassmorphism |
| ModernButton | `components/ui/ModernButton.vue` | Bouton avec variants |
| StatusOrb | `components/ui/StatusOrb.vue` | Indicateur de statut animé |
| ChatInput | `components/ui/ChatInput.vue` | Input style Claude/ChatGPT |
| SidebarNav | `components/layout/SidebarNav.vue` | Navigation latérale |
| ErrorBoundary | `components/ui/ErrorBoundary.vue` | Capture erreurs JS |
| SkeletonLoader | `components/ui/SkeletonLoader.vue` | Loading states |
| Toast | `components/ui/Toast.vue` | Notifications |

#### 🟡 Priorité Moyenne (Semaine 2)

| Composant | Fichier | Description |
|-----------|---------|-------------|
| MetricCard | `components/ui/MetricCard.vue` | KPI avec icône et trend |
| AgentCard | `components/ui/AgentCard.vue` | Carte agent cliquable |
| PipelineSteps | `components/ui/PipelineSteps.vue` | SPEC→PLAN→EXEC→QA→FIX |
| ThinkingDots | `components/ui/ThinkingDots.vue` | Animation "réflexion" |
| CodeBlock | `components/ui/CodeBlock.vue` | Code avec syntax highlight |
| TopBar | `components/layout/TopBar.vue` | Header avec status |
| EmptyState | `components/ui/EmptyState.vue` | États vides élégants |

#### 🟢 Priorité Basse (Semaine 3)

| Composant | Fichier | Description |
|-----------|---------|-------------|
| ModalDialog | `components/ui/ModalDialog.vue` | Modal glassmorphism |
| Tooltip | `components/ui/Tooltip.vue` | Tooltips animés |
| Dropdown | `components/ui/Dropdown.vue` | Menu déroulant |
| Badge | `components/ui/Badge.vue` | Tags et labels |
| Avatar | `components/ui/Avatar.vue` | Avatar utilisateur/agent |
| ProgressBar | `components/ui/ProgressBar.vue` | Barre de progression |

### 7.2 Implémentation GlassCard

```vue
<!-- components/ui/GlassCard.vue -->
<template>
  <div 
    class="glass-card"
    :class="[
      `glass-card--${variant}`,
      { 'glass-card--hoverable': hoverable },
      { 'glass-card--active': active }
    ]"
    @click="hoverable && $emit('click')"
  >
    <div v-if="glow" class="glass-card__glow" />
    <div class="glass-card__content">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'elevated', 'bordered'].includes(v)
  },
  hoverable: Boolean,
  active: Boolean,
  glow: Boolean,
})

defineEmits(['click'])
</script>

<style scoped>
.glass-card {
  position: relative;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--bg-glass-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all var(--transition-normal);
}

.glass-card__content {
  position: relative;
  z-index: 1;
  padding: var(--space-6);
}

.glass-card__glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle at center,
    rgba(139, 92, 246, 0.1) 0%,
    transparent 50%
  );
  opacity: 0;
  transition: opacity var(--transition-normal);
  pointer-events: none;
}

/* Variants */
.glass-card--elevated {
  box-shadow: var(--shadow-lg);
}

.glass-card--bordered {
  border: 1px solid var(--border-default);
}

/* States */
.glass-card--hoverable {
  cursor: pointer;
}

.glass-card--hoverable:hover {
  background: var(--bg-surface-hover);
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.glass-card--hoverable:hover .glass-card__glow {
  opacity: 1;
}

.glass-card--active {
  border-color: var(--border-accent);
  box-shadow: var(--accent-glow-medium);
}
</style>
```

### 7.3 Implémentation ModernButton

```vue
<!-- components/ui/ModernButton.vue -->
<template>
  <button 
    class="modern-btn"
    :class="[
      `modern-btn--${variant}`,
      `modern-btn--${size}`,
      { 'modern-btn--loading': loading },
      { 'modern-btn--icon-only': iconOnly }
    ]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="modern-btn__loader">
      <span></span>
      <span></span>
      <span></span>
    </span>
    <span v-else class="modern-btn__content">
      <slot name="icon-left" />
      <span v-if="!iconOnly" class="modern-btn__text">
        <slot />
      </span>
      <slot name="icon-right" />
    </span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'ghost', 'danger'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  loading: Boolean,
  disabled: Boolean,
  iconOnly: Boolean,
})

defineEmits(['click'])
</script>

<style scoped>
.modern-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-weight: var(--font-medium);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
}

/* Sizes */
.modern-btn--sm {
  height: 32px;
  padding: 0 var(--space-3);
  font-size: var(--text-sm);
  border-radius: var(--radius-md);
}

.modern-btn--md {
  height: 40px;
  padding: 0 var(--space-5);
  font-size: var(--text-sm);
  border-radius: var(--radius-lg);
}

.modern-btn--lg {
  height: 48px;
  padding: 0 var(--space-6);
  font-size: var(--text-base);
  border-radius: var(--radius-lg);
}

/* Primary */
.modern-btn--primary {
  background: var(--accent-primary-gradient);
  color: var(--text-on-accent);
  box-shadow: var(--accent-glow-soft);
}

.modern-btn--primary:hover:not(:disabled) {
  box-shadow: var(--accent-glow-medium);
  transform: translateY(-1px);
}

/* Secondary */
.modern-btn--secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.modern-btn--secondary:hover:not(:disabled) {
  background: var(--bg-surface-hover);
  border-color: var(--border-strong);
}

/* Ghost */
.modern-btn--ghost {
  background: transparent;
  color: var(--text-secondary);
}

.modern-btn--ghost:hover:not(:disabled) {
  background: var(--bg-surface);
  color: var(--text-primary);
}

/* Danger */
.modern-btn--danger {
  background: var(--color-error);
  color: var(--text-on-accent);
}

.modern-btn--danger:hover:not(:disabled) {
  box-shadow: var(--color-error-glow);
}

/* Loading */
.modern-btn__loader {
  display: flex;
  gap: 4px;
}

.modern-btn__loader span {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: btn-loading 1.4s infinite ease-in-out both;
}

.modern-btn__loader span:nth-child(1) { animation-delay: -0.32s; }
.modern-btn__loader span:nth-child(2) { animation-delay: -0.16s; }

@keyframes btn-loading {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Disabled */
.modern-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* Icon only */
.modern-btn--icon-only.modern-btn--sm { width: 32px; padding: 0; }
.modern-btn--icon-only.modern-btn--md { width: 40px; padding: 0; }
.modern-btn--icon-only.modern-btn--lg { width: 48px; padding: 0; }
</style>
```

### 7.4 Implémentation StatusOrb

```vue
<!-- components/ui/StatusOrb.vue -->
<template>
  <div 
    class="status-orb"
    :class="[
      `status-orb--${status}`,
      `status-orb--${size}`,
      { 'status-orb--pulse': pulse }
    ]"
  >
    <span class="status-orb__core" />
    <span v-if="pulse" class="status-orb__ring" />
    <span v-if="label" class="status-orb__label">{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'active', 'success', 'warning', 'error', 'processing'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  pulse: Boolean,
  label: String,
})
</script>

<style scoped>
.status-orb {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.status-orb__core {
  position: relative;
  border-radius: 50%;
  transition: all var(--transition-normal);
}

.status-orb__ring {
  position: absolute;
  border-radius: 50%;
  animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Sizes */
.status-orb--sm .status-orb__core { width: 8px; height: 8px; }
.status-orb--md .status-orb__core { width: 10px; height: 10px; }
.status-orb--lg .status-orb__core { width: 14px; height: 14px; }

.status-orb--sm .status-orb__ring { width: 16px; height: 16px; top: -4px; left: -4px; }
.status-orb--md .status-orb__ring { width: 20px; height: 20px; top: -5px; left: -5px; }
.status-orb--lg .status-orb__ring { width: 28px; height: 28px; top: -7px; left: -7px; }

/* Status colors */
.status-orb--active .status-orb__core,
.status-orb--success .status-orb__core {
  background: var(--color-success);
  box-shadow: 0 0 12px var(--color-success);
}

.status-orb--active .status-orb__ring,
.status-orb--success .status-orb__ring {
  border: 2px solid var(--color-success);
}

.status-orb--processing .status-orb__core {
  background: var(--accent-primary);
  box-shadow: 0 0 12px var(--accent-primary);
}

.status-orb--processing .status-orb__ring {
  border: 2px solid var(--accent-primary);
}

.status-orb--error .status-orb__core {
  background: var(--color-error);
  box-shadow: 0 0 12px var(--color-error);
}

.status-orb--error .status-orb__ring {
  border: 2px solid var(--color-error);
}

.status-orb--warning .status-orb__core {
  background: var(--color-warning);
  box-shadow: 0 0 12px var(--color-warning);
}

.status-orb--default .status-orb__core {
  background: var(--text-muted);
}

/* Label */
.status-orb__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.status-orb--active .status-orb__label,
.status-orb--success .status-orb__label { color: var(--color-success); }
.status-orb--error .status-orb__label { color: var(--color-error); }
.status-orb--processing .status-orb__label { color: var(--accent-primary); }
.status-orb--warning .status-orb__label { color: var(--color-warning); }

/* Pulse animation */
@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}
</style>
```

### 7.5 Implémentation ErrorBoundary

```vue
<!-- components/ui/ErrorBoundary.vue -->
<template>
  <div v-if="error" class="error-boundary">
    <GlassCard variant="bordered">
      <div class="error-boundary__content">
        <div class="error-boundary__icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4m0 4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 class="error-boundary__title">Une erreur est survenue</h3>
        <p class="error-boundary__message">{{ error.message }}</p>
        <div class="error-boundary__actions">
          <ModernButton variant="primary" @click="retry">
            Réessayer
          </ModernButton>
          <ModernButton variant="ghost" @click="showDetails = !showDetails">
            {{ showDetails ? 'Masquer' : 'Détails' }}
          </ModernButton>
        </div>
        <pre v-if="showDetails" class="error-boundary__stack">{{ error.stack }}</pre>
      </div>
    </GlassCard>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import GlassCard from './GlassCard.vue'
import ModernButton from './ModernButton.vue'

const error = ref(null)
const showDetails = ref(false)

onErrorCaptured((err) => {
  error.value = err
  console.error('ErrorBoundary caught:', err)
  return false // Prevent propagation
})

const retry = () => {
  error.value = null
  showDetails.value = false
}
</script>

<style scoped>
.error-boundary__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-8);
}

.error-boundary__icon {
  color: var(--color-error);
  margin-bottom: var(--space-4);
}

.error-boundary__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.error-boundary__message {
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
}

.error-boundary__actions {
  display: flex;
  gap: var(--space-3);
}

.error-boundary__stack {
  margin-top: var(--space-6);
  padding: var(--space-4);
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  text-align: left;
  overflow-x: auto;
  max-width: 100%;
}
</style>
```

### 7.6 Implémentation SkeletonLoader

```vue
<!-- components/ui/SkeletonLoader.vue -->
<template>
  <div class="skeleton" :class="`skeleton--${variant}`">
    <div 
      v-for="i in lines" 
      :key="i"
      class="skeleton__line"
      :style="{ width: getLineWidth(i) }"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'card', 'avatar', 'button'].includes(v)
  },
  lines: {
    type: Number,
    default: 3
  }
})

const getLineWidth = (index) => {
  if (props.variant === 'card') return '100%'
  const widths = ['100%', '80%', '60%', '90%', '70%']
  return widths[(index - 1) % widths.length]
}
</script>

<style scoped>
.skeleton__line {
  height: 16px;
  background: linear-gradient(
    90deg,
    var(--bg-surface) 25%,
    var(--bg-surface-hover) 50%,
    var(--bg-surface) 75%
  );
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: skeleton-shimmer 1.5s infinite;
  margin-bottom: var(--space-2);
}

.skeleton__line:last-child {
  margin-bottom: 0;
}

.skeleton--card .skeleton__line {
  height: 120px;
  border-radius: var(--radius-lg);
}

.skeleton--avatar .skeleton__line {
  width: 48px !important;
  height: 48px;
  border-radius: var(--radius-full);
}

.skeleton--button .skeleton__line {
  width: 120px !important;
  height: 40px;
  border-radius: var(--radius-lg);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

### Tests Phase 7

| # | Test | Attendu |
|---|------|---------|
| 1 | GlassCard render | Affiche sans erreur |
| 2 | GlassCard hover | Animation glow |
| 3 | ModernButton variants | Tous styles corrects |
| 4 | ModernButton loading | Animation dots |
| 5 | StatusOrb pulse | Animation ring |
| 6 | ErrorBoundary catch | Erreur capturée et affichée |
| 7 | SkeletonLoader shimmer | Animation fluide |
| 8 | Tous composants | 0 erreur console |

### Verdict Phase 7
```
[ ] PASS → Continuer Phase 8
[ ] FAIL → Corriger composants
```

---

## Phase 8 — Refonte Pages Principales

### Objectif
Appliquer les nouveaux composants à toutes les pages.

**Durée estimée :** 3-4 semaines

### 8.1 Pages à Refondre (Par Priorité)

| Priorité | Page | Route | Complexité |
|----------|------|-------|------------|
| 🔴 1 | Dashboard | `/v8/dashboard` | Moyenne |
| 🔴 2 | Chat | `/v8/chat` | Haute |
| 🔴 3 | Runs | `/v8/runs` | Moyenne |
| 🟡 4 | Run Console | `/v8/runs/:id` | Haute |
| 🟡 5 | Agents | `/v8/agents` | Basse |
| 🟡 6 | Models | `/v8/models` | Basse |
| 🟡 7 | Tools | `/v8/tools` | Basse |
| 🟢 8 | Memory | `/v8/memory` | Moyenne |
| 🟢 9 | Audit | `/v8/audit` | Basse |
| 🟢 10 | System | `/v8/system` | Basse |
| 🟢 11 | Settings | `/v8/settings` | Basse |

### 8.2 Template Dashboard Refait

```vue
<!-- views/DashboardView.vue -->
<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="dashboard__header">
      <div>
        <h1 class="heading-1">AI Orchestrator v8</h1>
        <p class="body-default">Dashboard système et métriques temps réel</p>
      </div>
      <StatusOrb 
        :status="wsConnected ? 'active' : 'error'" 
        :label="wsConnected ? 'Connecté' : 'Déconnecté'"
        pulse
        size="lg"
      />
    </header>

    <!-- Metrics Grid -->
    <section class="dashboard__metrics">
      <MetricCard
        v-for="metric in metrics"
        :key="metric.id"
        :title="metric.title"
        :value="metric.value"
        :icon="metric.icon"
        :trend="metric.trend"
        :status="metric.status"
      />
    </section>

    <!-- Two Column Layout -->
    <div class="dashboard__grid">
      <!-- Recent Runs -->
      <GlassCard>
        <template #header>
          <h2 class="heading-3">Runs récents</h2>
        </template>
        <SkeletonLoader v-if="isLoading" :lines="5" />
        <EmptyState v-else-if="!recentRuns.length" message="Aucun run récent" />
        <RunList v-else :runs="recentRuns" />
      </GlassCard>

      <!-- Quick Actions -->
      <GlassCard>
        <template #header>
          <h2 class="heading-3">Actions rapides</h2>
        </template>
        <div class="dashboard__actions">
          <ModernButton 
            variant="primary" 
            size="lg" 
            @click="$router.push('/v8/chat')"
          >
            <template #icon-left><IconChat /></template>
            Nouveau Chat
          </ModernButton>
          <ModernButton 
            variant="secondary" 
            size="lg"
            @click="$router.push('/v8/runs')"
          >
            <template #icon-left><IconList /></template>
            Voir Runs
          </ModernButton>
          <ModernButton 
            variant="ghost" 
            size="lg"
            @click="$router.push('/v8/system')"
          >
            <template #icon-left><IconSettings /></template>
            Système
          </ModernButton>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRunStore } from '@/stores/runs'
import { useWebSocket } from '@/composables/useWebSocket'

const runStore = useRunStore()
const { isConnected: wsConnected } = useWebSocket()

const isLoading = computed(() => runStore.isLoading)
const recentRuns = computed(() => runStore.recentRuns.slice(0, 5))

const metrics = computed(() => [
  {
    id: 'active',
    title: 'Runs actifs',
    value: runStore.activeCount,
    icon: 'IconActivity',
    status: runStore.activeCount > 0 ? 'processing' : 'default'
  },
  {
    id: 'today',
    title: 'Runs (24h)',
    value: runStore.todayCount,
    icon: 'IconClock',
    trend: '+12%'
  },
  {
    id: 'success',
    title: 'Taux de succès',
    value: `${runStore.successRate}%`,
    icon: 'IconCheck',
    status: runStore.successRate > 90 ? 'success' : 'warning'
  },
  {
    id: 'ws',
    title: 'WebSocket',
    value: wsConnected ? 'Connecté' : 'Déconnecté',
    icon: 'IconWifi',
    status: wsConnected ? 'active' : 'error'
  }
])
</script>

<style scoped>
.dashboard {
  padding: var(--space-8);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-8);
}

.dashboard__metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.dashboard__grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-6);
}

.dashboard__actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

@media (max-width: 1024px) {
  .dashboard__grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

### 8.3 Règles de Refonte

```
✅ FAIRE:
- Utiliser UNIQUEMENT les nouveaux composants
- Wraper tout dans ErrorBoundary
- Ajouter SkeletonLoader pour loading
- Ajouter EmptyState pour données vides
- Utiliser les design tokens CSS
- Tester chaque page individuellement

❌ NE PAS FAIRE:
- Mélanger ancien et nouveau style
- Hardcoder des couleurs
- Oublier les états loading/error/empty
- Modifier plusieurs pages en même temps
```

### Tests Phase 8

| # | Page | Tests |
|---|------|-------|
| 1 | Dashboard | Métriques, actions, runs récents |
| 2 | Chat | Input, messages, sidebar |
| 3 | Runs | Liste, filtres, pagination |
| 4 | Run Console | Timeline, détails, logs |
| 5 | Agents | Cartes cliquables, modal |
| 6 | Models | Liste, sélection |
| 7 | Tools | Filtre fonctionnel |
| 8 | Memory | Collections, recherche |
| 9 | Toutes | 0 erreur console |

### Verdict Phase 8
```
[ ] PASS → Continuer Phase 9
[ ] FAIL → Corriger pages
```

---

## Phase 9 — Animations & Micro-interactions

### Objectif
Ajouter les animations qui donnent vie à l'interface.

**Durée estimée :** 1 semaine

### 9.1 Animations à Implémenter

| Animation | Composant | Déclencheur |
|-----------|-----------|-------------|
| Fade in | Pages | Route change |
| Slide up | Cards | Apparition |
| Pulse | StatusOrb | État actif |
| Shimmer | Skeleton | Loading |
| Glow | GlassCard | Hover |
| Thinking | ThinkingDots | Processing |
| Gradient shift | Accent elements | Continuous |

### 9.2 Fichier Animations

```css
/* src/styles/animations.css */

/* Page transitions */
.page-enter-active,
.page-leave-active {
  transition: all var(--transition-normal);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Card stagger */
.stagger-enter-active {
  transition: all var(--transition-normal);
}

.stagger-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

/* Thinking gradient */
@keyframes thinking-gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.thinking-animation {
  background: var(--accent-thinking);
  background-size: 200% 200%;
  animation: thinking-gradient 3s ease infinite;
}

/* Glow pulse */
@keyframes glow-pulse {
  0%, 100% { box-shadow: var(--accent-glow-soft); }
  50% { box-shadow: var(--accent-glow-strong); }
}

.glow-animation {
  animation: glow-pulse 2s ease-in-out infinite;
}

/* Float */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.float-animation {
  animation: float 3s ease-in-out infinite;
}

/* Typing cursor */
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.cursor-blink {
  animation: blink 1s step-end infinite;
}
```

### Tests Phase 9

| # | Test | Attendu |
|---|------|---------|
| 1 | Page transition | Smooth fade |
| 2 | Card hover | Glow effect |
| 3 | Thinking dots | Gradient animé |
| 4 | Skeleton shimmer | Fluide 60fps |
| 5 | Performance | Pas de jank |

### Verdict Phase 9
```
[ ] PASS → Continuer Phase 10
[ ] FAIL → Optimiser animations
```

---

## Phase 10 — Polish & Optimisation

### Objectif
Finaliser l'expérience et optimiser les performances.

**Durée estimée :** 1 semaine

### 10.1 Checklist Polish

| # | Item | Statut |
|---|------|--------|
| 1 | Responsive < 1024px | ☐ |
| 2 | Responsive < 768px | ☐ |
| 3 | Responsive < 640px | ☐ |
| 4 | Dark mode cohérent | ☐ |
| 5 | Focus states visibles | ☐ |
| 6 | Tab navigation | ☐ |
| 7 | Screen reader labels | ☐ |
| 8 | Color contrast WCAG AA | ☐ |
| 9 | Loading < 3s | ☐ |
| 10 | FPS > 55 animations | ☐ |

### 10.2 Optimisations Performance

```javascript
// Lazy loading des pages
const routes = [
  {
    path: '/v8/dashboard',
    component: () => import('@/views/DashboardView.vue')
  },
  // ...
]

// Code splitting des composants lourds
const CodeBlock = defineAsyncComponent(() => 
  import('@/components/ui/CodeBlock.vue')
)
```

### 10.3 Accessibilité

```vue
<!-- Exemple accessible -->
<ModernButton 
  aria-label="Créer un nouveau chat"
  @click="createChat"
>
  <template #icon-left>
    <IconPlus aria-hidden="true" />
  </template>
  Nouveau Chat
</ModernButton>

<!-- Skip link -->
<a href="#main-content" class="skip-link">
  Aller au contenu principal
</a>
```

### Tests Phase 10

| # | Test | Outil | Seuil |
|---|------|-------|-------|
| 1 | Lighthouse Performance | Chrome DevTools | > 90 |
| 2 | Lighthouse Accessibility | Chrome DevTools | > 90 |
| 3 | WCAG Contrast | axe DevTools | Pass |
| 4 | Keyboard nav | Manuel | Toutes actions |
| 5 | Mobile responsive | Chrome DevTools | Pas de scroll H |

### Verdict Phase 10
```
[ ] PASS → Continuer Phase 11
[ ] FAIL → Corriger issues
```

---

## Phase 11 — Tests Finaux & Release v8.1

### Objectif
Certifier v8.1.0 pour release.

**Durée estimée :** 2-3 jours

### 11.1 Tests Complets

#### Tests Fonctionnels
| # | Test | Durée | Statut |
|---|------|-------|--------|
| 1 | Parcours complet nouveau user | 10 min | ☐ |
| 2 | Création run + suivi | 5 min | ☐ |
| 3 | Navigation toutes pages | 5 min | ☐ |
| 4 | Toutes actions boutons | 10 min | ☐ |
| 5 | WebSocket 30 min stable | 30 min | ☐ |
| 6 | Session 1h sans expiration | 1h | ☐ |

#### Tests Non-Régression
| # | Test | Attendu | Statut |
|---|------|---------|--------|
| 1 | Toutes fonctions v8.0.1 | Fonctionnent | ☐ |
| 2 | API endpoints | Répondent | ☐ |
| 3 | Auth flow | Fonctionne | ☐ |
| 4 | Tools execution | Fonctionne | ☐ |

#### Tests Qualité
| # | Critère | Seuil | Statut |
|---|---------|-------|--------|
| 1 | Erreurs console | 0 | ☐ |
| 2 | Warnings console | < 3 | ☐ |
| 3 | Lighthouse Perf | > 90 | ☐ |
| 4 | Lighthouse A11y | > 90 | ☐ |
| 5 | Bundle size | < 500KB | ☐ |

### 11.2 Livrables Release

```
✅ CHANGELOG_v8.1.0.md
✅ README.md mis à jour
✅ Documentation composants
✅ Tag git v8.1.0
✅ Backup pre-deploy
✅ Rollback plan documenté
```

### 11.3 Déploiement

```bash
# 1. Backup
./scripts/backup.sh pre-v8.1.0

# 2. Build production
npm run build

# 3. Tag
git tag -a v8.1.0 -m "AI Orchestrator v8.1.0 - UI Refresh"
git push origin v8.1.0

# 4. Deploy
./scripts/deploy.sh production

# 5. Smoke tests
./scripts/smoke-test.sh

# 6. Monitor 30 min
# Si problème → rollback
```

### Verdict Final Phase 11

```
╔══════════════════════════════════════════════════════════════════╗
║  CERTIFICATION v8.1.0                                            ║
╠══════════════════════════════════════════════════════════════════╣
║  [ ] Tous tests fonctionnels PASS                                ║
║  [ ] Tous tests non-régression PASS                              ║
║  [ ] Tous tests qualité PASS                                     ║
║  [ ] Tous livrables prêts                                        ║
║  [ ] Rollback plan validé                                        ║
╠══════════════════════════════════════════════════════════════════╣
║  DÉCISION:                                                       ║
║  [ ] ✅ RELEASE v8.1.0                                           ║
║  [ ] ❌ REPORT - Retour phase ___                                ║
╚══════════════════════════════════════════════════════════════════╝
```

---

# ANNEXES

## Annexe A — Inventaire des Bugs

### Bugs Critiques (P0)

| ID | Bug | Composant | Phase Fix |
|----|-----|-----------|-----------|
| BUG-001 | Runs bloqués RUNNING | WS + Store | Phase 1-2 |
| BUG-002 | Spinner infini | Chat UI | Phase 1-2 |
| BUG-003 | Page Models erreur JS | ModelsView | Phase 3 |
| BUG-004 | Page Memory vide | MemoryView | Phase 3 |
| BUG-005 | Session expire | Auth | Phase 4 |
| BUG-006 | Run Inspector incomplet | RunInspector | Phase 1-2 |

### Bugs Modérés (P1-P2)

| ID | Bug | Composant | Phase Fix |
|----|-----|-----------|-----------|
| BUG-007 | Run Console détails vide | RunConsole | Phase 8 |
| BUG-008 | Agents non cliquables | AgentsView | Phase 8 |
| BUG-009 | Filtre Tools cassé | ToolsView | Phase 3 |
| BUG-010 | 2 UIs incohérentes | Layout | Phase 8 |
| BUG-011 | Sidebar "Aucune conversation" | Sidebar | Phase 3 |

---

## Annexe B — Design Tokens Complets

Voir [Phase 6 - Design Tokens](#62-design-tokens-complets)

---

## Annexe C — Composants à Créer

| Composant | Fichier | Phase | Priorité |
|-----------|---------|-------|----------|
| GlassCard | `ui/GlassCard.vue` | 7 | 🔴 |
| ModernButton | `ui/ModernButton.vue` | 7 | 🔴 |
| StatusOrb | `ui/StatusOrb.vue` | 7 | 🔴 |
| ChatInput | `ui/ChatInput.vue` | 7 | 🔴 |
| ErrorBoundary | `ui/ErrorBoundary.vue` | 7 | 🔴 |
| SkeletonLoader | `ui/SkeletonLoader.vue` | 7 | 🔴 |
| Toast | `ui/Toast.vue` | 7 | 🔴 |
| EmptyState | `ui/EmptyState.vue` | 7 | 🔴 |
| MetricCard | `ui/MetricCard.vue` | 7 | 🟡 |
| AgentCard | `ui/AgentCard.vue` | 7 | 🟡 |
| PipelineSteps | `ui/PipelineSteps.vue` | 7 | 🟡 |
| ThinkingDots | `ui/ThinkingDots.vue` | 7 | 🟡 |
| CodeBlock | `ui/CodeBlock.vue` | 7 | 🟡 |
| SidebarNav | `layout/SidebarNav.vue` | 7 | 🔴 |
| TopBar | `layout/TopBar.vue` | 7 | 🟡 |
| ModalDialog | `ui/ModalDialog.vue` | 7 | 🟢 |
| Tooltip | `ui/Tooltip.vue` | 7 | 🟢 |
| Dropdown | `ui/Dropdown.vue` | 7 | 🟢 |

---

## Annexe D — Checklist de Validation

### Checklist Stabilisation (v8.0.1)

```
PHASE 0 - INVENTAIRE
[ ] Arborescence documentée
[ ] Composants identifiés
[ ] Risques listés

PHASE 1 - WEBSOCKET
[ ] EventEmitter centralisé
[ ] Events v8 implémentés
[ ] Compat v7.1 maintenue
[ ] Tests 5/5 PASS

PHASE 2 - RUN STORE
[ ] Store refondé
[ ] Watchdog implémenté
[ ] Tests 5/5 PASS

PHASE 3 - PAGES
[ ] Models fix
[ ] Memory fix
[ ] Tools filtre fix
[ ] Sidebar fix
[ ] Tests 5/5 PASS

PHASE 4 - SESSION
[ ] Refresh token auto
[ ] Notification expiration
[ ] Tests 4/4 PASS

PHASE 5 - VALIDATION
[ ] Tests fonctionnels OK
[ ] Tests non-régression OK
[ ] Tests qualité OK
[ ] Tag v8.0.1 créé
```

### Checklist UI/UX (v8.1.0)

```
PHASE 6 - DESIGN SYSTEM
[ ] tokens.css créé
[ ] typography.css créé
[ ] Fonts chargées
[ ] Tests 4/4 PASS

PHASE 7 - COMPOSANTS
[ ] GlassCard OK
[ ] ModernButton OK
[ ] StatusOrb OK
[ ] ErrorBoundary OK
[ ] SkeletonLoader OK
[ ] Tests 8/8 PASS

PHASE 8 - PAGES
[ ] Dashboard refait
[ ] Chat refait
[ ] Runs refait
[ ] Toutes pages OK
[ ] Tests 9/9 PASS

PHASE 9 - ANIMATIONS
[ ] Transitions OK
[ ] Micro-interactions OK
[ ] Performance OK

PHASE 10 - POLISH
[ ] Responsive OK
[ ] Accessibilité OK
[ ] Performance > 90

PHASE 11 - RELEASE
[ ] Tests finaux OK
[ ] Livrables OK
[ ] Tag v8.1.0 créé
[ ] Déploiement OK
```

---

## 📞 Support

| Contact | Rôle | Responsabilité |
|---------|------|----------------|
| Lalpha | Owner | Décisions, validation |
| Claude Code | Dev | Implémentation |
| Claude (Claude.ai) | Advisor | Review, documentation |

---

## 📝 Historique des Révisions

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 1.0 | 2026-02-03 | Claude | Document initial fusionné |

---

**FIN DU DOCUMENT**

```
╔══════════════════════════════════════════════════════════════════╗
║  AI ORCHESTRATOR v8.1 MASTER PLAYBOOK                            ║
║  Document de référence unique                                    ║
║  Stabilisation + Refonte UI/UX                                   ║
╚══════════════════════════════════════════════════════════════════╝
```
