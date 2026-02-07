<template>
  <div class="h-full flex bg-gray-900 text-gray-100" role="main" aria-label="Interface de chat">
    <!-- Left Panel: Conversations Sidebar -->
    <aside
      class="flex-shrink-0 transition-all duration-300 border-r border-gray-800"
      :class="showSidebar ? 'w-72' : 'w-0 overflow-hidden'"
      role="complementary"
      aria-label="Liste des conversations"
      :aria-expanded="showSidebar"
    >
      <ConversationSidebar v-if="showSidebar" />
    </aside>

    <!-- Toggle sidebar button (Floating) -->
    <button
      class="absolute top-4 z-10 p-1 bg-gray-800 border border-gray-700 rounded-r shadow-sm hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
      :class="showSidebar ? 'left-72' : 'left-0'"
      :aria-label="showSidebar ? 'Fermer la barre latérale' : 'Ouvrir la barre latérale'"
      :aria-expanded="showSidebar"
      :aria-controls="sidebarId"
      type="button"
      @click="toggleSidebar"
      @keydown="handleSidebarToggleKeydown"
    >
      <svg
        class="w-4 h-4 text-gray-400 transition-transform"
        :class="showSidebar ? '' : 'rotate-180'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Center Panel: Chat -->
    <main
      :id="mainContentId"
      class="flex-1 flex flex-col min-w-0 relative"
      role="region"
      aria-label="Zone de conversation"
    >
      <!-- Toggle sidebar button (In-flow when closed) -->
      <button
        v-if="!showSidebar"
        class="absolute left-0 top-4 z-10 p-1 bg-gray-800 border border-gray-700 rounded-r shadow-sm hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Ouvrir la barre latérale"
        :aria-expanded="false"
        :aria-controls="sidebarId"
        type="button"
        @click="toggleSidebar"
        @keydown="handleSidebarToggleKeydown"
      >
        <svg
          class="w-4 h-4 text-gray-400 rotate-180"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <!-- Chat header -->
      <header
        class="h-14 px-4 flex items-center justify-between border-b border-gray-800 bg-gray-900"
        role="banner"
      >
        <div class="flex items-center gap-2 pl-8">
          <h1 id="conversation-title" class="font-medium text-gray-200 truncate">
            {{ chat.currentConversation?.title || t('chat.newConversation') }}
          </h1>
          <span
            v-if="chat.currentConversation"
            class="text-xs text-gray-500"
            aria-label="Identifiant de conversation"
          >
            #{{ chat.currentConversation.id?.slice(0, 8) }}
          </span>
        </div>
      </header>

      <!-- Messages -->
      <section
        class="flex-1 overflow-hidden relative"
        role="log"
        aria-label="Messages de la conversation"
        aria-live="polite"
        aria-atomic="false"
      >
        <MessageList
          :messages="chat.messages"
          aria-labelledby="conversation-title"
          @send="chat.sendMessage"
        />
      </section>

      <!-- Input -->
      <section
        class="p-4 border-t border-gray-800 bg-gray-900"
        role="form"
        aria-label="Envoyer un message"
      >
        <MessageInput :placeholder="t('chat.placeholder')" @submit="handleMessageSubmit" />
      </section>
    </main>

    <!-- Right Panel: Run Inspector -->
    <aside
      :id="inspectorId"
      class="flex-shrink-0 transition-all duration-300 border-l border-gray-800"
      :class="showInspector ? 'w-96' : 'w-0 overflow-hidden'"
      role="complementary"
      aria-label="Inspecteur d'exécution"
      :aria-expanded="showInspector"
    >
      <RunInspector v-if="showInspector" />
    </aside>

    <!-- Toggle inspector button -->
    <button
      class="absolute right-0 top-20 z-10 p-1.5 bg-gray-800 border border-gray-700 rounded-l-lg hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
      :class="showInspector ? 'mr-96' : 'mr-0'"
      :aria-label="showInspector ? 'Fermer l\'inspecteur' : 'Ouvrir l\'inspecteur'"
      :aria-expanded="showInspector"
      :aria-controls="inspectorId"
      type="button"
      @click="toggleInspector"
      @keydown="handleInspectorToggleKeydown"
    >
      <svg
        class="w-4 h-4 text-gray-400 transition-transform"
        :class="showInspector ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
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
import { t } from '@/i18n/messages'
import { useSkipLink, generateId, announceToScreenReader } from '@/composables/useAccessibility'
import ConversationSidebar from '@/components/chat/ConversationSidebar.vue'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import RunInspector from '@/components/chat/RunInspector.vue'

const chat = useChatStore()
const auth = useAuthStore()

// Accessibility IDs
const sidebarId = generateId('sidebar')
const inspectorId = generateId('inspector')
const mainContentId = generateId('main-content')

// State
const showSidebar = ref(true)
const showInspector = ref(true)

// Skip link for accessibility
useSkipLink(mainContentId)

// Toggle functions with accessibility announcements
function toggleSidebar() {
  showSidebar.value = !showSidebar.value
  announceToScreenReader(
    showSidebar.value ? 'Barre latérale ouverte' : 'Barre latérale fermée',
    'polite'
  )
}

function toggleInspector() {
  showInspector.value = !showInspector.value
  announceToScreenReader(showInspector.value ? 'Inspecteur ouvert' : 'Inspecteur fermé', 'polite')
}

// Keyboard handlers
function handleSidebarToggleKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleSidebar()
  }
}

function handleInspectorToggleKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleInspector()
  }
}

function handleMessageSubmit(message) {
  chat.sendMessage(message)
  announceToScreenReader('Message envoyé', 'polite')
}

onMounted(() => {
  if (auth.isAuthenticated) {
    // Ensure WS is connected and data loaded
    if (chat.wsState === 'disconnected') {
      chat.initWebSocket()
    }
    if (chat.availableModels.length === 0) {
      chat.fetchModels()
    }
    if (chat.conversations.length === 0) {
      chat.fetchConversations()
    }
  }
})
</script>

<style>
/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only:focus {
  position: absolute;
  width: auto;
  height: auto;
  padding: 0.5rem 1rem;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
  z-index: 50;
}

/* Focus visible styles */
button:focus-visible,
[role='button']:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
