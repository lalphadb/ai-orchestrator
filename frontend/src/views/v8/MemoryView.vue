<template>
  <div class="h-full flex flex-col bg-gray-900 text-gray-100 p-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold flex items-center gap-3">
        <svg class="w-7 h-7 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        Memory (ChromaDB)
      </h1>
      <p class="text-gray-400 text-sm mt-1">Mémoire sémantique et embeddings</p>
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
      <div v-if="searching" class="flex items-center justify-center h-64">
        <div class="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"></div>
      </div>
      
      <div v-else-if="results.length === 0 && searchQuery" class="text-center text-gray-500 py-12">
        Aucun résultat pour "{{ searchQuery }}"
      </div>
      
      <div v-else-if="results.length === 0" class="text-center text-gray-500 py-12">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p>Entrez une requête pour rechercher dans la mémoire</p>
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
                <span class="px-2 py-0.5 bg-primary-500/20 text-primary-400 rounded text-xs">
                  Score: {{ (result.score * 100).toFixed(1) }}%
                </span>
                <span v-if="result.metadata?.topic" class="px-2 py-0.5 bg-gray-700 rounded text-xs">
                  {{ result.metadata.topic }}
                </span>
              </div>
              <p class="text-gray-300">{{ result.document }}</p>
            </div>
          </div>
          
          <div v-if="result.metadata" class="mt-3 text-xs text-gray-500">
            <span v-if="result.metadata.timestamp">
              {{ new Date(result.metadata.timestamp).toLocaleString('fr-CA') }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Stats -->
    <div class="mt-6 pt-4 border-t border-gray-800">
      <div class="flex items-center gap-6 text-sm text-gray-400">
        <div>Collections: <span class="text-gray-200">{{ stats.collections || 'N/A' }}</span></div>
        <div>Documents: <span class="text-gray-200">{{ stats.documents || 'N/A' }}</span></div>
        <div>Status: 
          <span :class="stats.connected ? 'text-green-400' : 'text-red-400'">
            {{ stats.connected ? 'Connecté' : 'Déconnecté' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const searchQuery = ref('')
const searching = ref(false)
const results = ref([])
const stats = ref({ connected: false, collections: 0, documents: 0 })

const search = async () => {
  if (!searchQuery.value.trim()) return

  searching.value = true
  try {
    const response = await api.get('/api/v1/learning/experiences', {
      params: {
        query: searchQuery.value,
        limit: 10
      }
    })
    results.value = response.data || []
  } catch (err) {
    console.error('Search failed:', err)
    results.value = []
  } finally {
    searching.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await api.get('/api/v1/learning/stats')
    stats.value = response.data
  } catch (err) {
    stats.value = { connected: false, collections: 0, documents: 0 }
  }
}

onMounted(fetchStats)
</script>
