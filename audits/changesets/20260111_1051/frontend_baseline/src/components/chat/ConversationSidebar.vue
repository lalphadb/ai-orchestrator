<template>
  <div class="h-full flex flex-col bg-gray-900/50 border-r border-gray-700/50">
    <!-- Header -->
    <div class="p-3 border-b border-gray-700/50">
      <button
        @click="chat.newConversation()"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors font-medium"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Nouvelle conversation
      </button>
    </div>
    
    <!-- Search -->
    <div class="p-3 border-b border-gray-700/50">
      <div class="relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          v-model="chat.searchQuery"
          type="text"
          placeholder="Rechercher..."
          class="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
        />
      </div>
    </div>
    
    <!-- Conversations List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="chat.conversationsLoading" class="flex items-center justify-center py-8">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"></div>
      </div>
      
      <div v-else-if="chat.filteredConversations.length === 0" class="text-center py-8 text-gray-500 text-sm">
        Aucune conversation
      </div>
      
      <div v-else class="p-2 space-y-1">
        <div
          v-for="conv in chat.filteredConversations"
          :key="conv.id"
          @click="selectConversation(conv.id)"
          class="group relative px-3 py-2.5 rounded-lg cursor-pointer transition-colors"
          :class="chat.currentConversation?.id === conv.id 
            ? 'bg-primary-600/20 border border-primary-500/30' 
            : 'hover:bg-gray-800/50 border border-transparent'"
        >
          <!-- Title -->
          <div v-if="editingId !== conv.id" class="flex items-start gap-2">
            <svg class="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-300 truncate">{{ conv.title || 'Conversation sans titre' }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ formatDate(conv.updated_at) }}</p>
            </div>
          </div>
          
          <!-- Edit mode -->
          <input
            v-else
            ref="editInput"
            v-model="editTitle"
            @blur="saveEdit(conv.id)"
            @keydown.enter="saveEdit(conv.id)"
            @keydown.escape="cancelEdit"
            class="w-full px-2 py-1 bg-gray-800 border border-primary-500 rounded text-sm text-white focus:outline-none"
          />
          
          <!-- Actions -->
          <div 
            v-if="editingId !== conv.id"
            class="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-1"
          >
            <button
              @click.stop="startEdit(conv)"
              class="p-1 text-gray-500 hover:text-gray-300 transition-colors"
              title="Renommer"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
              </svg>
            </button>
            <button
              @click.stop="confirmDelete(conv)"
              class="p-1 text-gray-500 hover:text-red-400 transition-colors"
              title="Supprimer"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Delete Modal -->
  <Teleport to="body">
    <div v-if="deleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div class="bg-gray-800 rounded-xl p-6 max-w-sm w-full shadow-xl border border-gray-700">
        <h3 class="text-lg font-semibold text-white mb-2">Supprimer la conversation ?</h3>
        <p class="text-gray-400 text-sm mb-6">
          Cette action est irréversible. La conversation "{{ deleteModal.title || 'Sans titre' }}" sera définitivement supprimée.
        </p>
        <div class="flex gap-3 justify-end">
          <button
            @click="deleteModal = null"
            class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Annuler
          </button>
          <button
            @click="doDelete"
            class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
          >
            Supprimer
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const editingId = ref(null)
const editTitle = ref('')
const editInput = ref(null)
const deleteModal = ref(null)

function selectConversation(id) {
  if (editingId.value) return
  chat.selectConversation(id)
}

function startEdit(conv) {
  editingId.value = conv.id
  editTitle.value = conv.title || ''
  nextTick(() => {
    editInput.value?.focus()
    editInput.value?.select()
  })
}

function cancelEdit() {
  editingId.value = null
  editTitle.value = ''
}

async function saveEdit(id) {
  if (editTitle.value.trim()) {
    try {
      await chat.renameConversation(id, editTitle.value.trim())
    } catch (e) {
      console.error('Failed to rename:', e)
    }
  }
  cancelEdit()
}

function confirmDelete(conv) {
  deleteModal.value = conv
}

async function doDelete() {
  if (!deleteModal.value) return
  try {
    await chat.deleteConversation(deleteModal.value.id)
  } catch (e) {
    console.error('Failed to delete:', e)
  }
  deleteModal.value = null
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return 'À l\'instant'
  if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)} min`
  if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)}h`
  if (diff < 604800000) return date.toLocaleDateString('fr-FR', { weekday: 'short' })
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}
</script>
