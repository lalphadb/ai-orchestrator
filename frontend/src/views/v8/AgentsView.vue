<template>
  <div class="h-full flex flex-col p-6">
    <header class="mb-6">
      <h1 class="heading-2 flex items-center gap-3">
        <svg
          width="28"
          height="28"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          style="color: var(--accent-primary)"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        Agents
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Agents autonomes disponibles
      </p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <AgentCard
        v-for="agent in agentCards"
        :key="agent.name"
        :name="agent.name"
        :description="agent.description"
        :status="agent.status"
        :status-pulse="agent.statusPulse"
        :metrics="agent.metrics"
        :interactive="true"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import AgentCard from '@/components/ui/AgentCard.vue'

const agents = ref([
  {
    id: 'system.health',
    name: 'System Health 🏥',
    description: 'Surveille la santé du système et génère des alertes',
    enabled: true,
    tools: ['get_system_info', 'check_service_status', 'get_disk_usage', 'get_network_info'],
  },
  {
    id: 'docker.monitor',
    name: 'Docker Monitor 🐳',
    description: 'Surveille les conteneurs Docker et leur état',
    enabled: true,
    tools: ['docker_list_containers', 'docker_logs', 'docker_inspect', 'docker_stats'],
  },
  {
    id: 'unifi.monitor',
    name: 'UniFi Monitor 📡',
    description: 'Surveille le réseau UniFi et les appareils connectés',
    enabled: false,
    tools: ['http_request'],
  },
  {
    id: 'web.researcher',
    name: 'Web Researcher 🔍',
    description: 'Recherche des informations sur le web',
    enabled: false,
    tools: ['web_search', 'web_read', 'http_request'],
  },
  {
    id: 'self_improve',
    name: 'Self Improve 🧠',
    description: 'Auto-amélioration du système avec rollback',
    enabled: false,
    tools: ['read_file', 'write_file', 'run_tests', 'run_lint', 'git_status', 'git_diff'],
  },
  {
    id: 'qa.runner',
    name: 'QA Runner ✅',
    description: 'Exécute les tests et vérifie la qualité du code',
    enabled: true,
    tools: ['run_tests', 'run_lint', 'analyze_code', 'check_types'],
  },
])

const agentCards = computed(() => {
  return agents.value.map((agent) => ({
    name: agent.name,
    description: agent.description,
    status: agent.enabled ? 'active' : 'default',
    statusPulse: agent.enabled,
    metrics: [
      { label: 'ID', value: agent.id },
      { label: 'Tools', value: agent.tools.length },
    ],
  }))
})
</script>
