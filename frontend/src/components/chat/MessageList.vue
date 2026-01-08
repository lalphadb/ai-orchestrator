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
      v-for="msg in messages"
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
        
        <!-- Content -->
        <div 
          class="prose prose-invert prose-sm max-w-none"
          :class="{ 'whitespace-pre-wrap': !isMarkdown(msg.content) }"
          v-html="renderContent(msg.content)"
        ></div>
        
        <!-- Meta info -->
        <div 
          v-if="msg.role === 'assistant' && !msg.streaming && (msg.tools_used?.length || msg.duration_ms || msg.model)"
          class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-gray-700/50"
        >
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
import { ref, watch, nextTick, onMounted } from 'vue'
import { marked } from 'marked'

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
