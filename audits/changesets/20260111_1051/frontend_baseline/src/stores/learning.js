/**
 * Store Pinia pour le système d'apprentissage
 * Gère le feedback utilisateur et les stats d'apprentissage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useLearningStore = defineStore('learning', () => {
  // State
  const stats = ref(null)
  const feedbackStats = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const lastFeedback = ref(null)

  // Actions
  
  /**
   * Envoie un feedback positif
   */
  async function sendPositiveFeedback(messageId, conversationId, query, response, toolsUsed = []) {
    return sendFeedback({
      message_id: messageId,
      conversation_id: conversationId,
      feedback_type: 'positive',
      query,
      response,
      tools_used: toolsUsed
    })
  }

  /**
   * Envoie un feedback négatif
   */
  async function sendNegativeFeedback(messageId, conversationId, query, response, toolsUsed = [], comment = null) {
    return sendFeedback({
      message_id: messageId,
      conversation_id: conversationId,
      feedback_type: 'negative',
      query,
      response,
      tools_used: toolsUsed,
      comment
    })
  }

  /**
   * Envoie une correction
   */
  async function sendCorrection(messageId, conversationId, query, response, correction, toolsUsed = []) {
    return sendFeedback({
      message_id: messageId,
      conversation_id: conversationId,
      feedback_type: 'correction',
      query,
      response,
      correction,
      tools_used: toolsUsed
    })
  }

  /**
   * Envoie un feedback générique
   */
  async function sendFeedback(feedbackData) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/learning/feedback', feedbackData)
      lastFeedback.value = {
        ...feedbackData,
        id: response.feedback_id,
        timestamp: new Date().toISOString()
      }
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Récupère les stats d'apprentissage
   */
  async function fetchLearningStats() {
    try {
      const response = await api.get('/learning/stats')
      stats.value = response
      return response
    } catch (err) {
      console.error('Erreur fetch learning stats:', err)
      return null
    }
  }

  /**
   * Récupère les stats de feedback
   */
  async function fetchFeedbackStats(hours = 24) {
    try {
      const response = await api.get(`/learning/feedback/stats?hours=${hours}`)
      feedbackStats.value = response
      return response
    } catch (err) {
      console.error('Erreur fetch feedback stats:', err)
      return null
    }
  }

  /**
   * Enregistre une préférence utilisateur
   */
  async function setPreference(preferenceType, preferenceValue) {
    try {
      await api.post(`/learning/preference?preference_type=${preferenceType}&preference_value=${preferenceValue}`)
      return true
    } catch (err) {
      console.error('Erreur set preference:', err)
      return false
    }
  }

  /**
   * Récupère le contexte utilisateur
   */
  async function fetchUserContext() {
    try {
      const response = await api.get('/learning/context')
      return response.context
    } catch (err) {
      console.error('Erreur fetch user context:', err)
      return {}
    }
  }

  // Computed
  const hasStats = computed(() => stats.value !== null)
  const isConnected = computed(() => stats.value?.status === 'connected')
  const experiencesCount = computed(() => stats.value?.experiences_count || 0)
  const patternsCount = computed(() => stats.value?.patterns_count || 0)

  return {
    // State
    stats,
    feedbackStats,
    loading,
    error,
    lastFeedback,

    // Actions
    sendPositiveFeedback,
    sendNegativeFeedback,
    sendCorrection,
    sendFeedback,
    fetchLearningStats,
    fetchFeedbackStats,
    setPreference,
    fetchUserContext,

    // Computed
    hasStats,
    isConnected,
    experiencesCount,
    patternsCount
  }
})
