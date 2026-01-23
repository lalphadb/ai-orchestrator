<template>
  <div class="feedback-buttons flex items-center gap-1">
    <!-- Bouton Positif -->
    <button
      @click="handlePositive"
      :disabled="loading || feedbackSent"
      :class="[
        'p-1.5 rounded-lg transition-all duration-200',
        feedbackSent === 'positive' 
          ? 'bg-green-100 text-green-600' 
          : 'hover:bg-gray-100 text-gray-400 hover:text-green-500'
      ]"
      title="Réponse utile"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
      </svg>
    </button>

    <!-- Bouton Négatif -->
    <button
      @click="handleNegative"
      :disabled="loading || feedbackSent"
      :class="[
        'p-1.5 rounded-lg transition-all duration-200',
        feedbackSent === 'negative' 
          ? 'bg-red-100 text-red-600' 
          : 'hover:bg-gray-100 text-gray-400 hover:text-red-500'
      ]"
      title="Réponse pas utile"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
      </svg>
    </button>

    <!-- Bouton Correction -->
    <button
      @click="showCorrectionModal = true"
      :disabled="loading || feedbackSent"
      :class="[
        'p-1.5 rounded-lg transition-all duration-200',
        feedbackSent === 'correction' 
          ? 'bg-blue-100 text-blue-600' 
          : 'hover:bg-gray-100 text-gray-400 hover:text-blue-500'
      ]"
      title="Suggérer une correction"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    </button>

    <!-- Indicateur de chargement -->
    <span v-if="loading" class="ml-1">
      <svg class="w-4 h-4 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
    </span>

    <!-- Confirmation -->
    <span v-if="feedbackSent && !loading" class="ml-1 text-xs text-gray-500">
      ✓ Merci!
    </span>

    <!-- Modal Correction -->
    <Teleport to="body">
      <div 
        v-if="showCorrectionModal" 
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCorrectionModal = false"
      >
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
          <!-- Header -->
          <div class="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4">
            <h3 class="text-lg font-semibold text-white">Suggérer une correction</h3>
            <p class="text-blue-100 text-sm">Votre correction aidera l'IA à s'améliorer</p>
          </div>

          <!-- Body -->
          <div class="p-6">
            <!-- Réponse originale -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Réponse originale
              </label>
              <div class="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 max-h-32 overflow-y-auto">
                {{ response.substring(0, 300) }}{{ response.length > 300 ? '...' : '' }}
              </div>
            </div>

            <!-- Correction -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Votre correction <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="correctionText"
                rows="4"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Quelle aurait été la meilleure réponse?"
              ></textarea>
            </div>

            <!-- Commentaire optionnel -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Commentaire (optionnel)
              </label>
              <input
                v-model="commentText"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Pourquoi cette correction est meilleure?"
              />
            </div>
          </div>

          <!-- Footer -->
          <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
            <button
              @click="showCorrectionModal = false"
              class="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition"
            >
              Annuler
            </button>
            <button
              @click="submitCorrection"
              :disabled="!correctionText.trim() || loading"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Envoyer la correction
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useLearningStore } from '@/stores/learning'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  messageId: {
    type: String,
    required: true
  },
  query: {
    type: String,
    required: true
  },
  response: {
    type: String,
    required: true
  },
  toolsUsed: {
    type: Array,
    default: () => []
  }
})

const learningStore = useLearningStore()
const chatStore = useChatStore()

const loading = ref(false)
const feedbackSent = ref(null)
const showCorrectionModal = ref(false)
const correctionText = ref('')
const commentText = ref('')

async function handlePositive() {
  loading.value = true
  try {
    await learningStore.sendPositiveFeedback(
      props.messageId,
      chatStore.currentConversation?.id,
      props.query,
      props.response,
      props.toolsUsed
    )
    feedbackSent.value = 'positive'
  } catch (err) {
    console.error('Erreur feedback positif:', err)
  } finally {
    loading.value = false
  }
}

async function handleNegative() {
  loading.value = true
  try {
    await learningStore.sendNegativeFeedback(
      props.messageId,
      chatStore.currentConversation?.id,
      props.query,
      props.response,
      props.toolsUsed
    )
    feedbackSent.value = 'negative'
  } catch (err) {
    console.error('Erreur feedback négatif:', err)
  } finally {
    loading.value = false
  }
}

async function submitCorrection() {
  if (!correctionText.value.trim()) return

  loading.value = true
  try {
    await learningStore.sendCorrection(
      props.messageId,
      chatStore.currentConversation?.id,
      props.query,
      props.response,
      correctionText.value,
      props.toolsUsed
    )
    feedbackSent.value = 'correction'
    showCorrectionModal.value = false
    correctionText.value = ''
    commentText.value = ''
  } catch (err) {
    console.error('Erreur correction:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.feedback-buttons {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.feedback-buttons:hover {
  opacity: 1;
}
</style>
