# 🎨 AI ORCHESTRATOR v8.1.0 — UI/UX ROADMAP & CRQ
## Plan de Corrections et Implémentation Phase B

**Document de référence pour la refonte UI "Neural Glow"**

---

| Métadonnée | Valeur |
|------------|--------|
| **Numéro CRQ** | CRQ-2026-0203-UI-001 |
| **Version actuelle** | 8.0.1 (Phase A COMPLÉTÉE) |
| **Version cible** | 8.1.0 |
| **Date création** | 2026-02-03 |
| **Auteur** | Lalpha (root3d) |
| **Environnement** | Production - ai.4lb.ca |
| **Statut** | 📋 Planifié |

---

## 📊 ÉTAT ACTUEL — CONFORMANCE ANALYSIS

### ✅ Phase A — Stabilisation (COMPLÉTÉE)

| Composant | Statut | Notes |
|-----------|--------|-------|
| WebSocket v8 EventEmitter | ✅ | Centralisé avec run_id tracking |
| Terminal event guarantees | ✅ | complete/error garantis |
| Event normalization v7→v8 | ✅ | Compatibilité maintenue |
| Run Store Pinia | ✅ | Multi-run, watchdog, cleanup |
| 5-phase workflow | ✅ | SPEC→PLAN→EXECUTE→VERIFY→REPAIR |
| Session management | ✅ | Auth flow fonctionnel |
| Error handling | ✅ | Recovery mechanisms |

### ❌ Phase B — UI/UX Refactoring (À IMPLÉMENTER)

| Composant | Statut | Priorité |
|-----------|--------|----------|
| Design System "Neural Glow" | ❌ | 🔴 CRITIQUE |
| Design Tokens (tokens.css) | ❌ | 🔴 CRITIQUE |
| Typography System | ❌ | 🔴 CRITIQUE |
| 18 UI Components | ❌ | 🔴 CRITIQUE |
| Refonte 11 Pages | ❌ | 🟡 HAUTE |
| Animations & Micro-interactions | ❌ | 🟢 MOYENNE |
| Polish & Optimisation | ❌ | 🟢 BASSE |

---

## 📁 STRUCTURE CIBLE

```
frontend/src/
├── styles/                          # ❌ À CRÉER
│   ├── tokens.css                   # Design tokens
│   ├── typography.css               # Typography system
│   ├── spacing.css                  # Spacing utilities
│   └── animations.css               # Keyframes & transitions
│
├── components/
│   ├── ui/                          # ❌ À CRÉER
│   │   ├── GlassCard.vue            # P0 - Glassmorphism cards
│   │   ├── ModernButton.vue         # P0 - Boutons avec variants
│   │   ├── StatusOrb.vue            # P0 - Indicateurs d'état
│   │   ├── ChatInput.vue            # P0 - Input chat moderne
│   │   ├── ErrorBoundary.vue        # P0 - Gestion erreurs
│   │   ├── SkeletonLoader.vue       # P0 - Loading states
│   │   ├── Toast.vue                # P0 - Notifications (existant)
│   │   ├── EmptyState.vue           # P0 - États vides
│   │   ├── MetricCard.vue           # P1 - Cards métriques
│   │   ├── AgentCard.vue            # P1 - Cards agents
│   │   ├── PipelineSteps.vue        # P1 - Pipeline visualization
│   │   ├── ThinkingDots.vue         # P1 - Animation thinking
│   │   ├── CodeBlock.vue            # P1 - Code blocks améliorés
│   │   ├── ModalDialog.vue          # P2 - Modals
│   │   ├── Tooltip.vue              # P2 - Tooltips
│   │   └── Dropdown.vue             # P2 - Dropdowns
│   │
│   ├── layout/                      # ❌ À CRÉER
│   │   ├── SidebarNav.vue           # Navigation sidebar
│   │   └── TopBar.vue               # Barre supérieure
│   │
│   ├── chat/                        # ✅ EXISTE
│   └── common/                      # ✅ EXISTE (Toast, StatusBar)
│
└── views/v8/                        # ✅ EXISTE → À REFONDRE
    ├── DashboardView.vue
    ├── ChatView.vue
    ├── RunsView.vue
    ├── RunConsoleView.vue
    ├── AgentsView.vue
    ├── ModelsView.vue
    ├── ToolsView.vue (racine)
    ├── MemoryView.vue
    ├── AuditView.vue
    ├── SystemView.vue
    └── SettingsView.vue (racine)
```

---

## 🔧 CRQ DÉTAILLÉES PAR PHASE

---

## CRQ-UI-001: Design System Foundation

### Phase 6.1 — Design Tokens

**Fichier:** `src/styles/tokens.css`

**Objectif:** Établir les variables CSS fondamentales du design "Neural Glow"

**Tokens à implémenter:**

```css
:root {
  /* BACKGROUNDS */
  --bg-deep: linear-gradient(135deg, #0a0a12 0%, #12101f 25%, #1a1528 50%, #12101f 75%, #0a0a12 100%);
  --bg-surface: rgba(255, 255, 255, 0.03);
  --bg-surface-hover: rgba(255, 255, 255, 0.06);
  --bg-glass: rgba(255, 255, 255, 0.05);
  --bg-glass-border: rgba(255, 255, 255, 0.08);
  --bg-sidebar: rgba(10, 10, 18, 0.95);
  
  /* ACCENTS */
  --accent-primary: #8b5cf6;
  --accent-primary-hover: #a78bfa;
  --accent-primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  --accent-glow-soft: 0 0 20px rgba(139, 92, 246, 0.2);
  --accent-glow-medium: 0 0 40px rgba(139, 92, 246, 0.3);
  
  /* SEMANTIC */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #06b6d4;
  
  /* TEXT */
  --text-primary: #f8fafc;
  --text-secondary: rgba(248, 250, 252, 0.7);
  --text-tertiary: rgba(248, 250, 252, 0.5);
  
  /* BORDERS & SHADOWS */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --shadow-glow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(139, 92, 246, 0.1);
  
  /* SPACING (base 4px) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  
  /* RADIUS */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  
  /* TRANSITIONS */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Tests:**
- [ ] Variables chargées sans erreur
- [ ] Tokens accessibles dans tous les composants
- [ ] Pas de conflits avec Tailwind existant

**Verdict:** [ ] PASS [ ] FAIL

---

### Phase 6.2 — Typography System

**Fichier:** `src/styles/typography.css`

**Classes à implémenter:**

```css
.heading-1 { font-size: 2rem; font-weight: 700; line-height: 1.2; }
.heading-2 { font-size: 1.5rem; font-weight: 600; line-height: 1.3; }
.heading-3 { font-size: 1.25rem; font-weight: 600; line-height: 1.4; }
.body-default { font-size: 0.9375rem; line-height: 1.6; }
.body-small { font-size: 0.8125rem; line-height: 1.5; }
.label { font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.code { font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; }
```

**Fonts requises:**
- Inter (ou Satoshi) pour le texte
- JetBrains Mono pour le code

**Tests:**
- [ ] Fonts chargées correctement
- [ ] Classes typographiques fonctionnelles
- [ ] Rendu cohérent sur Chrome, Firefox, Safari

---

### Phase 6.3 — Tailwind Integration

**Fichier:** `tailwind.config.js`

**Modifications:**

```javascript
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Mapping vers les CSS variables
        primary: {
          DEFAULT: 'var(--accent-primary)',
          hover: 'var(--accent-primary-hover)',
        },
        surface: 'var(--bg-surface)',
        'surface-hover': 'var(--bg-surface-hover)',
      },
      boxShadow: {
        'glow': 'var(--shadow-glow)',
        'glow-soft': 'var(--accent-glow-soft)',
      },
      borderRadius: {
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
      },
    },
  },
  plugins: [],
}
```

---

## CRQ-UI-002: Core UI Components

### Phase 7.1 — GlassCard Component

**Fichier:** `src/components/ui/GlassCard.vue`

**Props:**
- `variant`: 'default' | 'bordered' | 'elevated' | 'interactive'
- `padding`: 'none' | 'sm' | 'md' | 'lg'
- `glow`: boolean

**Features:**
- Backdrop blur effect
- Subtle border with glassmorphism
- Hover glow animation
- Slots: default, header, footer

**Estimation:** 2-3h

---

### Phase 7.2 — ModernButton Component

**Fichier:** `src/components/ui/ModernButton.vue`

**Props:**
- `variant`: 'primary' | 'secondary' | 'ghost' | 'danger'
- `size`: 'sm' | 'md' | 'lg'
- `loading`: boolean
- `disabled`: boolean
- `iconOnly`: boolean

**Features:**
- Gradient backgrounds
- Glow effects on hover
- Loading animation (3 dots)
- Icon slots (left/right)

**Estimation:** 2-3h

---

### Phase 7.3 — StatusOrb Component

**Fichier:** `src/components/ui/StatusOrb.vue`

**Props:**
- `status`: 'default' | 'active' | 'success' | 'warning' | 'error' | 'processing'
- `size`: 'sm' | 'md' | 'lg'
- `pulse`: boolean
- `label`: string

**Features:**
- Animated pulse ring
- Color-coded states
- Optional label
- Glow effect

**Estimation:** 1-2h

---

### Phase 7.4 — Autres Composants P0

| Composant | Fichier | Estimation |
|-----------|---------|------------|
| ErrorBoundary | `ui/ErrorBoundary.vue` | 2h |
| SkeletonLoader | `ui/SkeletonLoader.vue` | 1h |
| EmptyState | `ui/EmptyState.vue` | 1h |
| ChatInput | `ui/ChatInput.vue` | 3h |

---

## CRQ-UI-003: Page Refactoring

### Phase 8.1 — Dashboard Refonte

**Fichier:** `src/views/v8/DashboardView.vue`

**Changements requis:**

| Avant (Tailwind direct) | Après (Design System) |
|------------------------|----------------------|
| `bg-gray-800/50 border border-gray-700/50 rounded-xl` | `<GlassCard>` |
| `<div class="w-3 h-3 rounded-full bg-green-400">` | `<StatusOrb status="active" pulse />` |
| Boutons Tailwind | `<ModernButton variant="primary">` |
| `text-2xl font-bold` | `class="heading-1"` |
| Empty div pour loading | `<SkeletonLoader />` |
| `text-center text-gray-500` | `<EmptyState message="..." />` |

**Estimation:** 4-6h

---

### Phase 8.2 — Chat Refonte

**Fichier:** `src/views/v8/ChatView.vue`

**Composants à utiliser:**
- `GlassCard` pour le conteneur principal
- `ChatInput` pour l'input
- `ThinkingDots` pour l'état de réflexion
- `CodeBlock` pour les blocs de code
- `StatusOrb` pour l'état de connexion

**Estimation:** 6-8h

---

### Phase 8.3 — Autres Pages

| Page | Route | Complexité | Estimation |
|------|-------|------------|------------|
| Runs | `/v8/runs` | Moyenne | 3-4h |
| Run Console | `/v8/runs/:id` | Haute | 5-6h |
| Agents | `/v8/agents` | Basse | 2-3h |
| Models | `/v8/models` | Basse | 2-3h |
| Tools | `/tools` | Basse | 2-3h |
| Memory | `/v8/memory` | Moyenne | 3-4h |
| Audit | `/v8/audit` | Basse | 2-3h |
| System | `/v8/system` | Basse | 2-3h |
| Settings | `/settings` | Basse | 2-3h |

---

## CRQ-UI-004: Animations & Polish

### Phase 9 — Animations

**Fichier:** `src/styles/animations.css`

```css
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

@keyframes thinking-gradient {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Phase 10 — Polish

- [ ] Responsive mobile
- [ ] Accessibilité (WCAG AA)
- [ ] Lighthouse Performance > 90
- [ ] Lighthouse Accessibility > 90
- [ ] Bundle size < 500KB

---

## 📅 PLANNING ESTIMÉ

| Phase | Durée | Dépendances |
|-------|-------|-------------|
| 6. Design System | 3-5 jours | Aucune |
| 7. Core Components | 5-7 jours | Phase 6 |
| 8. Page Refactoring | 10-14 jours | Phase 7 |
| 9. Animations | 2-3 jours | Phase 8 |
| 10. Polish | 3-5 jours | Phase 9 |
| 11. Tests & Release | 2-3 jours | Phase 10 |

**Total estimé:** 25-37 jours (5-8 semaines)

---

## ✅ CHECKLIST DE VALIDATION

### Phase 6 — Design System
- [ ] `tokens.css` créé et importé
- [ ] `typography.css` créé et importé
- [ ] `animations.css` créé et importé
- [ ] Tailwind config mis à jour
- [ ] Fonts chargées

### Phase 7 — Composants
- [ ] GlassCard fonctionnel
- [ ] ModernButton fonctionnel
- [ ] StatusOrb fonctionnel
- [ ] ErrorBoundary fonctionnel
- [ ] SkeletonLoader fonctionnel
- [ ] EmptyState fonctionnel
- [ ] Tous composants sans erreur console

### Phase 8 — Pages
- [ ] Dashboard refait
- [ ] Chat refait
- [ ] Toutes 11 pages refaites
- [ ] Navigation cohérente
- [ ] 0 erreur console

### Phase 9-10 — Polish
- [ ] Animations fluides
- [ ] Responsive OK
- [ ] Lighthouse > 90

### Phase 11 — Release
- [ ] Tests fonctionnels OK
- [ ] Tag v8.1.0 créé
- [ ] Déploiement OK

---

## 🚨 RÈGLES STRICTES

```
╔══════════════════════════════════════════════════════════════════╗
║  INTERDICTIONS                                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  ❌ Commencer Phase 8 avant Phase 7 complète                     ║
║  ❌ Modifier des pages sans utiliser les nouveaux composants     ║
║  ❌ Supprimer les classes Tailwind sans remplacement             ║
║  ❌ Casser la compatibilité Phase A (WebSocket, Store)           ║
║  ❌ Livrer sans tests                                            ║
╠══════════════════════════════════════════════════════════════════╣
║  OBLIGATIONS                                                      ║
╠══════════════════════════════════════════════════════════════════╣
║  ✅ Backup avant chaque phase                                    ║
║  ✅ Tests après chaque composant                                 ║
║  ✅ Commits atomiques (1 composant = 1 commit)                   ║
║  ✅ Utiliser les CSS variables, pas de couleurs hardcodées       ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 📞 CONTACTS

| Rôle | Contact | Responsabilité |
|------|---------|----------------|
| Owner | Lalpha | Décisions, validation |
| Dev | Claude Code | Implémentation |
| Advisor | Claude (claude.ai) | Review, documentation |

---

**FIN DU DOCUMENT CRQ**

```
╔══════════════════════════════════════════════════════════════════╗
║  AI ORCHESTRATOR v8.1.0 — UI/UX ROADMAP                          ║
║  CRQ-2026-0203-UI-001                                            ║
║  Phase B: Design System "Neural Glow"                            ║
╚══════════════════════════════════════════════════════════════════╝
```
