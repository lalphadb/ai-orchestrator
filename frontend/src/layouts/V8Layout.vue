<template>
  <div class="h-screen flex bg-gray-900 text-gray-100">
    <!-- Sidebar Navigation -->
    <aside class="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
      <!-- Logo -->
      <div class="p-4 border-b border-gray-800">
        <router-link to="/" class="flex items-center gap-3 hover:opacity-80 transition">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center"
          >
            <span class="text-lg font-bold">AI</span>
          </div>
          <div>
            <div class="font-semibold">Orchestrator</div>
            <div class="text-xs text-gray-500">v8.1.0</div>
          </div>
        </router-link>
      </div>

      <!-- Nav Links -->
      <nav class="flex-1 py-4 overflow-y-auto">
        <div class="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Principal
        </div>
        <router-link
          v-for="item in mainNav"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link-active': isActive(item.to) }"
        >
          <component :is="item.icon" class="w-5 h-5" />
          {{ item.label }}
        </router-link>

        <div class="px-3 mt-6 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Monitoring
        </div>
        <router-link
          v-for="item in monitoringNav"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link-active': isActive(item.to) }"
        >
          <component :is="item.icon" class="w-5 h-5" />
          {{ item.label }}
        </router-link>

        <div class="px-3 mt-6 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Configuration
        </div>
        <router-link
          v-for="item in configNav"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link-active': isActive(item.to) }"
        >
          <component :is="item.icon" class="w-5 h-5" />
          {{ item.label }}
        </router-link>
      </nav>

      <!-- Status -->
      <div class="p-4 border-t border-gray-800">
        <div class="flex items-center gap-2 text-sm">
          <div class="w-2 h-2 rounded-full transition-colors" :class="wsStatusClass"></div>
          <span class="text-gray-400">{{ wsStatusText }}</span>
        </div>
        <div v-if="auth.user" class="mt-2 text-xs text-gray-500 truncate">
          {{ auth.user.username || auth.user }}
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, h, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const chat = useChatStore()
const auth = useAuthStore()

// ===== FIX: Initialize WebSocket at layout level =====
// Previously only ChatView called initWebSocket(), causing
// "Disconnected" status on all other pages.
onMounted(() => {
  if (auth.isAuthenticated) {
    chat.initWebSocket()
  }
})

// Also connect when auth state changes (e.g. after login redirect)
watch(
  () => auth.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      chat.initWebSocket()
    }
  }
)

const wsStatusClass = computed(() => {
  switch (chat.wsState) {
    case 'connected':
      return 'bg-green-400'
    case 'connecting':
      return 'bg-yellow-400 animate-pulse'
    default:
      return 'bg-red-400'
  }
})

const wsStatusText = computed(() => {
  switch (chat.wsState) {
    case 'connected':
      return 'Connecté'
    case 'connecting':
      return 'Connexion...'
    default:
      return 'Déconnecté'
  }
})

// Icon components (inline SVG)
const DashboardIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
      }),
    ]),
}

const RunsIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z',
      }),
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      }),
    ]),
}

const ChatIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
      }),
    ]),
}

const AgentsIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
      }),
    ]),
}

const ModelsIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
      }),
    ]),
}

const ToolsIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
      }),
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z',
      }),
    ]),
}

const MemoryIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
      }),
    ]),
}

const AuditIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      }),
    ]),
}

const SystemIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
      }),
    ]),
}

const SettingsIcon = {
  render: () =>
    h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4',
      }),
    ]),
}

const mainNav = [
  { to: '/v8/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/v8/chat', label: 'Chat', icon: ChatIcon },
  { to: '/v8/runs', label: 'Runs', icon: RunsIcon },
]

const monitoringNav = [
  { to: '/v8/agents', label: 'Agents', icon: AgentsIcon },
  { to: '/v8/models', label: 'Models', icon: ModelsIcon },
  { to: '/v8/tools', label: 'Tools', icon: ToolsIcon },
  { to: '/v8/memory', label: 'Memory', icon: MemoryIcon },
  { to: '/v8/audit', label: 'Audit', icon: AuditIcon },
  { to: '/v8/system', label: 'System', icon: SystemIcon },
]

const configNav = [{ to: '/v8/settings', label: 'Settings', icon: SettingsIcon }]

const isActive = (to) => {
  return route.path === to || (to !== '/' && route.path.startsWith(to))
}
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors;
}

.nav-link-active {
  background: rgba(139, 92, 246, 0.2);
  color: white;
  border-left: 2px solid var(--accent-primary);
}
</style>
