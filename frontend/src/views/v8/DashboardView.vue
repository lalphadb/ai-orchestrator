<template>
  <div class="h-full overflow-auto p-6">
    <!-- Header -->
    <header class="mb-8">
      <h1 class="heading-2 flex items-center gap-3">
        <svg
          class="w-7 h-7"
          style="color: var(--accent-primary)"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
          />
        </svg>
        AI Orchestrator v8
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Dashboard système et métriques temps réel
      </p>
    </header>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <MetricCard label="Runs actifs" :value="activeRuns" color="info">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </template>
      </MetricCard>

      <MetricCard label="Runs (24h)" :value="totalRuns" color="success">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </template>
      </MetricCard>

      <MetricCard label="Taux de succès" :value="successRate" unit="%" color="primary">
        <template #icon>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </template>
      </MetricCard>

      <GlassCard variant="bordered" padding="md">
        <div class="flex items-center justify-between">
          <div class="label" style="color: var(--text-secondary)">WebSocket</div>
          <StatusOrb :status="wsConnected ? 'success' : 'error'" :pulse="wsConnected" size="md" />
        </div>
        <div
          class="heading-3"
          :style="{
            color: wsConnected ? 'var(--color-success)' : 'var(--color-error)',
            marginTop: 'var(--space-2)',
          }"
        >
          {{ wsConnected ? 'Connecté' : 'Déconnecté' }}
        </div>
      </GlassCard>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Runs -->
      <GlassCard variant="bordered" padding="md">
        <template #header>
          <h3 class="heading-4 flex items-center gap-2">
            <svg
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              style="color: var(--accent-primary)"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Runs récents
          </h3>
        </template>

        <EmptyState
          v-if="recentRuns.length === 0"
          title="Aucun run récent"
          description="Lancez un nouveau chat pour démarrer"
        />

        <div v-else class="space-y-3">
          <router-link
            v-for="run in recentRuns"
            :key="run.id"
            :to="`/v8/runs/${run.id}`"
            class="block"
          >
            <GlassCard variant="interactive" padding="sm">
              <div class="flex items-center justify-between">
                <code class="code text-xs" style="color: var(--text-secondary)">
                  {{ run.id.slice(0, 12) }}...
                </code>
                <StatusOrb :status="statusToOrbStatus(run.status)" size="sm" :label="run.status" />
              </div>
              <div
                class="body-small"
                style="color: var(--text-secondary); margin-top: var(--space-1)"
              >
                Phase: {{ run.currentPhase || 'INIT' }}
              </div>
            </GlassCard>
          </router-link>
        </div>
      </GlassCard>

      <!-- Quick Actions -->
      <GlassCard variant="bordered" padding="md">
        <template #header>
          <h3 class="heading-4 flex items-center gap-2">
            <svg
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              style="color: var(--accent-primary)"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            Actions rapides
          </h3>
        </template>

        <div class="grid grid-cols-2 gap-3">
          <router-link to="/">
            <ModernButton variant="primary" size="md" style="width: 100%; height: 100%">
              <template #iconLeft>
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </template>
              Nouveau Chat
            </ModernButton>
          </router-link>

          <router-link to="/v8/runs">
            <ModernButton variant="secondary" size="md" style="width: 100%; height: 100%">
              <template #iconLeft>
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </template>
              Voir Runs
            </ModernButton>
          </router-link>

          <router-link to="/v8/system">
            <ModernButton variant="secondary" size="md" style="width: 100%; height: 100%">
              <template #iconLeft>
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  />
                </svg>
              </template>
              Système
            </ModernButton>
          </router-link>

          <router-link to="/tools">
            <ModernButton variant="secondary" size="md" style="width: 100%; height: 100%">
              <template #iconLeft>
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              Outils
            </ModernButton>
          </router-link>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import GlassCard from '@/components/ui/GlassCard.vue'
import MetricCard from '@/components/ui/MetricCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'

const chat = useChatStore()

const activeRuns = computed(() => {
  let count = 0
  chat.runs.forEach((run) => {
    if (run.status === 'running') count++
  })
  return count
})

const totalRuns = computed(() => chat.runs.size)

const successRate = computed(() => {
  if (chat.runs.size === 0) return 100
  let success = 0
  chat.runs.forEach((run) => {
    if (run.status === 'complete') success++
  })
  return Math.round((success / chat.runs.size) * 100)
})

const wsConnected = computed(() => chat.isConnected)

const recentRuns = computed(() => {
  const runs = []
  chat.runs.forEach((run, id) => {
    runs.push({ ...run, id })
  })
  return runs.sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt)).slice(0, 5)
})

const statusToOrbStatus = (status) =>
  ({
    running: 'processing',
    complete: 'success',
    failed: 'error',
  })[status] || 'default'
</script>
