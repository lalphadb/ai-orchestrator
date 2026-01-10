<template>
  <div class="models-display bg-gray-900/50 rounded-xl p-4 border border-gray-700/50">
    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
      <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
      </svg>
      Modèles LLM Disponibles
    </h3>

    <!-- Summary -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
      <div class="bg-gray-800/50 rounded-lg p-2 text-center">
        <div class="text-xl font-bold text-primary-400">{{ totalModels }}</div>
        <div class="text-xs text-gray-400">Total</div>
      </div>
      <div class="bg-gray-800/50 rounded-lg p-2 text-center">
        <div class="text-xl font-bold text-green-400">{{ localModels }}</div>
        <div class="text-xs text-gray-400">Locaux</div>
      </div>
      <div class="bg-gray-800/50 rounded-lg p-2 text-center">
        <div class="text-xl font-bold text-blue-400">{{ cloudModels }}</div>
        <div class="text-xs text-gray-400">Cloud</div>
      </div>
      <div class="bg-gray-800/50 rounded-lg p-2 text-center">
        <div class="text-xl font-bold text-purple-400">{{ formatSize(totalSize) }}</div>
        <div class="text-xs text-gray-400">Espace</div>
      </div>
    </div>

    <!-- Categories -->
    <div class="space-y-4">
      <CategorySection 
        v-for="cat in categories" 
        :key="cat.name"
        :category="cat"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import CategorySection from './CategorySection.vue'

const props = defineProps({
  models: { type: Array, required: true }
})

// Categorize models
const categories = computed(() => {
  const cats = {
    general: { name: '🧠 Généraux', icon: 'brain', models: [], color: 'emerald' },
    code: { name: '💻 Code', icon: 'code', models: [], color: 'blue' },
    vision: { name: '👁️ Vision', icon: 'eye', models: [], color: 'purple' },
    embedding: { name: '🔍 Embeddings & RAG', icon: 'search', models: [], color: 'amber' },
    safety: { name: '🛡️ Sécurité', icon: 'shield', models: [], color: 'red' },
    cloud: { name: '☁️ Cloud Proxies', icon: 'cloud', models: [], color: 'cyan' }
  }

  for (const model of props.models) {
    const name = model.name?.toLowerCase() || ''
    const size = model.size || 0

    // Cloud proxies (très petite taille = config seulement)
    if (size < 1000 || name.includes('cloud') || name.includes('gemini') || name.includes('kimi')) {
      cats.cloud.models.push(model)
    }
    // Embeddings
    else if (name.includes('embed') || name.includes('nomic') || name.includes('bge') || name.includes('mxbai')) {
      cats.embedding.models.push(model)
    }
    // Reranker (aussi embeddings/RAG)
    else if (name.includes('rerank')) {
      cats.embedding.models.push(model)
    }
    // Vision
    else if (name.includes('vision') || name.includes('-vl') || name.includes('vl:')) {
      cats.vision.models.push(model)
    }
    // Code
    else if (name.includes('coder') || name.includes('code')) {
      cats.code.models.push(model)
    }
    // Safety
    else if (name.includes('safeguard') || name.includes('guard') || name.includes('safety')) {
      cats.safety.models.push(model)
    }
    // General (default)
    else {
      cats.general.models.push(model)
    }
  }

  // Filter out empty categories and sort models by size
  return Object.values(cats)
    .filter(c => c.models.length > 0)
    .map(c => ({
      ...c,
      models: c.models.sort((a, b) => (b.size || 0) - (a.size || 0))
    }))
})

const totalModels = computed(() => props.models.filter(m => m.available !== false).length)
const localModels = computed(() => props.models.filter(m => m.available !== false && (m.size || 0) > 1000).length)
const cloudModels = computed(() => props.models.filter(m => m.available !== false && (m.size || 0) < 1000).length)
const totalSize = computed(() => props.models.reduce((acc, m) => acc + (m.size || 0), 0))

function formatSize(bytes) {
  if (!bytes || bytes < 1000) return '< 1 KB'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(0)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(0)} MB`
}
</script>
