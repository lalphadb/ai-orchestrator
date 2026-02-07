<template>
  <div class="flex items-center gap-3">
    <!-- Health indicator -->
    <div
      class="flex items-center gap-1.5 px-2 py-1 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors"
      @click="showDetails = !showDetails"
    >
      <span
        class="w-2 h-2 rounded-full"
        :class="{
          'bg-green-500': system.isHealthy,
          'bg-yellow-500 animate-pulse': system.health?.status === 'degraded',
          'bg-red-500': system.health?.status === 'error' || !system.health,
        }"
      ></span>
      <span class="text-xs text-gray-400">
        {{ statusLabel }}
      </span>
    </div>

    <!-- Details dropdown -->
    <Teleport to="body">
      <div
        v-if="showDetails"
        class="fixed top-14 right-4 z-50 p-4 bg-gray-800 border border-gray-700 rounded-xl shadow-xl min-w-64"
      >
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-medium text-white">État système</h4>
          <button class="p-1 text-gray-400 hover:text-white" @click="refresh">
            <svg
              class="w-4 h-4"
              :class="{ 'animate-spin': loading }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>

        <div class="space-y-2">
          <!-- Ollama -->
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">Ollama</span>
            <span :class="system.ollamaStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ system.ollamaStatus }}
            </span>
          </div>

          <!-- Database -->
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">Database</span>
            <span :class="system.dbStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ system.dbStatus }}
            </span>
          </div>

          <!-- Stats -->
          <div v-if="system.stats" class="pt-2 mt-2 border-t border-gray-700 space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400">Conversations</span>
              <span class="text-gray-300">{{ system.stats.total_conversations || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400">Messages</span>
              <span class="text-gray-300">{{ system.stats.total_messages || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400">Outils</span>
              <span class="text-gray-300">{{ system.stats.total_tools || 0 }}</span>
            </div>
          </div>

          <!-- Last check -->
          <div v-if="system.lastCheck" class="pt-2 mt-2 border-t border-gray-700">
            <span class="text-xs text-gray-500">
              Dernière vérification: {{ formatTime(system.lastCheck) }}
            </span>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Click outside to close -->
    <div v-if="showDetails" class="fixed inset-0 z-40" @click="showDetails = false"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'

const system = useSystemStore()
const showDetails = ref(false)
const loading = ref(false)
let healthInterval = null

const statusLabel = computed(() => {
  if (!system.health) return 'Vérification...'
  if (system.isHealthy) return 'Opérationnel'
  if (system.health.status === 'degraded') return 'Dégradé'
  return 'Erreur'
})

async function refresh() {
  loading.value = true
  await Promise.all([system.fetchHealth(), system.fetchStats()])
  loading.value = false
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString('fr-FR')
}

onMounted(() => {
  healthInterval = system.startHealthCheck(30000)
  system.fetchStats()
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})
</script>
