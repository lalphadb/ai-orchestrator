<template>
  <div class="h-full flex flex-col bg-gray-900 text-gray-100 p-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold flex items-center gap-3">
        <svg class="w-7 h-7 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        Models
      </h1>
      <p class="text-gray-400 text-sm mt-1">Modèles LLM disponibles via Ollama ({{ models?.length ?? 0 }})</p>
    </header>
    
    <!-- Category filter -->
    <div v-if="categories.length > 1" class="mb-4 flex gap-2 flex-wrap">
      <button
        v-for="cat in categories"
        :key="cat"
        @click="selectedCategory = cat"
        class="px-3 py-1 rounded-lg text-sm transition"
        :class="selectedCategory === cat ? 'bg-primary-500/30 text-primary-300 border border-primary-500/50' : 'bg-gray-800 text-gray-400 border border-gray-700 hover:bg-gray-700'"
      >
        {{ cat === 'all' ? 'Tous' : cat }}
      </button>
    </div>
    
    <div class="flex-1 overflow-auto">
      <!-- CRQ-2026-0203-001: Skeleton loader for better UX -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="i" class="bg-gray-800/30 border border-gray-700/30 rounded-xl p-5 animate-pulse">
          <div class="h-6 bg-gray-700/50 rounded w-3/4 mb-3"></div>
          <div class="h-4 bg-gray-700/30 rounded w-1/2 mb-4"></div>
          <div class="grid grid-cols-2 gap-2">
            <div class="h-3 bg-gray-700/30 rounded"></div>
            <div class="h-3 bg-gray-700/30 rounded"></div>
            <div class="h-3 bg-gray-700/30 rounded"></div>
            <div class="h-3 bg-gray-700/30 rounded"></div>
          </div>
          <div class="h-8 bg-gray-700/30 rounded mt-4"></div>
        </div>
      </div>
      
      <div v-else-if="error" class="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
        <p class="text-red-400">{{ error }}</p>
        <button @click="fetchModels" class="mt-3 px-4 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded text-sm text-red-300 transition">
          Réessayer
        </button>
      </div>
      
      <div v-else-if="filteredModels.length === 0" class="flex items-center justify-center h-64 text-gray-500">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p class="text-lg">Aucun modèle disponible</p>
          <p class="text-sm mt-1">Vérifiez la connexion Ollama</p>
        </div>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div 
          v-for="model in filteredModels" 
          :key="model.name"
          class="bg-gray-800/50 border rounded-xl p-5 transition-all"
          :class="model.name === currentModel ? 'border-primary-500/50 ring-1 ring-primary-500/20' : 'border-gray-700/50 hover:border-gray-600'"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-lg truncate" :title="model?.name">{{ model?.name ?? 'Unknown' }}</h3>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-xs text-gray-500">{{ formatSize(model?.size) }}</span>
                <span v-if="model?.category" class="text-xs px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400">
                  {{ model.category }}
                </span>
              </div>
            </div>
            <span 
              class="px-2 py-0.5 rounded text-xs flex-shrink-0 ml-2"
              :class="model.name === currentModel ? 'bg-primary-500/20 text-primary-400' : model.available ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/20 text-gray-400'"
            >
              {{ model.name === currentModel ? '● Actif' : model.available ? 'Prêt' : 'Non dispo' }}
            </span>
          </div>
          
          <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="text-gray-500">Format:</span>
              <span class="ml-1 text-gray-300">{{ model.details?.format || 'N/A' }}</span>
            </div>
            <div>
              <span class="text-gray-500">Famille:</span>
              <span class="ml-1 text-gray-300">{{ model.details?.family || 'N/A' }}</span>
            </div>
            <div>
              <span class="text-gray-500">Taille:</span>
              <span class="ml-1 text-gray-300">{{ model.details?.parameter_size || 'N/A' }}</span>
            </div>
            <div>
              <span class="text-gray-500">Quant:</span>
              <span class="ml-1 text-gray-300">{{ model.details?.quantization_level || 'N/A' }}</span>
            </div>
          </div>
          
          <div class="mt-4">
            <button 
              @click="setModel(model.name)"
              class="w-full px-3 py-1.5 rounded-lg text-sm transition"
              :class="model.name === currentModel ? 'bg-primary-500/20 text-primary-400 cursor-default' : 'bg-gray-700 hover:bg-gray-600 text-gray-200'"
              :disabled="model.name === currentModel"
            >
              {{ model.name === currentModel ? '✓ Modèle actif' : 'Utiliser ce modèle' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const models = ref([])
const currentModel = computed(() => chat.currentModel)
const loading = ref(true)
const error = ref(null)
const selectedCategory = ref('all')

const categories = computed(() => {
  // CRQ-2026-0203-001: Safe access with optional chaining
  const cats = new Set(models.value?.map(m => m?.category).filter(Boolean) ?? [])
  return ['all', ...Array.from(cats).sort()]
})

const filteredModels = computed(() => {
  // CRQ-2026-0203-001: Safe access with optional chaining
  if (!models.value) return []
  if (selectedCategory.value === 'all') return models.value
  return models.value.filter(m => m?.category === selectedCategory.value)
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
    // CRQ-2026-0203-001: Enhanced error handling with optional chaining
    // api.get() returns parsed JSON directly (not Axios .data wrapper)
    const response = await api.get('/system/models')

    // Safe access to response properties
    if (!response) {
      throw new Error('Réponse vide du serveur')
    }

    models.value = Array.isArray(response.models) ? response.models : []

    // Backend returns default_model, not current_model
    if (response?.default_model && !chat.currentModel) {
      chat.setModel(response.default_model)
    }
  } catch (err) {
    // CRQ-2026-0203-001: Detailed error message for debugging
    const errorMsg = err?.message || err?.detail || 'Erreur inconnue'
    error.value = `Impossible de charger les modèles: ${errorMsg}`
    console.error('[ModelsView] fetchModels error:', {
      message: err?.message,
      status: err?.status,
      data: err?.data,
      stack: err?.stack
    })
    // Ensure models is still an empty array on error
    models.value = []
  } finally {
    loading.value = false
  }
}

const setModel = (modelName) => {
  chat.setModel(modelName)
}

onMounted(fetchModels)
</script>
