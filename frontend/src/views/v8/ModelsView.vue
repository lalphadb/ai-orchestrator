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
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
        Models
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Modèles LLM disponibles via Ollama ({{ models.length }})
      </p>
    </header>

    <!-- Category filter -->
    <div v-if="categories.length > 1" class="mb-4 flex gap-2 flex-wrap">
      <ModernButton
        v-for="cat in categories"
        :key="cat"
        :variant="selectedCategory === cat ? 'primary' : 'secondary'"
        size="sm"
        @click="selectedCategory = cat"
      >
        {{ cat === 'all' ? 'Tous' : cat }}
      </ModernButton>
    </div>

    <div class="flex-1 overflow-auto">
      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <SkeletonLoader v-for="i in 6" :key="i" variant="rect" :height="200" />
      </div>

      <!-- Error State -->
      <GlassCard
        v-else-if="error"
        variant="bordered"
        padding="md"
        style="border-color: var(--color-error-border); background: rgba(239, 68, 68, 0.1)"
      >
        <p class="body-default" style="color: var(--color-error)">{{ error }}</p>
        <ModernButton
          variant="danger"
          size="sm"
          style="margin-top: var(--space-3)"
          @click="fetchModels"
        >
          Réessayer
        </ModernButton>
      </GlassCard>

      <!-- Empty State -->
      <EmptyState
        v-else-if="filteredModels.length === 0"
        title="Aucun modèle disponible"
        message="Vérifiez la connexion Ollama"
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
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        </template>
      </EmptyState>

      <!-- Models Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <GlassCard
          v-for="model in filteredModels"
          :key="model.name"
          :variant="model.name === currentModel ? 'elevated' : 'bordered'"
          :glow="model.name === currentModel"
          padding="md"
        >
          <div class="flex items-start justify-between" style="margin-bottom: var(--space-3)">
            <div class="flex-1 min-w-0">
              <h3 class="heading-4 truncate" :title="model.name">{{ model.name }}</h3>
              <div class="flex items-center gap-2" style="margin-top: var(--space-1)">
                <span class="label" style="color: var(--text-tertiary)">{{
                  formatSize(model.size)
                }}</span>
                <span
                  v-if="model.category"
                  class="label"
                  style="
                    padding: var(--space-1) var(--space-2);
                    background: var(--bg-surface);
                    border-radius: var(--radius-sm);
                    color: var(--text-tertiary);
                  "
                >
                  {{ model.category }}
                </span>
              </div>
            </div>
            <StatusOrb
              :status="
                model.name === currentModel ? 'active' : model.available ? 'success' : 'default'
              "
              :label="
                model.name === currentModel ? 'Actif' : model.available ? 'Prêt' : 'Non dispo'
              "
              :pulse="model.name === currentModel"
              size="sm"
            />
          </div>

          <div class="grid grid-cols-2 gap-2 body-small" style="margin-top: var(--space-3)">
            <div>
              <span style="color: var(--text-tertiary)">Format:</span>
              <span style="margin-left: var(--space-1)">{{ model.details?.format || 'N/A' }}</span>
            </div>
            <div>
              <span style="color: var(--text-tertiary)">Famille:</span>
              <span style="margin-left: var(--space-1)">{{ model.details?.family || 'N/A' }}</span>
            </div>
            <div>
              <span style="color: var(--text-tertiary)">Taille:</span>
              <span style="margin-left: var(--space-1)">{{
                model.details?.parameter_size || 'N/A'
              }}</span>
            </div>
            <div>
              <span style="color: var(--text-tertiary)">Quant:</span>
              <span style="margin-left: var(--space-1)">{{
                model.details?.quantization_level || 'N/A'
              }}</span>
            </div>
          </div>

          <ModernButton
            :variant="model.name === currentModel ? 'primary' : 'secondary'"
            size="sm"
            :disabled="model.name === currentModel"
            style="width: 100%; margin-top: var(--space-4)"
            @click="setModel(model.name)"
          >
            {{ model.name === currentModel ? '✓ Modèle actif' : 'Utiliser ce modèle' }}
          </ModernButton>
        </GlassCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useChatStore } from '@/stores/chat'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'

const chat = useChatStore()

const models = ref([])
const currentModel = computed(() => chat.currentModel)
const loading = ref(true)
const error = ref(null)
const selectedCategory = ref('all')

const categories = computed(() => {
  const cats = new Set(models.value.map((m) => m.category).filter(Boolean))
  return ['all', ...Array.from(cats).sort()]
})

const filteredModels = computed(() => {
  if (selectedCategory.value === 'all') return models.value
  return models.value.filter((m) => m.category === selectedCategory.value)
})

const formatSize = (bytes) => {
  if (!bytes) return 'N/A'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(0)} MB`
}

const fetchModels = async () => {
  loading.value = true
  error.value = null
  try {
    // api.get() returns parsed JSON directly (not Axios .data wrapper)
    const response = await api.get('/system/models')
    models.value = response.models || []
    // Backend returns default_model, not current_model
    if (response.default_model && !chat.currentModel) {
      chat.setModel(response.default_model)
    }
  } catch (err) {
    error.value = 'Impossible de charger les modèles: ' + (err.message || 'Erreur inconnue')
    console.error('[ModelsView] fetchModels error:', err)
  } finally {
    loading.value = false
  }
}

const setModel = (modelName) => {
  chat.setModel(modelName)
}

onMounted(fetchModels)
</script>
