<template>
  <div class="category-section">
    <button 
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between p-3 bg-gray-800/30 hover:bg-gray-800/50 rounded-lg transition-colors"
    >
      <div class="flex items-center gap-2">
        <span class="text-base">{{ category.name }}</span>
        <span class="px-2 py-0.5 bg-gray-700/50 rounded-full text-xs text-gray-400">
          {{ category.models.length }}
        </span>
      </div>
      <svg 
        class="w-4 h-4 text-gray-400 transition-transform" 
        :class="{ 'rotate-180': expanded }"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </button>

    <div v-show="expanded" class="mt-2 space-y-1">
      <div 
        v-for="model in category.models" 
        :key="model.name"
        class="flex items-center justify-between p-2 bg-gray-800/20 rounded-lg hover:bg-gray-800/40 transition-colors"
      >
        <div class="flex items-center gap-2 min-w-0">
          <!-- Status indicator -->
          <div 
            class="w-2 h-2 rounded-full flex-shrink-0"
            :class="model.available !== false ? 'bg-green-500' : 'bg-gray-500'"
          ></div>
          
          <!-- Model name -->
          <span class="text-sm text-gray-200 truncate" :title="model.name">
            {{ formatName(model.name) }}
          </span>
          
          <!-- Quantization badge -->
          <span 
            v-if="getQuantization(model.name)"
            class="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs text-gray-400 flex-shrink-0"
          >
            {{ getQuantization(model.name) }}
          </span>
        </div>

        <div class="flex items-center gap-3 text-xs text-gray-500 flex-shrink-0">
          <!-- Size -->
          <span v-if="model.size > 1000">{{ formatSize(model.size) }}</span>
          <span v-else class="text-cyan-400">proxy</span>
          
          <!-- Date -->
          <span v-if="model.modified_at" class="hidden md:inline">
            {{ formatDate(model.modified_at) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  category: { type: Object, required: true }
})

const expanded = ref(true)

function formatName(name) {
  if (!name) return name
  // Remove common suffixes for cleaner display
  return name
    .replace(':latest', '')
    .replace('-instruct', '')
    .replace('-q4_K_M', '')
    .replace('-q8_0', '')
}

function getQuantization(name) {
  if (!name) return null
  const match = name.match(/(q\d+_K_M|q\d+_\d+|q\d+)/i)
  return match ? match[1].toUpperCase() : null
}

function formatSize(bytes) {
  if (!bytes) return ''
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(0)} MB`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return "Aujourd'hui"
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays}j`
  if (diffDays < 30) return `Il y a ${Math.floor(diffDays / 7)}sem`
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}
</script>
