<template>
  <div class="h-[calc(100vh-3.5rem)] flex">
    <!-- Tools List -->
    <div class="w-80 flex-shrink-0 flex flex-col bg-gray-900/50 border-r border-gray-700/50">
      <!-- Search & Filter -->
      <div class="p-4 space-y-3 border-b border-gray-700/50">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
            v-model="tools.searchQuery"
            type="text"
            placeholder="Rechercher un outil..."
            class="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
          />
        </div>
        
        <select
          v-model="tools.selectedCategory"
          class="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-primary-500/50"
        >
          <option value="all">Toutes les catégories</option>
          <option v-for="cat in tools.categories.filter(c => c !== 'all')" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>
      
      <!-- Tools list -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="tools.loading" class="flex items-center justify-center py-8">
          <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"></div>
        </div>
        
        <div v-else-if="tools.filteredTools.length === 0" class="text-center py-8 text-gray-500 text-sm">
          Aucun outil trouvé
        </div>
        
        <div v-else class="p-2 space-y-1">
          <button
            v-for="tool in tools.filteredTools"
            :key="tool.name"
            @click="selectTool(tool.name)"
            class="w-full px-3 py-2.5 rounded-lg text-left transition-colors"
            :class="selectedToolName === tool.name 
              ? 'bg-primary-600/20 border border-primary-500/30' 
              : 'hover:bg-gray-800/50 border border-transparent'"
          >
            <div class="flex items-start gap-2">
              <div 
                class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                :class="getRiskClass(tool.risk_level)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-200 truncate">{{ tool.name }}</p>
                <p class="text-xs text-gray-500 truncate">{{ tool.category }}</p>
              </div>
            </div>
          </button>
        </div>
      </div>
      
      <!-- Stats -->
      <div class="p-3 border-t border-gray-700/50 text-xs text-gray-500">
        {{ tools.filteredTools.length }} / {{ tools.tools.length }} outils
      </div>
    </div>
    
    <!-- Tool Detail -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <div v-if="!tools.selectedTool" class="flex-1 flex items-center justify-center text-gray-500">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <p>Sélectionnez un outil pour voir les détails</p>
        </div>
      </div>
      
      <div v-else class="flex-1 overflow-y-auto p-6">
        <!-- Header -->
        <div class="flex items-start justify-between mb-6">
          <div>
            <h2 class="text-2xl font-semibold text-white mb-2">{{ tools.selectedTool.name }}</h2>
            <div class="flex items-center gap-3">
              <span class="px-2 py-0.5 bg-gray-700/50 rounded text-xs text-gray-300">
                {{ tools.selectedTool.category }}
              </span>
              <span 
                class="px-2 py-0.5 rounded text-xs"
                :class="getRiskBadgeClass(tools.selectedTool.risk_level)"
              >
                {{ tools.selectedTool.risk_level || 'low' }} risk
              </span>
              <span v-if="tools.selectedTool.usage_count" class="text-xs text-gray-500">
                {{ tools.selectedTool.usage_count }} utilisations
              </span>
            </div>
          </div>
        </div>
        
        <!-- Description -->
        <div class="mb-6">
          <h3 class="text-sm font-medium text-gray-400 mb-2">Description</h3>
          <p class="text-gray-300">{{ tools.selectedTool.description }}</p>
        </div>
        
        <!-- Parameters -->
        <div v-if="tools.selectedTool.parameters?.length" class="mb-6">
          <h3 class="text-sm font-medium text-gray-400 mb-3">Paramètres</h3>
          <div class="space-y-3">
            <div 
              v-for="param in tools.selectedTool.parameters"
              :key="param.name"
              class="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50"
            >
              <div class="flex items-center gap-2 mb-1">
                <code class="text-sm text-primary-400">{{ param.name }}</code>
                <span class="text-xs text-gray-500">{{ param.type }}</span>
                <span v-if="param.required" class="text-xs text-red-400">requis</span>
              </div>
              <p class="text-sm text-gray-400">{{ param.description }}</p>
            </div>
          </div>
        </div>
        
        <!-- Examples -->
        <div v-if="tools.selectedTool.examples?.length" class="mb-6">
          <h3 class="text-sm font-medium text-gray-400 mb-3">Exemples</h3>
          <div class="space-y-2">
            <button
              v-for="(example, idx) in tools.selectedTool.examples"
              :key="idx"
              @click="loadExample(example)"
              class="w-full p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 text-left hover:border-primary-500/50 transition-colors"
            >
              <pre class="text-sm text-gray-300 overflow-x-auto">{{ JSON.stringify(example, null, 2) }}</pre>
            </button>
          </div>
        </div>
        
        <!-- Test Form (admin only) -->
        <div v-if="auth.isAdmin" class="mb-6">
          <h3 class="text-sm font-medium text-gray-400 mb-3">Tester l'outil</h3>
          <div class="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
            <div class="space-y-3 mb-4">
              <div v-for="param in tools.selectedTool.parameters" :key="param.name">
                <label class="block text-sm text-gray-400 mb-1">
                  {{ param.name }}
                  <span v-if="param.required" class="text-red-400">*</span>
                </label>
                <input
                  v-model="testParams[param.name]"
                  :type="param.type === 'integer' ? 'number' : 'text'"
                  :placeholder="param.description"
                  class="w-full px-3 py-2 bg-gray-900/50 border border-gray-700/50 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
                />
              </div>
            </div>
            
            <button
              @click="executeTool"
              :disabled="tools.executing"
              class="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <svg v-if="tools.executing" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>{{ tools.executing ? 'Exécution...' : 'Exécuter' }}</span>
            </button>
          </div>
          
          <!-- Execution result -->
          <div v-if="tools.executionResult" class="mt-4 p-4 rounded-lg border" :class="tools.executionResult.success ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'">
            <div class="flex items-center gap-2 mb-2">
              <svg v-if="tools.executionResult.success" class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <svg v-else class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span :class="tools.executionResult.success ? 'text-green-300' : 'text-red-300'">
                {{ tools.executionResult.success ? 'Succès' : 'Erreur' }}
              </span>
            </div>
            <pre class="text-sm text-gray-300 bg-gray-900/50 rounded p-3 overflow-x-auto">{{ formatResult(tools.executionResult) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useToolsStore } from '@/stores/tools'
import { useAuthStore } from '@/stores/auth'

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
  Object.keys(testParams).forEach(k => delete testParams[k])
}

function loadExample(example) {
  Object.assign(testParams, example)
}

async function executeTool() {
  if (!tools.selectedTool) return
  await tools.executeTool(tools.selectedTool.name, testParams)
}

function getRiskClass(risk) {
  switch (risk) {
    case 'high': return 'bg-red-500/20 text-red-400'
    case 'medium': return 'bg-yellow-500/20 text-yellow-400'
    default: return 'bg-green-500/20 text-green-400'
  }
}

function getRiskBadgeClass(risk) {
  switch (risk) {
    case 'high': return 'bg-red-500/20 text-red-300'
    case 'medium': return 'bg-yellow-500/20 text-yellow-300'
    default: return 'bg-green-500/20 text-green-300'
  }
}

function formatResult(result) {
  if (result.success) {
    return JSON.stringify(result.data, null, 2)
  }
  return result.error
}

watch(() => tools.selectedTool, (tool) => {
  if (tool?.parameters) {
    tool.parameters.forEach(p => {
      if (!(p.name in testParams)) {
        testParams[p.name] = p.default || ''
      }
    })
  }
})
</script>
