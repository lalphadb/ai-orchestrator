<template>
  <div ref="container" class="flex-1 overflow-y-auto p-4 space-y-4">
    <!-- Empty state -->
    <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center">
      <div class="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
        <span class="text-white text-2xl font-bold">AI</span>
      </div>
      <h2 class="text-xl font-semibold text-white mb-2">AI Orchestrator</h2>
      <p class="text-gray-400 max-w-md mb-6">
        Un orchestrateur autonome avec boucle ReAct,<br/>capable d'exécuter des outils et d'interagir avec votre système.
      </p>
      <div class="grid grid-cols-2 gap-3 max-w-md">
        <button
          v-for="example in examples"
          :key="example"
          @click="$emit('send', example)"
          class="px-4 py-3 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 rounded-xl text-sm text-gray-300 text-left transition-colors"
        >
          {{ example }}
        </button>
      </div>
    </div>
    
    <!-- Messages -->
    <div
      v-for="(msg, index) in messages"
      :key="msg.id"
      class="flex gap-3"
      :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <!-- Avatar -->
      <div v-if="msg.role === 'assistant'" class="flex-shrink-0">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
          <span class="text-white text-sm font-bold">AI</span>
        </div>
      </div>
      
      <!-- Message content -->
      <div
        class="max-w-[80%] rounded-2xl px-4 py-3"
        :class="msg.role === 'user' 
          ? 'bg-primary-600 text-white' 
          : msg.isError 
            ? 'bg-red-500/10 border border-red-500/30 text-red-200'
            : 'bg-gray-800/80 text-gray-200'"
      >
        <!-- Streaming indicator -->
        <div v-if="msg.streaming" class="flex items-center gap-2 mb-2 text-primary-300">
          <div class="animate-spin w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full"></div>
          <span class="text-sm">Génération...</span>
        </div>
        
        <!-- Special: Models Display -->
        <ModelsDisplay 
          v-if="isModelsList(msg.content)"
          :models="parseModels(msg.content)"
        />
        
        <!-- Regular Content -->
        <div 
          v-else
          class="prose prose-invert prose-sm max-w-none"
          :class="{ 'whitespace-pre-wrap': !isMarkdown(msg.content) }"
          v-html="renderContent(msg.content)"
        ></div>
        
        <!-- Meta info + Feedback -->
        <div 
          v-if="msg.role === 'assistant' && !msg.streaming"
          class="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2 border-t border-gray-700/50"
        >
          <!-- Meta gauche -->
          <div class="flex flex-wrap items-center gap-2">
            <span v-if="msg.model" class="text-xs text-gray-500">{{ msg.model }}</span>
            <span v-if="msg.duration_ms" class="text-xs text-gray-500">{{ formatDuration(msg.duration_ms) }}</span>
            <span v-if="msg.iterations" class="text-xs text-gray-500">{{ msg.iterations }} iter</span>
            <div v-if="msg.tools_used?.length" class="flex flex-wrap gap-1">
              <span 
                v-for="t in msg.tools_used" 
                :key="t"
                class="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs text-gray-400"
              >
                {{ t }}
              </span>
            </div>
          </div>
          
          <!-- Feedback buttons droite -->
          <FeedbackButtons
            v-if="msg.content && !msg.isError"
            :message-id="msg.id"
            :query="getQueryForMessage(index)"
            :response="msg.content"
            :tools-used="msg.tools_used || []"
          />
        </div>
        
        <!-- Learning indicator (si contexte appris utilisé) -->
        <div 
          v-if="msg.learning?.context_used"
          class="mt-2 flex items-center gap-1 text-xs text-purple-400"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span>Enrichi par l'apprentissage</span>
        </div>
      </div>
      
      <!-- User avatar -->
      <div v-if="msg.role === 'user'" class="flex-shrink-0">
        <div class="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
          <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
          </svg>
        </div>
      </div>
    </div>
    
    <!-- Scroll anchor -->
    <div ref="scrollAnchor"></div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import FeedbackButtons from './FeedbackButtons.vue'
import ModelsDisplay from './ModelsDisplay.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] }
})

defineEmits(['send'])

const container = ref(null)
const scrollAnchor = ref(null)

const examples = [
  "Quel est le status du serveur ?",
  "Liste les conteneurs Docker",
  "Montre l'espace disque",
  "Quelles sont les mises à jour disponibles ?"
]

// Auto-scroll on new messages
watch(() => props.messages, () => {
  nextTick(() => {
    scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
  })
}, { deep: true })

// Also watch streaming content
watch(() => props.messages[props.messages.length - 1]?.content, () => {
  if (props.messages[props.messages.length - 1]?.streaming) {
    nextTick(() => {
      scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
    })
  }
})

/**
 * Detect if content is a models list (JSON array with name/size/available fields)
 */
function isModelsList(content) {
  if (!content || typeof content !== 'string') return false
  
  // Check for multiple model-like JSON objects
  const modelPattern = /\{\s*"name":\s*"[^"]+",\s*"size":\s*\d+/g
  const matches = content.match(modelPattern)
  
  return matches && matches.length >= 3
}

/**
 * Parse models from content string
 */
function parseModels(content) {
  if (!content) return []
  
  try {
    // Try parsing as JSON array first
    const parsed = JSON.parse(content)
    if (Array.isArray(parsed)) return parsed
    if (parsed.models && Array.isArray(parsed.models)) return parsed.models
  } catch {}
  
  // Extract individual model objects from text
  const models = []
  const regex = /\{\s*"name":\s*"([^"]+)"[^}]*"size":\s*(\d+)[^}]*"modified_at":\s*"([^"]+)"[^}]*"available":\s*(true|false)\s*\}/g
  
  let match
  while ((match = regex.exec(content)) !== null) {
    models.push({
      name: match[1],
      size: parseInt(match[2]),
      modified_at: match[3],
      available: match[4] === 'true'
    })
  }
  
  // Alternative pattern (different field order)
  if (models.length === 0) {
    const altRegex = /\{\s*"name":\s*"([^"]+)"[^}]*\}/g
    while ((match = altRegex.exec(content)) !== null) {
      const objStr = match[0]
      const nameMatch = objStr.match(/"name":\s*"([^"]+)"/)
      const sizeMatch = objStr.match(/"size":\s*(\d+)/)
      const availMatch = objStr.match(/"available":\s*(true|false)/)
      const modMatch = objStr.match(/"modified_at":\s*"([^"]+)"/)
      
      if (nameMatch) {
        models.push({
          name: nameMatch[1],
          size: sizeMatch ? parseInt(sizeMatch[1]) : 0,
          modified_at: modMatch ? modMatch[1] : null,
          available: availMatch ? availMatch[1] === 'true' : true
        })
      }
    }
  }
  
  return models
}

function isMarkdown(content) {
  if (!content) return false
  return content.includes('```') || content.includes('**') || content.includes('##') || content.includes('- ')
}

function renderContent(content) {
  if (!content) return ''
  if (isMarkdown(content)) {
    return marked.parse(content, { breaks: true, gfm: true })
  }
  return escapeHtml(content)
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatDuration(ms) {
  if (!ms) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Récupère la question utilisateur correspondant à une réponse assistant
 */
function getQueryForMessage(assistantIndex) {
  // Chercher le message user précédent
  for (let i = assistantIndex - 1; i >= 0; i--) {
    if (props.messages[i].role === 'user') {
      return props.messages[i].content
    }
  }
  return ''
}
</script>

<style>
.prose pre {
  @apply bg-gray-900/80 rounded-lg p-3 overflow-x-auto;
}
.prose code {
  @apply bg-gray-700/50 px-1.5 py-0.5 rounded text-sm;
}
.prose pre code {
  @apply bg-transparent p-0;
}
</style>
