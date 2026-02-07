<template>
  <div class="h-[calc(100vh-3.5rem)] flex">
    <!-- Left Panel: Conversations Sidebar -->
    <div class="flex-shrink-0 transition-all duration-300" :class="showSidebar ? 'w-72' : 'w-0'">
      <ConversationSidebar v-if="showSidebar" />
    </div>

    <!-- Toggle sidebar button -->
    <button
      class="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-gray-800 border border-gray-700 rounded-r-lg hover:bg-gray-700 transition-colors"
      :class="showSidebar ? 'ml-72' : 'ml-0'"
      @click="showSidebar = !showSidebar"
    >
      <svg
        class="w-4 h-4 text-gray-400 transition-transform"
        :class="showSidebar ? '' : 'rotate-180'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Center Panel: Chat -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Chat header -->
      <div
        class="h-12 px-4 flex items-center justify-between border-b border-gray-700/50 bg-gray-900/30"
      >
        <div class="flex items-center gap-2">
          <h2 class="font-medium text-gray-200 truncate">
            {{ chat.currentConversation?.title || 'Nouvelle conversation' }}
          </h2>
          <span v-if="chat.currentConversation" class="text-xs text-gray-500">
            #{{ chat.currentConversation.id?.slice(0, 8) }}
          </span>
        </div>
      </div>

      <!-- Messages -->
      <MessageList :messages="chat.messages" @send="chat.sendMessage" />

      <!-- Input -->
      <MessageInput />
    </div>

    <!-- Right Panel: Run Inspector -->
    <div class="flex-shrink-0 transition-all duration-300" :class="showInspector ? 'w-80' : 'w-0'">
      <RunInspector v-if="showInspector" />
    </div>

    <!-- Toggle inspector button -->
    <button
      class="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-gray-800 border border-gray-700 rounded-l-lg hover:bg-gray-700 transition-colors"
      :class="showInspector ? 'mr-80' : 'mr-0'"
      @click="showInspector = !showInspector"
    >
      <svg
        class="w-4 h-4 text-gray-400 transition-transform"
        :class="showInspector ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import ConversationSidebar from '@/components/chat/ConversationSidebar.vue'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import RunInspector from '@/components/chat/RunInspector.vue'

const chat = useChatStore()
const auth = useAuthStore()

const showSidebar = ref(true)
const showInspector = ref(true)

onMounted(() => {
  // FIX: Ne connecter WebSocket que si authentifié
  if (auth.isAuthenticated) {
    chat.initWebSocket()
    chat.fetchModels()
    chat.fetchConversations()
  } else {
    console.warn('WebSocket non initialisé: utilisateur non authentifié')
  }
})
</script>
