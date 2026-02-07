<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <header class="px-6 py-4" style="border-bottom: 1px solid var(--border-subtle)">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="heading-3 flex items-center gap-2">
            <svg
              width="24"
              height="24"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              style="color: var(--accent-primary)"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Runs
          </h1>
          <p class="body-small" style="color: var(--text-secondary); margin-top: var(--space-1)">
            Historique et monitoring des exécutions
          </p>
        </div>

        <div class="flex items-center gap-3">
          <!-- Filters -->
          <select
            v-model="statusFilter"
            class="body-small"
            style="
              background: var(--bg-surface);
              border: 1px solid var(--border-default);
              border-radius: var(--radius-lg);
              padding: var(--space-2) var(--space-3);
              color: var(--text-primary);
            "
          >
            <option value="all">Tous les statuts</option>
            <option value="running">En cours</option>
            <option value="complete">Complétés</option>
            <option value="failed">Échoués</option>
          </select>

          <ModernButton variant="secondary" size="sm" @click="refreshRuns">
            <template #iconLeft>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </template>
            Refresh
          </ModernButton>
        </div>
      </div>
    </header>

    <!-- Runs Table -->
    <div class="flex-1 overflow-auto p-6">
      <EmptyState
        v-if="filteredRuns.length === 0"
        title="Aucun run trouvé"
        message="Lancez une commande dans le chat pour voir les runs"
      >
        <template #icon>
          <svg
            width="64"
            height="64"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style="color: var(--text-tertiary)"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </template>
      </EmptyState>

      <GlassCard v-else variant="bordered" padding="none">
        <div style="overflow-x: auto">
          <table class="w-full">
            <thead
              class="label"
              style="color: var(--text-secondary); border-bottom: 1px solid var(--border-subtle)"
            >
              <tr>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Run ID
                </th>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Conversation
                </th>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Phase
                </th>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Statut
                </th>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Durée
                </th>
                <th
                  style="padding: var(--space-3); text-align: left; font-weight: var(--font-medium)"
                >
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="run in filteredRuns"
                :key="run.id"
                class="run-row"
                style="
                  border-bottom: 1px solid var(--border-subtle);
                  cursor: pointer;
                  transition: background var(--transition-fast);
                "
                @click="selectRun(run)"
              >
                <td style="padding: var(--space-4)">
                  <code
                    class="code text-xs"
                    style="
                      background: var(--bg-surface);
                      padding: var(--space-1) var(--space-2);
                      border-radius: var(--radius-sm);
                    "
                  >
                    {{ run.id.slice(0, 12) }}...
                  </code>
                </td>
                <td style="padding: var(--space-4)">
                  <span class="body-small" style="color: var(--text-secondary)">
                    {{ run.conversationId?.slice(0, 8) || 'N/A' }}
                  </span>
                </td>
                <td style="padding: var(--space-4)">
                  <span
                    class="label"
                    style="padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm)"
                    :style="phaseStyle(run.currentPhase)"
                  >
                    {{ run.currentPhase || 'INIT' }}
                  </span>
                </td>
                <td style="padding: var(--space-4)">
                  <div class="flex items-center gap-2">
                    <StatusOrb
                      :status="statusToOrbStatus(run.status)"
                      size="sm"
                      :pulse="run.status === 'running'"
                    />
                    <span class="body-small">{{ statusLabel(run.status) }}</span>
                  </div>
                </td>
                <td style="padding: var(--space-4)">
                  <span class="body-small" style="color: var(--text-tertiary)">
                    {{ formatDuration(run.startedAt, run.completedAt) }}
                  </span>
                </td>
                <td style="padding: var(--space-4)">
                  <router-link :to="`/v8/runs/${run.id}`" @click.stop>
                    <ModernButton variant="ghost" size="sm"> Détails → </ModernButton>
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'

const router = useRouter()
const chat = useChatStore()

const statusFilter = ref('all')

const filteredRuns = computed(() => {
  const runs = []
  chat.runs.forEach((run, id) => {
    runs.push({ ...run, id })
  })

  if (statusFilter.value === 'all')
    return runs.sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))

  return runs
    .filter((r) => r.status === statusFilter.value)
    .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))
})

const statusToOrbStatus = (status) =>
  ({
    running: 'processing',
    complete: 'success',
    failed: 'error',
    idle: 'default',
  })[status] || 'default'

const statusLabel = (status) =>
  ({
    running: 'En cours',
    complete: 'Complété',
    failed: 'Échoué',
    idle: 'En attente',
  })[status] || status

const phaseStyle = (phase) => {
  const styles = {
    SPEC: { background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' },
    PLAN: { background: 'rgba(168, 85, 247, 0.2)', color: '#a78bfa' },
    EXECUTE: { background: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24' },
    VERIFY: { background: 'rgba(6, 182, 212, 0.2)', color: '#22d3ee' },
    REPAIR: { background: 'rgba(251, 146, 60, 0.2)', color: '#fb923c' },
    COMPLETE: { background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80' },
  }
  return styles[phase] || { background: 'var(--bg-surface)', color: 'var(--text-tertiary)' }
}

const formatDuration = (start, end) => {
  if (!start) return '-'
  const startTime = new Date(start).getTime()
  const endTime = end ? new Date(end).getTime() : Date.now()
  const ms = endTime - startTime

  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

const selectRun = (run) => {
  router.push(`/v8/runs/${run.id}`)
}

const refreshRuns = () => {
  // Trigger refresh from store if needed
  console.log('Refreshing runs...')
}
</script>

<style scoped>
.run-row:hover {
  background: var(--bg-surface-hover);
}
</style>
