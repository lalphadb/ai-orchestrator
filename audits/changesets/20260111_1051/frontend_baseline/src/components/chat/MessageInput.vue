<template>
  <div class="p-4 border-t border-gray-700/50 bg-gray-900/30">
    <!-- Model selector -->
    <div class="flex items-center gap-3 mb-3">
      <select
        v-model="chat.currentModel"
        class="px-3 py-1.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-primary-500/50"
      >
        <option v-for="model in chat.availableModels" :key="model" :value="model">
          {{ model }}
        </option>
      </select>
      
      <div class="flex items-center gap-2 ml-auto">
        <!-- WS Status -->
        <div class="flex items-center gap-1.5">
          <span 
            class="w-2 h-2 rounded-full"
            :class="{
              'bg-green-500': chat.wsState === 'connected',
              'bg-yellow-500 animate-pulse': chat.wsState === 'connecting' || chat.wsState === 'reconnecting',
              'bg-red-500': chat.wsState === 'disconnected'
            }"
          ></span>
          <span class="text-xs text-gray-500">
            {{ wsLabel }}
          </span>
        </div>
        
        <!-- Export -->
        <button
          v-if="chat.currentConversation"
          @click="showExportMenu = !showExportMenu"
          class="p-1.5 text-gray-500 hover:text-gray-300 transition-colors relative"
          title="Exporter"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
          
          <!-- Export dropdown -->
          <div 
            v-if="showExportMenu"
            class="absolute bottom-full right-0 mb-2 py-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl min-w-32"
          >
            <button
              @click="exportAs('json')"
              class="w-full px-3 py-1.5 text-left text-sm text-gray-300 hover:bg-gray-700/50"
            >
              Export JSON
            </button>
            <button
              @click="exportAs('markdown')"
              class="w-full px-3 py-1.5 text-left text-sm text-gray-300 hover:bg-gray-700/50"
            >
              Export Markdown
            </button>
          </div>
        </button>
      </div>
    </div>
    
    <!-- Input -->
    <div class="relative">
      <textarea
        ref="inputRef"
        v-model="message"
        @keydown="handleKeydown"
        :disabled="chat.isLoading"
        placeholder="Tapez votre message... (Entrée pour envoyer, Shift+Entrée pour nouvelle ligne)"
        rows="1"
        class="w-full px-4 py-3 pr-12 bg-gray-800/50 border border-gray-700/50 rounded-xl text-gray-200 placeholder-gray-500 resize-none focus:outline-none focus:border-primary-500/50 transition-colors disabled:opacity-50"
        :style="{ height: textareaHeight }"
      ></textarea>
      
      <button
        @click="send"
        :disabled="!message.trim() || chat.isLoading"
        class="absolute right-2 bottom-2 p-2 rounded-lg transition-colors disabled:opacity-30"
        :class="message.trim() && !chat.isLoading 
          ? 'bg-primary-600 hover:bg-primary-500 text-white' 
          : 'bg-gray-700 text-gray-500'"
      >
        <svg v-if="!chat.isLoading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
        </svg>
        <div v-else class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const message = ref('')
const inputRef = ref(null)
const showExportMenu = ref(false)

const wsLabel = computed(() => {
  switch (chat.wsState) {
    case 'connected': return 'Connecté'
    case 'connecting': return 'Connexion...'
    case 'reconnecting': return 'Reconnexion...'
    default: return 'Déconnecté'
  }
})

const textareaHeight = computed(() => {
  const lines = message.value.split('\n').length
  const baseHeight = 48
  const lineHeight = 24
  const maxHeight = 200
  return Math.min(baseHeight + (lines - 1) * lineHeight, maxHeight) + 'px'
})

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function send() {
  if (!message.value.trim() || chat.isLoading) return
  chat.sendMessage(message.value)
  message.value = ''
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function exportAs(format) {
  const content = chat.exportConversation(format)
  if (!content) return
  
  const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `conversation-${chat.currentConversation.id}.${format === 'json' ? 'json' : 'md'}`
  a.click()
  URL.revokeObjectURL(url)
  showExportMenu.value = false
}

// Close export menu on click outside
watch(showExportMenu, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', closeExportMenu)
    }, 0)
  }
})

function closeExportMenu() {
  showExportMenu.value = false
  document.removeEventListener('click', closeExportMenu)
}
</script>
