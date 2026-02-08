import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // Redirect root to v8 dashboard
  {
    path: '/',
    redirect: '/v8/dashboard',
  },
  // Main Chat (v7.1 compatible - legacy)
  {
    path: '/v7',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
  },
  {
    path: '/tools',
    name: 'tools',
    component: () => import('@/views/ToolsView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
  },
  {
    path: '/learning',
    name: 'learning',
    component: () => import('@/views/LearningView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
  },

  // v8 Routes (Wrapped in V8Layout)
  {
    path: '/v8',
    component: () => import('@/layouts/V8Layout.vue'),
    redirect: '/v8/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/v8/DashboardView.vue'),
      },
      {
        path: 'chat',
        name: 'v8-chat',
        component: () => import('@/views/v8/ChatView.vue'),
      },
      {
        path: 'runs',
        name: 'runs',
        component: () => import('@/views/v8/RunsView.vue'),
      },
      {
        path: 'runs/:id',
        name: 'run-console',
        component: () => import('@/views/v8/RunConsoleView.vue'),
        props: true,
      },
      {
        path: 'agents',
        name: 'agents',
        component: () => import('@/views/v8/AgentsView.vue'),
      },
      {
        path: 'models',
        name: 'models',
        component: () => import('@/views/v8/ModelsView.vue'),
      },
      {
        path: 'memory',
        name: 'memory',
        component: () => import('@/views/v8/MemoryView.vue'),
      },
      {
        path: 'audit',
        name: 'audit',
        component: () => import('@/views/v8/AuditView.vue'),
      },
      {
        path: 'system',
        name: 'system',
        component: () => import('@/views/v8/SystemView.vue'),
      },
      {
        path: 'tools',
        name: 'v8-tools',
        component: () => import('@/views/ToolsView.vue'),
      },
      {
        path: 'settings',
        name: 'v8-settings',
        component: () => import('@/views/SettingsView.vue'),
      },
      {
        path: 'test-ui',
        name: 'test-ui',
        component: () => import('@/views/TestUIView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// V8: Authentication guard for /v8 routes
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  // Check if route is under /v8
  if (to.path.startsWith('/v8')) {
    // Allow access to v8 only if authenticated
    if (!auth.isAuthenticated) {
      // Validate redirect path to prevent open redirect
      const redirect = to.fullPath.startsWith('/') ? to.fullPath : '/v8/dashboard'
      next({ name: 'login', query: { redirect } })
      return
    }
  }

  // Always allow access to login page
  if (to.name === 'login') {
    next()
    return
  }

  next()
})

export default router
