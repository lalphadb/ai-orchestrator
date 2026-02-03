<template>
  <div class="h-full flex flex-col bg-gray-900 text-gray-100 p-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold flex items-center gap-3">
        <svg class="w-7 h-7 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Agents
      </h1>
      <p class="text-gray-400 text-sm mt-1">Agents autonomes disponibles</p>
    </header>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- CRQ-2026-0203-001 Phase 6: Make agent cards clickable -->
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="bg-gray-800/50 border rounded-xl p-5 hover:border-primary-500/50 transition cursor-pointer"
        :class="selectedAgent?.id === agent.id ? 'border-primary-500/50 ring-2 ring-primary-500/30' : 'border-gray-700/50'"
        @click="selectAgent(agent)"
        role="button"
        tabindex="0"
        @keypress.enter="selectAgent(agent)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div 
              class="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
              :class="agent.color"
            >
              {{ agent.icon }}
            </div>
            <div>
              <h3 class="font-semibold">{{ agent.name }}</h3>
              <span class="text-xs text-gray-500">{{ agent.id }}</span>
            </div>
          </div>
          <span 
            class="px-2 py-0.5 rounded text-xs"
            :class="agent.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'"
          >
            {{ agent.enabled ? 'Actif' : 'Inactif' }}
          </span>
        </div>
        
        <p class="text-sm text-gray-400 mt-3">{{ agent.description }}</p>
        
        <div class="mt-4 flex flex-wrap gap-1">
          <span 
            v-for="tool in agent.tools.slice(0, 4)" 
            :key="tool"
            class="px-2 py-0.5 bg-gray-700 rounded text-xs"
          >
            {{ tool }}
          </span>
          <span v-if="agent.tools.length > 4" class="text-xs text-gray-500">
            +{{ agent.tools.length - 4 }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// CRQ-2026-0203-001 Phase 6: Add agent selection handler
const selectedAgent = ref(null)

function selectAgent(agent) {
  selectedAgent.value = agent
  console.log('[AgentsView] Selected agent:', agent.id)
  // TODO: Show agent details modal or navigate to agent detail page
}

const agents = ref([
  {
    id: 'system.health',
    name: 'System Health',
    icon: '🏥',
    color: 'bg-green-500/20',
    description: 'Surveille la santé du système et génère des alertes',
    enabled: true,
    tools: ['get_system_info', 'check_service_status', 'get_disk_usage', 'get_network_info']
  },
  {
    id: 'docker.monitor',
    name: 'Docker Monitor',
    icon: '🐳',
    color: 'bg-blue-500/20',
    description: 'Surveille les conteneurs Docker et leur état',
    enabled: true,
    tools: ['docker_list_containers', 'docker_logs', 'docker_inspect', 'docker_stats']
  },
  {
    id: 'unifi.monitor',
    name: 'UniFi Monitor',
    icon: '📡',
    color: 'bg-purple-500/20',
    description: 'Surveille le réseau UniFi et les appareils connectés',
    enabled: false,
    tools: ['http_request']
  },
  {
    id: 'web.researcher',
    name: 'Web Researcher',
    icon: '🔍',
    color: 'bg-yellow-500/20',
    description: 'Recherche des informations sur le web',
    enabled: false,
    tools: ['web_search', 'web_read', 'http_request']
  },
  {
    id: 'self_improve',
    name: 'Self Improve',
    icon: '🧠',
    color: 'bg-pink-500/20',
    description: 'Auto-amélioration du système avec rollback',
    enabled: false,
    tools: ['read_file', 'write_file', 'run_tests', 'run_lint', 'git_status', 'git_diff']
  },
  {
    id: 'qa.runner',
    name: 'QA Runner',
    icon: '✅',
    color: 'bg-cyan-500/20',
    description: 'Exécute les tests et vérifie la qualité du code',
    enabled: true,
    tools: ['run_tests', 'run_lint', 'analyze_code', 'check_types']
  }
])
</script>
