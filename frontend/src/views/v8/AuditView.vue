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
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>
        Audit & Security
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Logs de sécurité et audit des actions
      </p>
    </header>

    <!-- Security Score -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <MetricCard label="Score Sécurité" :value="stats.security_score" unit="%" color="success">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </template>
      </MetricCard>

      <MetricCard label="Actions bloquées" :value="stats.blocked_actions" color="error">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
            />
          </svg>
        </template>
      </MetricCard>

      <MetricCard label="Tools exécutés" :value="stats.tools_executed" color="info">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </template>
      </MetricCard>

      <GlassCard variant="bordered" padding="md">
        <div class="label" style="color: var(--text-secondary)">Mode Sandbox</div>
        <div
          class="heading-3"
          :style="{
            color: sandboxEnabled ? 'var(--color-success)' : 'var(--color-warning)',
            marginTop: 'var(--space-2)',
          }"
        >
          {{ sandboxEnabled ? 'Activé' : 'Désactivé' }}
        </div>
      </GlassCard>
    </div>

    <!-- Audit Logs -->
    <div class="flex-1 overflow-auto">
      <h3 class="heading-4" style="margin-bottom: var(--space-4)">Logs d'audit récents</h3>

      <div v-if="loading" class="text-center py-8">
        <span class="text-gray-400">Chargement des logs...</span>
      </div>

      <div v-else-if="auditLogs.length === 0" class="text-center py-8">
        <span class="text-gray-500">Aucun log d'audit enregistré</span>
      </div>

      <div v-else class="space-y-2">
        <GlassCard v-for="(log, idx) in auditLogs" :key="idx" variant="bordered" padding="sm">
          <div class="flex items-center gap-4">
            <StatusOrb :status="log.allowed ? 'default' : 'error'" size="sm" />
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="code body-small" style="color: var(--accent-primary)">{{
                  log.action
                }}</span>
                <StatusOrb
                  :status="log.allowed ? 'success' : 'error'"
                  :label="log.allowed ? 'OK' : 'BLOCKED'"
                  size="sm"
                />
              </div>
              <div
                class="body-small"
                style="color: var(--text-secondary); margin-top: var(--space-1)"
              >
                {{ log.command || log.resource || '-' }}
              </div>
            </div>
            <div class="label flex-shrink-0" style="color: var(--text-tertiary)">
              {{ formatTime(log.timestamp) }}
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import GlassCard from '@/components/ui/GlassCard.vue'
import MetricCard from '@/components/ui/MetricCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'

const loading = ref(true)
const sandboxEnabled = ref(true)

const stats = ref({
  security_score: 0,
  blocked_actions: 0,
  tools_executed: 0,
  total_actions: 0,
})

const auditLogs = ref([])

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString('fr-CA')
}

async function fetchAuditData() {
  loading.value = true
  try {
    const [logsRes, statsRes] = await Promise.all([
      api.get('/audit/logs?limit=50'),
      api.get('/audit/stats'),
    ])
    auditLogs.value = logsRes.logs || []
    stats.value = statsRes
  } catch {
    // API not available - show empty state
    auditLogs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAuditData()
})
</script>
