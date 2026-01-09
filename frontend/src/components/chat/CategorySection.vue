<template>
  <div class="category-section">
    <!-- Header cliquable -->
    <button 
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between p-3 bg-gray-800/30 hover:bg-gray-800/50 rounded-lg transition-all duration-200"
      :class="{ 'rounded-b-none': expanded }"
    >
      <div class="flex items-center gap-3">
        <span class="text-lg">{{ category.name }}</span>
        <span 
          class="text-xs px-2 py-0.5 rounded-full"
          :class="getBadgeClass()"
        >
          {{ category.models.length }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">{{ getCategorySize() }}</span>
        <svg 
          class="w-4 h-4 text-gray-400 transition-transform duration-200"
          :class="{ 'rotate-180': expanded }"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
      </div>
    </button>
    
    <!-- Liste des modèles (avec transition) -->
    <transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div 
        v-if="expanded" 
        class="bg-gray-800/20 rounded-b-lg border-t border-gray-700/30 p-2 space-y-1"
      >
        <!-- Description de la catégorie -->
        <p v-if="category.description" class="text-xs text-gray-500 px-2 py-1 italic">
          {{ category.description }}
        </p>
        
        <!-- Liste des modèles -->
        <div 
          v-for="model in category.models" 
          :key="model.name"
          class="flex items-center justify-between p-2 hover:bg-gray-700/30 rounded-lg transition-colors group"
        >
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <!-- Indicateur de disponibilité -->
            <span 
              class="w-2 h-2 rounded-full flex-shrink-0"
              :class="model.available !== false ? 'bg-green-400' : 'bg-red-400'"
              :title="model.available !== false ? 'Disponible' : 'Non disponible'"
            ></span>
            
            <!-- Nom du modèle -->
            <span class="text-gray-200 font-mono text-xs truncate" :title="model.name">
              {{ model.name }}
            </span>
            
            <!-- Badge cloud si applicable -->
            <span 
              v-if="isCloudModel(model)"
              class="text-[10px] px-1.5 py-0.5 bg-cyan-900/50 text-cyan-300 rounded"
            >
              cloud
            </span>
          </div>
          
          <!-- Infos à droite -->
          <div class="flex items-center gap-3 text-xs text-gray-500 flex-shrink-0">
            <!-- Taille -->
            <span class="font-mono">{{ formatSize(model.size) }}</span>
            
            <!-- Date de modification (au hover) -->
            <span 
              v-if="model.modified_at"
              class="hidden group-hover:inline text-gray-600"
            >
              {{ formatDate(model.modified_at) }}
            </span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  category: { type: Object, required: true },
  defaultExpanded: { type: Boolean, default: true }
})

const expanded = ref(props.defaultExpanded)

// Couleurs selon la catégorie
function getBadgeClass() {
  const colorMap = {
    'emerald': 'bg-emerald-900/50 text-emerald-300',
    'blue': 'bg-blue-900/50 text-blue-300',
    'purple': 'bg-purple-900/50 text-purple-300',
    'amber': 'bg-amber-900/50 text-amber-300',
    'red': 'bg-red-900/50 text-red-300',
    'cyan': 'bg-cyan-900/50 text-cyan-300'
  }
  return colorMap[props.category.color] || 'bg-gray-700 text-gray-300'
}

// Taille totale de la catégorie
function getCategorySize() {
  const total = props.category.models.reduce((acc, m) => acc + (m.size || 0), 0)
  return formatSize(total)
}

// Vérifier si c'est un modèle cloud
function isCloudModel(model) {
  const name = model.name?.toLowerCase() || ''
  const size = model.size || 0
  return size < 1000 || name.includes('cloud') || name.includes('gemini') || name.includes('kimi')
}

function formatSize(bytes) {
  if (!bytes || bytes < 1000) return '< 1 KB'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(0)} MB`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
  } catch {
    return ''
  }
}
</script>
