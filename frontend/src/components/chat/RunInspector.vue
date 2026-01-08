<template>
  <div class="h-full flex flex-col bg-gray-900/50 border-l border-gray-700/50">
    <!-- Header -->
    <div class="p-3 border-b border-gray-700/50 flex items-center justify-between">
      <h3 class="font-medium text-gray-300 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        Run Inspector
      </h3>
      <div class="flex items-center gap-2">
        <span 
          class="px-2 py-0.5 rounded-full text-xs font-medium"
          :class="phaseClass"
        >
          {{ phaseLabel }}
        </span>
      </div>
    </div>
    
    <!-- No run -->
    <div v-if="!run" class="flex-1 flex items-center justify-center text-gray-500 text-sm p-4 text-center">
      <div>
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
        <p>Envoyez un message pour voir<br/>la trace d'exécution ici</p>
      </div>
    </div>
    
    <!-- Run content -->
    <div v-else class="flex-1 overflow-y-auto">
      <!-- Current Status -->
      <div v-if="run.currentPhase !== 'complete' && run.currentPhase !== 'error'" class="p-3 bg-primary-600/10 border-b border-primary-500/20">
        <div class="flex items-center gap-2">
          <div class="animate-spin w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full"></div>
          <span class="text-sm text-primary-300">
            <template v-if="run.currentPhase === 'thinking'">
              Réflexion (itération {{ run.currentIteration }})...
            </template>
            <template v-else-if="run.currentPhase === 'tool'">
              Exécution: {{ run.currentTool }}
            </template>
            <template v-else-if="run.currentPhase === 'streaming'">
              Génération de la réponse...
            </template>
            <template v-else>
              Démarrage...
            </template>
          </span>
        </div>
      </div>
      
      <!-- Timeline -->
      <div class="p-3 space-y-3">
        <!-- Model -->
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          <span>{{ run.model }}</span>
        </div>
        
        <!-- Thinking steps -->
        <div v-if="run.thinking.length > 0 && chat.settings.showThinking" class="space-y-2">
          <div 
            v-for="(thought, idx) in run.thinking" 
            :key="'t-' + idx"
            class="flex gap-2"
          >
            <div class="flex-shrink-0 w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <span class="text-xs text-yellow-400">{{ thought.iteration }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs text-yellow-300/80">Thinking</p>
              <p class="text-sm text-gray-300 break-words">{{ thought.message }}</p>
            </div>
          </div>
        </div>
        
        <!-- Tool calls -->
        <div v-if="run.toolCalls.length > 0" class="space-y-2">
          <div 
            v-for="(tool, idx) in run.toolCalls" 
            :key="'tool-' + idx"
            class="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <div class="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                <svg class="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              </div>
              <span class="text-sm font-medium text-blue-300">{{ tool.tool }}</span>
              <span class="text-xs text-gray-500">Iter {{ tool.iteration }}</span>
            </div>
            
            <!-- Params -->
            <div v-if="chat.settings.showToolParams && tool.params" class="mt-2">
              <pre class="text-xs text-gray-400 bg-gray-900/50 rounded p-2 overflow-x-auto">{{ formatParams(tool.params) }}</pre>
            </div>
          </div>
        </div>
        
        <!-- Complete -->
        <div v-if="run.complete" class="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="font-medium text-green-300">Terminé</span>
          </div>
          
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="text-gray-500">Durée:</span>
              <span class="text-gray-300 ml-1">{{ formatDuration(run.complete.duration_ms || run.duration) }}</span>
            </div>
            <div>
              <span class="text-gray-500">Itérations:</span>
              <span class="text-gray-300 ml-1">{{ run.complete.iterations || run.toolCalls.length }}</span>
            </div>
          </div>
          
          <div v-if="run.complete.tools_used?.length" class="mt-2">
            <span class="text-xs text-gray-500">Outils utilisés:</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span 
                v-for="t in run.complete.tools_used" 
                :key="t"
                class="px-2 py-0.5 bg-gray-700/50 rounded text-xs text-gray-300"
              >
                {{ t }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Error -->
        <div v-if="run.error" class="bg-red-500/10 rounded-lg p-3 border border-red-500/30">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="font-medium text-red-300">Erreur</span>
          </div>
          <p class="text-sm text-red-200">{{ run.error }}</p>
          <button 
            @click="chat.retryLastMessage()"
            class="mt-3 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-sm rounded transition-colors"
          >
            ↻ Réessayer
          </button>
        </div>
      </div>
    </div>
    
    <!-- Footer with actions -->
    <div v-if="run?.complete" class="p-3 border-t border-gray-700/50">
      <div class="flex gap-2">
        <button
          @click="copyTrace"
          class="flex-1 px-3 py-1.5 bg-gray-700/50 hover:bg-gray-700 text-gray-300 text-sm rounded transition-colors flex items-center justify-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
          </svg>
          Copier trace
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()
const run = computed(() => chat.currentRun)

const phaseClass = computed(() => {
  if (!run.value) return 'bg-gray-700 text-gray-400'
  switch (run.value.currentPhase) {
    case 'thinking': return 'bg-yellow-500/20 text-yellow-300'
    case 'tool': return 'bg-blue-500/20 text-blue-300'
    case 'streaming': return 'bg-purple-500/20 text-purple-300'
    case 'complete': return 'bg-green-500/20 text-green-300'
    case 'error': return 'bg-red-500/20 text-red-300'
    default: return 'bg-gray-700 text-gray-400'
  }
})

const phaseLabel = computed(() => {
  if (!run.value) return 'Inactif'
  switch (run.value.currentPhase) {
    case 'thinking': return 'Réflexion'
    case 'tool': return 'Outil'
    case 'streaming': return 'Streaming'
    case 'complete': return 'Terminé'
    case 'error': return 'Erreur'
    default: return 'Démarrage'
  }
})

function formatParams(params) {
  if (typeof params === 'string') return params
  return JSON.stringify(params, null, 2)
}

function formatDuration(ms) {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function copyTrace() {
  if (!run.value) return
  
  const trace = {
    model: run.value.model,
    duration: run.value.duration,
    iterations: run.value.complete?.iterations,
    tools_used: run.value.complete?.tools_used,
    thinking: run.value.thinking,
    toolCalls: run.value.toolCalls
  }
  
  navigator.clipboard.writeText(JSON.stringify(trace, null, 2))
}
</script>
