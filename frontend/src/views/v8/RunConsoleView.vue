<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <header
      class="px-6 py-4 flex items-center justify-between"
      style="border-bottom: 1px solid var(--border-subtle)"
    >
      <div class="flex items-center gap-4">
        <router-link to="/v8/runs">
          <ModernButton variant="ghost" size="sm" icon-only>
            <template #iconLeft>
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </template>
          </ModernButton>
        </router-link>
        <div>
          <h1 class="heading-3">Run Console</h1>
          <code class="code text-xs" style="color: var(--text-tertiary)">{{ runId }}</code>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <StatusOrb
          :status="statusToOrbStatus(run?.status)"
          :label="run?.status || 'Unknown'"
          :pulse="run?.status === 'running'"
          size="md"
        />
        <ModernButton variant="secondary" size="sm" @click="exportRun"> Export JSON </ModernButton>
      </div>
    </header>

    <!-- Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Phase Timeline -->
      <div class="w-64 p-4 overflow-auto" style="border-right: 1px solid var(--border-subtle)">
        <h3 class="heading-4" style="margin-bottom: var(--space-4)">Phases</h3>
        <div class="space-y-3">
          <GlassCard
            v-for="phase in phases"
            :key="phase.name"
            :variant="selectedPhase === phase.name ? 'elevated' : 'default'"
            padding="sm"
            :interactive="true"
            :glow="selectedPhase === phase.name"
            class="cursor-pointer"
            @click="selectedPhase = phase.name"
          >
            <div class="flex items-center gap-3">
              <StatusOrb
                :status="phaseStatusToOrb(phase.status)"
                :pulse="phase.status === 'active'"
                size="sm"
              />
              <div class="flex-1">
                <div class="body-small font-medium">{{ phase.name }}</div>
                <div class="label" style="color: var(--text-tertiary)">
                  {{ phase.events?.length || 0 }} events
                </div>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      <!-- Events Stream -->
      <div class="flex-1 overflow-auto p-6">
        <EmptyState
          v-if="!run"
          title="Run non trouvé"
          message="Vérifiez que l'ID du run est correct"
        />

        <div v-else class="space-y-4">
          <GlassCard
            v-for="(event, idx) in displayedEvents"
            :key="idx"
            variant="bordered"
            padding="md"
          >
            <!-- Event Header -->
            <div class="flex items-center justify-between" style="margin-bottom: var(--space-2)">
              <span
                class="code"
                style="
                  padding: var(--space-1) var(--space-2);
                  border-radius: var(--radius-sm);
                  font-size: var(--font-size-xs);
                "
                :style="eventTypeStyle(event.type)"
              >
                {{ event.type }}
              </span>
              <span class="label" style="color: var(--text-tertiary)">
                {{ formatTime(event.timestamp) }}
              </span>
            </div>

            <!-- Event Content -->
            <div class="body-small">
              <!-- Thinking -->
              <template v-if="event.type === 'thinking'">
                <p style="font-style: italic; color: var(--text-secondary)">
                  {{ event.data?.message }}
                </p>
              </template>

              <!-- Phase -->
              <template v-else-if="event.type === 'phase'">
                <p>
                  Phase
                  <span style="font-weight: var(--font-bold); color: var(--accent-primary)">{{
                    event.data?.phase
                  }}</span>
                  → {{ event.data?.status }}
                </p>
              </template>

              <!-- Tool -->
              <template v-else-if="event.type === 'tool'">
                <div class="flex items-center gap-2" style="margin-bottom: var(--space-2)">
                  <span class="code" style="color: var(--color-warning)">{{
                    event.data?.tool_name
                  }}</span>
                  <StatusOrb :status="event.data?.success ? 'success' : 'error'" size="sm" />
                </div>
                <CodeBlock
                  v-if="event.data?.result"
                  :code="formatResult(event.data.result)"
                  language="json"
                />
              </template>

              <!-- Verification -->
              <template v-else-if="event.type === 'verification_item'">
                <div class="flex items-center gap-2">
                  <StatusOrb :status="event.data?.passed ? 'success' : 'error'" size="sm" />
                  <span>{{ event.data?.check }}</span>
                </div>
              </template>

              <!-- Complete -->
              <template v-else-if="event.type === 'complete'">
                <div style="color: var(--color-success); font-weight: var(--font-medium)">
                  Run terminé avec succès
                </div>
                <p
                  v-if="event.data?.response"
                  style="margin-top: var(--space-2); color: var(--text-secondary)"
                  class="line-clamp-3"
                >
                  {{ event.data.response }}
                </p>
              </template>

              <!-- Error -->
              <template v-else-if="event.type === 'error'">
                <div style="color: var(--color-error)">
                  {{ event.data?.message || event.data?.error }}
                </div>
              </template>

              <!-- Default -->
              <template v-else>
                <CodeBlock :code="JSON.stringify(event.data, null, 2)" language="json" />
              </template>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'
import CodeBlock from '@/components/ui/CodeBlock.vue'

const route = useRoute()
const chat = useChatStore()

const selectedPhase = ref(null)

const runId = computed(() => route.params.id)
const run = computed(() => chat.runs.get(runId.value))

const statusToOrbStatus = (status) => {
  if (status === 'running') return 'processing'
  if (status === 'complete') return 'success'
  if (status === 'failed') return 'error'
  return 'default'
}

const phases = computed(() => {
  const phaseList = ['SPEC', 'PLAN', 'EXECUTE', 'VERIFY', 'REPAIR']
  return phaseList.map((name) => ({
    name,
    status:
      run.value?.currentPhase === name
        ? 'active'
        : phaseList.indexOf(run.value?.currentPhase) > phaseList.indexOf(name)
          ? 'complete'
          : 'pending',
    events: run.value?.events?.filter((e) => e.data?.phase === name) || [],
  }))
})

const displayedEvents = computed(() => {
  if (!run.value?.events) return []
  if (!selectedPhase.value) return run.value.events
  return run.value.events.filter((e) => e.data?.phase === selectedPhase.value)
})

const phaseStatusToOrb = (status) => {
  if (status === 'active') return 'processing'
  if (status === 'complete') return 'success'
  return 'default'
}

const eventTypeStyle = (type) => {
  const styles = {
    thinking: { background: 'rgba(168, 85, 247, 0.2)', color: '#a78bfa' },
    phase: { background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' },
    tool: { background: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24' },
    verification_item: { background: 'rgba(6, 182, 212, 0.2)', color: '#22d3ee' },
    complete: { background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80' },
    error: { background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' },
  }
  return styles[type] || { background: 'var(--bg-surface)', color: 'var(--text-tertiary)' }
}

const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('fr-CA')
}

const formatResult = (data) => {
  if (typeof data === 'string') return data.slice(0, 500)
  try {
    return JSON.stringify(data, null, 2).slice(0, 500)
  } catch {
    return String(data).slice(0, 500)
  }
}

const exportRun = () => {
  if (!run.value) return
  const blob = new Blob([JSON.stringify(run.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `run-${runId.value}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
