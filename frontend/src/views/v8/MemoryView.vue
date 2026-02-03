<template>
  <div class="h-full flex flex-col bg-gray-900 text-gray-100 p-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold flex items-center gap-3">
        <svg class="w-7 h-7 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        Memory
      </h1>
      <p class="text-gray-400 text-sm mt-1">Mémoire d'apprentissage et expériences</p>
    </header>
    
    <!-- Search -->
    <div class="mb-6">
      <div class="flex gap-3">
        <input 
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher dans la mémoire..."
          class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-primary-500"
          @keyup.enter="search"
        />
        <button 
          @click="search"
          class="px-6 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg transition"
          :disabled="searching"
        >
          {{ searching ? 'Recherche...' : 'Rechercher' }}
        </button>
      </div>
    </div>
    
    <!-- Results -->
    <div class="flex-1 overflow-auto">
      <!-- CRQ-2026-0203-001: Skeleton loader for better UX -->
      <div v-if="searching" class="space-y-4">
        <div v-for="i in 3" :key="i" class="bg-gray-800/30 border border-gray-700/30 rounded-xl p-5 animate-pulse">
          <div class="flex items-center gap-2 mb-3">
            <div class="h-5 bg-gray-700/50 rounded w-16"></div>
            <div class="h-5 bg-gray-700/50 rounded w-20"></div>
          </div>
          <div class="h-4 bg-gray-700/30 rounded w-full mb-2"></div>
          <div class="h-4 bg-gray-700/30 rounded w-3/4 mb-3"></div>
          <div class="h-3 bg-gray-700/20 rounded w-1/3"></div>
        </div>
      </div>

      <div v-else-if="error" class="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
        <p class="text-red-400">{{ error }}</p>
        <button @click="fetchStats" class="mt-3 px-4 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded text-sm text-red-300 transition">
          Réessayer
        </button>
      </div>
      
      <div v-else-if="results.length === 0 && hasSearched" class="text-center text-gray-500 py-12">
        <p>Aucun résultat pour "{{ lastQuery }}"</p>
      </div>
      
      <div v-else-if="results.length === 0" class="text-center text-gray-500 py-12">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-lg">Mémoire d'apprentissage</p>
        <p class="text-sm mt-2">Entrez une requête pour rechercher dans les expériences</p>
      </div>
      
      <div v-else class="space-y-4">
        <div 
          v-for="(result, idx) in results" 
          :key="idx"
          class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span v-if="result.score != null" class="px-2 py-0.5 bg-primary-500/20 text-primary-400 rounded text-xs">
                  Score: {{ (result.score * 100).toFixed(1) }}%
                </span>
                <span v-if="result.metadata?.topic || result.topic" class="px-2 py-0.5 bg-gray-700 rounded text-xs">
                  {{ result.metadata?.topic || result.topic }}
                </span>
                <span v-if="result.type" class="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                  {{ result.type }}
                </span>
              </div>
              <!-- CRQ-2026-0203-001: Safe access with optional chaining -->
              <p class="text-gray-300">{{ result?.document || result?.content || result?.query || 'Contenu indisponible' }}</p>
              <p v-if="result?.response" class="text-gray-400 text-sm mt-2 line-clamp-3">{{ result.response }}</p>
            </div>
          </div>
          
          <div class="mt-3 text-xs text-gray-500 flex gap-4">
            <span v-if="result.metadata?.timestamp || result.timestamp">
              {{ new Date(result.metadata?.timestamp || result.timestamp).toLocaleString('fr-CA') }}
            </span>
            <span v-if="result.tools_used?.length">
              Outils: {{ result.tools_used.join(', ') }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Stats -->
    <div class="mt-6 pt-4 border-t border-gray-800">
      <div v-if="statsLoading" class="text-sm text-gray-500">Chargement des stats...</div>
      <!-- CRQ-2026-0203-001: Safe access with optional chaining -->
      <div v-else class="flex items-center gap-6 text-sm text-gray-400 flex-wrap">
        <div>Status:
          <span :class="stats?.status === 'active' || stats?.status === 'healthy' ? 'text-green-400' : stats?.status === 'error' ? 'text-red-400' : 'text-yellow-400'">
            {{ stats?.status || 'inconnu' }}
          </span>
        </div>
        <div>Expériences: <span class="text-gray-200">{{ stats?.experiences_count ?? 'N/A' }}</span></div>
        <div>Patterns: <span class="text-gray-200">{{ stats?.patterns_count ?? 'N/A' }}</span></div>
        <div>Corrections: <span class="text-gray-200">{{ stats?.corrections_count ?? 'N/A' }}</span></div>
        <div>Contextes: <span class="text-gray-200">{{ stats?.user_contexts_count ?? 'N/A' }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const searchQuery = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const lastQuery = ref('')
const results = ref([])
const error = ref(null)
const stats = ref({})
const statsLoading = ref(true)

const search = async () => {
  if (!searchQuery.value?.trim()) return

  searching.value = true
  hasSearched.value = true
  lastQuery.value = searchQuery.value
  error.value = null
  try {
    const query = encodeURIComponent(searchQuery.value)
    // CRQ-2026-0203-001: Enhanced error handling with optional chaining
    // api.get() returns parsed JSON directly (not .data wrapper)
    const response = await api.get(`/learning/experiences?query=${query}&limit=10`)

    // Safe access to response properties
    if (!response) {
      results.value = []
      return
    }

    // Response could be an array or object with results
    results.value = Array.isArray(response) ? response : (response?.experiences || response?.results || [])
  } catch (err) {
    console.error('[MemoryView] search error:', {
      message: err?.message,
      status: err?.status,
      data: err?.data
    })
    const errorMsg = err?.message || err?.detail || 'Erreur inconnue'
    error.value = `Erreur de recherche: ${errorMsg}`
    results.value = []
  } finally {
    searching.value = false
  }
}

const fetchStats = async () => {
  statsLoading.value = true
  error.value = null
  try {
    // CRQ-2026-0203-001: Enhanced error handling with optional chaining
    // api.get() returns parsed JSON directly
    // Backend returns: {status, experiences_count, patterns_count, corrections_count, user_contexts_count}
    const response = await api.get('/learning/stats')

    // Safe access with fallback to empty object
    stats.value = response ?? {}
  } catch (err) {
    console.error('[MemoryView] fetchStats error:', {
      message: err?.message,
      status: err?.status,
      data: err?.data
    })
    stats.value = {
      status: 'error',
      experiences_count: 0,
      patterns_count: 0,
      corrections_count: 0,
      user_contexts_count: 0
    }
    // Don't show error for stats - page is still usable for search
  } finally {
    statsLoading.value = false
  }
}

onMounted(fetchStats)
</script>
