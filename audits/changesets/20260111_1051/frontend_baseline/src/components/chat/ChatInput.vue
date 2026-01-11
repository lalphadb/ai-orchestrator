<template>
  <div class="p-4 border-t border-gray-700/50 bg-gray-900/30">
    <!-- Model selector -->
    <div class="flex items-center gap-3 mb-3">
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">Modèle:</span>
        <select
          v-model="chat.currentModel"
          class="px-2 py-1 bg-gray-800/50 border border-gray-700/50 rounded text-xs text-gray-300 focus:outline-none focus:border-primary-500/50"
        >
          <option v-for="m in chat.availableModels" :key="m" :value="m">
            {{ formatModelName(m) }}
          </option>
        </select>
      </div>
      
      <!-- WS Status -->
      <div class="flex items-center gap-1.5 ml-auto">
        <div 
          class="w-2 h-2 rounded-full"
          :class="{
            'bg-green-500': chat.wsState === 'connected',
            'bg-yellow-500 animate-pulse': chat.wsState === 'connecting' || chat.wsState === 'reconnecting',
            'bg-red-500': chat.wsState === 'disconnected'
          }"
        ></div>
        <span class="text-xs text-gray-500">{{ wsLabel }}</span>
      </div>
    </div>
    
    <!-- Input area -->
    <div class="relative">
      <textarea
        ref="inputRef"
        v-model="message"
        @keydown="handleKeydown"
        :disabled="chat.isLoading"
        placeholder="Tapez votre message... (Entrée pour envoyer, Shift+Entrée pour retour à la ligne)"
        rows="1"
        class="w-full px-4 py-3 pr-12 bg-gray-800/50 border border-gray-700/50 rounded-xl text-gray-200 placeholder-gray-500 resize-none focus:outline-none focus:border-primary-500/50 transition-colors disabled:opacity-50"
        :style="{ height: textareaHeight }"
      ></textarea>
      
      <!-- Send button -->
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
        <div v-else class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
      </button>
    </div>
    
    <!-- Hints -->
    <div class="flex items-center justify-between mt-2 text-xs text-gray-500">
      <span>⌘+Entrée pour envoyer</span>
      <span v-if="chat.currentConversation">
        Conversation: {{ chat.currentConversation.title || chat.currentConversation.id?.slice(0, 8) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const message = ref('')
const inputRef = ref(null)

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
  const minHeight = 48
  const lineHeight = 24
  const maxHeight = 200
  return Math.min(Math.max(minHeight, lines * lineHeight), maxHeight) + 'px'
})

function formatModelName(name) {
  if (!name) return name
  // Shorten long model names
  return name.replace(':latest', '').replace('-instruct', '').replace('-q4_K_M', '')
}

function handleKeydown(e) {
  // Cmd/Ctrl + Enter or just Enter (without Shift)
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault()
    send()
  } else if (e.key === 'Enter' && !e.shiftKey) {
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

// Auto-resize textarea
watch(message, () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.style.height = inputRef.value.scrollHeight + 'px'
    }
  })
})
</script>
