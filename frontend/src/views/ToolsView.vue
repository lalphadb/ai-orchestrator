<template>
  <div class="h-[calc(100vh-3.5rem)] flex">
    <!-- Tools List -->
    <div
      class="w-80 flex-shrink-0 flex flex-col"
      style="background: var(--bg-surface); border-right: 1px solid var(--border-subtle)"
    >
      <!-- Search & Filter -->
      <div class="p-4 space-y-3" style="border-bottom: 1px solid var(--border-subtle)">
        <div class="relative">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
            style="color: var(--text-tertiary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            v-model="tools.searchQuery"
            type="text"
            placeholder="Rechercher un outil..."
            class="body-default w-full pl-10 pr-4"
            style="
              background: var(--bg-deep);
              border: 1px solid var(--border-default);
              border-radius: var(--radius-lg);
              padding-top: var(--space-2);
              padding-bottom: var(--space-2);
              color: var(--text-primary);
            "
          />
        </div>

        <select
          v-model="tools.selectedCategory"
          class="body-default w-full px-3 py-2"
          style="
            background: var(--bg-deep);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-lg);
            color: var(--text-primary);
          "
        >
          <option value="all">Toutes les catégories</option>
          <option
            v-for="cat in tools.categories.filter((c) => c !== 'all')"
            :key="cat"
            :value="cat"
          >
            {{ cat }}
          </option>
        </select>
      </div>

      <!-- Tools list -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="tools.loading" class="flex items-center justify-center py-8">
          <div
            class="animate-spin w-6 h-6 rounded-full"
            style="border: 2px solid var(--accent-primary); border-top-color: transparent"
          ></div>
        </div>

        <div
          v-else-if="tools.filteredTools.length === 0"
          class="text-center py-8 body-small"
          style="color: var(--text-tertiary)"
        >
          Aucun outil trouvé
        </div>

        <div v-else class="p-2 space-y-1">
          <button
            v-for="tool in tools.filteredTools"
            :key="tool.name"
            class="w-full px-3 py-2.5 rounded-lg text-left transition-all"
            :style="
              selectedToolName === tool.name
                ? `
                  background: rgba(139, 92, 246, 0.1);
                  border: 1px solid var(--accent-primary);
                  box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
                `
                : `
                  background: transparent;
                  border: 1px solid transparent;
                `
            "
            @click="selectTool(tool.name)"
          >
            <div class="flex items-start gap-2">
              <div
                class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                :style="getRiskStyle(tool.risk_level)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              </div>
              <div class="flex-1 min-w-0">
                <p class="body-default truncate" style="color: var(--text-primary)">
                  {{ tool.name }}
                </p>
                <p class="label truncate" style="color: var(--text-tertiary)">
                  {{ tool.category }}
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div
        class="p-3 label"
        style="border-top: 1px solid var(--border-subtle); color: var(--text-tertiary)"
      >
        {{ tools.filteredTools.length }} / {{ tools.tools.length }} outils
      </div>
    </div>

    <!-- Tool Detail -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <div
        v-if="!tools.selectedTool"
        class="flex-1 flex items-center justify-center"
        style="color: var(--text-tertiary)"
      >
        <div class="text-center">
          <svg
            class="w-16 h-16 mx-auto mb-4"
            style="color: var(--text-tertiary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <p class="body-default">Sélectionnez un outil pour voir les détails</p>
        </div>
      </div>

      <div v-else class="flex-1 overflow-y-auto p-6">
        <!-- Header -->
        <div class="flex items-start justify-between" style="margin-bottom: var(--space-6)">
          <div>
            <h2 class="heading-2" style="margin-bottom: var(--space-2)">
              {{ tools.selectedTool.name }}
            </h2>
            <div class="flex items-center gap-3">
              <span
                class="label"
                style="
                  padding: var(--space-1) var(--space-2);
                  background: var(--bg-surface);
                  border-radius: var(--radius-sm);
                  color: var(--text-secondary);
                "
              >
                {{ tools.selectedTool.category }}
              </span>
              <StatusOrb
                :status="getRiskStatus(tools.selectedTool.risk_level)"
                :label="`${tools.selectedTool.risk_level || 'low'} risk`"
                size="sm"
              />
              <span
                v-if="tools.selectedTool.usage_count"
                class="label"
                style="color: var(--text-tertiary)"
              >
                {{ tools.selectedTool.usage_count }} utilisations
              </span>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div style="margin-bottom: var(--space-6)">
          <h3 class="heading-4" style="color: var(--text-secondary); margin-bottom: var(--space-2)">
            Description
          </h3>
          <p class="body-default" style="color: var(--text-primary)">
            {{ tools.selectedTool.description }}
          </p>
        </div>

        <!-- Parameters -->
        <div v-if="tools.selectedTool.parameters?.length" style="margin-bottom: var(--space-6)">
          <h3 class="heading-4" style="color: var(--text-secondary); margin-bottom: var(--space-3)">
            Paramètres
          </h3>
          <div class="space-y-3">
            <GlassCard
              v-for="param in tools.selectedTool.parameters"
              :key="param.name"
              variant="bordered"
              padding="sm"
            >
              <div class="flex items-center gap-2" style="margin-bottom: var(--space-1)">
                <code class="code" style="color: var(--accent-primary)">{{ param.name }}</code>
                <span class="label" style="color: var(--text-tertiary)">{{ param.type }}</span>
                <span v-if="param.required" class="label" style="color: var(--color-error)"
                  >requis</span
                >
              </div>
              <p class="body-small" style="color: var(--text-secondary)">{{ param.description }}</p>
            </GlassCard>
          </div>
        </div>

        <!-- Examples -->
        <div v-if="tools.selectedTool.examples?.length" style="margin-bottom: var(--space-6)">
          <h3 class="heading-4" style="color: var(--text-secondary); margin-bottom: var(--space-3)">
            Exemples
          </h3>
          <div class="space-y-2">
            <GlassCard
              v-for="(example, idx) in tools.selectedTool.examples"
              :key="idx"
              variant="bordered"
              padding="sm"
              :interactive="true"
              @click="loadExample(example)"
            >
              <pre class="code body-small" style="color: var(--text-primary); overflow-x: auto">{{
                JSON.stringify(example, null, 2)
              }}</pre>
            </GlassCard>
          </div>
        </div>

        <!-- Test Form (admin only) -->
        <div v-if="auth.isAdmin" style="margin-bottom: var(--space-6)">
          <h3 class="heading-4" style="color: var(--text-secondary); margin-bottom: var(--space-3)">
            Tester l'outil
          </h3>
          <GlassCard variant="bordered" padding="md">
            <div class="space-y-3" style="margin-bottom: var(--space-4)">
              <div v-for="param in tools.selectedTool.parameters" :key="param.name">
                <label
                  class="label block"
                  style="color: var(--text-secondary); margin-bottom: var(--space-1)"
                >
                  {{ param.name }}
                  <span v-if="param.required" style="color: var(--color-error)">*</span>
                </label>
                <input
                  v-model="testParams[param.name]"
                  :type="param.type === 'integer' ? 'number' : 'text'"
                  :placeholder="param.description"
                  class="body-default w-full px-3 py-2"
                  style="
                    background: var(--bg-deep);
                    border: 1px solid var(--border-default);
                    border-radius: var(--radius-lg);
                    color: var(--text-primary);
                  "
                />
              </div>
            </div>

            <ModernButton
              variant="primary"
              size="md"
              :disabled="tools.executing"
              :loading="tools.executing"
              @click="executeTool"
            >
              {{ tools.executing ? 'Exécution...' : 'Exécuter' }}
            </ModernButton>
          </GlassCard>

          <!-- Execution result -->
          <GlassCard
            v-if="tools.executionResult"
            variant="bordered"
            padding="md"
            :style="{
              marginTop: 'var(--space-4)',
              borderColor: tools.executionResult.success
                ? 'var(--color-success-border)'
                : 'var(--color-error-border)',
              background: tools.executionResult.success
                ? 'rgba(34, 197, 94, 0.1)'
                : 'rgba(239, 68, 68, 0.1)',
            }"
          >
            <div class="flex items-center gap-2" style="margin-bottom: var(--space-2)">
              <StatusOrb
                :status="tools.executionResult.success ? 'success' : 'error'"
                :label="tools.executionResult.success ? 'Succès' : 'Erreur'"
                size="sm"
              />
            </div>
            <pre
              class="code body-small"
              style="
                background: var(--bg-deep);
                border-radius: var(--radius-md);
                padding: var(--space-3);
                overflow-x: auto;
                color: var(--text-primary);
              "
              >{{ formatResult(tools.executionResult) }}</pre
            >
          </GlassCard>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useToolsStore } from '@/stores/tools'
import { useAuthStore } from '@/stores/auth'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import ModernButton from '@/components/ui/ModernButton.vue'

const tools = useToolsStore()
const auth = useAuthStore()

const selectedToolName = ref(null)
const testParams = reactive({})

onMounted(() => {
  tools.fetchTools()
})

function selectTool(name) {
  selectedToolName.value = name
  tools.fetchTool(name)
  tools.clearExecutionResult()
  // Reset test params
  Object.keys(testParams).forEach((k) => delete testParams[k])
}

function loadExample(example) {
  Object.assign(testParams, example)
}

async function executeTool() {
  if (!tools.selectedTool) return
  await tools.executeTool(tools.selectedTool.name, testParams)
}

function getRiskStyle(risk) {
  switch (risk) {
    case 'high':
      return 'background: rgba(239, 68, 68, 0.2); color: #f87171'
    case 'medium':
      return 'background: rgba(251, 191, 36, 0.2); color: #fbbf24'
    default:
      return 'background: rgba(34, 197, 94, 0.2); color: #4ade80'
  }
}

function getRiskStatus(risk) {
  switch (risk) {
    case 'high':
      return 'error'
    case 'medium':
      return 'warning'
    default:
      return 'success'
  }
}

function formatResult(result) {
  if (result.success) {
    return JSON.stringify(result.data, null, 2)
  }
  return result.error
}

watch(
  () => tools.selectedTool,
  (tool) => {
    if (tool?.parameters) {
      tool.parameters.forEach((p) => {
        if (!(p.name in testParams)) {
          testParams[p.name] = p.default || ''
        }
      })
    }
  }
)
</script>
