<template>
  <div class="h-full flex">
    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <header
        class="px-6 py-4 flex items-center justify-between"
        style="border-bottom: 1px solid var(--border-subtle)"
      >
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
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            Chat
          </h1>
          <p class="body-small" style="color: var(--text-secondary); margin-top: var(--space-1)">
            {{ currentConversation?.title || 'Nouvelle conversation' }}
          </p>
        </div>

        <ModernButton variant="primary" size="sm" @click="newConversation">
          <template #iconLeft>
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
          </template>
          Nouvelle conversation
        </ModernButton>
      </header>

      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <!-- Empty state -->
        <EmptyState
          v-if="messages.length === 0"
          title="Commencez une conversation"
          message="Envoyez un message pour démarrer"
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
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </template>
        </EmptyState>

        <!-- Messages -->
        <div
          v-for="message in messages"
          :key="message.id"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- User Message -->
          <GlassCard
            v-if="message.role === 'user'"
            variant="bordered"
            padding="sm"
            :glow="true"
            style="
              max-width: 70%;
              background: rgba(139, 92, 246, 0.1);
              border-color: rgba(139, 92, 246, 0.3);
            "
          >
            <p class="body-default" style="white-space: pre-wrap">{{ message.content }}</p>
          </GlassCard>

          <!-- Assistant Message -->
          <GlassCard v-else variant="bordered" padding="sm" style="max-width: 70%">
            <ThinkingDots
              v-if="message.streaming"
              label="Génération en cours"
              style="margin-bottom: var(--space-2)"
            />

            <p class="body-default" style="white-space: pre-wrap">{{ message.content }}</p>

            <!-- Tools used -->
            <div
              v-if="message.tools_used && message.tools_used.length > 0"
              style="
                margin-top: var(--space-3);
                padding-top: var(--space-3);
                border-top: 1px solid var(--border-subtle);
              "
            >
              <p class="label" style="color: var(--text-tertiary); margin-bottom: var(--space-2)">
                Outils utilisés:
              </p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(tool, i) in message.tools_used"
                  :key="i"
                  class="code"
                  style="
                    padding: var(--space-1) var(--space-2);
                    background: var(--bg-surface);
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    color: var(--text-tertiary);
                  "
                >
                  {{ tool.tool }}
                </span>
              </div>
            </div>

            <!-- Verification -->
            <div
              v-if="message.verification"
              style="
                margin-top: var(--space-3);
                padding-top: var(--space-3);
                border-top: 1px solid var(--border-subtle);
              "
            >
              <p class="label" style="color: var(--text-tertiary); margin-bottom: var(--space-2)">
                Vérification:
              </p>
              <StatusOrb
                :status="message.verification.passed ? 'success' : 'error'"
                :label="message.verification.passed ? '✓ Passed' : '✗ Failed'"
                size="sm"
              />
            </div>

            <!-- Error -->
            <div
              v-if="message.isError"
              style="margin-top: var(--space-2); color: var(--color-error)"
              class="body-small"
            >
              ⚠️ Erreur lors de la génération
            </div>
          </GlassCard>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4" style="border-top: 1px solid var(--border-subtle)">
        <ChatInput
          v-model="messageInput"
          placeholder="Tapez votre message... (Entrée pour envoyer, Shift+Entrée pour nouvelle ligne)"
          :disabled="chat.isLoading"
          :loading="chat.isLoading"
          :submit-on-enter="true"
          @submit="sendMessage"
        />
      </div>
    </div>

    <!-- Right Sidebar: Run Inspector -->
    <aside
      class="w-96 flex flex-col"
      style="border-left: 1px solid var(--border-subtle); background: var(--bg-deep)"
    >
      <div class="p-4" style="border-bottom: 1px solid var(--border-subtle)">
        <h2
          class="label"
          style="color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em"
        >
          Run Inspector
        </h2>
      </div>

      <EmptyState
        v-if="!activeRun"
        title="Aucun run actif"
        message="Les détails du run apparaîtront ici"
      />

      <div v-else class="flex-1 overflow-y-auto">
        <!-- Run Header -->
        <GlassCard variant="bordered" padding="md">
          <div class="flex items-center justify-between" style="margin-bottom: var(--space-2)">
            <code class="code text-xs" style="color: var(--text-tertiary)">
              {{ activeRun.id.slice(0, 12) }}...
            </code>
            <StatusOrb
              :status="statusToOrbStatus(activeRun.status)"
              :label="activeRun.status.toUpperCase()"
              size="sm"
              :pulse="activeRun.status === 'running'"
            />
          </div>
          <div class="label" style="color: var(--text-tertiary)">
            Durée: {{ formatDuration(activeRun) }}
          </div>
        </GlassCard>

        <!-- Phase Timeline -->
        <div class="p-4">
          <h3 class="heading-4" style="margin-bottom: var(--space-4)">Timeline des phases</h3>
          <PipelineSteps :steps="pipelineSteps" />
        </div>

        <!-- Tools Used -->
        <GlassCard
          v-if="activeRun.tools && activeRun.tools.length > 0"
          variant="bordered"
          padding="md"
          style="margin: var(--space-4)"
        >
          <h3 class="heading-4" style="margin-bottom: var(--space-3)">
            Outils ({{ activeRun.tools.length }})
          </h3>
          <div class="space-y-2">
            <GlassCard v-for="(tool, i) in activeRun.tools" :key="i" variant="default" padding="sm">
              <div
                class="code"
                style="color: var(--accent-primary); font-size: var(--font-size-xs)"
              >
                {{ tool.tool }}
              </div>
              <div class="label" style="color: var(--text-tertiary); margin-top: var(--space-1)">
                Iteration {{ tool.iteration }}
              </div>
            </GlassCard>
          </div>
        </GlassCard>

        <!-- Verification Items -->
        <GlassCard
          v-if="activeRun.verification && activeRun.verification.length > 0"
          variant="bordered"
          padding="md"
          style="margin: var(--space-4)"
        >
          <h3 class="heading-4" style="margin-bottom: var(--space-3)">Vérification</h3>
          <div class="space-y-2">
            <div
              v-for="item in activeRun.verification"
              :key="item.check_name"
              class="flex items-center justify-between"
              style="
                padding: var(--space-2);
                background: var(--bg-surface);
                border-radius: var(--radius-md);
              "
            >
              <span class="body-small">{{ item.check_name }}</span>
              <StatusOrb
                :status="
                  item.status === 'passed'
                    ? 'success'
                    : item.status === 'failed'
                      ? 'error'
                      : 'warning'
                "
                :label="item.status"
                size="sm"
              />
            </div>
          </div>
        </GlassCard>

        <!-- Error -->
        <GlassCard
          v-if="activeRun.error"
          variant="bordered"
          padding="md"
          style="
            margin: var(--space-4);
            border-color: var(--color-error-border);
            background: rgba(239, 68, 68, 0.1);
          "
        >
          <div class="heading-4" style="color: var(--color-error); margin-bottom: var(--space-1)">
            ❌ Erreur
          </div>
          <div class="body-small" style="color: var(--color-error)">
            {{ activeRun.error }}
          </div>
        </GlassCard>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'
import ChatInput from '@/components/ui/ChatInput.vue'
import ThinkingDots from '@/components/ui/ThinkingDots.vue'
import PipelineSteps from '@/components/ui/PipelineSteps.vue'

const chat = useChatStore()

const messageInput = ref('')

const messages = computed(() => chat.messages)
const currentConversation = computed(() => chat.currentConversation)
const activeRun = computed(() => {
  if (!chat.activeRunId) return null
  return chat.runs.get(chat.activeRunId)
})

const phases = [
  { name: 'spec', label: 'Specification' },
  { name: 'plan', label: 'Planning' },
  { name: 'execute', label: 'Execution' },
  { name: 'verify', label: 'Verification' },
  { name: 'repair', label: 'Repair' },
  { name: 'complete', label: 'Complete' },
]

const pipelineSteps = computed(() => {
  const run = activeRun.value
  if (!run) return []

  return phases.map((phase) => {
    const isComplete = isPhaseComplete(phase, run)
    const isRunning = isPhaseRunning(phase, run)

    return {
      title: phase.label,
      description: phaseDescription(phase, run),
      status: isComplete ? 'completed' : isRunning ? 'active' : 'pending',
      duration: isComplete || isRunning ? formatDuration(run) : undefined,
    }
  })
})

async function sendMessage() {
  if (!messageInput.value.trim()) return

  const content = messageInput.value
  messageInput.value = ''

  await chat.sendMessage(content)
}

function newConversation() {
  chat.currentConversation = null
  chat.messages = []
  chat.activeRunId = null
}

function isPhaseComplete(phase, run) {
  if (!run) return false
  const phaseIndex = phases.findIndex((p) => p.name === phase.name)
  const currentPhaseIndex = phases.findIndex((p) => p.name === run.workflowPhase)
  return phaseIndex < currentPhaseIndex || (run.status === 'complete' && phase.name === 'complete')
}

function isPhaseRunning(phase, run) {
  if (!run) return false
  return run.workflowPhase === phase.name && run.status === 'running'
}

function phaseDescription(phase, run) {
  if (!run) return 'En attente'
  if (isPhaseComplete(phase, run)) return 'Terminé'
  if (isPhaseRunning(phase, run)) return 'En cours...'
  return 'En attente'
}

function statusToOrbStatus(status) {
  if (status === 'running') return 'processing'
  if (status === 'complete') return 'success'
  if (status === 'failed') return 'error'
  return 'default'
}

function formatDuration(run) {
  if (!run || !run.startedAt) return '0s'
  const startMs = new Date(run.startedAt).getTime()
  const endMs = run.endedAt ? new Date(run.endedAt).getTime() : Date.now()
  const duration = endMs - startMs
  if (isNaN(duration) || duration < 0) return '0s'
  if (duration < 1000) return `${duration}ms`
  return `${(duration / 1000).toFixed(1)}s`
}

// Auto-scroll to bottom when new messages arrive
watch(
  messages,
  async () => {
    await nextTick()
    const container = document.querySelector('.overflow-y-auto')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  },
  { deep: true }
)

// WebSocket initialization is handled by V8Layout.vue
// No need to initialize here to avoid duplicate connections
</script>
